import pytest


@pytest.fixture(autouse=True)
def _sem_reavaliacao_de_pdf_real(monkeypatch):
    """`roda_telas` reavalia DIVERGE 200x200 de PDF falando com o docker; nos testes isso e desligado (os
    testes da reavaliacao chamam `_reavalia_pdf_impl` ou ligam `_reavalia_pdf` explicitamente)."""
    from regressao.php import telas
    monkeypatch.setattr(telas, "_reavalia_pdf", lambda sid, tela: False)
