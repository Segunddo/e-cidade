"""Segundo vhost (porta 8091) servindo a arvore instrumentada, em cada contêiner PHP.

O vhost normal (porta 80) NAO muda. O novo usa o mesmo `mod_php`, o mesmo `.htaccess` (link para o original) e
carrega `rt.php` por `auto_prepend_file`. Banco e sessoes sao os mesmos da bateria (mesmo volume).
Sem publicar porta no host: as requisicoes sao `curl` por `docker exec`, como `telas._requisita_status`.
"""
from regressao.nucleo.banco import _docker

PORTA = 8091
RAIZ = "/var/www/html/tmp/ecidade-rastro"
MAPAS = "/var/www/html/tmp/ecidade-rastro-mapas"          # fora da arvore: nenhum arquivo a mais em nenhum diretorio
RT = "/var/www/html/tmp/rastro-rt.php"                      # idem: o rt.php nao aparece na listagem da raiz
CONF = "/etc/apache2/sites-available/rastro.conf"
TIMEOUT = 60

# php.error_reporting do e-Cidade (config/application.php): E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED & ~E_STRICT.
# E o conjunto de tipos que o handler da aplicacao recebe; o rt.php so o repassa para esses (o PHP nao expoe a mascara).
MASCARA_DO_APP = 22517
# Teto de eventos por requisicao. Uma tela em laco (sys4_processa008.php) gerou 2.000.001 eventos = 340 MB so no 7.4; o
# alinhador em Python chegou a 6 GB. Rastro que bate no teto e INCONCLUSIVO (nunca reconvergente), entao o teto so evita o custo.
TETO_EVENTOS = 300_000

VHOST = f"""Listen {PORTA}
<VirtualHost *:{PORTA}>
    DocumentRoot {RAIZ}
    LimitRequestLine 16382
    LimitRequestFieldSize 16382
    Timeout 12000
    AddDefaultCharset ISO-8859-1
    SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
    SetEnv RASTRO_MASCARA {MASCARA_DO_APP}
    SetEnv RASTRO_TETO {TETO_EVENTOS}
    <Directory {RAIZ}>
        Options +Indexes +FollowSymLinks +MultiViews
        AllowOverride All
        Require all granted
        php_value auto_prepend_file {RT}
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
