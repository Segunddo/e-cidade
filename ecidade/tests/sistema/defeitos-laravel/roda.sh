#!/usr/bin/env bash
# Roda cada trecho no 7.4 (vendor do composer.lock do PR) e no 8.5 (vendor da integracao: Laravel 13) por roda-isolado.sh
# e mostra a saida de cada um e se sao iguais. Uso (raiz do repositorio): bash ecidade/tests/sistema/defeitos-laravel/roda.sh [trecho ...]
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; D="$R/ecidade/tests/sistema/defeitos-laravel"
V74="${TESTA_VENDOR74:-$R/runtime-85/referencia-74/vendor}"; V85="${TESTA_VENDOR85:-$R/runtime-85/vendor}"
O="$(mktemp -d)"; trap 'rm -rf "$O"' EXIT
avisos() { local n; n=$(grep -cE '^(Deprecated|Warning|Notice|Fatal)' "$1" 2>/dev/null); echo "${n:-0}"; }
rodar() { # nome trecho [args]
  local nome="$1" t="$D/$2"; shift 2
  for v in 7.4 8.5; do
    ven="$V74"; [ "$v" = 8.5 ] && ven="$V85"
    VENDOR="$ven" STDERR_ARQ="$O/$nome.$v.err" bash "$R/docker/composer-85/roda-isolado.sh" "$v" "$t" "$@" > "$O/$nome.$v.out" 2> "$O/$nome.$v.rc"
    echo "rc=$?" >> "$O/$nome.$v.rc"
  done
  echo "=== $nome"
  echo "--- 7.4 ($(tail -1 "$O/$nome.7.4.rc"), avisos $(avisos "$O/$nome.7.4.err"))"; cat "$O/$nome.7.4.out" | cut -c1-200
  echo "--- 8.5 ($(tail -1 "$O/$nome.8.5.rc"), avisos $(avisos "$O/$nome.8.5.err"))"; cat "$O/$nome.8.5.out" | cut -c1-200
  if cmp -s "$O/$nome.7.4.out" "$O/$nome.8.5.out"; then echo "=> IGUAL"; else echo "=> DIFERE"; diff "$O/$nome.7.4.out" "$O/$nome.8.5.out" | sed 's/^/   /' | head -12; fi
  [ -s "$O/$nome.7.4.err" ] && { echo "   stderr 7.4:"; grep -v '^$' "$O/$nome.7.4.err" | sort | uniq -c | sort -rn | head -3 | cut -c1-200 | sed 's/^/     /'; }
  [ -s "$O/$nome.8.5.err" ] && { echo "   stderr 8.5:"; grep -v '^$' "$O/$nome.8.5.err" | sort | uniq -c | sort -rn | head -3 | cut -c1-200 | sed 's/^/     /'; }
}
[ $# -gt 0 ] && { for t in "$@"; do rodar "${t%.php}" "$t"; done; exit 0; }
rodar 01_cache_ttl 01_cache_ttl.php; rodar 02_helpers 02_helpers.php; rodar 03_env_cache 03_env_cache.php
rodar 04_form_request 04_form_request.php; rodar 06_classe_duplicada 06_classe_duplicada.php; rodar 07_factory 07_factory.php
rodar 08c_pacotes 08c_pacotes.php; rodar 08a_schedule_list 08_artisan.php schedule:list; rodar 08b_list_json 08_artisan.php list --format=json
rodar 08d_list_json_migrate 08_artisan.php list migrate --format=json; rodar 09_cast_datetime 09_cast_datetime.php
