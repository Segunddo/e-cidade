#!/usr/bin/env python3
"""PHP8-12 (T-128): compara duas saidas de php8_12_sem_token.php (7.4 x 8.5).
Uso: php8_12_sem_token_compara.py saida74.jsonl saida85.jsonl [tsv_de_diferencas]
Imprime contagens e escreve o TSV com uma linha por pedido que difere (status, content-type ou corpo)."""
import json, sys, collections

def le(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        if not l.startswith('{"rota"'):
            continue  # linha que nao e resultado (ex.: aviso do PHP escrito direto na saida do processo)
        r = json.loads(l)
        d[(r['rota'], r['metodo'], r['auth'], r['accept'])] = r
    return d

a, b = le(sys.argv[1]), le(sys.argv[2])
chaves = sorted(set(a) | set(b))
dif, cont = [], collections.Counter()
for k in chaves:
    x, y = a.get(k), b.get(k)
    if not x or not y:
        dif.append((k, 'so-em-' + ('7.4' if x else '8.5'), x or y, x or y)); cont['so-em-um'] += 1; continue
    ct = lambda r: r.get('cabecalhos', {}).get('content-type', '')
    cab = lambda r: json.dumps(r.get('cabecalhos', {}), sort_keys=True)
    if x['status'] != y['status']: m = 'status'
    elif x.get('corpo_md5') != y.get('corpo_md5') or x.get('corpo') != y.get('corpo'): m = 'corpo'
    elif cab(x) != cab(y): m = 'cabecalhos'
    elif x.get('tentou_banco') != y.get('tentou_banco'): m = 'tentou_banco'
    else: m = None
    cont['pedidos'] += 1
    cont['tentou_banco_74'] += 1 if x.get('tentou_banco') else 0
    cont['tentou_banco_85'] += 1 if y.get('tentou_banco') else 0
    if m: cont['difere_' + m] += 1; dif.append((k, m, x, y))
    else: cont['igual'] += 1
st = collections.Counter((x['status']) for x in a.values())
st2 = collections.Counter((x['status']) for x in b.values())
print('pedidos', cont['pedidos'], 'iguais', cont['igual'], {k: v for k, v in cont.items() if k.startswith('difere') or k == 'so-em-um'})
print('tentou_banco 7.4:', cont['tentou_banco_74'], '8.5:', cont['tentou_banco_85'])
print('status 7.4:', dict(st)); print('status 8.5:', dict(st2))
if len(sys.argv) > 3:
    with open(sys.argv[3], 'w', encoding='utf-8') as f:
        f.write('rota\tmetodo\turi\tauth\taccept\tmotivo\tstatus74\tstatus85\tcorpo74\tcorpo85\n')
        for k, m, x, y in dif:
            c = lambda r: (r.get('corpo') or '')[:300].replace('\t', ' ').replace('\n', ' ')
            f.write('\t'.join([str(k[0]), k[1], x['uri'], k[2], k[3], m, str(x['status']), str(y['status']), c(x), c(y)]) + '\n')
