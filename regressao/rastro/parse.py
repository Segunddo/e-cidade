"""Parse de `.php` com nikic/php-parser (o do proprio ecidade/vendor) dentro do contêiner do PHP 8.5.

POR QUE EXISTE: o instrumentador reescreve arquivos a partir da AST; um arquivo que nao parseia fica sem
sonda. Esta etapa mede, antes de instrumentar, quantos dos ~36.7k arquivos o parser le.

COMO RODA: copia `php/parse_todos.php` para o contêiner e passa a lista por stdin a varios processos
(`xargs -P`), como `arvore._falhas`.
"""
import tempfile
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker

SCRIPT_LOCAL = Path(__file__).resolve().parent / "php" / "parse_todos.php"
SCRIPT_REMOTO = "/tmp/rastro/parse_todos.php"
TIMEOUT_PARSE = 3600
PARALELISMO = 8
LOTE = 200
_CMD = ('cd /var/www/html && xargs -d "\\n" -P %d -n %d php %s' % (PARALELISMO, LOTE, SCRIPT_REMOTO))


def _copia_script(container: str) -> None:
    _docker(["exec", "-u", "root", container, "sh", "-c", "mkdir -p /tmp/rastro && chmod 777 /tmp/rastro"], 30)
    _docker(["cp", str(SCRIPT_LOCAL), f"{container}:{SCRIPT_REMOTO}"], 30)


def roda_parse(arquivos: list[str], container: str | None = None) -> dict:
    """{"ok": n, "falhas": [{"arquivo": ..., "msg": ...}]} para `arquivos` (relativos a /var/www/html)."""
    if not arquivos:
        return {"ok": 0, "falhas": []}
    container = container or containers_do_ambiente().php_novo
    _copia_script(container)
    with tempfile.TemporaryFile() as entrada:
        entrada.write(("\n".join(arquivos) + "\n").encode("utf-8"))
        entrada.seek(0)
        saida = _docker(["exec", "-i", container, "sh", "-c", _CMD], TIMEOUT_PARSE,
                        stdin=entrada).decode("utf-8", errors="replace")
    ok, falhas = 0, []
    for linha in saida.splitlines():
        partes = linha.split("\t", 2)
        if partes[0] == "OK":
            ok += 1
        elif partes[0] == "FALHA" and len(partes) >= 2:
            falhas.append({"arquivo": partes[1], "msg": partes[2].strip() if len(partes) == 3 else ""})
    return {"ok": ok, "falhas": falhas}
