"""O atalho `python -m regressao.laravel.caso` nao pode gravar a baseline (sem RecusaBaseline)."""
from unittest.mock import patch

from regressao.laravel import caso


def test_main_recusa_gravar_e_aponta_a_bateria_protegida(capsys):
    with patch.object(caso, "gravar") as g, patch.object(caso, "carrega_casos") as c:
        assert caso._main(["gravar"]) == 2
        assert caso._main(["gravar", "http://localhost:8080"]) == 2
    g.assert_not_called()
    c.assert_not_called()
    err = capsys.readouterr().err
    assert "regressao.laravel.bateria gravar" in err and "--confirmo-sobrescrever" in err


def test_main_modo_desconhecido_e_uso_2(capsys):
    assert caso._main([]) == 2
    assert "comparar" in capsys.readouterr().err
