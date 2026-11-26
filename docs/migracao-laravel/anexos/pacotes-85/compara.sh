#!/bin/bash
# compara dois diretorios de PDF por conteudo: paginas/tamanho (pdfinfo), texto (pdftotext -layout) e imagem de cada pagina (pdftoppm 60 dpi, md5)
# uso: compara.sh <dir A> <dir B>  (requer poppler-utils)
A=$1; B=$2; iguais=0; dif=0
for fa in "$A"/*.pdf; do
  n=$(basename "$fa"); fb="$B/$n"
  ia=$(pdfinfo "$fa" | grep -E "^(Pages|Page size)"); ib=$(pdfinfo "$fb" | grep -E "^(Pages|Page size)")
  ta=$(pdftotext -layout "$fa" - | md5sum); tb=$(pdftotext -layout "$fb" - | md5sum)
  ra=$(pdftoppm -r 60 -png "$fa" | md5sum); rb=$(pdftoppm -r 60 -png "$fb" | md5sum)
  [ "$ia" = "$ib" ] && r1=igual || r1=DIFERE; [ "$ta" = "$tb" ] && r2=igual || r2=DIFERE; [ "$ra" = "$rb" ] && r3=igual || r3=DIFERE
  echo -e "$n\tpaginas=$(echo "$ia" | head -1 | awk '{print $2}')\tinfo:$r1\ttexto:$r2\timagem:$r3"
  if [ "$r1$r2$r3" = igualigualigual ]; then iguais=$((iguais+1)); else dif=$((dif+1)); fi
done
echo "TOTAL iguais=$iguais difere=$dif"
