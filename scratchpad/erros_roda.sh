#!/bin/bash
# PHP8-62: configuracao efetiva de erros (o que aparece na resposta e o que vai para o log), 7.4 x 8.5, sem banco e sem rede.
# Sobe o Apache da imagem (mod_php) dentro de um conteiner --network none e chama erros_probe.php por localhost.
# Uso: erros_roda.sh <ecidade> <vendor L8 p/ 7.4> <vendor L8 p/ 8.5> <img 7.4> <img 8.5> <env de teste> <saida>
set -u
E=$(realpath "$1"); V74=$(realpath "$2"); V85=$(realpath "$3"); I74=$4; I85=$5; ENVF=$(realpath "$6"); O=$(realpath -m "$7"); T=$(dirname "$(realpath "$0")")
mkdir -p "$O"
# pontos de montagem do conteiner: ecidade/.env e ecidade/vendor precisam existir no host
[ -e "$E/.env" ] || { echo "ERRO: falta $E/.env (o .env de teste e montado em /e/.env; sem o ponto de montagem o docker falha)"; exit 1; }
[ -d "$E/vendor" ] || { echo "ERRO: falta $E/vendor (ponto de montagem do vendor; crie a pasta vazia ou rode o composer install do composer.lock do PR)"; exit 1; }
for v in 74 85; do
  img=$I74; ven=$V74; [ $v = 85 ] && img=$I85 && ven=$V85
  APPLOCAL=""; [ -f "$E/config/application.php" ] && APPLOCAL="-v $O/vazio.php:/e/config/application.php:ro"   # a copia local nao versionada fica de fora: vale so o config/application.default.php
  : > "$O/vazio.php"
  D="$O/docroot"; rm -rf "$D" "$O/ext$v" "$O/sto$v"; mkdir -p "$D" "$O/ext$v" "$O/sto$v"
  cp "$T/erros_probe.php" "$D/probe.php"; cp "$E/.user.ini" "$D/.user.ini"     # o .user.ini do ecidade ao lado do script
  (cd "$E/storage" && find . -type d -exec mkdir -p "$O/sto$v/{}" \;); chmod -R 777 "$O/ext$v" "$O/sto$v" "$D"
  docker run --rm --network none -v "$D:/var/www/html:ro" -v "$E:/e:ro" -v "$ven:/e/vendor:ro" -v "$ENVF:/e/.env:ro" $APPLOCAL \
    --tmpfs /e/bootstrap/cache:mode=1777 -v "$O/ext$v:/e/extension/log" -v "$O/sto$v:/e/storage" -v "$O:/o" "$img" bash -c '
      : > /var/log/php_errors.log; chmod 666 /var/log/php_errors.log
      apache2ctl start >/dev/null 2>&1; for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null localhost/probe.php && break; sleep 1; done
      pega() {  # pega <rotulo> <query>: a 1a requisicao com o Apache recem-iniciado (opcache frio) e a 2a logo depois (opcache quente)
        for fase in frio quente; do
          [ $fase = frio ] && { apache2ctl stop >/dev/null 2>&1; sleep 1; apache2ctl start >/dev/null 2>&1; for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null localhost/nada && break; sleep 1; done; }
          : > /var/log/php_errors.log; rm -f /e/extension/log/*.log /e/storage/logs/*.log 2>/dev/null
          curl -s "localhost/probe.php?$2" > /o/resp_'$v'_$1_$fase.txt
          cp /var/log/php_errors.log /o/log_php_'$v'_$1_$fase.txt
          cat /e/extension/log/error.log > /o/log_ecidade_'$v'_$1_$fase.txt 2>/dev/null || : > /o/log_ecidade_'$v'_$1_$fase.txt
          cat /e/storage/logs/*.log > /o/log_laravel_'$v'_$1_$fase.txt 2>/dev/null || : > /o/log_laravel_'$v'_$1_$fase.txt
        done
      }
      pega a "camada=a"; pega a_exibir "camada=a&exibir=on"; pega b "camada=b"; pega b_exibir "camada=b&exibir=on"; pega c "camada=c"; pega c_exibir "camada=c&exibir=on"
      pega b_er_texto "camada=b&er=E_ALL%20%26%20~NOTICE"; pega b_er_zero "camada=b&er=0"
      php -r "echo json_encode([\"error_reporting\"=>ini_get(\"error_reporting\"),\"display_errors\"=>ini_get(\"display_errors\"),\"log_errors\"=>ini_get(\"log_errors\"),\"error_log\"=>ini_get(\"error_log\"),\"html_errors\"=>ini_get(\"html_errors\"),\"ini\"=>php_ini_loaded_file()]),\"\n\";" > /o/cli_'$v'.json
      php -v | head -1 > /o/versao_'$v'.txt
    '
  rc=$?; [ $rc -eq 0 ] || { echo "ERRO: docker run do php$v saiu com $rc"; exit $rc; }
  for f in a b c; do [ -s "$O/resp_${v}_${f}_frio.txt" ] || { echo "ERRO: resposta vazia ou ausente: resp_${v}_${f}_frio.txt"; exit 1; }; done
  echo "php$v: $(ls "$O" | grep -c "_$v")"
done
