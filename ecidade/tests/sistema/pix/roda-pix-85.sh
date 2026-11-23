#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$TEST_DIR/../../../.." && pwd)"
VENDOR_DIR="$ROOT/runtime-85/pix-vendor"

if ! command -v patch >/dev/null 2>&1; then
  echo "FALHOU: o comando patch e necessario para adaptar o SDK no vendor isolado." >&2
  exit 1
fi

composer install \
  --working-dir="$TEST_DIR" \
  --no-interaction \
  --no-scripts \
  --no-plugins

if patch --dry-run --batch --forward -p1 -d "$VENDOR_DIR/dbseller/sdk-api-pix-bb" \
    < "$TEST_DIR/patches/sdk-api-pix-bb-php85.patch" >/dev/null 2>&1; then
  patch --batch --forward --silent -p1 -d "$VENDOR_DIR/dbseller/sdk-api-pix-bb" \
    < "$TEST_DIR/patches/sdk-api-pix-bb-php85.patch"
elif ! patch --dry-run --batch --reverse -p1 -d "$VENDOR_DIR/dbseller/sdk-api-pix-bb" \
    < "$TEST_DIR/patches/sdk-api-pix-bb-php85.patch" >/dev/null 2>&1; then
  echo "FALHOU: patch do SDK nao corresponde ao pacote instalado." >&2
  exit 1
fi

PHP85="${PHP85:-php8.5}"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

"$PHP85" -d error_reporting=-1 -d display_errors=stderr \
  "$TEST_DIR/test_pix.php" >"$TEMP_DIR/stdout" 2>"$TEMP_DIR/stderr" || {
    cat "$TEMP_DIR/stdout"
    cat "$TEMP_DIR/stderr" >&2
    exit 1
  }

if [[ -s "$TEMP_DIR/stderr" ]]; then
  cat "$TEMP_DIR/stderr" >&2
  echo "FALHOU: PHP emitiu avisos ou deprecations." >&2
  exit 1
fi

EXPECTED_OUTPUT="OK: PHP 8.5 + Laravel 13; OAuth e emissao PIX BB simulados; payload de producao e encoding conferidos."
if [[ "$(cat "$TEMP_DIR/stdout")" != "$EXPECTED_OUTPUT" ]]; then
  cat "$TEMP_DIR/stdout"
  echo "FALHOU: saida inesperada do teste PIX." >&2
  exit 1
fi

echo "$EXPECTED_OUTPUT"
