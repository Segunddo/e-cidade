# Rastreador - casos reais (2026-11-27)

Rodada: `python -m regressao.rastro rastreia cad2_setor002.php con2_anexo_i_2014.php con2_lrfgarantias002_2010.php` sobre a arvore instrumentada de `ceef42c8d`, PHP 7.4.33 (2 execucoes) x PHP 8.5.12. Nenhuma linha foi lida de log pelo autor: o relatorio aponta a linha e o dado sozinho. Os 3 casos viram o teste `regressao/tests/test_rastro_casos_reais.py`.

Em todos o 7.4 emite so um **aviso** e o 8.5 **lanca excecao** na mesma linha (`aviso_x_excecao`); a cadeia mostra de onde veio o dado que quebrou.

## `cad2_setor002.php`


**Linha causal:** `cad2_setor002.php:79` - o 7.4 so emite **aviso** e o 8.5 **lanca excecao** na mesma linha. 7.4: aviso: pg_num_rows() expects parameter 1 to be resource, bool given | 8.5: excecao: TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given

**Cadeia de atribuicoes ate a linha causal (no 8.5, em ordem de execucao):**

1. `cad2_setor002.php:37` `orderBy` = string: s29:j34_setor,j34_quadra,j34_zona
2. `cad2_setor002.php:62` `sJ34Setor` = string: s2:''
3. `cad2_setor002.php:63` `sJ34Quadra` = string: s2:''
4. `cad2_setor002.php:75` `sSql` = string: s359: select distinct j34_setor, j34_quadra, j34_zona, j50_descr from lote inner join zonas on j50_zon
5. `cad2_setor002.php:78` `rsSql` = bool: false


## `con2_anexo_i_2014.php`


**Linha causal:** `std/DBDate.php:203` - o 7.4 so emite **aviso** e o 8.5 **lanca excecao** na mesma linha. 7.4: aviso: checkdate() expects parameter 1 to be int, string given | 8.5: excecao: TypeError: checkdate(): Argument #1 ($month) must be of type int, string given

**Cadeia de atribuicoes ate a linha causal (no 8.5, em ordem de execucao):**

1. `std/DBDate.php:196` `ano` = string: s4:2026
2. `std/DBDate.php:196` `mes` = string: s0:
3. `std/DBDate.php:196` `dia` = string: s0:


## `con2_lrfgarantias002_2010.php`


**Linha causal:** `fpdf151/pdf.php:186` - o 7.4 so emite **aviso** e o 8.5 **lanca excecao** na mesma linha. 7.4: aviso: pg_result() expects parameter 1 to be resource, bool given | 8.5: excecao: TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given

**Cadeia de atribuicoes ate a linha causal (no 8.5, em ordem de execucao):**

1. `fpdf151/pdf.php:183` `sSqlMenuAcess` = string: s509: select trim(modulo.descricao)//'>'//trim(menu.descricao)//'>'//trim(item.descricao) as menu from
2. `fpdf151/pdf.php:185` `rsMenuAcess` = bool: false


## `ate1_tarefa004.php`

**Linha causal (confirmada a mao):** `forms/db_frmtarefa.php:976` e `:992` - `$aut=='t'?"t":"0"` com `$aut = 0;` (linhas 65 e 151). `0 == 't'` e `true` no 7.4 e `false` no 8.5, entao a resposta traz `aut=t` no 7.4 e `aut=0` no 8.5. Nao ha aviso nem excecao.

**O rastreador apontou outra linha:** o backend Xdebug escolheu `libs/db_stdlib.php:818` (`substr` so no 7.4). Sondei a linha ao vivo nos dois contêineres e `$HTTP_SERVER_VARS`/`$DB_URL_ABS` saem identicos: e um artefato do trace (uma chamada interna que aparece num trace e no outro nao), nao a causa. Este e o caso das telas sem excecao, em que a linha causal tem confianca baixa. O detector de comparacao frouxa (`rastro-comparacoes-2026-11-27.md`) aponta a linha certa.

## Como ler

- **Linha causal**: o 7.4 so avisa e o 8.5 lanca excecao. A correcao e **neste arquivo:linha** (proteger o valor antes de usa-lo).
- **Cadeia**: as atribuicoes que alimentaram a linha, em ordem. O ultimo item e o valor que quebrou (ex.: `rsSql = false`: a consulta falhou).
- Em `cad2_setor002.php` o relatorio tambem lista os avisos `Undefined variable $j34_setor` (so no 8.5): sao a razao de os filtros da consulta virarem `''`.
