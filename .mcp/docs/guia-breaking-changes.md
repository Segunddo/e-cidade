# Guia de quebras: PHP 7.4 → 8.5 e Laravel 8 → 13

Para quem migra o e-Cidade (gente e IA). A IA lê este guia pelo resource `ecidade://docs/breaking-changes`. Cada
item diz **o que quebra**, **em que versão**, **como achar** (padrão do `buscar_codigo_legado`) e **a correção
padrão**. O que está marcado **(verificado)** foi conferido nos contêineres `ecidade74_php74` (7.4.33) e
`ecidade74_php85` (8.5.12) em 17/11/2026. Os números **medidos pelo grupo** vêm do guia "Migração do PHP 7.4 para
o 8.5 a partir do PR #8" (18/11/2026; íntegra em `ecidade://grupo/guia-7.4-para-8.5`) e as regras de trabalho em
`ecidade://grupo/regras`.

**Alvo (corrigido):** PHP 8.5 com **Laravel 13 + Passport 13**. O 7.4 fica **intacto** com o Laravel 8 do PR e o
8.5 ganha um composer próprio. Ninguém sobe o Laravel do 7.4.

## Medidas do grupo na nova base (`origin/base-php74`, 18/11/2026)

| O quê | Tamanho | Efeito no 8.5 | Padrão MCP |
|---|---|---|---|
| Arquivos PHP (fora `vendor/`) | 36.683 | — | — |
| Compilam no 7.4 e **não compilam no 8.5** | **32 arquivos**: `$s{0}` 20, ternário encadeado 3, nome com `\` que virou token 4, assinatura incompatível com a mãe (jpgraph) 4, `(real)` 1 | erro de compilação | `chaves_offset_string` (`chave_offset`), `ternario_encadeado`, `cast_real`; o resto só o `php -l` do 8.5 (`validar_arquivo_php`) |
| Já não compilam nem no 7.4 | 13 arquivos | ficam como estão e são **registrados** | — |
| `each()` | 84 usos / 28 arq | erro fatal quando a linha roda | `each` (`each_removido`) |
| `pg_lo_export`/`pg_lo_import` | 40 usos / 33 arq (o MCP aponta os ~15 com a conexão no FIM, a ordem removida) | erro de tipo; a exportação não acontece | `pg_lo_export_ordem_antiga` |
| `create_function` | 1 arq | erro fatal | `create_function` |
| `get_magic_quotes_*` | 2 arq | erro fatal | `get_magic_quotes` |
| `count()` de não-lista | amplo | `TypeError` | `count_null` (ruidoso) |
| `$this->x == ""` | **36.729 pontos em 4.054 arquivos** | **silencioso**: com `$x` inteiro o formulário deixa de ser lido | `comparacao_vazio` (o MCP conta todo `$var == ""`, por isso acha mais); regra Rector do grupo `GuardaComparacaoLiteralRector` |
| Construtor no estilo antigo | **152 classes em 143 arquivos** `.php` | **silencioso**: o objeto nasce sem inicializar | `construtor_php4` (`construtor_antigo`; o MCP também varre `.class`/`.inc` do `dbagata`) |
| `utf8_encode`/`utf8_decode` | 1.832 usos / 376 arq | obsoleto (8.2) | `utf8_encode_decode` |
| `"${var}"` | 113 arq | obsoleto (8.2) | `interpolacao_dolar_chave` (`string_interp_dolar`; o MCP também casa `${x}` de JavaScript) |
| `strftime`/`gmstrftime` | 12 arq | obsoleto (8.1) | `strftime` |
| `FILTER_SANITIZE_STRING` | 3 arq | obsoleto (8.1) | `filter_sanitize_string` |

Ordem de trabalho do grupo (e do `proximo_trabalho`): **não compila no 8.5 > quebra em execução > silencioso >
obsoleto**. Aviso de obsoleto que não aparece na tela e não muda o resultado não precisa de correção (regra
"funciona igual"); confira `error_reporting`/`display_errors` do 8.5 contra o 7.4.

## O que dá para copiar da `base-php84` e o que não

Parte do que foi corrigido na `base-php84` era diferença 5.6 → 7, que o 7.4 do PR **já tem**. Copiar muda o
comportamento em relação à referência. **Nunca** copie arquivo inteiro da `base-php84` por cima do da
`base-php74` (desfaz as mudanças funcionais do PR); parta do arquivo do PR e mude só as linhas necessárias.

| Correção na `base-php84` | Copiar? |
|---|---|
| `$$x[$i]` e `$o->$p[$i]` (mudaram de sentido no 7.0) | **NÃO**: o 7.4 já lê do jeito novo; mexer mudaria o resultado |
| `split()` coberto por função de compatibilidade | **NÃO**, se a mesma função de compatibilidade estiver no 7.4 e no 8.5 (hoje o 7.4 do PR não tem `split`: a tela já quebra na referência, então registre) |
| `break` fora de laço | **NÃO**: já é erro de compilação no 7.4; se compila no 7.4, não existe |
| `$s{i}` → `$s[i]` | sim (8.0) |
| `pg_lo_export` com a conexão no fim | sim (8.0) |
| Construtor do jpgraph e assinaturas compatíveis | sim (8.0) |
| `== ""` com inteiro | sim (8.0) |
| `each()`, `create_function`, `count(null)` | sim (8.0) |

Prioridade: se o PR já resolveu e roda no 8.5, fica o do PR; se resolveu mas não roda, ajuste mínimo no código do
PR; só se o PR não mexeu e o ponto quebra no 8.5 a `base-php84` serve de modelo, adaptada. Antes de aplicar, rode o
trecho no 7.4 e no 8.5: se o 8.5 já se comporta como o 7.4, não mexa.

## 0. O que a rodada "antes" mediu na base 7.4 (18/11/2026)

A suíte rodou inteira sobre a `base-php74` (referência 7.4 × 8.5, causa de cada tela lida ao vivo no log do 8.5).
Detalhes em `ecidade://regressao/triagem` e `ecidade://regressao/decisoes` (tool `ler_triagem`). O que vale levar:

1. **9.206 divergências; três causas explicam 90% das 6.635 telas e relatórios**: `parse_str()` com 1 argumento
   (3.585 casos; 7.645 chamadas em 7.560 arquivos; o guia do grupo não a cita), `fpdf151/fpdf.php:614` (1.425) e
   `libs/JSON.php:188` (985; derruba também o login no 8.5). As duas últimas são 2 dos 32 arquivos que não compilam:
   **corrija-as primeiro**.
2. **Silencioso**: `0 == ""` em `atualizacampos()` faz 2.478 classes e 19 dos 35 cadastros testados não gravarem nada
   no 8.5, sem erro. Construtor antigo: 101 telas (`label() on null`) e 53 classes. SQL que falha (`pg_*(false)`): 428.
3. **Efeito cebola**: cada correção revela a próxima quebra da mesma tela (760 telas de PDF têm `parse_str` logo
   depois do `fpdf.php`). Uma tela que vira de "500" para "500 com outra mensagem" não é regressão nova: é a suíte
   enxergando mais. Rode a regressão **depois de cada passo**.
4. **Ordem do grupo**: não compila (as 2 linhas, depois os outros 30) → quebra ao rodar (`parse_str`, construtor,
   `each`, `count`, `pg_lo_export`) → silencioso (`0 == ""` com a regra Rector do grupo). `each()` não foi a primeira
   quebra de nenhuma tela: está atrás das outras ou em linhas que a bateria não executa.
5. **As janelas de pesquisa `func_*.php` (as "lupas") não entram na bateria PHP**: 2.920 das 3.154 têm o mesmo
   `parse_str` (amostra ao vivo: 8 de 8 quebram). Rode `--prefixo '^func_'` quando mexer nelas.
6. A migração anterior (gabarito 5.6, branch `regressao`) chegou às mesmas lições; os números dela não valem mais.
7. **"Aceitar" em `conhecidas.tsv` não conserta nada**: só silencia o alarme e manda funcionalidade quebrada para
   produção. Divergência nascida na migração se corrige.
8. **SQL que falha** (`pg_*` recebendo `false`): no 7.4 a tela seguia vazia em silêncio; no 8.x aborta. Pela regra
   "funciona igual ao 7.4", reproduzir o vazio; mostrar erro claro é decisão do grupo.
9. A bateria abre as telas **sem parâmetros**: ela prova que a tela "abre igual", não que os números batem.

## 1. O que muda partindo do 7.4 (e não mais do 5.6)

- **Já quebrado no 7.4** (`split`, `ereg*`, `mysql_*`, `mcrypt_*` não existem no 7.4, **verificado**): o código que
  ainda os usa quebra **na referência também**. Na regressão aparece como erro igual dos dois lados
  (INCONCLUSIVO), não como DIVERGE. Pela regra do grupo ("funciona igual ao 7.4" / "só atualizar"), **registre e
  avise o dono da área**; corrigir é decisão do grupo, não da migração.
- **Depreciado no 7.4 e fatal no 8.0** (o 7.4 avisa e segue; o 8.5 para): `parse_str` com 1 argumento, construtor
  PHP 4, `each`, `create_function`, `money_format`, `get_magic_quotes_*`, `$str{0}`, ternário aninhado sem
  parênteses, `implode($array, $sep)`, `array_key_exists` em objeto, `mktime()` sem argumentos. **Estes viram
  DIVERGE** na bateria 7.4 × 8.5. São a maior parte do trabalho.
- **A base 7.4 já veio com boa parte corrigida**: o grupo mediu 152 classes com construtor antigo (eram ~600 na
  base 5.6), mas o `parse_str` de 1 argumento continua em milhares de telas. Números: "Medidas do grupo" e seção 7.

## 2. PHP 8.0 (o grosso das quebras)

| Quebra | Sintoma no 8.5 | Padrão MCP | Correção padrão |
|---|---|---|---|
| `parse_str($qs)` / `mb_parse_str($qs)` com 1 argumento | `ArgumentCountError: parse_str() expects exactly 2 arguments, 1 given` **(verificado)** → tela 500 | `parse_str_1_arg` | `parse_str($qs, $__qs); unset($__qs['this'], $__qs['GLOBALS']); extract($__qs);` |
| Construtor PHP 4 (`function cl_x()` na classe `cl_x`) | não é mais chamado **(verificado: `ok=0` no 8.5, `ok=1` no 7.4)** → propriedades nulas, `Call to a member function label() on null` | `construtor_php4` | renomear para `__construct`; `parent::cl_x()` → `parent::__construct()` |
| `each()`, `create_function()`, `money_format()`, `get_magic_quotes_*()`, `is_real()`, `fgetss()`, `hebrevc()`, `restore_include_path()`, `__autoload()` | `Call to undefined function` **(verificado)** | `each`, `create_function`, `removidas_php8` | `foreach`; closure; `NumberFormatter`/`number_format`; remover magic quotes; `is_float`; `strip_tags(fgets())`; `spl_autoload_register` |
| `$str{0}` | **erro de compilação** (`ParseError`, verificado): o arquivo inteiro para | `chaves_offset_string` | `$str[0]` |
| `(real)` | **erro de compilação** | `cast_real` | `(float)` |
| `pg_lo_export($oid, $arq, $conn)` (conexão no fim) | erro de tipo; o arquivo não é exportado | `pg_lo_export_ordem_antiga` | conexão primeiro: `pg_lo_export($conn, $oid, $arq)` |
| Ternário aninhado sem parênteses `a ? b : c ? d : e` | **erro de compilação** (o 7.4 só avisava) | `ternario_encadeado` (heurística ruidosa; o `php -l` do 8.5 via `validar_arquivo_php` é quem decide) | parênteses explícitos, mantendo a associatividade do 7.4: `(a ? b : c) ? d : e` |
| `count(null)` / `sizeof` de não contável | `TypeError` **(verificado)** (7.4: warning e seguia) | `count_null` (baixa confiança: acha todos os `count($x)`) | `is_countable($x) ? count($x) : 0` ou `count($x ?? [])` só onde pode ser null |
| `pg_*` recebendo `false` (consulta que falhou) | `TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given` **(verificado)** | `pg_resultado_false` (só o caso aninhado `pg_numrows(db_query(...))`) | decisão 2a (19/11/2026): reproduzir o 7.4, que devolvia `null` e seguia com a tela vazia: `$rs ? pg_num_rows($rs) : null`. Os wrappers centrais (`db_fieldsmemory`, `db_lovrot`, `db_utils::fieldsMemory`/`getCollectionByRecord`/`makeCollectionFromRecord`, menu do Agata, `cl_estrutura::db_mascara`, `linhaRelatorioContabil`) já fazem isso; chamada direta na tela continua caso a caso |
| Comparação número × string | `0 == ""` e `0 == "abc"` passam a ser **false** (eram true) **(verificado)** | `comparacao_vazio` para `== ""` (o resto não dá para achar por regex) | regra Rector do grupo `GuardaComparacaoLiteralRector`, em commit separado; prove com `escrita.php` (o caminho de escrita das classes de dados não é exercitado por GET) |
| Aritmética com texto não numérico | `"abc" + 1` → `TypeError: Unsupported operand types: string + int` **(verificado)**; `"10abc" + 1` só avisa | — | converter/validar a entrada (`(int)`, `is_numeric`); em biblioteca (Agata: acumulador não inicializado) corrigir 1 vez na origem |
| `implode($array, ',')` (ordem invertida) | `TypeError` **(verificado)** | regex livre: `implode\(\s*\$\w+\s*,\s*['"]` | `implode(',', $array)` |
| `array_key_exists($k, $objeto)` | `TypeError` **(verificado)** | regex livre | `property_exists`/`isset` |
| `mktime()` sem argumentos | `ArgumentCountError` **(verificado)** | regex livre: `mktime\(\s*\)` | `time()` |
| `ReflectionParameter::getClass()` | depreciado **(verificado)** | `reflection_getclass` | `getType()` + `ReflectionNamedType` |
| `@` não silencia mais erro fatal; `match`/`mixed` viram palavras reservadas | fatal/compilação | — | `php -l` no 8.5 acusa nomes reservados |

## 3. PHP 8.1 a 8.4

| Versão | Mudança | Sintoma | Padrão MCP / correção |
|---|---|---|---|
| 8.1 | **pgsql devolve objetos** (`PgSql\Connection`, `PgSql\Result`) **(verificado)** | `is_resource($rs)` dá `false` e o código toma o caminho de erro | `is_resource_pgsql`: trocar por `$rs !== false` |
| 8.1 | **null em parâmetro não anulável de função nativa** (`strlen(null)`, `trim(null)`, `str_replace(..., null)`) | `Deprecated: Passing null to parameter...` **(verificado)**; vira erro numa versão futura e enche o log | `?? ''` na origem do valor; não silencie com `@` |
| 8.1 | `htmlspecialchars()`/`htmlentities()` escapam aspas simples por padrão (`'` → `&#039;`) **(verificado)** | HTML/valores de input diferentes | passe as flags explícitas se o 7.4 não escapava: `htmlspecialchars($s, ENT_COMPAT, 'ISO-8859-1')` |
| 8.1 | `strftime`/`gmstrftime`, `FILTER_SANITIZE_STRING` depreciados **(verificado)** | Deprecated | `strftime`, `filter_sanitize_string` |
| 8.1 | classes que implementam `ArrayAccess`/`Iterator`/`Countable` sem tipos de retorno | Deprecated ("Return type ... should be compatible") | declarar o tipo de retorno (compatível com 7.4 quando possível) ou `#[\ReturnTypeWillChange]` |
| 8.2 | **propriedades dinâmicas** (`$obj->campo_novo = 1` sem declarar) **(verificado)** | Deprecated em massa nas classes legadas | declarar a propriedade; em classe de dados genérica, `#[\AllowDynamicProperties]` |
| 8.2 | **`strtolower`/`strtoupper`/`ucfirst`/`ucwords` ignoram o locale** **(verificado: `ção` → `ÇãO` no 7.4 com locale pt_BR, `çãO` no 8.5)** | maiúsculas com acento **mudam** em telas, relatórios e chaves de busca da base LATIN1 | `mb_strtoupper($s, 'ISO-8859-1')` (o 7.4 com locale dava o mesmo) |
| 8.2 | `utf8_encode`/`utf8_decode` depreciados **(verificado)**; `"${var}"` depreciado **(verificado)** | Deprecated | `utf8_encode_decode` (`mb_convert_encoding`), `interpolacao_dolar_chave` (`{$var}`) |
| 8.3 | `get_class()`/`get_parent_class()` sem argumento depreciados **(verificado)** | Deprecated | `get_class($this)` / `static::class` |
| 8.4 | **nulo implícito** (`function f(Foo $x = null)`) **(verificado)** | Deprecated (vendor antigo também: Guzzle, lcobucci/jwt, PHPStan 1.x emitem isto no 8.5) | `nulo_implicito`: `?Foo $x = null` |
| 8.4 | `E_STRICT` depreciado **(verificado)**; `trigger_error(..., E_USER_ERROR)` depreciado | Deprecated | `e_strict`; lançar exceção no lugar de `E_USER_ERROR` |

## 4. PHP 8.5

| Mudança | Sintoma | Padrão MCP / correção |
|---|---|---|
| casts `(integer)`, `(boolean)`, `(double)`, `(binary)` depreciados **(verificado)** | Deprecated | `casts_nao_canonicos`: `(int)`, `(bool)`, `(float)`, `(string)` |
| operador crase `` `cmd` `` depreciado **(verificado)** | Deprecated | `shell_exec()` (e reveja: executar shell a partir de tela é risco) |
| apelidos `pg_numrows`, `pg_exec`, `pg_result`, `pg_fieldname`... emitem `deprecated since 8.0` **(verificado)** | Deprecated (funciona) | `pg_aliases`: nome atual com a mesma assinatura |
| novas funções nativas `array_first()`/`array_last()` **(verificado)** | o helper do Laravel de mesmo nome tem outra assinatura (`array_first($arr, $callback)`) | `laravel_helpers_globais`: use `Arr::first()` |

> Depreciação não quebra a tela, mas **enche o log** e vira erro na próxima major. A bateria PHP compara a saída:
> se o `display_errors` do alvo mostrar o aviso na página, vira DIVERGE. A paridade de ini está em
> `regressao/lab/php85/paridade-74.ini`.

## 5. Laravel 8 → 13 (frente do grupo Laravel)

**Estratégia do grupo:** o Laravel 13 exige PHP 8.3+ e não roda no 7.4. O **7.4 fica com o Laravel 8 do PR,
intacto**, e o **8.5 ganha bibliotecas próprias** (um composer só dele, com Laravel 13 e Passport 13): a referência
nunca muda e os dois são comparados lado a lado. Os degraus 9, 10 e 11 não ajudam (nenhum tem suporte oficial no
8.5). `composer.json`, `composer.lock` e `vendor/` são do grupo Laravel: ninguém mexe sem combinar.

### O que muda do Laravel 8 ao 13 (contado pelo grupo na nova base)

| Assunto | Tamanho | O que muda | Padrão MCP |
|---|---|---|---|
| Inicialização e configuração | esqueleto 5.4 mantido | `bootstrap/app.php`, `Kernel`, `Handler`, providers e `configuration/` seguem a estrutura antiga (o 11+ aceita) | — |
| Passport 13 e login | `/v4/login` + tabelas `oauth_*` | login por senha precisa ser ativado (`enablePasswordGrant()`); o model de usuário precisa de `OAuthenticatable`; `Passport::ignoreRoutes()`; ids inteiros dos clientes | `passport_routes` |
| Datas | 21 models com `$dates`; 256 usos do Carbon; 242 pontos que geram JSON | `$dates` sai no 10; Carbon 2 → 3 (`diffIn*` com sinal e float) | `laravel_dates_property` (`dates_model`), `carbon_diff_in` |
| Consultas | 302 usos de `DB::raw` | no 10 a expressão não vira texto sozinha | `db_raw` |
| Validação | 82 pontos com `validated()`/`validate()` | chaves sem regra deixam de voltar | `validated` |
| E-mail | SwiftMailer | trocado pelo Symfony Mailer no 9 | — |
| Arquivos | 3 arquivos de configuração | Flysystem 3; raiz padrão do disco local muda no 12 | — |
| Rotas | 1.300 rotas | ordem de precedência no 12 | — |
| Documentos | mPDF, dompdf, PhpSpreadsheet, PHPWord | versões novas; conferir PDF, planilha e Word contra o 7.4 | — |
| Helpers globais `array_*`/`str_*` | — | fora do framework desde o 6 | `laravel_helpers_globais` |
| Doctrine DBAL | — | removido no 11; `->change()` exige a definição completa | `doctrine_dbal` |

No total o grupo achou **134 itens** dos guias oficiais em uso no código.

### Bibliotecas que travam o PHP 8.5 (composer.lock do PR)

- **10 pacotes excluem o 8.5**: `lcobucci/jwt` 3.4, `dompdf` 0.8.6, `mpdf` 8.2.4, `laminas-escaper`,
  `htmlpurifier`, `nette/schema`, `nette/utils`, `bacon-qr-code`, `qrcode-detector-decoder` e `faker` (dev);
  `phpspreadsheet ^1.08` resolve para 1.30.x, que declara `<8.5`. A maioria sai ao atualizar o pacote que a puxa
  (`analisar_composer` lista o que o lock declara).
- **Sobram 2 bloqueios** com o Laravel novo nas versões liberadas (testado com Composer e PHP 8.5.12): `dbseller/sdk-api-pix-bb` 2.0.0
  (exige Guzzle 7.5.0 exato; solução medida: ajuste mínimo na instalação, só no 8.5, provado contra dublê) e
  `proner/phppimaco` 1.4.5 (puxa `endroid/qr-code ^2.5` e `bacon-qr-code` 1.0.3; solução medida mantém a etiqueta
  com o mesmo tamanho impresso).

### Defeitos que o Laravel 8 do PR JÁ tem (também no 7.4): registrar, não corrigir

| Defeito | Onde | Padrão MCP |
|---|---|---|
| `Cache::put` conta em **segundos** desde o 5.8 | `AssinadorAPI.php:177` e `EmissaoContraChequeJob.php:124` (provavelmente `LicitaconObrasClient.php:47`) guardavam 5 e 10 minutos e agora guardam 5 e 10 segundos | `cache_put_ttl` |
| Helpers removidos sem `laravel/helpers` | `array_pluck` (`ComissaoController.php:75`, `edu4_cancelaprogressao001.php:96`), `str_random` (`ModelFactory.php:22`) | `array_pluck`, `str_random` |
| `env()` fora de `configuration/` | 82 usos em 33 arquivos: com a configuração em cache devolvem `null` | `env_fora_config` |

Estão na referência: a regra manda **registrar e avisar quem cuida da área**; corrigir é decisão do grupo (replicar
o defeito no 8.5 ou corrigir).

## 6. Como verificar uma correção (sempre)

1. **Antes de mexer**, prove a diferença: `validar_arquivo_php(caminho, versao="ambas")` e a comparação 7.4 × 8.5
   da tela/classe. Se o 8.5 já se comporta como o 7.4, não mexa.
2. Depois: de novo `validar_arquivo_php(versao="ambas")` — o mesmo código legado roda no 7.4 e no 8.5: a correção
   precisa compilar e funcionar nos dois (nada de sintaxe só do PHP 8 em arquivo que o 7.4 usa).
3. `validar_arquivo_php(caminho, ferramentas=["phpstan"], versao="alvo")` — o PHPStan no 8.5 já acusa, por exemplo,
   `Function parse_str invoked with 1 parameter, 2 required` **(verificado)**.
4. `rodar_regressao` no recorte da tela/rota e `ler_resultado_regressao`. IDENTICO = mesma resposta que o 7.4.
   INCONCLUSIVO/ERRO_AMBIENTE não aprovam nada.

## 7. Quanto ainda existe na base 7.4 (varredura estática do MCP em `ecidade/`, 17 e 18/11/2026)

Gerado com o catálogo do MCP (`buscar_codigo_legado`); conte de novo com `padroes_ja_corrigidos(contar_em="ecidade")`.
Número de ocorrências é teto (comentários e strings também casam).

| Padrão | Ocorrências | Arquivos | Efeito no 8.5 |
|---|---:|---:|---|
| `parse_str_1_arg` | 46 (eram 7.645) | 44 (eram 7.560) | **fatal** (tela 500). Na branch `migracao/decisoes-2a-3-11` (19/11/2026) as 7.610 chamadas de verdade em 7.535 arquivos viraram `parse_str(x, $__qs); unset(...); extract($__qs);`; as 46 que sobram são comentários e strings (o analisador de tokens do PHP não acha nenhuma chamada) |
| `construtor_php4` | 253 | 202 | **silencioso** (construtor não roda); classes com `namespace` ficam de fora (no 7.4 já não eram construtor); só `.php`: 150 arquivos, o grupo mediu 143 |
| `split` | 368 | 86 | já quebrado no 7.4 |
| `each` | 85 | 28 | **fatal** |
| `ereg` | 23 | 7 | já quebrado no 7.4 |
| `create_function` | 2 | 2 | **fatal** |
| `removidas_php8` | 30 | 7 | **fatal** (ou já quebrado no 7.4: `mysql_*`, `mcrypt_*`) |
| `chaves_offset_string` | 95 | 23 | **compilação** |
| `pg_resultado_false` | 183 | 110 | **fatal se a consulta falhar** |
| `is_resource_pgsql` | 253 | 87 | **comportamento** (só os de pgsql; o resto é arquivo) |
| `reflection_getclass` | 0 | 0 | — |
| `nulo_implicito` | 285 | 206 | depreciado |
| `utf8_encode_decode` | 1.800 | 376 | depreciado |
| `strftime` | 55 | 12 | depreciado |
| `filter_sanitize_string` | 8 | 3 | depreciado |
| `e_strict` | 9 | 6 | depreciado |
| `interpolacao_dolar_chave` | 1.286 | 340 | depreciado |
| `casts_nao_canonicos` | 483 | 174 | depreciado |
| `pg_aliases` (ruidoso) | 88.914 | 5.684 | depreciado |
| `count_null` (ruidoso, teto) | 24.117 | 6.105 | **fatal só onde o valor for null** |
| `laravel_helpers_globais` | 2 | 2 | Laravel |
| `laravel_dates_property` | 21 | 21 | Laravel 10 |
| `passport_routes` | 1 | 1 | Passport 11 |
| `carbon_diff_in` | 1 | 1 | Laravel 13 (Carbon 3) |
| `request_get` (ruidoso) | 920 | 147 | Symfony do Laravel 13 (confira) |
| `laravel_dispatch_now`, `doctrine_dbal` | 0 | 0 | — |
| `cast_real` (18/11) | 4 | 1 | **compilação** |
| `ternario_encadeado` (ruidoso, 18/11) | 23 | 9 | **compilação** (o grupo mediu 3 arquivos pelo `php -l`) |
| `pg_lo_export_ordem_antiga` (18/11) | 15 | 15 | **fatal** |
| `get_magic_quotes` (18/11) | 9 | 4 | **fatal** |
| `comparacao_vazio` (ruidoso, 18/11) | 57.682 | 5.356 | **silencioso** (o grupo conta só `$this->x == ""`: 36.729 / 4.054) |
| `db_raw` (18/11) | 344 | 87 | Laravel 10 |
| `validated` (18/11, só `app/` `routes/` `database/` `resources/` `bootstrap/`) | 82 | 37 | Laravel (o grupo mediu os mesmos 82) |
| `env_fora_config` (18/11) | 84 | 33 | defeito já no 7.4 |
| `cache_put_ttl` (18/11) | 6 | 6 | defeito já no 7.4 |
| `array_pluck` / `str_random` (18/11) | 1 / 1 | 1 / 1 | defeito já no 7.4 |
