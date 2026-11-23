from dataclasses import replace
from pathlib import Path

from .veredito import Caso, Veredito


def carregar_conhecidas(caminho: Path) -> dict[str, str]:
    """TSV id<TAB>motivo; ignora linhas em branco e iniciadas por '#'."""
    out: dict[str, str] = {}
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        id_, _, motivo = linha.partition("\t")
        out[id_.strip()] = motivo.strip()
    return out


def marcar(casos: list[Caso], conhecidas: dict[str, str]) -> list[Caso]:
    return [
        replace(c, conhecida=True)
        if c.veredito == Veredito.DIVERGE and c.id in conhecidas
        else c
        for c in casos
    ]
