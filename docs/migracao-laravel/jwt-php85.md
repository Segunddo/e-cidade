# Token no PHP 8.5: `lcobucci/jwt` (PHP8-60)

Medido sem banco e sem rede, em contêineres `php:7.4-cli` e `php:8.5-cli` (8.5.12) descartáveis, com `--network none`.

## O problema

O `ecidade/composer.lock` do PR traz `lcobucci/jwt` **3.4.0** (`composer.json` fixa `"3.4"`), exigido por `league/oauth2-server` 8.3.2 e `laravel/passport` 10.4.2. A 3.4.0 declara `php ^5.6 || ^7.0` e no 8.5 não assina nem valida: `OpenSSL.php` testa a chave com `is_resource()`, e desde o PHP 8.0 `openssl_pkey_get_*` devolve `OpenSSLAsymmetricKey`. Medido: `InvalidKeyProvided: It was not possible to parse your key, reason:` já na emissão do token. Efeito: todo `POST /v4/oauth/token` e todo Bearer.

## A menor troca que destrava: `~4.1.0`

| `lcobucci/jwt` | com `league/oauth2-server` 8.3.2 (o do PR) no 8.5 |
|---|---|
| 3.4.0 | falha ao emitir (acima) |
| 4.0.4, 4.1.5 | emite e valida |
| 4.2.1, 4.3.0 | `InvalidKeyProvided: Key cannot be empty`: o 8.3.2 passa `InMemory::plainText('')` como chave de verificação e a 4.2 passou a recusar chave vazia |
| 5.7.0 | só com `league/oauth2-server` ^8.5 (8.5.5) |

`~4.1.0` (4.1.5) mantém `league/oauth2-server` 8.3.2 e `laravel/passport` 10.4.2 como estão no lock do PR: muda só `lcobucci/jwt` e acrescenta `lcobucci/clock` (a 4.1.5 pede `^2.0`).

**`lcobucci/clock` precisa de trava própria.** Com o `update` rodando com `--ignore-platform-req=php+`, o resolvedor escolhe a 2.3.0, que declara `php ~8.1.0 || ~8.2.0` e também exclui o 8.5 (e puxa `stella-maris/clock`). As 2.x que aceitam o 8.5: 2.0.0 (`^7.4 || ^8.0`), 2.1.0 e 2.2.0 (`^8.0`, esta com `stella-maris/clock`). Foi fixada a **2.0.0**: a menor troca, sem pacote a mais além do próprio `lcobucci/clock`. Medido: `composer prohibits php 8.5.12 --locked` sem nenhum `lcobucci/*` (sobram os 9 pacotes da PHP8-87).

A 4.0.4 também serve; a 4.1.5 é a mais nova que serve. Subir o `league/oauth2-server` para o 8.5.x permitiria a 4.3/5.x, mas é troca maior e fica como alternativa.

O `league/oauth2-server` 8.3.2 e o Passport 10.4.2 já usam a API que a 3.4 e a 4.x têm em comum (`Configuration`, `InMemory`, `claims()->get()`, `Configuration::forUnsecuredSigner()->parser()`), por isso nada do código deles muda.

## Prova (critério 2)

`anexos/jwt-prova.php` emite um token pelo caminho do `league/oauth2-server` (`AccessTokenTrait::convertToJWT`, `CryptKey`) e o valida com o `BearerTokenValidator`, com chave RSA 2048 gerada na hora (`openssl genrsa`, fora do repositório). Também lê o token como o Passport faz (`Configuration::forUnsecuredSigner()->parser()->parse()->claims()->get('jti')`).

```
openssl genrsa -out chaves/a.key 2048; openssl rsa -in chaves/a.key -pubout -out chaves/a.pub; openssl genrsa -out chaves/b.key 2048
# vendor-34: league/oauth2-server 8.3.2 + lcobucci/jwt 3.4.0 + nyholm/psr7;  vendor-41: o mesmo com lcobucci/jwt ~4.1.0
docker run --rm --network none -v $PWD:/s:ro php:7.4-cli php /s/jwt-prova.php /s/vendor-34 /s/chaves
docker run --rm --network none -v $PWD:/s:ro php:8.5-cli php -d error_reporting='E_ALL&~E_DEPRECATED' /s/jwt-prova.php /s/vendor-41 /s/chaves
```

Resultado, 7.4 + jwt 3.4.0 contra 8.5.12 + jwt 4.1.5 (saída idêntica, fora as versões):

| Caso | Resultado nos dois |
|---|---|
| cabeçalho | `{"typ":"JWT","alg":"RS256"}` |
| claims | `aud`, `exp`, `iat`, `jti`, `nbf`, `scopes`, `sub` (mesmas 7; `exp`/`iat`/`nbf` numéricos) |
| assinatura | 256 bytes |
| Passport lê o token | `jti=abc123`, `sub=42`, `aud=["7"]`, `scopes=["*"]` |
| válido | `VALIDO user=42 client=7 scopes=["*"] id=abc123` |
| expirado | recusado, código 9, `Access token could not be verified` |
| assinatura de outra chave | idem |
| payload adulterado | idem |
| lixo (`abc.def.ghi`) | recusado, código 9, `Error while decoding from JSON` |

O 8.5 com a 3.4.0 morre no primeiro caso (`InvalidKeyProvided`). O 7.4 com a 3.4.0 não muda: nada aqui toca o `composer.json`/`composer.lock` do 7.4.

## O que mais muda da 3.4 para a 4.x (critério 3)

- Exige `php ^7.4 || ^8.0`, `ext-sodium`, `ext-hash`, `ext-mbstring`, `ext-openssl` e `lcobucci/clock`.
- Saem as classes soltas da 3.x (`new Builder()`, `Signer\Key`, `ValidationData`, `Token::getClaim()`); ficam `Configuration`, `Signer\Key\InMemory`, `Validation\Constraint\*` e `claims()->get()`.
- 4.2 em diante recusa chave vazia (por isso o teto 4.1).
- Quem chama a biblioteca no código próprio: `git grep -i lcobucci -- ecidade ':!ecidade/composer.lock'` só acha `ecidade/composer.json` (a restrição) e `ecidade/symfony.lock`. Nenhum arquivo PHP do e-cidade usa a biblioteca; só `league/oauth2-server` e `laravel/passport` (em `vendor/`).
- Defeitos das bibliotecas do PR vistos no 8.5 (avisos `Deprecated` do `league/oauth2-server` 8.3.2) ficam no registro da PHP8-49, não aqui.

## Estado

- Feito: `ecidade/composer-85.json` com `"lcobucci/jwt": "~4.1.0"` e `"lcobucci/clock": "2.0.0"`, e `ecidade/composer-85.lock` regerado com `bash docker/composer-85/composer-85.sh update lcobucci/jwt lcobucci/clock --no-install --no-scripts --ignore-platform-req=php+`. A trava muda em 2 pacotes, de 165 para 166: `lcobucci/jwt` 3.4.0 para 4.1.5 e entra `lcobucci/clock` 2.0.0. `validate` sem trava desatualizada; `install` da trava no `runtime-85/vendor` com rc=0.
- O 7.4 não muda: `ecidade/composer.json` e `ecidade/composer.lock` iguais aos da `laravel/integracao-74` (`git diff` vazio); nenhum PHP mudou.
- A mesma prova rodada com o `vendor/` real do 8.5 (`runtime-85/vendor` montado em `/app/vendor`, PHP 8.5.12, `league/oauth2-server` 8.3.2 e `nyholm/psr7` da trava) dá saída idêntica à do 7.4 + jwt 3.4.0 nos 9 casos.
- A prova HTTP (`POST /v4/oauth/token`, Bearer de verdade) depende de banco e fica para quando houver decisão sobre o banco.
