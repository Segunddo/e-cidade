"""Fix round 1 da Task 11a: guarda de sondas, fingerprint, janela de SQL invertida,
integridade da baseline, poda e `espera_status`."""
import datetime
import json
import shutil

import pytest

from regressao.laravel import caso as mod
from regressao.laravel.caso import carrega_casos, comparar, gravar
from regressao.nucleo.veredito import Veredito
from regressao.tests.test_laravel_caso import REAL_CASOS, _caso, fake  # noqa: F401  (fixture)


@pytest.mark.parametrize("sql,alvo", [
    ('insert into "pessoal"."jetomfuncao" ("a") values ($1)', "jetomfuncao"),
    ("INSERT INTO foo(a) values (1)", "foo"),
    ("update db_config set a = (select 1 from oauth_clients)", "db_config"),
    ("delete from only public.bar where x = 1", "bar"),
    ("with n as (select 1) insert into baz select * from n", "baz"),
    ("copy qux (a,b) from stdin", "qux"),
    ("truncate table s.quux", "quux"),
    ("select * from foo", None),
])
def test_alvo_de_escrita(sql, alvo):
    assert mod._alvo_escrita(sql) == alvo


def test_infra_vale_pelo_alvo_e_nao_por_mencao():
    negocio = "update foo set a = (select max(id) from oauth_access_tokens) where b in (select x from db_acount)"
    assert mod._e_negocio(negocio) is True
    assert mod._e_negocio('insert into "oauth_access_tokens" ("id") values ($1)') is False
    assert mod._e_negocio("insert into db_logsacessa values (1)") is False
    assert mod._e_negocio("with n as (select 1) insert into db_logsacessa select 1") is False
    assert mod._e_negocio("with n as (select 1) insert into pessoal.jetomfuncao select 1") is True
    assert mod._e_negocio("truncate table x") is True
    assert mod._e_negocio("select 1") is False


def test_janela_de_sql_captura_sessao_desconhecida_e_exclui_marcador_e_pg_dump(monkeypatch):
    def l(pid, s):
        return f"2026-11-14 10:20:30.123 -03 [{pid}] LOG:  instrucao: {s}"
    log = "\n".join([
        l(7, "select 'REGRESSAO_a_ini'"),
        l(21, "SET statement_timeout = 0"), l(21, "insert into dump_t values (1)"),
        l(30, "set client_encoding to 'LATIN1'"), l(30, "insert into negocio(a) values (1)"),
        l(44, "BEGIN"), l(44, "update outro_cliente set a = 2"),   # sessao desconhecida: CAPTURA
        l(8, "select 'REGRESSAO_a_fim'"),
    ]).encode()
    monkeypatch.setattr(mod, "_logs_banco", lambda desde: log)
    sql = mod._sql_entre(datetime.datetime.now(datetime.timezone.utc),
                         "REGRESSAO_a_ini", "REGRESSAO_a_fim")
    assert sql == ["insert into negocio(a) values (1)", "update outro_cliente set a = 2"]


# ---- I-1 guarda de sondas

def test_sonda_que_escreve_no_gravar_levanta_erro_gravacao_e_nao_grava_nada(fake):
    casos = [_caso("rota:GET:/protegido", "/protegido"),
             _caso("rota:POST:/escreve", "/escreve", "POST", corpo={})]
    with pytest.raises(mod.ErroGravacao) as e:
        gravar(casos, fake.url, fake.baseline)
    assert "rota:POST:/escreve" in str(e.value)
    assert not fake.baseline.exists() or not list(fake.baseline.glob("*.json"))


def test_caso_de_escrita_declarado_nao_e_sonda(fake):
    casos = [_caso("escrita-x", "/escreve", "POST", corpo={}, espera_escrita=True, tabelas=["foo"])]
    gravar(casos, fake.url, fake.baseline)
    assert (fake.baseline / "escrita-x.json").is_file()


def test_comparar_sonda_que_passa_a_escrever_diverge(fake):
    fake.statements = []
    casos = [_caso("rota:POST:/escreve", "/escreve", "POST", corpo={})]
    gravar(casos, fake.url, fake.baseline)
    fake.statements = ["insert into foo(a) values (1)"]
    res = comparar(casos, fake.url, fake.baseline)
    assert res[0].veredito == Veredito.DIVERGE and "sql_negocio" in res[0].detalhe


# ---- I-5 fingerprint

def test_tabelas_alteradas_compara_fingerprints():
    a = {"a.t": 1, "a.u": 5, "a.v": 2}
    b = {"a.t": 1, "a.u": 6, "a.n": 1, "a.v": 2}
    assert mod._tabelas_alteradas(a, b) == {"a.u", "a.n"}


def test_fingerprint_acusa_escrita_invisivel_ao_log_mas_ignora_infra(fake):
    casos = [_caso("rota:GET:/protegido", "/protegido"),
             _caso("rota:POST:/muda", "/muda", "POST", corpo={})]
    with pytest.raises(mod.ErroGravacao) as e:
        gravar(casos, fake.url, fake.baseline)
    msg = str(e.value)
    assert "s.t" in msg and "oauth_clients" not in msg


def test_fingerprint_desconta_tabela_declarada_de_caso_de_escrita_na_janela(fake):
    casos = [_caso("rota:GET:/protegido", "/protegido"),
             _caso("escrita-muda", "/muda", "POST", corpo={}, tabelas=["s.t"]),
             _caso("rota:GET:/vazio", "/vazio")]
    gravar(casos, fake.url, fake.baseline)
    assert (fake.baseline / "escrita-muda.json").is_file()


def test_comparar_devolve_caso_fingerprint_diverge(fake):
    # grava sem a escrita invisivel (/muda ainda nao muda nada), depois ela passa a mudar
    casos = [_caso("rota:GET:/protegido", "/protegido"), _caso("rota:POST:/muda", "/muda", "POST", corpo={})]
    original = mod._fingerprint
    mod._fingerprint = lambda: {}   # gravacao sem fingerprint util
    try:
        gravar(casos, fake.url, fake.baseline)
    finally:
        mod._fingerprint = original
    res = comparar(casos, fake.url, fake.baseline)
    fps = [c for c in res if c.id == "fingerprint:probes"]
    assert fps and fps[0].veredito == Veredito.DIVERGE and "s.t" in fps[0].detalhe
    assert {c.id for c in res if c.id != "fingerprint:probes"} == {c.id for c in casos}


# ---- I-2 integridade da baseline

def test_comparar_recusa_meta_ids_diferente_dos_casos_carregados(fake):
    gravar([_caso("a"), _caso("b", "/vazio")], fake.url, fake.baseline)
    fake.chamadas.clear()
    res = comparar([_caso("a")], fake.url, fake.baseline)
    assert [c.veredito for c in res] == [Veredito.ERRO_AMBIENTE]
    assert "b" in res[0].detalhe and fake.chamadas == []
    res = comparar([_caso("a"), _caso("b", "/vazio"), _caso("c", "/quebra")], fake.url, fake.baseline)
    assert [c.veredito for c in res] == [Veredito.ERRO_AMBIENTE] and "c" in res[0].detalhe


def test_comparar_recusa_arquivo_de_baseline_sem_caso(fake):
    gravar([_caso("a")], fake.url, fake.baseline)
    (fake.baseline / "orfao.json").write_text("{}")
    fake.chamadas.clear()
    res = comparar([_caso("a")], fake.url, fake.baseline)
    assert [c.veredito for c in res] == [Veredito.ERRO_AMBIENTE]
    assert "orfao.json" in res[0].detalhe and fake.chamadas == []


def test_poda_remove_orfaos_e_reescreve_meta(fake, monkeypatch):
    gravar([_caso("a"), _caso("b", "/vazio")], fake.url, fake.baseline)
    monkeypatch.setattr(mod, "_commit", lambda: "abc1234")
    removidos = mod.poda([_caso("a")], fake.baseline)
    assert removidos == ["b.json"] and not (fake.baseline / "b.json").exists()
    meta = json.loads((fake.baseline / "_meta.json").read_text())
    assert meta["ids"] == ["a"] and meta["n_casos"] == 1 and meta["podado_no_commit"] == "abc1234"
    assert comparar([_caso("a")], fake.url, fake.baseline)[0].veredito == Veredito.IDENTICO


def test_poda_recusa_caso_sem_baseline(fake):
    gravar([_caso("a")], fake.url, fake.baseline)
    with pytest.raises(mod.ErroGravacao):
        mod.poda([_caso("a"), _caso("z", "/vazio")], fake.baseline)


def test_gravar_completo_remove_arquivos_antigos(fake):
    gravar([_caso("a"), _caso("b", "/vazio")], fake.url, fake.baseline)
    gravar([_caso("a")], fake.url, fake.baseline, completo=True)
    assert sorted(p.name for p in fake.baseline.glob("*.json")) == ["_meta.json", "a.json"]


# ---- I-4 espera_status

def test_espera_status_torna_a_rejeicao_documentada_identica(fake):
    declarado = [_caso("rej", "/quebra", espera_status=500)]
    gravar(declarado, fake.url, fake.baseline)
    assert comparar(declarado, fake.url, fake.baseline)[0].veredito == Veredito.IDENTICO


def test_sem_espera_status_o_500_continua_inconclusivo(fake):
    casos = [_caso("rej", "/quebra")]
    gravar(casos, fake.url, fake.baseline)
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.INCONCLUSIVO


def test_gravar_com_espera_status_diferente_do_real_levanta(fake):
    with pytest.raises(mod.ErroGravacao) as e:
        gravar([_caso("rej", "/protegido", espera_status=500)], fake.url, fake.baseline)
    assert "rej" in str(e.value)


def test_espera_status_so_vale_se_o_corpo_tambem_for_igual(fake):
    casos = [_caso("rej", "/quebra", espera_status=500)]
    gravar(casos, fake.url, fake.baseline)
    reg = mod._le_registro(fake.baseline / "rej.json")
    reg["json"] = {"message": "outra"}
    mod._grava_registro(fake.baseline / "rej.json", reg)
    assert comparar(casos, fake.url, fake.baseline)[0].veredito == Veredito.DIVERGE


def test_auth_yml_real_so_os_casos_de_rejeicao_tem_espera_status_500():
    casos = {c.id: c for c in carrega_casos(REAL_CASOS)}
    com = {i for i, c in casos.items() if c.espera_status is not None}
    assert com == {"auth-sem-token", "auth-token-invalido", "auth-token-expirado", "auth-token-revogado"}
    assert all(casos[i].espera_status == 500 for i in com)
    assert not any(c.espera_status for i, c in casos.items() if i.startswith("rota:"))
