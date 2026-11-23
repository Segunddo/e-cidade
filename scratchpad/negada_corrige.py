#!/usr/bin/env python3
"""Passo 6c: aplica a guarda da forma NEGADA nos pontos medidos.

    $this->x != ""   ->   ($this->x != "" && $this->x !== 0 && $this->x !== 0.0)

So nos pares (classe, campo, metodo) da lista -- que devem ser os que o negada.php mostrou com o
MESMO valor 0 nos dois runtimes e resultado diferente -- e so DENTRO do metodo medido. A forma
com trim() nao e tocada (trim(0) e "0", seguro nos dois).

Uso: python3 scratchpad/negada_corrige.py <tsv: classe<TAB>campo<TAB>metodo, relativo a ecidade/>
Depois: python3 scratchpad/negada_alvos.py -> os pares corrigidos tem de sumir.

Usado no passo 6c do guia (docs/migrar-um-modulo.md), quando o negada_compara.py acusa
FORMA_NEGADA nas classes do lote.

Entrada: TSV com classe<TAB>campo<TAB>metodo (colunas extras sao ignoradas, entao linhas do
TSV do negada_alvos.py servem direto). O script faz chdir para ecidade/ ANTES de abrir o TSV:
caminho relativo do proprio TSV tambem e relativo a ecidade/ (ou use caminho absoluto).

Como faz, por arquivo: para cada par, localiza o metodo pelo nome (tem de haver exatamente uma
`function <metodo>(` no arquivo), delimita o corpo ate a proxima `function` (ou o fim do
arquivo), substitui ali toda forma negada daquele campo que ainda nao tenha a guarda e grava o
arquivo em bytes (preserva Latin-1 e finais de linha). Aborta com AssertionError se o metodo
nao existir/for ambiguo ou se nao houver ponto a corrigir -- arquivos ja gravados antes do
erro ficam gravados.
Saida: altera os arquivos de classes/ no lugar e imprime "arquivos: <n>  pontos: <k>".
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
        # recalculado a cada par: a substituicao anterior mudou o tamanho de b
        funs = [(m.start(), m.group(1).decode()) for m in RX_FUN.finditer(b)]
        ini = [p for p, n in funs if n == metodo]
        assert len(ini) == 1, (f, metodo, "metodo nao encontrado ou ambiguo")
        i = ini[0]
        fim = min([p for p, n in funs if p > i] or [len(b)])
        c = campo.encode()
        # casa `$this-><campo> != ""` (ou '') que:
        #   - nao esteja dentro de trim(  (lookbehind; a forma com trim() e segura);
        #   - nao seja seguido de `&& $this-><campo> !==`  (lookahead; ja guardado -- nao guarda
        #     duas vezes; mas um par ja todo corrigido da 0 substituicoes e o assert abaixo aborta).
        # O grupo 1 guarda as aspas originais para a substituicao reproduzi-las.
        # Nao ha \b depois do campo, mas `\s*!=` logo em seguida impede casar um campo mais longo.
        rx = re.compile(rb'(?<!trim\()\$this->' + c + rb'\s*!=\s*(["\']{2})(?!\s*&&\s*\$this->' + c + rb'\s*!==)')
        corpo, k = rx.subn(lambda m: b'($this->' + c + b' != ' + m.group(1) + b' && $this->' + c +
                           b' !== 0 && $this->' + c + b' !== 0.0)', b[i:fim])
        assert k >= 1, (f, campo, metodo, "forma negada sem guarda nao encontrada")
        b = b[:i] + corpo + b[fim:]
        tot += k
    open(f, "wb").write(b)
print(f"arquivos: {len(porarq)}  pontos: {tot}")
