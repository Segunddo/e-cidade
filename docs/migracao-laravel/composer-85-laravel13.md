# Composer do 8.5 com Laravel 13 e Passport 13 (PHP8-62)

**Resumo:** a trava do 8.5 (`ecidade/composer-85.lock`) passa a ter `laravel/framework` 13.43.0 e `laravel/passport`
13.12.0, com 171 pacotes. Ela foi gerada com o comando único (`docker/composer-85/composer-85.sh`), sem banco e sem subir
o sistema.

- **Pacotes:** sobre a trava anterior (Laravel 8, depois da PHP8-87), entram 19, saem 15, 48 sobem de versão maior e
  80 ficam iguais.
- **Avisos de segurança:** nenhum aviso fora da lista do 7.4. O `config.audit.ignore` não mudou.
- **PHP 8.5:** os mesmos 2 pacotes de antes ainda excluem o 8.5, os da PHP8-70.
- **Mudança de API:** a única quebra que já aparece ao carregar as classes é a dos 20 comandos de `src/Console/Command/`
  com o Symfony Console 7+.
- **7.4:** o `composer.json` e o `composer.lock` do 7.4 não mudam.

Medido em 20/11/2026 com o Composer 2.11.2 / PHP 8.5.12 (imagem de `docker/composer-85/`). Os trechos rodaram nas
imagens construídas de `docker/php74-apache` (PHP 7.4.33) e `docker/php85-apache` (PHP 8.5.13), em contêineres
`--network none`.

## O que mudou no `composer-85.json` (critério 1)

O Laravel 13 e o Passport 13 não resolvem sobre a lista do PR. Cada linha abaixo foi um bloqueio do Composer, e cada
um foi resolvido com a menor mudança que destravou o seguinte.

| Pacote | PR (7.4) | 8.5 | Bloqueio | Trava |
|---|---|---|---|---|
| `laravel/framework` | `^8.0` | `^13.0` | objetivo | v13.43.0 |
| `laravel/passport` | `^10.0` | `^13.0` | objetivo | v13.12.0 |
| `guzzlehttp/guzzle` | `7.5.0` | `7.16.3 as 7.5.0` | o Laravel 13 pede `^7.8.2 \|\| ^8.0`, e o `dbseller/sdk-api-pix-bb` 2.0.0 fixa `7.5.0` exato (ver *Guzzle* abaixo) | 7.16.3 |
| `symfony/console`, `process`, `filesystem`, `yaml` | `v5.3.7` / `v5.4.12` exatos | `^7.4 \|\| ^8.0` | o Laravel 13 pede `^7.4 \|\| ^8.0` (a mesma restrição dele) | v8.1.x |
| `barryvdh/laravel-ide-helper` (require e require-dev) | `^2.4` / `^2.8` | `^3.0` | a 2.x vai só até o `illuminate/console` 10 | v3.8.0 |
| `lcobucci/jwt` | `~4.1.0` (PHP8-60) | `^5.6` | `league/oauth2-server` 9 (Passport 13) pede `^5.6` | 5.7.0 |
| `lcobucci/clock` | `2.0.0` (PHP8-60) | `^3.0` | o `lcobucci/jwt` 5 pede `^3` | 3.7.0 |
| `doctrine/dbal` | `2.*` | sai | o `symfony/http-foundation` 7.4+ declara conflito com `doctrine/dbal <3.6`; o Laravel 11+ não precisa dele | — |
| `laravel/tinker` | `^2.6` | `^3.0` | a 2.x vai só até o `illuminate/support` 12 | v3.2.0 |
| `nfephp-org/sped-common` | `~5.0.40` | `~5.1.1` | a 5.0.x pede `psr/log ^1.0`, e o Monolog 3 do Laravel 13 pede `^2 \|\| ^3`. A 5.1.1 é a primeira que aceita `^1.0\|\|^2.0\|\|^3.0` | v5.1.18 |

Ficam como estavam: o dompdf 0.8.6 com o patch da PHP8-87 (o `install` mostra `Applying patches for dompdf/dompdf`),
as versões que a PHP8-87 escolheu (`mpdf` 8.2.6, `htmlpurifier` 4.19.0, `laminas-escaper` 2.18.0, `nette/schema`
1.3.3, `nette/utils` 4.0.8, `phpspreadsheet` 1.29.1) e o `intervention/image` 2.7.2.

**`doctrine/dbal`:** nenhum arquivo do código cita `Doctrine\DBAL`. O único uso indireto é o `->change()` de 2
migrations (`2021_10_25_083540_alter_secret_to_oauth_clients.php:17,29` e
`2024_08_13_093320_M28685_ajuste_schema_tabela_mensageriaacordo.php:243`). No Laravel 11+ o `change()` é nativo, mas
precisa repetir todos os modificadores da coluna. Isso fica para quem rodar as migrations no 8.5.

### Guzzle: 7.16.3 com alias, não 8

O `dbseller/sdk-api-pix-bb` 2.0.0 declara `guzzlehttp/guzzle` `7.5.0` exato. Com o alias `7.16.3 as 7.5.0`, o resolvedor
aceita a restrição do SDK e instala o 7.16.3, que atende ao `^7.8.2` do Laravel 13. O alias só existe no
`composer-85.json`. O 7.4 continua com o 7.5.0 do PR.

O Guzzle 8 não resolve: o `intervention/image` 2.7.2, a última 2.x, exige `guzzlehttp/psr7 ~1.1 || ^2.0`, e o Guzzle 8
exige `psr7 ^3.4` (`composer why-not --locked guzzlehttp/psr7 3.4.0`). O pacote é registrado em
`configuration/app.php:190,239` e usado em `app/Domain/Assinador/Controllers/AssinadorAPI.php:471-473`. A 3.x muda a
API (`Image::make` e `Image::canvas` não existem nela).

Com o Guzzle 7, o SDK roda **sem patch**: o 7.16.3 ainda tem `\GuzzleHttp\json_encode`
(`vendor/guzzlehttp/guzzle/src/functions.php:256`). O patch para o Guzzle 8 continua só como anexo da PHP8-91
(`anexos/pix-bb/sdk-api-pix-bb-guzzle8.patch`) e não entra em `extra.patches`.

**Prova do SDK com o 7.16.3:** os scripts são os da PHP8-91 (`anexos/pix-bb/rodar.sh`), com o dublê local e sem rede.

- **7.4:** imagem de `docker/php74-apache`, com um `vendor/` dos 9 pacotes nas versões do `composer.lock` do PR (Guzzle
  7.5.0).
- **8.5:** imagem de `docker/php85-apache`, com o `runtime-85/vendor` da trava nova (Guzzle 7.16.3, `psr7` 2.13.5,
  `promises` 2.6.1).

| Modo | 8 pedidos (sha256 da seção `---PEDIDOS`) | Diferença na saída |
|---|---|---|
| padrão | iguais nos dois | só o texto do aviso do PHP no caso de resposta inválida (`Notice: Trying to get property…` × `Warning: Attempt to read property…`), o mesmo da PHP8-91 |
| `PIX_LARAVEL=1` | iguais nos dois | só o texto da `ErrorException` no mesmo caso, o mesmo da PHP8-91 |
| máscara `22517` | iguais nos dois | nenhuma (arquivos idênticos) |

As mensagens das exceções do Guzzle (400 e 500) saem iguais às do 7.5.0, ao contrário do que a PHP8-91 mediu com o
Guzzle 8.

## Como saiu a trava

```bash
bash docker/composer-85/composer-85.sh update --no-install --no-scripts --ignore-platform-req=php+ \
  laravel/framework laravel/passport laravel/tinker barryvdh/laravel-ide-helper guzzlehttp/guzzle \
  symfony/console symfony/process symfony/filesystem symfony/yaml lcobucci/jwt lcobucci/clock doctrine/dbal \
  nfephp-org/sped-common dbseller/sdk-api-pix-bb maennchen/zipstream-php mpdf/psr-http-message-shim -W
# o -W tinha subido o nette; volta para as versoes da PHP8-87:
bash docker/composer-85/composer-85.sh update --no-install --no-scripts --ignore-platform-req=php+ \
  nette/schema nette/utils --with nette/schema:1.3.3 --with nette/utils:4.0.8
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+
```

O `maennchen/zipstream-php` (2.2.6, do `phpspreadsheet`) e o `mpdf/psr-http-message-shim` (1.0.0, do `mpdf`) entram na
lista porque pedem `psr/http-message ^1.0`, e o `league/oauth2-server` 9 pede `^2.0`. Eles sobem para 3.2.2 e 2.0.1;
as restrições dos pacotes que os pedem aceitam as duas versões.

Conferências (a ferramenta está em `scratchpad/`):

| O quê | Comando | Resultado |
|---|---|---|
| entram, saem, versão maior | `python3 scratchpad/php8_62_compara.py <trava anterior> ecidade/composer-85.lock` (anterior: `git show 016147447:ecidade/composer-85.lock`) | 19, 15, 48; 167 → 171 |
| pacotes que excluem o PHP 8.5 | `php scratchpad/php8_62_php85.php ecidade/composer-85.lock`, na imagem de `docker/composer-85/` | 2: `bacon/bacon-qr-code` 1.0.3 e `khanamiryan/qrcode-detector-decoder` 1, os mesmos da PHP8-87 (ficam para a PHP8-70) |
| avisos fora da lista do 7.4 | `bash docker/composer-85/composer-85.sh audit --locked` | nenhum |
| 7.4 intacto | `sha256sum ecidade/composer.json ecidade/composer.lock` | `69367bdc…` e `38fe5a63…`, os da base |

## Pacotes que sobem de versão maior e onde o código os usa (critério 2)

Contagem de arquivos e linhas do código versionado de `ecidade/` (sem `vendor/`) que citam cada pacote:
`sh scratchpad/php8_62_usos.sh` (padrões em `scratchpad/php8_62_usos.tsv`, 41 pacotes). O inventário das mudanças do
Laravel 8 ao 13 (o que muda no código do Laravel) está em `inventario-8-a-13.md`. Esta lista cobre as bibliotecas.

| Pacote | Versão | Arquivos / linhas | O que muda para o código |
|---|---|---|---|
| `nesbot/carbon` | 2.72.5 → 3.15.1 | 118 / 279 | Carbon 3 (diferenças com sinal e fracionárias; `createFromTimestamp` em UTC). Datas: PHP8-55 |
| `symfony/http-foundation` | 5.4 → 8.1 | 130 / 135 | 107 dos usos são `Response` (constantes de status); 15 `Request`, 6 `ParameterBag`, 5 `JsonResponse` |
| `symfony/console` | 5.3.7 → 8.1 | 20 / 88 | **quebra:** os 20 comandos de `src/Console/Command/` (Extension 5, Modification 8, Plugin 5, Tools 2) declaram `configure()` e `execute()` sem tipo de retorno. O Console 7+ exige `configure(): void` e `execute(...): int`, e a classe nem carrega (abaixo) |
| `symfony/http-kernel` | 5.4 → 8.1 | 12 / 14 | só as exceções HTTP (`NotFoundHttpException` 7, `NotAcceptableHttpException` 3...) |
| `symfony/finder` | 5.4 → 8.1 | 10 / 11 | exceções e `Finder` |
| `psr/http-message` | 1.1 → 2.0 | 9 / 14 | só usa as interfaces; nenhuma classe do código as implementa |
| `symfony/yaml` | 5.4.12 → 8.1 | 3 / 4 | `src/Configuracao/Formulario/Arquivo/Yaml/` |
| `symfony/process` | 5.3.7 → 8.1 | 1 / 1 | `src/Task/Executor/Background.php` |
| `symfony/translation` | 5.4 → 7.2 | 1 / 1 | `api/V1/Controllers/Auth/Login.php` (API V1, que o PR já não encaminha) |
| `monolog/monolog` | 2.9 → 3.13 | 1 / 1 | `configuration/logging.php` (`StreamHandler`) |
| `league/oauth2-server` | 8.3 → 9.4 | 1 / 2 | `app/Domain/Configuracao/Usuario/Services/AuthService.php`. Login e Passport: PHP8-39 |
| `guzzlehttp/psr7` | 2.7 → 2.13 | 1 / 2 | o mesmo `AuthService.php` (`Response`, `ServerRequest`); não é versão maior |
| `league/flysystem` | 1.1 → 3.36 | 0 / 0 | só pelo `Storage` do Laravel: PHP8-77 |
| `swiftmailer/swiftmailer` | sai (Symfony Mailer 8.1 entra) | 0 / 0 | só pelo `Mail` do Laravel: PHP8-51 |
| `lcobucci/jwt`, `phpseclib` 3 → 4, `firebase/php-jwt` 6 → 7 | | 0 / 0 | só por dentro do Passport: PHP8-39 |
| `doctrine/dbal`, `opis/closure`, `nyholm/psr7`, `neitanod/forceutf8`, `webmozart/assert` | saem | 0 / 0 | nada no código |
| `vlucas/phpdotenv` | 5.6.1 → 5.8.0 | | não é versão maior |

Os outros pacotes que sobem de versão maior (contratos `psr/*`, `symfony/*-contracts`, `brick/math`, `ramsey/collection`,
`voku/portable-ascii`, `egulias/email-validator`, `league/event`, `maennchen/zipstream-php`...) têm 0 citações no código:
só o Laravel e as bibliotecas os usam.

**Classes que deixam de carregar:** foram 288 arquivos de `ecidade/`, os que citam um desses pacotes e declaram
classe, interface ou trait. Cada um foi carregado num processo próprio no 8.5 pelo `docker/composer-85/roda-isolado.sh`,
primeiro com o vendor da trava anterior e depois com o da nova (`scratchpad/php8_62_carrega_lista.php` chama
`scratchpad/php8_62_carrega.php` arquivo por arquivo). Com a trava anterior carregam 270, e com a nova, 250. A
diferença são exatamente os 20 comandos do Console:

```
Fatal error: Declaration of ECidade\Console\Command\Tools\DiffCache::configure() must be compatible with
Symfony\Component\Console\Command\Command::configure(): void
```

As outras 18 falhas são iguais nas duas e não vêm dos pacotes. São 16 de `api/V1/`: Pimple, que o PR tirou, e classes
que o carregador do trecho não acha. As outras 2 são do legado: `FpdfMultiCellBorder` e `modification()`.

Lista dos arquivos e comando:

```bash
(cd ecidade && git ls-files -z -- '*.php' ':!vendor/' | xargs -0 grep -laP -- "$(cut -f2 ../scratchpad/php8_62_usos.tsv | paste -sd'|')" \
  | xargs grep -laP '^\s*(abstract\s+|final\s+)?(class|interface|trait)\s+\w+') > scratchpad/php8_62_carrega.lst   # 288
bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/php8_62_carrega_lista.php /trecho/php8_62_carrega.lst > l13.tsv
VENDOR=<vendor da trava anterior> bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/php8_62_carrega_lista.php /trecho/php8_62_carrega.lst > l8.tsv
grep -c $'\tOK$' l8.tsv l13.tsv   # 270 e 250
```

O vendor da trava anterior sai de `git show 016147447:ecidade/composer-85.lock`, instalado numa pasta à parte com o
mesmo contêiner do `composer-85.sh`.

## O que não foi feito

- O sistema não subiu com o Laravel 13: a inicialização no 8.5 é a PHP8-62 (aceite).
- Os 20 comandos do Console não foram corrigidos: é mudança de código, fica para a tarefa que cuidar do `bin/console`.
- Nada rodou contra banco.
