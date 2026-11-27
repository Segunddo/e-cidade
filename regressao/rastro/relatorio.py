"""Relatorio (Markdown) do rastreador: um veredito por tela, com a linha causal e a cadeia que levou ao valor errado."""
import re
from pathlib import Path

from regressao.rastro.alinha import Divergencia
from regressao.rastro.classifica import Resultado

ORDEM = ["DIVERGE-CAUSAL", "INCONCLUSIVO", "DIVERGE-RECONVERGENTE", "IDENTICO"]
TITULOS = {
    "DIVERGE-CAUSAL": "Defeitos (a resposta final difere): onde o dado se separou",
    "INCONCLUSIVO": "Inconclusivos (nao contam como aprovados)",
    "DIVERGE-RECONVERGENTE": "Reconvergentes (o dado divergiu no meio, mas o resultado final e igual: correto)",
    "IDENTICO": "Identicos",
}


def _curto(v: dict | None, n: int = 110) -> str:
    if v is None:
        return "(nao ocorreu)"
    return re.sub(r"\s+", " ", f"{v.get('t', '')}: {v.get('r', '')}")[:n].replace("|", "/")


def descreve(d: Divergencia) -> str:
    onde = f"`{d.arquivo}:{d.linha}`"
    if d.motivo == "aviso_x_excecao":
        return (f"{onde} - o 7.4 so emite **aviso** e o 8.5 **lanca excecao** na mesma linha. "
                f"7.4: {_curto(d.valor_ref)} | 8.5: {_curto(d.valor_alvo)}")
    if d.motivo == "so_ref":
        return f"{onde} - `{d.nome}` ({d.tipo}) acontece **so no 7.4**: {_curto(d.valor_ref)}"
    if d.motivo == "so_alvo":
        return f"{onde} - `{d.nome}` ({d.tipo}) acontece **so no 8.5**: {_curto(d.valor_alvo)}"
    return f"{onde} - `{d.nome}` ({d.tipo}): 7.4 = {_curto(d.valor_ref)} | 8.5 = {_curto(d.valor_alvo)}"


def escreve_relatorio(resultados: dict[str, Resultado], destino: Path, rastros: dict[str, dict[str, list[str]]] | None = None) -> Path:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    L = ["# Rastreador de fluxo de dados - relatorio", "",
         "Regra: divergiu no meio e o resultado final e igual = correto (reconvergente); divergiu e o resultado final "
         "difere = defeito, e a linha apontada e a **primeira divergencia que nao reconverge**.", "",
         "| Veredito | Telas |", "|---|---|"]
    for v in ORDEM:
        L.append(f"| {v} | {sum(1 for r in resultados.values() if r.veredito == v)} |")
    L.append("")
    for v in ORDEM:
        grupo = {t: r for t, r in resultados.items() if r.veredito == v}
        if not grupo:
            continue
        L += [f"## {TITULOS[v]}", ""]
        for tela, r in sorted(grupo.items()):
            L.append(f"### `{tela}`")
            if r.causal:
                L += ["", f"**Linha causal:** {descreve(r.causal)}"]
            if r.cadeia:
                L += ["", "**Cadeia de atribuicoes ate a linha causal (no 8.5, em ordem de execucao):**", ""]
                L += [f"{i}. `{e.arquivo}:{e.linha}` `{e.nome}` = {_curto(e.valor)}" for i, e in enumerate(r.cadeia, 1)]
            if r.reconvergentes:
                L += ["", f"Divergencias que reconvergiram ({len(r.reconvergentes)}):", ""]
                L += [f"- {descreve(d)}" for d in r.reconvergentes[:15]]
            if r.ruido:
                L += ["", f"Descartadas como ruido (ja variam entre duas execucoes do 7.4): {len(r.ruido)}"]
            if r.nota:
                L += ["", f"Nota: {r.nota}"]
            if r.truncado:
                L += ["", "**Rastro truncado** (teto de eventos): nada foi concluido."]
            L.append("")
    arq = destino / "relatorio.md"
    arq.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    for tela, partes in (rastros or {}).items():
        pasta = destino / "rastro" / tela
        pasta.mkdir(parents=True, exist_ok=True)
        for nome, linhas in partes.items():
            (pasta / f"{nome}.jsonl").write_text("\n".join(linhas) + ("\n" if linhas else ""), encoding="utf-8")
    return arq
