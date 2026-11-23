#!/usr/bin/env python3
"""Passos 1-3 da receita de porte: enumera o universo de um modulo pelas frentes
(eram seis; hoje sao nove -- ver abaixo), faz o inventario das categorias conhecidas
e grava a lista de alvos.

Le tudo em BYTES -- 64% da base e LATIN-1 e o grep a pula em silencio.

Como faz:
  1. telas de partida: os .php da raiz de ecidade/ com o prefixo (<pref>[0-9]*_, sem
     diferenciar maiusculas) -- ou a lista de TELAS=, quando o lote nao e um prefixo;
  2. soma os .php citados em string pelas telas (abertos por JavaScript, UM nivel so);
  3. fecho transitivo pelas frentes de diretas(): include/require, `new cl_X`,
     getDao('X'), classes de model/ e std/ por autoload, e classes com namespace
     (src/app/api, via ns_fecho.refs);
  4. descarta o que ja esta pago (NUCLEO, vazio na base-php74, + commits "Porta ...") e, em cada
     arquivo restante, conta as categorias que quebram no PHP 8 (CAT, parse_str de 1
     argumento, construtor PHP 4, `$this->X == "<literal>"`); quem tem alguma vira alvo.

Uso (da raiz do repo):
  python3 scratchpad/enumera.py <prefixo>
  TELAS=a.php,b.php python3 scratchpad/enumera.py <nome-do-lote>    # lote que nao e prefixo
  TELAS=@/caminho/absoluto/lista.txt python3 scratchpad/enumera.py <nome-do-lote>   # uma tela por linha
  SEM_NS=1 ...  desliga a 9a frente (namespace), para medir o que ela acrescenta
Entradas: os arquivos de ecidade/, o `git log` (commits "Porta ...") e ns_fecho.py.
Saida: tmp/<prefixo>_universo.txt  e  tmp/<prefixo>_alvos.txt (relativos a ecidade/);
  imprime telas, tamanho do universo, quanto ja esta pago, quantos A ALTERAR e a
  contagem por categoria.
Usado em: passos 1-3 do guia (docs/migrar-um-modulo.md); tambem chamado pelo
  dimensiona.py (com TELAS=) para medir as areas.
"""
import os, re, sys, collections, subprocess

# O projeto passou a viver em ecidade/ (reorganizacao upstream 2169884a8);
# scratchpad/ continua na raiz, ao lado dele.
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
PREF = sys.argv[1]

# Arquivos do nucleo ja portados a mao: contam como pagos (nunca viram alvo).
# base-php74: VAZIO -- o nucleo desta base NAO foi portado (fpdf.php:614 e JSON.php:188 quebram no 8.5).
# A lista de 21 arquivos da base-php84: git show origin/base-php84:scratchpad/enumera.py
NUCLEO = set()
# Os commits anteriores a reorganizacao registram "classes/x.php"; os
# posteriores registrarao "ecidade/classes/x.php". Como o universo e relativo a
# ecidade/, normaliza-se o prefixo -- senao o proximo modulo veria tudo como
# nao-pago e o porta.py re-aplicaria guardas JA aplicadas.
PORTADO = {l.strip().removeprefix("ecidade/") for l in subprocess.run(
    ["git","log","--name-only","--format=","--grep=^Porta "],
    capture_output=True, text=True).stdout.splitlines() if l.strip().endswith(".php")}
PAGO = NUCLEO | PORTADO          # o que ja foi portado: entra no universo, mas nunca vira alvo

# re.I nas tres: PHP nao diferencia maiusculas em palavra-chave nem em nome de
# metodo/classe. 9a lacuna: `db_utils::getdao('atolegal')` (minusculas) -- 781
# chamadas em 244 arquivos com grafia diferente de getDao, invisiveis a frente.
# include/require[_once] com caminho literal, com ou sem parenteses e com ou sem o
# envelope modification(...) do extension/ -- captura o caminho .php.
RX_INC = re.compile(rb'(?:include|require)(?:_once)?\s*\(?\s*(?:modification\s*\(\s*)?["\']([^"\']+\.php)["\']', re.I)
# `new cl_x` -> classes/db_x_classe.php (autoload das classes de tabela).
RX_NEW = re.compile(rb'new\s+(cl_\w+)', re.I)
# 7a lacuna: db_utils::getDao('x') instancia cl_x por autoload sem citar o
# nome da classe. Achada no `fis`, em db_cadtipo_classe.php -- cujo construtor
# PHP4 inicializa $this->rotulo, e sem ele a tela morre com label() on null.
RX_DAO = re.compile(rb'''getDao\s*\(\s*['"]([A-Za-z0-9_]+)['"]''', re.I)
# nome de arquivo .php (ou .RPC.php) sem pasta dentro de string: o que o JavaScript abre.
RX_STR = re.compile(rb'["\']([A-Za-z0-9_]+\.(?:RPC\.)?php)["\']')
# 13a lacuna: classes de model/ e std/ usadas por `new Classe` ou `Classe::metodo()` sao
# carregadas pelo AUTOLOADER, sem include -- nenhuma frente as via. Achada porque o calculo
# da folha morreu em AjustePrevidencia::...; escondia 5 classes de folha com LSP e 6 each().
# `new Classe` (grupo 1) ou `Classe::` (grupo 2); o nome e procurado em MAPA_CLS.
RX_CLS = re.compile(rb'\bnew\s+([A-Za-z_]\w*)|\b([A-Za-z_]\w*)::')
# nome da classe/interface em minusculas -> arquivo de model/ ou std/ que a declara
# (o primeiro achado vence, como no autoload).
MAPA_CLS = {}
for _raiz in ("model", "std"):
    for _d, _, _fs in os.walk(_raiz):
        for _f in _fs:
            if _f.endswith(".php"):
                _p = os.path.join(_d, _f)
                for _m in re.finditer(rb'^\s*(?:abstract\s+|final\s+)?(?:class|interface)\s+(\w+)', open(_p, "rb").read(), re.M):
                    MAPA_CLS.setdefault(_m.group(1).decode().lower(), _p)

# 15a lacuna: classes COM NAMESPACE (src/, app/, api/), carregadas pelo autoload PSR-4 --
# `use ECidade\...;`, `new \ECidade\...`, e os servicos por chave de texto do bootstrap.php.
# Achada no Patrimonial: um RPC de Ouvidoria quebrou em src/Patrimonial/Protocolo/Container.php,
# que nenhum universo listava. O resolvedor vive em ns_fecho.py (tambem roda sozinho).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ns_fecho import refs as ns_refs

def classes_php4(b):
    """Classes cujo construtor e o metodo homonimo (estilo PHP 4), olhando o corpo de
    CADA classe isoladamente. Fatiar por `class X` evita dois erros do regex de arquivo
    inteiro: mascarar classes vizinhas por causa de um __construct alheio, e contar um
    METODO homonimo de outra classe como se fosse construtor."""
    # Em classe COM namespace o metodo homonimo nao e construtor desde o PHP 5.3.3 --
    # conferido no 5.6. Renomea-lo para __construct MUDARIA o 5.6 (15a lacuna:
    # src/Educacao/Escola/Censo/Identificacao/Importar.php).
    if re.search(rb'^\s*namespace\s+[\w\\]+\s*;', b, re.M): return []
    pos = [(m.start(), m.group(1)) for m in re.finditer(rb'\bclass\s+(\w+)', b)]
    out = []
    for i, (ini, nome) in enumerate(pos):
        corpo = b[ini: pos[i+1][0] if i+1 < len(pos) else len(b)]
        if re.search(rb'function\s+__construct\s*\(', corpo, re.I): continue
        if re.search(rb'function\s+' + re.escape(nome) + rb'\s*\(', corpo, re.I):
            out.append((nome, ini))
    return out

_c = {}                                                 # cache: arquivo -> dependencias diretas
def diretas(p):
    """Dependencias DIRETAS de um arquivo (relativo a ecidade/), pelas frentes de codigo:
    include/require, `new cl_*`, getDao(), classes de model/std e namespace. Devolve so
    caminhos que existem em disco. O fecho transitivo e feito por quem chama."""
    if p in _c: return _c[p]
    out = set()
    try: b = open(p, "rb").read()
    except OSError: _c[p] = out; return out
    for m in RX_INC.finditer(b):
        q = m.group(1).decode("latin1").lstrip("./")
        if os.path.isfile(q): out.add(q)
    for m in RX_NEW.finditer(b):                       # 4a lacuna: autoload
        q = f"classes/db_{m.group(1).decode('latin1')[3:]}_classe.php"
        if not os.path.isfile(q): q = q.lower()   # o nome no codigo pode vir capitalizado
        if os.path.isfile(q): out.add(q)
    for m in RX_DAO.finditer(b):                       # 7a lacuna: getDao()
        q = f"classes/db_{m.group(1).decode('latin1')}_classe.php"
        if not os.path.isfile(q): q = q.lower()   # o nome no codigo pode vir capitalizado
        if os.path.isfile(q): out.add(q)
    for m in RX_CLS.finditer(b):                       # 13a lacuna: autoload de model/ e std/
        q = MAPA_CLS.get((m.group(1) or m.group(2)).decode('latin1').lower())
        if q: out.add(q)
    if not os.environ.get("SEM_NS"):                  # SEM_NS=1 mede o universo SEM esta frente
        out |= ns_refs(p)                              # 15a lacuna: namespace (src/app/api)
    _c[p] = out
    return out

def citados(p):                                        # 3a lacuna: aberto por JavaScript
    """Arquivos .php da raiz citados em string por p (menos o proprio p). So um nivel:
    e o navegador que os abre, nao um include."""
    try: b = open(p, "rb").read()
    except OSError: return set()
    return {q for q in (m.group(1).decode("latin1") for m in RX_STR.finditer(b))
            if os.path.isfile(q) and q != os.path.basename(p)}

rx = re.compile(r'^' + PREF + r'[0-9]*_', re.IGNORECASE)   # 1a lacuna: maiusculas
# so a raiz de ecidade/: as telas de menu ficam todas ali
telas = sorted(f for f in os.listdir(".") if os.path.isfile(f) and f.endswith(".php") and rx.match(f))
# Lote que nao e um prefixo (ex.: telas de menu soltas): TELAS=a.php,b.php -- o
# <prefixo> passa a ser so o nome dos arquivos de saida.
if os.environ.get("TELAS"):
    telas = sorted(os.environ["TELAS"].split(","))
    # TELAS=@<arquivo>: uma por linha -- listas grandes nao cabem numa variavel de ambiente
    if len(telas) == 1 and telas[0].startswith("@"):
        telas = sorted({l.strip() for l in open(telas[0][1:]) if l.strip()})
# fecho: as telas + o que elas abrem por JavaScript sao a partida; dai segue-se
# diretas() ate nao aparecer arquivo novo (busca em largura com `universo` como vistos)
js = set().union(*[citados(f) for f in telas]) - set(telas)
universo, fila = set(telas) | js, list(telas) + sorted(js)
while fila:
    for d in diretas(fila.pop()):
        if d not in universo: universo.add(d); fila.append(d)
universo = sorted(universo)

# Categorias contadas por regex sobre bytes. O lookbehind (?<![A-Za-z0-9_>$.]) evita
# casar metodo (->split), variavel ($each), nome composto (preg_split) e concatenacao.
CAT = {
 'split(':            re.compile(rb'(?<![A-Za-z0-9_>$.])split\s*\('),
 'each(':             re.compile(rb'(?<![A-Za-z0-9_>$.])each\s*\('),
 'ereg*(':            re.compile(rb'(?<![A-Za-z0-9_>$.])(?:ereg|eregi|ereg_replace|eregi_replace)\s*\('),
 # cobre $v{..}, $v[..]{..}, $v->p{..} e $v[$i]->p{..} -- a forma com ->prop
 # escapou no div e so o php -l do 8.5 a pegou (model/cda.model.php:1226)
 'offset {}':         re.compile(rb'\$\w+(?:\[[^\]\n]*\])*(?:\s*->\s*\w+(?:\[[^\]\n]*\])*)*\{\s*[^{}\n;]{1,25}?\s*\}'),
 '=& new':            re.compile(rb'=\s*&\s*new\b'),
 'create_function':   re.compile(rb'create_function\s*\('),
 'magic_quotes':      re.compile(rb'(?:get|set)_magic_quotes\w*\s*\('),
 'cast (real)':       re.compile(rb'\(\s*real\s*\)'),
 'db_fieldsmemory 1': re.compile(rb'db_fieldsmemory\(\s*\$\w+\s*\)'),
}
def parse_str_1arg(b):
    """Conta parse_str de 1 argumento contando virgulas no NIVEL SUPERIOR.
    Um regex [^,()] nao enxerga chamada aninhada -- foi assim que duas telas do
    jur ficaram fatais depois do porte."""
    n = 0
    for m in re.finditer(rb'parse_str\s*\(', b):
        i, prof, virg = m.end(), 1, False
        while i < len(b) and prof:
            c = b[i:i+1]
            if c == b'(': prof += 1
            elif c == b')': prof -= 1
            elif c == b',' and prof == 1: virg = True
            i += 1
        if not virg: n += 1
    return n

# inventario: so os arquivos NAO pagos; alvo = arquivo com ao menos uma ocorrencia
alvos, tot = set(), collections.Counter()
arq = collections.defaultdict(set)
for p in universo:
    if p in PAGO: continue
    b = open(p, "rb").read()
    for k, r in CAT.items():
        n = len(r.findall(b))
        if n: tot[k] += n; arq[k].add(p); alvos.add(p)
    n = parse_str_1arg(b)
    if n: tot['parse_str 1 arg'] += n; arq['parse_str 1 arg'].add(p); alvos.add(p)
    # 8a lacuna: a checagem de __construct precisa ser por CLASSE, nao pelo arquivo.
    # Com a checagem no arquivo inteiro, UMA classe com __construct mascarava todas as
    # outras do mesmo arquivo -- foi assim que 42 classes do NUCLEO (3 em db_stdlib.php,
    # 2 em JSON.php, 34 no jpgraph) sobreviveram a oito portes sem serem renomeadas.
    for nome, _ in classes_php4(b):
        tot['construtor PHP4'] += 1; arq['construtor PHP4'].add(p); alvos.add(p)
    # propriedades declaradas com valor inteiro (`var $x = 0;`, `public $x = -1;`)
    props = {m.group(1) for m in re.finditer(rb'(?:var|public)\s+\$(\w+)\s*=\s*-?\d+\s*;', b)}
    # Inclui literal NAO-NUMERICO, nao so "". No 5.6 a string nao-numerica era
    # coagida para 0 e casava com a propriedade inteira; no PHP 8 vira comparacao
    # de string. Variante achada pelo harness de escrita: `== "f"` em
    # db_cadtipoparc_classe.php. Literal numerico ("0", "5") e seguro nos dois.
    n = 0
    for x in props:
        for m in re.finditer(rb'\$this->'+re.escape(x)+rb'\s*==\s*["\']([^"\']{0,3})["\']', b):
            v = m.group(1)
            if v == b'' or not v.strip().isdigit(): n += 1
    if n: tot['$this->X == <literal>'] += n; arq['$this->X == <literal>'].add(p); alvos.add(p)

os.makedirs("tmp", exist_ok=True)
# com "\n" final: sem ele o `while read` do lint perde o ULTIMO arquivo da lista
open(f"tmp/{PREF}_universo.txt","w").write("\n".join(universo) + "\n")
open(f"tmp/{PREF}_alvos.txt","w").write("\n".join(sorted(alvos)) + "\n")
print(f"  telas (prefixo {PREF}[0-9]*_) : {len(telas)}")
print(f"  universo (6 frentes)        : {len(universo)}   | ja pago: {len([p for p in universo if p in PAGO])}")
print(f"  {'':28}| A ALTERAR: {len(alvos)}\n")
for k, n in tot.most_common():
    print(f"    {k:22s} {n:6d} ocorrencias em {len(arq[k]):4d} arquivos")
