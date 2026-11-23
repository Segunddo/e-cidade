"""Task 4 (base 7.4): orquestrador e fluxos com nomes/versoes do e74, avisos do relatorio e o Desktop do PR."""
import re
from pathlib import Path

import pytest

from regressao.completa import fluxos, orquestra
from regressao.nucleo.veredito import Caso, Veredito
from regressao.tests.test_completa import carrega, executores, roda  # noqa: F401 (fixture autouse reaproveitada)
from regressao.tests.test_completa import _sem_ambiente_real  # noqa: F401

I, D, N, E = Veredito.IDENTICO, Veredito.DIVERGE, Veredito.INCONCLUSIVO, Veredito.ERRO_AMBIENTE
RAIZ = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("arq", ["completa/orquestra.py", "completa/fluxos.py"])
def test_completa_nao_fala_da_pilha_antiga(arq):
    texto = (RAIZ / "regressao" / arq).read_text(encoding="utf-8")
    assert not re.search(r"\b5\.6\b|:80(80|85|87|90)\b|ecidade_php56|inicio\.php|Laravel 12 nao existe", texto)


def _resumo(tmp_path) -> str:
    return (tmp_path / "saida" / "resumo.md").read_text(encoding="utf-8")


def test_resumo_abre_com_o_resultado_e_os_avisos_fixos(tmp_path):
    roda(tmp_path)
    r = _resumo(tmp_path)
    assert r.splitlines()[2].startswith("**Resultado: VERDE (saida 0)")
    assert "REFERENCIA: o gabarito e a base PHP 7.4/Laravel 8" in r
    assert "INCONCLUSIVO e ERRO_AMBIENTE NUNCA sao aprovacao" in r
    assert "paridade referencia 7.4 x 8.5" in r
    assert "COMO-USAR.md" in r


@pytest.mark.parametrize("casos,inicio", [
    ([Caso("tela:a.php", "x", D, "ref=200 85=500")], "VERMELHO (saida 1): 1 divergencia"),
    ([Caso("tela:a.php", "x", E, "container fora")], "ERRO (saida 2)"),
    ([Caso("tela:a.php", "x", N, "pagina de erro nos dois")], "VERDE (saida 0): nenhuma divergencia nova; 1 caso(s) INCONCLUSIVO"),
    ([Caso("tela:a.php", "x", D, "sabida", conhecida=True)], "VERDE (saida 0)"),
])
def test_linha_de_resultado_por_situacao(tmp_path, casos, inicio):
    roda(tmp_path, executores=executores(php={"casos": casos}))
    assert f"**Resultado: {inicio}" in _resumo(tmp_path)


def test_alvo_laravel_igual_a_referencia_avisa_que_e_auto_consistencia(tmp_path, monkeypatch):
    monkeypatch.delenv("REGRESSAO_REF_URL", raising=False)
    ex = executores(laravel={"casos": [Caso("rota:GET:/a", "laravel", I)], "meta": {"alvo": "http://localhost:8074/"}})
    roda(tmp_path, executores=ex)
    assert "ALVO LARAVEL = REFERENCIA" in _resumo(tmp_path)


def test_alvo_laravel_laboratorio_nao_traz_aviso_de_auto_consistencia(tmp_path, monkeypatch):
    monkeypatch.delenv("REGRESSAO_REF_URL", raising=False)
    ex = executores(laravel={"casos": [Caso("rota:GET:/a", "laravel", I)], "meta": {"alvo": "http://localhost:8187"}})
    roda(tmp_path, executores=ex)
    assert "ALVO LARAVEL = REFERENCIA" not in _resumo(tmp_path)


def test_veredito_geral_nao_comparavel_e_erro():
    meta = {"totais": {"ERRO_AMBIENTE": 0, "INCONCLUSIVO": 0}, "comparavel": False, "divergencias": {"novas": 0}}
    assert orquestra.veredito_geral(meta).startswith("ERRO (saida 2)")


def test_ajuda_do_alvo_laravel_aponta_o_laboratorio_e74(capsys):
    assert orquestra.main(["--help"]) == 0
    ajuda = " ".join(capsys.readouterr().out.split())
    assert ":8187, laboratorio" in ajuda and ":8074" in ajuda


# ---------------------------------------------------------------- fluxos no Desktop do PR

def test_coletor_ignora_o_ping_periodico_do_desktop():
    c = fluxos.Coletor()
    c.resposta("GET", "http://p/extension/desktop/Window/ping/", 200, "xhr", "PHP-7.4 (referencia)")
    c.resposta("GET", "http://p/w/1/extension/desktop/Window/ping/", 500, "xhr", None)
    c.resposta("GET", "http://p/extension/desktop/Menu/getAreas/?iInstitId=1", 200, "xhr", "PHP-7.4 (referencia)")
    p = c.fecha_passo()
    assert p["requisicoes"] == ["GET 200 /extension/desktop/Menu/getAreas/?iInstitId"]
    assert c.falhas == []


def test_navegacao_passa_pelo_menu_do_desktop():
    nomes = [n for n, _f, _s in fluxos.FLUXOS["navegacao"][1]()]
    assert nomes == ["login", "menu", "area", "modulo", "tela-cadastro", "tela-relatorio", "sair"]


def test_janela_sem_tela_aberta_avisa_em_vez_de_pegar_frame_errado():
    from regressao.tests.test_fluxos import _Browser
    j = fluxos._Janela(_Browser(), "http://p", fluxos.Coletor(), 60)
    with pytest.raises(RuntimeError, match="nenhuma tela aberta"):
        j.corpo()


def test_busca_de_item_de_menu_e_pela_action_exata():
    assert "n.action === acao" in fluxos._Janela._BUSCA_ITEM
