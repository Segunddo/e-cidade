#!/bin/bash
# PHP8-62: roda scratchpad/locale_lc_time.php no 7.4 e no 8.5 (sem banco, --network none) e compara as duas saidas byte a byte.
# Do zero, na raiz do repositorio:   bash scratchpad/roda_locale.sh [pasta-de-trabalho]
# - vendor do PR fora do repositorio (composer install da composer.lock; so baixa pacotes), ao lado de ecidade/ (autoload ../ecidade/app);
# - imagens php-cli com o locale pt_BR (scratchpad/locale-img/Dockerfile; rede so no build);
# - sai com erro se o docker run falhar ou a saida vier vazia (nada de "igual" por duas saidas vazias).
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d /tmp/t139-XXXXXX)}"
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
for v in 7.4 8.5; do docker image inspect "t139-php${v/./}" >/dev/null 2>&1 || docker build -q --network host --build-arg PHPV=$v -t "t139-php${v/./}" "$R/scratchpad/locale-img" >/dev/null; done
ENVMNT=()
if [ -e "$R/ecidade/.env" ]; then : > "$W/env.vazio"; ENVMNT=(-v "$W/env.vazio:/w/ecidade/.env:ro"); fi
for v in 7.4 8.5; do
  S="$W/st-$v"; mkdir -p "$S/logs" "$S/framework/cache/data" "$S/framework/sessions" "$S/framework/views" "$W/cache-$v"; chmod -R 777 "$S" "$W/cache-$v"
  docker run --rm --network none -u "$(id -u):$(id -g)" \
    -v "$R/ecidade:/w/ecidade:ro" "${ENVMNT[@]}" -v "$W/pr:/w/pr:ro" -v "$R/scratchpad:/s:ro" -v "$S:/tmp/storage" -v "$W/cache-$v:/tmp/cache" \
    -e APP_ENV=production -e APP_KEY=base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    -e APP_PACKAGES_CACHE=/tmp/cache/packages.php -e APP_SERVICES_CACHE=/tmp/cache/services.php -e APP_CONFIG_CACHE=/tmp/cache/config.php \
    "t139-php${v/./}" php -d memory_limit=1G /s/locale_lc_time.php /w/ecidade /w/pr/vendor > "$W/saida-$v.txt" 2> "$W/err-$v.txt"
  test -s "$W/saida-$v.txt" || { echo "saida vazia no $v" >&2; exit 1; }
  echo "$v: $(wc -l < "$W/saida-$v.txt") linhas"
done
sed -n '1,3p' "$W/saida-7.4.txt" | sed 's/^/7.4  /'; sed -n '1,3p' "$W/saida-8.5.txt" | sed 's/^/8.5  /'
if cmp "$W/saida-7.4.txt" "$W/saida-8.5.txt"; then echo "7.4 = 8.5 (byte a byte)"; else echo "7.4 x 8.5 DIFEREM"; diff "$W/saida-7.4.txt" "$W/saida-8.5.txt" | head -20; fi
echo "pasta de trabalho: $W"
