"""Fluxos de navegador: normalizacao, coleta de eventos e comparacao contra a baseline (sem navegador)."""
import copy
import json
from pathlib import Path

import pytest

from regressao.completa import fluxos
from regressao.nucleo.veredito import Veredito

I, D, N, E = Veredito.IDENTICO, Veredito.DIVERGE, Veredito.INCONCLUSIVO, Veredito.ERRO_AMBIENTE


def passo(nome, dom="<p>x</p>", **kw):
    p = {"nome": nome, "ok": True, "erro": None, "url": "/a.php", "dom": dom,
         "dom_sha256": fluxos.sha(dom) if dom is not None else None, "dom_truncado": False,
         "requisicoes": ["GET 200 /a.php"], "runtime": {"/a.php": "PHP-5.6 (referencia)"},
         "dialogos": [], "banco": None, "extra": {}}
    p.update(kw)
    return p


def fluxo(*passos, id="nav", console=(), falhas=()):
    return {"id": id, "descricao": "d", "passos": list(passos), "console": list(console), "falhas": list(falhas)}


def veredictos(casos):
    return {c.id: c.veredito for c in casos}


# ---------------------------------------------------------------- normalizacao

def test_normaliza_dom_tira_scripts_estilos_datas_horas_sessao_e_saudacao():
    html = ("<html><head><style>a{x:1}</style><script src='s.js'></script>"
            "<script>var t = 'Math.random 12345';</script></head><body>\n"
            "  <div>Boa noite, <b>FULANO</b> em 14/11/2026 as 23:59:01</div>\n"
            "  <a href='x.php?sid=" + "a" * 32 + "'>l</a> ECIDADEWINDOWMAIN=" + "b" * 40 + "\n"
            "</body></html>")
    out = fluxos.normaliza_dom(html)
    assert "Math.random" not in out and "a{x:1}" not in out
    assert "<script src='s.js'>" in out or 'src="s.js"' in out or "s.js" in out
    assert "14/11/2026" not in out and "23:59:01" not in out and "Boa noite" not in out
    assert "a" * 32 not in out and "b" * 40 not in out
    assert "FULANO" in out
    # estavel: duas serializacoes que so diferem em volateis ficam iguais
    out2 = fluxos.normaliza_dom(html.replace("14/11/2026", "15/12/2027").replace("23:59:01", "01:02:03")
                                .replace("Boa noite", "Bom dia").replace("a" * 32, "c" * 32))
    assert out == out2


def test_normaliza_dom_omite_a_lista_de_ultimos_acessos_do_modulo():
    """`modulos.php` lista os ultimos acessos do usuario (db_logsacessa, janela por data): e historico
    de uso, nao comportamento da tela; muda a cada rodada de fluxos."""
    antes = ('<div id="acessosModulo"><table><tr><td>Ultimos</td></tr><tr><td><a href="x.php">Inclusao</a>'
             '</td><td>14/11/2026</td></tr></table></div><p>resto</p>')
    depois = '<div id="acessosModulo"><table><tr><td>Ultimos</td></tr></table></div><p>resto</p>'
    assert fluxos.normaliza_dom(antes) == fluxos.normaliza_dom(depois)
    assert "resto" in fluxos.normaliza_dom(antes) and "x.php" not in fluxos.normaliza_dom(antes)


def test_normaliza_dom_uma_tag_por_linha_e_sem_espacos_repetidos():
    out = fluxos.normaliza_dom("<div>  <p>a   b</p>\n\n   <p>c</p></div>")
    assert out.splitlines() == ["<div>", "<p>a b</p>", "<p>c</p>", "</div>"]


def test_caminho_seguro_nao_guarda_valores_de_query_nem_credenciais():
    assert fluxos.caminho_seguro("http://localhost:8090/abrir.php?sAuth=REJfbG9naW49ZGJzZWxsZXI%3D&conteudoCaptcha=") \
        == "/abrir.php?conteudoCaptcha&sAuth"
    assert fluxos.caminho_seguro("http://localhost:8090/corpo.php?aW5zdGl0PTE=") == "/corpo.php?<opaco>"
    assert fluxos.caminho_seguro("http://localhost:8090/x.php") == "/x.php"
    assert fluxos.caminho_seguro("http://localhost:8090/f.php?pesquisa_chave=1&funcao_js=x") == "/f.php?funcao_js&pesquisa_chave"


def test_confere_sem_segredos_barra_sid_hash_de_senha_e_token():
    ok = fluxo(passo("a"))
    fluxos.confere_sem_segredos(ok)  # nao levanta
    for sujo in ("PHPSESSID=" + "a" * 26, "sAuth=REJfbG9naW49", "ECIDADEWINDOWMAIN=" + "a" * 40,
                 "Bearer eyJhbGciOiJSUzI1NiJ9.eyJ.abc", "senha=05b071fc2d1f5f4dd4cd6dfb6ee06ad3"):
        f = fluxo(passo("a", dom=f"<p>{sujo}</p>"))
        with pytest.raises(fluxos.SegredoNaBaseline):
            fluxos.confere_sem_segredos(f)


# ---------------------------------------------------------------- coletor

def test_coletor_ordena_requisicoes_registra_runtime_e_dialogos():
    c = fluxos.Coletor()
    c.resposta("GET", "http://x/b.php?z=1", 200, "document", "PHP-8.5 (migrado)")
    c.resposta("GET", "http://x/a.php", 200, "document", "PHP-5.6 (referencia)")
    c.resposta("GET", "http://x/img.png", 404, "image", "PHP-5.6 (referencia)")
    c.resposta("POST", "http://x/rpc.php", 200, "xhr", None)
    c.dialogo("alert", "Inclusao efetuada\n com Sucesso\nValores : 4")
    c.erro_console("Failed to load resource: the server responded with a status of 404 (Not Found)")
    p = c.fecha_passo()
    assert p["requisicoes"] == ["GET 200 /a.php", "GET 200 /b.php?z", "POST 200 /rpc.php"]  # so document/xhr/fetch
    assert p["runtime"] == {"/a.php": "PHP-5.6 (referencia)", "/b.php?z": "PHP-8.5 (migrado)"}
    assert p["dialogos"] == ["alert: Inclusao efetuada com Sucesso Valores : 4"]
    assert c.falhas == ["404 GET /img.png"]
    assert c.console and "404" in c.console[0]
    assert c.fecha_passo()["requisicoes"] == []  # o balde foi esvaziado


def test_coletor_dedupa_requisicoes_e_ignora_scripts_carregados_por_xhr():
    c = fluxos.Coletor()
    for _ in range(2):  # require_once do e-cidade baixa o mesmo script duas vezes por XHR
        c.resposta("GET", "http://x/scripts/prototype.js", 200, "xhr", "PHP-5.6 (referencia)")
        c.resposta("GET", "http://x/a.php", 200, "document", "PHP-5.6 (referencia)")
    assert c.fecha_passo()["requisicoes"] == ["GET 200 /a.php"]
    c.resposta("GET", "http://x/scripts/quebrado.js", 404, "xhr", None)
    assert c.falhas == ["404 GET /scripts/quebrado.js"]


def test_coletor_ignora_err_aborted_mas_guarda_outras_falhas_de_rede():
    c = fluxos.Coletor()
    c.requisicao_falhou("GET", "http://x/topo.php?uso=1", "net::ERR_ABORTED")
    c.requisicao_falhou("GET", "http://x/b.png", "net::ERR_CONNECTION_REFUSED")
    assert c.falhas == ["FALHOU GET /b.png: net::ERR_CONNECTION_REFUSED"]


def test_coletor_guarda_a_url_do_pdf_so_em_memoria():
    c = fluxos.Coletor()
    c.resposta("GET", "http://x/r.php?a=1", 200, "document", "PHP-8.5 (migrado)", "application/pdf")
    assert c.pdfs == ["http://x/r.php?a=1"]
    assert c.fecha_passo()["requisicoes"] == ["GET 200 /r.php?a"]  # no passo so entra o caminho seguro


def test_coletor_deduplica_e_ordena_console_e_falhas():
    c = fluxos.Coletor()
    for _ in range(3):
        c.erro_console("boom em 14/11/2026")
    c.erro_console("alfa")
    c.requisicao_falhou("GET", "http://x/z.js", "net::ERR_FAILED")
    assert c.console == ["alfa", "boom em DD/MM/AAAA"]
    assert c.falhas == ["FALHOU GET /z.js: net::ERR_FAILED"]


# ---------------------------------------------------------------- definicao dos fluxos

def test_fluxos_registrados_cobrem_as_areas_criticas_e_tem_passos_bem_formados():
    assert {"navegacao", "incluir-registro", "emitir-relatorio", "financeiro", "tributario", "cadastros"} == set(fluxos.FLUXOS)
    for fid, (descricao, fabrica) in fluxos.FLUXOS.items():
        passos = fabrica()
        nomes = [n for n, _f, _s in passos]
        assert descricao and len(nomes) == len(set(nomes)), fid          # nomes unicos
        assert nomes[0] in ("login", "entrada"), fid                       # 1o passo = ambiente (ERRO_AMBIENTE se falhar)
        assert all(callable(f) and isinstance(s, bool) for _n, f, s in passos), fid


def test_banco_linhas_devolve_hash_e_contagem_por_tabela(monkeypatch):
    from regressao.nucleo import banco
    monkeypatch.setattr(banco, "hash_tabelas", lambda ts: {t: f"h-{t}" for t in ts})
    monkeypatch.setattr(banco, "_psql", lambda sql, db=banco.BASE: "7\n")
    r = fluxos._banco_linhas(["a.t1", "b.t2"])
    assert r == {"hash": {"a.t1": "h-a.t1", "b.t2": "h-b.t2"}, "linhas": {"a.t1": 7, "b.t2": 7}}


def test_hash_sem_horas_mascara_hhmm_no_sql_e_valida_o_nome(monkeypatch):
    from regressao.nucleo import banco
    sqls = []
    monkeypatch.setattr(banco, "_psql", lambda sql, db=banco.BASE: sqls.append(sql) or "abc\n")
    assert fluxos.hash_sem_horas(["protocolo.cgm"]) == {"protocolo.cgm": "abc"}
    # so a coluna do relogio (z01_hora) sai do hash: o resto da linha, inclusive outras horas, continua comparado
    assert "to_jsonb(t) - 'z01_hora'" in sqls[0] and "regexp_replace" not in sqls[0]
    assert "from protocolo.cgm t" in sqls[0]
    with pytest.raises(ValueError):
        fluxos.hash_sem_horas(["cgm; drop table x"])


def test_inclui_nao_tem_parametro_morto():
    import inspect
    assert list(inspect.signature(fluxos._inclui).parameters) == ["j", "tabelas", "botao", "sem_horas"]


def test_n_passos_do_meta_conta_todos_os_fluxos_da_pasta(tmp_path):
    fluxos.grava_baseline(tmp_path, [fluxo(passo("a"), id="x")], dump_sha256="s", commit="c")
    fluxos.grava_baseline(tmp_path, [fluxo(passo("a"), passo("b"), id="y")], dump_sha256="s", commit="c")  # sem apagar x
    meta = json.loads((tmp_path / "_meta.json").read_text())
    assert meta["fluxos"] == ["x", "y"] and meta["n_passos"] == 3


# ---------------------------------------------------------------- _Janela (contexto falso)

class _Pg:
    def wait_for_timeout(self, ms):
        import time
        time.sleep(ms / 1000)


class _Ctx:
    def __init__(self):
        self.h: dict[str, list] = {}

    def on(self, ev, fn):
        self.h.setdefault(ev, []).append(fn)

    def set_default_timeout(self, _):
        pass

    def new_page(self):
        return _Pg()

    def emite(self, ev, *a):
        for fn in self.h.get(ev, []):
            fn(*a)


class _Browser:
    def __init__(self):
        self.ctx = _Ctx()

    def new_context(self, **_):
        return self.ctx


class _Req:
    method, url, failure = "GET", "http://x/a.php", "net::ERR_ABORTED"


def test_janela_registra_cada_handler_de_rede_uma_vez():
    b = _Browser()
    fluxos._Janela(b, "http://p", fluxos.Coletor(), 60)
    for ev in ("request", "requestfinished", "requestfailed", "response"):
        assert len(b.ctx.h[ev]) == 1, ev


def test_requisicao_que_falha_nao_trava_o_assenta_e_a_contagem_volta_a_zero():
    import time
    b = _Browser()
    j = fluxos._Janela(b, "http://p", fluxos.Coletor(), 60)
    b.ctx.emite("request", _Req())
    b.ctx.emite("request", _Req())
    assert j.em_voo == 2
    b.ctx.emite("requestfailed", _Req())     # inclusive ERR_ABORTED
    b.ctx.emite("requestfinished", _Req())
    assert j.em_voo == 0
    t0 = time.monotonic()
    j.assenta(maximo_s=5)
    assert time.monotonic() - t0 < 3         # saiu por quietude, nao pelo teto de 5 s


# ---------------------------------------------------------------- comparacao

def test_fluxo_igual_e_identico_por_passo():
    b = fluxo(passo("login"), passo("tela"))
    casos = fluxos.compara_fluxo(b, copy.deepcopy(b))
    assert veredictos(casos) == {"fluxo:nav:login": I, "fluxo:nav:tela": I, "fluxo:nav:eventos": I}


def test_mudanca_so_do_runtime_e_informacao_nunca_falha():
    b = fluxo(passo("tela"))
    a = copy.deepcopy(b)
    a["passos"][0]["runtime"] = {"/a.php": "PHP-8.5 (migrado)"}
    casos = fluxos.compara_fluxo(b, a)
    tela = next(c for c in casos if c.id == "fluxo:nav:tela")
    assert tela.veredito == I
    assert "INFO" in tela.detalhe and "PHP-5.6" in tela.detalhe and "PHP-8.5" in tela.detalhe


def test_dom_diferente_diverge_com_diff_unificado():
    b = fluxo(passo("tela", dom="<p>a</p>\n<p>b</p>"))
    a = fluxo(passo("tela", dom="<p>a</p>\n<p>c</p>"))
    c = next(x for x in fluxos.compara_fluxo(b, a) if x.id == "fluxo:nav:tela")
    assert c.veredito == D
    assert "-<p>b</p>" in c.diff and "+<p>c</p>" in c.diff


def test_status_http_diferente_diverge():
    b = fluxo(passo("tela"))
    a = fluxo(passo("tela", requisicoes=["GET 500 /a.php"]))
    c = next(x for x in fluxos.compara_fluxo(b, a) if x.id == "fluxo:nav:tela")
    assert c.veredito == D and "200" in c.detalhe and "500" in c.detalhe


def test_efeito_no_banco_diferente_diverge():
    b = fluxo(passo("salvar", banco={"arrecadacao.grupotaxa": "h1"}))
    a = fluxo(passo("salvar", banco={"arrecadacao.grupotaxa": "h2"}))
    c = next(x for x in fluxos.compara_fluxo(b, a) if x.id == "fluxo:nav:salvar")
    assert c.veredito == D and "arrecadacao.grupotaxa" in c.detalhe


def test_dialogo_diferente_diverge():
    b = fluxo(passo("salvar", dialogos=["alert: ok"]))
    a = fluxo(passo("salvar", dialogos=["alert: erro"]))
    assert next(x for x in fluxos.compara_fluxo(b, a) if x.id == "fluxo:nav:salvar").veredito == D


def test_passo_que_falha_agora_mas_passou_na_baseline_diverge_e_os_seguintes_ficam_inconclusivos():
    b = fluxo(passo("login"), passo("tela"), passo("sair"))
    a = fluxo(passo("login"), passo("tela", ok=False, erro="Timeout 20000ms: input[name=incluir]", dom=None,
                                    dom_sha256=None), passo("sair", ok=False, erro="nao exercitado", dom=None,
                                                            dom_sha256=None, exercitado=False))
    v = veredictos(fluxos.compara_fluxo(b, a))
    assert v["fluxo:nav:login"] == I and v["fluxo:nav:tela"] == D and v["fluxo:nav:sair"] == N


def test_falha_no_primeiro_passo_e_erro_de_ambiente():
    b = fluxo(passo("login"), passo("tela"))
    a = fluxo(passo("login", ok=False, erro="Timeout", dom=None, dom_sha256=None),
              passo("tela", ok=False, erro="nao exercitado", dom=None, dom_sha256=None, exercitado=False))
    v = veredictos(fluxos.compara_fluxo(b, a))
    assert v["fluxo:nav:login"] == E and v["fluxo:nav:tela"] == N


def test_passo_que_ja_falhava_na_baseline_e_inconclusivo():
    b = fluxo(passo("login"), passo("tela", ok=False, erro="sem formulario", dom=None, dom_sha256=None))
    a = copy.deepcopy(b)
    assert veredictos(fluxos.compara_fluxo(b, a))["fluxo:nav:tela"] == N


def test_passo_novo_ou_removido_em_relacao_a_baseline_diverge():
    b = fluxo(passo("login"), passo("tela"))
    a = fluxo(passo("login"))
    assert veredictos(fluxos.compara_fluxo(b, a))["fluxo:nav:tela"] == D


def test_erros_de_console_e_falhas_de_rede_so_viram_veredito_se_diferem_da_baseline():
    b = fluxo(passo("tela"), console=["erro antigo"], falhas=["404 GET /logo.png"])
    mesmo = copy.deepcopy(b)
    ev = next(c for c in fluxos.compara_fluxo(b, mesmo) if c.id == "fluxo:nav:eventos")
    assert ev.veredito == I and "erro antigo" in ev.detalhe  # informacao
    novo = copy.deepcopy(b)
    novo["console"].append("Uncaught TypeError: x is not a function")
    ev = next(c for c in fluxos.compara_fluxo(b, novo) if c.id == "fluxo:nav:eventos")
    assert ev.veredito == D and "Uncaught TypeError" in ev.detalhe
    menos = fluxo(passo("tela"), console=[], falhas=[])
    ev = next(c for c in fluxos.compara_fluxo(b, menos) if c.id == "fluxo:nav:eventos")
    assert ev.veredito == I  # sumiu um erro: nao e regressao


# ---------------------------------------------------------------- baseline em disco

def test_grava_e_carrega_baseline_com_meta_e_recusa_segredo(tmp_path):
    f = fluxo(passo("a"))
    fluxos.grava_baseline(tmp_path, [f], dump_sha256="abc", commit="c1")
    assert json.loads((tmp_path / "_meta.json").read_text())["dump_sha256"] == "abc"
    assert fluxos.carrega_baseline(tmp_path, "abc")["nav"]["passos"][0]["nome"] == "a"
    with pytest.raises(fluxos.SegredoNaBaseline):
        fluxos.grava_baseline(tmp_path / "x", [fluxo(passo("a", dom="<p>PHPSESSID=" + "z" * 26 + "</p>"))],
                              dump_sha256="abc", commit="c1")
    assert not (tmp_path / "x").exists() or not list((tmp_path / "x").glob("*.json"))


def test_baseline_ausente_ou_de_outro_dump_e_erro_de_ambiente(tmp_path):
    with pytest.raises(fluxos.BaselineInvalida, match="ausente"):
        fluxos.carrega_baseline(tmp_path / "nada", "abc")
    fluxos.grava_baseline(tmp_path, [fluxo(passo("a"))], dump_sha256="abc", commit="c1")
    with pytest.raises(fluxos.BaselineInvalida, match="outro dump"):
        fluxos.carrega_baseline(tmp_path, "outro")


def test_compara_fluxos_com_executor_falso(tmp_path, monkeypatch):
    base = tmp_path / "base"
    fluxos.grava_baseline(base, [fluxo(passo("login"))], dump_sha256="s", commit="c")
    atual = fluxo(passo("login", dom="<p>mudou</p>"))
    casos, meta = fluxos.compara_fluxos("http://p", base, "s", executa=lambda proxy, ids: [atual], restaurar=False)
    assert veredictos(casos)["fluxo:nav:login"] == D
    assert meta["comparavel"] is False and meta["restauracao_s"] is None
    casos, _ = fluxos.compara_fluxos("http://p", tmp_path / "nada", "s", executa=lambda p, i: [atual], restaurar=False)
    assert [c.veredito for c in casos] == [E] and casos[0].id == "fluxo:baseline"
    # fluxo na baseline sem execucao correspondente
    fluxos.grava_baseline(base / "2", [fluxo(passo("a"), id="x"), fluxo(passo("a"), id="y")], dump_sha256="s", commit="c")
    casos, _ = fluxos.compara_fluxos("http://p", base / "2", "s", executa=lambda p, i: [fluxo(passo("a"), id="x")],
                                      restaurar=False)
    assert veredictos(casos)["fluxo:y:execucao"] == N


# ---------------------------------------------------------------- runtime: 7.4 x 7.4 e gravacao so na referencia

R74, R85 = "PHP-7.4 (referencia)", "PHP-8.5 (migrado)"


def test_aviso_quando_nenhum_passo_veio_do_php85():
    assert "7.4 x 7.4" in fluxos.aviso_sem_php85({R74: 12})
    assert "7.4 x 7.4" in fluxos.aviso_sem_php85({})
    assert fluxos.aviso_sem_php85({R74: 11, R85: 1}) is None


def test_resumo_dos_fluxos_avisa_que_mediu_7_4_x_7_4(tmp_path, monkeypatch):
    from regressao.nucleo import ambiente
    from regressao.nucleo.veredito import Caso
    monkeypatch.setattr(ambiente, "_responde", lambda url: True)
    monkeypatch.setattr(fluxos, "_dump_sha", lambda: "s")
    for observado, avisa in (({R74: 3}, True), ({R74: 2, R85: 1}, False)):
        monkeypatch.setattr(fluxos, "compara_fluxos", lambda *a, o=observado, **k: (
            [Caso("fluxo:nav:login", "fluxos", I)], {"comparavel": True, "runtime_observado": o}))
        saida = tmp_path / ("a" if avisa else "b")
        fluxos.roda_fluxos_rodada(saida, "http://proxy")
        resumo = (saida / "resumo.md").read_text(encoding="utf-8")
        assert ("7.4 x 7.4" in resumo) is avisa


def test_resumo_da_completa_avisa_quando_os_fluxos_nao_passaram_pelo_8_5():
    from regressao.completa import orquestra
    from regressao.nucleo.veredito import Caso
    for observado, avisa in (({R74: 3}, True), ({R85: 1}, False)):
        fl = orquestra.Frente("fluxos", 0, [Caso("fluxo:nav:login", "fluxos", I)],
                              {"comparavel": True, "runtime_observado": observado}, 1.0)
        _, _, avisos = orquestra.agrega({"fluxos": fl}, {}, {}, ["fluxos"])
        assert any("7.4 x 7.4" in a for a in avisos) is avisa


@pytest.fixture
def gravacao(tmp_path, monkeypatch):
    """`grava_fluxos` sem navegador, banco nem proxy; devolve a lista de baselines gravadas."""
    from regressao.nucleo import ambiente
    gravadas = []
    monkeypatch.setattr(fluxos, "DIR_BASELINE", tmp_path / "baseline")
    monkeypatch.setattr(ambiente, "_responde", lambda url: True)
    monkeypatch.setattr(fluxos, "_prepara_banco", lambda restaurar, meta: None)
    monkeypatch.setattr(fluxos, "versoes_navegador", lambda: {})
    monkeypatch.setattr(fluxos, "_dump_sha", lambda: "s")
    monkeypatch.setattr(fluxos, "grava_baseline", lambda d, fs, *a, **k: gravadas.append([f["id"] for f in fs]))
    return gravadas


def test_gravar_recusa_passo_servido_por_outro_runtime(gravacao, tmp_path, monkeypatch, capsys):
    misto = fluxo(passo("login", runtime={"/a.php": R74}), passo("tela", runtime={"/b.php": R85}))
    monkeypatch.setattr(fluxos, "executa_fluxos", lambda proxy, ids, versoes: [misto])
    assert fluxos.grava_fluxos(tmp_path / "s", "http://proxy") == 2
    assert gravacao == []
    err = capsys.readouterr().err
    assert "baseline NAO gravada" in err and "/b.php" in err and "PHP-8.5" in err


def test_gravar_aceita_quando_todos_os_passos_vieram_do_7_4(gravacao, tmp_path, monkeypatch):
    so74 = fluxo(passo("login", runtime={"/a.php": R74}), passo("sair", runtime={}))
    monkeypatch.setattr(fluxos, "executa_fluxos", lambda proxy, ids, versoes: [so74])
    assert fluxos.grava_fluxos(tmp_path / "s", "http://proxy") == 0
    assert gravacao == [["nav"]]
