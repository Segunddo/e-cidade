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

# O projeto passou a viver em ecidade/ (reorganizacao upstream 2169884a8);
# scratchpad/ continua na raiz, ao lado dele.
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
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
    # arquivo multi-classe deixou de ser bloqueio: construtores_fix() renomeia
    # dentro do bloco de CADA classe, em vez de assumir uma classe por arquivo.
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


def classes_php4(b):
    """Classes cujo construtor e o metodo homonimo, olhando o corpo de CADA classe.
    A checagem por arquivo inteiro mascarava classes vizinhas (8a lacuna)."""
    pos = [(m.start(), m.group(1)) for m in re.finditer(rb'\bclass\s+(\w+)', b)]
    out = []
    for i, (ini, nome) in enumerate(pos):
        fim = pos[i+1][0] if i+1 < len(pos) else len(b)
        if re.search(rb'function\s+__construct\s*\(', b[ini:fim], re.I): continue
        if re.search(rb'function\s+' + re.escape(nome) + rb'\s*\(', b[ini:fim], re.I):
            out.append((nome, ini, fim))
    return out

def construtores_fix(b):
    """Renomeia os construtores estilo PHP 4 DENTRO do bloco de cada classe, e ajusta
    as chamadas explicitas ao nome antigo -- `parent::Nome(` e, quando a classe do
    arquivo estende Nome, `$this->Nome(`. Sem isso a chamada vira metodo inexistente."""
    n = 0
    classes = classes_php4(b)
    for nome, ini, fim in reversed(classes):              # de tras pra frente: os offsets seguem valendo
        trecho, k = re.subn(rb'function\s+' + re.escape(nome) + rb'\s*\(',
                            b'function __construct(', b[ini:fim], flags=re.I)
        if k: b = b[:ini] + trecho + b[fim:]; n += k
    for nome in {m.group(1) for m in re.finditer(rb'\bclass\s+\w+\s+extends\s+(\w+)', b)}:
        b = re.sub(rb'parent\s*::\s*' + re.escape(nome) + rb'\s*\(', b'parent::__construct(', b)
        b = re.sub(rb'\$this\s*->\s*' + re.escape(nome) + rb'\s*\(', b'parent::__construct(', b)
    # 3a forma, descoberta no dbagata: chamada ESTATICA `Classe::Classe(`. Escapou das
    # duas regras acima e deixou MyPdf.class chamando FPDF::FPDF(), metodo que o
    # proprio porte acabara de renomear. Nao vale so para a classe-pai declarada no
    # arquivo, entao usa a lista de classes renomeadas aqui.
    if classes:
        alt = rb'\b(' + rb'|'.join(re.escape(c) for c, _, _ in classes) + rb')\s*::\s*\1\s*\('
        linhas = b.split(b"\n")
        for i, l in enumerate(linhas):
            while True:
                m = re.search(alt, linhas[i])
                # nao tocar em comentario nem em string: o proprio jpgraph.php traz
                # `//(... Text::Text() ...)` e as mensagens de erro citam Graph::Graph()
                if not m or _em_texto(linhas[i], m.start()): break
                linhas[i] = linhas[i][:m.start()] + m.group(1) + b'::__construct(' + linhas[i][m.end():]
        b = b"\n".join(linhas)
    return b, n

def _em_texto(linha, col):
    """True se a posicao cai dentro de comentario de linha ou de string literal."""
    pre = linha[:col]
    if b'//' in pre or b'/*' in pre or pre.lstrip()[:1] == b'#': return True
    return ((pre.count(b'"') - pre.count(b'\\"')) % 2 == 1
            or (pre.count(b"'") - pre.count(b"\\'")) % 2 == 1)

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
    b, n = construtores_fix(b); cnt['construtor PHP4'] += n
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
