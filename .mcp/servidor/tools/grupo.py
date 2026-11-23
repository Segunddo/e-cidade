"""regras_do_grupo e ferramentas_do_grupo: o que o grupo combinou e as ferramentas que ele ja tem (scratchpad/)."""
from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from servidor.config import Config
from servidor.seguranca import ErroFerramenta, decodificar, eh_negado, limitar, relativo, resolver_caminho
from servidor.tools.regressao import _norm

ARQ_REGRAS = ".mcp/docs/regras-do-grupo.md"
_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,100}$")
MAX_FERRAMENTAS = 200
MAX_DESCRICAO = 300


def regras_do_grupo(config: Config, topico: str | None = None) -> dict[str, Any]:
    arq = resolver_caminho(config.raiz, ARQ_REGRAS, tipo="arquivo")
    linhas = arq.read_text(encoding="utf-8").splitlines()
    secoes = []
    for i, linha in enumerate(linhas, start=1):
        m = _TITULO.match(linha)
        if m:
            secoes.append({"titulo": m.group(2), "nivel": len(m.group(1)), "linha": i})
    r: dict[str, Any] = {"documento": ARQ_REGRAS, "topicos": [s["titulo"] for s in secoes if s["nivel"] == 2],
                         "integra_do_guia": "ecidade://grupo/guia-7.4-para-8.5"}
    if topico:
        alvo, partes = _norm(topico), []
        for k, s in enumerate(secoes):
            if alvo in _norm(s["titulo"]):
                fim = next((t["linha"] - 1 for t in secoes[k + 1:] if t["nivel"] <= s["nivel"]), len(linhas))
                partes.append("\n".join(linhas[s["linha"] - 1:fim]).strip())
        if not partes:
            raise ErroFerramenta("topico_inexistente", f"nenhum topico com {topico!r}; veja `topicos`")
        r["texto"] = limitar("\n\n".join(partes), config.max_saida)[0]
    else:
        r["texto"] = limitar("\n".join(linhas), config.max_saida)[0]
    return r


# ---------- ferramentas do grupo ----------

def descricao_do_cabecalho(nome: str, texto: str) -> str:
    """Primeiro comentario/docstring do arquivo (Python, PHP, shell), em uma linha curta."""
    t = texto[:6000]
    blocos: list[str] = []
    if nome.endswith(".py"):
        m = re.search(r'^\s*(?:#![^\n]*\n)?(?:\s*#[^\n]*\n)*\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', t, re.S)
        if m:
            blocos.append(m.group(1))
    if not blocos and nome.endswith((".php", ".inc", ".class")):
        corpo = re.sub(r"^\s*<\?php\s*", "", t)
        m = re.match(r"\s*((?://[^\n]*\n\s*)+)", corpo)
        if m:
            blocos.append(re.sub(r"^\s*//\s?", "", m.group(1), flags=re.M))
        else:
            m = re.search(r"/\*\*?(.*?)\*/", corpo, re.S)
            if m:
                blocos.append(re.sub(r"^\s*\*\s?", "", m.group(1), flags=re.M))
            else:
                m = re.search(r"^\s*(?:final\s+|abstract\s+)?class\s+(\w+)(?:\s+extends\s+([\w\\]+))?", corpo, re.M)
                if m:
                    blocos.append(f"classe {m.group(1)}" + (f" (estende {m.group(2)})" if m.group(2) else ""))
    if not blocos:
        linhas = [ln for ln in t.splitlines()[:40] if ln.startswith("#") and not ln.startswith("#!")]
        if linhas:
            blocos.append("\n".join(ln.lstrip("# ") for ln in linhas[:6]))
    if not blocos:
        return "(sem cabecalho)" if not nome.endswith((".tsv", ".txt", ".csv")) else "(dados)"
    d = " ".join(" ".join(blocos).split())
    return d[:MAX_DESCRICAO] + ("..." if len(d) > MAX_DESCRICAO else "")


def _git(config: Config, args: list[str], runner: Callable[..., Any]) -> subprocess.CompletedProcess | None:
    try:
        return runner(["git", "-C", str(config.raiz), *args], capture_output=True, timeout=20,
                      stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.SubprocessError):
        return None


def ferramentas_do_grupo(config: Config, ref: str | None = "origin/base-php74",
                         git_runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    """Lista scratchpad/ (arvore de trabalho) e, se `ref` existir, o scratchpad/ dessa branch, com a descricao
    do cabecalho de cada arquivo. So leitura; caminhos confinados; a ref e validada e vai como argumento fixo."""
    itens: dict[str, dict[str, Any]] = {}
    avisos: list[str] = []
    raiz = config.raiz.resolve()
    sp = raiz / "scratchpad"
    if sp.is_dir():
        base = resolver_caminho(config.raiz, "scratchpad", tipo="diretorio")
        for p in sorted(base.rglob("*")):
            if len(itens) >= MAX_FERRAMENTAS:
                avisos.append(f"lista cortada em {MAX_FERRAMENTAS} arquivos")
                break
            if not p.is_file() or "__pycache__" in p.parts or p.name.startswith("."):
                continue
            alvo = p.resolve()
            if raiz not in alvo.parents or eh_negado(alvo.relative_to(raiz)) or eh_negado(p.relative_to(raiz)):
                continue
            try:
                texto = decodificar(alvo.read_bytes()[:6000])
            except OSError:
                continue
            rel = relativo(config.raiz, p)
            itens[rel] = {"arquivo": rel, "origem": "arvore de trabalho",
                          "descricao": descricao_do_cabecalho(p.name, texto)}
    else:
        avisos.append("scratchpad/ nao existe nesta arvore de trabalho")
    if ref:
        if not _REF.match(ref) or ".." in ref:
            raise ErroFerramenta("parametro_invalido", "ref invalida (ex.: origin/base-php74)")
        r = _git(config, ["ls-tree", "-r", "--name-only", ref, "--", "scratchpad"], git_runner)
        if r is None or r.returncode != 0:
            avisos.append(f"ref {ref!r} indisponivel (git fetch?): so a arvore de trabalho foi listada")
        else:
            for caminho in decodificar(r.stdout).splitlines():
                if len(itens) >= MAX_FERRAMENTAS:
                    break
                caminho = caminho.strip()
                if (not caminho.startswith("scratchpad/") or ".." in caminho.split("/") or caminho in itens
                        or eh_negado(Path(caminho)) or "__pycache__" in caminho
                        or Path(caminho).name.startswith(".")):
                    continue
                c = _git(config, ["show", f"{ref}:{caminho}"], git_runner)
                texto = decodificar((c.stdout if c is not None and c.returncode == 0 else b"")[:6000])
                itens[caminho] = {"arquivo": caminho, "origem": f"so em {ref}",
                                  "descricao": descricao_do_cabecalho(caminho, texto),
                                  "como_obter": f"git show {ref}:{caminho}"}
    destaques = [i for i in itens if any(k in i for k in ("cmp.py", "escrita.php", "escrita_post.py",
                                                            "rector-rules/", "rector-curado.php"))]
    return {"ferramentas": sorted(itens.values(), key=lambda x: x["arquivo"]), "destaques": sorted(destaques),
            "avisos": avisos,
            "lembrete": "scratchpad/ fica fora do bind mount do conteiner: copie com docker cp antes de rodar la "
                        "dentro; saida do Rector vai em commit separado"}
