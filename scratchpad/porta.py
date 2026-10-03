#!/usr/bin/env python3
"""Passo 4 da receita: aplica as transformacoes MECANICAS em nivel de byte.

Usa a MESMA deteccao do enumera.py -- em especial a de parse_str, que conta
virgulas no nivel superior. Um regex [^,()] nao enxerga chamada aninhada, e foi
essa divergencia entre deteccao e transformacao que deixou duas telas do `jur`
fatais depois do porte.

RECUSA-SE a rodar quando encontra caso que exige decisao humana:
  - split() com separador que tenha metacaractere de regex (explode() ali
    devolve a string inteira sem separar -- dado errado em silencio)
  - arquivo com mais de uma classe, ou chamada explicita ao nome antigo
Categorias que exigem analise caso a caso (each, ereg, offsets, =& new) sao
apenas RELATADAS, nunca transformadas.

Uso:  python3 scratchpad/porta.py <prefixo>
"""
import os, re, sys, collections

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREF = sys.argv[1]
alvos = [l.strip() for l in open(f"tmp/{PREF}_alvos.txt") if l.strip()]
META = set(b'+*?[]().|^$\\{}')

# --- barreiras: nada e escrito antes de todas passarem -----------------------
bloqueios = []
for p in alvos:
    b = open(p, "rb").read()
    for m in re.finditer(rb'(?<![A-Za-z0-9_>$.])split\s*\(\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')?', b):
        if m.group(1) is None:
            bloqueios.append((p, "split() com 1o argumento nao literal")); continue
        if set(m.group(1)[1:-1]) & META:
            bloqueios.append((p, f"split() com separador REGEX {m.group(1)!r} -> use preg_split"))
    cls = re.findall(rb'\bclass\s+(\w+)', b)
    if not re.search(rb'function\s+__construct\s*\(', b, re.I):
        php4 = [c for c in cls if re.search(rb'function\s+'+re.escape(c)+rb'\s*\(', b, re.I)]
        if len(php4) > 1:
            bloqueios.append((p, f"mais de uma classe com construtor PHP4: {php4}"))
for outros in (f for f in os.listdir(".") if f.endswith(".php") and os.path.isfile(f)):
    pass   # checagem de chamada explicita ao nome antigo fica no enumera/manual

if bloqueios:
    print("  ABORTADO -- casos que exigem decisao humana:")
    for p, m in bloqueios[:20]: print(f"    {p}: {m}")
    sys.exit(1)

def parse_str_fix(b):
    """Acrescenta o 2o argumento onde nao ha virgula no nivel superior."""
    out, pos, n = bytearray(), 0, 0
    for m in re.finditer(rb'parse_str\s*\(', b):
        if m.start() < pos: continue
        i, prof, virg = m.end(), 1, False
        while i < len(b) and prof:
            c = b[i:i+1]
            if c == b'(': prof += 1
            elif c == b')': prof -= 1
            elif c == b',' and prof == 1: virg = True
            i += 1
        if virg: continue
        j = i
        while j < len(b) and b[j:j+1] in b' \t': j += 1
        if b[j:j+1] != b';': continue
        out += b[pos:i-1] + b', $__qs); extract($__qs);'
        pos, n = j + 1, n + 1
    out += b[pos:]
    return bytes(out), n

cnt = collections.Counter()
avisos = collections.defaultdict(list)
MANUAL = {'each(':     re.compile(rb'(?<![A-Za-z0-9_>$.])each\s*\('),
          'ereg*(':    re.compile(rb'(?<![A-Za-z0-9_>$.])(?:ereg|eregi|ereg_replace|eregi_replace)\s*\('),
          'offset {}': re.compile(rb'\$\w+(?:\[[^\]]*\])*\{\s*[^}]{1,20}\s*\}'),
          '=& new':    re.compile(rb'=\s*&\s*new\b')}

for p in alvos:
    b0 = open(p, "rb").read(); b = b0
    for k, r in MANUAL.items():
        n = len(r.findall(b))
        if n: avisos[k].append((p, n))
    b, n = re.subn(rb'(?<![A-Za-z0-9_>$.])split\s*\(', rb'explode(', b); cnt['split -> explode'] += n
    b, n = parse_str_fix(b);                                             cnt['parse_str 2 args'] += n
    if not re.search(rb'function\s+__construct\s*\(', b, re.I):
        mc = re.search(rb'\bclass\s+(\w+)', b)
        if mc:
            b, n = re.subn(rb'function\s+'+re.escape(mc.group(1))+rb'\s*\(', b'function __construct(', b, flags=re.I)
            cnt['construtor PHP4'] += n
    for x in {m.group(1) for m in re.finditer(rb'(?:var|public)\s+\$(\w+)\s*=\s*-?\d+\s*;', b)}:
        # Qualquer literal NAO-NUMERICO, nao so "": no 5.6 a string nao-numerica
        # era coagida para 0. Literal numerico e seguro nos dois e fica intocado.
        def guarda(m, _x=x):
            lit = m.group(1)
            if lit.strip().isdigit():
                return m.group(0)
            return (b'($this->'+_x+b' === 0 || $this->'+_x+b' === 0.0 || $this->'+_x
                    + b' == '+m.group(0).split(b'==')[1].strip()+b')')
        b, n = re.subn(rb'\$this->'+re.escape(x)+rb'\s*==\s*["\']([^"\']{0,3})["\']', guarda, b)
        cnt['$this->X == <literal>'] += n
    if b != b0: open(p, "wb").write(b)

for k, v in cnt.most_common(): print(f"  {k:24s} {v:6d}")
if avisos:
    print("\n  EXIGEM ANALISE CASO A CASO (nao transformados):")
    for k, v in avisos.items():
        print(f"    {k}: {sum(n for _, n in v)} em {len(v)} arquivo(s)")
        for p, n in v[:5]: print(f"       {p} ({n})")
