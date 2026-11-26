# Aceite da inicializacao do Laravel 8 do PR no 8.5, com o vendor do 8.5 integrado (PHP8-62)

Repete a medicao preliminar (vendor do PR nos dois PHP) com o **vendor do 8.5 da integracao**: `bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+`
(`ecidade/composer-85.json` e `composer-85.lock` com a troca do `lcobucci/jwt` da PHP8-60 e os 9 pacotes da PHP8-87), 167 pacotes em `runtime-85/vendor`. Sem banco.

## Como foi medido

- **Imagens do projeto** (`docker/php74-apache` -> PHP 7.4.33 e `docker/php85-apache` -> PHP 8.5.13, o `php.ini` delas e o `paridade-56.ini` do 8.5 montado em `conf.d`), `--network none`.
  Para ver os `Deprecated` a execucao usa `-d display_errors=stderr -d error_reporting=E_ALL` (o `php.ini` do 8.5 so os registra).
- **7.4:** vendor do PR (`composer install` da `ecidade/composer.lock` + `composer dump-autoload` com o `composer.json` real), montado em `/w/ecidade/vendor`.
  **8.5:** `runtime-85/vendor`, montado em `/w/ecidade/vendor` (o autoload resolve os `files` do projeto a partir de `dirname(vendor)`).
- `config/` so com os arquivos versionados (`git archive HEAD ecidade/config`; `config/application.php` local fora), `.env` vazio se houver um local, chaves do Passport geradas na hora com `openssl`,
  `storage/` e `bootstrap/cache/` gravaveis em pasta nova. `bootstrap.php`, `bootstrap/app.php` e o Kernel de console rodam sem alteracao (como o `artisan`).
- Script de medicao: `scratchpad/laravel_init.php`; runner do zero: `scratchpad/roda_inicializacao.sh` (falha se o `docker run` falhar ou a saida vier vazia).

## Resultado (criterio 1): 1.932 linhas iguais, 1 diferenca explicada

Saidas: `laravel85-inicializacao/saida-7.4.txt` (1.932 linhas) e `saida-8.5.txt` (1.933); diferenca: `diferenca-7.4-8.5.txt` (3 linhas).

| Item | 7.4 (vendor do PR) | 8.5 (vendor do 8.5) |
|---|---|---|
| Versao do framework | 8.73.2 | 8.73.2 |
| Rotas (metodos, URI, nome, acao, middleware, dominio) | 1.427 | 1.427, **identicas** |
| Comandos do artisan | 112 | 112, identicos |
| Configuracao efetiva (chaves e tipos) | 307 | 308: so `logging.channels.deprecations` |
| Providers carregados / adiados | 43 / 0 | 43 / 0, identicos |
| Aliases, fuso, `env()`, `Cache::put` (60 s), sessao (`file`, `laravel_session`), Handler | iguais | iguais |

**A unica diferenca** e a chave `logging.channels.deprecations` (valor `NULL`): o Laravel 8 a cria ao tratar um `Deprecated`, e so ha `Deprecated` no 8.5. Some se nao houver nenhum aviso; nao e erro da inicializacao.

## O que o vendor novo mudou em relacao a preliminar (criterio 3)

Mesmo resultado funcional da preliminar (rotas, comandos, providers, configuracao, `env()`, cache, sessao, Handler: a mesma unica diferenca). Muda a lista de avisos:

| | Preliminar (vendor do PR no 8.5) | Aceite (vendor do 8.5) |
|---|---|---|
| `Deprecated` ao subir o kernel no 8.5 | 15 | **12** |
| `lcobucci/jwt` (`Token.php:75,77,289`) | 3 | **0** (4.1.5) |
| Guzzle promises (`functions.php:24,262,263,288,289,310`) | 6 | 6 |
| Opis Closure (`functions.php:32`), Laravel `helpers.php:184,375` | 3 | 3 |
| Codigo do e-Cidade: `ParameterBag.php:133`, `:142`; `config/application.default.php:27` (`E_STRICT`) | 3 | 3 |

Lista completa em `laravel85-inicializacao/deprecated-8.5.txt` (`grep -c '^Deprecated' <saida do stderr>`).

Pacotes que mudam entre a `composer.lock` do PR e o vendor do 8.5 (dependencias, `composer-85.lock`): `lcobucci/jwt` 3.4.0 -> 4.1.5 (+ `lcobucci/clock` 2.0.0), `mpdf/mpdf` 8.2.4 -> 8.2.6,
`ezyang/htmlpurifier` 4.17.0 -> 4.19.0, `laminas/laminas-escaper` 2.12.0 -> 2.18.0, `nette/schema` 1.2.5 -> 1.3.3, `nette/utils` 3.2.10 -> 4.0.8, `fakerphp/faker` 1.10.0 no lugar de `fzaninotto/faker` (dev),
`cweagans/composer-patches` 1.7.3 (aplica o patch do `dompdf` 0.8.6).

## Correcao no codigo (criterio 2)

Nenhuma: o 8.5 sobe como o 7.4 sem mexer em arquivo (nem em `app-85/`). Os 3 `Deprecated` do codigo do e-Cidade ficam como ponteiro para quem faz o lint do 8.5: mudar `ParameterBag.php`
ou `config/application.default.php` mexe em arquivo que o 7.4 le (o atributo `#[\ReturnTypeWillChange]` e comentario no 7.4, mas a retirada de `E_STRICT` muda o nivel de erro).

## Repetir

```bash
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+     # vendor do 8.5 em runtime-85/vendor
bash scratchpad/roda_inicializacao.sh [pasta-de-trabalho]                                  # 7.4 e 8.5 nas imagens do projeto, compara
diff <pasta>/saida-7.4.txt docs/migracao-laravel/laravel85-inicializacao/saida-7.4.txt     # referencia do 7.4
```
