#!/usr/bin/env python3
"""Telas de menu servidas pelo 8.5 que, ao abrir, mandam o navegador para uma tela que
o proxy serve pelo 7.4 (redirecionamento imediato ou iframe carregado na abertura).

Uso (da raiz do repo):
     python3 scratchpad/redirecionamentos.py <SID> <saida.tsv> [AREA,AREA...]
     (areas: inicio do nome em atendcadarea, sem "DB:"; padrao TRIBUT,EDUCA,RECURSOS.
      No SQL o filtro e ILIKE '%AREA%', ou seja, TRECHO do nome, nao so o inicio.)
     <SID>: sessao autenticada do 7.4 (o rotear.py 8b acha a mais recente sozinho).
     Antes de cada GET copia /tmp/_sess.bak (dentro do ecidade_php74; quem o cria e o
     cmp.py) sobre a sessao <SID>, porque uma tela pode estragar a sessao. Nem este script
     nem o rotear.py criam o .bak: se ele nao existe o cp falha em silencio; se e de outra
     sessao, sobrescreve a do <SID> com aquele conteudo.

Saida: uma linha por (classe, tipo, tela de origem, destino, areas). Classe NO_7.4 e o
que importa: destino que o proxy manda ao 7.4. Os destinos que JA estao no 8.5 (abas
roteadas) tambem sao abertos, para pegar o segundo salto.

Como faz: lista do banco as telas de menu das areas e fica com as que o proxy ja serve pelo
8.5 (mesmo criterio do nginx: LOC + MAP). Faz GET de cada uma DIRETO no 8.5 (:8085, com o
cookie da sessao) e procura no cabecalho `Location:`, no corpo `<script>location=...</script>`
e `<iframe|frame src=...>`. Cada destino .php e classificado: pasta, inexistente, NO_7.4 ou,
se ja esta no 8.5, entra na fila para ser aberto tambem (segundo salto). So ve o que a tela
faz ao abrir por GET sem parametros; aba criada por JavaScript ao clicar fica de fora.

Entradas: o banco, docker/proxy/faseb_map.conf, a lista de ecidade/, a copia do regex do
  `location` (LOC, mantida a mao/pelo rotear.py) e os containers no ar.
Saida: <saida.tsv> (classe, tipo, origem, destino, areas; ordenado, sem repeticao) e, no
  terminal, progresso a cada 200 telas e a contagem por (classe, tipo).
Usado em: passo 8b do guia (abas e redirecionamentos, 14a lacuna), normalmente via
  `python3 scratchpad/rotear.py 8b <AREA>`; a lista NO_7.4/iframe alimenta
  docker/proxy/faseb_map_abas.txt.
"""
import os, re, subprocess, sys, collections

RAIZ = "/home/diego/e-cidade"                     # caminho fixo (os outros scripts usam __file__)
ECI = os.path.join(RAIZ, "ecidade")
SID, SAIDA = sys.argv[1], sys.argv[2]
AREAS = (sys.argv[3] if len(sys.argv) > 3 else "TRIBUT,EDUCA,RECURSOS").upper().split(",")
SESS = f"/var/lib/php/sessions/sess_{SID}"          # dentro do container (volume compartilhado)

# mesmo criterio do nginx: location por prefixo + map por nome exato. LOC e COPIA do
# regex do nginx.conf -- prefixo novo no `location` tem de entrar aqui (o rotear.py faz isso)
# base-php74: nada vai ao 8.5 ainda. "nenhum_prefixo_no_85" e um marcador que nao casa com nenhuma tela;
# o rotear.py acrescenta os prefixos depois dele (ex.: nenhum_prefixo_no_85|soc|hab) ao rotear um lote.
LOC = re.compile(r"^(?:nenhum_prefixo_no_85)[0-9]*_", re.I)
MAP = {l.split()[0].lower() for l in open(os.path.join(RAIZ, "docker/proxy/faseb_map.conf"))
       if l.strip() and not l.startswith("#")}
def no85(nome): return bool(LOC.match(nome)) or nome.lower() in MAP

# (area, modulo, funcao COM o ?parametro) dos itens de menu das areas pedidas: a tela e
# aberta com os parametros que o menu passa
SQL = ("SELECT DISTINCT replace(a.at25_descr,'DB:',''), m.nome_modulo, di.funcao "
       "FROM configuracoes.atendcadareamod am "
       "JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea "
       "JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item "
       "JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item "
       "JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho "
       "WHERE split_part(di.funcao,'?',1) ~ '^[A-Za-z]+[0-9]*_.*\\.php$' "
       "AND (" + " OR ".join(f"a.at25_descr ILIKE '%{a}%'" for a in AREAS) + ")")
out = subprocess.run(["docker", "exec", "-e", "PGCLIENTENCODING=UTF8", "ecidade_database", "psql", "-U", "postgres",
                      "-d", "ecidade", "-tA", "-F", "\t", "-c", SQL], capture_output=True, check=True).stdout.decode()

disco = {f.lower(): f for f in os.listdir(ECI) if os.path.isfile(os.path.join(ECI, f))}
itens = collections.defaultdict(set)              # funcao (com parametro) -> {(area, modulo)}
for l in out.splitlines():
    area, mod, funcao = l.split("\t")
    nome = funcao.split("?")[0].lower()
    if nome in disco and no85(disco[nome]):
        itens[funcao].add((area, mod))

# roda um comando de shell e devolve o CompletedProcess (stdout em bytes)
def sh(c): return subprocess.run(["bash", "-c", c], capture_output=True)

# <script> que so faz `[window.|document.|parent.]location[.href] = '...'` -- o
# redirecionamento imediato que db_redireciona() emite
RX_REDIR = re.compile(rb"<script[^>]*>\s*(?:window\.|document\.|parent\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]\s*;?\s*</script>", re.I)
# src de <iframe ...> ou <frame ...>
RX_IFRAME = re.compile(rb"<i?frame\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"]", re.I)

def destino(url):
    """URL achada na resposta (bytes) -> nome do arquivo de destino, sem query, ancora,
    esquema/host, o prefixo /w/<n>/ do proxy e o ./ inicial. Pasta, se houver, fica."""
    u = url.decode("latin1").split("?")[0].split("#")[0]
    u = re.sub(r"^(?:https?://[^/]+)?/?(?:w/[0-9]+/)?(?:\./)?", "", u)
    return u

# fila: funcoes do menu (com parametro), depois as abas ja no 8.5 achadas no caminho.
# vistos guarda os nomes em minusculas (das funcoes do menu, ainda COM o ?parametro)
linhas, n = [], 0
fila, vistos = sorted(itens), set(f.lower() for f in itens)
while fila:
    funcao = fila.pop(0)
    n += 1
    sh(f"docker exec -u root ecidade_php74 sh -c 'cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}'")
    r = sh(f"curl -s -m 60 -D - -b 'ECIDADEWINDOWMAIN={SID}' 'http://localhost:8085/{funcao}'")
    resp = r.stdout
    # curl -D - poe os cabecalhos antes do corpo, separados pela primeira linha vazia
    cab, _, corpo = resp.partition(b"\r\n\r\n")
    achados = []
    m = re.search(rb"^Location:\s*(\S+)", cab, re.I | re.M)
    if m: achados.append(("redireciona", destino(m.group(1))))
    for m in RX_REDIR.finditer(corpo): achados.append(("redireciona", destino(m.group(1))))
    for m in RX_IFRAME.finditer(corpo): achados.append(("iframe", destino(m.group(1))))
    for tipo, d in achados:
        if not d.lower().endswith(".php"): continue
        if "/" in d:
            classe = "pasta"                       # dbforms/, extension/...: o proxy nunca roteia por pasta
        elif d.lower() not in disco:
            classe = "inexistente"
        elif no85(disco[d.lower()]):
            # destino tambem no 8.5: sem problema -- mas abri-lo tambem, porque a aba
            # pode abrir outra aba (segundo salto), que a lista do menu nao conhece
            if d.lower() not in vistos:
                vistos.add(d.lower()); fila.append(disco[d.lower()]); itens[disco[d.lower()]] |= itens[funcao]
            continue
        else:
            classe = "NO_7.4"
        areas = "; ".join(sorted(f"{a}/{mo}" for a, mo in itens[funcao]))
        linhas.append((classe, tipo, funcao, d, areas))
    if n % 200 == 0: print(f"  ... {n}/{len(vistos)}", flush=True)

with open(SAIDA, "w") as f:
    for l in sorted(set(linhas)): f.write("\t".join(l) + "\n")
print(f"telas no 8.5 examinadas: {n} (menu + abas ja roteadas)")
c = collections.Counter((l[0], l[1]) for l in set(linhas))
for k, v in sorted(c.items()): print(f"  {k[0]:12s} {k[1]:12s} {v}")
