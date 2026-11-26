# Composer do PHP 8.5 (so dependencias: nao serve paginas, nao acessa banco). Imagens pinadas por digest para o lock
# do 8.5 sair igual em qualquer maquina. Extensoes = as do runtime 8.5 (docker/php85-apache), para o Composer conferir
# os ext-* do composer-85.json contra o mesmo PHP que vai rodar o codigo. Uso: docker/composer-85/composer-85.sh
FROM php:8.5-cli@sha256:50956f094e90a716d43bea28087d447555ad80510e386ab8c9c10d8c70d781a9
RUN apt-get update && apt-get install -y --no-install-recommends \
      git unzip libpq-dev libzip-dev libpng-dev libjpeg62-turbo-dev libfreetype6-dev libicu-dev libxml2-dev libonig-dev \
    && rm -rf /var/lib/apt/lists/* \
    && docker-php-ext-configure gd --with-jpeg --with-freetype \
    && docker-php-ext-install -j"$(nproc)" bcmath calendar gd intl mbstring pgsql pdo_pgsql soap zip exif
COPY --from=composer:2.11.2@sha256:919efe8e62179c71dfd31fad035fd671fe7454211c6b2aa30a10af0ab4acedba /usr/bin/composer /usr/local/bin/composer
