#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$TEST_DIR/../../../../" && pwd)"
VENDOR_DIR="$ROOT/runtime-85/pimaco-vendor"

if ! command -v patch >/dev/null 2>&1; then
  echo "FALHOU: o comando patch e necessario para adaptar as dependencias no vendor isolado." >&2
  exit 1
fi

composer install \
  --working-dir="$TEST_DIR" \
  --ignore-platform-req=php+ \
  --no-interaction \
  --no-scripts \
  --no-plugins

apply_vendor_patch() {
  package="$1"
  patch_file="$2"
  package_dir="$VENDOR_DIR/$package"

  if patch --dry-run --batch --forward -p1 -d "$package_dir" < "$TEST_DIR/$patch_file" >/dev/null 2>&1; then
    patch --batch --forward --silent -p1 -d "$package_dir" < "$TEST_DIR/$patch_file"
  elif patch --dry-run --batch --reverse -p1 -d "$package_dir" < "$TEST_DIR/$patch_file" >/dev/null 2>&1; then
    return
  else
    echo "FALHOU: patch $patch_file nao corresponde a $package instalado." >&2
    return 1
  fi
}

apply_vendor_patch "proner/phppimaco" "patches/proner-phppimaco-php85.patch"
apply_vendor_patch "bacon/bacon-qr-code" "patches/bacon-qr-code-php85.patch"
apply_vendor_patch "picqer/php-barcode-generator" "patches/picqer-barcode-generator-php85.patch"

cd "$ROOT"
python3 "$TEST_DIR/verifica_pimaco.py" "${PHP85:-php8.5}"
