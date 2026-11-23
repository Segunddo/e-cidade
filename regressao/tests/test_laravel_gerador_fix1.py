"""Fix round 1 da Task 11a: allowlist de metodos destrutivos e cobertura por razao."""
import pytest

from regressao.laravel import cobertura as cob
from regressao.laravel import gerador
from regressao.laravel.caso import CasoHttp, _grava_registro, nome_arquivo
from regressao.laravel.rotas import Rota


def _r(metodo, caminho, origem="laravel", mw="api,auth:api", acao="App\\X\\Ctl@acao"):
    return Rota(metodo, caminho, mw.split(","), acao, origem)


@pytest.mark.parametrize("metodo", ["DELETE", "PUT|PATCH", "PUT", "PATCH"])
def test_metodo_destrutivo_nao_e_gerado_sem_allowlist(metodo):
    r = _r(metodo, "/v4/api/x/lista")
    assert "metodo destrutivo sem allowlist" in gerador.motivo_nao_gerada(r)
    assert gerador.gera([r])["laravel"] == []
    id_ = gerador.id_do_caso(r)
    assert gerador.motivo_nao_gerada(r, {"permitidas": [id_]}) is None
    assert [c.id for c in gerador.gera([r], {"permitidas": [id_]})["laravel"]] == [id_]


def test_post_e_get_seguem_gerados():
    assert gerador.motivo_nao_gerada(_r("POST", "/v4/api/x/salvar")) is None
    assert gerador.motivo_nao_gerada(_r("GET|HEAD", "/v4/api/x/lista")) is None


def test_inventario_real_nao_gera_delete_put_patch():
    g = gerador.gera(gerador.le_inventario())
    assert not [c for l in g.values() for c in l if c.metodo in ("DELETE", "PUT", "PATCH")]


def _base(dir, id_, status):
    _grava_registro(dir / nome_arquivo(id_), {"id": id_, "status": status, "json": {}, "cabecalhos": {},
                                              "texto": "", "tipos": {}, "sql_negocio": [], "tabelas": {}})


def test_cobertura_separa_inconclusivos_por_razao(tmp_path):
    rotas = [_r("GET|HEAD", "/v4/api/a"), _r("GET|HEAD", "/v4/api/b"), _r("PUT|PATCH", "/v4/api/c")]
    casos = [CasoHttp(id="rota:GET:/v4/api/a", metodo="GET", caminho="/v4/api/a", corpo=None),
             CasoHttp(id="rota:GET:/v4/api/b", metodo="GET", caminho="/v4/api/b", corpo=None),
             CasoHttp(id="auth-x", metodo="GET", caminho="/v4/api/b", corpo=None, espera_status=500)]
    for c, s in zip(casos, (500, 200, 500)):
        _base(tmp_path, c.id, s)
    rel = cob.cobertura_rotas(rotas, casos, tmp_path, {})
    assert rel["casos"]["total"] == 3 and rel["casos"]["5xx"] == 2
    assert rel["casos"]["inconclusivos_5xx"] == ["rota:GET:/v4/api/a"]
    assert rel["casos"]["rejeicao_esperada_5xx"] == ["auth-x"]
    assert rel["inconclusivos_5xx"] == ["rota:GET:/v4/api/a"]
    assert any("destrutivo" in n["motivo"] for n in rel["nao_cobertas"])
    assert rel["notas"]["metodos_colapsados"] == 0
    md = cob.escreve_cobertura(rel, tmp_path) or (tmp_path / "_cobertura.md").read_text(encoding="utf-8")
    assert "rejeicao esperada" in md and "INCONCLUSIVO" in md
