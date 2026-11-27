"""Backend B: rastro pelo Xdebug (modo trace), SEM reescrever o codigo.

O Xdebug fica carregado nos dois contêineres com `xdebug.mode=trace` e `start_with_request=trigger`: so grava quando a
requisicao traz o cookie `XDEBUG_TRACE=1`. O trace (formato 4, computer readable) tem uma linha por evento:

    entrada   nivel  id  0  tempo  mem  funcao  user(0|1)  include  arquivo  linha  nparams  args...
    saida     nivel  id  1  tempo  mem
    retorno   nivel  id  R  ''     ''   valor                       (xdebug.collect_return=1)
    atribuic. nivel  ''  A  ''  ''  ''  ''  arquivo  linha  `$var = valor`   (xdebug.collect_assignments=1)

Aqui o trace vira a MESMA lista de `Evento` do backend A (sondas), e o alinhador/classificador/relatorio sao reaproveitados.
Diferencas em relacao ao backend A: nao ha sondas de condicao (`b`), nem a lista `le` (variaveis lidas) para a cadeia, e nao
ha aviso do 7.4 (so excecao pelo log da aplicacao); em troca, nada precisa ser instrumentado nem reinstrumentado.
"""
import re
import shlex

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.rastro import executor
from regressao.rastro.evento import Evento, le_rastro

DIR_TRACE = "/tmp/xdebug"
LIMITE_LINHAS = 3_000_000
PREFIXO = "/var/www/html/"
_PGRES = re.compile(r"^(?:resource\(\d+\) of type \(pgsql result\)|class PgSql\\Result\b.*)$", re.S)
_PGCON = re.compile(r"^(?:resource\(\d+\) of type \(pgsql link[^)]*\)|class PgSql\\Connection\b.*)$", re.S)
_RECURSO = re.compile(r"^resource\(\d+\) of type \(([^)]*)\)$")


CONF_TRACE = """xdebug.mode=trace
xdebug.start_with_request=trigger
xdebug.output_dir=/tmp/xdebug
xdebug.trace_output_name=trace.%u
xdebug.trace_format=1
xdebug.use_compression=0
xdebug.collect_assignments=1
xdebug.collect_return=1
"""
CONF_OFF = "xdebug.mode=off\n"
TIMEOUT_DOCKER = 600


def _e_php74(container: str) -> bool:
    return _docker(["exec", container, "sh", "-c", "test -d /etc/php/7.4 && echo sim; true"], 20).decode().strip() == "sim"


def versao_instalada(container: str) -> str:
    """Versao do Xdebug INSTALADO, mesmo com a extensao descarregada (modo off): tenta a carregada e, se vazio, carrega so para ler."""
    cmd = ("v=$(php -r 'echo phpversion(\"xdebug\");' 2>/dev/null); "
           "[ -n \"$v\" ] || v=$(php -d zend_extension=xdebug.so -r 'echo phpversion(\"xdebug\");' 2>/dev/null); echo \"$v\"")
    return _docker(["exec", container, "sh", "-c", cmd], 30).decode().strip()


def prepara(container: str) -> str:
    """Instala o Xdebug se faltar (7.4: pacote `php7.4-xdebug` do apt; 8.x: `pecl install xdebug`) e o deixa com `mode=off`.
    Idempotente. Devolve a versao instalada. O que e instalado aqui some se o contêiner for recriado: rode de novo."""
    if not versao_instalada(container):
        if _e_php74(container):
            _docker(["exec", "-u", "root", container, "sh", "-c",
                     "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq php7.4-xdebug"], TIMEOUT_DOCKER)
        else:
            _docker(["exec", "-u", "root", container, "sh", "-c", "pecl install xdebug"], TIMEOUT_DOCKER)
    modo(container, "off")
    return versao_instalada(container)


def modo(container: str, qual: str) -> None:
    """`trace` (so grava com o cookie XDEBUG_TRACE) ou `off`. O modo e lido na INICIALIZACAO do PHP: por isso reinicia o Apache.
    `off` deixa a porta 80 (e a bateria) sem custo; `trace` custa alguns ms por requisicao mesmo sem o gatilho."""
    conf = CONF_TRACE if qual == "trace" else CONF_OFF
    ligado = qual == "trace"
    if _e_php74(container):
        cmd = ("tee /etc/php/7.4/cli/conf.d/99-xdebug-rastro.ini > /etc/php/7.4/apache2/conf.d/99-xdebug-rastro.ini && "
               + ("phpenmod xdebug" if ligado else "phpdismod xdebug"))
    else:
        # `off` DESCARREGA a extensao (sem a linha zend_extension): mesmo com mode=off o Xdebug carregado custa alguns ms por requisicao
        cmd = ("( echo zend_extension=xdebug.so; cat ) > /usr/local/etc/php/conf.d/99-xdebug-rastro.ini" if ligado
               else "( echo '; xdebug descarregado (modo off)'; cat ) > /usr/local/etc/php/conf.d/99-xdebug-rastro.ini")
    import tempfile
    with tempfile.TemporaryFile() as f:
        f.write(conf.encode())
        f.seek(0)
        _docker(["exec", "-i", "-u", "root", container, "sh", "-c", f"mkdir -p {DIR_TRACE} && chmod 777 {DIR_TRACE} && {cmd}"],
                60, stdin=f)
    _docker(["exec", "-u", "root", container, "sh", "-c", "(apache2ctl graceful || apachectl graceful) 2>&1 | grep -v AH00558; true"], 60)


def valor(texto: str) -> dict:
    """Texto de valor do Xdebug -> resumo `{t, r}` comparavel entre as versoes (resource do 7.4 = objeto do 8.x)."""
    t = texto.strip()
    if _PGRES.match(t):
        return {"t": "pgresult", "r": "pgresult"}
    if _PGCON.match(t):
        return {"t": "pgconn", "r": "pgconn"}
    m = _RECURSO.match(t)
    if m:
        return {"t": "resource:" + m.group(1), "r": "resource:" + m.group(1)}
    if t in ("TRUE", "FALSE"):
        tipo = "bool"
    elif t == "NULL":
        tipo = "null"
    elif re.fullmatch(r"-?\d+", t):
        tipo = "int"
    elif re.fullmatch(r"-?\d+\.\d+(?:[eE][-+]?\d+)?", t):
        tipo = "float"
    elif t.startswith("'"):
        tipo = "string"
    elif t.startswith(("[", "array")):
        tipo = "array"
    elif t.startswith(("class ", "object")):
        tipo = "object"
    else:
        tipo = "raw"
    return {"t": tipo, "r": t[:300]}


def _relativo(arq: str) -> str:
    arq = arq.removeprefix(PREFIXO)
    return arq.removeprefix("tmp/ecidade-rastro/")


def le_trace(texto: str, funcoes: set[str] | None = None) -> list[Evento]:
    """Converte o trace em eventos. Atribuicoes (`a`) entram todas; chamadas (`c`) so as de `funcoes` (None = todas).
    Chamada que ENTRA e nunca SAI (excecao dentro dela) fica com valor `nao_retornou`."""
    eventos: list[dict] = []
    abertas: dict[str, dict] = {}
    seq = 0
    for linha in texto.splitlines():
        c = linha.split("\t")
        if len(c) < 3:
            continue
        tipo = c[2]
        if tipo == "A" and len(c) >= 4:
            m = re.match(r"^(\$?[^=]+?) = (.*)$", c[-1], re.S)
            if not m:
                continue
            seq += 1
            nome = m.group(1).strip().lstrip("$")
            eventos.append(dict(seq=seq, arquivo=_relativo(c[-3]), linha=int(c[-2] or 0), tipo="a", nome=nome,
                                valor=valor(m.group(2)), args=None, fn=None))
        elif tipo == "0" and len(c) >= 11:
            nome = c[5]
            if funcoes is not None and nome.lower() not in funcoes:
                continue
            seq += 1
            ev = dict(seq=seq, arquivo=_relativo(c[8]), linha=int(c[9] or 0), tipo="c", nome=nome,
                      valor={"t": "nao_retornou", "r": "(a chamada nao retornou)"},
                      args=tuple(str(valor(a)) for a in c[11:]), fn=c[1])
            eventos.append(ev)
            abertas[c[1]] = ev
        elif tipo == "1":
            ev = abertas.get(c[1])
            if ev is not None and ev["valor"]["t"] == "nao_retornou":
                ev["valor"] = {"t": "null", "r": "NULL"}      # saiu sem valor de retorno registrado
        elif tipo == "R" and len(c) >= 6:
            ev = abertas.get(c[1])
            if ev is not None:
                ev["valor"] = valor(c[5])
    return [Evento(e["seq"], 0, e["arquivo"], e["linha"], e["tipo"], e["nome"], e["valor"], e["args"]) for e in eventos]


def roda_requisicao_xdebug(sid: str, tela: str, container: str, funcoes: set[str] | None = None) -> tuple[executor.Execucao, list[Evento]]:
    """Uma requisicao com o gatilho do Xdebug: devolve a Execucao (status/corpo, eventos `e` do log da aplicacao em `rastro`) e
    os eventos do trace. O arquivo do trace e apagado depois de lido."""
    executor._restaura(sid)
    antes = _docker(["exec", container, "sh", "-c", f"ls {DIR_TRACE} 2>/dev/null; true"], 20).decode().split()
    n0 = executor._linhas_do_log(container)
    saida = _docker(["exec", container, "sh", "-c",
                     f"curl -s -m 60 -b 'ECIDADEWINDOWMAIN={sid}; XDEBUG_TRACE=1' -w '\n@@%{{http_code}}' "
                     f"{shlex.quote('http://localhost/' + tela)} | head -c 5000000"], 90)
    i = saida.rfind(b"\n@@")
    status, corpo = (int(saida[i + 3:]) if i >= 0 and saida[i + 3:].strip().isdigit() else 0), (saida[:i] if i >= 0 else saida)
    depois = _docker(["exec", container, "sh", "-c", f"ls {DIR_TRACE} 2>/dev/null; true"], 20).decode().split()
    novos = sorted(set(depois) - set(antes))
    trace = ""
    if novos:
        arq = f"{DIR_TRACE}/{novos[-1]}"
        trace = _docker(["exec", container, "sh", "-c", f"head -n {LIMITE_LINHAS} {arq}; rm -f {arq}"], 300).decode("utf-8", "replace")
    log = _docker(["exec", container, "sh", "-c", f"tail -n +{n0 + 1} {executor.LOG_APP} 2>/dev/null | head -c 200000; true"], 30).decode("utf-8", "replace")
    from regressao.rastro.evento import le_rastro
    exec_ = executor.Execucao(status, corpo, executor.eventos_do_log_da_aplicacao(log))
    return exec_, le_trace(trace, funcoes) + le_rastro(exec_.rastro)


def funcoes_da_lista() -> set[str]:
    from regressao.rastro.instrumenta import FUNCOES
    return {l.strip().lower() for l in FUNCOES.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
