"""Alinha dois rastros (7.4 x 8.5) e lista onde divergem.

CHAVE: uma sonda e (arquivo, id da sonda) e a n-esima vez que ela dispara; um evento de handler (aviso/fatal) e
(arquivo, linha, tipo, nome) + n-esima vez. Alinhar por ocorrencia (e nao por posicao) faz um laco que itera mais vezes
num lado nao descalibrar o resto do rastro.

VALOR: dois eventos sao iguais se tem o mesmo tipo e o mesmo resumo normalizado (mesma normalizacao da bateria: data/hora
e ids por requisicao saem); resumo longo (>=300 bytes, truncado) tambem compara o hash. A MENSAGEM de um aviso nao conta
(a redacao muda entre versoes do PHP): so existir ou nao existir.
"""
from collections import defaultdict
from dataclasses import dataclass

from regressao.nucleo.normaliza import normaliza
from regressao.rastro.evento import Evento

LIMITE_RESUMO = 300


@dataclass(frozen=True)
class Divergencia:
    sonda: int
    ocorrencia: int
    arquivo: str
    linha: int
    tipo: str
    nome: str
    valor_ref: dict | None
    valor_alvo: dict | None
    motivo: str            # valor | so_ref | so_alvo | aviso_x_excecao
    ordem: int = 0

    @property
    def chave(self) -> tuple:
        return (self.arquivo, self.sonda, self.linha, self.tipo, self.ocorrencia)


def _chave(e: Evento) -> tuple:
    return (e.arquivo, "s", e.sonda) if e.sonda else (e.arquivo, "h", e.linha, e.tipo, e.nome)


def _norm(v: dict | None) -> tuple:
    if v is None:
        return (None,)
    r = v.get("r", "")
    return (v.get("t"), normaliza(r.encode("utf-8", "replace")), v.get("h") if len(r) >= LIMITE_RESUMO else None)


def iguais(a: Evento, b: Evento) -> bool:
    if a.tipo == "w":                       # so a existencia importa
        return True
    return _norm(a.valor) == _norm(b.valor) and a.args == b.args


def _agrupa(eventos: list[Evento]) -> dict[tuple, list[Evento]]:
    g: dict[tuple, list[Evento]] = defaultdict(list)
    for e in eventos:
        if e.tipo != "T":
            g[_chave(e)].append(e)
    return g


def alinha_completo(ref: list[Evento], alvo: list[Evento]) -> tuple[list[Divergencia], list[tuple[Evento, Evento, int]]]:
    gr, ga = _agrupa(ref), _agrupa(alvo)
    chaves = list(dict.fromkeys([*gr, *ga]))
    divs: list[Divergencia] = []
    pares: list[tuple[Evento, Evento, int]] = []
    for ch in chaves:
        lr, la = gr.get(ch, []), ga.get(ch, [])
        for i in range(max(len(lr), len(la))):
            r = lr[i] if i < len(lr) else None
            a = la[i] if i < len(la) else None
            base = r or a
            if r and a:
                ordem = min(r.seq, a.seq)
                if iguais(r, a):
                    pares.append((r, a, ordem))
                else:
                    divs.append(Divergencia(base.sonda, i, base.arquivo, base.linha, base.tipo, base.nome,
                                            r.valor, a.valor, "valor", ordem))
            else:
                divs.append(Divergencia(base.sonda, i, base.arquivo, base.linha, base.tipo, base.nome,
                                        r.valor if r else None, a.valor if a else None,
                                        "so_ref" if r else "so_alvo", base.seq))
    return _funde_aviso_x_excecao(sorted(divs, key=lambda d: d.ordem)), pares


def _funde_aviso_x_excecao(divs: list[Divergencia]) -> list[Divergencia]:
    """Aviso so no 7.4 e excecao/fatal so no 8.5 na MESMA linha: e UMA divergencia (o 8.x endureceu o erro)."""
    usados: set[int] = set()
    saida: list[Divergencia] = []
    for i, d in enumerate(divs):
        if i in usados:
            continue
        if d.motivo == "so_ref" and d.tipo == "w":
            for j, o in enumerate(divs):
                if j not in usados and j != i and o.motivo == "so_alvo" and o.tipo == "e" and (o.arquivo, o.linha) == (d.arquivo, d.linha):
                    usados.update({i, j})
                    saida.append(Divergencia(0, d.ocorrencia, d.arquivo, d.linha, "e", o.nome, d.valor_ref, o.valor_alvo,
                                             "aviso_x_excecao", min(d.ordem, o.ordem)))
                    break
            else:
                saida.append(d)
        else:
            saida.append(d)
    return [d for k, d in enumerate(saida)]


def alinha(ref: list[Evento], alvo: list[Evento]) -> list[Divergencia]:
    return alinha_completo(ref, alvo)[0]
