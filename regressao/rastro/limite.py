"""Limite de tempo por tela: uma analise que nao termina (trace enorme, alinhamento patologico) vira INCONCLUSIVO com o motivo em vez de
parar a corrida de 182 telas. Usa SIGALRM: so funciona na thread principal (e onde a CLI roda)."""
import signal
from contextlib import contextmanager


class TempoEsgotado(Exception):
    pass


@contextmanager
def limite_de_tempo(segundos: int):
    """`with limite_de_tempo(300): ...` levanta TempoEsgotado se o bloco passar de `segundos`. 0 = sem limite."""
    if not segundos or not hasattr(signal, "SIGALRM"):
        yield
        return

    def estoura(signum, frame):
        raise TempoEsgotado(f"passou de {segundos} s")
    antigo = signal.signal(signal.SIGALRM, estoura)
    signal.setitimer(signal.ITIMER_REAL, segundos)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, antigo)
