# Compara dois JSON do laravel8_validacao_medir.php (e/ou do ..._matriz.php): lista cada caso diferente com a causa provavel.
# Uso: laravel13_validacao_compara.py <a.json> <b.json>   (A = referencia 7.4/Laravel 8; B = medido)
import json, sys, collections
a = json.load(open(sys.argv[1], encoding='utf-8')); b = json.load(open(sys.argv[2], encoding='utf-8'))
def resumo(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)
if 'casos' in a:
    dif = collections.defaultdict(list); total = 0
    for cl in sorted(a['casos']):
        for ent in sorted(a['casos'][cl]):
            total += 1
            ca, cb = a['casos'][cl][ent], b['casos'].get(cl, {}).get(ent)
            if resumo(ca) != resumo(cb):
                partes = []
                for k in ('passa', 'validado', 'excecao'):
                    if resumo(ca.get(k)) != resumo((cb or {}).get(k)):
                        partes.append(k)
                if resumo(ca.get('erros')) != resumo((cb or {}).get('erros')):
                    partes.append('erros')
                dif[tuple(partes)].append((cl, ent, ca, cb))
    print('casos', total, 'diferentes', sum(len(v) for v in dif.values()))
    for k, v in sorted(dif.items(), key=lambda kv: -len(kv[1])):
        print(' campos que mudam', k, len(v), 'casos,', len({c for c, _, _, _ in v}), 'classes')
        for cl, ent, ca, cb in v[:3]:
            print('    ', cl.split('\\')[-1], ent, '|', resumo(ca)[:140], '=>', resumo(cb)[:140])
    for k in ('classes', 'sem_regras', 'erro_ao_ler', 'regras_de_banco'):
        print(k, 'igual' if resumo(a.get(k)) == resumo(b.get(k)) else 'DIFERE')
    print('deprecations A', len(a['deprecations']), 'B', len(b['deprecations']))
else:
    n = d = 0
    for r in sorted(a):
        for v in sorted(a[r]):
            n += 1
            if resumo(a[r][v]) != resumo(b[r][v]):
                d += 1; print('  ', r, v, '|', resumo(a[r][v])[:120], '=>', resumo(b[r][v])[:120])
    print('combinacoes', n, 'diferentes', d)
