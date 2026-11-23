#!/bin/sh
# Caminho manual do passo 6b (docs "Como provar que o verificador funciona"): le o TEXTO das classes,
# sem executar nada. Imprime "arquivo campo" para cada campo com valor inicial numerico ($x = 0;) que o
# atualizacampos() compara com "" SEM a guarda === 0 que o porte coloca. No PHP 8, 0 == "" e falso: o
# valor digitado no formulario e ignorado. Depois do porte tem de sair vazio.
# Uso (de dentro de ecidade/): sh ../scratchpad/sem_guarda.sh $(cat /tmp/cls.txt)
# Conferido em 19/11/2026: soc nao migrado = 3.660 campos em 890 classes; db_cgm_classe.php migrado = 0.
for f in "$@"; do
  grep -a -E '\$this->[A-Za-z0-9_]+ *== *""' "$f" | grep -a -v '=== *0' \
    | grep -a -o -E '\$this->[A-Za-z0-9_]+ *== *""' | sed -E 's/\$this->([A-Za-z0-9_]+).*/\1/' | sort -u \
    | while read c; do grep -a -q -E "(var|public|protected) +\\\$$c *= *-?[0-9]" "$f" && echo "$f $c"; done
done
