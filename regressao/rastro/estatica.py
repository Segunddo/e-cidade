"""Fase C: analise ESTATICA sobre o mesmo parser (nada e executado, nada e instrumentado, nao ha cache a invalidar).

Duas saidas (`php/analise.php`):
  - `candidatos`: usos de um resultado que pode ser `false` (pg_query, db_query, fopen...) sem checagem. E o padrao que mais
    divergiu no PHP 8 (`pg_num_rows($rs)` com `$rs === false` vira TypeError).
  - `leituras`: variaveis lidas por linha. Da ao backend Xdebug a cadeia por DEPENDENCIA de dados (so o backend de sondas tinha).
"""
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker

PHP_DIR = Path(__file__).resolve().parent / "php"
REMOTO = "/tmp/rastro/estatica"
RAIZ = "/var/www/html"
LOTE = 400
PARALELISMO = 8
TIMEOUT = 3600


def _copia(container: str) -> None:
    _docker(["exec", "-u", "root", container, "sh", "-c", f"mkdir -p {REMOTO} && chmod -R 777 /tmp/rastro"], 30)
    for nome in ("analise.php", "autoload.php"):
        _docker(["cp", str(PHP_DIR / nome), f"{container}:{REMOTO}/{nome}"], 30)


def _roda(container: str, modo: str, arquivos: list[str]) -> list[dict]:
    with tempfile.TemporaryFile() as f:
        f.write(("\n".join(arquivos) + "\n").encode("utf-8"))
        f.seek(0)
        saida = _docker(["exec", "-i", container, "sh", "-c", f"php {REMOTO}/analise.php --raiz={RAIZ} --modo={modo}"],
                        TIMEOUT, stdin=f).decode("utf-8", "replace")
    return [json.loads(l) for l in saida.splitlines() if l.startswith("{")]


def candidatos(arquivos: list[str], container: str | None = None) -> dict[str, list[dict]]:
    """{arquivo: [{linha, funcao, variavel, origem}]} so dos arquivos que tem candidato."""
    container = container or containers_do_ambiente().php_novo
    _copia(container)
    lotes = [arquivos[i:i + LOTE] for i in range(0, len(arquivos), LOTE)]
    with ThreadPoolExecutor(max_workers=PARALELISMO) as pool:
        partes = list(pool.map(lambda l: _roda(container, "candidatos", l), lotes))
    return {r["arquivo"]: r["candidatos"] for p in partes for r in p}


def comparacoes(arquivos: list[str], container: str | None = None) -> dict[str, list[dict]]:
    """{arquivo: [{linha, tipo, op, expressao, literal}]}: //switch entre literal (texto, '' ou 0) e outra expressao.
    O PHP 8 mudou o resultado quando um lado e inteiro e o outro e texto nao numerico (): nao ha aviso nem excecao."""
    container = container or containers_do_ambiente().php_novo
    _copia(container)
    lotes = [arquivos[i:i + LOTE] for i in range(0, len(arquivos), LOTE)]
    with ThreadPoolExecutor(max_workers=PARALELISMO) as pool:
        partes = list(pool.map(lambda l: _roda(container, "comparacoes", l), lotes))
    return {r["arquivo"]: r["comparacoes"] for p in partes for r in p}


def leitor_de_linhas(container: str | None = None):
    """`le_linha(arquivo, linha) -> [variaveis lidas]`. Analisa o arquivo sob demanda (uma vez) e guarda em cache."""
    container = container or containers_do_ambiente().php_novo
    _copia(container)
    cache: dict[str, dict] = {}

    def le_linha(arquivo: str, linha: int) -> list[str]:
        if arquivo not in cache:
            r = _roda(container, "leituras", [arquivo])
            cache[arquivo] = r[0]["leituras"] if r else {}
        return list(cache[arquivo].get(str(linha), []))
    return le_linha


def avalia(achados: dict[str, list[dict]], gabarito: set[tuple[str, int]]) -> dict:
    """Cobertura dos candidatos contra as linhas ja confirmadas pelo rastreio (arquivo, linha)."""
    previstos = {(a, c["linha"]) for a, cs in achados.items() for c in cs}
    acertos = previstos & gabarito
    return dict(candidatos=len(previstos), gabarito=len(gabarito), acertos=len(acertos),
                recall=round(len(acertos) / len(gabarito), 3) if gabarito else 0.0,
                perdidos=sorted(gabarito - previstos), fora_do_gabarito=len(previstos - gabarito))
