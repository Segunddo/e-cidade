import io
from pathlib import Path
from unittest.mock import patch

import openpyxl
import pytest

from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.veredito import Veredito
from regressao.php import relatorios
from regressao.php.relatorios import RelCaso, carrega_catalogo_relatorios, compara_relatorio, extrai_conteudo, roda_relatorio

FIX = Path(__file__).parent / "fixtures"
PDF = RelCaso("cem2_x.php", "cod=1", "pdf", "cemiterio", True)
XLS = RelCaso("con2_x.php", "a=1", "xls", "contabil", True)
HTML = RelCaso("cad3_x.php", "", "html", "cadastro", True)


def xlsx(celulas: dict[str, object], aba: str = "Plan1") -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = aba
    for ref, v in celulas.items():
        ws[ref] = v
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_pdf_com_metadado_diferente_e_identico_pelo_conteudo():
    a = (FIX / "relatorio_a.pdf").read_bytes()
    b = (FIX / "relatorio_b.pdf").read_bytes()
    assert a != b and b"20260101" in a and b"20261114" in b  # bytes e metadados diferem
    c = compara_relatorio(a, b, PDF)
    assert c.veredito == Veredito.IDENTICO
    assert "100,00" in extrai_conteudo(a, "pdf")


def test_pdf_com_texto_diferente_diverge():
    a = (FIX / "relatorio_a.pdf").read_bytes()
    c = (FIX / "relatorio_c.pdf").read_bytes()
    r = compara_relatorio(a, c, PDF)
    assert r.veredito == Veredito.DIVERGE
    assert "-Relatorio de teste 100,00" in r.diff and "+Relatorio de teste 200,00" in r.diff


def test_xls_celula_diferente_diverge():
    a = xlsx({"A1": "Nome", "B1": 10, "A2": "Ana", "B2": 5})
    b = xlsx({"A1": "Nome", "B1": 10, "A2": "Ana", "B2": 6})
    r = compara_relatorio(a, b, XLS)
    assert r.veredito == Veredito.DIVERGE
    assert "Plan1|2|2|5" in r.diff and "Plan1|2|2|6" in r.diff
    assert "Plan1|2|1|Ana" in extrai_conteudo(a, "xls")


def test_xls_bytes_diferentes_mesmas_celulas_e_identico():
    a = xlsx({"A1": "x", "B1": 1})
    b = xlsx({"A1": "x", "B1": 1})
    assert compara_relatorio(a, b, XLS).veredito == Veredito.IDENTICO


def test_xls_html_ou_csv_servido_como_excel():
    tabela = b"<table><tr><td>Jos\xe9</td><td>1</td></tr></table>"
    assert "Jos\xe9" in extrai_conteudo(tabela, "xls")  # latin-1, nunca utf-8
    csv = "nome;valor\nJos\xe9;1\n".encode("latin-1")
    assert extrai_conteudo(csv, "xls") == "csv|1|1|nome\ncsv|1|2|valor\ncsv|2|1|Jos\xe9\ncsv|2|2|1"
    assert compara_relatorio(csv, csv, XLS).veredito == Veredito.IDENTICO


def test_html_e_doc_decodificam_latin1_e_normalizam():
    a = b"<p>A\xe7\xe3o</p><a href='x.php?sid=" + b"a" * 20 + b"'>"
    b = b"<p>A\xe7\xe3o</p><a href='x.php?sid=" + b"b" * 20 + b"'>"
    assert "A\xe7\xe3o" in extrai_conteudo(a, "html")
    assert compara_relatorio(a, b, HTML).veredito == Veredito.IDENTICO
    assert extrai_conteudo(a, "doc") == extrai_conteudo(a, "html")


def test_relatorio_vazio_e_inconclusivo():
    assert compara_relatorio(b"", b"", HTML).veredito == Veredito.INCONCLUSIVO
    assert compara_relatorio(b" \n", b"\n", HTML).veredito == Veredito.INCONCLUSIVO
    vazio_xlsx = xlsx({})
    assert compara_relatorio(vazio_xlsx, vazio_xlsx, XLS).veredito == Veredito.INCONCLUSIVO
    pdf_sem_texto = (FIX / "relatorio_a.pdf").read_bytes().replace(b"Tj", b"  ")
    assert extrai_conteudo(pdf_sem_texto, "pdf") == ""
    assert compara_relatorio(pdf_sem_texto, pdf_sem_texto, PDF).veredito == Veredito.INCONCLUSIVO
    # um lado vazio e o outro nao: divergencia real
    assert compara_relatorio(b"", b"<p>x</p>", HTML).veredito == Veredito.DIVERGE


def test_pdf_que_nao_e_pdf_nao_aprova():
    erro = b"<b>Fatal error</b>: Call to undefined function"
    assert compara_relatorio(erro, erro, PDF).veredito == Veredito.INCONCLUSIVO
    pdf = (FIX / "relatorio_a.pdf").read_bytes()
    assert compara_relatorio(pdf, erro, PDF).veredito == Veredito.DIVERGE
    assert compara_relatorio(erro, erro, HTML).veredito == Veredito.INCONCLUSIVO  # erro PHP igual nos dois lados


def test_sessao_invalida_e_erro_ambiente():
    morta = b"Sess\xe3o inv\xe1lida (12). Feche seu navegador e fa\xe7a login novamente."
    ok = (FIX / "relatorio_a.pdf").read_bytes()
    assert compara_relatorio(morta, morta, HTML).veredito == Veredito.ERRO_AMBIENTE
    assert compara_relatorio(ok, morta, PDF).veredito == Veredito.ERRO_AMBIENTE
    assert compara_relatorio(morta, ok, PDF).veredito == Veredito.ERRO_AMBIENTE


def test_diff_e_limitado():
    a = "\n".join(f"<p>linha {i} a</p>" for i in range(1000)).encode()
    b = "\n".join(f"<p>linha {i} b</p>" for i in range(1000)).encode()
    r = compara_relatorio(a, b, HTML)
    assert r.veredito == Veredito.DIVERGE
    linhas = r.diff.splitlines()
    assert len(linhas) <= 202 and "omitidas" in linhas[-1]


def test_catalogo_relatorios_exige_quinta_coluna(tmp_path):
    ok = tmp_path / "ok.tsv"
    ok.write_text("# c\n\ncem2_renovacoes.php\tcod=1\tpdf\tcemiterio\tverificado\n"
                  "cad3_x.php\t\thtml\tcadastro\tnao-verificado\n", encoding="utf-8")
    casos = carrega_catalogo_relatorios(ok)
    assert casos == [RelCaso("cem2_renovacoes.php", "cod=1", "pdf", "cemiterio", True),
                     RelCaso("cad3_x.php", "", "html", "cadastro", False)]
    for ruim in ["a.php\tq=1\tpdf\tarea\n",                    # sem 5a coluna
                 "a.php\tq=1\tpdf\tarea\tok\n",                # status invalido
                 "a.php\tq=1\tzip\tarea\tverificado\n",        # tipo invalido
                 "a\tq=1\tpdf\tarea\tverificado\n"]:           # tela sem .php
        arq = tmp_path / "ruim.tsv"
        arq.write_text("a.php\tq=1\tpdf\tarea\tverificado\n" + ruim, encoding="utf-8")
        with pytest.raises(ValueError, match="linha 2"):
            carrega_catalogo_relatorios(arq)


ACHADOS = {"mat2_cadunidade002.php", "prot2_cadcgm002.php", "con2_relinstituicoes002.php",
           "con2_conhist002.php", "con2_conhistdoc002.php", "con2_balancrece002.php"}


def test_catalogo_semeado_carrega():
    casos = carrega_catalogo_relatorios(relatorios.CATALOGO)
    assert all(c.tipo in ("html", "pdf", "xls", "doc") for c in casos)
    assert len(casos) == 42
    # reverificado ao vivo na referencia 7.4 (2026-11-18): os 3 db_download.php dao 302 (o CSV nao existe em tmp/ da base
    # 7.4) e orc2_despsecretaria002 da 500 na propria referencia; func_cgm so devolve a pagina de pesquisa
    assert sum(c.verificado for c in casos) == 37
    assert {c.tela for c in casos if not c.verificado} == {"func_cgm.php", "db_download.php", "orc2_despsecretaria002.php"}
    assert len([c for c in casos if not c.verificado and c.tela == "db_download.php"]) == 3
    assert {c.tela for c in casos if c.verificado} >= ACHADOS


def test_roda_relatorio_restaura_sessao_antes_de_cada_runtime():
    chamadas = []
    pdf = (FIX / "relatorio_a.pdf").read_bytes()
    with patch.object(relatorios, "restaura_sessao", side_effect=lambda sid: chamadas.append(("restaura", sid))), \
         patch.object(relatorios, "_requisita_status",
                      side_effect=lambda sid, url, container: chamadas.append((container, url)) or (200, pdf)):
        c = roda_relatorio("sid1", PDF)
    assert c.veredito == Veredito.IDENTICO and c.id == "cem2_x.php?cod=1"
    assert chamadas == [("restaura", "sid1"), ("ecidade74_php74", "cem2_x.php?cod=1"),
                        ("restaura", "sid1"), ("ecidade74_php85", "cem2_x.php?cod=1")]


def test_roda_relatorio_nao_verificado_e_erro_de_docker():
    nv = RelCaso("a.php", "", "html", "x", False)
    with patch.object(relatorios, "restaura_sessao"), \
         patch.object(relatorios, "_requisita_status", return_value=(200, b"<p>dados</p>")):
        c = roda_relatorio("s", nv)
    assert c.veredito == Veredito.IDENTICO and c.detalhe.startswith("[nao-verificado]")
    with patch.object(relatorios, "restaura_sessao", side_effect=ErroAmbienteBanco("docker caiu")):
        c = roda_relatorio("s", nv)
    assert c.veredito == Veredito.ERRO_AMBIENTE and "docker caiu" in c.detalhe


def test_pdf_ignora_hora_de_emissao_do_rodape():
    a = (FIX / "rodape_a.pdf").read_bytes()
    b = (FIX / "rodape_b.pdf").read_bytes()
    assert a != b and "Total 5" in extrai_conteudo(a, "pdf")
    assert compara_relatorio(a, b, PDF).veredito == Veredito.IDENTICO


PAGINA_500 = ("<html><title>Notifica\xe7\xe3o do Sistema</title><p class='notification'>Erro interno</p></html>"
              ).encode("latin-1")


def test_um_lado_200_e_outro_500_e_diverge_com_codigos():
    pdf = (FIX / "relatorio_a.pdf").read_bytes()
    r = compara_relatorio(pdf, PAGINA_500, PDF, 200, 500)
    assert r.veredito == Veredito.DIVERGE
    assert "ref=200" in r.detalhe and "8.5=500" in r.detalhe and "%PDF" in r.detalhe
    assert "Erro interno" in r.diff
    with patch.object(relatorios, "restaura_sessao"), \
         patch.object(relatorios, "_requisita_status", side_effect=[(200, pdf), (500, PAGINA_500)]):
        assert roda_relatorio("s", PDF).veredito == Veredito.DIVERGE


def test_mesmo_500_nos_dois_lados_e_inconclusivo_para_html():
    r = compara_relatorio(b"<p>falhou</p>", b"<p>falhou</p>", HTML, 500, 500)
    assert r.veredito == Veredito.INCONCLUSIVO and "ambos 500" in r.detalhe


def test_pagina_notificacao_do_sistema_nos_dois_lados_e_inconclusiva():
    for caso in (HTML, XLS, RelCaso("a.php", "", "doc", "x")):
        assert compara_relatorio(PAGINA_500, PAGINA_500, caso).veredito == Veredito.INCONCLUSIVO


def test_pdf_ilegivel_identico_e_inconclusivo():
    lixo = b"%PDF-1.4\nisto nao e um pdf valido\n"
    assert extrai_conteudo(lixo, "pdf").startswith("<<pdf ilegivel")
    r = compara_relatorio(lixo, lixo, PDF)
    assert r.veredito == Veredito.INCONCLUSIVO and "ilegivel" in r.detalhe


def test_pdf_ilegivel_so_de_um_lado_diverge():
    lixo = b"%PDF-1.4\nisto nao e um pdf valido\n"
    ok = (FIX / "relatorio_a.pdf").read_bytes()
    assert compara_relatorio(ok, lixo, PDF).veredito == Veredito.DIVERGE
    assert compara_relatorio(lixo, ok, PDF).veredito == Veredito.DIVERGE


def test_requisita_status_separa_trailer_sem_perder_bytes():
    from regressao.php import telas
    corpo = b"%PDF\x00\xff\n@@ nao e trailer\n"
    with patch.object(telas, "_docker", return_value=corpo + b"\n@@500"):
        assert telas._requisita_status("s", "a.php") == (500, corpo)
    with patch.object(telas, "_docker", return_value=b"truncado sem trailer"):
        assert telas._requisita_status("s", "a.php") == (0, b"truncado sem trailer")
