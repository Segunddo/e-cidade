# Passport 13 + oauth2-server 9 sobre o login do PR: rascunho sem banco (PHP8-39)

**Resumo:** o código do login do PR (`AuthServiceProvider`, `AuthService`, `Usuario`) não sobe com o Laravel 13.43.0 / Passport 13.12.0 / `league/oauth2-server` 9.4.1 / `lcobucci/jwt` 5.7.0: a primeira quebra é `Passport::routes()` (`AuthServiceProvider.php:31`). Com **dois patches** (um arquivo do PR com 26 linhas mudadas e uma classe nova de 32 linhas, só do 8.5), o password grant, o refresh, o Bearer e as rotas com `clientCredential` funcionam e dão o mesmo resultado do 7.4 (Laravel 8.73.2 / Passport 10.4.2) nas situações medidas; o 7.4 fica **idêntico antes e depois** dos patches. Tudo sem banco, em contêineres `--network none`. Nada foi aplicado em `ecidade/`; os patches ficam anexados para depois da T-119 (trava do Laravel 13). Complementa `docs/registro/passport13-leitura-e-plano.md` (os 14 pontos, por leitura).

## Como foi medido

- **Lado 13:** `anexos/passport13/composer-13/composer.json` (Laravel `^13.0`, Passport `^13.0`, Testbench 11) resolve em Laravel 13.43.0, Passport 13.12.0, `league/oauth2-server` 9.4.1 e `lcobucci/jwt` 5.7.0, instalado com a imagem pinada do Composer do 8.5. `boot-13.php.txt` e `grant-13.php.txt` (PHP 8; a extensão `.txt` é para o `php -l` do 7.4 do CI não os ler: copie como `boot.php`/`grant.php`) sobem um app Testbench, registram o `AuthServiceProvider` do PR (`/pr/app`, ou o proposto) e o `PassportServiceProvider` na ordem do PR (`configuration/app.php`), com chaves RSA geradas na hora.
- **Lado 7.4:** `composer-10/composer.json` (Laravel 8.73.2, Passport 10.4.2, `league/oauth2-server` 8.3.2, `lcobucci/jwt` 3.4.0, Testbench 6, `platform.php` 7.4.33) e `boot10.php`/`grant10.php` no `php:7.4-cli`.
- **Sem banco:** o cliente OAuth, os repositórios de token e a busca do usuário são substituídos por classes em memória (`ClienteMem`, `AccessMem`, `RefreshMem`, `UsuarioMem`: só `findForPassport` troca a consulta; `validateForPassportPasswordGrant` e o resto do `Usuario` são do PR). O cliente usa o esquema de hoje: id inteiro `9999999`, `secret` em texto puro (`setRawAttributes`, sem passar pelo setter do 13), `password_client` = 1. A chamada é a do PR: `AuthService::requestToPassport` (`AuthService.php:359-393`), por reflexão, com `GuzzleHttp\Psr7\ServerRequest` e `Response`.

## O que quebra no 13 e a mudança mínima (critérios 1 e 2)

Numeração dos 14 pontos do registro da leitura.

| Ponto | O que se mediu no 13 com o código do PR como está | Mudança mínima | Prova |
|---|---|---|---|
| 1 `Passport::routes()` | `Error: Call to undefined method Laravel\Passport\Passport::routes()` em `AuthServiceProvider.php:31`: o boot do app para | no próprio arquivo, `if (method_exists(Passport::class, 'routes'))` mantém a chamada de hoje; senão, `config(['passport.path' => 'v4/oauth'])` no `register()` (as rotas vêm do provider do pacote) | boot ok no 13; no 7.4 as 15 rotas de `v4/oauth` são as mesmas antes e depois |
| 2 password grant | sem `Passport::enablePasswordGrant()`: `grant_type=password` (o login) e `refresh_token` voltam `The authorization grant type is not supported` | `Passport::enablePasswordGrant()` no ramo 13 | password e refresh emitem token (`token_type`, `expires_in`, `access_token`, `refresh_token`), `expires_in` ≤ 86400 |
| 3 `tokensExpireIn`/`refreshTokensExpireIn` | compatível (aceitam `Carbon`) | nenhuma | `expires_in` entre 80000 e 86400 s |
| 4 `HasApiTokens` sem `OAuthenticatable` | **não quebra no que o PR faz**: o guard `api` entrega o `Usuario` do PR com `token()` (`Laravel\Passport\AccessToken`, com `revoke()`), `getProviderName()` devolve `users`, `Passport::actingAs()` aceita; só o contrato não está declarado | nenhuma; o `implements` não pode entrar em `Usuario.php` (a interface não existe no Passport 10); uma subclasse só do 8.5 como `model` do provider não foi proposta: pela leitura de `HasApiTokens.php:123`, `getProviderName()` usa `is_a($this, $config['model'])`, e um `Usuario` puro (como o `new Usuario()` de `ClientRepository.php:18` do PR) deixaria de achar o provider | guard `api`: `implementa=false` e o usuário resolve |
| 5 `findForPassport` / `validateForPassportPasswordGrant` | compatível: o `Bridge\UserRepository` do 13 os chama | nenhuma | login do usuário de teste emite token |
| 6 `$usuario->token()->revoke()` | `token()` é `AccessToken`, e `revoke()` existe (`AccessToken.php:92`); o efeito é um `UPDATE` em `oauth_access_tokens` | nenhuma | só confere o método; o efeito precisa de banco (P6) |
| 7 `respondToAccessTokenRequest` | `AuthService::requestToPassport` roda sem mudança com `league/oauth2-server` 9.4.1 | nenhuma (a versão do `lcobucci/jwt` é da trava: o 9 pede `^5.6`, a T-101 fixou `~4.1.0` para o 8.3.2) | password, refresh e Bearer ok; no 13, o refresh revoga o access token anterior (o Bearer do token velho dá `access_denied`) |
| 8 `$clientUuids` | com o padrão (`true`) o grant, o refresh e o Bearer funcionam com id inteiro `9999999`; só afeta a **criação** de cliente pelo Passport (`Client.php:72`) | **nenhuma** (o rascunho tinha `Passport::$clientUuids = false` e foi tirado); só faria falta se algo criar cliente pelo Passport, o que o PR não faz (as migrations inserem) | grant, refresh e Bearer com e sem a linha |
| 9 segredo sem hash | `RuntimeException: This password does not use the Bcrypt algorithm` em `BcryptHasher.php:89`, no password, no refresh e no segredo errado | classe nova `App\Auth\SegredoClienteTextoPuro` (`hash_equals`; 32 linhas, em `ecidade/app-85/`, que o 7.4 não lê) ligada **só** ao `Bridge\ClientRepository` (`$this->app->when(...)->needs(Hasher::class)->give(...)`, no `register()` do ramo 13) | segredo certo valida; errado: `invalid_client` (código 4); vazio já é recusado por `! empty($clientSecret)` em `Bridge/ClientRepository.php`; o hasher da aplicação não muda |
| 10 coluna `provider` | sem banco não se mede | nenhuma | P1 |
| 11 `clientCredential` | o alias do Kernel (`CheckClientCredentials`) aponta para classe que não existe: a rota dá 500 | `aliasMiddleware('clientCredential', CheckToken::class)` no ramo 13 do `AuthServiceProvider` (o provider roda depois do Kernel, então vence) | ver a tabela abaixo |
| 12 `createToken('tokenId')` | a escolha do cliente pessoal e a emissão pelo servidor chegam até o `UPDATE` do nome em `oauth_access_tokens`, que precisa de banco | nenhuma até medir | P7 |
| 13 `PruneOldTokens`, 14 provider manual | compatíveis (leitura) | nenhuma | — |

**Rotas `clientCredential`, mesmo roteiro nos dois lados** (HTTP, `Kernel` do Laravel, rota `GET` simples com o middleware):

| Token | 7.4: `CheckClientCredentials` | 13: alias do PR (sem patch) | 13: `CheckToken` (patch) | 13: `EnsureClientIsResourceOwner` |
|---|---|---|---|---|
| de cliente (`client_credentials`) | 200 | 500 | 200 | 200 |
| inválido | 401 | 500 | 401 | 401 |

`CheckToken` mantém o resultado do 7.4 nas situações medidas; a troca para `EnsureClientIsResourceOwner` é decisão do grupo.

## Diferenças que o 13 traz e o PR deve saber

- **Rotas de `v4/oauth`:** o `Passport::routes()` do 10.4.2 registra 15 (`authorize` ×3, `token`, `token/refresh`, `clients` ×4, `scopes`, `tokens` ×2, `personal-access-tokens` ×3). O 13 registra 10: as 5 primeiras mais as do device code (`device`, `device/code`, `device/authorize` ×3). **Somem** `clients`, `scopes`, `tokens` e `personal-access-tokens` (10 rotas). Dentro de `ecidade/` (`git grep`) nada chama essas rotas; o que chama de fora (clientes externos, front) não se sabe: **pergunta para o grupo**.
- **Claim `sub` do token de cliente** (`client_credentials`): vazio (`""`) no `league/oauth2-server` 8.3.2 e igual ao id do cliente (`"9999999"`) no 9.4.1. No token do password grant o `sub` é o id do usuário nos dois lados, e `aud`, `scopes` e o cabeçalho (`{"typ":"JWT","alg":"RS256"}`) são iguais nos dois lados (medidos com a mesma chave).

## Patches propostos (aplicar depois da T-119)

`anexos/passport13/patches/`:
- `0001-auth-service-provider.patch`: `ecidade/app/Providers/AuthServiceProvider.php` (26 linhas mudadas: `register()` novo, `boot()` com o `if (method_exists(Passport::class, 'routes'))`).
- `0002-segredo-cliente-texto-puro.patch`: arquivo novo `ecidade/app-85/Auth/SegredoClienteTextoPuro.php`.

`git apply --check` passa sobre a `laravel/integracao-74`; os dois arquivos passam em `php -l` no 7.4 e no 8.5; o arquivo resultante é byte a byte o que o harness provou (`anexos/passport13/proposto/`). **7.4 igual:** `boot10.php` e `grant10.php` (Laravel 8.73.2, Passport 10.4.2) dão saída idêntica com o `AuthServiceProvider` original e com o proposto: o mesmo boot (as mesmas 15 rotas, sem alias `clientCredential`), password, refresh, Bearer, segredo errado e as 3 rotas `clientCredential` iguais. No composer do 8.5 de hoje (Laravel 8) o ramo novo também não roda, pelo mesmo `method_exists`.

## O que ainda precisa de banco (planejado, não feito)

P1 (esquema real de `oauth_*`, coluna `provider`), P2–P4 (token gravado em `oauth_access_tokens`/`oauth_refresh_tokens`, Bearer com usuário real), P5/P6 (`/v4/login` inteiro, `logout` com `revoke()`), P7 (`createToken` do cliente pessoal) e P9 (`PruneOldTokens`), conforme o plano do registro da leitura. A prova pela rota HTTP do app inteiro não foi feita: o harness usa o `Kernel` do Testbench, não o do PR.

## Repetir

Em uma pasta de trabalho fora do repositório (`pp13` e `pp10`), com `ecidade/` do checkout montado só para leitura:

```
# instalar (rede só aqui; a imagem pinada do Composer do 8.5 serve para os dois conjuntos)
cp anexos/passport13/composer-13/composer.json pp13/ ; cp anexos/passport13/composer-10/composer.json pp10/
docker run --rm --init --network host -u $(id -u):$(id -g) -v $PWD/pp13:/w -e COMPOSER_HOME=/w/.composer -w /w \
  ecidade-composer-85:2.11.2 composer --no-interaction update --no-scripts
docker run --rm --init --network host -u $(id -u):$(id -g) -v $PWD/pp10:/w -e COMPOSER_HOME=/w/.composer -w /w \
  ecidade-composer-85:2.11.2 composer --no-interaction update --no-scripts      # sem --ignore-platform-reqs: usa o platform.php 7.4.33 do composer.json (com a opção, o ramsey/uuid vem na versao do PHP 8 e da Parse error no 7.4)

# scripts e chaves
mkdir -p pp13/h pp13/s85/Providers pp13/s85/Auth pp13/keys pp10/keys
cp anexos/passport13/boot-13.php.txt pp13/h/boot.php ; cp anexos/passport13/grant-13.php.txt pp13/h/grant.php
cp anexos/passport13/boot10.php anexos/passport13/grant10.php pp10/
cp anexos/passport13/proposto/Providers/AuthServiceProvider.php pp13/s85/Providers/ ; cp anexos/passport13/proposto/Auth/SegredoClienteTextoPuro.php pp13/s85/Auth/
openssl genrsa -out pp13/keys/oauth-private.key 2048 ; openssl rsa -in pp13/keys/oauth-private.key -pubout -out pp13/keys/oauth-public.key
chmod 600 pp13/keys/* ; cp pp13/keys/* pp10/keys/

# rodar (sem rede); conferir o codigo de saida e que a saida nao esta vazia antes de comparar
docker run --rm --network none -u $(id -u):$(id -g) -v $PWD/pp13:/w -v $PWD/ecidade:/pr:ro -v $PWD/pp13/s85:/s85:ro ecidade-composer-85:2.11.2 php /w/h/grant.php proposto
docker run --rm --network none -u $(id -u):$(id -g) -v $PWD/pp10:/w -v $PWD/ecidade:/pr:ro -v $PWD/pp13/s85:/s85:ro php:7.4-cli php /w/grant10.php original   # e proposto: diff vazio
```
