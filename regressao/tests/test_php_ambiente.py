"""A bateria PHP e os auxiliares do scratchpad leem containers e portas de regressao/nucleo/ambiente.py:
padroes do ambiente e74 (referencia PHP 7.4 em ecidade74_php74/:8074, alvo PHP 8.5 em ecidade74_php85/:8185,
banco ecidade74_database), trocaveis por variavel de ambiente. Nenhum nome da pilha antiga (ecidade_php56,
:8080/:8085) pode sobrar."""
import importlib.util
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from regressao.php import bateria, classes, relatorios, sintaxe, telas
from regressao.php.relatorios import RelCaso

RAIZ = Path(__file__).resolve().parents[2]
SCRATCH = RAIZ / "scratchpad"
_VARS = ("REGRESSAO_REF_URL", "REGRESSAO_PHP_NOVO_URL", "REGRESSAO_NOVO_URL", "REGRESSAO_LARAVEL_NOVO_URL",
         "REGRESSAO_PROXY_URL", "REGRESSAO_CONTAINER_REF", "REGRESSAO_CONTAINER_PHP_NOVO",
         "REGRESSAO_CONTAINER_BANCO", "REGRESSAO_CONTAINER_PROXY")


@pytest.fixture(autouse=True)
def sem_variaveis(monkeypatch):
    for v in _VARS:
        monkeypatch.delenv(v, raising=False)
    return monkeypatch


def _outro_ambiente(m):
    m.setenv("REGRESSAO_CONTAINER_REF", "c_ref")
    m.setenv("REGRESSAO_CONTAINER_PHP_NOVO", "c_novo")
    m.setenv("REGRESSAO_CONTAINER_BANCO", "c_banco")
    m.setenv("REGRESSAO_REF_URL", "http://localhost:9001")
    m.setenv("REGRESSAO_PHP_NOVO_URL", "http://localhost:9002/")


def _carrega(nome: str):
    spec = importlib.util.spec_from_file_location(f"_scratch_{nome}", SCRATCH / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # nao pode rodar nada no import (sem argv, sem docker)
    return mod


def _docker_que_grava(chamadas, resposta=b""):
    def f(args, timeout, stdin=None, stdout=None):
        chamadas.append(args)
        return resposta
    return f


# ---------------------------------------------------------------- codigo da bateria (regressao/php)

@pytest.mark.parametrize("arq", ["telas.py", "sintaxe.py", "relatorios.py", "bateria.py", "classes.py",
                                 "posts.py"])
def test_php_nao_tem_nome_nem_porta_da_pilha_antiga(arq):
    texto = (RAIZ / "regressao" / "php" / arq).read_text(encoding="utf-8")
    assert not re.search(r"ecidade_php56|ecidade_php85|ecidade_database|localhost:80(80|85|90)|:8080\b|:8085\b",
                         texto)


@pytest.mark.parametrize("arq", ["cmp.py", "escrita_post.py", "porclasse.sh"])
def test_scratchpad_nao_tem_nome_nem_porta_da_pilha_antiga(arq):
    texto = (SCRATCH / arq).read_text(encoding="utf-8")
    assert not re.search(r"ecidade_php56|ecidade_php85|ecidade_database|ecidade_tcc|ecidade_lar12|\b80(80|85|86|87)\b",
                         texto)


def test_sintaxe_usa_os_containers_do_ambiente(sem_variaveis):
    vistos = []
    ok = b"No syntax errors detected in a.php\n"
    with patch.object(sintaxe, "_docker", lambda a, t, stdin=None, stdout=None: vistos.append(a[1]) or ok):
        sintaxe.roda_lint(["a.php"])
        _outro_ambiente(sem_variaveis)
        sintaxe.roda_lint(["a.php"])
    assert vistos == ["ecidade74_php74", "ecidade74_php85", "c_ref", "c_novo"]


def test_sintaxe_diz_referencia_e_nao_5_6():
    respostas = iter([b"PHP Parse error: x\n", b"No syntax errors detected in a.php\n"])
    with patch.object(sintaxe, "_docker", lambda *a, **k: next(respostas)):
        c = sintaxe.roda_lint(["a.php"])[0]
    assert "referencia (7.4)" in c.detalhe and "5.6" not in c.detalhe


def test_classes_rodam_nos_containers_do_ambiente(sem_variaveis, tmp_path):
    chamadas = []
    _outro_ambiente(sem_variaveis)
    with patch.object(classes, "DESTINO", tmp_path), patch.object(classes, "_docker", _docker_que_grava(chamadas)):
        classes.roda_classes(["classes/db_x_classe.php"])
    assert [a[2] for a in chamadas] == ["c_ref", "c_novo"]


def test_classes_divergencia_diz_ref_e_nao_5_6():
    c = classes.compara_classes("classes/a.php\tz\t'1'\n", "classes/a.php\tz\t0\n")[0]
    assert "ref='1'" in c.detalhe and "5.6" not in c.detalhe


def test_telas_sessao_e_requisicao_no_container_de_referencia(sem_variaveis):
    chamadas = []
    _outro_ambiente(sem_variaveis)
    with patch.object(telas, "_docker", _docker_que_grava(chamadas, b"/var/lib/php/sessions/sess_abc\n")):
        assert telas.obtem_sid() == "abc"
        telas.restaura_sessao("abc")
        telas._atualiza_backup("abc")
        telas._requisita("abc", "x.php")
        telas._requisita_status("abc", "x.php")
    conts = [a[a.index("sh") - 1] for a in chamadas]
    assert conts == ["c_ref"] * 5


def test_reavalia_pdf_usa_referencia_e_alvo_do_ambiente(sem_variaveis):
    _outro_ambiente(sem_variaveis)
    vistos = []
    with patch.object(telas, "restaura_sessao"), \
         patch.object(telas, "_requisita_status", lambda sid, tela, container: vistos.append(container) or (200, b"x")):
        telas._reavalia_pdf_impl("s", "r.php")
    assert vistos == ["c_ref"]  # nao e PDF: para no primeiro lado
    vistos.clear()
    with patch.object(telas, "restaura_sessao"), \
         patch.object(telas, "_requisita_status",
                      lambda sid, tela, container: vistos.append(container) or (200, b"%PDF-1.3 x")), \
         patch("regressao.php.relatorios.extrai_conteudo", return_value="t"):
        assert telas._reavalia_pdf_impl("s", "r.php") is True
    assert vistos == ["c_ref", "c_novo"]


def test_relatorio_requisita_referencia_e_alvo_do_ambiente(sem_variaveis):
    _outro_ambiente(sem_variaveis)
    vistos = []
    with patch.object(relatorios, "restaura_sessao"), \
         patch.object(relatorios, "_requisita_status",
                      side_effect=lambda sid, url, container: vistos.append(container) or (200, b"<p>a</p>")):
        relatorios.roda_relatorio("s", RelCaso("a.php", "", "html", "x", True))
    assert vistos == ["c_ref", "c_novo"]


def test_relatorio_mensagens_e_diff_dizem_ref():
    r = relatorios.compara_relatorio(b"<p>a</p>", b"<p>b</p>", RelCaso("a.php", "", "html", "x", True), 200, 500)
    assert "ref=200" in r.detalhe and "8.5=500" in r.detalhe and "5.6" not in r.detalhe
    assert r.diff.startswith("--- ref (7.4)\n+++ 8.5")


def test_metadados_da_bateria_usam_containers_do_ambiente(sem_variaveis):
    _outro_ambiente(sem_variaveis)
    vistos = []
    with patch.object(bateria, "_docker", lambda a, t: vistos.append(a[1]) or b"7.4.33"):
        meta = bateria._metadados_ambiente()
    assert vistos == ["c_ref", "c_novo"]
    assert meta["php_ref"] == "7.4.33" and "php_85" in meta and "php_56" not in meta


def test_orquestrador_leva_a_versao_da_referencia_da_bateria_php():
    from regressao.completa.orquestra import Frente, _versoes
    v = _versoes({"php": Frente("php", 0, [], {"php_ref": "7.4.33", "php_85": "8.5.12"}, 0)})
    assert v == {"php_ref": "7.4.33", "php_85": "8.5.12"}


# ---------------------------------------------------------------- scratchpad/cmp.py

def test_cmp_importa_sem_efeito_e_le_lados_do_ambiente(sem_variaveis):
    cmp = _carrega("cmp")
    assert cmp.lados() == [("ref", "http://localhost:8074", "ecidade74_php74"),
                           ("85", "http://localhost:8185", "ecidade74_php85")]
    _outro_ambiente(sem_variaveis)
    assert cmp.lados() == [("ref", "http://localhost:9001", "c_ref"), ("85", "http://localhost:9002", "c_novo")]


def test_cmp_normaliza_o_host_dos_alvos_do_ambiente(sem_variaveis):
    cmp = _carrega("cmp")
    regras = cmp.regras_norm()
    a = cmp.norm(b"<a href='http://localhost:8074/x.php'>", regras)
    b = cmp.norm(b"<a href='http://localhost:8185/x.php'>", regras)
    assert a == b == b"<a href='http://localhost:PORT/x.php'>"
    _outro_ambiente(sem_variaveis)
    regras = cmp.regras_norm()
    assert cmp.norm(b"localhost:9001", regras) == cmp.norm(b"localhost:9002", regras) == b"localhost:PORT"


def test_cmp_imprime_ref_e_85_e_restaura_no_container_de_referencia(sem_variaveis, tmp_path, capsys):
    cmp = _carrega("cmp")
    (tmp_path / "cem1_a001.php").write_text("x")
    comandos = []

    def sh(c):
        comandos.append(c)

        class R:
            stdout = b"corpo\n@@200@0.1" if ":8074/" in c else b"outro\n@@500@0.1" if ":8185/" in c else b""
        return R()
    with patch.object(cmp, "sh", sh):
        cmp.main(["cmp.py", "SID", "^cem"], diretorio=tmp_path)
    out = capsys.readouterr().out
    assert re.search(r"DIVERGE cem1_a001\.php  ref=200/5B  85=500/5B", out)
    assert "=== 0/1 identicas, 1 divergentes, 0 timeout ===" in out
    assert all("ecidade74_php74" in c for c in comandos if c.startswith("docker exec"))


# ---------------------------------------------------------------- scratchpad/escrita_post.py

def test_escrita_post_importa_sem_efeito_e_usa_banco_e_alvos_do_ambiente(sem_variaveis):
    ep = _carrega("escrita_post")
    assert ep.cmd_banco() == "docker exec -i ecidade74_database psql -U postgres -d ecidade"
    assert ep.lados() == [("ref", "http://localhost:8074"), ("8.5", "http://localhost:8185")]
    assert ep.container_sessoes() == "ecidade74_php74"
    _outro_ambiente(sem_variaveis)
    assert ep.cmd_banco().startswith("docker exec -i c_banco psql")
    assert ep.lados() == [("ref", "http://localhost:9001"), ("8.5", "http://localhost:9002")]
    assert ep.container_sessoes() == "c_ref"
