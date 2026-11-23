#!/usr/bin/env python3
"""Classes que a regressao do grupo testa x as que o universo do enumera.py alcanca (passo 6b).

Uso (da raiz do repo, depois de `enumera.py <p>` para cada prefixo):
    python3 scratchpad/e1_cobertura.py <pasta com os <p>_universo.txt> [lista de filhas LSP confirmadas]

- R(p): copia fiel de _classes_das_telas() (origin/regressao-php74:regressao/php/bateria.py:138):
        `classes/db_*_classe.php` citadas LITERALMENTE no texto das telas ^p[0-9]*_*.php.
- M(p): R(p) + as classes que a tela cria por `new cl_x` ou `getDao('x')` (a correcao barata proposta).
- U(p): as entradas `classes/` do universo do enumera.py (o que o passo 6b usa).
- exposta: a classe tem um campo com valor inicial numerico (`$x = 0;`) que o atualizacampos() compara
  com "" (`$this->x == ""`): no PHP 8, 0 == "" e falso e o valor digitado e ignorado. Calibrado: acusa
  91% das classes db_*; a regressao mediu 94% divergindo por essa causa.
"""
import os, re, sys

UNIV = sys.argv[1]
LSP = set(open(sys.argv[2]).read().split()) if len(sys.argv) > 2 else set()
E = "ecidade"
EXIST = {f.lower(): f for f in os.listdir(os.path.join(E, "classes"))}
PAD = re.compile(rb"classes/(db_[A-Za-z0-9_]+_classe\.php)")
PADN = re.compile(rb"new\s+cl_(\w+)|getDao\s*\(\s*['\"](\w+)", re.I)

def regressao(telas, melhor=False):
    ach = set()
    for t in telas:
        b = open(os.path.join(E, t), "rb").read()
        ach.update(m.decode() for m in PAD.findall(b))
        if melhor:
            ach.update(f"db_{(a or b_).decode().lower()}_classe.php" for a, b_ in PADN.findall(b))
    return {"classes/" + EXIST[c.lower()] for c in ach if c.lower() in EXIST}

_exp = {}
def exposta(c):
    if c not in _exp:
        b = open(os.path.join(E, c), "rb").read()
        num = {m.group(1) for m in re.finditer(rb"(?:var|public|protected)\s+\$(\w+)\s*=\s*-?[0-9][0-9.]*\s*;", b)}
        cmp_ = {m.group(1) for m in re.finditer(rb"\$this->(\w+)\s*==\s*(?:\"\"|'')", b)}
        _exp[c] = bool(num & cmp_)
    return _exp[c]

R, M, U, UL = set(), set(), set(), set()
for a in sorted(os.listdir(UNIV)):
    if not a.endswith("_universo.txt"): continue
    p = a[:-len("_universo.txt")]
    rx = re.compile(rf"^{p}[0-9]*_", re.I)
    telas = [f for f in os.listdir(E) if f.endswith(".php") and rx.match(f) and os.path.isfile(os.path.join(E, f))]
    univ = {l.strip() for l in open(os.path.join(UNIV, a), encoding="latin-1") if l.strip()}
    R |= regressao(telas); M |= regressao(telas, True)
    U |= {c for c in univ if c.startswith("classes/") and c.endswith(".php")}
    UL |= univ & LSP
n = lambda s: f"{len(s)} ({sum(map(exposta, s))} expostas ao 0 == '')"
print(f"prefixos: {sum(1 for a in os.listdir(UNIV) if a.endswith('_universo.txt'))}")
print(f"regressao hoje testa ......... {len(R)}")
print(f"com new cl_/getDao ........... {len(M)}")
print(f"universo alcanca ............. {len(U)}")
print(f"so o universo (hoje) ......... {n(U - R)}")
print(f"so o universo (com correcao) . {n(U - M)}")
print(f"so a regressao ............... {len(R - U)}")
if LSP:
    print(f"filhas LSP confirmadas: {len(LSP)}; em algum universo: {len(UL)}; fora de todos: {len(LSP - UL)}")
    for f in sorted(LSP - UL): print("   fora:", f)
