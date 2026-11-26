# Locale `pt_BR` (LC_TIME) no 8.5: guarda de versao do `AppServiceProvider` (PHP8-62)

## O defeito (medido)

`ecidade/app/Providers/AppServiceProvider.php:25-39`: `setlocale(LC_TIME, config('app.locale'))` e, **dentro de `if (PHP_VERSION_ID < 74000)`**, uma segunda
`setlocale(LC_TIME, ['ptb','pt_BR','portuguese-brazil','portuguese-brazilian','bra','brazil','br'])`. O valor `74000` e maior que qualquer `7.4.x` (`70433` no 7.4.33), entao a
guarda **vale em todo PHP 7 e nao vale em nenhum PHP 8** (`80512` no 8.5). `config('app.locale')` e `'pt-br'`, que o `setlocale` nao reconhece (devolve `false`); so a lista da
segunda chamada acha um locale (`pt_BR`). Resultado, depois do boot do kernel, nos mesmos conteineres (`php:7.4-cli` e `php:8.5-cli` com `pt_BR` gerado, `--network none`):

| | LC_TIME depois do boot | `formatLocalized('%B')` (2025-03-01) | `%d de %B de %Y` | `%A` |
|---|---|---|---|---|
| 7.4 | `pt_BR` | `mar\xe7o` | `01 de mar\xe7o de 2025` | `s\xe1bado` |
| 8.5 (antes) | `C` | `March` | `01 de March de 2025` | `Saturday` |

(`\xe7`/`\xe1`: bytes ISO-8859-1.) Saidas completas: `locale-lc-time/saida-referencia-7.4.txt` e `saida-8.5-antes-da-correcao.txt`.

## O que depende desse locale (criterio 1)

So passa pelo `AppServiceProvider::boot()` o que roda dentro do Laravel (`/v4`, comandos, filas); as telas legadas fora do Laravel nao o executam e ficam em `LC_TIME=C` nos dois.
Levantado com `grep -rnE "strftime|gmstrftime|formatLocalized|money_format|localeconv|setlocale\(" --include=*.php --include=*.inc ecidade` (fora do `vendor/`):

| Uso | Onde (arquivo:linha) | Depende do nome de mes/dia? |
|---|---|---|
| `Carbon::formatLocalized` | `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:61`, `:73`, `:98` (`'%B'`); `app/Domain/Configuracao/GeradorRelatorio/Services/ImprimirRelatorioTemplateService.php:87` (`'%d de %B de %Y'`) | **sim** (4 usos, os unicos do codigo da aplicacao) |
| `setlocale` | `app/Providers/AppServiceProvider.php:25` e `:28` (a guarda); `fpdf151/fpdf.php:124` `setlocale(LC_ALL,"bra")` (legado, nome invalido no Linux); `dbagata/classes/jpgraph/jpgraph.php:368,376` e `libs/jpgraph/jpgraph.php:756` (JpGraph poe o locale que o grafico pede e o restaura) | so o do provider afeta os 4 usos acima |
| `strftime` com `%a %A %b %B` | JpGraph (`dbagata/classes/jpgraph/jpgraph_gantt.php:2504-2553`, `jpgraph.php:386-394`, `libs/jpgraph/jpgraph.php:764-772`): ja define o proprio locale; `ext/php/adodb-time.inc.php` (`%c/%x`, biblioteca) | nao pelo provider |
| `strftime` numerico (`%Y-%m-%d`, `%d/%m/%Y`, `%j`, `%w`) | `con4_lancamentoscontabeisempenho.RPC.php:66` (`%d/%m/%Y` ou `%Y-%m-%d`), `edu3_progprevisao001.php:153,177`, `edu3_progmatricula001.php:121,422`, `forms/db_frmprogmatricula.php:182,206`, `forms/db_frmtfd_agendaprestsaida.php:49`, `inf4_criainfla001.php:106`, `dbagata/classes/util/nusoap.php:661` | nao |
| `localeconv`, `money_format` | nenhum uso | - |

## Correcao minima (criterio 2)

`ecidade/app/Providers/AppServiceProvider.php:27`: `if (PHP_VERSION_ID < 74000) {` -> `if (PHP_VERSION_ID < 90000) {` (1 linha, no proprio arquivo). No 7.4 a condicao continua verdadeira
(a mesma `setlocale` roda); no 8.x passa a rodar. `php -l` no 7.4 e no 8.5 limpo.

**Imagem do 8.5:** `docker/php85-apache/Dockerfile:18-21` ja gera `pt_BR` (ISO-8859-1) e `pt_BR.UTF-8` (`locale-gen`); o do 7.4 (`docker/php74-apache/Dockerfile:20-22`) gera `pt_BR` em ISO-8859-1. Nada a
acrescentar nos Dockerfiles. Nas imagens `php:*-cli` descartaveis da prova o `pt_BR` e gerado do mesmo jeito (`scratchpad/locale-img/Dockerfile`).

## Prova sem banco (criterio 3)

`bash scratchpad/roda_locale.sh [pasta]` (do zero: vendor do PR fora do repositorio, imagens com `pt_BR`, sai com erro se o `docker run` falhar ou a saida vier vazia). O trecho
`scratchpad/locale_lc_time.php` sobe o kernel (executa o `AppServiceProvider::boot()`), imprime `LC_TIME` e, em hexa, `formatLocalized` e `strftime` de 5 formatos
(`%B`, `%d de %B de %Y`, `%A`, `%a %b`, `%A, %d de %B`) e os dois usos reais (`ucfirst(%B)` do `ApropriacaoDecimoFeriasService` e o `%d de %B de %Y` do `ImprimirRelatorioTemplateService`).

| Comparacao | Resultado |
|---|---|
| 7.4 antes x 7.4 depois da correcao | **identicas byte a byte** (16 linhas) |
| 8.5 depois x 7.4 | **identicas byte a byte** (`LC_TIME='pt_BR'`, `mar\xe7o`, `s\xe1bado`...) |
| 8.5 antes x 8.5 depois | muda (de `C`/ingles para `pt_BR`): era o defeito |

## Reflexo na T-134 (Carbon 3)

O Carbon 3 nao tem `formatLocalized`; o que o 7.4 imprime e **em portugues** (`Mar\xe7o`/`01 de mar\xe7o de 2025`, em ISO-8859-1), nao em ingles como a medicao anterior da PHP8-55 supunha (aquela rodou sem o locale
do provider). Os patches A e B daquela medicao precisam ser refeitos com esta correcao como base.
