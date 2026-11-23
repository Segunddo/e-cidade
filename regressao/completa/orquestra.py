"""Bateria completa: PHP -> Laravel -> fluxos de navegador, agregadas numa rodada so.

    python -m regressao.completa.orquestra --saida DIR [--area A ...] [--prefixo RX ...]
        [--sem-fluxos] [--alvo-laravel URL]
    python -m regressao.completa.orquestra --comparar ANTES DEPOIS [--saida-comparacao DIR]

Referencia (gabarito) = base PHP 7.4/Laravel 8 (`REGRESSAO_REF_URL`, padrao :8074); alvo PHP = 8.5
(`REGRESSAO_PHP_NOVO_URL`, :8185); alvo Laravel = `--alvo-laravel` ou `REGRESSAO_LARAVEL_NOVO_URL` (padrao o
laboratorio :8187, que hoje roda o Laravel 8 da base sob PHP 8.5: o Laravel 13 do grupo ainda nao existe).

Ordem e higiene de estado: ambiente -> bateria PHP (restaura a baseline) -> bateria Laravel em
`comparar` (restaura de novo) -> fluxos de navegador (restauram de novo e rodam por ULTIMO; o banco
termina SUJO por construcao: a proxima bateria, qualquer que seja, restaura). Custo: ~3 restauracoes
(~4 min cada) + o tempo de cada bateria. Uma frente que falha (inclusive "o Laravel do alvo nao autentica",
que vira UM ERRO_AMBIENTE `laravel:banco`/`laravel:boot`) NAO aborta as outras: tudo e agregado e o codigo
de saida e o PIOR das frentes (2 > 1 > 0, mesma semantica de `codigo_saida`).

Saida: <saida>/php/, <saida>/laravel/, <saida>/fluxos/ (rodadas completas de cada frente) e, no topo,
resultado.json + resumo.md (copia identica em relatorio.md). Ids dos casos ganham o prefixo da frente
(`php:`, `laravel:`, `fluxo:`) para continuarem unicos. `meta.comparavel` e False se alguma
sub-rodada nao for comparavel (ex.: --sem-restaurar) ou nao existir; `--comparar` recusa essas rodadas.

`--comparar ANTES DEPOIS`: regressoes (IDENTICO/INCONCLUSIVO -> DIVERGE/ERRO_AMBIENTE e a PERDA DE
VERIFICACAO IDENTICO -> INCONCLUSIVO), correcoes (DIVERGE/ERRO -> IDENTICO), casos adicionados e
removidos, e diferencas de meta. Saida 1 se houver regressao ou caso removido, 2 se a entrada for
invalida/nao comparavel, senao 0. Escreve comparacao.md/.json (por padrao dentro de DEPOIS).
"""
import argparse
import json
import re
import shutil
import sys
import time
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path

from regressao.completa.fluxos import aviso_sem_php85
from regressao.laravel.token import redige
from regressao.nucleo import git
from regressao.nucleo.ambiente import alvos_do_ambiente, verifica
from regressao.nucleo.banco import ARQ_SHA256
from regressao.nucleo.relatorio import RodadaInvalida, compara_rodadas, escreve_rodada
from regressao.nucleo.veredito import Caso, Veredito, codigo_saida

RAIZ = Path(__file__).resolve().parents[2]
FRENTES = ("php", "laravel", "fluxos")
PREFIXO_ID = {"php": "php", "laravel": "laravel", "fluxos": "fluxo"}
AREA_COMPLETA = "completa"
LIMITE_LISTA = 60
AVISO_ESCOPO_PHP = ("ESCOPO: ./ecidade e montado nos DOIS runtimes; a bateria PHP prova so paridade referencia 7.4 x 8.5 "
                    "sobre o codigo ATUAL e NAO detecta regressao de codigo comum aos dois. So Laravel e fluxos sao "
                    "golden master.")
AVISO_REFERENCIA = ("REFERENCIA: o gabarito e a base PHP 7.4/Laravel 8 (base-php74, PR #8); a base antiga virou "
                    "historico. \"Igual\" quer dizer igual ao 7.4.")
AVISO_VEREDITOS = ("INCONCLUSIVO e ERRO_AMBIENTE NUNCA sao aprovacao: INCONCLUSIVO e caso nao exercitado, ERRO_AMBIENTE e "
                   "rodada que nao pode ser feita. Verde = saida 0 E leitura da Cobertura e dos INCONCLUSIVO.")
AVISO_AUTOCONSISTENCIA = ("ALVO LARAVEL = REFERENCIA: a bateria Laravel comparou o Laravel 8 com a propria baseline "
                          "(prova de estabilidade da medicao), nao a migracao.")


# ------------------------------------------------------------------ ambiente e meta

def _verifica_ambiente() -> list[str]:
    """Docker, banco, referencia 7.4 (:8074), PHP 8.5 (:8185) e o proxy (:8190), pelos nomes de
    regressao/nucleo/ambiente.py. O Laravel novo NAO entra: sua ausencia e um achado da
    bateria Laravel (ERRO_AMBIENTE proprio), nao motivo para abortar a rodada completa."""
    alvos = alvos_do_ambiente()
    return verifica(replace(alvos, laravel_novo=alvos.ref))


def _meta_repo() -> dict:
    meta: dict = {"git_commit": git.commit(RAIZ)}
    meta.update(git.sujo(RAIZ))
    meta.update(git.sujo_regressao(RAIZ))
    try:
        meta["baseline_sha256"] = ARQ_SHA256.read_text().split()[0]
    except Exception as e:
        meta["baseline_sha256"] = f"indisponivel: {type(e).__name__}"
    return meta


def _mesma_url(a: str, b: str) -> bool:
    return (a or "").rstrip("/") == (b or "").rstrip("/")


def veredito_geral(meta: dict) -> str:
    """Uma linha para quem so quer saber se a rodada e verde: o pior codigo das frentes e dos casos."""
    t = meta.get("totais") or {}
    if t.get("ERRO_AMBIENTE") or meta.get("comparavel") is False:
        return ("ERRO (saida 2): a rodada nao pode ser concluida (ERRO_AMBIENTE ou sub-rodada nao comparavel); "
                "nada se conclui, corrija o ambiente e rode de novo")
    novas = (meta.get("divergencias") or {}).get("novas", 0)
    if novas:
        return f"VERMELHO (saida 1): {novas} divergencia(s) nova(s) em relacao a referencia 7.4"
    n_inc = t.get("INCONCLUSIVO", 0)
    return ("VERDE (saida 0): nenhuma divergencia nova" + (f"; {n_inc} caso(s) INCONCLUSIVO NAO foram verificados"
                                                          if n_inc else ""))


def prefixa(frente: str, id: str) -> str:
    """Prefixo da frente no id do caso, sem duplicar quando ele ja o traz (`laravel:boot`)."""
    p = PREFIXO_ID.get(frente, frente) + ":"
    return id if id.startswith(p) else p + id


# ------------------------------------------------------------------ sub-rodadas

@dataclass
class Frente:
    nome: str
    codigo: int
    casos: list[Caso]
    meta: dict
    tempo_s: float
    erro: str | None = None  # frente sem sub-rodada valida
    totais: dict = field(default_factory=dict)


def _le_subrodada(diretorio: Path) -> tuple[list[Caso], dict]:
    arq = Path(diretorio) / "resultado.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        casos = [Caso(c["id"], c.get("area", ""), Veredito(c["veredito"]), c.get("detalhe", ""),
                      conhecida=bool(c.get("conhecida", False))) for c in dados["casos"]]
        meta = dados["meta"]
        if not isinstance(meta, dict):
            raise TypeError("meta")
    except FileNotFoundError as e:
        raise RodadaInvalida(f"{arq}: arquivo ausente") from e
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as e:
        raise RodadaInvalida(f"{arq}: rodada invalida ({type(e).__name__}: {e})") from e
    return casos, meta


def _roda_frente(nome: str, fn, diretorio: Path) -> Frente:
    """Roda uma frente e le a sub-rodada que ela escreveu. Nada aqui levanta: excecao, ausencia ou
    corrupcao da sub-rodada viram UM caso ERRO_AMBIENTE da frente (a rodada completa segue)."""
    if diretorio.exists():
        shutil.rmtree(diretorio)  # nunca ler resultado.json velho de uma rodada anterior
    t0 = time.monotonic()
    codigo, erro = 2, None
    try:
        codigo = fn(diretorio)
    except SystemExit as e:
        erro = f"SystemExit({e.code})"
    except Exception as e:
        erro = redige(f"{type(e).__name__}: {e}")
    tempo = round(time.monotonic() - t0, 1)
    if erro is None:
        try:
            casos, meta = _le_subrodada(diretorio)
            return Frente(nome, int(codigo), casos, meta, tempo)
        except RodadaInvalida as e:
            erro = str(e)
    caso = Caso(prefixa(nome, f"{nome}:execucao"), AREA_COMPLETA, Veredito.ERRO_AMBIENTE,
                f"a frente {nome} nao produziu rodada valida: {erro}")
    return Frente(nome, 2, [caso], {"comparavel": False}, tempo, erro=erro)


def _contagem(casos: list[Caso]) -> dict[str, int]:
    c = Counter(Veredito(x.veredito).value for x in casos)
    return {v.value: c.get(v.value, 0) for v in Veredito}


def _motivo(c: Caso) -> str:
    d = (c.detalhe or "").strip().splitlines()
    d = d[0].strip() if d else ""
    if d.startswith("HTTP ") and "nos dois lados" in d:
        return "5xx nos dois lados (nao exercitado)"
    return (d or "sem motivo")[:120]


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


def _inconclusivos(casos: list[Caso]) -> dict[str, int]:
    return dict(Counter(_motivo(c) for c in casos if c.veredito == Veredito.INCONCLUSIVO))


def _cobertura(f: Frente) -> dict:
    m = f.meta
    if f.nome == "php":
        cob: dict = {}
        for chave, nome in (("catalogo_posts", "posts"), ("catalogo_relatorios", "relatorios")):
            c = m.get(chave)
            if isinstance(c, dict):
                cob[nome] = {k: c.get(k) for k in ("verificado", "nao_verificado", "nao_verificado_pulados",
                                                   "rodadas", "linhas", "erro") if k in c}
        for k in ("telas_selecionadas", "telas_com_dados", "telas_tabela_vazia", "classes_selecionadas"):
            if k in m:
                cob[k] = m[k]
        return cob
    if f.nome == "laravel":
        c = m.get("cobertura") or {}
        if "rotas_cobertas" in c:
            return {"rotas_cobertas": c["rotas_cobertas"], "rotas_total": c["rotas_total"]}
        return dict(c) if c else {}
    return dict(m.get("cobertura") or {})


def _versoes(frentes: dict[str, Frente]) -> dict:
    v: dict = {}
    # (frente, chave no meta da frente, chave em `versoes`): o php_alvo da bateria Laravel e o PHP do alvo
    # Laravel (laboratorio), que nao e necessariamente o php_85 da bateria PHP
    for nome, k, destino in (("php", "php_ref", "php_ref"), ("php", "php_85", "php_85"),
                             ("laravel", "php_ref", "php_ref"), ("laravel", "laravel_ref", "laravel_ref"),
                             ("laravel", "php_alvo", "php_alvo_laravel"), ("laravel", "laravel_alvo", "laravel_alvo")):
        meta = frentes.get(nome, Frente(nome, 0, [], {}, 0)).meta
        if k in meta and destino not in v:
            v[destino] = meta[k]
    fl = frentes.get("fluxos")
    if fl and isinstance(fl.meta.get("versoes"), dict):
        v.update(fl.meta["versoes"])
    return v


def agrega(frentes: dict[str, Frente], meta_repo: dict, tempos: dict, partes: list[str],
           extra_avisos: list[str] | None = None) -> tuple[list[Caso], dict, list[str]]:
    """Casos com ids prefixados + meta agregada + avisos (puro: sem E/S)."""
    from regressao.php.bateria import _ids_unicos  # reuso: sufixo #N em duplicata residual

    casos: list[Caso] = []
    for f in frentes.values():
        casos += [replace(c, id=prefixa(f.nome, c.id)) for c in f.casos]
    casos, renomeados = _ids_unicos(casos)

    baterias: dict = {}
    for f in frentes.values():
        div = [c for c in f.casos if c.veredito == Veredito.DIVERGE]
        baterias[f.nome] = {
            "codigo_saida": f.codigo, "totais": _contagem(f.casos), "total": len(f.casos),
            "divergencias_novas": sum(1 for c in div if not c.conhecida),
            "divergencias_conhecidas": sum(1 for c in div if c.conhecida),
            "comparavel": f.meta.get("comparavel") is not False and f.erro is None,
            "tempo_s": f.tempo_s, "restauracao_s": f.meta.get("restauracao_s"),
            "erro": f.erro, "subdiretorio": f.nome}
    div_todas = [c for c in casos if c.veredito == Veredito.DIVERGE]
    pct = {n: _pct(b["totais"]["INCONCLUSIVO"], b["total"]) for n, b in baterias.items()}
    pct["total"] = _pct(sum(1 for c in casos if c.veredito == Veredito.INCONCLUSIVO), len(casos))
    comparavel = all(b["comparavel"] for b in baterias.values()) and bool(baterias)

    meta = {
        "tipo": "completa", "comparavel": comparavel, "partes_executadas": list(partes),
        **meta_repo, "versoes": _versoes(frentes), "tempos_s": tempos,
        "baterias": baterias, "totais": _contagem(casos), "total": len(casos),
        "divergencias": {"novas": sum(1 for c in div_todas if not c.conhecida),
                         "conhecidas": sum(1 for c in div_todas if c.conhecida)},
        "inconclusivos_por_motivo": {n: _inconclusivos(f.casos) for n, f in frentes.items()},
        "inconclusivos_percentual": pct,
        "cobertura": {n: _cobertura(f) for n, f in frentes.items()},
        "ids_renomeados": renomeados,
    }
    lar = frentes.get("laravel")
    if lar and isinstance(lar.meta.get("baseline"), dict):
        meta["baseline_laravel"] = lar.meta["baseline"]
    if lar and lar.meta.get("alvo"):
        meta["alvo_laravel"] = lar.meta["alvo"]

    avisos = list(extra_avisos or [])
    avisos.append(AVISO_REFERENCIA)
    avisos.append(AVISO_VEREDITOS)
    if "php" in frentes:
        avisos.append(AVISO_ESCOPO_PHP)
    if lar and lar.meta.get("alvo") and _mesma_url(lar.meta["alvo"], alvos_do_ambiente().ref):
        avisos.append(AVISO_AUTOCONSISTENCIA)
    for n, b in baterias.items():
        if not b["comparavel"]:
            avisos.append(f"{n}: sub-rodada NAO COMPARAVEL"
                          + (f" ({b['erro']})" if b["erro"] else " (ver meta da sub-rodada)"))
    if not partes or "fluxos" not in partes:
        avisos.append("fluxos de navegador NAO executados (--sem-fluxos)")
    fl = frentes.get("fluxos")
    if fl and "runtime_observado" in fl.meta and (a := aviso_sem_php85(fl.meta["runtime_observado"])):
        avisos.append(a)
    n_inc = sum(1 for c in casos if c.veredito == Veredito.INCONCLUSIVO)
    if n_inc:
        avisos.append(f"{n_inc} caso(s) INCONCLUSIVO: NAO sao aprovacao (nao foram exercitados) - "
                      "motivos abaixo")
    for c in casos:
        if c.veredito == Veredito.ERRO_AMBIENTE:
            avisos.append(f"ERRO_AMBIENTE {c.id}: {(c.detalhe or '').splitlines()[0][:200] if c.detalhe else ''}")
    return casos, meta, avisos[:40]


def _lista(titulo: str, itens: list[Caso]) -> list[str]:
    out = ["", f"## {titulo}", ""]
    if not itens:
        return out + ["(nenhum)"]
    for c in itens[:LIMITE_LISTA]:
        out.append(f"- {c.id}" + (f": {(c.detalhe or '').splitlines()[0][:160]}" if c.detalhe else ""))
    if len(itens) > LIMITE_LISTA:
        out.append(f"- ... e mais {len(itens) - LIMITE_LISTA} (ver resultado.json)")
    return out


def resumo_md(casos: list[Caso], meta: dict, avisos: list[str]) -> str:
    L = ["# Resumo da bateria completa", "", f"**Resultado: {veredito_geral(meta)}**", "",
         "Referencia (gabarito): PHP 7.4/Laravel 8. Alvo: PHP 8.5. Como ler: regressao/COMO-USAR.md.", ""]
    if avisos:
        L += ["## AVISOS", ""] + [f"- **{a}**" for a in avisos] + [""]
    L += ["## Meta", ""]
    for k in ("git_commit", "git_sujo", "git_sujo_regressao", "baseline_sha256", "comparavel",
              "partes_executadas", "alvo_laravel"):
        if k in meta:
            L.append(f"- {k}: {meta[k]}")
    for k, v in meta["versoes"].items():
        L.append(f"- versao {k}: {v}")
    bl = meta.get("baseline_laravel")
    if bl:
        L.append(f"- baseline Laravel: dump_sha256={bl.get('dump_sha256')} n_casos={bl.get('n_casos')} "
                 f"commit={bl.get('commit')}")
    L += ["", "## Totais por bateria", "",
          "| bateria | casos | " + " | ".join(v.value for v in Veredito) + " | novas | conhecidas | saida | tempo (s) |",
          "|---|---|" + "---|" * len(Veredito) + "---|---|---|---|"]
    for n, b in meta["baterias"].items():
        L.append(f"| {n} | {b['total']} | " + " | ".join(str(b["totais"][v.value]) for v in Veredito)
                 + f" | {b['divergencias_novas']} | {b['divergencias_conhecidas']} | {b['codigo_saida']} | {b['tempo_s']} |")
    L.append(f"| **total** | {meta['total']} | " + " | ".join(str(meta["totais"][v.value]) for v in Veredito)
             + f" | {meta['divergencias']['novas']} | {meta['divergencias']['conhecidas']} | | {meta['tempos_s'].get('total')} |")
    n_inc = meta["totais"]["INCONCLUSIVO"]
    pcts = meta.get("inconclusivos_percentual", {"total": 0.0})
    L += ["", f"**INCONCLUSIVO: {n_inc} de {meta['total']} casos ({pcts['total']}%). "
              "Isso NAO e aprovacao: esses casos nao foram exercitados.** Por bateria: "
          + "; ".join(f"{n}: {b['totais']['INCONCLUSIVO']} de {b['total']} ({pcts.get(n, 0.0)}%)"
                      for n, b in meta["baterias"].items())]
    L += ["", "## Tempos por fase (s)", ""] + [f"- {k}: {v}" for k, v in meta["tempos_s"].items()]
    L += ["", "## Cobertura", ""]
    cob = meta["cobertura"]
    p = cob.get("php", {})
    for nome in ("posts", "relatorios"):
        c = p.get(nome)
        if c:
            L.append(f"- PHP catalogo de {nome}: verificado={c.get('verificado')} nao-verificado="
                     f"{c.get('nao_verificado')} (pulados nesta rodada: {c.get('nao_verificado_pulados')})")
    for k in ("telas_selecionadas", "telas_com_dados", "telas_tabela_vazia", "classes_selecionadas"):
        if k in p:
            extra = " (limite superior: a heuristica conta qualquer <td)" if k == "telas_com_dados" else ""
            L.append(f"- PHP {k}: {p[k]}{extra}")
    L.append("- PHP lint: so as telas selecionadas (nao cobre classes, libs/ nem models)")
    lar = cob.get("laravel", {})
    if "rotas_cobertas" in lar:
        L.append(f"- Laravel: rotas cobertas {lar['rotas_cobertas']} de {lar['rotas_total']} "
                 f"({lar['rotas_total'] - lar['rotas_cobertas']} NAO cobertas)")
    elif lar:
        L.append(f"- Laravel: {lar}")
    fl = cob.get("fluxos", {})
    if fl:
        L.append(f"- Fluxos: {fl}")
    L += ["", "## INCONCLUSIVO por motivo (NAO sao aprovacao)", ""]
    algum = False
    for n, motivos in meta["inconclusivos_por_motivo"].items():
        for m, q in sorted(motivos.items(), key=lambda x: -x[1]):
            L.append(f"- {n}: {m}: {q}")
            algum = True
    if not algum:
        L.append("(nenhum)")
    div = [c for c in casos if c.veredito == Veredito.DIVERGE]
    L += _lista("Divergencias novas", [c for c in div if not c.conhecida])
    L += _lista("Divergencias conhecidas", [c for c in div if c.conhecida])
    L += _lista("ERRO_AMBIENTE", [c for c in casos if c.veredito == Veredito.ERRO_AMBIENTE])
    L += ["", "Detalhes e diffs de cada frente: php/, laravel/ e fluxos/ (resumo.md, resultado.json, diffs/).", ""]
    return "\n".join(L)


def _escreve_completa(saida: Path, casos: list[Caso], meta: dict, avisos: list[str]) -> None:
    escreve_rodada(saida, casos, meta)  # resultado.json (+ resumo.md basico, sobrescrito abaixo)
    texto = resumo_md(casos, meta, avisos)
    (saida / "resumo.md").write_text(texto, encoding="utf-8", newline="\n")
    (saida / "relatorio.md").write_text(texto, encoding="utf-8", newline="\n")
    try:
        (saida / "diffs").rmdir()  # vazio: os diffs ficam em php/diffs, laravel/diffs, fluxos/diffs
    except OSError:
        pass


# ------------------------------------------------------------------ rodada completa

def _executores_padrao() -> dict:
    def php(d, areas, prefixos):
        from regressao.php.bateria import roda_bateria_php
        return roda_bateria_php(d, areas, prefixos_regex=prefixos)

    def laravel(d, alvo):
        from regressao.laravel.bateria import roda_bateria_laravel
        return roda_bateria_laravel(d, "comparar", alvo)

    def fluxos(d):
        from regressao.completa.fluxos import roda_fluxos_rodada
        return roda_fluxos_rodada(d)

    return {"php": php, "laravel": laravel, "fluxos": fluxos}


def roda_completa(diretorio_saida: Path, areas: list[str] | None = None, prefixos: list[str] | None = None,
                  fluxos: bool = True, laravel_alvo: str | None = None, executores: dict | None = None) -> int:
    """Roda as frentes em ordem, agrega e devolve o PIOR codigo de saida (2 > 1 > 0)."""
    saida = Path(diretorio_saida)
    ex = executores or _executores_padrao()
    inicio = time.monotonic()
    tempos: dict = {}
    saida.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()
    problemas = _verifica_ambiente()
    tempos["ambiente"] = round(time.monotonic() - t0, 1)
    meta_repo = _meta_repo()
    if problemas:
        caso = Caso("completa:ambiente", AREA_COMPLETA, Veredito.ERRO_AMBIENTE, "; ".join(problemas))
        tempos["total"] = round(time.monotonic() - inicio, 1)
        meta = {"tipo": "completa", "comparavel": False, "partes_executadas": [], **meta_repo,
                "versoes": {}, "tempos_s": tempos, "baterias": {}, "totais": _contagem([caso]), "total": 1,
                "divergencias": {"novas": 0, "conhecidas": 0}, "inconclusivos_por_motivo": {},
                "cobertura": {}, "ids_renomeados": []}
        _escreve_completa(saida, [caso], meta, [f"ambiente indisponivel: {caso.detalhe}"])
        return 2

    plano = [("php", lambda d: ex["php"](d, areas, prefixos)),
             ("laravel", lambda d: ex["laravel"](d, laravel_alvo))]
    if fluxos:
        plano.append(("fluxos", lambda d: ex["fluxos"](d)))
    frentes: dict[str, Frente] = {}
    for nome, fn in plano:
        frentes[nome] = _roda_frente(nome, fn, saida / nome)
        tempos[nome] = frentes[nome].tempo_s
    tempos["total"] = round(time.monotonic() - inicio, 1)

    casos, meta, avisos = agrega(frentes, meta_repo, tempos, [n for n, _ in plano])
    meta["areas"] = areas or []
    meta["prefixos_regex"] = prefixos or []
    _escreve_completa(saida, casos, meta, avisos)
    codigos = [f.codigo for f in frentes.values()] + [codigo_saida(casos)]
    return max(c if c in (0, 1) else 2 for c in codigos)


# ------------------------------------------------------------------ --comparar

def _le_rodada(diretorio: Path, rotulo: str) -> dict:
    arq = Path(diretorio) / "resultado.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise RodadaInvalida(f"rodada {rotulo} invalida: {arq} ausente") from e
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise RodadaInvalida(f"rodada {rotulo} invalida: {arq} nao e JSON valido ({e})") from e
    if not isinstance(dados, dict) or not isinstance(dados.get("meta"), dict) or not isinstance(dados.get("casos"), list):
        raise RodadaInvalida(f"rodada {rotulo} invalida: {arq} sem as chaves `meta` e `casos`")
    return dados


def _achata(meta: dict) -> dict:
    """Campos de meta que importam para a comparacao antes/depois (versoes achatadas)."""
    plano = {k: meta.get(k) for k in ("git_commit", "baseline_sha256", "git_sujo_regressao", "alvo_laravel")}
    for k, v in (meta.get("versoes") or {}).items():
        plano[f"versoes.{k}"] = v
    bl = meta.get("baseline_laravel") or {}
    if isinstance(bl, dict):
        plano["baseline_laravel.dump_sha256"] = bl.get("dump_sha256")
    return plano


def _diferencas_meta(a: dict, d: dict) -> dict:
    pa, pd = _achata(a), _achata(d)
    return {k: {"antes": pa.get(k), "depois": pd.get(k)} for k in sorted(pa.keys() | pd.keys())
            if pa.get(k) != pd.get(k)}


def classifica(mudancas: list[tuple[str, Veredito | None, Veredito | None]]) -> dict[str, list[dict]]:
    """Separa as mudancas de `compara_rodadas` em regressoes / correcoes / adicionados / removidos / outras."""
    ruim = {Veredito.DIVERGE, Veredito.ERRO_AMBIENTE}
    secoes: dict[str, list[dict]] = {"regressoes": [], "correcoes": [], "adicionados": [], "removidos": [],
                                  "lacunas": [], "outras": []}
    for id, a, d in mudancas:
        item = {"id": id, "antes": a.value if a else None, "depois": d.value if d else None}
        if a is None:
            secoes["adicionados"].append(item)
        elif d is None:
            secoes["removidos"].append(item)
        elif a in (Veredito.IDENTICO, Veredito.INCONCLUSIVO) and d in ruim:
            secoes["regressoes"].append({**item, "tipo": "falha nova"})
        elif a == Veredito.IDENTICO and d == Veredito.INCONCLUSIVO:
            secoes["regressoes"].append({**item, "tipo": "perda de verificacao"})
        elif a in ruim and d == Veredito.IDENTICO:
            secoes["correcoes"].append(item)
        elif a in ruim and d == Veredito.INCONCLUSIVO:
            secoes["lacunas"].append(item)  # saiu do vermelho sem ser verificado: nao e correcao
        else:
            secoes["outras"].append(item)
    return secoes


def _avisos_depois(dd: dict) -> list[str]:
    """Avisos sobre o estado da rodada DEPOIS em si (independente de ter mudado em relacao a ANTES)."""
    casos = [Caso(c["id"], c.get("area", ""), Veredito(c["veredito"]), conhecida=bool(c.get("conhecida")))
             for c in dd["casos"]]
    avisos = []
    n_err = sum(1 for c in casos if c.veredito == Veredito.ERRO_AMBIENTE)
    n_div = sum(1 for c in casos if c.veredito == Veredito.DIVERGE and not c.conhecida)
    if n_err:
        avisos.append(f"DEPOIS tem {n_err} caso(s) ERRO_AMBIENTE (mesmo que ja existissem em ANTES): saida 2")
    if n_div:
        avisos.append(f"DEPOIS tem {n_div} DIVERGE nao conhecida(s) (mesmo que ja existissem em ANTES): saida 1")
    return avisos


def _codigo_depois(dd: dict) -> int:
    return codigo_saida([Caso(c["id"], c.get("area", ""), Veredito(c["veredito"]), conhecida=bool(c.get("conhecida")))
                         for c in dd["casos"]])


def _md_comparacao(antes: Path, depois: Path, secoes: dict, difmeta: dict, ma: dict, md: dict,
                   avisos: list[str] | None = None) -> str:
    def tabela(titulo: str, itens: list[dict], com_tipo: bool = False) -> list[str]:
        out = ["", f"## {titulo} ({len(itens)})", ""]
        if not itens:
            return out + ["(nenhum)"]
        for i in itens[:200]:
            ant, dep = i["antes"] or "(ausente)", i["depois"] or "(ausente)"
            out.append(f"- {i['id']}: {ant} -> {dep}" + (f" [{i['tipo']}]" if com_tipo else ""))
        if len(itens) > 200:
            out.append(f"- ... e mais {len(itens) - 200} (ver comparacao.json)")
        return out

    L = ["# Comparacao antes/depois", "", f"- ANTES: {antes}", f"- DEPOIS: {depois}",
         f"- totais ANTES: {ma.get('totais')}", f"- totais DEPOIS: {md.get('totais')}"]
    if avisos:
        L += ["", "## AVISOS", ""] + [f"- **{a}**" for a in avisos]
    L += tabela("Regressoes", secoes["regressoes"], com_tipo=True)
    L += tabela("Correcoes", secoes["correcoes"])
    L += tabela("Adicionados", secoes["adicionados"])
    L += tabela("Removidos", secoes["removidos"])
    L += tabela("Lacunas (DIVERGE/ERRO_AMBIENTE -> INCONCLUSIVO: nao e correcao, nao foi verificado)", secoes["lacunas"])
    L += tabela("Outras mudancas de veredito", secoes["outras"])
    L += ["", "## Diferencas de meta", ""]
    if not difmeta:
        L.append("(nenhuma)")
    for k, v in difmeta.items():
        L.append(f"- {k}: {v['antes']} -> {v['depois']}")
    L.append("")
    return "\n".join(L)


def compara_completas(antes: Path, depois: Path, saida: Path | None = None) -> int:
    """Saida = max(comparacao, estado de DEPOIS): 1 se ha regressao/removido OU DEPOIS tem DIVERGE nao
    conhecida; 2 se a entrada e invalida/nao comparavel OU DEPOIS tem ERRO_AMBIENTE; senao 0."""
    antes, depois = Path(antes), Path(depois)
    try:
        da = _le_rodada(antes, "ANTES")
        dd = _le_rodada(depois, "DEPOIS")
        for rotulo, d in (("ANTES", da), ("DEPOIS", dd)):
            if d["meta"].get("comparavel") is False:
                print(f"erro: rodada {rotulo} nao comparavel (meta.comparavel=false: restauracao pulada ou "
                      f"sub-rodada ausente/invalida). Refaca a rodada completa.", file=sys.stderr)
                return 2
        mudancas = compara_rodadas(antes, depois)
    except RodadaInvalida as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    secoes = classifica(mudancas)
    difmeta = _diferencas_meta(da["meta"], dd["meta"])
    destino = Path(saida) if saida else depois
    destino.mkdir(parents=True, exist_ok=True)
    avisos = _avisos_depois(dd)
    resultado = {"antes": str(antes), "depois": str(depois), **secoes, "meta": difmeta, "avisos": avisos,
                 "totais": {"antes": da["meta"].get("totais"), "depois": dd["meta"].get("totais")}}
    (destino / "comparacao.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                                             encoding="utf-8", newline="\n")
    (destino / "comparacao.md").write_text(_md_comparacao(antes, depois, secoes, difmeta, da["meta"], dd["meta"], avisos),
                                           encoding="utf-8", newline="\n")
    mudou = 1 if secoes["regressoes"] or secoes["removidos"] else 0
    return max(mudou, _codigo_depois(dd))  # DEPOIS vermelho continua vermelho, mesmo igual a ANTES


# ------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m regressao.completa.orquestra",
                                 description=__doc__.split("\n")[0])
    ap.add_argument("--saida", type=Path, help="diretorio da rodada completa")
    ap.add_argument("--area", action="append", default=None, help="repetivel; so a bateria PHP")
    ap.add_argument("--prefixo", action="append", default=None, metavar="RX", help="repetivel; so a bateria PHP")
    ap.add_argument("--sem-fluxos", action="store_true", help="nao roda os fluxos de navegador")
    ap.add_argument("--alvo-laravel", default=None, metavar="URL", help="padrao: REGRESSAO_LARAVEL_NOVO_URL (:8187, laboratorio); "
                         "a referencia (:8074) da a prova de estabilidade")
    ap.add_argument("--comparar", nargs=2, metavar=("ANTES", "DEPOIS"), type=Path)
    ap.add_argument("--saida-comparacao", type=Path, default=None, help="onde gravar comparacao.md/.json (padrao: DEPOIS)")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    if a.comparar:
        return compara_completas(a.comparar[0], a.comparar[1], a.saida_comparacao)
    if not a.saida:
        print("erro: informe --saida DIR (ou --comparar ANTES DEPOIS)", file=sys.stderr)
        return 2
    try:
        from regressao.php.bateria import resolve_areas
        resolve_areas(a.area)
        if a.prefixo:
            re.compile("|".join(f"(?:{r})" for r in a.prefixo))
    except (ValueError, re.error) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    return roda_completa(a.saida, a.area, a.prefixo, fluxos=not a.sem_fluxos, laravel_alvo=a.alvo_laravel)


if __name__ == "__main__":
    sys.exit(main())
