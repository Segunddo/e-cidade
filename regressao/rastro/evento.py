"""Evento de rastro (uma linha do .jsonl gravado pelo rt.php, ou do log da aplicacao) e leitura."""
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Evento:
    seq: int
    sonda: int            # 0 = evento de handler (aviso `w`, fatal/excecao `e`, truncado `T`)
    arquivo: str
    linha: int
    tipo: str             # a atribuicao | c chamada | b condicao | r retorno | x catch | w aviso | e excecao/fatal | T truncado
    nome: str
    valor: dict | None = None
    args: tuple | None = None


def le_rastro(linhas: list[str]) -> list[Evento]:
    saida = []
    for l in linhas:
        l = l.strip()
        if not l:
            continue
        try:
            j = json.loads(l)
        except ValueError:
            continue
        a = j.get("a")
        saida.append(Evento(seq=int(j.get("s", 0)), sonda=int(j.get("p", 0) or 0), arquivo=j.get("f", ""),
                            linha=int(j.get("l", 0) or 0), tipo=j.get("k", ""), nome=str(j.get("n", "")),
                            valor=j.get("v"), args=tuple(json.dumps(x, sort_keys=True) for x in a) if a else None))
    return saida
