"""regressao/rastro/servidor.py: vhost da arvore instrumentada (docker simulado)."""
from regressao.rastro import servidor


class DockerFalso:
    def __init__(self):
        self.conf = ""
        self.habilitado = False
        self.chamadas: list[str] = []

    def __call__(self, args, timeout, stdin=None, stdout=None):
        cmd = args[-1]
        self.chamadas.append(cmd)
        if cmd.startswith(f"cat {servidor.CONF}"):
            return self.conf.encode()
        if cmd.startswith("ls /etc/apache2/sites-enabled"):
            return b"/etc/apache2/sites-enabled/rastro.conf\n" if self.habilitado else b""
        if cmd.startswith(f"cat > {servidor.CONF}"):
            stdin.seek(0)
            self.conf = stdin.read().decode()
            return b""
        if "a2ensite" in cmd:
            self.habilitado = True
        return b""


def test_liga_vhost_e_idempotente(monkeypatch):
    falso = DockerFalso()
    monkeypatch.setattr(servidor, "_docker", falso)
    assert servidor.liga_vhost("c") is True
    assert any("a2ensite" in c and "graceful" in c for c in falso.chamadas)
    antes = len(falso.chamadas)
    assert servidor.liga_vhost("c") is False
    novas = falso.chamadas[antes:]
    assert not any("a2ensite" in c or c.startswith("cat >") for c in novas)   # nao reescreve nem recarrega


def test_mascara_do_app_bate_com_as_constantes_do_php_nos_dois_contêineres():
    """22517 = E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED & ~E_STRICT (config/application.php:27) em 7.4 e 8.5."""
    import pytest
    from regressao.nucleo.ambiente import containers_do_ambiente
    from regressao.nucleo.banco import _docker as docker_real
    c = containers_do_ambiente()
    try:
        saidas = [docker_real(["exec", n, "php", "-r",
                               "echo E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED & ~E_STRICT;"], 20).decode()
                  for n in (c.ref, c.php_novo)]
    except Exception:
        pytest.skip("contêineres docker indisponiveis")
    assert saidas == [str(servidor.MASCARA_DO_APP)] * 2


def test_vhost_usa_a_arvore_instrumentada_o_rt_e_nao_toca_na_porta_80():
    assert f"SetEnv RASTRO_MASCARA {servidor.MASCARA_DO_APP}" in servidor.VHOST
    assert f"Listen {servidor.PORTA}" in servidor.VHOST and "VirtualHost *:80>" not in servidor.VHOST
    assert f"DocumentRoot {servidor.RAIZ}" in servidor.VHOST
    assert f"php_value auto_prepend_file {servidor.RAIZ}/rt.php" in servidor.VHOST
    assert "AllowOverride All" in servidor.VHOST and "FollowSymLinks" in servidor.VHOST   # .htaccess e link simbolico
    assert servidor.url_rastro("c") == "http://localhost:8091"
