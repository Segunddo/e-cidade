#!/bin/bash
# PHP8-51: console (comandos e agendamento), payload de fila e funcoes removidas, 7.4 x 8.5, sem banco (host
# inexistente) e sem rede. Cada trecho roda pelo docker/composer-85/roda-isolado.sh (imagens do projeto, ecidade/ so
# leitura, --network none, falha alto), com o vendor de cada lado em VENDOR e as variaveis de teste de gera_env.py.
# Uso: roda.sh <vendor 7.4> <vendor 8.5> <saida>
#   vendor 7.4 = composer install do ecidade/composer.lock do PR (comando em filas-comandos-85.md, "Como reproduzir");
#   vendor 8.5 = o de uma trava do 8.5 (docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+)
# Avisos do PHP (warning, notice, deprecated): o roda-isolado.sh os manda ao stderr; aqui vao para err74.txt/err85.txt,
# fora da saida comparada, e a contagem entra no resumo.
set -u
V74=$(realpath "$1"); V85=$(realpath "$2"); O=$(realpath -m "$3"); T=$(dirname "$(realpath "$0")")
RI="$T/../../../../docker/composer-85/roda-isolado.sh"
exec 3>&2
falha() { echo "FALHOU: $*" >&3; exit 1; }
mkdir -p "$O"; : > "$O/err74.txt"; : > "$O/err85.txt"; python3 "$T/gera_env.py" "$O/env"
r() {   # r <74|85> <trecho> [args]: stdout do trecho; avisos acrescentados a err<74|85>.txt
  local v=$1 ver=7.4 ven=$V74; shift; [ $v = 85 ] && ver=8.5 && ven=$V85
  VENDOR="$ven" ENV_EXTRA="$O/env" EXTRA_RO="$O:/o" STDERR_ARQ="$O/err.ultimo" bash "$RI" $ver "$T/$@" \
    || { cat "$O/err.ultimo" >> "$O/err$v.txt" 2>/dev/null; falha "roda-isolado $ver $1 (stderr em $O/err$v.txt)"; }
  cat "$O/err.ultimo" >> "$O/err$v.txt"
}
# classes ShouldQueue: candidatas = arquivos de app/ que citam ShouldQueue; confirmadas por reflexao no 7.4
(cd "$T/../../../../ecidade" && grep -l -a -r 'ShouldQueue' app | sort) | STDIN=1 r 74 lista_filas.php > "$O/jobs.lista"
[ -s "$O/jobs.lista" ] || falha "lista de classes de fila vazia"
for v in 74 85; do
  r $v console.php > "$O/console$v.txt"
  r $v artisan.php list --raw > "$O/list$v.txt"
  r $v funcoes.php > "$O/funcoes$v.txt"
  : > "$O/jobs$v.txt"; while read -r c; do r $v jobs.php "$c" >> "$O/jobs$v.txt"; done < "$O/jobs.lista"
done
for de in 74 85; do for em in 74 85; do r $em cruzado.php /o/jobs$de.txt > "$O/cruzado_${de}_lido_no_$em.txt"; done; done
n=$(wc -l < "$O/jobs.lista")
for v in 74 85; do [ "$(grep -c '^== ' "$O/jobs$v.txt")" -eq "$n" ] || falha "jobs$v.txt sem as $n classes"; done
c() { cmp -s "$O/$1" "$O/$2" && echo "igual" || echo "DIFERE"; }
echo "artisan list:          $(c list74.txt list85.txt) ($(wc -l < "$O/list74.txt") linhas)"
echo "comandos e agenda:     $(c console74.txt console85.txt) ($(grep -c "'classe' =>" "$O/console74.txt") comandos, $(grep -c "'cron' =>" "$O/console74.txt") eventos)"
echo "jobs (payload):        $(diff <(grep -v '^command:' "$O/jobs74.txt") <(grep -v '^command:' "$O/jobs85.txt") >/dev/null && echo igual || echo DIFERE) ($(grep -c '^== ' "$O/jobs74.txt") classes; command serializado diferente em $(diff <(grep '^command' "$O/jobs74.txt") <(grep '^command' "$O/jobs85.txt") | grep -c '^<'))"
echo "jobs (estado cruzado): $(md5sum "$O"/cruzado_* | awk '{print $1}' | sort -u | wc -l) estado(s) distinto(s) em 4 leituras (1 = igual)"
echo "funcoes:               $(grep -c ' => ' "$O/funcoes74.txt") casos ($(grep -c '^array_pluck\|^str_random' "$O/funcoes74.txt") removidas + $(grep -c '^str_contains #' "$O/funcoes74.txt") str_contains); resultado diferente em $(diff <(grep ' => ' "$O/funcoes74.txt") <(grep ' => ' "$O/funcoes85.txt") | grep -c '^<'), dos quais TypeError nos dois: $(paste -d'|' <(grep ' => ' "$O/funcoes74.txt") <(grep ' => ' "$O/funcoes85.txt") | awk -F'|' '$1!=$2' | grep -c 'TypeError.*|.*TypeError')"
dep() { grep -c '^Deprecated:' "$O/err$1.txt"; }; out() { grep -v -e '^Deprecated:' -e '^$' "$O/err$1.txt"; }
echo "avisos (stderr):       7.4 $(grep -c . "$O/err74.txt") linhas, 8.5 $(grep -c . "$O/err85.txt") ($(dep 85) Deprecated, $(grep '^Deprecated:' "$O/err85.txt" | sort -u | wc -l) distintos); fora Deprecated: 7.4 $(out 74 | wc -l), 8.5 $(out 85 | wc -l)"
