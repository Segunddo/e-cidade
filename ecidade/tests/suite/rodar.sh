#!/bin/bash
# Suite unica dos testes proprios (sem banco): PHPUnit de cada composer, no 7.4 (referencia) e no 8.5.
# Uso (raiz do repositorio):  bash ecidade/tests/suite/rodar.sh [--runtime 74|85|ambos] [--saida PASTA]
# Pre-requisitos: vendor do 7.4 em ecidade/vendor (ou VENDOR_74=<pasta>) e vendor do 8.5 em runtime-85/vendor
#   (bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+). ecidade/vendor e ecidade/tmp sao criados aqui.
# Nada aqui usa banco nem rede: os contêineres sobem com --network none, ecidade/ somente leitura, vendor somente
#   leitura e so tmp/ gravavel (pasta de saida). Entradas: camadas/unitario.lista. Lacunas: camadas/lacunas.lista.
# Saida: 0 = tudo passou nos runtimes pedidos; 1 = algum teste falhou; 2 = uso/ambiente.
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ECIDADE="$(cd "$AQUI/../.." && pwd)"
RAIZ="$(cd "$ECIDADE/.." && pwd)"
RUNTIMES="74 85"; SAIDA="$AQUI/relatorios"
V74="${VENDOR_74:-$ECIDADE/vendor}"; V85="${VENDOR_85:-$RAIZ/runtime-85/vendor}"
while [ $# -gt 0 ]; do
  case "$1" in
    --runtime) case "$2" in ambos) RUNTIMES="74 85";; 74|85) RUNTIMES="$2";; *) echo "runtime invalido: $2" >&2; exit 2;; esac; shift 2;;
    --saida)   SAIDA="$2"; shift 2;;
    -h|--help) sed -n '2,9p' "$0"; exit 0;;
    *) echo "opcao desconhecida: $1" >&2; exit 2;;
  esac
done
# ecidade/ sobe somente leitura: vendor/ e tmp/ sao pontos de montagem e precisam existir (num checkout novo nao existem;
# se o Docker os criasse, viriam root:root e o composer install do 7.4 deixaria de gravar em vendor/). Criados aqui, como o usuario.
mkdir -p "$ECIDADE/vendor" "$ECIDADE/tmp" || exit 2
mkdir -p "$SAIDA"; SAIDA="$(cd "$SAIDA" && pwd)"
STATUS=0
for RT in $RUNTIMES; do
  if [ "$RT" = 74 ]; then PHP=7.4; VENDOR="$V74"; else PHP=8.5; VENDOR="$V85"; fi
  [ -f "$VENDOR/autoload.php" ] || { echo "sem vendor do $PHP em $VENDOR" >&2; exit 2; }
  # imagem do projeto (mesmas extensoes e php.ini do runtime), nao a php:<v>-cli oficial; construida 1x se faltar (precisa de rede)
  IMG="ecidade-php${RT}-apache"
  docker image inspect "$IMG" >/dev/null 2>&1 || docker build -q -t "$IMG" "$RAIZ/docker/php${RT}-apache" >/dev/null || { echo "imagem $IMG ausente e o build falhou" >&2; exit 2; }
  echo "=== PHP $PHP ==="
  mkdir -p "$SAIDA/$RT/tmp"; chmod 777 "$SAIDA/$RT/tmp"
  while IFS= read -r ENTRADA; do
    [[ "$ENTRADA" =~ ^[[:space:]]*(#|$) ]] && continue
    NOME="$(echo "$ENTRADA" | tr '/.' '__')"
    docker run --rm --network none -u "$(id -u):$(id -g)" \
      -v "$ECIDADE:/app:ro" -v "$VENDOR:/app/vendor:ro" -v "$SAIDA/$RT:/out" -v "$SAIDA/$RT/tmp:/app/tmp" -w /app "$IMG" \
      php -d memory_limit=1G vendor/bin/phpunit --no-configuration --colors=never --bootstrap tests/suite/bootstrap.php \
      --cache-result-file /out/cache --log-junit "/out/$NOME.xml" "$ENTRADA" </dev/null > "$SAIDA/$RT/$NOME.txt" 2>&1
    RC=$?
    RES="$(grep -E '^(OK|Tests:)' "$SAIDA/$RT/$NOME.txt" | head -1)"
    [ -n "$RES" ] || { RES="SEM RESULTADO DO PHPUNIT"; RC=1; }
    echo "$ENTRADA: $RES (rc=$RC)" | tee -a "$SAIDA/resumo-$RT.txt.novo"
    [ "$RC" -eq 0 ] || STATUS=1
  done < "$AQUI/camadas/unitario.lista"
  mv "$SAIDA/resumo-$RT.txt.novo" "$SAIDA/resumo-$RT.txt"
done
[ "$STATUS" -eq 0 ] && echo "SUITE SEM FALHAS" || echo "SUITE COM FALHAS (compare os dois runtimes; diferencas explicadas em docs/registro/testes-proprios-85.md)"
exit "$STATUS"
