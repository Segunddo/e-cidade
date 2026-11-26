#!/usr/bin/env python3
# PHP8-55: troca $dates por $casts ('datetime') nos models de app/ (so arquivos com $dates). Uso: troca.py <ecidade> [--dry]
import os, re, sys
raiz = sys.argv[1]; dry = '--dry' in sys.argv
DEC = re.compile(r'^([ \t]*)(protected|public)\s+\$dates\s*=\s*\[(.*?)\]\s*;[ \t]*\r?\n(?:[ \t]*\r?\n)?', re.S | re.M)
CAS = re.compile(r'^([ \t]*)(protected|public)\s+\$casts\s*=\s*\[(.*?)\](\s*;)', re.S | re.M)
Q = re.compile(r'''(['"])([^'"]+)\1''')
n = 0
for r, d, fs in os.walk(os.path.join(raiz, 'app')):
    for f in sorted(fs):
        if not f.endswith('.php'):
            continue
        p = os.path.join(r, f)
        s = open(p, 'rb').read().decode('latin-1')
        m = DEC.search(s)
        if not m:
            continue
        ind, vis, corpo = m.group(1), m.group(2), m.group(3)
        attrs = [(x.group(1), x.group(2)) for x in Q.finditer(corpo)]
        eol = '\r\n' if '\r\n' in s else '\n'
        c = CAS.search(s)
        if c:
            existentes = set(re.findall(r'''['"]([^'"]+)['"]\s*=>''', c.group(3)))
            novos = [(q, a) for q, a in attrs if a not in existentes]
            s = s[:m.start()] + s[m.end():]
            c = CAS.search(s)
            cb = c.group(3)
            if novos:
                if '\n' in cb:
                    rs = cb.rstrip()
                    ind_item = re.match(r'[ \t]*', rs.split('\n')[-1]).group(0)
                    if not rs.endswith(','):
                        rs += ','
                    add = ''.join('%s%s%s%s%s => %sdatetime%s,' % (eol, ind_item, q, a, q, q, q) for q, a in novos)
                    nb = rs + add + cb[len(cb.rstrip()):]
                else:
                    t = cb.rstrip()
                    nb = t + (',' if t and not t.endswith(',') else '') + ' ' + ', '.join('%s%s%s => %sdatetime%s' % (q, a, q, q, q) for q, a in novos) + cb[len(t):]
                s = s[:c.start(3)] + nb + s[c.end(3):]
        else:
            nb = Q.sub(lambda x: '%s%s%s => %sdatetime%s' % (x.group(1), x.group(2), x.group(1), x.group(1), x.group(1)), corpo)
            tail = s[m.start():m.end()]
            blank = tail[len(tail.rstrip('\r\n \t')):] if False else ''
            s = s[:m.start()] + '%s%s $casts = [%s];%s' % (ind, vis, nb, eol) + (eol if m.group(0).rstrip('\r\n \t') != m.group(0).rstrip(' \t').rstrip('\r\n') or re.search(r'\n[ \t]*\r?\n$', m.group(0)) else '') + s[m.end():]
        n += 1
        print(('DRY ' if dry else '') + os.path.relpath(p, raiz))
        if not dry:
            open(p, 'wb').write(s.encode('latin-1'))
print(n, 'arquivos')
