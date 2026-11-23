# uso: docker cp scratchpad/porclasse.sh <container>:/tmp/pc.sh; docker exec -i <container> sh /tmp/pc.sh /tmp/<harness>.php < lista
# A bateria (regressao/php/classes.py) copia este script e escrita.php para ecidade/tmp/ (= /var/www/html/tmp nos dois
# runtimes) e o roda no container da referencia (PHP 7.4) e no do alvo (PHP 8.5); os nomes vem de
# regressao/nucleo/ambiente.py (REGRESSAO_CONTAINER_REF / REGRESSAO_CONTAINER_PHP_NOVO).
# uma classe por processo (um fatal nao mata o resto da lista); marca quem nao produziu saida
#
# Usado nos passos 6/6b do guia (docs/migrar-um-modulo.md); no 6b com o escrita.php:
#   docker exec -i $c sh /tmp/pc.sh /tmp/esc.php < /tmp/cls.txt > /tmp/w_$c.txt
# Roda DENTRO do container (sh, sem bash). Entradas: $1 = harness PHP; stdin = lista de
# caminhos relativos a /var/www/html, um por linha.
# Como faz: para cada linha, grava SO aquela linha em /tmp/_um.txt e roda o harness com esse
# arquivo-lista de um item, num processo php novo. Se o processo morrer num fatal, perde-se
# so aquela classe.
# Saida: stdout = a saida do harness para cada classe, ou "SEM_SAIDA <caminho>" quando ele
# nao imprimiu nada (fatal, classe sem campos...); stderr, no fim = "#TOTAL <n> COM_SAIDA <v>".
# O TOTAL tem de ser igual ao `wc -l` da lista.
# ATENCAO: /tmp/_um.txt tem nome fixo e o /tmp e compartilhado entre os containers -- rodar
# um runtime de cada vez, nunca os dois em paralelo.
h=$1; n=0; v=0
# o </dev/null no php abaixo e obrigatorio: sem ele o php herda o stdin do laco e engole o
# resto da lista (armadilha do `while read`); display_errors=0 e 2>/dev/null tiram a mensagem
# do fatal da saida, que assim fica vazia e vira SEM_SAIDA
while read c; do n=$((n+1)); echo "$c" > /tmp/_um.txt
  o=$(cd /var/www/html && php -d display_errors=0 "$h" /tmp/_um.txt 2>/dev/null </dev/null)
  if [ -n "$o" ]; then v=$((v+1)); echo "$o"; else echo "SEM_SAIDA $c"; fi
done
echo "#TOTAL $n COM_SAIDA $v" >&2
