#!/usr/bin/env python3
"""Metrica de RESIDUO por modulo, para escolher o proximo a portar.

Residuo = dependencias que ainda PRECISAM de porte e que NAO sao exclusivas do
modulo -- ou seja, arquivos compartilhados com modulos ainda nao portados, que
o porte vai arrastar junto. E o que impede a fatia vertical de ser cortada limpa.

Classificacao de cada dependencia, nesta ordem:
  ja pago    -> nucleo, ou arquivo ja tocado por um commit "Porta ..."  (custo 0)
  exclusiva  -> so este modulo a alcanca                                (custo proprio)
  RESIDUO    -> compartilhada com modulo(s) nao portado(s)              (contamina)

Le tudo em BYTES: 64% da base e LATIN-1 e o grep a pula em silencio.
Enumera pelas frentes da receita (CLAUDE.md): includes transitivos, classes por
autoload (`new cl_X` -> classes/db_X_classe.php) e nomes de arquivo citados em
strings -- estes UM NIVEL a partir dos scripts do modulo, porque e o JavaScript
que os abre por HTTP; seguir strings transitivamente pela base inteira infla o
fecho sem corresponder a nenhum caminho de execucao.

Uso:  python3 scratchpad/residuo.py arr div jur
"""
import os, re, sys, subprocess, collections

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUCLEO = {
 "libs/db_stdlib.php","libs/db_conecta.php","libs/db_sessoes.php","libs/db_usuariosonline.php",
 "libs/db_acessa.php","libs/db_calcula.php","libs/db_libpessoal.php","libs/db_utils.php",
 "libs/db_sql.php","libs/db_app.utils.php","libs/JSON.php","dbforms/db_funcoes.php",
 "dbforms/db_classesgenericas.php","std/DBString.php","std/db_stdClass.php",
 "config/ecidade_config.php","fpdf151/fpdf.php","fpdf151/pdf.php",
 "model/pessoal/std/DBPessoal.model.php","model/configuracao/mensagem/DBMensagem.model.php",
 "classes/db_cgm_classe.php",
}
if os.path.isdir("libs/exceptions"):
    NUCLEO |= {f"libs/exceptions/{x}" for x in os.listdir("libs/exceptions")}

PORTADO = {l.strip() for l in subprocess.run(
    ["git","log","--name-only","--format=","--grep=^Porta "],
    capture_output=True, text=True).stdout.splitlines() if l.strip().endswith(".php")}
PAGO = NUCLEO | PORTADO

RX_INC = re.compile(rb'(?:include|require)(?:_once)?\s*\(?\s*(?:modification\s*\(\s*)?["\']([^"\']+\.php)["\']')
RX_NEW = re.compile(rb'new\s+(cl_\w+)')
RX_STR = re.compile(rb'["\']([A-Za-z0-9_]+\.(?:RPC\.)?php)["\']')

_c = {}
def diretas(path):
    if path in _c: return _c[path]
    out = set()
    try: b = open(path, "rb").read()
    except OSError: _c[path] = out; return out
    for m in RX_INC.finditer(b):
        p = m.group(1).decode("latin1").lstrip("./")
        if os.path.isfile(p): out.add(p)
    for m in RX_NEW.finditer(b):
        p = f"classes/db_{m.group(1).decode('latin1')[3:]}_classe.php"
        if os.path.isfile(p): out.add(p)
    _c[path] = out
    return out

def citados(path):
    try: b = open(path, "rb").read()
    except OSError: return set()
    return {p for p in (m.group(1).decode("latin1") for m in RX_STR.finditer(b))
            if os.path.isfile(p) and p != os.path.basename(path)}

def fecho(seeds):
    v, fila = set(), list(seeds)
    while fila:
        for d in diretas(fila.pop()):
            if d not in v: v.add(d); fila.append(d)
    return v

RX_MOD = re.compile(r'^([A-Za-z]+)[0-9]*_.*\.php$')
raiz = [f for f in os.listdir(".") if os.path.isfile(f) and RX_MOD.match(f)]

def universo(pref):
    rx = re.compile(r'^' + pref + r'[0-9]*_', re.IGNORECASE)
    s = sorted(f for f in raiz if rx.match(f))
    js = set().union(*[citados(f) for f in s]) if s else set()
    js -= set(s)
    return s, (fecho(s + sorted(js)) | js) - set(s)

alcanca = collections.defaultdict(set)
for f in raiz:
    p = RX_MOD.match(f).group(1).lower()
    for d in fecho([f]) | citados(f):
        alcanca[d].add(p)

print(f"{'mod':>5} {'telas':>6} {'deps':>5} {'ja pago':>8} {'exclus':>7} {'RESIDUO':>8} {'a portar':>9}   arrasta")
print("-" * 104)
for pref in sys.argv[1:]:
    s, deps = universo(pref)
    pago = exc = 0
    res, arrasta = [], collections.Counter()
    for d in sorted(deps):
        outros = {m for m in alcanca[d] if not m.startswith(pref)}
        if d in PAGO:      pago += 1
        elif not outros:   exc  += 1
        else:
            res.append(d)
            for m in outros: arrasta[m] += 1
    nao_pagos = [f for f in s if f not in PAGO]
    print(f"{pref:>5} {len(s):>6} {len(deps):>5} {pago:>8} {exc:>7} {len(res):>8} "
          f"{len(nao_pagos)+exc+len(res):>9}   "
          + "  ".join(f"{m}:{n}" for m, n in arrasta.most_common(5)))
