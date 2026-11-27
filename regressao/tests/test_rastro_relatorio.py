"""regressao/rastro/relatorio.py e __main__.py (sem docker)."""
import json

from regressao.rastro import __main__ as cli
from regressao.rastro.alinha import Divergencia
from regressao.rastro.classifica import Resultado
from regressao.rastro.evento import Evento
from regressao.rastro.relatorio import escreve_relatorio


def div(**kw):
    base = dict(sonda=3, ocorrencia=0, arquivo="fpdf151/pdf.php", linha=186, tipo="a", nome="x",
                valor_ref={"t": "int", "r": "2"}, valor_alvo={"t": "int", "r": "99"}, motivo="valor", ordem=1)
    return Divergencia(**{**base, **kw})


def test_causal_aparece_com_arquivo_linha_variavel_e_valores(tmp_path):
    causal = div(arquivo="std/DBDate.php", linha=203, nome="mes")
    cadeia = [Evento(1, 2, "std/DBDate.php", 198, "a", "mes", {"t": "string", "r": ""})]
    arq = escreve_relatorio({"con2_anexo_i_2014.php": Resultado("DIVERGE-CAUSAL", causal=causal, cadeia=cadeia)}, tmp_path)
    t = arq.read_text(encoding="utf-8")
    assert "`std/DBDate.php:203`" in t and "`mes`" in t and "int: 2" in t and "int: 99" in t
    assert "`std/DBDate.php:198` `mes`" in t                                           # a cadeia


def test_aviso_x_excecao_e_descrito_com_clareza(tmp_path):
    d = div(arquivo="fpdf151/pdf.php", linha=186, tipo="e", motivo="aviso_x_excecao",
            valor_ref={"t": "aviso", "r": "pg_result(): supplied argument"}, valor_alvo={"t": "excecao", "r": "TypeError: pg_result()"})
    t = escreve_relatorio({"a.php": Resultado("DIVERGE-CAUSAL", causal=d)}, tmp_path).read_text(encoding="utf-8")
    assert "so emite **aviso**" in t and "lanca excecao" in t and "`fpdf151/pdf.php:186`" in t


def test_reconvergente_em_secao_separada_e_truncado_e_inconclusivo(tmp_path):
    rs = {"a.php": Resultado("DIVERGE-RECONVERGENTE", reconvergentes=[div(arquivo="a.php", linha=3)]),
          "b.php": Resultado("INCONCLUSIVO", truncado=True, nota="rastro truncado"),
          "c.php": Resultado("IDENTICO")}
    t = escreve_relatorio(rs, tmp_path).read_text(encoding="utf-8")
    assert t.index("Reconvergentes") < t.index("`a.php`") and "correto" in t
    assert "Inconclusivos (nao contam como aprovados)" in t and "**Rastro truncado**" in t
    assert t.index("Defeitos") if "Defeitos" in t else True


def test_grava_os_rastros_por_tela(tmp_path):
    escreve_relatorio({"a.php": Resultado("IDENTICO")}, tmp_path, {"a.php": {"ref74": ['{"s":1}'], "alvo85": []}})
    assert (tmp_path / "rastro" / "a.php" / "ref74.jsonl").read_text() == '{"s":1}\n'
    assert (tmp_path / "rastro" / "a.php" / "alvo85.jsonl").read_text() == ""


def test_telas_divergentes_le_so_telas_diverge_do_resultado(tmp_path):
    (tmp_path / "saude").mkdir()
    (tmp_path / "saude" / "resultado.json").write_text(json.dumps({"casos": [
        {"id": "tela:b.php", "veredito": "DIVERGE"}, {"id": "tela:a.php", "veredito": "DIVERGE"},
        {"id": "tela:c.php", "veredito": "IDENTICO"}, {"id": "relatorio:r.php", "veredito": "DIVERGE"}]}), encoding="utf-8")
    assert cli.telas_divergentes(tmp_path, "saude") == ["a.php", "b.php"]


def test_cli_rastreia_chama_rastreia_telas(monkeypatch, tmp_path):
    chamadas = []
    monkeypatch.setattr(cli, "rastreia_telas", lambda telas, saida: chamadas.append((telas, saida)))
    assert cli.main(["rastreia", "x.php", "y.php", "--saida", str(tmp_path)]) == 0
    assert chamadas == [(["x.php", "y.php"], tmp_path)]
