import os
from pathlib import Path

import pytest

from servidor.config import Config


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    """Repositorio falso: ecidade/ (codigo montado no conteiner), regressao/baseline e .mcp/estado."""
    r = tmp_path / "repo"
    (r / "ecidade" / "classes").mkdir(parents=True)
    (r / "regressao" / "baseline").mkdir(parents=True)
    (r / ".mcp" / "estado").mkdir(parents=True)
    (r / ".mcp" / "docs").mkdir(parents=True)
    (r / "ecidade" / "tela001.php").write_text("<?php\nparse_str(base64_decode($_SERVER['QUERY_STRING']));\n")
    return r


@pytest.fixture
def config(raiz: Path) -> Config:
    return Config(raiz=raiz.resolve())


@pytest.fixture(autouse=True)
def _sem_env_do_usuario(monkeypatch):
    for k in list(os.environ):
        if k.startswith("ECIDADE_MCP_") or k.startswith("REGRESSAO_CONTAINER_"):
            monkeypatch.delenv(k, raising=False)
