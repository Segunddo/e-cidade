import re

from regressao.nucleo.veredito import Caso, Veredito

_CABECALHO = re.compile(rb"<thead\b.*?</thead>", re.S | re.I)
_TD = re.compile(rb"<td\b", re.I)


def tem_dados(corpo: bytes) -> bool:
    """Heuristica fixa: ha linha de dados se existir `<td` fora do cabecalho (<thead>)."""
    return _TD.search(_CABECALHO.sub(b"", corpo)) is not None


def cobertura_de_flags(flags: dict[str, bool]) -> dict:
    """Como cobertura_telas, a partir de {tela: tem_dados} (sem guardar corpos)."""
    return {"com_dados": sorted(t for t, f in flags.items() if f),
            "tabela_vazia": sorted(t for t, f in flags.items() if not f)}


def cobertura_telas(casos: list[Caso], corpos: dict[str, bytes]) -> dict:
    """Separa as telas com dados das de tabela vazia (nao exercitam o conteudo). Telas com
    ERRO_AMBIENTE nos casos sao ignoradas (nao ha corpo confiavel)."""
    ignorar = {c.id for c in casos if c.veredito == Veredito.ERRO_AMBIENTE}
    return cobertura_de_flags({t: tem_dados(c) for t, c in corpos.items() if t not in ignorar})
