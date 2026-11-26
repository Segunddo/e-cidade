# Passport 13 e `/v4/login` sobre o código do PR: leitura e plano (sem banco)

O PR #8 usa `laravel/passport` 10.4.2 (`composer.lock`) com `league/oauth2-server` 8.3.2 e `lcobucci/jwt` 3.4 fixado no `composer.json:37`. Este registro lê o código do PR contra o **Passport 13.12.0** (a versão que o resolvedor escolhe hoje para o Laravel 13)
e contra o Passport 10.4.2, e diz o que muda, o que o esquema `oauth_*` exige e quais provas fazer quando houver banco. **Só leitura de código e das migrations; nada foi rodado contra banco e nada foi alterado.**

**Resumo:** o login novo (`POST /v4/login`) e o `POST /v4/oauth/token` dependem de 14 pontos do código do PR que tocam o Passport: **6 mudam no 13**, 3 precisam de conferência em execução e 5 continuam compatíveis.
O esquema `oauth_*` que as migrations do PR deixam não é o que as migrations do 13 criam, mas o 13 o lê sem migration (medido na base antiga com o 13.10.0); o que não funciona sem contorno é o segredo do cliente sem hash.

## 1. Os 14 pontos do código do PR (arquivo:linha)

Conferência: `git grep -nE 'Passport|HasApiTokens|findForPassport|validateForPassportPasswordGrant|CheckClientCredentials|clientCredential|createToken\(|->token\(\)' -- ecidade/app ecidade/configuration ecidade/routes ecidade/database ecidade/src` dá 43 linhas, que a tabela agrupa em 14 pontos (os 12 usos de `clientCredential` nas rotas são um só ponto, o 11).

| # | Código do PR | Passport 10.4.2 | Passport 13.12.0 | Situação |
|---|---|---|---|---|
| 1 | `app/Providers/AuthServiceProvider.php:31-33`: `Passport::routes(null, ['prefix' => 'v4/oauth'])` | `Passport::routes()` registra as rotas (`Passport.php:211`) | não existe; as rotas vêm do provider com `config('passport.path', 'oauth')` (`PassportServiceProvider.php:55-62`); `Passport::ignoreRoutes()` desliga (`Passport.php:673`) | **muda**: chamar `routes()` quebra o boot; o prefixo `v4/oauth` passa a ser `passport.path`, ou `ignoreRoutes()` e rotas próprias |
| 2 | `AuthServiceProvider.php` (não chama `enablePasswordGrant()`) | o password grant vem ligado (`PassportServiceProvider.php:116`) | só com `Passport::enablePasswordGrant()` (`Passport.php:194`, `PassportServiceProvider.php:151`) | **muda**: sem a chamada `grant_type=password` (`AuthService.php:359`, o login) é recusado |
| 3 | `AuthServiceProvider.php:35,37`: `tokensExpireIn(Carbon::now()->addDay())`, `refreshTokensExpireIn(...addDays(2))` | aceita data | aceita `DateTimeInterface` e converte para intervalo (`Passport.php:293-301`, `:307-315`) | compatível |
| 4 | `app/Domain/Configuracao/Usuario/Models/Usuario.php:61` e `app/User.php:16`: `use HasApiTokens` | trait | trait exige o contrato `Laravel\Passport\Contracts\OAuthenticatable` (`HasApiTokens.php:12`, `Contracts/OAuthenticatable.php`: `oauthApps()`, `tokens()`, `tokenCan()`, `createToken()`, `currentAccessToken()`, `withAccessToken()`, `getProviderName()`) | **muda**: os dois modelos passam a declarar `implements OAuthenticatable` |
| 5 | `Usuario.php:102` `findForPassport($login)` e `:111` `validateForPassportPasswordGrant($password)` | chamados por `Bridge/UserRepository.php:51-60` | continuam chamados (`Bridge/UserRepository.php:42-51`); `findForPassport` ganha o 2º argumento `$clientEntity` (assinatura de 1 parâmetro continua válida) | compatível |
| 6 | `app/Domain/Configuracao/Usuario/Services/AuthService.php:107`: `$usuario->token()->revoke()` | `token()` devolve o `Token` (`HasApiTokens.php:41`) | `token(): ?ScopeAuthorizable` (`HasApiTokens.php:67`; `currentAccessToken()` em `:75`) | conferir em execução: `revoke()` existe no `Token`, não na interface |
| 7 | `AuthService.php:359-363`, `:378-381`, `:392-393`: `password` e `refresh_token` direto no `AuthorizationServer::respondToAccessTokenRequest()` com `ServerRequest` do Guzzle | `league/oauth2-server` 8.x | `league/oauth2-server` 9.x (resolvido 9.4.1), que exige `lcobucci/jwt ^5.6` (`composer.json:11` do pacote; o `league/oauth2-server` 8.3.2 do `composer.lock` do PR exige `lcobucci/jwt ^3.4 \|\| ^4.0` e o `laravel/passport` v10.4.2 exige `^3.4\|^4.0`), então o 3.4 fixado no `composer.json:37` do PR não serve | conferir em execução: a assinatura do método é a mesma; a trava do `lcobucci/jwt` é assunto do composer do 8.5 |
| 8 | `config/application.default.php:162`: `api.client.id` = 9999999 (inteiro); `config/application.php` é cópia local do default, fora do versionamento (`ecidade/.gitignore:9`) | ids inteiros (`Passport.php:127`: `$clientUuids = false`) | `$clientUuids = true` por padrão (`Passport.php:128`) | **muda**: ids inteiros pedem `Passport::$clientUuids = false` |
| 9 | `database/migrations/2020_01_24_152723_add_oauth_clients.php` (cliente 9999999) e `2022_03_02_130549_m20063_…php` (cliente `MatriculaOnline`): `secret` gravado sem hash | `hash_equals` do texto (`Bridge/ClientRepository.php:100-105`, `$hashesClientSecrets = false`, `Passport.php:169`) | sempre `Hasher::check()` (`Bridge/ClientRepository.php`, `validateClient`) | **muda**: segredo sem hash não valida; precisa de `Hasher` de texto puro (contorno já montado na base antiga) ou `passport:hash` (grava no banco) |
| 10 | `database/migrations/2021_10_25_084718_add_provider_to_oauth_clients.php`: coluna `provider` em `oauth_clients` | não usa | usa em SQL (`ClientRepository::personalAccessClient`, `HasApiTokens::tokens()`) | compatível: a coluna vem da migration do Passport 10.4.2 ou da do PR |
| 11 | `app/Http/Kernel.php:16,82`: alias `clientCredential` => `CheckClientCredentials`, usado em **12 linhas de 9 arquivos de `routes/api/`** (`dbpref`, `patrimonial/ouvidoria`, `patrimonial/protocolo`, `saude/ambulatorial`, `saude/laboratorio`, `tributario/arrecadacao`, `tributario/cadastro`, `tributario/diversos`, `tributario/itbi`) | `Http/Middleware/CheckClientCredentials.php` | não existe; os middlewares são `CheckToken`, `CheckTokenForAnyScope`, `EnsureClientIsResourceOwner`, `ValidateToken`, `CreateFreshApiToken` | **muda**: o alias aponta para classe inexistente; precisa de `EnsureClientIsResourceOwner` (ou equivalente) |
| 12 | `app/Domain/Client/Repositories/ClientRepository.php:41`: `$user->createToken('tokenId')` (cliente pessoal; migration `m20063…` cria `MatriculaOnline` com `personal_access_client`) | `oauth_personal_access_clients` | escolhe o cliente por `grant_types` e `provider` (`ClientRepository.php:83-97`); não usa mais `oauth_personal_access_clients` | conferir em execução (depende de `provider` nulo ou igual ao do guard `api`, e de `personal_access` em `grant_types`, que o 13 deriva de `personal_access_client`) |
| 13 | `app/Console/Commands/PruneOldTokens.php:7,33` e `database/migrations/2023_10_16_091816_m26025_acerto_tokens_passport.php:18`: modelo `Laravel\Passport\Token`, colunas `revoked` e `expires_at` | existe | existe, mesmas colunas | compatível |
| 14 | `configuration/app.php:183`: `Laravel\Passport\PassportServiceProvider::class` registrado à mão | exigido | descoberto pelo auto-discovery (`extra.laravel.providers` do pacote); o registro manual fica redundante | compatível |

Rotas do login novo (não são do Passport, mas dependem dele): `app/Providers/RouteServiceProvider.php:49-53` (`POST v4/login`, `POST v4/unblock`, `PUT v4/kill`, `PUT v4/logout` com `auth:api`); `LoginController@authenticate` em `app/Domain/Configuracao/Usuario/Controller/LoginController.php:25`;
o front chama `v4/login` em `templates/template_login_e-cidade.php:203`; `app/Http/Middleware/DatabaseMiddleware.php:77` prepara a conexão só no caminho `v4/login`.

## 2. Esquema `oauth_*`: o que o PR cria × o que o 13 espera

O PR **não tem** migration que crie as tabelas `oauth_*`: elas vêm das migrations do próprio Passport 10 (carregadas do pacote), e o PR só altera `oauth_clients`:
`2021_10_25_083540_alter_secret_to_oauth_clients.php` (`secret` passa a `nullable`), `2021_10_25_084718_add_provider_to_oauth_clients.php` (`provider` nulo), e insere os clientes (`2020_01_24…`, `2022_03_02…`).
As migrations do Passport 13 só são **publicadas**, não rodam sozinhas (`PassportServiceProvider.php:73`); como as tabelas já existem, nenhuma migration do 13 precisa rodar se o 13 ler o esquema como está.

| Tabela e coluna | Passport 10.4.2 (+ PR) | Passport 13.12.0 (migrations do pacote) | O 13 lê sem migration? |
|---|---|---|---|
| `oauth_clients.id` | `bigIncrements` | `uuid` primária | sim, com `Passport::$clientUuids = false` |
| `oauth_clients.user_id` | `unsignedBigInteger` nulo, indexado | não existe (virou `nullableMorphs('owner')`: `owner_type`, `owner_id`) | sim: `firstParty()` usa `user_id` se a coluna existe (`Client.php:182-185`) |
| `oauth_clients.secret` | `string(100)` nulo: a migration do próprio Passport 10.4.2 (`2016_06_01_000004`) já cria assim; a `2021_10_25_083540` do PR só ajusta bancos criados antes | `string` nulo | lê; **não valida** segredo sem hash (ponto 9) |
| `oauth_clients.provider` | nulo: a migration `2016_06_01_000004` do Passport 10.4.2 já cria a coluna; a `2021_10_25_084718` do PR só a acrescenta em bancos criados antes. **Por isso a prova P1 precisa ler o banco real**: só ele diz qual dos dois caminhos o criou | nulo | sim |
| `oauth_clients.redirect` | `text` | `redirect_uris` (`text`) | sim: `redirectUris()` cai para `redirect` (`Client.php:150-155`) |
| `oauth_clients.personal_access_client`, `password_client` | `boolean` | não existem; `grant_types` (`text`) | sim: `grantTypes()` monta a lista a partir dos dois (`Client.php:164-172`) |
| `oauth_clients.revoked`, `created_at`, `updated_at`, `name` | iguais | iguais | sim |
| `oauth_access_tokens` | `id string(100)`, `user_id` e `client_id` `unsignedBigInteger`, `name`, `scopes`, `revoked`, timestamps, `expires_at` | `id char(80)`, `user_id` `foreignId`, `client_id` `foreignUuid`, demais iguais | sim (colunas iguais; só o tipo do `client_id` muda) |
| `oauth_refresh_tokens` | `id string(100)`, `access_token_id string(100)`, `revoked`, `expires_at` | `char(80)` nos dois ids, demais iguais | sim |
| `oauth_auth_codes` | `id string(100)`, `user_id`, `client_id`, `scopes`, `revoked`, `expires_at` | `char(80)`, `client_id` `foreignUuid` | sim |
| `oauth_personal_access_clients` | existe (`id`, `client_id`, timestamps) | não existe e não é usada (ponto 12) | irrelevante |
| `oauth_device_codes` | não existe | nova (`2024_06_01_000001`) | só se o device code grant for ligado (o PR não usa) |

Esta leitura é das migrations dos pacotes e das do PR; **o esquema real do banco do PR não foi consultado** (sem banco). Onde a coluna do banco difere da migration (por exemplo, o lab restaurado de dump), vale o banco: ver o plano.

## 3. O que o medido na base antiga ainda vale

Base antiga (branches de arquivo `arquivo/base-php84-20261118`, `arquivo/medicoes-20261118`; documentos `passport-esquema.md` e `passport-esquema-atual.md`, medidos com banco somente leitura, Passport 4 → 13.10.0):

| Achado antigo | Vale com o PR? |
|---|---|
| O 13.10.0 lê o esquema de hoje sem migration (clientes e tokens) | **vale**, mesma leitura de `redirect`, `password_client`, `personal_access_client`, `user_id` (`Client.php`, tabela acima); 13.12.0 não foi medida (sem banco) |
| Segredo em texto puro: `Bridge\ClientRepository::validateClient()` do 13 lança `RuntimeException: This password does not use the Bcrypt algorithm` | **vale** (ponto 9): o PR guarda o segredo sem hash nas duas migrations que inserem clientes |
| Contorno: `Hasher` de texto puro (`hash_equals`) ligado só ao `Bridge\ClientRepository`; medido: segredo certo valida, errado e vazio não | **vale** e é o contorno do ponto 9 |
| `personalAccessClient()` do 13 falha com `SQLSTATE[42703] … coluna "provider"` e o contorno lê `oauth_personal_access_clients` | **muda**: o Passport 10.4.2 (`2016_06_01_000004`) ou a migration do PR (`2021_10_25_084718`) criam `provider`; se o banco do PR tem a coluna, o contorno não é necessário. Só se confirma com o banco |
| `Passport::$clientUuids = false` mantém ids inteiros | **vale** (ponto 8) |
| `Passport::enablePasswordGrant()` e fim de `Passport::routes()` | **vale** (pontos 1 e 2); a base antiga também tinha de tratá-los |
| o `league/oauth2-server` 9 aceita o token emitido pelo Passport antigo | **vale**, mas era o Passport 4 e `lcobucci/jwt` 3.x: com o PR (Passport 10.4.2, `lcobucci/jwt` 3.4) o token é do mesmo formato; a validação depende de o composer do 8.5 trocar o `lcobucci/jwt` |
| Risco do usuário de id igual ao do cliente pessoal (caso #1912) | **vale**, é do Passport 13 e depende de dados |

Código e teste da base antiga que serviram de contorno (para consulta, **não copiar o arquivo inteiro**): `app/Auth/PassportEsquemaAtual/SegredoClienteTextoPuro.php` (uma classe de 30 linhas), `app-runtime-novo/Auth/PassportEsquemaAtual/ClientRepository.php`, `PassportEsquemaAtualServiceProvider.php` e `tests/runtime-novo/PassportEsquemaAtualTest.php` (5 testes, 17 asserções).

## 4. Plano das provas quando houver banco

Todas em contêiner descartável e, enquanto não houver decisão contrária, **somente leitura no banco** salvo onde o login precisa gravar (token, log de acesso e sessão, como no resto do projeto).

| # | Prova | Compara | Depende de |
|---|---|---|---|
| P0 | `route:list` e boot do Laravel 13 com `passport.path = v4/oauth`, `enablePasswordGrant()` e `$clientUuids = false` (sem banco) | rotas `v4/oauth/*` iguais às de `Passport::routes()` no 7.4 | só do composer do 8.5 |
| P1 | leitura do esquema real (`information_schema`) contra a tabela da seção 2 | colunas e tipos de `oauth_*` do banco × migrations | banco, só leitura |
| P2 | `POST /v4/oauth/token` password grant (cliente 9999999, usuário de teste) | status, chaves do corpo (`token_type`, `expires_in`, `access_token`, `refresh_token`) e linhas gravadas em `oauth_access_tokens` e `oauth_refresh_tokens` no 7.4 × 8.5 | banco, escrita do token |
| P3 | Bearer do token em uma rota `auth:api` | 200 com o token, 401 sem ele, adulterado e revogado | P2 |
| P4 | `refresh_token` (`AuthService.php:372`) e `unblock` | novo par de tokens; refresh reaproveitado recusado | P2 |
| P5 | `POST /v4/login` inteiro (`LoginController@authenticate`): captcha, sessão, `DatabaseMiddleware` | corpo, cookies e variáveis de sessão iguais no 7.4 × 8.5 | banco, sessão |
| P6 | `PUT /v4/logout` (`token()->revoke()`, ponto 6) e `PUT /v4/kill` | token revogado, sessão destruída | P5 |
| P7 | `createToken('tokenId')` do cliente pessoal (ponto 12) | token emitido e linhas em `oauth_access_tokens` | banco |
| P8 | rotas com `clientCredential` (ponto 11), 1 por arquivo de rota (9) | 200 com token de cliente, 401 sem ele | P2 com `grant_type=client_credentials` |
| P9 | `PruneOldTokens` e a migration `m26025` (ponto 13) | mesmas linhas apagadas | banco, escrita (descartável) |

Sem banco, o que dá para provar antes: P0 e, por leitura, o que já está nas seções 1 e 2. Um banco em memória sem conexão (SQLite) para P2–P4 seria possível, mas é um banco: **decisão do grupo**.
