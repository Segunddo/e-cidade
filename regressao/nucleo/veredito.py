from dataclasses import dataclass
from enum import Enum


class Veredito(str, Enum):
    IDENTICO = "IDENTICO"
    DIVERGE = "DIVERGE"
    INCONCLUSIVO = "INCONCLUSIVO"
    ERRO_AMBIENTE = "ERRO_AMBIENTE"


@dataclass
class Caso:
    id: str
    area: str
    veredito: Veredito
    detalhe: str = ""
    diff: str = ""
    conhecida: bool = False


def codigo_saida(casos: list[Caso]) -> int:
    """2 se houver ERRO_AMBIENTE; 1 se houver DIVERGE nao conhecida; senao 0."""
    if any(c.veredito == Veredito.ERRO_AMBIENTE for c in casos):
        return 2
    if any(c.veredito == Veredito.DIVERGE and not c.conhecida for c in casos):
        return 1
    return 0
