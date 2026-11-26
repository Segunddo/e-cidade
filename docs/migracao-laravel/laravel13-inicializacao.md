# Inicialização do app do PR sobre o Laravel 13 no 8.5 (PHP8-62)

**Resumo:** esta medição repete o aceite da inicialização (`laravel85-inicializacao.md`), agora com o composer do 8.5 em
Laravel 13.43.0 + Passport 13.12.0. Tudo rodou sem banco.

- **Quebra:** o app do PR quebra **num ponto só**, `Passport::routes()` em `app/Providers/AuthServiceProvider.php:31`.
- **Correção:** a correção mínima tem 2 partes, e com ela o app sobe.
- **7.4:** continua igual: as 1.427 rotas são idênticas antes e depois, e a configuração ganha só a chave
  `passport.path`, que o Passport 10 não lê.
- **Rotas no 8.5:** das 1.427 rotas do 7.4, 1.412 saem idênticas. As 15 de `v4/oauth` viram 10, diferença aberta para a
  PHP8-39.
- **Resto da inicialização:** comandos, providers, `env()`, cache, sessão e Handler saem iguais ao 7.4, ou só ganham
  itens novos do framework.
- **Configuração:** nenhuma chave muda de tipo.

## Como foi medido

- Pelo `docker/composer-85/roda-isolado.sh`, que usa as imagens de `docker/php74-apache` (7.4.33) e
  `docker/php85-apache` (8.5.13) com o `php.ini` delas, `--network none` e as variáveis de teste do
  `ecidade/.env.example`.
- O trecho `scratchpad/php8_62_init_isolado.php` liga a exibição de erros no stderr e roda o mesmo
  `scratchpad/laravel_init.php` do aceite. Esse script carrega `bootstrap.php`, `bootstrap/app.php` e o Kernel de
  console, e lista versão, rotas, comandos, configuração (chaves e tipos), providers, `env()`, cache, sessão e Handler.
- **7.4:** vendor do PR (`composer install` do `ecidade/composer.lock` + `dump-autoload` com `ecidade/` em `/app`),
  passado em `VENDOR`.
- **8.5:** `runtime-85/vendor`, da trava do 8.5.
- Runner: `bash scratchpad/php8_62_init_l13.sh <vendor do 7.4> <pasta>`. Ele falha se o app não subir num dos lados.
- Valores que mudam comportamento: `scratchpad/php8_62_init_valores.php`, pelo mesmo `roda-isolado.sh`.

A saída do 7.4 aqui difere da do aceite só nos valores que vêm do `.env.example` (`APP_ENV=local`, `database.default`,
portas), porque o `roda-isolado.sh` os injeta. São os mesmos nos dois lados.

## O que quebra na inicialização (critério 1)

| Ordem | Onde | Mensagem | Tarefa |
|---|---|---|---|
| 1 | `app/Providers/AuthServiceProvider.php:31` | `Call to undefined method Laravel\Passport\Passport::routes()` | PHP8-39 (Passport 13), ponto 1 da leitura `docs/registro/passport13-leitura-e-plano.md` |

Corrigido esse ponto, nada mais impede o app de subir. Os 3 `Deprecated` que aparecem são do código do e-Cidade e
já existiam com o Laravel 8:

- `src/V3/Extension/ParameterBag.php:133` e `:142`;
- `config/application.default.php:27`, com `E_STRICT`.

Um `config/application.php` local, quando existe, repete o aviso do `E_STRICT`. Com o vendor do Laravel 8 no 8.5,
o aceite contou 12 `Deprecated`. Os 9 que eram do Guzzle promises, do Opis Closure e do `helpers.php` do Laravel saíram.

## A correção (critério 2)

Duas mudanças, no próprio arquivo:

1. `app/Providers/AuthServiceProvider.php`: `Passport::routes(null, ['prefix' => 'v4/oauth'])` só roda se o método
   existir (`method_exists`). O Passport 10 do 7.4 tem o método, então o 7.4 segue igual. O Passport 13 não tem e
   registra as rotas pelo próprio provider.
2. `configuration/passport.php` (novo): `'path' => 'v4/oauth'`. O Passport 13 lê o prefixo das rotas de
   `passport.path` ao registrar as rotas. Sem esse arquivo, elas iriam para `oauth/*`. Definir a chave no `boot()` do
   `AuthServiceProvider` não basta: medido, as rotas já estão registradas nessa hora. O Passport 10 junta este
   arquivo com a configuração dele, e a única mudança no 7.4 é a chave a mais.

**Prova de que o 7.4 fica igual:** a saída do 7.4 antes e depois difere em 2 linhas, `CONFIG chaves=307` → `308` e
`C passport.path : string`. As 1.427 rotas, os 112 comandos e os 43 providers saem iguais. `php -n -l` passou nos
2 arquivos, no 7.4 e no 8.5.

## O app no 8.5 comparado com o 7.4 (critério 3)

Saídas: `laravel13-inicializacao/saida-7.4.txt` e `saida-8.5.txt`; diferença: `diferenca-7.4-8.5.txt`.

| Item | 7.4 (Laravel 8.73.2) | 8.5 (Laravel 13.43.0) | Causa |
|---|---|---|---|
| Rotas | 1.427 | 1.422 | 1.412 idênticas (método, URI, nome, ação, middleware, domínio); as 15 de `v4/oauth` viram 10 (abaixo) |
| Comandos do artisan | 112 | 158 | os 112 continuam; os 46 novos são do framework e dos pacotes novos |
| Providers carregados | 43 | 45 | os 43 continuam; entram `Illuminate\Log\Context\ContextServiceProvider` e `Termwind\Laravel\TermwindServiceProvider` |
| Configuração (chaves) | 308 | 436 | nenhum tipo muda; 6 saem e 134 entram (abaixo) |
| Valores de `app.timezone`, `app.locale`, `cache.default`, `session.driver`/`lifetime`/`cookie`, `queue.default`, `filesystems.default`, `logging.default`, `database.default`, `auth.defaults.guard`, `hashing.driver` | | iguais | |
| `env()` (9 casos), cache `file` (TTL 60 s), sessão `file`/`laravel_session`, Handler (4 exceções) | | iguais | |

**Rotas `v4/oauth`, diferença aberta para a PHP8-39 (Passport 13), não resolvida aqui:**

- **Somem 10:** o Passport 13 tirou a API JSON de clientes, tokens pessoais, escopos e tokens autorizados.
  - `GET`/`POST v4/oauth/clients`, `PUT`/`DELETE v4/oauth/clients/{client_id}`;
  - `GET`/`POST v4/oauth/personal-access-tokens`, `DELETE v4/oauth/personal-access-tokens/{token_id}`;
  - `GET v4/oauth/scopes`;
  - `GET v4/oauth/tokens`, `DELETE v4/oauth/tokens/{token_id}`.
- **Entram 5 do fluxo de dispositivo:**
  - `GET v4/oauth/device`;
  - `GET`/`POST`/`DELETE v4/oauth/device/authorize`;
  - `POST v4/oauth/device/code`.
- **Ficam 5:**
  - `POST v4/oauth/token` sai idêntica, com `throttle`.
  - Nas outras 4, muda o middleware: `GET`, `POST` e `DELETE v4/oauth/authorize` e `POST v4/oauth/token/refresh`.
    - O `auth` vira `auth:web`, guarda explícita do `passport.guard`.
    - O `GET v4/oauth/authorize` fica só com `web`, sem `auth`.

**Configuração:**

- **Saem 6 chaves:**
  - `ide-helper.custom_db_types` e `ide-helper.include_factory_builders` (laravel-ide-helper 3);
  - `passport.client_uuids`, `passport.personal_access_client.id`, `passport.personal_access_client.secret` e
    `passport.storage.database.connection`, que o Passport 13 trocou por `passport.connection`.
- **Entram 134:** os padrões que o Laravel 11+ junta aos arquivos de `configuration/`, mais os dos pacotes. Os que
  mudam comportamento, medidos com `php8_62_init_valores.php`:

| Chave | 7.4 | 8.5 | Para quem |
|---|---|---|---|
| `session.same_site` | `null` | `"lax"` | cookie de sessão passa a sair com `SameSite=Lax`: PHP8-38 (middlewares e sessão) |
| `session.partitioned` | `null` | `false` | idem |
| `hashing.rehash_on_login` | `null` | `true` | o Laravel 11+ refaz o hash da senha no login: PHP8-39 |
| `auth.password_timeout` | `null` | `10800` | confirmação de senha; o código não usa `password.confirm` |
| `passport.guard` / `passport.middleware` | `null` | `"web"` / `[]` | PHP8-39 |
| `app.previous_keys` | `null` | `[]` | rotação de `APP_KEY`; sem efeito com a lista vazia |
| `logging.deprecations` | `null` | canal `null` | os `Deprecated` não vão ao log |
| `app.maintenance.driver` | `null` | `"file"` | modo de manutenção; o mesmo comportamento do 8 |

## Repetir

```bash
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+      # vendor do 8.5
bash scratchpad/php8_62_init_l13.sh <vendor do 7.4> /tmp/init13                               # 7.4 e 8.5, compara
diff /tmp/init13/saida-8.5.txt docs/migracao-laravel/laravel13-inicializacao/saida-8.5.txt
VENDOR=<vendor do 7.4> bash docker/composer-85/roda-isolado.sh 7.4 scratchpad/php8_62_init_valores.php
bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/php8_62_init_valores.php
```

Sem banco: nada abre conexão (`DB_HOST` inexistente). O `/v4/login` e o token ficam para a PHP8-39.
