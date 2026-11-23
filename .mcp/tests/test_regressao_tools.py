import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from servidor.docker_exec import DockerExec
from servidor.seguranca import ErroFerramenta
from servidor.tools.regressao import ler_resultado_regressao, ler_triagem, rodar_regressao


def docker_ok(argv, **kw):
    return subprocess.CompletedProcess(argv, 0, "true\n", "")


def docker_sem(nome):
    def run(argv, **kw):
        if argv[-1] == nome:
            return subprocess.CompletedProcess(argv, 1, "", "Error: No such object")
        return subprocess.CompletedProcess(argv, 0, "true\n", "")
    return run


class FakePopen:
    chamadas = []

    def __init__(self, argv, **kw):
        FakePopen.chamadas.append((argv, kw))
        self.pid = 999999


@pytest.fixture
def cfg(config):
    py = config.raiz / "regressao" / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("")
    FakePopen.chamadas = []
    return config


def roda(cfg, runner=docker_ok, **kw):
    kw.setdefault("_rodada_manual", lambda: None)  # a maquina de teste pode ter uma rodada real em curso
    return rodar_regressao(cfg, docker=DockerExec(cfg, runner=runner), popen=FakePopen, **kw)


def test_rodar_php_por_prefixo_destacado(cfg):
    r = roda(cfg, bateria="php", prefixo=["^arr1_grupotaxa001\\.php$"], quem="ana")
    assert r["status"] == "iniciada" and r["id"].endswith(r["id"][-4:])
    argv, kw = FakePopen.chamadas[0]
    assert argv[0] == sys.executable and argv[1].endswith("executor.py")
    assert kw["start_new_session"] is True and kw["stdin"] == subprocess.DEVNULL
    assert kw["cwd"] == str(cfg.raiz)
    meta = json.loads((cfg.dir_rodadas / r["id"] / "meta.json").read_text())
    assert meta["argv"][0] == str(cfg.raiz / "regressao/.venv/bin/python")
    assert meta["argv"][1:4] == ["-m", "regressao.php.bateria", "--saida"]
    assert meta["argv"][4] == str(cfg.dir_rodadas / r["id"] / "saida")
    assert meta["argv"][5:] == ["--prefixo=^arr1_grupotaxa001\\.php$"]
    assert meta["quem"] == "ana" and meta["pid"] == 999999


def test_laravel_so_compara_nunca_grava(cfg):
    r = roda(cfg, bateria="laravel", confirmo_rodada_longa=True)
    meta = json.loads((cfg.dir_rodadas / r["id"] / "meta.json").read_text())
    assert meta["argv"][2:4] == ["regressao.laravel.bateria", "comparar"]
    assert "gravar" not in meta["argv"] and "--confirmo-sobrescrever" not in meta["argv"]


def test_fluxos_e_completa(cfg):
    r = roda(cfg, bateria="fluxos", fluxo=["navegacao"])
    meta = json.loads((cfg.dir_rodadas / r["id"] / "meta.json").read_text())
    assert meta["argv"][2:4] == ["regressao.completa.fluxos", "comparar"] and "--fluxo=navegacao" in meta["argv"]
    (cfg.dir_rodadas / r["id"] / "fim.json").write_text('{"codigo_saida": 0}')
    r = roda(cfg, bateria="completa", area=["tributario"], sem_fluxos=True)
    meta = json.loads((cfg.dir_rodadas / r["id"] / "meta.json").read_text())
    assert meta["argv"][2] == "regressao.completa.orquestra"
    assert "--area=tributario" in meta["argv"] and "--sem-fluxos" in meta["argv"]


@pytest.mark.parametrize("kw", [{"bateria": "php"}, {"bateria": "completa"}, {"bateria": "laravel"},
                                {"bateria": "fluxos"}])
def test_rodada_sem_filtro_exige_confirmacao(cfg, kw):
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, **kw)
    assert e.value.codigo == "confirmacao_necessaria"
    assert FakePopen.chamadas == []
    assert roda(cfg, confirmo_rodada_longa=True, **kw)["status"] == "iniciada"


def _meta_em(cfg, rid, meta, idade_s=0):
    d = cfg.dir_rodadas / rid
    d.mkdir(parents=True)
    (d / "meta.json").write_text(meta if isinstance(meta, str) else json.dumps(meta))
    if idade_s:
        t = time.time() - idade_s
        os.utime(d / "meta.json", (t, t))
    return d


def test_pid_none_recente_bloqueia_e_antigo_libera(cfg):
    _meta_em(cfg, "20261117-120000-php-aaaa", {"bateria": "php", "pid": None})
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, bateria="php", prefixo=["^a"])
    assert e.value.codigo == "rodada_em_andamento" and e.value.detalhes["status"] == "iniciando"
    os.utime(cfg.dir_rodadas / "20261117-120000-php-aaaa" / "meta.json", (time.time() - 3600,) * 2)
    assert roda(cfg, bateria="php", prefixo=["^a"])["status"] == "iniciada"


def test_meta_ilegivel_bloqueia_e_vira_estado_corrompido_na_leitura(cfg):
    _meta_em(cfg, "20261117-120000-php-bbbb", "{nao json")
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, bateria="php", prefixo=["^a"])
    assert e.value.detalhes["status"] == "desconhecida"
    with pytest.raises(ErroFerramenta) as e:
        ler_resultado_regressao(cfg, id="20261117-120000-php-bbbb")
    assert e.value.codigo == "estado_corrompido"


@pytest.mark.parametrize("meta", ['[]', '{"pid": "abc"}', '{"bateria": 3, "pid": 1}'])
def test_meta_com_forma_invalida(cfg, meta):
    _meta_em(cfg, "20261117-120000-php-cccc", meta)
    with pytest.raises(ErroFerramenta) as e:
        ler_resultado_regressao(cfg, id="20261117-120000-php-cccc")
    assert e.value.codigo == "estado_corrompido"


def test_resultado_json_com_forma_invalida(cfg):
    rid = _rodada(cfg)
    (cfg.dir_rodadas / rid / "saida" / "resultado.json").write_text('{"casos": [1, 2]}')
    with pytest.raises(ErroFerramenta) as e:
        ler_resultado_regressao(cfg, id=rid)
    assert e.value.codigo == "estado_corrompido"


def _dispara(raiz: str, fila) -> None:
    """Processo filho: tenta disparar uma rodada; o Popen falso segura a trava 1 s e devolve um pid vivo."""
    import time as t
    from servidor.config import Config
    from servidor.docker_exec import DockerExec
    from servidor.tools.regressao import rodar_regressao

    class PopenLento:
        def __init__(self, argv, **kw):
            t.sleep(1.0)
            self.pid = os.getppid()  # vivo durante o teste

    cfg = Config(raiz=Path(raiz))
    ok = lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "true\n", "")  # noqa: E731
    try:
        r = rodar_regressao(cfg, bateria="php", prefixo=["^a"], docker=DockerExec(cfg, runner=ok), popen=PopenLento,
                            _cmdline_executor=lambda pid: True, _rodada_manual=lambda: None)
        fila.put(("ok", r["id"]))
    except Exception as e:  # ErroFerramenta
        fila.put(("erro", getattr(e, "codigo", repr(e))))


def test_corrida_dois_processos_so_um_dispara(cfg):
    ctx = mp.get_context("spawn")
    fila = ctx.Queue()
    procs = [ctx.Process(target=_dispara, args=(str(cfg.raiz), fila)) for _ in range(2)]
    for p in procs:
        p.start()
    res = sorted(fila.get(timeout=60) for _ in procs)
    for p in procs:
        p.join(timeout=30)
    assert [r[0] for r in res] == ["erro", "ok"]
    assert res[0][1] == "rodada_em_andamento"
    assert len([d for d in cfg.dir_rodadas.iterdir() if d.is_dir()]) == 1


@pytest.mark.parametrize("kw,codigo", [
    ({"bateria": "shell"}, "parametro_invalido"),
    ({"bateria": "php", "area": ["inexistente"]}, "parametro_invalido"),
    ({"bateria": "php", "prefixo": ["("]}, "regex_invalida"),
    ({"bateria": "fluxos", "fluxo": ["a; rm -rf /"]}, "parametro_invalido"),
    ({"bateria": "php", "prefixo": ["--sem-restaurar"]}, None),
])
def test_validacao_de_argumentos(cfg, kw, codigo):
    if codigo is None:
        r = roda(cfg, **kw)  # vira --prefixo=--sem-restaurar: nunca uma opcao solta
        meta = json.loads((cfg.dir_rodadas / r["id"] / "meta.json").read_text())
        assert "--sem-restaurar" not in meta["argv"] and "--prefixo=--sem-restaurar" in meta["argv"]
        return
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, **kw)
    assert e.value.codigo == codigo


def test_conteiner_ausente_nao_dispara(cfg):
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, runner=docker_sem("ecidade74_database"), bateria="php", prefixo=["^a"])
    assert e.value.codigo == "conteiner_indisponivel"
    assert FakePopen.chamadas == []


def test_venv_da_regressao_ausente(config):
    with pytest.raises(ErroFerramenta) as e:
        rodar_regressao(config, bateria="php", prefixo=["^a"], docker=DockerExec(config, runner=docker_ok),
                        popen=FakePopen)
    assert e.value.codigo == "venv_regressao_ausente"


def test_uma_rodada_por_vez(cfg):
    r = roda(cfg, bateria="php", prefixo=["^a"])
    meta = cfg.dir_rodadas / r["id"] / "meta.json"
    m = json.loads(meta.read_text())
    m["pid"] = os.getpid()  # processo vivo
    meta.write_text(json.dumps(m))
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, bateria="php", prefixo=["^b"], _cmdline_executor=lambda pid: True)
    assert e.value.codigo == "rodada_em_andamento"


def test_rodada_manual_em_curso_bloqueia(cfg):
    with pytest.raises(ErroFerramenta) as e:
        roda(cfg, bateria="php", prefixo=["^a"], _rodada_manual=lambda: "rodada do atalho em 20261118-090000-pequena")
    assert e.value.codigo == "rodada_em_andamento" and e.value.detalhes["status"] == "manual"
    assert "20261118-090000-pequena" in e.value.mensagem and FakePopen.chamadas == []


def test_rodada_manual_ve_a_trava_viva_do_atalho(tmp_path, monkeypatch):
    from servidor.tools import regressao as mod
    monkeypatch.setenv("REGRESSAO_RODADAS", str(tmp_path))
    pgreps = []
    monkeypatch.setattr(mod.subprocess, "run", lambda argv, **kw: pgreps.append(argv) or
                        subprocess.CompletedProcess(argv, 1, "", ""))
    assert mod._rodada_manual() is None and pgreps[-1] == ["pgrep", "-f", "--", r"-m regressao\."]
    (tmp_path / ".em-andamento").write_text(f"{os.getpid()}\t{tmp_path}/20261118-090000-pequena\n")
    assert "20261118-090000-pequena" in mod._rodada_manual()
    (tmp_path / ".em-andamento").write_text("2147483646\tx\n")  # pid morto: a trava ficou para tras
    assert mod._rodada_manual() is None


def test_rodada_manual_ve_processo_da_suite_disparado_a_mao(tmp_path, monkeypatch):
    from servidor.tools import regressao as mod
    monkeypatch.setenv("REGRESSAO_RODADAS", str(tmp_path))
    monkeypatch.setattr(mod.subprocess, "run", lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "4321\n", ""))
    assert "4321" in mod._rodada_manual()


# ---------- leitura ----------

def _rodada(cfg, rid="20261117-120000-php-abcd", fim=1, casos=None):
    d = cfg.dir_rodadas / rid
    (d / "saida").mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"id": rid, "bateria": "php", "inicio": "2026-11-17T12:00:00Z",
                                             "pid": 999999, "argv": []}))
    (d / "execucao.log").write_text("linha 1\nlinha 2\n")
    if fim is not None:
        (d / "fim.json").write_text(json.dumps({"codigo_saida": fim, "fim": "2026-11-17T12:10:00Z"}))
    casos = casos if casos is not None else [
        {"id": "php:tela:a.php", "area": "php-telas", "veredito": "DIVERGE", "detalhe": "200 x 500", "conhecida": False},
        {"id": "php:tela:b.php", "area": "php-telas", "veredito": "DIVERGE", "detalhe": "x", "conhecida": True},
        {"id": "php:tela:c.php", "area": "php-telas", "veredito": "INCONCLUSIVO", "detalhe": "500 nos dois lados",
         "conhecida": False},
        {"id": "php:tela:d.php", "area": "php-telas", "veredito": "IDENTICO", "detalhe": "", "conhecida": False},
        {"id": "php:amb", "area": "php", "veredito": "ERRO_AMBIENTE", "detalhe": "sessao invalida", "conhecida": False},
    ]
    (d / "saida" / "resultado.json").write_text(json.dumps({"meta": {"comparavel": True}, "casos": casos}))
    (d / "saida" / "resumo.md").write_text("# Resumo\n")
    return rid


def test_ler_resultado(cfg):
    rid = _rodada(cfg)
    r = ler_resultado_regressao(cfg, id=rid)
    assert r["status"] == "concluida" and r["codigo_saida"] == 1
    assert r["totais"] == {"IDENTICO": 1, "DIVERGE": 2, "INCONCLUSIVO": 1, "ERRO_AMBIENTE": 1}
    assert [c["id"] for c in r["divergencias_novas"]] == ["php:tela:a.php"]
    assert r["erros_ambiente"][0]["detalhe"] == "sessao invalida"
    assert r["inconclusivo_por_motivo"] == {"500 nos dois lados": 1}
    assert "INCONCLUSIVO" in r["aviso"] and "aprovacao" in r["aviso"]
    assert "linha 2" in r["log_final"] and r["resumo_md"].startswith("# Resumo")


def test_ler_em_andamento_e_interrompida(cfg):
    rid = _rodada(cfg, fim=None)
    r = ler_resultado_regressao(cfg, id=rid, _cmdline_executor=lambda pid: True)
    assert r["status"] == "em_andamento"
    r = ler_resultado_regressao(cfg, id=rid, _cmdline_executor=lambda pid: False)
    assert r["status"] == "interrompida"


def test_listar_rodadas(cfg):
    _rodada(cfg, "20261117-120000-php-abcd")
    _rodada(cfg, "20261117-130000-laravel-beef", fim=0, casos=[])
    r = ler_resultado_regressao(cfg)
    assert [x["id"] for x in r["rodadas"]] == ["20261117-130000-laravel-beef", "20261117-120000-php-abcd"]


@pytest.mark.parametrize("rid", ["../../etc", "20261117-120000-php-zzzz", "x"])
def test_id_invalido(cfg, rid):
    with pytest.raises(ErroFerramenta) as e:
        ler_resultado_regressao(cfg, id=rid)
    assert e.value.codigo in ("parametro_invalido", "rodada_inexistente")


def test_ler_pasta_dentro_do_repo(cfg):
    d = cfg.raiz / "regressao" / "rodada-manual"
    d.mkdir()
    (d / "resultado.json").write_text(json.dumps({"meta": {}, "casos": []}))
    r = ler_resultado_regressao(cfg, pasta="regressao/rodada-manual")
    assert r["totais"] == {"IDENTICO": 0, "DIVERGE": 0, "INCONCLUSIVO": 0, "ERRO_AMBIENTE": 0}
    with pytest.raises(ErroFerramenta):
        ler_resultado_regressao(cfg, pasta="/tmp")


# ---------- triagem ----------

TRIAGEM = """# Triagem dos DIVERGE (7.4 x 8.5)

Intro.

## Categoria parse_str

parse_str de 1 argumento em ~460 telas.

## Construtor PHP4

classes sem __construct.

### Detalhe

sub.

## Outra
fim
"""


def test_ler_triagem(cfg):
    (cfg.raiz / "regressao" / "baseline" / "triagem-divergencias.md").write_text(TRIAGEM)
    r = ler_triagem(cfg)
    assert [s["titulo"] for s in r["secoes"]][:3] == ["Triagem dos DIVERGE (7.4 x 8.5)", "Categoria parse_str",
                                                      "Construtor PHP4"]
    assert r["base"] == "7.4 x 8.5"
    r = ler_triagem(cfg, secao="construtor")
    assert "classes sem __construct" in r["texto"] and "sub." in r["texto"] and "fim" not in r["texto"]
    r = ler_triagem(cfg, busca="460")
    assert r["linhas"] == [{"linha": 7, "texto": "parse_str de 1 argumento em ~460 telas."}]


def test_triagem_inexistente(cfg):
    with pytest.raises(ErroFerramenta) as e:
        ler_triagem(cfg, documento="como_usar")
    assert e.value.codigo == "documento_inexistente"


TRIAGEM_COM_RESUMO = """# Triagem das divergencias da rodada "antes" (referencia PHP 7.4 x PHP 8.5)

## Resumo (10 linhas)

1. linha um.
2. linha dois.

## Por causa

tabela.
"""


def test_ler_triagem_devolve_o_resumo_do_topo(cfg):
    (cfg.raiz / "regressao" / "baseline" / "triagem-divergencias.md").write_text(TRIAGEM_COM_RESUMO)
    r = ler_triagem(cfg)
    assert r["base"] == "7.4 x 8.5"
    assert r["resumo"].startswith("## Resumo") and "linha dois" in r["resumo"] and "tabela" not in r["resumo"]
    r = ler_triagem(cfg, busca="dois")
    assert "resumo" in r and r["linhas"][0]["texto"] == "2. linha dois."


def test_documento_historico_5_6_continua_marcado(cfg):
    (cfg.raiz / "regressao" / "baseline" / "triagem-divergencias.md").write_text(
        "# Triagem dos 781 DIVERGE (bateria PHP)\n\nFonte: gabarito PHP 5.6.\n")
    r = ler_triagem(cfg)
    assert r["base"].startswith("5.6 x 8.5 (historico") and r["resumo"] is None


@pytest.mark.parametrize("documento", ["triagem", "decisoes"])
def test_documentos_reais_sao_da_base_7_4_e_tem_resumo(documento):
    """Os documentos do repositorio (rodada antes74) substituiram os da migracao 5.6: sem rotulo historico."""
    from servidor.config import carregar_config
    r = ler_triagem(carregar_config({}), documento=documento)
    assert r["base"] == "7.4 x 8.5", r["base"]
    assert r["resumo"] and "historico" not in r["base"]
