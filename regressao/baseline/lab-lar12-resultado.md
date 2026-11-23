# Laboratório :8187: Laravel 8 da base 7.4 sob PHP 8.5 (18/11/2026)

Rodada da bateria Laravel contra o laboratório `ecidade74_lar12` (`regressao/lab/docker-compose.lar12.yml`). **Não é
Laravel 12**: não existe código do e-Cidade em Laravel 12. O laboratório roda o **mesmo runtime do `ecidade74_php85`**
(imagem `ecidade74-php85:latest`, mesmo `paridade-74.ini`, mesmos volumes) sobre o `./ecidade` atual, ou seja, o
**Laravel 8.73.2 / Passport 10.4.2 da base 7.4 sob PHP 8.5.12**. A baseline Laravel (gravada na referência :8074) não
foi alterada. (O resultado anterior deste arquivo, "Laravel 5.4 sob PHP 8.5" na porta :8087, era da branch antiga.)

## Comandos

```bash
docker compose -p e74-lar12 -f regressao/lab/docker-compose.lar12.yml up -d     # container ecidade74_lar12, PHP 8.5.12
regressao/.venv/bin/python -m regressao.laravel.bateria comparar \
  --saida ~/e74-logs/task3/lab1 --alvo http://localhost:8187                   # saída 2
```

Commit `cf5670b02`, baseline de 996 casos (`_meta.json`: `alvo: ref`, dump `15cd994a…`). Rodada arquivada em
`~/e74-logs/task3/lab1/` (WSL). O console `artisan` usou o `ecidade74_lar12` sozinho (alvo = `REGRESSAO_LARAVEL_NOVO_URL`).

## Resultado

| IDENTICO | DIVERGE | INCONCLUSIVO | ERRO_AMBIENTE |
|---|---|---|---|
| 0 | 0 | 0 | **1** (`laravel:banco`: `POST /v4/oauth/token` devolveu HTTP 500) |

Diferente do 5.4, **o Laravel 8 sobe no PHP 8.5**: o portão de boot passou (`GET /v4/oauth/token` → 405 JSON, igual à
referência), o banco foi restaurado (190 s) e a bateria parou no **preparo**: sem token OAuth nenhum dos 996 casos roda
(todos os casos de rota usam o token compartilhado). Nenhum caso foi avaliado; nada aqui é aprovação.

O que responde em :8187 (comparado com a referência :8074, mesmas requisições):

| Requisição | Referência 7.4 | Laboratório 8.5 |
|---|---|---|
| `php artisan --version` / `env` / `list --raw` | Laravel 8.73.2 / `local` / 111 linhas | **igual** (o console funciona) |
| `GET /v4/oauth/token` | 405 JSON | 405 JSON (igual) |
| `POST /v4/oauth/token` (password grant do cliente 9999999) | 200 com token | **500** `{"error":true,"message":"It was not possible to parse your key, reason: "}` |
| `GET` rota protegida **sem** token | 500 `Unauthenticated.` | 500 `Unauthenticated.` (igual) |
| `GET` rota protegida com token **emitido pela referência** | 200 com dados | **500** `It was not possible to parse your key, reason: error:1E08010C:DECODER routines::unsupported` |
| `GET /api/v1/protocolo/cgm` (Silex) | 500 "Notificação do Sistema" | igual |

## Causa exata

**`lcobucci/jwt` 3.4.0** (dependência do `league/oauth2-server` 8.3.2 / `laravel/passport` 10.4.2 no `composer.lock` da
base 7.4; o próprio pacote declara `"php": "^5.6 || ^7.0"`) valida a chave assim
(`vendor/lcobucci/jwt/src/Signer/OpenSSL.php:82-86`):

```php
private function validateKey($key)
{
    if (! is_resource($key)) {
        throw InvalidKeyProvided::cannotBeParsed(openssl_error_string());
    }
```

Desde o PHP 8.0, `openssl_pkey_get_private()`/`openssl_pkey_get_public()` devolvem um objeto `OpenSSLAsymmetricKey`, não
mais um `resource`. Conferido nos dois containers, com as mesmas `storage/oauth-{private,public}.key` (sem imprimir as
chaves):

```
8.5.12 OpenSSL 3.5.7: privada=OpenSSLAsymmetricKey is_resource=false; publica=OpenSSLAsymmetricKey is_resource=false
7.4.33 OpenSSL 3.0.2: privada=resource is_resource=true; publica=resource is_resource=true
```

Logo, no PHP 8.5 **toda** assinatura (emitir access token) e **toda** verificação (validar o Bearer) de JWT do Passport
lança `Lcobucci\JWT\Signer\InvalidKeyProvided`, que o handler da aplicação devolve como HTTP 500. A "reason" vem vazia
(emissão) ou com um erro antigo da fila do OpenSSL 3 (`DECODER routines::unsupported`, na verificação), que **não** é a
causa: a chave é lida corretamente, só o `is_resource` falha. O instalador não barrou isso porque o `vendor/` foi
instalado no PHP 7.4 (o `platform_check.php` do Composer só confere o mínimo `>= 7.4`).

Efeitos colaterais vistos no mesmo teste (não derrubam o request, mas poluem):

- `storage/logs/laravel.log` (o **mesmo arquivo** da referência, porque o código montado é o mesmo) ganha a cada request
  `laravel.EMERGENCY: Unable to create configured logger … Log [deprecations] is not defined` seguido de cada
  deprecation do PHP 8.x convertida em `laravel.WARNING`: o Laravel 8.73 manda deprecations para o canal `deprecations`
  e, sem ele, copia `logging.channels.<logging.deprecations ?? 'null'>` (`HandleExceptions::ensureDeprecationLoggerIsConfigured`);
  a base não tem `config/logging.php`, então nem `deprecations` nem `null` existem. Exemplos: `Carbon\Carbon::createFromTimestamp()` sem tipo de
  retorno compatível com `DateTime::createFromTimestamp()` (nesbot/carbon 2.72.5), parâmetros implicitamente nullable
  (`Illuminate\Log\Logger::__construct`, `Lcobucci\JWT\Validation\Constraint\ValidAt`), `pg_query()` sem conexão explícita
  em `app/Http/Middleware/DatabaseMiddleware.php:48`.
- `/var/log/php_errors.log` do `ecidade74_lar12`: só `Illuminate\Log\Logger::__construct(): Implicitly marking parameter
  $dispatcher as nullable is deprecated` (antes de o handler do Laravel assumir).

## O que falta para a bateria avaliar os casos

- **Migração** (não é tarefa da suíte): `lcobucci/jwt` 4.x (o `laravel/passport` 10.4.2 e o `league/oauth2-server`
  8.3.2 instalados já aceitam `^3.4|^4.0`; o 4.x trata `OpenSSLAsymmetricKey`) ou subir direto para Passport 11/12 +
  Laravel 9+ no caminho do Laravel 12; criar `config/logging.php` com os canais `null`/`deprecations` para o log não
  virar ruído; atualizar Carbon. Só depois disso o
  `POST /v4/oauth/token` passa e a rodada avalia os 996 casos; então os `DIVERGE` serão os achados reais do PHP 8.5 (e,
  quando houver, do Laravel 12) contra a referência.
- **Laboratório**: pronto. Para um Laravel 12 de verdade basta apontar `LAR12_CODIGO` para o código (com `vendor/` e
  `.env`) e recriar o container (`regressao/lab/README.md`).
- **Bateria**: nada a mudar. O console (`list`, `env`, `migrate:status`) já roda no container do laboratório; quando o
  framework mudar ele vai divergir por natureza (lista de comandos, versão) e pede triagem.
