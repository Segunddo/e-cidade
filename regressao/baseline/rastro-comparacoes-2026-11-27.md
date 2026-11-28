# Rastreador - fase C: comparacao frouxa que mudou no PHP 8 (2026-11-27)

`python -m regressao.rastro estatica --modo comparacoes` lista `==`, `!=` e `switch` entre um **literal** (texto nao numerico, `''` ou `0`) e outra expressao. No PHP 8 a comparacao entre inteiro e texto nao numerico mudou: `0 == 't'` era `true` no 7.4 e e `false` no 8.5 (medido nos dois contêineres; `'' == 0` idem). **Nao ha aviso nem excecao**: so a resposta muda, e so a bateria/o rastreio pegam quando a tela e exercitada.

## Caso que originou o detector

`ate1_tarefa004.php` (DIVERGE): a resposta trazia `aut=t` no 7.4 e `aut=0` no 8.5. Causa: `forms/db_frmtarefa.php:65` e `:151` fazem `$aut = 0;` e as linhas `976` e `992` testam `$aut=='t'?"t":"0"`. O detector aponta as duas linhas, com evidencia de inteiro.

## Resultado (arvore inteira, ~50 s)

- **193696** comparacoes em **18050** arquivos. Por tipo: texto **39214**, vazio (`''`) **105846**, zero (`0`) **48636**.
- **Nivel de evidencia forte: 134 pontos em 79 arquivos** (texto 33, vazio 101): a mesma variavel recebeu um valor inteiro no mesmo escopo (`$k = 0; ... $k == 't'`, `count()`, `strlen()`, aritmetica, cast). E a lista para os migradores revisarem primeiro: `rastro-comparacoes-alta-2026-11-27.tsv`.
- O restante e **inventario de risco**, nao lista de defeitos: sem evidencia o valor pode ser texto (vindo de formulario ou banco) e a comparacao continua igual.

### Padroes mais comuns (tipo texto, sem filtro)

| Expressao | Literal | Ocorrencias |
|---|---|---|
| `$campos` | `"*"` | 7946 |
| `$opcao` | `"alterar"` | 512 |
| `$opcao` | `"excluir"` | 467 |
| `isset($HTTP_POST_VARS["db_opcao"]) && $HTTP_POST_VARS["db_opcao"]` | `"Alterar"` | 461 |
| `isset($HTTP_POST_VARS["db_opcao"]) && $HTTP_POST_VARS["db_opcao"]` | `"Excluir"` | 442 |
| `isset($HTTP_POST_VARS["db_opcao"]) && $HTTP_POST_VARS["db_opcao"]` | `"Incluir"` | 414 |

## Limites

- A evidencia de inteiro vem de **atribuicao no mesmo escopo** (funcao/arquivo). Valor que chega por `include`, parametro, propriedade ou banco nao tem origem conhecida: entra so no nivel geral. No caso real, o `$aut = 0` esta no mesmo arquivo do uso e foi pego.
- So literais `''`, `0` e texto nao numerico. Nao cobre `in_array`/`array_search` sem modo estrito, `<`/`>` entre tipos, nem `==` entre duas variaveis.
- Nao aponta quando o outro lado e sabidamente texto (`trim()`, `$_GET[..]`, concatenacao, `pg_result()`...).
- Contra o literal `0` a evidencia de inteiro nao agrava (`$k = 0; $k == 0` e inocuo): esse tipo fica so no nivel geral.
- Precisao nao medida: ha **um** caso confirmado (`ate1_tarefa004.php`). Os 134 pontos fortes sao candidatos, nao defeitos confirmados.

Lista completa (uma linha por uso, ~14 MB): `python -m regressao.rastro estatica --modo comparacoes --saida comparacoes.tsv`.
