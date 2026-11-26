# PHP8-62: php-cli descartavel com o locale pt_BR (ISO-8859-1), como os Dockerfiles do 7.4 e do 8.5 (docker/php74-apache e docker/php85-apache).
# Uso: docker build --build-arg PHPV=7.4 -t t139-php74 scratchpad/locale-img   (precisa de rede so no build)
ARG PHPV=8.5
FROM php:${PHPV}-cli
RUN if grep -q bullseye /etc/os-release; then echo 'deb http://archive.debian.org/debian bullseye main' > /etc/apt/sources.list; fi \
 && apt-get -o Acquire::Check-Valid-Until=false update && apt-get install -y --no-install-recommends locales \
 && sed -i 's/^# *pt_BR ISO-8859-1/pt_BR ISO-8859-1/; s/^# *pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
