"""Fluxos de navegador (Playwright, headless) pelo proxy (REGRESSAO_PROXY_URL, padrao :8190), em modo golden-master.

    python -m regressao.completa.fluxos gravar   --saida DIR [--proxy URL] [--fluxo ID ...] [--confirmo-sobrescrever]
    python -m regressao.completa.fluxos comparar --saida DIR [--proxy URL] [--fluxo ID ...] [--sem-restaurar]

O proxy e a entrada real do usuario: ele manda cada tela para a referencia PHP 7.4 ou para o 8.5 e diz
qual no cabecalho `X-Ecidade-Runtime`. Esse cabecalho e REGISTRADO em cada requisicao principal mas NUNCA
e motivo de falha no `comparar`: ele vai mudar na migracao; aparece como INFO no detalhe, e o resumo AVISA quando
nenhum passo veio do 8.5 (a rodada mediu 7.4 x 7.4). O `gravar` recusa passo servido por outro runtime que nao o 7.4.

Base 7.4 (PR #8): o login abre o Desktop (`/extension/desktop`, ECIDADE_DESKTOP forcado). O usuario abre o
MENU, escolhe instituicao, area e modulo, e cada item de menu abre uma JANELA do Desktop com o frame `corpo`
(a tela). O menu de modulos so monta com as migrations Laravel do PR aplicadas no banco (dump v2,
regressao/README.md secao 2).

Fluxos (cada um com sua propria sessao de navegador, limite de 120 s):
  navegacao         login (Desktop) -> MENU (instituicao) -> area -> modulo Arrecadacao ->
                    tela de cadastro (arr1_grupotaxa001) -> tela de relatorio (cai2_relcaixa_001) -> sair (Logout)
  incluir-registro  entra no modulo, abre arr1_grupotaxa001, preenche pela UI (com a consulta de
                    "tipo de grupo"), clica Incluir; confere o alerta e o EFEITO NO BANCO
                    (hash_tabelas de arrecadacao.grupotaxa antes/depois)
  emitir-relatorio  entra no modulo, abre cai2_relcaixa_001?db_opcao=tabrecjm e clica Imprimir; confere
                    status/tipo/texto do PDF aberto na janela nova

Por passo guardamos: DOM normalizado do frame `corpo` da janela aberta (antes de abrir uma tela, o DOM
do MENU do Desktop), sem scripts/estilos, datas, horas, ids de sessao, saudacao; status HTTP das requisicoes principais (documentos e XHR), runtime (info),
alertas, valores digitados e efeito no banco. Console errors e requisicoes que falham sao coletados por
fluxo e so viram veredito se DIFEREM da baseline. Nunca se grava senha, sessao, token ou cabecalho:
`confere_sem_segredos` barra a gravacao.

Estado do banco: o fluxo `incluir-registro` depende de banco recem-restaurado (a sequence de
grupotaxa entra no alerta). `gravar` e `comparar` restauram a baseline por padrao (~4 min);
`--sem-restaurar` marca a rodada como NAO comparavel. Os fluxos deixam o banco SUJO por construcao
(um registro de teste em grupotaxa, sessoes/auditoria de login): a proxima bateria restaura.

Veredito por passo: IDENTICO / DIVERGE (diff unificado do DOM) / INCONCLUSIVO (passo que ja nao
funcionava na baseline, ou nao exercitado porque um passo anterior falhou) / ERRO_AMBIENTE (o primeiro
passo falhou: proxy fora, login recusado, baseline ausente ou de outro dump, navegador indisponivel).
Passo que funcionava na baseline e agora falha = DIVERGE (e os seguintes ficam INCONCLUSIVO).
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from regressao.nucleo import git
from regressao.nucleo.normaliza import normaliza
from regressao.nucleo.veredito import Caso, Veredito

RAIZ = Path(__file__).resolve().parents[2]
DIR_BASELINE = Path(__file__).resolve().parents[1] / "baseline" / "fluxos"
AREA = "fluxos"
LIMITE_DOM = 80_000          # caracteres do DOM guardados por passo (o sha256 cobre o DOM inteiro)
LIMITE_CONTEUDO = 3_000
PRAZO_FLUXO_S = 120
TIMEOUT_ACAO_MS = 20_000
TABELA_REGISTRO = "arrecadacao.grupotaxa"
INSTITUICAO_PADRAO = "1 - PREFEITURA DBSELLER"  # texto da instituicao no MENU do Desktop
AREA_PADRAO = "DB:TRIBUTÁRIO"       # texto da area no MENU do Desktop
MODULO_PADRAO = "Arrecadação"       # texto do modulo no MENU do Desktop
# Requisicoes periodicas do Desktop (o "ping" da sessao): caem em qualquer passo conforme o relogio, entao
# nao entram nas requisicoes por passo (senao o mesmo fluxo daria DIVERGE de uma rodada para outra).
PERIODICAS = ("/extension/desktop/Window/ping/",)


class SegredoNaBaseline(ValueError):
    """Um fluxo traria sessao/token/hash de senha para a baseline: a gravacao e barrada."""


class BaselineInvalida(Exception):
    """Baseline de fluxos ausente, corrompida ou gravada com outro dump (-> ERRO_AMBIENTE)."""


class RecusaBaseline(ValueError):
    """`gravar` recusado para proteger a baseline pre-migracao."""


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8", errors="replace")).hexdigest()


# ------------------------------------------------------------------ normalizacao

_RE_SCRIPT = re.compile(r"<script\b([^>]*)>.*?</script\s*>", re.I | re.S)
_RE_STYLE = re.compile(r"<style\b[^>]*>.*?</style\s*>", re.I | re.S)
_RE_ACESSOS = re.compile(r'(<div id="acessosModulo">)(.*?)(</div>)', re.S)  # "Ultimos acessos ao Modulo"
_RE_DATA_URI =re.compile(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]{40,}")
_RE_DATA = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
_RE_HORA = re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b")
_RE_SAUDACAO = re.compile(r"\b(?:Bom dia|Boa tarde|Boa noite)\b")
_RE_HEX40 = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])")


def _volateis(texto: str) -> str:
    texto = _RE_HEX40.sub("SHA1X", texto)
    texto = normaliza(texto.encode("utf-8")).decode("utf-8", errors="replace")  # sid=, md5, tmp/, porta...
    texto = _RE_DATA.sub("DD/MM/AAAA", texto)
    texto = _RE_HORA.sub("HH:MM", texto)
    return _RE_SAUDACAO.sub("SAUDACAO", texto)


def normaliza_dom(html: str) -> str:
    """DOM comparavel: sem corpo de <script>/<style> (o `src` das tags fica), sem imagens embutidas,
    sem volateis (datas, horas, ids de sessao, saudacao), uma tag por linha, espacos colapsados."""
    html = _RE_SCRIPT.sub(lambda m: f"<script{m.group(1)}></script>", html)
    html = _RE_STYLE.sub("<style></style>", html)
    html = _RE_ACESSOS.sub(r"\1<!-- historico de acessos omitido -->\3", html)
    html = _RE_DATA_URI.sub("data:X", html)
    html = _volateis(html)
    html = re.sub(r"\s+", " ", html)
    html = re.sub(r">\s*<", ">\n<", html)
    return "\n".join(l.strip() for l in html.split("\n") if l.strip())


def normaliza_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", _volateis(texto)).strip()


def caminho_seguro(url: str) -> str:
    """Caminho + NOMES dos parametros de query (nunca os valores: `abrir.php?sAuth=` carrega o hash da
    senha). Um unico parametro sem valor com cara de base64 (`corpo.php?aW5zdGl0PTE=`) vira `<opaco>`."""
    partes = urlsplit(url)
    caminho = partes.path or "/"
    if not partes.query:
        return caminho
    pares = parse_qsl(partes.query, keep_blank_values=True)
    if len(pares) == 1 and re.fullmatch(r"[A-Za-z0-9+/%]{8,}", pares[0][0]) and set(pares[0][1]) <= {"="}:
        return f"{caminho}?<opaco>"
    return f"{caminho}?" + "&".join(sorted({k for k, _ in pares}))


_SEGREDOS = [re.compile(p) for p in (
    r"PHPSESSID=", r"sAuth=", r"ECIDADEWINDOWMAIN=[0-9a-fA-F]", r"Bearer\s+\S", r"eyJ[\w-]{8,}",
    r"(?<![0-9a-fA-F])[0-9a-fA-F]{32,}(?![0-9a-fA-F])", r"(?i)\bsenha\s*[:=]\s*\S{4,}")]
_CAMPOS_SEM_VARREDURA = {"dom_sha256", "banco", "hash_antes", "conteudo_sha256"}  # hashes legitimos (md5/sha256 de tabelas e de DOM)


def _textos(obj, chave=""):
    if chave in _CAMPOS_SEM_VARREDURA:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _textos(v, k)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _textos(v, chave)


def confere_sem_segredos(fluxo: dict) -> None:
    for t in _textos(fluxo):
        for rx in _SEGREDOS:
            if rx.search(t):
                raise SegredoNaBaseline(
                    f"fluxo {fluxo.get('id')}: texto casa {rx.pattern!r} (sessao/token/hash de senha?): {t[:80]!r}")


# ------------------------------------------------------------------ coleta de eventos

class Coletor:
    """Acumula o que o navegador viu. `fecha_passo` devolve (e zera) o que e POR PASSO (requisicoes
    principais, runtime, alertas); console e falhas de rede sao do FLUXO inteiro (sem janela de tempo,
    para nao depender de qual passo uma requisicao tardia cai)."""

    PRINCIPAIS = ("document", "xhr", "fetch")
    ESTATICOS = (".js", ".css", ".png", ".gif", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2", ".ttf")

    def __init__(self):
        self._req: set[str] = set()
        self._runtime: dict[str, str] = {}
        self._dialogos: list[str] = []
        self._console: set[str] = set()
        self._falhas: set[str] = set()
        self.pdfs: list[str] = []  # URLs (so em memoria) de documentos PDF abertos pelo navegador

    def resposta(self, metodo: str, url: str, status: int, tipo: str, runtime: str | None,
                 content_type: str | None = None) -> None:
        caminho = caminho_seguro(url)
        if urlsplit(url).path.endswith(PERIODICAS):
            return
        # `require_once` do e-cidade carrega scripts por XHR: sao estaticos, nao "requisicoes principais"
        principal = tipo in self.PRINCIPAIS and not urlsplit(url).path.lower().endswith(self.ESTATICOS)
        if principal:
            self._req.add(f"{metodo} {status} {caminho}")
            if runtime:
                self._runtime[caminho] = runtime
            if tipo == "document" and "pdf" in (content_type or "").lower():
                self.pdfs.append(url)
        elif status >= 400:
            self._falhas.add(f"{status} {metodo} {caminho}")

    def requisicao_falhou(self, metodo: str, url: str, motivo: str | None) -> None:
        if motivo and "ERR_ABORTED" in motivo:
            return  # cancelamento por navegacao/download: ruido, nao falha de rede
        self._falhas.add(normaliza_texto(f"FALHOU {metodo} {caminho_seguro(url)}: {motivo or 'desconhecido'}"))

    def dialogo(self, tipo: str, mensagem: str) -> None:
        self._dialogos.append(normaliza_texto(f"{tipo}: {mensagem}"))

    def erro_console(self, texto: str) -> None:
        self._console.add(normaliza_texto(texto))

    @property
    def console(self) -> list[str]:
        return sorted(self._console)

    @property
    def falhas(self) -> list[str]:
        return sorted(self._falhas)

    def fecha_passo(self) -> dict:
        saida = {"requisicoes": sorted(self._req), "runtime": dict(sorted(self._runtime.items())),
                 "dialogos": list(self._dialogos)}
        self._req, self._runtime, self._dialogos = set(), {}, []
        return saida


# ------------------------------------------------------------------ comparacao

def _passo_por_nome(fluxo: dict, nome: str) -> dict | None:
    return next((p for p in fluxo["passos"] if p["nome"] == nome), None)


def _info_runtime(base: dict, atual: dict) -> str:
    mud = [f"{c}: {base['runtime'].get(c, '-')} -> {atual['runtime'].get(c, '-')}"
           for c in sorted(base["runtime"].keys() | atual["runtime"].keys())
           if base["runtime"].get(c) != atual["runtime"].get(c)]
    return ("INFO runtime (nao e falha): " + "; ".join(mud)) if mud else ""


def _diff_dom(base: dict, atual: dict, id: str) -> str:
    a, b = (base.get("dom") or "").splitlines(), (atual.get("dom") or "").splitlines()
    return "\n".join(difflib.unified_diff(a, b, f"baseline/{id}", f"atual/{id}", lineterm="", n=2)) + "\n"


def _compara_passo(fid: str, idx: int, bp: dict, ap: dict | None) -> Caso:
    id = f"fluxo:{fid}:{bp['nome']}"
    if ap is None:
        return Caso(id, AREA, Veredito.DIVERGE, "passo existe na baseline e nao foi executado agora")
    if not bp.get("ok", True):
        return Caso(id, AREA, Veredito.INCONCLUSIVO, f"o passo ja nao funcionava na baseline: {bp.get('erro')}")
    if ap.get("exercitado") is False:
        return Caso(id, AREA, Veredito.INCONCLUSIVO, f"nao exercitado: {ap.get('erro')}")
    if not ap.get("ok", True):
        if idx == 0:
            return Caso(id, AREA, Veredito.ERRO_AMBIENTE, f"o primeiro passo falhou: {ap.get('erro')}")
        return Caso(id, AREA, Veredito.DIVERGE, f"o passo funcionava na baseline e agora falha: {ap.get('erro')}")
    motivos, diff = [], ""
    if bp.get("dom_sha256") != ap.get("dom_sha256"):
        motivos.append("DOM diferente")
        diff = _diff_dom(bp, ap, id)
        if bp.get("dom_truncado") or ap.get("dom_truncado"):
            motivos[-1] += f" (so os primeiros {LIMITE_DOM} caracteres entram no diff)"
    if bp["requisicoes"] != ap["requisicoes"]:
        so_b = sorted(set(bp["requisicoes"]) - set(ap["requisicoes"]))
        so_a = sorted(set(ap["requisicoes"]) - set(bp["requisicoes"]))
        motivos.append(f"requisicoes/status diferentes: baseline={so_b} atual={so_a}")
    if bp["dialogos"] != ap["dialogos"]:
        motivos.append(f"alertas diferentes: baseline={bp['dialogos']} atual={ap['dialogos']}")
    if bp.get("banco") != ap.get("banco"):
        tabs = sorted((bp.get("banco") or {}).keys() | (ap.get("banco") or {}).keys())
        dif = [t for t in tabs if (bp.get("banco") or {}).get(t) != (ap.get("banco") or {}).get(t)]
        motivos.append(f"efeito no banco diferente em {dif}")
    if bp.get("extra") != ap.get("extra"):
        chaves = sorted(k for k in (bp.get("extra") or {}).keys() | (ap.get("extra") or {}).keys()
                        if (bp.get("extra") or {}).get(k) != (ap.get("extra") or {}).get(k))
        motivos.append(f"dados do passo diferentes: {chaves}")
    info = _info_runtime(bp, ap)
    if motivos:
        return Caso(id, AREA, Veredito.DIVERGE, "; ".join(motivos) + (f". {info}" if info else ""), diff=diff)
    return Caso(id, AREA, Veredito.IDENTICO, info)


def compara_fluxo(base: dict, atual: dict) -> list[Caso]:
    fid = base["id"]
    casos = [_compara_passo(fid, i, bp, _passo_por_nome(atual, bp["nome"])) for i, bp in enumerate(base["passos"])]
    for ap in atual["passos"]:
        if _passo_por_nome(base, ap["nome"]) is None:
            casos.append(Caso(f"fluxo:{fid}:{ap['nome']}", AREA, Veredito.DIVERGE, "passo novo, sem baseline"))
    novos_c = sorted(set(atual.get("console", [])) - set(base.get("console", [])))
    novos_f = sorted(set(atual.get("falhas", [])) - set(base.get("falhas", [])))
    idev = f"fluxo:{fid}:eventos"
    if novos_c or novos_f:
        casos.append(Caso(idev, AREA, Veredito.DIVERGE,
                          f"eventos novos em relacao a baseline: console={novos_c} rede={novos_f}"))
    else:
        info = []
        if atual.get("console"):
            info.append(f"console errors (ja na baseline): {atual['console']}")
        if atual.get("falhas"):
            info.append(f"requisicoes com falha (ja na baseline): {atual['falhas']}")
        casos.append(Caso(idev, AREA, Veredito.IDENTICO, "INFO " + "; ".join(info) if info else ""))
    return casos


# ------------------------------------------------------------------ baseline em disco

def grava_baseline(diretorio: Path, fluxos: list[dict], dump_sha256: str, commit: str,
                   completo: bool = False) -> None:
    for f in fluxos:
        confere_sem_segredos(f)  # antes de tocar no disco
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    for f in fluxos:
        (diretorio / f"{f['id']}.json").write_text(json.dumps(f, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                                   encoding="utf-8", newline="\n")
    if completo:
        ids = {f["id"] for f in fluxos}
        for velho in diretorio.glob("*.json"):
            if velho.stem not in ids and velho.name != "_meta.json":
                velho.unlink()
    existentes = sorted(p.stem for p in diretorio.glob("*.json") if p.name != "_meta.json")
    meta = {"dump_sha256": dump_sha256, "commit": commit, "data": time.strftime("%Y-%m-%d"),
            "fluxos": existentes,
            "n_passos": sum(len(json.loads((diretorio / f"{i}.json").read_text(encoding="utf-8"))["passos"])
                            for i in existentes)}
    (diretorio / "_meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n",
                                          encoding="utf-8", newline="\n")


def carrega_baseline(diretorio: Path, dump_sha256: str) -> dict[str, dict]:
    diretorio = Path(diretorio)
    try:
        meta = json.loads((diretorio / "_meta.json").read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise BaselineInvalida(f"baseline de fluxos ausente: {diretorio}/_meta.json (rode `gravar`)") from e
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BaselineInvalida(f"{diretorio}/_meta.json invalido: {e}") from e
    if meta.get("dump_sha256") != dump_sha256:
        raise BaselineInvalida(f"baseline de fluxos gravada com outro dump ({meta.get('dump_sha256')}); "
                               f"o atual e {dump_sha256}")
    fluxos: dict[str, dict] = {}
    for fid in meta.get("fluxos", []):
        try:
            fluxos[fid] = json.loads((diretorio / f"{fid}.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise BaselineInvalida(f"baseline do fluxo {fid} ausente/invalida: {e}") from e
    if not fluxos:
        raise BaselineInvalida(f"baseline de fluxos ausente: nenhum fluxo em {diretorio}")
    return fluxos


# ------------------------------------------------------------------ navegador (verificado ao vivo)

class TempoEsgotado(Exception):
    pass


class _Janela:
    """Uma sessao de navegador: contexto + pagina de login + janela principal (frames topo/corpo)."""

    def __init__(self, browser, proxy: str, coletor: Coletor, prazo_s: int):
        self.proxy = proxy.rstrip("/")
        self.c = coletor
        self.fim = time.monotonic() + prazo_s
        self.ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR",
                                       timezone_id="America/Sao_Paulo")
        self.ctx.set_default_timeout(TIMEOUT_ACAO_MS)
        self.em_voo = 0
        self.ultimo = time.monotonic()
        self.ctx.on("request", self._inicio)
        self.ctx.on("requestfinished", self._fim_req)
        self.ctx.on("response", self._resposta)
        self.ctx.on("requestfailed", self._falhou)
        self.ctx.on("console", lambda m: coletor.erro_console(m.text) if m.type == "error" else None)
        self.ctx.on("weberror", lambda e: coletor.erro_console(f"pageerror: {e.error.message if e.error else ''}"))
        self.ctx.on("dialog", self._dialogo)
        self.login_pg = self.ctx.new_page()
        self.main = None   # a pagina do Desktop (a mesma do login, depois do POST /v4/login)
        self._corpo = None  # frame `corpo` da janela do Desktop em uso

    # eventos
    def _inicio(self, _r) -> None:
        self.em_voo += 1
        self.ultimo = time.monotonic()

    def _fim_req(self, _r) -> None:
        self.em_voo = max(0, self.em_voo - 1)
        self.ultimo = time.monotonic()

    def _falhou(self, r) -> None:
        self.em_voo = max(0, self.em_voo - 1)
        self.ultimo = time.monotonic()
        self.c.requisicao_falhou(r.method, r.url, r.failure)

    def _resposta(self, r) -> None:
        try:
            self.c.resposta(r.request.method, r.url, r.status, r.request.resource_type,
                            r.headers.get("x-ecidade-runtime"), r.headers.get("content-type"))
        except Exception:
            pass  # evento tardio de pagina fechada: nao e falha do fluxo

    def _dialogo(self, d) -> None:
        self.c.dialogo(d.type, d.message)
        d.accept()

    # utilitarios
    def prazo(self) -> None:
        if time.monotonic() > self.fim:
            raise TempoEsgotado(f"fluxo passou de {PRAZO_FLUXO_S}s")

    def espera(self, ms: int = 400) -> None:
        self.login_pg.wait_for_timeout(ms)

    def assenta(self, maximo_s: float = 10.0) -> None:
        """Espera a pagina quietar: nada em voo e 0,6 s sem evento de rede (no maximo `maximo_s`).
        `networkidle` do Playwright nao serve: o e-cidade mantem requisicoes pendentes."""
        self.prazo()
        limite = time.monotonic() + maximo_s
        while time.monotonic() < limite:
            self.login_pg.wait_for_timeout(250)
            if self.em_voo <= 0 and time.monotonic() - self.ultimo > 0.6:
                return

    def corpo(self):
        """Frame `corpo` da ultima janela do Desktop aberta por `abre_menu` (a tela em uso)."""
        if self._corpo is None:
            raise RuntimeError("nenhuma tela aberta no Desktop")
        return self._corpo

    @staticmethod
    def _sel_texto(seletor: str, texto: str) -> str:
        return f"{seletor}:text-is({json.dumps(texto, ensure_ascii=False)})"

    # passos
    def login(self) -> None:
        """login.php -> POST /v4/login -> Desktop (/extension/desktop) na mesma pagina."""
        self.login_pg.goto(f"{self.proxy}/login.php")
        self.login_pg.fill("#usu_login", "dbseller")
        self.login_pg.fill("#usu_senha", "dbseller")
        self.login_pg.click("#btnlogar")
        try:
            self.login_pg.wait_for_url(lambda u: "/extension/desktop" in u)
        except Exception as e:
            raise RuntimeError("login nao abriu o Desktop (/extension/desktop)") from e
        self.main = self.login_pg
        self.main.wait_for_load_state("load")
        self.main.wait_for_selector(".taskbar-menu-button")
        self.assenta()

    def abre_menu_principal(self, instituicao: str = INSTITUICAO_PADRAO) -> None:
        """Botao MENU do Desktop; escolhe a instituicao (a lista de areas recarrega)."""
        if not self.main.locator("#menu.active").count():
            self.main.click(".taskbar-menu-button")
        self.main.wait_for_selector(self._sel_texto("#instituicoes span", instituicao))
        self.main.click(self._sel_texto("#instituicoes span", instituicao))
        self.main.wait_for_selector("#areas span")
        self.assenta()

    def escolhe_area(self, area: str = AREA_PADRAO, modulo: str = MODULO_PADRAO) -> None:
        self.main.click(self._sel_texto("#areas span", area))
        self.main.wait_for_selector(self._sel_texto("#modulos span", modulo))
        self.assenta()

    def escolhe_modulo(self, modulo: str = MODULO_PADRAO) -> None:
        self.main.click(self._sel_texto("#modulos span", modulo))
        self.main.wait_for_selector(".menu-itens .menu-list > span")
        self.assenta()

    _BUSCA_ITEM = """(acao) => {
      const $ = window.jQuery;
      const raiz = $('.menu-itens').first().find('.menu-list > span').map((i, s) => $(s).data('menu.filhos')).get();
      function busca(nos, cam) {
        for (const n of nos) {
          if (n && n.action === acao) return [...cam, n.id];
          if (n && n.filhos) { const r = busca(Object.values(n.filhos), [...cam, n.id]); if (r) return r; }
        }
        return null;
      }
      return busca(raiz, []);
    }"""

    def abre_menu(self, acao: str) -> None:
        """Abre, pelo MENU do modulo atual, o item cuja action e `acao` (clica cada nivel, como o usuario);
        a janela nova passa a ser a tela em uso (`corpo`)."""
        if not self.main.locator("#menu.active").count():
            self.main.click(".taskbar-menu-button")
            self.main.wait_for_selector(".menu-itens .menu-list > span")
        caminho = self.main.evaluate(self._BUSCA_ITEM, acao)
        if not caminho:
            raise RuntimeError(f"item de menu inexistente no modulo: {acao}")
        antes = {id(f) for f in self.main.frames}
        for mid in caminho:
            # o evento vai direto ao item (o handler do menu e delegado): as listas deslizam/rolam com animacao
            # e um clique por coordenada as vezes nao acha o item "estavel" a tempo
            item = self.main.locator(f"#menu_id_{mid}")
            item.wait_for(state="attached")
            item.dispatch_event("click")
        pagina = acao.split("?")[0]
        for _ in range(80):
            self.prazo()
            novos = [f for f in self.main.frames if f.name == "corpo" and id(f) not in antes and pagina in f.url]
            if novos:
                self._corpo = novos[-1]
                break
            self.login_pg.wait_for_timeout(250)
        else:
            raise RuntimeError(f"a janela de {pagina} nao abriu")
        self._corpo.wait_for_load_state("load")
        self.assenta()

    def entra_no_modulo(self, area: str = AREA_PADRAO, modulo: str = MODULO_PADRAO) -> None:
        self.login()
        self.abre_menu_principal()
        self.escolhe_area(area, modulo)
        self.escolhe_modulo(modulo)

    def snapshot(self) -> dict:
        """DOM da tela em uso; antes de abrir uma tela, o do MENU do Desktop (instituicoes/areas/modulos/itens)."""
        if self._corpo is not None:
            html, url = self._corpo.content(), self._corpo.url
        else:
            html, url = self.main.inner_html("#menu"), self.main.url
        dom = normaliza_dom(html)
        return {"url": caminho_seguro(url), "dom": dom[:LIMITE_DOM], "dom_sha256": sha(dom),
                "dom_truncado": len(dom) > LIMITE_DOM}

    def fecha(self) -> None:
        try:
            self.ctx.close()
        except Exception:
            pass


def _erro_curto(e: Exception) -> str:
    linha = (str(e).strip().splitlines() or [""])[0]
    return normaliza_texto(f"{type(e).__name__}: {linha}")[:300]


def _passo_vazio(nome: str, ok: bool, erro: str | None, exercitado: bool = True) -> dict:
    p = {"nome": nome, "ok": ok, "erro": erro, "url": None, "dom": None, "dom_sha256": None, "dom_truncado": False,
         "requisicoes": [], "runtime": {}, "dialogos": [], "banco": None, "extra": {}}
    if not exercitado:
        p["exercitado"] = False
    return p


def hash_sem_horas(tabelas: list[str]) -> dict[str, str]:
    """Como `hash_tabelas`, mas sem a coluna `z01_hora` (o CGM grava a hora do relogio, que mudaria o hash a
    cada rodada). SO essa coluna sai: o resto da linha, inclusive outras horas, continua no hash."""
    from regressao.nucleo.banco import _NOME_TABELA, _psql
    saida = {}
    for t in tabelas:
        if not _NOME_TABELA.fullmatch(t):
            raise ValueError(f"nome de tabela invalido: {t!r}")
        expr = "(to_jsonb(t) - 'z01_hora')::text"
        saida[t] = _psql(f"select md5(coalesce(string_agg({expr}, E'\\n' order by {expr}), '')) from {t} t").strip()
    return saida


def _banco_linhas(tabelas: list[str] | None = None, sem_horas: bool = False) -> dict:
    """hash_tabelas + contagem de linhas por tabela (padrao: a tabela do fluxo `incluir-registro`)."""
    from regressao.nucleo.banco import _psql, hash_tabelas
    tabelas = tabelas or [TABELA_REGISTRO]
    return {"hash": (hash_sem_horas if sem_horas else hash_tabelas)(tabelas),
            "linhas": {t: int(_psql(f"select count(*) from {t}").strip()) for t in tabelas}}


# Cada fluxo: lista de (nome, funcao(janela) -> extra|None, tira_snapshot). A funcao devolve um dict
# `extra` (valores que entram na comparacao) e pode trazer "banco" (dict tabela->hash) a ser promovido.

def _f_navegacao():
    def login(j):
        j.login()

    def menu(j):
        j.abre_menu_principal()

    def area(j):
        j.escolhe_area()

    def modulo(j):
        j.escolhe_modulo()

    def cadastro(j):
        j.abre_menu("arr1_grupotaxa001.php")
        return {"campos": sorted(j.corpo().eval_on_selector_all("input[name]", "els => els.map(e => e.name)"))}

    def relatorio(j):
        j.abre_menu("cai2_relcaixa_001.php?db_opcao=tabrecjm")

    def sair(j):
        # Menu do usuario (topo) -> Logout. Na referencia, no Chromium headless, o clique nao gera requisicao e o
        # Desktop continua aberto (medido em 2026-11-18): o passo registra o que acontece, nao o que se espera.
        j.main.click(".topbar .user-name")
        j.main.click("#logout")
        try:
            j.main.wait_for_url(lambda u: "/extension/desktop" not in u, timeout=5000)
        except Exception:
            pass
        j.assenta()
        return {"saiu_do_desktop": "/extension/desktop" not in j.main.url}

    return [("login", login, True), ("menu", menu, True), ("area", area, True), ("modulo", modulo, True),
            ("tela-cadastro", cadastro, True), ("tela-relatorio", relatorio, True), ("sair", sair, False)]


def _f_incluir():
    def entrada(j):
        j.entra_no_modulo()

    def cadastro(j):
        j.abre_menu("arr1_grupotaxa001.php")

    def preenche(j):
        c = j.corpo()
        c.fill("input[name=ar37_grupotaxatipo]", "1")
        c.press("input[name=ar37_grupotaxatipo]", "Tab")
        c.wait_for_function("() => document.querySelector('input[name=ar38_descricao]').value !== ''")
        c.fill("input[name=ar37_descricao]", "TESTE_FLUXO")
        j.assenta()
        return {"valores": {n: c.input_value(f"input[name={n}]")
                            for n in ("ar37_grupotaxatipo", "ar38_descricao", "ar37_descricao")}}

    def salvar(j):
        antes = _banco_linhas()
        j.c.fecha_passo()  # as requisicoes do passo anterior ja foram guardadas; este so olha o POST
        j.corpo().click("input[name=incluir]")
        j.corpo().wait_for_load_state("load")
        j.assenta()
        depois = _banco_linhas()
        return {"banco": depois["hash"], "linhas_antes": antes["linhas"][TABELA_REGISTRO],
                "linhas_depois": depois["linhas"][TABELA_REGISTRO],
                "hash_antes": antes["hash"][TABELA_REGISTRO]}

    return [("entrada", entrada, False), ("tela-cadastro", cadastro, True), ("preenche", preenche, True),
            ("salvar", salvar, True)]


def _f_relatorio():
    def entrada(j):
        j.entra_no_modulo()

    def tela(j):
        j.abre_menu("cai2_relcaixa_001.php?db_opcao=tabrecjm")

    def emite(j):
        return _emite_pdf(j, "#exibir_relatorio")

    return [("entrada", entrada, False), ("tela-relatorio", tela, True), ("emitir", emite, False)]


def _emite_pdf(j, seletor: str) -> dict:
    """Clica no botao que abre o relatorio e confere o PDF aberto na janela nova."""
    from regressao.php.relatorios import extrai_conteudo
    j.c.fecha_passo()
    j.c.pdfs.clear()
    antes = set(j.ctx.pages)
    j.corpo().click(seletor)
    for _ in range(40):
        j.prazo()
        if j.c.pdfs:
            break
        j.login_pg.wait_for_timeout(500)
    j.assenta()
    if not j.c.pdfs:
        raise RuntimeError("o clique em Imprimir nao abriu um PDF")
    # o headless trata o PDF como download (a navegacao e abortada): o corpo vem de um GET
    # identico com os cookies da sessao do navegador (idempotente)
    resp = j.ctx.request.get(j.c.pdfs[0])
    corpo = resp.body()
    texto = normaliza_texto(extrai_conteudo(corpo, "pdf"))
    for q in set(j.ctx.pages) - antes:
        if not q.is_closed():
            q.close()
    return {"relatorio": caminho_seguro(j.c.pdfs[0]), "status_corpo": resp.status,
            "content_type": (resp.headers.get("content-type") or "").split(";")[0],
            "e_pdf": corpo.lstrip().startswith(b"%PDF"), "conteudo": texto[:LIMITE_CONTEUDO],
            "conteudo_sha256": sha(texto)}


def _inclui(j, tabelas: list[str], botao: str, sem_horas: bool = False) -> dict:
    """Passo `salvar` generico: hash/linhas das tabelas antes e depois de clicar no botao de incluir."""
    antes = _banco_linhas(tabelas, sem_horas)
    j.c.fecha_passo()
    j.corpo().click(botao)
    j.corpo().wait_for_load_state("load")
    j.assenta()
    depois = _banco_linhas(tabelas, sem_horas)
    return {"banco": depois["hash"], "linhas_antes": antes["linhas"], "linhas_depois": depois["linhas"],
            "hash_antes": antes["hash"]}


def _f_financeiro():
    """Financeiro / Orcamento: inclui uma funcao orcamentaria (campos de uma linha `verificado` do catalogo)."""
    area, modulo, tabela = "DB:FINANCEIRO", "Orçamento", "orcamento.orcfuncao"

    def entrada(j):
        j.entra_no_modulo(area, modulo)

    def cadastro(j):
        j.abre_menu("orc1_orcfuncao001.php")

    def preenche(j):
        c = j.corpo()
        valores = {"o52_funcao": "91", "o52_descr": "TESTE_FLUXO", "o52_siconfi": "1",
                   "o52_codtri": "1", "o52_finali": "OBS_FLUXO"}  # a UI exige so digitos no codigo do tribunal
        for n, v in valores.items():
            c.fill(f"[name={n}]", v)
        j.assenta()
        return {"valores": {n: c.input_value(f"[name={n}]") for n in valores}}

    def salvar(j):
        return _inclui(j, [tabela], "input[name=db_opcao]")

    return [("entrada", entrada, False), ("tela-cadastro", cadastro, True), ("preenche", preenche, True),
            ("salvar", salvar, True)]


def _f_tributario():
    """Tributario / ISSQN: abre o formulario do relatorio de tipos de calculo e o emite (PDF)."""
    area, modulo = "DB:TRIBUTÁRIO", "ISSQN"

    def entrada(j):
        j.entra_no_modulo(area, modulo)

    def tela(j):
        j.abre_menu("iss2_tipcalc001.php")
        return {"campos": sorted(j.corpo().eval_on_selector_all("input[name]", "els => els.map(e => e.name)"))}

    def emite(j):
        return _emite_pdf(j, "#exibir_relatorio")

    return [("entrada", entrada, False), ("tela-relatorio", tela, True), ("emitir", emite, False)]


TABELAS_CGM = ["protocolo.cgm", "protocolo.cgmfisico", "protocolo.db_cgmcpf", "patrimonio.cgmendereco",
               "protocolo.personacgm"]


def _f_cadastros():
    """Cadastros / Protocolo: inclui um CGM pessoa fisica (CPF -> formulario completo -> Incluir)."""
    area, modulo = "DB:PATRIMONIAL", "Protocolo"

    def entrada(j):
        j.entra_no_modulo(area, modulo)

    def cadastro(j):
        j.abre_menu("prot1_cadcgm001.php")

    def cpf(j):
        c = j.corpo()
        c.fill("input[name=cpf]", "11144477735")
        c.click("input[name=enviar][value=Confirma]")
        c.wait_for_selector("input[name=z01_nome]")
        j.assenta()

    def preenche(j):
        c = j.corpo()
        # a regra de nome do CGM recusa "_" e nome de uma palavra ("Nome inconsistente (regra 1)")
        editaveis = {"z01_nome": "MARIA TESTE FLUXO", "z01_nomecomple": "MARIA TESTE FLUXO", "z01_numero": "1",
                     "z01_nasc": "01/01/1990"}
        # endereco/municipio/UF/bairro/CEP sao somente-leitura na UI (preenchidos por consulta de CEP/rua):
        # o fluxo os define por script, como a consulta faria
        somente_leitura = {"z01_ender": "RUA TESTE", "z01_munic": "SOUSA", "z01_uf": "PB", "z01_bairro": "CENTRO",
                           "z01_cep": "58800000",
                           # codigos de rua/bairro "NAO INFORMADO": sem eles o formulario abre a pesquisa de ruas
                           "j14_codigo": "0", "j13_codi": "0"}
        valores = {**editaveis, **somente_leitura}
        for n, v in editaveis.items():
            c.fill(f"[name={n}]", v)
        c.evaluate("(m) => { for (const [n, v] of Object.entries(m)) document.querySelector('[name='+n+']').value = v; }",
                   somente_leitura)
        c.evaluate("() => { const f = document.form1; f.z01_nasc_dia.value='01'; f.z01_nasc_mes.value='01';"
                   " f.z01_nasc_ano.value='1990'; f.z01_cadast.value='01/01/2026'; f.z01_cadast_dia.value='01';"
                   " f.z01_cadast_mes.value='01'; f.z01_cadast_ano.value='2026'; f.z01_ultalt.value='01/01/2026';"
                   " f.z01_ultalt_dia.value='01'; f.z01_ultalt_mes.value='01'; f.z01_ultalt_ano.value='2026'; }")
        c.select_option("select[name=z01_sexo]", "M")
        j.assenta()
        return {"valores": {n: c.input_value(f"[name={n}]") for n in valores}}

    def salvar(j):
        return _inclui(j, TABELAS_CGM, "input[name=db_opcao]", sem_horas=True)

    return [("entrada", entrada, False), ("tela-cadastro", cadastro, True), ("cpf", cpf, True),
            ("preenche", preenche, True), ("salvar", salvar, True)]


FLUXOS = {
    "navegacao": ("login ate sair passando por modulo, tela de cadastro e tela de relatorio", _f_navegacao),
    "incluir-registro": ("inclusao pela UI em arr1_grupotaxa001 com conferencia do efeito no banco", _f_incluir),
    "emitir-relatorio": ("emissao do relatorio cai2_relcaixa (PDF) pela UI", _f_relatorio),
    "financeiro": ("Orcamento: inclusao de funcao orcamentaria (orc1_orcfuncao001) com efeito no banco", _f_financeiro),
    "tributario": ("ISSQN: formulario e emissao do relatorio de tipos de calculo (iss2_tipcalc)", _f_tributario),
    "cadastros": ("Protocolo: inclusao de CGM pessoa fisica (prot1_cadcgm001) com efeito no banco", _f_cadastros),
}


def _roda_um(browser, proxy: str, fid: str, prazo_s: int = PRAZO_FLUXO_S) -> dict:
    descricao, fabrica = FLUXOS[fid]
    coletor = Coletor()
    passos: list[dict] = []
    quebrou: str | None = None
    j = _Janela(browser, proxy, coletor, prazo_s)
    try:
        for nome, fn, snap in fabrica():
            if quebrou:
                passos.append(_passo_vazio(nome, False, f"passo anterior falhou ({quebrou})", exercitado=False))
                continue
            try:
                j.prazo()
                extra = dict(fn(j) or {})
                banco = extra.pop("banco", None)
                dados = coletor.fecha_passo()
                p = {"nome": nome, "ok": True, "erro": None, "url": None, "dom": None, "dom_sha256": None,
                     "dom_truncado": False, **dados, "banco": banco, "extra": extra}
                if snap:
                    p.update(j.snapshot())
                else:
                    p["requisicoes"], p["runtime"] = ([], {}) if nome == "entrada" else (p["requisicoes"], p["runtime"])
                passos.append(p)
            except Exception as e:  # inclui TempoEsgotado e timeouts do Playwright
                coletor.fecha_passo()
                quebrou = f"{nome}: {_erro_curto(e)}"
                passos.append(_passo_vazio(nome, False, _erro_curto(e)))
    finally:
        j.fecha()
    return {"id": fid, "descricao": descricao, "passos": passos, "console": coletor.console, "falhas": coletor.falhas}


def versoes_navegador() -> dict:
    try:
        from importlib.metadata import version
        return {"playwright": version("playwright")}
    except Exception as e:
        return {"playwright": f"indisponivel: {type(e).__name__}"}


def executa_fluxos(proxy_url: str, ids: list[str] | None = None, versoes: dict | None = None) -> list[dict]:
    """Roda os fluxos escolhidos (padrao: todos) num unico Chromium headless; cada fluxo tem contexto proprio."""
    from playwright.sync_api import sync_playwright
    escolhidos = ids or list(FLUXOS)
    desconhecidos = [i for i in escolhidos if i not in FLUXOS]
    if desconhecidos:
        raise ValueError(f"fluxo desconhecido: {desconhecidos}; validos: {', '.join(FLUXOS)}")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        try:
            if versoes is not None:
                versoes["chromium"] = browser.version
            return [_roda_um(browser, proxy_url, fid) for fid in escolhidos]
        finally:
            browser.close()


# ------------------------------------------------------------------ gravar / comparar

RUNTIME_REFERENCIA = "PHP-7.4"  # inicio do X-Ecidade-Runtime da referencia (regressao/lab/proxy/nginx-e74.conf)


def aviso_sem_php85(runtime_observado: dict) -> str | None:
    """AVISO quando nenhuma requisicao dos fluxos foi servida pelo PHP 8.5: com o proxy mandando tudo ao 7.4, a
    rodada comparou 7.4 x 7.4 (prova a estabilidade da medicao, nao a migracao)."""
    if any("8.5" in str(v) for v in runtime_observado):
        return None
    return ("FLUXOS 7.4 x 7.4: nenhum passo veio do PHP 8.5 (X-Ecidade-Runtime); o proxy mandou tudo a referencia. "
            "Os fluxos NAO mediram a migracao: mande telas ao 8.5 em regressao/lab/proxy/map-e74.conf.")


def _fora_da_referencia(fluxos: list[dict]) -> list[str]:
    """Requisicoes principais servidas por um runtime que nao e a referencia 7.4 (`fluxo/passo caminho: runtime`)."""
    return [f"{f['id']}/{p['nome']} {caminho}: {rt}" for f in fluxos for p in f["passos"]
            for caminho, rt in sorted(p.get("runtime", {}).items()) if not str(rt).startswith(RUNTIME_REFERENCIA)]


def _dump_sha() -> str:
    from regressao.nucleo.banco import ARQ_SHA256
    return ARQ_SHA256.read_text().split()[0]


def _prepara_banco(restaurar: bool, meta: dict) -> Caso | None:
    """Confere a baseline do dump e restaura. Devolve um Caso ERRO_AMBIENTE se falhar."""
    from regressao.nucleo.banco import ARQ_DUMP, BancoDiferente, ErroAmbienteBanco, confere_baseline, restaura_dump
    try:
        confere_baseline(ARQ_DUMP)
        if restaurar:
            t0 = time.monotonic()
            restaura_dump(ARQ_DUMP)
            meta["restauracao_s"] = round(time.monotonic() - t0, 1)
    except (BancoDiferente, ErroAmbienteBanco) as e:
        return Caso("fluxo:banco", AREA, Veredito.ERRO_AMBIENTE, f"{type(e).__name__}: {e}")
    return None


def compara_fluxos(proxy_url: str, diretorio_baseline: Path, dump_sha256: str, executa=None,
                   restaurar: bool = True, ids: list[str] | None = None) -> tuple[list[Caso], dict]:
    """Caso por passo (+ `eventos` por fluxo). `executa(proxy, ids) -> list[dict]` e injetavel (testes)."""
    meta: dict = {"comparavel": restaurar, "restauracao_s": None}
    if not restaurar:
        meta["aviso"] = "banco NAO restaurado: resultado nao comparavel"
    try:
        base = carrega_baseline(diretorio_baseline, dump_sha256)
    except BaselineInvalida as e:
        return [Caso("fluxo:baseline", AREA, Veredito.ERRO_AMBIENTE, str(e))], meta
    if ids:
        base = {k: v for k, v in base.items() if k in ids}
    if executa is None:
        falha = _prepara_banco(restaurar, meta)  # confere o dump e (se pedido) restaura
        if falha:
            return [falha], meta
        versoes = versoes_navegador()
        meta["versoes"] = versoes
        executa = lambda proxy, i: executa_fluxos(proxy, i, versoes)  # noqa: E731
    try:
        atuais = {f["id"]: f for f in executa(proxy_url, list(base))}
    except Exception as e:
        return [Caso("fluxo:execucao", AREA, Veredito.ERRO_AMBIENTE, f"{type(e).__name__}: {e}"[:400])], meta
    casos: list[Caso] = []
    for fid, b in base.items():
        if fid not in atuais:
            casos.append(Caso(f"fluxo:{fid}:execucao", AREA, Veredito.INCONCLUSIVO, "fluxo nao executado nesta rodada"))
        else:
            casos += compara_fluxo(b, atuais[fid])
    meta["runtime_observado"] = dict(Counter(v for f in atuais.values() for p in f["passos"]
                                            for v in p["runtime"].values()))
    meta["cobertura"] = {"fluxos": len(atuais), "passos": sum(len(f["passos"]) for f in atuais.values()),
                         "passos_ok": sum(1 for f in atuais.values() for p in f["passos"] if p.get("ok")),
                         "ids": sorted(atuais)}
    return casos, meta


def roda_fluxos(proxy_url: str, restaurar: bool = True, ids: list[str] | None = None) -> list[Caso]:
    """Compara os fluxos de navegador com a baseline e devolve os Casos (interface do plano)."""
    try:
        sha_dump = _dump_sha()
    except Exception as e:
        return [Caso("fluxo:baseline", AREA, Veredito.ERRO_AMBIENTE, f"dump_sha256 indisponivel: {e}")]
    return compara_fluxos(proxy_url, DIR_BASELINE, sha_dump, restaurar=restaurar, ids=ids)[0]


def _meta_base() -> dict:
    meta = {"git_commit": git.commit(RAIZ)}
    meta.update(git.sujo(RAIZ))
    meta.update(git.sujo_regressao(RAIZ))
    try:
        meta["baseline_sha256"] = _dump_sha()
    except Exception as e:
        meta["baseline_sha256"] = f"indisponivel: {type(e).__name__}"
    return meta


def roda_fluxos_rodada(diretorio_saida: Path, proxy_url: str | None = None, restaurar: bool = True,
                       ids: list[str] | None = None) -> int:
    """Modo `comparar` completo: escreve a rodada (resultado.json, resumo.md, diffs/) e devolve o codigo de saida."""
    from regressao.nucleo.ambiente import _responde, alvos_do_ambiente
    from regressao.nucleo.veredito import codigo_saida
    from regressao.php.bateria import _fim
    proxy = proxy_url or alvos_do_ambiente().proxy
    inicio = time.monotonic()
    meta: dict = {"modo": "comparar", "proxy": proxy, **_meta_base()}
    avisos: list[str] = []
    try:
        sha_dump = _dump_sha()
    except Exception as e:
        sha_dump = ""
        meta["baseline_sha256"] = f"indisponivel: {e}"
    if not _responde(proxy):
        casos = [Caso("fluxo:ambiente", AREA, Veredito.ERRO_AMBIENTE, f"proxy sem resposta em 5s: {proxy}")]
        meta["comparavel"] = False
    else:
        casos, extra = compara_fluxos(proxy, DIR_BASELINE, sha_dump, restaurar=restaurar, ids=ids)
        meta.update(extra)
        if extra.get("aviso"):
            avisos.append(extra["aviso"])
        if "runtime_observado" in extra and (a := aviso_sem_php85(extra["runtime_observado"])):
            avisos.append(a)
    meta["tempo_total_s"] = round(time.monotonic() - inicio, 1)
    meta["banco_apos_a_rodada"] = "SUJO por construcao (registro de teste em grupotaxa, sessoes); a proxima bateria restaura"
    if any(c.veredito == Veredito.INCONCLUSIVO for c in casos):
        avisos.append("ha passos INCONCLUSIVO: NAO sao aprovacao (nao foram exercitados)")
    for c in casos:
        if c.veredito == Veredito.ERRO_AMBIENTE:
            avisos.append(f"ERRO_AMBIENTE {c.id}: {(c.detalhe or '').splitlines()[0][:200] if c.detalhe else ''}")
    if (inf := [c for c in casos if "INFO runtime" in (c.detalhe or "")]):
        avisos.append(f"{len(inf)} passo(s) com X-Ecidade-Runtime diferente da baseline (INFORMACAO, nao e falha)")
    return _fim(Path(diretorio_saida), casos, meta, avisos)


def grava_fluxos(diretorio_saida: Path, proxy_url: str | None = None, restaurar: bool = True,
                 ids: list[str] | None = None, confirmo_sobrescrever: bool = False) -> int:
    from regressao.nucleo.ambiente import _responde, alvos_do_ambiente
    proxy = proxy_url or alvos_do_ambiente().proxy
    existe = DIR_BASELINE.is_dir() and any(DIR_BASELINE.glob("*.json"))
    if existe and not confirmo_sobrescrever:
        raise RecusaBaseline(f"gravar recusado: {DIR_BASELINE} ja tem baseline de fluxos. Ela e a referencia "
                             "pre-migracao; sobrescreve-la com um sistema migrado destroi a comparacao. "
                             "Use --confirmo-sobrescrever se tem certeza.")
    if not restaurar:
        raise ValueError("--sem-restaurar nao vale para gravar: a baseline nasce de banco restaurado")
    if not _responde(proxy):
        print(f"erro: proxy sem resposta em 5s: {proxy}", file=sys.stderr)
        return 2
    meta: dict = {}
    falha = _prepara_banco(True, meta)
    if falha:
        print(f"erro: {falha.detalhe}", file=sys.stderr)
        return 2
    versoes = versoes_navegador()
    atuais = executa_fluxos(proxy, ids, versoes)
    quebrados = [(f["id"], p["nome"], p["erro"]) for f in atuais for p in f["passos"] if not p["ok"]]
    if quebrados:
        print(f"erro: passos falharam na gravacao; baseline NAO gravada: {quebrados}", file=sys.stderr)
        return 2
    if fora := _fora_da_referencia(atuais):
        print(f"erro: a baseline so nasce da referencia {RUNTIME_REFERENCIA}; {len(fora)} requisicao(oes) vieram de "
              f"outro runtime (X-Ecidade-Runtime); baseline NAO gravada. Volte o proxy (map-e74.conf) para o 7.4: "
              f"{fora[:10]}", file=sys.stderr)
        return 2
    grava_baseline(DIR_BASELINE, atuais, _dump_sha(), git.commit(RAIZ), completo=ids is None)
    d = Path(diretorio_saida)
    d.mkdir(parents=True, exist_ok=True)
    (d / "gravacao.json").write_text(json.dumps({"fluxos": [f["id"] for f in atuais], "restauracao_s": meta.get("restauracao_s"),
                                                 "versoes": versoes, "passos": {f["id"]: [p["nome"] for p in f["passos"]]
                                                                              for f in atuais}},
                                                indent=1), encoding="utf-8", newline="\n")
    print(f"baseline de fluxos gravada em {DIR_BASELINE}: {[f['id'] for f in atuais]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m regressao.completa.fluxos", description=__doc__.split("\n")[0])
    ap.add_argument("modo", choices=("gravar", "comparar"))
    ap.add_argument("--saida", required=True, type=Path)
    ap.add_argument("--proxy", default=None, metavar="URL")
    ap.add_argument("--fluxo", action="append", default=None, metavar="ID", help=f"repetivel; validos: {', '.join(FLUXOS)}")
    ap.add_argument("--confirmo-sobrescrever", action="store_true")
    ap.add_argument("--sem-restaurar", action="store_true", help="SO desenvolvimento: resultado nao comparavel")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    try:
        if a.modo == "gravar":
            return grava_fluxos(a.saida, a.proxy, not a.sem_restaurar, a.fluxo, a.confirmo_sobrescrever)
        return roda_fluxos_rodada(a.saida, a.proxy, not a.sem_restaurar, a.fluxo)
    except ValueError as e:  # RecusaBaseline, fluxo desconhecido, --sem-restaurar em gravar
        print(f"erro: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
