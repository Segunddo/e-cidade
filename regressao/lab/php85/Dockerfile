# Ambiente PHP 8.5 para o projeto de migração do e-cidade.
# Espelha deliberadamente as configurações do docker/php56-apache (charset ISO-8859-1,
# locale pt_BR, timezone, short_open_tag, limites do Apache) para que a ÚNICA variável
# alterada em relação ao ambiente de referência seja a versão do PHP.
FROM php:8.5-apache

LABEL projeto="e-cidade-migracao" etapa="fase-0-linha-de-base"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

RUN apt-get update && apt-get install -y --no-install-recommends \
      locales tzdata curl unzip zip git vim libxml2-utils \
      libpq-dev libzip-dev libpng-dev libjpeg62-turbo-dev libfreetype6-dev \
      libicu-dev libxml2-dev libonig-dev libcurl4-openssl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# locale pt_BR em ISO-8859-1 (o e-cidade e o banco operam em LATIN1)
RUN sed -i 's/^# *pt_BR ISO-8859-1/pt_BR ISO-8859-1/' /etc/locale.gen \
    && sed -i 's/^# *pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Extensões declaradas no composer.json do e-cidade.
# NÃO incluídas por terem sido removidas do core do PHP:
#   - interbase  -> removida no PHP 7.4 (foi para PECL)
#   - xmlrpc     -> removida no PHP 8.0 (foi para PECL)
# json, curl, openssl, fileinfo, dom, simplexml e xmlwriter já vêm habilitadas na imagem.
RUN docker-php-ext-configure gd --with-jpeg --with-freetype \
    && docker-php-ext-install -j"$(nproc)" \
        bcmath calendar gd intl mbstring pgsql pdo_pgsql soap zip exif

# php.ini calibrado para MEDIÇÃO: registra tudo, mas não injeta erro no HTML
# (display_errors=Off evita que avisos corrompam o layout e mascarem falhas reais).
RUN touch /var/log/php_errors.log \
    && chown www-data:www-data /var/log/php_errors.log \
    && chmod 666 /var/log/php_errors.log \
    && { \
      echo "short_open_tag = On"; \
      echo "date.timezone = \"America/Sao_Paulo\""; \
      echo "session.gc_maxlifetime = 7200"; \
      echo "session.save_path = \"/var/lib/php/sessions\""; \
      echo "error_reporting = E_ALL"; \
      echo "display_errors = Off"; \
      echo "log_errors = On"; \
      echo "error_log = /var/log/php_errors.log"; \
      echo "memory_limit = 512M"; \
      echo "max_execution_time = 300"; \
      echo "default_charset = \"ISO-8859-1\""; \
    } > /usr/local/etc/php/conf.d/zz-ecidade.ini

RUN { \
      echo '<VirtualHost *:80>'; \
      echo '    DocumentRoot /var/www/html'; \
      echo '    LimitRequestLine 16382'; \
      echo '    LimitRequestFieldSize 16382'; \
      echo '    Timeout 12000'; \
      echo '    AddDefaultCharset ISO-8859-1'; \
      echo '    SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1'; \
      echo '    <Directory /var/www/html>'; \
      echo '        Options +Indexes +FollowSymLinks +MultiViews'; \
      echo '        AllowOverride All'; \
      echo '        Require all granted'; \
      echo '    </Directory>'; \
      echo '    ErrorLog ${APACHE_LOG_DIR}/error.log'; \
      echo '    CustomLog ${APACHE_LOG_DIR}/access.log combined'; \
      echo '    RewriteEngine on'; \
      echo '</VirtualHost>'; \
    } > /etc/apache2/sites-available/000-default.conf \
    && a2enmod rewrite setenvif

# www-data permanece no uid 33, IGUAL ao container de referência PHP 5.6.
# Tentou-se remapear para o uid 1000 do host, mas isso criou uma assimetria de
# permissões entre os dois runtimes: arquivos de log gravados por um ficavam
# inacessíveis ao outro, e diferenças de comportamento passavam a ter causa em
# permissão, não em versão do PHP. Com o mesmo uid, a ÚNICA variável entre os
# dois ambientes é a versão do PHP — que é a premissa de todo o experimento.
# Requisito: pastas de runtime graváveis por ambos (ver `chmod 777 extension/log`).

COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
ENV COMPOSER_ALLOW_SUPERUSER=1

EXPOSE 80
WORKDIR /var/www/html

CMD ["apache2-foreground"]
