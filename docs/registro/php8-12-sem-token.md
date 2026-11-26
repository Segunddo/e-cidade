# Rotas `/v4` sem token e com token malformado: 7.4 x 8.5, sem banco (PHP8-12, 20/11/2026)

**Resumo:** as 1.320 combinacoes metodo+URI vivas de `/v4` e `/rest/v1` (1.314 rotas) foram pedidas pelo kernel HTTP do
Laravel 8.73.2 **em processo** (sem servidor, sem rede, sem banco), no PHP 7.4.33 (vendor do PR) e no PHP 8.5.12 (vendor do
8.5, `jwt` 4.1.5), cada uma em 4 casos: sem `Authorization` e com `Authorization: Bearer x`, com e sem
`Accept: application/json` (5.280 pedidos por runtime). Resultado (so `MODO=neutro`):

- **Pilha do PR como esta:** nenhuma rota chega a autenticacao sem banco. O `DatabaseMiddleware` esta na lista
  **global** de `App\Http\Kernel` e roda antes dos middlewares de rota: `ECidade\V3\Datasource\Database::getInstance`
  chama `pg_connect()` (leitura do codigo, sem numero: a rodada com a pilha inteira exige arquivos locais que um
  checkout novo nao tem, como `libs/db_conn.php`, e nao foi medida). Por isso a medida abaixo troca so esse middleware.
- **Com so o `DatabaseMiddleware` trocado por passagem direta (`MODO=neutro`):** 5.228 de 5.280 iguais (99,0 %); **52
  diferem (13 metodo+rota x 4 casos)**, todos explicados abaixo. As diferencas reais do 8.5: **7 metodo+rota que nao
  compilam no 8.5** (6 do protocolo e `POST /v4/login`, via `securimage`). As outras 6 so mudam a redacao da mensagem do
  PHP.
- 195 metodo+rota (780 pedidos, 14,8 %) ainda tentam abrir banco mesmo no modo neutro: listados e **nao** tratados como
  resposta (lista em `php8-12-sem-token-tentam-banco.tsv`).

## Como foi medido (sem banco)

- Entrada igual a `public/index.php`: `bootstrap.php` do sistema, `libs/db_stdlib.php`, `bootstrap/app.php`, `Kernel::handle`.
  O processo pai nunca escreve na saida (avisos do boot sao capturados), e cada pedido roda num filho
  (`pcntl_fork`, 20 s): `exit`/`die` de um controller nao derruba a medicao.
- Nenhuma conexao: container `--network none`, `ecidade/` e `vendor/` somente leitura, `storage/`, `bootstrap/cache/` e
  `tmp/` em `tmpfs`, par de chaves OAuth gerado na hora e descartado. As imagens nao tem a extensao `pgsql`, e o resolvedor
  de conexao do Laravel (`DatabaseManager::extend`) levanta um marcador: `tentou_banco` = o marcador, `pg_*()` indefinido ou
  `could not find driver` na resposta.
- `APP_DEBUG=false` (o `.env` do PR liga o debug e poria rastros com caminhos na resposta). Rotas = as vivas do
  `RouteCollection` do app (a lista da PHP8-12 anterior, `docs/registro/php8-12-rotas.tsv`, e a mesma: 1.308 de `/v4` mais `/rest/v1`).
- Corpo normalizado: caminho do repositorio vira `/app`, datas viram `<data>`; comparados status, corpo e os cabecalhos
  `content-type`, `cache-control`, `www-authenticate`, `location`, `allow`, `vary`, `access-control-*`.
- Cada rodada confere que a saida nao esta vazia e que a primeira linha (`boot`) diz o PHP certo: 5.281 linhas (1 de
  boot + 5.280 pedidos) nas 2 rodadas, `php` 7.4.33 / 8.5.12, `laravel` 8.73.2 nos dois.

Pre-requisitos de um checkout novo (nao versionados; sem eles a rodada nao reproduz): `ecidade/.env` nao existe e o
`.env.example` tem `APP_KEY=` vazio, entao o Laravel responde `No application encryption key has been specified.` em
vez de `Unauthenticated.` (4.372 pedidos no 7.4 e 4.348 no 8.5, e a rodada daria 48 diferencas em vez de 52, porque o
`POST /v4/login` fica igual). Por isso o comando passa uma `APP_KEY` de teste, **gerada na hora e descartada**
(as chaves OAuth tambem sao geradas na hora, pelo proprio `php8_12_sem_token.php`). `ecidade/` e montado somente leitura: `vendor`, `bootstrap/cache`, `storage` e `tmp`
precisam existir como pontos de montagem, criadas pelo usuario antes (`mkdir -p`); senao o Docker nao monta o vendor
(`read-only file system`) e a rodada nao comeca.

```bash
# imagem: php:<v>-cli + docker-php-ext-install bcmath calendar pcntl   (so isso; sem pgsql de proposito)
# vendor 7.4: composer install do composer.lock do PR (COMPOSER_VENDOR_DIR fora da arvore); vendor 8.5: composer-85.sh install --no-scripts --ignore-platform-req=php+   (SEM --no-plugins: aplica os patches da integracao, como em estrutura-85.md)
mkdir -p ecidade/vendor ecidade/bootstrap/cache ecidade/storage ecidade/tmp
KEY="base64:$(head -c 32 /dev/urandom | base64)"      # chave de teste, descartada no fim
docker run --rm --network none -u $(id -u):$(id -g) -v $PWD/ecidade:/app:ro -v <vendor>:/app/vendor:ro \
  -v <pasta-saida>:/out -v $PWD/scratchpad:/s:ro --tmpfs /app/bootstrap/cache:uid=$(id -u) --tmpfs /app/storage:uid=$(id -u) \
  --tmpfs /app/tmp:uid=$(id -u) -e APP_KEY="$KEY" -e MODO=neutro -e APP_DEBUG=false -e SAIDA=/out/neutro-74.jsonl -w /app <imagem> sh -c '
  mkdir -p storage/framework/cache storage/framework/views storage/framework/sessions storage/logs
  php /s/php8_12_sem_token.php'          # o script gera as chaves OAuth de teste em storage/ (tmpfs, descartado)
python3 scratchpad/php8_12_sem_token_compara.py neutro-74.jsonl neutro-85.jsonl diferencas.tsv
```

Para o 8.5 troque `<vendor>` (`runtime-85/vendor`), `<imagem>` e o nome em `SAIDA`.

Conferido a partir de um checkout novo (`git worktree add --detach`, sem `ecidade/.env` e sem `libs/db_conn.php`), com
o bloco acima extraido deste arquivo e rodado **exatamente como impresso** (so os 3 marcadores `<...>` trocados; as duas
rodadas sairam com rc=0, e o vendor 8.5 veio de `composer-85.sh install --no-scripts --ignore-platform-req=php+`, sem
`--no-plugins`, com o patch da dompdf aplicado), `APP_KEY` e chaves OAuth geradas na hora: 5.280 pedidos nos dois runtimes, 5.228 iguais e 52 diferentes (as mesmas 52 de
`php8-12-sem-token-diferencas.tsv`), 4.356 `Unauthenticated.` e 195 metodo+rota (780 pedidos) que tentam o banco.


## O que as rotas respondem (7.4 = referencia; `MODO=neutro`, 5.280 pedidos)

| Status | Pedidos | Corpo / causa |
|---|---|---|
| 500 | 4.356 | `{"error":true,"message":"Unauthenticated."}`: rota com `auth`, sem token ou com `Bearer x` (o mesmo corpo nos dois) |
| 500 | 712 + 36 + 12 + 8 + 8 | tentou o banco: `Call to undefined function pg_query()` (712) e `could not find driver (SQL: ...)` (64) |
| 500 | 32 | `Method ...Job\Controller...` inexistente: a acao nao existe no PR (ja no 7.4) |
| 302 | 26 | redirecionamento para a pagina de login (pedido sem `Accept` json) |
| 403 | 16 | `{"error":true,"message":"Acesso negado!"}` |
| 422 | 10 | validacao antes de qualquer consulta (ex.: `failed_ids`) |
| 200 | 4 | `PUT /v4/kill` (rota publica) |
| 404 | 4 | rota sem recurso para o caminho de exemplo |
| 500 | demais | mensagens de excecao do proprio codigo (`Pelo menos um arquivo deve ser informado.`, `The authorization grant type is not supported`, `fopen(.../application.log)`...) |

`Bearer x` e sem token dao a **mesma** resposta em todas as rotas (nenhuma consulta o banco para validar um JWT
malformado). O status de `Unauthenticated.` e 500, e nao 401, no 7.4 e no 8.5. Nenhuma resposta escreveu na saida direta do processo.

## Diferencas 7.4 x 8.5 (52 pedidos = 13 metodo+rota x 4 casos; lista: `php8-12-sem-token-diferencas.tsv`)

| Metodo e rota | Pedidos | 7.4 | 8.5 | Causa |
|---|---|---|---|---|
| `GET /v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos` (e `DELETE` ali, `GET .../campos-dinamicos/{codigo_processo}`, `POST .../{tipo_processo}/.../campos-dinamicos/{ordem}`) | 16 | `Unauthenticated.` (500) | `syntax error, unexpected namespaced name "AndamentoPadrao\CamposDinamico..."` (500) | `use App\...\Contracts\` + quebra de linha + `AndamentoPadrao\CamposDinamicosRepository ...` em `app/Domain/Patrimonial/Protocolo/Repository/Processo/AndamentoPadrao/CamposDinamicosRepository.php:6-7`: nome com espaco em branco no meio, aceito no 7.4 e rejeitado no 8.x (nome qualificado e um token so) |
| `GET` e `POST .../andamento-padrao/campos-dinamicos/resposta` | 8 | `Unauthenticated.` | `syntax error, unexpected fully qualified name "\CamposDinamicosResposta"` | mesma causa, em `.../Controller/Processo/AndamentoPadrao/CamposDinamicosRespostaController.php:12-13` |
| `POST /v4/login` | 4 | 302 (`Accept` html) ou 422 (json) | 500 `syntax error, unexpected token "{", expecting ")"` | `securimage/securimage.php:1915` e `securimage/WavFile.php:1555` usam `$texto{n}` (removido no PHP 8); o login carrega a classe |
| `GET /v4/api/educacao/matricula-online/configuracoes/parametros-notificacoes/getParametros` e `POST .../salvar` | 8 | `Class 'ECidade\...\ConfiguracaoRepository' not found` | `Class "ECidade\..."` | **so a aspa** da mensagem do PHP; a classe nao existe nos dois |
| 4 `GET` de `configuracao/documentos-assinar/...` e `configuracao/usuario/assinantes` | 16 | `fopen(.../application.log): failed to open stream: Read-only file system` | `... Failed to open stream ...` | **so a maiuscula** da mensagem do PHP 8; o erro e o log ficar em sistema de arquivos somente leitura nesta medicao, igual nos dois |

Resumo da causa: 4 pontos de codigo do PR que nao compilam no 8.5 (`CamposDinamicosRepository.php`, `CamposDinamicosRespostaController.php`, `securimage.php`, `WavFile.php`), e 6 metodo+rota que so mudam a redacao de mensagens do PHP.
Nada foi corrigido aqui: a lista e o ponto de partida do porte dessas 4 linhas (a regra de troca minima no proprio arquivo se aplica: juntar o nome do `use` na mesma linha e trocar `$s{n}` por `$s[n]` sao validos no 7.4).

## Limites e a repeticao com o Laravel 13

- Mede o contrato de erro **antes do controller**: sem token e com token malformado. Sucesso das rotas autenticadas exige banco.
- No modo neutro a pilha difere da real so pelo `DatabaseMiddleware` global (sem ele nenhuma rota alcanca a autenticacao sem
  banco). Com a pilha inteira o resultado nao foi medido (ver o resumo).
- O caminho de exemplo de cada rota e o primeiro valor que casa (`1`, `a`, `2026-01-01`, `x1`); rotas com `where` estrito podem dar 404.
- O 7.4 e o 8.5 usam o mesmo Laravel 8.73.2: a comparacao mede o PHP, nao o framework. Para o Laravel 13, trocar o vendor
  e repetir os 2 comandos (`php8_12_sem_token.php` aceita `MODO` e `SAIDA`); as contagens acima sao a linha de base.
- Os avisos de boot do 8.5 (13 `Deprecated`: `guzzlehttp/promises`, `laravel/framework helpers.php`, `ParameterBag`, `E_STRICT`) foram
  capturados fora das respostas; no 7.4 sao 0.
