#!/bin/bash
# PHP8-51 (e-mail): renderiza os e-mails e notificacoes do PR com mailer array, sem banco e sem rede, no 7.4 e no 8.5.
# Uso: emails_roda.sh <ecidade> <vendor L8 p/ 7.4> <vendor L8 p/ 8.5> <vendor L13 p/ 8.5> <img 7.4> <img 8.5> <saida>
# (vendor L8 = composer install do ecidade/composer.lock do PR; vendor L13 = Laravel 13 isolado; so leitura; --network none)
set -u
E=$(realpath "$1"); V74=$(realpath "$2"); V85=$(realpath "$3"); V13=$(realpath "$4"); I74=$5; I85=$6; O=$(realpath -m "$7"); T=$(dirname "$(realpath "$0")")
mkdir -p "$O"
[ -d "$E/vendor" ] || { echo "ERRO: falta $E/vendor (ponto de montagem do vendor; crie a pasta vazia como o seu usuario antes)"; exit 1; }
r() {   # r <img> <vendor> <script args...>: aborta se o docker run falhar ou se a saida ficar vazia (senao o "igual" seria falso)
  local img=$1 ven=$2 saida=$3; shift 2
  docker run --rm --network none -u "$(id -u):$(id -g)" -v "$E:/e:ro" -v "$ven:/e/vendor:ro" -v "$T:/s:ro" -v "$O:/o" -w /e -e VENDOR=/e/vendor "$img" \
    php -d display_errors=1 -d error_reporting=E_ALL /s/emails_render.php /e "$@"
  local rc=$?
  [ $rc -eq 0 ] || { echo "ERRO: docker run ($img) saiu com $rc"; exit $rc; }
  [ -s "$O/$(basename "$saida")" ] || { echo "ERRO: saida vazia ou ausente: $saida"; exit 1; }
}
r "$I74" "$V74" /o/l8-74.json l8
r "$I85" "$V85" /o/l8-85.json l8
r "$I85" "$V13" /o/l13-85.json l13
for f in l8-74 l8-85 l13-85; do echo "$f: $(wc -c < "$O/$f.json") bytes"; done
