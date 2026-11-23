import json
from pathlib import Path

import pytest

from regressao.laravel import bateria
from regressao.laravel.caso import CasoHttp, ErroGravacao
from regressao.nucleo.ambiente import Alvos
from regressao.nucleo.banco import BancoDiferente, ErroAmbienteBanco
from regressao.nucleo.relatorio import RodadaInvalida
from regressao.nucleo.veredito import Caso, Veredito, codigo_saida

V = Veredito
REF = "http://ref:8074"
NOVO = "http://novo:8187"


@pytest.fixture
def amb(monkeypatch, tmp_path):
    """Tudo que toca rede, docker ou banco substituido; `chamadas` registra a ordem."""
    chamadas: list = []
    base = tmp_path / "baseline"
    base.mkdir()
    conhecidas = tmp_path / "conhecidas.tsv"
    conhecidas.write_text("# id\tmotivo\n", encoding="utf-8")
    m = monkeypatch
    m.setattr(bateria, "DIR_BASELINE", base)
    m.setattr(bateria, "CONHECIDAS", conhecidas)
    m.setattr(bateria, "alvos_do_ambiente", lambda: Alvos(REF, "http://x:8085", NOVO, "http://x:8090"))
    m.setattr(bateria, "carrega_casos", lambda d: [CasoHttp("rota:GET:/a", "GET", "/a", None)])
    m.setattr(bateria, "_metadados_ambiente", lambda alvo: {"php_ref": "7.4.33", "laravel_alvo": "8.73.2",
                                                           "git_commit": "abc", "dump_sha256": "ff"})
    m.setattr(bateria, "_versoes_do_alvo", lambda url: ("7.4.33", "Laravel Framework 8.73.2"))

    def verifica(alvos):
        chamadas.append(("verifica", alvos))
        return []
    m.setattr(bateria, "verifica", verifica)
    m.setattr(bateria, "laravel_sobe", lambda url: chamadas.append(("boot", url)))

    def gravar(casos, url, dir, completo=False):
        chamadas.append(("gravar", url, completo))
    m.setattr(bateria.caso, "gravar", gravar)

    def comparar(casos, url, dir, restaurar=True):
        chamadas.append(("comparar", url, restaurar))
        return [Caso("rota:GET:/a", "laravel", V.IDENTICO)]
    m.setattr(bateria.caso, "comparar", comparar)
    return chamadas


def le(saida: Path) -> dict:
    return json.loads((saida / "resultado.json").read_text(encoding="utf-8"))


def test_modo_invalido_levanta_erro(amb, tmp_path):
    with pytest.raises(ValueError, match="modo"):
        bateria.roda_bateria_laravel(tmp_path / "s", "apagar")
    assert amb == []
    assert not (tmp_path / "s").exists()


def test_comparar_com_laravel_fora_devolve_um_unico_erro_ambiente_e_codigo_2(amb, monkeypatch, tmp_path):
    boot = Caso("laravel:boot", "laravel", V.ERRO_AMBIENTE, "Laravel fora do ar")
    monkeypatch.setattr(bateria, "laravel_sobe", lambda url: boot)
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "comparar") == 2
    casos = le(saida)["casos"]
    assert [(c["id"], c["veredito"]) for c in casos] == [("laravel:boot", "ERRO_AMBIENTE")]
    assert [c for c in amb if c[0] in ("comparar", "gravar")] == []
    assert "laravel:boot" in (saida / "resumo.md").read_text(encoding="utf-8")


def test_gravar_nao_altera_baseline_quando_ambiente_falha(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria, "verifica", lambda a: ["ref: sem resposta em 5s"])
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "gravar") == 2
    assert [c for c in amb if c[0] == "gravar"] == []
    assert list(bateria.DIR_BASELINE.iterdir()) == []
    assert [c["veredito"] for c in le(saida)["casos"]] == ["ERRO_AMBIENTE"]


def test_gravar_recusa_sobrescrever_baseline_existente(amb, tmp_path):
    (bateria.DIR_BASELINE / "_meta.json").write_text("{}", encoding="utf-8")
    with pytest.raises(bateria.RecusaBaseline, match="pre-migracao"):
        bateria.roda_bateria_laravel(tmp_path / "s", "gravar")
    assert [c for c in amb if c[0] in ("gravar", "verifica")] == []
    # com a confirmacao explicita grava
    assert bateria.roda_bateria_laravel(tmp_path / "s2", "gravar", confirmo_sobrescrever=True) == 0
    assert ("gravar", REF, True) in amb


def test_gravar_recusa_alvo_diferente_do_5_4_sem_confirmacao(amb, tmp_path):
    # baseline vazia: so o alvo protege
    with pytest.raises(bateria.RecusaBaseline, match="--alvo"):
        bateria.roda_bateria_laravel(tmp_path / "s", "gravar", alvo="http://outro:9000")
    with pytest.raises(bateria.RecusaBaseline):
        bateria.roda_bateria_laravel(tmp_path / "s", "gravar", alvo="http://outro:9000",
                                     confirmo_sobrescrever=False)
    assert [c for c in amb if c[0] == "gravar"] == []
    assert bateria.roda_bateria_laravel(tmp_path / "s3", "gravar", alvo="http://outro:9000",
                                        confirmo_sobrescrever=True) == 0
    assert ("gravar", "http://outro:9000", True) in amb
    # alvo explicito igual a referencia nao exige confirmacao (baseline vazia)
    assert bateria.roda_bateria_laravel(tmp_path / "s4", "gravar", alvo=REF + "/") == 0


@pytest.mark.parametrize("php,laravel", [("8.5.12", "Laravel Framework 8.73.2"), ("7.4.33", "Laravel Framework 12.0.1"),
                                         ("indisponivel: ErroAmbienteBanco", "indisponivel: ErroAmbienteBanco")])
def test_gravar_na_url_da_referencia_confere_php_7_4_e_laravel_8(amb, monkeypatch, tmp_path, php, laravel):
    """A URL certa nao basta: REGRESSAO_REF_URL/REGRESSAO_CONTAINER_REF podem apontar para o 8.5."""
    monkeypatch.setattr(bateria, "_versoes_do_alvo", lambda url: (php, laravel))
    with pytest.raises(bateria.RecusaBaseline, match="PHP 7.4 e Laravel 8"):
        bateria.roda_bateria_laravel(tmp_path / "s", "gravar", confirmo_sobrescrever=True)
    assert [c for c in amb if c[0] == "gravar"] == []


def test_cli_gravar_sem_confirmacao_sai_nao_zero(amb, tmp_path, capsys):
    (bateria.DIR_BASELINE / "_meta.json").write_text("{}", encoding="utf-8")
    assert bateria.main(["gravar", "--saida", str(tmp_path / "s")]) == 2
    assert "pre-migracao" in capsys.readouterr().err
    assert bateria.main(["xx", "--saida", str(tmp_path / "s")]) == 2


def test_ids_unicos_na_rodada(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria.caso, "comparar", lambda c, u, d, restaurar=True: [
        Caso("rota:GET:/a", "laravel", V.IDENTICO),
        Caso("rota:GET:/a", "laravel", V.DIVERGE, "x", diff="d1"),
        Caso("auth-x/y:z", "laravel", V.DIVERGE, "x", diff="d2"),
        Caso("AUTH-x_y_z", "laravel", V.DIVERGE, "x", diff="d3")])
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "comparar") == 1
    r = le(saida)
    ids = [c["id"] for c in r["casos"]]
    assert len(set(ids)) == 4 and "rota:GET:/a#2" in ids
    assert r["meta"]["ids_renomeados"] == ["rota:GET:/a -> rota:GET:/a#2"]
    nomes = list(r["meta"]["arquivos_diff"].values())
    assert len({n.lower() for n in nomes}) == 3
    for n in nomes:
        assert (saida / "diffs" / n).is_file()


def test_sem_restaurar_marca_o_resumo_e_comparavel_false(amb, tmp_path, capsys):
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "comparar", restaurar=False) == 0
    assert ("comparar", NOVO, False) in amb
    r = le(saida)
    assert r["meta"]["comparavel"] is False and r["meta"]["restauracao_s"] is None
    assert "NAO restaurado" in (saida / "resumo.md").read_text(encoding="utf-8")
    assert "NAO restaurado" in capsys.readouterr().err
    with pytest.raises(ValueError, match="sem-restaurar"):
        bateria.roda_bateria_laravel(tmp_path / "g", "gravar", restaurar=False)


def test_inconclusivos_aparecem_no_resumo_com_motivo(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria.caso, "comparar", lambda c, u, d, restaurar=True: [
        Caso("rota:GET:/a", "laravel", V.IDENTICO),
        Caso("rota:GET:/b", "laravel", V.INCONCLUSIVO, "HTTP 500 nos dois lados: o caso nao foi exercitado"),
        Caso("rota:GET:/c", "laravel", V.INCONCLUSIVO, "HTTP 502 nos dois lados: o caso nao foi exercitado"),
        Caso("escrita-x", "laravel", V.INCONCLUSIVO, "esperava escrita e nada foi gravado nos dois lados")])
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "comparar") == 0
    md = (saida / "resumo.md").read_text(encoding="utf-8")
    assert "3 caso(s) INCONCLUSIVO" in md and "NAO sao aprovacao" in md
    assert "5xx nos dois lados" in md and "esperava escrita" in md
    assert le(saida)["meta"]["inconclusivos_por_motivo"] == {
        "5xx nos dois lados (nao exercitado)": 2, "esperava escrita e nada foi gravado nos dois lados": 1}


@pytest.mark.parametrize("exc", [ErroGravacao("a sonda x escreveu"), BancoDiferente("sha"),
                                 ErroAmbienteBanco("docker"), RodadaInvalida("r")])
def test_erro_gravacao_vira_erro_ambiente_exit_2(amb, monkeypatch, tmp_path, exc):
    def explode(*a, **k):
        raise exc
    monkeypatch.setattr(bateria.caso, "gravar", explode)
    monkeypatch.setattr(bateria.caso, "comparar", explode)
    for modo in ("gravar", "comparar"):
        saida = tmp_path / modo
        assert bateria.roda_bateria_laravel(saida, modo) == 2
        casos = le(saida)["casos"]
        assert len(casos) == 1 and casos[0]["veredito"] == "ERRO_AMBIENTE"
        assert type(exc).__name__ in casos[0]["detalhe"]


def test_comparar_usa_alvo_do_ambiente_ou_o_informado_e_marca_conhecidas(amb, monkeypatch, tmp_path):
    bateria.CONHECIDAS.write_text("rota:GET:/a\tpreexistente\n", encoding="utf-8")
    monkeypatch.setattr(bateria.caso, "comparar", lambda c, u, d, restaurar=True: [
        Caso("rota:GET:/a", "laravel", V.DIVERGE, "x")])
    assert bateria.roda_bateria_laravel(tmp_path / "s", "comparar", alvo=REF) == 0
    verif = [c for c in amb if c[0] == "verifica"][0][1]
    assert verif.laravel_novo == REF
    assert le(tmp_path / "s")["meta"]["alvo"] == REF
    assert codigo_saida([Caso("x", "l", V.DIVERGE)]) == 1


# ---- fix round 1 ----

def test_gravar_com_sucesso_nao_emite_caso_e_marca_gravacao(amb, tmp_path):
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "gravar") == 0
    r = le(saida)
    assert r["casos"] == []
    assert r["meta"]["modo"] == "gravar" and r["meta"]["gravacao"]["n_casos"] == 1
    md = (saida / "resumo.md").read_text(encoding="utf-8")
    assert "GRAVACAO da baseline" in md and "nenhum caso foi avaliado" in md
    assert "IDENTICO" not in json.dumps(r["casos"]) and "IDENTICO: 0" in md


def test_gravar_com_erro_continua_erro_ambiente(amb, monkeypatch, tmp_path):
    def explode(*a, **k):
        raise ErroGravacao("x")
    monkeypatch.setattr(bateria.caso, "gravar", explode)
    assert bateria.roda_bateria_laravel(tmp_path / "s", "gravar") == 2
    assert [c["veredito"] for c in le(tmp_path / "s")["casos"]] == ["ERRO_AMBIENTE"]


def test_gitkeep_nao_conta_como_baseline(amb, tmp_path):
    (bateria.DIR_BASELINE / ".gitkeep").write_text("", encoding="utf-8")
    assert bateria.roda_bateria_laravel(tmp_path / "s", "gravar") == 0
    (bateria.DIR_BASELINE / "x.json").write_text("{}", encoding="utf-8")
    with pytest.raises(bateria.RecusaBaseline):
        bateria.roda_bateria_laravel(tmp_path / "s2", "gravar")


@pytest.mark.parametrize("onde", ["verifica", "laravel_sobe", "alvos", "baseline", "carrega"])
def test_excecao_inesperada_vira_erro_ambiente_com_erro_log(amb, monkeypatch, tmp_path, onde):
    def boom(*a, **k):
        raise RuntimeError("falha password=segredo123 inesperada")
    alvo = {"verifica": "verifica", "laravel_sobe": "laravel_sobe", "alvos": "alvos_do_ambiente",
            "baseline": "_baseline_existe", "carrega": "carrega_casos"}[onde]
    monkeypatch.setattr(bateria, alvo, boom)
    saida = tmp_path / "s"
    modo = "gravar" if onde == "baseline" else "comparar"
    assert bateria.roda_bateria_laravel(saida, modo) == 2
    casos = le(saida)["casos"]
    assert len(casos) == 1 and casos[0]["veredito"] == "ERRO_AMBIENTE"
    if onde in ("alvos",):
        assert casos[0]["id"] == "laravel:inesperado"
        log = (saida / "erro.log").read_text(encoding="utf-8")
        assert "RuntimeError" in log and "segredo123" not in log
    assert "segredo123" not in json.dumps(le(saida))


def test_excecao_em_fim_escreve_a_rodada_na_segunda_tentativa(amb, monkeypatch, tmp_path):
    real = bateria._fim
    n = {"k": 0}

    def fim(*a, **k):
        n["k"] += 1
        if n["k"] == 1:
            raise OSError("disco cheio")
        return real(*a, **k)
    monkeypatch.setattr(bateria, "_fim", fim)
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "comparar") == 2
    assert le(saida)["casos"][0]["id"] == "laravel:inesperado"
    assert "OSError" in (saida / "erro.log").read_text(encoding="utf-8")


def test_saida_nao_gravavel_imprime_erro_e_sai_2_sem_traceback(amb, monkeypatch, tmp_path, capsys):
    def fim(*a, **k):
        raise PermissionError("negado password=abc123")
    monkeypatch.setattr(bateria, "_fim", fim)
    assert bateria.main(["comparar", "--saida", str(tmp_path / "s")]) == 2
    err = capsys.readouterr().err
    assert "PermissionError" in err and "abc123" not in err and "Traceback" not in err


def test_saida_realmente_nao_gravavel(amb, tmp_path, capsys):
    arq = tmp_path / "arquivo"
    arq.write_text("x")
    assert bateria.main(["comparar", "--saida", str(arq / "sub")]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_ids_renomeados_geram_aviso_e_meta_tem_tempos_e_git(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria.caso, "comparar", lambda c, u, d, restaurar=True: [
        Caso("rota:GET:/a", "laravel", V.IDENTICO), Caso("rota:GET:/a", "laravel", V.IDENTICO)])
    saida = tmp_path / "s"
    assert bateria.roda_bateria_laravel(saida, "comparar") == 0
    assert "renomeado" in (saida / "resumo.md").read_text(encoding="utf-8")
    meta = le(saida)["meta"]
    assert "tempo_casos_s" in meta and "tempo_total_s" in meta


def test_metadados_usam_o_helper_de_git(monkeypatch):
    from regressao.nucleo import git
    monkeypatch.setattr(git, "commit", lambda raiz, curto=False, runner=None: "c0ffee")
    monkeypatch.setattr(git, "sujo", lambda raiz, runner=None: {"git_sujo": False, "git_sujo_arquivos": []})
    monkeypatch.setattr(bateria, "_docker", lambda *a, **k: b"5.6.40\n")
    monkeypatch.setattr(bateria, "alvos_do_ambiente", lambda: Alvos(REF, "p", NOVO, "q"))
    meta = bateria._metadados_ambiente(NOVO)
    assert meta["git_commit"] == "c0ffee" and meta["git_sujo"] is False
