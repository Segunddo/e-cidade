"""Token Passport (password grant) e deteccao de Laravel fora do ar.

Referencia: Laravel 8.73 + Passport 10.4 (league/oauth2-server 8): `POST /v4/oauth/token` com o cliente
`9999999` (password client que ja vem no dump da base 7.4; o segredo fica em `config/application.php`, chave
`api.client.secret`, nunca gravado). O access_token e um JWT RS256 com `jti`, `exp`, `nbf`, `iat`, `sub`,
`scopes`; o `jti` e o id em `oauth_access_tokens`. Rota protegida sem token valido responde HTTP 500
`{"error":true,"message":"Unauthenticated."}` (handler da aplicacao, igual ao 5.4)."""
import re
from pathlib import Path

import requests

from regressao.nucleo.ambiente import container_do_alvo
from regressao.nucleo.banco import ErroAmbienteBanco, _docker
from regressao.nucleo.veredito import Caso, Veredito

RAIZ_REPO = Path(__file__).resolve().parents[2]
ARQ_CONFIG = RAIZ_REPO / "ecidade" / "config" / "application.php"
CLIENT_ID = "9999999"
LOG_ERROS = "/var/log/php_errors.log"  # error_log dos dois runtimes (7.4 e 8.5)
TIMEOUT = 15
REDIGIDO = "<redigido>"
LIMITE_REDIGE = 20000
MARCAS_BOOT = ("Fatal error", "Parse error", "Uncaught", "Cannot make non abstract method")
_RE_JWT = re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")
_RE_SEGREDO = re.compile(
    r"(?i)((?:secret|password|passwd|senha|token|bearer|authorization|api[_-]?key)[\w-]{0,40}[\"'\]]?\s{0,20}(?:=>|[=:])\s{0,20}[\"']?)"
    r"(?:(?:bearer|basic)\s+)?[^\s\"',&;]+"
)
_RE_USUARIO_LITERAL = re.compile(
    r"(?i)((?:user(?:name)?|usuario|login|password|senha)[\w\]]{0,40}[\s\"'=:>\[\]]{0,6})dbseller")


class ErroToken(Exception):
    """Falha ao obter o token. A mensagem nunca contem segredo, senha ou token."""


def _segredo_cliente() -> str:
    try:
        texto = ARQ_CONFIG.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        raise ErroToken(f"nao foi possivel ler {ARQ_CONFIG.name}: {type(e).__name__}") from None
    m = re.search(r"""['"]api\.client\.secret['"]\s*=>\s*(['"])(.*?)\1""", texto)
    if not m:
        raise ErroToken("chave api.client.secret nao encontrada em application.php")
    return m.group(2)


def obtem_token(base_url: str, usuario: str = "dbseller", senha: str = "dbseller") -> str:
    url = base_url.rstrip("/") + "/v4/oauth/token"
    try:
        r = requests.post(url, data={
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": _segredo_cliente(),
            "username": usuario,
            "password": senha,
        }, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise ErroToken(f"sem resposta de {url}: {type(e).__name__}") from None
    if r.status_code != 200:
        raise ErroToken(f"POST {url} devolveu HTTP {r.status_code}")
    try:
        tok = r.json()["access_token"]
    except (ValueError, KeyError, TypeError):
        raise ErroToken(f"POST {url} sem access_token na resposta (HTTP 200)") from None
    if not isinstance(tok, str) or not tok:
        raise ErroToken(f"POST {url} devolveu access_token vazio")
    return tok


def redige(texto: str) -> str:
    """Remove JWTs, pares segredo=valor (=, :, =>; JSON e query), o segredo do cliente em
    qualquer lugar e o usuario/senha padrao so quando colados a palavra-chave."""
    # Ordem importa: (1) o segredo do cliente e trocado ANTES do corte, para que o corte
    # nunca deixe um fragmento dele; (2) o texto e cortado em LIMITE_REDIGE caracteres
    # ANTES das regexes, limitando o custo; o corte so descarta o final do texto.
    try:
        segredo = _segredo_cliente()
    except ErroToken:
        segredo = ""
    if segredo:
        texto = texto.replace(segredo, REDIGIDO)
    texto = texto[:LIMITE_REDIGE]
    texto = _RE_JWT.sub(REDIGIDO, texto)
    texto = _RE_SEGREDO.sub(lambda m: m.group(1) + REDIGIDO, texto)
    texto = _RE_USUARIO_LITERAL.sub(lambda m: m.group(1) + REDIGIDO, texto)
    return texto


def _cauda_php_errors(base_url: str = "", linhas: int = 5) -> str:
    """Ultimas linhas do php_errors.log do container que ATENDE `base_url` (nucleo/ambiente.py);
    URL desconhecida ou proxy: nada (nunca mostra o log de outro runtime como se fosse do alvo)."""
    container = container_do_alvo(base_url) if base_url else None
    if not container:
        return ""
    try:
        saida = _docker(["exec", container, "tail", "-n", str(linhas), LOG_ERROS], 15)
    except ErroAmbienteBanco:
        return ""
    brutas = saida.decode("utf-8", errors="replace").strip().splitlines()[-linhas:]
    return "\n".join(redige(l[:300]) for l in brutas)


def _boot_falho(base_url: str, detalhe: str) -> Caso:
    log = _cauda_php_errors(base_url)
    if log:
        detalhe += (f"\nphp_errors.log de {container_do_alvo(base_url)} (ultimas linhas do log global do php; "
                    "podem ser antigas e nao relacionadas):\n" + log)
    return Caso("laravel:boot", "laravel", Veredito.ERRO_AMBIENTE, detalhe)


def laravel_sobe(base_url: str, timeout: float = TIMEOUT) -> Caso | None:
    """None se o Laravel responde sem erro de boot; senao UM Caso ERRO_AMBIENTE
    (fora do ar, timeout, HTTP>=500 ou corpo com erro fatal de PHP)."""
    url = base_url.rstrip("/") + "/v4/oauth/token"
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=False)
    except requests.RequestException as e:
        return Caso("laravel:boot", "laravel", Veredito.ERRO_AMBIENTE,
                    f"Laravel fora do ar em {base_url}: {type(e).__name__}")
    if r.status_code >= 500:
        return _boot_falho(base_url, f"Laravel em {base_url} devolveu HTTP {r.status_code} no boot")
    corpo = r.text or ""
    marca = next((m for m in MARCAS_BOOT if m in corpo), None)
    if marca:
        return _boot_falho(base_url, f"Laravel em {base_url} nao subiu: HTTP {r.status_code} "
                                     f"com erro de PHP no corpo ({marca})")
    return None