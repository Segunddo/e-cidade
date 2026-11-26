#!/usr/bin/env bash
# Teste do roda-isolado.sh num clone limpo (sem ecidade/.env, ecidade/vendor nem runtime-85).
# Uso: bash docker/composer-85/testa-roda-isolado.sh
# O caso do kernel do Laravel precisa dos vendors: TESTA_VENDOR74 (composer install do ecidade/composer.lock, padrao
# runtime-85/referencia-74/vendor) e TESTA_VENDOR85 (padrao runtime-85/vendor) do repositorio que roda o teste.
set -uo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"
V74="${TESTA_VENDOR74:-$R/runtime-85/referencia-74/vendor}"; V85="${TESTA_VENDOR85:-$R/runtime-85/vendor}"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
git clone -q --local "$R" "$W/clone" || { echo "FALHOU: clone"; exit 1; }
cp "$R/docker/composer-85/roda-isolado.sh" "$W/clone/docker/composer-85/"   # versao em teste (pode ainda nao estar no commit)
S="$W/clone/docker/composer-85/roda-isolado.sh"
mkdir "$W/t"; echo '<?php echo PHP_MAJOR_VERSION, ".", PHP_MINOR_VERSION, PHP_EOL;' > "$W/t/ok.php"
echo '<?php exit(3);' > "$W/t/erro.php"; echo '<?php // nada' > "$W/t/vazio.php"
cat > "$W/t/kernel.php" <<'PHP'
<?php
// sobe o kernel do Laravel do PR: precisa de bootstrap/cache e storage gravaveis e das variaveis de ambiente de teste
require '/app/vendor/autoload.php';
$app = require '/app/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
echo get_class($app), ' env=', $app->environment(), ' php=', PHP_MAJOR_VERSION, '.', PHP_MINOR_VERSION, PHP_EOL;
PHP
n=0; f=0
ok()   { n=$((n+1)); if "$@" >"$W/o" 2>"$W/e"; then echo "ok   $*"; else f=$((f+1)); echo "FALHOU (esperava rc=0): $*"; cat "$W/e"; fi; }
quebra() { n=$((n+1)); if "$@" >"$W/o" 2>"$W/e"; then f=$((f+1)); echo "FALHOU (esperava rc!=0): $*"; else echo "ok   rc=$? $*"; grep -q "roda-isolado: ERRO" "$W/e" || { f=$((f+1)); echo "FALHOU: sem mensagem"; }; fi; }
ok bash "$S" 7.4 "$W/t/ok.php"; grep -q '^7\.4' "$W/o" || { f=$((f+1)); echo "FALHOU: saida 7.4: $(cat "$W/o")"; }
ok bash "$S" 8.5 "$W/t/ok.php"; grep -q '^8\.5' "$W/o" || { f=$((f+1)); echo "FALHOU: saida 8.5: $(cat "$W/o")"; }
[ ! -e "$W/clone/ecidade/.env" ] && [ "$(stat -c %U "$W/clone/ecidade/vendor")" = "$(id -un)" ] && echo "ok   sem ecidade/.env na arvore; ecidade/vendor do usuario" || { f=$((f+1)); echo "FALHOU: .env criado ou vendor de root"; }
for v in 7.4 8.5; do
  ven="$V74"; [ "$v" = 8.5 ] && ven="$V85"
  ok env VENDOR="$ven" bash "$S" "$v" "$W/t/kernel.php"
  grep -q "^App.Application env=local php=$v" "$W/o" || { f=$((f+1)); echo "FALHOU: kernel $v: $(head -c 300 "$W/o")"; }
  grep -q "Deprecated" "$W/o" && { f=$((f+1)); echo "FALHOU: Deprecated no stdout ($v)"; }
done
quebra bash "$S" 7.4 "$W/t/erro.php"
quebra bash "$S" 8.5 "$W/t/vazio.php"
quebra env IMAGEM=nao-existe-xyz bash "$S" 7.4 "$W/t/ok.php"
printf '#!/usr/bin/env bash\n[ "$1" = image ] && exit 0\necho "docker: Error response: mountpoint read-only" >&2; exit 125\n' > "$W/dockerquebrado"; chmod +x "$W/dockerquebrado"
quebra env DOCKER="$W/dockerquebrado" bash "$S" 8.5 "$W/t/ok.php"
quebra bash "$S" 5.6 "$W/t/ok.php"
quebra bash "$S" 7.4 "$W/t/nao-existe.php"
# --- opcoes: ENV_EXTRA, stdin, EXTRA_RO, avisos separados (AVISOS, STDERR_ARQ)
cat > "$W/t/opcoes.php" <<'PHP'
<?php
echo 'API=', getenv('API_DATA_AVAILABLE_URL'), ' extra=', getenv('OUTRA'), PHP_EOL;
echo 'stdin=', trim((string)stream_get_contents(STDIN)), PHP_EOL;
echo 'ro=', @file_get_contents('/dados/oi.txt'), PHP_EOL;
echo 'gravavel=', var_export(@file_put_contents('/dados/x', '1') !== false, true), PHP_EOL;
echo 'display_errors=', ini_get('display_errors'), ' log_errors=', var_export((bool)ini_get('log_errors'), true), PHP_EOL;
echo $variavel_inexistente;
PHP
mkdir "$W/dados"; echo -n conteudo-ro > "$W/dados/oi.txt"; printf 'API_DATA_AVAILABLE_URL=http://api.invalid/\nOUTRA=valor\n' > "$W/envx"
for v in 7.4 8.5; do
  ven="$V74"; [ "$v" = 8.5 ] && ven="$V85"
  echo ola | env STDIN=1 VENDOR="$ven" ENV_EXTRA="$W/envx" EXTRA_RO="$W/dados:/dados" STDERR_ARQ="$W/err$v" bash "$S" "$v" "$W/t/opcoes.php" > "$W/o$v" 2>"$W/e$v"; rc=$?; n=$((n+1))
  { [ $rc -eq 0 ] && grep -q '^API=http://api.invalid/ extra=valor$' "$W/o$v" && grep -q '^stdin=ola$' "$W/o$v" && grep -q '^ro=conteudo-ro$' "$W/o$v" \
    && grep -q '^gravavel=false$' "$W/o$v" && grep -q '^display_errors=.*log_errors=false' "$W/o$v"; } && echo "ok   opcoes $v (ENV_EXTRA, stdin, EXTRA_RO somente leitura)" || { f=$((f+1)); echo "FALHOU: opcoes $v rc=$rc"; cat "$W/o$v" "$W/e$v"; }
  n=$((n+1)); { grep -q 'Undefined variable' "$W/err$v" && ! grep -q 'Undefined variable' "$W/o$v" "$W/e$v"; } && echo "ok   aviso do $v so no STDERR_ARQ: $(grep -o '[A-Za-z ]*: Undefined variable' "$W/err$v" | head -1)" || { f=$((f+1)); echo "FALHOU: aviso $v"; cat "$W/err$v"; }
done
n=$((n+1)); grep -q '^Warning: Undefined' "$W/err8.5" && grep -q '^Notice: Undefined' "$W/err7.4" && echo "ok   a diferenca 7.4 (Notice) x 8.5 (Warning) fica visivel" || { f=$((f+1)); echo "FALHOU: Notice x Warning"; }
n=$((n+1)); echo x | env STDIN=1 VENDOR="$V85" AVISOS=0 STDERR_ARQ="$W/errsem" bash "$S" 8.5 "$W/t/opcoes.php" >"$W/o" 2>/dev/null; { ! grep -q Undefined "$W/errsem" && grep -q 'display_errors=' "$W/o"; } && echo "ok   AVISOS=0 nao liga display_errors (php.ini da imagem)" || { f=$((f+1)); echo "FALHOU: AVISOS=0"; cat "$W/o"; }
quebra env EXTRA_RO="/nao/existe:/x" bash "$S" 7.4 "$W/t/ok.php"
quebra env ENV_EXTRA="$W/nao-existe" bash "$S" 7.4 "$W/t/ok.php"
# --- APP_KEY de teste gerada na hora (nunca a real)
echo '<?php echo getenv("APP_KEY"), PHP_EOL;' > "$W/t/appkey.php"
bash "$S" 7.4 "$W/t/appkey.php" > "$W/k1" 2>/dev/null; bash "$S" 7.4 "$W/t/appkey.php" > "$W/k2" 2>/dev/null; printf 'APP_KEY=base64:%s\n' "$(head -c 32 /dev/zero | base64)" > "$W/envkey"
env ENV_EXTRA="$W/envkey" bash "$S" 7.4 "$W/t/appkey.php" > "$W/k3" 2>/dev/null
n=$((n+1)); { k=$(sed 's/^base64://' "$W/k1"); [ "$(printf %s "$k" | base64 -d 2>/dev/null | wc -c)" -eq 32 ] && grep -q '^base64:' "$W/k1" && ! cmp -s "$W/k1" "$W/k2" \
  && [ "$(cat "$W/k3")" = "base64:$(head -c 32 /dev/zero | base64)" ]; } && echo "ok   APP_KEY: 32 bytes, nova a cada execucao, ENV_EXTRA a fixa" || { f=$((f+1)); echo "FALHOU: APP_KEY: $(cat "$W/k1" "$W/k2" "$W/k3")"; }
# --- stdin so com STDIN=1: um while read do chamador nao pode ser consumido pelo script
printf '<?php echo "ok\\n";' > "$W/t/curto.php"
for v in 7.4 8.5; do
  n=$((n+1)); linhas=$(printf 'a\nb\nc\n' | { c=0; while read -r _; do bash "$S" "$v" "$W/t/curto.php" >/dev/null 2>&1; c=$((c+1)); done; echo $c; })
  [ "$linhas" = 3 ] && echo "ok   while read com 3 linhas roda 3x no $v (stdin do chamador intacto sem STDIN=1)" || { f=$((f+1)); echo "FALHOU: while read rodou ${linhas}x no $v (esperava 3)"; }
done
echo '<?php echo trim(stream_get_contents(STDIN)), "|", PHP_EOL;' > "$W/t/le.php"
n=$((n+1)); r=$(printf 'x\ny\n' | env STDIN=1 VENDOR="$V85" bash "$S" 8.5 "$W/t/le.php" 2>/dev/null | tr '\n' ' '); r2=$(printf 'x\ny\n' | env VENDOR="$V85" bash "$S" 8.5 "$W/t/le.php" 2>/dev/null | tr '\n' ' ')
[ "$r" = "x y| " ] && [ "$r2" = "| " ] && echo "ok   STDIN=1 repassa o stdin; sem ele o trecho le vazio" || { f=$((f+1)); echo "FALHOU: stdin '$r' / '$r2'"; }
echo "$((n-f))/$n"; [ "$f" -eq 0 ]
