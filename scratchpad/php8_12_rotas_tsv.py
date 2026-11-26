#!/usr/bin/env python3
"""PHP8-12: transforma o JSON de php8_12_rotas.php na lista de rotas (TSV) e imprime o resumo do registro.
Uso: python3 php8_12_rotas_tsv.py rotas.json docs/registro/php8-12-rotas.tsv"""
import collections, json, os, sys
d = json.load(open(sys.argv[1])); R = d['rotas']
sit = {}
for r in R:
    s = 'viva'
    for m, x in r['responde'].items():
        if isinstance(x, str): s = 'nao-casa-o-proprio-caminho'
        elif x != r['ordem']:
            o = R[x]
            s = ('substituida-pela-%d' if o['uri'] == r['uri'] else 'sombreada-pela-%d') % x
    sit[r['ordem']] = s
with open(sys.argv[2], 'w') as f:
    f.write('ordem\tmetodos\turi\tnome\tacao\tonde\tsituacao\tget_so_leitura\tacao_onde\n')
    for r in R:
        f.write('\t'.join(str(x) for x in (r['ordem'], ','.join(r['metodos']), r['uri'], r['nome'] or '', r['acao'], r['onde'],
                sit[r['ordem']], r['leitura'] or '', r['acao_onde'])) + '\n')
c = collections.Counter(s.split('-pela-')[0] for s in sit.values())
print('laravel', d['laravel'], '| registradas', len(R), '| situacao', dict(c))
dup = collections.defaultdict(list)
for r in R:
    for m in r['metodos']: dup[(m, r['uri'])].append(r)
dup = {k: v for k, v in dup.items() if len(v) > 1}
ac = lambda x: x['acao'].lstrip('\\')   # '\\App\\X@y' e 'App\\X@y' sao a mesma acao
print('metodo+uri repetidos', len(dup), '| com acao diferente', sum(1 for v in dup.values() if len({ac(x) for x in v}) > 1))
for (m, u), v in sorted(dup.items(), key=lambda kv: kv[1][0]['ordem']):
    print('  R\t%s %s\t%s\t%s' % (m, u, ' | '.join('%s %s' % (x['onde'], x['acao'].split('\\')[-1]) for x in v), 'acao igual' if len({ac(x) for x in v}) == 1 else 'ACAO DIFERENTE: ' + ' x '.join(ac(x) for x in v)))
rep = {n: v for n, v in d['nomes'].items() if len(v['rotas']) > 1}
print('nomes', len(d['nomes']), '| repetidos', len(rep))
for n, v in rep.items():
    print('  N\t%s\tL8: %s %s\tL12+: %s %s' % (n, R[v['l8']]['uri'], R[v['l8']]['onde'], R[v['l12']]['uri'], R[v['l12']]['onde']))
cl = collections.Counter(r['uri'].split('/')[0] for r in R if r['acao'] == 'Closure')
print('closures', sum(cl.values()), dict(cl))
g = collections.Counter()
for r in R:
    if r['leitura'] is None or sit[r['ordem']] != 'viva': continue
    pre = 'v4/api' if r['uri'].startswith('v4/api') else r['uri'].split('/')[0]
    g[(pre, r['leitura'].split(':')[0])] += 1
print('GET vivas', sum(g.values()), dict(sorted(g.items())))
todos = {os.path.relpath(os.path.join(dp, f), 'ecidade') for dp, dn, fs in os.walk('ecidade/routes') for f in fs if f.endswith('.php')}
nao = sorted(todos - set(d['arquivos_de_rota_carregados']))
print('arquivos em routes/', len(todos), '| nao carregados', len(nao), nao)
