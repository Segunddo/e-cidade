"""Execucao de php/phpstan/pint SEMPRE dentro dos conteineres do projeto e74, por `docker exec`.

Sem shell: o comando e uma lista de argumentos conferida contra modelos fixos (allowlist). O conteiner
precisa estar na lista configurada (referencia 7.4 e alvo 8.5). Conteiner ausente/parado, docker ausente
e tempo esgotado viram `ErroFerramenta` (resposta estruturada; o servidor continua de pe).
"""
from __future__ import annotations

import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from servidor.config import Config
from servidor.seguranca import ErroFerramenta, decodificar, limitar

_NOME_CONTEINER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_D_PERMITIDO = re.compile(r"^memory_limit=\d+[MG]$")
_OPCOES_PHPSTAN = re.compile(r"^--(no-progress|no-interaction|error-format=json|level=[0-9]|memory-limit=\d+[MG])$")
FERRAMENTAS = ("lint", "phpstan", "pint", "phpcs")


@dataclass
class ResultadoExec:
    conteiner: str
    comando: list[str]
    codigo_saida: int
    stdout: str
    stderr: str
    truncado: bool
    duracao_s: float

    def como_dict(self) -> dict[str, Any]:
        return {
            "conteiner": self.conteiner,
            "comando": self.comando,
            "codigo_saida": self.codigo_saida,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "truncado": self.truncado,
            "duracao_s": self.duracao_s,
        }


def caminho_no_conteiner(config: Config, absoluto: Path) -> str:
    """`<raiz>/ecidade/x/y.php` -> `/var/www/html/x/y.php`. So `ecidade/` esta montado nos conteineres."""
    base = (config.raiz / config.dir_codigo).resolve()
    try:
        rel = absoluto.resolve().relative_to(base)
    except ValueError:
        raise ErroFerramenta(
            "fora_do_codigo",
            f"so arquivos dentro de {config.dir_codigo}/ existem no conteiner (montado em {config.dir_no_conteiner})",
        ) from None
    return f"{config.dir_no_conteiner}/{rel.as_posix()}"


def comando_ferramenta(ferramenta: str, arquivo: str, nivel: int | None = None) -> list[str]:
    if ferramenta == "lint":
        # display_errors=stderr: os conteineres tem display_errors=Off (paridade 7.4 x 8.5); sem isso o motivo e a
        # linha do erro de sintaxe so vao para o log do PHP e o lint diz apenas "Errors parsing <arquivo>"
        return ["php", "-d", "display_errors=stderr", "-l", arquivo]
    if ferramenta == "phpstan":
        # display_errors=stderr: avisos do proprio PHPStan (ex.: Deprecated no 8.5) nao sujam o JSON do stdout
        cmd = ["php", "-d", "memory_limit=1G", "-d", "display_errors=stderr", "vendor/bin/phpstan", "analyse",
               "--no-progress", "--no-interaction", "--error-format=json"]
        if nivel is not None:
            cmd.append(f"--level={int(nivel)}")
        return cmd + [arquivo]
    if ferramenta == "pint":
        return ["vendor/bin/pint", "--test", arquivo]
    if ferramenta == "phpcs":
        return ["vendor/bin/phpcs", "--report=json", "--standard=PSR12", arquivo]
    raise ErroFerramenta("ferramenta_desconhecida", f"ferramenta {ferramenta!r}; use uma de {', '.join(FERRAMENTAS)}")


def _caminho_ok(arg: str, base: str) -> bool:
    return arg.startswith(base + "/") and ".." not in arg.split("/")


def _validar_argv(argv: list[str], base: str) -> None:
    """Allowlist por modelo: so os comandos que as tools montam passam."""
    ruim = ErroFerramenta("comando_nao_permitido", f"comando fora da lista permitida: {argv!r}")
    if not argv or any((not isinstance(a, str)) or "\x00" in a or "\n" in a for a in argv):
        raise ruim
    match argv:
        case ["php", "-v"] | ["php", "-m"] | ["test", "-x", "vendor/bin/pint" | "vendor/bin/phpcs" | "vendor/bin/phpstan"]:
            return
        case ["php", "-l", arq] | ["php", "-d", "display_errors=stderr", "-l", arq] if _caminho_ok(arq, base):
            return
        case ["php", "-d", d, "-d", "display_errors=stderr", "vendor/bin/phpstan", "analyse", *resto] if (
                _D_PERMITIDO.match(d) and resto):
            *opcoes, arq = resto
            if _caminho_ok(arq, base) and all(_OPCOES_PHPSTAN.match(o) for o in opcoes):
                return
        case ["vendor/bin/pint", "--test", arq] if _caminho_ok(arq, base):
            return
        case ["vendor/bin/phpcs", "--report=json", "--standard=PSR12", arq] if _caminho_ok(arq, base):
            return
    raise ruim


class DockerExec:
    def __init__(self, config: Config, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.config = config
        self.runner = runner

    def _run(self, argv: list[str], timeout: float) -> subprocess.CompletedProcess:
        try:
            r = self.runner(argv, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL, check=False)
            # bytes -> texto com a regra do repositorio (ISO-8859-1 por padrao; UTF-8 so se valido)
            for campo in ("stdout", "stderr"):
                v = getattr(r, campo)
                if isinstance(v, bytes):
                    setattr(r, campo, decodificar(v))
            return r
        except FileNotFoundError:
            raise ErroFerramenta("docker_indisponivel",
                                 f"comando {self.config.docker!r} nao encontrado (Docker instalado e no PATH?)") from None
        except subprocess.TimeoutExpired:
            raise ErroFerramenta("tempo_esgotado", f"o comando passou de {timeout:.0f}s", comando=argv) from None

    def verificar_conteiner(self, nome: str) -> None:
        if not _NOME_CONTEINER.match(nome or ""):
            raise ErroFerramenta("conteiner_nao_permitido", f"nome de conteiner invalido: {nome!r}")
        r = self._run([self.config.docker, "inspect", "--format", "{{.State.Running}}", nome], timeout=20)
        if r.returncode != 0:
            raise ErroFerramenta(
                "conteiner_indisponivel",
                f"conteiner {nome!r} nao existe neste Docker. Suba o ambiente: "
                "docker compose -p e74 -f regressao/lab/docker-compose.e74.yml up -d",
                stderr=(r.stderr or "").strip()[:500],
            )
        if (r.stdout or "").strip() != "true":
            raise ErroFerramenta("conteiner_parado", f"conteiner {nome!r} existe mas esta parado (docker start {nome})")

    def executar(self, conteiner: str, argv: list[str], *, timeout: int) -> ResultadoExec:
        if conteiner not in self.config.conteineres_permitidos:
            raise ErroFerramenta(
                "conteiner_nao_permitido",
                f"so os conteineres do projeto: {', '.join(self.config.conteineres_permitidos)}",
            )
        _validar_argv(argv, self.config.dir_no_conteiner)
        self.verificar_conteiner(conteiner)
        # `timeout` DENTRO do conteiner: matar o cliente docker nao mata o processo la dentro.
        cmd = [self.config.docker, "exec", "-w", self.config.dir_no_conteiner, conteiner,
               "timeout", "-k", "5", f"{int(timeout)}s", *argv]
        inicio = time.monotonic()
        r = self._run(cmd, timeout=timeout + 20)
        dur = round(time.monotonic() - inicio, 2)
        err = r.stderr or ""
        if r.returncode in (125, 126, 127) and ("No such container" in err or "is not running" in err):
            raise ErroFerramenta("conteiner_indisponivel", f"conteiner {conteiner!r} sumiu durante o exec",
                                 stderr=err.strip()[:500])
        if r.returncode == 124:
            raise ErroFerramenta("tempo_esgotado", f"{argv[0]} passou de {timeout}s dentro do conteiner")
        out, t1 = limitar(r.stdout or "", self.config.max_saida)
        err, t2 = limitar(err, self.config.max_saida // 4)
        return ResultadoExec(conteiner, argv, r.returncode, out, err, t1 or t2, dur)
