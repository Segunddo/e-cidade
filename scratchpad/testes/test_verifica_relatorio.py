#!/usr/bin/env python3
"""Teste do relatorio do passo 7 do verifica_lote.py (divergencias conhecidas x novas).

Uso (da raiz do repo): python3 scratchpad/testes/test_verifica_relatorio.py   -> "OK" e codigo 0, ou AssertionError

Simula uma bateria (sem Docker: o sh() do script e trocado por um duble que devolve uma saida pronta do cmp.py)
em que, com uma lista de divergencias conhecidas carregada e SEM nenhum timeout:
  - b.php diverge e esta na lista       -> "ja conhecida", nao conta como nova;
  - c.php esta na lista e saiu identica -> tem de aparecer em "Conhecidas que agora saem identicas";
  - o relatorio NAO pode dizer "Sem lista de divergencias conhecidas" (a lista esta carregada).
Pega o defeito de indentacao em que essas duas mensagens dependiam de haver timeout so no 7.4.
"""
import argparse, os, sys, tempfile
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scratchpad"))
sys.argv = ["x"]
import verifica_lote as v

SAIDA_CMP = ("3 telas\n\n  DIVERGE b.php  ref=200/10B  85=500/20B\n\n"
             "=== 2/3 identicas, 1 divergentes, 0 timeout ===\n")

def duble_sh(cmd, entrada=None, timeout=None, env=None):
    if cmd[0] == "curl":
        return 0, "5000", ""                 # prova de fumaca: sessao valida (> 1 KB)
    if len(cmd) > 1 and cmd[1] == "scratchpad/cmp.py":
        return 0, SAIDA_CMP, ""
    return 0, "", ""                         # docker exec cp ... (backup/restauro da sessao)
v.sh = duble_sh
v.diagnosticar = lambda telas, sid, p: []    # nao ha divergencia nova para diagnosticar

ctx = {"pasta": tempfile.mkdtemp(), "sid": "a" * 40,
       "telas": {"location": ["a.php", "b.php", "c.php"], "map": [], "regex": "^(?:x)[0-9]*_"},
       "conhecidas": {"arquivo": "lista-de-teste", "nomes": {"b.php", "c.php"}}}
args = argparse.Namespace(prefixos=[], amostra=0, telas=None, lote="teste")
res = v.passo_7(ctx, args)

assert res.situacao == "OK", f"situacao {res.situacao}: a unica divergencia e conhecida, deveria ser OK"
assert "Conhecidas que agora saem **identicas**" in res.detalhe and "c.php" in res.detalhe, \
    "c.php (conhecida que voltou identica) nao foi listada sem timeout no 7.4"
assert "Sem lista de divergencias conhecidas" not in res.detalhe, \
    "o relatorio diz que nao ha lista de conhecidas, mas ela esta carregada"
print("OK")
