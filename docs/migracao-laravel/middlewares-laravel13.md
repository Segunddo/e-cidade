# Middlewares e sessao com o Laravel 13 (PHP8-38): repetir os 32 casos

Repete os 32 casos de `middlewares-sessao.md` (7.4 com o vendor do PR x 8.5 com o **vendor do 8.5 da integracao**, agora Laravel 13.43.0, Passport 13.12.0, Carbon 3.15.1, `symfony/http-foundation` 8.1),
sem banco, pelo `docker/composer-85/roda-isolado.sh` (imagens do projeto, sem rede, falha alto). Scripts: `scratchpad/middlewares_trecho.php` (os 32 casos), `scratchpad/middlewares_classes.php`
(as classes do Kernel existem?), runner `scratchpad/roda_middlewares_l13.sh`. Saidas em `middlewares-laravel13/`.

## O app do PR ainda nao sobe no Laravel 13

`Kernel::bootstrap()` no 8.5 para em `app/Providers/AuthServiceProvider.php:31`: `Call to undefined method Laravel\Passport\Passport::routes()` (o metodo saiu do Passport 13; e do PHP8-39, T-135).
Para medir os middlewares assim mesmo, o trecho aceita um 3o argumento com providers a nao carregar e roda o 8.5 **sem o `AuthServiceProvider`** (as outras partes do boot sobem: providers, configuracao, facades).
Quando o app subir no 13 (a T-143 faz o boot subir: `method_exists` em volta do `Passport::routes()` e `configuration/passport.php`), rodar sem esse argumento (`PULAR= bash scratchpad/roda_middlewares_l13.sh`) e ajustar a referencia.

## Resultado

**32 casos nos dois, 3 linhas de diferenca, as mesmas 2 mensagens do motor do PHP da PHP8-38** (`Undefined offset: 1` x `Undefined array key 1`, no JSON e no log do `AuthSim`; texto de `session_set_cookie_params()` do `WindowSession`),
e **0 pares de depreciacao do vendor no log** (o vendor do Laravel 8 no 8.5 dava 84; o Laravel 13 ja e PHP 8.5). Saidas: `saida-7.4.txt`, `saida-8.5-laravel13.txt`, `diferenca-7.4-8.5.txt`.

| Grupo (criterio 1) | Laravel 8 (7.4) | Laravel 13 (8.5) |
|---|---|---|
| `TrimStrings` + `ConvertEmptyStringsToNull` (guia: `TrimStrings`/`ConvertEmptyStringsToNull`) | resposta e dados iguais | iguais |
| `CorsMiddleware`, `DBRequestMiddleware`, `AuthRedesim`, `AuthSim` | iguais | iguais (so o texto do motor acima) |
| Grupo `web` (`EncryptCookies`, `StartSession`, `VerifyCsrfToken`, ...): cookies `XSRF-TOKEN` e `laravel_session` | `SameSite` ausente (`NULL`) | **`SameSite=lax`** (ver abaixo) -> corrigido, igual ao 7.4 |
| `throttle:2000,1` e `throttle:1,1`, `RedirectIfAuthenticated`, `WindowSession` | iguais | iguais |

### Diferenca achada e corrigida: `SameSite` dos cookies (sessao)

`configuration/session.php` do PR nao tem a chave `same_site`. O Laravel 8 nao envia `SameSite` nesse caso. O Laravel 13 completa as chaves que faltam em cada `configuration/*.php` com o padrao do proprio framework
(`LoadConfiguration` faz `array_merge($base[$name], $config)`), e o padrao de `same_site` e `lax`: `laravel_session` e `XSRF-TOKEN` passam a sair com `SameSite=lax`
(`saida-8.5-laravel13-sem-same_site.txt`: **8 linhas de diferenca**, 5 a mais que as 3 do motor: a linha `CONFIG session` e os 4 cookies `XSRF-TOKEN`/`laravel_session` com `samesite='lax'`;
comando: `diff saida-7.4.txt saida-8.5-laravel13-sem-same_site.txt | grep -c '^[<>]'` da 16 (as 8 linhas aparecem como `<` e `>`) e, com a correcao, `diff saida-7.4.txt saida-8.5-laravel13.txt | grep -c '^[<>]'` da 6, as 3 do motor).

Correcao minima, **no proprio arquivo**: `ecidade/configuration/session.php` ganha `'same_site' => null,` (com comentario). No 7.4 a chave extra vale `null`, que e o que o Laravel 8 usava:
medido, a saida do 7.4 antes x depois muda so a linha `CONFIG session` (a chave nova, `null`); cookies e demais casos iguais. No Laravel 13 os cookies voltam a sair sem `SameSite`, como no 7.4.
Trocar para `lax` muda o comportamento do 7.4 e fica como decisao do grupo.

O mesmo mecanismo vale para qualquer chave que falte nos arquivos de `configuration/`: o Laravel 13 usa o padrao dele. Aqui so a sessao foi medida; comparar as demais configuracoes e assunto da medicao do app no Laravel 13.

## O Kernel no Laravel 13 (guias 9-13)

`scratchpad/middlewares_classes.php` lista as 32 entradas do `app/Http/Kernel.php` (8 globais, 9 do `web`, 4 do `api`, 11 aliases) e se a classe existe (`middlewares-laravel13/classes-7.4.txt` x `classes-8.5-laravel13.txt`):

- **Existem no 13**: `CheckForMaintenanceMode`, `VerifyCsrfToken` e `ValidatePostSize` seguem como classes finas que estendem as novas (`PreventRequestsDuringMaintenance`, `ValidateCsrfToken`/`PreventRequestForgery`,
  `Illuminate\Http\Middleware\ValidatePostSize`); `ConvertEmptyStringsToNull`, `TrimStrings`, `AuthenticateSession`, `StartSession`, `AddQueuedCookiesToResponse`, `ShareErrorsFromSession`, `SubstituteBindings`, `ThrottleRequests`, `Authenticate`,
  `AuthenticateWithBasicAuth`, `Authorize` e `CreateFreshApiToken` (Passport 13).
- **Propriedades do Kernel**: o `Illuminate\Foundation\Http\Kernel` do 13 ainda le `$middleware`, `$middlewareGroups` e `$routeMiddleware` (soma `$routeMiddleware` e `$middlewareAliases`, `Kernel.php:644`): nada a mudar na estrutura.
- **Nao existe no 13**: `Laravel\Passport\Http\Middleware\CheckClientCredentials` (alias `clientCredential`, 12 usos em 9 arquivos de rota, `Kernel.php:16,82`); o Passport 13 traz `EnsureClientIsResourceOwner` no lugar.
  Ja esta no plano do Passport 13 (`passport13-leitura-e-plano.md`, ponto 11; T-135); nao foi alterado aqui.

## O que continua dependendo de banco (igual a `middlewares-sessao.md`)

`DatabaseMiddleware`, `StartWebSessionMiddleware`, `SessionMiddleware`, `LegacySessionMiddleware`, `SessionDataMiddleware`, `PermissoesMenuMiddleware`, os de Passport/`AuthenticateSession` com usuario e `LogPhpActivities` (classe legada `TraceLog`).

## Repetir

```bash
# 1) vendor do 8.5 (Laravel 13) em runtime-85/vendor
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+
# 2) vendor do PR para o 7.4 em runtime-85/referencia-74/vendor (so baixa pacotes): instala a ecidade/composer.lock e gera o autoload completo com o composer.json real
mkdir -p runtime-85/referencia-74/lock && cp ecidade/composer.json ecidade/composer.lock runtime-85/referencia-74/lock/
python3 - <<'PY'
import json
p = 'runtime-85/referencia-74/lock/composer.json'
d = json.load(open(p)); [d.pop(k, None) for k in ('scripts', 'autoload', 'autoload-dev')]
json.dump(d, open(p, 'w'), indent=1)
PY
docker run --rm -u $(id -u):$(id -g) -e COMPOSER_HOME=/tmp/ch -v $PWD/runtime-85/referencia-74/lock:/pr -w /pr composer:2 \
  composer install --no-scripts --no-interaction --ignore-platform-reqs --no-progress --no-autoloader
mv runtime-85/referencia-74/lock/vendor runtime-85/referencia-74/vendor
docker run --rm -u $(id -u):$(id -g) -e COMPOSER_HOME=/tmp/ch -v $PWD/ecidade:/app:ro -v $PWD/runtime-85/referencia-74/vendor:/app/vendor -w /app composer:2 \
  composer dump-autoload --no-scripts --no-interaction
# 3) os 32 casos x2, classes do Kernel e comparacao com middlewares-laravel13/ (falha se um docker run falhar ou a saida vier vazia)
bash scratchpad/roda_middlewares_l13.sh
```

Conferido assim (pasta de trabalho nova): `7.4 = saida-7.4.txt`, `diferenca 7.4 x 8.5 (Laravel 13) = a da referencia` e `diferenca de classes = a da referencia`.

**Efeito na prova da PHP8-38 (`middlewares-sessao.md`):** a chave nova aparece na linha `CONFIG session` da saida do 7.4 daquela prova; `middlewares-sessao/saida-7.4.txt` foi atualizada (`"same_site":null`), e a diferenca 7.4 x 8.5 (Laravel 8) segue igual (a chave vale `null` nos dois).
