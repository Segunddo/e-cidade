#!/bin/bash
# PHP8-62: inicializacao do app do PR no 7.4 (Laravel 8 do PR) e no 8.5 (Laravel 13 da trava do 8.5), sem banco,
# pelo docker/composer-85/roda-isolado.sh (imagens do projeto, --network none, falha alto), e compara.
# Uso (raiz do repositorio): bash scratchpad/php8_62_init_l13.sh <vendor do 7.4> <pasta de saida>
#   <vendor do 7.4>: composer install do ecidade/composer.lock com autoload gerado para /app (ver o registro)
#   vendor do 8.5: runtime-85/vendor (bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+)
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
V74="$(cd "${1:?vendor do 7.4}" && pwd)"; O="$(mkdir -p "${2:?pasta de saida}" && cd "$2" && pwd)"
VENDOR="$V74" bash "$R/docker/composer-85/roda-isolado.sh" 7.4 "$R/scratchpad/php8_62_init_isolado.php" > "$O/saida-7.4.txt" 2> "$O/err-7.4.txt"
bash "$R/docker/composer-85/roda-isolado.sh" 8.5 "$R/scratchpad/php8_62_init_isolado.php" > "$O/saida-8.5.txt" 2> "$O/err-8.5.txt"
for v in 7.4 8.5; do
  grep -q '^ROTAS ' "$O/saida-$v.txt" || { echo "o app nao subiu no $v:" >&2; head -5 "$O/saida-$v.txt" >&2; exit 1; }
  echo "$v: $(head -1 "$O/saida-$v.txt"), $(grep -E '^(ROTAS|COMANDOS|CONFIG|PROVIDERS)' "$O/saida-$v.txt" | tr '\n' ' ')$(grep -c '^Deprecated' "$O/err-$v.txt" || true) Deprecated"
done
diff "$O/saida-7.4.txt" "$O/saida-8.5.txt" > "$O/diferenca-7.4-8.5.txt" || true
echo "diferenca 7.4 x 8.5: $(grep -c '^[<>]' "$O/diferenca-7.4-8.5.txt") linhas"
