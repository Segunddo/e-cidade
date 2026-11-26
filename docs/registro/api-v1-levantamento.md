# API V1 (Silex) no PR #8: levantamento para a decisão do grupo

O PR #8 tirou o `silex/silex` do `composer.json` e o roteamento `api/vN/` do `FrontController.php`, mas deixou o código da API V1 (`ecidade/api/`, 34 arquivos, 1.932 linhas) no repositório.
Este registro levanta, **sem mudar código e sem banco**, o que a decisão precisa: o que o PR mudou, quem usa a V1, e as três opções com custo e risco. Só leitura de código e de histórico.

## 1. O que o PR mudou (arquivo:linha)

O corte está no commit `c2c9af06a` (04/11/2026, "feat: atualizações do ecidade"), comparado com o código anterior ao PR (`base-php84`, que ainda roteava a V1).

| Arquivo | Antes do PR | Depois do PR |
|---|---|---|
| `ecidade/FrontController.php` | linhas 4-6: `if (preg_match('/[^?]*api\/v\d\//', $requestUri)) { return require_once 'api/api.php'; }` | removidas; entra a linha 3, `$_SERVER['HOME'] = __DIR__ . '/tmp';`. Um pedido a `/api/v1/…` agora não casa nenhuma regra e cai em `return require('app.php')` (linha 13) |
| `ecidade/composer.json` | linha 50: `"silex/silex": "^2.0"`; linha 56: `"symfony/validator": "~3.2"`; `symfony/console`, `filesystem`, `process`, `yaml` em `~3.2` | `silex/silex` e `symfony/validator` fora; as outras quatro em `v5.3.7` / `v5.4.12`. No `composer.lock`, o pacote `silex/silex` passa de 1 ocorrência para 0 |
| `ecidade/api/` (34 arquivos) | — | **só 1 linha mudou**, em `api/V1/Middleware/Session/MenuAcessadoSessionMiddleware.php:55`: `DefaultSession::getInstance()->status() !== DefaultSession::ACTIVE` virou `session_status() !== PHP_SESSION_ACTIVE`. O resto da V1 ficou como estava |
| `ecidade/app.php` | `use Silex\Application;` (linha 15) | igual (import sem uso; a classe não é carregada) |
| `ecidade/con4_manutencaoformulario001.php` | linha 498: `request.send('api/v1/configuracao/formulario/' + …)` | linha 506: `URL = "<?= ECIDADE_REQUEST_PATH ?>v4/api/" + rota`: o único consumidor interno da V1 passou a chamar `/v4/` |

Efeito: com a base do PR a V1 **não responde mais** (o `FrontController` não a despacha) e **não poderia subir** de qualquer jeito: `api/api.php` importa `Silex\Application` (linhas 19-20, 37) e o Silex não está mais no `vendor/`.
Ou seja, o 7.4 do PR, que é a referência, já está sem a V1.

## 2. O que a V1 faz e quem a usa

Prefixo `/api/v1` (`ApplicationConfig::APPLICATION_PREFIX`, `Configs/ApplicationConfig.php:9`), 5 providers montados em `APIServiceProvider.php:28-32` e 7 rotas:

| # | Método e caminho | Controller | Observação |
|---|---|---|---|
| 1 | `POST /auth/login` | `Auth\Login` | |
| 2 | `GET /protocolo/cgm` | `Protocolo\Cgm::getAll` | |
| 3 | `GET /protocolo/cgm/{id}` (`id` numérico) | `Protocolo\Cgm::get` | |
| 4 | `GET /configuracao/formulario/{id}/instituicao/{instituicao}` | `Configuracao\Formulario::getAll` | consumidor interno migrado pelo PR (item 1) |
| 5 | `POST /tributario/recibo` | `Tributario\Recibo::geraRecibo` | |
| 6 | `POST /matriculaonline/inscricao` | `MatriculaOnline\InscricaoCandidato::inscricao` | |
| 7 | `GET /matriculaonline/emissaoProtocolo` | `MatriculaOnline\InscricaoCandidato::emissaoProtocolo` | |

**Consumidores dentro do repositório** (`git grep -i 'api/v1'` fora de `vendor/` e de `api/`): só `scripts/HTTPRequest.js:17`, que aponta para um servidor de desenvolvimento da DBSeller (`dev23.dbseller.com.br:5300/dbportal_prj/api/v1/protocolo/cgm/`): resto de teste, não uma chamada de produção.
O consumidor que havia em `con4_manutencaoformulario001.php` o PR já trocou para `/v4/` (item 1). **Consumidores externos:** não dá para saber pelo código; as rotas 1, 5, 6 e 7 (login, recibo, inscrição e protocolo de matrícula online) têm forma de integração externa.
**Notas de versão:** em `ecidade/release_notes/` (até `v2.3.57`) nenhuma nota cita `api/v1`, Silex ou o desligamento da V1.

Existem rotas `/v4` de nome parecido (`routes/api/patrimonial/protocolo.php:64` `cgm`, `routes/api/educacao/central-de-matriculas.php:30` `emissao-protocolo`, `routes/api/tributario/arrecadacao.php:94` `gerar` do recibo/pix), mas **este levantamento não comparou o contrato** (corpo, autenticação, códigos de resposta) com o da V1.

Sobre a rota que atende a chamada migrada de `con4_manutencaoformulario001.php` (`v4/api/configuracao/formulario/…`), ver `defeitos-laravel8-do-pr.md` (seção 5): é defeito do PR, registrado lá.

## 3. As opções

| | (a) Seguir o PR: V1 desligada | (b) Container separado com a V1 | (c) Perguntar à DBSeller antes |
|---|---|---|---|
| O que é | nada a fazer no sistema; `api/` fica como está ou sai do repositório | container próprio (imagem do 8.5) com `vendor/` só da V1: `silex/silex` 2.2.4, Symfony 3.4, `league/fractal` 0.11, `cakephp/utility` 3.10.5, `zend-eventmanager` 2.2.10 (7 pacotes diretos, 23 na trava), e regra `/api/v1/` no proxy | enviar a pergunta abaixo e decidir com a resposta |
| Custo | zero de código (já está feito pelo PR) | um container a mais, um `vendor/` a manter, uma regra no proxy; nada muda no `./ecidade` | uma mensagem; o resto da migração segue |
| Risco | quebra qualquer integração externa que chame `/api/v1/` (rotas 1, 5, 6, 7) sem aviso; a V1 só existiria como código morto de 34 arquivos que importam uma classe ausente | mantém um framework arquivado (Silex, 2018) e o Symfony 3.4 fora de suporte; **o PR tirou o Silex e o roteamento da V1**, então manter é ir contra o que o PR fez | atraso se a resposta demorar |
| Evidência | leitura do PR (seção 1) | já existe e foi medido na base antiga: `docker-compose.api-v1.yml`, `docker/api-v1/composer.json` e `composer.lock`, `docs/migracao-laravel/api-v1-*.md` (branch local `arquivo/runtime-novo-laravel13-20261118`; medições em `arquivo/base-php84-20261118`). Lá: 4 rotas GET iguais ao runtime de referência e 233 telas iguais pelo proxy. **Medido com banco e na base antiga; não repetido aqui** | — |

**Recomendação para o levantamento (a decisão é do grupo):** (c) primeiro, porque a escolha entre (a) e (b) depende só de existir ou não integração externa, e isso o código não diz. Sem resposta, (a) é coerente com o PR e tem custo zero; (b) só se alguma integração externa for confirmada.

### Texto da pergunta à DBSeller (opção c)

> No PR #8 o `composer.json` perdeu o `silex/silex` e o `FrontController.php` deixou de despachar `/api/v1/…` para `api/api.php`, mas a pasta `ecidade/api/` (34 arquivos, 7 rotas: `POST auth/login`, `GET protocolo/cgm`, `GET protocolo/cgm/{id}`, `GET configuracao/formulario/{id}/instituicao/{instituicao}`, `POST tributario/recibo`, `POST matriculaonline/inscricao`, `GET matriculaonline/emissaoProtocolo`) continua no repositório.
> 1. O desligamento da API V1 foi intencional?
> 2. Algum cliente ou integração (portal de matrícula online, Redesim, sistema de terceiros) ainda chama `/api/v1/`? Em especial `auth/login`, `tributario/recibo` e `matriculaonline/*`.
> 3. Se sim, qual é o substituto previsto em `/v4/api/`? (Achamos rotas de nome parecido, mas não comparamos o contrato.)
> 4. A tela `con4_manutencaoformulario001.php` passou a chamar `v4/api/configuracao/formulario/{id}/instituicao/{instituicao}`: qual rota atende essa chamada?
> 5. A pasta `ecidade/api/` deve ser removida ou mantida?

## Conferência das contagens

Rodar da raiz do repositório, na `base-php74` (a coluna "Antes" é a `origin/base-php84`):

| Contagem | Comando | Resultado |
|---|---|---|
| arquivos em `ecidade/api/` | `git ls-files ecidade/api \| wc -l` | 34 |
| linhas em `ecidade/api/` | `git grep -c '' -- ecidade/api \| awk -F: '{s+=$NF} END {print s}'` | 1.932 |
| rotas HTTP | `git grep -nE '\$controllers->(get\|post\|put\|delete)\(' -- ecidade/api \| wc -l` | 7 |
| providers de rota montados | `git grep -nE '\$app->mount\(' -- ecidade/api \| wc -l` | 5 |
| arquivos de `api/` que citam Silex ou Pimple | `git grep -lE 'Silex\|Pimple' -- ecidade/api \| wc -l` | 20 |
| `silex/silex` no `composer.lock` | `git show origin/<base>:ecidade/composer.lock \| grep -c '"name": "silex/silex"'` | 1 em `base-php84`, 0 em `base-php74` |
| consumidores de `api/v1` fora de `vendor/` e de `api/` | `git grep -niE 'api/v1' -- ecidade ':!ecidade/vendor' ':!ecidade/api' \| wc -l` | 1 (`scripts/HTTPRequest.js:17`) |
| notas de versão que citam `api/v1` ou Silex | `git grep -niE 'api/v1\|silex' -- ecidade/release_notes \| wc -l` | 0 |

## Como foi levantado

`git diff origin/base-php84 origin/base-php74` limitado a `FrontController.php`, `composer.json`, `composer.lock`, `api/` e `app.php`; `git log -S` para achar o commit; `git grep` por `api/v1`, `Silex` e `formulario`; leitura de `api/api.php`,
dos 5 providers de rota e das rotas `/v4`. Sem rodar nada e sem banco.
