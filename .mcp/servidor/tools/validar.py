"""validar_arquivo_php: php -l / PHPStan / Pint / PHPCS dentro dos conteineres 7.4 (referencia) e 8.5 (alvo)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from servidor.config import Config
from servidor.docker_exec import FERRAMENTAS, DockerExec, caminho_no_conteiner, comando_ferramenta
from servidor.seguranca import ErroFerramenta, limitar, relativo, resolver_caminho

VERSOES = {"referencia": "7.4 (referencia)", "alvo": "8.5 (alvo)"}
MAX_MENSAGENS = 100
CONFIGS_PHPSTAN = ("phpstan.neon", "phpstan.neon.dist", "phpstan.dist.neon")
# chaves cujos itens o PHPStan EXECUTA (bootstrapFiles) ou carrega (includes, autoload/scan)
_CHAVES_ARQUIVO = {"bootstrapfiles", "bootstrap", "includes", "autoload_files", "autoload_directories",
                   "scanfiles", "scandirectories"}
_CHAVE = re.compile(r"^(\s*)([A-Za-z_]+)\s*:\s*(.*?)\s*$")
_ITEM = re.compile(r"^(\s*)-\s*(.+?)\s*$")


def _itens_de_arquivo(texto: str) -> list[str]:
    """Itens das chaves perigosas de um .neon (lista em bloco `- x` ou inline `[a, b]`)."""
    itens, chave_ind = [], None
    for linha in texto.splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        m = _CHAVE.match(linha)
        if m and not linha.lstrip().startswith("-"):
            ind, chave, valor = len(m.group(1)), m.group(2).lower(), m.group(3)
            chave_ind = ind if chave in _CHAVES_ARQUIVO else None
            if chave_ind is not None and valor:
                itens += [v.strip().strip("'\"") for v in valor.strip("[]").split(",") if v.strip()]
            continue
        mi = _ITEM.match(linha)
        if mi and chave_ind is not None and len(mi.group(1)) > chave_ind:
            itens.append(mi.group(2).strip("'\""))
        elif mi is None:
            chave_ind = None
    return itens


def conferir_config_phpstan(config: Config) -> None:
    """Recusa rodar o PHPStan se a config do repo manda carregar/executar arquivo fora da raiz do repositorio
    (bootstrapFiles roda PHP; um commit malicioso poderia apontar para fora). Dentro da raiz e permitido."""
    codigo = (config.raiz / config.dir_codigo).resolve()
    raiz = config.raiz.resolve()
    for nome in CONFIGS_PHPSTAN:
        arq = codigo / nome
        if not arq.is_file():
            continue
        for item in _itens_de_arquivo(arq.read_text(encoding="utf-8", errors="replace")):
            v = (item.replace("%currentWorkingDirectory%", str(codigo))
                 .replace("%rootDir%", str(codigo / "vendor" / "phpstan" / "phpstan")))
            if v.startswith(config.dir_no_conteiner + "/") or v == config.dir_no_conteiner:
                v = str(codigo) + v[len(config.dir_no_conteiner):]
            if "%" in v:
                raise ErroFerramenta("config_phpstan_recusada", f"{nome}: item {item!r} com variavel desconhecida")
            alvo = (Path(v) if Path(v).is_absolute() else arq.parent / v).resolve()
            if alvo != raiz and raiz not in alvo.parents:
                raise ErroFerramenta("config_phpstan_recusada",
                                     f"{nome} manda o PHPStan carregar {item!r}, fora do repositorio; revise o arquivo "
                                     "(bootstrapFiles executa PHP)")


def _phpstan(stdout: str) -> tuple[bool | None, list[dict[str, Any]]]:
    dados = None
    for linha in reversed(stdout.splitlines()):  # o JSON e a ultima linha que comeca com '{'
        if linha.lstrip().startswith("{"):
            try:
                dados = json.loads(linha)
            except json.JSONDecodeError:
                dados = None
            break
    if dados is None and "{" in stdout:
        try:
            dados = json.loads(stdout[stdout.find("{"):])
        except json.JSONDecodeError:
            dados = None
    if not isinstance(dados, dict) or "totals" not in dados:
        return None, []
    msgs = [{"linha": m.get("line"), "mensagem": m.get("message", "")}
            for f in (dados.get("files") or {}).values() for m in f.get("messages", [])]
    msgs += [{"linha": None, "mensagem": e} for e in dados.get("errors") or []]
    t = dados["totals"]
    return (t.get("errors", 0) == 0 and t.get("file_errors", 0) == 0), msgs[:MAX_MENSAGENS]


def _um(docker: DockerExec, conteiner: str, ferramenta: str, arquivo: str, nivel: int | None,
        config: Config) -> dict[str, Any]:
    item: dict[str, Any] = {"conteiner": conteiner, "ferramenta": ferramenta}
    try:
        if ferramenta in ("pint", "phpcs", "phpstan"):
            binario = {"pint": "vendor/bin/pint", "phpcs": "vendor/bin/phpcs", "phpstan": "vendor/bin/phpstan"}[ferramenta]
            t = docker.executar(conteiner, ["test", "-x", binario], timeout=20)
            if t.codigo_saida != 0:
                raise ErroFerramenta("ferramenta_indisponivel",
                                     f"{binario} nao esta instalado em {conteiner} (dependencia de dev do composer); "
                                     "instalar e decisao da equipe")
        if ferramenta == "phpstan":
            conferir_config_phpstan(config)
        timeout = config.timeout_phpstan_s if ferramenta == "phpstan" else config.timeout_lint_s
        r = docker.executar(conteiner, comando_ferramenta(ferramenta, arquivo, nivel), timeout=timeout)
    except ErroFerramenta as e:
        item.update(ok=False, erro=e.como_dict())
        return item
    saida, _ = limitar((r.stdout + ("\n" + r.stderr if r.stderr.strip() else "")).strip(), 8000)
    item.update(codigo_saida=r.codigo_saida, duracao_s=r.duracao_s)
    if ferramenta == "phpstan":
        ok, msgs = _phpstan(r.stdout)
        if ok is None:
            aviso = ("o phpstan.neon nao define nivel: passe nivel_phpstan (0 a 9)" if "No rules detected" in saida
                     else "saida do PHPStan nao e JSON (erro de execucao?)")
            item.update(ok=False, saida=saida, aviso=aviso)
        else:
            item.update(ok=ok, mensagens=msgs)
    else:
        item.update(ok=r.codigo_saida == 0, saida=saida)
    return item


def validar_arquivo_php(
    config: Config,
    caminho: str,
    ferramentas: list[str] | None = None,
    versao: str = "ambas",
    nivel_phpstan: int | None = None,
    docker: DockerExec | None = None,
) -> dict[str, Any]:
    ferramentas = ferramentas or ["lint"]
    for f in ferramentas:
        if f not in FERRAMENTAS:
            raise ErroFerramenta("ferramenta_desconhecida", f"{f!r}; use {', '.join(FERRAMENTAS)}")
    if versao not in ("ambas", "alvo", "referencia"):
        raise ErroFerramenta("parametro_invalido", "versao: ambas | alvo | referencia")
    arq = resolver_caminho(config.raiz, caminho, tipo="arquivo")
    no_conteiner = caminho_no_conteiner(config, arq)
    docker = docker or DockerExec(config)
    alvos = [("referencia", config.container_ref), ("alvo", config.container_alvo)]
    if versao != "ambas":
        alvos = [a for a in alvos if a[0] == versao]
    resultados = []
    for papel, conteiner in alvos:
        for f in ferramentas:
            item = _um(docker, conteiner, f, no_conteiner, nivel_phpstan, config)
            resultados.append({"versao": VERSOES[papel], **item})
    falhas = [f"{r['ferramenta']} em {r['versao']}" for r in resultados if not r["ok"]]
    lint = {r["versao"]: r["ok"] for r in resultados if r["ferramenta"] == "lint" and "erro" not in r}
    resumo = "tudo ok" if not falhas else "falhou: " + "; ".join(falhas)
    if lint.get(VERSOES["referencia"]) and lint.get(VERSOES["alvo"]) is False:
        resumo += ". Compila no 7.4 e NAO no 8.5: e quebra da migracao"
    elif lint.get(VERSOES["referencia"]) is False and lint.get(VERSOES["alvo"]) is False:
        resumo += ". Nao compila em nenhum dos dois: ja estava quebrado na referencia"
    return {"arquivo": relativo(config.raiz, arq), "no_conteiner": no_conteiner, "ok": not falhas,
            "resultados": resultados, "resumo": resumo}
