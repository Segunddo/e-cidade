#!/bin/bash
# PHP8-55 (T-146): os 58 models em memoria (scratchpad/models_dates_casts.php) no 7.4 (vendor do PR) e no 8.5 (vendor do 8.5 = Laravel 13), pelo roda-isolado.sh
# (imagens do projeto, sem rede, falha alto). Na raiz do repositorio:   bash scratchpad/roda_models_l13.sh [pasta-de-trabalho]
# Pre-requisitos: runtime-85/vendor (composer-85.sh install --no-scripts --ignore-platform-req=php+, depois composer-85.sh dump-autoload --no-scripts para a sobreposicao app-85/)
#   e runtime-85/referencia-74/vendor (vendor do PR com autoload completo; ver docs/migracao-laravel/middlewares-laravel13.md).
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d /tmp/t146-XXXXXX)}"; mkdir -p "$W"
V74="${V74:-$R/runtime-85/referencia-74/vendor}"
RI="$R/docker/composer-85/roda-isolado.sh"
VENDOR="$V74" bash "$RI" 7.4 "$R/scratchpad/models_dates_casts.php" /app /app/vendor 2>/dev/null | sed 's/DateTime::__construct(): //' > "$W/saida-7.4.txt"
bash "$RI" 8.5 "$R/scratchpad/models_dates_casts.php" /app /app/vendor 2>/dev/null > "$W/saida-8.5.txt"
echo "7.4: $(wc -l < "$W/saida-7.4.txt") linhas; 8.5: $(wc -l < "$W/saida-8.5.txt") linhas"
D="$R/docs/migracao-laravel"
cmp "$W/saida-7.4.txt" "$D/models-dates-casts/saida-7.4-antes-e-depois.txt" && echo "7.4 = saida de referencia da PHP8-55 (T-124)"
diff "$W/saida-7.4.txt" "$W/saida-8.5.txt" > "$W/diferenca-7.4-8.5.txt" || true
if [ -d "$D/eloquent-laravel13" ]; then
  cmp "$W/saida-8.5.txt" "$D/eloquent-laravel13/saida-8.5-laravel13.txt" && echo "8.5 (Laravel 13) = a da referencia"
  cmp "$W/diferenca-7.4-8.5.txt" "$D/eloquent-laravel13/diferenca-7.4-8.5.txt" && echo "diferenca 7.4 x 8.5 = a da referencia"
fi
echo "linhas de diferenca: $(grep -c '^[<>]' "$W/diferenca-7.4-8.5.txt"); fora do cast DateTime (c142_): $(grep '^[<>]' "$W/diferenca-7.4-8.5.txt" | grep -vc 'c142_' || true)"
echo "pasta de trabalho: $W"
