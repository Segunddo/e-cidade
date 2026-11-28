# Rastreador - fase C: comparacao frouxa que mudou no PHP 8 (2026-11-27)

`python -m regressao.rastro estatica --modo comparacoes` lista `==`, `!=` e `switch` entre um **literal** (texto nao numerico, `''` ou `0`) e outra expressao. No PHP 8 a comparacao entre inteiro e texto nao numerico mudou: `0 == 't'` era `true` no 7.4 e e `false` no 8.5 (medido nos dois contêineres; `'' == 0` idem). **Nao ha aviso nem excecao**: so a resposta muda, e so a bateria/o rastreio pegam quando a tela e exercitada.

## Caso que originou o detector

`ate1_tarefa004.php` (DIVERGE): a resposta trazia `aut=t` no 7.4 e `aut=0` no 8.5. Causa: `forms/db_frmtarefa.php:65` e `:151` fazem `$aut = 0;` e as linhas `976` e `992` testam `$aut=='t'?"t":"0"`. O detector aponta as duas linhas, com evidencia de inteiro.

## Resultado (arvore inteira, ~50 s)

- **172682** comparacoes em **18032** arquivos. Por tipo: texto **39138**, vazio (`''`) **85029**, zero (`0`) **48515**.
- **Nivel de evidencia forte: 57 pontos em 28 arquivos** (texto 5, vazio 52): a mesma variavel recebeu um valor inteiro no mesmo escopo (`$k = 0; ... $k == 't'`, `count()`, `strlen()`, aritmetica, cast). E a lista para os migradores revisarem primeiro: `rastro-comparacoes-alta-2026-11-27.tsv`.
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
- A evidencia **nao segue o fluxo**: uma reatribuicao em ramo (`if`) nao anula a anterior e nao ha analise de lacos. A amostra de 20 foi sorteada com semente fixa; uma amostra maior pode achar novos padroes benignos.
- **Confirmado por execucao: um caso** (`ate1_tarefa004.php`). Os 57 pontos fortes sao candidatos plausiveis, nao defeitos confirmados.

## Conferencia por amostra (leitura do codigo, nao execucao)

A primeira versao do nivel forte tinha 134 pontos. Conferi 25 deles lendo a funcao inteira e achei tres defeitos do proprio detector, todos corrigidos (com teste) antes de fechar o numero:

| Defeito | Exemplo | Correcao |
|---|---|---|
| Literal inteiro diferente de zero contava como evidencia | `$t52_bem = 5; ... != ""` | so conta numero que **pode ser 0** (`0`, `count()`, aritmetica, cast) |
| Atribuicao em ramo anterior do mesmo `if/elseif` contava | `if ($s=="solid") $s=1; elseif ($s=="dotted")` | ramos exclusivos do mesmo `if` nao se alcancam |
| Padroes em que o zero ja e tratado | `$v==0 \|\| $v==''`, `$v != '' && $v !== 0`, `$v=='' ? 0 : $v`, `if ($v=='') { $v = 0; }`, `is_string($v) && ...`, `(int)$v == '' \|\| (int)$v == 0` | suprimidos |
| `$x + 1` contava como possivel zero | `$cod = $max + 1; ... != ""` | `+` com literal positivo nao conta (heuristica: assume $x >= 0) |

Resultado: **134 -> 103 -> 66 -> 57**. Na lista final, em 20 pontos sorteados, **19 sao candidatos plausiveis** e 1 e benigno (um cast `(int)` em `cai1_lista001.php:566`). Plausivel quer dizer: o valor `0` chega a comparacao e o resultado muda; **nao** quer dizer que a tela exercita esse caminho com `0`.

### Padroes dos candidatos finais

- **Familia `cad4_geracarneiptutxt*.php` (5 arquivos, ~25 pontos):** `$k00_valor = 0; ... if ($k00_numpre == '' && $k00_numpar == '' && $k00_dtvenc == '' && $k00_valor == '')` ("nada informado" -> zeros no registro do carne). Com o valor em `0`/`0.0`, `0 == ''` e `true` no 7.4 e `false` no 8.5: o ramo deixa de ser tomado. Os 5 arquivos sao variantes do mesmo gerador: corrigir uma vez e replicar.
- **`strlen($x) != ''`** (`cai3_gerfinanc013.php:339,574`): no 8.x e **sempre `true`** (`strlen('') != ''` e `false` no 7.4 e `true` no 8.5, medido). O teste certo e `strlen($x) > 0`.
- **`$x = 0; ... isset($x) && $x != ''`** em formularios (`forms/db_frmdespachoalt.php:224`, `forms/db_frmprocandamint.php:251`): com `$x` em `0`, o 7.4 escondia a mensagem e o 8.x passa a mostra-la.
- **`$n = (int) ...; if ($n != '' && ...)`** (`edu4_atualizacadastrocenso_2009_001.php:375`) e **`$v = 0; ... if ($v != '' ...)`** (`lic4_geraaut004.php:1179`, `pes2_resumo002.php:934`).

Para todos, o conserto e comparar de forma explicita (`=== ''`, `> 0`, `!== null`) conforme a intencao. Eu nao os classifiquei como defeito sem ver a tela rodar com `0`.

Lista completa (uma linha por uso, ~14 MB): `python -m regressao.rastro estatica --modo comparacoes --saida comparacoes.tsv`.
