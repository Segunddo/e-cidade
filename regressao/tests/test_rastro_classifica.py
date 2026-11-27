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
