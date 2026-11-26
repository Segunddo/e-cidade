#!/bin/bash
# PHP8-87: compara os usos de dompdf, mPDF, Faker, laminas-escaper, htmlpurifier, nette e PhpWord HTML entre o 7.4 do PR
# e o 8.5, sem banco e sem rede (--network none). Codigo montado so leitura.
# Uso: roda.sh <ecidade> <vendor 7.4> <vendor 8.5> <img 7.4> <img 8.5> <saida>
#   vendor 7.4 = composer install do ecidade/composer.lock do PR; vendor 8.5 = runtime-85/vendor (docker/composer-85/composer-85.sh install)
#   img 7.4 = construida de docker/php74-apache; img 8.5 = construida de docker/php85-apache
#   requer pdfinfo/pdftotext/pdftoppm (poppler-utils) no host
set -u
E=$(realpath "$1"); V74=$(realpath "$2"); V85=$(realpath "$3"); I74=$4; I85=$5; O=$(realpath -m "$6"); T=$(dirname "$(realpath "$0")")
falha() { echo "FALHOU: $*" >&2; exit 1; }
# ponto de montagem de /e/vendor: sem ele, o docker run falha (ecidade/ montado so leitura) e a saida vazia pareceria igual
mkdir -p "$E/vendor" || falha "nao criou $E/vendor"
mkdir -p "$O/74/html" "$O/85/html" "$O/74/dompdf" "$O/74/mpdf" "$O/74/tmp" "$O/85/dompdf" "$O/85/mpdf" "$O/85/tmp"; chmod -R 777 "$O"
# o vendor vai em /e/vendor, como no runtime: o autoload carrega os arquivos de app/Helpers do proprio ecidade/
r() { local img=$1 v=$2; shift 2; docker run --rm --network none -u "$(id -u):$(id -g)" -v "$E:/e:ro" -v "$v:/e/vendor:ro" -v "$T:/t:ro" -v "$O:/o" -w /o "$img" php -d error_reporting='E_ALL&~E_DEPRECATED&~E_NOTICE&~E_WARNING' "$@" || falha "docker run $img $1 (rc=$?)"; }
for v in 74 85; do
  img=$I74; ven=$V74; [ $v = 85 ] && img=$I85 && ven=$V85
  # o HTML das capas e compilado pelo Blade de cada lado (Laravel do PR no 7.4, o da trava do 8.5 no 8.5)
  r "$img" "$ven" /t/html_capas.php /e /e/vendor /o/$v/html >/dev/null
  r "$img" "$ven" /t/dompdf.php /e/vendor /o/$v/html /o/$v/dompdf >/dev/null
  r "$img" "$ven" /t/mpdf.php /e/vendor /e /o/$v/mpdf >/dev/null
  r "$img" "$ven" /t/faker.php /e/vendor > "$O/$v/faker.tsv"
  r "$img" "$ven" /t/indiretos.php /e/vendor /o/$v/tmp > "$O/$v/indiretos.tsv"
done
for v in 74 85; do
  [ "$(ls "$O/$v/dompdf"/*.pdf 2>/dev/null | wc -l)" -eq 12 ] && [ "$(ls "$O/$v/html"/*.html 2>/dev/null | wc -l)" -eq 12 ] || falha "faltam PDFs do dompdf no $v"
  [ "$(ls "$O/$v/mpdf"/*.pdf 2>/dev/null | wc -l)" -gt 0 ] || falha "nenhum PDF do mPDF no $v"
  [ -s "$O/$v/faker.tsv" ] && [ -s "$O/$v/indiretos.tsv" ] || falha "saida vazia do faker ou dos indiretos no $v"
done
echo "== html das capas (Blade)"; d=0; for f in "$O/74/html"/*.html; do cmp -s "$f" "$O/85/html/$(basename "$f")" || d=$((d+1)); done; echo "TOTAL iguais=$((12-d)) difere=$d"
echo "== dompdf"; bash "$T/compara.sh" "$O/74/dompdf" "$O/85/dompdf"
echo "== mpdf"; bash "$T/compara.sh" "$O/74/mpdf" "$O/85/mpdf"
echo "== faker"; echo "linhas=$(wc -l < "$O/74/faker.tsv") diferentes=$(diff "$O/74/faker.tsv" "$O/85/faker.tsv" | grep -c '^<')"
echo "== indiretos"; for k in E P N W; do echo "$k casos=$(grep -c "^$k" "$O/74/indiretos.tsv") diferentes=$(diff <(grep "^$k" "$O/74/indiretos.tsv") <(grep "^$k" "$O/85/indiretos.tsv") | grep -c '^<')"; done
