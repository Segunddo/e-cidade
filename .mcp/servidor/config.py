"""Configuracao do servidor, lida do ambiente a cada chamada (nada fica preso no import).

Os nomes de conteiner usam as MESMAS variaveis da suite `regressao/` (regressao/nucleo/ambiente.py), com os
padroes do ambiente isolado `e74`.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from servidor.seguranca import ErroFerramenta

RAIZ_PADRAO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    raiz: Path
    dir_codigo: str = "ecidade"              # relativo a raiz; e o que esta montado nos conteineres
    dir_no_conteiner: str = "/var/www/html"  # onde `ecidade/` aparece dentro dos conteineres
    container_ref: str = "ecidade74_php74"   # referencia (gabarito) PHP 7.4 / Laravel 8
    container_alvo: str = "ecidade74_php85"  # alvo PHP 8.5
    container_banco: str = "ecidade74_database"
    docker: str = "docker"
    python_regressao: str = "regressao/.venv/bin/python"
    timeout_lint_s: int = 60
    timeout_phpstan_s: int = 600
    timeout_busca_s: float = 120.0
    max_saida: int = 60_000                  # caracteres devolvidos por saida de comando/texto
    max_arquivo: int = 3_000_000             # bytes: arquivos maiores sao pulados na busca
    expira_horas: float = 4.0
    usuario: str | None = None
    area: str | None = None                  # sua area no grupo (ECIDADE_MCP_AREA): nucleo, educacao, pessoal...
    tarefa: str | None = None                # numero da tarefa do grupo (ECIDADE_MCP_TAREFA): vira o NN de "PHP8-NN:"

    @property
    def prefixo_commit(self) -> str:
        """Prefixo do assunto do commit (CONTRIBUINDO.md, "Commits"): `PHP8-NN:`, NN = numero da tarefa do grupo."""
        return f"PHP8-{self.tarefa or 'NN'}:"

    @property
    def arquivo_estado(self) -> Path:
        return self.raiz / ".mcp" / "estado" / "trabalho.json"

    @property
    def dir_rodadas(self) -> Path:
        return self.raiz / ".mcp" / "rodadas"

    @property
    def dir_docs(self) -> Path:
        return self.raiz / ".mcp" / "docs"

    @property
    def conteineres_permitidos(self) -> tuple[str, str]:
        return (self.container_ref, self.container_alvo)


def _num(env: Mapping[str, str], nome: str, padrao: float, tipo=float):
    bruto = env.get(nome)
    if bruto is None or bruto == "":
        return padrao
    try:
        v = tipo(bruto)
    except ValueError:
        raise ErroFerramenta("config_invalida", f"{nome}={bruto!r} nao e um numero") from None
    if v <= 0:
        raise ErroFerramenta("config_invalida", f"{nome} precisa ser > 0")
    return v


def _tarefa(env: Mapping[str, str]) -> str | None:
    bruto = (env.get("ECIDADE_MCP_TAREFA") or "").strip()
    if not bruto:
        return None
    if not bruto.isascii() or not bruto.isdigit() or len(bruto) > 6:
        raise ErroFerramenta("config_invalida", f"ECIDADE_MCP_TAREFA={bruto!r}: use so o numero da tarefa (ex.: 31)")
    return str(int(bruto))


def carregar_config(env: Mapping[str, str] | None = None) -> Config:
    env = os.environ if env is None else env
    raiz = Path(env.get("ECIDADE_MCP_RAIZ") or RAIZ_PADRAO).resolve()
    if not raiz.is_dir():
        raise ErroFerramenta("config_invalida", f"ECIDADE_MCP_RAIZ nao e diretorio: {raiz}")
    return Config(
        raiz=raiz,
        container_ref=env.get("REGRESSAO_CONTAINER_REF") or "ecidade74_php74",
        container_alvo=env.get("REGRESSAO_CONTAINER_PHP_NOVO") or "ecidade74_php85",
        container_banco=env.get("REGRESSAO_CONTAINER_BANCO") or "ecidade74_database",
        docker=env.get("ECIDADE_MCP_DOCKER") or "docker",
        timeout_phpstan_s=int(_num(env, "ECIDADE_MCP_TIMEOUT_PHPSTAN", 600, int)),
        expira_horas=float(_num(env, "ECIDADE_MCP_EXPIRA_HORAS", 4.0)),
        usuario=env.get("ECIDADE_MCP_USUARIO") or None,
        area=env.get("ECIDADE_MCP_AREA") or None,
        tarefa=_tarefa(env),
    )
