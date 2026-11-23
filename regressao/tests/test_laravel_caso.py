import base64
import contextlib
import http.server
import json
import socket
import threading
from pathlib import Path

import pytest

from regressao.laravel import caso as mod
from regressao.laravel import token as token_mod
from regressao.laravel.caso import CasoHttp, carrega_casos, comparar, gravar
from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.veredito import Veredito

REAL_CASOS = Path(mod.__file__).resolve().parent / "casos"


def _jwt(jti: str) -> str:
    def b(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{b({'alg': 'RS256'})}.{b({'jti': jti})}.assinatura"


class Fake:
    """Servidor HTTP falso + estado compartilhado com o banco falso."""

    def __init__(self):
        self.v = 1
        self.pedidos: list[tuple[str, str, str | None]] = []
        self.log: list[str] = []
        self.n_token = 0
        self.statements = ["insert into foo(a,b) values (1, '2026-11-14 10:20:30.123')"]

    def linha(self, sql: str, pid: int = 9):
        self.log.append(f"2026-11-14 10:20:30.123 -03 [{pid}] LOG:  instrucao: {sql}")


@pytest.fixture
def fake(monkeypatch, tmp_path):
    f = Fake()

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _envia(self, status, corpo=b"", extra=None):
            self.send_response(status)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def _json(self, status, obj, extra=None):
            h = {"Content-Type": "application/json", "Set-Cookie": "sessao=segredo123",
                 "X-Debug": "interno"}
            h.update(extra or {})
            self._envia(status, json.dumps(obj).encode(), h)

        def _trata(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n:
                self.rfile.read(n)
            f.pedidos.append((self.command, self.path, self.headers.get("Authorization")))
            if self.path == "/v4/oauth/token":
                if self.command == "GET":
                    return self._json(405, {"error": "metodo"})
                f.n_token += 1
                return self._json(200, {"token_type": "Bearer", "expires_in": 1000 + f.n_token,
                                        "access_token": _jwt(f"jti{f.n_token}"),
                                        "refresh_token": "r" * 20})
            if self.path == "/protegido":
                if self.headers.get("Authorization") != "Bearer VALIDO":
                    return self._json(401, {"message": "Unauthenticated."})
                return self._json(200, {"v": f.v})
            if self.path == "/vazio":
                return self._envia(200)
            if self.path == "/quebra":
                return self._json(500, {"message": "Server Error"})
            if self.path == "/escreve":
                f.linha("set client_encoding to 'LATIN1'")   # assinatura de sessao da aplicacao
                f.linha("SET statement_timeout = 0", pid=5)       # sessao do pg_dump (cliente nao-app)
                f.linha("insert into foo(z) values (99)", pid=5)
                for s in f.statements:
                    f.linha(s)
                f.linha("insert into db_acount(x) values (1)")
                f.linha("select * from foo")
                return self._json(200, {"ok": True})
            if self.path == "/muda":  # escrita invisivel ao log: so o fingerprint percebe
                f.fp["s.t"] = f.fp.get("s.t", 0) + 1
                f.fp["public.oauth_clients"] = f.fp.get("public.oauth_clients", 0) + 1  # infra
                return self._json(200, {"ok": True})
            return self._json(404, {"message": "nao existe"})

        do_GET = do_POST = do_PUT = do_DELETE = _trata

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    f.url = f"http://127.0.0.1:{srv.server_address[1]}"
    f.chamadas = []
    f.psql = []
    f.hashes = {}
    f.fp = {}
    monkeypatch.setattr(mod, "_fingerprint", lambda: dict(f.fp))
    monkeypatch.setattr(mod, "ESPERA_ESTATISTICAS", 0)

    sha = tmp_path / "dump.sha256"
    sha.write_text("abc123\n")
    monkeypatch.setattr(mod, "ARQ_SHA256", sha)
    monkeypatch.setattr(mod, "restaura_dump", lambda d: f.chamadas.append("restaura"))
    monkeypatch.setattr(mod, "confere_baseline", lambda d: None)
    monkeypatch.setattr(mod, "hash_tabelas",
                        lambda ts: {t: f.hashes.get(t, "h0") for t in ts})
    monkeypatch.setattr(mod, "com_log_statement", contextlib.nullcontext)

    def psql(sql, db="ecidade"):
        f.psql.append(sql)
        if "REGRESSAO_" in sql:
            f.linha(sql, pid=7)  # sessao do marcador (psql), diferente da da aplicacao
        return ""
    monkeypatch.setattr(mod, "_psql", psql)
    monkeypatch.setattr(mod, "_logs_banco", lambda desde: "\n".join(f.log).encode())
    monkeypatch.setattr(mod, "obtem_token", lambda base_url, *a, **k: "VALIDO")
    monkeypatch.setattr(mod, "_segredo_cliente", lambda: "segredo-de-teste")
    monkeypatch.setattr(token_mod, "_docker", lambda *a, **k: (_ for _ in ()).throw(
        ErroAmbienteBanco("sem docker (teste)")))
    f.baseline = tmp_path / "baseline"
    yield f
    srv.shutdown()


def _caso(id, caminho="/protegido", metodo="GET", **kw):
    kw.setdefault("corpo", None)
    return CasoHttp(id=id, metodo=metodo, caminho=caminho, **kw)


def test_gravar_e_comparar_mesma_resposta_e_identico(fake):
    casos = [_caso("protegido"),
             _caso("escreve", "/escreve", "POST", corpo={"a": 1}, tabelas=["foo"],
                   espera_escrita=True)]
    gravar(casos, fake.url, fake.baseline)
    res = comparar(casos, fake.url, fake.baseline)
    assert [(c.id, c.veredito) for c in res] == [("protegido", Veredito.IDENTICO),
                                                 ("escreve", Veredito.IDENTICO)]
    assert fake.chamadas == ["restaura", "restaura"]
    reg = json.loads((fake.baseline / "escreve.json").read_text(encoding="utf-8"))
    assert reg["sql_negocio"] == ["insert into foo(a,b) values (1, '<TS>')"]
    assert reg["tabelas"] == {"foo": "h0"}
    meta = json.loads((fake.baseline / "_meta.json").read_text(encoding="utf-8"))
    assert meta["dump_sha256"] == "abc123" and meta["n_casos"] == 2


def test_comparar_json_diferente_diverge_com_diff(fake):
    casos = [_caso("protegido")]
    gravar(casos, fake.url, fake.baseline)
    fake.v = 2
    res = comparar(casos, fake.url, fake.baseline)
    assert res[0].veredito == Veredito.DIVERGE
    assert '-    "v": 1' in res[0].diff and '+    "v": 2' in res[0].diff


def test_comparar_sql_ou_hash_diferente_diverge(fake):
    casos = [_caso("escreve", "/escreve", "POST", corpo={}, tabelas=["foo"])]
    gravar(casos, fake.url, fake.baseline)
    fake.hashes["foo"] = "h1"
    res = comparar(casos, fake.url, fake.baseline)
    assert res[0].veredito == Veredito.DIVERGE and "h1" in res[0].diff
    fake.hashes.clear()
    fake.statements = ["insert into foo(a,b) values (2, 'x')"]
    res = comparar(casos, fake.url, fake.baseline)
    assert res[0].veredito == Veredito.DIVERGE and "values (2" in res[0].diff


def test_sem_token_e_401_gravado_e_comparado(fake):
    casos = [_caso("sem-token", token="")]
    gravar(casos, fake.url, fake.baseline)
    reg = json.loads((fake.baseline / "sem-token.json").read_text(encoding="utf-8"))
    assert reg["status"] == 401
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.IDENTICO
    assert all(p[2] is None for p in fake.pedidos if p[1] == "/protegido")


def test_token_invalido_e_401(fake):
    casos = [_caso("invalido", token="lixo")]
    gravar(casos, fake.url, fake.baseline)
    reg = json.loads((fake.baseline / "invalido.json").read_text(encoding="utf-8"))
    assert reg["status"] == 401
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.IDENTICO
    assert ("GET", "/protegido", "Bearer lixo") in fake.pedidos


def test_baseline_ausente_e_erro_ambiente(fake):
    res = comparar([_caso("x")], fake.url, fake.baseline)
    assert [c.veredito for c in res] == [Veredito.ERRO_AMBIENTE]
    assert res[0].id == "x" and "baseline" in res[0].detalhe.lower()
    assert fake.chamadas == []
    # caso carregado sem registro no _meta (fix round 1: integridade da baseline recusa tudo)
    gravar([_caso("a")], fake.url, fake.baseline)
    res = comparar([_caso("a"), _caso("b")], fake.url, fake.baseline)
    assert [(c.id, c.veredito) for c in res] == [("laravel:baseline", Veredito.ERRO_AMBIENTE)]
    assert "'b'" in res[0].detalhe
    assert fake.chamadas == ["restaura"]  # so o do gravar
    # arquivo do caso ausente com o _meta listando o id: registro por caso
    meta = json.loads((fake.baseline / "_meta.json").read_text())
    meta["ids"] = ["a", "b"]
    (fake.baseline / "_meta.json").write_text(json.dumps(meta))
    res = comparar([_caso("a"), _caso("b")], fake.url, fake.baseline)
    assert [(c.id, c.veredito) for c in res] == [("b", Veredito.ERRO_AMBIENTE)]


def test_resposta_vazia_nos_dois_lados_e_inconclusiva(fake):
    casos = [_caso("vazio", "/vazio")]
    gravar(casos, fake.url, fake.baseline)
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.INCONCLUSIVO


def test_5xx_nos_dois_lados_e_escrita_esperada_sem_escrita_sao_inconclusivos(fake):
    casos = [_caso("quebra", "/quebra"),
             _caso("nada", "/protegido", "GET", espera_escrita=True)]
    gravar(casos, fake.url, fake.baseline)
    res = comparar(casos, fake.url, fake.baseline)
    assert [c.veredito for c in res] == [Veredito.INCONCLUSIVO, Veredito.INCONCLUSIVO]


def test_comparar_recusa_baseline_de_outro_dump(fake):
    casos = [_caso("protegido")]
    gravar(casos, fake.url, fake.baseline)
    (fake.baseline / "_meta.json").write_text(
        json.dumps({"dump_sha256": "outro", "n_casos": 1}), encoding="utf-8")
    fake.chamadas.clear()
    n = len(fake.pedidos)
    res = comparar(casos, fake.url, fake.baseline)
    assert len(res) == 1 and res[0].veredito == Veredito.ERRO_AMBIENTE
    assert "dump" in res[0].detalhe.lower()
    assert fake.chamadas == []
    assert not [p for p in fake.pedidos[n:] if p[1] == "/protegido"]


def test_laravel_fora_do_ar_nao_restaura_banco(fake):
    gravar([_caso("protegido")], fake.url, fake.baseline)
    fake.chamadas.clear()
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    morta = f"http://127.0.0.1:{s.getsockname()[1]}"
    s.close()
    res = comparar([_caso("protegido")], morta, fake.baseline)
    assert len(res) == 1 and res[0].veredito == Veredito.ERRO_AMBIENTE
    assert res[0].id == "laravel:boot"
    assert fake.chamadas == []


def test_token_nunca_e_gravado_na_baseline(fake):
    casos = [_caso("token-valido", "/v4/oauth/token", "POST", autenticado=False, form=True,
                   corpo={"grant_type": "password", "client_secret": "${CLIENT_SECRET}"},
                   campos_volateis=["access_token", "refresh_token", "expires_in"]),
             _caso("protegido")]
    gravar(casos, fake.url, fake.baseline)
    texto = "".join(p.read_text(encoding="utf-8") for p in fake.baseline.glob("*.json"))
    assert "eyJ" not in texto and "jti1" not in texto and "VALIDO" not in texto
    assert "segredo-de-teste" not in texto and "rrrrrrrr" not in texto
    reg = json.loads((fake.baseline / "token-valido.json").read_text(encoding="utf-8"))
    assert reg["json"]["access_token"] == "<X>" and reg["json"]["token_type"] == "Bearer"
    assert reg["tipos"]["access_token"] == ["str"] and reg["tipos"]["expires_in"] == ["int"]
    # outro token / outro expires_in na comparacao: ainda IDENTICO
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.IDENTICO


def test_estrutura_do_token_diferente_diverge(fake):
    casos = [_caso("tok", "/v4/oauth/token", "POST", autenticado=False, form=True,
                   campos_volateis=["access_token", "expires_in"])]
    gravar(casos, fake.url, fake.baseline)
    reg = json.loads((fake.baseline / "tok.json").read_text(encoding="utf-8"))
    reg["tipos"]["expires_in"] = ["str"]
    reg.pop("sha256")
    mod._grava_registro(fake.baseline / "tok.json", reg)
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.DIVERGE


def test_baseline_adulterada_e_erro_ambiente(fake):
    gravar([_caso("protegido")], fake.url, fake.baseline)
    p = fake.baseline / "protegido.json"
    p.write_text(p.read_text(encoding="utf-8").replace('"v": 1', '"v": 9'), encoding="utf-8")
    assert comparar([_caso("protegido")], fake.url, fake.baseline)[0].veredito == Veredito.ERRO_AMBIENTE


def test_cabecalhos_fora_da_lista_nao_sao_gravados(fake):
    gravar([_caso("protegido")], fake.url, fake.baseline)
    reg = json.loads((fake.baseline / "protegido.json").read_text(encoding="utf-8"))
    assert set(reg["cabecalhos"]) <= {"content-type", "www-authenticate", "cache-control"}
    assert "content-type" in reg["cabecalhos"]
    assert "segredo123" not in json.dumps(reg)


def test_token_expirado_forcado_por_sql_no_caso(fake):
    caso = _caso("expirado", token="@novo",
                 sql_antes=["update oauth_access_tokens set expires_at = now() where id = '{jti}'"])
    gravar([caso], fake.url, fake.baseline)
    assert any("where id = 'jti1'" in s for s in fake.psql)
    assert any(p[2] and p[2].startswith("Bearer eyJ") for p in fake.pedidos if p[1] == "/protegido")


def test_ordem_dos_casos_e_fixa(fake, tmp_path):
    d = tmp_path / "casos"
    d.mkdir()
    (d / "b.yml").write_text(
        "- id: b1\n  metodo: GET\n  caminho: /protegido\n- id: b2\n  metodo: GET\n  caminho: /vazio\n",
        encoding="utf-8")
    (d / "a.yml").write_text(
        "- id: a1\n  metodo: GET\n  caminho: /quebra\n- id: a2\n  metodo: get\n  caminho: /protegido\n"
        "  token: ''\n", encoding="utf-8")
    casos = carrega_casos(d)
    assert [c.id for c in casos] == ["a1", "a2", "b1", "b2"]
    assert casos[1].metodo == "GET" and casos[1].token == ""
    gravar(casos, fake.url, fake.baseline)
    ordem_gravar = [p[1] for p in fake.pedidos if p[1] != "/v4/oauth/token"]
    fake.pedidos.clear()
    comparar(casos, fake.url, fake.baseline)
    ordem_comparar = [p[1] for p in fake.pedidos if p[1] != "/v4/oauth/token"]
    assert ordem_gravar == ordem_comparar == ["/quebra", "/protegido", "/protegido", "/vazio"]


def test_carrega_auth_yml_real_tem_os_casos_exigidos():
    casos = {c.id: c for c in carrega_casos(REAL_CASOS)}
    for obrigatorio in ("auth-token-valido", "auth-client-secret-errado", "auth-senha-errada",
                        "auth-usuario-inexistente", "auth-sem-grant-type", "auth-sem-token",
                        "auth-token-invalido", "auth-token-expirado", "auth-refresh-token"):
        assert obrigatorio in casos, obrigatorio
    assert casos["auth-token-valido"].campos_volateis == ["access_token", "refresh_token", "expires_in"]
    assert casos["auth-sem-token"].token == ""


# ------------------------------------------------------------ Task 11a: M1, ids de rota, janela de SQL

def test_diff_passa_por_redige_e_nao_vaza_segredo_fora_de_jwt():
    base = {"status": 200, "json": {"senha": "hunter2-segredo", "x": 1}}
    novo = {"status": 200, "json": {"senha": "outra-senha-xyz", "x": 1}}
    d = mod._diff(base, novo)
    assert "hunter2-segredo" not in d and "outra-senha-xyz" not in d
    assert "<redigido>" in d


def test_id_de_rota_com_dois_pontos_e_barras_grava_arquivo_seguro(fake, tmp_path):
    d = tmp_path / "casos"
    d.mkdir()
    (d / "r.yml").write_text(
        "- id: 'rota:GET:/protegido'\n  metodo: GET\n  caminho: /protegido\n", encoding="utf-8")
    casos = carrega_casos(d)
    assert casos[0].id == "rota:GET:/protegido"
    gravar(casos, fake.url, fake.baseline)
    assert (fake.baseline / mod.nome_arquivo("rota:GET:/protegido")).is_file()
    assert sorted(p.name for p in fake.baseline.iterdir()) == ["_meta.json", "rota=GET=~protegido.json"]
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.IDENTICO


def test_carrega_ignora_arquivos_com_underscore(tmp_path):
    (tmp_path / "a.yml").write_text("- id: a\n  metodo: GET\n  caminho: /x\n", encoding="utf-8")
    (tmp_path / "_instaveis.yml").write_text("- id: b\n  metodo: GET\n  caminho: /y\n", encoding="utf-8")
    assert [c.id for c in carrega_casos(tmp_path)] == ["a"]


def test_id_invalido_continua_rejeitado(tmp_path):
    (tmp_path / "a.yml").write_text("- id: 'a b'\n  metodo: GET\n  caminho: /x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        carrega_casos(tmp_path)


def test_sql_de_negocio_ignora_outras_sessoes_e_a_do_marcador(fake):
    casos = [_caso("escreve", "/escreve", "POST", corpo={}, espera_escrita=True)]
    gravar(casos, fake.url, fake.baseline)
    reg = json.loads((fake.baseline / "escreve.json").read_text(encoding="utf-8"))
    # `insert into foo(z)` veio do pid 5 (sem assinatura de sessao da app): nao entra
    assert reg["sql_negocio"] == ["insert into foo(a,b) values (1, '<TS>')"]


def test_statements_com_pid_devolve_pid_por_statement():
    bruto = (b"2026-11-14 10:20:30.123 -03 [11] LOG:  instrucao: set names 'latin1'\n"
             b"2026-11-14 10:20:30.124 -03 [12] LOG:  executar pdo_stmt_00000002: insert into t values ($1)\n"
             b"2026-11-14 10:20:30.124 -03 [12] DETAIL:  parameters: $1 = '1'\n")
    assert mod._statements_pid(bruto) == [(11, "set names 'latin1'"),
                                          (12, "insert into t values ($1) parameters: $1 = '1'")]
    assert mod._statements(bruto) == [s for _, s in mod._statements_pid(bruto)]


def test_parametros_do_statement_em_portugues_sao_anexados():
    # o log real do postgres do e-cidade e em portugues: DETALHE / par\xe2metros
    bruto = ("2026-11-14 21:31:58.776 -03 [21569] LOG:  executar pdo_stmt_00000004: "
             "insert into \"t\" (\"a\") values ($1)\n"
             "2026-11-14 21:31:58.776 -03 [21569] DETALHE:  par\xe2metros: $1 = 'x'\n").encode("latin1")
    (pid, stm), = mod._statements_pid(bruto)
    assert pid == 21569 and stm == "insert into \"t\" (\"a\") values ($1) parameters: $1 = 'x'"


# ------------------------------------------------------------ token expirado (exp no JWT)

def _jwt_valido():
    return _jwt("jtiX")


def test_jwt_expirado_tem_exp_no_passado_e_assinatura_valida(tmp_path):
    import shutil
    import subprocess
    if shutil.which("openssl") is None:
        pytest.skip("openssl ausente")
    priv, pub = tmp_path / "priv.key", tmp_path / "pub.key"
    subprocess.run(["openssl", "genrsa", "-out", str(priv), "2048"], check=True, capture_output=True)
    subprocess.run(["openssl", "rsa", "-in", str(priv), "-pubout", "-out", str(pub)],
                   check=True, capture_output=True)
    novo = mod._jwt_expirado(_jwt_valido(), priv)
    cab, pl, sig = novo.split(".")
    dados = json.loads(base64.urlsafe_b64decode(pl + "=" * (-len(pl) % 4)))
    import time
    assert dados["exp"] < time.time() and dados["jti"] == "jtiX"
    arq_sig = tmp_path / "sig"
    arq_sig.write_bytes(base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4)))
    r = subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(pub), "-signature", str(arq_sig)],
                       input=f"{cab}.{pl}".encode(), capture_output=True)
    assert r.returncode == 0, r.stdout


def test_jwt_expirado_sem_chave_e_erro_de_requisicao(tmp_path):
    with pytest.raises(mod.ErroRequisicao):
        mod._jwt_expirado(_jwt_valido(), tmp_path / "nao-existe.key")


def test_caso_token_expirado_usa_o_jwt_forjado(fake, monkeypatch):
    monkeypatch.setattr(mod, "_jwt_expirado", lambda jwt, chave=None: "EXPIRADO")
    casos = [_caso("exp", token="@expirado")]
    gravar(casos, fake.url, fake.baseline)
    assert ("GET", "/protegido", "Bearer EXPIRADO") in fake.pedidos
    reg = json.loads((fake.baseline / "exp.json").read_text(encoding="utf-8"))
    assert reg["status"] == 401


def test_auth_yml_real_as_quatro_rotas_apontam_para_a_mesma_rota_de_controle():
    casos = {c.id: c for c in carrega_casos(REAL_CASOS)}
    ids = ("auth-sem-token", "auth-token-invalido", "auth-token-expirado",
           "auth-rota-protegida-com-token")
    assert len({casos[i].caminho for i in ids}) == 1
    assert casos[ids[0]].caminho != "/v4/api/configuracao/bancos"
    assert casos["auth-token-expirado"].token == "@expirado"
    assert casos["auth-token-revogado"].token == "@novo"
    assert casos["auth-token-expirado-so-no-banco"].token == "@novo"


def test_escrita_yml_real_declara_tabela_e_espera_escrita():
    casos = {c.id: c for c in carrega_casos(REAL_CASOS)}
    w = casos["escrita-jetom-funcao-incluir"]
    assert w.metodo == "POST" and w.espera_escrita and w.tabelas == ["pessoal.jetomfuncao"]
    assert w.corpo and w.corpo["descricao"]
