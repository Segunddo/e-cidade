"""Robustez de sessao em rodadas longas: renovar a sessao autenticada, cp /tmp/_sess.bak, timeout com 1 retentativa."""
import base64
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.veredito import Veredito
from regressao.php import telas


# ---------------------------------------------------------------- login por HTTP

class FakeHttp:
    """requests.Session falso: guarda as chamadas e devolve paginas por caminho."""

    def __init__(self, paginas=None, sid="NOVASID123"):
        self.chamadas, self.cookies, self._sid = [], {}, sid
        self.paginas = paginas or {}

    def _resp(self, url, **k):
        self.chamadas.append((k.get("_m", "GET"), url, k.get("params"), k.get("data")))
        if "login.php" in url:
            self.cookies["ECIDADEWINDOWMAIN"] = self._sid
        corpo = next((v for ch, v in self.paginas.items() if ch in url), b"")
        return SimpleNamespace(content=corpo, text=corpo.decode("latin-1"), status_code=200)

    def get(self, url, **k):
        return self._resp(url, **k)

    def post(self, url, **k):
        return self._resp(url, _m="POST", **k)


# ordem real dos atributos no HTML do e-cidade: href antes de title
MODULOS = (b'<a href="modulos.php?QUdVQQ==" title="Agua"  onmouseover="x">'
           b'<a href="modulos.php?YW5vdXN1PTIwMjYmbW9kdWxvPTI4OTU3OSZub21lbW9kPUNlbWl06XJpbw==" title="Cemit\xe9rio"  onmouseover="x">')


def test_login_http_segue_a_sequencia_do_navegador_e_devolve_o_sid_sem_vazar_a_senha():
    http = FakeHttp({"corpo.php": MODULOS})
    sid = telas.login_http("http://localhost:8080", http=http)
    assert sid == "NOVASID123"
    metodos_urls = [(m, u.replace("http://localhost:8080", "")) for m, u, _p, _d in http.chamadas]
    caminhos = [u.split("?")[0] for _m, u in metodos_urls]
    assert caminhos[:3] == ["/login.php", "/abrir.php", "/inicio.php"]
    assert ("POST", "/con4_atualizacadastro001.php") in metodos_urls          # Cancelar da tela "atualizar cadastro"
    assert any(u.startswith("/corpo.php?" + base64.b64encode(b"instit=1").decode()) for _m, u in metodos_urls)
    assert metodos_urls[-1][1].startswith("/modulos.php?YW5vdXN1")           # entra no modulo Cemiterio (DB_modulo)
    abrir = next(p for m, u, p, d in http.chamadas if "abrir.php" in u)
    auth = base64.b64decode(abrir["sAuth"]).decode()
    assert auth.startswith("DB_login=dbseller&DB_senha=") and "DB_senha=dbseller" not in auth  # so md5


def test_login_http_sem_cookie_de_sessao_e_sessao_perdida():
    class SemCookie(FakeHttp):
        def _resp(self, url, **k):
            r = super()._resp(url, **k)
            self.cookies.clear()
            return r
    with pytest.raises(telas.SessaoPerdida):
        telas.login_http("http://h", http=SemCookie({"corpo.php": MODULOS}))


# ---------------------------------------------------------------- renovar

def test_renova_sessao_devolve_o_sid_novo_validado_e_atualiza_o_backup():
    docker = []
    with patch.object(telas, "_docker", side_effect=lambda a, t, **k: docker.append(a) or b""):
        novo = telas.renova_sessao("velha", login=lambda: "nova", valida=lambda s: s == "nova", espera=lambda s: None)
    assert novo == "nova"
    cp = " ".join(docker[-1])
    assert "/var/lib/php/sessions/sess_nova" in cp and "/tmp/_sess.bak" in cp


def test_renova_sessao_tenta_ate_o_limite_e_desiste_com_none():
    chamadas = []

    def login():
        chamadas.append(1)
        raise telas.SessaoPerdida("sem cookie")
    assert telas.renova_sessao("v", max_tentativas=3, login=login, valida=lambda s: True, espera=lambda s: None) is None
    assert len(chamadas) == 3


def test_renova_sessao_sid_que_nao_autentica_conta_como_tentativa_falha():
    sids = iter(["a", "b", "c"])
    vistos = []
    with patch.object(telas, "_docker", return_value=b""):
        novo = telas.renova_sessao("v", max_tentativas=3, login=lambda: next(sids),
                                   valida=lambda s: vistos.append(s) or s == "c", espera=lambda s: None)
    assert vistos == ["a", "b", "c"] and novo == "c"


def test_sessao_renova_respeita_o_limite_e_registra_o_motivo():
    s = telas.Sessao("s0", max_renovacoes=2, renova=lambda sid: sid + "x")
    assert s.renova("expirou 1") and s.sid == "s0x"
    assert s.renova("expirou 2") and s.sid == "s0xx"
    assert s.renova("expirou 3") is False and s.sid == "s0xx"
    assert [r["ok"] for r in s.renovacoes] == [True, True]


def test_sessao_renova_que_falha_mantem_o_sid_e_registra():
    s = telas.Sessao("s0", renova=lambda sid: None)
    assert s.renova("x") is False and s.sid == "s0" and s.renovacoes == [{"motivo": "x", "ok": False}]


# ---------------------------------------------------------------- restaura_sessao / cp /tmp/_sess.bak

def test_restaura_sessao_sem_o_arquivo_de_sessao_vira_sessao_perdida_nao_erro_generico():
    with patch.object(telas, "_docker", side_effect=ErroAmbienteBanco("codigo de saida 3: docker exec ...")):
        with pytest.raises(telas.SessaoPerdida):
            telas.restaura_sessao("sumiu")


def test_restaura_sessao_outro_erro_de_docker_continua_sendo_erro_de_ambiente():
    with patch.object(telas, "_docker", side_effect=ErroAmbienteBanco("timeout de 90s")):
        with pytest.raises(ErroAmbienteBanco) as e:
            telas.restaura_sessao("x")
    assert not isinstance(e.value, telas.SessaoPerdida)


def test_restaura_sessao_comando_recria_o_backup_ausente_a_partir_da_sessao_viva():
    docker = []
    with patch.object(telas, "_docker", side_effect=lambda a, t, **k: docker.append(a) or b""):
        telas.restaura_sessao("abc")
    sh = docker[0][-1]
    assert "exit 3" in sh and "[ -s /tmp/_sess.bak ] ||" in sh and "cp /var/lib/php/sessions/sess_abc /tmp/_sess.bak" in sh


# ---------------------------------------------------------------- DIVERGE de PDF so por compressao/metadados

PDF_A = b"%PDF-1.3\n1 0 obj<<>>stream\nAAAA\nendstream"
PDF_B = b"%PDF-1.3\n1 0 obj<<>>stream\nBBBBB\nendstream"


def _req_pdfs(corpos):
    it = iter(corpos)
    return lambda sid, tela, container="ecidade_php56": (200, next(it))


def test_reavalia_pdf_texto_igual_com_bytes_diferentes_nao_e_divergencia():
    with patch.object(telas, "restaura_sessao"), patch.object(telas, "_requisita_status", _req_pdfs([PDF_A, PDF_B])), \
         patch("regressao.php.relatorios.extrai_conteudo", return_value="=== pagina 1 === Titulo"):
        assert telas._reavalia_pdf_impl("s", "r.php") is True


def test_reavalia_pdf_texto_diferente_continua_divergindo():
    textos = iter(["=== pagina 1 === 10", "=== pagina 1 === 11"])
    with patch.object(telas, "restaura_sessao"), patch.object(telas, "_requisita_status", _req_pdfs([PDF_A, PDF_B])), \
         patch("regressao.php.relatorios.extrai_conteudo", side_effect=lambda c, t: next(textos)):
        assert telas._reavalia_pdf_impl("s", "r.php") is False


@pytest.mark.parametrize("par", [[(500, b"x"), (200, PDF_A)], [(200, b"<html>"), (200, b"<html>")]])
def test_reavalia_pdf_so_vale_para_pdf_200_nos_dois_lados(par):
    it = iter(par)
    with patch.object(telas, "restaura_sessao"), patch.object(telas, "_requisita_status", lambda *a, **k: next(it)):
        assert telas._reavalia_pdf_impl("s", "r.php") is False


def test_roda_telas_rebaixa_diverge_200x200_de_pdf_quando_o_texto_e_igual():
    saida = "2 telas\n\n  DIVERGE a.php ref=200/636B  85=200/609B\n  DIVERGE b.php ref=200/10B  85=200/11B\n\n=== 0/2 identicas, 2 divergentes, 0 timeout ===\n"
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "sessao_autenticada", return_value=True), \
         patch.object(telas, "_roda_cmp", return_value=saida), \
         patch.object(telas, "_reavalia_pdf", side_effect=lambda sid, t: t == "a.php"):
        casos, _ = telas.roda_telas("s", "^", "x")
    v = {c.id: c for c in casos}
    assert v["a.php"].veredito == Veredito.IDENTICO and "texto do PDF" in v["a.php"].detalhe
    assert v["b.php"].veredito == Veredito.DIVERGE            # nao e PDF idem: continua divergindo


def test_roda_telas_nao_reavalia_diverge_de_status_http():
    saida = "1 telas\n\n  DIVERGE a.php ref=200/636B  85=500/3721B\n\n=== 0/1 identicas, 1 divergentes, 0 timeout ===\n"
    chamadas = []
    with patch.object(telas, "lista_telas", return_value=["a.php"]), \
         patch.object(telas, "sessao_autenticada", return_value=True), \
         patch.object(telas, "_roda_cmp", return_value=saida), \
         patch.object(telas, "_reavalia_pdf", side_effect=lambda s, t: chamadas.append(t) or True):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert chamadas == [] and casos[0].veredito == Veredito.DIVERGE   # 200 x 500 e achado real


# ---------------------------------------------------------------- roda_telas: sessao perdida e timeout

def test_roda_telas_sessao_perdida_ao_buscar_corpo_vira_erro_de_sessao_para_a_bateria_renovar():
    saida = "2 telas\n\n=== 2/2 identicas, 0 divergentes, 0 timeout ===\n"
    with patch.object(telas, "lista_telas", return_value=["a.php", "b.php"]), \
         patch.object(telas, "sessao_autenticada", return_value=True), \
         patch.object(telas, "_roda_cmp", return_value=saida), \
         patch.object(telas, "busca_corpo", side_effect=telas.SessaoPerdida("sumiu")):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert [c.veredito for c in casos] == [Veredito.ERRO_AMBIENTE] and casos[0].detalhe.startswith("sessao")


def test_timeout_de_tela_ganha_uma_retentativa_e_o_resultado_substitui_o_timeout():
    s1 = "3 telas\n\n  TIMEOUT b.php ref=000  85=500\n\n=== 2/3 identicas, 0 divergentes, 1 timeout ===\n"
    s2 = "1 telas\n\n=== 1/1 identicas, 0 divergentes, 0 timeout ===\n"
    chamadas = []

    def cmp(sid, prefixo):
        chamadas.append(prefixo)
        return s1 if len(chamadas) == 1 else s2
    lista = {"^": ["a.php", "b.php", "c.php"]}
    with patch.object(telas, "lista_telas", side_effect=lambda p: lista["^"] if p == "^" else ["b.php"]), \
         patch.object(telas, "sessao_autenticada", return_value=True), \
         patch.object(telas, "_roda_cmp", side_effect=cmp), \
         patch.object(telas, "busca_corpo", return_value=b"<td>x</td>"):
        casos, corpos = telas.roda_telas("s", "^", "x")
    assert len(chamadas) == 2 and chamadas[1] == "^(?:b\\.php)$"
    assert {c.id: c.veredito for c in casos} == {"a.php": Veredito.IDENTICO, "b.php": Veredito.IDENTICO,
                                                 "c.php": Veredito.IDENTICO}
    assert set(corpos) == {"a.php", "b.php", "c.php"}


def test_timeout_que_persiste_apos_a_retentativa_continua_erro_de_ambiente_e_nao_retenta_de_novo():
    s = "1 telas\n\n  TIMEOUT b.php ref=000  85=500\n\n=== 0/1 identicas, 0 divergentes, 1 timeout ===\n"
    chamadas = []
    with patch.object(telas, "lista_telas", return_value=["b.php"]), \
         patch.object(telas, "sessao_autenticada", return_value=True), \
         patch.object(telas, "_roda_cmp", side_effect=lambda sid, p: chamadas.append(p) or s):
        casos, _ = telas.roda_telas("s", "^", "x")
    assert len(chamadas) == 2                                            # 1 original + 1 retentativa, nunca mais
    assert casos[0].veredito == Veredito.ERRO_AMBIENTE and "retentativa" in casos[0].detalhe
