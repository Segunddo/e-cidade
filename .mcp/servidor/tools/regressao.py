"""rodar_regressao / ler_resultado_regressao / ler_triagem.

A suite `regressao/` roda no host com o venv dela (ela mesma orquestra os conteineres e74 por HTTP e
`docker exec`; o codigo dela nao esta montado nos conteineres). A tool so dispara comandos FIXOS da suite, em
processo destacado, depois de conferir os conteineres; nunca `gravar` baseline (protecao da referencia).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import secrets
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from servidor.config import Config
from servidor.docker_exec import DockerExec
from servidor.seguranca import ErroFerramenta, limitar, limpar_texto, relativo, resolver_caminho, validar_regex

AREAS = ("assistenciasocial", "cidadao", "configuracao", "educacao", "financeiro", "gestor", "integracoes",
         "patrimonial", "recursoshumanos", "saude", "tributario")
BATERIAS = ("php", "laravel", "fluxos", "completa")
VEREDITOS = ("IDENTICO", "DIVERGE", "INCONCLUSIVO", "ERRO_AMBIENTE")
_ID = re.compile(r"^\d{8}-\d{6}-(php|laravel|fluxos|completa)-[0-9a-f]{4}$")
_FLUXO = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
EXECUTOR = Path(__file__).resolve().parents[1] / "executor.py"
AVISO = ("INCONCLUSIVO e ERRO_AMBIENTE NUNCA sao aprovacao: INCONCLUSIVO = caso nao exercitado (lacuna), "
         "ERRO_AMBIENTE = nada se conclui. O gabarito e a referencia PHP 7.4/Laravel 8. A bateria PHP mede paridade "
         "7.4 x 8.5 sobre o MESMO codigo (nao detecta bug igual nos dois lados).")
SIGNIFICADO_SAIDA = {0: "sem DIVERGE nova e sem ERRO_AMBIENTE (leia INCONCLUSIVO e a cobertura antes de confiar)",
                     1: "ha DIVERGE nao conhecida: achado real (veja divergencias_novas e diffs/)",
                     2: "ERRO_AMBIENTE ou rodada invalida: nada se conclui"}


def _agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cmdline_executor(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError, OverflowError):
        return False
    try:
        return b"executor.py" in Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False


def _rodada_manual() -> str | None:
    """Rodada da suite disparada FORA do MCP (atalho regressao/bin/regressao ou `python -m regressao...` a mao):
    descricao dela, ou None. Ve a trava do atalho (~/rodadas/.em-andamento ou $REGRESSAO_RODADAS) com pid vivo e
    qualquer processo `-m regressao.`; as duas restauram o mesmo banco que a rodada do MCP restauraria."""
    trava = Path(os.environ.get("REGRESSAO_RODADAS") or Path.home() / "rodadas") / ".em-andamento"
    try:
        pid_txt, _, pasta = trava.read_text(encoding="utf-8").strip().partition("\t")
        os.kill(int(pid_txt), 0)
        return f"rodada do atalho regressao/bin/regressao em {Path(pasta).name or pasta} (trava {trava.name})"
    except (OSError, ValueError, OverflowError):
        pass
    try:
        r = subprocess.run(["pgrep", "-f", "--", r"-m regressao\."], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    pids = r.stdout.split() if r.returncode == 0 else []
    return f"processo da suite rodando (pgrep -af 'm regressao\\.': pid {', '.join(pids[:5])})" if pids else None


INICIO_TOLERANCIA_S = 120  # meta.json sem pid ha menos que isso = rodada ainda iniciando (bloqueia outra)
BLOQUEIAM = ("em_andamento", "iniciando", "desconhecida")


def _ler_meta(d: Path) -> dict[str, Any]:
    try:
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ErroFerramenta("estado_corrompido", f"{d.name}/meta.json ilegivel ({type(e).__name__}); se a rodada "
                             "nao existe mais, apague a pasta em .mcp/rodadas/") from None
    if (not isinstance(meta, dict) or not isinstance(meta.get("bateria", ""), str)
            or not (meta.get("pid") is None or isinstance(meta.get("pid"), int))):
        raise ErroFerramenta("estado_corrompido", f"{d.name}/meta.json com formato invalido; apague a pasta se a "
                             "rodada nao existe mais")
    return meta


def _status(d: Path, vivo: Callable[[int], bool]) -> tuple[str, int | None]:
    fim = d / "fim.json"
    if fim.is_file():
        try:
            cod = json.loads(fim.read_text(encoding="utf-8")).get("codigo_saida")
            return "concluida", cod if isinstance(cod, int) else None
        except (json.JSONDecodeError, OSError, AttributeError):
            return "concluida", None
    try:
        meta = _ler_meta(d)
    except ErroFerramenta:
        return "desconhecida", None  # conservador: BLOQUEIA nova rodada (veja BLOQUEIAM)
    pid = meta.get("pid")
    if pid is None:  # meta gravado, Popen ainda nao devolveu (ou o servidor caiu no meio)
        try:
            idade = time.time() - (d / "meta.json").stat().st_mtime
        except OSError:
            return "desconhecida", None
        return ("iniciando" if idade < INICIO_TOLERANCIA_S else "interrompida"), None
    return ("em_andamento" if pid > 0 and vivo(pid) else "interrompida"), None


@contextmanager
def _trava_rodadas(config: Config, espera_s: float = 30.0):
    """Trava de arquivo cobrindo verificacao + criacao + Popen: duas IAs nao disparam rodadas juntas."""
    config.dir_rodadas.mkdir(parents=True, exist_ok=True)
    fd = os.open(config.dir_rodadas / ".lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        limite = time.monotonic() + espera_s
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > limite:
                    raise ErroFerramenta("rodada_em_andamento", "outra rodada esta sendo disparada agora") from None
                time.sleep(0.05)
        yield
    finally:
        os.close(fd)


def _grava_meta(d: Path, meta: dict[str, Any]) -> None:
    tmp = d / "meta.json.tmp"
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, d / "meta.json")


def _argv(config: Config, bateria: str, saida: Path, area: list[str], prefixo: list[str], fluxo: list[str],
          sem_fluxos: bool) -> list[str]:
    base = [str(config.raiz / config.python_regressao), "-m"]
    if bateria == "php":
        return base + ["regressao.php.bateria", "--saida", str(saida)] + \
            [f"--area={a}" for a in area] + [f"--prefixo={p}" for p in prefixo]
    if bateria == "laravel":
        return base + ["regressao.laravel.bateria", "comparar", "--saida", str(saida)]
    if bateria == "fluxos":
        return base + ["regressao.completa.fluxos", "comparar", "--saida", str(saida)] + [f"--fluxo={f}" for f in fluxo]
    return base + ["regressao.completa.orquestra", "--saida", str(saida)] + \
        [f"--area={a}" for a in area] + [f"--prefixo={p}" for p in prefixo] + (["--sem-fluxos"] if sem_fluxos else [])


def rodar_regressao(
    config: Config,
    bateria: str,
    area: list[str] | None = None,
    prefixo: list[str] | None = None,
    fluxo: list[str] | None = None,
    sem_fluxos: bool = False,
    confirmo_rodada_longa: bool = False,
    quem: str | None = None,
    docker: DockerExec | None = None,
    popen: Callable[..., Any] = subprocess.Popen,
    _cmdline_executor: Callable[[int], bool] = _cmdline_executor,
    _rodada_manual: Callable[[], str | None] = _rodada_manual,
) -> dict[str, Any]:
    area, prefixo, fluxo = list(area or []), list(prefixo or []), list(fluxo or [])
    if bateria not in BATERIAS:
        raise ErroFerramenta("parametro_invalido", f"bateria: {', '.join(BATERIAS)}")
    for a in area:
        if a not in AREAS:
            raise ErroFerramenta("parametro_invalido", f"area {a!r}; validas: {', '.join(AREAS)}")
    if len(area) > len(AREAS) or len(prefixo) > 10 or len(fluxo) > 10:
        raise ErroFerramenta("parametro_invalido", "no maximo 10 prefixos/fluxos")
    for p in prefixo:
        validar_regex(p)
    for f in fluxo:
        if not _FLUXO.match(f):
            raise ErroFerramenta("parametro_invalido", f"fluxo invalido: {f!r}")
    if (area or prefixo) and bateria not in ("php", "completa"):
        raise ErroFerramenta("parametro_invalido", "area/prefixo so valem para as baterias php e completa")
    if fluxo and bateria != "fluxos":
        raise ErroFerramenta("parametro_invalido", "fluxo so vale para a bateria fluxos")
    if bateria in ("php", "completa") and not (area or prefixo) and not confirmo_rodada_longa:
        raise ErroFerramenta("confirmacao_necessaria",
                             "sem area/prefixo a bateria PHP roda ~12 mil telas (HORAS). Restrinja com prefixo "
                             "(ex.: '^arr1_') ou passe confirmo_rodada_longa=true")
    if bateria == "laravel" and not confirmo_rodada_longa:
        raise ErroFerramenta("confirmacao_necessaria",
                             "a bateria laravel restaura o banco e roda todos os 992 casos (~16 min); confirme com "
                             "confirmo_rodada_longa=true")
    if bateria == "fluxos" and not fluxo and not confirmo_rodada_longa:
        raise ErroFerramenta("confirmacao_necessaria",
                             "sem `fluxo` roda todos os fluxos de navegador; escolha fluxo=[...] ou passe "
                             "confirmo_rodada_longa=true")

    py = config.raiz / config.python_regressao
    if not py.is_file():
        raise ErroFerramenta("venv_regressao_ausente",
                             f"{config.python_regressao} nao existe: python3 -m venv regressao/.venv && "
                             "regressao/.venv/bin/pip install -r regressao/requirements.txt")
    docker = docker or DockerExec(config)
    for nome in (config.container_ref, config.container_alvo, config.container_banco):
        docker.verificar_conteiner(nome)

    with _trava_rodadas(config):
        for d in sorted(config.dir_rodadas.iterdir()):
            if not (d.is_dir() and _ID.match(d.name)):
                continue
            st = _status(d, _cmdline_executor)[0]
            if st in BLOQUEIAM:
                raise ErroFerramenta("rodada_em_andamento",
                                     f"a rodada {d.name} esta '{st}' (cada bateria restaura o banco: duas juntas se "
                                     "atrapalham). Acompanhe com ler_resultado_regressao; se ela nao existe mais, "
                                     "apague a pasta em .mcp/rodadas/", id=d.name, status=st)
        if manual := _rodada_manual():
            raise ErroFerramenta("rodada_em_andamento",
                                 f"ha uma rodada da regressao fora do MCP: {manual}. Cada bateria restaura o banco: "
                                 "espere ela terminar (regressao/bin/regressao ver-ultimo)", status="manual")

        rid = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{bateria}-{secrets.token_hex(2)}"
        d = config.dir_rodadas / rid
        d.mkdir()
        argv = _argv(config, bateria, d / "saida", area, prefixo, fluxo, sem_fluxos)
        meta = {"id": rid, "bateria": bateria, "argv": argv, "raiz": str(config.raiz), "inicio": _agora_iso(),
                "quem": limpar_texto(quem or config.usuario or "", 80), "pid": None}
        _grava_meta(d, meta)
        with open(d / "execucao.log", "wb") as log:
            proc = popen([sys.executable, str(EXECUTOR), str(d / "meta.json")], cwd=str(config.raiz),
                         stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                         close_fds=True)
        meta["pid"] = proc.pid
        _grava_meta(d, meta)
    return {"id": rid, "status": "iniciada", "pasta": relativo(config.raiz, d), "comando": argv[2:],
            "acompanhe": f"ler_resultado_regressao(id='{rid}')",
            "duracao_esperada": "restauracao do banco ~4 min + casos (prefixo pequeno ~5-6 min; area inteira: horas)"}


def _cauda(p: Path, n: int = 30) -> str:
    try:
        linhas = p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return ""
    return limitar("\n".join(linhas), 4000)[0]


def _resultado(saida: Path, max_itens: int, veredito: str | None) -> dict[str, Any] | None:
    arq = saida / "resultado.json"
    if not arq.is_file():
        return None
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        casos = dados["casos"]
        if not isinstance(dados, dict) or not isinstance(casos, list) or not all(isinstance(c, dict) for c in casos):
            raise TypeError("casos precisa ser lista de objetos")
    except (json.JSONDecodeError, KeyError, OSError, TypeError, UnicodeDecodeError) as e:
        raise ErroFerramenta("estado_corrompido", f"resultado.json com formato invalido: {str(e)[:200]}") from None
    totais = {v: 0 for v in VEREDITOS}
    for c in casos:
        v = str(c.get("veredito", "?"))[:30]
        totais[v] = totais.get(v, 0) + 1
    novas = [c for c in casos if c.get("veredito") == "DIVERGE" and not c.get("conhecida")]
    erros = [c for c in casos if c.get("veredito") == "ERRO_AMBIENTE"]
    inc = Counter(str(c.get("detalhe") or "")[:100] for c in casos if c.get("veredito") == "INCONCLUSIVO")

    def corta(xs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{k: (str(c.get(k))[:300] if c.get(k) is not None else None) for k in ("id", "area", "detalhe")}
                for c in xs[:max_itens]]
    r: dict[str, Any] = {
        "totais": totais, "total_casos": len(casos),
        "divergencias_novas": corta(novas), "divergencias_novas_total": len(novas),
        "divergencias_conhecidas_total": sum(1 for c in casos if c.get("veredito") == "DIVERGE" and c.get("conhecida")),
        "erros_ambiente": corta(erros), "inconclusivo_por_motivo": dict(inc.most_common(15)),
        "meta": {k: v for k, v in (dados.get("meta") if isinstance(dados.get("meta"), dict) else {}).items()
                 if k in ("tipo", "comparavel", "versoes", "baseline_sha256", "tempos_s", "baterias", "git_commit")},
    }
    if veredito:
        r["filtrados"] = corta([c for c in casos if c.get("veredito") == veredito])
    resumo = saida / "resumo.md"
    if resumo.is_file():
        r["resumo_md"] = limitar(resumo.read_text(encoding="utf-8", errors="replace"), 6000)[0]
    return r


def ler_resultado_regressao(
    config: Config,
    id: str | None = None,
    pasta: str | None = None,
    max_itens: int = 50,
    veredito: str | None = None,
    _cmdline_executor: Callable[[int], bool] = _cmdline_executor,
) -> dict[str, Any]:
    if veredito and veredito not in VEREDITOS:
        raise ErroFerramenta("parametro_invalido", f"veredito: {', '.join(VEREDITOS)}")
    if not (1 <= max_itens <= 500):
        raise ErroFerramenta("parametro_invalido", "max_itens entre 1 e 500")
    if pasta:
        d = resolver_caminho(config.raiz, pasta, tipo="diretorio")
        res = _resultado(d, max_itens, veredito) or _resultado(d / "saida", max_itens, veredito)
        if res is None:
            raise ErroFerramenta("rodada_inexistente", f"{pasta} nao tem resultado.json")
        return {"pasta": relativo(config.raiz, d), **res, "aviso": AVISO}
    if id is None:
        rodadas = []
        if config.dir_rodadas.is_dir():
            for d in sorted((x for x in config.dir_rodadas.iterdir() if x.is_dir() and _ID.match(x.name)),
                            key=lambda x: x.name, reverse=True)[:20]:
                st, cod = _status(d, _cmdline_executor)
                rodadas.append({"id": d.name, "bateria": d.name.split("-")[2], "status": st, "codigo_saida": cod})
        return {"rodadas": rodadas, "dica": "chame com id=<id> para o detalhe"}
    if not _ID.match(id or ""):
        raise ErroFerramenta("parametro_invalido", "id no formato AAAAMMDD-HHMMSS-<bateria>-xxxx")
    d = config.dir_rodadas / id
    if not d.is_dir():
        raise ErroFerramenta("rodada_inexistente", f"rodada {id} nao existe em .mcp/rodadas/")
    st, cod = _status(d, _cmdline_executor)
    meta = _ler_meta(d)  # formato invalido -> estado_corrompido (nunca erro_interno)
    r: dict[str, Any] = {"id": id, "bateria": meta.get("bateria"), "status": st, "inicio": meta.get("inicio"),
                         "quem": meta.get("quem"), "codigo_saida": cod,
                         "significado_saida": SIGNIFICADO_SAIDA.get(cod) if cod is not None else None,
                         "log_final": _cauda(d / "execucao.log")}
    res = _resultado(d / "saida", max_itens, veredito)
    if res is None:
        alt = next(iter(sorted((d / "saida").glob("*/resultado.json"))), None) if (d / "saida").is_dir() else None
        res = _resultado(alt.parent, max_itens, veredito) if alt else None
    if res:
        r.update(res)
    elif st == "em_andamento":
        r["dica"] = "ainda rodando: chame de novo em alguns minutos"
    r["aviso"] = AVISO
    return r


# ---------- triagem ----------

DOCUMENTOS = {
    "triagem": "regressao/baseline/triagem-divergencias.md",
    "decisoes": "regressao/baseline/decisoes-migracao.md",
    "lab_lar12": "regressao/baseline/lab-lar12-resultado.md",
    "como_usar": "regressao/COMO-USAR.md",
}
_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def ler_triagem(config: Config, documento: str = "triagem", secao: str | None = None,
                busca: str | None = None) -> dict[str, Any]:
    if documento not in DOCUMENTOS:
        raise ErroFerramenta("parametro_invalido", f"documento: {', '.join(DOCUMENTOS)}")
    rel = DOCUMENTOS[documento]
    try:
        arq = resolver_caminho(config.raiz, rel, tipo="arquivo")
    except ErroFerramenta as e:
        if e.codigo == "caminho_inexistente":
            raise ErroFerramenta("documento_inexistente", f"{rel} ainda nao existe nesta branch") from None
        raise
    linhas = arq.read_text(encoding="utf-8", errors="replace").splitlines()
    secoes = []
    em_codigo = False
    for i, l in enumerate(linhas, start=1):
        if l.lstrip().startswith("```"):
            em_codigo = not em_codigo
        m = None if em_codigo else _TITULO.match(l)
        if m:
            secoes.append({"titulo": m.group(2), "nivel": len(m.group(1)), "linha": i})
    cab = " ".join(linhas[:3])
    # os documentos da rodada "antes74" (gabarito 7.4) substituiram os da migracao 5.6 -> 8.5; o rotulo historico
    # so aparece se alguem ler um documento antigo (outra branch)
    base = "7.4 x 8.5" if "7.4" in cab else ("5.6 x 8.5 (historico: gabarito antigo)" if "5.6" in cab else "?")
    resumo = None
    for k, s in enumerate(secoes):
        if s["nivel"] == 2 and _norm(s["titulo"]).startswith("resumo"):
            fim = next((t["linha"] - 1 for t in secoes[k + 1:] if t["nivel"] <= 2), len(linhas))
            resumo = limitar("\n".join(linhas[s["linha"] - 1:fim]).strip(), 6000)[0]
            break
    r: dict[str, Any] = {"documento": rel, "base": base, "resumo": resumo, "secoes": secoes}
    if secao:
        alvo = _norm(secao)
        partes = []
        for k, s in enumerate(secoes):
            if alvo in _norm(s["titulo"]):
                fim = next((t["linha"] - 1 for t in secoes[k + 1:] if t["nivel"] <= s["nivel"]), len(linhas))
                partes.append("\n".join(linhas[s["linha"] - 1:fim]).strip())
        if not partes:
            raise ErroFerramenta("secao_inexistente", f"nenhuma secao com {secao!r}; veja `secoes`")
        r["texto"] = limitar("\n\n".join(partes), config.max_saida)[0]
    elif busca:
        alvo = _norm(busca)
        r["linhas"] = [{"linha": i, "texto": l} for i, l in enumerate(linhas, start=1) if alvo in _norm(l)][:100]
    else:
        r["texto"], r["truncado"] = limitar("\n".join(linhas), config.max_saida)
    return r
