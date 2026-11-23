"""Catalogo de padroes legados (PHP 7.4 -> 8.5 e Laravel 8 -> 13) usados por `buscar_codigo_legado`,
`proximo_trabalho` e `padroes_ja_corrigidos`.

Cada padrao e uma regex (ou um detector em Python, quando regex nao basta) sobre o TEXTO do arquivo. E
heuristica estatica: acha candidatos, nao prova bug. Comentarios e strings tambem casam.

Severidade (guia do grupo "Migracao 7.4 -> 8.5", 18/11/2026): `quebra_8_5` (nao compila ou da erro fatal ao rodar),
`silenciosa` (nao da erro, da resultado diferente), `obsoleto` (aviso de deprecated; funciona no 8.5) e `laravel`
(muda no caminho Laravel 8 -> 13). Ordem de trabalho: nao compila no 8.5 > quebra em execucao > silencioso >
obsoleto > laravel; dentro de cada faixa, `prioridade`.
"""
from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# chamada de FUNCAO global: nao metodo (->, ::), nao variavel, nao sufixo de outro nome, nao definicao
FN = r"(?<![\w$>:\\.])(?<!function )"


@dataclass(frozen=True)
class Padrao:
    nome: str
    titulo: str
    alvo: str          # php | laravel
    origem: str        # em que versao quebrou/depreciou
    correcao: str
    exemplo_antes: str
    exemplo_depois: str
    mecanico: str      # sim | semi | nao
    confianca: str     # alta | media | baixa (taxa de falso positivo)
    prioridade: int    # menor = antes
    regex: str | None = None
    flags: int = 0
    detector: Callable[[str], list[int]] | None = field(default=None, compare=False)
    filtro: tuple[str, ...] = ()  # substrings: arquivo sem nenhuma delas e pulado (velocidade)
    ruidoso: bool = False  # fora de 'todos' (milhares de ocorrencias ou muito falso positivo)
    severidade: str = ""   # quebra_8_5 | silenciosa | obsoleto | laravel (preenchido em _SEVERIDADE)
    nao_compila: bool = False  # erro de COMPILACAO no 8.5 (php -l falha): topo da fila
    so_em: Callable[[str], bool] | None = field(default=None, compare=False)  # filtro pelo caminho relativo

    def como_dict(self) -> dict[str, Any]:
        return {
            "nome": self.nome, "titulo": self.titulo, "alvo": self.alvo, "origem": self.origem,
            "correcao": self.correcao, "exemplo_antes": self.exemplo_antes, "exemplo_depois": self.exemplo_depois,
            "mecanico": self.mecanico, "confianca": self.confianca, "prioridade": self.prioridade,
            "ruidoso": self.ruidoso, "severidade": self.severidade, "nao_compila": self.nao_compila,
            "apelidos": sorted(a for a, n in APELIDOS.items() if n == self.nome),
        }


# ---------- detectores ----------

def _conta_args(texto: str, i: int, limite: int = 5000) -> int | None:
    """Numero de argumentos da chamada cujo '(' termina em i-1 (respeita strings e parenteses)."""
    prof, n, vazio, j, fim = 0, 1, True, i, min(len(texto), i + limite)
    while j < fim:
        ch = texto[j]
        if ch in "'\"":
            vazio = False
            j += 1
            while j < fim and texto[j] != ch:
                j += 2 if texto[j] == "\\" else 1
        elif ch in "([{":
            prof += 1
            vazio = False
        elif ch in ")]}":
            if prof == 0:
                return 0 if vazio else n
            prof -= 1
        elif ch == "," and prof == 0:
            n += 1
        elif not ch.isspace():
            vazio = False
        j += 1
    return None


_PARSE_STR = re.compile(FN + r"(?:mb_)?parse_str\s*\(")


def _parse_str_1_arg(texto: str) -> list[int]:
    return [m.start() for m in _PARSE_STR.finditer(texto) if _conta_args(texto, m.end()) == 1]


_CLASSE = re.compile(r"(?m)^[ \t]*(?:(?:abstract|final)\s+)?class\s+([A-Za-z_]\w*)")
_FUNCAO = re.compile(r"function\s+&?\s*([A-Za-z_]\w*)\s*\(")


_NAMESPACE = re.compile(r"^\s*namespace\s+[\w\\]+\s*[;{]", re.M)


def _construtor_php4(texto: str) -> list[int]:
    # em classe com namespace o metodo de mesmo nome JA nao era construtor no 7.4: nada muda no 8.5
    if _NAMESPACE.search(texto):
        return []
    classes = list(_CLASSE.finditer(texto))
    achados = []
    for k, m in enumerate(classes):
        fim = classes[k + 1].start() if k + 1 < len(classes) else len(texto)
        metodos: dict[str, int] = {}
        for f in _FUNCAO.finditer(texto, m.end(), fim):
            metodos.setdefault(f.group(1).lower(), f.start())
        nome = m.group(1).lower()
        if nome in metodos and "__construct" not in metodos:
            achados.append(metodos[nome])
    return achados


# ---------- catalogo ----------

CATALOGO: tuple[Padrao, ...] = (
    Padrao(
        "parse_str_1_arg", "parse_str()/mb_parse_str() com 1 argumento", "php",
        "depreciado no 7.2, REMOVIDO no 8.0: ArgumentCountError (tela 500). Causa n.1 da triagem antiga (~560 telas, "
        "~2.500 func_*)",
        "Use a forma de 2 argumentos e jogue as variaveis no escopo, como os ~3.800 arquivos ja corrigidos do "
        "repositorio. Filtre 'this' e 'GLOBALS' antes do extract (no 8.x `?this=1` vira erro fatal). "
        "`parse_str(x, $_GET)` NAO serve: as telas leem as variaveis locais.",
        "parse_str(base64_decode($HTTP_SERVER_VARS['QUERY_STRING']));",
        "parse_str(base64_decode($HTTP_SERVER_VARS['QUERY_STRING']), $__qs);\n"
        "unset($__qs['this'], $__qs['GLOBALS']);\nextract($__qs);",
        "sim", "alta", 10, detector=_parse_str_1_arg, filtro=("parse_str",),
    ),
    Padrao(
        "construtor_php4", "construtor estilo PHP 4 (metodo com o nome da classe, sem __construct)", "php",
        "depreciado no 7.0; no 8.0 deixa de ser construtor: propriedades ficam nulas "
        "(`Call to a member function label() on null` nos forms). Causa n.2 (~600 classes db_*_classe.php)",
        "Renomeie o metodo para __construct (mesmo corpo). Se algum codigo chamar o nome antigo "
        "(`parent::cl_x()`, `$this->cl_x()`), troque por `parent::__construct()`.",
        "class cl_tabela {\n  function cl_tabela() {\n    $this->rotulo = new rotulo('tabela');\n  }\n}",
        "class cl_tabela {\n  function __construct() {\n    $this->rotulo = new rotulo('tabela');\n  }\n}",
        "sim", "alta", 20, detector=_construtor_php4, filtro=("class",),
    ),
    Padrao(
        "split", "split() (extensao ereg)", "php",
        "REMOVIDO no 7.0 (ja quebra na referencia 7.4: `Call to undefined function split()`). 2a camada escondida "
        "em ~190 telas e nos 5 balancetes",
        "JA QUEBRA NA REFERENCIA 7.4: pela regra do grupo (funciona igual ao 7.4 / so atualizar) registre e avise o "
        "dono; nao corrija na migracao sem decisao do grupo. A base-php84 cobria com funcao de compatibilidade: NAO "
        "copie so para um lado (o guia: 'nao, se a mesma funcao estiver no 7.4 e no 8.5'). Se o grupo decidir "
        "corrigir: separador literal -> `explode`; separador regex -> `preg_split`; mantenha o limite.",
        "$partes = split(\"-\", $db_selinstit);", "(registrar; se o grupo decidir: explode(\"-\", $db_selinstit))",
        "nao", "alta", 30, regex=FN + r"split\s*\(", filtro=("split",),
    ),
    Padrao(
        "each", "each()", "php",
        "depreciado no 7.2, REMOVIDO no 8.0 (Call to undefined function each())",
        "Troque o `while (list($k, $v) = each($arr))` por `foreach ($arr as $k => $v)`. Cuidado se o laco depende "
        "do ponteiro interno (reset/next) ou altera o array durante o laco.",
        "while (list($k, $v) = each($arr)) { ... }", "foreach ($arr as $k => $v) { ... }",
        "semi", "alta", 31, regex=FN + r"each\s*\(", filtro=("each",),
    ),
    Padrao(
        "ereg", "ereg*/eregi*/spliti/sql_regcase", "php",
        "REMOVIDOS no 7.0 (ja quebram na referencia 7.4)",
        "JA QUEBRA NA REFERENCIA 7.4: registre e avise o dono (regra 'so atualizar'). Se o grupo decidir corrigir: "
        "preg_* com delimitador e o modificador i quando era eregi.",
        "if (ereg('^[0-9]+$', $x)) { ... }", "(registrar; se o grupo decidir: preg_match('/^[0-9]+$/', $x))",
        "nao", "alta", 32, regex=FN + r"(?:eregi?_replace|eregi?|spliti|sql_regcase)\s*\(",
        filtro=("ereg", "spliti", "sql_regcase"),
    ),
    Padrao(
        "create_function", "create_function()", "php",
        "depreciado no 7.2, REMOVIDO no 8.0",
        "Troque por closure (`function (...) use (...) { ... }`); o codigo em string vira codigo de verdade.",
        "$f = create_function('$a', 'return $a * 2;');", "$f = function ($a) { return $a * 2; };",
        "semi", "alta", 33, regex=FN + r"create_function\s*\(", filtro=("create_function",),
    ),
    Padrao(
        "removidas_php8", "funcoes removidas (money_format, magic_quotes, fgetss, mysql_*, mcrypt_*, ...)", "php",
        "removidas no 7.0 (mysql_*), 7.2 (mcrypt_*) ou 8.0 (money_format, get_magic_quotes_*, fgetss, hebrevc, "
        "convert_cyr_string, restore_include_path, ezmlm_hash, image2wbmp, is_real, __autoload)",
        "money_format -> NumberFormatter/number_format; get_magic_quotes_gpc() -> false; fgetss -> "
        "strip_tags(fgets()); is_real -> is_float; mysql_* -> pg_*/PDO; __autoload -> spl_autoload_register.",
        "if (get_magic_quotes_gpc()) { $x = stripslashes($x); }", "// magic quotes nao existem desde o 5.4: remova",
        "semi", "alta", 34,
        regex=FN + r"(?:money_format|get_magic_quotes_(?:gpc|runtime)|set_magic_quotes_runtime|fgetss|gzgetss|"
                   r"hebrevc|convert_cyr_string|restore_include_path|ezmlm_hash|image2wbmp|is_real|mysql_\w+|"
                   r"mcrypt_\w+)\s*\(|\bfunction\s+__autoload\s*\(",
    ),
    Padrao(
        "chaves_offset_string", "acesso a offset com chaves ($str{0})", "php",
        "depreciado no 7.4, REMOVIDO no 8.0: erro de COMPILACAO (php -l falha)",
        "Use colchetes: $str[0].", "$c = $str{0};", "$c = $str[0];",
        "sim", "media", 35, regex=r"(?<![\w\"'{$\\])\$[A-Za-z_]\w*\{(?:\d+|\$[A-Za-z_]\w*)\}",
    ),
    Padrao(
        "pg_resultado_false", "pg_num_rows/pg_numrows/pg_fetch_* direto sobre db_query()/pg_query()", "php",
        "no 8.0 pg_* com `false` (consulta que falhou) levanta TypeError: `pg_numrows(): Argument #1 must be of "
        "type PgSql\\Result, false given`. No 7.4 era so warning e a tela seguia vazia",
        "Decisao 2a (19/11/2026): reproduzir o 7.4, que devolvia null (aviso escondido) e a tela seguia vazia. Os "
        "wrappers centrais (db_fieldsmemory, db_lovrot, db_utils::fieldsMemory/getCollectionByRecord...) ja fazem "
        "isso; fora deles, guarde o resultado e devolva o mesmo null: `$rs ? pg_num_rows($rs) : null`. Mostrar "
        "erro claro e mudanca de comportamento (opcao b, fora da migracao).",
        "$n = pg_numrows(db_query($sql));",
        "$rs = db_query($sql);\n$n = $rs ? pg_numrows($rs) : null; // como o 7.4: null quando a consulta falha",
        "nao", "media", 40,
        regex=FN + r"pg_(?:num_?rows|num_?fields|fetch_\w+|result|affected_rows|free_result)\s*\(\s*@?\s*"
                   r"(?:db_query|pg_query|pg_exec|pg_query_params)\s*\(",
        filtro=("pg_",),
    ),
    Padrao(
        "is_resource_pgsql", "is_resource() sobre resultado/conexao do PostgreSQL", "php",
        "no 8.1 as funcoes pg_* devolvem objetos (PgSql\\Connection, PgSql\\Result): is_resource() passa a dar "
        "false e o codigo toma o caminho de erro. Tambem casa com arquivos (fopen), que continuam resource",
        "Para pgsql: troque `is_resource($rs)` por `$rs !== false` (ou `$rs instanceof \\PgSql\\Result`). "
        "Para fopen/curl, confira caso a caso.",
        "if (!is_resource($rs)) { return false; }", "if ($rs === false) { return false; }",
        "semi", "media", 41, regex=FN + r"is_resource\s*\(", filtro=("is_resource",),
    ),
    Padrao(
        "reflection_getclass", "ReflectionParameter::getClass()", "php",
        "depreciado no 8.0 (a triagem antiga achou a mensagem em con2_anexovirgf_002)",
        "Use getType(): `$t = $p->getType(); $classe = ($t instanceof ReflectionNamedType && !$t->isBuiltin()) ? "
        "new ReflectionClass($t->getName()) : null;`",
        "$classe = $parametro->getClass();",
        "$t = $parametro->getType();\n$classe = ($t instanceof ReflectionNamedType && !$t->isBuiltin())\n"
        "    ? new ReflectionClass($t->getName()) : null;",
        "semi", "media", 42, regex=r"->getClass\s*\(\s*\)", filtro=("getClass",),
    ),
    Padrao(
        "nulo_implicito", "parametro tipado com default null sem `?` (nulo implicito)", "php",
        "depreciado no 8.4",
        "Declare o tipo como anulavel: `?Foo $x = null` (ou `Foo|null`).",
        "function f(Foo $x = null) {}", "function f(?Foo $x = null) {}",
        "sim", "media", 50, flags=re.IGNORECASE,
        regex=r"function\b[^(]*\([^)]*?(?<![?|\w\\])(?!mixed\b|null\b)[A-Za-z_\\][\w\\]*\s+&?(?:\.\.\.)?\$\w+\s*=\s*null\b",
    ),
    Padrao(
        "pg_aliases", "apelidos antigos de pg_* (pg_numrows, pg_exec, pg_result, pg_fieldname...)", "php",
        "depreciados desde o 8.0; o 8.5 emite `Function pg_numrows() is deprecated since 8.0` (verificado no "
        "ecidade74_php85). Ainda funcionam: e aviso, nao quebra",
        "Troque pelo nome atual: pg_numrows->pg_num_rows, pg_numfields->pg_num_fields, pg_fieldname->pg_field_name, "
        "pg_result->pg_fetch_result, pg_exec->pg_query, pg_freeresult->pg_free_result, pg_cmdtuples->"
        "pg_affected_rows, pg_errormessage->pg_last_error, pg_getlastoid->pg_last_oid (mesma assinatura).",
        "$n = pg_numrows($rs); $v = pg_result($rs, 0, 'codigo');",
        "$n = pg_num_rows($rs); $v = pg_fetch_result($rs, 0, 'codigo');",
        "sim", "alta", 57,
        regex=FN + r"pg_(?:numrows|numfields|fieldname|fieldsize|fieldtype|fieldnum|fieldprtlen|fieldisnull|"
                   r"freeresult|getlastoid|cmdtuples|errormessage|exec|result|clientencoding|setclientencoding|"
                   r"loreadall|lounlink|loread|lowrite|locreate|loopen|loclose|loimport|loexport)\s*\(",
        filtro=("pg_",), ruidoso=True,
    ),
    Padrao(
        "utf8_encode_decode", "utf8_encode()/utf8_decode()", "php",
        "depreciadas no 8.2 (base LATIN1 usa muito)",
        "mb_convert_encoding($s, 'UTF-8', 'ISO-8859-1') no lugar de utf8_encode; invertido para utf8_decode.",
        "$s = utf8_decode($x);", "$s = mb_convert_encoding($x, 'ISO-8859-1', 'UTF-8');",
        "sim", "alta", 51, regex=FN + r"utf8_(?:en|de)code\s*\(", filtro=("utf8_",),
    ),
    Padrao(
        "strftime", "strftime()/gmstrftime()", "php",
        "depreciadas no 8.1",
        "date()/DateTime::format() para formatos numericos; IntlDateFormatter para nomes de mes/dia em portugues.",
        "echo strftime('%d/%m/%Y');", "echo date('d/m/Y');",
        "semi", "alta", 52, regex=FN + r"(?:gm)?strftime\s*\(", filtro=("strftime",),
    ),
    Padrao(
        "filter_sanitize_string", "FILTER_SANITIZE_STRING", "php", "depreciado no 8.1",
        "htmlspecialchars() na saida, ou FILTER_SANITIZE_SPECIAL_CHARS/FILTER_UNSAFE_RAW conforme o uso.",
        "filter_var($x, FILTER_SANITIZE_STRING);", "htmlspecialchars($x, ENT_QUOTES, 'ISO-8859-1');",
        "semi", "alta", 53, regex=r"\bFILTER_SANITIZE_STRING\b",
    ),
    Padrao(
        "e_strict", "constante E_STRICT", "php", "depreciada no 8.4 (E_STRICT nao e mais emitido desde o 8.0)",
        "Remova E_STRICT das mascaras de error_reporting.", "error_reporting(E_ALL & ~E_STRICT);",
        "error_reporting(E_ALL);", "sim", "alta", 54, regex=r"\bE_STRICT\b",
    ),
    Padrao(
        "interpolacao_dolar_chave", "interpolacao \"${var}\" em string", "php", "depreciada no 8.2",
        "Use \"{$var}\".", "echo \"valor ${nome}\";", "echo \"valor {$nome}\";",
        "sim", "media", 55, regex=r"\$\{[A-Za-z_]\w*\}",
    ),
    Padrao(
        "casts_nao_canonicos", "casts (integer)/(boolean)/(double)/(binary)", "php", "depreciados no 8.5",
        "Use (int), (bool), (float), (string).", "$i = (integer) $x;", "$i = (int) $x;",
        "sim", "media", 56, regex=r"\(\s*(?:integer|boolean|double|binary)\s*\)",
    ),
    Padrao(
        "count_null", "count()/sizeof() sobre variavel (pode ser null)", "php",
        "no 8.0 count(null)/count(nao-contavel) levanta TypeError (no 7.4 era warning e devolvia 0/1)",
        "Se a variavel pode ser null/false/escalar: `count($x ?? [])` ou `is_countable($x) ? count($x) : 0`. "
        "Nao troque as que ja sao sempre array (a busca acha TODAS: muitos falsos positivos).",
        "$n = count($linhas);", "$n = is_countable($linhas) ? count($linhas) : 0;",
        "nao", "baixa", 90, regex=FN + r"(?:count|sizeof)\s*\(\s*@?\$", filtro=("count", "sizeof"), ruidoso=True,
    ),
    # ---------------- Laravel 8 -> 13 ----------------
    Padrao(
        "laravel_helpers_globais", "helpers globais array_*/str_* do Laravel (array_get, str_slug, starts_with...)",
        "laravel",
        "removidos do framework no Laravel 6 (so existem com o pacote laravel/helpers). Atencao: o PHP 8.5 criou "
        "array_first()/array_last() NATIVOS com outra assinatura",
        "Use Illuminate\\Support\\Arr e Illuminate\\Support\\Str: array_get -> Arr::get, str_slug -> Str::slug, "
        "starts_with -> Str::startsWith.",
        "$v = array_get($dados, 'a.b'); $s = str_slug($titulo);",
        "$v = Arr::get($dados, 'a.b'); $s = Str::slug($titulo);",
        "sim", "alta", 60,
        regex=FN + r"(?:array_(?:add|collapse|divide|dot|except|first|flatten|forget|get|has|last|only|pluck|"
                   r"prepend|pull|random|set|sort_recursive|sort|where|wrap)|str_(?:after|before|finish|is|limit|"
                   r"plural|random|replace_array|replace_first|replace_last|singular|slug|start)|studly_case|"
                   r"camel_case|snake_case|kebab_case|title_case|starts_with|ends_with)\s*\(",
    ),
    Padrao(
        "laravel_dates_property", "propriedade $dates em Model", "laravel", "REMOVIDA no Laravel 10",
        "Mova para $casts com 'datetime' (ou 'date').", "protected $dates = ['dt_inicio'];",
        "protected $casts = ['dt_inicio' => 'datetime'];", "sim", "alta", 61,
        regex=r"(?:protected|public)\s+\$dates\s*=", filtro=("$dates",),
    ),
    Padrao(
        "laravel_dispatch_now", "dispatchNow()/dispatch_now()", "laravel",
        "depreciado no Laravel 8, REMOVIDO no 9", "Use dispatchSync()/dispatch_sync().",
        "Bus::dispatchNow(new GeraRelatorio($id));", "Bus::dispatchSync(new GeraRelatorio($id));",
        "sim", "alta", 62, regex=r"\bdispatch(?:_now|Now)\s*\(", filtro=("ispatch",),
    ),
    Padrao(
        "passport_routes", "Passport::routes()", "laravel",
        "REMOVIDO no Passport 11 (as rotas passam a ser registradas sozinhas)",
        "Apague a chamada; para customizar, Passport::ignoreRoutes() + rotas proprias.",
        "Passport::routes();", "// rotas do Passport sao registradas automaticamente",
        "sim", "alta", 63, regex=r"Passport::routes\s*\(", filtro=("Passport",),
    ),
    Padrao(
        "doctrine_dbal", "metodos Doctrine DBAL do Laravel (getDoctrineSchemaManager, getDoctrineColumn...)",
        "laravel", "integracao com Doctrine DBAL REMOVIDA no Laravel 11",
        "Use os metodos nativos do Schema Builder (Schema::getColumns, getIndexes, getTables). Em migrations, "
        "->change() precisa repetir TODOS os modificadores da coluna.",
        "$cols = DB::connection()->getDoctrineSchemaManager()->listTableColumns('t');",
        "$cols = Schema::getColumns('t');", "semi", "alta", 64,
        regex=r"getDoctrine(?:SchemaManager|Column|Connection|Driver)\s*\(", filtro=("getDoctrine",),
    ),
    Padrao(
        "carbon_diff_in", "Carbon ->diffIn*()", "laravel",
        "Carbon 3 (obrigatorio no Laravel 13): diffIn* devolve float e COM SINAL (antes int absoluto); grupo mediu "
        "256 usos do Carbon",
        "Se o codigo espera inteiro positivo: `(int) abs($a->diffInDays($b))`, ou inverta a ordem; reveja "
        "comparacoes e divisoes.", "$dias = $inicio->diffInDays($fim);", "$dias = (int) abs($inicio->diffInDays($fim));",
        "semi", "media", 65, regex=r"->diffIn[A-Z]\w*\s*\(", filtro=("diffIn",),
    ),
    Padrao(
        "request_get", "$request->get() (Symfony Request::get)", "laravel",
        "o Laravel 13 roda sobre um Symfony que marca Request::get() como depreciado (confira o UPGRADE da versao "
        "instalada do symfony/http-foundation)",
        "Prefira $request->input('x') (body+query) ou $request->query('x')/$request->route('x').",
        "$id = $request->get('id');", "$id = $request->input('id');",
        "sim", "baixa", 91, regex=r"\$request->get\s*\(|\brequest\(\)->get\s*\(", filtro=("->get",), ruidoso=True,
    ),
)


# ---------- padroes do guia do grupo (18/11/2026) ----------

def _args(texto: str, i: int, limite: int = 2000) -> list[str] | None:
    """Textos dos argumentos de nivel 0 da chamada cujo '(' termina em i-1."""
    prof, j, ini, fim, out = 0, i, i, min(len(texto), i + limite), []
    while j < fim:
        ch = texto[j]
        if ch in "'\"":
            j += 1
            while j < fim and texto[j] != ch:
                j += 2 if texto[j] == "\\" else 1
        elif ch in "([{":
            prof += 1
        elif ch in ")]}":
            if prof == 0:
                ultimo = texto[ini:j].strip()
                return out + [ultimo] if (ultimo or out) else []
            prof -= 1
        elif ch == "," and prof == 0:
            out.append(texto[ini:j].strip())
            ini = j + 1
        j += 1
    return None


_PG_LO = re.compile(FN + r"pg_lo_(?:export|import)\s*\(")
_PARECE_CONEXAO = re.compile(r"conn|conex|link|banco|\$db\b", re.IGNORECASE)


def _pg_lo_ordem_antiga(texto: str) -> list[int]:
    """pg_lo_export/import com 3 argumentos e a conexao no FIM (ordem antiga, removida no 8.0)."""
    achados = []
    for m in _PG_LO.finditer(texto):
        a = _args(texto, m.end())
        if a and len(a) == 3 and (_PARECE_CONEXAO.search(a[2]) or not _PARECE_CONEXAO.search(a[0])):
            achados.append(m.start())
    return achados


# trecho de uma linha sem ? : ; ( ) -- texto comum ou string simples sem esses caracteres
_SEG = r"(?:[^\n?;:()'\"]|'[^'\n?:;]*'|\"[^\"\n?:;]*\")*"


_DIRS_LARAVEL = ("app/", "routes/", "database/", "resources/", "bootstrap/")


def _so_fora_de_configuration(rel: str) -> bool:
    """Codigo Laravel fora de configuration/ (o guia mediu 82 env() em 33 arquivos de app/). env() de outras pastas
    do legado nao passa pelo cache de configuracao do Laravel."""
    r = rel[len("ecidade/"):] if rel.startswith("ecidade/") else rel
    return r.startswith(_DIRS_LARAVEL)


NOVOS: tuple[Padrao, ...] = (
    Padrao(
        "cast_real", "conversao (real)", "php", "REMOVIDA no 8.0: erro de COMPILACAO (1 arquivo medido pelo grupo)",
        "Troque por (float).", "$v = (real) $x;", "$v = (float) $x;", "sim", "alta", 5,
        regex=r"\(\s*real\s*\)", flags=re.IGNORECASE, filtro=("real", "REAL", "Real"),
    ),
    Padrao(
        "ternario_encadeado", "ternario encadeado sem parenteses (a ? b : c ? d : e)", "php",
        "depreciado no 7.4, erro de COMPILACAO no 8.0 (3 arquivos medidos). Heuristica de linha: o detector de "
        "verdade e o `php -l` do 8.5 (validar_arquivo_php)",
        "Ponha os parenteses na ordem que o 7.4 usa (da ESQUERDA): `(a ? b : c) ? d : e`.",
        "$x = $a ? 1 : $b ? 2 : 3;", "$x = ($a ? 1 : $b) ? 2 : 3;", "semi", "baixa", 6,
        regex=r"\?(?![?>:=])" + _SEG + r":(?!:)" + _SEG + r"\?(?![?>:=])" + _SEG + r":(?!:)", ruidoso=True,
    ),
    Padrao(
        "pg_lo_export_ordem_antiga", "pg_lo_export/pg_lo_import com a conexao no FIM", "php",
        "ordem antiga REMOVIDA no 8.0: erro de tipo e a exportacao nao acontece (grupo mediu 40 usos/33 arquivos)",
        "Passe a conexao como PRIMEIRO argumento: pg_lo_export($conn, $oid, $arquivo).",
        "pg_lo_export($oid, $arquivo, $conn);", "pg_lo_export($conn, $oid, $arquivo);", "sim", "media", 32,
        detector=_pg_lo_ordem_antiga, filtro=("pg_lo_",),
    ),
    Padrao(
        "get_magic_quotes", "get_magic_quotes_gpc()/get_magic_quotes_runtime()", "php",
        "REMOVIDAS no 8.0: erro fatal (2 arquivos medidos)",
        "Sempre devolviam false desde o 5.4: troque a chamada por `false` (o ramo que dependia dela nunca rodava).",
        "if (get_magic_quotes_gpc()) { $x = stripslashes($x); }", "if (false) { $x = stripslashes($x); }",
        "sim", "alta", 33, regex=FN + r"(?:get|set)_magic_quotes_(?:gpc|runtime)\s*\(", filtro=("magic_quotes",),
    ),
    Padrao(
        "comparacao_vazio", "comparacao frouxa com texto vazio (== \"\")", "php",
        "MUDANCA SILENCIOSA no 8.0: `0 == \"\"` era true e virou false. O idioma `$this->x == \"\" ? <POST> : "
        "$this->x` das classes de dados deixa de ler o formulario quando x e inteiro (grupo mediu 36.729 pontos em "
        "4.054 arquivos)",
        "Use a regra Rector do grupo (scratchpad/rector-rules/GuardaComparacaoLiteralRector.php), em commit SO do "
        "Rector; a mao, reproduza o 7.4: `($this->x === \"\" || $this->x === 0 || ...)` conforme o tipo.",
        "$this->cm34_tipo = ($this->cm34_tipo == \"\" ? $POST : $this->cm34_tipo);",
        "(saida da regra GuardaComparacaoLiteralRector, revisada; prove 7.4 x 8.5 com escrita.php)",
        "semi", "media", 21,
        # operando PHP (variavel/propriedade/indice) dos dois lados: deixa de fora o `x == ""` de JavaScript
        regex=r"\$\w+(?:->\w+)*(?:\[[^\]\n]*\])*\s*==\s*(?:\"\"|'')(?![=\w])|(?:\"\"|'')\s*==\s*\$",
        filtro=('""', "''"), ruidoso=True,
    ),
    Padrao(
        "db_raw", "DB::raw()", "laravel",
        "Laravel 10: a Expression nao vira texto sozinha (302 usos medidos); concatenar ou passar como string quebra",
        "Onde o valor e usado como texto, chame ->getValue(DB::connection()->getQueryGrammar()).",
        "$sql = 'select ' . DB::raw('count(*)');", "DB::raw('count(*)') usado so como argumento do query builder",
        "nao", "media", 70, regex=r"DB::raw\s*\(", filtro=("DB::raw",),
    ),
    Padrao(
        "validated", "$request->validated()", "laravel",
        "muda no caminho ate o 13 (82 pontos medidos): chaves sem regra deixam de voltar",
        "Confira se todo campo lido depois tem regra; nao acrescente regra que mude o que o 7.4 aceita.",
        "$dados = $request->validated();", "$dados = $request->validated(); // cada campo usado tem regra",
        "nao", "media", 71, regex=r"->validated?\s*\(", filtro=("validate",), so_em=_so_fora_de_configuration,
    ),
    Padrao(
        "env_fora_config", "env() fora de configuration/", "laravel",
        "DEFEITO JA PRESENTE no Laravel 8 do PR (82 usos em 33 arquivos): com a configuracao em cache, env() fora "
        "dos arquivos de configuracao devolve null",
        "NAO corrija na migracao: registre e avise o dono da area (esta no 7.4, que e a referencia). Decisao do "
        "grupo: replicar ou corrigir no 8.5.",
        "$url = env('PIX_URL');", "(registrar; correcao e decisao do grupo: config('servicos.pix_url'))",
        "nao", "alta", 72, regex=r"(?<![\w$>:\\.])env\s*\(", filtro=("env(", "env ("),
        so_em=_so_fora_de_configuration,
    ),
    Padrao(
        "cache_put_ttl", "Cache::put/add/remember com tempo", "laravel",
        "DEFEITO JA PRESENTE no PR: desde o Laravel 5.8 o tempo e em SEGUNDOS (AssinadorAPI.php:177 e "
        "EmissaoContraChequeJob.php:124 guardavam 5 e 10 minutos e agora guardam 5 e 10 segundos)",
        "NAO corrija na migracao: registre e avise o dono da area; decisao do grupo.",
        "Cache::put('k', $v, 10);", "(registrar; se o grupo decidir corrigir: Cache::put('k', $v, now()->addMinutes(10)))",
        "nao", "media", 73, regex=r"Cache::(?:put|add|remember|set)\s*\(|\bcache\(\)->(?:put|add|remember)\s*\(",
        filtro=("ache",),
    ),
    Padrao(
        "array_pluck", "array_pluck()", "laravel",
        "DEFEITO JA PRESENTE no PR: helper removido sem o pacote laravel/helpers (ComissaoController.php:75, "
        "edu4_cancelaprogressao001.php:96)",
        "NAO corrija na migracao: registre e avise o dono; se o grupo decidir, Arr::pluck().",
        "$ids = array_pluck($lista, 'id');", "(registrar; decisao do grupo: Arr::pluck($lista, 'id'))",
        "nao", "alta", 74, regex=FN + r"array_pluck\s*\(", filtro=("array_pluck",),
    ),
    Padrao(
        "str_random", "str_random()", "laravel",
        "DEFEITO JA PRESENTE no PR: helper removido sem laravel/helpers (ModelFactory.php:22)",
        "NAO corrija na migracao: registre e avise o dono; se o grupo decidir, Str::random().",
        "$t = str_random(40);", "(registrar; decisao do grupo: Str::random(40))",
        "nao", "alta", 75, regex=FN + r"str_random\s*\(", filtro=("str_random",),
    ),
)

_SEVERIDADE: dict[str, tuple[str, bool]] = {
    "parse_str_1_arg": ("quebra_8_5", False), "split": ("quebra_8_5", False), "each": ("quebra_8_5", False),
    "ereg": ("quebra_8_5", False), "create_function": ("quebra_8_5", False),
    "removidas_php8": ("quebra_8_5", False), "chaves_offset_string": ("quebra_8_5", True),
    "cast_real": ("quebra_8_5", True), "ternario_encadeado": ("quebra_8_5", True),
    "pg_lo_export_ordem_antiga": ("quebra_8_5", False), "get_magic_quotes": ("quebra_8_5", False),
    "pg_resultado_false": ("quebra_8_5", False), "count_null": ("quebra_8_5", False),
    "construtor_php4": ("silenciosa", False), "comparacao_vazio": ("silenciosa", False),
    "is_resource_pgsql": ("silenciosa", False),
    "reflection_getclass": ("obsoleto", False), "nulo_implicito": ("obsoleto", False),
    "pg_aliases": ("obsoleto", False), "utf8_encode_decode": ("obsoleto", False), "strftime": ("obsoleto", False),
    "filter_sanitize_string": ("obsoleto", False), "e_strict": ("obsoleto", False),
    "interpolacao_dolar_chave": ("obsoleto", False), "casts_nao_canonicos": ("obsoleto", False),
}
SEVERIDADES = ("quebra_8_5", "silenciosa", "obsoleto", "laravel")

CATALOGO = tuple(
    dataclasses.replace(p, severidade=_SEVERIDADE.get(p.nome, ("laravel", False))[0],
                        nao_compila=_SEVERIDADE.get(p.nome, ("laravel", False))[1])
    for p in (*CATALOGO, *NOVOS)
)

# nomes usados no guia do grupo que ja existiam aqui com outro nome
APELIDOS: dict[str, str] = {
    "chave_offset": "chaves_offset_string", "each_removido": "each", "construtor_antigo": "construtor_php4",
    "utf8_encode": "utf8_encode_decode", "utf8_decode": "utf8_encode_decode",
    "string_interp_dolar": "interpolacao_dolar_chave", "dates_model": "laravel_dates_property",
}


def ordem_trabalho(p: Padrao) -> tuple[int, int]:
    """Nao compila no 8.5 > quebra em execucao > silencioso > obsoleto > laravel; depois `prioridade`."""
    faixa = 0 if p.nao_compila else 1 + SEVERIDADES.index(p.severidade)
    return faixa, p.prioridade


PADROES: dict[str, Padrao] = {p.nome: p for p in CATALOGO}
_COMPILADAS: dict[str, re.Pattern[str]] = {p.nome: re.compile(p.regex, p.flags) for p in CATALOGO if p.regex}


def ocorrencias(padrao: Padrao, texto: str) -> list[int]:
    """Offsets (inicio) das ocorrencias do padrao no texto."""
    if padrao.filtro and not any(f in texto for f in padrao.filtro):
        return []
    if padrao.detector is not None:
        return padrao.detector(texto)
    return [m.start() for m in _COMPILADAS[padrao.nome].finditer(texto)]


def padroes_para(nome: str, incluir_ruidosos: bool = False) -> list[Padrao]:
    """`todos` -> catalogo (sem os ruidosos, a menos que pedidos); senao o padrao pelo nome."""
    if nome == "todos":
        return [p for p in sorted(CATALOGO, key=ordem_trabalho) if incluir_ruidosos or not p.ruidoso]
    if nome in SEVERIDADES:  # ex.: padrao="silenciosa" busca todos dessa severidade (ruidosos inclusive)
        return [p for p in sorted(CATALOGO, key=ordem_trabalho) if p.severidade == nome]
    nome = APELIDOS.get(nome, nome)
    if nome not in PADROES:
        from servidor.seguranca import ErroFerramenta
        raise ErroFerramenta("padrao_desconhecido",
                             f"padrao {nome!r}; validos: todos, {', '.join(SEVERIDADES)}, {', '.join(PADROES)}, "
                             f"{', '.join(APELIDOS)}")
    return [PADROES[nome]]


def nome_canonico(nome: str) -> str:
    return APELIDOS.get(nome, nome)
