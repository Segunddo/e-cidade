#!/usr/bin/env python3
"""Gera docker/proxy/faseb_map.conf a partir do BANCO.

Fase B: os prefixos compartilhados (con, cai, cad, pro, pre, amb, prot, rec, dv)
servem varias areas. Medido tela a tela, 319 de 345 sao exclusivas de Tributario
e so 26 sao compartilhadas -- entao o roteamento e por LISTA EXATA, nao por prefixo.

Uso:  python3 scratchpad/gera_map_faseb.py <area>:<pref>[,<pref>...] [...]
      python3 scratchpad/gera_map_faseb.py tribut:amb,pre educa:mat,pro
<area> e o inicio do nome em atendcadarea, sem o "DB:" (TRIBUT, EDUCA...).
Cada prefixo so leva as telas que o banco atribui AQUELA area.

Mais as ABAS de docker/proxy/faseb_map_abas.txt: telas que nao estao no menu (o banco
nao as atribui a area nenhuma), mas que uma tela roteada ao 8.5 abre em iframe ou por
redirecionamento ao abrir. Sem elas o contêiner roda no 8.5 e o formulario no 7.4 (14a
lacuna). A lista sai de scratchpad/redirecionamentos.py, classe NO_7.4.

(A lista de prefixos compartilhados acima e da epoca da Fase B; cai, amb e rec foram
depois para o `location` -- ver FASE_A.)

Como faz: grava um \\copy em /tmp/_g.sql (no host), copia para o container do banco e roda
o psql, que exporta (tela, area) de todo o menu -- menos os prefixos ja no `location` --
para /tmp/faseb_all.txt no container; traz o arquivo de volta. Filtra as telas cujo prefixo
e area batem com algum <area>:<pref> pedido, soma as abas, descarta as que nao existem em
disco e REESCREVE o faseb_map.conf inteiro, com o proprio comando na linha 2.

Uso (da raiz do repo): o arquivo e reescrito do zero, entao os argumentos tem de incluir
TODOS os lotes ja roteados, nao so o novo. Pegue-os da linha 2 do faseb_map.conf atual e
acrescente o novo <area>:<pref> (o rotear.py faz isso). Depois recriar o proxy:
  docker compose -f docker-compose.proxy.yml up -d --force-recreate
Entradas: o banco, docker/proxy/faseb_map_abas.txt, a lista de ecidade/.
Saida: docker/proxy/faseb_map.conf (sobrescrito), /tmp/_g.sql e /tmp/faseb_all.txt no host
  e no container; imprime o total de telas, de entradas e as ausentes em disco.
Usado em: passo 8 do guia, roteamento por `map`, e depois do 8b ao acrescentar abas
  (chamado pelo rotear.py).
"""
import os, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# [(AREA em maiusculas, (pref, pref...))] a partir de "area:pref,pref"
LOTES = [(a.upper(), tuple(p.lower().split(","))) for a, p in (x.split(":", 1) for x in sys.argv[1:])]
if not LOTES: sys.exit("informe ao menos um <area>:<prefixos>")

# Prefixos ja roteados por `location` (Fase A) -- ficam de fora do map.
# LIDOS da linha `location` ATIVA do nginx.conf (por extenso: itbi? -> 'itb','itbi'). Era uma copia escrita a
# mao ("manter junto"); na base-php74 ela ficou com os 50 prefixos da base-php84 e as telas rec, cai, pes...
# nunca entravam no map. Sem linha ativa (inicio da base-php74), nenhum prefixo fica de fora.
import re
_loc = re.search(r"^[ \t]*location ~\* \^\(\?:/w/\[0-9\]\+\)\?/\(\?:\(\?:([^)]+)",
                 open(os.path.join(RAIZ, "docker/proxy/nginx.conf")).read(), re.M)
_pref = []
for _p in (_loc.group(1).split("|") if _loc else []):
    _pref += [_p[:-2], _p[:-1]] if _p.endswith("?") else [_p]
FASE_A = ",".join(f"'{p.lower()}'" for p in _pref) or "'nenhum_prefixo_no_85'"
# ATENCAO: `\\copy` e meta-comando do psql e tem de caber em UMA LINHA.
# Quebrado em varias, o psql falha -- e a mensagem de erro vem em LATIN-1, que
# o Python nao decodifica como UTF-8: o sintoma e um UnicodeDecodeError, nao um
# erro de SQL. Mesma familia da armadilha de encoding do resto do projeto.
SQL = ("\\copy (WITH ta AS ("
  "SELECT DISTINCT lower(split_part(di.funcao,'?',1)) AS tela, replace(a.at25_descr,'DB:','') AS area "
  "FROM configuracoes.atendcadareamod am "
  "JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea "
  "JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item "
  "JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item "
  "JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho "
  # 10a lacuna: o menu guarda telas COM parametro (`con1_manutexto.php?db_opcao=x`).
  # Sem o split_part o `\.php$` as excluia em silencio -- 13 telas de menu ficaram no 5.6.
  "WHERE split_part(di.funcao,'?',1) ~ '^[A-Za-z]+[0-9]*_.*\\.php$') "
  "SELECT DISTINCT tela, area FROM ta WHERE "
  f"lower(substring(tela from '^[A-Za-z]+')) NOT IN ({FASE_A}) "
  "ORDER BY 1) TO '/tmp/faseb_all.txt'")

# o \copy roda no CLIENTE psql, dentro do container: o arquivo de saida fica no /tmp de la.
# O retorno do psql nao e conferido: se ele falhar, um /tmp/faseb_all.txt antigo no container
# seria usado sem aviso.
open("/tmp/_g.sql","w").write(SQL + "\n")
subprocess.run(["docker","cp","/tmp/_g.sql","ecidade_database:/tmp/_g.sql"],check=True,capture_output=True)
subprocess.run(["docker","exec","-i","ecidade_database","psql","-U","postgres","-d","ecidade",
                "-f","/tmp/_g.sql"],capture_output=True)
subprocess.run(["docker","cp","ecidade_database:/tmp/faseb_all.txt","/tmp/faseb_all.txt"],check=True,capture_output=True)

# nome em minusculas -> grafia real (so para saber se existe; o map e emitido em minusculas)
disco = {f.lower(): f for f in os.listdir(os.path.join(RAIZ,"ecidade"))
         if os.path.isfile(os.path.join(RAIZ,"ecidade",f))}
pares = [l.rstrip("\n").split("\t") for l in open("/tmp/faseb_all.txt", encoding="latin1") if l.strip()]
# a tela entra se a area dela COMECA com a area pedida e o nome comeca com o prefixo
# (startswith: `pro` tambem pega `prot...`)
lote  = sorted({t for t, area in pares for a, pref in LOTES
                if area.upper().startswith(a) and t.startswith(pref)})

# 14a lacuna: abas e destinos de redirecionamento, que o menu nao lista
ABAS = os.path.join(RAIZ, "docker/proxy/faseb_map_abas.txt")
# uma tela por linha, `#` comenta; as que ja vieram do menu nao se repetem
abas = sorted({l.split("#")[0].strip().lower() for l in open(ABAS) if l.split("#")[0].strip()}
              - set(lote)) if os.path.exists(ABAS) else []
lote_menu = len(lote)
lote = lote + abas

linhas, falta = [], []
for t in lote:
    if t not in disco: falta.append(t); continue
    # UMA grafia so, em minuscula. O `map` do nginx ja casa de forma INSENSIVEL a
    # caso -- descoberto porque emitir as duas grafias de cad4_emiteiptuNovo.php
    # fez o nginx recusar a config com "conflicting parameter". Ou seja: a
    # armadilha que obrigou o `location ~*` NAO se repete aqui, e tentar
    # prevenir-se dela quebra o proxy.
    linhas.append(f"    {t:46s} php85;")

cab = ("# GERADO de configuracoes.db_menu -- NAO editar a mao.\n"
       "# Reproduzir:  python3 scratchpad/gera_map_faseb.py " + " ".join(sys.argv[1:]) + "\n#\n"
       "# Roteamento por LISTA EXATA: os prefixos da Fase B servem varias areas, e so\n"
       "# as telas que o banco atribui a area indicada vao para o 8.5.\n#\n"
       f"# Neste arquivo: {' '.join(sys.argv[1:])} = {lote_menu} telas de menu"
       f" + {len(abas)} abas de faseb_map_abas.txt = {len(linhas)} entradas.\n\n")
open(os.path.join(RAIZ,"docker/proxy/faseb_map.conf"),"w").write(cab + "\n".join(linhas) + "\n")
print(f"  {len(lote)} telas, {len(linhas)} entradas"
      + (f"  | AUSENTES em disco: {falta}" if falta else "  | todas existem em disco"))
