#!/usr/bin/env python3
"""Passo 6c: aplica a guarda da forma NEGADA nos pontos medidos.

    $this->x != ""   ->   ($this->x != "" && $this->x !== 0 && $this->x !== 0.0)

So nos pares (classe, campo, metodo) da lista -- que devem ser os que o negada.php mostrou com o
MESMO valor 0 nos dois runtimes e resultado diferente -- e so DENTRO do metodo medido. A forma
com trim() nao e tocada (trim(0) e "0", seguro nos dois).

Uso: python3 scratchpad/negada_corrige.py <tsv: classe<TAB>campo<TAB>metodo, relativo a ecidade/>
Depois: python3 scratchpad/negada_alvos.py -> os pares corrigidos tem de sumir.
"""
import os, re, sys, collections

os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
RX_FUN = re.compile(rb'function\s+(\w+)\s*\(')

porarq = collections.defaultdict(list)
for l in open(sys.argv[1]):
    if l.strip():
        f, campo, metodo = l.rstrip("\n").split("\t")[:3]
        porarq[f].append((campo, metodo))

tot = 0
for f, pares in porarq.items():
    b = open(f, "rb").read()
    for campo, metodo in pares:
        funs = [(m.start(), m.group(1).decode()) for m in RX_FUN.finditer(b)]
        ini = [p for p, n in funs if n == metodo]
        assert len(ini) == 1, (f, metodo, "metodo nao encontrado ou ambiguo")
        i = ini[0]
        fim = min([p for p, n in funs if p > i] or [len(b)])
        c = campo.encode()
        rx = re.compile(rb'(?<!trim\()\$this->' + c + rb'\s*!=\s*(["\']{2})(?!\s*&&\s*\$this->' + c + rb'\s*!==)')
        corpo, k = rx.subn(lambda m: b'($this->' + c + b' != ' + m.group(1) + b' && $this->' + c +
                           b' !== 0 && $this->' + c + b' !== 0.0)', b[i:fim])
        assert k >= 1, (f, campo, metodo, "forma negada sem guarda nao encontrada")
        b = b[:i] + corpo + b[fim:]
        tot += k
    open(f, "wb").write(b)
print(f"arquivos: {len(porarq)}  pontos: {tot}")
