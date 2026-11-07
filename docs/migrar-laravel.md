# Migrar o Laravel do e-cidade: direcionamento

Oct 16, 2026 · @Diego

**Para quem vai migrar o Laravel, de 5.4 para 12.** O código legado (as telas `*.php` da raiz, `classes/`, `libs/`…) já roda em PHP 8.5 nas áreas Tributário e Educação, e essa parte **não é sua**. A sua é a camada HTTP do Laravel: `app/`, `routes/`, o login (Passport) e a API REST antiga (`api/V1`, Silex).

Tudo o que está aqui foi **medido** neste repositório, não suposto. O que ainda não se sabe está marcado como **não medido**. O registro completo, com o porquê de cada decisão, fica em `docs/registro/laravel.md`: procure por *MEDIÇÃO (14/10/2026)*, *LARAVEL SÓ PARA O TRIBUTÁRIO* e *TESTE: o token*.

**Se é a sua primeira vez no projeto, comece pelo §0.** Ele explica o que é o sistema, onde fica cada coisa e como ver tudo funcionando antes de mudar qualquer linha. Os §1 a §9 supõem que você já passou por ele.

## 0. Antes de tudo: o mapa

### O que é o e-cidade

É um sistema de gestão de prefeituras, da DBSeller, de código aberto. Ele calcula impostos (IPTU, ISS, ITBI), emite guias, controla escolas, folha de pagamento e contabilidade. É grande: são ~33 mil arquivos PHP e 8,7 milhões de linhas. Quase todo o código foi escrito para o PHP 5.6, de 2014.

O projeto de que você faz parte migra esse sistema para o PHP 8.5. A migração é feita **por áreas** do sistema (Tributário, Educação…) e com **duas versões do PHP rodando lado a lado**: a antiga continua viva e serve de gabarito para a nova. Essa técnica se chama *strangler fig* (figueira estranguladora): o sistema novo cresce em volta do velho até o velho poder ser desligado.

### As duas metades do código

| | **Legado** (já migrado, não é seu) | **Laravel** (é o seu trabalho) |
|---|---|---|
| Onde | ~15 mil scripts soltos na raiz de `ecidade/` (`iss1_*.php`, `cad4_*.php`…), mais `classes/`, `forms/`, `libs/`, `dbforms/`, `model/` | `app/` (controllers, models, providers), `routes/`, `public/index.php`, `config/` |
| Estilo | PHP procedural, uma tela por arquivo, SQL direto com `pg_query` | Laravel 5.4 (2017), organizado por domínio em `app/Domain/<Área>/<Módulo>/` |
| Estado | roda no 5.6 **e** no 8.5, verificado tela por tela | só roda no 5.6 |

Existem mais duas peças, que não são nem uma coisa nem outra:

- `src/` é um framework próprio da DBSeller (o "V3"). Ele carrega as telas legadas e quase não usa Laravel (44 de 2.651 arquivos).
- `api/` é uma API REST antiga escrita em Silex, um micro-framework morto.

**Encoding:** 64% dos arquivos estão em LATIN-1, não em UTF-8, e o banco também. Configure o seu editor para não converter os arquivos ao salvar. Ao buscar texto, use sempre `grep -a`: sem o `-a`, o `grep` trata esses arquivos como binários e os pula sem avisar.

### Por onde passa uma requisição

```
navegador
   │
   ▼
.htaccess  →  FrontController.php  (ecidade/FrontController.php, 16 linhas)
                 ├── /api/v1/...        → api/api.php           (Silex)
                 ├── /v4/...            → public/index.php       (LARAVEL)
                 ├── /rest/v1/...       → public/index.php       (LARAVEL)
                 └── todo o resto       → app.php                (V3 → telas legadas)
```

Dentro do Laravel, `app/Providers/RouteServiceProvider.php` monta `routes/api.php` sob o prefixo `v4/api`. Esse arquivo inclui `routes/api/tributario/<módulo>.php`, e cada rota aponta para um controller em `app/Domain/Tributario/...`.

Exemplo real, para seguir com o dedo:

1. A tela legada `iss4_ordemservico001.php` faz, por JavaScript, uma chamada a `/v4/api/tributario/issqn/alvaraeventos/ordemservico`.
2. `routes/api.php` (linha ~163) manda o prefixo `issqn` para `routes/api/tributario/issqn.php`.
3. Esse arquivo liga a rota a `App\Domain\Tributario\ISSQN\Controller\AlvaraEventos\OrdemServicoController@index`.

### O ambiente: os containers e as portas

Tudo roda em Docker. O banco e a pasta `ecidade/` são **compartilhados** por todos os containers. A única coisa que muda entre eles é a versão do PHP e, no laboratório, o `vendor/`.

| Porta | Container | O que é | Pode mexer? |
|---|---|---|---|
| `:8080` | `ecidade_php56` | PHP 5.6 + Laravel 5.4: **a referência**, o gabarito | **não** |
| `:8085` | `ecidade_php85` | PHP 8.5, com o mesmo `vendor/` (Laravel 5.4, que aqui não funciona) | só o compose dele |
| `:8087` | `ecidade_lar12` | PHP 8.5 + **Laravel 12**: o laboratório (§8) | sim, é o seu |
| `:8090` | `ecidade_proxy` | nginx: o endereço que o usuário usa, e que manda cada tela para o PHP certo | ao rotear |
| — | `ecidade_database` | PostgreSQL 16, banco `ecidade`, LATIN1 | não destrutivamente |

Para subir o ambiente, use os comandos da seção *Como subir o ambiente* do `CLAUDE.md`, na ordem em que estão lá. A ordem importa, e as permissões também. Login: `dbseller` / `dbseller`.

### Glossário rápido

- **5.6 / 8.5**: versões do PHP. "Rodar nos dois" quer dizer que o mesmo arquivo funciona no container `:8080` e no `:8085`.
- **Referência**: o 5.6. Uma coisa está "certa" no 8.5 quando faz **o mesmo** que o 5.6, inclusive os mesmos erros.
- **`vendor/`**: as bibliotecas instaladas pelo Composer (Laravel inclusive). Não é versionado no git.
- **Boot / provider**: ao receber uma requisição, o Laravel primeiro executa os *service providers* de `app/Providers/` e `config/app.php`. Isso é o "boot". Hoje, no Laravel 12, ele morre ali, antes de chegar a qualquer rota.
- **Passport / token**: o login. A tela de login pede um token a `/v4/oauth/token` (Passport, OAuth2) e as rotas `/v4/api/*` exigem esse token (`auth:api`).
- **Sessão compartilhada**: o login cria uma sessão PHP num volume que os dois containers leem. Por isso dá para entrar pelo 5.6 e usar telas servidas pelo 8.5.
- **Bateria**: rodar `scratchpad/cmp.py` sobre muitas telas, comparando byte a byte a resposta do 5.6 com a do 8.5.

### A primeira hora, antes de mudar qualquer coisa

1. Suba o ambiente e entre em `http://localhost:8090` com `dbseller`.
2. Abra ISSQN → Procedimentos → Alvará de Eventos → Ordem de Serviço com as ferramentas do desenvolvedor (F12) na aba Rede. A tela vem com o cabeçalho `X-Ecidade-Runtime: PHP-8.5 (migrado)`, e a chamada a `/v4/api/tributario/issqn/...` vem com `PHP-5.6 (referencia)`. É exatamente essa chamada que você vai mudar de lado.
3. Peça um token ao 5.6:
   ```bash
   curl -s http://localhost:8080/v4/oauth/token -d grant_type=password -d client_id=9999999 \
        -d client_secret=<api.client.secret de ecidade/config/application.php> \
        -d username=dbseller -d password=dbseller
   ```
   Chame a mesma rota no `:8080` com `-H "Authorization: Bearer <token>"` e guarde a resposta. Ela é o gabarito.
4. Faça a mesma chamada no `:8087`. Hoje ela dá 500. Leia o erro com `docker exec ecidade_lar12 tail /var/log/php_errors.log`, e não no `storage/logs/` do laboratório, que fica vazio. O erro de hoje é este, e é ele o seu primeiro problema:
   ```
   Cannot make non abstract method Illuminate\Support\ServiceProvider::register() abstract
   in class App\Domain\Core\Base\Providers\BaseDeferredProvider (linha 19)
   ```
   Ele acontece no boot, antes de qualquer rota.
5. Leia o §1 em diante.

Se algo no passo 1 ou 2 não funcionar, o problema é de ambiente, não do Laravel. O `docs/registro/ambiente.md` tem uma seção para cada armadilha de ambiente já encontrada (permissões, sessão, `/tmp`).

## 1. O problema em uma frase

Nenhuma versão do Laravel roda nos dois PHPs:

| Laravel | PHP |
|---|---|
| 5.4 (o atual) | ≥ 5.6.4, **não roda no 8** |
| 12 | 8.2 a 8.5 |
| 13 | 8.3 a 8.5 |

Os dois containers (5.6 em `:8080`, 8.5 em `:8085`) montam **o mesmo diretório**, e com ele o mesmo `vendor/`. Se você rodar `composer update` para o Laravel 12 ali, **derruba o 5.6**. O 5.6 é a referência: serve o login, os módulos ainda não migrados e é contra ele que toda tela é comparada. Ele **não pode cair**, e o `docker-compose.yml` dele **não se altera**.

## 2. A solução: um `vendor/` só do 8.5

```
ecidade/                     <- código, o MESMO para os dois
├── vendor/                  <- Laravel 5.4, usado pelo 5.6
└── ...
vendor-85/  (novo)           <- Laravel 12, montado POR CIMA de /var/www/html/vendor
                                só no container 8.5
```

Montam-se por cima, só no lado 8.5, também `bootstrap/cache` e `storage/`. O Laravel 12 grava cache num formato que o 5.4 não lê; compartilhar essas pastas quebraria o 5.6.

**Isso já foi provado num laboratório** (`ecidade_lar12`, porta 8087, ver §8):

- **3.294 telas legadas** rodaram sobre o vendor do Laravel 12 e ficaram **idênticas ao 5.6**, salvo as 23 divergências que já existiam antes (zero regressão). O legado não depende do Laravel novo e não é afetado por ele.
- O Laravel 12 **não inicializa**. Ele morre no primeiro *service provider* (`BaseDeferredProvider`), e `/v4/oauth/token` dá 500. **Todo o seu trabalho começa daí.**

## 3. O que já se sabe que vai quebrar

### Pacotes que não instalam com Laravel 12

| Pacote | Por quê | Quem usa |
|---|---|---|
| `silex/silex` | projeto morto | `api/V1` (20 arquivos); 1 rota do Tributário, `post recibo` |
| `dbseller/sdk-api-pix-bb` | guzzle 6 | **PIX do Tributário**: `app/Domain/Tributario/Arrecadacao/Pix/Bancos/BancoDoBrasil.php` |
| `dbseller/phinx_postgres` | phinx 0.10 / symfony antigo | migrações de banco |
| `proner/phppimaco` | mpdf 7, PHP ≤ 7.3 | etiquetas |

Fora esses quatro, **135 pacotes resolveram** (symfony 7/8, guzzle 7, phpspreadsheet 5, dompdf 3, mpdf 8). A lista de bloqueios e o motivo de cada um estão em `ecidade/tmp/lar12/trava_*.txt`.

### Classes que deixam de carregar

São **29 de 3.910** classes de `app/` + `src/`:

- 21 em `src/Console`: `execute()` sem `: int`, exigido pelo symfony 7;
- 8 em `app/`:
  - `Handler::report(Exception)` em vez de `Throwable`;
  - `BaseDeferredProvider::register()`;
  - traits de Auth que foram removidas;
  - Pimaco.

### APIs removidas, por varredura

- 50 `DB::raw` em `app/` (mudou no 10);
- 10 helpers `str_*`/`array_*` (removidos no 6);
- 5 `$dates` em models (removido no 10);
- 1 `Passport::routes()` (removido no 11);
- 105 usos do PhpOffice (1.8 → 5).

**Isso é o que a varredura enxerga, não o custo total.** O custo real só aparece depois que o boot funcionar e as rotas começarem a responder. Ele é **não medido**, e qualquer estimativa feita antes disso é chute.

## 4. Decisões já tomadas (não refaça)

1. **Passport 12.4, NÃO o 13.** O banco é compartilhado com o 5.6, que usa Passport 4. A migração do Passport 13 **apaga** colunas de `oauth_clients` que o Passport 4 usa (`user_id`, `redirect`, `personal_access_client`, `password_client`) e passa a exigir segredo com hash. Isso derrubaria o login do 5.6. O 12.4 aceita Laravel 12 e só **acrescenta** colunas opcionais. Atenção: o `composer.lock` do laboratório resolveu para o 13.10, então **fixe `"laravel/passport": "~12.4"`**.
2. **O password grant vem desligado no Passport 12.** O login do e-cidade usa esse grant. Ligue-o com `Passport::enablePasswordGrant()`.
3. **O login fica no 5.6 até o fim.** Testado: um token **real**, emitido pelo Passport 4 do 5.6, é **aceito** pelo `league/oauth2-server` 8.5.5 (o do Passport 12.4). Os controles negativos foram recusados: token adulterado e token revogado. Logo as rotas `/v4/api/*` podem passar ao 8.5 com o login ainda no 5.6. O verificador é `scratchpad/valida_token.php`.
   **Limite do teste:** ele valida a assinatura e a revogação. A camada de cima (`TokenGuard`, que carrega o cliente e o usuário) só roda com o Laravel 12 inicializando. Repita a conferência quando o boot funcionar.
4. **Nada de migração destrutiva no banco.** Ele é compartilhado. Toda migração do Laravel novo tem de deixar o 5.6 funcionando: só acrescentar, nunca apagar nem renomear.

## 5. A ordem recomendada

Cada passo tem um critério de pronto. Não avance sem ele.

```
0. Laboratório reproduzido          -> /v4/oauth/token no :8087 dá o MESMO 500 descrito aqui
1. composer.json do 8.5 fechado     -> composer install sem erro, Passport ~12.4,
                                       os 4 bloqueados resolvidos ou isolados
2. Laravel 12 inicializa            -> `php artisan route:list` lista as 138 rotas
3. Rotas /v4/api/tributario/* no 8.5, login ainda no 5.6
                                    -> mesma resposta JSON nos dois (ver §6)
4. Demais rotas /v4/api/*           -> idem
5. Login (/v4/oauth/token) no 8.5   -> por último, quando nada mais depender do 5.6
```

Sobre o passo 1, os quatro bloqueados:

- **`silex`**: o uso real é só a API `api/V1`. O `use Silex\Application` do `app.php` é import sem uso. Reescrever as rotas dela em Laravel é provavelmente mais barato que substituir o Silex por outro micro-framework. Meça antes: são 20 arquivos.
- **PIX BB**: é preciso para o Tributário. A saída é atualizar o SDK (o repositório é da DBSeller) ou trocá-lo por chamadas guzzle 7 diretas.
- **`phinx_postgres`** e **`phppimaco`**: não estão no caminho do Tributário. Podem ficar fora do `vendor` do 8.5 enquanto as rotas que os usam continuarem no 5.6.

Por que **cedo** importa: trocar o vendor do 8.5 **antes** das próximas áreas legadas serem migradas significa que elas já nascem verificadas sobre o Laravel novo. Trocar depois obriga a reverificar tudo.

## 6. Como verificar: a mesma ideia do legado, aplicada a JSON

A regra do projeto inteiro é **"a única variável é a versão"**. O 5.6 continua vivo como referência, e o 8.5 tem de responder **igual**. Para o legado, isso é feito comparando HTML byte a byte com `scratchpad/cmp.py`. Para a API:

1. obtenha um token no `:8080` (`POST /v4/oauth/token`);
2. chame a mesma rota com o mesmo token no `:8080` e no `:8085`;
3. compare o JSON. Normalize só o que muda por construção (datas de geração, ids aleatórios) e **anote cada regra de normalização com o falso positivo que a motivou**. É assim que o `cmp.py` foi construído.

Para rotas que **gravam**, use o nível 3, `scratchpad/escrita_post.py` e o roteiro de `scratchpad/demo_nivel3.sh`: snapshot das tabelas e das sequências, POST no 5.6, restore, POST no 8.5, restore, e compare o SQL que cada lado emitiu no log do PostgreSQL.

**Critério de sucesso de uma rota:** a mesma resposta (status + corpo normalizado) nos dois runtimes, **e**, se ela grava, o mesmo SQL de negócio. "Respondeu 200" não é critério: no legado, dezenas de telas respondiam 200 com dado errado.

## 7. Armadilhas que já morderam este projeto

- **Ponto cego atual, 14 telas legadas chamam a API por JavaScript:**
  - TEF: `arr2_operacoespendentestef001/002`, `cai3_gerfinanc075`;
  - PIX: `cai3_gerfinanc001`, `cai1_pix002`;
  - parcelamentos vencidos: `arr4_rollback_parc_venc`, `arr4_agendamendo_parc_venc`;
  - ISSQN: `iss4_ordemservico001`, `iss4_alvaraeventos001`, `iss179_inscricaoredesim`;
  - veículos do ISSQN: `forms/db_frminscricaoveiculos_aba_condutores`, `_incricao`;
  - tipo de débito: `forms/db_frmarretipo002`;
  - número cadastral: `cad4_parametrosnumerocadastral001`.

  Elas já são servidas pelo 8.5, mas o AJAX vai a `/v4/api/tributario/*`, que hoje responde no 5.6. **Nenhuma bateria exercitou essas chamadas** (o `curl` não executa JS). Quando as rotas passarem ao 8.5, são estas telas que provam o resultado ponta a ponta.
- **18 telas legadas do Tributário usam classes de `app/` diretamente** (93 classes de `app/` são usadas pelo legado na base toda, 44 delas models). Elas rodam **sob os dois Laravels** ao mesmo tempo: no 5.6 com o 5.4, no 8.5 com o 12. Qualquer mudança nessas classes tem de funcionar nas duas versões até o 5.6 sair. Antes de alterar uma classe de `app/`, procure se o legado a usa (`grep -ra` pelo nome, com `-a`: 64% da base é LATIN-1 e o `grep` sem `-a` pula esses arquivos em silêncio).
- **Testes não podem contatar terceiros reais.** PIX (Banco do Brasil) e TEF (adquirente) chamam serviços externos. Use sandbox ou dublê. Uma tela de lote do ISSQN já foi pega disparando conexão a um servidor real durante a bateria.
- **As rotas do ITBI usam o middleware `clientCredential`.** Quem as chama é uma aplicação externa (ITBI online), não uma tela. Teste-as com um token de *client credentials*, não de usuário.
- **O Laravel transforma *deprecation* em exceção.** O handler converte qualquer erro, inclusive `E_DEPRECATED`, em `ErrorException`. Uma deprecation do PHP 8.5 numa rota derruba a requisição inteira, enquanto o legado (que não passa pelo handler) segue. Não confunda os dois comportamentos.
- **Encoding.** O banco é LATIN1 e 64% dos fontes também. Não abra e salve arquivos LATIN-1 num editor configurado para UTF-8: os acentos se corrompem. Isso já aconteceu no TCC de referência.
- **Verificação que dá "0 erros" também precisa ser conferida.** Neste projeto, quase toda falha de instrumento pareceu sucesso:
  - `while read … php -l` engoliu a lista;
  - `xargs` parou no primeiro fatal;
  - o comparador contou timeout como idêntico.

  Sempre confira **quantos itens entraram** contra **quantos saíram**.

## 8. O laboratório, para reproduzir

Container `ecidade_lar12`, porta **8087**, mesma imagem do 8.5 (`e-cidade-ecidade_php85`), na rede `e-cidade_ecidade`:

| Montagem | Destino |
|---|---|
| `ecidade/` | `/var/www/html` |
| `ecidade/tmp/lar12/vendor` | `/var/www/html/vendor` |
| `ecidade/tmp/lar12/bcache` | `/var/www/html/bootstrap/cache` |
| `ecidade/tmp/lar12/storage` | `/var/www/html/storage` |
| `docker/php85-apache/paridade-56.ini` | `/usr/local/etc/php/conf.d/zz-paridade-56.ini` (ro) |
| volumes `ecidade_tmp`, `ecidade_sessions` | `/tmp`, `/var/lib/php/sessions` |

`ecidade/tmp/` é gitignored: o laboratório **não está versionado**. O `composer.json` dele é o atual com `laravel/framework ^12.0` e os demais pacotes em `*`. Para a migração de verdade, transforme isso num `docker-compose` próprio (o do 5.6 não se altera) e num `composer.json` do 8.5 **versionado**, com versões fixadas.

Duas armadilhas desta montagem:

- **`storage/` sobreposto começa vazio**: sem `oauth-public.key` e `oauth-private.key`. Copie as chaves do `storage/` real, senão todo token é recusado com `Invalid key supplied`, o que parece incompatibilidade e é só a chave faltando.
- **Ao clonar pacotes da DBSeller por SSH**, o Composer falha sem chave. Use `git config --global url."https://github.com/".insteadOf git@github.com:`. Os repositórios são públicos por HTTPS.

Para comparar telas legadas contra o laboratório: `PORTA_B=8087 python3 scratchpad/cmp.py <SID> '<regex>'`. Para remover tudo: `docker rm -f ecidade_lar12 && rm -rf ecidade/tmp/lar12`.

## 9. O que ainda é desconhecido

- **O custo real.** Não dá para medir até o boot funcionar (passo 2).
- Se as 138 rotas respondem igual depois do boot. Nenhuma foi exercitada sob Laravel 12.
- O `TokenGuard` do Passport 12.4 com o `oauth_clients` do Passport 4 (§4, item 3).
- Se vale mais a escada de versões (5.4 → 5.5 → … → 12, um guia oficial por degrau) ou reescrever direto sobre o 12. O laboratório pulou direto para o 12. Como o legado não depende do stack HTTP, só do Eloquent (que já roda no 8.5), a reescrita pode sair mais barata. É uma decisão sua, e vale medir as duas num módulo pequeno antes de escolher.
