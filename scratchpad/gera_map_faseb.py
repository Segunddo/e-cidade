#!/usr/bin/env python3
"""Gera docker/proxy/faseb_map.conf a partir do BANCO.

Fase B: os prefixos compartilhados (con, cai, cad, pro, pre, amb, prot, rec, dv)
servem varias areas. Medido tela a tela, 319 de 345 sao exclusivas de Tributario
e so 26 sao compartilhadas -- entao o roteamento e por LISTA EXATA, nao por prefixo.

Uso:  python3 scratchpad/gera_map_faseb.py <pref1> [pref2 ...]
      python3 scratchpad/gera_map_faseb.py amb pre
"""
import os, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFS = [p.lower() for p in sys.argv[1:]]
if not PREFS: sys.exit("informe ao menos um prefixo")

# Prefixos ja roteados por `location` (Fase A) -- ficam de fora do map.
FASE_A = "'cem','itb','itbi','agu','agua','jur','div','mar','not','fis','iss','dvr','arr','tri','inf','tra'"
# ATENCAO: `\\copy` e meta-comando do psql e tem de caber em UMA LINHA.
# Quebrado em varias, o psql falha -- e a mensagem de erro vem em LATIN-1, que
# o Python nao decodifica como UTF-8: o sintoma e um UnicodeDecodeError, nao um
# erro de SQL. Mesma familia da armadilha de encoding do resto do projeto.
SQL = ("\\copy (WITH ta AS ("
  "SELECT DISTINCT lower(di.funcao) AS tela, replace(a.at25_descr,'DB:','') AS area "
  "FROM configuracoes.atendcadareamod am "
  "JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea "
  "JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item "
  "JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item "
  "JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho "
  "WHERE di.funcao ~ '^[A-Za-z]+[0-9]*_.*\\.php$') "
  "SELECT DISTINCT tela FROM ta WHERE area LIKE 'TRIBUT%' "
  f"AND lower(substring(tela from '^[A-Za-z]+')) NOT IN ({FASE_A}) "
  "ORDER BY 1) TO '/tmp/faseb_all.txt'")

open("/tmp/_g.sql","w").write(SQL + "\n")
subprocess.run(["docker","cp","/tmp/_g.sql","ecidade_database:/tmp/_g.sql"],check=True,capture_output=True)
subprocess.run(["docker","exec","-i","ecidade_database","psql","-U","postgres","-d","ecidade",
                "-f","/tmp/_g.sql"],capture_output=True)
subprocess.run(["docker","cp","ecidade_database:/tmp/faseb_all.txt","/tmp/faseb_all.txt"],check=True,capture_output=True)

disco = {f.lower(): f for f in os.listdir(os.path.join(RAIZ,"ecidade"))
         if os.path.isfile(os.path.join(RAIZ,"ecidade",f))}
todas = [l.strip().lower() for l in open("/tmp/faseb_all.txt") if l.strip()]
lote  = [t for t in todas if t.startswith(tuple(PREFS))]

linhas, falta = [], []
for t in sorted(lote):
    if t not in disco: falta.append(t); continue
    # UMA grafia so, em minuscula. O `map` do nginx ja casa de forma INSENSIVEL a
    # caso -- descoberto porque emitir as duas grafias de cad4_emiteiptuNovo.php
    # fez o nginx recusar a config com "conflicting parameter". Ou seja: a
    # armadilha que obrigou o `location ~*` NAO se repete aqui, e tentar
    # prevenir-se dela quebra o proxy.
    linhas.append(f"    {t:46s} php85;")

cab = ("# GERADO de configuracoes.db_menu -- NAO editar a mao.\n"
       "# Reproduzir:  python3 scratchpad/gera_map_faseb.py " + " ".join(PREFS) + "\n#\n"
       "# Roteamento por LISTA EXATA: os prefixos da Fase B servem varias areas, e so\n"
       "# as telas que o banco atribui a Tributario vao para o 8.5.\n#\n"
       f"# Neste arquivo: {' + '.join(PREFS)} = {len(lote)} telas, {len(linhas)} entradas.\n\n")
open(os.path.join(RAIZ,"docker/proxy/faseb_map.conf"),"w").write(cab + "\n".join(linhas) + "\n")
print(f"  {len(lote)} telas, {len(linhas)} entradas"
      + (f"  | AUSENTES em disco: {falta}" if falta else "  | todas existem em disco"))
