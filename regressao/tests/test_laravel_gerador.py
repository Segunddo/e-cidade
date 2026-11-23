import json

import pytest
import yaml

from regressao.laravel import cobertura as cob
from regressao.laravel import gerador
from regressao.laravel.caso import CasoHttp, _grava_registro, carrega_casos, nome_arquivo
from regressao.laravel.rotas import Rota, grava_tsv


def _r(metodo, caminho, origem="laravel", mw="api,auth:api", acao="App\\X\\Ctl@acao"):
    return Rota(metodo, caminho, mw.split(",") if mw else [], acao, origem)


# ------------------------------------------------------------ decisao por rota

@pytest.mark.parametrize("uri,esperado", [
    ("/v4/api/a/{id}", True),
    ("/v4/api/a/{id?}", True),
    ("/v4/api/a/{x}/b/{y?}", True),
    ("/v4/api/a/lista", False),
    ("/v4/api/a/lista-x_y", False),
])
def test_detecta_parametro_de_caminho_obrigatorio_e_opcional(uri, esperado):
    assert gerador.tem_parametro(uri) is esperado


def test_rota_com_parametro_nao_e_gerada_e_o_motivo_diz_isso():
    assert "parametro" in gerador.motivo_nao_gerada(_r("GET|HEAD", "/v4/api/a/{id}"))
    assert "parametro" in gerador.motivo_nao_gerada(_r("POST", "/v4/api/a/{id?}"))
    assert gerador.motivo_nao_gerada(_r("GET|HEAD", "/v4/api/a/lista")) is None


@pytest.mark.parametrize("palavra", ["delete", "destroy", "truncate", "reset", "import", "sync",
                                     "logout", "migrate", "excluir"])
def test_rota_perigosa_por_uri_ou_acao_nao_e_gerada(palavra):
    assert "perigosa" in gerador.motivo_nao_gerada(_r("POST", f"/v4/api/x/{palavra}"))
    assert "perigosa" in gerador.motivo_nao_gerada(
        _r("POST", "/v4/api/x/ok", acao=f"App\\Ctl@{palavra.upper()}Tudo"))
    if gerador.PERIGOSA.search(palavra):  # vocabulario do brief vale tambem para GET
        assert "perigosa" in gerador.motivo_nao_gerada(_r("GET|HEAD", f"/v4/api/x/{palavra}"))


def test_get_so_evita_o_vocabulario_do_brief_post_evita_tambem_verbos_de_efeito():
    # verbos de efeito em portugues valem so para quem escreve (POST/PUT/DELETE)
    assert gerador.motivo_nao_gerada(_r("GET|HEAD", "/v4/api/x/processar")) is None
    assert "perigosa" in gerador.motivo_nao_gerada(_r("POST", "/v4/api/x/processar"))
    assert "perigosa" in gerador.motivo_nao_gerada(_r("POST", "/v4/api/x/cancelar"))


def test_metodo_efetivo():
    assert gerador.metodo_efetivo("GET|HEAD") == "GET"
    assert gerador.metodo_efetivo("GET") == "GET"
    assert gerador.metodo_efetivo("PUT|PATCH") == "PUT"
    assert gerador.metodo_efetivo("POST") == "POST"
    assert gerador.metodo_efetivo("DELETE") == "DELETE"


def test_caso_get_autenticado_sem_corpo_e_post_com_corpo_vazio_sem_escrita():
    g = gerador.caso_para(_r("GET|HEAD", "/v4/api/a/lista"), {})
    assert (g.id, g.metodo, g.caminho, g.corpo) == ("rota:GET:/v4/api/a/lista", "GET", "/v4/api/a/lista", None)
    assert g.autenticado and g.token is None and g.campos_volateis == [] and not g.espera_escrita
    p = gerador.caso_para(_r("POST", "/v4/api/a/salvar"), {})
    assert (p.id, p.metodo, p.corpo) == ("rota:POST:/v4/api/a/salvar", "POST", {})
    assert p.espera_escrita is False and p.autenticado


def test_silex_nao_usa_bearer():
    c = gerador.caso_para(_r("GET", "/api/v1/protocolo/cgm", origem="silex", mw="silex"), {})
    assert c.autenticado is False


def test_ajuste_de_volateis_vem_do_arquivo_de_ajustes():
    c = gerador.caso_para(_r("GET|HEAD", "/v4/api/a/lista"),
                          {"volateis": {"rota:GET:/v4/api/a/lista": ["data.*.hora"]}})
    assert c.campos_volateis == ["data.*.hora"]


# ------------------------------------------------------------ geracao e determinismo

ROTAS = [
    _r("POST", "/v4/api/z/salvar"),
    _r("GET|HEAD", "/v4/api/b/lista"),
    _r("GET|HEAD", "/v4/api/a/lista"),
    _r("GET|HEAD", "/v4/api/a/{id}"),
    _r("DELETE", "/v4/api/a/{id}"),
    _r("POST", "/v4/api/a/excluir"),
    _r("POST", "/v4/api/p"),
    _r("GET", "/api/v1/protocolo/cgm", origem="silex", mw="silex"),
    _r("GET|HEAD", "/rest/v1/pessoa/{cpf}", origem="rest", mw="AuthSim"),
]


def test_gera_ordem_ordenada_por_uri_e_metodo_por_origem():
    g = gerador.gera(ROTAS)
    assert [c.id for c in g["laravel"]] == [
        "rota:GET:/v4/api/a/lista", "rota:GET:/v4/api/b/lista",
        "rota:POST:/v4/api/p", "rota:POST:/v4/api/z/salvar"]
    assert [c.id for c in g["silex"]] == ["rota:GET:/api/v1/protocolo/cgm"]
    assert g["rest"] == []


def test_nao_cobertas_listam_motivo():
    nc = gerador.nao_geradas(ROTAS)
    assert {(r.metodo, r.caminho) for r, _ in nc} == {
        ("GET|HEAD", "/v4/api/a/{id}"), ("DELETE", "/v4/api/a/{id}"),
        ("POST", "/v4/api/a/excluir"), ("GET|HEAD", "/rest/v1/pessoa/{cpf}")}


def test_instaveis_vao_para_arquivo_proprio_com_motivo(tmp_path):
    ajustes = {"instaveis": {"rota:GET:/v4/api/b/lista": "contador a cada chamada"}}
    arqs = gerador.escreve(tmp_path, ROTAS, ajustes)
    nomes = {a.name for a in arqs}
    assert nomes == {"rotas_laravel.yml", "rotas_rest.yml", "rotas_silex.yml", "_instaveis.yml"}
    texto = (tmp_path / "_instaveis.yml").read_text(encoding="utf-8")
    assert "contador a cada chamada" in texto and "rota:GET:/v4/api/b/lista" in texto
    # nao carregado por padrao, e fora de rotas_laravel
    assert "rota:GET:/v4/api/b/lista" not in {c.id for c in carrega_casos(tmp_path)}
    assert "rota:GET:/v4/api/a/lista" in {c.id for c in carrega_casos(tmp_path)}


def test_geracao_e_idempotente_byte_a_byte(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    gerador.escreve(a, ROTAS, {})
    gerador.escreve(b, list(reversed(ROTAS)), {})   # ordem de entrada nao importa
    gerador.escreve(a, ROTAS, {})                   # re-executar nao muda
    for arq in sorted(a.iterdir()):
        assert arq.read_bytes() == (b / arq.name).read_bytes(), arq.name
    assert b"\r" not in (a / "rotas_laravel.yml").read_bytes()


def test_yaml_gerado_volta_igual_por_carrega_casos(tmp_path):
    gerador.escreve(tmp_path, ROTAS, {"volateis": {"rota:GET:/v4/api/a/lista": ["data.*.t"]}})
    lidos = {c.id: c for c in carrega_casos(tmp_path)}
    esperados = {c.id: c for lista in gerador.gera(
        ROTAS, {"volateis": {"rota:GET:/v4/api/a/lista": ["data.*.t"]}}).values() for c in lista}
    assert lidos == esperados
    assert lidos["rota:POST:/v4/api/z/salvar"].corpo == {}
    assert lidos["rota:GET:/api/v1/protocolo/cgm"].autenticado is False


def test_nome_de_arquivo_da_baseline_e_seguro_e_injetivo():
    a = nome_arquivo("rota:GET:/v4/api/a/lista")
    assert "/" not in a and ":" not in a and a.endswith(".json")
    assert nome_arquivo("rota:GET:/v4/api/a/lista") != nome_arquivo("rota:GET:/v4/api/a-lista")
    assert nome_arquivo("auth-sem-token") == "auth-sem-token.json"


def test_inventario_real_gera_so_rotas_sem_parametro_e_nada_perigoso():
    rotas = gerador.le_inventario()
    g = gerador.gera(rotas)
    todos = [c for lista in g.values() for c in lista]
    assert todos, "inventario real sem casos"
    assert all("{" not in c.caminho for c in todos)
    assert not any(gerador.PERIGOSA.search(c.caminho) for c in todos)
    assert len({c.id for c in todos}) == len(todos)
    assert all(c.metodo in ("GET", "POST", "PUT", "PATCH", "DELETE") for c in todos)
    # nenhuma rota fica sem destino: gerada ou listada com motivo
    nc = gerador.nao_geradas(rotas)
    # (HEAD nao e expandido; PUT|PATCH vira um caso) => conta por rota
    assert len(todos) + len(nc) == len(rotas)


# ------------------------------------------------------------ cobertura

def _grava_baseline(dir, caso, status):
    _grava_registro(dir / nome_arquivo(caso.id), {"id": caso.id, "status": status, "json": {},
                                                  "cabecalhos": {}, "texto": "", "tipos": {},
                                                  "sql_negocio": [], "tabelas": {}})


def test_cobertura_conta_origem_cobertas_nao_cobertas_e_classes(tmp_path):
    rotas = [r for r in ROTAS] + [_r("POST", "/v4/oauth/token", mw="")]
    inv = tmp_path / "inv.tsv"
    grava_tsv(rotas, inv)
    casos = [c for lista in gerador.gera(rotas).values() for c in lista]
    status = {"rota:GET:/v4/api/a/lista": 200, "rota:GET:/v4/api/b/lista": 500,
              "rota:POST:/v4/api/p": 422, "rota:POST:/v4/api/z/salvar": 406,
              "rota:GET:/api/v1/protocolo/cgm": 403, "rota:POST:/v4/oauth/token": 400}
    base = tmp_path / "base"
    for c in casos:
        _grava_baseline(base, c, status[c.id])
    rel = cob.cobertura_rotas(gerador.le_inventario(inv), casos, base)
    assert rel["total"] == len(rotas)
    assert rel["por_origem"]["laravel"]["total"] == 8 and rel["por_origem"]["silex"]["total"] == 1
    assert rel["por_origem"]["laravel"]["cobertas"] == 5   # a/lista b/lista p salvar token
    assert rel["por_origem"]["rest"] == {"total": 1, "cobertas": 0, "nao_cobertas": 1}
    assert rel["classes"] == {"2xx": 1, "3xx": 0, "4xx": 4, "5xx": 1, "sem_baseline": 0}
    assert rel["inconclusivos_5xx"] == ["rota:GET:/v4/api/b/lista"]
    motivos = {(n["metodo"], n["uri"]): n["motivo"] for n in rel["nao_cobertas"]}
    assert "parametro" in motivos[("GET|HEAD", "/v4/api/a/{id}")]
    assert "perigosa" in motivos[("POST", "/v4/api/a/excluir")]


def test_cobertura_escreve_json_e_md_sem_segredo(tmp_path):
    rotas = [_r("GET|HEAD", "/v4/api/a/lista"), _r("GET|HEAD", "/v4/api/a/{id}")]
    casos = gerador.gera(rotas)["laravel"]
    _grava_baseline(tmp_path, casos[0], 500)
    rel = cob.cobertura_rotas(rotas, casos, tmp_path)
    cob.escreve_cobertura(rel, tmp_path)
    j = json.loads((tmp_path / "_cobertura.json").read_text(encoding="utf-8"))
    assert j["classes"]["5xx"] == 1
    md = (tmp_path / "_cobertura.md").read_text(encoding="utf-8")
    assert "INCONCLUSIVO" in md and "5xx" in md and "/v4/api/a/{id}" in md


def test_cobertura_sem_baseline_conta_a_parte(tmp_path):
    rotas = [_r("GET|HEAD", "/v4/api/a/lista")]
    rel = cob.cobertura_rotas(rotas, gerador.gera(rotas)["laravel"], tmp_path)
    assert rel["classes"]["sem_baseline"] == 1 and rel["classes"]["2xx"] == 0


def test_ajustes_yml_real_e_valido():
    aj = gerador.le_ajustes()
    assert set(aj) <= {"volateis", "instaveis", "perigosas", "sem_ordem"}
    for chave in ("volateis", "sem_ordem"):
        for caminhos in (aj.get(chave) or {}).values():
            assert isinstance(caminhos, list)
    assert isinstance(yaml.safe_dump(aj), str)


def test_sonda_que_escreveu_ao_vivo_deixa_de_ser_gerada_e_vira_nao_coberta():
    aj = {"perigosas": {"rota:POST:/v4/api/z/salvar": "update db_config com corpo vazio"}}
    g = gerador.gera(ROTAS, aj)
    assert "rota:POST:/v4/api/z/salvar" not in [c.id for c in g["laravel"]]
    motivos = {r.caminho: m for r, m in gerador.nao_geradas(ROTAS, aj)}
    assert "provada ao vivo" in motivos["/v4/api/z/salvar"] and "db_config" in motivos["/v4/api/z/salvar"]
    rel = cob.cobertura_rotas(ROTAS, [c for l in g.values() for c in l], "/nao/existe", aj)
    assert any(n["uri"] == "/v4/api/z/salvar" and "perigosa" in n["motivo"] for n in rel["nao_cobertas"])
