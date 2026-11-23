"""Onde estao os alvos e os containers da regressao.

Os padroes sao os do ambiente isolado da base PHP 7.4 (projeto compose `e74`,
regressao/lab/docker-compose.e74.yml): referencia PHP 7.4/Laravel 8 em :8074, PHP 8.5 em :8185,
laboratorio Laravel 12 em :8187 (container ecidade74_lar12, regressao/lab/docker-compose.lar12.yml),
proxy em :8190. Tudo pode ser trocado por variavel de ambiente,
lida a cada chamada (nada fica preso no import).
"""
import os
import subprocess
from dataclasses import dataclass

import requests


@dataclass
class Alvos:
    ref: str
    php_novo: str
    laravel_novo: str
    proxy: str


@dataclass(frozen=True)
class Containers:
    ref: str
    php_novo: str
    banco: str
    proxy: str
    laravel_novo: str  # laboratorio Laravel 12 (regressao/lab/docker-compose.lar12.yml)


def alvos_do_ambiente() -> Alvos:
    # REGRESSAO_NOVO_URL e apelido de REGRESSAO_PHP_NOVO_URL (o nome mais especifico vence).
    php_novo = (os.environ.get("REGRESSAO_PHP_NOVO_URL")
                or os.environ.get("REGRESSAO_NOVO_URL")
                or "http://localhost:8185")
    return Alvos(
        ref=os.environ.get("REGRESSAO_REF_URL", "http://localhost:8074"),
        php_novo=php_novo,
        laravel_novo=os.environ.get("REGRESSAO_LARAVEL_NOVO_URL", "http://localhost:8187"),
        proxy=os.environ.get("REGRESSAO_PROXY_URL", "http://localhost:8190"),
    )


def containers_do_ambiente() -> Containers:
    return Containers(
        ref=os.environ.get("REGRESSAO_CONTAINER_REF", "ecidade74_php74"),
        php_novo=os.environ.get("REGRESSAO_CONTAINER_PHP_NOVO", "ecidade74_php85"),
        banco=os.environ.get("REGRESSAO_CONTAINER_BANCO", "ecidade74_database"),
        proxy=os.environ.get("REGRESSAO_CONTAINER_PROXY", "ecidade74_proxy"),
        laravel_novo=os.environ.get("REGRESSAO_CONTAINER_LARAVEL_NOVO", "ecidade74_lar12"),
    )


def container_do_alvo(url: str) -> str | None:
    """Container PHP que atende a URL de um alvo do ambiente (ref, PHP novo, laboratorio Laravel);
    None para o proxy (nginx, nao roda PHP) e para URL desconhecida: quem chama nunca deve cair, sem
    saber, no container de outro runtime."""
    a, c = alvos_do_ambiente(), containers_do_ambiente()
    u = url.rstrip("/")
    for alvo, container in ((a.ref, c.ref), (a.php_novo, c.php_novo), (a.laravel_novo, c.laravel_novo)):
        if u == alvo.rstrip("/"):
            return container
    return None


def containers_ativos() -> set[str] | None:
    """Nomes em `docker ps`; None se o docker nao puder ser consultado."""
    try:
        r = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                           capture_output=True, text=True, timeout=15, check=True)
    except (OSError, subprocess.SubprocessError):
        return None
    return set(r.stdout.split())


def _responde(url: str) -> bool:
    try:
        requests.get(url, timeout=5, allow_redirects=False)
        return True
    except requests.RequestException:
        return False


def verifica(alvos: Alvos) -> list[str]:
    problemas = []
    for nome, url in (("ref", alvos.ref), ("php_novo", alvos.php_novo),
                      ("laravel_novo", alvos.laravel_novo), ("proxy", alvos.proxy)):
        if not _responde(url):
            problemas.append(f"{nome}: sem resposta em 5s: {url}")
    ativos = containers_ativos()
    banco = containers_do_ambiente().banco
    if ativos is None:
        problemas.append("docker ps indisponivel")
    elif banco not in ativos:
        problemas.append(f"container ausente em docker ps: {banco}")
    return problemas
