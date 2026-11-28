"""regressao/rastro/limite.py: uma tela que nao termina nao pode parar a corrida inteira."""
import time

import pytest

from regressao.rastro.limite import TempoEsgotado, limite_de_tempo


def test_estourar_o_tempo_interrompe_o_calculo():
    t0 = time.time()
    with pytest.raises(TempoEsgotado):
        with limite_de_tempo(1):
            while True:
                pass
    assert time.time() - t0 < 5


def test_dentro_do_limite_nao_interfere():
    with limite_de_tempo(5):
        x = sum(range(1000))
    assert x == 499500


def test_o_alarme_e_desarmado_ao_sair():
    with limite_de_tempo(1):
        pass
    time.sleep(1.3)        # se o alarme continuasse armado, estouraria aqui


def test_sem_limite_nao_arma_nada():
    with limite_de_tempo(0):
        time.sleep(0.05)
