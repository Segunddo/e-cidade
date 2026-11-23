import subprocess

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import ErroAmbienteBanco, _docker
from regressao.nucleo.veredito import Caso, Veredito

AREA = "php-sintaxe"
TIMEOUT_LINT = 60
_OK = "No syntax errors detected"
ROTULO_REF = "referencia (7.4)"
ROTULO_NOVO = "php8.5"


def containers_php() -> tuple[str, str]:
    """(referencia, alvo PHP 8.5), lidos de regressao/nucleo/ambiente.py a cada chamada."""
    c = containers_do_ambiente()
    return c.ref, c.php_novo


def _lint(container: str, arquivo: str) -> tuple[bool, str]:
    # stdin de /dev/null: sem isso o php consome o resto de uma lista lida em loop.
    # 2>&1 + `|| true`: php -l sai com 255 e escreve a mensagem em stdout/stderr.
    saida = _docker(
        ["exec", container, "sh", "-c",
         'cd /var/www/html && php -l "$1" 2>&1 </dev/null || true', "sh", arquivo],
        TIMEOUT_LINT, stdin=subprocess.DEVNULL,
    ).decode("utf-8", errors="replace").strip()
    return _OK in saida, saida


def roda_lint(arquivos: list[str]) -> list[Caso]:
    ref, novo = containers_php()
    casos = []
    for arq in arquivos:
        try:
            ok_ref, msg_ref = _lint(ref, arq)
            ok85, msg85 = _lint(novo, arq)
        except ErroAmbienteBanco as e:
            casos.append(Caso(arq, AREA, Veredito.ERRO_AMBIENTE, str(e)))
            continue
        if ok_ref and ok85:
            casos.append(Caso(arq, AREA, Veredito.IDENTICO))
        elif ok_ref != ok85:
            falha = f"{ROTULO_NOVO}: {msg85}" if ok_ref else f"{ROTULO_REF}: {msg_ref}"
            casos.append(Caso(arq, AREA, Veredito.DIVERGE, falha))
        else:
            casos.append(Caso(arq, AREA, Veredito.INCONCLUSIVO,
                              f"nao compila em nenhum runtime. {ROTULO_REF}: {msg_ref} | {ROTULO_NOVO}: {msg85}"))
    return casos
