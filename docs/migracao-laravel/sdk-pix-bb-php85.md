# SDK do Pix do BB (`dbseller/sdk-api-pix-bb` 2.0.0) no PHP 8.5 (PHP8-91)

**Resumo:** com o composer do 8.5 de hoje (Laravel 8, `guzzlehttp/guzzle` 7.5.0 exato, como no PR) o SDK 2.0.0 roda no 8.5.12 **sem patch e sem mudar a trava**. Contra um dublê HTTP local, sem rede, os 8 pedidos saem iguais byte a byte ao 7.4 e os 4 casos (sucesso, 400, 500, resposta inválida) dão o mesmo resultado. O patch de 12 linhas só passa a ser necessário com o Guzzle 8 (Laravel 13): fica preparado em `anexos/pix-bb/` para a tarefa que subir o Laravel.

## O que o PR já traz

`ecidade/composer.json` e `composer-85.json` pedem `"dbseller/sdk-api-pix-bb": "^2.0"` e `"guzzlehttp/guzzle": "7.5.0"`; a trava tem o SDK 2.0.0, Guzzle 7.5.0, `guzzlehttp/promises` 1.5.3 e `guzzlehttp/psr7` 2.7.0. O SDK declara `guzzlehttp/guzzle` `7.5.0` exato e `php >=7.4.0`. O único código do sistema que o usa é `ecidade/app/Domain/Tributario/Arrecadacao/Pix/Bancos/BancoDoBrasil.php` (`Oauth2Api::gerarAccessToken` e `QrCodesApi::criaBoletoBancarioId`).

## Diferença 1.0.0 para 2.0.0 (critério 1)

Tags do repositório público `https://github.com/DBSeller/sdk-api-pix-bb.git`: 1.0.0, 2.0.0 e 3.0.0 (esta última não é usada). `git diff 1.0.0 2.0.0`:

| Arquivo | Linhas | O quê |
|---|---|---|
| `composer.json` | 5 | `php >=5.5` para `>=7.4.0`; `guzzlehttp/guzzle` `^6.2` para `7.5.0`; versões das dependências de desenvolvimento |
| `lib/Api/Oauth2Api.php` | 2 | `\GuzzleHttp\Psr7\build_query` para `\GuzzleHttp\Psr7\Query::build` |
| `lib/Api/QrCodesApi.php` | 12 | idem (14 trocas ao todo, nenhuma outra) |

As 12 chamadas `\GuzzleHttp\json_encode` de `QrCodesApi.php` continuam na 2.0.0 (e na 3.0.0). No Guzzle 7 a função existe (obsoleta); o Guzzle 8 a removeu.

## Prova contra o dublê (critério 2)

Anexos em `docs/migracao-laravel/anexos/pix-bb/`: `double.php` (servidor `php -S 127.0.0.1`, grava cada pedido e responde sucesso, 400, 500 ou JSON inválido), `exercicio.php` (usa o SDK como o `BancoDoBrasil.php`) e `rodar.sh`. Tudo em contêiner `--network none`; nenhuma chamada real, nenhum banco. Credenciais e chave são texto de teste, o cabeçalho `Authorization` sai mascarado (`Basic <segredo>`, `Bearer <segredo>`).

- **7.4:** `php:7.4-cli` com um `vendor/` de 9 pacotes nas versões da `composer.lock` do 7.4 (SDK 2.0.0, Guzzle 7.5.0, promises 1.5.3, psr7 2.7.0, `psr/http-client` 1.0.3, `psr/http-factory` 1.1.0, `psr/http-message` 1.1, `ralouphie/getallheaders` 3.0.3, `symfony/deprecation-contracts` 2.5.3), montado com o Composer fora do repositório.
- **8.5:** `php:8.5-cli` (8.5.12) com o `runtime-85/vendor` real, instalado da trava do 8.5.

| Comparação | Resultado |
|---|---|
| 8 pedidos (2 por situação: OAuth e `arrecadacao-qrcodes`): método, URI com `gw-dev-app-key`, cabeçalhos, corpo | **iguais byte a byte** (mesmo `sha256`) |
| sucesso: token `tok-do-duble` e `InlineResponse201` com os 6 campos | igual |
| 400 e 500: `ClientException`/`ServerException` do Guzzle e `ApiException` `[400]`/`[500]` do SDK, mesma mensagem | igual |
| resposta inválida (`{nao-e-json`, HTTP 201): token `NULL` e `criaBoletoBancarioId` `NULL` | igual |

A única diferença na saída é o texto de um aviso do PHP, no caso de resposta inválida, em `lib/Api/Oauth2Api.php:84` (`$bodyJson->{'access_token'}` com `$bodyJson` nulo):

- 7.4: `Notice: Trying to get property 'access_token' of non-object`
- 8.5: `Warning: Attempt to read property "access_token" on null`

Onde isso aparece depende de por onde a chamada entra. Os controladores do Pix (`RecibobarpixController`, `ArrecadacaoPixItbiService`) rodam pelo Laravel (`FrontController.php` manda `v4/` e `rest/v1/` para `public/index.php`), e lá o `HandleExceptions` do Laravel 8 faz `error_reporting(-1)` e transforma qualquer aviso em `ErrorException`. Medido com um tratador igual (`PIX_LARAVEL=1`): no caso de resposta inválida, `gerarAccessToken` **lança `ErrorException` nos dois runtimes**, só com o texto diferente (o mesmo do Notice/Warning acima); os outros 7 resultados e os 8 pedidos continuam iguais. O `catch (Exception $e)` do SDK não segura: no namespace `Swagger\Client\Api` ele resolve para uma classe que não existe. Ou seja, nos dois a resposta inválida do banco vira erro do Laravel (mesma classe de falha); o que muda é só a mensagem, que o usuário vê se o `Handler` a mostrar (modo debug) ou lê no log.

Pela entrada legada (`app.php`), que não é a do Pix, a máscara de `config/application.default.php:22,27` (`bootstrap.php:77` só a sobrescreve se existir um `config/application.php` local; vale quando não há) (`display_errors` falso, `E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED & ~E_STRICT`) esconde o aviso nos dois; repetida a prova com essa máscara (`PIX_ER=22517`), a saída é idêntica e sem aviso. O contêiner do 8.5 sobe com `display_errors = Off`.

## Guzzle 8 (Laravel 13): patch pronto, não aplicado (tarefa do Laravel 13)

Com `guzzlehttp/guzzle` `8.5.0 as 7.5.0` (alias, para o resolvedor aceitar a restrição exata do SDK) o SDK 2.0.0 só quebra nas 12 chamadas `\GuzzleHttp\json_encode`. `anexos/pix-bb/sdk-api-pix-bb-guzzle8.patch` troca cada uma por `\GuzzleHttp\Utils::jsonEncode` (12 trechos, 24 linhas, só em `lib/Api/QrCodesApi.php`; formato `-p1`, o que o `cweagans/composer-patches` espera em `extra.patches`). Medido no 8.5.12 com Guzzle 8.5.0, promises 3.1.1 e psr7 3.5.1: com o patch, os **8 pedidos saem iguais aos do 7.4**; as classes de resultado e de exceção nos 4 casos também. O texto das exceções muda por conta do Guzzle 8 (resposta na mesma linha, sem a query `?gw-dev-app-key=...` na URL da mensagem), e vale conferir quando o Laravel 13 entrar. Não foi copiado nenhum arquivo do SDK (licença proprietária): o patch só tem as linhas trocadas e uma de contexto.

## O que não foi feito

- Sem banco e sem chamada ao banco real; só o dublê.
- Falta, para depois, a prova pela rota HTTP do Laravel (`/v4`), que precisa de banco.
- Nada muda em `composer-85.json`, `composer-85.lock`, `composer.json` ou `composer.lock` do 7.4.
- O patch fica anexado e **não aplicado**: o composer do 8.5 de hoje usa Guzzle 7.5.0 e não precisa dele.

## Como repetir

```
bash docs/migracao-laravel/anexos/pix-bb/rodar.sh php:7.4-cli <vendor-7.4> /tmp/74.txt [mascara]
ECIDADE=1 bash docs/migracao-laravel/anexos/pix-bb/rodar.sh php:8.5-cli runtime-85/vendor /tmp/85.txt [mascara]
diff <(sed -n '/---PEDIDOS/,$p' /tmp/74.txt) <(sed -n '/---PEDIDOS/,$p' /tmp/85.txt)
```
