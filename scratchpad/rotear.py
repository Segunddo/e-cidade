#!/usr/bin/env python3
"""Passos 8 e 8b do guia (roteamento no proxy) em um comando. Sem --aplicar, SO MOSTRA o que mudaria.

Uso (da raiz do repositorio):
    python3 scratchpad/rotear.py location <prefixo> [<prefixo> ...] [--aplicar]
    python3 scratchpad/rotear.py map <area>:<pref>[,<pref>...] [--aplicar]
    python3 scratchpad/rotear.py abas <tela> [<tela> ...] [--aplicar]
    python3 scratchpad/rotear.py 8b <AREA> [--todas]

    python3 scratchpad/rotear.py location soc hab              # mostra a linha do nginx antes e depois
    python3 scratchpad/rotear.py location soc hab --aplicar    # aplica, testa, recria o proxy e confere
    python3 scratchpad/rotear.py map assist:pre,con --aplicar   # so as telas que o banco da a area
    python3 scratchpad/rotear.py abas hab1_avaliacao004 --aplicar
    python3 scratchpad/rotear.py 8b ASSIST                     # abas/redirecionamentos que voltam ao 7.4

Os modos (qual usar: guia, "O fluxo de uma area", B, e passo 8):
    location  prefixo INTEIRO para o 8.5 (nenhuma outra area pendente usa o prefixo). Acrescenta os
              prefixos a alternancia do `location` em docker/proxy/nginx.conf E as duas copias desse
              regex que os scripts usam para saber o que o 8.5 serve (scratchpad/dimensiona.py e
              scratchpad/redirecionamentos.py) -- esquecer as copias faz as medicoes seguintes contarem
              as telas como "no 7.4".
    map       so as telas que o banco atribui a area (prefixo compartilhado). Acrescenta o argumento ao
              comando da linha 2 do docker/proxy/faseb_map.conf e regenera o arquivo com o
              scratchpad/gera_map_faseb.py -- que REESCREVE o arquivo inteiro, por isso o comando dos
              lotes anteriores e reaproveitado -- e confere que nenhuma tela saiu do map.
    abas      destinos que o 8b achou no 7.4 (abas, redirecionamentos): acrescenta os nomes, em
              minuscula, a docker/proxy/faseb_map_abas.txt e regenera o map do mesmo jeito.
    8b        roda o scratchpad/redirecionamentos.py nas telas de menu da AREA (e, com --todas, das
              areas ja concluidas) e mostra as que ainda mandam o usuario ao 7.4. Nao altera nada.

Com --aplicar (location, map, abas):
    1. grava as alteracoes, guardando o conteudo anterior de cada arquivo;
    2. testa a configuracao com `nginx -t` num container DESCARTAVEL -- se falhar, desfaz tudo e para
       (uma config quebrada derrubaria o proxy: aconteceu no lote 5 do Financeiro);
    3. recria o proxy (`up -d --force-recreate`: o nginx.conf e bind mount de arquivo unico, reload nao basta);
    4. confere o cabecalho X-Ecidade-Runtime de algumas telas novas (com e sem /w/2/) e do login.php.
    Depois, rode o modo 8b. Os arquivos alterados entram no commit do lote (passo 9).

Pre-requisitos: os containers no ar (o proxy e o banco). O 8b precisa de sessao autenticada (achada sozinha).
Codigo de saida: 0 = OK; 1 = nginx -t falhou, conferencia falhou ou 8b achou telas no 7.4; 2 = uso/pre-requisito.

As ALTERACOES ficam no git (docker/proxy/ e scratchpad/): para desfazer, `git checkout -- <arquivo>` e
recriar o proxy.

Como faz: edita texto com regex (location), ou regenera o map com o gerador versionado e compara o conjunto de
entradas `<tela> php85;` antes e depois (map/abas); valida com `nginx -t` antes de tocar no proxy de verdade e,
depois de recriado, pede as telas por curl a :8090 e le o cabecalho X-Ecidade-Runtime.
Entradas: docker/proxy/nginx.conf, faseb_map.conf, faseb_map_abas.txt, as listas LOC de dimensiona.py e
redirecionamentos.py, os .php de ecidade/ e (8b) a sessao do 7.4. Saidas: o resumo no terminal; com --aplicar,
esses arquivos alterados e o container ecidade_proxy recriado; o 8b grava ecidade/tmp/rotear_8b.tsv.
"""
import argparse, os, re, subprocess, sys, time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ECIDADE = os.path.join(RAIZ, "ecidade")
NGINX = "docker/proxy/nginx.conf"
MAP = "docker/proxy/faseb_map.conf"
ABAS = "docker/proxy/faseb_map_abas.txt"
# Os tres lugares com a MESMA lista de prefixos do location: (arquivo, regex que separa a lista).
# Grupo 2 = a lista "cem|itbi?|...|sys". Precisam mudar juntos.
# Os regex casam o TEXTO-FONTE de cada arquivo (por isso os \( \? \[ escapados): o do nginx casa
# `location ~* ^(?:/w/[0-9]+)?/(?:(?:` e os dos scripts casam `LOC = re.compile(r"^(?:`. A lista termina
# no primeiro ")", entao nenhum prefixo pode conter parentese (os que usam "?" como itbi? funcionam).
LISTAS = [
    # So a linha ATIVA do location (re.M + ^ sem "#"): na base-php74 o bloco nasce comentado, e editar a linha
    # comentada nao teria efeito no nginx. Sem linha ativa, modo_location cria o bloco (BLOCO_LOCATION).
    (NGINX, re.compile(r"^([ \t]*location ~\* \^\(\?:/w/\[0-9\]\+\)\?/\(\?:\(\?:)([^)]+)(\))", re.M)),
    ("scratchpad/dimensiona.py", re.compile(r"(LOC = re\.compile\(r\"\^\(\?:)([^)]+)(\))")),
    ("scratchpad/redirecionamentos.py", re.compile(r"(LOC = re\.compile\(r\"\^\(\?:)([^)]+)(\))")),
]

# Bloco do location criado quando o nginx.conf ainda nao tem um ativo (base-php74 no inicio): vai antes do
# "location /" de tudo o mais, com os prefixos do primeiro lote roteado.
BLOCO_LOCATION = ('    location ~* ^(?:/w/[0-9]+)?/(?:(?:{prefixos})[0-9]*_) {{\n'
                  '        add_header X-Ecidade-Runtime "PHP-8.5 (migrado)" always;\n'
                  '        proxy_pass http://php85;\n'
                  '    }}\n\n')
ANTES_DO_BLOCO = "    # ---- TUDO O MAIS"

def erro(msg):
    """Erro de uso ou de pre-requisito: mensagem no stderr e saida com codigo 2."""
    print("ERRO: " + msg, file=sys.stderr)
    sys.exit(2)

def sh(cmd, timeout=None):
    """Roda um comando (lista de argumentos) e devolve (codigo, stdout, stderr) decodificados como latin-1."""
    r = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    return r.returncode, r.stdout.decode("latin-1"), r.stderr.decode("latin-1")

def ler(p):
    # os arquivos que este script edita (nginx.conf, map, .py) sao UTF-8/ASCII, diferente do codigo da base
    return open(p, encoding="utf-8").read()

def gravar(p, t):
    open(p, "w", encoding="utf-8").write(t)

def runtime(url):
    """O valor do cabecalho X-Ecidade-Runtime que o proxy devolve para a URL."""
    _, out, _ = sh(["curl", "-sI", "-m", "20", f"http://localhost:8090/{url}"])
    m = re.search(r"x-ecidade-runtime:\s*(.+)", out, re.I)
    return m.group(1).strip() if m else "?"

def comando_do_map():
    """Os argumentos do gera_map_faseb.py que geraram o faseb_map.conf atual (linha 2 do arquivo)."""
    linhas = ler(MAP).splitlines()
    m = re.search(r"gera_map_faseb\.py\s+(.+)", linhas[1]) if len(linhas) > 1 else None
    if not m:
        # Map nunca gerado (base-php74 no inicio: so comentarios, nenhuma entrada): nao ha lote anterior a
        # preservar, e o primeiro `map` comeca do zero. Com entradas e sem o comando, recusar: regenerar
        # sem o comando apagaria os lotes ja roteados.
        if not entradas_map():
            return []
        erro(f"nao achei o comando na linha 2 de {MAP}")
    return m.group(1).split()

def entradas_map():
    """Conjunto das telas (em minuscula, como o map guarda) com linha `<tela> php85;` no faseb_map.conf atual."""
    return {m.group(1) for l in ler(MAP).splitlines() for m in [re.match(r"\s+(\S+)\s+php85;", l)] if m}

def testar_nginx():
    """nginx -t num container descartavel, com os arquivos ATUAIS do disco. Devolve (ok, saida)."""
    _, img, _ = sh(["docker", "inspect", "-f", "{{.Config.Image}}", "ecidade_proxy"])
    _, net, _ = sh(["docker", "inspect", "-f", "{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}", "ecidade_proxy"])
    # mesma imagem e mesma rede do proxy: o nginx -t resolve os nomes dos upstream (ecidade_php74/85) e falha
    # se nao achar; o default.conf e o faseb_map.conf montados sao os do disco, ja com a alteracao
    rc, out, err = sh(["docker", "run", "--rm", "--network", net.strip(),
                       "-v", f"{RAIZ}/{NGINX}:/etc/nginx/conf.d/default.conf:ro",
                       "-v", f"{RAIZ}/{MAP}:/etc/nginx/faseb_map.conf:ro", img.strip(), "nginx", "-t"], timeout=120)
    return rc == 0, (out + err).strip()

def aplicar(novos_conteudos, conferir):
    """Grava os arquivos, testa o nginx, recria o proxy e confere as URLs. Desfaz tudo se o teste falhar.
    novos_conteudos: {arquivo: texto novo}; conferir: [(url, runtime esperado '8.5' ou '7.4')]."""
    antigos = {p: ler(p) for p in novos_conteudos}
    for p, t in novos_conteudos.items():
        gravar(p, t)
    ok, saida = testar_nginx()
    if not ok:
        for p, t in antigos.items():
            gravar(p, t)
        print("nginx -t FALHOU num container descartavel; as alteracoes foram DESFEITAS e o proxy nao foi tocado:")
        print(saida)
        sys.exit(1)
    print("nginx -t ok (container descartavel). Recriando o proxy...")
    rc, out, err = sh(["docker", "compose", "-f", "docker-compose.proxy.yml", "up", "-d", "--force-recreate"], timeout=300)
    if rc:
        print("FALHA ao recriar o proxy:\n" + out + err)
        sys.exit(1)
    time.sleep(3)
    falhas = 0
    print("\nConferencia (cabecalho X-Ecidade-Runtime pelo proxy :8090):")
    for url, esperado in conferir:
        rt = runtime(url)
        bate = (f"PHP-{esperado}" in rt)      # o cabecalho traz a versao, ex. "PHP-8.5..." ou "PHP-7.4..."
        falhas += not bate
        print(f"  {'ok ' if bate else 'ERRO'} /{url:50} {rt}   (esperado PHP-{esperado})")
    print("\nArquivos alterados: " + ", ".join(novos_conteudos) + " (entram no commit do lote).")
    print("Proximo: python3 scratchpad/rotear.py 8b <AREA>")
    sys.exit(1 if falhas else 0)

def modo_location(prefixos, aplicar_):
    """Acrescenta os prefixos que faltam as tres copias da lista (LISTAS), mostra antes/depois e quantas telas
    passam ao 8.5; com --aplicar, chama aplicar() conferindo o login.php (7.4) e uma tela de cada prefixo,
    com e sem /w/2/ (8.5)."""
    novos, mostrar = {}, []
    for arq, rx in LISTAS:
        t = ler(arq)
        m = rx.search(t)
        if not m and arq == NGINX:
            # nenhum location ativo ainda (base-php74): cria o bloco com os prefixos pedidos
            if ANTES_DO_BLOCO not in t:
                erro(f"sem location ativo e sem o marcador '{ANTES_DO_BLOCO.strip()}' em {arq}: criar o bloco a mao")
            i = t.index(ANTES_DO_BLOCO)
            novos[arq] = t[:i] + BLOCO_LOCATION.format(prefixos="|".join(prefixos)) + t[i:]
            mostrar.append(f"{arq}:\n  antes:  (nenhum location ativo)\n  depois: location novo com {'|'.join(prefixos)}")
            continue
        if not m:
            erro(f"nao achei a lista de prefixos em {arq}")
        atuais = m.group(2).split("|")
        faltam = [p for p in prefixos if p not in atuais]
        if not faltam:
            mostrar.append(f"{arq}: ja tem {', '.join(prefixos)}")
            continue
        nova = "|".join(atuais + faltam)
        novos[arq] = t[:m.start(2)] + nova + t[m.end(2):]
        mostrar.append(f"{arq}:\n  antes:  ...|{'|'.join(atuais[-4:])})\n  depois: ...|{'|'.join((atuais + faltam)[-4 - len(faltam):])})")
    telas = sorted(f for f in os.listdir(ECIDADE) if f.endswith(".php")
                   and re.match(rf"^(?:{'|'.join(map(re.escape, prefixos))})[0-9]*_", f, re.I))
    print("\n".join(mostrar))
    print(f"\nTelas que passam ao 8.5 pelo prefixo: {len(telas)} arquivos .php em ecidade/ "
          f"({', '.join(telas[:5])}{'...' if len(telas) > 5 else ''})")
    if not novos:
        print("Nada a mudar.")
        return
    if not aplicar_:
        print("\nNada foi alterado. Para aplicar: o mesmo comando com --aplicar")
        return
    conferir = [("login.php", "7.4")]          # a referencia na base-php74 e o 7.4
    for p in prefixos:
        uma = next((f for f in telas if re.match(rf"^{re.escape(p)}[0-9]*_", f, re.I)), None)
        if uma:
            conferir += [(uma, "8.5"), (f"w/2/{uma}", "8.5")]
    aplicar(novos, conferir)

def regenerar_map(args_gera):
    """Roda o gerador com os argumentos dados e devolve o texto novo do map, SEM deixa-lo gravado
    (o gerador escreve direto no arquivo: guardamos o antigo e o repomos)."""
    antigo = ler(MAP)
    try:
        rc, out, err = sh(["python3", "scratchpad/gera_map_faseb.py"] + args_gera, timeout=300)
        if rc:
            erro("o gera_map_faseb.py falhou:\n" + out + err)
        return ler(MAP)
    finally:
        gravar(MAP, antigo)

def comparar_map(novo_texto):
    """Entradas acrescentadas e removidas em relacao ao map atual."""
    novo = {m.group(1) for l in novo_texto.splitlines() for m in [re.match(r"\s+(\S+)\s+php85;", l)] if m}
    atual = entradas_map()
    return sorted(novo - atual), sorted(atual - novo)

def mostrar_e_aplicar_map(args_gera, extras, aplicar_, novo_texto=None):
    """Comum a map e abas: regenera o map com args_gera, mostra o que entra e RECUSA (sai 1) se alguma tela
    sairia dele. Com --aplicar, grava o map e os arquivos de `extras` ({arquivo: texto}) via aplicar().
    O map guarda os nomes em minuscula; `disco` devolve a grafia real para pedir a URL na conferencia."""
    if novo_texto is None:                   # o modo abas ja regenerou (com a lista nova no disco)
        novo_texto = regenerar_map(args_gera)
    novas, sairam = comparar_map(novo_texto)
    print(f"Comando do gerador: python3 scratchpad/gera_map_faseb.py {' '.join(args_gera)}")
    print(f"Entradas no map: {len(entradas_map())} -> {len(entradas_map()) + len(novas) - len(sairam)} "
          f"(+{len(novas)}, -{len(sairam)})")
    if novas:
        print("  novas: " + ", ".join(novas[:15]) + (" ..." if len(novas) > 15 else ""))
    if sairam:
        print("  SAIRIAM do map (voltariam ao 7.4!): " + ", ".join(sairam[:15]))
        print("RECUSADO: nenhuma tela pode sair do map. Confira o comando da linha 2 do faseb_map.conf.")
        sys.exit(1)
    if not novas:
        print("Nada a mudar (as telas ja estao no map, ou o banco nao atribui nenhuma a area).")
        return
    if not aplicar_:
        print("\nNada foi alterado. Para aplicar: o mesmo comando com --aplicar")
        return
    disco = {f.lower(): f for f in os.listdir(ECIDADE)}
    conferir = [("login.php", "7.4")] + [(disco.get(n, n), "8.5") for n in novas[:4]] + \
               [(f"w/2/{disco.get(novas[0], novas[0])}", "8.5")]
    aplicar({MAP: novo_texto, **extras}, conferir)

def modo_map(lotes, aplicar_):
    """lotes: ["area:pref,pref", ...]. Funde cada um nos argumentos atuais do gerador (linha 2 do map) e
    segue para mostrar_e_aplicar_map."""
    args_gera = comando_do_map()
    for lote in lotes:
        if ":" not in lote:
            erro(f"use <area>:<pref>[,<pref>] (ex.: assist:pre,con), nao {lote}")
        area, prefs = lote.split(":", 1)
        # se a area ja esta no comando, junta os prefixos; senao, acrescenta o argumento
        for i, a in enumerate(args_gera):
            if a.split(":", 1)[0].lower() == area.lower():
                ja = a.split(":", 1)[1].split(",")
                args_gera[i] = a.split(":", 1)[0] + ":" + ",".join(ja + [p for p in prefs.split(",") if p not in ja])
                break
        else:
            args_gera.append(lote)
    mostrar_e_aplicar_map(args_gera, {}, aplicar_)

def modo_abas(telas, aplicar_):
    """Acrescenta as telas (nome com ou sem .php; devem existir em ecidade/) ao faseb_map_abas.txt e regenera o
    map com o comando atual. Como o gerador le a lista do DISCO, o arquivo e gravado antes de regenerar e,
    sem --aplicar, reposto no fim."""
    texto = ler(ABAS)
    atuais = {l.strip().lower() for l in texto.splitlines() if l.strip() and not l.startswith("#")}
    novas = []
    for t in telas:
        t = (t if t.endswith(".php") else t + ".php").lower()
        if t not in {f.lower() for f in os.listdir(ECIDADE)}:
            erro(f"{t} nao existe em ecidade/")
        if t not in atuais:
            novas.append(t)
    if not novas:
        print("Todas ja estao em " + ABAS + ".")
        return
    args_gera = comando_do_map()
    if not args_gera:
        erro("o map ainda nao tem nenhum lote (nada foi roteado por lista): as abas entram junto com um lote -- "
             "rode antes `rotear.py map <area>:<pref>`")
    novo_abas = texto.rstrip("\n") + "\n" + "\n".join(novas) + "\n"
    # O gerador le a lista do DISCO: grava a nova so para regenerar o map e devolve a original LOGO EM SEGUIDA,
    # aconteca o que acontecer. Quem grava de verdade e o aplicar(), que assim guarda a lista ORIGINAL para
    # desfazer se o nginx -t falhar. (Antes a lista era devolvida so sem --aplicar, e com --aplicar o aplicar()
    # guardava a lista ja alterada como "antiga" -- ver scratchpad/testes/test_rotear_abas.py.)
    gravar(ABAS, novo_abas)
    try:
        novo_texto = regenerar_map(args_gera)
    finally:
        gravar(ABAS, texto)
    mostrar_e_aplicar_map(args_gera, {ABAS: novo_abas}, aplicar_, novo_texto)

def modo_8b(areas, todas):
    """Abas e redirecionamentos que voltam ao 7.4 (passo 8b), sem alterar nada."""
    if todas:
        # areas ja concluidas: a tupla JA = ("TRIBUT", ...) do dimensiona.py (prefixos dos nomes de area)
        m = re.search(r"JA = \(([^)]*)\)", ler("scratchpad/dimensiona.py"))
        areas = [a.strip(' "\'') for a in m.group(1).split(",") if a.strip()] + areas
    # sessao autenticada mais recente do 7.4 (a que tem DB_modulo); sess_?* exclui o arquivo "sess_" vazio
    _, out, _ = sh(["docker", "exec", "-i", "ecidade_php74", "sh", "-c",
                    "ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_?*) | head -1"])
    sid = out.strip().rsplit("sess_", 1)[-1]
    if len(sid) != 40:
        erro("nenhuma sessao autenticada. Entre em http://localhost:8090 (dbseller/dbseller) e rode de novo.")
    saida = os.path.join(ECIDADE, "tmp", "rotear_8b.tsv")
    print(f"Levantamento do 8b nas areas {','.join(areas)} (abre cada tela de menu no 8.5; pode levar minutos)...")
    rc, out, err = sh(["python3", "scratchpad/redirecionamentos.py", sid, saida, ",".join(areas)], timeout=6 * 3600)
    print("\n".join(l for l in out.splitlines() if not l.strip().startswith("...")))
    # cada linha do TSV (redirecionamentos.py): classe (NO_7.4...), tipo, tela de origem, destino, areas
    linhas = [l.split("\t") for l in open(saida, encoding="latin-1").read().splitlines() if l.strip()]
    # corpo.php (voltar ao inicio) e db_erros.php (pagina de erro) nao sao formulario nem lacuna
    no56 = [l for l in linhas if l[0] == "NO_7.4" and not re.search(r"^(corpo|db_erros)\.php", l[3])]
    if not no56:
        print("\nOK: nenhuma aba ou redirecionamento das telas no 8.5 manda o usuario ao 7.4.")
        sys.exit(0)
    print(f"\n{len(no56)} destino(s) ainda no 7.4 (tipo, tela de origem -> destino):")
    for l in no56:
        print(f"  {l[1]:12} {l[2]} -> {l[3]}")
    destinos = sorted({re.split(r"[?#]", l[3])[0] for l in no56})
    print("\nPortar o universo desses destinos (TELAS=... enumera.py, passos 4 a 7) e depois rotear:\n"
          f"  python3 scratchpad/rotear.py abas {' '.join(d.replace('.php', '') for d in destinos)}\n"
          "Pasta (dbforms/...) e destino inexistente nao sao lacuna (guia, passo 8b).")
    sys.exit(1)

def main():
    """Argumentos, conferencia de que proxy e banco estao no ar, e despacho para o modo pedido."""
    ap = argparse.ArgumentParser(description="Passos 8 e 8b em um comando. Ver o docstring do arquivo.")
    ap.add_argument("modo", choices=["location", "map", "abas", "8b"])
    ap.add_argument("itens", nargs="+", help="prefixos (location), area:prefixos (map), telas (abas) ou AREA (8b)")
    ap.add_argument("--aplicar", action="store_true", help="grava, testa, recria o proxy e confere")
    ap.add_argument("--todas", action="store_true", help="8b: incluir as areas ja concluidas")
    args = ap.parse_args()
    _, ps, _ = sh(["docker", "ps", "--format", "{{.Names}}"])
    if "ecidade_proxy" not in ps.split() or "ecidade_database" not in ps.split():
        erro("o proxy ou o banco esta parado. Religue (guia, 'Antes de comecar').")
    if args.modo == "location":
        modo_location([p.lower() for p in args.itens], args.aplicar)
    elif args.modo == "map":
        modo_map(args.itens, args.aplicar)
    elif args.modo == "abas":
        modo_abas(args.itens, args.aplicar)
    else:
        modo_8b([a.upper() for a in args.itens], args.todas)

if __name__ == "__main__":
    main()
