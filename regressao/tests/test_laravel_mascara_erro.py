"""Mascara de erro na COMPARACAO: file/line/trace e caminhos absolutos nao viram DIVERGE falso."""
from regressao.laravel.caso import CasoHttp, Resposta, _veredito
from regressao.laravel.mascara import MARCA, normaliza_erro
from regressao.nucleo.veredito import Veredito

ERRO_54 = {
    "message": "Call to undefined method Query\\Builder::all()",
    "exception": "BadMethodCallException",
    "file": "/var/www/html/vendor/laravel/framework/src/Illuminate/Database/Query/Builder.php",
    "line": 2445,
    "trace": [{"file": "/var/www/html/app/Http/Controllers/X.php", "line": 12, "function": "all"}],
}


def test_file_line_trace_de_erro_sao_mascarados_mas_exception_e_message_ficam():
    n = normaliza_erro(ERRO_54)
    assert n["file"] == MARCA and n["line"] == MARCA and n["trace"] == MARCA
    assert n["exception"] == "BadMethodCallException" and "undefined method" in n["message"]
    assert ERRO_54["line"] == 2445  # entrada intacta


def test_stacktrace_aninhado_e_alias_stack_trace():
    n = normaliza_erro({"data": {"error": {"message": "x", "stacktrace": ["a"], "stack_trace": "b", "file": "/a", "line": 1}}})
    e = n["data"]["error"]
    assert e["stacktrace"] == MARCA and e["stack_trace"] == MARCA and e["file"] == MARCA


def test_campo_de_negocio_line_ou_file_sem_cara_de_erro_nao_e_mascarado():
    assert normaliza_erro({"id": 1, "line": 3, "file": "a.txt"}) == {"id": 1, "line": 3, "file": "a.txt"}


def test_caminhos_absolutos_de_vendor_e_app_em_texto_sao_normalizados():
    a = normaliza_erro({"message": "Class X not found in /var/www/html/vendor/a/b.php:41 on line 41"})
    b = normaliza_erro({"message": "Class X not found in /srv/novo/vendor/a/b.php:99 on line 99"})
    assert a == b
    assert "<caminho>" in a["message"] and "/var/www" not in a["message"]
    assert normaliza_erro("em /var/www/html/app/Foo.php") == "em <caminho>"


def test_texto_que_nao_e_caminho_fica_intacto():
    assert normaliza_erro({"message": "Token invalido", "n": [1, "a/b"]}) == {"message": "Token invalido", "n": [1, "a/b"]}


def _caso():
    return CasoHttp(id="rota:GET:/x", metodo="GET", caminho="/x", corpo=None)


def _reg(json):
    return {"id": "rota:GET:/x", "status": 500, "cabecalhos": {}, "json": json, "texto": "", "tipos": {},
            "sql_negocio": [], "tabelas": {}}


def test_veredito_ignora_diferenca_so_de_file_line_trace():
    novo = dict(ERRO_54, file="/srv/l12/vendor/laravel/framework/Builder.php", line=77,
                trace=[{"file": "/srv/l12/app/Z.php", "line": 3, "function": "all"}])
    r = Resposta(500, {}, novo, [])
    c = _veredito(CasoHttp(id="rota:GET:/x", metodo="GET", caminho="/x", corpo=None, espera_status=500),
                  _reg(ERRO_54), r)
    assert c.veredito == Veredito.IDENTICO


def test_veredito_continua_divergindo_se_a_excecao_ou_a_mensagem_mudam():
    novo = dict(ERRO_54, exception="ErrorException", message="outra coisa")
    c = _veredito(_caso(), _reg(ERRO_54), Resposta(500, {}, novo, []))
    assert c.veredito == Veredito.DIVERGE and "json" in c.detalhe


def _reg200(json, **extra):
    return {"id": "rota:GET:/x", "status": 200, "cabecalhos": {}, "json": json, "texto": "", "tipos": {},
            "sql_negocio": [], "tabelas": {}, **extra}


def _div(base, novo, status=200, **kw):
    r = Resposta(status, kw.get("cab", {}), novo, kw.get("sql", []), texto=kw.get("texto", ""))
    return _veredito(_caso(), base, r).veredito


def test_negativo_objeto_de_negocio_com_message_file_line_nao_e_mascarado():
    assert normaliza_erro({"message": "ok", "file": "a.pdf", "line": 3}) == {"message": "ok", "file": "a.pdf", "line": 3}
    assert _div(_reg200({"message": "ok", "file": "a.pdf", "line": 3}),
                {"message": "ok", "file": "b.pdf", "line": 4}) == Veredito.DIVERGE


def test_negativo_url_de_storage_e_public_continua_diferindo():
    assert _div(_reg200({"url": "/storage/a.pdf"}), {"url": "/storage/b.pdf"}) == Veredito.DIVERGE
    assert _div(_reg200({"url": "/public/a.png"}), {"url": "/public/b.png"}) == Veredito.DIVERGE
    assert normaliza_erro({"message": "x", "exception": "E", "url": "http://h/storage/a.pdf"})["url"] == "http://h/storage/a.pdf"


def test_negativo_sql_cabecalhos_e_texto_de_sucesso_nao_sao_normalizados():
    sql_a = ["select * from /var/www/html/vendor/a.php"]
    base = _reg200({"ok": 1}, sql_negocio=sql_a)
    assert _div(base, {"ok": 1}, sql=["select * from /var/www/html/vendor/b.php"]) == Veredito.DIVERGE
    base = _reg200({"ok": 1}, cabecalhos={"content-type": "/var/www/html/app/a.php"})
    assert _div(base, {"ok": 1}, cab={"content-type": "/var/www/html/app/b.php"}) == Veredito.DIVERGE
    base = _reg200(None, texto="gerado em /var/www/html/storage/a.txt")
    assert _div(base, None, texto="gerado em /var/www/html/storage/b.txt") == Veredito.DIVERGE


def test_resposta_2xx_com_json_de_negocio_nao_tem_caminho_normalizado():
    assert _div(_reg200({"p": "/var/www/html/vendor/a.php"}), {"p": "/var/www/html/vendor/b.php"}) == Veredito.DIVERGE


def test_envelope_de_erro_do_app_error_true_com_file_line_e_mascarado_mesmo_em_406():
    env = {"error": True, "message": "O campo X e obrigatorio.", "file": "/var/www/html/app/Helpers/Functions.php",
           "line": 113, "code": 0}
    novo = dict(env, file="/srv/l12/app/Helpers/Functions.php", line=201)
    assert _div({**_reg200(env), "status": 406}, novo, status=406) == Veredito.IDENTICO


def test_caminho_so_com_raiz_conhecida_e_normalizado():
    assert normaliza_erro({"message": "m", "exception": "E", "x": "em /var/www/html/vendor/a.php:3"})["x"] == "em <caminho>"
    assert normaliza_erro({"message": "m", "exception": "E", "x": "em /outra/raiz/vendor/a.php"})["x"] == "em /outra/raiz/vendor/a.php"


def test_registro_bruto_nao_e_alterado_pela_comparacao():
    reg = _reg(ERRO_54)
    _veredito(_caso(), reg, Resposta(500, {}, ERRO_54, []))
    assert reg["json"]["line"] == 2445 and reg["json"]["file"].startswith("/var/www/html")
