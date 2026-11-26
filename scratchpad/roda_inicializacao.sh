#!/bin/bash
# PHP8-62: roda scratchpad/laravel_init.php no 7.4 (vendor do PR) e no 8.5 (vendor do 8.5 da integracao), SEM banco, nas imagens do projeto
# (docker/php74-apache e docker/php85-apache, com o php.ini delas), --network none, e compara as saidas.
# Do zero, na raiz do repositorio:   bash scratchpad/roda_inicializacao.sh [pasta-de-trabalho]
# Pre-requisito: vendor do 8.5 em runtime-85/vendor (bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+).
# - 7.4: vendor do PR (composer install da composer.lock numa pasta de trabalho + dump-autoload com o composer.json real), montado em /w/ecidade/vendor;
# - config/ so com os arquivos versionados (git archive), sem config/application.php local; .env vazio se houver um local;
# - chaves do Passport geradas na hora (openssl), so para o teste; storage/cache gravaveis em pasta nova;
# - sai com erro se o docker run falhar ou a saida vier vazia.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d /tmp/t123-XXXXXX)}"; mkdir -p "$W"
SCRIPT="${SCRIPT:-/s/laravel_init.php}"
test -f "$R/runtime-85/vendor/autoload.php" || { echo "falta runtime-85/vendor (bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+)" >&2; exit 1; }
# imagens do projeto
docker image inspect t123-proj-php74 >/dev/null 2>&1 || docker build -q -t t123-proj-php74 "$R/docker/php74-apache" >/dev/null
docker image inspect t123-proj-php85 >/dev/null 2>&1 || docker build -q -t t123-proj-php85 "$R/docker/php85-apache" >/dev/null
# vendor do PR com autoload completo
if [ ! -f "$W/prvendor/vendor/autoload.php" ]; then
  mkdir -p "$W/prlock"; cp "$R/ecidade/composer.json" "$R/ecidade/composer.lock" "$W/prlock/"
  python3 - "$W/prlock/composer.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1])); d.pop('scripts', None); d.pop('autoload', None); d.pop('autoload-dev', None)
json.dump(d, open(sys.argv[1], 'w'), indent=1)
PY
  docker run --rm -u "$(id -u):$(id -g)" -e COMPOSER_HOME=/tmp/ch -v "$W/prlock:/pr" -w /pr composer:2 composer install --no-scripts --no-interaction --ignore-platform-reqs --no-progress --no-autoloader >/dev/null
  mkdir -p "$W/prvendor"; mv "$W/prlock/vendor" "$W/prvendor/vendor"
  docker run --rm -u "$(id -u):$(id -g)" -e COMPOSER_HOME=/tmp/ch -v "$R/ecidade:/app:ro" -v "$W/prvendor/vendor:/app/vendor" -w /app composer:2 composer dump-autoload --no-scripts --no-interaction >/dev/null
fi
# config/ versionado, chaves de teste
mkdir -p "$W/cfg"; (cd "$R" && git archive HEAD ecidade/config | tar -x -C "$W/cfg")
mkdir -p "$W/keys"; [ -f "$W/keys/oauth-private.key" ] || { openssl genrsa -out "$W/keys/oauth-private.key" 2048 2>/dev/null; openssl rsa -in "$W/keys/oauth-private.key" -pubout -out "$W/keys/oauth-public.key" 2>/dev/null; }
ENVMNT=(); if [ -e "$R/ecidade/.env" ]; then : > "$W/env.vazio"; ENVMNT=(-v "$W/env.vazio:/w/ecidade/.env:ro"); fi
mkdir -p "$R/ecidade/vendor"   # ponto de montagem do vendor (o composer-85.sh tambem o cria)
for v in 7.4 8.5; do
  if [ "$v" = 7.4 ]; then VEND="$W/prvendor/vendor"; else VEND="$R/runtime-85/vendor"; fi
  S="$W/run-$v"; mkdir -p "$S/storage/logs" "$S/storage/framework/cache" "$S/storage/framework/sessions" "$S/storage/framework/views" "$S/bcache" "$S/tmp" "$S/arquivos"
  cp "$W/keys"/oauth-*.key "$S/storage/"; chmod -R 777 "$S"
  docker run --rm --network none -u "$(id -u):$(id -g)" -w /w/ecidade \
    -v "$R/ecidade:/w/ecidade:ro" "${ENVMNT[@]}" -v "$W/cfg/ecidade/config:/w/ecidade/config:ro" -v "$VEND:/w/ecidade/vendor:ro" \
    -v "$S/storage:/w/ecidade/storage" -v "$S/bcache:/w/ecidade/bootstrap/cache" -v "$S/tmp:/w/ecidade/tmp" -v "$S/arquivos:/w/ecidade/arquivos" -v "$R/scratchpad:/s:ro" \
    -v "$R/docker/php85-apache/paridade-56.ini:/usr/local/etc/php/conf.d/zz-paridade-56.ini:ro" \
    -e APP_ENV=production -e APP_KEY=base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    "t123-proj-php${v/./}" php -d memory_limit=1G -d display_errors=stderr -d error_reporting=E_ALL "$SCRIPT" /w/ecidade > "$W/saida-$v.txt" 2> "$W/err-$v.txt"
  test -s "$W/saida-$v.txt" || { echo "saida vazia no $v" >&2; exit 1; }
  echo "$v: $(wc -l < "$W/saida-$v.txt") linhas, $(grep -c '^Deprecated' "$W/err-$v.txt" || true) Deprecated"
done
diff "$W/saida-7.4.txt" "$W/saida-8.5.txt" > "$W/diferenca-7.4-8.5.txt" || true
echo "diferenca 7.4 x 8.5: $(grep -c '^[<>]' "$W/diferenca-7.4-8.5.txt") linhas"
echo "pasta de trabalho: $W"
