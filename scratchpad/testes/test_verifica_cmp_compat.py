#!/usr/bin/env python3
"""Teste: o verifica_lote.py funciona com as DUAS versoes do scratchpad/cmp.py.

Uso (da raiz do repo): python3 scratchpad/testes/test_verifica_cmp_compat.py   -> "OK" e codigo 0, ou AssertionError

A base tem um cmp.py que roda a bateria ao ser importado e marca a referencia com `56=`; a regressao-php74 (que o
PR #30 traz) tem outro, importavel, com regras_norm() e o rotulo `ref=`. O verifica_lote.py tem de:
  1. ler a normalizacao do cmp.py da base (lista NORM) sem importa-lo;
  2. reconhecer o timeout so na referencia com os dois rotulos (`56=000` e `ref=000`) como pre-existente.
Sem Docker: o sh() do script e trocado por um duble que devolve uma saida pronta do cmp.py.
"""
import argparse, os, sys, tempfile
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scratchpad"))
sys.argv = ["x"]
import verifica_lote as v

# 1. normalizacao do cmp.py da base (o que esta no disco deste repositorio, quando nao tem regras_norm)
CMP_BASE = '''import re, sys
SID = sys.argv[1]          # o cmp.py da base le os argumentos ao ser importado: nao pode ser importado
NORM = [
    (re.compile(rb'sid=[0-9a-f]{8,}'), b'sid=X'),
]
def norm(b):
    return b
'''
ler_original = v.ler
v.ler = lambda caminho: CMP_BASE if caminho.endswith("cmp.py") else ler_original(caminho)
n = v.normalizacao_do_cmp()
assert n(b"x sid=abcdef0123 y") == b"x sid=X y", "a normalizacao do cmp.py da base nao foi aplicada"
v.ler = ler_original

# 2. timeout so na referencia, com os dois rotulos
for rotulo in ("56", "ref"):
    saida = (f"2 telas\n\n  TIMEOUT a.php  {rotulo}=000  85=200  (nao conta como identica)\n\n"
             "=== 1/2 identicas, 0 divergentes, 1 timeout ===\n")
    def duble_sh(cmd, entrada=None, timeout=None, env=None, saida=saida):
        if cmd[0] == "curl":
            return 0, "5000", ""                 # prova de fumaca: sessao valida (> 1 KB)
        if len(cmd) > 1 and cmd[1] == "scratchpad/cmp.py":
            return 0, saida, ""
        return 0, "", ""
    v.sh = duble_sh
    v.diagnosticar = lambda telas, sid, p: []
    ctx = {"pasta": tempfile.mkdtemp(), "sid": "a" * 40,
           "telas": {"location": ["a.php", "b.php"], "map": [], "regex": "^(?:x)[0-9]*_"},
           "conhecidas": {"arquivo": "lista-de-teste", "nomes": set()}}
    res = v.passo_7(ctx, argparse.Namespace(prefixos=[], amostra=0, telas=None, lote="teste"))
    assert "Timeout so no 7.4" in res.detalhe and "a.php" in res.detalhe, \
        f"o timeout so na referencia com o rotulo {rotulo}= nao foi reconhecido como pre-existente"
    assert res.situacao == "OK", f"rotulo {rotulo}=: situacao {res.situacao}, deveria ser OK (timeout pre-existente)"
print("OK")
