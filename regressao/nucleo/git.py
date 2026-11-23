"""Fatos do git para o `meta` das rodadas: certos ou explicitamente indisponiveis (nunca vazios).

`safe.directory` e passado por comando: rodar como outro usuario (ex.: root no WSL) nao pode
virar um commit vazio por causa de "dubious ownership".
"""
import subprocess
from pathlib import Path

LIMITE_ARQUIVOS = 20


def _roda(args: list[str]) -> subprocess.CompletedProcess:
    """Unico ponto de chamada ao git (substituivel nos testes)."""
    return subprocess.run(args, capture_output=True, text=True, timeout=30)


def _git(raiz: Path, *args: str, runner=None) -> tuple[str | None, str]:
    """(saida, erro): saida None se falhou; erro = 1a linha de stderr (ou o tipo da excecao)."""
    raiz = str(raiz)
    cmd = ["git", "-c", f"safe.directory={raiz}", "-C", raiz, *args]
    try:
        r = (runner or _roda)(cmd)
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}: {e}".splitlines()[0]
    if r.returncode != 0:
        linhas = (r.stderr or "").strip().splitlines()
        return None, linhas[0] if linhas else f"git saiu com codigo {r.returncode}"
    return r.stdout or "", ""


def commit(raiz: Path, curto: bool = False, runner=None) -> str:
    saida, erro = _git(raiz, "rev-parse", *(["--short"] if curto else []), "HEAD", runner=runner)
    if saida is None:
        return f"indisponivel: {erro}"
    return saida.strip() or "indisponivel: git rev-parse sem saida"


def sujo(raiz: Path, runner=None) -> dict:
    """{"git_sujo": bool | "indisponivel: ...", "git_sujo_arquivos": [ate 20 entradas]}."""
    saida, erro = _git(raiz, "status", "--porcelain", runner=runner)
    if saida is None:
        return {"git_sujo": f"indisponivel: {erro}", "git_sujo_arquivos": []}
    linhas = [l for l in saida.splitlines() if l.strip()]
    return {"git_sujo": bool(linhas), "git_sujo_arquivos": linhas[:LIMITE_ARQUIVOS]}


def sujo_regressao(raiz: Path, runner=None) -> dict:
    """Como `sujo`, mas so a pasta `regressao/` (o repo inteiro costuma estar sujo por causa do
    ambiente Docker: este flag diz se o CODIGO DA BATERIA que rodou tem alteracoes nao commitadas).
    Chaves proprias, para nunca se misturar com `git_sujo`."""
    saida, erro = _git(raiz, "status", "--porcelain", "--", "regressao", runner=runner)
    if saida is None:
        return {"git_sujo_regressao": f"indisponivel: {erro}", "git_sujo_regressao_arquivos": []}
    linhas = [l for l in saida.splitlines() if l.strip()]
    return {"git_sujo_regressao": bool(linhas), "git_sujo_regressao_arquivos": linhas[:LIMITE_ARQUIVOS]}
