#!/usr/bin/env python3
"""Teste do rotear.py, modo abas: a lista faseb_map_abas.txt NUNCA pode ficar alterada quando nada foi aplicado.

Uso (da raiz do repo): python3 scratchpad/testes/test_rotear_abas.py      -> "OK" e codigo 0, ou AssertionError

Casos (todos sobre COPIAS temporarias de nginx.conf, faseb_map.conf e faseb_map_abas.txt; nada real e tocado,
nao precisa de Docker nem de banco):
  0. map SEM o comando do gerador na linha 2 (o estado da base-php74 no inicio): tem de recusar com mensagem
     clara (codigo 2) e sem deixar a lista alterada.
  1. --aplicar com o `nginx -t` falhando: o desfazer tem de devolver a lista ao original.
  2. --aplicar com "Nada a mudar" (a tela nova nao entra no map): a lista tem de ficar como estava.
  3. sem --aplicar (so mostrar): a lista tem de ficar como estava.
O gerador do map e o `nginx -t` sao substituidos por dubles: o que se testa e o vai-e-volta dos arquivos.
"""
import os, shutil, sys, tempfile
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scratchpad"))
sys.argv = ["x"]
import rotear as r

TELA = "teste_aba_inexistente_no_map.php"   # nome que nao esta na lista de abas

CABECALHO = "# GERADO de configuracoes.db_menu -- NAO editar a mao.\n# Reproduzir:  python3 scratchpad/gera_map_faseb.py teste:xyz\n#\n"

def prepara(com_comando=True):
    d = tempfile.mkdtemp()
    for nome in ("nginx.conf", "faseb_map.conf", "faseb_map_abas.txt"):
        shutil.copy(os.path.join(RAIZ, "docker", "proxy", nome), d)
    r.NGINX, r.MAP, r.ABAS = (os.path.join(d, n) for n in ("nginx.conf", "faseb_map.conf", "faseb_map_abas.txt"))
    eci = os.path.join(d, "ecidade"); os.mkdir(eci); open(os.path.join(eci, TELA), "w").close()
    r.ECIDADE = eci                          # a tela precisa "existir em ecidade/"
    if com_comando:                          # map ja gerado por um lote: linha 2 com o comando
        open(r.MAP, "w").write(CABECALHO + "    outra_tela.php    php85;\n")
    return {p: open(p).read() for p in (r.NGINX, r.MAP, r.ABAS)}

def roda(aplicar, entra_no_map=True, nginx_ok=False):
    # duble do gerador: le a lista de abas DO DISCO (como o gera_map_faseb.py) e poe no map o que estiver nela
    def regenerar(args):
        tem = TELA in open(r.ABAS).read()
        return open(r.MAP).read() + (f"    {TELA}    php85;\n" if (tem and entra_no_map) else "")
    r.regenerar_map = regenerar
    r.testar_nginx = lambda: (nginx_ok, "duble: nginx -t " + ("ok" if nginx_ok else "falhou"))
    try:
        r.modo_abas([TELA], aplicar)
    except SystemExit:
        pass

import contextlib, io
silencio = contextlib.redirect_stdout(io.StringIO())

orig = prepara(com_comando=False)
codigo = None
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    try:
        r.modo_abas([TELA], True)
    except SystemExit as e:
        codigo = e.code
assert codigo == 2, f"caso 0: map sem comando deveria recusar com codigo 2, saiu {codigo}"
assert open(r.ABAS).read() == orig[r.ABAS], "caso 0: map sem comando deixou a lista de abas alterada"

orig = prepara()
with silencio: roda(aplicar=True, nginx_ok=False)
assert open(r.ABAS).read() == orig[r.ABAS], "caso 1: nginx -t falhou e a lista de abas NAO voltou ao original"
assert open(r.MAP).read() == orig[r.MAP], "caso 1: o map nao voltou ao original"

orig = prepara()
with contextlib.redirect_stdout(io.StringIO()): roda(aplicar=True, entra_no_map=False)
assert open(r.ABAS).read() == orig[r.ABAS], "caso 2: 'Nada a mudar' com --aplicar deixou a lista de abas alterada"

orig = prepara()
with contextlib.redirect_stdout(io.StringIO()): roda(aplicar=False)
assert open(r.ABAS).read() == orig[r.ABAS], "caso 3: sem --aplicar a lista de abas ficou alterada"
print("OK")
