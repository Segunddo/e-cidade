# uso: sh runner_resumivel.sh <harness.php> <lista> <saida> <tag>
# Roda o harness numa lista inteira; se o processo morrer antes do fim (fatal OU exit), marca a
# classe em andamento como FATAL(rc) e retoma da seguinte. Equivale a "um processo por classe"
# sem o custo de uma partida por classe. O harness precisa imprimir "#C <arquivo>" ao iniciar
# cada classe.
h=$1; lista=$2; out=$3; tag=$4
rem=/tmp/_rem_$tag.txt; part=/tmp/_part_$tag.txt
cp "$lista" "$rem"; : > "$part"
cd /var/www/html
while [ -s "$rem" ]; do
  antes=$(grep -ac '^#C ' "$part")
  php -d display_errors=0 "$h" "$rem" >> "$part" 2>/dev/null </dev/null; rc=$?
  depois=$(grep -ac '^#C ' "$part")
  [ "$depois" = "$antes" ] && break                       # nenhuma classe nova: acabou
  falha=$(grep -a '^#C ' "$part" | tail -1 | cut -c4-)
  fim=$(grep -ax '' "$rem" | tail -1)
  # terminou normal se rc=0 e a classe em andamento ja imprimiu tudo: so sabemos que e a
  # ultima da lista se nao ha mais nenhuma classe depois dela
  n=$(grep -nxF "$falha" "$rem" | head -1 | cut -d: -f1)
  [ -z "$n" ] && break
  if [ $rc -eq 0 ]; then
     resto=$(tail -n +$((n+1)) "$rem" | tr -d ' \r\n')
     [ -z "$resto" ] && break
     # rc=0 com linhas restantes: ou so faltam arquivos sem classe, ou houve exit()
     tail -n +$((n+1)) "$rem" > "$rem.n"; mv "$rem.n" "$rem"
     printf '%s\tSAIU_RC0\n' "$falha" >> "$part"
     continue
  fi
  printf '%s\tFATAL_RC%s\n' "$falha" "$rc" >> "$part"
  tail -n +$((n+1)) "$rem" > "$rem.n"; mv "$rem.n" "$rem"
done
grep -av '^#C ' "$part" | sort > "$out"; echo "FIM $tag rc=$rc linhas=$(wc -l < $out)" > "$out.done"
