import json
from pathlib import Path

import pytest

from regressao.nucleo.relatorio import RodadaInvalida, compara_rodadas, escreve_rodada
from regressao.nucleo.veredito import Caso, Veredito


def test_resumo_conta_por_area_e_veredito(tmp_path: Path):
    casos = [
        Caso("a1", "login", Veredito.IDENTICO),
        Caso("a2", "login", Veredito.DIVERGE),
        Caso("b1", "tributario", Veredito.DIVERGE, conhecida=True),
        Caso("b2", "tributario", Veredito.INCONCLUSIVO, detalhe="sem dados"),
    ]
    escreve_rodada(tmp_path, casos, {"php": "8.2", "commit": "abc"})

    dados = json.loads((tmp_path / "resultado.json").read_text(encoding="utf-8"))
    assert dados["meta"] == {"php": "8.2", "commit": "abc"}
    assert len(dados["casos"]) == 4
    resumo = (tmp_path / "resumo.md").read_text(encoding="utf-8")
    assert "Total de casos: 4" in resumo
    assert "- IDENTICO: 1" in resumo
    assert "- DIVERGE: 2" in resumo
    assert "- INCONCLUSIVO: 1" in resumo
    assert "- ERRO_AMBIENTE: 0" in resumo
    assert "- login: IDENTICO=1, DIVERGE=1, INCONCLUSIVO=0, ERRO_AMBIENTE=0" in resumo
    assert "- tributario: IDENTICO=0, DIVERGE=1, INCONCLUSIVO=1, ERRO_AMBIENTE=0" in resumo

    def secao(titulo):
        return resumo.split(f"## {titulo}")[1].split("##")[0]

    novas = secao("Divergencias novas")
    conhecidas = secao("Divergencias conhecidas")
    assert "a2" in novas and "b1" not in novas
    assert "b1" in conhecidas and "a2" not in conhecidas
    assert "b2" in secao("INCONCLUSIVO")


def test_diff_vai_para_arquivo_do_caso(tmp_path: Path):
    casos = [Caso("x1", "a", Veredito.DIVERGE, diff="-um\n+dois\n")]
    escreve_rodada(tmp_path, casos, {})
    assert (tmp_path / "diffs" / "x1.diff").read_text(encoding="utf-8") == "-um\n+dois\n"


def test_compara_rodadas_lista_so_o_que_mudou(tmp_path: Path):
    antes, depois = tmp_path / "antes", tmp_path / "depois"
    escreve_rodada(antes, [Caso("A", "a", Veredito.IDENTICO), Caso("B", "a", Veredito.DIVERGE)], {})
    escreve_rodada(depois, [Caso("A", "a", Veredito.DIVERGE), Caso("B", "a", Veredito.DIVERGE)], {})
    assert compara_rodadas(antes, depois) == [("A", Veredito.IDENTICO, Veredito.DIVERGE)]


def _rodada(d: Path, *pares):
    escreve_rodada(d, [Caso(i, "a", v) for i, v in pares], {})
    return d


def test_compara_rodadas_caso_removido_aparece_como_none_depois(tmp_path: Path):
    antes = _rodada(tmp_path / "a", ("A", Veredito.IDENTICO), ("B", Veredito.IDENTICO))
    depois = _rodada(tmp_path / "d", ("B", Veredito.IDENTICO))
    assert compara_rodadas(antes, depois) == [("A", Veredito.IDENTICO, None)]


def test_compara_rodadas_caso_novo_aparece_como_none_antes(tmp_path: Path):
    antes = _rodada(tmp_path / "a", ("B", Veredito.IDENTICO))
    depois = _rodada(tmp_path / "d", ("B", Veredito.IDENTICO), ("A", Veredito.DIVERGE))
    assert compara_rodadas(antes, depois) == [("A", None, Veredito.DIVERGE)]


def test_compara_rodadas_veredito_que_volta_a_identico_aparece(tmp_path: Path):
    antes = _rodada(tmp_path / "a", ("Z", Veredito.DIVERGE), ("A", Veredito.INCONCLUSIVO))
    depois = _rodada(tmp_path / "d", ("Z", Veredito.IDENTICO), ("A", Veredito.IDENTICO))
    assert compara_rodadas(antes, depois) == [
        ("A", Veredito.INCONCLUSIVO, Veredito.IDENTICO),
        ("Z", Veredito.DIVERGE, Veredito.IDENTICO),
    ]


def test_compara_rodadas_json_ausente_levanta_rodada_invalida(tmp_path: Path):
    ok = _rodada(tmp_path / "ok", ("A", Veredito.IDENTICO))
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    with pytest.raises(RodadaInvalida, match="resultado.json"):
        compara_rodadas(ok, vazio)


def test_compara_rodadas_json_corrompido_levanta_rodada_invalida(tmp_path: Path):
    ok = _rodada(tmp_path / "ok", ("A", Veredito.IDENTICO))
    ruim = tmp_path / "ruim"
    ruim.mkdir()
    (ruim / "resultado.json").write_text("{nao eh json", encoding="utf-8")
    with pytest.raises(RodadaInvalida, match="JSON"):
        compara_rodadas(ok, ruim)
    (ruim / "resultado.json").write_text('{"meta": {}}', encoding="utf-8")
    with pytest.raises(RodadaInvalida, match="chave"):
        compara_rodadas(ok, ruim)
