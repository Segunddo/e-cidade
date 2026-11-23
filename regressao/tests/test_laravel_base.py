import copy
import http.server
import json
import threading
import time
from pathlib import Path

import pytest

from regressao.laravel import rotas, token
from regressao.laravel.mascara import mascara_json
from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.veredito import Veredito

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _sem_docker(monkeypatch):
    def sem_docker(*a, **k):
        raise ErroAmbienteBanco("docker indisponivel (teste)")
    monkeypatch.setattr(token, "_docker", sem_docker)


def test_mascara_troca_volateis_e_ordena_chaves():
    obj = {"z": 1, "a": {"criado_em": "2024-01-01", "b": 2, "id": 7}, "m": [3, 1]}
    r = mascara_json(obj, ["a.criado_em", "a.id", "nao.existe"])
    assert r == {"a": {"b": 2, "criado_em": "<X>", "id": "<X>"}, "m": [3, 1], "z": 1}
    assert list(r) == ["a", "m", "z"]
    assert list(r["a"]) == ["b", "criado_em", "id"]


def test_mascara_lista_com_asterisco():
    obj = {"itens": [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}], "total": 2}
    r = mascara_json(obj, ["itens.*.id"])
    assert r == {"itens": [{"id": "<X>", "n": "a"}, {"id": "<X>", "n": "b"}], "total": 2}
    assert mascara_json([{"t": 1}, {"t": 2}], ["*.t"]) == [{"t": "<X>"}, {"t": "<X>"}]


def test_mascara_nao_muta_a_entrada():
    obj = {"b": [{"id": 1}], "a": {"id": 2}}
    copia = copy.deepcopy(obj)
    mascara_json(obj, ["b.*.id", "a.id"])
    assert obj == copia
    assert list(obj) == ["b", "a"]


def test_inventario_silex_varre_providers(tmp_path):
    prov = tmp_path / "ecidade/api/V1/Providers/Controller"
    prov.mkdir(parents=True)
    (tmp_path / "ecidade/api/V1/APIServiceProvider.php").write_text(
        '$app->mount($prefix . "/tributario", new TributarioControllerProvider());', encoding="utf-8")
    (prov / "TributarioControllerProvider.php").write_text(
        "$controllers->post('recibo', \"recibo.controller:geraRecibo\");\n"
        "$controllers->get('/x/{id}', \"x:y\")->assert('id', '\\d+');", encoding="utf-8")
    lista = rotas.varre_silex(tmp_path)
    assert [(r.metodo, r.caminho, r.controller, r.origem) for r in lista] == [
        ("POST", "/api/v1/tributario/recibo", "recibo.controller:geraRecibo", "silex"),
        ("GET", "/api/v1/tributario/x/{id}", "x:y", "silex"),
    ]


def test_grava_tsv_deterministico_e_contagem(tmp_path):
    texto = (FIXTURES / "route_list_l8.json").read_text(encoding="utf-8")
    lista = rotas.parseia_route_list_json(texto)
    a, b = tmp_path / "a.tsv", tmp_path / "b.tsv"
    rotas.grava_tsv(lista, a)
    rotas.grava_tsv(list(reversed(lista)), b)
    assert a.read_bytes() == b.read_bytes()
    assert rotas.contagem(lista) == {"laravel": 7, "rest": 1, "silex": 0}


class _Servidor:
    def __init__(self, status, corpo, atraso=0):
        corpo_b = corpo.encode() if isinstance(corpo, str) else json.dumps(corpo).encode()
        self.pedidos = []
        pedidos = self.pedidos

        class H(http.server.BaseHTTPRequestHandler):
            def _r(self):
                n = int(self.headers.get("Content-Length") or 0)
                pedidos.append((self.command, self.path, self.rfile.read(n).decode()))
                if atraso:
                    time.sleep(atraso)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo_b)))
                self.end_headers()
                self.wfile.write(corpo_b)
            do_GET = do_POST = _r

            def log_message(self, *a):
                pass

        self.srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fecha(self):
        self.srv.shutdown()
        self.srv.server_close()


@pytest.fixture
def servidor_factory():
    abertos = []

    def f(status, corpo, atraso=0):
        s = _Servidor(status, corpo, atraso)
        abertos.append(s)
        return s
    yield f
    for s in abertos:
        s.fecha()


def test_laravel_que_nao_sobe_e_um_so_erro_ambiente(servidor_factory):
    s = servidor_factory(500, {"message": "boom"})
    r = token.laravel_sobe(s.url)
    assert r is not None and r.veredito == Veredito.ERRO_AMBIENTE
    assert r.area == "laravel"


def test_laravel_fora_do_ar_e_erro_ambiente():
    r = token.laravel_sobe("http://127.0.0.1:9")
    assert r is not None and r.veredito == Veredito.ERRO_AMBIENTE


def test_laravel_que_sobe_devolve_none(servidor_factory):
    s = servidor_factory(405, {"message": "Method Not Allowed"})
    assert token.laravel_sobe(s.url) is None


def test_obtem_token_devolve_access_token(servidor_factory, monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "SEGREDO-XYZ")
    s = servidor_factory(200, {"access_token": "tok123", "token_type": "Bearer"})
    assert token.obtem_token(s.url) == "tok123"
    metodo, caminho, corpo = s.pedidos[0]
    assert (metodo, caminho) == ("POST", "/v4/oauth/token")
    assert "grant_type=password" in corpo and "client_id=9999999" in corpo


def test_obtem_token_nao_vaza_o_segredo_na_excecao(servidor_factory, monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "SEGREDO-XYZ")
    s = servidor_factory(401, {"error": "invalid_client", "echo": "SEGREDO-XYZ"})
    with pytest.raises(token.ErroToken) as e:
        token.obtem_token(s.url, senha="SENHA-ABC")
    msg = str(e.value) + repr(e.value)
    assert "SEGREDO-XYZ" not in msg and "SENHA-ABC" not in msg
    assert "401" in msg

def test_5xx_anexa_cauda_do_log_redigida(servidor_factory, monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    bruto = ("PHP Fatal error: x\n"
             "client_secret=ABC123SECRET\n"
             "Authorization: Bearer eyJ0eXAi.eyJzdWIi.c2ln\n"
             "eco VALORREAL-9Z8Y7X e dbseller aqui\n" + "y" * 400 + "\n").encode()
    monkeypatch.setattr(token, "_docker", lambda *a, **k: bruto)
    s = servidor_factory(500, {"message": "boom"})
    monkeypatch.setenv("REGRESSAO_LARAVEL_NOVO_URL", s.url)  # o log lido e o do container do alvo
    r = token.laravel_sobe(s.url)
    assert r.veredito == Veredito.ERRO_AMBIENTE
    for proibido in ("ABC123SECRET", "eyJ0eXAi", "c2ln", "VALORREAL-9Z8Y7X"):
        assert proibido not in r.detalhe
    assert "<redigido>" in r.detalhe and "PHP Fatal error: x" in r.detalhe
    assert "podem ser antigas e nao relacionadas" in r.detalhe
    assert max(len(l) for l in r.detalhe.splitlines()) < 400
    assert len(r.detalhe.split("antigas e nao relacionadas):\n")[1].splitlines()) <= 5


def test_cauda_do_log_vazia_quando_docker_falha(servidor_factory, monkeypatch):
    s = servidor_factory(500, "x")
    monkeypatch.setenv("REGRESSAO_LARAVEL_NOVO_URL", s.url)
    r = token.laravel_sobe(s.url)
    assert r.veredito == Veredito.ERRO_AMBIENTE
    assert "php_errors.log" not in r.detalhe
    assert token._cauda_php_errors(s.url) == ""


@pytest.mark.parametrize("marca", ["Fatal error", "Parse error", "Uncaught",
                                   "Cannot make non abstract method"])
@pytest.mark.parametrize("status", [200, 404])
def test_corpo_com_erro_de_php_e_falha_de_boot(servidor_factory, marca, status):
    s = servidor_factory(status, f"<b>{marca}</b>: algo em x.php")
    r = token.laravel_sobe(s.url)
    assert r is not None and r.veredito == Veredito.ERRO_AMBIENTE and r.id == "laravel:boot"
    assert marca in r.detalhe


def test_pagina_404_saudavel_continua_no_ar(servidor_factory):
    assert token.laravel_sobe(servidor_factory(404, "<html>Not Found</html>").url) is None


def test_timeout_e_erro_ambiente(servidor_factory):
    s = servidor_factory(200, {"ok": 1}, atraso=1.5)
    r = token.laravel_sobe(s.url, timeout=0.2)
    assert r is not None and r.veredito == Veredito.ERRO_AMBIENTE
    assert "Timeout" in r.detalhe


def test_mascara_asterisco_sobre_dict_e_caminho_por_escalar_sao_ignorados():
    assert mascara_json({"a": {"x": 1}}, ["a.*"]) == {"a": {"x": 1}}
    assert mascara_json({"a": 5, "b": "s"}, ["a.b.c", "b.x"]) == {"a": 5, "b": "s"}


def test_mascara_caminho_desconhecido_nunca_levanta():
    for obj in (None, 3, "s", [], {}, [1, [2]], {"a": None}):
        mascara_json(obj, ["a.b", "*", "*.x", "a.*.b", ""])

def test_redige_estilo_print_r_seta(monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    for k in ("password", "secret", "token", "senha", "api_key", "passwd"):
        out = token.redige(f"[{k}] => valorzinho1\n{k} => valorzinho2")
        assert "valorzinho" not in out, k
        assert out.count("<redigido>") == 2


def test_redige_bearer_opaco(monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    for linha in ("Authorization: Bearer opaco-abc123", "authorization=Basic Zm9vOmJhcg=="):
        out = token.redige(linha)
        assert "opaco-abc123" not in out and "Zm9vOmJhcg" not in out and "Bearer opaco" not in out
        assert "<redigido>" in out


def test_redige_nao_apaga_caminho_com_dbseller(monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    linha = "PHP Fatal error in /var/www/html/cache/user/dbseller/libs/db_conecta.php on line 3"
    assert token.redige(linha) == linha
    out = token.redige('username: dbseller, login="dbseller"')
    assert "dbseller" not in out
    assert token.redige("x VALORREAL-9Z8Y7X y") == "x <redigido> y"


def test_redige_preserva_chaves_vizinhas_em_json_e_query(monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    assert token.redige('{"password":"abc","user":"x"}') == '{"password":"<redigido>","user":"x"}'
    assert token.redige("?password=abc&user=x") == "?password=<redigido>&user=x"

@pytest.mark.parametrize("linha", [
    "password" * 12500,
    "token" * 20000,
    "secret" * 16700,
    "Authorization: Bearer " + "a" * 100000,
], ids=["password", "token", "secret", "bearer"])
def test_redige_nao_tem_custo_quadratico(monkeypatch, linha):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    assert len(linha) >= 100000
    t0 = time.perf_counter()
    out = token.redige(linha)
    dt = time.perf_counter() - t0
    print(f"redige 100KB: {dt:.3f}s")
    assert isinstance(out, str)
    assert dt < 1.0


def test_redige_segredo_cortado_pelo_limite_nao_deixa_fragmento(monkeypatch):
    monkeypatch.setattr(token, "_segredo_cliente", lambda: "VALORREAL-9Z8Y7X")
    texto = "a" * (token.LIMITE_REDIGE - 5) + "VALORREAL-9Z8Y7X"
    out = token.redige(texto)
    assert "VALORREAL" not in out and "9Z8Y7X" not in out and "VALORRE" not in out
    assert len(out) <= token.LIMITE_REDIGE + 20