#!/usr/bin/env python3
"""Passos 1-3 da receita de porte: enumera o universo de um modulo pelas SEIS
frentes, faz o inventario das categorias conhecidas e grava a lista de alvos.

Le tudo em BYTES -- 64% da base e LATIN-1 e o grep a pula em silencio.

Uso:  python3 scratchpad/enumera.py <prefixo>
Saida: tmp/<prefixo>_universo.txt  e  tmp/<prefixo>_alvos.txt
"""
import os, re, sys, collections, subprocess

# O projeto passou a viver em ecidade/ (reorganizacao upstream 2169884a8);
# scratchpad/ continua na raiz, ao lado dele.
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
PREF = sys.argv[1]

NUCLEO = {
 "libs/db_stdlib.php","libs/db_conecta.php","libs/db_sessoes.php","libs/db_usuariosonline.php",
 "libs/db_acessa.php","libs/db_calcula.php","libs/db_libpessoal.php","libs/db_utils.php",
 "libs/db_sql.php","libs/db_app.utils.php","libs/JSON.php","dbforms/db_funcoes.php",
 "dbforms/db_classesgenericas.php","std/DBString.php","std/db_stdClass.php",
 "config/ecidade_config.php","fpdf151/fpdf.php","fpdf151/pdf.php",
 "model/pessoal/std/DBPessoal.model.php","model/configuracao/mensagem/DBMensagem.model.php",
 "classes/db_cgm_classe.php"}
# Os commits anteriores a reorganizacao registram "classes/x.php"; os
# posteriores registrarao "ecidade/classes/x.php". Como o universo e relativo a
# ecidade/, normaliza-se o prefixo -- senao o proximo modulo veria tudo como
# nao-pago e o porta.py re-aplicaria guardas JA aplicadas.
PORTADO = {l.strip().removeprefix("ecidade/") for l in subprocess.run(
    ["git","log","--name-only","--format=","--grep=^Porta "],
    capture_output=True, text=True).stdout.splitlines() if l.strip().endswith(".php")}
PAGO = NUCLEO | PORTADO

# re.I nas tres: PHP nao diferencia maiusculas em palavra-chave nem em nome de
# metodo/classe. 9a lacuna: `db_utils::getdao('atolegal')` (minusculas) -- 781
# chamadas em 244 arquivos com grafia diferente de getDao, invisiveis a frente.
RX_INC = re.compile(rb'(?:include|require)(?:_once)?\s*\(?\s*(?:modification\s*\(\s*)?["\']([^"\']+\.php)["\']', re.I)
RX_NEW = re.compile(rb'new\s+(cl_\w+)', re.I)
# 7a lacuna: db_utils::getDao('x') instancia cl_x por autoload sem citar o
# nome da classe. Achada no `fis`, em db_cadtipo_classe.php -- cujo construtor
# PHP4 inicializa $this->rotulo, e sem ele a tela morre com label() on null.
RX_DAO = re.compile(rb'''getDao\s*\(\s*['"]([A-Za-z0-9_]+)['"]''', re.I)
RX_STR = re.compile(rb'["\']([A-Za-z0-9_]+\.(?:RPC\.)?php)["\']')

def classes_php4(b):
    """Classes cujo construtor e o metodo homonimo (estilo PHP 4), olhando o corpo de
    CADA classe isoladamente. Fatiar por `class X` evita dois erros do regex de arquivo
    inteiro: mascarar classes vizinhas por causa de um __construct alheio, e contar um
    METODO homonimo de outra classe como se fosse construtor."""
    pos = [(m.start(), m.group(1)) for m in re.finditer(rb'\bclass\s+(\w+)', b)]
    out = []
    for i, (ini, nome) in enumerate(pos):
        corpo = b[ini: pos[i+1][0] if i+1 < len(pos) else len(b)]
        if re.search(rb'function\s+__construct\s*\(', corpo, re.I): continue
        if re.search(rb'function\s+' + re.escape(nome) + rb'\s*\(', corpo, re.I):
            out.append((nome, ini))
    return out

_c = {}
def diretas(p):
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
    _c[p] = out
    return out

def citados(p):                                        # 3a lacuna: aberto por JavaScript
    try: b = open(p, "rb").read()
    except OSError: return set()
    return {q for q in (m.group(1).decode("latin1") for m in RX_STR.finditer(b))
            if os.path.isfile(q) and q != os.path.basename(p)}

rx = re.compile(r'^' + PREF + r'[0-9]*_', re.IGNORECASE)   # 1a lacuna: maiusculas
telas = sorted(f for f in os.listdir(".") if os.path.isfile(f) and f.endswith(".php") and rx.match(f))
js = set().union(*[citados(f) for f in telas]) - set(telas)
universo, fila = set(telas) | js, list(telas) + sorted(js)
while fila:
    for d in diretas(fila.pop()):
        if d not in universo: universo.add(d); fila.append(d)
universo = sorted(universo)

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
