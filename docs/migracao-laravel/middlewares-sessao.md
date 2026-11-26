# Middlewares e sessao no 8.5 (PHP8-38), sem banco

Base: `origin/base-php74` (PHP 7.4, Laravel 8.73.2). Referencia = 7.4. Nada aqui usa banco: os middlewares rodam em pipeline com
requisicoes montadas em memoria (`Request::create`), em conteineres `php:7.4-cli` e `php:8.5-cli` com `--network none`, com o mesmo
`vendor` do PR (Laravel 8.73.2, instalado da `composer.lock` fora do repositorio), `.env` vazio e variaveis de ambiente definidas pelo trecho.
O kernel e inicializado de verdade (`bootstrap/app.php` + `Kernel::bootstrap()`: configuracao, providers, facades); so o roteamento e
o banco ficam de fora.

Script: `scratchpad/middlewares_trecho.php <raiz do ecidade> <pasta vendor>`. Saida de referencia (7.4): `middlewares-sessao/saida-7.4.txt`
(32 casos). Diferenca 7.4 x 8.5: `middlewares-sessao/diferenca-7.4-8.5.txt`.

Defeitos do Laravel 8 do PR e de bibliotecas (por exemplo os avisos de depreciacao do `vendor` no 8.5) ficam no registro da PHP8-49;
a inicializacao do kernel no 8.5 e da PHP8-62. Aqui so se aponta.

## 1. Inventario (base-php74)

`app/Http/Middleware/` tem 17 arquivos (a especificacao falava em 15). Kernel (`app/Http/Kernel.php`):

| Onde | Middlewares |
|---|---|
| Global (8) | `LogPhpActivities`, `CheckForMaintenanceMode`, `ValidatePostSize`, `TrimStrings`, `ConvertEmptyStringsToNull`, `CorsMiddleware`, `DBRequestMiddleware`, `DatabaseMiddleware` |
| Grupo `web` (9) | `EncryptCookies`, `AddQueuedCookiesToResponse`, `StartSession`, `AuthenticateSession`, `ShareErrorsFromSession`, `VerifyCsrfToken`, `SubstituteBindings`, `CreateFreshApiToken`, `StartWebSessionMiddleware` |
| Grupo `api` (4) | `throttle:2000,1`, `bindings`, `SessionMiddleware`, `LogPhpActivities` |
| Por rota (11) | `auth`, `auth.basic`, `bindings`, `can`, `guest` (`RedirectIfAuthenticated`), `throttle`, `legacySession`, `clientCredential` (Passport), `AuthSim`, `AuthRedesim`, `permissaoMenu` |
| Sem uso no Kernel | `SessionDataMiddleware`, `WindowSessionMiddleware`, `MenuAcessadoMiddleware` (comentado; depende da classe `ECidade\Api\V1`) |

Uso nas rotas (`routes/`): `legacySession` 17 usos em 5 arquivos, `clientCredential` 12 usos em 9 arquivos, `permissaoMenu` 3 usos, `AuthRedesim` 1 uso;
`AuthSim` esta registrado mas nenhuma rota o usa.

## 2. Prova por middleware (7.4 x 8.5)

Resultado: **32 casos, saida igual**, exceto o texto de **2 mensagens do proprio PHP** (3 linhas de diferenca, itens abaixo). Comparado: codigo HTTP, todos os cabecalhos
(menos `Date`), cookies (nome, caminho, dominio, secure, httponly, samesite, validade em minutos, tamanho do valor), corpo, excecao
(classe, codigo, status, mensagem) e as linhas do log do aplicativo (`storage/logs`, sem data).

| Middleware | Casos | Resultado |
|---|---|---|
| `TrimStrings` + `ConvertEmptyStringsToNull` | query com espacos, vazio, array aninhado, `password*` exceto, JSON | igual |
| `CorsMiddleware` | sem origem, com origem, `ALLOWED_ORIGINS` ausente / `*` / lista / origem fora da lista | igual (cabecalhos `Access-Control-*`, `Vary`) |
| `DBRequestMiddleware` | `_path`, UTF-8 (`acao` com cedilha e til) decodificado para ISO-8859-1 (`61e7e36f`), numero, arrays aninhados, `null`/booleano/vazio em JSON | igual byte a byte |
| `AuthRedesimMiddleware` | sem cabecalho, sem chave no ambiente, chave correta, chave errada | igual (excecao, codigo e linhas do log) |
| `AuthSimMiddleware` | IP fora da lista, sem `Authorization`, usuario errado, hash errado, token valido, sem `:` no token, sem variaveis de ambiente | igual, **exceto** token sem `:` (ver abaixo) |
| Grupo `web` (sem `StartWebSession` e sem `AuthenticateSession`, que tocam banco) | GET, POST sem token, POST com token invalido, cookie de sessao com lixo | igual: `laravel_session` e `XSRF-TOKEN`, 120 min, `httponly` so na sessao, `secure=false`, `samesite=NULL`; POST sem token -> `TokenMismatchException` |
| `throttle:2000,1`, `throttle:1,1` | 2 pedidos seguidos e limite estourado | igual (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, 429 `ThrottleRequestsException`), cache em arquivo |
| `RedirectIfAuthenticated` | sem usuario | igual (passa) |
| `WindowSessionMiddleware` | sem cabecalho `X-Window-Session` | igual (passa); com cabecalho, a mesma `ErrorException` nos dois (`session_destroy(): Trying to destroy uninitialized session`, texto igual; com sessao ja ativa, `session_set_cookie_params()`, texto diferente: ver abaixo) |

### Diferencas medidas: 2 mensagens do motor do PHP (3 linhas)

`AuthSimMiddleware`, token `Authorization` decodificado sem `:` (`list($user, $hash) = explode(':', ...)`): o PHP gera um aviso, o handler do
Laravel o transforma em `ErrorException` e o middleware devolve 500 com a mensagem do PHP no JSON:

- 7.4: `{"error":true,"message":"Undefined offset: 1"}`
- 8.5: `{"error":true,"message":"Undefined array key 1"}`

Mesmo fluxo, mesmo codigo (500), so o texto da mensagem do motor muda (aparece tambem no log `[Api SIM] Erro: ...`). Nao se corrige no codigo:
qualquer troca (`$p[1] ?? null`) mudaria o comportamento do 7.4. 
`WindowSessionMiddleware` com o cabecalho `X-Window-Session` e a sessao nativa ja ativa: mesma `ErrorException` nos dois, com texto diferente de
`session_set_cookie_params()` (o `diferenca-7.4-8.5.txt` tem essa linha):

- 7.4: `session_set_cookie_params(): Cannot change session cookie parameters when session is active`
- 8.5: `session_set_cookie_params(): Session cookie parameters cannot be changed when a session is active (started from /s/middlewares_trecho.php on line 134)`

O texto do `session_destroy(): Trying to destroy uninitialized session` (caso sem sessao iniciada) e igual nos dois. Total: o `AuthSim` aparece em 2 linhas
(corpo JSON e log), o `WindowSession` em 1.

### Vendor do PR no 8.5 (informativo)

O kernel inicializa nos dois PHP. No 8.5 o `vendor` do PR (Laravel 8, Guzzle, `lcobucci/jwt`, Passport, Opis) emite `Deprecated` (parametro implicitamente
nulo); como a configuracao `logging.php` nao tem o canal `deprecations`, o Laravel grava, para cada aviso, um par de linhas
(`laravel.EMERGENCY: Unable to create configured logger ... Log [deprecations] is not defined` + `laravel.WARNING: ...`) em `storage/logs`:
84 pares na rodada (64 mensagens distintas), 0 no 7.4 (numero que o `roda_middlewares.sh` imprime num checkout limpo; num worktree de desenvolvimento com arquivos locais nao versionados a mesma rodada deu 89 pares, 5 a mais, de avisos do Carbon). Isso nao muda resposta de middleware, mas enche o log; ver PHP8-62 e o registro da PHP8-49.

## 3. Sessao

- Sessao do Laravel: driver `file` (`SESSION_DRIVER`, padrao `file`), pasta `storage/framework/sessions`, cookie `laravel_session`, 120 min,
  `expire_on_close=false`, `encrypt=false`, `http_only=true`, `secure` pelo ambiente (`SESSION_SECURE_COOKIE`), sem `same_site` na configuracao.
  Igual no 7.4 e no 8.5 (cabecalho `Set-Cookie` medido acima). Cache padrao `file`.
- Sessao nativa do PHP (legado): `StartWebSessionMiddleware` (`session_start()` + `session($_SESSION)`), `SessionMiddleware`, `LegacySessionMiddleware`,
  `WindowSessionMiddleware` (cookie `ECIDADEWINDOW*`, `session_set_cookie_params` em array com `samesite=Lax`).
  O contrato das funcoes `session_*` usado nesses pontos (nomes, array de parametros do cookie, `session_status`) vale no 7.4 e no 8.5.

### O que depende de banco e fica sem prova (aguarda decisao)

| Item | Motivo |
|---|---|
| `DatabaseMiddleware` (global) | `DB::beginTransaction`, `pg_query("SET application_name...")`, `Database::getInstance()`, commit/rollback por resposta |
| `StartWebSessionMiddleware` (web) | consulta `db_itensmenu`/`db_menu` e grava `db_logsacessa` com `nextval` |
| `SessionMiddleware` (api) | `DefaultSession` (usuario, instituicao, PCASP) e `DatabaseSession::addSessionToDatabase()` (`fc_putsession`) |
| `LegacySessionMiddleware` (`legacySession`) | `DefaultSession` le dados de usuario do banco |
| `SessionDataMiddleware` | `DB::statement(fc_putsession)` |
| `PermissoesMenuMiddleware` (`permissaoMenu`) | `MenuPermissionRepository` consulta permissoes |
| `clientCredential`, `auth:api`, `AuthenticateSession`, `CreateFreshApiToken` | Passport e usuario autenticado leem `oauth_*` e a tabela de usuarios |
| `LogPhpActivities` (global) | usa a classe legada `TraceLog` e `QueryLogger` (carregadas pelo `bootstrap.php` legado); nao exercitado aqui |

## Repetir (do zero, num checkout novo)

```bash
bash scratchpad/roda_middlewares.sh [pasta-de-trabalho]     # na raiz do repositorio; sem argumento usa /tmp/t112-XXXXXX
```

O script faz tudo o que a medicao precisou e que um checkout novo nao tem:

- **vendor do PR:** `composer install` da `ecidade/composer.lock` numa pasta de trabalho fora do repositorio (`<pasta>/pr`, so baixa pacotes; sem banco). O `composer.json` dessa
  pasta tem so o autoload PSR-4 `App\` apontando para `../ecidade/app/` (os `autoload.files` do PR sao relativos ao proprio `ecidade/` e nao servem a um vendor montado fora dele);
  por isso o vendor fica em `<pasta>/pr/vendor`, montado em `/w/pr`, ao lado de `ecidade/` em `/w/ecidade`.
- **`.env`:** a base nao versiona `ecidade/.env`; so se existir um local ele e coberto por um arquivo vazio montado por cima (nao e necessario criar nada num checkout novo).
- **storage gravavel** em pasta nova a cada rodada, ja com `logs`, `framework/sessions`, `framework/cache/data` e `framework/views` (sem eles aparecem erros de `session_start`/`file_put_contents`).
- **encoding:** a saida do trecho e ISO-8859-1 (mensagens do `AuthRedesim`); o script converte para UTF-8 (`iconv`) e tira as linhas `Deprecated`/`LOG laravel.` do vendor antes de comparar.
- **comparacao:** `cmp` da saida do 7.4 com `middlewares-sessao/saida-7.4.txt` e do `diff` 7.4 x 8.5 com `middlewares-sessao/diferenca-7.4-8.5.txt`; imprime 32 casos nos dois e os
  pares `EMERGENCY` do vendor (0 no 7.4, 84 no 8.5 em checkout limpo).

Medido do zero (pasta nova, vendor instalado na hora): `7.4: 32 casos`, `8.5: 32 casos`, `84` pares no 8.5 (84 `laravel.EMERGENCY` + 84 `laravel.WARNING`, 64 mensagens distintas), as duas comparacoes iguais.

Com o vendor do 8.5 (PHP8-79): usar uma pasta de trabalho cujo `pr/vendor` seja o dele, instalado com o mesmo layout (autoload de `App\` em `../ecidade/app/`); o script so instala se nao houver `pr/vendor/autoload.php`.
