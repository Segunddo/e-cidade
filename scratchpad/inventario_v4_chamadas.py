#!/usr/bin/env python3
"""Acha as chamadas a /v4 no codigo (telas legadas .php, scripts .js, front Vue) e casa cada uma com as rotas lidas por inventario_v4_rotas.py.

Sem rodar o sistema e sem banco: so leitura dos arquivos versionados (git ls-files). Extrai toda ocorrencia de `v4/...` dentro de string,
troca expressoes (`${x}`, `' + x + '`, `" . $x . "`, `<?= ... ?>`) por `{x}`, tira a query string, detecta o metodo pela chamada
(`.get(`, `.post(`, `.put(`, `.patch(`, `.delete(`, `method:`/`type:`), e classifica:
  exata      o caminho (com `{x}` casando qualquer trecho) existe nas rotas
  composta   o arquivo define a base (`baseURL = 'v4/api/x'`) e usa outro literal do mesmo arquivo que fecha uma rota
  prefixo    so ha a base (o resto e montado por variavel/outro arquivo): casa com todas as rotas sob ela
  sem_rota   nenhuma rota registrada casa

Uso (da raiz do repositorio): python3 scratchpad/inventario_v4_chamadas.py <rotas.tsv> <saida-chamadas.tsv> <saida-rotas.tsv>
"""
import os, re, subprocess, sys, collections

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ECI = os.path.join(RAIZ, 'ecidade')

EXT = ('.php', '.js', '.vue', '.html', '.htm', '.inc', '.class')
EXCLUI = ('vendor/', 'tmp/', 'release_notes/', 'manuais/', 'public/', 'tests/', 'node_modules/', 'routes/', 'database/', 'dbagata/')


def arquivos():
    out = subprocess.run(['git', 'ls-files', 'ecidade'], cwd=RAIZ, capture_output=True, text=True).stdout.split('\n')
    for f in out:
        r = f[len('ecidade/'):]
        if not r or not r.endswith(EXT) or r.startswith(EXCLUI) or r.endswith(('.min.js', '.bkp', '.ok')):
            continue
        yield r


def tipo(r):
    if r.startswith('resources/vue'):
        return 'vue'
    if r.startswith(('app/', 'src/')):
        return 'servidor'
    if r.endswith('.js'):
        return 'js'
    if r.startswith('resources/assets'):
        return 'js'
    if r.startswith('extension/'):
        return 'extension'
    return 'php-legado'


TOK = re.compile(r"(?<![A-Za-z0-9_])v4/[^\s'\"`),;]*")
EXPR = [(re.compile(r'\$\{[^}]*\}'), '{x}'), (re.compile(r"""['"]\s*\+\s*[A-Za-z_$][\w$.\[\]()]*\s*\+\s*['"]"""), '{x}'),
        (re.compile(r"""['"]\s*\.\s*\$[\w>\[\]'"-]+\s*\.\s*['"]"""), '{x}'), (re.compile(r'<\?=.*?\?>'), '{x}'), (re.compile(r'\{\$[^}]*\}'), '{x}'),
        (re.compile(r'\$\w+'), '{x}')]


def extrai(linha_txt):
    """ocorrencias de v4/... na linha: (caminho normalizado, parcial?)"""
    res = []
    for m in re.finditer(r"(?<![A-Za-z0-9_])v4/", linha_txt):
        ini = m.start()
        resto = linha_txt[ini:]
        # corta no fecha-aspas da string em que esta; expressoes de concatenacao ficam
        quote = None
        k = ini - 1
        while k >= 0 and linha_txt[k] not in '\'"`':
            k -= 1
        quote = linha_txt[k] if k >= 0 else None
        fim = len(resto)
        if quote:
            j = resto.find(quote)
            fim = j if j >= 0 else len(resto)
        lit = resto[:fim]
        depois = resto[fim:fim + 12]
        parcial = bool(re.match(r"""\s*[`'"]?\s*(\+|\.\s)""", depois)) and not lit.endswith('{x}') or lit.endswith('/')
        for rx, rep in EXPR:
            lit = rx.sub(rep, lit)
        lit = lit.split('?')[0].split('#')[0].rstrip('\\')
        res.append((lit, parcial or bool(re.match(r"\s*\+", depois))))
    return res


METODO = re.compile(r"\.(get|post|put|patch|delete)\s*\(|(?:method|type)\s*[:=]\s*['\"](GET|POST|PUT|PATCH|DELETE)['\"]", re.I)


def metodo_perto(linhas, i):
    for k in (i, i - 1, i - 2):
        if 0 <= k < len(linhas):
            m = METODO.search(linhas[k])
            if m:
                return (m.group(1) or m.group(2)).upper()
    return '?'


def segs(p):
    return [s for s in p.strip('/').split('/') if s != '']


def param(s):
    return s.startswith('{') and s.endswith('}')


def casa_seg(a, b):
    return a == b or param(a) or param(b)


def main():
    rotas_tsv, saida_ch, saida_ro = sys.argv[1:4]
    rotas = []
    for l in open(rotas_tsv, encoding='utf-8').read().split('\n')[1:]:
        if not l:
            continue
        mt, cam, ctrl, org, mw = (l.split('\t') + [''] * 5)[:5]
        rotas.append({'metodo': mt, 'caminho': cam, 'controller': ctrl, 'origem': org, 'segs': segs(cam), 'chamadores': set(), 'prefixo': set(), 'provavel': set(), 'refs': []})
    # arquivos de rotas que ninguem carrega ja estao fora da lista; indice por numero de segmentos
    por_n = collections.defaultdict(list)
    for r in rotas:
        por_n[len(r['segs'])].append(r)

    chamadas = []
    for rel in arquivos():
        try:
            txt = open(os.path.join(ECI, rel), encoding='latin-1').read()
        except OSError:
            continue
        if 'v4/' not in txt and 'v4\\/' not in txt:
            continue
        linhas = txt.split('\n')
        for i, lt in enumerate(linhas):
            if 'v4/' not in lt:
                continue
            for cam, parcial in extrai(lt):
                if cam in ('v4/', 'v4'):
                    parcial = True
                chamadas.append({'arq': rel, 'lin': i + 1, 'tipo': tipo(rel), 'metodo': metodo_perto(linhas, i), 'caminho': '/' + cam.strip('/'),
                                 'parcial': parcial, 'classe': '', 'rotas': []})
        # literais do arquivo (para as chamadas compostas)
    def procura(cam, metodo):
        s = segs(cam)
        achadas = []
        for r in por_n.get(len(s), []):
            if all(casa_seg(a, b) for a, b in zip(s, r['segs'])):
                if metodo == '?' or r['metodo'] == metodo or r['metodo'] == 'ANY':
                    achadas.append(r)
        return achadas

    # 2a passagem: caminhos RELATIVOS a base da API (`'financeiro/planejamento/x'` com a base vinda de requestApi/urlApi/apiUrl),
    # sem o `v4/` no arquivo. So conta se o literal inteiro, com /v4/api/ na frente, fecha uma rota e o arquivo usa um desses mecanismos.
    areas = {r['segs'][2] for r in rotas if len(r['segs']) > 3 and r['segs'][:2] == ['v4', 'api']}
    rx_rel = re.compile(r"""['"`](?:\$\{[^}]*\})?/?((?:%s)/[A-Za-z0-9_\-{}$./]+?)['"`]""" % '|'.join(sorted(areas)))
    mecanismo = re.compile(r'requestApi|urlApi|apiUrl|ApiUrl|api_url|HttpClient|axios|request\.send|\$http|ECIDADE_REQUEST_PATH')
    ja = {(c['arq'], c['lin']) for c in chamadas}
    for rel in arquivos():
        try:
            txt = open(os.path.join(ECI, rel), encoding='latin-1').read()
        except OSError:
            continue
        if rel.startswith(('app/', 'src/')) or not (mecanismo.search(txt) or tipo(rel) in ('vue', 'js')):
            continue
        linhas = txt.split('\n')
        for i, lt in enumerate(linhas):
            if (rel, i + 1) in ja:
                continue
            for m in rx_rel.finditer(lt):
                lit = re.sub(r'\$\{[^}]*\}', '{x}', m.group(1)).split('?')[0]
                lit = re.sub(r'\$\w+', '{x}', lit)
                full = '/v4/api/' + lit.strip('/')
                metodo = metodo_perto(linhas, i)
                ach = procura(full, metodo)
                classe = 'relativa'
                if not ach and metodo != '?':
                    ach = procura(full, '?')
                    classe = 'relativa(metodo difere)'
                if ach:
                    chamadas.append({'arq': rel, 'lin': i + 1, 'tipo': tipo(rel), 'metodo': metodo, 'caminho': full, 'parcial': False,
                                     'classe': classe, 'rotas': ach})
    por_arq = collections.defaultdict(list)
    for c in chamadas:
        por_arq[c['arq']].append(c)

    for c in chamadas:
        if c['classe'].startswith(('relativa', 'provavel')):
            continue
        achadas = procura(c['caminho'], c['metodo']) if not c['parcial'] else []
        if not achadas and not c['parcial'] and c['metodo'] != '?':
            achadas = procura(c['caminho'], '?')
            if achadas:
                c['classe'] = 'exata(metodo difere)'
        if achadas:
            c['classe'] = c['classe'] or 'exata'
            c['rotas'] = achadas
        else:
            base = segs(c['caminho'])
            sob = [r for r in rotas if r['segs'][:len(base)] == base]
            # composta: outro literal do mesmo arquivo fecha uma rota
            txt = open(os.path.join(ECI, c['arq']), encoding='latin-1').read()
            lits = set(re.findall(r"""['"`](/?[A-Za-z][A-Za-z0-9_/{}\-]{1,80})['"`]""", txt)) | set(re.findall(r"""['"`](/[A-Za-z0-9_/{}\-]{1,80})['"`]""", txt))
            comp = []
            for lit in lits:
                full = '/' + '/'.join(base + segs(lit))
                for r in procura(full, c['metodo']):
                    if r not in comp:
                        comp.append(r)
            if comp:
                c['classe'], c['rotas'] = 'composta', comp
            elif len(base) <= 2:
                c['classe'] = 'base_global'   # /v4 ou /v4/api: o resto do caminho e montado em outro arquivo
            elif sob:
                c['classe'], c['rotas'] = 'prefixo', sob
            else:
                c['classe'] = 'sem_rota'

    # 3a passagem (provavel): literal que e o RABO de uma rota (os 2 ultimos segmentos ou mais, ou 1 segmento unico de 12+ caracteres),
    # em arquivo que usa um mecanismo de chamada. Menos firme que as anteriores: base e rabo ficam em lugares diferentes.
    def norm(t):
        t = re.sub(r'\$\{[^}]*\}', '{}', t)
        t = re.sub(r'\{[^}/]*\}', '{}', t)
        return t.strip('/')
    cobertas = {id(r) for c in chamadas if c['classe'] in ('exata', 'exata(metodo difere)', 'composta', 'relativa', 'relativa(metodo difere)') for r in c['rotas']}
    rabo = collections.defaultdict(list)
    for r in rotas:
        if r['segs'][:2] != ['v4', 'api'] or id(r) in cobertas:
            continue
        ss = [x if not param(x) else '{}' for x in r['segs'][2:]]
        for k in range(1, min(5, len(ss)) + 1):
            rabo['/'.join(ss[-k:])].append(r)
        sem_param = list(ss)
        while sem_param and sem_param[-1] == '{}':
            sem_param.pop()
        if sem_param != ss:
            for k in range(1, min(5, len(sem_param)) + 1):
                rabo['/'.join(sem_param[-k:])].append(r)
    ultimo_unico = collections.Counter(r['segs'][-1] for r in rotas)
    ja = {(c['arq'], c['lin']) for c in chamadas}
    rx_lit = re.compile(r"""['"`](?:\$\{[^}]*\})?/?([A-Za-z][A-Za-z0-9_\-]*(?:/[A-Za-z0-9_\-{}$.]+)*)/?['"`]""")
    for rel in arquivos():
        try:
            txt = open(os.path.join(ECI, rel), encoding='latin-1').read()
        except OSError:
            continue
        if rel.startswith(('app/', 'src/')) or not (mecanismo.search(txt) or tipo(rel) in ('vue', 'js')):
            continue
        linhas = txt.split('\n')
        for i, lt in enumerate(linhas):
            if (rel, i + 1) in ja:
                continue
            for m in rx_lit.finditer(lt):
                lit = norm(m.group(1).split('?')[0])
                nseg = len(lit.split('/'))
                if nseg == 1 and (len(lit) < 12 or ultimo_unico.get(lit, 0) != 1):
                    continue
                for r in rabo.get(lit, [])[:3]:
                    metodo = metodo_perto(linhas, i)
                    chamadas.append({'arq': rel, 'lin': i + 1, 'tipo': tipo(rel), 'metodo': metodo, 'caminho': '.../' + lit, 'parcial': False,
                                     'classe': 'provavel', 'rotas': [r]})
    por_arq = collections.defaultdict(list)
    for c in chamadas:
        por_arq[c['arq']].append(c)
    chamadas = [c for c in chamadas if c['tipo'] != 'servidor']   # app/ e src/: so comentario apidoc das rotas, nao e chamador
    for c in chamadas:
        for r in c['rotas']:
            if c['classe'] == 'prefixo':
                r['prefixo'].add(c['arq'])
            elif c['classe'] == 'provavel':
                r['provavel'].add(c['arq'])
            else:
                r['chamadores'].add(c['arq'])
                r['refs'].append('%s:%d' % (c['arq'], c['lin']))

    with open(saida_ch, 'w', encoding='utf-8') as f:
        f.write('arquivo\tlinha\ttipo\tmetodo\tcaminho\tclasse\trotas_casadas\texemplo_de_rota\n')
        for c in sorted(chamadas, key=lambda c: (c['arq'], c['lin'])):
            ex = ''
            if c['rotas']:
                r = c['rotas'][0]
                ex = '%s %s %s' % (r['metodo'], r['caminho'], r['controller'])
            f.write('%s\t%d\t%s\t%s\t%s\t%s\t%d\t%s\n' % (c['arq'], c['lin'], c['tipo'], c['metodo'], c['caminho'] + ('...' if c['parcial'] else ''), c['classe'], len(c['rotas']), ex))
    with open(saida_ro, 'w', encoding='utf-8') as f:
        f.write('metodo\tcaminho\tcontroller\torigem\tarquivos_chamadores\tarquivos_so_pela_base\tarquivos_provaveis\texemplos\n')
        for r in rotas:
            ex = ' | '.join(sorted(set(r['refs']))[:3])
            f.write('%s\t%s\t%s\t%s\t%d\t%d\t%d\t%s\n' % (r['metodo'], r['caminho'], r['controller'], r['origem'], len(r['chamadores']), len(r['prefixo']), len(r['provavel']), ex))
    cont = collections.Counter(c['classe'] for c in chamadas)
    sys.stderr.write('%d chamadas em %d arquivos: %s\n' % (len(chamadas), len(por_arq), dict(cont)))


if __name__ == '__main__':
    main()
