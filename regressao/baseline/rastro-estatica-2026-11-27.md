# Rastreador - fase C: analise estatica (2026-11-27)

`python -m regressao.rastro estatica` le o codigo (mesmo `php-parser`) e lista os usos de um resultado que pode ser `false` (`pg_query`, `db_query`, `$cl->sql_record()`, `fopen`...) **sem checagem** antes. E o padrao que mais divergiu no PHP 8: o 7.4 so avisava, o 8.x lanca `TypeError`. Nada e executado, nada e instrumentado e nao ha cache a invalidar: a arvore inteira sai em ~40 s.

## Resultado

- Arquivos analisados: **36712** em **39.5 s**; com candidato: **13801**
- Usos sem checagem: **64720**
- **Cobertura contra o que o rastreio confirmou: 110 de 110 linhas (100%)** (as linhas `arquivo:linha` com `TypeError` de resultado `false` nas telas DIVERGE da rodada base85b)

### Por funcao

| Funcao | Usos |
|---|---|
| `pg_result` | 34576 |
| `db_fieldsmemory` | 16798 |
| `pg_num_rows` | 4405 |
| `fputs` | 3694 |
| `pg_numrows` | 2492 |
| `pg_fetch_result` | 1012 |
| `fclose` | 382 |
| `pg_fetch_array` | 353 |
| `fwrite` | 331 |
| `pg_fetch_object` | 144 |

### Por onde

| Grupo | Usos |
|---|---|
| `classes/` | 31018 |
| `telas (raiz)` | 28559 |
| `forms/` | 1578 |
| `model/` | 1426 |
| `src/` | 573 |
| `libs/` | 414 |
| `fpdf151/` | 405 |
| `integracao_externa/` | 385 |
| `dbforms/` | 126 |
| `std/` | 66 |

## O que isso diz

- **E um inventario de risco, nao uma lista de defeitos.** So 110 dos 64 mil pontos foram confirmados, porque so falham quando a consulta falha e os dados de teste da bateria disparam isso numa minoria. O restante e codigo que o PHP 7.4 tolerava e o 8.x deixa de tolerar se a consulta falhar.
- **Risco que a bateria nao ve:** das **814 telas INCONCLUSIVO** (a bateria nao as exercitou de verdade), **504** tem candidatos, somando **2368 pontos**. Essas telas nao aparecem como DIVERGE e podem quebrar em uso real.
- Das 182 telas DIVERGE, 146 tem candidatos (2131 pontos); a divergencia medida e so o ponto que o teste executou.
- **`classes/` (31 mil usos)** sao os DAOs `db_*_classe.php`: sao 4.337 arquivos, 3.636 com o cabecalho `//MODULO:` e o gerador `sys4_criaclasse001.php` cita `_classe.php`. **Nao confirmei** que todos saem do gerador; se sairem, corrigir o padrao no gerador e regenerar rende mais que editar um a um.
- Arquivos com mais usos: `sys4_processa003.php` (758), `sys4_processa008.php` (750), `sys4_criaclasse001.php` (678): sao geradores de codigo.

## Segunda saida: variaveis lidas por linha

`analise.php --modo=leituras` devolve, por linha, as variaveis lidas (uma chamada em varias linhas vale para todas; `list($a, $b) = ...` escreve, nao le). O backend Xdebug usa isso para montar a cadeia **por dependencia de dados** em vez de por proximidade. Nos 4 casos reais a cadeia ficou mais curta e exata:
`cad2_setor002.php`: `sSql` (linha 65) -> `rsSql = FALSE` (78) -> estoura em `pg_num_rows` (79).

## Limites

- Analise por **funcao/arquivo**, sequencial (sem seguir ramos): uma checagem em qualquer ponto antes do uso conta como guarda (favorece precisao, perde casos).
- Resultado que **vem de outro arquivo** (`include`, propriedade `$this->rs`, parametro) nao tem origem conhecida e nao e apontado.
- Cobre `false` de consulta/arquivo; nao cobre `null` em funcoes de array (`sizeof($x)`), conversoes de tipo nem aritmetica com string (as outras causas medidas).
- Os 110 confirmados incluem o idioma `$cl->sql_record(...)`: sem ele a cobertura era 92% (28 mil usos); com ele, 100% (64 mil).

## Arquivos

- `rastro-estatica-arquivos-2026-11-27.tsv`: um arquivo por linha, ordenado por quantidade de usos, com as 8 primeiras linhas e se a tela e DIVERGE/INCONCLUSIVA.
- Lista completa (uma linha por uso): `python -m regressao.rastro estatica --saida candidatos.tsv`.
