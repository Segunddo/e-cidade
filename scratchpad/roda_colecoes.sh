#!/bin/bash
# PHP8-62 (T-155): Collection / Str / Arr / helpers do codigo no 7.4 (Laravel 8), no 8.5 com o Laravel 13 e no 8.5 com o Laravel 8 (isola o que e do PHP), pelo roda-isolado.sh
# (imagens do projeto, sem rede, falha alto). Na raiz do repositorio:   bash scratchpad/roda_colecoes.sh [pasta-de-trabalho]
# Pre-requisitos: runtime-85/vendor (Laravel 13: bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+) e runtime-85/referencia-74/vendor (vendor do PR; ver docs/migracao-laravel/middlewares-laravel13.md).
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d /tmp/t155-XXXXXX)}"; mkdir -p "$W"
V74="${V74:-$R/runtime-85/referencia-74/vendor}"; RI="$R/docker/composer-85/roda-isolado.sh"; T="$R/scratchpad/colecoes_str_arr.php"
VENDOR="$V74" bash "$RI" 7.4 "$T" /app /app/vendor > "$W/saida-7.4-laravel8.txt"
VENDOR="$V74" bash "$RI" 8.5 "$T" /app /app/vendor > "$W/saida-8.5-laravel8.txt"
bash "$RI" 8.5 "$T" /app /app/vendor > "$W/saida-8.5-laravel13.txt"
echo "casos: $(wc -l < "$W/saida-7.4-laravel8.txt") / $(wc -l < "$W/saida-8.5-laravel8.txt") / $(wc -l < "$W/saida-8.5-laravel13.txt")"
diff "$W/saida-7.4-laravel8.txt" "$W/saida-8.5-laravel8.txt" > "$W/diferenca-php.txt" || true
diff "$W/saida-8.5-laravel8.txt" "$W/saida-8.5-laravel13.txt" > "$W/diferenca-laravel.txt" || true
diff "$W/saida-7.4-laravel8.txt" "$W/saida-8.5-laravel13.txt" > "$W/diferenca-7.4-8.5.txt" || true
echo "linhas mudadas: PHP (7.4 x 8.5, Laravel 8) = $(grep -c '^[0-9]' "$W/diferenca-php.txt") blocos, $(grep -c '^[<>]' "$W/diferenca-php.txt") linhas '<'/'>'; Laravel (8 x 13, PHP 8.5) = $(grep -c '^[<>]' "$W/diferenca-laravel.txt") linhas; total 7.4 x 8.5/13 = $(grep -c '^[<>]' "$W/diferenca-7.4-8.5.txt") linhas"
D="$R/docs/migracao-laravel/colecoes-str-arr"
if [ -d "$D" ]; then
  for f in saida-7.4-laravel8 saida-8.5-laravel8 saida-8.5-laravel13 diferenca-php diferenca-laravel diferenca-7.4-8.5; do cmp "$W/$f.txt" "$D/$f.txt" && echo "$f = referencia"; done
fi
echo "pasta de trabalho: $W"
