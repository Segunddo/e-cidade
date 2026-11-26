# Eloquent e datas no 8.5 (PHP8-55): leitura e trechos sem banco

Base: `origin/base-php74` (PHP 7.4, Laravel 8.73.2, Carbon 2.72.5, versoes da `composer.lock`). Referencia = 7.4.
Nada aqui usa banco: os models sao criados em memoria (`new Model`, `setRawAttributes`, `setAttribute`), com uma conexao
`pgsql` apenas declarada (nunca aberta), em conteineres `php:7.4-cli` e `php:8.5-cli` com `--network none`.

Defeitos do Laravel 8 do PR (por exemplo o cast `DateTime`, abaixo) ficam no registro da PHP8-49; aqui so se aponta.

## 1. Models com `$dates` e `$casts` de data (arquivo:linha)

Lista completa em `eloquent-datas/listas-dates-casts.md` (gerada por `scratchpad/lista_dates_casts.py`).

| Item | Medido |
|---|---|
| Models com `$dates` | 21 models, 43 atributos |
| Models com `$casts` de tipo data | 20 models, 35 atributos: `datetime` 31, `date` 2, `DateTime` 2 |
| Models com os dois | 1 |
| Models carregados pelo trecho (`$dates` ou `$casts` atribuidos) | 58 (49 com atributo de data, 9 sem; 101 atributos de data no total) |

Todos ficam em `app/Domain/...`. Nenhum model define `$dateFormat` nem `serializeDate()`: valem os padroes do framework.

## 2. Trecho isolado 7.4 x 8.5 (mesmo vendor do PR nos dois)

Script: `scratchpad/eloquent_datas.php <raiz do ecidade> <pasta vendor>`. Para cada atributo de data de cada um dos 58 models,
7 valores de entrada (`2021-03-15`, `2021-03-15 10:20:30`, `...30.123456`, `15/03/2021`, timestamp inteiro, `null`, `''`) x
leitura (`getAttribute`), `attributesToArray()`, `toJson()` e escrita (`setAttribute`), mais escrita com `Carbon` e `DateTime`.
Relogio fixado em `2030-01-01 12:00` e fuso `America/Sao_Paulo`. Saida de referencia: `eloquent-datas/models-7.4.txt` (3.089 linhas, saida do 7.4 normalizada).

Resultado: **3.089 linhas iguais nos dois PHP**. A unica diferenca bruta (402 linhas) e o prefixo `DateTime::__construct(): ` que o PHP 7.4 poe no texto
das mensagens de erro e o 8.5 nao; com o prefixo removido da saida do 7.4 (`sed 's/DateTime::__construct(): //'`) o `diff` e vazio. Tipo da excecao igual.
O arquivo guardado (`models-7.4.txt`) e a saida do 7.4 **ja normalizada** por esse `sed`; a saida crua do 8.5 e igual a ele byte a byte.

O que o PR faz hoje (confirmado nos dois PHP):

| Caso | Resultado |
|---|---|
| `$dates` e cast `datetime`, valor com hora | JSON ISO-8601 em UTC com microssegundos: `2021-03-15 10:20:30` -> `2021-03-15T13:20:30.000000Z` |
| Coluna so de data (`2021-03-15`) | `2021-03-15T03:00:00.000000Z` (meia-noite local convertida para UTC) |
| Cast `date` | mesmo formato; a hora e zerada na leitura (`...T03:00:00.000000Z`) e preservada na escrita (`2021-03-15 10:20:30`) |
| Escrita de texto, `Carbon` ou `DateTime` | grava `Y-m-d H:i:s` (formato da gramatica pgsql), sem microssegundos |
| `''` | vira "agora" (`2030-01-01T15:00:00.000000Z` com o relogio fixado) |
| `15/03/2021` | `Carbon\Exceptions\InvalidFormatException` (leitura, array, JSON e escrita) |
| `null` | continua `null` (leitura, array e JSON); `setAttribute(null)` grava `null` |
| Cast `DateTime` (2 atributos, `Assinador/CertificadoUsuario.php`) | le como data; a escrita falha, igual no 7.4 e no 8.5. Defeito do Laravel 8 do PR: ver registro da PHP8-49 |

Avisos do PHP durante o trecho (so informativo, sem efeito na saida): 7.4 = 426 ocorrencias (2 mensagens distintas: o
`DateTime::modify()` do valor `15/03/2021` e um indice indefinido em `Matricula.php:50`); 8.5 = 129 ocorrencias (80 mensagens distintas), quase todas
`Deprecated` vindas do `vendor` do PR (Laravel 8, Guzzle, `lcobucci/jwt`, Carbon 2) rodando no 8.5. Esse e o motivo de o vendor do 8.5 (PHP8-79) ser
o ponto de partida da inicializacao do Laravel (PHP8-62).

### Repetir com o vendor do 8.5

O trecho recebe a pasta `vendor` por argumento. O `vendor` tem de ser montado em **`/w/ecidade/vendor`** (por cima de `ecidade/vendor`): o autoload do Composer resolve
os `files` do projeto (`app/Helpers/*`) a partir de `dirname(vendor)`, que precisa ser o proprio `ecidade/`. Quando o vendor do 8.5 estiver na integracao
(`bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+` o deixa em `runtime-85/vendor`; num checkout novo, `mkdir ecidade/vendor` antes):

```bash
docker run --rm --network none -v $PWD/ecidade:/w/ecidade:ro -v $PWD/runtime-85/vendor:/w/ecidade/vendor:ro -v $PWD/scratchpad:/s:ro \
  php:8.5-cli php -d memory_limit=1G /s/eloquent_datas.php /w/ecidade /w/ecidade/vendor \
  | diff - docs/migracao-laravel/eloquent-datas/models-7.4.txt     # saida do 8.5 e comparada crua; a referencia ja esta normalizada
# para refazer a referencia no 7.4: ... php:7.4-cli php ... | sed 's/DateTime::__construct(): //' > models-7.4.txt
```

### Antecipando o Laravel 13 (informativo)

Mesmo trecho com `illuminate/database` 13.43 + Carbon 3.15.1 no 8.5 (sem `Usuario`, que precisa do pacote de autenticacao):
o `getDates()` do 13 so devolve `created_at`/`updated_at` e a propriedade `$dates` deixa de ser lida.
Dos 58 models, **18 models (37 atributos) deixam de converter data**: Departamento, Aluno, AtividadeProfissionalEscola, Calendario,
ExcecaoBloqueioNota, Matricula, ProfissionalEscola, Alocado, Candidato, Ciclo, Fase, ApropriacaoDecimoFerias,
ApropriacaoDecimoFeriasLancamentos, EncerramentoPeriodoContabil, Lancamento, ParametroIntegracaoPatrimonial, Recurso, Slip.
Os 3 restantes dos 21 com `$dates` (BnafarBatchProtocolo, ObservacaoInscricao, Planejamento) seguem convertidos: colunas de `timestamps` (`created_at`/`updated_at` ou as constantes `CREATED_AT`/`UPDATED_AT`) ou cast. O conserto e passar os
atributos para `$casts` (`datetime`, ou `date` para colunas so de data), o que muda o JSON das colunas `date` (ver plano, item 6).

## 3. Carbon 2 -> 3: classificacao dos usos

Contagem: `python3 scratchpad/carbon_usos.py ecidade docs/migracao-laravel/eloquent-datas/carbon-usos.tsv` conta as linhas com a palavra
`Carbon` fora de `use` (fora do `vendor`): **275 linhas em 111 arquivos** (a estimativa anterior era 256). A lista linha a linha esta em
`eloquent-datas/carbon-usos.tsv`.

| Categoria | Linhas | Efeito no Carbon 3 |
|---|---|---|
| `@param`/`@return`/`@var` (docblock) | 95 | nenhum |
| tipo em assinatura (`Carbon $x`) | 4 | nenhum |
| `new Carbon(...)` | 22 | nenhum nos argumentos usados (data de model, texto, sem argumento) |
| `Carbon::now()` | 45 | nenhum |
| `Carbon::parse()` | 21 | nenhum nas 8 formas medidas do proprio `parse` (o `->age` encadeado em 3 deles esta a parte) (data, data-hora, ISO com fuso, `''`, texto invalido, `null`) |
| `Carbon::create()` | 8 | nenhum nas formas medidas (inclui mes 13 e 31/02) |
| `Carbon::createFromFormat()` | 73 | nenhum nos 13 formatos/valores medidos (68 linhas com formato literal: `Y-m-d` 40, `d/m/Y` 17, `Ymd` 9, `Y-m-d H:i` 1, `D M d Y H:i:s e+` 1; 5 com formato em variavel) |
| `Carbon::createFromTimestamp()` | 7 | **muda**: sem fuso, devolve UTC (`+00:00`) em vez do fuso padrao |
| Chamadas `->diffInMinutes()` (fora da contagem da palavra) | 1 | **muda o tipo**: devolve float e com sinal |
| Propriedade `->age` sobre `Carbon::parse(...)` (fora da contagem da palavra) | 3 | **muda o sinal** para data futura (ver abaixo) |

Medido em `carbon_2x3.php` (75 linhas de saida): Carbon 2.72.5 no 7.4 e no 8.5 e **identico** (`cmp`); Carbon 3.15.1 no 8.5 difere so em:

- `createFromTimestamp(1615777200)`: `2021-03-15 00:00:00 -03:00` -> `2021-03-15 03:00:00 +00:00`; `format('H:i')`, `startOfDay()`, `hour`, `day`
  passam a ser do UTC. Os 7 usos: `ApropriacaoDecimoFeriasService.php:377`, `RegistroAulaController.php:67` e `:77`,
  `CalendarioController.php:83`, `DiarioClassePdf.php:362`, `:1110` e `:1116`. Os de `DB_datausu` (meia-noite local = 03:00Z) mantem o dia;
  os do `DiarioClassePdf` usam `->month`/`->day`/`lt()` e so mudam de dia se o horario local passar de 21:00. Conferir com dados reais (plano, item 4).
  Contorno de uma linha, se necessario: passar o fuso (`createFromTimestamp($ts, date_default_timezone_get())`).
- `diffInMinutes`/`diffInDays`: 1500 -> `1500.0`; data futura (`fut->diffInMinutes(now)`) 90 -> `-90.5`; `diffInDays` 1 -> `1.0416...`.
  O unico uso (`ApropriacaoDecimoFeriasService.php:382`) compara `> 10` com uma data do passado (arquivo de trava): o resultado nao muda.

- `->age` (`RhDepend.php:27`, `RhDependController.php:73`, `AjudaCustoService.php:247`, este com `subMonth($quantidade)` antes): no Carbon 3 vem de `diffInYears` com sinal.
  Medido com relogio em 2030-01-01: nascimento `1990-05-20` -> 39 nos dois; `2029-12-31` -> 0 nos dois; **`2031-06-01` (futuro) -> 1 no Carbon 2.72.5 e -1 no 3.15.1**
  (igual com `subMonth(3)`). So difere para `rh31_dtnasc` no futuro, que e dado errado; em `AjudaCustoService` o valor e comparado com `rh311_idademax`
  (`> idademax`), entao `-1` deixaria de barrar o lancamento de um dependente com nascimento futuro. Datas passadas: sem mudanca.

`->diff()` encontrados (`rec1_protelacoes.RPC.php:172`, `rec2_absenteismo002.php:263`, `edu2_ficai002.php:93`, `AlunoDiarioClasse.php:198`) usam o `DateTime::diff()` nativo, sem mudanca no Carbon 3.

## 4. Plano das provas com banco (para quando houver decisao)

1. Ler linhas reais de 1 model por tipo de coluna (`date`, `timestamp`, `timestamptz`, com e sem microssegundos) nos dois PHP e comparar
   `toArray()`/`toJson()` (mesma comparacao da secao 2, com valor vindo do `pg`).
2. Escrever e reler (`save()`, `created_at`/`updated_at` automaticos) nos models com `timestamps` e conferir o formato gravado.
3. Bindings: `whereDate`, `where('campo', '>', Carbon)` e `whereBetween` com Carbon (formato do binding na gramatica pgsql).
4. Os 7 `createFromTimestamp`: telas/rotas Educacao (`RegistroAula`, `Calendario`, `DiarioClasse`) com `DB_datausu` real, 7.4 x 8.5 e Carbon 2 x 3.
5. Carbon 3: `->age` (3 usos) com `rh31_dtnasc` no futuro e `subMonth($quantidade)`, e o `createFromTimestamp` do item 4, com dados reais.
6. Laravel 13: migrar os 18 models de `$dates` para `$casts` e medir o JSON das colunas `date` antes e depois (o cast `date` e o `datetime`
   geram `...T03:00:00.000000Z` hoje; comparar com o que as telas/consumidores da API esperam).
7. Fuso: sessao do PostgreSQL (`timezone`) x `America/Sao_Paulo` do PHP para colunas `timestamp`.

## Comandos

```bash
# vendor do PR (composer.lock) e de comparacao, so dependencias, sem banco
docker run --rm -v /tmp/pr:/pr -w /pr composer:2 composer install --no-scripts --ignore-platform-reqs   # composer.json/lock do ecidade
docker run --rm -v /tmp/c3:/c -w /c composer:2 composer require nesbot/carbon:^3 --ignore-platform-reqs
# trechos (cada um com --network none)
php scratchpad/eloquent_datas.php ecidade <vendor>
php scratchpad/carbon_2x3.php <vendor>
python3 scratchpad/lista_dates_casts.py ecidade saida.md
python3 scratchpad/carbon_usos.py ecidade saida.tsv
```
