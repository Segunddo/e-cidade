from pathlib import Path
from unittest.mock import patch

import pytest

from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.veredito import Veredito
from regressao.php import telas
from regressao.php.cobertura import cobertura_telas
from regressao.php.hashes import compara_hashes, grava_hashes
from regressao.php.telas import parse_cmp

SAIDA = """3 telas

  DIVERGE cem1_cadastro001.php  ref=200/18668B  85=500/4558B
  TIMEOUT cem1_lento002.php  ref=000  85=200  (nao conta como identica)

=== 1/3 identicas, 1 divergentes, 1 timeout ===
"""
TELAS = ["cem1_cadastro001.php", "cem1_lento002.php", "cem1_ok003.php"]


def test_telas_que_destroem_a_sessao_nao_entram_na_lista_e_a_pulada_diz_o_motivo(tmp_path):
    for n in ("edu4_informacoesdump.php", "cad4_geracarneiptutxt_cli.php", "cad4_ok001.php", "iss4_siss002.php"):
        (tmp_path / n).write_text("x")
    assert telas.lista_telas(r"^(edu4|cad4|iss4)_", tmp_path) == ["cad4_ok001.php"]
    assert {"edu4_informacoesdump.php", "cad4_geracarneiptutxt_cli.php"} == telas.PULAR_SESSAO
    saida = ("3 telas\n\n  PULADA iss4_siss002.php  (contata servico externo)\n"
             "  PULADA cad4_geracarneiptutxt_cli.php  (destroi a sessao do harness)\n\n"
             "=== 0/0 identicas, 0 divergentes, 0 timeout ===\n")
    casos = {c.id: c for c in parse_cmp(saida, "x", [])}
    assert "servico externo" in casos["iss4_siss002.php"].detalhe
    assert "destroi a sessao" in casos["cad4_geracarneiptutxt_cli.php"].detalhe
    assert all(c.veredito == Veredito.INCONCLUSIVO for c in casos.values())


@pytest.fixture(autouse=True)
def _sessao_ok(request):
    """Fora dos testes que tratam da sessao, a sonda de autenticacao diz OK."""
    if "sessao" in request.node.name:
        yield
        return
    with patch.object(telas, "sessao_autenticada", return_value=True):
        yield


def _por_id(casos):
    return {c.id: c for c in casos}


def test_parse_cmp_divergente_vira_diverge():
    c = _por_id(parse_cmp(SAIDA, "configuracao", TELAS))["cem1_cadastro001.php"]
    assert c.veredito == Veredito.DIVERGE
    assert "ref=200/18668B" in c.detalhe and "85=500/4558B" in c.detalhe
    assert c.area == "configuracao"


def test_parse_cmp_timeout_nao_conta_como_igual():
    casos = _por_id(parse_cmp(SAIDA, "configuracao", TELAS))
    assert casos["cem1_lento002.php"].veredito == Veredito.ERRO_AMBIENTE
    assert casos["cem1_ok003.php"].veredito == Veredito.IDENTICO


def test_parse_cmp_sem_lista_de_telas_resume_as_identicas():
    casos = parse_cmp(SAIDA, "configuracao")
    resumo = [c for c in casos if c.id == "identicas"]
    assert len(resumo) == 1 and resumo[0].veredito == Veredito.IDENTICO
    assert "1" in resumo[0].detalhe


def test_parse_cmp_resumo_inconsistente_e_erro_ambiente():
    casos = parse_cmp("", "configuracao", TELAS)
    assert [c.veredito for c in casos] == [Veredito.ERRO_AMBIENTE]


def test_resposta_vazia_nos_dois_lados_e_inconclusiva():
    casos = _por_id(parse_cmp(SAIDA, "configuracao", TELAS, corpos={"cem1_ok003.php": b""}))
    assert casos["cem1_ok003.php"].veredito == Veredito.INCONCLUSIVO


def test_tela_pulada_e_inconclusiva():
    saida = "  PULADA iss4_siss002.php  (contata servico externo)\n2 telas\n\n=== 2/2 identicas, 0 divergentes, 0 timeout ===\n"
    casos = _por_id(parse_cmp(saida, "x", ["a.php", "b.php"]))
    assert casos["iss4_siss002.php"].veredito == Veredito.INCONCLUSIVO
    assert casos["a.php"].veredito == Veredito.IDENTICO


def test_compara_hashes_lista_telas_alteradas(tmp_path):
    a = grava_hashes(tmp_path / "a", {"t1": b"x", "t2": b"y", "t3": b"z"}, rodada="a")
    b = grava_hashes(tmp_path / "b", {"t1": b"x", "t2": b"mudou", "t4": b"w"}, rodada="b")
    assert a.name == "hashes_a.tsv"
    assert compara_hashes(a, b) == ["t2", "-t3", "+t4"]


def test_grava_hashes_ordenado_e_normalizado(tmp_path):
    p = grava_hashes(tmp_path, {"b": b"sid=0123456789abcdef", "a": b"sid=fedcba9876543210"}, rodada="r")
    linhas = p.read_text().splitlines()
    assert [l.split("\t")[0] for l in linhas] == ["a", "b"]
    assert linhas[0].split("\t")[1] == linhas[1].split("\t")[1]


def test_cobertura_distingue_tabela_vazia():
    corpos = {
        "cheia": b"<table><thead><tr><th>a</th></tr></thead><tr><td>1</td></tr></table>",
        "vazia": b"<table><thead><tr><td>cab</td></tr></thead></table>",
        "sem": b"<html>nada</html>",
    }
    r = cobertura_telas([], corpos)
    assert r["com_dados"] == ["cheia"]
    assert r["tabela_vazia"] == ["sem", "vazia"]


def test_roda_telas_erro_de_docker_vira_erro_ambiente():
    with patch.object(telas, "lista_telas", return_value=["a.php"]), \
         patch.object(telas, "_roda_cmp", side_effect=OSError("sem python3")):
        casos, corpos = telas.roda_telas("abc", "^cem", "configuracao")
    assert [c.veredito for c in casos] == [Veredito.ERRO_AMBIENTE]
    assert corpos == {}


def test_roda_telas_junta_lista_de_telas_e_saida_do_cmp():
    saida = ("2 telas\n\n  DIVERGE cem1_a.php  ref=200/1B  85=200/2B\n"
             "\n=== 1/2 identicas, 1 divergentes, 0 timeout ===\n")
    with patch.object(telas, "lista_telas", return_value=["cem1_a.php", "cem1_b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=saida), \
         patch.object(telas, "busca_corpo", return_value=b"<td>x</td>"):
        casos, corpos = telas.roda_telas("s", "^cem", "x")
    assert {c.id: c.veredito for c in casos} == {"cem1_a.php": Veredito.DIVERGE, "cem1_b.php": Veredito.IDENTICO}
    assert list(corpos) == ["cem1_b.php"]


SAIDA_TODAS_IGUAIS = "2 telas\n\n=== 2/2 identicas, 0 divergentes, 0 timeout ===\n"


def test_tela_vazia_nos_dois_lados_e_inconclusiva_via_roda_telas():
    corpos_reais = {"a.php": b"", "b.php": b"<td>1</td>"}
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=SAIDA_TODAS_IGUAIS), \
         patch.object(telas, "busca_corpo", side_effect=lambda sid, t: corpos_reais[t]):
        casos, corpos = telas.roda_telas("s", "^", "x")
    v = {c.id: c for c in casos}
    assert v["a.php"].veredito == Veredito.INCONCLUSIVO and "vazi" in v["a.php"].detalhe
    assert v["b.php"].veredito == Veredito.IDENTICO
    assert corpos == corpos_reais


def test_corpo_so_com_normalizacao_vazia_e_inconclusivo():
    # heuristica fixa = 0 bytes apos normalizar; so quebra de linha continua IDENTICO
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=SAIDA_TODAS_IGUAIS), \
         patch.object(telas, "busca_corpo", return_value=b"\n"):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert {c.veredito for c in casos} == {Veredito.IDENTICO}


@pytest.mark.parametrize("corpo", [
    b"<html><title>Notifica\xe7\xe3o do Sistema</title><body>Erro interno</body></html>",
    b"<br />\n<b>Fatal error</b>: Uncaught Error: Call to undefined function x() in /var/www/html/a.php",
    b"<b>Parse error</b>: syntax error",
])
def test_pagina_de_erro_igual_nos_dois_lados_e_inconclusiva(corpo):
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=SAIDA_TODAS_IGUAIS), \
         patch.object(telas, "busca_corpo", side_effect=lambda sid, t: corpo if t == "a.php" else b"<td>1</td>"):
        casos, _ = telas.roda_telas("s", "^", "x")
    v = {c.id: c for c in casos}
    assert v["a.php"].veredito == Veredito.INCONCLUSIVO and "erro" in v["a.php"].detalhe.lower()
    assert v["b.php"].veredito == Veredito.IDENTICO


def test_tela_grande_que_apenas_cita_erro_interno_continua_identica():
    corpo = b"<td>x</td>" * 5000 + b"<p>Erro interno</p>"   # > 20 KB: tela real, nao pagina de erro
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=SAIDA_TODAS_IGUAIS), \
         patch.object(telas, "busca_corpo", return_value=corpo):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert {c.veredito for c in casos} == {Veredito.IDENTICO}


def test_falha_ao_buscar_corpo_e_erro_ambiente():
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=SAIDA_TODAS_IGUAIS), \
         patch.object(telas, "busca_corpo", side_effect=ErroAmbienteBanco("docker caiu")):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert [c.veredito for c in casos] == [Veredito.ERRO_AMBIENTE]
    assert "docker caiu" in casos[0].detalhe


def test_roda_cmp_remove_only_e_porta_b_do_ambiente(monkeypatch):
    for k in ("ONLY", "PORTA_B", "NORM_MENU"):
        monkeypatch.setenv(k, "1")
    monkeypatch.setenv("PATH_MARCA", "mantida")
    capturado = {}

    def falso_run(cmd, **kw):
        capturado.update(kw)

        class R:
            stdout = b"ok"
        return R()

    with patch.object(telas.subprocess, "run", side_effect=falso_run):
        assert telas._roda_cmp("s", "^cem") == "ok"
    env = capturado["env"]
    assert not {"ONLY", "PORTA_B", "NORM_MENU"} & set(env)
    assert env["PATH_MARCA"] == "mantida"


def test_total_do_resumo_diferente_da_lista_e_erro_ambiente():
    saida = "3 telas\n\n=== 3/3 identicas, 0 divergentes, 0 timeout ===\n"
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=saida), \
         patch.object(telas, "busca_corpo", return_value=b"x"):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert [c.veredito for c in casos] == [Veredito.ERRO_AMBIENTE]
    assert "3" in casos[0].detalhe and "2" in casos[0].detalhe


def test_lista_telas_espelha_selecao_do_cmp(tmp_path):
    for n in ("cem1_a.php", "CEM2_b.php", "cem3.txt", "outra.php", "iss4_siss002.php"):
        (tmp_path / n).write_text("")
    assert telas.lista_telas("^cem", tmp_path) == ["CEM2_b.php", "cem1_a.php"]
    assert telas.lista_telas("^iss4", tmp_path) == []


INVALIDA = "Sessão inválida (12).\nFeche seu navegador e faça login novamente.\n".encode("iso-8859-1")


def test_sessao_autenticada_false_com_pagina_sessao_invalida():
    with patch.object(telas, "_docker", return_value=INVALIDA):
        assert telas.sessao_autenticada("x") is False


VARIANTES = {
    "db_conecta (12)": "Sessão inválida (12).\nFeche seu navegador e faça login novamente.\n",
    "db_sessoes (14)": "Sessão Inválida!(14)<br>Feche seu navegador e faça login novamente.<Br>\n",
    "terminada": "Contate com Administrador do Sistema! (Conexão Inválida.)   <br>Sessão terminada, feche seu navegador!\n",
    "desativado": "Sistema desativado pelo administrador!   <br>Sessão terminada, feche seu navegador!\n",
    # libs/db_usuariosonline.php:49 e topo.php:43: a sessao nao abre conexao com o banco (rodada pequena de
    # 2026-11-18: 50 B, sem '<', aceitos como sessao valida e todas as telas da referencia vieram assim)
    "usuariosonline (27)": "Erro:(27) inserindo arquivo em db_usuariosonline: ",
    "usuariosonline (26)": "Erro(26) atualizando db_usuariosonline",
}


@pytest.mark.parametrize("corpo", [b"Erro:(27) inserindo arquivo em db_usuariosonline: ",
                                   b"Erro(26) atualizando db_usuariosonline"])
def test_sessao_autenticada_false_quando_a_sessao_nao_conecta_no_banco(corpo):
    with patch.object(telas, "_docker", return_value=corpo):
        assert telas.sessao_autenticada("x") is False


@pytest.mark.parametrize("codificacao", ["iso-8859-1", "utf-8"])
@pytest.mark.parametrize("nome", list(VARIANTES))
def test_corpo_de_sessao_invalida_reconhece_variantes(nome, codificacao):
    assert telas.corpo_de_sessao_invalida(VARIANTES[nome].encode(codificacao)) is True


def test_corpo_de_sessao_invalida_ignora_maiusculas():
    assert telas.corpo_de_sessao_invalida(b"SESS\xc3O INV\xc1LIDA") is True


def test_pagina_legitima_grande_com_a_frase_nao_e_sessao_invalida():
    corpo = b"<html>" + b"x" * 1500 + "Sessão inválida (12). Feche seu navegador".encode("utf-8")
    assert telas.corpo_de_sessao_invalida(corpo) is False


@pytest.mark.parametrize("corpo", [b"", b"ok", b"\n\n"])
def test_sessao_autenticada_falha_fechado_com_corpo_vazio_ou_minusculo(corpo):
    with patch.object(telas, "_docker", return_value=corpo):
        assert telas.sessao_autenticada("x") is False


def test_sessao_autenticada_true_com_pagina_normal():
    with patch.object(telas, "_docker", return_value=b"<html>" + b"x" * 5000):
        assert telas.sessao_autenticada("x") is True


def test_roda_telas_sessao_nao_autenticada_e_erro_ambiente_sem_rodar_cmp():
    def nao_deve_rodar(*a):
        raise AssertionError("cmp.py nao pode rodar sem sessao autenticada")
    with patch.object(telas, "sessao_autenticada", return_value=False), \
         patch.object(telas, "lista_telas", return_value=["a.php"]), \
         patch.object(telas, "_roda_cmp", side_effect=nao_deve_rodar):
        casos, corpos = telas.roda_telas("lixo", "^", "x")
    assert [c.veredito for c in casos] == [Veredito.ERRO_AMBIENTE]
    assert "sessao nao autenticada" in casos[0].detalhe and corpos == {}


def test_sessao_que_expira_no_meio_nao_aprova_tela():
    corpos_reais = {"a.php": INVALIDA, "b.php": b"<td>1</td>"}
    with patch.object(telas, "sessao_autenticada", return_value=True), \
         patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "_roda_cmp", return_value=SAIDA_TODAS_IGUAIS), \
         patch.object(telas, "busca_corpo", side_effect=lambda sid, t: corpos_reais[t]):
        casos, _ = telas.roda_telas("s", "^", "x")
    v = {c.id: c.veredito for c in casos}
    assert v == {"a.php": Veredito.ERRO_AMBIENTE, "b.php": Veredito.IDENTICO}


def test_busca_corpo_nao_forja_sessao_inexistente():
    comandos = []
    with patch.object(telas, "_docker", side_effect=lambda args, t, **k: comandos.append(args) or b"ok"):
        telas.busca_corpo("sid1", "a.php")
    assert "[ -f /var/lib/php/sessions/sess_sid1 ]" in comandos[0][-1]


def test_obtem_sid_extrai_nome_da_sessao():
    with patch.object(telas, "_docker", return_value=b"/var/lib/php/sessions/sess_abc123\n"):
        assert telas.obtem_sid() == "abc123"
