#!/usr/bin/env python3
"""Inventario do codigo proprio do Laravel (ecidade/app, routes, configuration, bootstrap, database, public, tests, resources)
contra as quebras documentadas nos guias oficiais de upgrade 9 -> 13 (raw.githubusercontent.com/laravel/docs/<versao>/upgrade.md).

Somente leitura. Uso (da raiz do repositorio):
  python3 scratchpad/inventario_laravel.py contagem                 # item 1 do relatorio: o que existe no codigo proprio
  python3 scratchpad/inventario_laravel.py guias <pasta-dos-guias>  # baixa os guias 9 a 13 (precisa de rede)
  python3 scratchpad/inventario_laravel.py itens <pasta-dos-guias>  # TSV: uma linha por quebra dos guias, com ocorrencias
  python3 scratchpad/inventario_laravel.py helpers                  # funcoes globais do codigo proprio x helpers do Laravel
  python3 scratchpad/inventario_laravel.py ocorrencias <pasta-dos-guias>  # TSV com todas as ocorrencias (arquivo:linha)
  python3 scratchpad/inventario_laravel.py md <itens.tsv>           # tabela markdown so dos itens em que o codigo usa algo
Cada padrao e uma regex (PCRE-ish do Python) aplicada linha a linha; "0" significa que o padrao nao casou em nenhuma linha.
Padrao nao e prova de ausencia semantica (ex.: uma chamada dinamica nao aparece); a coluna 'tipo' diz quando e so um sinal.
"""
import os, re, sys, glob, collections

RAIZ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade')
ESCOPO = ['app', 'routes', 'configuration', 'bootstrap', 'database', 'public', 'tests', 'resources']
VERSOES = ['9.x', '10.x', '11.x', '12.x', '13.x']  # guias 9 a 13 (o 8 ja e o do PR)
PULA = {'High Impact Changes', 'Medium Impact Changes', 'Low Impact Changes'}


def arquivos():
    for pasta in ESCOPO:
        for dp, dn, fn in os.walk(os.path.join(RAIZ, pasta)):
            dn[:] = [d for d in dn if d not in ('vendor', 'node_modules', 'cache', 'relatorios', 'logs')]
            for f in fn:
                if f.endswith('.php'):
                    yield os.path.join(dp, f)
    for extra in ('composer.json', 'phpunit.xml', '.env.example'):
        p = os.path.join(RAIZ, extra)
        if os.path.exists(p):
            yield p


_cache = {}


def linhas(caminho):
    if caminho not in _cache:
        with open(caminho, 'rb') as f:
            _cache[caminho] = f.read().decode('latin-1').split('\n')
    return _cache[caminho]


def varre(regex, so=None):
    """Devolve (n_ocorrencias, n_arquivos, exemplos[arquivo:linha]). 'so' = prefixo de caminho relativo (ex. 'app/')."""
    rx = re.compile(regex)
    n, arqs, ex = 0, set(), []
    for c in arquivos():
        rel = os.path.relpath(c, RAIZ)
        if so and not rel.startswith(so):
            continue
        for i, l in enumerate(linhas(c), 1):
            if rx.search(l):
                n += 1
                arqs.add(rel)
                if len(ex) < 3:
                    ex.append('%s:%d' % (rel, i))
    return n, len(arqs), ex


def contagem():
    def n_arq(pasta, padrao='*.php'):
        return sum(1 for _ in glob.glob(os.path.join(RAIZ, pasta, '**', padrao), recursive=True))
    def n_cls(pasta, rx):
        r = re.compile(rx)
        return sum(1 for c in glob.glob(os.path.join(RAIZ, pasta, '**', '*.php'), recursive=True)
                   if any(r.search(l) for l in linhas(c)))
    print('# contagem do codigo proprio (ecidade/)')
    for pasta in ('app', 'routes', 'configuration', 'bootstrap', 'database', 'public', 'tests'):
        total = sum(len(linhas(c)) for c in glob.glob(os.path.join(RAIZ, pasta, '**', '*.php'), recursive=True))
        print('%s\tarquivos .php\t%d\tlinhas\t%d' % (pasta, n_arq(pasta), total))
    print('providers (app/Providers)\t%d' % n_arq('app/Providers'))
    print('providers (classes que estendem ServiceProvider em app/)\t%d' % n_cls('app', r'extends\s+\\?(\w+\\)*ServiceProvider\b'))
    print('middlewares (app/Http/Middleware)\t%d' % n_arq('app/Http/Middleware'))
    print('controllers (app/Http/Controllers)\t%d' % n_arq('app/Http/Controllers'))
    print('controllers (classes em app/Domain/**/Controllers)\t%d' % sum(1 for c in glob.glob(os.path.join(RAIZ, 'app/Domain/**/Controllers/*.php'), recursive=True)))
    print('form requests (extends FormRequest/DBFormRequest/BaseFormRequest em app/)\t%d' % n_cls('app', r'extends\s+\\?(\w+\\)*(DB|Base)?FormRequest\b'))
    print('models Eloquent (extends Model direto em app/)\t%d' % n_cls('app', r'extends\s+\\?(\w+\\)*Model\b'))
    print('jobs (app/Jobs)\t%d' % n_arq('app/Jobs'))
    print('commands (app/Console/Commands)\t%d' % n_arq('app/Console/Commands'))
    print('console tasks (app/Console/Tasks)\t%d' % n_arq('app/Console/Tasks'))
    print('policies/gates (arquivos com Gate:: ou Policy em app/)\t%d' % n_cls('app', r'Gate::|Policy\b'))
    print('events/listeners/notifications/mailables (extends Mailable etc.)\t%d' % n_cls('app', r'extends\s+\\?(\w+\\)*(Mailable|Notification)\b'))
    print('arquivos de rota (routes/**.php)\t%d' % n_arq('routes'))
    n, a, _ = varre(r'\bRoute::')
    print('chamadas Route:: em routes/ (e app/)\t%d em %d arquivos' % (n, a))
    print('configs do Laravel (configuration/*.php)\t%s' % ', '.join(sorted(os.path.basename(p) for p in glob.glob(os.path.join(RAIZ, 'configuration', '*.php')))))
    print('migrations Laravel (database/migrations)\t%d' % n_arq('database/migrations'))
    print('migrations Phinx/outras (database/**)\t%d' % (n_arq('database') - n_arq('database/migrations') - n_arq('database/seeds') - n_arq('database/factories')))


def helpers():
    """Funcoes globais declaradas no codigo proprio (autoload 'files' do composer + app/Helpers) x helpers do Laravel."""
    laravel = set('''abort abort_if abort_unless app app_path asset auth back base_path bcrypt broadcast blank cache class_basename class_uses_recursive collect config config_path cookie csrf_field csrf_token data_fill data_get data_set data_forget database_path decrypt dispatch dispatch_now dd dump e encrypt env event factory filled flash fluent forward_static_call get_class_name head info last lang_path logger logs method_field mix now old optional policy preg_replace_array public_path redirect report rescue resolve resource_path response retry request route report_if report_unless session str storage_path tap throw_if throw_unless today trait_uses_recursive trans trans_choice transform url validator value view with windows_os literal'''.split())
    removidos = set('''array_add array_collapse array_divide array_dot array_except array_first array_flatten array_forget array_get array_has array_last array_only array_pluck array_prepend array_pull array_random array_set array_sort array_sort_recursive array_where array_wrap camel_case ends_with kebab_case snake_case starts_with str_after str_before str_contains str_finish str_is str_limit str_plural str_random str_replace_array str_replace_first str_replace_last str_singular str_slug str_start studly_case title_case'''.split())
    achados = collections.defaultdict(list)
    for c in glob.glob(os.path.join(RAIZ, 'app', 'Helpers', '**', '*.php'), recursive=True):  # composer.json: autoload.files
        rel = os.path.relpath(c, RAIZ)
        for i, l in enumerate(linhas(c), 1):
            m = re.match(r'^\s*function\s+&?(\w+)\s*\(', l)
            if m:
                achados[m.group(1)].append('%s:%d' % (rel, i))
    print('# funcoes globais declaradas nos arquivos de autoload "files" (app/Helpers): %d' % len(achados))
    for nome in sorted(achados):
        marca = 'CONFLITA com helper atual do Laravel' if nome in laravel else ('mesmo nome de helper REMOVIDO do Laravel 6 (laravel/helpers)' if nome in removidos else '')
        print('%s\t%s\t%s' % (nome, achados[nome][0], marca))
    print('# conflitos: %d' % sum(1 for n in achados if n in laravel or n in removidos))


def baixa_guias(pasta):
    import urllib.request
    os.makedirs(pasta, exist_ok=True)
    for v in VERSOES:
        url = 'https://raw.githubusercontent.com/laravel/docs/%s/upgrade.md' % v
        with urllib.request.urlopen(url) as r:
            open(os.path.join(pasta, v + '.md'), 'wb').write(r.read())
        print(v, 'ok')


# --- itens: (versao, titulo exato do guia sem crases, regex, escopo|None, tipo) ---
# tipo: 'uso' = a regex acha o uso do recurso; 'sinal' = so um indicio (precisa de olho); 'config' = chave de config.
def itens(pasta):
    from inventario_laravel_padroes import PADROES, DISPOSICOES, TAREFAS
    saida = []
    for v in VERSOES:
        t = open(os.path.join(pasta, v + '.md'), encoding='utf-8').read()
        for m in re.finditer(r'^(#{2,4}) (.*)$', t, re.M):
            h = re.sub(r'<[^>]+>', '', m.group(2)).strip().replace('`', '')
            if h in PULA:
                continue
            saida.append((v, h))
    print('versao\titem do guia\tresultado\tocorrencias\tarquivos\texemplos\ttipo\tpadrao ou motivo\ttarefa')
    sem = []
    for v, h in saida:
        p = PADROES.get((v, h))
        if p:
            regex, so, tipo = p
            n, a, ex = varre(regex, so)
            print('%s\t%s\t%s\t%d\t%d\t%s\t%s\t%s\t%s' % (v, h, 'USA' if n else 'NAO USA', n, a, ' '.join(ex), tipo, regex, TAREFAS.get((v, h), '') if n else ''))
            continue
        d = DISPOSICOES.get((v, h)) or DISPOSICOES.get(('*', h))
        if d:
            print('%s\t%s\t%s\t\t\t\t%s\t%s' % (v, h, d[0], 'manual', d[1]))
        else:
            sem.append((v, h))
            print('%s\t%s\t%s\t\t\t\t%s\t%s' % (v, h, 'SEM TRATAMENTO', '-', '-'))
    if sem:
        sys.stderr.write('SEM TRATAMENTO: %d\n' % len(sem))
        for v, h in sem:
            sys.stderr.write('  %s | %s\n' % (v, h))


def ocorrencias(pasta):
    """TSV com TODAS as ocorrencias (versao, item, tarefa, arquivo:linha) dos itens que o codigo usa."""
    from inventario_laravel_padroes import PADROES, TAREFAS
    print('versao\titem do guia\ttarefa\tarquivo:linha')
    for v in VERSOES:
        t = open(os.path.join(pasta, v + '.md'), encoding='utf-8').read()
        for m in re.finditer(r'^(#{2,4}) (.*)$', t, re.M):
            h = re.sub(r'<[^>]+>', '', m.group(2)).strip().replace('`', '')
            p = PADROES.get((v, h))
            if not p:
                continue
            rx, so = re.compile(p[0]), p[1]
            for c in arquivos():
                rel = os.path.relpath(c, RAIZ)
                if so and not rel.startswith(so):
                    continue
                for i, l in enumerate(linhas(c), 1):
                    if rx.search(l):
                        print('%s\t%s\t%s\t%s:%d' % (v, h, TAREFAS.get((v, h), ''), rel, i))


def md(tsv):
    print('| Guia | Item | Ocorrencias | Arquivos | Exemplos | Tipo | Tarefa |')
    print('|---|---|---|---|---|---|---|')
    for l in open(tsv, encoding='utf-8').read().split('\n')[1:]:
        c = l.split('\t')
        if len(c) > 6 and c[2] == 'USA':
            print('| %s | %s | %s | %s | %s | %s | %s |' % (c[0], c[1].replace('|', '/'), c[3], c[4], ' '.join('`%s`' % e for e in c[5].split()[:3]), c[6], c[8] if len(c) > 8 else ''))


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'contagem':
        contagem()
    elif cmd == 'helpers':
        helpers()
    elif cmd == 'guias':
        baixa_guias(sys.argv[2])
    elif cmd == 'md':
        md(sys.argv[2])
    elif cmd == 'ocorrencias':
        ocorrencias(sys.argv[2])
    elif cmd == 'itens':
        itens(sys.argv[2])
    else:
        print(__doc__)
