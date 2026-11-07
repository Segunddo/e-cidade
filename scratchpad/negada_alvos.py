#!/usr/bin/env python3
"""Forma NEGADA do 0 == "": `$this->X != ""` com X inteiro e SEM trim(), nas classes de dados.

O GuardaComparacaoLiteralRector so trata `==`. Para cada ocorrencia da forma negada, este
script anota o metodo onde ela esta e o atualizacampos() que vem antes dela NO MESMO metodo:
  false  -> atualizacampos() / atualizacampos(false): le todos os campos do POST
  true   -> atualizacampos(true): modo exclusao, le so a chave
  sem    -> nenhum: a propriedade chega com o valor que tiver (o padrao e o inteiro 0)
e se a comparacao decide AUDITORIA (db_acount logo adiante) ou SQL de NEGOCIO.

Saida (TSV): classe  campo  metodo  modo  tipo   -- entrada do scratchpad/negada.php
Uso: python3 scratchpad/negada_alvos.py <saida.tsv>
"""
import os, re, sys

os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
RX_INT = re.compile(rb'(?:var|public)\s+\$(\w+)\s*=\s*-?\d+(?:\.\d+)?\s*;')
RX_NEG = re.compile(rb'(?<!trim\()\$this->(\w+)\s*!=\s*["\']{2}')
RX_FUN = re.compile(rb'function\s+(\w+)\s*\(')
RX_ATU = re.compile(rb'\$this->atualizacampos\s*\(\s*(true|false)?\s*\)', re.I)

linhas = set()
for f in sorted(os.listdir("classes")):
    if not f.endswith(".php"): continue
    b = open("classes/" + f, "rb").read()
    ints = {m.group(1) for m in RX_INT.finditer(b)}
    funs = [(m.start(), m.group(1).decode()) for m in RX_FUN.finditer(b)]
    for m in RX_NEG.finditer(b):
        if m.group(1) not in ints: continue
        # ja guardada: ($this->X != "" && $this->X !== 0 && $this->X !== 0.0) -- a guarda
        # contem a propria forma negada, e sem isto o detector nunca daria zero
        if re.match(rb'\s*&&\s*\$this->' + re.escape(m.group(1)) + rb'\s*!==\s*0\b', b[m.end():m.end() + 80]): continue
        ini, metodo = max(((p, n) for p, n in funs if p < m.start()), default=(0, "?"))
        atu = [x.group(1) for x in RX_ATU.finditer(b, ini, m.start())]
        modo = "sem" if not atu else ("true" if (atu[-1] or b"").lower() == b"true" else "false")
        tipo = "auditoria" if b"db_acount" in b[m.end():m.end() + 260] else "negocio"
        linhas.add(("classes/" + f, m.group(1).decode(), metodo, modo, tipo))

open(sys.argv[1], "w").write("".join("\t".join(l) + "\n" for l in sorted(linhas)))
print(f"{len(linhas)} pares (classe, campo, metodo) distintos")
