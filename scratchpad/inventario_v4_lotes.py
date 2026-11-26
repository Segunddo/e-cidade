#!/usr/bin/env python3
"""Junta rotas (com middleware) e chamadas em: inventario-v4-rotas.tsv (uma linha por rota, com o uso) e inventario-v4-lotes.tsv (por area/modulo).
Uso: python3 scratchpad/inventario_v4_lotes.py <rotas.tsv> <rotas-uso.tsv> <chamadas.tsv> <saida-rotas.tsv> <saida-lotes.tsv>"""
import collections, sys

rotas_tsv, uso_tsv, ch_tsv, saida_ro, saida_lo = sys.argv[1:6]
mw = {}
for l in open(rotas_tsv, encoding='utf-8').read().split('\n')[1:]:
    if l:
        p = (l.split('\t') + [''] * 5)[:5]
        mw[(p[0], p[1])] = p[4]
uso = [l.split('\t') for l in open(uso_tsv, encoding='utf-8').read().split('\n')[1:] if l]


def lote(caminho):
    s = caminho.strip('/').split('/')
    if s[:2] == ['v4', 'api']:
        return '/'.join(s[2:4]) if len(s) > 3 else '/'.join(s[2:])
    return '/'.join(s[:2])


def situacao(f, p, b):
    if f > 0:
        return 'firme'
    if p > 0:
        return 'provavel'
    if b > 0:
        return 'so_base'
    return 'sem_chamador'


tipo_arq = {}
for l in open(ch_tsv, encoding='utf-8').read().split('\n')[1:]:
    if l:
        p = l.split('\t')
        tipo_arq[p[0]] = p[2]

with open(saida_ro, 'w', encoding='utf-8') as f:
    f.write('metodo\tcaminho\tcontroller\tmiddleware\torigem\tsituacao\tarquivos_chamadores\tarquivos_provaveis\tarquivos_so_pela_base\texemplos\n')
    for u in uso:
        mt, cam, ctrl, org, nf, nb, npv, ex = (u + [''] * 8)[:8]
        f.write('\t'.join([mt, cam, ctrl, mw.get((mt, cam), ''), org, situacao(int(nf), int(npv), int(nb)), nf, npv, nb, ex]) + '\n')

lotes = collections.defaultdict(lambda: {'rotas': 0, 'firme': 0, 'provavel': 0, 'so_base': 0, 'sem': 0, 'ext': 0, 'arq': set(), 'vue': set(), 'php': set(), 'js': set()})
for u in uso:
    mt, cam = u[0], u[1]
    if not cam.startswith('/v4/'):
        continue
    L = lotes[lote(cam)]
    L['rotas'] += 1
    s = situacao(int(u[4]), int(u[6]), int(u[5]))
    L[{'firme': 'firme', 'provavel': 'provavel', 'so_base': 'so_base', 'sem_chamador': 'sem'}[s]] += 1
    if s == 'sem_chamador' and 'clientCredential' in mw.get((mt, cam), ''):
        L['ext'] += 1
    for ref in u[7].split(' | '):
        arq = ref.rsplit(':', 1)[0]
        if arq:
            L['arq'].add(arq)
            t = tipo_arq.get(arq, '')
            (L['vue'] if t == 'vue' else L['js'] if t in ('js', 'extension') else L['php']).add(arq)
with open(saida_lo, 'w', encoding='utf-8') as f:
    f.write('lote\trotas\tcom_chamador_firme\tso_provavel\tso_pela_base\tsem_chamador\tdestas_com_clientCredential\tarquivos_chamadores\tvue\tjs\tphp_legado\n')
    for k, L in sorted(lotes.items(), key=lambda kv: (-len(kv[1]['arq']), -kv[1]['rotas'], kv[0])):
        f.write('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n' % (k, L['rotas'], L['firme'], L['provavel'], L['so_base'], L['sem'], L['ext'],
                                                                 len(L['arq']), len(L['vue']), len(L['js']), len(L['php'])))
