import hashlib

import pytest

from regressao.nucleo import ambiente, banco


def test_confere_baseline_rejeita_dump_alterado(tmp_path, monkeypatch):
    sha = tmp_path / "baseline.dump.sha256"
    monkeypatch.setattr(banco, "ARQ_SHA256", sha)
    sha.write_text(hashlib.sha256(b"original").hexdigest() + "\n")
    dump = tmp_path / "baseline.dump"
    dump.write_bytes(b"alterado")
    with pytest.raises(banco.BancoDiferente):
        banco.confere_baseline(dump)


def test_confere_baseline_aceita_dump_igual(tmp_path, monkeypatch):
    sha = tmp_path / "baseline.dump.sha256"
    monkeypatch.setattr(banco, "ARQ_SHA256", sha)
    sha.write_text(hashlib.sha256(b"original").hexdigest() + "\n")
    dump = tmp_path / "baseline.dump"
    dump.write_bytes(b"original")
    banco.confere_baseline(dump)


_VARS_URL = ("REGRESSAO_REF_URL", "REGRESSAO_PHP_NOVO_URL", "REGRESSAO_NOVO_URL",
             "REGRESSAO_LARAVEL_NOVO_URL", "REGRESSAO_PROXY_URL")
_VARS_CONTAINER = ("REGRESSAO_CONTAINER_REF", "REGRESSAO_CONTAINER_PHP_NOVO",
                   "REGRESSAO_CONTAINER_BANCO", "REGRESSAO_CONTAINER_PROXY", "REGRESSAO_CONTAINER_LARAVEL_NOVO")


@pytest.fixture
def sem_variaveis(monkeypatch):
    for v in _VARS_URL + _VARS_CONTAINER:
        monkeypatch.delenv(v, raising=False)
    return monkeypatch


def test_alvos_padrao_sao_os_do_ambiente_e74(sem_variaveis):
    padrao = ambiente.alvos_do_ambiente()
    assert padrao.ref == "http://localhost:8074"
    assert padrao.php_novo == "http://localhost:8185"
    assert padrao.laravel_novo == "http://localhost:8187"
    assert padrao.proxy == "http://localhost:8190"


def test_alvos_usam_variaveis_de_ambiente(sem_variaveis):
    sem_variaveis.setenv("REGRESSAO_REF_URL", "http://x:1")
    sem_variaveis.setenv("REGRESSAO_PROXY_URL", "http://y:2")
    alvos = ambiente.alvos_do_ambiente()
    assert alvos.ref == "http://x:1"
    assert alvos.proxy == "http://y:2"
    assert alvos.php_novo == "http://localhost:8185"


def test_alvo_php_novo_aceita_regressao_novo_url(sem_variaveis):
    sem_variaveis.setenv("REGRESSAO_NOVO_URL", "http://n:3")
    assert ambiente.alvos_do_ambiente().php_novo == "http://n:3"
    # o nome antigo, mais especifico, vence
    sem_variaveis.setenv("REGRESSAO_PHP_NOVO_URL", "http://p:4")
    assert ambiente.alvos_do_ambiente().php_novo == "http://p:4"


def test_containers_padrao_sao_os_do_projeto_e74(sem_variaveis):
    c = ambiente.containers_do_ambiente()
    assert c.ref == "ecidade74_php74"
    assert c.php_novo == "ecidade74_php85"
    assert c.banco == "ecidade74_database"
    assert c.proxy == "ecidade74_proxy"


def test_containers_usam_variaveis_de_ambiente(sem_variaveis):
    sem_variaveis.setenv("REGRESSAO_CONTAINER_REF", "r")
    sem_variaveis.setenv("REGRESSAO_CONTAINER_PHP_NOVO", "n")
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "b")
    sem_variaveis.setenv("REGRESSAO_CONTAINER_PROXY", "p")
    sem_variaveis.setenv("REGRESSAO_CONTAINER_LARAVEL_NOVO", "l")
    assert ambiente.containers_do_ambiente() == ambiente.Containers(ref="r", php_novo="n", banco="b", proxy="p",
                                                                    laravel_novo="l")


def test_verifica_procura_o_container_de_banco_configurado(sem_variaveis):
    sem_variaveis.setattr(ambiente, "_responde", lambda url: True)
    sem_variaveis.setattr(ambiente, "containers_ativos", lambda: {"ecidade74_database"})
    alvos = ambiente.Alvos("http://a", "http://b", "http://c", "http://d")
    assert ambiente.verifica(alvos) == []
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "outro_banco")
    assert ambiente.verifica(alvos) == ["container ausente em docker ps: outro_banco"]


def test_banco_usa_o_container_configurado(sem_variaveis):
    cmds = []
    sem_variaveis.setattr(banco.subprocess, "run", lambda cmd, **k: cmds.append(cmd) or _Res(0, b"1"))
    banco._psql("select 1")
    assert cmds[-1][:3] == ["docker", "exec", "ecidade74_database"]
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "meu_banco")
    banco._psql("select 1")
    assert cmds[-1][:3] == ["docker", "exec", "meu_banco"]
    assert banco.container() == "meu_banco"


def test_logs_do_banco_da_bateria_laravel_usam_o_container_configurado(sem_variaveis):
    import datetime

    from regressao.laravel import caso
    cmds = []
    sem_variaveis.setattr(caso.subprocess, "run", lambda cmd, **k: cmds.append(cmd) or _Res(0, b""))
    caso._logs_banco(datetime.datetime(2026, 1, 1))
    assert cmds[-1][0:2] == ["docker", "logs"] and cmds[-1][-1] == "ecidade74_database"
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "meu_banco")
    caso._logs_banco(datetime.datetime(2026, 1, 1))
    assert cmds[-1][-1] == "meu_banco"


def test_verifica_reporta_alvo_fora(sem_variaveis):
    monkeypatch = sem_variaveis
    monkeypatch.setattr(ambiente, "containers_ativos", lambda: {"ecidade74_database"})
    alvos = ambiente.Alvos(
        ref="http://127.0.0.1:1",
        php_novo="http://127.0.0.1:1/php",
        laravel_novo="http://127.0.0.1:1/lv",
        proxy="http://127.0.0.1:1/px",
    )
    problemas = ambiente.verifica(alvos)
    assert len(problemas) == 4
    for url in (alvos.ref, alvos.php_novo, alvos.laravel_novo, alvos.proxy):
        assert any(url in p for p in problemas)


def test_verifica_reporta_container_ausente(sem_variaveis):
    monkeypatch = sem_variaveis
    monkeypatch.setattr(ambiente, "containers_ativos", lambda: {"outro"})
    monkeypatch.setattr(ambiente, "_responde", lambda url: True)
    alvos = ambiente.Alvos("http://a", "http://b", "http://c", "http://d")
    problemas = ambiente.verifica(alvos)
    assert any("ecidade74_database" in p for p in problemas)


def test_com_log_statement_reseta_mesmo_com_excecao(monkeypatch):
    chamadas = []
    monkeypatch.setattr(banco, "_psql", lambda sql, db="ecidade": chamadas.append(sql) or "")
    with pytest.raises(RuntimeError):
        with banco.com_log_statement():
            raise RuntimeError("falha")
    assert chamadas == [
        "ALTER DATABASE ecidade SET log_statement='all'",
        "ALTER DATABASE ecidade RESET log_statement",
    ]


def test_hash_tabelas_usa_psql(monkeypatch):
    sqls = []

    def falso(sql, db="ecidade"):
        sqls.append(sql)
        return "abc123\n"

    monkeypatch.setattr(banco, "_psql", falso)
    assert banco.hash_tabelas(["db_usuarios"]) == {"db_usuarios": "abc123"}
    assert "db_usuarios" in sqls[0] and "order by t::text" in sqls[0]


def test_confere_baseline_sem_sha256_levanta(tmp_path, monkeypatch):
    sha = tmp_path / "baseline.dump.sha256"
    monkeypatch.setattr(banco, "ARQ_SHA256", sha)
    dump = tmp_path / "baseline.dump"
    dump.write_bytes(b"x")
    with pytest.raises(banco.BancoDiferente, match="baseline.dump.sha256"):
        banco.confere_baseline(dump)


def test_confere_baseline_sem_dump_levanta(tmp_path, monkeypatch):
    sha = tmp_path / "baseline.dump.sha256"
    monkeypatch.setattr(banco, "ARQ_SHA256", sha)
    sha.write_text("abc\n")
    with pytest.raises(banco.BancoDiferente, match="inexistente.dump"):
        banco.confere_baseline(tmp_path / "inexistente.dump")


def test_confere_baseline_sha256_vazio_levanta(tmp_path, monkeypatch):
    sha = tmp_path / "baseline.dump.sha256"
    monkeypatch.setattr(banco, "ARQ_SHA256", sha)
    sha.write_text("  \n")
    dump = tmp_path / "baseline.dump"
    dump.write_bytes(b"x")
    with pytest.raises(banco.BancoDiferente, match="baseline.dump.sha256"):
        banco.confere_baseline(dump)


class _Res:
    def __init__(self, rc=0, out=b"", err=b""):
        self.returncode, self.stdout, self.stderr = rc, out, err


def test_erro_do_docker_inclui_stderr(monkeypatch):
    monkeypatch.setattr(
        banco.subprocess, "run", lambda *a, **k: _Res(3, b"", "falha ".encode() + bytes([0xe7]))
    )
    with pytest.raises(banco.ErroAmbienteBanco) as e:
        banco._psql("select 1")
    assert "falha" in str(e.value) and "3" in str(e.value)


def test_docker_ausente_vira_erro_ambiente_banco(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(banco.subprocess, "run", boom)
    with pytest.raises(banco.ErroAmbienteBanco):
        banco._psql("select 1")


def test_timeout_vira_erro_ambiente_banco(monkeypatch):
    def boom(*a, **k):
        raise banco.subprocess.TimeoutExpired("docker", 60)

    monkeypatch.setattr(banco.subprocess, "run", boom)
    with pytest.raises(banco.ErroAmbienteBanco):
        banco._psql("select 1")


def test_hash_tabelas_usa_ordenacao_por_texto_da_linha(monkeypatch):
    sqls = []
    monkeypatch.setattr(banco, "_psql", lambda sql, db="ecidade": sqls.append(sql) or "h\n")
    banco.hash_tabelas(["db_usuarios"])
    assert "order by t::text" in sqls[0]
    assert "order by 1" not in sqls[0]


def test_hash_tabelas_rejeita_nome_invalido(monkeypatch):
    monkeypatch.setattr(banco, "_psql", lambda sql, db="ecidade": "h")
    with pytest.raises(ValueError):
        banco.hash_tabelas(["x; drop table y"])


def test_restaura_dump_recria_banco_e_restaura_com_create(tmp_path, monkeypatch):
    monkeypatch.delenv("REGRESSAO_CONTAINER_BANCO", raising=False)  # padrao ecidade74_database: sem `inspect`
    chamadas = []

    def falso(*a, **k):
        chamadas.append((a[0], k))
        return _Res()

    monkeypatch.setattr(banco.subprocess, "run", falso)
    dump = tmp_path / "d.dump"
    dump.write_bytes(b"x")
    banco.restaura_dump(dump)
    assert len(chamadas) == 4
    (a0, _), (a1, _), (a2, _), (a3, k3) = chamadas
    assert "ALLOW_CONNECTIONS false" in a0[-1] and "postgres" in a0
    assert "pg_terminate_backend" in a1[-1] and "postgres" in a1
    assert "datname='ecidade'" in a1[-1] and "pg_backend_pid()" in a1[-1]
    assert a2[-1] == "DROP DATABASE IF EXISTS ecidade" and "postgres" in a2
    assert "pg_restore" in a3 and "--create" in a3 and "--exit-on-error" in a3
    assert "--clean" not in a3 and "--single-transaction" not in a3
    assert a3[a3.index("-d") + 1] == "postgres"
    assert k3["timeout"] == 900


def test_restaura_dump_falha_vira_erro_ambiente_banco(tmp_path, monkeypatch):
    monkeypatch.setattr(banco.subprocess, "run", lambda *a, **k: _Res(1, b"", b"boom"))
    dump = tmp_path / "d.dump"
    dump.write_bytes(b"x")
    with pytest.raises(banco.ErroAmbienteBanco, match="boom"):
        banco.restaura_dump(dump)


def test_gera_dump_usa_create(tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(banco, "ARQ_SHA256", tmp_path / "x.sha256")

    def falso(*a, **k):
        chamadas.append(a[0])
        return _Res()

    monkeypatch.setattr(banco.subprocess, "run", falso)
    banco.gera_dump(tmp_path / "d.dump")
    assert "--create" in chamadas[0] and "-Fc" in chamadas[0]


def test_hash_tabelas_aceita_schema_qualificado(monkeypatch):
    sqls = []
    monkeypatch.setattr(banco, "_psql", lambda sql, db="ecidade": sqls.append(sql) or "h")
    banco.hash_tabelas(["configuracoes.db_usuarios"])
    assert "from configuracoes.db_usuarios t" in sqls[0]


@pytest.mark.parametrize("nome", ["a.b.c", "x; drop table y", "A.b", "a."])
def test_hash_tabelas_rejeita_nomes_invalidos_com_schema(monkeypatch, nome):
    monkeypatch.setattr(banco, "_psql", lambda sql, db="ecidade": "h")
    with pytest.raises(ValueError):
        banco.hash_tabelas([nome])


def _restaura_com_docker_falso(monkeypatch, tmp_path, label: str | None):
    """restaura_dump com o docker falso: `inspect` devolve a label do projeto compose; o resto so registra."""
    cmds = []

    def falso(cmd, **k):
        cmds.append(cmd)
        if cmd[1] == "inspect":
            return _Res(1, b"", b"Error: No such object") if label is None else _Res(0, (label + "\n").encode())
        return _Res()

    monkeypatch.setattr(banco.subprocess, "run", falso)
    dump = tmp_path / "d.dump"
    dump.write_bytes(b"x")
    return cmds, dump


def test_restaura_dump_recusa_conteiner_fora_do_e74_sem_confirmacao(sem_variaveis, tmp_path):
    sem_variaveis.delenv("REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74", raising=False)
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "ecidade_database")  # o banco da pilha da raiz
    cmds, dump = _restaura_com_docker_falso(sem_variaveis, tmp_path, label="raiz")
    with pytest.raises(banco.ErroAmbienteBanco, match="REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74=sim"):
        banco.restaura_dump(dump)
    assert not any("DROP DATABASE" in " ".join(c) for c in cmds)
    assert not any("pg_restore" in c for c in cmds)
    # conteiner inexistente tambem e recusado (sem DROP)
    cmds, dump = _restaura_com_docker_falso(sem_variaveis, tmp_path, label=None)
    with pytest.raises(banco.ErroAmbienteBanco):
        banco.restaura_dump(dump)
    assert not any("DROP DATABASE" in " ".join(c) for c in cmds)


def test_restaura_dump_aceita_conteiner_do_projeto_e74_por_label(sem_variaveis, tmp_path):
    sem_variaveis.delenv("REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74", raising=False)
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "meu_banco")
    cmds, dump = _restaura_com_docker_falso(sem_variaveis, tmp_path, label="e74")
    banco.restaura_dump(dump)
    assert any("DROP DATABASE IF EXISTS ecidade" in " ".join(c) for c in cmds)


@pytest.mark.parametrize("valor,aceita", [("sim", True), ("SIM", False), ("1", False), ("", False)])
def test_restaura_dump_fora_do_e74_so_com_confirmacao_explicita(sem_variaveis, tmp_path, valor, aceita):
    sem_variaveis.setenv("REGRESSAO_CONTAINER_BANCO", "ecidade_database")
    sem_variaveis.setenv("REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74", valor)
    cmds, dump = _restaura_com_docker_falso(sem_variaveis, tmp_path, label="raiz")
    if aceita:
        banco.restaura_dump(dump)
        assert any("pg_restore" in c for c in cmds)
    else:
        with pytest.raises(banco.ErroAmbienteBanco):
            banco.restaura_dump(dump)
        assert not any("DROP DATABASE" in " ".join(c) for c in cmds)


def test_restaura_dump_bloqueio_tolera_banco_inexistente(tmp_path, monkeypatch):
    sqls = []
    monkeypatch.setattr(banco, "_psql", lambda sql, db="ecidade": sqls.append(sql) or "")
    monkeypatch.setattr(banco, "_docker", lambda *a, **k: b"")
    dump = tmp_path / "d.dump"
    dump.write_bytes(b"x")
    banco.restaura_dump(dump)
    assert "from pg_database where datname='ecidade'" in sqls[0]
    assert "ALLOW_CONNECTIONS false" in sqls[0]
    assert "pg_terminate_backend" in sqls[1]
    assert sqls[2] == "DROP DATABASE IF EXISTS ecidade"
