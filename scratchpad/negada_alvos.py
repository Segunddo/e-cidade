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

Usado no passo 6c do guia (docs/migrar-um-modulo.md), antes do negada.php, e de novo depois
do negada_corrige.py (os pontos corrigidos tem de sumir).

Como faz (analise estatica, sobre os bytes -- a base e em parte Latin-1):
  1. varre TODOS os .php de ecidade/classes/ (nao so os do lote);
  2. em cada um, anota as propriedades declaradas com valor inicial numerico (o padrao 0);
  3. para cada `$this->X != ""` sem trim() e com X numerica, que ainda nao tenha a guarda,
     acha o metodo que a contem (a ultima `function` antes dela), o modo do ultimo
     atualizacampos() entre o inicio desse metodo e a comparacao, e o tipo.
ATENCAO: o script faz chdir para ecidade/, entao <saida.tsv> relativo e relativo a ecidade/
(o guia usa tmp/negada.tsv = ecidade/tmp/negada.tsv). A coluna classe sai como classes/<arquivo>.
Imprime no fim "<n> pares (classe, campo, metodo) distintos" (linhas distintas do TSV).
"""
import os, re, sys

os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
# propriedade com inicializador numerico: `var $x = 0;`, `public $x = -1;`, `var $x = 0.5;`
RX_INT = re.compile(rb'(?:var|public)\s+\$(\w+)\s*=\s*-?\d+(?:\.\d+)?\s*;')
# a forma negada: `$this->x != ""` ou `!= ''` (duas aspas seguidas = string vazia);
# o lookbehind descarta `trim($this->x != ...`, i.e. a forma com trim(), que e segura
RX_NEG = re.compile(rb'(?<!trim\()\$this->(\w+)\s*!=\s*["\']{2}')
# inicio de cada declaracao de funcao/metodo, para saber em qual metodo cai a comparacao
RX_FUN = re.compile(rb'function\s+(\w+)\s*\(')
# chamada ao atualizacampos(), com argumento true/false opcional (grupo 1 = None se vazio)
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
        # metodo = a ultima `function` que comeca antes da comparacao ("?" se nenhuma)
        ini, metodo = max(((p, n) for p, n in funs if p < m.start()), default=(0, "?"))
        # vale o ULTIMO atualizacampos() entre o inicio do metodo e a comparacao;
        # sem argumento (None) conta como false
        atu = [x.group(1) for x in RX_ATU.finditer(b, ini, m.start())]
        modo = "sem" if not atu else ("true" if (atu[-1] or b"").lower() == b"true" else "false")
        # heuristica: a palavra db_acount nos 260 bytes seguintes = bloco de auditoria
        tipo = "auditoria" if b"db_acount" in b[m.end():m.end() + 260] else "negocio"
        linhas.add(("classes/" + f, m.group(1).decode(), metodo, modo, tipo))

open(sys.argv[1], "w").write("".join("\t".join(l) + "\n" for l in sorted(linhas)))
print(f"{len(linhas)} pares (classe, campo, metodo) distintos")
