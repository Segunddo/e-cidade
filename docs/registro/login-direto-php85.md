# Login direto no PHP 8.5 (sem proxy)

Medido em 24/11/2026 na `base-php85` (commit `b4abedcf8`), frente *Ambiente e linha de base*.
Pendência herdada da Fase 0 (`nucleo/ambiente-base-php74`): "o login direto pelo PHP 8.5 retorna
HTTP 500 ao carregar o CAPTCHA legado".

## Resultado

O CAPTCHA está resolvido. O login direto no 8.5 **continua falhando**, agora na emissão do token
OAuth, por causa da `lcobucci/jwt 3.4.0`, que é tarefa **L01** da frente Laravel.

| Passo | 7.4 (`:8074`) | 8.5 direto (`:8185`) |
| --- | --- | --- |
| `GET /login.php` | 200 | 200 |
| `GET /carregaCaptcha.php` | 200, PNG 215×80 | **200, PNG 215×80** |
| `POST /v4/login` (`dbseller`) | 200, `Bearer`, `expires_in` 86400, os dois tokens preenchidos | **500**, `It was not possible to parse your key, reason: ` |
| `GET /extension/desktop` | 200 | 302 para `login.php` (sem sessão) |
| `GET /v4/api/configuracao/menu/buscar-favoritos` | 200 | não chega |
| `PUT /v4/logout`, depois Desktop | 200, depois 302 para `login.php` | não chega |

Ambiente: laboratório `e74` (`regressao/lab/docker-compose.e74.yml`), banco restaurado do
`regressao/baseline/baseline.dump` v2 (sha256 `97251574…0fad`), `.env` do exemplo
(`UTILIZA_CAPTCHA=false`), chaves locais do Passport geradas por `passport:keys`. O proxy (`:8190`)
manda tudo ao 7.4; por isso o 8.5 foi medido direto na porta dele.

## CAPTCHA

`securimage/securimage.php` e `securimage/WavFile.php` não compilavam no 8.x (acesso a string com
chaves, `$s{i}`). Corrigido em `fd76939af` (`$s{i}` → `$s[i]`, 2 linhas), já na `base-php85`.
`carregaCaptcha.php` passou de HTTP 500 a PNG no 8.5, com as mesmas dimensões do 7.4.

Não exercitado: a conferência do código digitado (`Securimage::check`). O
`AuthService::validaCaptcha` só a chama com `UTILIZA_CAPTCHA=true` ou a partir da 3ª tentativa
errada, e no 8.5 o login para antes, no token.

## Causa do 500 no `/v4/login`

Pilha (`storage/logs/laravel.log`):

```text
Lcobucci\JWT\Signer\InvalidKeyProvided::cannotBeParsed()
  vendor/lcobucci/jwt/src/Signer/OpenSSL.php(85)  validateKey()
  vendor/lcobucci/jwt/src/Signer/OpenSSL.php(42)  getPrivateKey()
  vendor/lcobucci/jwt/src/Builder.php(548)        createSignature()
  vendor/league/oauth2-server/src/Entities/Traits/AccessTokenTrait.php(70)  convertToJWT()
```

`OpenSSL::validateKey()` testa `is_resource($key)` (linha 84). Desde o PHP 8.0,
`openssl_pkey_get_private()` devolve um objeto `OpenSSLAsymmetricKey`, não um recurso. A chave é
válida; a checagem da biblioteca é que não reconhece o tipo novo:

| Runtime | `openssl_pkey_get_private(storage/oauth-private.key)` | `is_resource()` |
| --- | --- | --- |
| 7.4.33 | `resource` | `true` |
| 8.5.13 | `OpenSSLAsymmetricKey` | `false` |

O `reason:` vem vazio porque `openssl_error_string()` não tem erro a relatar. A chamada é interna
(`AuthService::requestToPassport` → `AuthorizationServer::respondToAccessTokenRequest`), então o
`POST /v4/oauth/token` cai no mesmo ponto, como já medido em `regressao/baseline/lab-lar12-resultado.md`.

**Correção:** `lcobucci/jwt` 4 ou mais nova, junto com Passport e `league/oauth2-server` (L01,
frente Laravel; `composer.json` é do grupo Laravel). Sem o token, o login direto no 8.5 não fecha,
e a frente de ambiente não tem o que corrigir aqui.

## Como repetir

Com o laboratório `e74` instalado (`regressao/README.md`, seção 1):

```bash
B=http://localhost:8185; J=$(mktemp)
curl -s -o /tmp/c.png -w '%{http_code} %{content_type}\n' "$B/carregaCaptcha.php?sid=x" -c "$J" -b "$J"; file /tmp/c.png
curl -s -w '\n%{http_code}\n' -H 'Accept: application/json' -X POST "$B/v4/login" -c "$J" -b "$J" \
  --form-string username=dbseller --form-string password=dbseller
```

Trocar `8185` por `8074` dá a referência. Quando a L01 entrar na `base-php85`, o esperado no 8.5 é
o mesmo da coluna do 7.4.

## Notas para Mac com Apple Silicon (colima, aarch64)

- `docker/php74-apache/Dockerfile` não constrói: o repositório do PostgreSQL é declarado com
  `arch=amd64` e o `apt update` falha. Funciona usar uma imagem `ecidade-php74` amd64 já construída,
  rodando emulada (`platform: linux/amd64`).
- Emulado, o Apache não cria o mutex padrão (`AH00023: Couldn't create the mpm-accept mutex`).
  Resolve com um arquivo local contendo `Mutex posixsem`, montado em
  `/etc/apache2/conf-enabled/zz-mutex.conf`, por um override do compose fora do git.
- No bind mount do colima, `chgrp www-data` não tem efeito, mas o `www-data` lê a chave do Passport
  e grava em `storage/`, `tmp/` e `bootstrap/cache/` (conferido nos dois runtimes).
