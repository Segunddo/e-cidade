"""regressao/rastro/executor.py e equivalencia.py (docker simulado)."""
import json

import pytest

from regressao.rastro import equivalencia, executor


class DockerFalso:
    def __init__(self, respostas=None):
        self.cmds: list[str] = []
        self.respostas = respostas or {}     # (tela, "inst"/"normal") -> corpo
        self.contagem: dict = {}

    def __call__(self, args, timeout, stdin=None, stdout=None):
        cmd = args[-1]
        self.cmds.append(cmd)
        if "curl" in cmd:
            inst = "localhost:8091" in cmd
            tela = cmd.split("/")[-1].split("'")[0].split(" ")[0]
            chave = (tela, "inst" if inst else "normal")
            n = self.contagem[chave] = self.contagem.get(chave, 0) + 1
            corpo = self.respostas.get(chave, b"ok")
            if callable(corpo):
                corpo = corpo(n)
            return corpo + b"\n@@200"
        if cmd.startswith("cat /tmp/rastro/"):
            return b'{"s":1,"k":"a"}\n{"s":2,"k":"c"}\n'
        if cmd.startswith("wc -l"):
            return b"10\n"
        if cmd.startswith("tail -n +11"):
            return (b"[2026-11-27 10:22:36] ERROR: E_ERROR - Uncaught exception 'TypeError' with message 'pg_num_rows(): "
                    b"Argument #1 must be of type PgSql\\Result, false given' in cad2_x.php on line 7 in cad2_x.php on line 7\n"
                    b"#1 src/V3/Error/Handler/Exception.php:19 - X\n")
        return b""


@pytest.fixture
def falso(monkeypatch):
    f = DockerFalso()
    monkeypatch.setattr(executor, "_docker", f)
    return f


def test_envia_cabecalho_e_le_o_rastro(falso):
    r = executor.roda_requisicao("sid1", "a.php", "meuid", "c85", instrumentado=True)
    curl = next(c for c in falso.cmds if "curl" in c)
    assert "X-Rastro-Id: meuid" in curl and "localhost:8091/a.php" in curl
    assert r.status == 200 and r.corpo == b"ok"
    ev = [json.loads(l) for l in r.rastro]
    assert [e["k"] for e in ev] == ["a", "c", "e"]                       # 2 do rt.php + 1 do log da aplicacao
    assert ev[2]["f"] == "cad2_x.php" and ev[2]["l"] == 7 and "pg_num_rows" in ev[2]["v"]["r"]


def test_requisicao_normal_nao_envia_cabecalho_nem_le_rastro(falso):
    r = executor.roda_requisicao("sid1", "a.php", "x", "c85", instrumentado=False)
    curl = next(c for c in falso.cmds if "curl" in c)
    assert "X-Rastro-Id" not in curl and "localhost:8091" not in curl and "localhost/a.php" in curl
    assert not any(c.startswith("cat /tmp/rastro/") for c in falso.cmds)
    assert [json.loads(l)["k"] for l in r.rastro] == ["e"]


def test_usa_backup_de_sessao_proprio(falso):
    executor.roda_requisicao("sid1", "a.php", "x", "c85")
    restauracao = [c for c in falso.cmds if "sess_sid1" in c]
    assert restauracao and all("_sess_rastro.bak" in c for c in restauracao)
    assert not any("/tmp/_sess.bak" in c for c in falso.cmds)            # o backup da bateria nunca e tocado


def test_corpo_normalizado_ignora_a_porta_do_vhost():
    a = b"<a href='http://localhost:8091/x'>"
    b = b"<a href='http://localhost/x'>"
    assert executor.corpo_normalizado(a) == executor.corpo_normalizado(b)


def test_equivalencia_aponta_a_tela_que_difere(monkeypatch):
    f = DockerFalso({("b.php", "inst"): b"DIFERENTE"})
    monkeypatch.setattr(executor, "_docker", f)
    r = equivalencia.confere_equivalencia("sid1", ["a.php", "b.php"], containers=("c74",))
    assert r.total == 2 and r.diferentes == [("b.php", "c74")] and r.instaveis == []


def test_resposta_normal_instavel_nao_conta_como_diferenca(monkeypatch):
    f = DockerFalso({("a.php", "normal"): lambda n: b"v%d" % n, ("a.php", "inst"): b"v0"})
    monkeypatch.setattr(executor, "_docker", f)
    r = equivalencia.confere_equivalencia("sid1", ["a.php"], containers=("c74",))
    assert r.diferentes == [] and r.instaveis == [("a.php", "c74")]


def test_tudo_igual_da_lista_vazia(monkeypatch):
    monkeypatch.setattr(executor, "_docker", DockerFalso())
    r = equivalencia.confere_equivalencia("sid1", ["a.php", "b.php"], containers=("c74", "c85"))
    assert r.diferentes == [] and r.instaveis == []
