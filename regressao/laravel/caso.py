"""Bateria Laravel: casos HTTP, gravar a baseline (referencia Laravel 8) e comparar (alvo novo).

Modelo de estado: SEM snapshot por caso. `gravar` e `comparar` restauram o dump UMA vez e
rodam os casos numa ordem FIXA sobre esse unico estado; as duas execucoes percorrem a mesma
sequencia, entao ids e sequencias evoluem igual. Efeitos de escrita saem de (a) o SQL de
negocio do log do PostgreSQL entre marcadores por caso e (b) o hash das `tabelas` do caso.
"""
import base64
import datetime
import difflib
import hashlib
import json
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import requests
import yaml

from regressao.laravel import integracao
from regressao.laravel import mascara
from regressao.laravel.mascara import mascara_json, normaliza_erro
from regressao.laravel.token import (CLIENT_ID, _RE_JWT, ErroToken, _segredo_cliente,
                                     laravel_sobe, obtem_token, redige)
from regressao.nucleo import git
from regressao.nucleo.ambiente import alvos_do_ambiente
from regressao.nucleo.banco import (ARQ_DUMP, ARQ_SHA256, BancoDiferente,
                                    ErroAmbienteBanco, _psql, com_log_statement,
                                    confere_baseline, hash_tabelas, restaura_dump)
from regressao.nucleo.banco import container as container_banco
from regressao.nucleo.veredito import Caso, Veredito

DIR_CASOS = Path(__file__).resolve().parent / "casos"
DIR_BASELINE = Path(__file__).resolve().parents[1] / "baseline" / "laravel"
RAIZ_REPO = Path(__file__).resolve().parents[2]
AREA = "laravel"
TIMEOUT_HTTP = 60
TIMEOUT_SETUP = 30
CABECALHOS_GRAVADOS = ("content-type", "www-authenticate", "cache-control")
LIMITE_TEXTO = 4000
LIMITE_DIFF_LINHAS = 80
LIMITE_CONSOLE = 500_000  # teto de seguranca da saida do console; as saidas normalizadas ficam muito abaixo
ESPERA_MARCADOR = 8.0  # s para o marcador final aparecer no log do banco
TOKEN_NOVO = "@novo"
TOKEN_EXPIRADO = "@expirado"  # o token valido com `exp` no passado, re-assinado com a chave local
ARQ_CHAVE_PRIVADA = RAIZ_REPO / "ecidade" / "storage" / "oauth-private.key"


class ErroRequisicao(Exception):
    """Falha de transporte/ambiente ao exercitar um caso. A mensagem nunca leva segredo."""


class ErroGravacao(Exception):
    """gravar nao pode produzir uma baseline confiavel."""


@dataclass
class CasoHttp:
    id: str
    metodo: str
    caminho: str
    corpo: dict | None
    autenticado: bool = True
    token: str | None = None  # None = usar o valido; "" = ausente; "@novo" = token recem-emitido; outro = invalido
    campos_volateis: list[str] = field(default_factory=list)
    tabelas: list[str] = field(default_factory=list)
    form: bool = False  # corpo como application/x-www-form-urlencoded (senao JSON)
    sql_antes: list[str] = field(default_factory=list)  # preparacao no banco; `{jti}` = id do token @novo
    espera_escrita: bool = False  # INCONCLUSIVO se nao escrever nada nos dois lados
    # Status documentado do comportamento da referencia (ex.: 500 "Unauthenticated" do Laravel 8 da base 7.4):
    # igual nos dois lados e com o mesmo corpo => IDENTICO em vez de INCONCLUSIVO (5xx).
    espera_status: int | None = None
    # Arquivo gerado (PDF/CSV/XLS): caminho pontilhado, na resposta JSON, do arquivo a baixar; o TEXTO extraido
    # (nao os bytes) vai para `Resposta.texto` e e o que se compara. Mascare tambem o caminho em campos_volateis.
    arquivo: str | None = None
    # Console: `php artisan <console>` no container de console (nao ha HTTP); `console_modo: nomes` compara so
    # os nomes dos comandos (list --raw). Status = codigo de saida; texto = saida normalizada.
    console: list[str] | None = None
    console_modo: str | None = None
    # Listas do JSON que a API devolve SEM ordem garantida (ex.: SQL sem ORDER BY): comparadas como conjunto
    # ordenado (mascara.ordena_listas) antes da mascara de volateis. Vem de `sem_ordem` em _ajustes.yml.
    listas_sem_ordem: list[str] = field(default_factory=list)


@dataclass
class Resposta:
    status: int
    cabecalhos: dict[str, str]
    json: object
    sql_negocio: list[str]
    texto: str = ""
    tipos: dict[str, list[str]] = field(default_factory=dict)
    hashes: dict[str, str] = field(default_factory=dict)


_CAMPOS = {f for f in CasoHttp.__dataclass_fields__}
_RE_ID = re.compile(r"[\w.:/-]+")


def nome_arquivo(id: str) -> str:
    """Arquivo da baseline de um caso. `:` e `/` (ids `rota:GET:/uri`) viram `=` e `~`, que o
    `_RE_ID` nao admite: o mapeamento e injetivo e nao ha subdiretorio nem nome invalido."""
    return id.replace(":", "=").replace("/", "~") + ".json"


def carrega_casos(diretorio: Path) -> list[CasoHttp]:
    """YAML em ordem alfabetica de arquivo e, dentro dele, ordem do arquivo. Arquivos que
    comecam com `_` (ex.: `_instaveis.yml`) nao sao carregados."""
    casos: list[CasoHttp] = []
    vistos: set[str] = set()
    for arq in sorted(p for p in Path(diretorio).glob("*.yml") if not p.name.startswith("_")):
        dados = yaml.safe_load(arq.read_text(encoding="utf-8")) or []
        if not isinstance(dados, list):
            raise ValueError(f"{arq.name}: esperava uma lista de casos")
        for d in dados:
            extra = set(d) - _CAMPOS
            if extra:
                raise ValueError(f"{arq.name}: campos desconhecidos {sorted(extra)}")
            for obrig in ("id", "metodo", "caminho"):
                if obrig not in d:
                    raise ValueError(f"{arq.name}: caso sem '{obrig}'")
            if d["id"] in vistos or not _RE_ID.fullmatch(str(d["id"])):
                raise ValueError(f"{arq.name}: id repetido ou invalido: {d['id']!r}")
            vistos.add(d["id"])
            d = dict(d)
            d["metodo"] = str(d["metodo"]).upper()
            d.setdefault("corpo", None)
            casos.append(CasoHttp(**d))
    return casos


# ---------------------------------------------------------------- execucao

def _limpa(obj):
    """Rede de seguranca: nenhum JWT sobrevive em nada que va para a baseline/relatorio."""
    if isinstance(obj, str):
        return _RE_JWT.sub("<jwt>", obj)
    if isinstance(obj, list):
        return [_limpa(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _limpa(v) for k, v in obj.items()}
    return obj


def _jti(jwt: str) -> str:
    try:
        p = jwt.split(".")[1]
        dados = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
        jti = str(dados["jti"])
    except (IndexError, ValueError, KeyError, TypeError):
        raise ErroRequisicao("token emitido sem jti legivel") from None
    if not re.fullmatch(r"[\w-]+", jti):
        raise ErroRequisicao("jti do token com formato inesperado")
    return jti


def _b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def _jwt_expirado(jwt: str, chave: Path = ARQ_CHAVE_PRIVADA) -> str:
    """Copia de `jwt` com `exp` (e `nbf`/`iat`) no passado, re-assinada em RS256 com a chave
    privada local do Passport (dev; nao e rastreada no git). O jti continua valido no banco:
    so o `exp` do JWT distingue este token do valido."""
    try:
        cab, pl, _ = jwt.split(".")
        dados = json.loads(base64.urlsafe_b64decode(pl + "=" * (-len(pl) % 4)))
        agora = int(time.time())
        dados.update({"exp": agora - 3600, "nbf": agora - 7200, "iat": agora - 7200})
        corpo = f"{cab}.{_b64url(json.dumps(dados, separators=(',', ':')).encode())}"
        r = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(chave)],
                           input=corpo.encode(), capture_output=True, timeout=TIMEOUT_SETUP)
    except (ValueError, TypeError, OSError, subprocess.SubprocessError):
        raise ErroRequisicao("nao foi possivel forjar o token expirado") from None
    if r.returncode != 0 or not r.stdout:
        raise ErroRequisicao("nao foi possivel forjar o token expirado (openssl/chave)")
    return f"{corpo}.{_b64url(r.stdout)}"


def _grant_senha(base_url: str) -> dict:
    """Password grant de setup (fora da janela de captura). Devolve o JSON completo."""
    url = base_url.rstrip("/") + "/v4/oauth/token"
    try:
        r = requests.post(url, data={"grant_type": "password", "client_id": CLIENT_ID,
                                     "client_secret": _segredo_cliente(),
                                     "username": "dbseller", "password": "dbseller"},
                          timeout=TIMEOUT_SETUP)
        dados = r.json()
    except (requests.RequestException, ValueError, ErroToken) as e:
        raise ErroRequisicao(f"setup do token falhou: {type(e).__name__}") from None
    if r.status_code != 200 or not isinstance(dados, dict) or "access_token" not in dados:
        raise ErroRequisicao(f"setup do token: HTTP {r.status_code} sem access_token")
    return dados


class _Contexto:
    """Valores dos marcadores `${...}` dos casos; os caros/sigilosos sao resolvidos sob demanda."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._cache: dict[str, str] = {}

    def valor(self, nome: str) -> str:
        if nome in self._cache:
            return self._cache[nome]
        if nome == "CLIENT_ID":
            v = CLIENT_ID
        elif nome == "CLIENT_SECRET":
            try:
                v = _segredo_cliente()
            except ErroToken as e:
                raise ErroRequisicao(str(e)) from None
        elif nome == "USUARIO" or nome == "SENHA":
            v = "dbseller"
        elif nome == "REFRESH_TOKEN":
            v = str(_grant_senha(self.base_url).get("refresh_token", ""))
        else:
            raise ErroRequisicao(f"marcador desconhecido: ${{{nome}}}")
        self._cache[nome] = v
        return v

    def aplica(self, obj):
        if isinstance(obj, str):
            return re.sub(r"\$\{(\w+)\}", lambda m: self.valor(m.group(1)), obj)
        if isinstance(obj, list):
            return [self.aplica(x) for x in obj]
        if isinstance(obj, dict):
            return {k: self.aplica(v) for k, v in obj.items()}
        return obj


def _tipos(obj, partes: list[str]) -> list[str]:
    if not partes:
        return [type(obj).__name__]
    p, resto = partes[0], partes[1:]
    if p == "*":
        return [t for x in obj for t in _tipos(x, resto)] if isinstance(obj, list) else []
    if isinstance(obj, dict) and p in obj:
        return _tipos(obj[p], resto)
    return []


def tipos_mascarados(obj, campos: list[str]) -> dict[str, list[str]]:
    """Estrutura dos campos mascarados (tipo/presenca), ja que o valor nao e comparado."""
    return {c: sorted(set(_tipos(obj, c.split(".")))) or ["ausente"] for c in campos}


_RE_ESCRITA = re.compile(
    r"^\s*(?:insert|update|delete|truncate|copy\b.*\bfrom\b"
    r"|with\b.*\b(?:insert\s+into|update|delete\s+from)\b)", re.I | re.S)
_RE_ALVO = re.compile(
    r"""(?:\binsert\s+into|\bdelete\s+from|\bupdate|\btruncate(?:\s+table)?|\bcopy)\s+(?:only\s+)?"""
    r"""((?:"[^"]+"|\w+)(?:\s*\.\s*(?:"[^"]+"|\w+))?)""", re.I)
# Tabelas de infraestrutura (login, sessao, log de acesso, oauth): ignoradas SE FOREM O ALVO da
# escrita. `select fn(...)` com efeito de escrita NAO e reconhecido aqui: so o fingerprint de
# pg_stat_user_tables (`_fingerprint`) o pega.
_RE_INFRA = re.compile(
    r"(?:db_acount\w*|db_usuariosonline|db_logsacessa|db_menu\w*|db_sessao\w*|oauth_\w+)", re.I)
_RE_PREFIXO = re.compile(r"^\d{4}-\d{2}-\d{2} [\d:.]+ [^ ]+ \[(\d+)\] LOG:\s+[^:]*:\s*")
_RE_LINHA_LOG = re.compile(r"^\d{4}-\d{2}-\d{2} [\d:.]+ [^ ]+ \[\d+\] ")
# O log pode sair em ingles (DETAIL/parameters) ou portugues (DETALHE/parametros, com acento
# que o decode `replace` pode trocar por U+FFFD): ambos viram "parameters: ...".
_RE_PARAMS = re.compile(
    r"^\d{4}-\d{2}-\d{2} [\d:.]+ [^ ]+ \[\d+\] (?:DETAIL|DETALHE):\s+(?:parameters|par[^\s:]{1,4}metros):(.*)$",
    re.I)
# Clientes que NAO sao a aplicacao, reconhecidos pela primeira instrucao da sessao: pg_dump/
# pg_restore (`SET statement_timeout`, `SELECT pg_catalog.set_config(...)`) e a manutencao do
# harness. O log_line_prefix do servidor e `%m [%p] `: so ha o pid para distinguir sessoes (sem
# usuario nem application_name), por isso a exclusao e por pid. Ruido residual: um cliente
# interativo qualquer (psql de outra pessoa) rodando escrita DENTRO da janela seria capturado.
_RE_CLIENTE_NAO_APP = re.compile(
    r"^(set\s+statement_timeout\b|select\s+pg_catalog\.set_config\(|select\s+pg_terminate_backend\b"
    r"|alter\s+database\b|do\s+\$\$|select\s+'REGRESSAO_)", re.I)
ESPERA_ESTATISTICAS = 2.0  # s apos a ultima sonda ate ler pg_stat_user_tables (ver _fingerprint)
_SQL_FINGERPRINT = ("select schemaname||'.'||relname||'='||(n_tup_ins+n_tup_upd+n_tup_del) "
                    "from pg_stat_user_tables")


def _alvo_escrita(sql: str) -> str | None:
    """Tabela-alvo (sem schema nem aspas, minuscula) de uma escrita; None se nao for escrita
    ou se o alvo nao puder ser lido."""
    if not _RE_ESCRITA.match(sql):
        return None
    m = _RE_ALVO.search(sql)
    if not m:
        return None
    return m.group(1).split(".")[-1].strip().strip('"').lower()


def _e_negocio(sql: str) -> bool:
    """Escrita cujo ALVO nao e tabela de infraestrutura (mencionar `oauth_*` num subselect nao a
    torna infra). Escrita de alvo ilegivel conta como negocio (conservador)."""
    if not _RE_ESCRITA.match(sql):
        return False
    alvo = _alvo_escrita(sql)
    return alvo is None or not _RE_INFRA.fullmatch(alvo)


def _fingerprint() -> dict[str, int]:
    """Contadores n_tup_ins+upd+del de TODA tabela do banco (`schema.tabela` -> total). Leitura
    imediata: no PG16 deste ambiente o contador de uma sessao que terminou ja aparece em 0 s
    (medido: insert via psql visivel na 1a leitura); a espera de ESPERA_ESTATISTICAS (2 s,
    acima do PGSTAT_MIN_INTERVAL de 1 s) cobre sessoes longas que so descarregam as estatisticas
    ao ficar ociosas."""
    saida: dict[str, int] = {}
    for l in _psql(_SQL_FINGERPRINT).splitlines():
        nome, _, n = l.rpartition("=")
        if nome and n.strip().isdigit():
            saida[nome] = int(n)
    return saida


def _tabelas_alteradas(antes: dict[str, int], depois: dict[str, int]) -> set[str]:
    return {t for t in set(antes) | set(depois) if antes.get(t, 0) != depois.get(t, 0)}


def _e_rota(c: CasoHttp) -> bool:
    """Caso gerado do inventario que nao declara escrita: uma SONDA."""
    return c.id.startswith("rota:") and not c.espera_escrita and not c.tabelas


def _e_sonda_de_escrita(c: CasoHttp) -> bool:
    """Sonda que NAO e GET: nao pode escrever nada (nem SQL capturado)."""
    return _e_rota(c) and c.metodo != "GET"
_RE_TS = re.compile(r"'\d{4}-\d{2}-\d{2}[ T][\d:.]+(?:[+-]\d{2}(?::?\d{2})?|Z)?'")
_RE_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
_RE_HEX = re.compile(r"\b[0-9a-f]{40,}\b", re.I)


def normaliza_sql(sql: str) -> str:
    """Timestamps -> '<TS>'; a data de hoje -> '<HOJE>'; uuids/hex longos; espacos colapsados.
    Ids sequenciais ficam: com o mesmo dump e a mesma ordem de casos eles evoluem igual."""
    sql = _RE_TS.sub("'<TS>'", sql)
    hoje = {datetime.date.today().isoformat(),
            datetime.datetime.now(datetime.timezone.utc).date().isoformat()}
    for d in hoje:
        sql = sql.replace(f"'{d}'", "'<HOJE>'")
    sql = _RE_UUID.sub("<UUID>", sql)
    sql = _RE_HEX.sub("<HEX>", sql)
    return re.sub(r"\s+", " ", sql).strip()


def _logs_banco(desde: datetime.datetime) -> bytes:
    """`docker logs` do banco desde `desde` (stderr incluso: o postgres loga la)."""
    try:
        r = subprocess.run(["docker", "logs", "--since", desde.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            container_banco()], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=120)
    except (OSError, subprocess.SubprocessError) as e:
        raise ErroAmbienteBanco(f"docker logs falhou: {type(e).__name__}") from None
    if r.returncode != 0:
        raise ErroAmbienteBanco(f"docker logs saiu com {r.returncode}")
    return r.stdout


def _statements_pid(bruto: bytes) -> list[tuple[int, str]]:
    """(pid do backend, statement) do log, sem prefixo, com continuacoes juntadas (so elas) e
    a linha `DETAIL: parameters:` do protocolo estendido anexada ao statement anterior."""
    out: list[tuple[int, str]] = []
    aberto = False
    for l in bruto.decode("utf-8", errors="replace").split("\n"):
        l = l.rstrip("\r")
        m = _RE_PREFIXO.match(l)
        if m:
            out.append((int(m.group(1)), l[m.end():]))
            aberto = True
            continue
        p = _RE_PARAMS.match(l)
        if p:
            if out:
                out[-1] = (out[-1][0], out[-1][1] + " parameters:" + p.group(1))
            aberto = False
        elif _RE_LINHA_LOG.match(l):
            aberto = False
        elif aberto and l.strip():
            out[-1] = (out[-1][0], out[-1][1] + " " + l.strip())
    return out


def _statements(bruto: bytes) -> list[str]:
    return [s for _, s in _statements_pid(bruto)]


def _sql_entre(desde: datetime.datetime, ini: str, fim: str) -> list[str]:
    """SQL de escrita de negocio entre os marcadores. Captura TODA sessao, menos as que o proprio
    harness e a manutencao abrem: os backends que emitiram os marcadores e os clientes
    reconhecidos por `_RE_CLIENTE_NAO_APP` (pg_dump/pg_restore, manutencao). Sessoes da
    aplicacao ja abertas antes da janela (conexao reaproveitada) continuam capturadas."""
    limite = time.monotonic() + ESPERA_MARCADOR
    while True:
        pares = _statements_pid(_logs_banco(desde))
        stm = [s for _, s in pares]
        i = next((k for k, s in enumerate(stm) if ini in s), None)
        j = next((k for k, s in enumerate(stm) if fim in s), None)
        if i is not None and j is not None and j > i:
            break
        if time.monotonic() > limite:
            raise ErroAmbienteBanco("marcadores do caso nao apareceram no log do banco "
                                    "(log_statement ligado?)")
        time.sleep(0.25)
    excluidos = {pares[i][0], pares[j][0]}
    primeira: dict[int, str] = {}
    for pid, s in pares:
        primeira.setdefault(pid, s)
    excluidos |= {pid for pid, s in primeira.items() if _RE_CLIENTE_NAO_APP.match(s)}
    negocio = [s for pid, s in pares[i + 1:j] if pid not in excluidos and _e_negocio(s)]
    return [normaliza_sql(s) for s in negocio]


def executa(caso: CasoHttp, base_url: str, token: str, banco: bool = True) -> Resposta:
    """Exercita um caso. Setup (placeholders, token novo, sql_antes) acontece ANTES do
    marcador inicial, entao nao entra no SQL capturado. `token` = o token valido compartilhado."""
    if caso.console is not None:
        try:
            container = integracao.container_console(base_url)  # referencia, laboratorio ou variavel
            codigo, saida = integracao.roda_console(caso.console, caso.console_modo, container=container)
        except integracao.ErroConsole as e:  # container ausente/allowlist/alvo sem container: ambiente, nao veredito
            raise ErroRequisicao(f"console {' '.join(caso.console)}: {e}") from None
        hashes = hash_tabelas(caso.tabelas) if banco and caso.tabelas else {}
        return Resposta(status=codigo, cabecalhos={}, json=None, sql_negocio=[], texto=_limpa(saida)[:LIMITE_CONSOLE],
                        hashes=hashes)
    ctx = _Contexto(base_url)
    corpo = ctx.aplica(caso.corpo) if caso.corpo is not None else None
    usado = None
    if caso.autenticado:
        if caso.token is None:
            usado = token
        elif caso.token == TOKEN_NOVO:
            usado = str(_grant_senha(base_url)["access_token"])
        elif caso.token == TOKEN_EXPIRADO:
            usado = _jwt_expirado(token)
        elif caso.token != "":
            usado = caso.token
    if banco:
        for sql in caso.sql_antes:
            if "{jti}" in sql:
                if caso.token != TOKEN_NOVO or usado is None:
                    raise ErroRequisicao("sql_antes usa {jti} sem token '@novo'")
                sql = sql.replace("{jti}", _jti(usado))
            _psql(sql)
    marca = uuid.uuid4().hex[:16]
    ini, fim = f"REGRESSAO_{marca}_ini", f"REGRESSAO_{marca}_fim"
    desde = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)
    if banco:
        _psql(f"select '{ini}'")
    headers = {"Accept": "application/json"}
    if usado:
        headers["Authorization"] = "Bearer " + usado
    kw: dict = {"headers": headers, "timeout": TIMEOUT_HTTP, "allow_redirects": False}
    if corpo is not None:
        kw["data" if caso.form else "json"] = corpo
    url = base_url.rstrip("/") + caso.caminho
    try:
        r = requests.request(caso.metodo, url, **kw)
    except requests.RequestException as e:
        raise ErroRequisicao(f"{caso.metodo} {caso.caminho} sem resposta: {type(e).__name__}") from None
    sql: list[str] = []
    hashes: dict[str, str] = {}
    if banco:
        _psql(f"select '{fim}'")
        sql = _sql_entre(desde, ini, fim)
        if caso.tabelas:
            hashes = hash_tabelas(caso.tabelas)
    try:
        bruto = r.json()
    except ValueError:
        bruto = None
    if bruto is not None and caso.listas_sem_ordem:
        bruto = mascara.ordena_listas(bruto, caso.listas_sem_ordem)
    texto = "" if bruto is not None else _limpa(r.text or "")[:LIMITE_TEXTO]
    if caso.arquivo and r.status_code < 400:
        try:
            texto = _limpa(integracao.segue_arquivo(base_url, integracao.valor_json(bruto, caso.arquivo), headers))
        except requests.RequestException as e:
            raise ErroRequisicao(f"{caso.metodo} {caso.caminho}: arquivo gerado inacessivel: {type(e).__name__}") from None
    cab = {k.lower(): v for k, v in r.headers.items() if k.lower() in CABECALHOS_GRAVADOS}
    return Resposta(
        status=r.status_code, cabecalhos=_limpa(cab),
        json=_limpa(mascara_json(bruto, caso.campos_volateis)) if bruto is not None else None,
        sql_negocio=_limpa(sql), texto=texto,
        tipos=tipos_mascarados(bruto, caso.campos_volateis) if bruto is not None else {},
        hashes=hashes)


# ---------------------------------------------------------------- baseline

def _nucleo(r: Resposta) -> dict:
    return {"status": r.status, "cabecalhos": r.cabecalhos, "json": r.json, "texto": r.texto,
            "tipos": r.tipos, "sql_negocio": r.sql_negocio, "tabelas": r.hashes}


def _canonico(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(registro: dict) -> str:
    return hashlib.sha256(_canonico(registro).encode("utf-8")).hexdigest()


def _grava_registro(arq: Path, registro: dict) -> None:
    completo = dict(registro)
    completo.pop("sha256", None)
    completo["sha256"] = _sha(completo)
    arq.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(completo, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    arq.write_bytes(texto.encode("utf-8"))


def _le_registro(arq: Path) -> dict:
    """Levanta ValueError se ilegivel ou adulterado."""
    try:
        reg = json.loads(arq.read_text(encoding="utf-8"))
        sha = reg.pop("sha256")
    except (OSError, ValueError, KeyError, AttributeError):
        raise ValueError(f"baseline ilegivel: {arq.name}") from None
    if sha != _sha(reg):
        raise ValueError(f"baseline adulterada (sha256 nao confere): {arq.name}")
    return reg


def _sha_dump_atual() -> str | None:
    try:
        partes = ARQ_SHA256.read_text().split()
    except OSError:
        return None
    return partes[0] if partes else None


def _tipo_alvo(base_url: str) -> str:
    a = alvos_do_ambiente()
    u = base_url.rstrip("/")
    for nome in ("ref", "php_novo", "laravel_novo", "proxy"):
        if u == getattr(a, nome).rstrip("/"):
            return nome
    return "outro"


def _commit() -> str:
    return git.commit(RAIZ_REPO, curto=True)


def _nome_tabela(t: str) -> str:
    return t.rsplit(".", 1)[-1].strip('"').lower()


def _suspeitas_da_janela(casos: list[CasoHttp], respostas: dict[str, Resposta],
                         antes: dict[str, int], depois: dict[str, int], i0: int, i1: int) -> list[str]:
    """Tabelas cujos contadores mudaram na janela das sondas SEM explicacao: nao sao infra, nao
    foram declaradas por um caso de escrita dentro da janela e nao tem escrita capturada."""
    declaradas = {_nome_tabela(t) for c in casos[i0:i1 + 1] if not _e_rota(c) for t in c.tabelas}
    capturadas = {_alvo_escrita(s) for c in casos[i0:i1 + 1] if c.id in respostas
                  for s in respostas[c.id].sql_negocio}
    return sorted(t for t in _tabelas_alteradas(antes, depois)
                  if not _RE_INFRA.fullmatch(_nome_tabela(t))
                  and _nome_tabela(t) not in declaradas and _nome_tabela(t) not in capturadas)


def _roda(casos: list[CasoHttp], base_url: str, erros: dict | None = None,
          info: dict | None = None, restaurar: bool = True) -> dict[str, Resposta]:
    """Restaura o dump uma vez e roda os casos em ordem. Com `erros` (dict), falha por caso
    vira entrada ali; sem ele, a primeira falha propaga. `info["suspeitas"]` recebe as tabelas
    alteradas sem explicacao durante a janela das sondas (fingerprint de pg_stat_user_tables
    antes da primeira e depois da ultima, com ESPERA_ESTATISTICAS de folga)."""
    if restaurar:
        restaura_dump(ARQ_DUMP)
    try:
        token = obtem_token(base_url)
    except ErroToken as e:
        raise ErroRequisicao(str(e)) from None
    sondas = [k for k, c in enumerate(casos) if _e_rota(c)]
    i0, i1 = (sondas[0], sondas[-1]) if sondas else (-1, -1)
    antes: dict[str, int] = {}
    depois: dict[str, int] = {}
    respostas: dict[str, Resposta] = {}
    with com_log_statement():
        for k, c in enumerate(casos):
            if k == i0:
                antes = _fingerprint()
            try:
                respostas[c.id] = executa(c, base_url, token)
            except (ErroRequisicao, ErroAmbienteBanco) as e:
                if erros is None:
                    raise
                erros[c.id] = redige(str(e))
            if k == i1:
                time.sleep(ESPERA_ESTATISTICAS)
                depois = _fingerprint()
    if info is not None:
        info["suspeitas"] = _suspeitas_da_janela(casos, respostas, antes, depois, i0, i1) if i0 >= 0 else []
    return respostas


def gravar_novos(casos: list[CasoHttp], base_url: str, diretorio: Path) -> list[str]:
    """Acrescenta a uma baseline existente SO os casos que ainda nao tem registro (as outras centenas ficam
    intactas): restaura o dump, roda os novos e atualiza `_meta` (ids/n_casos). Recusa se a baseline foi
    gravada com outro dump, se algum caso antigo perdeu o registro ou se nao ha caso novo. Devolve os ids."""
    diretorio = Path(diretorio)
    if _tipo_alvo(base_url) != "ref":
        raise ErroGravacao(f"gravar_novos so grava contra a referencia Laravel 8 ({alvos_do_ambiente().ref}); "
                           f"recebeu {base_url}: a baseline nunca nasce do sistema migrado")
    boot = laravel_sobe(base_url)
    if boot is not None:
        raise ErroGravacao(f"alvo nao sobe, nada foi restaurado: {boot.detalhe}")
    confere_baseline(ARQ_DUMP)
    sha = _sha_dump_atual()
    try:
        meta = json.loads((diretorio / "_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroGravacao("baseline/_meta.json ilegivel: use `gravar` completo") from None
    if sha is None or meta.get("dump_sha256") != sha:
        raise ErroGravacao("baseline gravada com outro dump: grave de novo (completo)")
    ids_meta = set(meta.get("ids") or [])
    ids_casos = {c.id for c in casos}
    # novos = ids AUSENTES do _meta; perdidos = no _meta (e com caso) mas sem arquivo: perda de baseline que
    # o `--apenas-novos` nao pode "curar" calado (a referencia mudou); arquivo sem id no _meta e inconsistencia.
    perdidos = sorted(i for i in ids_meta & ids_casos if not (diretorio / nome_arquivo(i)).is_file())
    if perdidos:
        raise ErroGravacao("registros perdidos (no _meta, sem arquivo): " + ", ".join(perdidos[:10])
                           + ". Nao serao regravados em silencio: remova-os com "
                           "`caso remove <id> --confirmo-sobrescrever` (se for intencional) ou restaure o arquivo do git")
    novos = [c for c in casos if c.id not in ids_meta]
    com_arquivo = sorted(c.id for c in novos if (diretorio / nome_arquivo(c.id)).is_file())
    if com_arquivo:
        raise ErroGravacao("arquivo de baseline sem id no _meta (orfao/inconsistente): " + ", ".join(com_arquivo[:10]))
    if not novos:
        raise ErroGravacao("nenhum caso novo: todos ja tem registro na baseline")
    ids_novos = {c.id for c in novos}
    if ids_meta - ids_casos:
        raise ErroGravacao("_meta lista casos que nao existem mais: use `poda --confirmo-sobrescrever`")
    info: dict = {}
    respostas = _roda(novos, base_url, info=info)
    for c in novos:
        if _e_sonda_de_escrita(c) and respostas[c.id].sql_negocio:
            raise ErroGravacao(f"a sonda {c.id} ESCREVEU no banco: nao vira baseline")
        if c.espera_status is not None and respostas[c.id].status != c.espera_status:
            raise ErroGravacao(f"{c.id} declara espera_status={c.espera_status}, mas a referencia "
                               f"respondeu {respostas[c.id].status}")
    for c in novos:
        _grava_registro(diretorio / nome_arquivo(c.id), {"id": c.id, **_nucleo(respostas[c.id])})
    meta.update({"ids": [c.id for c in casos], "n_casos": len(casos), "novos_gravados_no_commit": _commit(),
                 "novos_gravados": sorted(ids_novos)})
    _grava_meta(diretorio, meta)
    return sorted(ids_novos)


def remove_registros(ids: list[str], diretorio: Path) -> list[str]:
    """Ferramenta OFICIAL para retirar registros da baseline (arquivo + id no `_meta`) sem tocar nos demais;
    em seguida `gravar --apenas-novos` os regrava. Recusa id que nao esta no `_meta`."""
    diretorio = Path(diretorio)
    try:
        meta = json.loads((diretorio / "_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroGravacao("baseline/_meta.json ilegivel") from None
    atuais = list(meta.get("ids") or [])
    ausentes = [i for i in ids if i not in atuais]
    if ausentes:
        raise ErroGravacao("id que nao esta na baseline: " + ", ".join(ausentes))
    for i in ids:
        (diretorio / nome_arquivo(i)).unlink(missing_ok=True)
    meta["ids"] = [i for i in atuais if i not in ids]
    meta["n_casos"] = len(meta["ids"])
    meta["removidos_no_commit"] = _commit()
    _grava_meta(diretorio, meta)
    return list(ids)


def gravar(casos: list[CasoHttp], base_url: str, diretorio: Path, completo: bool = False) -> None:
    """Restaura o dump, roda os casos contra `base_url` e grava `<id>.json` + `_meta.json`.
    Recusa (ErroGravacao, nada e gravado) sonda que escreve, escrita invisivel ao log na janela
    das sondas e `espera_status` que a referencia nao confirma. `completo=True` (conjunto inteiro
    de casos) remove arquivos antigos da baseline sem caso."""
    diretorio = Path(diretorio)
    boot = laravel_sobe(base_url)
    if boot is not None:
        raise ErroGravacao(f"alvo nao sobe, nada foi restaurado: {boot.detalhe}")
    confere_baseline(ARQ_DUMP)
    sha = _sha_dump_atual()
    if sha is None:
        raise ErroGravacao(f"hash do dump ausente: {ARQ_SHA256}")
    info: dict = {}
    respostas = _roda(casos, base_url, info=info)
    for c in casos:
        if _e_sonda_de_escrita(c) and respostas[c.id].sql_negocio:
            raise ErroGravacao(
                f"a sonda {c.id} ESCREVEU no banco com corpo vazio ({len(respostas[c.id].sql_negocio)} "
                "statement(s) de negocio): nao vira baseline; mova-a para `perigosas` em _ajustes.yml")
        if c.espera_status is not None and respostas[c.id].status != c.espera_status:
            raise ErroGravacao(f"{c.id} declara espera_status={c.espera_status}, mas a referencia "
                               f"respondeu {respostas[c.id].status}")
    if info.get("suspeitas"):
        raise ErroGravacao("escrita invisivel ao log durante as sondas (contadores de "
                           "pg_stat_user_tables mudaram sem SQL de negocio capturado): "
                           + ", ".join(info["suspeitas"]))
    for c in casos:
        _grava_registro(diretorio / nome_arquivo(c.id), {"id": c.id, **_nucleo(respostas[c.id])})
    if completo:
        esperados = {nome_arquivo(c.id) for c in casos}
        for p in diretorio.glob("*.json"):
            if not p.name.startswith("_") and p.name not in esperados:
                p.unlink()
    meta = {"dump_sha256": sha, "commit": _commit(),
            "data": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "n_casos": len(casos), "alvo": _tipo_alvo(base_url), "ids": [c.id for c in casos]}
    _grava_meta(diretorio, meta)


def _grava_meta(diretorio: Path, meta: dict) -> None:
    (Path(diretorio) / "_meta.json").write_bytes(
        (json.dumps(meta, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _arquivos_de_baseline(diretorio: Path) -> list[str]:
    return sorted(p.name for p in Path(diretorio).glob("*.json") if not p.name.startswith("_"))


def poda(casos: list[CasoHttp], diretorio: Path) -> list[str]:
    """Remove da baseline os arquivos sem caso carregado e reescreve `_meta` (ids, n_casos e o
    commit da poda). Recusa (ErroGravacao) se algum caso carregado nao tem baseline: podar nao
    grava nada. Devolve os nomes removidos."""
    diretorio = Path(diretorio)
    esperados = {nome_arquivo(c.id) for c in casos}
    sem = [c.id for c in casos if not (diretorio / nome_arquivo(c.id)).is_file()]
    if sem:
        raise ErroGravacao("casos sem baseline (grave de novo): " + ", ".join(sem[:10]))
    removidos = [n for n in _arquivos_de_baseline(diretorio) if n not in esperados]
    for n in removidos:
        (diretorio / n).unlink()
    try:
        meta = json.loads((diretorio / "_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroGravacao("baseline/_meta.json ilegivel: nada a podar") from None
    meta.update({"ids": [c.id for c in casos], "n_casos": len(casos), "podado_no_commit": _commit()})
    _grava_meta(diretorio, meta)
    return removidos


def _erro(id: str, detalhe: str) -> Caso:
    return Caso(id, AREA, Veredito.ERRO_AMBIENTE, redige(detalhe))


def _diff(base: dict, novo: dict) -> str:
    def pp(x):
        return json.dumps(x, sort_keys=True, ensure_ascii=False, indent=2).splitlines()
    linhas = list(difflib.unified_diff(pp(base), pp(novo), "baseline", "atual", lineterm="", n=2))
    if len(linhas) > LIMITE_DIFF_LINHAS:
        linhas = linhas[:LIMITE_DIFF_LINHAS] + [f"... (diff truncado, {len(linhas)} linhas)"]
    return redige(_RE_JWT.sub("<jwt>", "\n".join(linhas)))


def _normaliza_para_comparar(d: dict) -> dict:
    """Mascara de erro SO no JSON de respostas de erro e no texto de respostas 5xx; nunca em sql_negocio,
    cabecalhos, tipos, tabelas nem em respostas de sucesso."""
    status = d.get("status") or 0
    if not mascara.e_resposta_de_erro(status, d.get("json")):
        return d
    novo = dict(d)
    novo["json"] = normaliza_erro(d.get("json"))
    if status >= 500 and isinstance(d.get("texto"), str):
        novo["texto"] = normaliza_erro(d["texto"])
    return novo


def _veredito(caso: CasoHttp, reg: dict, r: Resposta) -> Caso:
    # mascara de erro so na comparacao: o registro bruto (com file/line/trace) segue guardado em disco
    base, novo = _normaliza_para_comparar({k: v for k, v in reg.items() if k != "id"}), \
        _normaliza_para_comparar(_nucleo(r))
    if base != novo:
        dif = [k for k in novo if base.get(k) != novo[k]]
        return Caso(caso.id, AREA, Veredito.DIVERGE, "difere em: " + ", ".join(dif),
                    _diff(base, novo))
    if r.status >= 500 and caso.espera_status != r.status:
        return Caso(caso.id, AREA, Veredito.INCONCLUSIVO,
                    f"HTTP {r.status} nos dois lados: o caso nao foi exercitado")
    if r.json is None and not r.texto:
        return Caso(caso.id, AREA, Veredito.INCONCLUSIVO, "resposta sem conteudo nos dois lados")
    if "<<ilegivel" in (r.texto or ""):
        return Caso(caso.id, AREA, Veredito.INCONCLUSIVO,
                    "arquivo gerado ilegivel nos dois lados: o conteudo nao foi comparado")
    if caso.espera_escrita and not r.sql_negocio:
        return Caso(caso.id, AREA, Veredito.INCONCLUSIVO,
                    "esperava escrita e nada foi gravado nos dois lados")
    return Caso(caso.id, AREA, Veredito.IDENTICO)


def comparar(casos: list[CasoHttp], base_url: str, diretorio: Path, restaurar: bool = True) -> list[Caso]:
    """Ordem: boot do alvo -> baseline/meta -> restauracao -> casos (fixos, mesma ordem do gravar).
    Nada e restaurado se uma das verificacoes iniciais falhar. `restaurar=False` (so
    desenvolvimento; resultado NAO comparavel) pula a restauracao."""
    diretorio = Path(diretorio)
    boot = laravel_sobe(base_url)
    if boot is not None:
        return [boot]
    meta_arq = diretorio / "_meta.json"
    if not meta_arq.is_file():
        return [_erro(c.id, f"baseline ausente: {meta_arq.name} em {diretorio}") for c in casos]
    try:
        meta = json.loads(meta_arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [_erro("laravel:baseline", "baseline/_meta.json ilegivel")]
    atual = _sha_dump_atual()
    if atual is None:
        return [_erro("laravel:baseline", f"hash do dump ausente: {ARQ_SHA256}")]
    if meta.get("dump_sha256") != atual:
        return [_erro("laravel:baseline",
                      f"baseline gravada com outro dump (sha256 {str(meta.get('dump_sha256'))[:12]} "
                      f"!= atual {atual[:12]}): grave a baseline de novo; nada foi restaurado")]
    ids_meta, ids_casos = set(meta.get("ids") or []), {c.id for c in casos}
    sobra_caso, sobra_meta = sorted(ids_casos - ids_meta), sorted(ids_meta - ids_casos)
    orfaos = sorted(set(_arquivos_de_baseline(diretorio)) - {nome_arquivo(c.id) for c in casos})
    if sobra_caso or sobra_meta or orfaos:
        return [_erro("laravel:baseline",
                      "baseline inconsistente com os casos carregados; nada foi restaurado. "
                      f"casos sem registro no _meta: {sobra_caso[:10]}; ids do _meta sem caso: "
                      f"{sobra_meta[:10]}; arquivos sem caso: {orfaos[:10]} "
                      "(use `python -m regressao.laravel.caso poda --confirmo-sobrescrever` ou grave de novo)")]
    registros: dict[str, dict] = {}
    faltando: list[Caso] = []
    for c in casos:
        arq = diretorio / nome_arquivo(c.id)
        if not arq.is_file():
            faltando.append(_erro(c.id, f"baseline ausente: {arq.name}"))
            continue
        try:
            registros[c.id] = _le_registro(arq)
        except ValueError as e:
            faltando.append(_erro(c.id, str(e)))
    if faltando:
        return faltando
    try:
        confere_baseline(ARQ_DUMP)
    except BancoDiferente as e:
        return [_erro("laravel:baseline", f"dump local diferente do registrado: {e}")]
    erros: dict[str, str] = {}
    info: dict = {}
    try:
        respostas = _roda(casos, base_url, erros, info, restaurar)
    except (ErroRequisicao, ErroAmbienteBanco) as e:
        return [_erro("laravel:banco", f"preparo do banco/token falhou: {e}")]
    res: list[Caso] = []
    for c in casos:
        if c.id in erros:
            res.append(_erro(c.id, erros[c.id]))
        else:
            res.append(_veredito(c, registros[c.id], respostas[c.id]))
    if info.get("suspeitas"):
        res.append(Caso("fingerprint:probes", AREA, Veredito.DIVERGE,
                        "tabelas alteradas durante as sondas sem SQL de negocio capturado: "
                        + ", ".join(info["suspeitas"])))
    return res


def _main(argv: list[str]) -> int:
    """python -m regressao.laravel.caso comparar [url] | poda (remove da baseline o que nao tem caso e
    reescreve o _meta) | remove <id>...; `poda` e `remove` exigem --confirmo-sobrescrever. NAO ha `gravar`
    aqui: gravar passa por `python -m regressao.laravel.bateria gravar`, que tem a protecao da baseline (RecusaBaseline / --confirmo-sobrescrever)."""
    import sys
    confirmo = "--confirmo-sobrescrever" in argv
    argv = [a for a in argv if a != "--confirmo-sobrescrever"]
    modo = argv[0] if argv else ""
    if modo in ("remove", "poda") and not confirmo:
        print(f"erro: `{modo}` apaga registros da baseline pre-migracao (a referencia Laravel 8); confira o que sai e "
              f"repita com --confirmo-sobrescrever", file=sys.stderr)
        return 2
    if modo == "gravar":
        print("erro: `gravar` saiu deste atalho (sem protecao da baseline). Use: "
              "python -m regressao.laravel.bateria gravar --saida DIR [--confirmo-sobrescrever]", file=sys.stderr)
        return 2
    if modo == "remove":
        try:
            ids = remove_registros(argv[1:], DIR_BASELINE) if len(argv) > 1 else None
        except ErroGravacao as e:
            print(f"remocao recusada: {e}", file=sys.stderr)
            return 1
        if ids is None:
            print("uso: python -m regressao.laravel.caso remove <id> [<id>...] --confirmo-sobrescrever", file=sys.stderr)
            return 2
        print(f"removidos da baseline: {ids}; regrave com `bateria gravar --apenas-novos --confirmo-sobrescrever`")
        return 0
    if modo not in ("comparar", "poda"):
        print("uso: python -m regressao.laravel.caso comparar [url] | poda --confirmo-sobrescrever | "
              "remove <id>... --confirmo-sobrescrever", file=sys.stderr)
        return 2
    casos = carrega_casos(DIR_CASOS)
    if modo == "poda":
        try:
            removidos = poda(casos, DIR_BASELINE)
        except ErroGravacao as e:
            print(f"poda recusada: {e}", file=sys.stderr)
            return 1
        print(f"podados {len(removidos)} arquivo(s): {removidos}; _meta com {len(casos)} casos")
        return 0
    alvos = alvos_do_ambiente()
    url = argv[1] if len(argv) > 1 else alvos.laravel_novo
    t0 = time.monotonic()
    res = comparar(casos, url, DIR_BASELINE)
    for c in res:
        print(f"{c.veredito.value:14} {c.id}  {c.detalhe.splitlines()[0] if c.detalhe else ''}")
        if c.diff:
            print(c.diff)
    print(f"({time.monotonic() - t0:.0f} s)")
    from regressao.nucleo.veredito import codigo_saida
    return codigo_saida(res)


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
