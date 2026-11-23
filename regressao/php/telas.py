import base64
import hashlib
import os
import re
import shlex
import subprocess
import time
from pathlib import Path

import requests

from regressao.nucleo.ambiente import alvos_do_ambiente, containers_do_ambiente
from regressao.nucleo.banco import ErroAmbienteBanco, _docker
from regressao.nucleo.normaliza import normaliza
from regressao.nucleo.veredito import Caso, Veredito

RAIZ = Path(__file__).resolve().parents[2]
SCRATCH = RAIZ / "scratchpad"
DIR_TELAS = RAIZ / "ecidade"
# Telas que cmp.py nunca requisita (contatam servico externo); espelha PULAR de cmp.py.
PULAR = {"iss4_siss002.php"}
# Telas que DESTROEM a sessao autenticada (session_destroy): dispara-las mata tudo o que vem depois. Achadas na
# rodada antes; espelha PULAR_SESSAO do cmp.py.
PULAR_SESSAO = {"edu4_informacoesdump.php", "cad4_geracarneiptutxt_cli.php"}
TIMEOUT_SID = 30
TIMEOUT_CMP = 6 * 3600

# cmp.py marca o lado da referencia (PHP 7.4) com `ref=` e o alvo (PHP 8.5) com `85=`.
_DIVERGE = re.compile(r"^\s*DIVERGE\s+(\S+)\s+(ref=\S+)\s+(85=\S+)")
_TIMEOUT = re.compile(r"^\s*TIMEOUT\s+(\S+)\s+(ref=\S+)\s+(85=\S+)")
_PULADA = re.compile(r"^\s*PULADA\s+(\S+)(?:\s+\((.*)\))?")
_RESUMO = re.compile(r"^=== (\d+)/(\d+) identicas, (\d+) divergentes, (\d+) timeout ===")


def parse_cmp(saida: str, area: str, telas: list[str] | None = None,
              corpos: dict[str, bytes] | None = None) -> list[Caso]:
    """Interpreta o que cmp.py REALMENTE imprime: so imprime as telas DIVERGE, TIMEOUT e
    PULADA, mais o resumo '=== N/M identicas, X divergentes, Y timeout ===' (nao ha
    linha por tela identica). Por isso:
    - `telas` (lista que cmp.py percorreu, ver lista_telas) permite gerar um Caso IDENTICO
      por tela; sem ela, as identicas viram um unico Caso 'identicas' com a contagem.
    - `corpos` opcional: tela identica com corpo vazio vira INCONCLUSIVO (cmp.py nao
      informa tamanho das identicas; so o chamador que tem o corpo sabe).
    Sem a linha de resumo a saida e considerada truncada: ERRO_AMBIENTE."""
    casos: list[Caso] = []
    vistas: set[str] = set()
    resumo = None
    for linha in saida.splitlines():
        if m := _DIVERGE.match(linha):
            tela, a, b = m.groups()
            vistas.add(tela)
            casos.append(Caso(tela, area, Veredito.DIVERGE, f"{a}  {b}"))
        elif m := _TIMEOUT.match(linha):
            tela, a, b = m.groups()
            vistas.add(tela)
            casos.append(Caso(tela, area, Veredito.ERRO_AMBIENTE, f"timeout: {a}  {b}"))
        elif m := _PULADA.match(linha):
            tela = m.group(1)
            vistas.add(tela)
            casos.append(Caso(tela, area, Veredito.INCONCLUSIVO,
                              f"pulada ({m.group(2) or 'contata servico externo'})"))
        elif m := _RESUMO.match(linha):
            resumo = tuple(int(x) for x in m.groups())
    if resumo is None:
        return [Caso("cmp", area, Veredito.ERRO_AMBIENTE, "cmp.py sem linha de resumo (saida truncada?)")]
    identicas, total, ndiv, ntout = resumo
    if telas is not None:
        for tela in telas:
            if tela in vistas:
                continue
            if corpos is not None and corpos.get(tela) == b"":
                casos.append(Caso(tela, area, Veredito.INCONCLUSIVO, "resposta de 0 bytes nos dois lados"))
            else:
                casos.append(Caso(tela, area, Veredito.IDENTICO))
    else:
        casos.append(Caso("identicas", area, Veredito.IDENTICO, f"{identicas}/{total} telas identicas"))
    return sorted(casos, key=lambda c: c.id)


def lista_telas(prefixo: str, diretorio: Path = DIR_TELAS) -> list[str]:
    """Mesma selecao de cmp.py: re.match(prefixo, IGNORECASE) e .php, menos PULAR."""
    return sorted(f for f in os.listdir(diretorio)
                  if re.match(prefixo, f, re.IGNORECASE) and f.endswith(".php")
                  and f not in PULAR and f not in PULAR_SESSAO)


def _container_ref() -> str:
    """Container da referencia (PHP 7.4): dono do volume de sessoes e do /tmp/_sess.bak (os dois sao
    compartilhados com o alvo PHP 8.5). Lido de regressao/nucleo/ambiente.py a cada chamada."""
    return containers_do_ambiente().ref


def obtem_sid() -> str:
    """Sessao autenticada mais recente (a que contem DB_modulo) no container da referencia."""
    saida = _docker(
        ["exec", _container_ref(), "sh", "-c",
         "ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_*) | head -1"],
        TIMEOUT_SID,
    ).decode("utf-8", errors="replace").strip()
    nome = saida.rsplit("/", 1)[-1]
    if not nome.startswith("sess_"):
        raise ErroAmbienteBanco(f"nenhuma sessao autenticada encontrada: {saida!r}")
    return nome[len("sess_"):]


_ENV_PROIBIDO = ("ONLY", "PORTA_B", "NORM_MENU")
TIMEOUT_CORPO = 90


def _roda_cmp(sid: str, prefixo: str) -> str:
    """Unico ponto que executa cmp.py (mockavel nos testes). cmp.py fala com o docker por
    conta propria; aqui so se captura a saida. ONLY/NORM_MENU do ambiente de quem chama mudariam a
    selecao/normalizacao do cmp.py, entao sao removidos (PORTA_B era o lado B da pilha antiga; tambem
    sai). As REGRESSAO_* passam: cmp.py le os mesmos alvos/containers de nucleo/ambiente.py."""
    env = {k: v for k, v in os.environ.items() if k not in _ENV_PROIBIDO}
    r = subprocess.run(["python3", str(SCRATCH / "cmp.py"), sid, prefixo],
                       capture_output=True, timeout=TIMEOUT_CMP, env=env)
    return r.stdout.decode("utf-8", errors="replace")


class SessaoPerdida(ErroAmbienteBanco):
    """A sessao autenticada nao existe mais no volume de sessoes (expirou, foi destruida por uma tela ou o
    container reiniciou). A bateria tenta RENOVAR a sessao antes de desistir."""


def restaura_sessao(sid: str) -> None:
    """Restaura a sessao a partir de /tmp/_sess.bak (backup que o proprio cmp.py deixa no container da
    referencia; o volume de sessoes e o /tmp sao compartilhados com o PHP 8.5), pois cada requisicao
    consome/reescreve a sessao. Sessao inexistente -> SessaoPerdida (nunca forja uma); backup ausente ou
    vazio (o /tmp e limpo) e recriado a partir da propria sessao viva."""
    sess = f"/var/lib/php/sessions/sess_{sid}"
    # `exit 3`: so restaura sobre uma sessao que existe; senao um SID qualquer ganharia, a partir de um
    # backup velho, uma sessao autenticada forjada.
    try:
        _docker(["exec", "-u", "root", _container_ref(), "sh", "-c",
                 f"[ -f {sess} ] || exit 3; [ -s /tmp/_sess.bak ] || cp {sess} /tmp/_sess.bak; "
                 f"cp /tmp/_sess.bak {sess} && chown www-data:www-data {sess} && chmod 600 {sess}"],
                TIMEOUT_CORPO)
    except ErroAmbienteBanco as e:
        if "codigo de saida 3" in str(e):
            raise SessaoPerdida(f"a sessao {sid[:6]}... nao existe mais no volume de sessoes") from None
        raise


# ---------------------------------------------------------------- login e renovacao da sessao

ARQ_BACKUP_SESSAO = "/tmp/_sess.bak"
MAX_TENTATIVAS_LOGIN = 3


def _b64(texto: str) -> str:
    return base64.b64encode(texto.encode("latin-1")).decode()


def login_http(base: str | None = None, usuario: str = "dbseller", senha: str = "dbseller", http=None) -> str:
    """Faz por HTTP o que o navegador faz (login.php -> abrir.php -> inicio.php -> `Cancelar` da tela de
    atualizacao de cadastro -> instituicao 1 -> area Tributario -> modulo Cemiterio) e devolve o SID da
    sessao com DB_modulo. A senha vai como md5 (como o JavaScript do login), nunca em claro."""
    base = (base or alvos_do_ambiente().ref).rstrip("/")
    s = http if http is not None else requests.Session()

    def get(caminho, **k):
        return s.get(base + caminho, timeout=60, **k)

    get("/login.php")
    auth = _b64(f"DB_login={usuario}&DB_senha={hashlib.md5(senha.encode()).hexdigest()}")
    get("/abrir.php", params={"sAuth": auth, "conteudoCaptcha": ""})
    get("/inicio.php", params={"uso": usuario, "janelaWidth": 1280, "janelaHeight": ""})
    get("/topo.php", params={"uso": usuario})  # frames do navegador: topo.php grava DB_uol_hora na sessao;
    get("/status.php")                          # sem isso area.php falha ("Erro(26) atualizando db_usuariosonline")
    get("/instit.php")
    s.post(base + "/con4_atualizacadastro001.php", data={"cancelar": "Cancelar"}, timeout=60)
    get("/instit.php")
    get("/corpo.php?" + _b64("instit=1"))
    get("/area.php?instit=1")
    modulos = get("/corpo.php?" + _b64("instit=1&area_de_acesso=1")).content
    ancoras = re.findall(rb"<a\b[^>]*>", modulos)
    achado = next((re.search(rb'href="(modulos\.php\?[^"]+)"', a) for a in ancoras
                   if b"Cemit" in a and b"modulos.php?" in a), None) \
        or next((m for m in (re.search(rb'href="(modulos\.php\?[^"]+)"', a) for a in ancoras) if m), None)
    if not achado:
        raise SessaoPerdida("login por HTTP nao chegou a lista de modulos")
    get("/" + achado.group(1).decode("latin-1"))
    sid = s.cookies.get("ECIDADEWINDOWMAIN")
    if not sid:
        raise SessaoPerdida("login por HTTP nao devolveu o cookie de sessao")
    return sid


def _atualiza_backup(sid: str) -> None:
    sess = f"/var/lib/php/sessions/sess_{sid}"
    _docker(["exec", "-u", "root", _container_ref(), "sh", "-c",
             f"cp {sess} {ARQ_BACKUP_SESSAO} && chmod 600 {ARQ_BACKUP_SESSAO}"], TIMEOUT_CORPO)


def renova_sessao(sid_antigo: str | None = None, max_tentativas: int = MAX_TENTATIVAS_LOGIN, login=None,
                  valida=None, espera=time.sleep) -> str | None:
    """Login novo + validacao + backup da sessao nova em /tmp/_sess.bak; None se nao conseguir em
    `max_tentativas` (a bateria entao registra ERRO_AMBIENTE)."""
    login = login or login_http
    valida = valida or sessao_autenticada
    for i in range(max_tentativas):
        try:
            novo = login()
            if valida(novo):
                _atualiza_backup(novo)
                return novo
        except (requests.RequestException, ErroAmbienteBanco, OSError, subprocess.SubprocessError):
            pass
        if i + 1 < max_tentativas:
            espera(2 * (i + 1))
    return None


class Sessao:
    """SID corrente da rodada + historico de renovacoes (limitado, para nao entrar em laco)."""

    def __init__(self, sid: str, max_renovacoes: int = 5, renova=None):
        self.sid = sid
        self.max_renovacoes = max_renovacoes
        self.renovacoes: list[dict] = []
        self._renova = renova or renova_sessao

    def renova(self, motivo: str) -> bool:
        if len(self.renovacoes) >= self.max_renovacoes:
            return False
        novo = self._renova(self.sid)
        self.renovacoes.append({"motivo": motivo[:120], "ok": bool(novo)})
        if novo:
            self.sid = novo
        return bool(novo)


def busca_corpo(sid: str, tela: str) -> bytes:
    """Corpo cru da tela no lado da referencia (o lado ja sabido identico ao 8.5). Espelha o fetch do
    cmp.py: restaura a sessao antes da requisicao; depois curl com o cookie
    ECIDADEWINDOWMAIN, -m 60 e teto de 5 MB. A requisicao parte de dentro do container (porta
    80 do apache), via banco._docker."""
    restaura_sessao(sid)
    return _requisita(sid, tela)


def _requisita(sid: str, tela: str, container: str | None = None) -> bytes:
    return _docker(["exec", container or _container_ref(), "sh", "-c",
                    f"curl -s -m 60 -b 'ECIDADEWINDOWMAIN={sid}' "
                    f"{shlex.quote(f'http://localhost/{tela}')} | head -c 5000000"],
                   TIMEOUT_CORPO)


def _requisita_status(sid: str, tela: str, container: str | None = None) -> tuple[int, bytes]:
    """Como _requisita, mas devolve (codigo HTTP, corpo cru). O codigo vem num trailer
    `\n@@<codigo>` (como no cmp.py), removido do corpo sem perder bytes. Teto de 5 MB no
    pipe: se o corpo estourar, o trailer se perde e o codigo e 0 (resposta truncada)."""
    saida = _docker(["exec", container or _container_ref(), "sh", "-c",
                     f"curl -s -m 60 -b 'ECIDADEWINDOWMAIN={sid}' -w '\n@@%{{http_code}}' "
                     f"{shlex.quote(f'http://localhost/{tela}')} | head -c 5000000"],
                    TIMEOUT_CORPO)
    i = saida.rfind(b"\n@@")
    if i < 0 or not saida[i + 3:].strip().isdigit():
        return 0, saida
    return int(saida[i + 3:]), saida[:i]


# Pagina que o e-cidade devolve a uma sessao invalida/expirada (observada com um SID
# inexistente, ISO-8859-1, 66 bytes): "Sessão inválida (12). Feche seu navegador e faça login
# novamente." Identica nos dois runtimes, logo cmp.py a daria como IDENTICA.
TELA_SONDA = "cem1_cemiterio001.php"
# Letras acentuadas nas duas codificacoes (Latin-1 e UTF-8) e nas duas caixas; IGNORECASE em
# bytes so dobra ASCII, por isso a caixa dos acentos e listada a mao.
_A_TIL = rb"(?:\xe3|\xc3\xa3|\xc3\x83|\xc3|a)"      # ã / Ã
_A_AGUDO = rb"(?:\xe1|\xc1|\xc3\xa1|\xc3\x81|a)"    # á / Á
_INVALIDA = re.compile(
    rb"sess" + _A_TIL + rb"o inv" + _A_AGUDO + rb"lida"   # libs/db_conecta.php:43 e db_sessoes.php:41 (sessao invalida (12)/(14))
    rb"|sess" + _A_TIL + rb"o terminada"                  # libs/db_conecta.php:76 e :309 (conexao invalida / sistema desativado); db_conecta_cli.php:48, db_conecta_plugin.php:49
    rb"|feche seu navegador"                              # frase comum a todas as variantes acima; cobre texto reescrito no db_erros.php?fechar=true
    # libs/db_usuariosonline.php:49/58 e topo.php:43: a sessao nao abriu conexao com o banco (a pagina tem 50 B, sem
    # '<'); visto na rodada pequena de 2026-11-18, logo depois de um restore, com todas as telas da referencia assim
    rb"|Erro:?\(2[67]\) (?:inserindo arquivo em|atualizando) db_usuariosonline",
    re.IGNORECASE,
)


def corpo_de_sessao_invalida(corpo: bytes) -> bool:
    """Pagina curta (< 1000 B apos normalizar) com alguma mensagem de sessao morta. Todas sao
    identicas nos dois runtimes, logo cmp.py as daria como IDENTICAS. O teto de tamanho
    evita acusar uma tela real que apenas cite a frase."""
    c = normaliza(corpo)
    return len(c) < 1000 and _INVALIDA.search(c) is not None


# Mesmos marcadores de php/relatorios.py (_ERRO_PHP). cmp.py da IDENTICO a uma pagina de erro igual
# nos dois lados; o corpo e pequeno (a 500 do e-cidade tem ~3,7 KB), entao o teto evita acusar uma
# tela real que apenas cite "Erro interno". Fatal/Parse error valem em qualquer tamanho.
_ERRO_FATAL = re.compile(rb"Fatal error|Parse error|Uncaught \w*(?:Error|Exception)", re.I)
_ERRO_SISTEMA = re.compile(rb"Notifica\S{1,6} do Sistema|Erro interno", re.I)
TETO_PAGINA_DE_ERRO = 20_000


def corpo_e_pagina_de_erro(corpo: bytes) -> bool:
    c = normaliza(corpo)
    return _ERRO_FATAL.search(c) is not None or (
        len(c) < TETO_PAGINA_DE_ERRO and _ERRO_SISTEMA.search(c) is not None)


def sessao_autenticada(sid: str) -> bool:
    """Sonda barata: uma tela conhecida com esta sessao (sem restaurar nada, para nao
    transformar um SID inexistente em sessao valida). Falha fechado: corpo vazio (ex.: o
    redirect para db_erros.php, que o curl sem -L nao segue) ou minusculo e sem HTML
    (< 50 B sem '<') conta como NAO autenticado."""
    corpo = _requisita(sid, TELA_SONDA)
    if len(corpo) < 50 and b"<" not in corpo:
        return False
    return not corpo_de_sessao_invalida(corpo)


def roda_telas(sid: str, prefixo: str, area: str, _retenta: bool = True) -> tuple[list[Caso], dict[str, bytes]]:
    """Roda cmp.py e devolve (casos, corpos). Um IDENTICO vindo so do cmp.py nunca significou
    "exercitada": uma tela vazia ou que falha igual nos dois lados tambem e "identica". Este
    passo busca UM corpo (lado da referencia) de cada tela que cmp.py nao acusou e, se o corpo
    normalizado tem 0 bytes, rebaixa a INCONCLUSIVO. `corpos` mapeia tela -> corpo cru dessas
    telas (entrada de grava_hashes/cobertura_telas); telas DIVERGE/TIMEOUT/PULADA nao tem corpo.
    Falha ao buscar corpo ou total do resumo != len(telas) -> um unico ERRO_AMBIENTE."""
    try:
        telas = lista_telas(prefixo)
        if not sessao_autenticada(sid):
            return [Caso("telas", area, Veredito.ERRO_AMBIENTE,
                         "sessao nao autenticada (pagina 'Sessao invalida')")], {}
        saida = _roda_cmp(sid, prefixo)
    except (ErroAmbienteBanco, OSError, subprocess.TimeoutExpired) as e:
        return [Caso("telas", area, Veredito.ERRO_AMBIENTE, str(e))], {}
    resumo = next((m for m in map(_RESUMO.match, saida.splitlines()) if m), None)
    if resumo is not None and int(resumo.group(2)) != len(telas):
        return [Caso("telas", area, Veredito.ERRO_AMBIENTE,
                     f"resumo do cmp.py tem {resumo.group(2)} telas, lista_telas tem {len(telas)}")], {}
    casos = parse_cmp(saida, area, telas)
    corpos: dict[str, bytes] = {}
    try:
        for c in casos:
            if c.veredito != Veredito.IDENTICO or c.id not in telas:
                continue
            corpos[c.id] = busca_corpo(sid, c.id)
    except SessaoPerdida as e:  # a bateria renova a sessao e refaz o prefixo
        return [Caso("telas", area, Veredito.ERRO_AMBIENTE,
                     f"sessao nao autenticada (sessao perdida ao buscar corpo: {e})")], {}
    except (ErroAmbienteBanco, OSError, subprocess.TimeoutExpired) as e:
        return [Caso("telas", area, Veredito.ERRO_AMBIENTE, f"falha ao buscar corpo: {e}")], corpos
    for c in casos:
        if c.id not in corpos:
            continue
        if corpo_de_sessao_invalida(corpos[c.id]):
            c.veredito = Veredito.ERRO_AMBIENTE
            c.detalhe = "sessao expirou durante a rodada (pagina 'Sessao invalida')"
        elif normaliza(corpos[c.id]) == b"":
            c.veredito = Veredito.INCONCLUSIVO
            c.detalhe = "resposta vazia (0 bytes) nos dois lados"
        elif corpo_e_pagina_de_erro(corpos[c.id]):
            c.veredito = Veredito.INCONCLUSIVO
            c.detalhe = "pagina de erro identica nos dois lados; tela nao exercitada"
    for c in casos:
        if c.veredito == Veredito.DIVERGE and _RE_200X200.match(c.detalhe or "") and _reavalia_pdf(sid, c.id):
            c.veredito = Veredito.IDENTICO
            c.detalhe = ("bytes diferem mas o texto do PDF e identico nos dois lados "
                         "(compressao/metadados do FPDF): " + c.detalhe)
    if _retenta:
        casos, corpos = _retenta_timeouts(sid, area, telas, casos, corpos)
    return casos, corpos


# DIVERGE do cmp.py com 200 nos dois lados: so ai pode haver "diferenca de bytes sem diferenca de conteudo"
_RE_200X200 = re.compile(r"ref=200/\d+B\s+85=200/\d+B")


def _reavalia_pdf_impl(sid: str, tela: str) -> bool:
    """cmp.py compara BYTES; o FPDF comprime os streams e embute metadados, entao um PDF de conteudo igual
    pode divergir (ruido, comprovado em con4_gerrrelatorio, orc2_orcprevmensalrec002 e sys3_modulos002:
    `/Length 636` x `/Length 609` no mesmo texto). Baixa os dois lados e compara o TEXTO extraido: so e ruido
    se os dois forem PDF 200 e o texto (nao vazio) for identico. Qualquer falha = continua DIVERGE."""
    from regressao.php.relatorios import extrai_conteudo
    textos = []
    try:
        conts = containers_do_ambiente()
        for container in (conts.ref, conts.php_novo):
            restaura_sessao(sid)
            status, corpo = _requisita_status(sid, tela, container=container)
            if status != 200 or not corpo.lstrip().startswith(b"%PDF"):
                return False
            textos.append(extrai_conteudo(corpo, "pdf"))
    except Exception:
        return False
    return bool(textos[0].strip()) and textos[0] == textos[1]


_reavalia_pdf = _reavalia_pdf_impl  # alias patchavel nos testes (conftest desliga a reavaliacao real)


def _retenta_timeouts(sid: str, area: str, telas: list[str], casos: list[Caso],
                      corpos: dict[str, bytes]) -> tuple[list[Caso], dict[str, bytes]]:
    """UMA retentativa das telas que deram TIMEOUT no cmp.py (um worker preso nao pode virar ERRO_AMBIENTE
    sem 2a chance). Persistindo, o ERRO_AMBIENTE fica com a marca `apos 1 retentativa`."""
    tos = [c.id for c in casos if c.veredito == Veredito.ERRO_AMBIENTE and c.detalhe.startswith("timeout:")
           and c.id in telas]
    if not tos:
        return casos, corpos
    cs2, cp2 = roda_telas(sid, "^(?:" + "|".join(re.escape(t) for t in tos) + ")$", area, _retenta=False)
    if any(c.id not in tos for c in cs2):  # a retentativa nao rodou (ex.: sessao): mantem os originais
        for c in casos:
            if c.id in tos:
                c.detalhe += " (retentativa nao executada)"
        return casos, corpos
    for c in cs2:
        if c.veredito == Veredito.ERRO_AMBIENTE and c.detalhe.startswith("timeout:"):
            c.detalhe += " (apos 1 retentativa)"
    resto = [c for c in casos if c.id not in tos]
    return sorted(resto + cs2, key=lambda c: c.id), {**corpos, **cp2}
