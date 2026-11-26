#!/usr/bin/env bash
# Composer do PHP 8.5: lista ecidade/composer-85.json, trava ecidade/composer-85.lock, vendor em runtime-85/vendor
# (fora de ecidade/: o 7.4 nunca o ve). O composer.json/.lock e o vendor/ do 7.4 nao sao tocados.
# Uso (raiz do repositorio):
#   bash docker/composer-85/composer-85.sh <comando do composer> [opcoes]
#   ex.: gerar o lock:  bash docker/composer-85/composer-85.sh update --no-install --no-scripts
#        instalar:      bash docker/composer-85/composer-85.sh install --no-scripts
#   (sem --no-plugins: o cweagans/composer-patches, o unico liberado em config.allow-plugins, aplica os patches)
# Registro: docs/registro/estrutura-85.md
set -euo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"
IMG=ecidade-composer-85:2.11.2
docker build -q -t "$IMG" "$R/docker/composer-85" >/dev/null
mkdir -p "$R/runtime-85/vendor" "$R/runtime-85/composer-home"
# ecidade/vendor e o ponto de montagem do vendor do 8.5 dentro de /app. Sem ele (checkout novo: o vendor/ do 7.4 nao e
# versionado) o Docker o cria como root:root 755 e o composer install do 7.4 deixa de conseguir gravar nele. Criado aqui,
# vazio e com o dono de quem chama, fica no mesmo estado de um checkout sem vendor/. Se ja existe, nao e tocado.
mkdir -p "$R/ecidade/vendor"
# GIT_CONFIG_*: o repositorio vcs do dbseller/session no composer.json do PR e git@github.com (SSH) e a imagem nao tem
# ssh; o git troca git@github.com: por https://github.com/ (repositorio publico), sem mudar o composer-85.json.
# --network host: so para baixar pacotes (a rede bridge desta maquina nao resolve DNS); --init: o timeout derruba o PHP
exec docker run --rm --init --network host -u "$(id -u):$(id -g)" \
  -v "$R/ecidade:/app" -v "$R/runtime-85/vendor:/app/vendor" -v "$R/runtime-85/composer-home:/composer" \
  -e COMPOSER=composer-85.json -e COMPOSER_HOME=/composer -w /app \
  -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf -e GIT_CONFIG_VALUE_0=git@github.com: \
  "$IMG" composer --no-interaction "$@"
