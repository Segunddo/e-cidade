#!/usr/bin/env python3
"""Quais prefixos uma area precisa migrar, e se cada um vai por `location` ou por `map`.

Uso (da raiz do repo):  python3 scratchpad/prefixos_area.py <AREA>
  <AREA> e o inicio do nome em configuracoes.atendcadarea, sem o "DB:" (ASSIST, CIDAD, GESTOR, INTEGRA...).

Para cada prefixo das telas de menu da area: quantas existem em disco, quantas o proxy ja manda
ao 8.5 (pelo `location` do nginx.conf ou pelo faseb_map.conf), quantas faltam, e quais OUTRAS
areas ainda tem telas desse prefixo no 5.6. Sem outra area pendente -> o prefixo inteiro vai pelo
`location`; com outra area pendente -> so as telas desta area, pelo `map`. A coluna "em disco" conta
os .php do prefixo inteiro: se ela e muito maior que "telas", rotear pelo `location` obriga a portar
o prefixo todo -- compare o custo com `enumera.py <pref>` antes (ver docs/migrar-um-modulo.md).
Telas que o menu cita mas nao existem em disco (fantasmas) nao entram na contagem.
"""
import collections, os, re, subprocess, sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if len(sys.argv) != 2:
    sys.exit(__doc__)
AREA = sys.argv[1].upper()

SQL = ("SELECT DISTINCT lower(split_part(di.funcao,'?',1)), upper(replace(a.at25_descr,'DB:','')) "
       "FROM configuracoes.atendcadareamod am "
       "JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea "
       "JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item "
       "JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item "
       "JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho "
       "WHERE di.funcao ~* '\\.php'")
out = subprocess.run(["docker", "exec", "-i", "ecidade_database", "psql", "-U", "postgres", "-d", "ecidade",
                      "-At", "-F", "\t", "-c", SQL], capture_output=True, stdin=subprocess.DEVNULL)
if out.returncode:
    sys.exit("psql falhou -- o container ecidade_database esta no ar?\n" + out.stderr.decode("latin-1"))

disco = {f.lower() for f in os.listdir("ecidade")}
# o mesmo criterio do proxy: location por prefixo + map por nome exato
loc = re.search(r'location ~\* \^\(\?:/w/\[0-9\]\+\)\?/\(\?:\(\?:([^)]+)',
                open("docker/proxy/nginx.conf").read()).group(1)
LOC = re.compile(rf'^(?:{loc})[0-9]*_', re.I)
MAP = {m.group(1) for l in open("docker/proxy/faseb_map.conf") for m in [re.match(r'\s+(\S+)\s+php85;', l)] if m}
no85 = lambda t: bool(LOC.match(t)) or t in MAP
pref = lambda t: (re.match(r'^([a-z]+?)(?:[0-9]*_|_)', t) or re.match(r'^([a-z]+)', t)).group(1)

areas = collections.defaultdict(set)
for l in out.stdout.decode("latin-1").splitlines():
    t, a = l.split("\t")
    areas[t].add(a)

tab = collections.defaultdict(lambda: [0, 0, 0, set()])   # telas, no 8.5, faltam, outras areas pendentes
for t, a in areas.items():
    if t in disco and any(x.startswith(AREA) for x in a):
        r = tab[pref(t)]
        r[0] += 1
        r[1 if no85(t) else 2] += 1
for t, a in areas.items():
    if t in disco and not no85(t) and pref(t) in tab:
        tab[pref(t)][3].update(x for x in a if not x.startswith(AREA))
if not tab:
    sys.exit(f"nenhuma tela de menu para a area '{AREA}' -- confira o nome (ASSIST, CIDAD, GESTOR, INTEGRA...)")

emdisco = lambda p: sum(1 for f in disco if f.endswith(".php") and re.match(rf'^{p}[0-9]*_', f))
print(f"{'prefixo':8} {'telas':>5} {'no 8.5':>6} {'faltam':>6} {'em disco':>8}  outras areas com telas desse prefixo ainda no 5.6")
for p, (n, ok, f, outras) in sorted(tab.items(), key=lambda x: (-x[1][2], x[0])):
    print(f"{p:8} {n:5} {ok:6} {f:6} {emdisco(p):8}  {', '.join(sorted(outras)) or '-'}")
print(f"\nfaltam {sum(r[2] for r in tab.values())} telas")
