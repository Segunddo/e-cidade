"""Portao de equivalencia: a arvore instrumentada responde IGUAL a normal?

Se uma sonda mudar o comportamento de uma tela, o rastreador nao serve para nada (anti-objetivo do design). Para cada tela:
o mesmo lado (7.4 e 8.5) na arvore normal (porta 80) x instrumentada (porta 8091), comparando codigo HTTP + resposta
normalizada. Diferenca so conta se a propria resposta normal e estavel (duas leituras iguais); senao e `instavel`.
"""
import random
from dataclasses import dataclass, field

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.php import telas as T
from regressao.rastro.executor import corpo_normalizado, roda_requisicao


@dataclass
class ResultadoEquivalencia:
    total: int = 0
    diferentes: list = field(default_factory=list)   # (tela, lado): normal estavel e instrumentada diferente
    instaveis: list = field(default_factory=list)    # (tela, lado): a resposta normal ja muda sozinha


def amostra_telas(n: int, semente: int = 7) -> list[str]:
    todas = T.lista_telas("")
    return sorted(random.Random(semente).sample(todas, min(n, len(todas))))


def confere_equivalencia(sid: str, telas: list[str], containers: tuple[str, ...] | None = None) -> ResultadoEquivalencia:
    c = containers_do_ambiente()
    containers = containers or (c.ref, c.php_novo)
    r = ResultadoEquivalencia(total=len(telas))
    for tela in telas:
        for lado in containers:
            normal = roda_requisicao(sid, tela, "eq", lado, instrumentado=False)
            inst = roda_requisicao(sid, tela, f"eq_{lado[-2:]}_{tela[:30]}", lado, instrumentado=True)
            a = (normal.status, corpo_normalizado(normal.corpo))
            if a == (inst.status, corpo_normalizado(inst.corpo)):
                continue
            outra = roda_requisicao(sid, tela, "eq", lado, instrumentado=False)
            if a != (outra.status, corpo_normalizado(outra.corpo)):
                r.instaveis.append((tela, lado))
            else:
                r.diferentes.append((tela, lado))
    return r
