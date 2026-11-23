"""Mascara de campos volateis em JSON para comparar respostas de API."""
import copy
import json
import re

MARCA = "<X>"


def _aplica(no, partes):
    if not partes:
        return MARCA
    p, resto = partes[0], partes[1:]
    if p == "*":
        if isinstance(no, list):
            return [_aplica(x, resto) for x in no]
        return no
    if isinstance(no, dict) and p in no:
        no[p] = _aplica(no[p], resto)
    return no


def _ordena(no):
    if isinstance(no, dict):
        return {k: _ordena(no[k]) for k in sorted(no, key=str)}
    if isinstance(no, list):
        return [_ordena(x) for x in no]
    return no


# --- Mascara de ERRO, aplicada so na COMPARACAO (a baseline em disco guarda o registro bruto) --------
# Erros do Laravel em modo debug trazem file/line/trace/stacktrace absolutos do servidor: num Laravel 12 em
# outro caminho eles sempre diferem sem que a API tenha mudado. Escopo ESTREITO (revisao):
#  - so em RESPOSTAS DE ERRO (ver `e_resposta_de_erro`: status >= 400 ou objeto com `exception`);
#  - os campos file/line/trace/stacktrace so em objetos com cara de erro: tem `exception`/`trace`/`stacktrace`
#    ou o envelope do app (`error: true`); um objeto de negocio {message, file, line} NAO e tocado;
#  - caminhos absolutos so com RAIZ conhecida do servidor (/var/www/html, /var/www, /app, /srv/<x>) seguida de
#    vendor|app|bootstrap|storage|... : URLs como /storage/a.pdf ou /public/x.png nunca casam.
# `exception` (classe) e `message` continuam comparados: mudar a excecao e DIVERGE real. Nao se aplica a
# sql_negocio, cabecalhos nem a texto de resposta de sucesso.
CAMPOS_DE_ERRO = ("file", "line", "trace", "stacktrace", "stack_trace")
_SINAIS_DE_ERRO = ("exception", "trace", "stacktrace", "stack_trace")
_RE_CAMINHO = re.compile(
    r"(?<![\w:/.@-])(?:/var/www/html|/var/www|/app|/srv/[\w.@-]+)"
    r"/(?:vendor|app|bootstrap|storage|ecidade|libs|model|classes|dbforms|public)/[^\s\"'),;]*?"
    r"(?:\.php)?(?::\d+)?(?=[\s\"'),;]|$)")
_RE_NA_LINHA = re.compile(r"\bon line \d+")


def _texto(s: str) -> str:
    return _RE_NA_LINHA.sub("on line <N>", _RE_CAMINHO.sub("<caminho>", s))


def e_resposta_de_erro(status: int, json_) -> bool:
    return status >= 400 or (isinstance(json_, dict) and "exception" in json_)


def _tem_cara_de_erro(obj: dict) -> bool:
    return any(k in obj for k in _SINAIS_DE_ERRO) or obj.get("error") is True


def normaliza_erro(obj):
    """Copia de `obj` sem file/line/trace de erro e com caminhos absolutos (raiz conhecida) normalizados."""
    if isinstance(obj, str):
        return _texto(obj)
    if isinstance(obj, list):
        return [normaliza_erro(x) for x in obj]
    if isinstance(obj, dict):
        erro = _tem_cara_de_erro(obj)
        return {k: (MARCA if erro and k in CAMPOS_DE_ERRO else normaliza_erro(v)) for k, v in obj.items()}
    return obj


def _ordena_em(no, partes):
    if not partes or partes == [""]:
        if isinstance(no, list):
            return sorted(no, key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
        return no
    p, resto = partes[0], partes[1:]
    if p == "*":
        return [_ordena_em(x, resto) for x in no] if isinstance(no, list) else no
    if isinstance(no, dict) and p in no:
        no[p] = _ordena_em(no[p], resto)
    return no


def ordena_listas(obj, caminhos: list[str]):
    """Copia de `obj` com as listas nos caminhos dados (pontos; `*` = cada elemento; "" = a raiz) ordenadas pelo
    JSON canonico de cada item. Para APIs que NAO prometem ordem (ex.: `select ... from pg_views` sem ORDER BY):
    compara o CONJUNTO (com repeticoes) em vez da ordem acidental do banco. Caminho ausente e ignorado."""
    novo = copy.deepcopy(obj)
    for caminho in caminhos:
        novo = _ordena_em(novo, caminho.split(".") if caminho else [""])
    return novo


def mascara_json(obj, campos_volateis: list[str]):
    """Copia `obj` trocando por "<X>" os valores nos caminhos dados (pontos; `*` = cada
    elemento de lista) e ordenando as chaves recursivamente. Caminhos ausentes sao
    ignorados; a entrada nao e alterada."""
    novo = copy.deepcopy(obj)
    for caminho in campos_volateis:
        novo = _aplica(novo, caminho.split("."))
    return _ordena(novo)