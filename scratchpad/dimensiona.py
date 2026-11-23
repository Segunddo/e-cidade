#!/usr/bin/env python3
"""Dimensiona as areas ainda nao migradas, a partir do BANCO e do estado atual do git.

Por area: telas de menu (atendcadarea -> ... -> db_itensmenu) que existem em disco e
que o 8.5 ainda NAO serve (nem pelo `location` do nginx nem pelo `map`); depois o
fecho das frentes do enumera.py (hoje nove; o texto original dizia sete) a partir delas
(TELAS=...), contando o que os commits `Porta ...` ja pagaram.

Como faz: uma consulta ao banco (container ecidade_database) lista (area, modulo, tela)
de todo o menu; cada tela e classificada como fantasma (nao existe em disco), ja no 8.5
(casa o LOC ou esta no MAP) ou faltando. Para cada area nao concluida (fora de JA) com
telas faltando, roda o enumera.py com TELAS=<as que faltam> e le os numeros da saida dele.

Uso (da raiz do repo):  python3 scratchpad/dimensiona.py
Entradas: o banco, docker/proxy/faseb_map.conf, a copia do regex do `location` (LOC) e a
  tupla JA -- as duas ultimas mantidas a mao (o rotear.py atualiza LOC ao rotear).
Saida: tabela por area + a uniao (a ordem pre-paga o residuo da seguinte). Como efeito
  colateral, o enumera.py grava ecidade/tmp/dim_<area>_universo.txt e _alvos.txt.
Usado em: parte B do fluxo de uma area no guia (dimensionar e dividir em lotes).
"""
import os, re, subprocess, sys, collections

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ECI = os.path.join(RAIZ, "ecidade")
# inicio do nome (sem "DB:") das areas concluidas; casado com startswith, entao "SA"
# pega SAUDE -- e qualquer outra area que comece por SA.
JA = ()  # areas concluidas NA BASE-PHP74 (nenhuma ainda; a base-php84 tinha 7, que nao valem aqui)

# o mesmo regex do `location` do nginx (docker/proxy/nginx.conf) -- COPIA: ao acrescentar
# prefixo ao nginx, acrescentar aqui tambem (o rotear.py faz isso)
# base-php74: nada vai ao 8.5 ainda. "nenhum_prefixo_no_85" e um marcador que nao casa com nenhuma tela;
# o rotear.py acrescenta os prefixos depois dele (ex.: nenhum_prefixo_no_85|soc|hab) ao rotear um lote.
LOC = re.compile(r"^(?:nenhum_prefixo_no_85)[0-9]*_", re.I)
# telas do `map` (faseb_map.conf): primeira palavra de cada linha que nao e comentario
MAP = {l.split()[0] for l in open(os.path.join(RAIZ, "docker/proxy/faseb_map.conf"))
       if l.strip() and not l.startswith("#")}

# (area, modulo, tela em minusculas sem o ?parametro) de cada item de menu que aponta
# para uma tela de prefixo (letras + digitos opcionais + _). Caminho no banco:
# atendcadarea -> atendcadareamod -> db_modulos -> db_menu -> db_itensmenu.funcao
SQL = ("SELECT DISTINCT replace(a.at25_descr,'DB:',''), m.nome_modulo, lower(split_part(di.funcao,'?',1)) "
       "FROM configuracoes.atendcadareamod am "
       "JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea "
       "JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item "
       "JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item "
       "JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho "
       "WHERE split_part(di.funcao,'?',1) ~ '^[A-Za-z]+[0-9]*_.*\\.php$'")
out = subprocess.run(["docker", "exec", "-e", "PGCLIENTENCODING=UTF8", "ecidade_database", "psql", "-U", "postgres",
                      "-d", "ecidade", "-tA", "-F", "\t", "-c", SQL], capture_output=True, check=True).stdout.decode()

# nome em minusculas -> grafia real no disco (o menu e o disco nem sempre concordam)
disco = {f.lower(): f for f in os.listdir(ECI) if os.path.isfile(os.path.join(ECI, f))}
areas = collections.defaultdict(lambda: {"mod": set(), "menu": set(), "falta": set(), "fantasma": set()})
for l in out.splitlines():
    area, mod, tela = l.split("\t")
    a = areas[area]
    a["mod"].add(mod); a["menu"].add(tela)
    if tela not in disco: a["fantasma"].add(tela)
    elif not (LOC.match(tela) or tela in MAP): a["falta"].add(disco[tela])

def enumera(nome, telas):
    """Roda o enumera.py com TELAS=<telas> e devolve (universo, ja pago, a alterar, alvos),
    os tres numeros tirados do texto que ele imprime e os alvos do arquivo que ele grava."""
    env = dict(os.environ, TELAS=",".join(sorted(telas)))
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scratchpad/enumera.py"), nome], env=env,
                       capture_output=True, text=True, check=True).stdout
    uni = int(re.search(r"universo.*?:\s*(\d+)", r).group(1))
    pago = int(re.search(r"ja pago:\s*(\d+)", r).group(1))
    alt = int(re.search(r"A ALTERAR:\s*(\d+)", r).group(1))
    alvos = set(open(os.path.join(ECI, f"tmp/{nome}_alvos.txt")).read().split())
    return uni, pago, alt, alvos

print(f"{'Area':22s} {'Mod':>3s} {'Menu':>5s} {'Faltam':>6s} {'Fant.':>5s} {'Univ.':>6s} {'Pago':>5s} {'A alterar':>9s}")
uniao, linhas = set(), []
# areas com mais telas faltando primeiro
for area in sorted(areas, key=lambda x: -len(areas[x]["falta"])):
    a = areas[area]
    if area.upper().startswith(JA) or not a["falta"]: continue
    nome = "dim_" + re.sub(r"\W+", "_", area.lower())
    uni, pago, alt, alvos = enumera(nome, a["falta"])
    uniao |= alvos
    print(f"{area[:22]:22s} {len(a['mod']):3d} {len(a['menu']):5d} {len(a['falta']):6d} {len(a['fantasma']):5d} {uni:6d} {pago:5d} {alt:9d}")
print(f"\nUniao dos 'a alterar' de todas as areas: {len(uniao)}")
