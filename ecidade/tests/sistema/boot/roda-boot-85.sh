#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
PHP85="${PHP85:-php8.5}"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

composer install \
  --working-dir="$TEST_DIR" \
  --no-interaction \
  --no-scripts \
  --no-plugins

if ! "$PHP85" -r 'exit(PHP_VERSION_ID >= 80500 ? 0 : 1);'; then
  echo "FALHOU: o teste exige PHP 8.5 ou superior." >&2
  exit 1
fi

BOOT_TEST_CACHE="$TEMP_DIR" "$PHP85" -d error_reporting=-1 -d display_errors=stderr \
  "$TEST_DIR/test_boot.php" >"$TEMP_DIR/stdout" 2>"$TEMP_DIR/stderr" || {
    cat "$TEMP_DIR/stdout"
    cat "$TEMP_DIR/stderr" >&2
    exit 1
  }

if [[ -s "$TEMP_DIR/stderr" ]]; then
  cat "$TEMP_DIR/stderr" >&2
  echo "FALHOU: PHP emitiu avisos ou deprecations." >&2
  exit 1
fi

EXPECTED_PREFIX="OK: PHP 8.5"
if [[ "$(cat "$TEMP_DIR/stdout")" != "$EXPECTED_PREFIX"* ]]; then
  cat "$TEMP_DIR/stdout"
  echo "FALHOU: saida inesperada do teste de boot." >&2
  exit 1
fi

cat "$TEMP_DIR/stdout"
