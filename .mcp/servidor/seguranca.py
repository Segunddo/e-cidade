"""Confinamento de caminhos, segredos, regex e limites. Toda tool passa por aqui antes de tocar no disco.

Regras: so caminhos dentro da raiz do repositorio (symlinks resolvidos), nunca `..`, nunca `.git/`, nunca
arquivos de segredo (.env, chaves, db_conn.php). Erros viram `ErroFerramenta` (resposta estruturada).
"""
from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Literal

MAX_CAMINHO = 1024
MAX_REGEX = 300

_SEGREDOS_NOME = re.compile(
    r"^(\.env.*|db_conn\.php|db_acessa\.php|auth\.json|id_rsa.*|.*\.(key|pem|p12|pfx|crt|log))$", re.IGNORECASE
)
# negacao por CAMINHO (nao so pelo nome): diretorios com dados de execucao, logs, sessoes, caches e configs com senha
_DIRS_NEGADOS = {".git", "storage", "tmp"}
_SEQUENCIAS_NEGADAS = (("bootstrap", "cache"), ("extension", "log"))
_FINAIS_NEGADOS = (("config", "application.php"), ("config", "ecidade_config.php"))
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-_]")
_METACARACTERES = re.compile(r"[;&|$`<>(){}*?!'\"\\\x00-\x1f\x7f]")


class ErroFerramenta(Exception):
    """Erro previsto de uma tool: vira `{"ok": false, "erro": {...}}` e nunca derruba o servidor."""

    def __init__(self, codigo: str, mensagem: str, **detalhes: Any) -> None:
        super().__init__(f"{codigo}: {mensagem}")
        self.codigo = codigo
        self.mensagem = mensagem
        self.detalhes = detalhes

    def como_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"codigo": self.codigo, "mensagem": self.mensagem}
        if self.detalhes:
            d["detalhes"] = self.detalhes
        return d


def eh_segredo(rel: Path) -> bool:
    """So pelo nome (.env*, chaves, db_conn.php, *.log...)."""
    return bool(_SEGREDOS_NOME.match(rel.name))


def eh_negado(rel: Path) -> bool:
    """Caminho relativo a raiz que nenhuma tool le nem varre (nome de segredo OU caminho negado)."""
    partes = tuple(p.lower() for p in rel.parts)
    if not partes:
        return False
    if any(p in _DIRS_NEGADOS for p in partes):
        return True
    pares = set(zip(partes, partes[1:]))
    if any(s in pares for s in _SEQUENCIAS_NEGADAS):
        return True
    if partes[-2:] in _FINAIS_NEGADOS:
        return True
    return eh_segredo(Path(partes[-1]))


def tem_metacaractere(s: str) -> bool:
    return bool(_METACARACTERES.search(s))


def limpar_texto(s: str | None, maximo: int) -> str:
    """Texto livre de terceiros (motivo, observacao, quem): sem ANSI, sem controles, uma linha, tamanho limitado."""
    s = _ANSI.sub("", s or "")
    s = "".join(" " if c in "\t\r\n" else c for c in s
                if unicodedata.category(c) not in ("Cc", "Cf") or c in "\t\r\n")
    return " ".join(s.split())[:maximo]


def resolver_caminho(
    raiz: Path,
    caminho: str,
    *,
    deve_existir: bool = True,
    tipo: Literal["arquivo", "diretorio"] | None = None,
) -> Path:
    """Caminho absoluto, com symlinks resolvidos, garantidamente dentro de `raiz`."""
    if not isinstance(caminho, str) or not caminho or "\x00" in caminho or len(caminho) > MAX_CAMINHO:
        raise ErroFerramenta("caminho_invalido", "caminho vazio, longo demais ou com byte nulo")
    p = Path(caminho)
    if ".." in p.parts:
        raise ErroFerramenta("caminho_fora_da_raiz", "nao use '..': informe o caminho relativo a raiz do repositorio")
    raiz_r = raiz.resolve(strict=True)
    pedido = Path(os.path.abspath(p if p.is_absolute() else raiz_r / p))  # sem resolver symlinks
    alvo = pedido.resolve(strict=False)
    if alvo != raiz_r and raiz_r not in alvo.parents:
        raise ErroFerramenta("caminho_fora_da_raiz", f"{caminho!r} fica fora do repositorio")
    rel = alvo.relative_to(raiz_r)
    if ".git" in rel.parts:
        raise ErroFerramenta("caminho_proibido", "o diretorio .git nao e acessivel pelas tools")
    rel_pedido = pedido.relative_to(raiz_r) if (pedido == raiz_r or raiz_r in pedido.parents) else rel
    if eh_negado(rel) or eh_negado(rel_pedido):  # o pedido E o alvo resolvido (symlink interno para .env)
        raise ErroFerramenta("caminho_proibido",
                             f"{rel_pedido.as_posix()} e segredo, log, cache ou dado de execucao e nao e lido")
    if deve_existir and not alvo.exists():
        raise ErroFerramenta("caminho_inexistente", f"{rel.as_posix() or '.'} nao existe")
    if tipo == "arquivo" and alvo.exists() and not alvo.is_file():
        raise ErroFerramenta("tipo_invalido", f"{rel.as_posix() or '.'} nao e arquivo")
    if tipo == "diretorio" and alvo.exists() and not alvo.is_dir():
        raise ErroFerramenta("tipo_invalido", f"{rel.as_posix() or '.'} nao e diretorio")
    return alvo


def relativo(raiz: Path, p: Path) -> str:
    rel = p.resolve().relative_to(raiz.resolve()).as_posix()
    return rel or "."


def validar_regex(rx: str, flags: int = 0) -> re.Pattern[str]:
    if not isinstance(rx, str) or not rx or len(rx) > MAX_REGEX:
        raise ErroFerramenta("regex_invalida", f"regex vazia ou maior que {MAX_REGEX} caracteres")
    try:
        return re.compile(rx, flags)
    except re.error as e:
        raise ErroFerramenta("regex_invalida", f"regex invalida: {e}") from None


def decodificar(dados: bytes) -> str:
    """Texto de arquivo do repositorio. O codigo do e-Cidade e ISO-8859-1 (regra do grupo: nao salvar em UTF-8):
    o padrao e latin-1, que nunca falha. So um arquivo que e UTF-8 VALIDO e tem bytes nao-ASCII (arquivos novos
    do Laravel, JSON) e lido como UTF-8 -- num arquivo ISO-8859-1 de verdade, acento solto (0xE7, 0xE3...) nunca
    forma UTF-8 valido, entao ele cai no latin-1."""
    if dados.isascii():
        return dados.decode("ascii")
    try:
        return dados.decode("utf-8")
    except UnicodeDecodeError:
        return dados.decode("latin-1", errors="replace")


def limitar(texto: str, maximo: int) -> tuple[str, bool]:
    if len(texto) <= maximo:
        return texto, False
    return texto[:maximo] + f"\n[... truncado: {len(texto) - maximo} caracteres omitidos]", True
