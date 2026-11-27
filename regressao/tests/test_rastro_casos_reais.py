"""Casos reais do rastreador (contêineres docker): a causa aponta a linha certa sem o migrador ler log nenhum."""
import pytest

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.rastro import __main__ as cli


@pytest.fixture(scope="module")
def resultados(tmp_path_factory):
    c = containers_do_ambiente()
    try:
        for n in (c.ref, c.php_novo):
            _docker(["exec", n, "true"], 15)
        _docker(["exec", c.php_novo, "test", "-f", "/var/www/html/tmp/ecidade-rastro/app.php"], 15)
    except Exception:
        pytest.skip("contêineres docker ou arvore instrumentada indisponiveis (rode `python -m regressao.rastro instrumenta`)")
    saida = tmp_path_factory.mktemp("rastro")
    return cli.rastreia_telas(["cad2_setor002.php", "con2_anexo_i_2014.php", "con2_lrfgarantias002_2010.php"], saida)


def test_pg_num_rows_sobre_false_aponta_a_linha_da_tela_e_o_dado_que_a_alimentou(resultados):
    r = resultados["cad2_setor002.php"]
    assert r.veredito == "DIVERGE-CAUSAL" and r.causal.motivo == "aviso_x_excecao"
    assert (r.causal.arquivo, r.causal.linha) == ("cad2_setor002.php", 79)
    assert r.cadeia[-1].nome == "rsSql" and r.cadeia[-1].valor["r"] == "false"      # a consulta falhou: o dado chegou como false
    assert "sSql" in [e.nome for e in r.cadeia]


def test_checkdate_com_string_aponta_dbdate_e_as_partes_vazias_da_data(resultados):
    r = resultados["con2_anexo_i_2014.php"]
    assert (r.causal.arquivo, r.causal.linha) == ("std/DBDate.php", 203)
    assert {e.nome for e in r.cadeia} == {"ano", "mes", "dia"}


def test_pdf_aponta_o_menu_do_rodape_em_pdf_php(resultados):
    r = resultados["con2_lrfgarantias002_2010.php"]
    assert (r.causal.arquivo, r.causal.linha) == ("fpdf151/pdf.php", 186)
    assert [e.nome for e in r.cadeia][-1] == "rsMenuAcess"
