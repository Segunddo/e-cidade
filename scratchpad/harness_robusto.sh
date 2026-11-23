#!/bin/sh
# Roda o harness repetidamente: quando ele morre num arquivo, registra o culpado,
# pula para o seguinte e continua. Sem isso, UM fatal esconde todo o resto da lista.
#
# SO SERVE para harness que emite UMA linha por entrada (instancia_classes.php).
# O avanco e `i = i + linhas_de_saida + 1`; com escrita.php, que emite MUITAS linhas
# por classe, a aritmetica pula a lista inteira. Para esse, rodar direto.
# (O guia hoje manda o escrita.php pelo porclasse.sh, uma classe por processo.)
#
# Usado no passo 6 do guia (docs/migrar-um-modulo.md). Roda no HOST, da raiz do repo:
#   docker cp scratchpad/instancia_classes.php $c:/tmp/ic.php; docker cp /tmp/cls.txt $c:/tmp/cls.txt
#   sh scratchpad/harness_robusto.sh $c          # $c = ecidade_php74 ou ecidade_php85
# Entradas (fixas): $1 = nome do container; /tmp/cls.txt no host = lista de classes
#   (caminhos relativos a ecidade/); /tmp/ic.php no container = o harness.
# Como faz: roda o harness sobre o RESTO da lista a partir da posicao i; conta as linhas que
#   ele produziu (n) antes de morrer; a entrada i+n e a que o matou -> vai para o SKIP; o
#   proximo ciclo recomeca em i+n+1. Termina quando i passa do fim da lista.
# Saidas no host: /tmp/rb_<container>.txt (as linhas do harness, concatenadas),
#   /tmp/skip_<container>.txt (os culpados, um por linha) e, no stdout, "<ok> ok, <p> pulados".
#   ok + pulados tem de dar o tamanho da lista.
# Usa /tmp/rest.txt e /tmp/part.txt com nome fixo: um container de cada vez.
C="$1"; LISTA=/tmp/cls.txt; OUT=/tmp/rb_$C.txt; SKIP=/tmp/skip_$C.txt
: > "$OUT"; : > "$SKIP"
total=$(wc -l < "$LISTA"); i=1
while [ "$i" -le "$total" ]; do
  tail -n +$i "$LISTA" > /tmp/rest.txt
  docker cp /tmp/rest.txt ${C}:/tmp/rest.txt >/dev/null
  # </dev/null: sem ele o docker exec -i consumiria o stdin de quem chamou o script
  docker exec -i $C php /tmp/ic.php /tmp/rest.txt </dev/null 2>/dev/null > /tmp/part.txt
  n=$(wc -l < /tmp/part.txt)
  cat /tmp/part.txt >> "$OUT"
  # avanca: n processados com sucesso + 1 que matou
  # (se o harness chegou ao fim sem morrer, a linha i+n esta alem do fim e o sed nao grava nada)
  sed -n "$((i+n))p" "$LISTA" >> "$SKIP"
  i=$((i+n+1))
done
echo "$(wc -l < "$OUT") ok, $(grep -c . "$SKIP" 2>/dev/null || echo 0) pulados"
