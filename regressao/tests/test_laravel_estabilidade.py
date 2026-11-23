from regressao.laravel import estabilidade as est
from regressao.laravel.caso import _grava_registro, _le_registro, nome_arquivo
from regressao.laravel.mascara import mascara_json


def _reg(id, js, status=200, sql=None):
    return {"id": id, "status": status, "json": js, "cabecalhos": {}, "texto": "", "tipos": {},
            "sql_negocio": sql or [], "tabelas": {}}


def test_caminhos_diferentes_usa_asterisco_para_listas():
    a = {"data": [{"id": 1, "hora": "10:00"}, {"id": 2, "hora": "10:01"}], "ok": True}
    b = {"data": [{"id": 1, "hora": "10:05"}, {"id": 2, "hora": "10:06"}], "ok": True}
    assert est.caminhos_diferentes(a, b) == {"data.*.hora"}
    assert est.caminhos_diferentes(a, a) == set()


def test_chave_que_some_e_lista_de_outro_tamanho_apontam_para_o_no():
    assert est.caminhos_diferentes({"a": 1}, {"a": 1, "b": 2}) == {"b"}
    assert est.caminhos_diferentes({"l": [1, 2]}, {"l": [1]}) == {"l"}


def test_compara_gravacoes_e_sugere_volateis_ou_instaveis(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d, h, n in ((a, "10:00", 1), (b, "10:09", 2)):
        _grava_registro(d / nome_arquivo("rota:GET:/hora"), _reg("rota:GET:/hora", {"hora": h, "x": 1}))
        _grava_registro(d / nome_arquivo("rota:GET:/lista"), _reg("rota:GET:/lista", {"l": list(range(n))}))
        _grava_registro(d / nome_arquivo("rota:GET:/status"), _reg("rota:GET:/status", {}, status=200 + n))
        _grava_registro(d / nome_arquivo("rota:GET:/igual"), _reg("rota:GET:/igual", {"k": 1}))
    difs = est.compara_gravacoes(a, b)
    assert set(difs) == {"rota:GET:/hora", "rota:GET:/lista", "rota:GET:/status"}
    aj = est.sugere_ajustes(difs)
    # lista que muda de tamanho: mascara-se o no inteiro (`l`); so a raiz nao e mascaravel
    assert aj["volateis"] == {"rota:GET:/hora": ["hora"], "rota:GET:/lista": ["l"]}
    assert set(aj["instaveis"]) == {"rota:GET:/status"}
    assert "status" in aj["instaveis"]["rota:GET:/status"]


def test_remascara_equivale_a_gravar_com_volateis(tmp_path):
    cid = "rota:GET:/hora"
    _grava_registro(tmp_path / nome_arquivo(cid), _reg(cid, {"hora": "10:00", "x": 1}))
    assert est.remascara(tmp_path, {cid: ["hora"]}) == 1
    reg = _le_registro(tmp_path / nome_arquivo(cid))   # sha256 refeito: nao levanta
    assert reg["json"] == mascara_json({"hora": "10:00", "x": 1}, ["hora"])
    assert reg["tipos"] == {"hora": ["str"]}
