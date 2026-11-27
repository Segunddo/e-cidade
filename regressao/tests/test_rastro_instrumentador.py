"""regressao/rastro/php/instrumentador.php: emenda de sondas sem mudar o comportamento (roda nos contêineres reais)."""
import io
import json
import re
import tarfile
import tempfile
from pathlib import Path

import pytest

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker

AQUI = Path(__file__).resolve().parent
FIXTURES = AQUI / "fixtures" / "rastro"
PHP_DIR = AQUI.parent / "rastro" / "php"
FUNCOES = AQUI.parent / "rastro" / "funcoes.txt"
BASE = "/tmp/rastro_t"
PAR = re.compile(rb" /\*R\*/.*? /\*R\*/", re.DOTALL)   # o espaco inicial faz parte do marcador
ISO = b"<?php\n$s = 'a\xe7\xe3o';\n$n = strlen($s);\necho $n, \"\\n\";\n"


def _tar(arquivos: dict[str, bytes]) -> io.BytesIO:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        for nome, dados in arquivos.items():
            info = tarfile.TarInfo(nome)
            info.size = len(dados)
            info.mode = 0o644
            t.addfile(info, io.BytesIO(dados))
    buf.seek(0)
    return buf


def _envia(container: str, destino: str, arquivos: dict[str, bytes]) -> None:
    with tempfile.TemporaryFile() as f:
        f.write(_tar(arquivos).read())
        f.seek(0)
        _docker(["exec", "-i", "-u", "root", container, "sh", "-c",
                 f"rm -rf {destino} && mkdir -p {destino} && tar x -C {destino} && chmod -R a+rwX {destino}"],
                60, stdin=f)


def _baixa(container: str, origem: str) -> dict[str, bytes]:
    dados = _docker(["exec", container, "tar", "c", "-C", origem, "."], 60)
    saida = {}
    with tarfile.open(fileobj=io.BytesIO(dados)) as t:
        for m in t.getmembers():
            if m.isfile():
                saida[m.name.removeprefix("./")] = t.extractfile(m).read()
    return saida


PREP = f"php -d display_errors=1 -d error_reporting=-1 -d auto_prepend_file={BASE}/stub/rt_stub.php"


def _php(container: str, *args: str) -> str:
    cmd = " ".join(args)
    return _docker(["exec", container, "sh", "-c", f"cd {BASE} && {cmd} 2>&1; true"], 60).decode("latin-1")


@pytest.fixture(scope="module")
def amb():
    c = containers_do_ambiente()
    try:
        for nome in (c.ref, c.php_novo):
            _docker(["exec", nome, "true"], 15)
    except Exception:
        pytest.skip("contêineres docker indisponiveis")
    entradas = {p.name: p.read_bytes() for p in FIXTURES.glob("*.php") if p.name != "rt_stub.php"}
    entradas["iso.php"] = ISO
    stub = (FIXTURES / "rt_stub.php").read_bytes()
    _envia(c.php_novo, f"{BASE}/in", entradas)
    scripts = {"php/" + p.name: p.read_bytes() for p in PHP_DIR.glob("*.php")}
    scripts["funcoes.txt"] = FUNCOES.read_bytes()
    _envia(c.php_novo, f"{BASE}/ferr", scripts)
    lista = "\n".join(sorted(entradas)) + "\n"
    with tempfile.TemporaryFile() as f:
        f.write(lista.encode())
        f.seek(0)
        resp = _docker(["exec", "-i", c.php_novo, "sh", "-c",
                        f"mkdir -p {BASE}/out && php {BASE}/ferr/php/instrumentador.php --raiz={BASE}/in "
                        f"--saida={BASE}/out --funcoes={BASE}/ferr/funcoes.txt"], 120, stdin=f).decode()
    status = {}
    for linha in resp.splitlines():
        if linha.startswith("{"):
            j = json.loads(linha)
            status[j["arquivo"]] = j
    saidas = _baixa(c.php_novo, f"{BASE}/out")
    for nome in (c.ref, c.php_novo):
        _envia(nome, f"{BASE}/in", entradas)
        _envia(nome, f"{BASE}/stub", {"rt_stub.php": stub})
        _envia(nome, f"{BASE}/out", {k: v for k, v in saidas.items() if not k.endswith(".map.json")})
    return dict(c=c, entradas=entradas, saidas=saidas, status=status, resp=resp)


def test_remover_sondas_devolve_o_arquivo_original_byte_a_byte(amb):
    for nome, original in amb["entradas"].items():
        assert amb["status"][nome]["status"] in ("ok", "sem_parse"), (nome, amb["resp"][:500])
        assert PAR.sub(b"", amb["saidas"][nome]) == original, nome


def test_numero_de_linhas_nao_muda(amb):
    for nome, original in amb["entradas"].items():
        assert amb["saidas"][nome].count(b"\n") == original.count(b"\n"), nome


def test_basico_tem_sondas_de_todos_os_tipos(amb):
    assert amb["status"]["basico.php"]["status"] == "ok"
    mapa = json.loads(amb["saidas"]["basico.php.map.json"])
    tipos = {v["tipo"] for v in mapa.values()}
    assert {"atrib", "chamada", "ramo", "retorno", "excecao"} <= tipos
    assert PAR.sub(b"", amb["saidas"]["basico.php"]) == amb["entradas"]["basico.php"]


@pytest.mark.parametrize("lado", ["ref", "php_novo"])
def test_arquivo_instrumentado_passa_em_lint_74_e_85(amb, lado):
    c = getattr(amb["c"], lado)
    for nome in amb["entradas"]:
        if amb["status"][nome]["status"] != "ok":
            continue
        assert "No syntax errors" in _php(c, "php -l", f"out/{nome}"), (lado, nome)


def test_arquivo_que_nao_parseia_fica_sem_sonda_e_e_registrado(amb):
    assert amb["status"]["invalido.php"]["status"] == "sem_parse"
    assert amb["status"]["invalido.php"]["sondas"] == 0
    assert amb["saidas"]["invalido.php"] == amb["entradas"]["invalido.php"]


@pytest.mark.parametrize("lado", ["ref", "php_novo"])
@pytest.mark.parametrize("nome", ["basico.php", "dinamico.php", "efeito.php", "iso.php", "divisao.php"])
def test_comportamento_igual_ao_original(amb, lado, nome):
    c = getattr(amb["c"], lado)
    orig = _php(c, PREP, f"in/{nome}")
    inst = _php(c, PREP, f"out/{nome}")
    # saida REAL (sem erro, nao vazia): senao a igualdade seria vazia nos dois lados e nao provaria nada
    assert orig.strip() != "" and "Fatal" not in orig and "Parse error" not in orig, orig[:300]
    assert orig == inst


def test_chamada_nao_e_avaliada_duas_vezes(amb):
    assert amb["status"]["efeito.php"]["sondas"] > 0
    assert _php(amb["c"].ref, PREP, "out/efeito.php").strip() == "323"


def test_codigo_dinamico_nao_quebra(amb):
    assert amb["status"]["dinamico.php"]["status"] == "ok"


def test_if_sem_chaves_e_com_chaves(amb):
    saida = _php(amb["c"].php_novo, PREP, "out/basico.php")
    assert "sem chaves" in saida and "if-chaves" in saida
