"""Executor: faz UMA requisicao num contêiner (arvore normal na porta 80 ou instrumentada na 8091) e devolve
status, corpo e o rastro daquela requisicao.

SESSAO: usa login proprio e um backup PROPRIO (`/tmp/_sess_rastro.bak`); nunca toca em `/tmp/_sess.bak`, que e da
bateria e pertence a outra sessao. A requisicao consome/reescreve a sessao, entao ela e restaurada antes de cada uma.

RASTRO: o rt.php grava `/tmp/rastro/<id>.jsonl`. Excecoes que o proprio e-Cidade trata (pagina "Erro interno") nao passam
pelo rt.php; elas ficam em `extension/log/error.log` (arquivo unico, compartilhado pelos dois contêineres), entao as linhas
NOVAS desse log, de cada requisicao, viram eventos `e` no fim do rastro.
"""
import hashlib
import json
import re
import shlex
from dataclasses import dataclass, field

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.nucleo.normaliza import normaliza
from regressao.php import telas as T
from regressao.rastro.servidor import PORTA

BACKUP_SESSAO = "/tmp/_sess_rastro.bak"
LOG_APP = "/var/www/html/extension/log/error.log"
TIMEOUT = 120
_EXC = re.compile(r"^\[[\d\- :]+\] \w+: (?:E_\w+ - )?Uncaught exception '(\w+)' with message '(.*)' in (\S+) on line (\d+)", re.S)


@dataclass
class Execucao:
    status: int
    corpo: bytes
    rastro: list = field(default_factory=list)   # linhas JSON (rt.php + eventos do log da aplicacao)


def nova_sessao() -> str:
    """Login proprio + backup proprio. Devolve o SID."""
    sid = T.login_http()
    ref = containers_do_ambiente().ref
    _docker(["exec", "-u", "root", ref, "sh", "-c", f"cp /var/lib/php/sessions/sess_{sid} {BACKUP_SESSAO}"], 30)
    return sid


def _restaura(sid: str) -> None:
    sess = f"/var/lib/php/sessions/sess_{sid}"
    _docker(["exec", "-u", "root", containers_do_ambiente().ref, "sh", "-c",
             f"cp {BACKUP_SESSAO} {sess}; chown www-data:www-data {sess}"], 30)


def _linhas_do_log(container: str) -> int:
    try:
        return int(_docker(["exec", container, "sh", "-c", f"wc -l < {LOG_APP} 2>/dev/null || echo 0"], 20).decode().strip() or 0)
    except ValueError:
        return 0


def eventos_do_log_da_aplicacao(texto: str, base_seq: int = 10**9) -> list[str]:
    """Blocos `[data] ERROR: ... Uncaught exception 'X' with message 'M' in arq on line N` -> eventos `e`."""
    saida = []
    for i, bloco in enumerate(re.split(r"(?m)^(?=\[\d{4}-\d\d-\d\d [\d:]+\] )", texto)):
        m = _EXC.match(bloco.strip().split("\n#")[0])
        if not m:
            continue
        tipo, msg, arq, lin = m.groups()
        r = f"{tipo}: {msg}"[:300]
        saida.append(json.dumps({"s": base_seq + i, "p": 0, "f": arq, "l": int(lin), "k": "e", "n": "excecao_app",
                                 "v": {"t": "excecao", "r": r, "h": hashlib.md5(r.encode("utf-8", "replace")).hexdigest()}},
                                ensure_ascii=False))
    return saida


def roda_requisicao(sid: str, tela: str, id_rastro: str, container: str, instrumentado: bool = True) -> Execucao:
    _restaura(sid)
    antes = _linhas_do_log(container)
    url = f"http://localhost:{PORTA}/{tela}" if instrumentado else f"http://localhost/{tela}"
    cab = f"-H {shlex.quote('X-Rastro-Id: ' + id_rastro)} " if instrumentado else ""
    saida = _docker(["exec", container, "sh", "-c",
                     f"curl -s -m 60 {cab}-b 'ECIDADEWINDOWMAIN={sid}' -w '\n@@%{{http_code}}' {shlex.quote(url)} | head -c 5000000"],
                    TIMEOUT)
    i = saida.rfind(b"\n@@")
    status, corpo = (int(saida[i + 3:]) if i >= 0 and saida[i + 3:].strip().isdigit() else 0), (saida[:i] if i >= 0 else saida)
    rastro: list[str] = []
    if instrumentado:
        bruto = _docker(["exec", container, "sh", "-c", f"cat /tmp/rastro/{id_rastro}.jsonl 2>/dev/null; true"], 60).decode("utf-8", "replace")
        rastro = [l for l in bruto.splitlines() if l.strip()]
    novo = _docker(["exec", container, "sh", "-c", f"tail -n +{antes + 1} {LOG_APP} 2>/dev/null | head -c 200000; true"], 30).decode("utf-8", "replace")
    return Execucao(status, corpo, rastro + eventos_do_log_da_aplicacao(novo))


def corpo_normalizado(corpo: bytes) -> bytes:
    """Mesma normalizacao da bateria; a pagina de erro carrega a porta do vhost, que nao e diferenca de comportamento."""
    return normaliza(corpo.replace(f"localhost:{PORTA}".encode(), b"localhost"))
