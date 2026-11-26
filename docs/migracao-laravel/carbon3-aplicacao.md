# Carbon 3 sobre o Laravel 13: patches da medicao aplicados (PHP8-55)

A medicao `carbon3-usos.md` deixou 5 patches anexados e nao aplicados, a espera do Laravel 13 (Carbon 3.15.1) no composer do 8.5. Com a T-119 (Laravel 13.43, Passport 13.12) e a correcao do locale (T-139) integradas, este registro rodou de novo cada uso com o vendor atual e **aplicou so os patches em que ha diferenca**. Sem banco, sem rede.

**Resultado:** aplicados 4 dos 5 patches (7 arquivos, 12 linhas trocadas); o 5 nao foi aplicado (sem diferenca com o dado real). **No 7.4 o comportamento fica identico** (as 18 saidas de prova, antes e depois, iguais byte a byte) e **no 8.5 com o Carbon 3 as 18 saidas do codigo corrigido igualam as do 7.4 (16 byte a byte; as 2 de `diffInMinutes` em valor: `15.0` no lugar de `15`)**, sem efeito no teste `> 10`.

## 1. Como foi medido

Imagens do projeto (`docker/php74-apache` e `docker/php85-apache`, com o `php.ini` delas), sem rede, pelo `docker/composer-85/roda-isolado.sh` (falha alto se o contêiner falhar ou a saida vier vazia):

| Lado | PHP | Vendor |
|---|---|---|
| 7.4 (referencia) | 7.4.33 | `composer install` do `ecidade/composer.lock` do PR: `nesbot/carbon` 2.72.5, `symfony/translation` 5.4.42 |
| 8.5 | 8.5.12 | `composer-85.lock`: `laravel/framework` 13.43.0, `nesbot/carbon` 3.15.1 (`composer-85.sh install --no-scripts --ignore-platform-req=php+`) |

```bash
# uso por uso, entrada real (o mesmo script da medicao anterior): 7.4 x 8.5/Carbon 3
VENDOR=<vendor 7.4> bash docker/composer-85/roda-isolado.sh 7.4 scratchpad/carbon_usos_2x3.php /app/vendor > usos-carbon2-php7.4-pr.txt
VENDOR=<vendor 8.5> bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/carbon_usos_2x3.php /app/vendor > usos-carbon3-php8.5-l13.txt
# prova antes/depois sobre o PROPRIO codigo: le a expressao de cada uso no arquivo (arvore original e arvore corrigida) e a executa
#   D = pasta com scratchpad/carbon_patches_prova.php e orig/app/Domain/... (os 7 arquivos como estavam: git show <commit anterior>:<arquivo>)
VENDOR=<vendor 7.4> bash docker/composer-85/roda-isolado.sh 7.4 $D/carbon_patches_prova.php /app/vendor /trecho/orig   # antes, 7.4
VENDOR=<vendor 7.4> bash docker/composer-85/roda-isolado.sh 7.4 $D/carbon_patches_prova.php /app/vendor /app          # depois, 7.4
VENDOR=<vendor 8.5> bash docker/composer-85/roda-isolado.sh 8.5 $D/carbon_patches_prova.php /app/vendor /trecho/orig   # antes, 8.5
VENDOR=<vendor 8.5> bash docker/composer-85/roda-isolado.sh 8.5 $D/carbon_patches_prova.php /app/vendor /app          # depois, 8.5
```

Saidas: `carbon3-aplicacao/usos-*.txt` (76 linhas cada) e `carbon3-aplicacao/prova-{74,85}-{antes,depois}.txt` (18 linhas cada). Relogio fixo 2030-01-01 23:30 `America/Sao_Paulo`; `setlocale(LC_TIME, ['pt_BR', ...])` como o boot do `AppServiceProvider` com a T-139.

## 2. Patch por patch

Diferenca = a saida do uso com o Carbon 3 no 8.5 contra a do 7.4 (`usos-*.txt`), com o dado real do uso:

| Patch | Uso | Antes (8.5, Carbon 3) | Diferenca com o 7.4? | Decisao |
|---|---|---|---|---|
| 01 `formatLocalized` | `ApropriacaoDecimoFeriasService.php:61,73,98` e `ImprimirRelatorioTemplateService.php:87` | `UnknownMethodException: Method formatLocalized does not exist` (o metodo foi removido no Carbon 3) | **sim: fatal** | **aplicado** |
| 02 `createFromTimestamp` | `RegistroAulaController.php:67,77`, `CalendarioController.php:83` (`DB_datausu` = `time()`, 23:30 local) | `2030-01-02 02:30 +00:00` (UTC); o 7.4 da `2030-01-01 23:30 -03:00` | **sim: o dia muda** | **aplicado** |
| 03 `diffInMinutes` | `ApropriacaoDecimoFeriasService.php:382` | trava no futuro: `-15.0` (o 7.4: `15`), a trava deixa de ser removida | **sim** | **aplicado** |
| 04 `age` | `RhDepend.php:27`, `RhDependController.php:73`, `AjudaCustoService.php:246-247` | nascimento no futuro: `-1` (o 7.4: `1`) | **sim** | **aplicado** |
| 05 `createFromTimestamp` do diario | `DiarioClassePdf.php:362,1110,1116` | com o dado real (data de encerramento a meia-noite local) `3/15` nos dois; so um horario depois de 21:00 local daria `3/16` | **nao, com o dado real** | **nao aplicado** (era opcional na medicao) |

O 01 usa `mb_convert_encoding(<Carbon>->locale('pt_BR')->translatedFormat(...), 'ISO-8859-1', 'UTF-8')`: o `formatLocalized` devolvia o mes em ISO-8859-1 (`mar\xe7o`, `6d6172e76f`) com o `LC_TIME=pt_BR` do 7.4; o `translatedFormat` do Carbon 2 e do 3 devolve UTF-8, e a conversao reproduz os mesmos bytes do 7.4.

## 3. Prova antes/depois (18 usos: 4 de nome de mes, 3 de `DB_datausu`, 2 de `diffInMinutes`, 9 de idade)

| Comparacao | Resultado |
|---|---|
| 7.4 antes x 7.4 depois (codigo original x corrigido, Carbon 2.72.5) | **18 de 18 iguais** (`cmp` sem diferenca) |
| 7.4 antes x 8.5 antes (codigo original, Carbon 3.15.1) | 12 diferentes: 4 `formatLocalized` (excecao), 3 `DB_datausu` (dia + 1 e fuso UTC), 2 `diffInMinutes` (`15.0` no passado, `-15.0` no futuro, onde o 7.4 da `15`), 3 de idade com nascimento no futuro (`-1`; as 3 expressoes) |
| 7.4 antes x 8.5 depois (codigo corrigido, Carbon 3.15.1) | **16 de 18 iguais byte a byte; 2 iguais em valor** (`diffInMinutes`: `15.0` no lugar de `15`, nota abaixo) |

Nota: as duas saidas de `diffInMinutes` (passado e futuro) passam a `15.0` no Carbon 3 (o 7.4 devolve `15`): o valor e o mesmo e o uso (`> 10`) da o mesmo resultado, entao nao se mexe. Todas as outras 16 linhas sao iguais byte a byte.

## 4. Verificacoes de sintaxe e alcance

`php -l` dos 7 arquivos alterados passa no 7.4 e no 8.5 (imagens do projeto). `git grep -n formatLocalized -- 'ecidade/*.php' ':!ecidade/vendor'` da 0 linha depois do patch 01 (eram 4). O 7.4 le o mesmo `./ecidade`: as linhas novas sao validas no 7.4 e o resultado la e o medido acima.

## Limites

- As expressoes foram executadas com a entrada real descrita na medicao `carbon3-usos.md`, nao dentro da aplicacao inteira (sem banco, sem sessao).
- O patch 05 fica anexado e nao aplicado em `carbon3-patches/`; vale se alguem passar a gravar a data de encerramento do diario com hora.
