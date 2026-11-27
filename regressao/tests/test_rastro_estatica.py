"""regressao/rastro/php/analise.php: candidatos de risco e variaveis lidas por linha (roda no contêiner 8.5)."""
import json

import pytest

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.tests.test_rastro_instrumentador import FIXTURES, PHP_DIR, _envia

B = "/tmp/rastro_estatica"


@pytest.fixture(scope="module")
def roda():
    c = containers_do_ambiente()
    try:
        _docker(["exec", c.php_novo, "true"], 15)
    except Exception:
        pytest.skip("contêineres docker indisponiveis")
    scripts = {p.name: p.read_bytes() for p in PHP_DIR.glob("*.php")}
    _envia(c.php_novo, f"{B}/php", scripts)
    _envia(c.php_novo, f"{B}/in", {"candidatos.php": (FIXTURES / "estatica_candidatos.php").read_bytes(),
                                    "leituras.php": (FIXTURES / "estatica_leituras.php").read_bytes()})

    def _roda(modo, arquivo):
        saida = _docker(["exec", c.php_novo, "sh", "-c",
                         f"echo {arquivo} | php {B}/php/analise.php --raiz={B}/in --modo={modo} 2>&1"], 60).decode()
        return [json.loads(l) for l in saida.splitlines() if l.startswith("{")]
    return _roda


def test_candidatos_aponta_so_o_uso_sem_checagem(roda):
    r = roda("candidatos", "candidatos.php")
    achados = sorted((c["linha"], c["funcao"], c["variavel"], c["origem"]) for c in r[0]["candidatos"])
    assert achados == [(5, "pg_num_rows", "rs", 4), (20, "pg_num_rows", "rs", 19), (33, "pg_numrows", "rs", 32), (47, "fputs", "fd", 46),
                       (56, "pg_numrows", "rs", 55), (61, "pg_numrows", "rs", 60)]


def test_arquivo_sem_candidato_nao_gera_saida(roda):
    assert roda("candidatos", "leituras.php") == []


def test_leituras_lista_as_variaveis_lidas_em_cada_linha_e_nao_as_atribuidas(roda):
    r = roda("leituras", "leituras.php")[0]["leituras"]
    assert sorted(r["3"]) == ["a", "b"]  # $x = $a + $b;  -> le a e b, nao x
    assert "x" not in r["3"]
    assert sorted(r["4"]) == ["c", "x"]  # $y = f($x, $c);


def test_desestruturacao_escreve_nao_le(roda):
    r = roda("leituras", "leituras.php")[0]["leituras"]
    assert r["8"] == ["data"]                     # list($ano, $mes) = explode('-', $data): le so $data


def test_chamada_em_varias_linhas_vale_para_todas_as_linhas_dela(roda):
    r = roda("leituras", "leituras.php")[0]["leituras"]
    assert all("sql" in r[str(l)] for l in (5, 6, 7))           # a chamada db_query(...) ocupa as linhas 5 a 7
