#!/usr/bin/env bash
# Roda cada trecho de traducao no 7.4 (vendor do composer.lock do PR) e no 8.5 (vendor da integracao) por roda-isolado.sh e mostra
# se a saida e igual byte a byte; senao, as linhas que diferem. Uso (raiz do repositorio): bash ecidade/tests/sistema/traducoes/roda.sh
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; D="$R/ecidade/tests/sistema/traducoes"
V74="${TESTA_VENDOR74:-$R/runtime-85/referencia-74/vendor}"; V85="${TESTA_VENDOR85:-$R/runtime-85/vendor}"
O="$(mktemp -d)"; trap 'rm -rf "$O"' EXIT; rc=0
for t in idioma regras notificacoes_auth; do
  for v in 7.4 8.5; do
    ven="$V74"; [ "$v" = 8.5 ] && ven="$V85"
    VENDOR="$ven" STDERR_ARQ="$O/$t.$v.err" bash "$R/docker/composer-85/roda-isolado.sh" "$v" "$D/$t.php" > "$O/$t.$v.out" 2> "$O/$t.$v.rc" || { echo "ERRO: $t no $v"; cat "$O/$t.$v.rc"; exit 1; }
  done
  n=$(wc -l < "$O/$t.7.4.out")
  if cmp -s "$O/$t.7.4.out" "$O/$t.8.5.out"; then echo "=== $t: IGUAL ($n linhas)"; else
    echo "=== $t: DIFERE ($(diff "$O/$t.7.4.out" "$O/$t.8.5.out" | grep -c '^<') linhas de $n)"; diff "$O/$t.7.4.out" "$O/$t.8.5.out" | grep '^[<>]' | cut -c1-150; rc=1; fi
  for v in 7.4 8.5; do [ -s "$O/$t.$v.err" ] && echo "    avisos $v: $(grep -cE '^(Deprecated|Warning|Notice)' "$O/$t.$v.err")"; done
done
exit $rc
