#!/usr/bin/env bash
# NIVEL 3 de verificacao: POST real nos dois runtimes, comparando o SQL que cada
# um grava no banco.
#
# Uso:
#   scratchpad/demo_nivel3.sh                        demonstracao completa (ver abaixo)
#   scratchpad/demo_nivel3.sh <tela.php> <tabelas>   compara UMA tela qualquer
#       <tabelas>: as tabelas que a tela grava, separadas por virgula
#       ex.: scratchpad/demo_nivel3.sh jur1_advog001.php advog
#   SID=<id> scratchpad/demo_nivel3.sh ...           usa uma sessao especifica
#
# Demonstracao (sem argumentos), na tela onde o defeito `0 == ""` foi descoberto
# (Cemiterio -> Tipos de isencao -> Inclusao). Tres rodadas:
#   1. codigo migrado             -> esperado: IDENTICO
#   2. correcao desfeita (temp.)  -> esperado: DIVERGE  (o teste PEGA o defeito)
#   3. correcao restaurada        -> esperado: IDENTICO
#
# Resultados de uma tela qualquer:
#   IDENTICO      os dois runtimes gravaram o mesmo SQL de negocio
#   DIVERGE       gravaram SQL diferente -- investigar
#   INCONCLUSIVO  nada foi gravado: o formulario montado automaticamente nao passou
#                 na validacao da tela (acontece em ~1/3 das telas); montar a mao
#   ABORTADO      o banco recusou repor a tabela porque outra a referencia (chave
#                 estrangeira) -- trava de seguranca: o teste para ANTES de enviar
#                 o formulario e nada e alterado. Acrescentar a tabela filha citada
#                 na mensagem ao 2o argumento (filha primeiro), ou escolher outra tela
#
# Exige o ambiente no ar (5.6, 8.5 e banco). Nao altera nada de forma permanente:
# as tabelas sao restauradas a cada rodada, a classe volta ao estado do git e o
# log_statement do banco e desligado no fim, mesmo se algo falhar no meio.
set -u
cd "$(dirname "$0")/.."

DB="docker exec -i ecidade_database psql -U postgres -d ecidade"

for c in ecidade_database ecidade_php56 ecidade_php85; do
  docker ps --format '{{.Names}}' | grep -qx "$c" || { echo "container $c parado -- suba o ambiente (ver CLAUDE.md)"; exit 1; }
done

if [ $# -eq 0 ]; then
  MODO=demo
  TELA=cem1_cemiterioisencao001.php
  TABELA=cemiterioisencao
  CLASSE=ecidade/classes/db_cemiterioisencao_classe.php
  # a rodada 2 edita a classe e a devolve com `git checkout`: nao pode haver alteracao local nela
  git diff --quiet -- "$CLASSE" || { echo "$CLASSE tem alteracao local -- commite ou descarte antes"; exit 1; }
elif [ $# -eq 2 ]; then
  MODO=tela
  TELA=$1
  TABELA=$2
  [ -f "ecidade/$TELA" ] || { echo "tela ecidade/$TELA nao existe"; exit 1; }
else
  echo "uso: $0 [<tela.php> <tabelas,separadas,por,virgula>]"; exit 1
fi

SID=${SID:-$(docker exec ecidade_php56 sh -c 'ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_*) 2>/dev/null | head -1' | sed 's#.*/sess_##')}
[ -n "$SID" ] || { echo "nenhuma sessao autenticada encontrada -- faca login em http://localhost:8080"; exit 1; }

limpar() {
  [ "$MODO" = demo ] && git checkout -q -- "$CLASSE"
  $DB -qc "ALTER DATABASE ecidade RESET log_statement;" </dev/null >/dev/null
}
trap limpar EXIT
$DB -qc "ALTER DATABASE ecidade SET log_statement='all';" </dev/null >/dev/null

# o formulario e montado a partir da tela que o proprio 5.6 emite
P=$(python3 scratchpad/payload_auto.py "$SID" "$TELA" </dev/null)
[ -n "$P" ] || { echo "nao foi possivel montar o formulario de $TELA (a tela tem <form>?)"; exit 2; }
echo "Formulario enviado: $P"

if [ "$MODO" = tela ]; then
  echo
  python3 scratchpad/escrita_post.py "$SID" "$TELA" "$TABELA" "$P"
  rc=$?
  for t in ${TABELA//,/ }; do
    echo "Tabela $t depois do teste: $($DB -tAc "select count(*) from $t" </dev/null) linhas"
  done
  exit $rc
fi

rodada() {
  echo; echo "=== $1 ==="
  sleep 3   # o opcache do 8.5 revalida a cada 2 s
  python3 scratchpad/escrita_post.py "$SID" "$TELA" "$TABELA" "$P" | tail -4
}

rodada "1. codigo migrado (esperado: IDENTICO)"

python3 - "$CLASSE" <<'EOF'
import sys
p = sys.argv[1]; b = open(p, 'rb').read()   # arquivo LATIN-1: editar em bytes
guarda = b'($this->cm34_tipo === 0 || $this->cm34_tipo === 0.0 || $this->cm34_tipo == "")'
assert b.count(guarda) == 1, "guarda nao encontrada"
open(p, 'wb').write(b.replace(guarda, b'$this->cm34_tipo == ""'))
EOF
rodada "2. correcao desfeita temporariamente (esperado: DIVERGE)"

git checkout -q -- "$CLASSE"
rodada "3. correcao restaurada (esperado: IDENTICO)"

echo; echo "Tabela $TABELA depois da demonstracao: $($DB -tAc "select count(*) from $TABELA" </dev/null) linhas (nada gravado pelo teste)"
