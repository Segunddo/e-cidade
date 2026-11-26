#!/bin/sh
# php8_62_usos.sh: arquivos e linhas do codigo versionado de ecidade/ (sem vendor/) que citam cada pacote
# que sobe de versao maior ou sai da trava do 8.5 (padroes em scratchpad/php8_62_usos.tsv).
R="$(cd "$(dirname "$0")/.." && pwd)"
L="$(mktemp)"; trap 'rm -f "$L"' EXIT
git -C "$R/ecidade" ls-files -z -- '*.php' ':!vendor/' > "$L"
cd "$R/ecidade" || exit 1
while IFS="$(printf '\t')" read -r pac re; do
    n=$(xargs -0 grep -laP -- "$re" < "$L" | wc -l)
    o=$(xargs -0 grep -caP -- "$re" < "$L" | awk -F: '{s+=$NF} END{print s+0}')
    printf '%s\t%s\t%s\n' "$pac" "$n" "$o"
done < "$R/scratchpad/php8_62_usos.tsv"
