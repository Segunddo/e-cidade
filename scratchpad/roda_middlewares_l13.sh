#!/bin/bash
# PHP8-38 (T-140): os 32 casos dos middlewares no 7.4 (vendor do PR) e no 8.5 (vendor do 8.5 = Laravel 13), pelo roda-isolado.sh (imagens do projeto, sem rede, falha alto).
# Na raiz do repositorio:   bash scratchpad/roda_middlewares_l13.sh [pasta-de-trabalho]
# Pre-requisitos: runtime-85/vendor (bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+) e
#   runtime-85/referencia-74/vendor (vendor do PR: composer install da ecidade/composer.lock + dump-autoload com o composer.json real; ver docs/migracao-laravel/middlewares-laravel13.md).
# O app do PR ainda nao sobe no Laravel 13 (AuthServiceProvider chama Passport::routes(), removido no Passport 13; a T-143 faz o boot subir): o 8.5 roda com
# esse provider fora (argumento 3 do trecho). Quando a T-143 integrar, rodar sem PULAR e ajustar a referencia.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$(mktemp -d /tmp/t140-XXXXXX)}"; mkdir -p "$W"
V74="${V74:-$R/runtime-85/referencia-74/vendor}"
PULAR="${PULAR-App\\Providers\\AuthServiceProvider}"
f() { iconv -f latin1 -t utf8 "$1" | grep -v '^Deprecated\|^$\|^LOG laravel\.\|^PROVIDERS NAO'; }
RI="$R/docker/composer-85/roda-isolado.sh"
VENDOR="$V74" bash "$RI" 7.4 "$R/scratchpad/middlewares_trecho.php" /app /app/vendor > "$W/raw-7.4.txt" 2> "$W/err-7.4.txt"
bash "$RI" 8.5 "$R/scratchpad/middlewares_trecho.php" /app /app/vendor "$PULAR" > "$W/raw-8.5.txt" 2> "$W/err-8.5.txt"
for v in 7.4 8.5; do f "$W/raw-$v.txt" > "$W/saida-$v.txt"; echo "$v: $(grep -c '^CASO' "$W/saida-$v.txt") casos; pares EMERGENCY do vendor: $(iconv -f latin1 -t utf8 "$W/raw-$v.txt" | grep -c '^LOG laravel.EMERGENCY' || true)"; done
VENDOR="$V74" bash "$RI" 7.4 "$R/scratchpad/middlewares_classes.php" /app /app/vendor > "$W/classes-7.4.txt"
bash "$RI" 8.5 "$R/scratchpad/middlewares_classes.php" /app /app/vendor > "$W/classes-8.5.txt"
diff "$W/saida-7.4.txt" "$W/saida-8.5.txt" > "$W/diferenca-7.4-8.5.txt" || true
diff "$W/classes-7.4.txt" "$W/classes-8.5.txt" > "$W/diferenca-classes.txt" || true
D="$R/docs/migracao-laravel/middlewares-laravel13"
if [ -d "$D" ]; then
  cmp "$W/saida-7.4.txt" "$D/saida-7.4.txt" && echo "7.4 = saida-7.4.txt da referencia"
  cmp "$W/diferenca-7.4-8.5.txt" "$D/diferenca-7.4-8.5.txt" && echo "diferenca 7.4 x 8.5(Laravel 13) = a da referencia"
  cmp "$W/diferenca-classes.txt" "$D/diferenca-classes.txt" && echo "diferenca de classes = a da referencia"
fi
echo "pasta de trabalho: $W"
