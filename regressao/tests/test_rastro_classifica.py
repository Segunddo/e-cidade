"""regressao/rastro/alinha.py e classifica.py com rastros sinteticos."""
from regressao.rastro.alinha import alinha
from regressao.rastro.classifica import classifica
from regressao.rastro.evento import Evento


def v(r, t="int"):
    return {"t": t, "r": str(r), "h": "h" + str(r)}


def ev(seq, sonda, linha, tipo, nome, valor=None, arq="t.php"):
    return Evento(seq=seq, sonda=sonda, arquivo=arq, linha=linha, tipo=tipo, nome=nome, valor=valor)


OK = (200, b"<html>ok</html>")
OUTRA = (500, b"<html>erro</html>")


def test_rastros_iguais_dao_identico():
    t = [ev(1, 1, 3, "a", "x", v(1)), ev(2, 2, 4, "a", "y", v(2))]
    r = classifica(t, list(t), list(t), OK, OK)
    assert r.veredito == "IDENTICO" and r.causal is None and r.ruido == []


def test_divergencia_que_reconverge_com_resposta_igual():
    ref = [ev(1, 1, 3, "a", "x", v(1)), ev(2, 2, 4, "a", "x", v(5))]
    alvo = [ev(1, 1, 3, "a", "x", v(9)), ev(2, 2, 4, "a", "x", v(5))]     # x diverge na linha 3 e volta a ser igual na 4
    r = classifica(ref, alvo, list(ref), OK, OK)
    assert r.veredito == "DIVERGE-RECONVERGENTE" and [d.linha for d in r.reconvergentes] == [3]


def test_divergencia_com_resposta_diferente_e_causal_e_aponta_a_primeira_que_nao_reconverge():
    ref = [ev(1, 1, 3, "a", "x", v(1)), ev(2, 2, 4, "a", "y", v(2)), ev(3, 3, 5, "a", "z", v(3))]
    alvo = [ev(1, 1, 3, "a", "x", v(1)), ev(2, 2, 4, "a", "y", v(99)), ev(3, 3, 5, "a", "z", v(98))]
    r = classifica(ref, alvo, list(ref), OK, OUTRA)
    assert r.veredito == "DIVERGE-CAUSAL"
    assert (r.causal.arquivo, r.causal.linha, r.causal.nome) == ("t.php", 4, "y")        # a PRIMEIRA, nao a z
    assert (r.causal.valor_ref["r"], r.causal.valor_alvo["r"]) == ("2", "99")


def test_divergencia_que_reconverge_nao_e_a_causal_mesmo_com_resposta_diferente():
    ref = [ev(1, 1, 3, "a", "x", v(1)), ev(2, 2, 4, "a", "x", v(5)), ev(3, 3, 6, "a", "z", v(3))]
    alvo = [ev(1, 1, 3, "a", "x", v(9)), ev(2, 2, 4, "a", "x", v(5)), ev(3, 3, 6, "a", "z", v(77))]
    r = classifica(ref, alvo, list(ref), OK, OUTRA)
    assert r.causal.linha == 6 and [d.linha for d in r.reconvergentes] == [3]


def test_aviso_no_ref_e_excecao_no_alvo_na_mesma_linha_e_causal():
    aviso = Evento(5, 0, "fpdf151/pdf.php", 186, "w", "warning", {"t": "aviso", "r": "pg_result(): supplied argument..."})
    exc = Evento(7, 0, "fpdf151/pdf.php", 186, "e", "excecao_app", {"t": "excecao", "r": "TypeError: pg_result(): Argument #1..."})
    ref = [ev(1, 1, 3, "a", "x", v(1)), aviso]
    alvo = [ev(1, 1, 3, "a", "x", v(1)), exc]
    d = alinha(ref, alvo)
    assert len(d) == 1 and d[0].motivo == "aviso_x_excecao" and (d[0].arquivo, d[0].linha) == ("fpdf151/pdf.php", 186)
    r = classifica(ref, alvo, list(ref), OK, OUTRA)
    assert r.veredito == "DIVERGE-CAUSAL" and r.causal.motivo == "aviso_x_excecao"


def test_aviso_de_depreciacao_so_do_alvo_nunca_e_a_causa_mas_o_sintoma_aparece():
    deprec = Evento(1, 0, "src/V3/Extension/ParameterBag.php", 133, "w", "deprecated", {"t": "aviso", "r": "Return type of ..."})
    ref = [ev(2, 1, 3, "a", "x", v(1)), Evento(5, 0, "cad.php", 40, "w", "warning", {"t": "aviso", "r": "pg_num_rows()"})]
    alvo = [deprec, ev(2, 1, 3, "a", "x", v(1)), Evento(6, 0, "cad.php", 40, "e", "excecao_app", {"t": "excecao", "r": "TypeError"})]
    r = classifica(ref, alvo, list(ref), OK, OUTRA)
    assert r.causal.motivo == "aviso_x_excecao" and (r.causal.arquivo, r.causal.linha) == ("cad.php", 40)
    assert r.causal.arquivo != "src/V3/Extension/ParameterBag.php"                # a depreciacao nao e causa
    assert r.sintoma == r.causal


def test_sintoma_e_a_excecao_e_a_causa_e_o_valor_que_a_alimentou():
    ref = [ev(1, 1, 3, "a", "rs", v("resource")), ev(2, 2, 9, "a", "n", v(0))]
    alvo = [ev(1, 1, 3, "a", "rs", v("false", "bool")), Evento(7, 0, "t.php", 9, "e", "excecao_app", {"t": "excecao", "r": "TypeError"})]
    le = {1: [], 2: ["rs"]}                                          # a linha 9 le `rs`
    r = classifica(ref, alvo, list(ref), OK, OUTRA, le=lambda arq, s: le[s])
    assert (r.causal.linha, r.causal.nome) == (3, "rs")            # onde o valor ficou errado
    assert (r.sintoma.arquivo, r.sintoma.linha) == ("t.php", 9)    # onde estourou


def test_a_causa_e_a_divergencia_que_alimenta_a_linha_que_estourou_e_nao_uma_anterior_sem_relacao():
    # linha 1: cookie (sem relacao) diverge; linha 3: rs diverge; linha 9 estoura lendo rs
    ref = [ev(1, 1, 1, "a", "cookie", v(1)), ev(2, 2, 3, "a", "rs", v("resource", "pgresult")), ev(3, 3, 9, "c", "pg_num_rows", v(0))]
    alvo = [ev(1, 1, 1, "a", "cookie", v(2)), ev(2, 2, 3, "a", "rs", v("false", "bool")),
            Evento(1000000007, 0, "t.php", 9, "e", "excecao_app", {"t": "excecao", "r": "TypeError"})]
    le = {1: [], 2: [], 3: ["rs"]}
    r = classifica(ref, alvo, list(ref), OK, OUTRA, le=lambda arq, s: le[s])
    assert (r.causal.nome, r.causal.linha) == ("rs", 3)
    assert (r.sintoma.arquivo, r.sintoma.linha) == ("t.php", 9)
    assert [d.nome for d in r.outras] == ["cookie"]                      # a anterior sem relacao vira "outra", nao causa


def test_sem_divergencia_de_valor_a_causa_e_o_proprio_sintoma_e_a_cadeia_mostra_o_dado():
    aviso = Evento(5, 0, "t.php", 9, "w", "warning", {"t": "aviso", "r": "pg_num_rows() expects resource"})
    exc = Evento(1000000001, 0, "t.php", 9, "e", "excecao_app", {"t": "excecao", "r": "TypeError: pg_num_rows()"})
    falso = v("false", "bool")                                              # $rs e false nos DOIS lados: nao ha divergencia de valor
    ref = [ev(1, 1, 1, "a", "cookie", v(1)), ev(2, 2, 3, "a", "rs", falso), ev(3, 3, 9, "c", "pg_num_rows", v(0)), aviso]
    alvo = [ev(1, 1, 1, "a", "cookie", v(2)), ev(2, 2, 3, "a", "rs", falso), exc]
    le = {1: [], 2: [], 3: ["rs"]}
    r = classifica(ref, alvo, list(ref), OK, OUTRA, le=lambda arq, s: le[s])
    assert r.causal.motivo == "aviso_x_excecao" and (r.causal.arquivo, r.causal.linha) == ("t.php", 9)
    assert [(e.nome, e.valor["r"]) for e in r.cadeia] == [("rs", "false")]  # de onde veio o dado que quebrou
    assert "endureceu" in r.nota and [d.nome for d in r.outras] == ["cookie"]


def test_sem_excecao_divergencia_de_infraestrutura_nao_e_causa_e_a_resposta_e_mostrada():
    ref = [ev(1, 1, 56, "a", "cookie", v(1), arq="src/V3/Window/Session.php"), ev(2, 2, 3, "a", "x", v(1))]
    alvo = [ev(1, 1, 56, "a", "cookie", v(2), arq="src/V3/Window/Session.php"), ev(2, 2, 3, "a", "x", v(1))]
    r = classifica(ref, alvo, list(ref), (200, b"<p>total 10</p>\n<p>fim</p>"), (200, b"<p>total 11</p>\n<p>fim</p>"))
    assert r.veredito == "INCONCLUSIVO" and r.causal is None and "infraestrutura" in r.nota
    assert "-<p>total 10</p>" in r.diff_resposta and "+<p>total 11</p>" in r.diff_resposta


def test_sem_excecao_divergencia_no_codigo_da_tela_continua_sendo_a_causa():
    ref = [ev(1, 1, 7, "a", "total", v(10), arq="cad9_x.php")]
    alvo = [ev(1, 1, 7, "a", "total", v(11), arq="cad9_x.php")]
    r = classifica(ref, alvo, list(ref), (200, b"a"), (200, b"b"))
    assert r.veredito == "DIVERGE-CAUSAL" and (r.causal.arquivo, r.causal.linha) == ("cad9_x.php", 7)


def test_backend_xdebug_cadeia_por_dependencia_de_dados_usando_as_leituras_por_linha():
    """Eventos do Xdebug (sonda 0): a cadeia vem das variaveis lidas por LINHA (analise estatica), nao por proximidade."""
    def a(seq, linha, nome, val):
        return Evento(seq, 0, "t.php", linha, "a", nome, {"t": "string", "r": val})
    ref = [a(1, 10, "tabela", "'x'"), a(2, 11, "sql", "'select'"), a(3, 12, "rs", "RESOURCE"), a(4, 13, "outra", "1")]
    alvo = [a(1, 10, "tabela", "'x'"), a(2, 11, "sql", "'select'"), a(3, 12, "rs", "FALSE"), a(4, 13, "outra", "1"),
            Evento(10**9, 0, "t.php", 15, "e", "excecao_app", {"t": "excecao", "r": "TypeError"})]
    lidas = {("t.php", 15): ["rs"], ("t.php", 12): ["sql"], ("t.php", 11): ["tabela"], ("t.php", 10): [], ("t.php", 13): []}
    r = classifica(ref, alvo, list(ref), OK, OUTRA, le_linha=lambda arq, l: lidas.get((arq, l), []))
    assert [e.nome for e in r.cadeia] == ["tabela", "sql", "rs"]          # rs <- sql <- tabela; `outra` fica de fora
    assert r.cadeia[-1].valor["r"] == "FALSE"


def test_atribuicao_que_so_existe_de_um_lado_nao_e_a_causa_do_sintoma_mesmo_lendo_a_mesma_variavel():
    """O 8.5 executa uma atribuicao a mais de `mes` (contagem/fluxo); isso nao e um valor errado que alimentou a linha que estourou."""
    ref = [ev(1, 0, 196, "a", "mes", v("01"), arq="d.php")]
    alvo = [ev(1, 0, 196, "a", "mes", v("01"), arq="d.php"), ev(2, 0, 196, "a", "mes", v(""), arq="d.php"),
            Evento(10**9, 0, "d.php", 203, "e", "excecao_app", {"t": "excecao", "r": "TypeError: checkdate()"})]
    r = classifica(ref, alvo, list(ref), OK, OUTRA, le_linha=lambda arq, l: ["mes"] if l == 203 else [])
    assert (r.causal.arquivo, r.causal.linha, r.causal.tipo) == ("d.php", 203, "e")


def test_texto_diferente_do_aviso_nao_e_divergencia():
    a74 = Evento(1, 0, "a.php", 3, "w", "warning", {"t": "aviso", "r": "supplied argument is not a valid resource"})
    a85 = Evento(1, 0, "a.php", 3, "w", "warning", {"t": "aviso", "r": "Argument must be of type X"})
    assert alinha([a74], [a85]) == []


def test_laco_com_mais_iteracoes_nao_desalinha_o_resto():
    ref = [ev(1, 1, 3, "a", "i", v(0)), ev(2, 1, 3, "a", "i", v(1)), ev(3, 2, 9, "a", "fim", v(7))]
    alvo = [ev(1, 1, 3, "a", "i", v(0)), ev(2, 1, 3, "a", "i", v(1)), ev(3, 1, 3, "a", "i", v(2)), ev(4, 2, 9, "a", "fim", v(7))]
    d = alinha(ref, alvo)
    assert len(d) == 1 and d[0].motivo == "so_alvo" and d[0].ocorrencia == 2        # so a iteracao extra; "fim" segue alinhado


def test_divergencia_presente_tambem_entre_ref_e_ref2_e_ruido():
    ref = [ev(1, 1, 3, "a", "hora", v("10:00")), ev(2, 2, 4, "a", "y", v(2))]
    ref2 = [ev(1, 1, 3, "a", "hora", v("10:01")), ev(2, 2, 4, "a", "y", v(2))]
    alvo = [ev(1, 1, 3, "a", "hora", v("10:02")), ev(2, 2, 4, "a", "y", v(2))]
    r = classifica(ref, alvo, ref2, OK, OK)
    assert r.veredito == "IDENTICO" and [d.nome for d in r.ruido] == ["hora"]


def test_rastro_truncado_nunca_e_reconvergente():
    ref = [ev(1, 1, 3, "a", "x", v(1)), Evento(2, 0, "", 0, "T", "")]
    alvo = [ev(1, 1, 3, "a", "x", v(9)), ev(2, 1, 3, "a", "x", v(1))]
    r = classifica(ref, alvo, list(ref), OK, OK)
    assert r.veredito == "INCONCLUSIVO" and r.truncado


def test_resposta_diferente_com_rastro_igual_e_inconclusivo():
    t = [ev(1, 1, 3, "a", "x", v(1))]
    r = classifica(t, list(t), list(t), OK, OUTRA)
    assert r.veredito == "INCONCLUSIVO" and "sem sonda" in r.nota


def test_cadeia_causal_segue_as_variaveis_lidas():
    # linha 3: a = ...; linha 4: b = f(a); linha 5: c = b + 1 (causal: le b)
    alvo = [ev(1, 1, 3, "a", "a", v(0)), ev(2, 2, 4, "a", "b", v(5)), ev(3, 3, 5, "a", "c", v(6)), ev(4, 4, 6, "a", "ruido", v(0))]
    ref = [ev(1, 1, 3, "a", "a", v(0)), ev(2, 2, 4, "a", "b", v(5)), ev(3, 3, 5, "a", "c", v(100)), ev(4, 4, 6, "a", "ruido", v(0))]
    le = {1: [], 2: ["a"], 3: ["b"], 4: []}
    r = classifica(ref, alvo, list(ref), OK, OUTRA, le=lambda arq, s: le[s])
    assert r.causal.nome == "c"
    assert [e.nome for e in r.cadeia] == ["a", "b"]                 # c leu b, b leu a; "ruido" fica fora
