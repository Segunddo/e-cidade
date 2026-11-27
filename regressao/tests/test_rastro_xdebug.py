"""regressao/rastro/xdebug.py: conversao do trace do Xdebug (formato 4) em eventos. Linhas copiadas de traces reais."""
from regressao.rastro import xdebug

TRACE = "\n".join([
    "Version: 3.5.3", "File format: 4", "TRACE START [2026-11-27 15:43:27.838397]",
    "3\t\tA\t\t\t\t\t/var/www/html/cad2_setor002.php\t78\t$rsSql = FALSE",
    "3\t\tA\t\t\t\t\t/var/www/html/cad2_setor002.php\t75\t$sSql = ' select distinct j34_setor,\\n\\t\\tj50_descr'",
    "4\t13911\t0\t0.339979\t919928\tpg_num_rows\t0\t\t/var/www/html/cad2_setor002.php\t79\t1\tFALSE",
    "6\t12935\t0\t0.268165\t905704\tpg_fetch_result\t0\t\t/var/www/html/libs/db_conecta.php\t138\t3\tclass PgSql\\Result {  }\t0\t0",
    "6\t12935\t1\t0.268173\t905736",
    "6\t12935\tR\t\t\t1",
    "7\t12940\t0\t0.3\t9\tstrlen\t0\t\t/var/www/html/a.php\t4\t1\t'abc'",
    "7\t12940\t1\t0.31\t9",
    "TRACE END   [2026-11-27 15:43:28.196294]",
])


def test_atribuicao_vira_evento_a_com_arquivo_linha_nome_e_valor():
    ev = [e for e in xdebug.le_trace(TRACE) if e.tipo == "a"]
    assert [(e.arquivo, e.linha, e.nome, e.valor["t"], e.valor["r"]) for e in ev][0] == ("cad2_setor002.php", 78, "rsSql", "bool", "FALSE")
    assert ev[1].nome == "sSql" and ev[1].valor["t"] == "string" and ev[1].valor["r"].startswith("' select distinct")


def test_chamada_com_retorno_tem_args_e_valor():
    c = next(e for e in xdebug.le_trace(TRACE) if e.nome == "pg_fetch_result")
    assert (c.arquivo, c.linha, c.tipo) == ("libs/db_conecta.php", 138, "c")
    assert c.valor == {"t": "int", "r": "1"} and len(c.args) == 3


def test_chamada_que_entra_e_nunca_sai_e_a_assinatura_da_excecao():
    c = next(e for e in xdebug.le_trace(TRACE) if e.nome == "pg_num_rows")
    assert (c.arquivo, c.linha) == ("cad2_setor002.php", 79) and c.valor["t"] == "nao_retornou"


def test_chamada_que_sai_sem_valor_de_retorno_registrado_e_null():
    c = next(e for e in xdebug.le_trace(TRACE) if e.nome == "strlen")
    assert c.valor == {"t": "null", "r": "NULL"}


def test_filtra_as_chamadas_pela_lista_de_funcoes_mas_nao_as_atribuicoes():
    ev = xdebug.le_trace(TRACE, funcoes={"pg_num_rows"})
    assert {e.nome for e in ev if e.tipo == "c"} == {"pg_num_rows"} and sum(e.tipo == "a" for e in ev) == 2


def test_resource_do_74_e_objeto_do_8x_viram_o_mesmo_valor():
    assert xdebug.valor("resource(5) of type (pgsql result)") == xdebug.valor("class PgSql\\Result {  }")
    assert xdebug.valor("resource(3) of type (pgsql link)") == xdebug.valor("class PgSql\\Connection {  }")
    assert xdebug.valor("FALSE")["t"] == "bool" and xdebug.valor("NULL")["t"] == "null" and xdebug.valor("[1, 2]")["t"] == "array"


class DockerFalso:
    def __init__(self, versao="", e74=False):
        self.versao, self.e74, self.cmds, self.escritos = versao, e74, [], []

    def __call__(self, args, timeout, stdin=None, stdout=None):
        cmd = args[-1]
        self.cmds.append(cmd)
        if "phpversion('xdebug')" in " ".join(args):
            return self.versao.encode()
        if "test -d /etc/php/7.4" in cmd:
            return b"sim\n" if self.e74 else b""
        if stdin is not None:
            stdin.seek(0)
            self.escritos.append((cmd, stdin.read().decode()))
        if "pecl install" in cmd or "apt-get install" in cmd:
            self.versao = "3.x"
        return b""


def test_prepara_instala_no_74_por_apt_e_no_85_por_pecl_e_deixa_em_off(monkeypatch):
    for e74, esperado in ((True, "apt-get install"), (False, "pecl install xdebug")):
        f = DockerFalso(e74=e74)
        monkeypatch.setattr(xdebug, "_docker", f)
        assert xdebug.prepara("c") == "3.x"
        assert any(esperado in c for c in f.cmds)
        assert f.escritos[-1][1] == xdebug.CONF_OFF


def test_prepara_nao_reinstala_se_ja_ha_xdebug(monkeypatch):
    f = DockerFalso(versao="3.5.3")
    monkeypatch.setattr(xdebug, "_docker", f)
    xdebug.prepara("c")
    assert not any("pecl install" in c or "apt-get install" in c for c in f.cmds)


def test_modo_trace_escreve_os_caminhos_certos_e_reinicia_o_apache(monkeypatch):
    f = DockerFalso(versao="3.1.6", e74=True)
    monkeypatch.setattr(xdebug, "_docker", f)
    xdebug.modo("c", "trace")
    cmd, conteudo = f.escritos[-1]
    assert "/etc/php/7.4/cli/conf.d/99-xdebug-rastro.ini" in cmd and "/etc/php/7.4/apache2/conf.d/99-xdebug-rastro.ini" in cmd
    assert "xdebug.start_with_request=trigger" in conteudo and "xdebug.collect_assignments=1" in conteudo
    assert any("graceful" in c for c in f.cmds)
    assert "phpenmod xdebug" in cmd
    f2 = DockerFalso(versao="3.5.3", e74=False)
    monkeypatch.setattr(xdebug, "_docker", f2)
    xdebug.modo("c", "trace")
    assert "/usr/local/etc/php/conf.d/99-xdebug-rastro.ini" in f2.escritos[-1][0] and "zend_extension=xdebug.so" in f2.escritos[-1][0]


def test_modo_off_descarrega_a_extensao_nos_dois_para_nao_custar_nada_na_porta_80(monkeypatch):
    f85 = DockerFalso(versao="3.5.3", e74=False)
    monkeypatch.setattr(xdebug, "_docker", f85)
    xdebug.modo("c", "off")
    assert "zend_extension" not in f85.escritos[-1][0]
    f74 = DockerFalso(versao="3.1.6", e74=True)
    monkeypatch.setattr(xdebug, "_docker", f74)
    xdebug.modo("c", "off")
    assert "phpdismod xdebug" in f74.escritos[-1][0] and "phpenmod" not in f74.escritos[-1][0]


def test_eventos_alinham_e_classificam_pelo_mesmo_pipeline_do_backend_de_sondas():
    """7.4 retorna de pg_num_rows(FALSE); 8.5 entra e nunca sai (excecao). Mesmo classificador, sem sonda nenhuma."""
    from regressao.rastro.classifica import classifica
    from regressao.rastro.evento import Evento
    t74 = TRACE.replace("79\t1\tFALSE", "79\t1\tFALSE\n4\t13911\t1\t0.34\t9\n4\t13911\tR\t\t\tNULL")
    ref, alvo = xdebug.le_trace(t74), xdebug.le_trace(TRACE)
    exc = Evento(10**9, 0, "cad2_setor002.php", 79, "e", "excecao_app", {"t": "excecao", "r": "TypeError: pg_num_rows()"})
    r = classifica(ref, alvo + [exc], list(ref), (200, b"ok"), (500, b"erro"))
    assert r.veredito == "DIVERGE-CAUSAL"
    assert (r.sintoma.arquivo, r.sintoma.linha) == ("cad2_setor002.php", 79)
