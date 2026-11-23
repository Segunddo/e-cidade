from pathlib import Path
from unittest.mock import patch

from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.php import classes
from regressao.php.classes import _parse, roda_classes

from regressao.nucleo.veredito import Veredito
from regressao.php.classes import compara_classes
from regressao.php import sintaxe
from regressao.php.sintaxe import roda_lint


def _rec(cls, campo, valor):
    return f"{cls}\t{campo}\t{valor}\n"


def test_compara_classes_iguais_sao_identicas():
    s = _rec("classes/a.php", "z01_nome", "'ANA'") + _rec("classes/a.php", "z01_numcgm", "'1012'")
    assert [c.veredito for c in compara_classes(s, s)] == [Veredito.IDENTICO]


def test_compara_classes_detecta_zero_vs_valor():
    casos = compara_classes(_rec("classes/a.php", "z01_numcgm", "'1012'"),
                            _rec("classes/a.php", "z01_numcgm", "0"))
    assert len(casos) == 1
    assert casos[0].veredito == Veredito.DIVERGE
    assert "z01_numcgm" in casos[0].detalhe


def test_compara_classes_sem_saida_nos_dois_lados_e_inconclusiva():
    s = "SEM_SAIDA classes/db_x.php\n"
    assert [c.veredito for c in compara_classes(s, s)] == [Veredito.INCONCLUSIVO]


def test_valor_multilinha_nao_cria_classes_falsas():
    s = _rec("classes/a.php", "campos", "'") + "                 z01_numcgm = int4 = Numcgm\n" \
        "                 z01_nome = varchar(40) = Nome\n                 '\n"
    p = _parse(s)
    assert list(p) == ["classes/a.php"] and list(p["classes/a.php"]) == ["campos"]
    assert p["classes/a.php"]["campos"].count("\n") == 3
    assert "                 z01_nome" in p["classes/a.php"]["campos"]
    assert [c.veredito for c in compara_classes(s, s)] == [Veredito.IDENTICO]


def test_fixture_real_multilinha_e_uma_classe_com_um_campo_multilinha():
    s = (Path(__file__).parent / "fixtures" / "escrita_cgm.txt").read_text(encoding="utf-8")
    casos = compara_classes(s, s)
    assert len(casos) == 1 and casos[0].veredito == Veredito.IDENTICO
    assert "z01_numcgm = int4" in _parse(s)["classes/db_cgm_classe.php"]["campos"]


def test_divergencia_no_formato_tab_real():
    a = _rec("classes/a.php", "campos", "'") + "  x = int4\n  '\n"
    b = _rec("classes/a.php", "campos", "'") + "  x = int8\n  '\n"
    casos = compara_classes(a, b)
    assert len(casos) == 1 and casos[0].veredito == Veredito.DIVERGE


def test_sem_saida_em_um_so_runtime_e_diverge():
    casos = compara_classes(_rec("classes/a.php", "x", "1"), "SEM_SAIDA classes/a.php\n")
    assert [c.veredito for c in casos] == [Veredito.DIVERGE]
    casos = compara_classes("SEM_SAIDA classes/a.php\n", _rec("classes/a.php", "x", "1"))
    assert [c.veredito for c in casos] == [Veredito.DIVERGE]


def test_erro_igual_nos_dois_runtimes_e_inconclusivo():
    s = _rec("classes/a.php", "<ERRO>", "Error")
    assert [c.veredito for c in compara_classes(s, s)] == [Veredito.INCONCLUSIVO]
    assert compara_classes(s, _rec("classes/a.php", "<ERRO>", "TypeError"))[0].veredito == Veredito.DIVERGE


def test_roda_classes_copia_scripts_e_compara(tmp_path):
    chamadas = []

    def f(args, timeout, stdin=None, stdout=None):
        chamadas.append(args)
        return _rec("classes/a.php", "x", "1").encode()
    with patch.object(classes, "DESTINO", tmp_path), patch.object(classes, "_docker", f):
        casos = roda_classes(["classes/a.php"])
    assert (tmp_path / "escrita.php").is_file() and (tmp_path / "porclasse.sh").is_file()
    assert len(chamadas) == 2 and [c.veredito for c in casos] == [Veredito.IDENTICO]


def test_roda_classes_falha_de_container_vira_um_erro_ambiente(tmp_path):
    def f(args, timeout, stdin=None, stdout=None):
        raise ErroAmbienteBanco("container caiu")
    with patch.object(classes, "DESTINO", tmp_path), patch.object(classes, "_docker", f):
        casos = roda_classes(["classes/a.php", "classes/b.php"])
    assert len(casos) == 1 and casos[0].veredito == Veredito.ERRO_AMBIENTE


def _fake(resp):
    def f(args, timeout, stdin=None, stdout=None):
        assert stdin is not None  # php -l precisa de stdin fechado
        return resp[args[1]].encode()
    return f


def test_lint_ambos_compilam():
    ok = "No syntax errors detected in a.php\n"
    with patch.object(sintaxe, "_docker", _fake({"ecidade74_php74": ok, "ecidade74_php85": ok})):
        assert roda_lint(["a.php"])[0].veredito == Veredito.IDENTICO


def test_lint_so_85_falha_diverge():
    with patch.object(sintaxe, "_docker", _fake({
            "ecidade74_php74": "No syntax errors detected in a.php\n",
            "ecidade74_php85": "PHP Parse error: syntax error in a.php on line 3\n"})):
        c = roda_lint(["a.php"])[0]
    assert c.veredito == Veredito.DIVERGE and "Parse error" in c.detalhe


def test_lint_ambos_falham_e_inconclusivo():
    err = "PHP Parse error: syntax error in a.php on line 3\n"
    with patch.object(sintaxe, "_docker", _fake({"ecidade74_php74": err, "ecidade74_php85": err})):
        c = roda_lint(["a.php"])[0]
    assert c.veredito == Veredito.INCONCLUSIVO and "Parse error" in c.detalhe
