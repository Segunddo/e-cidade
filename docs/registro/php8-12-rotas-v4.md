# Rotas `/v4`: precedência e conflitos, sem banco (PHP8-12, 20/11/2026)

**Resumo:** a `base-php74` (Laravel 8.73.2, PHP 7.4) registra **1.454** rotas, e **1.425** ficam vivas: 1.308 em `/v4`
(1.288 de `/v4/api` e 20 de `/v4`, login e OAuth), 113 em `/web` e 4 em `/rest/v1`.

- **Mesmo método e URI:** são 27 pares. Em todos a última rota registrada substitui a anterior, e essa regra é a mesma
  no Laravel 8 e no 12+.
- **Sombra:** 1 rota é sombreada por outra de padrão equivalente.
- **Rota que não casa:** 1 tem espaço no fim da URI e não casa com o próprio caminho.
- **Nome repetido:** a mudança de precedência do Laravel 12 só alcança `jobs.`, que passa a apontar para outra rota.
  Nenhum `route()` do código usa esse nome, então nada muda na resposta.
- **Closures:** 125 rotas usam closure.
- **Arquivos não carregados:** 5 dos 130 arquivos de `routes/`.
- **GET que só leem:** 460 das 629 GET vivas, pelos critérios abaixo; com as 113 telas de `/web`, 573.

Lista completa: `docs/registro/php8-12-rotas.tsv`, uma linha por rota registrada, na ordem.

## Como foi tirado (critério 1)

O `php artisan route:list --json` não serve sem banco. Ele instancia cada controller para ler o middleware, e o
construtor de `RegistroAulaService` consulta `secretariadeeducacao.sec_parametros`, o que dá
`could not find driver` sem servidor. Por isso foi usado um script próprio, `scratchpad/php8_12_rotas.php`:

- ele sobe o app do PR com o vendor da trava do PR no PHP 7.4, em contêiner `--network none`;
- `storage/` e `bootstrap/cache/` ficam em `tmpfs`, com um par de chaves OAuth gerado na hora e descartado;
- a `RouteCollection` é trocada por uma que anota onde cada rota foi registrada (arquivo:linha pelo `debug_backtrace`),
  inclusive as que outra rota substitui;
- depois a própria coleção responde qual rota casa com o caminho de exemplo de cada uma (`match()`), e nenhum
  controller é instanciado.

```bash
I74=php:7.4-cli@sha256:620a6b9f4d4feef2210026172570465e9d0c1de79766418d3affd09190a7fda5
# V=<pasta com o vendor/ da trava do PR (composer install do composer.lock, PHP 7.4)>
docker run --rm --network none -u $(id -u):$(id -g) -v $PWD/ecidade:/app:ro -v $V/vendor:/app/vendor:ro \
  -v $PWD/scratchpad:/s:ro --tmpfs /app/bootstrap/cache:uid=$(id -u) --tmpfs /app/storage:uid=$(id -u) -w /app $I74 sh -c '
  mkdir -p storage/framework/cache storage/framework/views storage/framework/sessions storage/logs
  php -r "\$k = openssl_pkey_new(array(\"private_key_bits\" => 2048)); openssl_pkey_export(\$k, \$p);
    file_put_contents(\"storage/oauth-private.key\", \$p); file_put_contents(\"storage/oauth-public.key\", openssl_pkey_get_details(\$k)[\"key\"]);"
  chmod 600 storage/oauth-*.key; php /s/php8_12_rotas.php' > rotas.json
python3 scratchpad/php8_12_rotas_tsv.py rotas.json docs/registro/php8-12-rotas.tsv   # lista + resumo (as contagens daqui)
```

O guia do grupo fala em cerca de 1.300 rotas. São as 1.308 vivas de `/v4`; esta lista conta também `/web` e
`/rest/v1`, e as rotas substituídas.

Colunas do `.tsv`: `ordem` de registro, `metodos`, `uri`, `nome`, `acao`, `onde` (arquivo:linha), `situacao` (`viva`,
`substituida-pela-N`, `sombreada-pela-N`, `nao-casa-o-proprio-caminho`), `get_so_leitura` (critério 4) e `acao_onde`.

## Conflitos e o que muda no 12+ (critério 2)

Regras usadas:

- **Guia oficial do Laravel 12, "Route Precedence":** *"The routing behavior when multiple routes have the same name has
  been unified between cached and uncached routing. This means that uncached routing now matches the first route
  registered with a given name instead of the last one."* No código: o `RouteCollection::refreshNameLookups()` do 8 fica
  com a última rota de cada nome, e o do 13 com a primeira (`! $this->inNameLookup($name)`).
- **Mesmo método e URI:** o `addToCollections()` guarda por método e domínio+URI, então a última rota substitui a
  anterior, no 8 e no 13.
- **Domínio:** o guia do 13 põe as rotas com domínio antes das outras. O código não tem nenhuma rota com domínio, então
  isso não o alcança.

| Grupo | Rotas | Responde no 8 | Responderia no 12+ |
|---|---|---|---|
| mesmo método e URI, mesma ação, declarada duas vezes | 9 pares: `escola.php:35/62`, `:36/63`, `:37/64`; `secretaria.php:6/11`, `:7/12`, `:56/65`, `:57/66`; `web/educacao/secretaria.php:21/36`; `sim/seguranca-integrada-municipios.php:8/9` | a segunda | a segunda (mesma ação) |
| `routes/api/patrimonial/licitacoes.php` carregado duas vezes (`api.php:128`, sem namespace, e `api.php:145`, com o namespace `Licitacoes\Controllers`) | 17 pares, linhas 3–25 | a segunda (`App\Domain\Patrimonial\Licitacoes\Controllers\…`) | a segunda |
| `POST v4/api/financeiro/orcamento/cadastro/recurso/excluir` | `orcamento.php:10` (`RecursoAntes2022Controller@excluir`) e `:17` (`RecursoController@excluir`) | `:17`, `RecursoController` | `:17`, `RecursoController` |
| padrão equivalente | `GET …/escola/{escola}/regimes-matricula/{codigo}` (`escola.php:120`) casa antes com `…/{ensino}` (`escola.php:119`) | `:119` | `:119` |
| URI com espaço no fim | `POST …/transporte-escolar/emitir-carteira ` (`transporte-escolar.php:11`) | nenhuma (o caminho sem espaço dá 404) | igual |
| nome repetido `jobs.` (grupo `->name("jobs.")` com rotas sem nome, `configuracao.php:139-143`) | `failed/retry-many` (`:141`) e `failed/destroy-many` (`:142`) | `route('jobs.')` → `destroy-many` | `route('jobs.')` → **`retry-many`** |

Só o nome `jobs.` muda com o 12+. Nenhum `route('jobs.')` existe no código (o único `route()` é `route('login')`, em
`app/Exceptions/Handler.php:120`), então a resposta das rotas não muda. Pela regra de não mexer no que não muda a saída,
não houve ajuste. Os outros 59 nomes são únicos.

## Nomes, closures e arquivos não carregados (critério 3)

- **Nomes:** 60, só `jobs.` repetido (acima).
- **Closures:** 125 rotas. São 14 em `/v4` (`educacao/files/*` 12, `educacao/escola/debug`, `saude/ambulatorial/cid`)
  e 111 em `/web`, as telas que devolvem a página. Lista: `acao = Closure` no `.tsv`. O `route:cache` do Laravel 8 não
  aceita closure, o do 13 aceita. Nada no projeto usa `route:cache` hoje.
- **Arquivos de `routes/` que nenhum outro carrega:** 5 de 130.

| Arquivo | Rotas no arquivo | Por quê |
|---|---|---|
| `routes/api/assinador/assinador.php` | 7 | o PR tirou a linha que o carregava de `routes/api.php` (existia na base anterior) |
| `routes/api/patrimonial/ouvidoria.php` | 29 | idem |
| `routes/web/Tributario/Arrecadacao.php` | 2 | cópia com maiúsculas de `routes/web/tributario/arrecadacao.php`, que é o carregado (`web.php:80`) |
| `routes/web/patrimonial/ouvidoria.php` | 0 | vazio |
| `routes/web/recursos-humanos/est-probatorio.php` | 0 | vazio, e a linha que o carregava está comentada (`web.php:100`) |

A referência é o PR, então as rotas de `assinador` e `ouvidoria` não existem no 7.4 e não entram na comparação.

## GET que só leem, para o lote 1 (critério 4)

Para cada GET viva, `get_so_leitura` lê o corpo do método do controller, ou da closure, por reflexão, sem instanciar.
O valor é `sim` quando nem o nome do método nem o corpo têm sinal de escrita:

- no nome: `salvar`, `incluir`, `excluir`, `processar`, `emitir`, `exportar`, `cancel…`, `atualiz…`, `limpar`...;
- no corpo: `->save(`, `::create(`, `->delete(`, `DB::statement`, `Cache::forget`, `session()->put`, `dispatch(`...

O que o corpo delega a outro serviço não é seguido: é o mesmo limite da leitura estática de antes. O `::create(` também
pega construtor estático de resposta, o que deixa a lista mais conservadora.

| Prefixo | `sim` | escrita pelo nome | escrita pelo corpo | ação inexistente | Total GET vivas |
|---|---|---|---|---|---|
| `/v4/api` | 451 | 14 | 16 | 25 | 506 |
| `/v4` (login, OAuth) | 5 | 0 | 1 (`oauth/authorize`, `session()->put`) | 0 | 6 |
| `/rest/v1` | 4 | 0 | 0 | 0 | 4 |
| `/web` (telas) | 113 | 0 | 0 | 0 | 113 |
| **Total** | **573** | **14** | **17** | **25** | **629** |

O lote 1 de `/v4` são as **460** com `sim` em `/v4/api`, `/v4` e `/rest/v1`. As 25 com ação inexistente dão erro já
no 7.4 e entram como erro igual. As 31 com sinal de escrita ficam para quando houver banco descartável.

## Lacunas

- Nada foi pedido por HTTP: o "quem responde" é o `match()` da própria coleção de rotas do Laravel 8, com um caminho de
  exemplo por rota (parâmetro `1` ou o primeiro valor que casa com o `where`).
- O 12+ foi avaliado pela regra do guia e pelo código do `RouteCollection` do 13, sem subir o Laravel 13 com as rotas.
- A classificação de leitura não segue os serviços que o controller chama.
