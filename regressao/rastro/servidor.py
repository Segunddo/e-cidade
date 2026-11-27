"""Segundo vhost (porta 8091) servindo a arvore instrumentada, em cada contêiner PHP.

O vhost normal (porta 80) NAO muda. O novo usa o mesmo `mod_php`, o mesmo `.htaccess` (link para o original) e
carrega `rt.php` por `auto_prepend_file`. Banco e sessoes sao os mesmos da bateria (mesmo volume).
Sem publicar porta no host: as requisicoes sao `curl` por `docker exec`, como `telas._requisita_status`.
"""
from regressao.nucleo.banco import _docker

PORTA = 8091
RAIZ = "/var/www/html/tmp/ecidade-rastro"
CONF = "/etc/apache2/sites-available/rastro.conf"
TIMEOUT = 60

VHOST = f"""Listen {PORTA}
<VirtualHost *:{PORTA}>
    DocumentRoot {RAIZ}
    LimitRequestLine 16382
    LimitRequestFieldSize 16382
    Timeout 12000
    AddDefaultCharset ISO-8859-1
    SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
    <Directory {RAIZ}>
        Options +Indexes +FollowSymLinks +MultiViews
        AllowOverride All
        Require all granted
        php_value auto_prepend_file {RAIZ}/rt.php
    </Directory>
    ErrorLog ${{APACHE_LOG_DIR}}/rastro_error.log
    CustomLog ${{APACHE_LOG_DIR}}/rastro_access.log combined
    RewriteEngine on
</VirtualHost>
"""


def url_rastro(container: str | None = None) -> str:
    return f"http://localhost:{PORTA}"


def _le_conf(container: str) -> str:
    try:
        return _docker(["exec", container, "sh", "-c", f"cat {CONF} 2>/dev/null; true"], TIMEOUT).decode()
    except Exception:
        return ""


def liga_vhost(container: str) -> bool:
    """Garante o vhost no contêiner. Idempotente: se ja esta igual e habilitado, nao reescreve nem recarrega.
    Devolve True se mudou alguma coisa."""
    if _le_conf(container) == VHOST:
        habilitado = _docker(["exec", container, "sh", "-c",
                              f"ls /etc/apache2/sites-enabled/rastro.conf 2>/dev/null; true"], TIMEOUT).decode().strip()
        if habilitado:
            return False
    import tempfile
    with tempfile.TemporaryFile() as f:
        f.write(VHOST.encode())
        f.seek(0)
        _docker(["exec", "-i", "-u", "root", container, "sh", "-c", f"cat > {CONF}"], TIMEOUT, stdin=f)
    _docker(["exec", "-u", "root", container, "sh", "-c",
             "a2ensite rastro >/dev/null && (apache2ctl graceful || apachectl graceful)"], TIMEOUT)
    return True
