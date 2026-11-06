#!/bin/sh
# Roda o harness repetidamente: quando ele morre num arquivo, registra o culpado,
# pula para o seguinte e continua. Sem isso, UM fatal esconde todo o resto da lista.
#
# SO SERVE para harness que emite UMA linha por entrada (instancia_classes.php).
# O avanco e `i = i + linhas_de_saida + 1`; com escrita.php, que emite MUITAS linhas
# por classe, a aritmetica pula a lista inteira. Para esse, rodar direto.
C="$1"; LISTA=/tmp/cls.txt; OUT=/tmp/rb_$C.txt; SKIP=/tmp/skip_$C.txt
: > "$OUT"; : > "$SKIP"
total=$(wc -l < "$LISTA"); i=1
while [ "$i" -le "$total" ]; do
  tail -n +$i "$LISTA" > /tmp/rest.txt
  docker cp /tmp/rest.txt ${C}:/tmp/rest.txt >/dev/null
  docker exec -i $C php /tmp/ic.php /tmp/rest.txt </dev/null 2>/dev/null > /tmp/part.txt
  n=$(wc -l < /tmp/part.txt)
  cat /tmp/part.txt >> "$OUT"
  # avanca: n processados com sucesso + 1 que matou
  sed -n "$((i+n))p" "$LISTA" >> "$SKIP"
  i=$((i+n+1))
done
echo "$(wc -l < "$OUT") ok, $(grep -c . "$SKIP" 2>/dev/null || echo 0) pulados"
