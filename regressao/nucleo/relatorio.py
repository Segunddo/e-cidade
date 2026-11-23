import json
from collections import Counter
from pathlib import Path

from regressao.nucleo.veredito import Caso, Veredito


def escreve_rodada(diretorio: Path, casos: list[Caso], meta: dict) -> None:
    diretorio = Path(diretorio)
    (diretorio / "diffs").mkdir(parents=True, exist_ok=True)

    dados = {
        "meta": meta,
        "casos": [
            {
                "id": c.id,
                "area": c.area,
                "veredito": Veredito(c.veredito).value,
                "detalhe": c.detalhe,
                "conhecida": c.conhecida,
            }
            for c in casos
        ],
    }
    (diretorio / "resultado.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )

    for c in casos:
        if c.diff:
            (diretorio / "diffs" / f"{c.id}.diff").write_text(
                c.diff, encoding="utf-8", newline=""
            )

    (diretorio / "resumo.md").write_text(_resumo(casos), encoding="utf-8", newline="\n")


def _resumo(casos: list[Caso]) -> str:
    linhas = ["# Resumo da rodada", "", f"Total de casos: {len(casos)}", ""]

    linhas += ["## Por veredito", ""]
    por_v = Counter(Veredito(c.veredito).value for c in casos)
    for v in Veredito:
        linhas.append(f"- {v.value}: {por_v.get(v.value, 0)}")

    linhas += ["", "## Por area", ""]
    areas: dict[str, Counter] = {}
    for c in casos:
        areas.setdefault(c.area, Counter())[Veredito(c.veredito).value] += 1
    for area in sorted(areas):
        partes = ", ".join(f"{v.value}={areas[area].get(v.value, 0)}" for v in Veredito)
        linhas.append(f"- {area}: {partes}")

    def secao(titulo: str, itens: list[Caso]) -> None:
        linhas.extend(["", f"## {titulo}", ""])
        if not itens:
            linhas.append("(nenhum)")
        for c in itens:
            linhas.append(f"- {c.id} ({c.area})" + (f": {c.detalhe}" if c.detalhe else ""))

    div = [c for c in casos if c.veredito == Veredito.DIVERGE]
    secao("Divergencias novas", [c for c in div if not c.conhecida])
    secao("Divergencias conhecidas", [c for c in div if c.conhecida])
    secao("INCONCLUSIVO", [c for c in casos if c.veredito == Veredito.INCONCLUSIVO])
    return "\n".join(linhas) + "\n"


class RodadaInvalida(Exception):
    """resultado.json ausente, corrompido ou sem as chaves esperadas."""


def _carrega(diretorio: Path) -> dict[str, Veredito]:
    arq = Path(diretorio) / "resultado.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise RodadaInvalida(f"{arq}: arquivo ausente") from e
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise RodadaInvalida(f"{arq}: JSON invalido ({e})") from e
    try:
        return {c["id"]: Veredito(c["veredito"]) for c in dados["casos"]}
    except (KeyError, TypeError) as e:
        raise RodadaInvalida(f"{arq}: chave ausente ou formato inesperado ({e!r})") from e
    except ValueError as e:
        raise RodadaInvalida(f"{arq}: veredito desconhecido ({e})") from e


def compara_rodadas(
    antes: Path, depois: Path
) -> list[tuple[str, Veredito | None, Veredito | None]]:
    """Mudancas entre rodadas, ordenadas por id. None = caso ausente na rodada."""
    a, d = _carrega(antes), _carrega(depois)
    return [
        (i, a.get(i), d.get(i)) for i in sorted(a.keys() | d.keys()) if a.get(i) != d.get(i)
    ]
