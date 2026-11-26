# Filas, comandos, agendamento e funções removidas no PHP 8.5 (PHP8-51)

Medido em 20/11/2026, sem banco, sem rede e sem fila de verdade. O 7.4 é o do PR: a imagem construída de
`docker/php74-apache` (PHP 7.4.33) com o `vendor/` instalado do `ecidade/composer.lock`. O 8.5 é a imagem de
`docker/php85-apache` (PHP 8.5.13) com o `vendor/` instalado da trava do 8.5 com Laravel 8.73.2: o
`ecidade/composer-85.lock` do commit `a4f604512` (sha256 `f2f90dd5fa05f75d72aefd3593a1ec6dc51d49279c2900317c3cb22d40f225a6`),
o último antes da troca para o Laravel 13 (PHP8-62), instalado com
`docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+`. Os dois lados têm o mesmo
Laravel 8.73.2 e sobem o kernel de console como o `artisan` faz (`bootstrap.php`, depois `bootstrap/app.php`). Cada
trecho roda pelo `docker/composer-85/roda-isolado.sh`. O ambiente de teste é o que ele gera do `.env.example`, mais
chave, token e endereços fictícios e banco num host que não existe (`anexos/filas-comandos-85/gera_env.py`, passado
em `ENV_EXTRA`).

**Resultado:** tudo igual. Nenhum arquivo do sistema muda nesta tarefa. A parte de e-mail e notificações da PHP8-51
fica em tarefa própria.

| O quê | Casos | 7.4 × 8.5 |
|---|---|---|
| `artisan list --raw` | 111 linhas | igual byte a byte |
| comandos: nome, classe, descrição, oculto, apelidos, argumentos e opções com padrão | 112 comandos (15 do e-cidade, em `app/Console/Commands`) | igual byte a byte |
| agendamento (`app/Console/Kernel.php`): comando, cron, fuso, descrição, `withoutOverlapping`, `onOneServer`, `runInBackground`, `evenInMaintenanceMode` e as 3 próximas execuções a partir de 01/01/2026 | 10 eventos | igual byte a byte |
| payload de fila (`createPayload` do Laravel): `displayName`, `job`, `maxTries`, `maxExceptions`, `failOnTimeout`, `backoff`, `timeout`, `retryUntil`, `commandName` e o `unserialize` de volta | 18 classes `ShouldQueue` (16 jobs e 2 notificações) | igual |
| objeto da fila gravado num runtime e lido no outro (estado de todas as propriedades, recursivo) | 18 classes × 4 combinações (7.4→7.4, 7.4→8.5, 8.5→7.4, 8.5→8.5) | 1 estado só nas 4 |
| `array_pluck` (`ComissaoController.php:75`) e `str_random` (`ModelFactory.php:22`) | 2 casos | igual: `Error: Call to undefined function` nos dois |
| `str_contains`: polyfill `symfony/polyfill-php80` no 7.4, nativa no 8.5 | 14 casos | 12 com o mesmo resultado; os 2 com array dão `TypeError` nos dois, só o texto da mensagem muda |
| avisos do PHP, no stderr e fora da saída comparada (seção abaixo) | todas as execuções | 7.4: nenhum; 8.5: 12 `Deprecated` de carga por execução, nenhum warning ou notice |

## Fila: o que muda e o que não muda

O `command` serializado sai igual byte a byte em 16 das 18 classes. Nas 2 notificações enfileiradas
(`EmissaoRelatorioLegalNotification`, `UserNotificationAcordoVencimento`, embrulhadas em `SendQueuedNotifications`,
como o Laravel faz), muda a **ordem** das propriedades na string. O `SerializesModels::__serialize` percorre
`ReflectionClass::getProperties()`. No 7.4, essa lista traz as propriedades herdadas (`id`, `locale` de
`Notification`) antes das do trait (`middleware` de `Queueable`); no 8.x, depois. As chaves e os valores são os
mesmos, e o `unserialize` monta o objeto por nome. A leitura cruzada prova isso: um job gravado pelo 7.4 e lido pelo
8.5, ou o contrário, chega ao mesmo estado. Por isso a fila pode ser gravada por um runtime e consumida pelo outro
durante a migração.

Quais classes: as de `app/` cujo arquivo cita `ShouldQueue` (21) e que implementam a interface, conferido por
reflexão (`anexos/filas-comandos-85/lista_filas.php`): 18. A busca por reflexão pega também as 2 declaradas com nome
qualificado (`implements \Illuminate\Contracts\Queue\ShouldQueue`: `EmissaoLrfJob`,
`ProcessarLancamentoContabilRequisicaoJob`). As outras 3 só importam a interface sem usá-la (2 Mailables e
`SolicitacaoAssinaturaNotification`).

Como o objeto foi montado (`anexos/filas-comandos-85/jobs.php`): primeiro o construtor real, com argumentos fixos
(classe tipada recebe instância sem construtor; `datausu` e `filtros` recebem o tipo que o código espera). Se o
construtor precisa de banco ou de serviço, vai sem construtor e cada propriedade da classe recebe um valor fixo. Os
dois runtimes seguiram o mesmo caminho nas 18 classes: 7 pelo construtor, 8 sem construtor por `QueryException` (banco
inexistente) e 3 sem construtor por `Exception` dos serviços do BNAFAR. Model vai como `ModelIdentifier`, e a
restauração, que consultaria o banco, não é feita.

O `ProcessPayrollDataJob` encerra no construtor com `die()` quando falta `API_DATA_AVAILABLE_TOKEN`/`_URL`, igual nos
dois. Com os dois valores fictícios no ambiente de teste, o payload sai.

## Avisos do PHP: fora da saída comparada

As imagens do projeto têm `display_errors=Off` e gravam o log de erros dentro do contêiner. O `roda-isolado.sh` sobe
cada trecho com `display_errors=stderr`, `error_reporting=E_ALL` e `log_errors=0`, e o `roda.sh` guarda o stderr de cada
lado em `err74.txt`/`err85.txt`, separado da saída comparada, com a contagem no resumo. Nada é filtrado. Depois do
`bootstrap()` do kernel, o Laravel assume (`HandleExceptions.php:42` põe `error_reporting(-1)`): warning e notice viram
exceção, que apareceria na saída comparada, e depreciação vai para o log.

Medido num checkout limpo, em todas as execuções:

- 7.4: nenhuma mensagem.
- 8.5: 12 `Deprecated` por execução, todas na carga, antes do kernel. São 0 warning e 0 notice.
  - `guzzlehttp/promises/src/functions.php`: 6 (parâmetro nulo implícito em `queue()`, `each()`, `each_limit()` e
    `each_limit_all()`);
  - `laravel/framework/src/Illuminate/Support/helpers.php`: 2 (`optional()`, `with()`);
  - `opis/closure/functions.php`: 1 (`unserialize()`);
  - `src/V3/Extension/ParameterBag.php`: 2 (tipo de retorno de `getIterator()` e `count()`);
  - `config/application.default.php:27`: 1 (constante `E_STRICT`).

São as mesmas 12 que o 8.5 dá ao subir o kernel em `laravel85-inicializacao.md` (lista em
`laravel85-inicializacao/deprecated-8.5.txt`). As 3 do código do e-cidade (`ParameterBag.php` e
`config/application.default.php`) vêm do `bootstrap.php`. Uma instalação com `config/application.php` local (fora do
git) soma mais 1 `E_STRICT` do mesmo tipo.

## Agendamento e lista de comandos: como foi lido

O `artisan schedule:list` e o `artisan list --format=json` do PR não servem para comparar: dão o mesmo erro nos dois
(defeitos do Laravel 8 do PR: `docs/registro/defeitos-laravel8-do-pr.md`). Por isso `anexos/filas-comandos-85/console.php` lê direto do kernel: os
comandos registrados e os eventos do `Schedule`, com a próxima execução calculada pela `CronExpression` a partir de uma
data fixa. A saída é `var_export`, porque as descrições estão em ISO-8859-1.

## Como reproduzir

```bash
bash docs/migracao-laravel/anexos/filas-comandos-85/roda.sh <vendor do 7.4> <vendor do 8.5> <saída>
```

Os dois `vendor/` vêm antes, com rede (só dependências). O do 8.5 é o de uma trava do 8.5; para a desta medição,
num checkout do commit `a4f604512`. O do 7.4 vai para uma pasta fora do repositório, pelo Composer
da própria imagem do 7.4, com `ecidade/` só leitura (o `mkdir` cria o ponto de montagem num checkout novo):

```bash
mkdir -p ecidade/vendor <vendor do 7.4>
docker run --rm -u "$(id -u):$(id -g)" -e COMPOSER_HOME=/tmp/ch -v "$PWD/ecidade:/app:ro" -v "<vendor do 7.4>:/app/vendor" \
  -w /app <imagem 7.4> composer install --no-scripts --no-plugins --no-interaction
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+   # o do 8.5, em runtime-85/vendor
```

O `roda.sh` chama o `docker/composer-85/roda-isolado.sh` para cada trecho, com `VENDOR` (o vendor de cada lado),
`ENV_EXTRA` (as variáveis de `gera_env.py`), `EXTRA_RO` (a pasta de saída em `/o`, para a leitura cruzada),
`STDERR_ARQ` (os avisos) e, na lista de classes, `STDIN=1`. O `artisan list` passa por `anexos/filas-comandos-85/artisan.php`,
que faz o mesmo que o `ecidade/artisan` com os caminhos em `/app`. Se um trecho falha ou sai vazio, o `roda-isolado.sh`
para, e o `roda.sh` imprime `FALHOU` e sai com código 1, em vez de comparar saídas vazias.

## Lacunas

- Nenhum job é executado (`handle()`), porque quase todos gravam no banco ou chamam serviço externo. Aqui se prova o
  que vai para a fila e volta dela, não o trabalho do job.
- Nenhum comando é executado além do `list`. A definição (assinatura, argumentos, opções) e o agendamento são os
  mesmos; o corpo de cada comando usa banco.
- O 8.5 foi medido com a trava do Laravel 8.73.2 (a mesma versão do 7.4). Com a trava atual do 8.5 (Laravel 13), a
  mesma prova roda passando o vendor dela no 2º argumento; essa medição é de etapa própria.
