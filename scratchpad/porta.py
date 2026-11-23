#!/usr/bin/env python3
"""Passo 4 da receita: aplica as transformacoes MECANICAS em nivel de byte.

Usa a MESMA deteccao do enumera.py -- em especial a de parse_str, que conta
virgulas no nivel superior. Um regex [^,()] nao enxerga chamada aninhada, e foi
essa divergencia entre deteccao e transformacao que deixou duas telas do `jur`
fatais depois do porte.

SUBSTITUIDO pelo Rector (scratchpad/rector-curado.php + rector-rules/, hoje via
rector_lote.py) a partir do `iss`. Fica como referencia e para comparar resultados.

RECUSA-SE a rodar quando encontra caso que exige decisao humana:
  - split() com separador que tenha metacaractere de regex (explode() ali
    devolve a string inteira sem separar -- dado errado em silencio), ou com
    1o argumento que nao e literal
  (Correcao: o texto antigo dizia que tambem recusava arquivo com mais de uma
  classe ou com chamada explicita ao nome antigo. Nao recusa mais: multi-classe
  e tratado por construtores_fix(), e a checagem de chamada explicita ficou como
  um laco vazio -- ver abaixo.)
Categorias que exigem analise caso a caso (each, ereg, offsets, =& new) sao
apenas RELATADAS, nunca transformadas.

Como faz: le tmp/<prefixo>_alvos.txt (gerado pelo enumera.py); confere as barreiras
em TODOS os alvos antes de escrever qualquer um; depois, arquivo por arquivo, em bytes:
split( -> explode(, parse_str de 1 argumento ganha `, $__qs); extract($__qs);`,
construtor PHP 4 -> __construct (e as chamadas ao nome antigo), e a guarda
`($this->X === 0 || $this->X === 0.0 || $this->X == "<lit>")` nas comparacoes de
propriedade inteira com literal nao numerico. So regrava o arquivo se mudou.

Uso (da raiz do repo):  python3 scratchpad/porta.py <prefixo>
Entradas: ecidade/tmp/<prefixo>_alvos.txt e os arquivos listados nele.
Saida: ALTERA os arquivos alvo no lugar; imprime a contagem por transformacao e os
  casos a analisar a mao (ate 5 arquivos por categoria). Sai com 1 se abortar.
Usado em: passo 4 do guia ate o `iss`; hoje o passo 4 e o rector_lote.py.
"""
import os, re, sys, collections

# O projeto passou a viver em ecidade/ (reorganizacao upstream 2169884a8);
# scratchpad/ continua na raiz, ao lado dele.
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
PREF = sys.argv[1]
alvos = [l.strip() for l in open(f"tmp/{PREF}_alvos.txt") if l.strip()]
# bytes que tornam o separador do split() uma regex de verdade (nao da para trocar por explode)
META = set(b'+*?[]().|^$\\{}')

# --- barreiras: nada e escrito antes de todas passarem -----------------------
bloqueios = []
for p in alvos:
    b = open(p, "rb").read()
    # split( seguido, opcionalmente, de um literal entre aspas duplas ou simples (com
    # escapes); grupo 1 vazio = 1o argumento nao literal
    for m in re.finditer(rb'(?<![A-Za-z0-9_>$.])split\s*\(\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')?', b):
        if m.group(1) is None:
            bloqueios.append((p, "split() com 1o argumento nao literal")); continue
        if set(m.group(1)[1:-1]) & META:
            bloqueios.append((p, f"split() com separador REGEX {m.group(1)!r} -> use preg_split"))
    # arquivo multi-classe deixou de ser bloqueio: construtores_fix() renomeia
    # dentro do bloco de CADA classe, em vez de assumir uma classe por arquivo.
for outros in (f for f in os.listdir(".") if f.endswith(".php") and os.path.isfile(f)):
    pass   # checagem de chamada explicita ao nome antigo fica no enumera/manual
    # (laco morto: percorre a raiz e nao faz nada)

if bloqueios:
    print("  ABORTADO -- casos que exigem decisao humana:")
    for p, m in bloqueios[:20]: print(f"    {p}: {m}")
    sys.exit(1)

def parse_str_fix(b):
    """Acrescenta o 2o argumento onde nao ha virgula no nivel superior.
    So quando a chamada e um comando sozinho (fecha e vem `;`): ai `parse_str(x);` vira
    `parse_str(x, $__qs); extract($__qs);`, que cria as variaveis no escopo como o 5.6.
    Chamada usada como expressao fica intocada. Devolve (bytes, quantas trocou)."""
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
    A checagem por arquivo inteiro mascarava classes vizinhas (8a lacuna).
    Devolve [(nome, inicio, fim)] em bytes; o "corpo" vai de `class X` ate o proximo `class`.
    Diferente do enumera.py, NAO pula arquivo com namespace (15a lacuna)."""
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
        # `Nome::Nome(` com o mesmo nome dos dois lados (\1), para cada classe renomeada
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
    """True se a posicao cai dentro de comentario de linha ou de string literal.
    Heuristica so na linha: `//`, `/*` ou `#` antes da posicao, ou numero impar de aspas
    nao escapadas antes dela."""
    pre = linha[:col]
    if b'//' in pre or b'/*' in pre or pre.lstrip()[:1] == b'#': return True
    return ((pre.count(b'"') - pre.count(b'\\"')) % 2 == 1
            or (pre.count(b"'") - pre.count(b"\\'")) % 2 == 1)

cnt = collections.Counter()
avisos = collections.defaultdict(list)
# so relatadas (exigem analise caso a caso). O regex de offset {} aqui e o ANTIGO,
# mais estreito que o do enumera.py (nao cobre $v->p{..}).
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
