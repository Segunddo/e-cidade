#!/usr/bin/env python3
# PHP8-62: contagens citadas em docs/migracao-laravel/laravel8-inicializacao.md (so leitura de codigo, fora de vendor/).
# Uso: python3 scratchpad/conta_laravel_init.py ecidade
import os, re, sys, collections
raiz = sys.argv[1]
env = collections.Counter(); envl = collections.Counter(); envf = collections.Counter(); cache = []
for r, d, fs in os.walk(raiz):
    rel = os.path.relpath(r, raiz)
    if rel == 'vendor' or rel.startswith('vendor' + os.sep):
        d[:] = []
        continue
    for f in fs:
        if not f.endswith('.php'):
            continue
        p = os.path.join(r, f)
        try:
            s = open(p, encoding='latin-1').read()
        except OSError:
            continue
        top = os.path.relpath(p, raiz).split(os.sep)[0] if os.sep in os.path.relpath(p, raiz) else '(raiz)'
        n = len(re.findall(r'(?<![\w>:$])env\(', s))
        if n:
            env[top] += n
            envl[top] += sum(1 for l in s.split('\n') if re.search(r'(?<![\w>:$])env\(', l))
            envf[top] += 1
        for m in re.finditer(r'Cache::put\(', s):
            cache.append('%s:%d' % (os.path.relpath(p, raiz), s.count('\n', 0, m.start()) + 1))
fora = [k for k in env if k != 'configuration']
print('env() fora de configuration: %d ocorrencias em %d linhas em %d arquivos' % (sum(env[k] for k in fora), sum(envl[k] for k in fora), sum(envf[k] for k in fora)))
print('env() em configuration: %d ocorrencias em %d linhas em %d arquivos' % (env['configuration'], envl['configuration'], envf['configuration']))
for k in sorted(fora, key=lambda k: -env[k]):
    print('  %s %d ocorrencias em %d linhas em %d arquivos' % (k, env[k], envl[k], envf[k]))
print('Cache::put: %d pontos' % len(cache))
for c in sorted(cache):
    print('  ' + c)
