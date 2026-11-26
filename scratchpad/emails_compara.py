# Compara os JSON do emails_render.php: tira php/laravel/deprecations e mostra diff. Uso: emails_compara.py a.json b.json
import json, sys, difflib
def carrega(f):
    d = json.load(open(f, encoding='utf-8'))
    dep = d.pop('deprecations', [])
    meta = (d.pop('php'), d.pop('laravel'))
    return json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True).splitlines(), dep, meta
a, da, ma = carrega(sys.argv[1]); b, db, mb = carrega(sys.argv[2])
print('A: php %s laravel %s, %d deprecations | B: php %s laravel %s, %d deprecations' % (ma + (len(da),) + mb + (len(db),)))
dif = list(difflib.unified_diff(a, b, 'A', 'B', n=0, lineterm=''))
print('IGUAL' if not dif else 'DIFERE (%d linhas):' % len(dif))
for l in dif:
    print(l[:300])
