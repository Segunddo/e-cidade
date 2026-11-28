"""regressao/rastro/raiz.py: a raiz do codigo e o que o contêiner MONTA, nao onde o pacote esta instalado."""
from pathlib import Path

from regressao.rastro import raiz


def test_raiz_vem_do_ponto_de_montagem_do_contêiner(monkeypatch, tmp_path):
    chamadas = []

    def falso(args, timeout, **kw):
        chamadas.append(args)
        return f"{tmp_path}\n".encode()
    monkeypatch.setattr(raiz, "_docker", falso)
    assert raiz.raiz_montada("c85") == tmp_path
    assert chamadas[0][0] == "inspect" and "c85" in chamadas[0]


def test_sem_docker_cai_na_arvore_do_pacote(monkeypatch):
    def quebra(args, timeout, **kw):
        raise RuntimeError("docker ausente")
    monkeypatch.setattr(raiz, "_docker", quebra)
    assert raiz.raiz_montada("c85") == raiz.T.DIR_TELAS


def test_montagem_que_nao_existe_no_host_cai_na_arvore_do_pacote(monkeypatch):
    monkeypatch.setattr(raiz, "_docker", lambda args, timeout, **kw: b"/caminho/que/nao/existe\n")
    assert raiz.raiz_montada("c85") == raiz.T.DIR_TELAS
    assert isinstance(raiz.raiz_montada("c85"), Path)
