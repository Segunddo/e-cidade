"""regressao/rastro/php/liga.php: links da arvore instrumentada (roda no contêiner 8.5)."""
import pytest

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.tests.test_rastro_instrumentador import PHP_DIR, _envia

B = "/tmp/rastro_liga"


@pytest.fixture(scope="module")
def container():
    c = containers_do_ambiente()
    try:
        _docker(["exec", c.php_novo, "true"], 15)
    except Exception:
        pytest.skip("contêineres docker indisponiveis")
    _envia(c.php_novo, f"{B}/php", {"liga.php": (PHP_DIR / "liga.php").read_bytes()})
    return c.php_novo


def _sh(container, cmd):
    return _docker(["exec", container, "sh", "-c", cmd], 30).decode().strip()


def _liga(container, instrucoes):
    return _docker(["exec", "-i", container, "sh", "-c", f"php {B}/php/liga.php --raiz={B}/raiz --saida={B}/saida"],
                   30, stdin=_stdin(instrucoes)).decode()


def _stdin(instrucoes):
    import tempfile
    f = tempfile.TemporaryFile()
    f.write(("\n".join(instrucoes) + "\n").encode())
    f.seek(0)
    return f


def test_link_de_diretorio_substitui_diretorio_real_que_so_tem_links(container):
    # estado herdado: a saida tem `extension/log` como diretorio REAL com um link de arquivo (o www-data nao escreve ali)
    _sh(container, f"rm -rf {B}/raiz {B}/saida; mkdir -p {B}/raiz/extension/log {B}/saida/extension/log; "
                   f"echo x > {B}/raiz/extension/log/.gitignore; ln -s {B}/raiz/extension/log/.gitignore {B}/saida/extension/log/.gitignore")
    _liga(container, ["+extension/log"])
    assert _sh(container, f"[ -L {B}/saida/extension/log ] && echo link || echo dir") == "link"
    assert _sh(container, f"readlink {B}/saida/extension/log") == f"{B}/raiz/extension/log"


def test_diretorio_real_com_arquivo_proprio_nao_e_apagado(container):
    _sh(container, f"rm -rf {B}/raiz {B}/saida; mkdir -p {B}/raiz/d {B}/saida/d; echo dado > {B}/saida/d/proprio.txt")
    _liga(container, ["+d"])
    assert _sh(container, f"cat {B}/saida/d/proprio.txt") == "dado"          # nunca apaga o que nao e link
    assert _sh(container, f"[ -L {B}/saida/d ] && echo link || echo dir") == "dir"
