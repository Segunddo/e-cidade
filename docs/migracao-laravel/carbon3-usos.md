# Carbon 2 -> 3 nos usos do codigo proprio (PHP8-55): medida e patches propostos

O Laravel 13 traz o Carbon 3. Aqui cada uso do Carbon do codigo do e-Cidade (base-php74) foi medido com a **entrada real** nos dois Carbon, num composer
descartavel, sem banco. Os patches ficam **anexados e nao aplicados**: so depois do Laravel 13 integrar (PHP8-55 com Laravel 13).
Depois da integracao do Laravel 13 os patches 01 a 04 foram aplicados (o 05 nao, sem diferenca com o dado real): ver `carbon3-aplicacao.md`.
A trava da integracao nao foi tocada.

## Como foi medido

- **Composer descartavel** (fora do repositorio, so baixa pacotes): Carbon 2 = `nesbot/carbon` 2.72.5 com `config.platform.php = 7.4.33` (resolve `symfony/translation` 5.4.45, a ultima que roda no 7.4; sem isso o
  Composer pega a 6.4, so PHP 8, e o 7.4 morre no `translatedFormat`) e `config.audit.block-insecure=false` (a 2.72.5 tem aviso de seguranca). Carbon 3 = `composer require nesbot/carbon:^3` (3.15.1).
  O vendor do PR (`symfony/translation` 5.4.42) da as mesmas saidas.
- **Imagens do projeto** (`docker/php74-apache` e `docker/php85-apache`, com o `php.ini` e o locale `pt_BR` delas), sem rede, pelo `docker/composer-85/roda-isolado.sh` (PHP8-79), que falha alto
  se o `docker run` falhar ou a saida vier vazia: `VENDOR=<pasta>/vendor bash docker/composer-85/roda-isolado.sh <7.4|8.5> scratchpad/carbon_usos_2x3.php /app/vendor`.
- Script: `scratchpad/carbon_usos_2x3.php <vendor>` (relogio fixo 2030-01-01 23:30 `America/Sao_Paulo`; cada linha da saida e um uso com o seu arquivo:linha).
  Saidas: `carbon3-usos/carbon2-php7.4.txt`, `carbon2-php8.5.txt` e `carbon3-php8.5.txt` (76 linhas cada).
- Carbon 2 no 7.4 x Carbon 2 no 8.5: iguais, **exceto** (a) o texto de 2 mensagens do PHP em `createFromFormat` vazio/`null` (`Data missing` x `Not enough data available to satisfy format`) e (b) o mes por extenso da tabela abaixo, que depende de o `AppServiceProvider` achar o locale `pt_BR` (so no 7.4, ver nota). A igualdade "Carbon 2 igual no 7.4 e no 8.5" vale no script isolado, sem o boot do provider.

## Contagem do que usa Carbon

`grep -rnE '\bCarbon\b' --include=*.php --include=*.inc ecidade | grep -v '^ecidade/vendor' | grep -vE '^[^:]+:[0-9]+:\s*use ' | wc -l` = **275 linhas**.
`Carbon::createFromFormat` 73, `Carbon::now` 45, `Carbon::parse` 21, `Carbon::createFromTimestamp` 7 (`grep -rn 'Carbon::createFromTimestamp'`),
`->formatLocalized` 4 (`grep -rn formatLocalized`), `->age` 3 (`grep -rnE '\->age\b'`), `diffIn*` 1 (`grep -rnE 'diffIn[A-Z]'`); o resto e docblock, assinatura de tipo,
`new Carbon` e encadeamentos que nao mudam. Acrescento aqui o que a classificacao anterior nao tinha: **`formatLocalized`** (removido no Carbon 3).

## Usos que mudam (arquivo:linha, entrada, saida nos dois Carbon)

| # | Uso (arquivo:linha) | Entrada | Carbon 2 (7.4 e 8.5; igual nos dois, salvo U1-U3) | Carbon 3 (8.5) | Patch |
|---|---|---|---|---|---|
| U1 | `ApropriacaoDecimoFeriasService.php:61` `ucfirst(...->formatLocalized('%B'))` | `c01_data` = 2025-03-01, depois do boot do `AppServiceProvider` | **7.4: `mar\xe7o`** (`LC_TIME=pt_BR`, hex `6d6172e76f`); 8.5: `March` (`LC_TIME=C`, o bloco `< 74000` nao roda; corrigido na PHP8-62, T-139) | `UnknownMethodException: Method formatLocalized does not exist.` | 01 |
| U2 | `ApropriacaoDecimoFeriasService.php:73` e `:98` `Carbon::create($ano,$mes,1)->formatLocalized('%B')` | 2025-03-01 | idem U1 | idem | 01 |
| U3 | `ImprimirRelatorioTemplateService.php:87` `formatLocalized('%d de %B de %Y')` | agora = 2030-01-01 | 7.4: `01 de janeiro de 2030`; 8.5: `01 de January de 2030` | idem | 01 |
| U5 | `RegistroAulaController.php:67` e `:77`, `CalendarioController.php:83` `Carbon::createFromTimestamp($request->get('DB_datausu'))->format('Y-m-d')` (vai para o SQL em `ProfissionalEscolaRepository.php:120` e `ConteudoDesenvolvidoRepository.php:87`) | `DB_datausu` = `time()` (`DefaultSession.php:115`), as 23:30 locais | `'2030-01-01'` (fuso `America/Sao_Paulo`) | **`'2030-01-02'`** (UTC, `+00:00`) | 02 |
| U6 | `DiarioClassePdf.php:362`, `:1110`, `:1116` `createFromTimestamp(...)` e `->month`/`->day`/`lt()` | data de encerramento/dia do diario (`getTimestamp()` de uma data, meia-noite local) | `3/15` | `3/15` (com 22:00 local passaria a `3/16`; com o dado real, meia-noite, nao muda) | 05 (opcional) |
| U7 | `ApropriacaoDecimoFeriasService.php:377`/`:382` `createFromTimestamp(mtime)->diffInMinutes(new Carbon()) > 10` | arquivo de trava de 15 min atras | `15`, `true` | `15.0`, `true` | 03 |
| U7 | idem, mtime 15 min **no futuro** (relogio atrasado) | | `15`, `true` | **`-15.0`, `false`** (a trava deixa de ser removida) | 03 |
| U8 | `RhDepend.php:27`, `RhDependController.php:73`, `AjudaCustoService.php:246-247` `->age` | nascimento `1990-05-20` / `2012-12-31` | 39 / 17 | 39 / 17 | - |
| U8 | idem | nascimento no **futuro** `2031-06-01` | `1` | **`-1`** | 04 |

**Nota sobre o locale (U1, U2, U3).** O boot do `AppServiceProvider` (linhas 25-39) faz `setlocale(LC_TIME,'pt-br')` (valor de `config('app.locale')`, que falha) e, **se `PHP_VERSION_ID < 74000`**,
tenta `['ptb','pt_BR',...]`. `74000` e maior que `70433` (7.4.33) e menor que `80512` (8.5): o bloco **roda no 7.4 e nao roda no 8.5**. Medido reproduzindo essa sequencia, com `pt_BR` gerado nas
imagens e o Carbon 2.72.5 do vendor do PR: no 7.4 `LC_TIME=pt_BR` e `formatLocalized('%B')` da `mar\xe7o` (ISO-8859-1, `6d6172e76f`); no 8.5, `LC_TIME=C` e `March`, **mesmo com o Carbon 2**.
O 7.4 de referencia imprime o mes **em portugues**. A guarda e o assunto da PHP8-62 (T-139: `74000` -> `90000`); as medidas abaixo mostram os dois estados do boot (`boot original` e `boot com a T-139`). A T-139 ja esta integrada (`ee5df55c5`): o estado `boot com a T-139` e o da integracao e o da `base` de hoje no 8.5.
O Carbon 3 nao tem o metodo em nenhum dos casos.

## Usos medidos que **nao** mudam

Todos iguais nos dois Carbon (linhas `U9` a `U15` da saida): `createFromFormat` com os formatos do codigo (`Y-m-d`, `d/m/Y`, `Ymd`, `Y-m-d H:i`) e valores de
coluna `date`/`timestamp` (`'2021-03-15'` ok; `'2021-03-15 10:20:30'` `Trailing data`; `''` e `null` `InvalidFormatException`; `'2021-02-30'` vira 2021-03-02), `addMonth(1)->firstOfMonth()`
(`RedesimAlterarInscricaoService.php:396`), `startOfDay`/`endOfDay`, `toDateString`, `getTimestamp`, `between`, `addDay`/`addDays`/`addMinutes`/`subDay`, `Carbon::now()`, `Carbon::parse`, `Carbon::create`.
O ponto de `AuthServiceProvider.php:35-37` (`Passport::tokensExpireIn(Carbon::now()->addDay())`) devolve `Carbon\Carbon` nos dois; o que o Passport 13 aceita ali e assunto da PHP8-39.

## Patches propostos (nao aplicados) em `carbon3-patches/`

Cada um e valido no 7.4 (mesmo resultado medido no Carbon 2) e no Carbon 3:

| Patch | O que muda | Prova (saida do script) |
|---|---|---|
| `01-formatLocalized.patch` | `formatLocalized('%B')` -> `mb_convert_encoding(<Carbon>->locale('pt_BR')->translatedFormat('F'), 'ISO-8859-1', 'UTF-8')` (3x; o primeiro com `->copy()` porque o Carbon e atributo do model) e `'%d de %B de %Y'` -> `translatedFormat('d \d\e F \d\e Y')` | **mesmos bytes do 7.4** (`mar\xe7o`, `01 de janeiro de 2030`) no Carbon 2 no 7.4, no Carbon 2 e no Carbon 3 no 8.5, **nos dois estados do boot** (nao depende do `LC_TIME` nem da T-139), sem `Deprecated`. Alternativa **B**, `strftime($fmt, ts)`: mesmos bytes so se `LC_TIME=pt_BR` (depende da T-139; com `boot original` o 8.5 imprime `March`) e `Deprecated` a partir do 8.1 |
| `02-createFromTimestamp-datausu.patch` | passa `date_default_timezone_get()` como 2o argumento nos 3 usos de `DB_datausu` | `'2030-01-01'` nos dois Carbon (o Carbon 2 com fuso explicito e igual ao padrao) |
| `03-diffInMinutes-absoluto.patch` | `diffInMinutes(new Carbon(), true)` | passado `15`/`true` e futuro `15`/`true` nos dois Carbon (o Carbon 2 ja era absoluto) |
| `04-age-absoluto.patch` | `abs(...->age)` nos 3 usos | `39`, `17`, `1` nos dois Carbon (`->age` do Carbon 2 nunca e negativo) |
| `05-createFromTimestamp-diario-opcional.patch` | mesmo fuso explicito nos 3 usos do `DiarioClassePdf` | opcional: o dado real e meia-noite local e nao muda; so protege contra um horario depois de 21:00 |

`git apply --check` passa nos cinco; aplicados juntos em 8 arquivos (18 linhas a mais, 15 a menos), `php -l` limpo no 7.4 e no 8.5 (o 8.5 so repete o `Deprecated` de
`DiarioClassePdf.php:1768`, que ja existe). Ordem de aplicacao: depois da integracao do Laravel 13; o 01 nao depende da T-139 (a B dependeria).

## Repetir

```bash
mkdir -p c2 c3
echo '{"require":{"nesbot/carbon":"2.72.5"},"config":{"platform":{"php":"7.4.33"},"audit":{"block-insecure":false}}}' > c2/composer.json
docker run --rm -u $(id -u):$(id -g) -e COMPOSER_HOME=/tmp/ch -v $PWD/c2:/c -w /c composer:2 composer update --no-interaction   # sem --ignore-platform-reqs: a plataforma 7.4.33 vale
docker run --rm -u $(id -u):$(id -g) -e COMPOSER_HOME=/tmp/ch -v $PWD/c3:/c -w /c composer:2 composer require 'nesbot/carbon:^3' --ignore-platform-reqs --no-interaction
VENDOR=$PWD/c2/vendor bash docker/composer-85/roda-isolado.sh 7.4 scratchpad/carbon_usos_2x3.php /app/vendor > carbon2-php7.4.txt
VENDOR=$PWD/c2/vendor bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/carbon_usos_2x3.php /app/vendor > carbon2-php8.5.txt
VENDOR=$PWD/c3/vendor bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/carbon_usos_2x3.php /app/vendor > carbon3-php8.5.txt
for f in carbon2-php7.4 carbon2-php8.5 carbon3-php8.5; do cmp $f.txt docs/migracao-laravel/carbon3-usos/$f.txt; done
diff carbon2-php8.5.txt carbon3-php8.5.txt          # as diferencas da tabela acima
```

Conferido assim (imagens do projeto, `roda-isolado.sh`): as tres saidas ficam identicas as guardadas.
