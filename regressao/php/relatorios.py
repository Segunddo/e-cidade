import csv
import difflib
import hashlib
import io
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import ErroAmbienteBanco
from regressao.nucleo.normaliza import normaliza
from regressao.nucleo.veredito import Caso, Veredito
from regressao.php.telas import _requisita_status, corpo_de_sessao_invalida, restaura_sessao

CATALOGO = Path(__file__).resolve().parent / "catalogo_relatorios.tsv"
TIPOS = ("html", "pdf", "xls", "doc")
LIMITE_DIFF = 200
# Referencia (PHP 7.4) e alvo (PHP 8.5) enxergam o mesmo volume de sessoes e /tmp; cada um recebe a
# requisicao na propria porta 80, de dentro do container (nomes em regressao/nucleo/ambiente.py).
ROTULO_REF = "ref (7.4)"
ROTULO_NOVO = "8.5"

# Pagina de erro do PHP (display_errors) identica nos dois runtimes: nao e relatorio.
_ERRO_PHP = re.compile(r"(?:Fatal error|Parse error|Uncaught \w*(?:Error|Exception)"
                       r"|Notifica\S+ do Sistema|Erro interno)", re.I)
_PDF_ILEGIVEL = "<<pdf ilegivel"


@dataclass
class RelCaso:
    tela: str
    query: str
    tipo: str  # "html" | "pdf" | "xls" | "doc"
    area: str
    verificado: bool = False

    @property
    def url(self) -> str:
        return f"{self.tela}?{self.query}" if self.query else self.tela


def carrega_catalogo_relatorios(tsv: Path) -> list[RelCaso]:
    """TSV `tela<TAB>query<TAB>tipo<TAB>area<TAB>status` (status obrigatorio: `verificado` ou
    `nao-verificado`; outro valor ou ausente -> ValueError). `query` pode ser vazia; `tipo` e
    html|pdf|xls|doc. Ignora linhas em branco e as que comecam com '#'."""
    casos = []
    for n, linha in enumerate(Path(tsv).read_text(encoding="utf-8").splitlines(), 1):
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        col = linha.split("\t")
        tela, query, tipo, area, status = (c.strip() for c in col[:5]) if len(col) >= 5 else ("",) * 5
        if (not (tela and area) or not tela.endswith(".php") or tipo not in TIPOS
                or status not in ("verificado", "nao-verificado")):
            raise ValueError(f"{tsv}: linha {n} malformada (esperado tela.php<TAB>query<TAB>html|pdf|xls|doc"
                             f"<TAB>area<TAB>verificado|nao-verificado): {linha[:80]!r}")
        casos.append(RelCaso(tela, query, tipo, area, status == "verificado"))
    return casos


# Rodape do PDF do e-cidade (fpdf151/pdf.php): "Data: 14-11-2026 - 20:01:54 Pag 1/1". O horario
# da emissao muda de uma requisicao a outra (observado ao vivo: cem2_renovacoes, com2_pcgrupo002).
_HORA_EMISSAO = re.compile(r"Data: \d{2}-\d{2}-\d{4} - \d{2}:\d{2}:\d{2}(?=\s+P[aá]g\s+\d+/\d+\s*$)")


def _texto_pdf(corpo: bytes) -> str:
    """Texto por pagina; so as paginas com texto entram. Metadados (CreationDate, Producer, ids)
    nunca sao lidos."""
    from pypdf import PdfReader
    try:
        paginas = [(p.extract_text() or "") for p in PdfReader(io.BytesIO(corpo)).pages]
    except Exception as e:  # pdf corrompido/truncado: compara pelos bytes normalizados
        return f"{_PDF_ILEGIVEL} ({type(e).__name__}) sha256={hashlib.sha256(normaliza(corpo)).hexdigest()}>>"
    saida = []
    for n, texto in enumerate(paginas, 1):
        linhas = [_HORA_EMISSAO.sub("Data: X", l.rstrip()) for l in texto.splitlines() if l.strip()]
        if linhas:
            saida.append(f"=== pagina {n} ===\n" + "\n".join(linhas))
    return "\n".join(saida)


def _celulas_xlsx(corpo: bytes) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(corpo), data_only=True)
    saida = []
    for ws in wb.worksheets:
        for r, linha in enumerate(ws.iter_rows(values_only=True), 1):
            for c, v in enumerate(linha, 1):
                if v is not None and str(v) != "":
                    saida.append(f"{ws.title}|{r}|{c}|{v}")
    return "\n".join(saida)


def _celulas_xls_binario(corpo: bytes) -> str:
    import xlrd
    wb = xlrd.open_workbook(file_contents=corpo)
    saida = []
    for ws in wb.sheets():
        for r in range(ws.nrows):
            for c in range(ws.ncols):
                v = ws.cell_value(r, c)
                if v != "":
                    saida.append(f"{ws.name}|{r + 1}|{c + 1}|{v}")
    return "\n".join(saida)


def _celulas_csv(texto: str) -> str:
    primeira = texto.splitlines()[0] if texto.strip() else ""
    delim = max(";,\t", key=primeira.count)
    saida = []
    for r, linha in enumerate(csv.reader(io.StringIO(texto), delimiter=delim), 1):
        for c, v in enumerate(linha, 1):
            if v.strip():
                saida.append(f"csv|{r}|{c}|{v.strip()}")
    return "\n".join(saida)


def _html(corpo: bytes) -> str:
    return normaliza(corpo).decode("latin-1").strip()


def extrai_conteudo(corpo: bytes, tipo: str) -> str:
    """Conteudo comparavel, sempre a partir de bytes (LATIN-1 nunca e lido como UTF-8).
    pdf -> texto por pagina (sem metadados); xls -> `sheet|linha|coluna|valor` por celula
    (xlsx via openpyxl, xls binario via xlrd; o que o e-cidade serve como "excel" costuma ser
    tabela HTML ou CSV, tratados como html e como celulas csv|linha|coluna|valor);
    html/doc -> normaliza(corpo) em latin-1. "" significa "sem dados"."""
    if tipo == "pdf":
        return _texto_pdf(corpo) if corpo.lstrip().startswith(b"%PDF") else _html(corpo)
    if tipo == "xls":
        if corpo.startswith(b"PK\x03\x04"):
            return _celulas_xlsx(corpo)
        if corpo.startswith(b"\xd0\xcf\x11\xe0"):
            return _celulas_xls_binario(corpo)
        texto = normaliza(corpo).decode("latin-1")
        return _html(corpo) if texto.lstrip().startswith("<") else _celulas_csv(texto)
    if tipo in ("html", "doc"):
        return _html(corpo)
    raise ValueError(f"tipo de relatorio desconhecido: {tipo!r}")


def _diff(a: str, b: str) -> str:
    linhas = list(difflib.unified_diff(a.splitlines(), b.splitlines(), ROTULO_REF, ROTULO_NOVO, lineterm="", n=1))
    if len(linhas) > LIMITE_DIFF:
        resto = len(linhas) - LIMITE_DIFF
        linhas = linhas[:LIMITE_DIFF] + [f"... ({resto} linhas omitidas)"]
    return "\n".join(linhas)


def compara_relatorio(corpo_ref: bytes, corpo85: bytes, caso: RelCaso,
                      status_ref: int = 200, status85: int = 200) -> Caso:
    """corpo_ref/status_ref = referencia (PHP 7.4, o gabarito); corpo85/status85 = alvo PHP 8.5."""
    id_ = caso.url
    if corpo_de_sessao_invalida(corpo_ref) or corpo_de_sessao_invalida(corpo85):
        return Caso(id_, caso.area, Veredito.ERRO_AMBIENTE, "sessao invalida (pagina 'Sessao invalida')")
    if status_ref != status85:  # ex.: ref=200 (PDF) e 8.5=500 (pagina de erro): a regressao a detectar
        try:
            c_ref, c85 = extrai_conteudo(corpo_ref, caso.tipo), extrai_conteudo(corpo85, caso.tipo)
        except Exception:
            c_ref, c85 = corpo_ref[:300].decode("latin-1"), corpo85[:300].decode("latin-1")
        return Caso(id_, caso.area, Veredito.DIVERGE,
                    f"codigo HTTP diverge: ref={status_ref} 8.5={status85}; "
                    f"inicio ref={corpo_ref[:60]!r} 8.5={corpo85[:60]!r}", _diff(c_ref, c85))
    if status_ref != 200:
        return Caso(id_, caso.area, Veredito.INCONCLUSIVO, f"nao exercitado: ambos {status_ref}")
    pdf_ref, pdf85 = (c.lstrip().startswith(b"%PDF") for c in (corpo_ref, corpo85))
    if caso.tipo == "pdf" and not (pdf_ref or pdf85):
        return Caso(id_, caso.area, Veredito.INCONCLUSIVO, "esperava PDF e nenhum dos lados devolveu PDF")
    try:
        c_ref, c85 = extrai_conteudo(corpo_ref, caso.tipo), extrai_conteudo(corpo85, caso.tipo)
    except Exception as e:  # xlsx/xls corrompido etc.: o conteudo nao pode ser lido, nao e aprovado
        return Caso(id_, caso.area, Veredito.INCONCLUSIVO, f"conteudo ilegivel ({type(e).__name__}: {e})")
    ileg_ref, ileg85 = c_ref.startswith(_PDF_ILEGIVEL), c85.startswith(_PDF_ILEGIVEL)
    if ileg_ref and ileg85:
        return Caso(id_, caso.area, Veredito.INCONCLUSIVO, "pdf ilegivel nos dois lados")
    if c_ref == c85:
        if not c_ref:
            return Caso(id_, caso.area, Veredito.INCONCLUSIVO, "sem dados (relatorio vazio) nos dois lados")
        if not pdf_ref and _ERRO_PHP.search(c_ref):
            return Caso(id_, caso.area, Veredito.INCONCLUSIVO, "pagina de erro identica nos dois lados; nao e relatorio")
        return Caso(id_, caso.area, Veredito.IDENTICO)
    return Caso(id_, caso.area, Veredito.DIVERGE, f"conteudo diverge ({len(c_ref)} vs {len(c85)} caracteres)",
                _diff(c_ref, c85))


def roda_relatorio(sid: str, caso: RelCaso) -> Caso:
    """GET com a query nos dois runtimes (referencia PHP 7.4 e alvo PHP 8.5, cada um pela porta 80 do
    proprio container), com a sessao restaurada antes de CADA requisicao: cada requisicao
    consome/reescreve a sessao, como no cmp.py. Os codigos HTTP dos dois lados entram na
    comparacao."""
    conts = containers_do_ambiente()
    try:
        respostas = []
        for container in (conts.ref, conts.php_novo):
            restaura_sessao(sid)
            respostas.append(_requisita_status(sid, caso.url, container))
    except (ErroAmbienteBanco, OSError, subprocess.TimeoutExpired) as e:
        return Caso(caso.url, caso.area, Veredito.ERRO_AMBIENTE,
                    ("" if caso.verificado else "[nao-verificado] ") + str(e))
    (s_ref, b_ref), (s85, b85) = respostas
    if 0 in (s_ref, s85):
        return Caso(caso.url, caso.area, Veredito.ERRO_AMBIENTE,
                    ("" if caso.verificado else "[nao-verificado] ") +
                    f"resposta sem codigo HTTP (truncada ou curl falhou): ref={s_ref} 8.5={s85}")
    resultado = compara_relatorio(b_ref, b85, caso, s_ref, s85)
    if not caso.verificado:
        resultado.detalhe = ("[nao-verificado] " + resultado.detalhe).rstrip()
    return resultado
