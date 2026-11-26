#!/bin/bash
# Roda o exercicio do SDK Pix do BB contra o duble local, sem rede (--network none).
# Uso (da raiz do repositorio): bash docs/migracao-laravel/anexos/pix-bb/rodar.sh <imagem-php> <pasta-vendor> <saida.txt> [mascara-error_reporting]
#   <pasta-vendor>: vendor/ com autoload.php (no 8.5: runtime-85/vendor; precisa de ecidade/ montado em /app: use ECIDADE=1)
#   ECIDADE=1  monta ecidade/ em /app e o vendor em /app/vendor (autoload do composer-85 exige app/Helpers)
set -u
IMG=${1:?imagem}; V=$(realpath "${2:?vendor}"); OUT=$(realpath -m "${3:?saida}"); ER=${4:-}
P=$(cd "$(dirname "$0")" && pwd); R=$(git rev-parse --show-toplevel)
if [ "${ECIDADE:-}" = 1 ]; then M="-v $R/ecidade:/app:ro -v $V:/app/vendor:ro"; AL=/app/vendor/autoload.php; else M="-v $V:/g:ro"; AL=/g/autoload.php; fi
docker run --rm --network none ${ER:+-e PIX_ER=$ER} ${PIX_LARAVEL:+-e PIX_LARAVEL=1} -v "$P":/pix:ro $M "$IMG" sh -c "DUBLE_LOG=/tmp/duble.jsonl php -S 127.0.0.1:8099 /pix/double.php >/tmp/server.log 2>&1 & sleep 1; php /pix/exercicio.php $AL - 8099; echo '---PEDIDOS'; cat /tmp/duble.jsonl" > "$OUT" 2>&1
echo "$(basename "$OUT"): $(wc -l < "$OUT") linhas"
