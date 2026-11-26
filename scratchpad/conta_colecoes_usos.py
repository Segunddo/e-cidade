#!/usr/bin/env python3
# PHP8-62 (T-155): contagens citadas em docs/migracao-laravel/colecoes-str-arr.md (so leitura de codigo, fora de vendor/).
# Uso (raiz do repositorio):  python3 scratchpad/conta_colecoes_usos.py ecidade
import os, re, sys, collections
raiz = sys.argv[1]
PADROES = {
    'Str::': re.compile(r'\b(?:Illuminate\\Support\\)?Str::(\w+)\('),
    'Arr::': re.compile(r'\b(?:Illuminate\\Support\\)?Arr::(\w+)\('),
    'collect(': re.compile(r'(?<![\w>:$\\])collect\('),
    'tap(': re.compile(r'(?<![\w>:$\\])tap\('),
    'str_contains(': re.compile(r'(?<![\w>:$\\])str_contains\('),
    'sortBy/sortByDesc': re.compile(r'->(sortBy|sortByDesc)\('),
}
SORT = re.compile(r'(?<![\w>:$\\])(usort|uasort|uksort|sort|rsort|asort|arsort|ksort|krsort|array_multisort)\s*\(')
cont = collections.Counter(); metodos = collections.defaultdict(collections.Counter); sorts = collections.Counter()
for r, d, fs in os.walk(raiz):
    rel = os.path.relpath(r, raiz)
    if rel == 'vendor' or rel.startswith('vendor' + os.sep) or 'node_modules' in rel or rel.startswith(('dbagata', 'fpdf', 'ext', 'libs/jpgraph', 'tests', 'database')):
        d[:] = []
        continue
    for f in fs:
        if not f.endswith('.php'):
            continue
        try:
            s = open(os.path.join(r, f), encoding='latin-1').read()
        except OSError:
            continue
        for nome, p in PADROES.items():
            for m in p.finditer(s):
                cont[nome] += 1
                if m.groups():
                    metodos[nome][m.group(1)] += 1
        for m in SORT.finditer(s):
            sorts[m.group(1)] += 1
for nome in PADROES:
    print('%s %d %s' % (nome, cont[nome], dict(metodos[nome]) if metodos[nome] else ''))
print('funcoes de ordenacao do PHP (fora de dbagata/fpdf/ext/jpgraph/tests/database): %d %s' % (sum(sorts.values()), dict(sorts)))
