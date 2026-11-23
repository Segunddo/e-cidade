import json
import re
from pathlib import Path

import pytest

from regressao.nucleo.ambiente import Alvos
from regressao.nucleo.banco import BancoDiferente, ErroAmbienteBanco
from regressao.nucleo.veredito import Caso, Veredito, codigo_saida
from regressao.php import bateria
from regressao.php.posts import PostCaso
from regressao.php.relatorios import RelCaso

V = Veredito


@pytest.fixture
def amb(monkeypatch, tmp_path):
    """Todos os passos substituidos por dubles; `chamadas` registra a ordem."""
    chamadas: list[str] = []

    def reg(nome, retorno):
        def f(*a, **k):
            chamadas.append(nome)
            return retorno(*a) if callable(retorno) else retorno
        return f

    conhecidas = tmp_path / "conhecidas.tsv"
    conhecidas.write_text("# id\tmotivo\n", encoding="utf-8")
    posts = [PostCaso("rec1_x.php", ["a"], "x=1", "rh", True),
             PostCaso("rec1_b001.php", ["b"], "x=1", "rh", False),
             PostCaso("orc1_c001.php", ["c"], "x=1", "orcamento", True)]
    rels = [RelCaso("pro2_r002.php", "", "pdf", "protocolo", True),
            RelCaso("con2_r002.php", "", "pdf", "contabilidade", False)]
    m = monkeypatch
    m.setattr(bateria, "CONHECIDAS", conhecidas)
    m.setattr(bateria, "alvos_do_ambiente", lambda: Alvos("a", "b", "c", "d"))
    m.setattr(bateria, "verifica", reg("verifica", []))
    m.setattr(bateria, "confere_baseline", reg("confere_baseline", None))
    m.setattr(bateria, "restaura_dump", reg("restaura_dump", None))
    m.setattr(bateria, "obtem_sid", reg("obtem_sid", "sid123"))
    m.setattr(bateria, "sessao_autenticada", reg("sessao_autenticada", True))
    m.setattr(bateria, "renova_sessao", lambda sid, **k: None)  # por padrao a renovacao falha (testes antigos)
    def fake_lista(rx):
        mm = re.fullmatch(r"(?:\(\?=\(\?:(.*)\)\))?\^([a-z]+)\[0-9\]\*_", rx)
        nome = f"{mm.group(2)}1_x.php"
        return [nome] if not mm.group(1) or re.match(mm.group(1), nome, re.I) else []
    m.setattr(bateria, "lista_telas", fake_lista)
    m.setattr(bateria, "_classes_das_telas", lambda t: ["classes/db_a_classe.php"])
    m.setattr(bateria, "_metadados_ambiente", lambda: {"php_ref": "7.4.33", "php_85": "8.5.0",
                                                       "git_commit": "abc", "baseline_sha256": "ff"})
    m.setattr(bateria, "roda_lint", reg("lint", lambda arqs: [Caso(a, "php-sintaxe", V.IDENTICO) for a in arqs]))
    m.setattr(bateria, "roda_classes", reg("classes", lambda l: [Caso(c, "php-classes", V.IDENTICO) for c in l]))
    def fake_telas(sid, rx, a):
        nome = fake_lista(rx)[0]
        return [Caso(nome, a, V.IDENTICO), Caso("telas", a, V.INCONCLUSIVO, "run")], {nome: b"<td>1</td>"}
    m.setattr(bateria, "roda_telas", reg("telas", fake_telas))
    m.setattr(bateria, "carrega_catalogo", lambda c: posts)
    m.setattr(bateria, "carrega_catalogo_relatorios", lambda c: rels)
    m.setattr(bateria, "roda_post", reg("post", lambda sid, c: Caso(c.tela, c.area, V.IDENTICO)))
    m.setattr(bateria, "roda_relatorio", reg("relatorio", lambda sid, c: Caso(c.url, c.area, V.IDENTICO)))
    return chamadas


def le(saida: Path) -> dict:
    return json.loads((saida / "resultado.json").read_text(encoding="utf-8"))


def ids(saida: Path) -> dict[str, str]:
    return {c["id"]: c["veredito"] for c in le(saida)["casos"]}


def test_fluxo_completo_na_ordem(amb, tmp_path):
    assert bateria.roda_bateria_php(tmp_path, ["tributario"]) == 0
    ordem = [c for i, c in enumerate(amb) if c not in amb[:i]]
    assert ordem == ["verifica", "confere_baseline", "restaura_dump", "obtem_sid", "sessao_autenticada",
                     "lint", "classes", "telas", "post", "relatorio"]
    assert amb.count("restaura_dump") == 1
    meta = le(tmp_path)["meta"]
    assert meta["php_ref"] == "7.4.33" and meta["php_85"] == "8.5.0" and meta["areas"] == ["tributario"]
    assert meta["git_commit"] == "abc" and meta["baseline_sha256"] == "ff" and meta["comparavel"] is True
    assert {"catalogo_posts", "catalogo_relatorios"} <= set(meta)
    assert "restauracao_s" in meta and "sintaxe_s" in meta["tempos_s"]
    assert any(p.name.startswith("hashes_") for p in tmp_path.iterdir())
    assert (tmp_path / "cobertura.json").is_file()


def test_ambiente_fora_gera_erro_ambiente_e_codigo_2(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria, "verifica", lambda a: ["ref: sem resposta em 5s: x", "docker ps indisponivel"])
    assert bateria.roda_bateria_php(tmp_path) == 2
    assert ids(tmp_path) == {"passo:ambiente": "ERRO_AMBIENTE"}
    assert "restaura_dump" not in amb and "lint" not in amb


@pytest.mark.parametrize("exc", [BancoDiferente("sha diferente"), ErroAmbienteBanco("docker caiu")])
def test_banco_diferente_rejeita_rodada(amb, monkeypatch, tmp_path, exc):
    def explode(*a):
        raise exc
    monkeypatch.setattr(bateria, "confere_baseline", explode)
    assert bateria.roda_bateria_php(tmp_path, ["gestor"]) == 2
    assert ids(tmp_path) == {"passo:banco": "ERRO_AMBIENTE"}
    for passo in ("restaura_dump", "obtem_sid", "lint", "classes", "telas", "post", "relatorio"):
        assert passo not in amb


def test_falha_na_restauracao_tambem_rejeita(amb, monkeypatch, tmp_path):
    def explode(*a):
        raise ErroAmbienteBanco("pg_restore falhou")
    monkeypatch.setattr(bateria, "restaura_dump", explode)
    assert bateria.roda_bateria_php(tmp_path, ["gestor"]) == 2
    assert "lint" not in amb and "telas" not in amb


def test_sessao_invalida_para_tudo(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria, "sessao_autenticada", lambda s: False)
    assert bateria.roda_bateria_php(tmp_path, ["gestor"]) == 2
    assert ids(tmp_path) == {"passo:sessao": "ERRO_AMBIENTE"}
    assert "lint" not in amb


def test_diverge_conhecida_nao_quebra_rodada(amb, monkeypatch, tmp_path):
    (bateria.CONHECIDAS).write_text("# id\tmotivo\nrelatorio:pro2_r002.php\tpreexistente, provado\n", encoding="utf-8")
    monkeypatch.setattr(bateria, "roda_relatorio",
                        lambda sid, c: Caso(c.url, c.area, V.DIVERGE, "dif"))
    # nao-verificado fica de fora; so o pro2 (conhecido) diverge
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 0
    casos = {c["id"]: c for c in le(tmp_path)["casos"]}
    assert casos["relatorio:pro2_r002.php"]["veredito"] == "DIVERGE" and casos["relatorio:pro2_r002.php"]["conhecida"] is True


def test_diverge_nova_da_codigo_1(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria, "roda_relatorio", lambda sid, c: Caso(c.url, c.area, V.DIVERGE, "HTTP 500"))
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 1


def test_nao_verificadas_nao_rodam_por_padrao_e_sao_contadas(amb, tmp_path):
    bateria.roda_bateria_php(tmp_path)  # todas as areas
    resultado = ids(tmp_path)
    assert "post:rec1_b001.php" not in resultado and "relatorio:con2_r002.php" not in resultado
    cat = le(tmp_path)["meta"]["catalogo_posts"]
    assert cat["nao_verificado_pulados"] == 1 and cat["nao_verificado_pulados_ids"] == ["rec1_b001.php"]
    assert le(tmp_path)["meta"]["catalogo_relatorios"]["nao_verificado_pulados"] == 1
    assert "nao_verificado_pulados" in (tmp_path / "resultado.json").read_text(encoding="utf-8")


def test_incluir_nao_verificados_roda_todas(amb, tmp_path):
    bateria.roda_bateria_php(tmp_path, incluir_nao_verificados=True)
    resultado = ids(tmp_path)
    assert "post:rec1_b001.php" in resultado and "relatorio:con2_r002.php" in resultado


def test_sem_restaurar_marca_o_resumo(amb, tmp_path, capsys):
    bateria.roda_bateria_php(tmp_path, ["gestor"], restaurar=False)
    assert "banco NAO restaurado: resultado nao comparavel" in capsys.readouterr().err
    assert le(tmp_path)["meta"]["comparavel"] is False
    assert "restaura_dump" not in amb
    resumo = (tmp_path / "resumo.md").read_text(encoding="utf-8")
    assert "banco NAO restaurado: resultado nao comparavel" in resumo
    assert le(tmp_path)["meta"]["aviso"] == "banco NAO restaurado: resultado nao comparavel"
    assert le(tmp_path)["meta"]["restauracao_s"] is None


def test_area_desconhecida_falha_antes_de_rodar(amb, tmp_path):
    with pytest.raises(bateria.AreaDesconhecida, match="nao-existe"):
        bateria.roda_bateria_php(tmp_path, ["gestor", "nao-existe"])
    assert amb == [] and not (tmp_path / "resultado.json").exists()
    assert bateria.main(["--saida", str(tmp_path), "--area", "xyz"]) == 2
    assert amb == []


def test_aliases_e_acentos_das_areas():
    assert bateria.resolve_areas(["Tributário"])[0] == ["tributario"]
    assert bateria.resolve_areas(["Recursos Humanos", "rh"])[0] == ["recursoshumanos"]
    assert bateria.resolve_areas(["Educação"])[0] == ["educacao"]
    assert bateria.resolve_areas(["configuracao"])[1][:2] == ["amb", "ate"]


def test_um_passo_que_falha_nao_derruba_os_outros(amb, monkeypatch, tmp_path):
    def explode(arqs):
        raise RuntimeError("php -l quebrou")
    monkeypatch.setattr(bateria, "roda_lint", explode)
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 2
    resultado = ids(tmp_path)
    assert resultado["passo:sintaxe"] == "ERRO_AMBIENTE"
    assert "telas" in amb and "post" in amb and "relatorio" in amb  # continuaram


def test_post_que_levanta_vira_erro_so_dessa_linha(amb, monkeypatch, tmp_path):
    def explode(sid, c):
        if c.tela == "rec1_x.php":
            raise OSError("boom")
        return Caso(c.tela, c.area, V.IDENTICO)
    monkeypatch.setattr(bateria, "roda_post", explode)
    bateria.roda_bateria_php(tmp_path)
    r = ids(tmp_path)
    assert r["post:rec1_x.php"] == "ERRO_AMBIENTE" and r["post:orc1_c001.php"] == "IDENTICO"


def test_filtra_catalogo_pela_area(amb, tmp_path):
    bateria.roda_bateria_php(tmp_path, ["assistenciasocial"])  # prefixos hab, pro, rec, soc
    r = ids(tmp_path)
    assert "post:rec1_x.php" in r and "relatorio:pro2_r002.php" in r and "post:orc1_c001.php" not in r
    assert le(tmp_path)["meta"]["catalogo_posts"]["fora_da_area"] == 1


def test_sem_normalizar_esvazia_regras_so_durante_a_rodada(amb, monkeypatch, tmp_path):
    from regressao.nucleo.normaliza import REGRAS, normaliza
    antes = len(REGRAS)
    vistas = []
    monkeypatch.setattr(bateria, "roda_lint", lambda arqs: vistas.append(normaliza(b"sid=" + b"a" * 10)) or [])
    bateria.roda_bateria_php(tmp_path, ["gestor"], normalizar=False)
    assert vistas == [b"sid=" + b"a" * 10] and len(REGRAS) == antes
    assert normaliza(b"sid=" + b"a" * 10) == b"sid=X"


@pytest.mark.parametrize("veredito,conhecida,esperado", [
    (V.IDENTICO, False, 0), (V.INCONCLUSIVO, False, 0), (V.DIVERGE, True, 0),
    (V.DIVERGE, False, 1), (V.ERRO_AMBIENTE, False, 2)])
def test_mapeamento_do_codigo_de_saida(veredito, conhecida, esperado):
    assert codigo_saida([Caso("x", "a", veredito, conhecida=conhecida)]) == esperado
    assert codigo_saida([Caso("x", "a", V.DIVERGE), Caso("y", "a", V.ERRO_AMBIENTE)]) == 2


def test_sem_normalizacao_restaura_regras_se_levantar():
    from regressao.nucleo.normaliza import REGRAS
    antes = list(REGRAS)
    with pytest.raises(RuntimeError):
        with bateria.sem_normalizacao():
            assert REGRAS == []
            raise RuntimeError("x")
    assert REGRAS == antes


def test_ids_unicos_no_resultado_json(amb, tmp_path):
    bateria.roda_bateria_php(tmp_path, ["assistenciasocial"])
    todos = [c["id"] for c in le(tmp_path)["casos"]]
    assert len(todos) == len(set(todos))
    assert {"sintaxe:rec1_x.php", "tela:rec1_x.php", "post:rec1_x.php"} <= set(todos)
    assert "tela-run:rec:telas" in todos and "classe:classes/db_a_classe.php" in todos


def test_ids_que_ainda_colidem_ganham_sufixo(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria, "roda_post", lambda sid, c: Caso("mesmo", "rh", V.IDENTICO))
    bateria.roda_bateria_php(tmp_path)  # todas as areas: duas linhas de POST devolvem o mesmo id
    todos = [c["id"] for c in le(tmp_path)["casos"]]
    assert len(todos) == len(set(todos)) and "post:mesmo#2" in todos
    assert le(tmp_path)["meta"]["ids_renomeados"]


def test_conhecida_so_cobre_a_etapa_do_id(amb, monkeypatch, tmp_path):
    bateria.CONHECIDAS.write_text("tela:rec1_x.php\tpreexistente\n", encoding="utf-8")
    monkeypatch.setattr(bateria, "roda_telas", lambda sid, rx, a: ([Caso("rec1_x.php", a, V.DIVERGE, "t")], {}))
    monkeypatch.setattr(bateria, "roda_post", lambda sid, c: Caso(c.tela, c.area, V.DIVERGE, "p"))
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 1
    casos = {c["id"]: c for c in le(tmp_path)["casos"]}
    assert casos["tela:rec1_x.php"]["conhecida"] is True
    assert casos["post:rec1_x.php"]["conhecida"] is False


def test_nome_de_diff_seguro_e_unico(amb, monkeypatch, tmp_path):
    monkeypatch.setattr(bateria, "roda_relatorio",
                        lambda sid, c: Caso("db_download.php?a=/x&b=1", c.area, V.DIVERGE, "d", "-a\n+b"))
    monkeypatch.setattr(bateria, "roda_post",
                        lambda sid, c: Caso("db/download.php?a=/x&b=1", c.area, V.DIVERGE, "d", "-a\n+b"))
    monkeypatch.setattr(bateria, "carrega_catalogo_relatorios",
                        lambda c: [RelCaso("db_download.php", "a=/x&b=1", "xls", "x", True)])
    bateria.roda_bateria_php(tmp_path, None)
    arqs = sorted(p.name for p in (tmp_path / "diffs").iterdir())
    assert len(arqs) == 3 and len(set(a.lower() for a in arqs)) == 3  # 2 POSTs (id repetido) + 1 relatorio
    assert all(re.fullmatch(r"[A-Za-z0-9._~-]+\.diff", a) for a in arqs)


def test_corpos_sao_reduzidos_a_hash_e_pico_registrado(amb, tmp_path):
    from regressao.nucleo.normaliza import hash_corpo
    bateria.roda_bateria_php(tmp_path, ["assistenciasocial"])
    hs = [p for p in tmp_path.iterdir() if p.name.startswith("hashes_")][0].read_text()
    assert f"rec1_x.php\t{hash_corpo(b'<td>1</td>')}\n" in hs
    meta = le(tmp_path)["meta"]
    assert meta["pico_corpos_em_memoria"] == 1 and meta["telas_com_dados"] == 4


def test_hashes_e_cobertura_a_partir_de_reducoes(tmp_path):
    from regressao.nucleo.normaliza import hash_corpo
    from regressao.php.cobertura import cobertura_de_flags, cobertura_telas
    from regressao.php.hashes import grava_hashes, grava_hashes_de_hashes
    corpos = {"b.php": b"<td>x", "a.php": b"<thead><td>x</thead>"}
    a = grava_hashes(tmp_path, corpos, "1")
    b = grava_hashes_de_hashes(tmp_path / "o", {t: hash_corpo(c) for t, c in corpos.items()}, "1")
    assert a.read_text() == b.read_text()
    assert cobertura_de_flags({"b.php": True, "a.php": False}) == cobertura_telas([], corpos)


def test_sessao_expirada_antes_dos_posts_para_a_rodada(amb, monkeypatch, tmp_path):
    estado = {"n": 0}

    def sessao(sid):
        estado["n"] += 1
        return estado["n"] == 1  # so a checagem inicial passa
    monkeypatch.setattr(bateria, "sessao_autenticada", sessao)
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 2
    r = ids(tmp_path)
    assert r["passo:sessao:posts"] == "ERRO_AMBIENTE"
    assert "post" not in amb and "relatorio" not in amb and "telas" in amb


def test_sessao_expirada_antes_dos_relatorios(amb, monkeypatch, tmp_path):
    estado = {"n": 0}

    def sessao(sid):
        estado["n"] += 1
        return estado["n"] <= 2
    monkeypatch.setattr(bateria, "sessao_autenticada", sessao)
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 2
    assert ids(tmp_path)["passo:sessao:relatorios"] == "ERRO_AMBIENTE"
    assert "post" in amb and "relatorio" not in amb


def test_sessao_que_morre_no_meio_e_renovada_e_a_rodada_segue_ate_o_fim(amb, monkeypatch, tmp_path):
    vivas = {"sid123": False, "nova1": True}                  # a sessao inicial passa so na 1a checagem
    estado = {"n": 0}

    def sessao(sid):
        estado["n"] += 1
        return True if estado["n"] == 1 else vivas.get(sid, False)
    monkeypatch.setattr(bateria, "sessao_autenticada", sessao)
    renovadas = []
    monkeypatch.setattr(bateria, "renova_sessao", lambda sid, **k: renovadas.append(sid) or "nova1")
    usados = []
    monkeypatch.setattr(bateria, "roda_post", lambda sid, c: usados.append(("post", sid)) or Caso(c.tela, c.area, V.IDENTICO))
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 0
    r = ids(tmp_path)
    assert not any(k.startswith("passo:sessao") for k in r)   # nada de ERRO_AMBIENTE em massa
    assert renovadas == ["sid123"] and all(sid == "nova1" for _, sid in usados) and usados
    assert "relatorio" in amb
    assert le(tmp_path)["meta"]["sessao_renovacoes"] == [{"motivo": "expirou antes de posts", "ok": True}]


def test_prefixo_cuja_sessao_morreu_e_refeito_com_a_sessao_renovada(amb, monkeypatch, tmp_path):
    chamadas = []

    def telas(sid, rx, a):
        chamadas.append(sid)
        if sid == "sid123":
            return [Caso("telas", a, V.ERRO_AMBIENTE, "sessao nao autenticada (pagina 'Sessao invalida')")], {}
        return [Caso("hab1_x.php", a, V.IDENTICO)], {"hab1_x.php": b"<td>1</td>"}
    monkeypatch.setattr(bateria, "roda_telas", telas)
    monkeypatch.setattr(bateria, "renova_sessao", lambda sid, **k: "nova1")
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 0
    assert chamadas[0] == "sid123" and set(chamadas[1:]) == {"nova1"}
    r = ids(tmp_path)
    assert "tela:hab1_x.php" in r and not any(v == "ERRO_AMBIENTE" for v in r.values())


def test_renovacao_limitada_sessao_que_nao_volta_vira_erro_de_ambiente_uma_vez_por_prefixo(amb, monkeypatch, tmp_path):
    tentativas = []
    monkeypatch.setattr(bateria, "renova_sessao", lambda sid, **k: tentativas.append(sid) or None)
    monkeypatch.setattr(bateria, "roda_telas", lambda sid, rx, a: ([Caso("telas", a, V.ERRO_AMBIENTE,
                        "sessao nao autenticada (pagina 'Sessao invalida')")], {}))
    assert bateria.roda_bateria_php(tmp_path, ["assistenciasocial"]) == 2
    assert len(tentativas) <= bateria.MAX_RENOVACOES


def test_so_ref_e_php_novo_sao_exigidos(amb, monkeypatch, tmp_path):
    vistos = []
    monkeypatch.setattr(bateria, "verifica", lambda a: vistos.append(a) or [])
    bateria.roda_bateria_php(tmp_path, ["gestor"])
    assert vistos[0].laravel_novo == vistos[0].ref == vistos[0].proxy == "a" and vistos[0].php_novo == "b"


def test_prefixo_regex_estreita_telas_e_catalogos(amb, tmp_path):
    bateria.roda_bateria_php(tmp_path, prefixos_regex=["^rec1_"])
    r = ids(tmp_path)
    assert "tela:rec1_x.php" in r and "post:rec1_x.php" in r
    assert not any(k.startswith("tela:") and not k.startswith("tela:rec1") for k in r)
    assert "post:orc1_c001.php" not in r and "relatorio:pro2_r002.php" not in r
    assert le(tmp_path)["meta"]["prefixos_regex"] == ["^rec1_"]


def test_pular_sintaxe_e_classes_roda_so_telas_posts_e_relatorios_e_marca_parcial(amb, tmp_path):
    bateria.roda_bateria_php(tmp_path, ["assistenciasocial"], pular={"sintaxe", "classes"})
    assert "lint" not in amb and "classes" not in amb and {"telas", "post", "relatorio"} <= set(amb)
    meta = le(tmp_path)["meta"]
    assert meta["etapas_puladas"] == ["classes", "sintaxe"] and meta["parcial"] is True
    assert not any(k.startswith(("sintaxe:", "classe:")) for k in ids(tmp_path))


def test_pular_etapa_desconhecida_e_argumento_invalido(amb, tmp_path):
    with pytest.raises(bateria.ArgumentoInvalido, match="etapa"):
        bateria.roda_bateria_php(tmp_path, ["gestor"], pular={"telas"})
    assert bateria.main(["--saida", str(tmp_path), "--pular", "xyz"]) == 2


def test_cli_pular_repetivel(amb, monkeypatch, tmp_path):
    vistos = {}
    monkeypatch.setattr(bateria, "roda_bateria_php", lambda *a, **k: vistos.update(k) or 0)
    assert bateria.main(["--saida", str(tmp_path), "--pular", "sintaxe", "--pular", "classes"]) == 0
    assert vistos["pular"] == {"sintaxe", "classes"}


def test_catalogo_fora_de_qualquer_area_roda_quando_o_prefixo_regex_casa_explicitamente(amb, monkeypatch, tmp_path):
    rels = [RelCaso("pro2_r002.php", "", "pdf", "protocolo", True),
            RelCaso("db_download.php", "arquivo=tmp/x.csv", "xls", "contabilidade", True)]
    monkeypatch.setattr(bateria, "carrega_catalogo_relatorios", lambda c: rels)
    bateria.roda_bateria_php(tmp_path, prefixos_regex=["^rec1_", r"^db_download\.php$"])
    r = ids(tmp_path)
    assert "relatorio:db_download.php?arquivo=tmp/x.csv" in r      # sem prefixo de area, mas pedido pelo regex
    assert "relatorio:pro2_r002.php" not in r                      # dentro de area: segue o filtro de sempre


def test_catalogo_fora_de_qualquer_area_continua_de_fora_sem_regex_explicito(amb, monkeypatch, tmp_path):
    rels = [RelCaso("db_download.php", "arquivo=tmp/x.csv", "xls", "contabilidade", True)]
    monkeypatch.setattr(bateria, "carrega_catalogo_relatorios", lambda c: rels)
    bateria.roda_bateria_php(tmp_path, ["assistenciasocial"])
    assert not any(k.startswith("relatorio:") for k in ids(tmp_path))


def test_prefixo_regex_invalido_ou_vazio_falha_antes_de_rodar(amb, tmp_path):
    with pytest.raises(bateria.ArgumentoInvalido):
        bateria.roda_bateria_php(tmp_path, prefixos_regex=["("])
    with pytest.raises(bateria.ArgumentoInvalido, match="nenhuma tela"):
        bateria.roda_bateria_php(tmp_path, prefixos_regex=["^nada_"])
    assert amb == []
    assert bateria.main(["--saida", str(tmp_path), "--prefixo", "("]) == 2


def test_todo_prefixo_de_area_casa_algum_arquivo():
    raiz = bateria.RAIZ / "ecidade"
    if not raiz.is_dir():
        pytest.skip(f"{raiz} ausente: sem arvore do e-cidade para conferir AREAS")
    nomes = [f.name for f in raiz.iterdir()]
    for area, prefixos in bateria.AREAS.items():
        for p in prefixos:
            rx = re.compile(bateria._regex_prefixo(p), re.I)
            assert any(rx.match(n) and n.endswith(".php") for n in nomes), f"{area}: prefixo {p} sem arquivo"
