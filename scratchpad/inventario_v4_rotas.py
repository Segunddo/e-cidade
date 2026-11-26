#!/usr/bin/env python3
"""Lista as rotas /v4 do e-Cidade lendo os arquivos de rotas (sem rodar o Laravel, sem banco).

Parte de app/Providers/RouteServiceProvider.php e segue os grupos (Route::prefix, Route::middleware, Route::group, ->group(closure),
->group(base_path('routes/...'))), os Route::get/post/put/patch/delete/any/match e Route::resource/apiResource. Variaveis de caminho e de controller
(`$path . "X@m"`, `$controller`, `"{$path}X@m"`) sao resolvidas quando a atribuicao e so de literais; o que nao resolve vira `{var}`.
Acrescenta as rotas do Passport 10 (`Passport::routes(null, ['prefix' => 'v4/oauth'])`, do pacote) e as 2 de `Broadcast::routes` (do framework).

Uso (da raiz do repositorio): python3 scratchpad/inventario_v4_rotas.py [saida.tsv]
Saida: TSV `metodo<TAB>caminho<TAB>controller<TAB>origem(arquivo:linha)<TAB>middleware`.
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ECI = os.path.join(RAIZ, 'ecidade')


def tira_comentarios(t):
    """remove // # e /* */ fora de strings (mantem as quebras de linha, para o numero da linha continuar certo)"""
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c in '\'"':
            q = c
            j = i + 1
            while j < n and t[j] != q:
                j += 2 if t[j] == '\\' else 1
            out.append(t[i:j + 1])
            i = j + 1
        elif t.startswith('//', i) or (c == '#' and not t.startswith('#[', i)):
            j = t.find('\n', i)
            i = n if j < 0 else j
        elif t.startswith('/*', i):
            j = t.find('*/', i)
            j = n if j < 0 else j + 2
            out.append('\n' * t.count('\n', i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def le(p):
    with open(os.path.join(ECI, p), encoding='latin-1') as f:
        return tira_comentarios(f.read())


def casa(texto, i, abre='(', fecha=')'):
    """indice do fecha que casa com o abre em texto[i], respeitando strings e comentarios"""
    prof, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if c in '\'"':
            q = c
            i += 1
            while i < n and texto[i] != q:
                i += 2 if texto[i] == '\\' else 1
        elif texto.startswith('//', i) or c == '#':
            j = texto.find('\n', i)
            i = n if j < 0 else j
        elif texto.startswith('/*', i):
            j = texto.find('*/', i)
            i = n if j < 0 else j + 1
        elif c == abre:
            prof += 1
        elif c == fecha:
            prof -= 1
            if prof == 0:
                return i
        i += 1
    return n - 1


def linha(texto, i):
    return texto.count('\n', 0, i) + 1


STR = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""


def avalia(expr, vars_):
    """expr PHP so de literais/variaveis/::class concatenados -> string (variavel desconhecida vira {nome})"""
    expr = expr.strip()
    if not expr:
        return ''
    partes, i, n = [], 0, len(expr)
    out = ''
    while i < n:
        c = expr[i]
        if c in '\'"':
            q = c
            j = i + 1
            while j < n and expr[j] != q:
                j += 2 if expr[j] == '\\' else 1
            lit = expr[i + 1:j]
            if q == '"':
                lit = re.sub(r'\{\$(\w+)\}', lambda m: vars_.get(m.group(1), '{%s}' % m.group(1)), lit)
                lit = re.sub(r'\$(\w+)', lambda m: vars_.get(m.group(1), '{%s}' % m.group(1)), lit)
            lit = lit.replace('\\\\', '\\')
            out += lit
            i = j + 1
        elif c == '$':
            m = re.match(r'\$(\w+)', expr[i:])
            out += vars_.get(m.group(1), '{%s}' % m.group(1))
            i += len(m.group(0))
        elif expr.startswith('::class', i):
            i += 7
        elif re.match(r'[\w\\]+::class', expr[i:]):
            m = re.match(r'([\w\\]+)::class', expr[i:])
            out += m.group(1).lstrip('\\')
            i += len(m.group(0))
        elif c in ' .\t\n\\':
            i += 1
        else:
            i += 1
    return out


def prof_chaves(texto):
    """profundidade de { } em cada posicao (strings ignoradas); o texto ja vem sem comentarios"""
    prof, d, i, n = [0] * (len(texto) + 1), 0, 0, len(texto)
    while i < n:
        c = texto[i]
        if c in '\'"':
            q = c
            j = i + 1
            while j < n and texto[j] != q:
                j += 2 if texto[j] == '\\' else 1
            for k in range(i, min(j + 1, n)):
                prof[k] = d
            i = j + 1
            continue
        if c == '{':
            d += 1
        elif c == '}':
            d -= 1
        prof[i] = d
        i += 1
    return prof


def atribuicoes(texto):
    """[(posicao, nome, expr)] das atribuicoes simples `$nome = <literais/variaveis>;` no NIVEL 0 deste texto (o escopo do arquivo/closure)"""
    prof = prof_chaves(texto)
    out = []
    for m in re.finditer(r'\$(\w+)\s*(\.?=)\s*((?:' + STR + r'|\$\w+|[\w\\]+::class|\s|\.)+);', texto):
        if prof[m.start()] == 0:
            out.append((m.start(), m.group(1), m.group(3), m.group(2)))
    return out


def vars_em(asg, pos, base):
    """variaveis vigentes na posicao: as de fora do escopo mais as atribuicoes de nivel 0 ANTES de pos, na ordem"""
    v = dict(base)
    for p, nome, expr, op in asg:
        if p >= pos:
            break
        v[nome] = (v.get(nome, '') if op == '.=' else '') + avalia(expr, v)
    return v


def args_top(args):
    """separa argumentos de nivel 0 por virgula"""
    out, prof, ini, i, n = [], 0, 0, 0, len(args)
    while i < n:
        c = args[i]
        if c in '\'"':
            q = c
            i += 1
            while i < n and args[i] != q:
                i += 2 if args[i] == '\\' else 1
        elif c in '([{':
            prof += 1
        elif c in ')]}':
            prof -= 1
        elif c == ',' and prof == 0:
            out.append(args[ini:i])
            ini = i + 1
        i += 1
    out.append(args[ini:])
    return [a.strip() for a in out if a.strip()]


METODOS = {'get', 'post', 'put', 'patch', 'delete', 'options', 'any'}
rotas = []


def junta(*partes):
    p = '/'.join(x.strip('/') for x in partes if x and x.strip('/'))
    return p


def registra(metodo, caminho, controller, arq, lin, mw):
    rotas.append((metodo.upper(), '/' + caminho.strip('/'), controller, '%s:%d' % (arq, lin), ','.join(mw)))


def expande_resource(nome, ctrl, opcoes, api):
    acoes = [('GET', '', 'index'), ('GET', '/create', 'create'), ('POST', '', 'store'), ('GET', '/{id}', 'show'),
             ('GET', '/{id}/edit', 'edit'), ('PUT|PATCH', '/{id}', 'update'), ('DELETE', '/{id}', 'destroy')]
    if api:
        acoes = [a for a in acoes if a[2] not in ('create', 'edit')]
    m = re.search(r"'only'\s*=>\s*\[([^\]]*)\]", opcoes)
    if m:
        so = set(re.findall(r"['\"](\w+)['\"]", m.group(1)))
        acoes = [a for a in acoes if a[2] in so]
    m = re.search(r"'except'\s*=>\s*\[([^\]]*)\]", opcoes)
    if m:
        ex = set(re.findall(r"['\"](\w+)['\"]", m.group(1)))
        acoes = [a for a in acoes if a[2] not in ex]
    return [(a[0], nome + a[1], '%s@%s' % (ctrl, a[2])) for a in acoes]


def processa(texto, arq, prefixo, mw, vars_, prof=0, base=0):
    base_vars = vars_
    asg = atribuicoes(texto)
    i = 0
    rx = re.compile(r'Route::(\w+)\s*\(')
    while True:
        m = rx.search(texto, i)
        if not m:
            break
        inicio = m.start()
        lin = base + linha(texto, inicio)
        vars_ = vars_em(asg, inicio, base_vars)
        pos = inicio
        cadeia = []
        while True:
            mm = re.compile(r'\s*(?:Route::|->)\s*(\w+)\s*\(').match(texto, pos)
            if not mm:
                break
            fim = casa(texto, mm.end() - 1)
            cadeia.append((mm.group(1), texto[mm.end():fim], mm.end()))
            pos = fim + 1
        i = max(pos, m.end())
        if not cadeia:
            continue
        pre, mws = prefixo, list(mw)
        ultimo, uargs, uini = cadeia[-1]
        if cadeia[0][0] in METODOS or cadeia[0][0] in ('match', 'resource', 'apiResource'):
            # rota com modificadores depois (->middleware(...), ->name(...), ->where(...)): a definicao e o 1o elemento
            for nome, a_, _ in cadeia[1:]:
                if nome == 'middleware':
                    mws += re.findall(r"['\"]([^'\"]+)['\"]", a_)
            ultimo, uargs, uini = cadeia[0]
            cadeia = [cadeia[0]]
        for nome, a, _ in cadeia[:-1]:
            if nome == 'prefix':
                pre = junta(pre, avalia(a, vars_))
            elif nome == 'middleware':
                mws += re.findall(r"['\"]([^'\"]+)['\"]", a)
        if ultimo == 'group':
            # Route::group([...], closure): opcoes no 1o argumento
            partes = args_top(uargs)
            corpo_arg = partes[-1] if partes else ''
            if len(cadeia) == 1 and partes and partes[0].startswith('['):
                opc = partes[0]
                mp = re.search(r"['\"]prefix['\"]\s*=>\s*(" + STR + r"|[^,\]]+)", opc)
                if mp:
                    pre = junta(pre, avalia(mp.group(1), vars_))
                mws += re.findall(r"['\"]middleware['\"]\s*=>\s*\[?([^\]\),]*)", opc) and re.findall(r"['\"]([^'\"]+)['\"]", ' '.join(re.findall(r"['\"]middleware['\"]\s*=>\s*(\[[^\]]*\]|" + STR + ")", opc)))
            if corpo_arg.startswith('function') or corpo_arg.startswith('fn'):
                b0 = corpo_arg.find('{')
                b1 = casa(corpo_arg, b0, '{', '}')
                abs_corpo = uini + uargs.rfind(corpo_arg) + b0 + 1
                processa(corpo_arg[b0 + 1:b1], arq, pre, mws, vars_, prof + 1, base + texto.count('\n', 0, abs_corpo))
            else:
                mf = re.search(r"base_path\(\s*(" + STR + r")\s*\)", corpo_arg)
                if mf:
                    caminho = mf.group(1)[1:-1]
                else:
                    mf = re.search(r"__DIR__\s*\.\s*(" + STR + ")", corpo_arg)
                    caminho = os.path.join(os.path.dirname(arq), mf.group(1)[1:-1].lstrip('/')) if mf else None
                if caminho and os.path.exists(os.path.join(ECI, caminho)):
                    processa(le(caminho), caminho, pre, mws, {}, prof + 1)
                else:
                    sys.stderr.write('grupo sem arquivo: %s:%d %s\n' % (arq, lin, corpo_arg[:60]))
        elif ultimo in METODOS or ultimo == 'match':
            partes = args_top(uargs)
            if ultimo == 'match':
                metodos = [x.upper() for x in re.findall(r"['\"](\w+)['\"]", partes[0])]
                partes = partes[1:]
            else:
                metodos = [ultimo.upper()]
            if not partes:
                continue
            caminho = avalia(partes[0], vars_)
            ctrl = ''
            if len(partes) > 1:
                alvo = partes[1]
                if alvo.startswith('function') or alvo.startswith('fn'):
                    ctrl = '(closure)'
                elif alvo.startswith('['):
                    ctrl = avalia(re.sub(r',\s*', '@', alvo.strip('[]'), 1), vars_)
                else:
                    ctrl = avalia(alvo, vars_)
                    if ctrl.startswith('{') and '@' not in ctrl:
                        ctrl = alvo[:60]
            for mt in metodos:
                registra(mt, junta(pre, caminho), ctrl.replace('\\\\', '\\').lstrip('\\'), arq, lin, mws)
        elif ultimo in ('resource', 'apiResource'):
            partes = args_top(uargs)
            nome = avalia(partes[0], vars_)
            ctrl = avalia(partes[1], vars_) if len(partes) > 1 else ''
            for mt, cam, c in expande_resource(nome, ctrl.lstrip('\\'), partes[2] if len(partes) > 2 else '', ultimo == 'apiResource'):
                registra(mt, junta(pre, cam), c, arq, lin, mws)


def passport():
    base = 'v4/oauth'
    lista = [('POST', 'token', 'AccessTokenController@issueToken'), ('GET', 'authorize', 'AuthorizationController@authorize'),
             ('POST', 'authorize', 'ApproveAuthorizationController@approve'), ('DELETE', 'authorize', 'DenyAuthorizationController@deny'),
             ('GET', 'tokens', 'AuthorizedAccessTokenController@forUser'), ('DELETE', 'tokens/{token_id}', 'AuthorizedAccessTokenController@destroy'),
             ('POST', 'token/refresh', 'TransientTokenController@refresh'), ('GET', 'clients', 'ClientController@forUser'),
             ('POST', 'clients', 'ClientController@store'), ('PUT', 'clients/{client_id}', 'ClientController@update'),
             ('DELETE', 'clients/{client_id}', 'ClientController@destroy'), ('GET', 'scopes', 'ScopeController@all'),
             ('GET', 'personal-access-tokens', 'PersonalAccessTokenController@forUser'), ('POST', 'personal-access-tokens', 'PersonalAccessTokenController@store'),
             ('DELETE', 'personal-access-tokens/{token_id}', 'PersonalAccessTokenController@destroy')]
    for mt, cam, c in lista:
        registra(mt, junta(base, cam), 'Laravel\\Passport\\Http\\Controllers\\' + c, 'pacote laravel/passport 10.4.2 (AuthServiceProvider.php:31)', 0, ['passport'])
        rotas[-1] = rotas[-1][:3] + ('pacote laravel/passport 10.4.2',) + rotas[-1][4:]


def broadcast():
    """Broadcast::routes(['prefix' => 'v4', 'middleware' => ['auth:api']]) (BroadcastServiceProvider.php:17): GET e POST v4/broadcasting/auth, do framework"""
    for mt in ('GET', 'POST'):
        rotas.append((mt, '/v4/broadcasting/auth', 'Illuminate\\Broadcasting\\BroadcastController@authenticate', 'framework laravel (app/Providers/BroadcastServiceProvider.php:17)', 'auth:api'))


def main():
    processa(le('app/Providers/RouteServiceProvider.php'), 'app/Providers/RouteServiceProvider.php', '', [], {})
    passport()
    broadcast()
    vistos, unicas = set(), []
    for r in rotas:
        if os.environ.get('TODOS'):
            unicas.append(r)
            continue
        k = (r[0], r[1])
        if k in vistos:
            continue
        vistos.add(k)
        unicas.append(r)
    saida = sys.argv[1] if len(sys.argv) > 1 else '-'
    f = sys.stdout if saida == '-' else open(saida, 'w', encoding='utf-8')
    f.write('metodo\tcaminho\tcontroller\torigem\tmiddleware\n')
    for r in sorted(unicas, key=lambda r: (r[1], r[0])):
        f.write('\t'.join(r) + '\n')
    sys.stderr.write('%d registros, %d rotas distintas (metodo+caminho)\n' % (len(rotas), len(unicas)))


if __name__ == '__main__':
    main()
