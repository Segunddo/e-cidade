"""Lint (`php -l`) de TODO `.php` de ecidade/ que as telas dos menus nao cobrem.

O QUE FAZ: lista os `.php` de ecidade/ fora das telas ja linteadas por `sintaxe.roda_lint`
(subpastas `app/`, `src/`, `forms/`, `model/`, `funcoes/`, `libs/`, `dbagata/`, `classes/` ... e as
telas da raiz que nao pertencem a nenhuma area) e compara, arquivo a arquivo, se compila no 7.4
(referencia) e no 8.5 (alvo). Mesma regra de veredito de `sintaxe.roda_lint`: compila nos dois =
IDENTICO; so um lado compila = DIVERGE; nenhum compila = INCONCLUSIVO (defeito que ja existe no 7.4).

POR QUE EXISTE: `roda_lint` so recebe telas da raiz. Uma medida na base-php85 (2026-11-26) achou 8
arquivos de subpastas que compilam no 7.4 e quebram no 8.5 (3 em `app/Domain/Patrimonial/Protocolo/`,
2 em `dbagata/classes/jpgraph/`, 2 em `ext/php/Michelf/`, 1 em `integracao_externa/gissonline/`),
sem que nenhum teste os visse.

COMO RODA: um `docker exec` por runtime recebe a lista pela entrada padrao e a distribui a 8 processos
(`xargs -P`); sao dezenas de milhares de arquivos, entao um exec por arquivo seria lento demais.
Saida do container: uma linha `FALHA<TAB>arquivo<TAB>mensagem` so para os que NAO compilam.

Usado por: `regressao/php/bateria.py` (etapa `sintaxe`, so em rodada de todas as areas).
"""
import os
import tempfile
from pathlib import Path

from regressao.nucleo.banco import ErroAmbienteBanco, _docker
from regressao.nucleo.veredito import Caso, Veredito
from regressao.php.sintaxe import AREA, ROTULO_NOVO, ROTULO_REF, containers_php

RAIZ = Path(__file__).resolve().parents[2]
DIR_ECIDADE = RAIZ / "ecidade"
# Pastas de topo que nao sao codigo do sistema: dependencias instaladas e area de trabalho dos testes.
PASTAS_IGNORADAS_NO_TOPO = frozenset({"vendor", "tmp"})
TIMEOUT_ARVORE = 3600
PARALELISMO = 8
LOTE = 50
# Roda dentro do container (cwd = raiz do sistema). `php -l` sai com 255 se nao compila; display_errors
# ligado para a mensagem vir completa (o php.ini do sistema o desliga e so sobraria "Errors parsing").
_SCRIPT = (
    'cd /var/www/html && xargs -d "\\n" -P %d -n %d sh -c \''
    'for f; do '
    'o=$(php -d display_errors=1 -d error_reporting=-1 -l "$f" 2>&1 </dev/null) && continue; '
    'm=$(printf %%s "$o" | grep -v "^Errors parsing" | tr "\\n\\t" "  " | cut -c1-300); '
    'printf "FALHA\\t%%s\\t%%s\\n" "$f" "$m"; '
    'done\' _'
) % (PARALELISMO, LOTE)


def lista_arvore(excluir: set[str] | frozenset[str] = frozenset(),
                 diretorio: Path = DIR_ECIDADE) -> list[str]:
    """`.php` de `diretorio` (caminhos relativos, com `/`), ordenados, sem os de `excluir`
    (as telas que `roda_lint` ja cobre) e sem `vendor/` e `tmp/` do topo nem `node_modules/`."""
    achados = []
    for pasta, subs, arquivos in os.walk(diretorio):
        rel = Path(pasta).relative_to(diretorio)
        if rel == Path("."):
            subs[:] = [s for s in subs if s not in PASTAS_IGNORADAS_NO_TOPO]
        subs[:] = [s for s in subs if s != "node_modules"]
        for nome in arquivos:
            if nome.endswith(".php"):
                caminho = (rel / nome).as_posix()
                if caminho not in excluir:
                    achados.append(caminho)
    return sorted(achados)


def _falhas(container: str, arquivos: list[str]) -> dict[str, str]:
    """{arquivo: mensagem} dos que NAO compilam em `container`."""
    with tempfile.TemporaryFile() as entrada:
        entrada.write(("\n".join(arquivos) + "\n").encode("utf-8"))
        entrada.seek(0)
        saida = _docker(["exec", "-i", container, "sh", "-c", _SCRIPT], TIMEOUT_ARVORE,
                        stdin=entrada).decode("utf-8", errors="replace")
    falhas: dict[str, str] = {}
    for linha in saida.splitlines():
        partes = linha.split("\t", 2)
        if len(partes) >= 2 and partes[0] == "FALHA":
            falhas[partes[1]] = partes[2].strip() if len(partes) == 3 else ""
    return falhas

def roda_lint_arvore(arquivos: list[str]) -> list[Caso]:
    ref, novo = containers_php()
    if not arquivos:
        return []
    try:
        falha_ref, falha85 = _falhas(ref, arquivos), _falhas(novo, arquivos)
    except ErroAmbienteBanco as e:
        return [Caso("passo:arvore", AREA, Veredito.ERRO_AMBIENTE, str(e))]
    casos = []
    for arq in arquivos:
        r, n = arq in falha_ref, arq in falha85
        if not r and not n:
            casos.append(Caso(arq, AREA, Veredito.IDENTICO))
        elif r != n:
            falha = f"{ROTULO_NOVO}: {falha85[arq]}" if n else f"{ROTULO_REF}: {falha_ref[arq]}"
            casos.append(Caso(arq, AREA, Veredito.DIVERGE, falha))
        else:
            casos.append(Caso(arq, AREA, Veredito.INCONCLUSIVO,
                              f"nao compila em nenhum runtime. {ROTULO_REF}: {falha_ref[arq]} | "
                              f"{ROTULO_NOVO}: {falha85[arq]}"))
    return casos
