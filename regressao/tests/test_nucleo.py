from pathlib import Path

from regressao.nucleo.conhecidas import carregar_conhecidas, marcar
from regressao.nucleo.normaliza import hash_corpo, normaliza
from regressao.nucleo.veredito import Caso, Veredito, codigo_saida


def c(id, v):
    return Caso(id=id, area="a", veredito=v)


def test_normaliza_caixa_do_warning_failed_to_open_stream_sem_esconder_o_resto():
    a = b"<b>Warning</b>:  file_put_contents(x): failed to open stream: No such file in <b>/v/D.php</b>"
    b = b"<b>Warning</b>:  file_put_contents(x): Failed to open stream: No such file in <b>/v/D.php</b>"
    assert normaliza(a) == normaliza(b)
    # outro arquivo/erro continua diferente
    assert normaliza(a) != normaliza(b.replace(b"No such file", b"Permission denied"))
    assert normaliza(a) != normaliza(b.replace(b"file_put_contents(x)", b"file_put_contents(y)"))


def test_codigo_saida_zero_sem_divergencia_nova():
    assert codigo_saida([c("1", Veredito.IDENTICO), c("2", Veredito.INCONCLUSIVO)]) == 0


def test_codigo_saida_um_com_diverge_novo():
    assert codigo_saida([c("1", Veredito.IDENTICO), c("2", Veredito.DIVERGE)]) == 1


def test_codigo_saida_ignora_diverge_conhecida():
    k = c("2", Veredito.DIVERGE)
    k.conhecida = True
    assert codigo_saida([c("1", Veredito.IDENTICO), k]) == 0


def test_codigo_saida_dois_com_erro_ambiente():
    casos = [c("1", Veredito.DIVERGE), c("2", Veredito.ERRO_AMBIENTE)]
    assert codigo_saida(casos) == 2


def test_normaliza_troca_sid_nos_dois_lados():
    assert normaliza(b"x?sid=abc12345") == normaliza(b"x?sid=0f0f0f0f")


def test_normaliza_nao_decodifica_latin1():
    assert normaliza(b"a\xe7\xe3o") == b"a\xe7\xe3o"


def test_hash_estavel_e_sensivel_a_um_byte():
    assert hash_corpo(b"abc") == hash_corpo(b"abc")
    assert hash_corpo(b"abc") != hash_corpo(b"abd")
    assert len(hash_corpo(b"abc")) == 64


def test_marcar_so_marca_diverge_listada():
    casos = [c("a", Veredito.DIVERGE), c("b", Veredito.DIVERGE), c("a2", Veredito.IDENTICO)]
    out = marcar(casos, {"a": "motivo", "a2": "x"})
    assert [x.conhecida for x in out] == [True, False, False]


def test_carregar_conhecidas_ignora_comentarios_e_vazias(tmp_path: Path):
    p = tmp_path / "k.tsv"
    p.write_text("# id\tmotivo\n\nx1\tbug antigo\n", encoding="utf-8")
    assert carregar_conhecidas(p) == {"x1": "bug antigo"}


import pytest

# (entrada A, entrada B: so a parte volatil difere, entrada C: diferenca real)
VOLATEIS = [
    (b"x?sid=0123456789ab&a=1", b"x?sid=fedcba987654&a=1", b"x?sid=0123456789ab&a=2"),
    (b"arquivo=QWxhZGRpbjpvcGVu&q", b"arquivo=ZZZZZZZZZZZZZZ==&q", b"arquivo=QWxhZGRpbjpvcGVu&r"),
    (b"w=wname123 ok", b"w=wname98765 ok", b"w=wname123 no"),
    (b"<iframe src=iframeab12.php>", b"<iframe src=iframezz99.php>", b"<iframe src=iframeab12.asp>"),
    (b"t=" + b"a" * 32 + b" z", b"t=" + b"0" * 32 + b" z", b"t=" + b"a" * 32 + b" y"),
    (b'nomeArquivo=a_1.pdf" k', b'nomeArquivo=b_99.pdf" k', b'nomeArquivo=a_1.pdf" j'),
    (b"/tmp/rel_123_45.pdf ok", b"/tmp/rel_999_77.pdf ok", b"/tmp/rel_123_45.pdf no"),
    (b"tmp/arq_17.csv a", b"tmp/arq_99.csv a", b"tmp/arq_17.csv b"),
    (b"tmp/arq_17.txt a", b"tmp/arq_99.txt a", b"tmp/arq_17.txt b"),
    (rb'"tmp\/arq_17.csv" a', rb'"tmp\/arq_99.csv" a', rb'"tmp\/arq_17.csv" b'),
    (b"http://localhost:8080/x", b"http://localhost:8087/x", b"http://localhost:8080/y"),
    (b"/CreationDate (D:20260101120000-03'00') k", b"/CreationDate (D:20271231235959Z) k",
     b"/CreationDate (D:20260101120000-03'00') j"),
    (b"/ModDate(D:20260101120000) k", b"/ModDate (D:20300505050505) k", b"/ModDate(D:20260101120000) j"),
]


@pytest.mark.parametrize("a,b,c", VOLATEIS)
def test_regra_normaliza_parte_volatil(a, b, c):
    assert a != b
    assert normaliza(a) == normaliza(b)
    assert normaliza(a) != normaliza(c)
    assert normaliza(a, regras=[]) != normaliza(b, regras=[])
