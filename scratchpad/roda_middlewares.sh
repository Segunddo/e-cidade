#!/bin/bash
# PHP8-38: roda scratchpad/middlewares_trecho.php no 7.4 e no 8.5 (sem banco, --network none) e compara com a referencia do repositorio.
# Do zero, na raiz do repositorio:   bash scratchpad/roda_middlewares.sh [pasta-de-trabalho]
# - o vendor do PR sai do ecidade/composer.lock num composer install FORA do repositorio (so baixa pacotes; sem banco);
# - o vendor fica em <pasta>/pr/vendor, ao lado de <raiz>/ecidade: o autoload usa ../ecidade/app e nao precisa dos "files" do projeto;
# - storage gravavel (logs, framework/sessions, framework/cache/data, framework/views) em pasta nova.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d /tmp/t112-XXXXXX)}"
mkdir -p "$W/pr"
if [ ! -f "$W/pr/vendor/autoload.php" ]; then
  cp "$R/ecidade/composer.lock" "$W/pr/"
  python3 - "$R/ecidade/composer.json" "$W/pr/composer.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d['autoload'] = {'psr-4': {'App\\': '../ecidade/app/'}}
d.pop('scripts', None); d.pop('autoload-dev', None)
json.dump(d, open(sys.argv[2], 'w'), indent=1)
PY
  docker run --rm -u "$(id -u):$(id -g)" -e COMPOSER_HOME=/tmp/ch -v "$W/pr:/pr" -w /pr composer:2 \
    composer install --no-scripts --no-interaction --ignore-platform-reqs --no-progress >/dev/null
fi
# .env: so se existir um local (a base nao o versiona); nesse caso e coberto por um arquivo vazio
ENVMNT=()
if [ -e "$R/ecidade/.env" ]; then : > "$W/env.vazio"; ENVMNT=(-v "$W/env.vazio:/w/ecidade/.env:ro"); fi
f() { grep -v '^Deprecated\|^$\|^LOG laravel\.' "$1"; }
for v in 7.4 8.5; do
  S="$W/st-$v"; mkdir -p "$S/logs" "$S/framework/cache/data" "$S/framework/sessions" "$S/framework/views" "$W/cache-$v"; chmod -R 777 "$S" "$W/cache-$v"
  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v "$R/ecidade:/w/ecidade:ro" "${ENVMNT[@]}" -v "$W/pr:/w/pr:ro" -v "$R/scratchpad:/s:ro" -v "$S:/tmp/storage" -v "$W/cache-$v:/tmp/cache" \
    -e APP_ENV=production -e APP_KEY=base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    -e APP_PACKAGES_CACHE=/tmp/cache/packages.php -e APP_SERVICES_CACHE=/tmp/cache/services.php -e APP_CONFIG_CACHE=/tmp/cache/config.php \
    "php:$v-cli" php -d memory_limit=1G /s/middlewares_trecho.php /w/ecidade /w/pr/vendor > "$W/out-$v.raw" 2> "$W/err-$v.txt"
  iconv -f latin1 -t utf8 "$W/out-$v.raw" > "$W/out-$v.txt"     # a saida do script e ISO-8859-1; a referencia do repositorio e UTF-8
  f "$W/out-$v.txt" > "$W/saida-$v.txt"
  echo "$v: $(grep -c '^CASO' "$W/saida-$v.txt") casos; pares EMERGENCY do vendor: $(grep -c '^LOG laravel.EMERGENCY' "$W/out-$v.txt")"
done
cmp "$W/saida-7.4.txt" "$R/docs/migracao-laravel/middlewares-sessao/saida-7.4.txt" && echo "7.4 = saida-7.4.txt da referencia"
diff "$W/saida-7.4.txt" "$W/saida-8.5.txt" > "$W/diferenca.txt" || true
cmp "$W/diferenca.txt" "$R/docs/migracao-laravel/middlewares-sessao/diferenca-7.4-8.5.txt" && echo "diferenca 7.4 x 8.5 = diferenca-7.4-8.5.txt da referencia"
echo "pasta de trabalho: $W"
