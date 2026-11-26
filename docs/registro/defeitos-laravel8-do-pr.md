# Defeitos do Laravel 8 do PR #8 já presentes no PHP 7.4

Registro de dez famílias de defeito que o código do PR #8 da DBSeller (`base-php74`, `laravel/framework` 8.73.2) já tem **no PHP 7.4**: as três primeiras medidas por trecho isolado (sem banco e sem rede), as quatro seguintes lidas no código, a oitava rodada com o `artisan` (sem banco e sem rede), a nona lida no inventário das chamadas do front a `/v4` e a décima medida no modelo `CertificadoUsuario` (sem banco e sem rede).
São herança do código escrito para o Laravel 5.4 e rodado sobre o Laravel 8: não dependem do PHP 8.5 e **não foram corrigidos aqui** (só registro, para o grupo e para a DBSeller decidirem).

| Família | Pontos na `base-php74` | Efeito no 7.4 |
|---|---|---|
| `Cache::put` com TTL em minutos | 6 chamadas em `app/` e `src/`: 5 com TTL errado, 1 correta (e 4 `forever` sem TTL, não afetadas) | o valor expira em segundos, e não em minutos |
| Helpers removidos do Laravel (`array_pluck`, `str_random`) | 2 chamadas em 2 arquivos | `Error: Call to undefined function` |
| `env()` fora de `configuration/` | 105 chamadas em 46 arquivos PHP (82 em 33 arquivos de `app/`); não contados: `libs/db_conn.php.dist` (10, arquivo-modelo) e `tests/cypress/**` (6, `Cypress.env` de JavaScript) | devolve `null` se a configuração for posta em cache (`config:cache`) |
| `DBFormRequest::response()` sem efeito no Laravel 8 | 1 método, herdado por 105 form requests | a resposta 406 de validação não é produzida; vale a 422 padrão |
| Rota ausente para a tela `con4_manutencaoformulario001.php` | 1 chamada (`:500-506`), 1 controller sem rota | a chamada a `v4/api/configuracao/formulario/{id}/instituicao/{instituicao}` não tem rota em `routes/` |
| Form request duplicado com o mesmo nome completo (`AutenticacaoRequest`) | 2 arquivos, 1 nome de classe | só o arquivo da pasta `ITBI` é carregado pelo autoload; o outro, com mais uma regra, nunca vale |
| Factory legada sem o pacote que a carrega (`database/factories/ModelFactory.php`) | 1 arquivo, 1 `$factory->define` (`:15`) | o arquivo não roda; falha em `$factory` antes do `str_random` da linha 22 |
| `artisan schedule:list` e `artisan list --format=json` | 2 comandos do console que não funcionam, iguais no 7.4 e no 8.5 | `schedule:list` termina com erro (rc 1); `list --format=json` termina sem saída (rc 0) |
| Front que chama rota `/v4` que não existe | 52 chamadas em 26 arquivos (29 em `tributario/cadastro`, 5 em `request-api-pix`) | a chamada não acha rota em `routes/` |
| Cast `'DateTime'` (nome de classe) em `CertificadoUsuario` | 1 modelo, 2 atributos (`c142_data`, `c142_validade`) | toda escrita falha com `Call to undefined method DateTime::set()`; a leitura devolve `Carbon` |

## 1. `Cache::put` com TTL em minutos

No Laravel 5.4 o terceiro argumento de `Cache::put` era em **minutos**; do 5.8 em diante é em **segundos** (`Illuminate\Cache\Repository::put` lê o TTL por `getSeconds()`, `Cache/Repository.php:207`
e `:524-533`; TTL ≤ 0 não guarda: chama `forget`, `:209-210`). O código do PR continua passando minutos.

Medido no PHP 7.4.33 com `illuminate/cache` 8.73.2 (`ArrayStore`, relógio controlado), sem rede:

| `put(..., N)` | depois de | resultado |
|---|---|---|
| 5 | 4 s / 6 s | ainda no cache / **expirado** |
| 10 | 9 s / 11 s | ainda no cache / **expirado** |
| 60 | 59 s / 61 s | ainda no cache / **expirado** |
| `Carbon::now()->addMinutes(10)` | 9 min / 11 min | ainda no cache / expirado (correto) |

Pontos na `base-php74` (arquivo:linha):

| Onde | TTL passado | Vale hoje | Pretendido |
|---|---|---|---|
| `app/Domain/Assinador/Controllers/AssinadorAPI.php:177` | `5` | 5 s | 5 min (propriedades do estorage entre pedidos) |
| `app/Jobs/RecursosHumanos/Pessoal/EmissaoContraChequeJob.php:124` | `10` | 10 s | 10 min |
| `app/Domain/Patrimonial/PNCP/Clients/PNCPClient.php:67` | `60` | 60 s | 60 min, se seguir a convenção das outras chamadas de token (sem comentário no código) |
| `app/Domain/Saude/Farmacia/Clients/BnafarClient.php:234` | `$response->expires_in / 60000` (o comentário diz "para minutos") | 60 s para um token de 3.600.000 ms | 60 min |
| `app/Domain/Patrimonial/Licitacoes/Clients/LicitaconObrasClient.php:47` | `expiraEm / 60000`, ou `30` sem `expiraEm` | 60 s para `expiraEm` = 3.600.000; 30 s sem `expiraEm`; **0** (não guarda) para `expiraEm` < 60.000 | 60 min; 30 min |
| `src/Lib/Request/ProcessoEletronico/ProcessoEletronico.php:209` | `Carbon::now()->addMinutes(10)` | 10 min | 10 min: **correto**, não é defeito |

Os 4 controllers que usam `Cache::store('file')->forever(...)` (`ProcessamentoConcessaoController.php:105`, `CancelamentoParcelamentoPorListaController.php:71`,
`AnulacaoCDAPorListaController.php:77`, `IncluirInicialListaController.php:82`) não têm TTL e não são afetados.

Efeito: onde o valor é um token de serviço externo (PNCP, Bnafar, Licitacon), o cache dura 60 vezes menos do que o autor queria e o sistema pede novo token a cada pedido fora da janela de segundos.
Onde o valor é um dado de passagem (`estorage_properties`), ele some em 5 ou 10 s; o código que o lê em seguida (`Cache::get('estorage_properties')`, `AssinadorAPI.php:172-173`) encontra vazio.
Medido com TTL fracionário: `expiraEm` de 3.600.000 ms vira TTL 60 e o valor vive 60 s; de 30.000 ms vira 0,5, que vira 0, e o valor não chega a ser guardado.

## 2. Helpers removidos do Laravel

O Laravel 6 tirou os helpers `array_*` e `str_*` do framework e os pôs no pacote `laravel/helpers`, que **não** está no `composer.json` nem no `composer.lock` da `base-php74`.
Medido no 7.4.33 com `illuminate/support` 8.73.2: `array_pluck`, `str_random`, `array_get` e `str_slug` não existem (`Error: Call to undefined function array_pluck()`);
`str_contains` existe (polyfill do Symfony que o `illuminate/support` já traz), `env`, `data_get` e `class_basename` também.

Busca na `base-php74` (fora de `vendor/`) por 40 helpers removidos (`array_add` … `array_wrap`, `camel_case`, `ends_with`, `snake_case`, `starts_with`, `str_*`, `head`, `last`, `title_case`…): só duas chamadas quebram.

| Onde | Chamada | Efeito |
|---|---|---|
| `app/Domain/RecursosHumanos/Pessoal/Controller/Jetom/ComissaoController.php:75` | `array_pluck($sessao->servidores->toArray(), 'dados_servidor.rh245_matricula')` | `Error` ao listar as comissões do Jetom (rota em `routes/api/recursos-humanos/pessoal.php`) com ao menos uma sessão |
| `database/factories/ModelFactory.php:22` | `str_random(10)` (`remember_token` da factory do `Usuario`) | `Error` se a linha fosse executada, mas a factory inteira já está morta antes dela (seção 7) |

Em `edu4_cancelaprogressao001.php` a linha 96 é um comentário (`/* TABELA diariofinal */`) e o arquivo não chama nenhum helper removido.

## 3. `env()` fora de `configuration/`

O Laravel recomenda chamar `env()` só nos arquivos de configuração: com `php artisan config:cache`, o `.env` deixa de ser carregado
(`Foundation/Bootstrap/LoadEnvironmentVariables.php:22-24` volta sem carregar quando a configuração está em cache) e `env()` fora de `configuration/` devolve `null`.
Sem `config:cache` funciona (nada no repositório pede `config:cache`; não foi medido com cache).

Contagem na `base-php74` (`git grep -nE '\benv\('` em `ecidade/*.php`, fora de `vendor/`, `tmp/`, `configuration/` e `config/`): **105 chamadas em 46 arquivos PHP**, das quais **82 em 33 arquivos de `app/`** e 23 em 13 arquivos fora de `app/`.
Esse mesmo `git grep` sem restringir a `.php` dá 121 em 50; a diferença são duas exclusões deliberadas: `libs/db_conn.php.dist` (10 chamadas, arquivo-modelo de configuração do banco, não é carregado como PHP) e `tests/cypress/**` (6 chamadas de `Cypress.env`, API do Cypress em JavaScript, não o `env()` do Laravel).

Dentro de `app/` (33 arquivos): `Redesim/RedesimService.php` 13; `Usuario/Services/AuthService.php` 8; 4 cada em `CentralMatriculasHelper.php`, `PNCPClient.php`, `AgataDocumentTemplateAlvara.php`,
`app/Helpers/Functions.php` e `AuthSimMiddleware.php`; 3 cada em `CertificadoPfxService.php`, `AuthRedesimMiddleware.php` e `RedesimErrorToProcessEstablishmentsMail.php`; 2 cada em 9 arquivos; 1 em 14 arquivos.
Fora de `app/` (13 arquivos): `model/documentoTemplate.model.php` 5 (`DB_HOST`, `DB_DATABASE`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`); `extension/package/Desktop/Controller/Menu.php` 4;
`src/Patrimonial/Protocolo/Servicos/AndamentoProcessoService.php` 4; 1 cada em `bootstrap.php`, `bnc4_processos001.php`, `con4_atividades_documentos.php`, `con4_mensagems.RPC.php`, `db_assinar_documentos.php`,
`iss3_consinscr003_imprimealvara.php` e 4 modelos de `fpdf151/impmodelos/` (`mod_imprime6`, `mod_imprime16`, `mod_imprime1016` e `especificos/mod_imprime_especifico_29_00001501.php`).

## 4. Validação: `DBFormRequest::response()` não é chamado

`app/Http/Requests/DBFormRequest.php:24` define `response(array $errors)`, que devolve `DBJsonResponse` com status 406 e a primeira mensagem de erro. O `FormRequest` do Laravel 8.73.2 **não tem** `response()` (saiu no 5.5; ele tem `failedValidation()`, `Foundation/Http/FormRequest.php:136`):
quem falha validação lança `ValidationException`, que `app/Exceptions/Handler.php:49` entrega ao `parent::render` (422 ou redirecionamento). O formato 406 do `DBFormRequest` não é produzido; 105 form requests herdam dessa classe.
Conferência: `git grep -lE 'extends DBFormRequest' -- ecidade/app ecidade/src | wc -l` dá 105 e `git grep -nE 'function response' -- ecidade/app/Http/Requests` dá 1 (o método acima).

## 5. Rota ausente para a tela de manutenção de formulário

`con4_manutencaoformulario001.php:500-506` monta `v4/api/configuracao/formulario/{id}/instituicao/{instituicao}` (o PR trocou a chamada que era `api/v1/configuracao/formulario/…`). Existe `FormularioGenericoController` (`app/Domain/Configuracao/Configuracao/Controllers/`),
mas nenhuma rota em `routes/` aponta para ele: `git grep -nE 'FormularioGenericoController' -- ecidade ':!ecidade/vendor'` só acha a própria declaração da classe e `git grep -niE 'formulario' -- ecidade/routes` não acha nada.
Se a rota existe por outro meio, o grupo confirma; se não, a tela chama um caminho sem rota.

## 6. Form request duplicado: `AutenticacaoRequest`

`app/Domain/Tributario/Arrecadacao/Requests/AutenticacaoRequest.php:3` declara `namespace App\Domain\Tributario\ITBI\Requests;`, o mesmo nome completo de `app/Domain/Tributario/ITBI/Requests/AutenticacaoRequest.php:3`.
As regras diferem: a cópia de `Arrecadacao` tem `dataPagamento` (`required|date|max:10`, linha 28), a de `ITBI` só `numeroGuia` (linha 27). O `composer.json` mapeia `App\` para `app/` (PSR-4, linha 87), então o autoload só acha a cópia da pasta `ITBI`;
o controller usa esse nome (`ITBI/Controllers/AutenticacaoController.php:7`) e nada importa a pasta `Arrecadacao` (`git grep -nE 'Arrecadacao.Requests.AutenticacaoRequest' -- ecidade ':!ecidade/vendor'` dá 0). A cópia de `Arrecadacao` é código que não roda; se um classmap carregasse as duas,
a segunda declaração daria erro de classe já declarada.
Conferência: `git grep -nE '^namespace App.Domain.Tributario.ITBI.Requests;' -- ecidade/app/Domain/Tributario/Arrecadacao` dá 1 linha.

## 7. Factory legada sem o pacote que a carrega

`database/factories/ModelFactory.php:15` usa `$factory->define(\App\Domain\Configuracao\Usuario\Models\Usuario::class, …)`, a forma do Laravel até o 7, em que a variável `$factory` é injetada por `Illuminate\Database\Eloquent\Factory`.
O Laravel 8.73.2 do PR **não tem** essa classe (só `Illuminate\Database\Eloquent\Factories\Factory`, a factory por classe) e o pacote que a manteria, `laravel/legacy-factories`, não está no `composer.json` nem no `composer.lock`.
Resultado no 7.4: o arquivo não é carregado por nada e, se fosse incluído, falharia na linha 15 (`$factory` indefinida) antes de chegar ao `str_random` da linha 22. A factory inteira está morta, não só uma chamada.
Conferência: `git grep -nE '\$factory->define' -- ecidade/database | wc -l` dá 1 e `git grep -nE 'laravel/legacy-factories' -- ecidade/composer.json ecidade/composer.lock | wc -l` dá 0.

## 8. Dois comandos do `artisan` que não funcionam

Medido com o `artisan` do PR (`php artisan ...`), sem banco e sem rede: o PHP 7.4.33 e o 8.5.12 com o Laravel 8.73.2, o `.env` de teste com host de banco inexistente. O resultado é o mesmo nos dois PHPs.

**8.1 `schedule:list` falha sempre.** `vendor/laravel/framework/src/Illuminate/Console/Scheduling/ScheduleListCommand.php:42` faz `->setTimezone($this->option('timezone', config('app.timezone')))`, mas `option()` aceita um só argumento (`Illuminate/Console/Concerns/InteractsWithIO.php:105`, `option($key = null)`):
o segundo é ignorado e o valor passado a `setTimezone()` é `null`. Saída (rc 1): no 7.4, `DateTime::setTimezone() expects parameter 1 to be DateTimeZone, null given`; no 8.5, `DateTime::setTimezone(): Argument #1 ($timezone) must be of type DateTimeZone, null given`.
Com `--timezone=America/Sao_Paulo` o erro é o mesmo, com a diferença de que o valor chega como texto (`string given`). O defeito é do pacote nesta versão (nenhum arquivo do PR chama `schedule:list`); atinge quem rodar o comando para ver o agendamento.

**8.2 `list --format=json` sai vazio com rc 0.** O `JsonDescriptor` do Symfony Console faz `json_encode($data, $flags)` sem `JSON_PARTIAL_OUTPUT_ON_ERROR` (`symfony/console/Descriptor/JsonDescriptor.php:103`); se qualquer descrição de comando não for UTF-8 válido, `json_encode` devolve `false` e nada é escrito.
No PR, 3 comandos têm a `$description` em ISO-8859-1: `RedesimAutomaticEstablishmentProcessTask.php:31` (`tributario:redesim:automaticEstablishmentProcess`), `ReenvioLancamentosRequisicaoMaterial.php:24` (`lancamento:requisicao-material-reenvio`) e `AlteracaoSituacaoInscricaoTask.php:28` (`matriculaonline:alteracaoinscricao`), todos em `app/Console/Commands/`.
Prova da causa: `list --format=json` de um namespace sem esses comandos funciona (`migrate`: 17.314 bytes), e dos três namespaces deles (`tributario`, `lancamento`, `matriculaonline`) sai com 0 byte. `list`, `list --raw` e `list --format=xml` funcionam (111 comandos no `--raw`).

## 9. Front que chama rota `/v4` que não existe

O inventário das chamadas a `/v4` (`inventario-telas-v4.md`) achou **52 chamadas em 26 arquivos** do front (telas legadas, `scripts/` e componentes Vue) a caminhos que não estão registrados em `routes/`.
29 são de `tributario/cadastro` (`emissao_ecarta`, `decad`, `calculo_iput`, `arquivo_xml_correios`: não há controller para elas na `base-php74`) e 5 de `tributario/arrecadacao/request-api-pix` (o `RequisicaoAPIPIXController` existe, mas nenhuma rota aponta para ele). A lista completa e o método estão em `inventario-telas-v4.md` e em `inventario-v4-chamadas.tsv` (classe `sem_rota`); não se repetem aqui.
Conferência: `awk -F'\t' 'NR>1 && $6=="sem_rota"' docs/registro/inventario-v4-chamadas.tsv | wc -l` dá 52 e a mesma linha com `| cut -f1 | sort -u | wc -l` dá 26.

## 10. Cast `'DateTime'` do `CertificadoUsuario`

`app/Domain/Assinador/CertificadoUsuario.php` declara `'c142_data' => 'DateTime'` e `'c142_validade' => 'DateTime'` (com o nome da classe, não `'datetime'`). Para o Eloquent isso é um
**cast de classe** (`class_exists('DateTime')`): a escrita chama `DateTime::set()`, que não existe. Medido com o modelo real, sem banco (formato de data fixado para não pedir conexão):

| Operação | 7.4 (Laravel 8.73.2) | 8.5 (Laravel 13.43) |
|---|---|---|
| `$m->c142_data = new DateTime(...)`, `= '2026-11-20 10:00:00'`, `= null` e `forceFill` | `Error: Call to undefined method DateTime::set()` | igual |
| leitura de `c142_data` com o valor cru do banco | `Illuminate\Support\Carbon` | `Error: Call to undefined method DateTime::get()` |
| `toArray()` | array | `Error: Call to undefined method DateTime::get()` |
| escrita de outro atributo (`c142_codigo`) | normal | igual |

Ou seja: gravar um certificado já falhava no 7.4 (defeito herdado, não corrigido aqui); o que o Laravel 13 acrescenta é a **leitura** quebrar (o Laravel 8 lia por causa do `strtolower` no tipo do cast). A sobreposição do 8.5 dessa classe (`app-85/`, tarefa de Eloquent e datas) cobre a leitura e mantém a escrita como no 7.4.
O trecho carrega de propósito o arquivo do PR (`app/Domain/Assinador/CertificadoUsuario.php`) nos dois lados, antes do autoload: a sobreposição do 8.5 (`app-85/`), quando existe, vence no PSR-4 e mediria outro código.
Conferência: `bash ecidade/tests/sistema/defeitos-laravel/roda.sh 09_cast_datetime.php`.

## 11. Revalidação no Laravel 13.43 (PHP 8.5)

Cada família medida de novo pelo trecho próprio, em `ecidade/tests/sistema/defeitos-laravel/` (`roda.sh` roda cada trecho no 7.4 com o
vendor do `ecidade/composer.lock` do PR, Laravel 8.73.2, e no 8.5 com o vendor da integração, Laravel 13.43.0 e Symfony Console 8.1.11, por
`docker/composer-85/roda-isolado.sh`: imagens do projeto, `--network none`, sem banco). Só registro: nada foi corrigido.

| Família | Laravel 13 (8.5) | Medido / causa |
|---|---|---|
| `Cache::put` com TTL em minutos (1) | **continua** | TTL inteiro é segundos nos dois; `put(..., 5/10/60)` expira em 5/10/60 s; `expiraEm` de 30.000 ms (TTL 0,5) não guarda. A diferença é o limite da expiração, para qualquer TTL: no 7.4 o valor ainda vale no segundo do TTL e no 8.5 não (1 s a menos). Medido: `expiraEm` de 3.600.000 ms (TTL 60) vive 61 s no 7.4 e 60 s no 8.5; de 1.800.000 ms (TTL 30, o caso do `LicitaconObrasClient.php:47` sem `expiraEm`) vive 31 s no 7.4 e 30 s no 8.5. O código do PR é o mesmo (6 chamadas) |
| Helpers removidos (2) | **continua** | `array_pluck`, `str_random`, `array_get`, `str_slug` não existem; `laravel/helpers` ausente da trava do 8.5; `Error: Call to undefined function array_pluck()`; 2 chamadas no código |
| `env()` fora de `configuration/` (3) | **continua** | `LoadEnvironmentVariables::bootstrap` do Laravel 13 também volta sem carregar o `.env` com a configuração em cache; 105 chamadas, sem mudança no código |
| `DBFormRequest::response()` (4) | **continua** | `FormRequest::response()` não existe no 13; `failedValidation` lança `ValidationException` nos dois (a mensagem `validation.required` × `The given data was invalid` vem só do tradutor vazio do trecho); 105 form requests herdam |
| Rota ausente `con4_manutencaoformulario001.php` (5) | **continua** (é do código) | `FormularioGenericoController` só aparece na declaração da classe; não depende da versão |
| `AutenticacaoRequest` duplicado (6) | **continua** | o autoload carrega `app/Domain/Tributario/ITBI/Requests/AutenticacaoRequest.php` (regra `numeroGuia`) nos dois; a cópia de `Arrecadacao` não vale |
| Factory legada (7) | **continua** | `Error: Call to a member function define() on null` nos dois; `laravel/legacy-factories` ausente |
| `artisan schedule:list` (8.1) | **some** | medido com o `artisan` real do PR: no 7.4 termina com `DateTime::setTimezone() expects parameter 1 to be DateTimeZone, null given` (rc 1); no 8.5 lista os agendamentos. O `ScheduleListCommand` do Laravel 13 foi reescrito: `new DateTimeZone($this->option('timezone') ?? config('app.timezone'))` (linha 74) |
| `artisan list --format=json` (8.2) | **continua** | com o `artisan` real: `list --format=json` e `list` dos namespaces `tributario`, `lancamento` e `matriculaonline` saem com 0 byte nos dois (ISO-8859-1 na descrição de 3 comandos do PR; o `JsonDescriptor` do Symfony Console 8.1.11 também não usa `JSON_PARTIAL_OUTPUT_ON_ERROR`); `list migrate --format=json` sai com JSON (17.315 bytes no 7.4, 18.925 no 8.5) |
| Front que chama rota `/v4` inexistente (9) | **continua** (é do código) | 52 chamadas sem rota; não depende da versão do Laravel |
| Cast `'DateTime'` de `CertificadoUsuario` (10) | **muda**: a escrita continua falhando, a leitura passa a falhar | seção 10 |

O app do PR sobe no Laravel 13 (inicialização integrada), por isso os itens 8.1 e 8.2 foram medidos pelo `artisan` real e a medida do item 5 com o roteador ligado
fica para a bateria de rotas. Nenhuma família muda por causa do PHP 8.5: as diferenças vêm do Laravel 13 (8.1 some, 10 muda a leitura) ou são o limite de 1 s do TTL.

Resumo: das 10 famílias, 8 continuam no Laravel 13 (a 1 com 1 s de diferença no limite do TTL), 1 some (`schedule:list`) e 1 muda (a leitura do cast `'DateTime'`). Para rodar:
`bash ecidade/tests/sistema/defeitos-laravel/roda.sh` (precisa de `runtime-85/vendor` e de `runtime-85/referencia-74/vendor`, instalados com
`composer-85.sh install --no-scripts --ignore-platform-req=php+` e com `composer install` do `ecidade/composer.lock`).

## Como foi medido

Sem banco e sem rede. `illuminate/support`, `illuminate/cache` (e as dependências) 8.73.2 baixados por `composer install --ignore-platform-reqs` numa pasta
(com `config.platform.php` = 7.4.33), e o script `scratchpad/laravel8_medir_defeitos.php` (copiado para essa pasta, ao lado de `vendor/`) rodado em contêiner descartável:

```bash
docker run --rm --network none -v <pasta>:/app:ro -w /app php:7.4-cli php laravel8_medir_defeitos.php
```

As buscas de arquivo:linha são `git grep` na `base-php74`; cada contagem do resumo se confere com o comando abaixo (rodado a partir da raiz do repositório). Nada no código foi alterado.

| Contagem | Comando | Resultado |
|---|---|---|
| `Cache::put` (seção 1) | `git grep -nE 'Cache::put\(' -- ecidade/app ecidade/src \| wc -l` | 6 (5 com TTL errado, 1 correta) |
| `Cache::store('file')->forever` | `git grep -nE "Cache::store\('file'\)->forever" -- ecidade/app ecidade/src \| wc -l` | 4 |
| `array_pluck`, `str_random` (seção 2) | `git grep -nE '(^\|[^A-Za-z_>:$])(array_pluck\|str_random)\(' -- ecidade ':!ecidade/vendor' ':!ecidade/tmp'` | 2 linhas, 2 arquivos |
| `env()` total (seção 3) | `git grep -nE '\benv\(' -- 'ecidade/*.php' ':!ecidade/vendor' ':!ecidade/tmp' ':!ecidade/configuration' ':!ecidade/config' \| wc -l` | 105 (46 arquivos com `-l`) |
| `env()` em `app/` | `git grep -nE '\benv\(' -- 'ecidade/app/*.php' \| wc -l` | 82 (33 arquivos com `-l`) |
| arquivos que declaram `class AutenticacaoRequest` (seção 6) | `git grep -lE '^class AutenticacaoRequest' -- ecidade/app \| wc -l` | 2 |
| …deles com a namespace de `ITBI` dentro da pasta `Arrecadacao` | `git grep -nE '^namespace App.Domain.Tributario.ITBI.Requests;' -- ecidade/app/Domain/Tributario/Arrecadacao \| wc -l` | 1 |
| `$factory->define` / pacote `laravel/legacy-factories` (seção 7) | os dois comandos da seção 7 | 1 / 0 |
| `$description` em ISO-8859-1 (seção 8) | `python3 -c "import re,glob;print(sum(1 for f in glob.glob('ecidade/app/**/*.php',recursive=True) for m in re.finditer(rb'\\\$description\s*=\s*([^;]*);',open(f,'rb').read()) if m.group(1).decode('utf-8','ignore').encode()!=m.group(1)))"` | 3 |
| form requests que herdam `DBFormRequest` (seção 4) | `git grep -lE 'extends DBFormRequest' -- ecidade/app ecidade/src \| wc -l` | 105 |
