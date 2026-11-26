# PHP8-51: inventario das filas do codigo do e-cidade, so por leitura (sem banco, sem PHP).
# Uso: python3 inventario_filas.py <ecidade> <inventario-8-a-13-ocorrencias.tsv> <saida-despachos.tsv> <saida-classes.tsv> [<saida do roda.sh>]
# - despachos: cada dispatch(, X::dispatch(, ->notify(, Queue::...->push*, com arquivo:linha, classe, fila e atraso
# - classes: cada classe ShouldQueue (implements com nome curto ou qualificado), onde e despachada e os itens do
#   inventario Laravel 8 -> 13 que citam o arquivo dela; com a saida do roda.sh, o resultado 7.4 x 8.5 de cada uma
import os, re, subprocess, sys
E_, OCOR, SAI_D, SAI_C = sys.argv[1:5]
RODA = sys.argv[5] if len(sys.argv) > 5 else None
def ler(a):
    return open(os.path.join(E_, a), encoding='latin-1').read().split('\n')
arqs = subprocess.run(['git', '-C', E_, 'ls-files', '*.php'], capture_output=True, text=True).stdout.split()
arqs = [a for a in arqs if not a.startswith(('vendor/', 'tmp/'))]
PAD = re.compile(r'(?:(?<![\w>$])dispatch\s*\(|(\w+)::dispatch\s*\(|->notify\s*\(|Queue::connection\([^)]*\)->(push\w*)\s*\()')
classes = {}
for a in arqs:
    if not a.startswith('app/'): continue
    t = '\n'.join(ler(a))
    if re.search(r'class\s+\w+[^{;]*implements[^{;]*ShouldQueue', t):
        classes[re.search(r'class\s+(\w+)', t).group(1)] = a
desp = []
for a in arqs:
    ls = ler(a)
    for i, l in enumerate(ls):
        if re.match(r'\s*(//|\*|#|/\*)', l): continue
        m = PAD.search(l)
        if not m: continue
        trecho = ' '.join(ls[i:i + 8])
        if m.group(2): forma, alvo = 'Queue::connection()->' + m.group(2), '(payload guardado)'
        elif m.group(1): forma, alvo = '::dispatch', m.group(1)
        elif '->notify' in m.group(0): forma = '->notify'; n = re.search(r'new\s+(\w+)', trecho); alvo = n.group(1) if n else '?'
        else:
            forma = 'dispatch()'; n = re.search(r'dispatch\s*\(\s*\(?\s*new\s+(\w+)', trecho)
            if n: alvo = n.group(1)
            else:
                v = re.search(r'dispatch\s*\(\s*(\$\w+)', l)
                alvo = '?'
                if v:
                    for j in range(i, max(-1, i - 15), -1):
                        n = re.search(re.escape(v.group(1)) + r'\s*=\s*new\s+(\w+)', ls[j])
                        if n: alvo = n.group(1); break
        fim = ' '.join(ls[i:i + 12]).split(';')[0]
        fila = re.search(r'->onQueue\(([^)]*)\)', fim); con = re.search(r'->onConnection\(([^)]*)\)', fim)
        atraso = 'sim' if re.search(r'->delay\(', ' '.join(ls[max(0, i - 3):i + 1]) + fim) else ''
        vai = 'fila' if alvo in classes else ('na hora (nao e ShouldQueue)' if alvo not in ('?', '(payload guardado)') else 'fila (reenvio)')
        desp.append((f'{a}:{i + 1}', forma, alvo, fila.group(1) if fila else '', con.group(1) if con else '', atraso, vai))
with open(SAI_D, 'w') as f:
    f.write('arquivo:linha\tforma\tclasse\tfila (onQueue)\tconexao (onConnection)\tatraso\tvai para\n')
    for d in desp: f.write('\t'.join(d) + '\n')
itens = {}
for l in open(OCOR, encoding='utf-8').read().split('\n')[1:]:
    c = l.split('\t')
    if len(c) == 4: itens.setdefault(c[3].split(':')[0], set()).add(f'{c[0]} {c[1]}')
def blocos(arq):   # '== Classe' -> linhas do bloco
    r, k = {}, None
    for l in open(arq, encoding='latin-1').read().split('\n'):
        if l.startswith('== '): k = l[3:].strip(); r[k] = []
        elif k: r[k].append(l)
    return r
res = {}
if RODA:
    j74, j85 = blocos(f'{RODA}/jobs74.txt'), blocos(f'{RODA}/jobs85.txt')
    cz = [blocos(f'{RODA}/cruzado_{a}_lido_no_{b}.txt') for a in (74, 85) for b in (74, 85)]
    for k in j74:
        sem = lambda b: [l for l in b if not l.startswith('command:')]
        cmd = lambda b: [l for l in b if l.startswith('command:')]
        p = 'igual' if sem(j74[k]) == sem(j85.get(k, [])) else 'DIFERE'
        c74, c85 = cmd(j74[k]), cmd(j85.get(k, []))
        if c74 == c85: c = 'igual'
        elif c74 and c85 and sorted(re.split(r'[;{}]', c74[0])) == sorted(re.split(r'[;{}]', c85[0])): c = 'mesmas partes, outra ordem'
        else: c = 'DIFERE'
        e = 'igual nas 4' if all(x.get(k) == cz[0].get(k) for x in cz) and cz[0].get(k) else 'DIFERE'
        res[k] = f'payload {p}; command {c}; estado cruzado {e}'
with open(SAI_C, 'w') as f:
    f.write('classe\tarquivo\tdespachada em\titens do inventario 8 -> 13 no arquivo' + ('\tresultado 7.4 x 8.5' if RODA else '') + '\n')
    for c in sorted(classes, key=lambda k: classes[k]):
        onde = ' '.join(d[0] for d in desp if d[2] == c)
        fq = 'App\\' + classes[c][4:-4].replace('/', '\\')
        f.write(f'{c}\t{classes[c]}\t{onde or "(nenhum ponto no codigo)"}\t{"; ".join(sorted(itens.get(classes[c], [])))}'
                + (f'\t{res.get(fq, "SEM MEDIDA")}' if RODA else '') + '\n')
print(f'classes ShouldQueue: {len(classes)}; pontos de despacho: {len(desp)} '
      f'(fila: {sum(1 for d in desp if d[6].startswith("fila"))}, na hora: {sum(1 for d in desp if d[6].startswith("na hora"))})')
