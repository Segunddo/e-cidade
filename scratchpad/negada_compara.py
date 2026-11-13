#!/usr/bin/env python3
"""Passo 6c: compara a saida do negada.php nos dois runtimes e da o veredito DO LOTE.

Uso (da raiz do repo):
  python3 scratchpad/negada_compara.py /tmp/neg_56.txt /tmp/neg_85.txt /tmp/cls.txt

O terceiro argumento e a lista de classes do lote (a /tmp/cls.txt do passo 6). O negada_alvos.py varre
TODAS as classes de classes/, entao a comparacao traz tambem classes de areas ainda nao migradas, que o
5.6 serve e que nao sao problema do lote. Este script separa as duas coisas.

Classifica cada par (classe, campo, metodo) que difere:
  VALOR_DIFERENTE  5.6 NULL, 8.5 0: falta a guarda do == no atualizacampos() -- a classe nao foi portada
  FORMA_NEGADA     mesmo valor 0, `!= ""` decide diferente: corrigir com scratchpad/negada_corrige.py
  ERRO             <ERRO>/<SEM_CLASSE> de um lado so
  SO_DE_UM_LADO    o par so aparece num runtime (o processo morreu?)
"""
import collections, sys

if len(sys.argv) != 4:
    sys.exit(__doc__)

def ler(p):
    d = {}
    for l in open(p, encoding="latin-1"):
        c = l.rstrip("\n").split("\t")
        if len(c) >= 6:                       # linhas de alert()/lixo do harness nao tem 6 colunas
            d[tuple(c[:3])] = c[5:]
    return d

a, b = ler(sys.argv[1]), ler(sys.argv[2])
lote = {l.strip() for l in open(sys.argv[3]) if l.strip()}

dif = []
for k in sorted(set(a) | set(b)):
    va, vb = a.get(k), b.get(k)
    if va == vb:
        continue
    if va is None or vb is None:
        tipo = "SO_DE_UM_LADO"
    elif any(x in ("<ERRO>", "<SEM_CLASSE>") for x in va + vb):
        tipo = "ERRO"
    elif va[0] != vb[0]:
        tipo = "VALOR_DIFERENTE"
    else:
        tipo = "FORMA_NEGADA"
    dif.append((tipo, k, va, vb))

print(f"pares medidos: 5.6={len(a)}  8.5={len(b)}" + ("" if len(a) == len(b) else "   <-- DIFEREM: um runtime parou no meio?"))
print(f"classes do lote: {len(lote)}")

dentro = [d for d in dif if d[1][0] in lote]
fora = [d for d in dif if d[1][0] not in lote]

print(f"\n== FORA DO LOTE: {len(fora)} pares em {len({d[1][0] for d in fora})} classes "
      "(areas nao migradas ou classes que o lote nao usa -- nao corrigir aqui)")
for t, n in collections.Counter(d[0] for d in fora).most_common():
    print(f"   {n:5d}  {t}")

print(f"\n== DO LOTE: {len(dentro)} pares")
for t, k, va, vb in dentro:
    print(f"   {t:16} {k[0]}  {k[1]}  {k[2]}   5.6={'/'.join(va)}  8.5={'/'.join(vb)}")

if len(a) != len(b):
    print("\nVEREDITO: INCOMPLETO -- os dois runtimes nao mediram o mesmo numero de pares; rode de novo")
elif not dentro:
    print("\nVEREDITO: PASSOU -- nenhuma divergencia nas classes do lote")
else:
    print("\nVEREDITO: INVESTIGAR -- FORMA_NEGADA: corrigir com negada_corrige.py; "
          "VALOR_DIFERENTE: a classe do lote ficou sem a guarda do == (falha do passo 4)")
