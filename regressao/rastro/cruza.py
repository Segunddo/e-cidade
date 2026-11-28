"""Cruza os relatorios dos dois backends (A = sondas por linha, B = Xdebug sem instrumentar) e diz onde concordam.

Por tela: as duas linhas causais sao a mesma? o mesmo arquivo? so um dos lados achou causa? Onde os dois concordam a confianca e alta;
onde discordam, a tela vai para revisao (um backend pode apontar uma chamada interna que aparece so num trace: caso `substr` do ate1_tarefa004).
"""
import re
from collections import Counter
from pathlib import Path

from regressao.rastro.relatorio import TITULOS

_SECOES = {titulo: veredito for veredito, titulo in TITULOS.items()}
_POS = re.compile(r"`([^`]+:\d+)`")


def le_relatorio(texto: str) -> dict[str, dict]:
    """{tela: {veredito, causal, sintoma}} a partir do Markdown de `escreve_relatorio`."""
    r: dict[str, dict] = {}
    veredito, tela = None, None
    for l in texto.splitlines():
        if l.startswith("## "):
            veredito = _SECOES.get(l[3:].strip())
            tela = None
        elif l.startswith("### `") and veredito:
            tela = l[5:].rstrip("`").strip()
            r[tela] = dict(veredito=veredito, causal=None, sintoma=None)
        elif tela and l.startswith("**Linha causal:**"):
            m = _POS.search(l)
            r[tela]["causal"] = m.group(1) if m else None
        elif tela and l.startswith("**Sintoma"):
            m = _POS.search(l)
            r[tela]["sintoma"] = m.group(1) if m else None
    return r


def _arquivo(pos: str | None) -> str | None:
    return pos.rsplit(":", 1)[0] if pos else None


def cruza(a: dict[str, dict], b: dict[str, dict]) -> list[dict]:
    linhas = []
    for tela in sorted(set(a) | set(b)):
        ra, rb = a.get(tela), b.get(tela)
        ca, cb = (ra or {}).get("causal"), (rb or {}).get("causal")
        if ca and cb:
            conc = "mesma-linha" if ca == cb else "mesmo-arquivo" if _arquivo(ca) == _arquivo(cb) else "arquivo-diferente"
        elif ca:
            conc = "so-A"
        elif cb:
            conc = "so-B"
        else:
            conc = "sem-causa"
        linhas.append(dict(tela=tela, veredito_A=(ra or {}).get("veredito", "-"), causal_A=ca or "", veredito_B=(rb or {}).get("veredito", "-"),
                           causal_B=cb or "", concordancia=conc))
    return linhas


def resumo(linhas: list[dict]) -> dict[str, int]:
    return dict(Counter(l["concordancia"] for l in linhas))


def escreve(linhas: list[dict], destino: Path) -> tuple[Path, Path]:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    cols = ["tela", "veredito_A", "causal_A", "veredito_B", "causal_B", "concordancia"]
    tsv = destino / "cruzamento.tsv"
    tsv.write_text("\t".join(cols) + "\n" + "\n".join("\t".join(l[c] for c in cols) for l in linhas) + "\n", encoding="utf-8", newline="\n")
    r = resumo(linhas)
    total = len(linhas)
    md = destino / "cruzamento.md"
    md.write_text("\n".join([
        "# Cruzamento dos backends do rastreador", "",
        f"{total} telas. **A** = sondas por linha (arvore instrumentada); **B** = Xdebug (nada instrumentado).", "",
        "| Concordancia | Telas |", "|---|---|"] + [f"| {k} | {r.get(k, 0)} |" for k in
                                                 ("mesma-linha", "mesmo-arquivo", "arquivo-diferente", "so-A", "so-B", "sem-causa")] + [""]),
        encoding="utf-8", newline="\n")
    return md, tsv
