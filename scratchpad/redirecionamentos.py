#!/usr/bin/env python3
"""Telas de menu servidas pelo 8.5 que, ao abrir, mandam o navegador para uma tela que
o proxy serve pelo 5.6 (redirecionamento imediato ou iframe carregado na abertura).

Uso: python3 redirecionamentos.py <SID> <saida.tsv> [AREA,AREA...]
     (areas: inicio do nome em atendcadarea, sem "DB:"; padrao TRIBUT,EDUCA,RECURSOS)

Saida: uma linha por (classe, tipo, tela de origem, destino, areas). Classe NO_5.6 e o
que importa: destino que o proxy manda ao 5.6. Os destinos que JA estao no 8.5 (abas
roteadas) tambem sao abertos, para pegar o segundo salto.
"""
import os, re, subprocess, sys, collections

RAIZ = "/home/diego/e-cidade"
ECI = os.path.join(RAIZ, "ecidade")
SID, SAIDA = sys.argv[1], sys.argv[2]
AREAS = (sys.argv[3] if len(sys.argv) > 3 else "TRIBUT,EDUCA,RECURSOS").upper().split(",")
SESS = f"/var/lib/php/sessions/sess_{SID}"

# mesmo criterio do nginx: location por prefixo + map por nome exato
LOC = re.compile(r"^(?:cem|itbi?|agua?|jur|div|mar|not|fis|iss|dvr|arr|tri|inf|tra|tre|esc|rel|sec|bib|mer|edu|rh|eso|rec|pes|ac|aco|ouv|lic|vei|pat)[0-9]*_", re.I)
MAP = {l.split()[0].lower() for l in open(os.path.join(RAIZ, "docker/proxy/faseb_map.conf"))
       if l.strip() and not l.startswith("#")}
def no85(nome): return bool(LOC.match(nome)) or nome.lower() in MAP

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

def sh(c): return subprocess.run(["bash", "-c", c], capture_output=True)

RX_REDIR = re.compile(rb"<script[^>]*>\s*(?:window\.|document\.|parent\.)?location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]\s*;?\s*</script>", re.I)
RX_IFRAME = re.compile(rb"<i?frame\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"]", re.I)

def destino(url):
    u = url.decode("latin1").split("?")[0].split("#")[0]
    u = re.sub(r"^(?:https?://[^/]+)?/?(?:w/[0-9]+/)?(?:\./)?", "", u)
    return u

linhas, n = [], 0
fila, vistos = sorted(itens), set(f.lower() for f in itens)
while fila:
    funcao = fila.pop(0)
    n += 1
    sh(f"docker exec -u root ecidade_php56 sh -c 'cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}'")
    r = sh(f"curl -s -m 60 -D - -b 'ECIDADEWINDOWMAIN={SID}' 'http://localhost:8085/{funcao}'")
    resp = r.stdout
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
            classe = "NO_5.6"
        areas = "; ".join(sorted(f"{a}/{mo}" for a, mo in itens[funcao]))
        linhas.append((classe, tipo, funcao, d, areas))
    if n % 200 == 0: print(f"  ... {n}/{len(vistos)}", flush=True)

with open(SAIDA, "w") as f:
    for l in sorted(set(linhas)): f.write("\t".join(l) + "\n")
print(f"telas no 8.5 examinadas: {n} (menu + abas ja roteadas)")
c = collections.Counter((l[0], l[1]) for l in set(linhas))
for k, v in sorted(c.items()): print(f"  {k[0]:12s} {k[1]:12s} {v}")
