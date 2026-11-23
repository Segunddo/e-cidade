"""Gerador deterministico dos casos por rota a partir de `casos/_inventario.tsv`.

Regra de seguranca (a que importa): so vira caso a rota que o gerador sabe exercitar SEM escrever
de proposito. Rota com parametro de caminho (`{id}`, `{id?}`) nao e gerada (nunca se manda
DELETE/PUT com id de verdade); rota cujo URI/acao carrega um verbo destrutivo tambem nao.
GET ganha um caso autenticado; POST/PUT/PATCH/DELETE ganham uma SONDA com corpo `{}` (exercita
roteamento, middleware e validacao). O que fica de fora e listado com o motivo.

Ajustes que a regeneracao preserva ficam em `casos/_ajustes.yml`:
  volateis:  {<id do caso>: [caminhos para mascarar]}
  instaveis: {<id do caso>: "motivo"}   # vao para `_instaveis.yml` (nao carregado por padrao)
  perigosas: {<id do caso>: "motivo"}   # sonda que ESCREVEU ao vivo: deixa de ser gerada
  permitidas: [<id do caso>, ...]       # allowlist de DELETE/PUT/PATCH (vazia por padrao)
  sem_ordem: {<id do caso>: [caminhos de listas]}  # API sem ordem garantida: compara o conjunto ordenado

Uso: python -m regressao.laravel.gerador
"""
import re
import sys
from pathlib import Path

import yaml

from regressao.laravel.caso import DIR_CASOS, CasoHttp
from regressao.laravel.rotas import ARQ_INVENTARIO, ORIGENS, Rota

ARQ_AJUSTES = DIR_CASOS / "_ajustes.yml"
_RE_PARAM = re.compile(r"\{[^}]*\}")
_RE_URI_OK = re.compile(r"[\w./-]+")  # o mesmo alfabeto de ids aceito por caso.carrega_casos
# Vocabulario do brief: vale para QUALQUER metodo (URI ou acao do controller).
PERIGOSA = re.compile(r"delete|destroy|truncate|reset|import|sync|logout|migrate", re.I)
# Quem escreve (nao-GET) evita tambem os verbos de efeito do dominio, em portugues.
PERIGOSA_ESCRITA = re.compile(
    PERIGOSA.pattern + r"|exclu|remov|apag|cancel|desfaz|desprocess|desvincul|inativ|desativ"
    r"|recalcul|processar|baix|estorn|arquiv|devolv|duplic|rejeit|aprov|limp|clear", re.I)
METODOS_DESTRUTIVOS = frozenset({"DELETE", "PUT", "PATCH"})  # so com `permitidas` em _ajustes.yml
CABECALHO = ("# GERADO por `python -m regressao.laravel.gerador` a partir de _inventario.tsv: "
             "nao edite a mao.\n# Ajustes (volateis/instaveis) ficam em _ajustes.yml.\n")


def tem_parametro(uri: str) -> bool:
    return bool(_RE_PARAM.search(uri))


def metodo_efetivo(metodo: str) -> str:
    """`GET|HEAD` -> GET; `PUT|PATCH` -> PUT; demais, o proprio."""
    return metodo.split("|")[0]


def motivo_nao_gerada(r: Rota, ajustes: dict | None = None) -> str | None:
    """None se a rota pode virar caso; senao o motivo (vai para o relatorio de cobertura).
    `ajustes["perigosas"]` (id -> motivo) traz o que a gravacao ao vivo provou: sonda que
    ESCREVEU no banco mesmo com corpo vazio."""
    provada = ((ajustes or {}).get("perigosas") or {}).get(id_do_caso(r))
    if provada:
        return f"rota perigosa (provada ao vivo): {provada}"
    achado = _RE_PARAM.search(r.caminho)
    if achado:
        return f"parametro de caminho {achado.group(0)}: nao se envia id real"
    if not _RE_URI_OK.fullmatch(r.caminho):
        return (f"caractere fora de [A-Za-z0-9_./-] na uri {r.caminho!r} (ex.: espaco no fim, erro do proprio "
                "arquivo de rotas): o id do caso seria invalido")
    if metodo_efetivo(r.metodo) in METODOS_DESTRUTIVOS and \
            id_do_caso(r) not in ((ajustes or {}).get("permitidas") or []):
        return "metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados"
    padrao = PERIGOSA if metodo_efetivo(r.metodo) == "GET" else PERIGOSA_ESCRITA
    alvo = f"{r.caminho} {r.controller}"
    m = padrao.search(alvo)
    if m:
        return f"rota perigosa ({m.group(0).lower()}): nao e sondada"
    return None


def id_do_caso(r: Rota) -> str:
    return f"rota:{metodo_efetivo(r.metodo)}:{r.caminho}"


def caso_para(r: Rota, ajustes: dict) -> CasoHttp:
    metodo = metodo_efetivo(r.metodo)
    cid = id_do_caso(r)
    return CasoHttp(
        id=cid, metodo=metodo, caminho=r.caminho,
        corpo=None if metodo == "GET" else {},
        autenticado=r.origem != "silex",  # Silex nao usa Bearer: id+hash no corpo
        campos_volateis=list((ajustes.get("volateis") or {}).get(cid, [])),
        espera_escrita=False,
        listas_sem_ordem=list((ajustes.get("sem_ordem") or {}).get(cid, [])))


def _ordem(r: Rota):
    return (r.caminho, metodo_efetivo(r.metodo), r.controller)


def _geraveis(rotas: list[Rota], ajustes: dict | None = None) -> list[Rota]:
    """Rotas geraveis, ordenadas, sem ids repetidos (a primeira vence)."""
    vistos: set[str] = set()
    saida: list[Rota] = []
    for r in sorted(rotas, key=_ordem):
        if motivo_nao_gerada(r, ajustes) is not None or id_do_caso(r) in vistos:
            continue
        vistos.add(id_do_caso(r))
        saida.append(r)
    return saida


def gera(rotas: list[Rota], ajustes: dict | None = None) -> dict[str, list[CasoHttp]]:
    """origem -> casos ordenados (por URI, metodo), SEM os marcados como instaveis."""
    ajustes = ajustes or {}
    instaveis = set((ajustes.get("instaveis") or {}))
    saida: dict[str, list[CasoHttp]] = {o: [] for o in ORIGENS}
    for r in _geraveis(rotas, ajustes):
        if id_do_caso(r) not in instaveis:
            saida[r.origem].append(caso_para(r, ajustes))
    return saida


def gera_instaveis(rotas: list[Rota], ajustes: dict) -> list[tuple[CasoHttp, str]]:
    instaveis = ajustes.get("instaveis") or {}
    return [(caso_para(r, ajustes), str(instaveis[id_do_caso(r)]))
            for r in _geraveis(rotas, ajustes) if id_do_caso(r) in instaveis]


def nao_geradas(rotas: list[Rota], ajustes: dict | None = None) -> list[tuple[Rota, str]]:
    """Rotas que o gerador recusa, com o motivo; ordenadas por origem/uri/metodo."""
    pares = [(r, m) for r in rotas if (m := motivo_nao_gerada(r, ajustes)) is not None]
    return sorted(pares, key=lambda p: (p[0].origem, p[0].caminho, p[0].metodo))


# ---------------------------------------------------------------- entrada/saida

def le_inventario(arquivo: Path = ARQ_INVENTARIO) -> list[Rota]:
    linhas = Path(arquivo).read_text(encoding="utf-8").splitlines()[1:]
    rotas = []
    for l in linhas:
        if not l.strip():
            continue
        campos = l.split("\t")
        if len(campos) == 5:  # inventario anterior, sem a coluna erro_controller
            campos.append("")
        metodo, uri, mw, acao, origem, erro = campos
        rotas.append(Rota(metodo, uri, [m for m in mw.split(",") if m], acao, origem, erro))
    return rotas


def le_ajustes(arquivo: Path = ARQ_AJUSTES) -> dict:
    try:
        dados = yaml.safe_load(Path(arquivo).read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    if not isinstance(dados, dict):
        raise ValueError(f"{Path(arquivo).name}: esperava um mapa")
    extra = set(dados) - {"volateis", "instaveis", "perigosas", "permitidas", "sem_ordem"}
    if extra:
        raise ValueError(f"{Path(arquivo).name}: chaves desconhecidas {sorted(extra)}")
    return dados


def _bloco(c: CasoHttp, comentario: str = "") -> str:
    d: dict = {"id": c.id, "metodo": c.metodo, "caminho": c.caminho}
    if c.corpo is not None:
        d["corpo"] = c.corpo
    if not c.autenticado:
        d["autenticado"] = False
    if c.campos_volateis:
        d["campos_volateis"] = list(c.campos_volateis)
    if c.listas_sem_ordem:
        d["listas_sem_ordem"] = list(c.listas_sem_ordem)
    texto = yaml.safe_dump([d], sort_keys=False, allow_unicode=True, width=10000)
    return (f"# {comentario}\n" if comentario else "") + texto


def _grava(arq: Path, texto: str) -> None:
    arq.write_bytes(texto.encode("utf-8"))  # LF, UTF-8, sem BOM


def escreve(destino: Path, rotas: list[Rota] | None = None, ajustes: dict | None = None) -> list[Path]:
    """Escreve `rotas_<origem>.yml` (um por origem) e, se houver, `_instaveis.yml`.
    Idempotente: mesma entrada -> mesmos bytes."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    rotas = le_inventario() if rotas is None else rotas
    ajustes = le_ajustes() if ajustes is None else ajustes
    grupos = gera(rotas, ajustes)
    arquivos: list[Path] = []
    for origem in ORIGENS:
        arq = destino / f"rotas_{origem}.yml"
        corpo = "".join(_bloco(c) for c in grupos[origem]) or "[]\n"
        _grava(arq, CABECALHO + corpo)
        arquivos.append(arq)
    arq_inst = destino / "_instaveis.yml"
    inst = gera_instaveis(rotas, ajustes)
    if inst:
        _grava(arq_inst, CABECALHO.replace("nao edite a mao", "NAO carregado por padrao")
               + "".join(_bloco(c, f"instavel: {motivo}") for c, motivo in inst))
        arquivos.append(arq_inst)
    elif arq_inst.exists():
        arq_inst.unlink()
    return arquivos


def main() -> int:
    rotas = le_inventario()
    ajustes = le_ajustes()
    arquivos = escreve(DIR_CASOS, rotas, ajustes)
    grupos = gera(rotas, ajustes)
    nc = nao_geradas(rotas, ajustes)
    print("casos gerados: " + ", ".join(f"{o}={len(grupos[o])}" for o in ORIGENS)
          + f"; instaveis={len(gera_instaveis(rotas, ajustes))}; nao geradas={len(nc)}; "
          f"rotas={len(rotas)}")
    for a in arquivos:
        print("  " + a.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
