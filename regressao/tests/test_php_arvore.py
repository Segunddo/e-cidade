"""regressao/php/arvore.py: lista os .php fora das telas e compara o lint 7.4 x 8.5 (docker simulado)."""
from pathlib import Path

import pytest

from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.veredito import Veredito as V
from regressao.php import arvore


def _monta(raiz: Path, arquivos: list[str]) -> None:
    for a in arquivos:
        p = raiz / a
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("<?php\n", encoding="utf-8")


def test_lista_so_php_sem_vendor_tmp_node_modules_e_sem_excluidos(tmp_path):
    _monta(tmp_path, ["a.php", "b.php", "app/X.php", "src/A/B.php", "libs/node_modules/z.php",
                      "vendor/v.php", "tmp/t.php", "libs/vendor/ok.php", "classes/db_a_classe.php"])
    (tmp_path / "app" / "leia.txt").write_text("x", encoding="utf-8")
    achados = arvore.lista_arvore({"a.php"}, tmp_path)
    assert achados == ["app/X.php", "b.php", "classes/db_a_classe.php", "libs/vendor/ok.php", "src/A/B.php"]


def test_lista_sai_ordenada_e_com_barra(tmp_path):
    _monta(tmp_path, ["z/y.php", "a/b/c.php"])
    assert arvore.lista_arvore(frozenset(), tmp_path) == ["a/b/c.php", "z/y.php"]


@pytest.fixture
def docker(monkeypatch):
    """Cada container devolve as linhas FALHA que o teste configurar; guarda o que recebeu."""
    saidas = {"ref74": b"", "php85": b""}
    vistas = {}

    def fake(args, timeout, stdin=None, stdout=None):
        c = args[2]
        vistas[c] = stdin.read().decode() if stdin else ""
        return saidas[c]
    monkeypatch.setattr(arvore, "_docker", fake)
    monkeypatch.setattr(arvore, "containers_php", lambda: ("ref74", "php85"))
    return saidas, vistas


def test_compila_nos_dois_e_identico(docker):
    casos = arvore.roda_lint_arvore(["app/A.php", "src/B.php"])
    assert {c.id: c.veredito for c in casos} == {"app/A.php": V.IDENTICO, "src/B.php": V.IDENTICO}


def test_envia_a_lista_inteira_a_cada_container(docker):
    saidas, vistas = docker
    arvore.roda_lint_arvore(["app/A.php", "src/B.php"])
    assert vistas["ref74"] == vistas["php85"] == "app/A.php\nsrc/B.php\n"


def test_so_o_85_quebra_e_diverge_com_a_mensagem(docker):
    saidas, _ = docker
    saidas["php85"] = "FALHA\text/Markdown.php\tParse error: unexpected token \"{\" on line 800\n".encode()
    c = {c.id: c for c in arvore.roda_lint_arvore(["ext/Markdown.php", "ext/outro.php"])}
    assert c["ext/outro.php"].veredito == V.IDENTICO
    assert c["ext/Markdown.php"].veredito == V.DIVERGE
    assert c["ext/Markdown.php"].detalhe.startswith("php8.5: Parse error")


def test_so_a_referencia_quebra_tambem_diverge(docker):
    saidas, _ = docker
    saidas["ref74"] = b"FALHA\tx.php\tparse error\n"
    r = arvore.roda_lint_arvore(["x.php"])[0]
    assert r.veredito == V.DIVERGE and r.detalhe.startswith("referencia (7.4): parse error")


def test_nenhum_compila_e_inconclusivo(docker):
    saidas, _ = docker
    saidas["ref74"] = saidas["php85"] = b"FALHA\tx.php\terro antigo\n"
    r = arvore.roda_lint_arvore(["x.php"])[0]
    assert r.veredito == V.INCONCLUSIVO and "nao compila em nenhum runtime" in r.detalhe


def test_mensagem_com_tab_dentro_nao_perde_o_arquivo(docker):
    saidas, _ = docker
    saidas["php85"] = b"FALHA\tx.php\tmsg\tcom tab\n"
    assert arvore.roda_lint_arvore(["x.php"])[0].detalhe.endswith("msg\tcom tab")


def test_falha_de_docker_vira_um_erro_de_ambiente(monkeypatch):
    def explode(*a, **k):
        raise ErroAmbienteBanco("docker ausente")
    monkeypatch.setattr(arvore, "_docker", explode)
    monkeypatch.setattr(arvore, "containers_php", lambda: ("ref74", "php85"))
    casos = arvore.roda_lint_arvore(["x.php"])
    assert [(c.id, c.veredito) for c in casos] == [("passo:arvore", V.ERRO_AMBIENTE)]


def test_lista_vazia_nao_chama_o_docker(monkeypatch):
    monkeypatch.setattr(arvore, "containers_php", lambda: ("a", "b"))
    monkeypatch.setattr(arvore, "_docker", lambda *a, **k: pytest.fail("nao devia chamar"))
    assert arvore.roda_lint_arvore([]) == []