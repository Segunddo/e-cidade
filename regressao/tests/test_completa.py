"""Bateria completa: agregacao, codigo de saida, ids prefixados e --comparar ANTES DEPOIS."""
import json
from pathlib import Path

import pytest

from regressao.completa import orquestra
from regressao.nucleo.relatorio import escreve_rodada
from regressao.nucleo.veredito import Caso, Veredito

I, D, N, E = Veredito.IDENTICO, Veredito.DIVERGE, Veredito.INCONCLUSIVO, Veredito.ERRO_AMBIENTE


def sub(diretorio: Path, casos: list[Caso], meta: dict | None = None, codigo: int | None = None) -> int:
    """Escreve uma sub-rodada como as baterias reais fazem e devolve o codigo de saida dela."""
    from regressao.nucleo.veredito import codigo_saida
    escreve_rodada(Path(diretorio), casos, {"comparavel": True, **(meta or {})})
    return codigo_saida(casos) if codigo is None else codigo


def executores(php=None, laravel=None, fluxos=None, chamadas=None):
    """Executores falsos: cada um escreve a propria sub-rodada em <saida>/<frente>."""
    chamadas = chamadas if chamadas is not None else []

    def _php(d, areas, prefixos):
        chamadas.append(("php", areas, prefixos))
        return sub(d, **(php or {"casos": [Caso("tela:a.php", "x", I)]}))

    def _laravel(d, alvo):
        chamadas.append(("laravel", alvo))
        return sub(d, **(laravel or {"casos": [Caso("rota:GET:/a", "laravel", I)]}))

    def _fluxos(d):
        chamadas.append(("fluxos",))
        return sub(d, **(fluxos or {"casos": [Caso("fluxo:nav:login", "fluxos", I)]}))

    return {"php": _php, "laravel": _laravel, "fluxos": _fluxos}


@pytest.fixture(autouse=True)
def _sem_ambiente_real(monkeypatch):
    monkeypatch.setattr(orquestra, "_verifica_ambiente", lambda: [])
    monkeypatch.setattr(orquestra, "_meta_repo", lambda: {
        "git_commit": "abc123", "git_sujo": True, "git_sujo_arquivos": ["M x"],
        "git_sujo_regressao": False, "git_sujo_regressao_arquivos": [],
        "baseline_sha256": "f" * 64})


def roda(tmp_path, **kw):
    ex = kw.pop("executores", None) or executores()
    return orquestra.roda_completa(tmp_path / "saida", executores=ex, **kw)


def carrega(tmp_path):
    return json.loads((tmp_path / "saida" / "resultado.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- agregacao

def test_agrega_resultados_das_tres_frentes(tmp_path):
    ex = executores(
        php={"casos": [Caso("tela:a.php", "x", I), Caso("tela:b.php", "x", D, "5.6=200 8.5=500"),
                       Caso("post:c.php", "x", N, "sem escrita")],
             "meta": {"catalogo_posts": {"verificado": 32, "nao_verificado": 2, "nao_verificado_pulados": 2},
                      "catalogo_relatorios": {"verificado": 17, "nao_verificado": 3, "nao_verificado_pulados": 3},
                      "php_ref": "7.4.33", "php_85": "8.5.0"}},
        laravel={"casos": [Caso("rota:GET:/a", "laravel", I), Caso("rota:GET:/b", "laravel", N, "HTTP 500 nos dois lados")],
                 "meta": {"cobertura": {"rotas_cobertas": 366, "rotas_total": 568}, "laravel_alvo": "Laravel 8"}},
        fluxos={"casos": [Caso("fluxo:nav:login", "fluxos", I), Caso("fluxo:nav:sair", "fluxos", D, "dom")]})
    assert roda(tmp_path, executores=ex) == 1
    dados = carrega(tmp_path)
    ids = [c["id"] for c in dados["casos"]]
    assert ids == sorted(set(ids), key=ids.index)  # unicos
    assert {"php:tela:a.php", "php:tela:b.php", "php:post:c.php", "laravel:rota:GET:/a",
            "laravel:rota:GET:/b", "fluxo:nav:login", "fluxo:nav:sair"} == set(ids)
    meta = dados["meta"]
    assert meta["baterias"]["php"]["totais"] == {"IDENTICO": 1, "DIVERGE": 1, "INCONCLUSIVO": 1, "ERRO_AMBIENTE": 0}
    assert meta["baterias"]["laravel"]["totais"]["INCONCLUSIVO"] == 1
    assert meta["totais"]["DIVERGE"] == 2 and meta["totais"]["IDENTICO"] == 3
    assert meta["cobertura"]["php"]["posts"]["verificado"] == 32
    assert meta["cobertura"]["laravel"] == {"rotas_cobertas": 366, "rotas_total": 568}
    assert meta["versoes"]["php_ref"] == "7.4.33" and meta["versoes"]["laravel_alvo"] == "Laravel 8"
    assert meta["git_commit"] == "abc123" and meta["git_sujo"] is True
    assert meta["git_sujo_regressao"] is False
    assert meta["baseline_sha256"] == "f" * 64
    assert set(meta["tempos_s"]) >= {"php", "laravel", "fluxos", "total"}
    assert meta["comparavel"] is True
    for sub_dir in ("php", "laravel", "fluxos"):
        assert (tmp_path / "saida" / sub_dir / "resultado.json").is_file()


def test_resumo_traz_totais_novas_conhecidas_e_inconclusivos_com_motivo(tmp_path):
    ex = executores(
        php={"casos": [Caso("tela:b.php", "x", D, "nova"), Caso("tela:k.php", "x", D, "ja sabida", conhecida=True),
                       Caso("post:c.php", "x", N, "sem escrita de negocio")]},
        laravel={"casos": [Caso("rota:GET:/b", "laravel", N, "HTTP 500 nos dois lados"),
                           Caso("rota:GET:/c", "laravel", N, "HTTP 500 nos dois lados")]})
    roda(tmp_path, executores=ex)
    resumo = (tmp_path / "saida" / "resumo.md").read_text(encoding="utf-8")
    assert resumo == (tmp_path / "saida" / "relatorio.md").read_text(encoding="utf-8")
    assert "Divergencias novas" in resumo and "php:tela:b.php" in resumo
    assert "Divergencias conhecidas" in resumo and "php:tela:k.php" in resumo
    assert "NAO sao aprovacao" in resumo
    assert "sem escrita de negocio" in resumo
    meta = carrega(tmp_path)["meta"]
    assert meta["inconclusivos_por_motivo"]["php"] == {"sem escrita de negocio": 1}
    assert sum(meta["inconclusivos_por_motivo"]["laravel"].values()) == 2
    assert meta["divergencias"] == {"novas": 1, "conhecidas": 1}


def test_resumo_mostra_percentual_de_inconclusivo_e_diz_que_nao_e_aprovacao(tmp_path):
    ex = executores(laravel={"casos": [Caso(f"rota:GET:/{i}", "l", N, "HTTP 500 nos dois lados") for i in range(3)]
                             + [Caso("rota:GET:/ok", "l", I)]})
    roda(tmp_path, executores=ex)
    resumo = (tmp_path / "saida" / "resumo.md").read_text(encoding="utf-8")
    assert "INCONCLUSIVO: 3 de 6 casos (50.0%)" in resumo  # 1 php + 4 laravel + 1 fluxo = 6
    assert "laravel: 3 de 4 (75.0%)" in resumo
    assert "NAO e aprovacao" in resumo
    assert carrega(tmp_path)["meta"]["inconclusivos_percentual"]["total"] == 50.0


def test_resumo_da_completa_traz_aviso_fixo_de_escopo_da_bateria_php(tmp_path):
    roda(tmp_path)
    resumo = (tmp_path / "saida" / "resumo.md").read_text(encoding="utf-8")
    assert "ESCOPO" in resumo and "DOIS runtimes" in resumo and "golden master" in resumo
    assert "limite superior" in resumo or "telas_com_dados" not in resumo
    assert "lint: so as telas selecionadas" in resumo


# ---------------------------------------------------------------- codigo de saida

@pytest.mark.parametrize("php,lar,flu,esperado", [
    (0, 2, 0, 2), (1, 0, 0, 1), (0, 0, 0, 0), (1, 2, 1, 2), (0, 0, 1, 1)])
def test_codigo_de_saida_pega_o_pior_das_frentes(tmp_path, php, lar, flu, esperado):
    def caso_para(codigo, prefixo):
        v = {0: I, 1: D, 2: E}[codigo]
        return {"casos": [Caso(f"{prefixo}:x", "a", v)]}
    ex = executores(php=caso_para(php, "tela"), laravel=caso_para(lar, "rota"), fluxos=caso_para(flu, "fluxo"))
    assert roda(tmp_path, executores=ex) == esperado


def test_codigo_de_saida_respeita_divergencia_conhecida(tmp_path):
    ex = executores(php={"casos": [Caso("tela:k.php", "x", D, conhecida=True)]})
    assert roda(tmp_path, executores=ex) == 0


def test_laravel_erro_ambiente_nao_aborta_as_outras_frentes(tmp_path):
    chamadas: list = []
    ex = executores(laravel={"casos": [Caso("laravel:boot", "laravel", E, "sem resposta")]}, chamadas=chamadas)
    assert roda(tmp_path, executores=ex) == 2
    assert [c[0] for c in chamadas] == ["php", "laravel", "fluxos"]
    dados = carrega(tmp_path)
    por_id = {c["id"]: c["veredito"] for c in dados["casos"]}
    assert por_id["laravel:boot"] == "ERRO_AMBIENTE"
    assert por_id["php:tela:a.php"] == "IDENTICO" and por_id["fluxo:nav:login"] == "IDENTICO"
    assert dados["meta"]["baterias"]["laravel"]["totais"]["ERRO_AMBIENTE"] == 1


def test_frente_que_levanta_excecao_vira_erro_ambiente_e_o_resto_roda(tmp_path):
    chamadas: list = []
    ex = executores(chamadas=chamadas)

    def quebra(d, alvo):
        chamadas.append(("laravel",))
        raise RuntimeError("boom segredo=abc")
    ex["laravel"] = quebra
    assert roda(tmp_path, executores=ex) == 2
    assert [c[0] for c in chamadas] == ["php", "laravel", "fluxos"]
    dados = carrega(tmp_path)
    erro = [c for c in dados["casos"] if c["veredito"] == "ERRO_AMBIENTE"]
    assert len(erro) == 1 and erro[0]["id"].startswith("laravel:") and "RuntimeError" in erro[0]["detalhe"]
    assert dados["meta"]["comparavel"] is False  # nao houve sub-rodada valida


def test_ambiente_ruim_escreve_um_erro_e_sai_2_sem_rodar_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(orquestra, "_verifica_ambiente", lambda: ["ref: sem resposta em 5s"])
    chamadas: list = []
    assert roda(tmp_path, executores=executores(chamadas=chamadas)) == 2
    assert chamadas == []
    dados = carrega(tmp_path)
    assert [c["id"] for c in dados["casos"]] == ["completa:ambiente"]


def test_comparavel_false_se_alguma_subrodada_nao_for_comparavel(tmp_path):
    ex = executores(php={"casos": [Caso("tela:a.php", "x", I)], "meta": {"comparavel": False}})
    roda(tmp_path, executores=ex)
    assert carrega(tmp_path)["meta"]["comparavel"] is False
    assert "NAO COMPARAVEL" in (tmp_path / "saida" / "resumo.md").read_text(encoding="utf-8").upper()


def test_sem_fluxos_nao_roda_fluxos_e_registra(tmp_path):
    chamadas: list = []
    assert roda(tmp_path, executores=executores(chamadas=chamadas), fluxos=False) == 0
    assert ("fluxos",) not in chamadas
    meta = carrega(tmp_path)["meta"]
    assert meta["partes_executadas"] == ["php", "laravel"]
    assert not (tmp_path / "saida" / "fluxos").exists()


def test_areas_prefixos_e_alvo_laravel_chegam_aos_executores(tmp_path):
    chamadas: list = []
    roda(tmp_path, executores=executores(chamadas=chamadas), areas=["saude"], prefixos=["^cem"],
         laravel_alvo="http://localhost:8080")
    assert ("php", ["saude"], ["^cem"]) in chamadas
    assert ("laravel", "http://localhost:8080") in chamadas


def test_ids_com_prefixo_nao_duplicam_nem_colidem():
    assert orquestra.prefixa("php", "tela:a.php") == "php:tela:a.php"
    assert orquestra.prefixa("laravel", "laravel:boot") == "laravel:boot"
    assert orquestra.prefixa("laravel", "rota:GET:/x") == "laravel:rota:GET:/x"
    assert orquestra.prefixa("fluxo", "fluxo:nav:login") == "fluxo:nav:login"
    assert orquestra.prefixa("php", "passo:ambiente") == "php:passo:ambiente"


# ---------------------------------------------------------------- --comparar

def completa(tmp_path, nome, casos_por_frente: dict[str, list[Caso]], meta_extra: dict | None = None,
             comparavel: bool = True) -> Path:
    ex = {k: (lambda *a, _c=v: sub(a[0], _c, {"comparavel": comparavel})) for k, v in casos_por_frente.items()}
    d = tmp_path / nome
    orquestra.roda_completa(d, executores=ex)
    if meta_extra:
        dados = json.loads((d / "resultado.json").read_text(encoding="utf-8"))
        dados["meta"].update(meta_extra)
        (d / "resultado.json").write_text(json.dumps(dados), encoding="utf-8")
    return d


def frentes(php, laravel=None, fluxos=None):
    return {"php": php, "laravel": laravel or [Caso("rota:GET:/a", "l", I)],
            "fluxos": fluxos or [Caso("fluxo:nav:login", "f", I)]}


def test_flag_comparar_lista_mudancas_de_veredito(tmp_path):
    antes = completa(tmp_path, "antes", frentes(
        [Caso("tela:reg.php", "x", I), Caso("tela:corr.php", "x", D), Caso("tela:some.php", "x", I),
         Caso("tela:igual.php", "x", I), Caso("tela:perde.php", "x", I)],
        laravel=[Caso("rota:GET:/a", "l", I)]), {"git_commit": "aaa", "versoes": {"php_85": "8.4"}})
    depois = completa(tmp_path, "depois", frentes(
        [Caso("tela:reg.php", "x", D), Caso("tela:corr.php", "x", I), Caso("tela:nova.php", "x", I),
         Caso("tela:igual.php", "x", I), Caso("tela:perde.php", "x", N)],
        laravel=[Caso("rota:GET:/a", "l", E)]), {"git_commit": "bbb", "versoes": {"php_85": "8.5"}})
    assert orquestra.compara_completas(antes, depois) == 2  # DEPOIS tem ERRO_AMBIENTE (laravel)
    cj = json.loads((depois / "comparacao.json").read_text(encoding="utf-8"))
    assert [m["id"] for m in cj["regressoes"]] == ["laravel:rota:GET:/a", "php:tela:perde.php", "php:tela:reg.php"]
    assert [m["id"] for m in cj["correcoes"]] == ["php:tela:corr.php"]
    assert [m["id"] for m in cj["adicionados"]] == ["php:tela:nova.php"]
    assert [m["id"] for m in cj["removidos"]] == ["php:tela:some.php"]
    assert cj["regressoes"][0]["antes"] == "IDENTICO" and cj["regressoes"][0]["depois"] == "ERRO_AMBIENTE"
    assert cj["meta"]["git_commit"] == {"antes": "aaa", "depois": "bbb"}
    assert cj["meta"]["versoes.php_85"] == {"antes": "8.4", "depois": "8.5"}
    md = (depois / "comparacao.md").read_text(encoding="utf-8")
    for titulo in ("Regressoes", "Correcoes", "Adicionados", "Removidos", "Diferencas de meta"):
        assert titulo in md
    assert "php:tela:reg.php" in md and "IDENTICO -> DIVERGE" in md


def test_comparar_so_com_correcoes_sai_0(tmp_path):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", D)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", I)]))
    assert orquestra.compara_completas(antes, depois) == 0


def test_comparar_igual_sai_0_e_diz_que_nao_ha_mudancas(tmp_path):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", I)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", I)]))
    assert orquestra.compara_completas(antes, depois) == 0
    assert "(nenhum)" in (depois / "comparacao.md").read_text(encoding="utf-8")


def test_comparar_caso_removido_sai_1(tmp_path):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", I), Caso("tela:b.php", "x", I)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", I)]))
    assert orquestra.compara_completas(antes, depois) == 1


def test_comparar_recusa_rodada_nao_comparavel(tmp_path, capsys):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", I)]), comparavel=False)
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", I)]))
    assert orquestra.compara_completas(antes, depois) == 2
    err = capsys.readouterr().err
    assert "nao comparavel" in err.lower() and "ANTES" in err
    assert not (depois / "comparacao.md").exists()
    # e o lado DEPOIS tambem
    assert orquestra.compara_completas(depois, antes) == 2


def test_comparar_recusa_rodada_invalida_ou_ausente(tmp_path, capsys):
    ok = completa(tmp_path, "ok", frentes([Caso("tela:a.php", "x", I)]))
    (tmp_path / "ruim").mkdir()
    (tmp_path / "ruim" / "resultado.json").write_text("{nao e json", encoding="utf-8")
    assert orquestra.compara_completas(ok, tmp_path / "ruim") == 2
    assert orquestra.compara_completas(tmp_path / "nao_existe", ok) == 2
    assert "invalida" in capsys.readouterr().err.lower()


def test_comparar_erro_contra_ok_e_demonstravel(tmp_path):
    """Laravel ausente (ERRO) numa rodada e Laravel presente na outra: o diff mostra os dois lados."""
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", I)],
                                                 laravel=[Caso("laravel:boot", "l", E)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", I)],
                                                  laravel=[Caso("rota:GET:/a", "l", I)]))
    assert orquestra.compara_completas(antes, depois) == 1  # laravel:boot sumiu
    cj = json.loads((depois / "comparacao.json").read_text(encoding="utf-8"))
    assert [m["id"] for m in cj["removidos"]] == ["laravel:boot"]
    assert [m["id"] for m in cj["adicionados"]] == ["laravel:rota:GET:/a"]
    assert cj["removidos"][0]["antes"] == "ERRO_AMBIENTE"


def test_comparar_depois_com_erro_ambiente_igual_ao_antes_sai_2_com_aviso(tmp_path):
    f = frentes([Caso("tela:a.php", "x", I)], laravel=[Caso("laravel:boot", "l", E)])
    antes = completa(tmp_path, "antes", f)
    depois = completa(tmp_path, "depois", f)
    assert orquestra.compara_completas(antes, depois) == 2
    cj = json.loads((depois / "comparacao.json").read_text(encoding="utf-8"))
    assert cj["regressoes"] == [] and any("ERRO_AMBIENTE" in a for a in cj["avisos"])
    assert "AVISOS" in (depois / "comparacao.md").read_text(encoding="utf-8")


def test_comparar_depois_com_diverge_nao_conhecida_igual_ao_antes_sai_1_com_aviso(tmp_path):
    f = frentes([Caso("tela:a.php", "x", D)])
    antes = completa(tmp_path, "antes", f)
    depois = completa(tmp_path, "depois", f)
    assert orquestra.compara_completas(antes, depois) == 1
    assert any("DIVERGE" in a for a in json.loads((depois / "comparacao.json").read_text())["avisos"])


def test_comparar_diverge_conhecida_no_depois_nao_forca_saida(tmp_path):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", D, conhecida=True)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", D, conhecida=True)]))
    assert orquestra.compara_completas(antes, depois) == 0
    assert json.loads((depois / "comparacao.json").read_text())["avisos"] == []


@pytest.mark.parametrize("de", [D, E])
def test_comparar_diverge_ou_erro_virando_inconclusivo_e_lacuna_nao_correcao(tmp_path, de):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", de)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", N)]))
    orquestra.compara_completas(antes, depois)
    cj = json.loads((depois / "comparacao.json").read_text(encoding="utf-8"))
    assert [m["id"] for m in cj["lacunas"]] == ["php:tela:a.php"]
    assert cj["correcoes"] == [] and cj["outras"] == []
    assert "Lacunas" in (depois / "comparacao.md").read_text(encoding="utf-8")


def test_cli_comparar_e_saida(tmp_path, monkeypatch):
    antes = completa(tmp_path, "antes", frentes([Caso("tela:a.php", "x", I)]))
    depois = completa(tmp_path, "depois", frentes([Caso("tela:a.php", "x", I)]))
    assert orquestra.main(["--comparar", str(antes), str(depois)]) == 0
    assert orquestra.main(["--comparar", str(antes)]) == 2  # argumentos faltando
