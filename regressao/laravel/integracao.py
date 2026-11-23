"""Integracoes da bateria Laravel (Task 11b): arquivo gerado (PDF/CSV/XLS) por CONTEUDO, console/artisan,
e-mail capturado por SMTP de teste, PIX contra stub. Tudo roda dentro da bateria existente: baseline
golden master gravada na referencia (Laravel 8 da base 7.4) e comparada no alvo novo.

- `segue_arquivo`: rotas que respondem JSON com o caminho do arquivo gerado (`data.path`, `data.csv`...)
  baixam o arquivo e comparam o TEXTO extraido (`extrai_conteudo`: pypdf/openpyxl/xlrd/CSV), nunca os bytes.
- `roda_console`: `php artisan <args>` no container do alvo (`container_console`: referencia, laboratorio ou
  REGRESSAO_LARAVEL_CONSOLE_CONTAINER); so comandos sem efeito (list, env, migrate:status): a saida e normalizada.
- `compara_email` / `stubs.smtp_stub`: normaliza Date/Message-ID/fronteiras MIME.
- `stubs.pix_stub`: servidor HTTP que responde como o PSP e registra o que a aplicacao enviou.
  LIMITE REAL (README): o app tem as URLs do BB fixas em constantes HTTPS (`BancoDoBrasil::BASE_URL`), entao
  apontar o app ao stub exige DNS/TLS no container, algo que esta bateria nao altera.
"""
import contextlib
import email
import email.policy
import hashlib
import os
import re
import subprocess
from email import message_from_bytes

import requests

from regressao.laravel.mascara import _texto as _normaliza_caminhos
from regressao.nucleo.ambiente import alvos_do_ambiente, containers_do_ambiente
from regressao.nucleo.veredito import Caso, Veredito

DIR_APP_PADRAO = "/var/www/html"
TIMEOUT_CONSOLE = 120
LIMITE_ARQUIVO = 20_000
_RE_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


# ---------------------------------------------------------------- arquivo gerado

def valor_json(obj, caminho: str):
    """`a.b.c` em dicts aninhados; None se ausente."""
    for parte in caminho.split("."):
        if not isinstance(obj, dict) or parte not in obj:
            return None
        obj = obj[parte]
    return obj


def tipo_do_arquivo(corpo: bytes) -> str:
    if corpo.lstrip().startswith(b"%PDF"):
        return "pdf"
    if corpo.startswith(b"PK\x03\x04") or corpo.startswith(b"\xd0\xcf\x11\xe0"):
        return "xls"
    return "csv"


def segue_arquivo(base_url: str, relativo, headers: dict, get=None) -> str:
    """Baixa o arquivo gerado e devolve `[arquivo <tipo> status=<s> ct=<content-type>]\\n<texto extraido>`."""
    from regressao.php.relatorios import extrai_conteudo
    if not isinstance(relativo, str) or not relativo:
        return "[arquivo ausente na resposta]"
    get = get or requests.get
    r = get(base_url.rstrip("/") + "/" + relativo.lstrip("/"), headers=headers, timeout=60, allow_redirects=False)
    tipo = tipo_do_arquivo(r.content)
    try:
        texto = extrai_conteudo(r.content, "pdf" if tipo == "pdf" else "xls")
    except Exception as e:  # arquivo ilegivel: fica registrado, nao vira aprovacao silenciosa
        texto = f"<<ilegivel: {type(e).__name__}>>"
    ct = (r.headers.get("content-type") or "").split(";")[0]
    return f"[arquivo {tipo} status={r.status_code} ct={ct}]\n" + texto[:LIMITE_ARQUIVO]


# ---------------------------------------------------------------- console

def normaliza_saida_console(texto: str, modo: str | None = None) -> str:
    """Sem ANSI, caminhos absolutos como `<caminho>`, sem espacos no fim. modo `nomes`: so o 1o campo de
    cada linha (comandos de `list --raw`), ordenado: descricoes mudam com a versao, a existencia nao."""
    texto = _RE_ANSI.sub("", texto).replace("\r", "")
    linhas = [_normaliza_caminhos(l).rstrip() for l in texto.split("\n")]
    if modo == "nomes":
        return "\n".join(sorted({l.split()[0] for l in linhas if l.strip()})) + "\n"
    if modo == "migracoes":
        # `migrate:status`: o CONJUNTO de migrations (estado + nome), sem depender da largura da tabela nem da
        # ordem, e sem truncar: cabecalho com contagem e sha256 do conjunto completo. Laravel 8 escreve
        # Yes/No (o 5.4 escrevia Y/N): os dois viram Y/N, a coluna Batch e ignorada.
        itens = sorted({f"{m.group(1)[0]} {m.group(2)}" for l in linhas
                        for m in [re.match(r"^\|\s*(Yes|No|Y|N)\s*\|\s*(\S+)\s*\|", l)] if m})
        corpo = "\n".join(itens)
        ran = sum(1 for i in itens if i.startswith("Y "))
        return (f"migrations={len(itens)} ran={ran} sha256={hashlib.sha256(corpo.encode()).hexdigest()}\n"
                + corpo + ("\n" if corpo else ""))
    return "\n".join(linhas).strip("\n") + "\n"


class ErroConsole(RuntimeError):
    """Falha de AMBIENTE do console (container ausente, docker, comando fora da allowlist): nunca e veredito."""


COMANDOS_PERMITIDOS = frozenset({"list", "env", "migrate:status"})  # so leitura; comandos de dominio escrevem
_FALHA_DO_DOCKER = (125, 126, 127)
_RE_DOCKER_ERRO = re.compile(rb"No such container|Error response from daemon|is not running|Cannot connect to the Docker",
                             re.I)


def container_console(base_url: str) -> str:
    """Container do `artisan` para ESTE alvo (nomes em nucleo/ambiente.py). Na referencia (REGRESSAO_REF_URL) e
    sempre o container de referencia: gravar nunca usa um container novo. Em outro alvo: a variavel
    REGRESSAO_LARAVEL_CONSOLE_CONTAINER, ou, sem ela, o container do laboratorio se o alvo for
    REGRESSAO_LARAVEL_NOVO_URL. Alvo desconhecido sem a variavel, ou um alvo novo que caia no container de
    referencia, e ErroConsole: o console rodaria na referencia e daria falso IDENTICO."""
    alvos, containers = alvos_do_ambiente(), containers_do_ambiente()
    u = base_url.rstrip("/")
    if u == alvos.ref.rstrip("/"):
        return containers.ref
    container = os.environ.get("REGRESSAO_LARAVEL_CONSOLE_CONTAINER")
    if not container and u == alvos.laravel_novo.rstrip("/"):
        container = containers.laravel_novo
    if not container:
        raise ErroConsole(f"alvo {base_url} nao e a referencia nem o laboratorio: defina "
                          "REGRESSAO_LARAVEL_CONSOLE_CONTAINER com o container do artisan do alvo "
                          "(senao o console rodaria na referencia: falso IDENTICO)")
    if container == containers.ref:
        raise ErroConsole(f"alvo {base_url} nao e a referencia, mas o console cairia no container de referencia "
                          f"({container}): falso IDENTICO")
    return container


def roda_console(args: list[str], modo: str | None = None, runner=None,
                 container: str | None = None) -> tuple[int, str]:
    """(codigo de saida, saida normalizada) de `php artisan <args>` no container de console (padrao: o de
    referencia). Comando fora da allowlist ou falha do `docker exec` (125/126/127, container inexistente)
    levanta ErroConsole."""
    if not args or args[0] not in COMANDOS_PERMITIDOS:
        raise ErroConsole(f"comando artisan fora da allowlist {sorted(COMANDOS_PERMITIDOS)}: {args[:1]}")
    container = container or containers_do_ambiente().ref
    cmd = ["docker", "exec", "-w", DIR_APP_PADRAO, container, "php", "artisan", *args]
    r = (runner or _roda)(cmd)
    erro = r.stderr or b""
    if r.returncode in _FALHA_DO_DOCKER or (r.returncode != 0 and _RE_DOCKER_ERRO.search(erro)):
        raise ErroConsole(f"docker exec falhou (codigo {r.returncode}) no container {container}: "
                          + erro.decode("utf-8", "replace").strip().splitlines()[0][:150] if erro.strip()
                          else f"docker exec falhou (codigo {r.returncode}) no container {container}")
    bruto = (r.stdout or b"") + (b"\n" + erro if erro else b"")
    return r.returncode, normaliza_saida_console(bruto.decode("utf-8", errors="replace"), modo)


def _roda(cmd: list[str]):
    try:
        return subprocess.run(cmd, capture_output=True, timeout=TIMEOUT_CONSOLE)
    except (OSError, subprocess.SubprocessError) as e:
        raise ErroConsole(f"console indisponivel ({type(e).__name__}): {' '.join(cmd[:6])}") from None


# ---------------------------------------------------------------- e-mail

_CABECALHOS_EMAIL = ("subject", "from", "to", "cc", "bcc", "reply-to", "content-type", "mime-version",
                     "content-transfer-encoding")
_RE_BOUNDARY = re.compile(r'boundary="?([^";\s]+)"?', re.I)


def normaliza_email(bruto: bytes) -> dict:
    """Assunto, remetente/destinatarios, tipos MIME e corpo; sem Date, Message-ID e fronteiras MIME."""
    msg = message_from_bytes(bruto, policy=email.policy.default)
    fronteiras = {m.group(1) for h in msg.walk() for m in [_RE_BOUNDARY.search(h.get("content-type", ""))] if m}
    cab = {}
    for nome in _CABECALHOS_EMAIL:
        valor = msg.get(nome)
        if valor is not None:
            v = str(valor)
            for f in fronteiras:
                v = v.replace(f, "<BOUNDARY>")
            cab[nome] = re.sub(r"\s+", " ", v).strip()
    partes = []
    for p in msg.walk():
        if p.is_multipart():
            continue
        try:
            conteudo = p.get_content()
        except Exception:
            conteudo = p.get_payload(decode=True) or b""
        if isinstance(conteudo, bytes):
            conteudo = f"<{len(conteudo)} bytes binarios>"
        for f in fronteiras:
            conteudo = conteudo.replace(f, "<BOUNDARY>")
        partes.append({"tipo": p.get_content_type(), "arquivo": p.get_filename(),
                       "corpo": re.sub(r"\s+", " ", conteudo).strip()})
    return {"cabecalhos": cab, "partes": partes}


def compara_email(msg_ref: bytes, msg_novo: bytes, id: str = "email") -> Caso:
    a, b = normaliza_email(msg_ref), normaliza_email(msg_novo)
    if a == b:
        return Caso(id, "laravel", Veredito.IDENTICO)
    dif = [k for k in ("cabecalhos", "partes") if a[k] != b[k]]
    return Caso(id, "laravel", Veredito.DIVERGE, "e-mail difere em: " + ", ".join(dif),
                f"ref: {a}\nnovo: {b}\n")


@contextlib.contextmanager
def com_stubs(smtp_porta: int = 0, pix_porta: int = 0):
    """Sobe o SMTP e o PIX de teste (threads locais) e garante a parada, ate com excecao."""
    from regressao.laravel.stubs.pix_stub import PixStub
    from regressao.laravel.stubs.smtp_stub import SmtpStub
    smtp, pix = SmtpStub(smtp_porta), PixStub(pix_porta)
    smtp.inicia()
    try:
        pix.inicia()
        try:
            yield smtp, pix
        finally:
            pix.para()
    finally:
        smtp.para()
