"""Orquestrador da bateria PHP (referencia PHP 7.4 x alvo PHP 8.5): ambiente -> baseline -> restauracao -> sessao ->
sintaxe -> classes -> telas -> POSTs -> relatorios -> conhecidas -> escreve_rodada.

    python -m regressao.php.bateria --saida DIR [--area NOME ...] [--sem-normalizar]
        [--prefixo REGEX ...] [--incluir-nao-verificados] [--sem-restaurar]

Ids dos casos (namespace por etapa; chaves de conhecidas.tsv usam a mesma forma):
sintaxe:<arq>, classe:<arq>, tela:<tela>, tela-run:<prefixo>:<id>, post:<tela>,
relatorio:<tela>[?<query>], passo:<nome>. Duplicata residual ganha sufixo #2, #3...

--prefixo REGEX (repetivel): areas nao sao pequenas (assistenciasocial 755 telas, configuracao
5394, financeiro 6601, tributario 5469); a regex e aplicada (re.match, sem diferenciar caixa) ao
nome do arquivo da tela: so as telas que casam entram, e so as linhas dos catalogos cuja `tela`
casa. Sem --area, parte de todas as areas.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
from contextlib import contextmanager, nullcontext
from dataclasses import replace
from pathlib import Path

from regressao.nucleo import git
from regressao.nucleo.ambiente import alvos_do_ambiente, containers_do_ambiente, verifica
from regressao.nucleo.banco import (ARQ_DUMP, ARQ_SHA256, BancoDiferente, ErroAmbienteBanco,
                                    _docker, confere_baseline, restaura_dump)
from regressao.nucleo.conhecidas import carregar_conhecidas, marcar
from regressao.nucleo.normaliza import REGRAS, hash_corpo
from regressao.nucleo.relatorio import RodadaInvalida, escreve_rodada
from regressao.nucleo.veredito import Caso, Veredito, codigo_saida
from regressao.php.classes import roda_classes
from regressao.php.cobertura import cobertura_de_flags, tem_dados
from regressao.php.hashes import grava_hashes_de_hashes
from regressao.php.posts import CATALOGO as CATALOGO_POSTS
from regressao.php.posts import carrega_catalogo, roda_post
from regressao.php.relatorios import CATALOGO as CATALOGO_RELATORIOS
from regressao.php.relatorios import carrega_catalogo_relatorios, roda_relatorio
from regressao.php.sintaxe import roda_lint
from regressao.php.telas import (Sessao, lista_telas, obtem_sid, renova_sessao, roda_telas,
                                 sessao_autenticada)

RAIZ = Path(__file__).resolve().parents[2]
CONHECIDAS = Path(__file__).resolve().parents[1] / "conhecidas.tsv"
AREA_BATERIA = "php-bateria"
AVISO_SEM_RESTAURAR = "banco NAO restaurado: resultado nao comparavel"

# Area -> prefixos das telas de menu. Gerado em 2026-11-14 (banco `ecidade` da baseline) pela mesma
# consulta de scratchpad/prefixos_area.py: configuracoes.atendcadareamod -> atendcadarea (at25_descr
# sem "DB:") / db_modulos -> db_menu -> db_itensmenu (funcao ~ '.php'), prefixo = pref() do script,
# so telas existentes em ecidade/. Para regenerar: rode essa consulta por area e copie os prefixos
# (o teste test_todo_prefixo_de_area_casa_algum_arquivo falha se um prefixo perder todos os
# arquivos). Fora: `func` (patrimonial; 4 telas de menu mas 2993 janelas func_*.php em disco) e
# prefixos sem arquivo em disco.
AREAS: dict[str, tuple[str, ...]] = {
    "assistenciasocial": ("hab", "pro", "rec", "soc"),
    "cidadao": ("con", "pre"),
    "configuracao": ("amb", "ate", "cai", "con", "edu", "hab", "mat", "orc", "pat", "pro", "sys"),
    "educacao": ("bib", "edu", "esc", "mat", "mer", "pro", "rel", "sec", "tre"),
    "financeiro": ("age", "cad", "cai", "com", "con", "cus", "div", "emp", "hab", "inf", "iss",
                   "orc", "pes", "pl", "pla", "pro", "sys", "tes"),
    "gestor": ("ges",),
    "integracoes": ("edf", "efd", "eso", "sped"),
    "patrimonial": ("ac", "aco", "cad", "cai", "com", "con", "emp", "lic", "mat", "orc", "ouv",
                    "pat", "pro", "processo", "prot", "vei"),
    "recursoshumanos": ("cai", "con", "es", "eso", "lic", "pes", "rec", "rh", "sped"),
    "saude": ("age", "amb", "far", "fum", "hip", "lab", "mat", "prot", "sau", "tfd", "vac"),
    "tributario": ("agu", "amb", "arr", "cad", "cai", "cem", "con", "div", "dv", "dvr", "fis",
                   "inf", "iss", "itb", "itbi", "jur", "mar", "not", "pre", "pro", "prot", "rec",
                   "sys", "tri"),
}
TODOS_PREFIXOS = tuple(sorted({p for ps in AREAS.values() for p in ps}))
ETAPAS_PULAVEIS = frozenset({"sintaxe", "classes"})  # ja validas numa rodada anterior (complemento de rodada)
ALIASES = {"rh": "recursoshumanos", "assistencia": "assistenciasocial", "social": "assistenciasocial",
           "tributaria": "tributario", "configuracoes": "configuracao"}


class ArgumentoInvalido(ValueError):
    pass


class AreaDesconhecida(ArgumentoInvalido):
    pass


def _chave_area(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[\s_\-]+", "", s)
    return ALIASES.get(s, s)


def resolve_areas(areas: list[str] | None) -> tuple[list[str], list[str]]:
    """(nomes canonicos, prefixos sem repeticao). None = todas as areas. Desconhecida -> AreaDesconhecida."""
    if areas is None:
        nomes = sorted(AREAS)
    else:
        nomes = []
        for a in areas:
            k = _chave_area(a)
            if k not in AREAS:
                raise AreaDesconhecida(f"area desconhecida: {a!r}; validas: {', '.join(sorted(AREAS))}")
            if k not in nomes:
                nomes.append(k)
    prefixos: list[str] = []
    for n in nomes:
        for p in AREAS[n]:
            if p not in prefixos:
                prefixos.append(p)
    return nomes, prefixos


def _regex_prefixo(p: str, user: str | None = None) -> str:
    """Regex do cmp.py/lista_telas para o prefixo p; `user` (alternancia das --prefixo) entra como
    lookahead, entao a mesma string serve a lista_telas e ao cmp.py (ambos re.match, IGNORECASE)."""
    base = rf"^{p}[0-9]*_"
    return rf"(?=(?:{user})){base}" if user else base


def _tela_da_area(tela: str, prefixos: list[str]) -> bool:
    return any(re.match(_regex_prefixo(p), tela, re.I) for p in prefixos)


@contextmanager
def sem_normalizacao():
    """Esvazia REGRAS no proprio objeto (o default de normaliza/hash_corpo) enquanto durar o bloco,
    para as Tasks 5/7 compararem/hashearem o corpo cru. Nao alcanca o cmp.py (subprocesso)."""
    guardadas = list(REGRAS)
    REGRAS.clear()
    try:
        yield
    finally:
        REGRAS[:] = guardadas


def _classes_das_telas(telas: list[str]) -> list[str]:
    """Classes `classes/db_*_classe.php` que as telas incluem (as que existem em disco)."""
    achadas: set[str] = set()
    pad = re.compile(rb"classes/(db_[A-Za-z0-9_]+_classe\.php)")
    for t in telas:
        try:
            achadas.update(m.decode() for m in pad.findall((RAIZ / "ecidade" / t).read_bytes()))
        except OSError:
            continue
    return [f"classes/{c}" for c in sorted(achadas) if (RAIZ / "ecidade" / "classes" / c).is_file()]


def _metadados_ambiente() -> dict:
    meta: dict = {}
    conts = containers_do_ambiente()
    for nome, cont in (("php_ref", conts.ref), ("php_85", conts.php_novo)):
        try:
            meta[nome] = _docker(["exec", cont, "php", "-r", "echo PHP_VERSION;"], 30).decode().strip()
        except Exception as e:
            meta[nome] = f"indisponivel: {e}"
    meta["git_commit"] = git.commit(RAIZ)
    meta.update(git.sujo(RAIZ))
    try:
        meta["baseline_sha256"] = ARQ_SHA256.read_text().split()[0]
    except Exception as e:
        meta["baseline_sha256"] = f"indisponivel: {e}"
    return meta


def _passo(nome: str, area: str, fn) -> list[Caso]:
    """Um passo que falha vira ERRO_AMBIENTE desse passo; o proximo continua."""
    try:
        return list(fn())
    except Exception as e:
        return [Caso(f"passo:{nome}", area, Veredito.ERRO_AMBIENTE, f"{type(e).__name__}: {e}")]


def _ns(casos: list[Caso], prefixo: str) -> list[Caso]:
    """Prefixa o id de cada caso com a etapa (ids de passo ja namespaced ficam como estao)."""
    return [c if c.id.startswith("passo:") else replace(c, id=f"{prefixo}:{c.id}") for c in casos]


def _ids_unicos(casos: list[Caso]) -> tuple[list[Caso], list[str]]:
    vistos: set[str] = set()
    saida, renomeados = [], []
    for c in casos:
        novo, n = c.id, 1
        while novo in vistos:
            n += 1
            novo = f"{c.id}#{n}"
        vistos.add(novo)
        if novo != c.id:
            renomeados.append(f"{c.id} -> {novo}")
            c = replace(c, id=novo)
        saida.append(c)
    return saida, renomeados


def _nomes_de_diff(casos: list[Caso]) -> dict[str, str]:
    """id -> nome de arquivo seguro e unico (sem diferenciar caixa) para diffs/."""
    usados: set[str] = set()
    nomes: dict[str, str] = {}
    for c in casos:
        if not c.diff:
            continue
        base = (re.sub(r"[^A-Za-z0-9._-]+", "_", c.id).strip("._") or "caso")[:150]
        nome, n = base, 1
        while nome.lower() in usados:
            n += 1
            nome = f"{base}~{n}"
        usados.add(nome.lower())
        nomes[c.id] = nome + ".diff"
    return nomes


def _fim(diretorio: Path, casos: list[Caso], meta: dict, avisos: list[str]) -> int:
    """Escreve a rodada (resumo.md ganha os avisos e a meta logo abaixo do titulo). Os diffs sao
    gravados aqui, com nome seguro: o id namespaced tem `:`, `/`, `?`, `&`."""
    nomes = _nomes_de_diff(casos)
    if nomes:
        meta["arquivos_diff"] = nomes
    escreve_rodada(diretorio, [replace(c, diff="") for c in casos], meta)
    for c in casos:
        if c.diff:
            (Path(diretorio) / "diffs" / nomes[c.id]).write_text(c.diff, encoding="utf-8", newline="")
    bloco = [""]
    if avisos:
        bloco += ["## AVISOS", ""] + [f"- **{a}**" for a in avisos] + [""]
    bloco += ["## Meta", ""] + [f"- {k}: {v}" for k, v in meta.items() if k != "arquivos_diff"] + [""]
    arq = Path(diretorio) / "resumo.md"
    linhas = arq.read_text(encoding="utf-8").split("\n")
    arq.write_text("\n".join(linhas[:1] + bloco + linhas[1:]), encoding="utf-8", newline="\n")
    return codigo_saida(casos)


def _filtra_catalogo(linhas, prefixos, todas_areas: bool, incluir_nv: bool, tela_de, rx_tela):
    """(a rodar, pulados nao-verificado, pulados de outra area/regex)."""
    rodar, nv, outra = [], [], []
    for r in linhas:
        tela = tela_de(r)
        # tela sem prefixo de NENHUMA area (db_download.php, func_*.php) so entra se o --prefixo a pedir de forma
        # explicita (rx_tela casa); sem regex, continua so na rodada "todas"
        pedida_fora_de_area = rx_tela is not None and not _tela_da_area(tela, TODOS_PREFIXOS)
        fora = (not todas_areas and not _tela_da_area(tela, prefixos) and not pedida_fora_de_area) or \
               (rx_tela is not None and not rx_tela.match(tela))
        if fora:
            outra.append(r)
        elif not r.verificado and not incluir_nv:
            nv.append(r)
        else:
            rodar.append(r)
    return rodar, nv, outra


def roda_bateria_php(diretorio_saida: Path, areas: list[str] | None = None, normalizar: bool = True,
                     incluir_nao_verificados: bool = False, restaurar: bool = True,
                     prefixos_regex: list[str] | None = None, pular: set[str] | None = None) -> int:
    pular = set(pular or ())
    if pular - ETAPAS_PULAVEIS:
        raise ArgumentoInvalido(f"etapa nao pulavel: {sorted(pular - ETAPAS_PULAVEIS)}; "
                                f"validas: {sorted(ETAPAS_PULAVEIS)}")
    nomes, prefixos = resolve_areas(areas)  # area desconhecida: levanta antes de qualquer passo
    rx_user = None
    if prefixos_regex:
        try:
            rx_user = "|".join(f"(?:{r})" for r in prefixos_regex)
            rx_tela = re.compile(rx_user, re.I)
        except re.error as e:
            raise ArgumentoInvalido(f"--prefixo invalido: {e}") from e
    else:
        rx_tela = None
    grupos: list[tuple[str, str, list[str]]] = []  # (prefixo, regex do cmp.py, telas)
    erros_lista: list[str] = []
    for p in prefixos:
        rx = _regex_prefixo(p, rx_user)
        try:
            telas = lista_telas(rx)
        except OSError as e:
            erros_lista.append(f"{p}: {e}")
            continue
        if telas:
            grupos.append((p, rx, telas))
    if rx_tela is not None and not grupos and not erros_lista:
        raise ArgumentoInvalido(f"nenhuma tela casa com --prefixo {prefixos_regex!r} nas areas {nomes}")
    diretorio_saida = Path(diretorio_saida)
    inicio = time.monotonic()
    tempos: dict[str, float] = {}
    meta: dict = {"areas": nomes, "prefixos": prefixos, "prefixos_regex": prefixos_regex or [],
                  "normalizar": normalizar, "incluir_nao_verificados": incluir_nao_verificados,
                  "comparavel": restaurar}
    avisos: list[str] = []
    if not restaurar:
        avisos.append(AVISO_SEM_RESTAURAR)
        meta["aviso"] = AVISO_SEM_RESTAURAR
        print(f"AVISO: {AVISO_SEM_RESTAURAR}", file=sys.stderr)
    if not normalizar:
        avisos.append("rodada SEM normalizacao (diff cru; o cmp.py das telas mantem a propria normalizacao)")

    def termina(casos: list[Caso]) -> int:
        tempos["total_s"] = round(time.monotonic() - inicio, 1)
        meta["tempos_s"] = tempos
        return _fim(diretorio_saida, casos, meta, avisos)

    def para(nome: str, detalhe: str) -> int:
        meta.update(_metadados_ambiente())
        return termina([Caso(f"passo:{nome}", AREA_BATERIA, Veredito.ERRO_AMBIENTE, detalhe)])

    # 1. ambiente: so ref (referencia PHP 7.4), php_novo (PHP 8.5) e o banco; laravel e proxy nao fazem parte
    alvos = alvos_do_ambiente()
    problemas = verifica(replace(alvos, laravel_novo=alvos.ref, proxy=alvos.ref))
    if problemas:
        return para("ambiente", "; ".join(problemas))

    # 2-3. baseline + restauracao (uma vez por rodada)
    try:
        confere_baseline(ARQ_DUMP)
        if restaurar:
            t0 = time.monotonic()
            restaura_dump(ARQ_DUMP)
            meta["restauracao_s"] = tempos["restauracao_s"] = round(time.monotonic() - t0, 1)
        else:
            meta["restauracao_s"] = None
    except (BancoDiferente, ErroAmbienteBanco, RodadaInvalida) as e:
        return para("banco", f"{type(e).__name__}: {e}")

    # 4. sessao autenticada (sobrevive ao restore: vive no volume de sessoes, nao no banco)
    # Sessao morta (expirou, uma tela a destruiu, container reiniciou) NAO derruba a rodada: renova-se por
    # login HTTP, com limite de renovacoes (MAX_RENOVACOES) para nao entrar em laco.
    sessao: Sessao | None = None
    try:
        sid = obtem_sid()
        sessao = Sessao(sid, MAX_RENOVACOES, renova=lambda s: renova_sessao(s))
        if not sessao_autenticada(sid) and not sessao.renova("sessao inicial invalida"):
            return para("sessao", "sessao nao autenticada (pagina 'Sessao invalida') e a renovacao falhou")
    except (ErroAmbienteBanco, OSError, subprocess.SubprocessError) as e:
        if sessao is None:
            sessao = Sessao("", MAX_RENOVACOES, renova=lambda s: renova_sessao(s))
        if not sessao.renova(f"{type(e).__name__} ao obter a sessao inicial"):
            return para("sessao", f"{type(e).__name__}: {e}")

    meta.update(_metadados_ambiente())
    with (sem_normalizacao() if not normalizar else nullcontext()):
        return _passos(termina, meta, tempos, sessao, nomes, prefixos, grupos, erros_lista,
                       areas is None and rx_tela is None, incluir_nao_verificados, rx_tela, diretorio_saida, pular)


MAX_RENOVACOES = 5


def _sessao_morreu(casos: list[Caso]) -> bool:
    """O prefixo falhou por sessao (nao autenticada, expirou ao buscar corpo ou no meio da rodada)."""
    return any(c.veredito == Veredito.ERRO_AMBIENTE and c.detalhe.startswith("sessao") for c in casos)


def _cronometra(tempos: dict, fase: str, fn):
    t0 = time.monotonic()
    try:
        return fn()
    finally:
        tempos[fase + "_s"] = round(time.monotonic() - t0, 1)


def _passos(termina, meta, tempos, sessao, nomes, prefixos, grupos, erros_lista, todas, incluir_nv,
            rx_tela, diretorio, pular=frozenset()) -> int:
    casos: list[Caso] = []
    if pular:
        meta["etapas_puladas"] = sorted(pular)
        meta["parcial"] = True  # rodada de COMPLEMENTO: nao cobre as etapas puladas
    rotulo = "+".join(nomes) if len(nomes) <= 3 else "todas"
    for e in erros_lista:
        casos.append(Caso("passo:lista_telas", rotulo, Veredito.ERRO_AMBIENTE, e))

    telas_alvo = sorted({t for _p, _rx, ts in grupos for t in ts})
    meta["telas_selecionadas"] = len(telas_alvo)

    if "sintaxe" not in pular:
        casos += _ns(_cronometra(tempos, "sintaxe", lambda: _passo(
            "sintaxe", rotulo, lambda: roda_lint(telas_alvo))), "sintaxe")

    def _classes():
        lista = _classes_das_telas(telas_alvo)
        meta["classes_selecionadas"] = len(lista)
        return roda_classes(lista) if lista else []
    if "classes" not in pular:
        casos += _ns(_cronometra(tempos, "classes", lambda: _passo("classes", rotulo, _classes)), "classe")

    hashes: dict[str, str] = {}
    flags: dict[str, bool] = {}
    meta["pico_corpos_em_memoria"] = 0

    def _telas():
        saida: list[Caso] = []
        for p, rx, _ts in grupos:
            cs, cp = roda_telas(sessao.sid, rx, rotulo)
            if _sessao_morreu(cs) and sessao.renova(f"expirou no prefixo {p}"):
                cs, cp = roda_telas(sessao.sid, rx, rotulo)  # refaz o prefixo com a sessao nova
            meta["pico_corpos_em_memoria"] = max(meta["pico_corpos_em_memoria"], len(cp))
            if not any(c.veredito == Veredito.ERRO_AMBIENTE for c in cs):
                # corpos parciais acompanham ERRO_AMBIENTE: ignorados. Senao, so hash e flag ficam.
                for tela, corpo in cp.items():
                    hashes[tela] = hash_corpo(corpo)
                    flags[tela] = tem_dados(corpo)
            del cp
            for c in cs:
                nao_tela = not c.id.endswith(".php")
                saida.append(replace(c, id=f"tela-run:{p}:{c.id}" if nao_tela else f"tela:{c.id}"))
        return saida
    casos += _cronometra(tempos, "telas", lambda: _passo("telas", rotulo, _telas))

    def _sessao_viva(passo: str) -> bool:
        try:
            ok = sessao_autenticada(sessao.sid)
            detalhe = f"sessao expirou no passo {passo}"
        except Exception as e:
            ok, detalhe = False, f"sessao nao verificavel no passo {passo}: {type(e).__name__}: {e}"
        if not ok and sessao.renova(f"expirou antes de {passo}"):
            ok = True  # sessao renovada e validada: o passo segue
        if not ok:
            casos.append(Caso(f"passo:sessao:{passo}", rotulo, Veredito.ERRO_AMBIENTE, detalhe))
        return ok

    def _catalogo(nome, carrega, caminho, tela_de, id_de, roda):
        try:
            linhas = carrega(caminho)
        except Exception as e:
            meta[f"catalogo_{nome}"] = {"erro": str(e)}
            return [Caso(f"passo:catalogo_{nome}", rotulo, Veredito.ERRO_AMBIENTE, f"{type(e).__name__}: {e}")]
        rodar, nv, outra = _filtra_catalogo(linhas, prefixos, todas, incluir_nv, tela_de, rx_tela)
        meta[f"catalogo_{nome}"] = {
            "linhas": len(linhas), "rodadas": len(rodar), "nao_verificado_pulados": len(nv),
            "nao_verificado_pulados_ids": [id_de(r) for r in nv], "fora_da_area": len(outra),
            "verificado": sum(1 for r in linhas if r.verificado),
            "nao_verificado": sum(1 for r in linhas if not r.verificado)}
        saida: list[Caso] = []
        for r in rodar:
            try:
                saida.append(roda(sessao.sid, r))
            except Exception as e:
                saida.append(Caso(id_de(r), r.area, Veredito.ERRO_AMBIENTE, f"{type(e).__name__}: {e}"))
        return saida

    if _sessao_viva("posts"):
        casos += _ns(_cronometra(tempos, "posts", lambda: _passo("posts", rotulo, lambda: _catalogo(
            "posts", carrega_catalogo, CATALOGO_POSTS, lambda r: r.tela, lambda r: r.tela, roda_post))), "post")
        if _sessao_viva("relatorios"):
            casos += _ns(_cronometra(tempos, "relatorios", lambda: _passo("relatorios", rotulo, lambda: _catalogo(
                "relatorios", carrega_catalogo_relatorios, CATALOGO_RELATORIOS, lambda r: r.tela,
                lambda r: r.url, roda_relatorio))), "relatorio")

    casos, renomeados = _ids_unicos(casos)
    meta["ids_renomeados"] = renomeados

    # conhecidas (chaves namespaced: ver cabecalho de conhecidas.tsv)
    try:
        casos = marcar(casos, carregar_conhecidas(CONHECIDAS))
    except Exception as e:
        casos.append(Caso("passo:conhecidas", rotulo, Veredito.ERRO_AMBIENTE, f"{type(e).__name__}: {e}"))

    # hashes das telas e cobertura (a partir das reducoes; os corpos ja foram descartados)
    def _artefatos():
        arq = grava_hashes_de_hashes(Path(diretorio), hashes)
        meta["hashes"] = arq.name
        cob = cobertura_de_flags(flags)
        meta["telas_com_dados"] = len(cob["com_dados"])
        meta["telas_tabela_vazia"] = len(cob["tabela_vazia"])
        (Path(diretorio) / "cobertura.json").write_text(json.dumps(cob, ensure_ascii=False, indent=2),
                                                        encoding="utf-8", newline="\n")
        return []
    casos += _passo("artefatos", rotulo, _artefatos)

    meta["sessao_renovacoes"] = sessao.renovacoes
    return termina(casos)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m regressao.php.bateria", description=__doc__.split("\n")[0])
    ap.add_argument("--saida", required=True, type=Path)
    ap.add_argument("--area", action="append", default=None, help=f"repetivel; validas: {', '.join(sorted(AREAS))}")
    ap.add_argument("--prefixo", action="append", default=None, metavar="REGEX",
                    help="repetivel; so telas (e linhas dos catalogos) cujo nome casa (re.match)")
    ap.add_argument("--sem-normalizar", action="store_true")
    ap.add_argument("--incluir-nao-verificados", action="store_true")
    ap.add_argument("--sem-restaurar", action="store_true",
                    help="SO desenvolvimento: nao restaura a baseline; resultado nao comparavel")
    ap.add_argument("--pular", action="append", default=None, metavar="ETAPA",
                    help="repetivel (sintaxe|classes): COMPLEMENTO de rodada; essas etapas ja foram validas antes. "
                         "A rodada fica marcada meta.parcial")
    a = ap.parse_args(argv)
    try:
        return roda_bateria_php(a.saida, a.area, normalizar=not a.sem_normalizar,
                                incluir_nao_verificados=a.incluir_nao_verificados,
                                restaurar=not a.sem_restaurar, prefixos_regex=a.prefixo,
                                pular=set(a.pular or ()))
    except ArgumentoInvalido as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
