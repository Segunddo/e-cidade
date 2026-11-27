"""Instrumenta a arvore inteira do ecidade/ (cache por hash: so reprocessa o que mudou).

SAIDA: `<raiz>/tmp/ecidade-rastro/`, uma copia espelhada onde cada `.php` instrumentado e um arquivo real e todo o
resto (assets, vendor/, tmp/, `.php` excluidos) e link simbolico para o original. A copia roda sozinha, sem
duplicar centenas de MB, e o codigo do e-Cidade nunca e alterado.

CACHE: `estado/manifesto.json` guarda, por arquivo, `sha256` do fonte e a versao do instrumentador (hash dos
arquivos do proprio instrumentador). Uma nova execucao reprocessa SO o que mudou; trocar o instrumentador ou a
lista de funcoes reprocessa tudo. Arquivos apagados saem da copia e do manifesto.

Quem escreve em `saida` e o contêiner (como root): o Python so le o fonte e manda os caminhos por stdin.
"""
import hashlib
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.php import arvore

AQUI = Path(__file__).resolve().parent
PHP_DIR = AQUI / "php"
FUNCOES = AQUI / "funcoes.txt"
ESTADO = AQUI / "estado" / "manifesto.json"
RAIZ_CONTAINER = "/var/www/html"
DESTINO_SCRIPTS = "/tmp/rastro/instr"
LOTE = 200
PARALELISMO = 8
TIMEOUT = 3600
LINKS_DE_TOPO = ("vendor", "tmp")      # diretorios inteiros que viram um unico link
ARQUIVOS_DO_INSTRUMENTADOR = ("instrumentador.php", "sondas.php", "autoload.php")


@dataclass
class Resumo:
    total: int = 0
    reprocessados: int = 0
    ignorados_cache: int = 0
    sem_parse: list = field(default_factory=list)
    removidos: int = 0
    falhas_lint: list = field(default_factory=list)          # instrumentado NAO compila e o original compila (defeito nosso)
    falhas_ja_no_original: list = field(default_factory=list)  # nao compila nem o original (defeito que ja existia)
    links: int = 0


def versao_instrumentador() -> str:
    """Muda quando o instrumentador, o visitor ou a lista de funcoes mudam."""
    h = hashlib.sha256()
    for nome in ARQUIVOS_DO_INSTRUMENTADOR:
        h.update((PHP_DIR / nome).read_bytes())
    h.update(FUNCOES.read_bytes())
    return h.hexdigest()[:12]


def _sha(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _carrega(estado: Path) -> dict:
    try:
        return json.loads(estado.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"arquivos": {}, "links": []}


def _grava(estado: Path, dados: dict) -> None:
    estado.parent.mkdir(parents=True, exist_ok=True)
    estado.write_text(json.dumps(dados, sort_keys=True), encoding="utf-8")


def _no_container(rel: str) -> str:
    return f"{RAIZ_CONTAINER}/{rel}"


def _copia_scripts(container: str) -> None:
    _docker(["exec", "-u", "root", container, "sh", "-c",
             f"mkdir -p {DESTINO_SCRIPTS} && chmod -R 777 /tmp/rastro"], 30)
    for nome in (*ARQUIVOS_DO_INSTRUMENTADOR, "liga.php"):
        _docker(["cp", str(PHP_DIR / nome), f"{container}:{DESTINO_SCRIPTS}/{nome}"], 30)
    _docker(["cp", str(FUNCOES), f"{container}:{DESTINO_SCRIPTS}/funcoes.txt"], 30)


def _exec_stdin(container: str, comando: str, linhas: list[str]) -> str:
    with tempfile.TemporaryFile() as f:
        f.write(("\n".join(linhas) + "\n").encode("utf-8"))
        f.seek(0)
        return _docker(["exec", "-i", "-u", "root", container, "sh", "-c", comando], TIMEOUT,
                       stdin=f).decode("utf-8", errors="replace")


def _roda_lote(container: str, saida_rel: str, lote: list[str]) -> list[dict]:
    cmd = (f"cd {RAIZ_CONTAINER} && php {DESTINO_SCRIPTS}/instrumentador.php --raiz={RAIZ_CONTAINER} "
           f"--saida={_no_container(saida_rel)} --funcoes={DESTINO_SCRIPTS}/funcoes.txt")
    saida = _exec_stdin(container, cmd, lote)
    return [json.loads(l) for l in saida.splitlines() if l.startswith("{")]


def _lint(container: str, arquivos: list[str]) -> dict[str, str]:
    return arvore._falhas(container, arquivos)


def _nao_instrumentados(raiz: Path, saida_rel: str, php_instrumentados: set[str]) -> list[str]:
    """Caminhos (relativos) que viram link: tudo que nao e `.php` instrumentado, exceto o que esta
    dentro dos links de topo e a propria pasta de saida."""
    achados = []
    for pasta, subs, arquivos in os.walk(raiz):
        rel = Path(pasta).relative_to(raiz)
        if rel == Path("."):
            subs[:] = [s for s in subs if s not in LINKS_DE_TOPO and s != ".git"]
        if rel.as_posix().startswith(saida_rel):
            subs[:] = []
            continue
        for nome in arquivos:
            caminho = (rel / nome).as_posix()
            if caminho not in php_instrumentados:
                achados.append(caminho)
    return sorted(achados)


def instrumenta_arvore(raiz: Path, saida: Path, forcar: bool = False, versao: str | None = None,
                       container: str | None = None, lint: bool = True, estado: Path = ESTADO,
                       excluir: frozenset[str] = frozenset()) -> Resumo:
    container = container or containers_do_ambiente().php_novo
    versao = versao or versao_instrumentador()
    saida_rel = saida.relative_to(raiz).as_posix()
    manifesto = _carrega(estado)
    antigos = manifesto.get("arquivos", {})
    arquivos = arvore.lista_arvore(excluir, raiz)
    resumo = Resumo(total=len(arquivos))
    atual = {a: _sha(raiz / a) for a in arquivos}

    mudar = [a for a in arquivos
             if forcar or antigos.get(a) != {"sha256": atual[a], "versao": versao}
             or not (saida / a).exists()]
    resumo.ignorados_cache = len(arquivos) - len(mudar)
    removidos = sorted(set(antigos) - set(atual))
    novos = dict(antigos)

    _copia_scripts(container)
    _docker(["cp", str(PHP_DIR / "rt.php"), f"{container}:{DESTINO_SCRIPTS}/rt.php"], 30)
    lotes = [mudar[i:i + LOTE] for i in range(0, len(mudar), LOTE)]
    with ThreadPoolExecutor(max_workers=PARALELISMO) as pool:
        resultados = list(pool.map(lambda l: _roda_lote(container, saida_rel, l), lotes))
    ok = []
    for lote in resultados:
        for r in lote:
            if r["status"] == "sem_parse":
                resumo.sem_parse.append(r["arquivo"])
            if r["status"] in ("ok", "sem_parse", "conflito_marcador"):
                novos[r["arquivo"]] = {"sha256": atual[r["arquivo"]], "versao": versao}
                if r["status"] == "ok":
                    ok.append(r["arquivo"])
    resumo.reprocessados = sum(len(l) for l in resultados)

    for a in removidos:
        novos.pop(a, None)
    resumo.removidos = len(removidos)
    if removidos:
        _exec_stdin(container, f"cd {_no_container(saida_rel)} && xargs -d '\\n' rm -f --",
                    [p for a in removidos for p in (a, a + ".map.json")])

    # links para o que nao e instrumentado
    desejados = sorted({*_nao_instrumentados(raiz, saida_rel, set(arquivos)), *LINKS_DE_TOPO})
    ja = set(manifesto.get("links", []))
    instrucoes = [f"+{p}" for p in desejados if p not in ja] + [f"-{p}" for p in sorted(ja - set(desejados))]
    if instrucoes:
        _exec_stdin(container, f"php {DESTINO_SCRIPTS}/liga.php --raiz={RAIZ_CONTAINER} "
                    f"--saida={_no_container(saida_rel)}", instrucoes)
    resumo.links = len(desejados)
    _docker(["cp", str(PHP_DIR / "rt.php"), f"{container}:{_no_container(saida_rel)}/rt.php"], 30)

    if lint and ok:
        resumo.falhas_lint, resumo.falhas_ja_no_original = confere_lint(saida_rel, ok, container)

    _grava(estado, {"arquivos": novos, "links": desejados, "versao": versao})
    return resumo


def confere_lint(saida_rel: str, arquivos: list[str], container: str | None = None) -> tuple[list[str], list[str]]:
    """`php -l` dos instrumentados nos DOIS PHP. Devolve (defeitos nossos, defeitos que ja existiam no original):
    so e defeito nosso o arquivo cujo original compila no mesmo PHP e o instrumentado nao."""
    container = container or containers_do_ambiente().php_novo
    ref = containers_do_ambiente().ref
    nossos: set[str] = set()
    antigos: set[str] = set()
    prefixados = [f"{saida_rel}/{a}" for a in arquivos]
    for c in {container, ref}:
        falhou = [p.removeprefix(f"{saida_rel}/") for p in _lint(c, prefixados)]
        if not falhou:
            continue
        originais = set(_lint(c, falhou))
        for a in falhou:
            (antigos if a in originais else nossos).add(a)
    return sorted(nossos), sorted(antigos - nossos)
