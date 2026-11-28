"""regressao/rastro/__main__.py `analisa`: um comando que instrumenta (incremental), roda os dois backends e cruza."""
import json

from regressao.rastro import __main__ as M

REL = """# Rastreador

## Defeitos (a resposta final difere): onde o dado se separou

### `t1.php`

**Linha causal:** `x.php:10` - algo
"""


def _falsos(monkeypatch, chamadas):
    monkeypatch.setattr(M, "_instrumenta", lambda forcar=False: chamadas.append("instrumenta") or 0)

    def sondas(telas, saida):
        chamadas.append(("sondas", list(telas)))
        saida.mkdir(parents=True, exist_ok=True)
        (saida / "relatorio.md").write_text(REL, encoding="utf-8")
        return {}

    def xdebug(telas, saida):
        chamadas.append(("xdebug", list(telas)))
        saida.mkdir(parents=True, exist_ok=True)
        (saida / "relatorio.md").write_text(REL, encoding="utf-8")
        return {}
    monkeypatch.setattr(M, "rastreia_telas", sondas)
    monkeypatch.setattr(M, "rastreia_telas_xdebug", xdebug)


def test_analisa_instrumenta_primeiro_roda_os_dois_backends_e_cruza(monkeypatch, tmp_path):
    chamadas = []
    _falsos(monkeypatch, chamadas)
    assert M.main(["analisa", "t1.php", "--saida", str(tmp_path)]) == 0
    assert chamadas == ["instrumenta", ("sondas", ["t1.php"]), ("xdebug", ["t1.php"])]
    assert "mesma-linha" in (tmp_path / "cruzamento" / "cruzamento.tsv").read_text(encoding="utf-8")
    assert (tmp_path / "sondas" / "relatorio.md").exists() and (tmp_path / "xdebug" / "relatorio.md").exists()


def test_analisa_sem_instrumentar_quando_pedido(monkeypatch, tmp_path):
    chamadas = []
    _falsos(monkeypatch, chamadas)
    M.main(["analisa", "t1.php", "--sem-instrumentar", "--saida", str(tmp_path)])
    assert "instrumenta" not in chamadas


def test_de_rodada_sem_area_junta_as_telas_diverge_de_todas_as_areas(tmp_path):
    for area, telas in {"tributario": ["a.php", "b.php"], "financeiro": ["b.php", "c.php"]}.items():
        (tmp_path / area).mkdir()
        (tmp_path / area / "resultado.json").write_text(json.dumps(
            {"casos": [{"id": f"tela:{t}", "veredito": "DIVERGE"} for t in telas] + [{"id": "tela:z.php", "veredito": "IDENTICO"}]}), encoding="utf-8")
    assert M.telas_divergentes(tmp_path, None) == ["a.php", "b.php", "c.php"]
