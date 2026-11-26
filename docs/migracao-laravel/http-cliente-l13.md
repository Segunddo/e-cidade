# Cliente HTTP (Guzzle direto) com o Laravel 13: pedidos iguais ao 7.4, contra um duble (PHP8-62)

Mede se o cliente HTTP do codigo do PR faz os mesmos pedidos no 8.5 com o vendor do Laravel 13 que no 7.4 com o vendor do PR. **Sem banco e sem rede**: um servidor `php -S 127.0.0.1` dentro do proprio contêiner faz o papel do servico externo. O SDK do Pix (`Pix/Bancos/*`, `dbseller/sdk-api-pix-bb`) ja foi medido a parte (`sdk-pix-bb-php85.md`) e fica de fora.

**Resultado:** o codigo nao usa o cliente do Laravel (`Http::`: 0 usos); usa o **Guzzle direto**. Em 26 casos de Guzzle (pedido e resposta/erro) e 1 de objetos PSR-7 os pedidos recebidos pelo duble (metodo, URI, cabecalhos, corpo) e o que o cliente observa (status, corpo, classe e texto das excecoes) sao **iguais no 7.4 com o Guzzle 7.5.0 e no 8.5 com o Guzzle 7.16.3**, exceto 4 linhas de ambiente, nenhuma do Guzzle (secao 3). Nada a corrigir no codigo.

## 1. O que o codigo usa

| Contagem | Comando | Resultado |
|---|---|---|
| uso do cliente do Laravel (`Http::`, `PendingRequest`) | `git grep -nE "Http::\|Facades\\\\Http\|PendingRequest" -- ecidade/app ecidade/src \| wc -l` | **0** |
| `new Client(...)` do Guzzle (inclui `\GuzzleHttp\Client`) | `git grep -nE "new \\\\?(GuzzleHttp\\\\)?Client\(" -- ecidade/app ecidade/src \| wc -l` | 23 em 18 arquivos (3 deles, `Pix/Bancos/*`, ficam com a medicao do SDK) |
| chamadas `->request/get/post/put/delete(` no cliente | `git grep -nE "(->\|\\\$)(client\|http\|httpClient\|oRequest\|clientGuzzle\|cliente)->(request\|get\|post\|put\|delete)\(" -- ecidade/app ecidade/src \| wc -l` | 28 |
| `->requestAsync(...)->wait()` | `git grep -nE "requestAsync\(" -- ecidade/app ecidade/src \| wc -l` | 10 (9 no `PNCPClient`, 1 no `BnafarClient`) |
| funcoes globais do Guzzle que o 8 removeu (`GuzzleHttp\json_encode`, `default_user_agent`, `Psr7\build_query`…) | `git grep -nE "GuzzleHttp\\\\(json_encode\|json_decode\|default_user_agent\|describe_type\|uri_template\|choose_handler\|default_ca_bundle\|headers_from_lines\|debug_resource\|is_host_in_noproxy)\(" -- ecidade/app ecidade/src ecidade/routes \| wc -l` | **0** |

Opcoes de cliente usadas: `headers` (25), `form_params` (13), `base_uri` (4), `json` (3), `verify` (2, `false`), `multipart` (2), `auth` (2), `timeout` (1, escrito dentro de `headers` em `ConsultaSituacaoContribuinteService`, vira o cabecalho `timeout: 20`), `http_errors` (1). Excecoes tratadas: `ClientException`, `ServerException`, `ConnectException`, `GuzzleException`.
Versoes: PR `guzzlehttp/guzzle` 7.5.0, `psr7` 2.7.0, `promises` 1.5.3 (`composer.lock`); integracao do 8.5 `guzzle` 7.16.3 (`composer-85.json` pede `"7.16.3 as 7.5.0"`), `psr7` 2.13.5, `promises` 2.6.1, `psr/http-message` 2.0 (`composer-85.lock`). Nenhuma classe do codigo implementa interface PSR-7/PSR-18 (`grep -rnE "implements .*(RequestInterface|ResponseInterface|MessageInterface|StreamInterface|ClientInterface|UriInterface)"` da 0), entao o tipo de retorno obrigatorio do PSR-7 2.0 nao alcanca o codigo.

## 2. Como foi medido

`scratchpad/http_cliente_prova.php`: sobe o duble (`php -S` com um roteador que grava cada pedido e responde `/ok`, `/criado` 201 com `Location`, `/vazio` 204, `/xml`, `/e400`, `/e401`, `/e404` com corpo de 300 bytes, `/e500`, `/e503`, `/redireciona` 302, `/gz` com `Content-Encoding: gzip` e `/lento` 1,5 s) e roda 26 casos Guzzle (H01 a H22; o H13 tem 5 variantes de erro) e 1 de objetos PSR-7 do `AuthService` (H23):
`request GET` com `headers`; `get` com `verify=false`; `post` com `form_params`, `json`, `multipart` (boundary normalizado), `auth` basico; `base_uri` com URI relativa; `put`, `delete`; `requestAsync(...)->wait()` com POST, DELETE e PUT; os erros 400, 401, 404, 500, 503 (`ClientException`/`ServerException`, com o corpo da resposta e o texto da mensagem); `http_errors=false`; `requestAsync` com 404; redirecionamento; gzip; 204; XML; timeout de 1 s numa resposta de 1,5 s; porta fechada e host que nao resolve (`ConnectException`).

Pelo `docker/composer-85/roda-isolado.sh` (imagens do projeto, sem rede, falha alto):

```bash
VENDOR=<vendor 7.4: composer install do composer.lock do PR> bash docker/composer-85/roda-isolado.sh 7.4 scratchpad/http_cliente_prova.php /app/vendor > pr-php7.4.txt
VENDOR=<vendor 7.4>                                          bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/http_cliente_prova.php /app/vendor > pr-php8.5.txt   # PHP 8.5, Guzzle 7.5.0 (isola o PHP)
VENDOR=<vendor 8.5: composer-85.sh install --no-scripts --ignore-platform-req=php+> bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/http_cliente_prova.php /app/vendor > l13-php8.5.txt
```

Saidas em `http-cliente/` (82 linhas cada; a ultima linha de cada uma diz as versoes de PHP, curl e Guzzle).

## 3. Resultado

| Comparacao | Resultado |
|---|---|
| 8.5 com Guzzle 7.5.0 × 8.5 com Guzzle 7.16.3 (`pr-php8.5` × `l13-php8.5`) | **iguais** (so o que muda de Guzzle: nada observado) |
| 7.4/Guzzle 7.5.0 × 8.5/Guzzle 7.16.3 (`pr-php7.4` × `l13-php8.5`) | iguais, **exceto 4 linhas**, as 4 tambem presentes na comparacao so de PHP (`pr-php7.4` × `pr-php8.5`) |

As 4 linhas, todas de ambiente:

| Linha | 7.4 | 8.5 | Causa |
|---|---|---|---|
| H13e500, H17, H18: `Content-Type` da resposta do duble sem charset explicito | `charset=UTF-8` | `charset=ISO-8859-1` | e o duble (`php -S` na propria imagem) quem anexa o `default_charset`: 7.4 sem diretiva no `php.ini` (padrao UTF-8), 8.5 com `default_charset = "ISO-8859-1"` do `docker/php85-apache`. Nao e o Guzzle; vale para qualquer resposta que o PHP do e-Cidade mande sem charset |
| H21: `ConnectException` de porta fechada | `... Connection refused` | `... Could not connect to server` | texto da libcurl (7.81.0 na imagem do 7.4, 8.14.1 na do 8.5); a classe, o codigo `cURL error 7` e o resto da mensagem sao iguais |

Pedidos recebidos: os 24 casos que chegam ao duble (todos, menos H21 porta fechada e H22 host que nao resolve) saem **byte a byte iguais** no duble: metodo, URI com a query (`?x=1&y=a b` vira `y=a%20b` nos dois), cabecalhos (inclusive o `User-Agent` de `GuzzleHttp/7`, cuja parte de versao do curl e do PHP e o unico que difere e esta normalizada), `Content-Length` e corpo (`form_params`, `json` e `multipart`, com o boundary normalizado). As mensagens de `ClientException`/`ServerException` (`... resulted in a `404 Not Found` response:` seguido dos 120 primeiros bytes do corpo) tambem saem iguais; o timeout (`cURL error 28`) sai igual depois de normalizado o tempo (1000 ms x 1001 ms). Objetos PSR-7 (`ServerRequest`, `Response`) iguais.

## 4. O que nao foi coberto

- As classes reais (`PNCPClient`, `BnafarClient`, `LicitaconClient`, `CertificadoPfxService`…) dependem de `env()` e de banco/token para montar a chamada; foi medido o **mesmo padrao de chamada** que cada uma usa (metodo, opcoes, tratamento de erro), nao a classe inteira.
- HTTPS e verificacao de certificado (o duble e HTTP; `verify=false` so e exercitado como opcao).
- SOAP (`SoapClient`, 17 ocorrencias de `SoapClient`/`curl_init` em `app/` e `src/`) e `curl_*` direto: fora do escopo (nao e Guzzle).
- Proxies, cookies e `sink`: o codigo nao usa essas opcoes.
- O SDK do Pix: ver `sdk-pix-bb-php85.md`.
