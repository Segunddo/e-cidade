"""Bateria Laravel sobre a base 7.4 (referencia Laravel 8.73/Passport 10, ambiente e74).

Inventario pelo `route:list --json` do Laravel 8 (com alternativa tolerante quando um controller da propria
referencia nao instancia), containers e URLs so de `nucleo/ambiente.py`, console artisan do Laravel 8 e o
container de log/console que acompanha o alvo (nunca a referencia quando o alvo e outro)."""
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from regressao.laravel import bateria, cobertura, gerador, integracao, rotas, token
from regressao.nucleo import ambiente
from regressao.nucleo.banco import ErroAmbienteBanco

FIXTURES = Path(__file__).parent / "fixtures"
DIR_LARAVEL = Path(__file__).resolve().parents[1] / "laravel"
_VARS = ("REGRESSAO_REF_URL", "REGRESSAO_PHP_NOVO_URL", "REGRESSAO_NOVO_URL", "REGRESSAO_LARAVEL_NOVO_URL",
         "REGRESSAO_PROXY_URL", "REGRESSAO_CONTAINER_REF", "REGRESSAO_CONTAINER_PHP_NOVO",
         "REGRESSAO_CONTAINER_BANCO", "REGRESSAO_CONTAINER_PROXY", "REGRESSAO_CONTAINER_LARAVEL_NOVO",
         "REGRESSAO_LARAVEL_CONSOLE_CONTAINER")


@pytest.fixture
def limpo(monkeypatch):
    for v in _VARS:
        monkeypatch.delenv(v, raising=False)
    return monkeypatch


# ------------------------------------------------------------------ ambiente

def test_container_do_laboratorio_laravel_vem_do_ambiente(limpo):
    assert ambiente.containers_do_ambiente().laravel_novo == "ecidade74_lar12"
    limpo.setenv("REGRESSAO_CONTAINER_LARAVEL_NOVO", "meu_lab")
    assert ambiente.containers_do_ambiente().laravel_novo == "meu_lab"


def test_container_do_alvo_mapeia_url_para_container(limpo):
    assert ambiente.container_do_alvo("http://localhost:8074/") == "ecidade74_php74"
    assert ambiente.container_do_alvo("http://localhost:8185") == "ecidade74_php85"
    assert ambiente.container_do_alvo("http://localhost:8187") == "ecidade74_lar12"
    assert ambiente.container_do_alvo("http://localhost:8190") is None   # nginx: nao roda PHP
    assert ambiente.container_do_alvo("http://outro:1") is None
    limpo.setenv("REGRESSAO_LARAVEL_NOVO_URL", "http://lab:9")
    limpo.setenv("REGRESSAO_CONTAINER_LARAVEL_NOVO", "c_lab")
    assert ambiente.container_do_alvo("http://lab:9") == "c_lab"


def test_nenhum_nome_da_pilha_antiga_no_codigo_laravel():
    for arq in sorted(DIR_LARAVEL.glob("*.py")):
        texto = arq.read_text(encoding="utf-8")
        assert not re.search(r"ecidade_(php56|php85|database|lar12)|\bCONTAINER_PHP\b|php_56|localhost:80(80|85|87|90)\b",
                             texto), arq.name


# ------------------------------------------------------------------ inventario (route:list --json)

def test_parseia_route_list_json_do_laravel_8():
    lista = rotas.parseia_route_list_json((FIXTURES / "route_list_l8.json").read_text(encoding="utf-8"))
    assert len(lista) == 8
    por_uri = {(r.metodo, r.caminho): r for r in lista}
    r = por_uri[("GET|HEAD", "/rest/v1/enderecopessoa/{cgm}")]
    assert r.origem == "rest" and r.middleware == ["AuthSim"] and r.controller.endswith("PessoasController@pesquisaEndereco")
    clos = por_uri[("GET|HEAD", "/v4/api/saude/ambulatorial/cid")]
    assert clos.controller == "Closure" and clos.middleware == ["api", "auth:api"] and clos.origem == "laravel"
    assert por_uri[("GET|HEAD", "/v4/api/configuracao/assinantes")].middleware == []
    assert por_uri[("GET|HEAD", "/v4/oauth/authorize")].controller.startswith("Laravel\\Passport\\")
    assert all(r.erro == "" for r in lista)


def test_parseia_route_list_json_guarda_erro_do_controller():
    texto = json.dumps([{"domain": None, "method": "POST", "uri": "v4/api/a/salvar", "name": None,
                         "action": "App\\A@salvar", "middleware": "api",
                         "erro": "Error: Class 'X'\tnot found\nlinha 2"}])
    r = rotas.parseia_route_list_json(texto)[0]
    assert r.erro.startswith("Error: Class 'X'") and "\t" not in r.erro and "\n" not in r.erro


def test_parseia_route_list_json_recusa_saida_que_nao_e_lista():
    with pytest.raises(rotas.ErroInventario):
        rotas.parseia_route_list_json("In Foo.php line 20: Class not found")
    with pytest.raises(rotas.ErroInventario):
        rotas.parseia_route_list_json('{"a": 1}')


def _ok(stdout: bytes, rc: int = 0, stderr: bytes = b""):
    return SimpleNamespace(returncode=rc, stdout=stdout, stderr=stderr)


def test_rotas_laravel_usa_route_list_json_no_container_de_referencia(limpo):
    vistos = []
    corpo = (FIXTURES / "route_list_l8.json").read_bytes()

    def runner(cmd, entrada=None):
        vistos.append((cmd, entrada))
        return _ok(corpo)
    lista, fonte = rotas.rotas_laravel(runner=runner)
    assert len(lista) == 8 and fonte == "route:list --json"
    cmd = vistos[0][0]
    assert cmd[:2] == ["docker", "exec"] and "ecidade74_php74" in cmd
    assert cmd[-4:] == ["php", "artisan", "route:list", "--json"]
    limpo.setenv("REGRESSAO_CONTAINER_REF", "outra_ref")
    rotas.rotas_laravel(runner=runner)
    assert "outra_ref" in vistos[-1][0]


def test_rotas_laravel_cai_na_listagem_tolerante_quando_um_controller_da_referencia_quebra(limpo):
    vistos = []
    tolerante = json.dumps([{"domain": None, "method": "GET|HEAD", "uri": "v4/api/ok", "name": None,
                             "action": "App\\Ok@index", "middleware": "api\nauth:api", "erro": None},
                            {"domain": None, "method": "GET|HEAD", "uri": "v4/api/quebrada", "name": None,
                             "action": "App\\Q@index", "middleware": "api",
                             "erro": "Error: Class 'Repo' not found"}]).encode()

    def runner(cmd, entrada=None):
        vistos.append((cmd, entrada))
        if "route:list" in cmd:
            return _ok(b"", 1, b"In Ctl.php line 20: Class 'Repo' not found")
        return _ok(tolerante)
    lista, fonte = rotas.rotas_laravel(runner=runner)
    assert fonte.startswith("tolerante")
    assert [r.caminho for r in lista] == ["/v4/api/ok", "/v4/api/quebrada"]
    assert lista[1].erro == "Error: Class 'Repo' not found" and lista[0].erro == ""
    cmd, entrada = vistos[1]
    assert cmd[:3] == ["docker", "exec", "-i"] and "ecidade74_php74" in cmd and cmd[-1] != "artisan"
    assert b"gatherRouteMiddleware" in entrada and b"getActionName" in entrada   # mesmo formato do route:list


def test_rotas_laravel_sem_nenhuma_listagem_levanta_erro(limpo):
    with pytest.raises(rotas.ErroInventario):
        rotas.rotas_laravel(runner=lambda cmd, entrada=None: _ok(b"", 255, b"Fatal"))


def test_tsv_guarda_o_erro_do_controller_e_le_os_dois_formatos(tmp_path):
    lista = [rotas.Rota("GET|HEAD", "/v4/api/b", ["api"], "App\\B@i", "laravel", "Error: Class 'X' not found"),
             rotas.Rota("POST", "/v4/api/a", ["api", "auth:api"], "App\\A@s", "laravel")]
    arq = tmp_path / "inv.tsv"
    rotas.grava_tsv(lista, arq)
    linhas = arq.read_text(encoding="utf-8").splitlines()
    assert linhas[0].split("\t") == ["metodo", "uri", "middleware", "action", "origem", "erro_controller"]
    lidas = gerador.le_inventario(arq)
    assert {r.caminho: r.erro for r in lidas} == {"/v4/api/a": "", "/v4/api/b": "Error: Class 'X' not found"}
    antigo = tmp_path / "antigo.tsv"
    antigo.write_text("metodo\turi\tmiddleware\taction\torigem\nGET|HEAD\t/x\tapi\tA@b\tlaravel\n", encoding="utf-8")
    assert gerador.le_inventario(antigo)[0].erro == ""


def test_rota_com_espaco_ou_caractere_estranho_na_uri_nao_vira_caso_e_aparece_com_motivo():
    r = rotas.Rota("POST", "/v4/api/educacao/transporte-escolar/emitir-carteira ", ["api"], "App\\C@emitir", "laravel")
    assert "caractere" in gerador.motivo_nao_gerada(r)
    assert gerador.gera([r])["laravel"] == []
    assert [m for _, m in gerador.nao_geradas([r])] == [gerador.motivo_nao_gerada(r)]


def test_lista_sem_ordem_e_comparada_como_conjunto_ordenado():
    from regressao.laravel.mascara import ordena_listas
    a = {"data": [{"nome": "b"}, {"nome": "a"}, {"nome": "c"}], "error": False}
    b = {"data": [{"nome": "c"}, {"nome": "b"}, {"nome": "a"}], "error": False}
    assert ordena_listas(a, ["data"]) == ordena_listas(b, ["data"])
    assert ordena_listas(a, ["data"])["data"] == [{"nome": "a"}, {"nome": "b"}, {"nome": "c"}]
    assert a["data"][0] == {"nome": "b"}                                   # nao muta a entrada
    assert ordena_listas(a, ["nao.existe"]) == a and ordena_listas([3, 1], [""]) == [1, 3]
    # conteudo diferente continua diferente
    assert ordena_listas(a, ["data"]) != ordena_listas({"data": [{"nome": "a"}, {"nome": "x"}, {"nome": "c"}],
                                                        "error": False}, ["data"])


def test_gerador_leva_sem_ordem_do_ajuste_ao_caso(tmp_path):
    r = rotas.Rota("GET|HEAD", "/v4/api/views", ["api"], "App\\V@index", "laravel")
    aj = {"sem_ordem": {"rota:GET:/v4/api/views": ["data"]}}
    c = gerador.gera([r], aj)["laravel"][0]
    assert c.listas_sem_ordem == ["data"]
    gerador.escreve(tmp_path, [r], aj)
    from regressao.laravel.caso import carrega_casos
    assert carrega_casos(tmp_path)[0].listas_sem_ordem == ["data"]
    arq = tmp_path / "aj.yml"
    arq.write_text("sem_ordem:\n  rota:GET:/v4/api/views: [data]\n", encoding="utf-8")
    assert gerador.le_ajustes(arq) == aj


def test_executa_ordena_a_lista_sem_ordem_antes_de_gravar(monkeypatch):
    from regressao.laravel import caso as mod_caso
    from regressao.laravel.caso import CasoHttp

    class R:
        status_code, headers, text = 200, {"content-type": "application/json"}, ""

        def json(self):
            return {"data": [{"nome": "z"}, {"nome": "a"}]}
    monkeypatch.setattr(mod_caso.requests, "request", lambda *a, **k: R())
    c = CasoHttp(id="rota:GET:/v", metodo="GET", caminho="/v", corpo=None, listas_sem_ordem=["data"])
    assert mod_caso.executa(c, "http://x", "tok", banco=False).json == {"data": [{"nome": "a"}, {"nome": "z"}]}


def test_cobertura_lista_rotas_com_controller_quebrado_na_referencia(tmp_path):
    lista = [rotas.Rota("GET|HEAD", "/v4/api/b", ["api"], "App\\B@i", "laravel", "Error: Class 'X' not found"),
             rotas.Rota("GET|HEAD", "/v4/api/a", ["api"], "App\\A@i", "laravel")]
    casos = [c for l in gerador.gera(lista).values() for c in l]
    rel = cobertura.cobertura_rotas(lista, casos, tmp_path, {})
    assert rel["controller_quebrado_na_referencia"] == [
        {"metodo": "GET|HEAD", "uri": "/v4/api/b", "erro": "Error: Class 'X' not found"}]
    cobertura.escreve_cobertura(rel, tmp_path)
    md = (tmp_path / "_cobertura.md").read_text(encoding="utf-8")
    assert "controller quebrado" in md.lower() and "Laravel 8" in md and "5.4" not in md


# ------------------------------------------------------------------ token / log do boot

def test_log_do_boot_vem_do_container_do_alvo(limpo, monkeypatch):
    chamadas = []

    def docker(args, timeout):
        chamadas.append(args)
        return b"PHP Fatal error: boom\n"
    monkeypatch.setattr(token, "_docker", docker)
    assert "boom" in token._cauda_php_errors("http://localhost:8187")
    assert chamadas[-1][:2] == ["exec", "ecidade74_lar12"]
    assert "boom" in token._cauda_php_errors("http://localhost:8074/")
    assert chamadas[-1][:2] == ["exec", "ecidade74_php74"]
    n = len(chamadas)
    assert token._cauda_php_errors("http://desconhecido:1") == ""   # nunca le o log de outro runtime
    assert len(chamadas) == n


# ------------------------------------------------------------------ console

def test_console_na_referencia_usa_o_container_de_referencia_do_ambiente(limpo):
    limpo.setenv("REGRESSAO_LARAVEL_CONSOLE_CONTAINER", "lab12")
    assert integracao.container_console("http://localhost:8074") == "ecidade74_php74"
    limpo.setenv("REGRESSAO_CONTAINER_REF", "minha_ref")
    assert integracao.container_console("http://localhost:8074/") == "minha_ref"


def test_console_no_laboratorio_usa_o_container_do_laboratorio_sem_variavel(limpo):
    assert integracao.container_console("http://localhost:8187") == "ecidade74_lar12"
    limpo.setenv("REGRESSAO_LARAVEL_CONSOLE_CONTAINER", "outro_lab")
    assert integracao.container_console("http://localhost:8187") == "outro_lab"


def test_console_em_alvo_desconhecido_exige_variavel_e_nunca_cai_na_referencia(limpo):
    with pytest.raises(integracao.ErroConsole, match="REGRESSAO_LARAVEL_CONSOLE_CONTAINER"):
        integracao.container_console("http://outro:9000")
    limpo.setenv("REGRESSAO_LARAVEL_CONSOLE_CONTAINER", "ecidade74_php74")
    with pytest.raises(integracao.ErroConsole, match="falso IDENTICO"):
        integracao.container_console("http://outro:9000")


def test_roda_console_sem_container_usa_a_referencia_do_ambiente(limpo):
    vistos = []
    integracao.roda_console(["env"], runner=lambda cmd: vistos.append(cmd) or _ok(b"x\n"))
    assert vistos[0][:5] == ["docker", "exec", "-w", "/var/www/html", "ecidade74_php74"]


def test_migrate_status_do_laravel_8_usa_yes_no():
    bruto = ("+------+-----------------------------------------------+-------+\n"
             "| Ran? | Migration                                     | Batch |\n"
             "+------+-----------------------------------------------+-------+\n"
             "| Yes  | 2016_06_01_000001_create_oauth_auth_codes_table | 1     |\n"
             "| Yes  | 2016_06_01_000002_create_oauth_access_tokens_table | 1  |\n"
             "| No   | 2026_01_01_000000_nova                        |       |\n"
             "+------+-----------------------------------------------+-------+\n")
    n = integracao.normaliza_saida_console(bruto, "migracoes")
    assert n.splitlines()[0].startswith("migrations=3 ran=2 sha256=")
    assert "N 2026_01_01_000000_nova" in n and "Y 2016_06_01_000001_create_oauth_auth_codes_table" in n
    # o mesmo conjunto no formato antigo (Y/N) da o mesmo resultado
    antigo = bruto.replace("| Yes  |", "| Y    |").replace("| No   |", "| N    |")
    assert integracao.normaliza_saida_console(antigo, "migracoes") == n


# ------------------------------------------------------------------ meta da bateria

def test_metadados_da_bateria_laravel_sao_da_referencia_e_do_alvo(limpo, monkeypatch):
    from regressao.nucleo import git
    monkeypatch.setattr(git, "commit", lambda raiz, curto=False, runner=None: "c0ffee")
    monkeypatch.setattr(git, "sujo", lambda raiz, runner=None: {"git_sujo": False})
    vistos = []

    def docker(args, timeout):
        vistos.append(args)
        if args[-1] == "--version":
            return b"Laravel Framework 8.73.2\n" if "ecidade74_php74" in args else b"Laravel Framework X\n"
        return b"7.4.33" if "ecidade74_php74" in args else b"8.5.12"
    monkeypatch.setattr(bateria, "_docker", docker)
    meta = bateria._metadados_ambiente("http://localhost:8187")
    assert meta["php_ref"] == "7.4.33" and meta["laravel_ref"] == "Laravel Framework 8.73.2"
    assert meta["php_alvo"] == "8.5.12" and meta["laravel_alvo"] == "Laravel Framework X"
    assert "php_56" not in meta
    meta = bateria._metadados_ambiente("http://localhost:8074")
    assert meta["laravel_alvo"] == "Laravel Framework 8.73.2" and meta["php_alvo"] == "7.4.33"
    meta = bateria._metadados_ambiente("http://outro:1")
    assert meta["laravel_alvo"].startswith("indisponivel")


def test_metadados_nao_estouram_sem_docker(limpo, monkeypatch):
    def sem(*a, **k):
        raise ErroAmbienteBanco("sem docker")
    monkeypatch.setattr(bateria, "_docker", sem)
    meta = bateria._metadados_ambiente("http://localhost:8187")
    assert meta["php_ref"].startswith("indisponivel") and meta["laravel_alvo"].startswith("indisponivel")


def test_completa_mostra_as_versoes_da_referencia_e_do_alvo_laravel():
    from regressao.completa import orquestra
    php = orquestra.Frente("php", 0, [], {"php_ref": "7.4.33", "php_85": "8.5.12"}, 0)
    lar = orquestra.Frente("laravel", 0, [], {"php_ref": "7.4.33", "laravel_ref": "Laravel Framework 8.73.2",
                                              "php_alvo": "8.5.12", "laravel_alvo": "indisponivel: X"}, 0)
    v = orquestra._versoes({"php": php, "laravel": lar})
    assert v == {"php_ref": "7.4.33", "php_85": "8.5.12", "laravel_ref": "Laravel Framework 8.73.2",
                 "php_alvo_laravel": "8.5.12", "laravel_alvo": "indisponivel: X"}


def test_casos_de_console_nao_citam_container_da_pilha_antiga():
    texto = (DIR_LARAVEL / "casos" / "integracao.yml").read_text(encoding="utf-8")
    assert "ecidade_php56" not in texto
