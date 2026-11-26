# Inventário do código próprio: Laravel 8 → 13 (guias 9 a 13)

Consulta de 20/11/2026, sobre a `base-php74` (PR da DBSeller: PHP 7.4, `laravel/framework ^8.0`, `laravel/passport ^10.0`, `doctrine/dbal 2.*`).
O guia do 8 já descreve o ponto de partida, então só entram os **guias de upgrade 9.x, 10.x, 11.x, 12.x e 13.x** (238 itens).
Somente leitura: nada neste inventário muda código.

## 1. Método

- **Guias:** `upgrade.md` de cada branch `9.x`…`13.x` de `github.com/laravel/docs`. Cada título de seção é um item.
- **Código varrido** (`ecidade/`): `app/`, `routes/`, `configuration/`, `bootstrap/`, `database/`, `public/`, `tests/`, `resources/` (116 arquivos Blade e 8 de `lang`; só os `.php`) e `composer.json`. Ficam de fora o legado procedural, `src/`, `api/` (Silex) e `vendor/`.
- **Varredura:** uma expressão regular por item, aplicada linha a linha (arquivos lidos como ISO-8859-1). Resultados:
  **USA** (padrão achado, com contagem e `arquivo:linha`), **NAO USA** (padrão sem ocorrência), **NAO APLICA** (item que não é código: versão de PHP, instalador, título de grupo) e **MANUAL** (não varrível por regex).
  Tipo **uso** = a regex acha o recurso; **sinal** = indício que precisa de olho (pode ser falso positivo); **config** = chave de configuração.
- **Limite:** regex acha texto, não semântica; chamada dinâmica não aparece. `grep` sem `-a` pula arquivos ISO-8859-1 e dá números menores.
- **"Miscellaneous"** de cada guia só remete ao diff do esqueleto `laravel/laravel`; não há lista de quebras, por isso é MANUAL.

| Resultado | Itens |
|---|---|
| USA | 42 |
| NAO USA | 92 |
| NAO APLICA | 99 |
| MANUAL | 5 |
| **Total** | **238** |

Arquivos de dados desta pasta:
- `inventario-8-a-13-itens.tsv`: os 238 itens (resultado, contagem, até 3 exemplos, tipo, padrão ou motivo, tarefa).
- `inventario-8-a-13-ocorrencias.tsv`: **todas** as ocorrências (versão, item, tarefa, `arquivo:linha`) dos itens que o código usa (2.782 linhas).

## 2. O que existe no código próprio

| Item | Quantidade |
|---|---|
| `app/` | 2.640 arquivos `.php`, 264.816 linhas |
| `routes/` | 130 arquivos, 4.234 linhas |
| `configuration/` | 13 arquivos (`app`, `auth`, `broadcasting`, `cache`, `database`, `filesystems`, `hashing`, `logging`, `mail`, `queue`, `services`, `session`, `view`) |
| `database/migrations` | 1.186 migrations do Laravel |
| Providers / middlewares | 7 em `app/Providers/` (8 classes `ServiceProvider` em `app/`) / 17 |
| Controllers | 5 em `app/Http/Controllers/` + 262 em `app/Domain/**/Controllers/` |
| Form requests | 289 declarações em `app/` (140 estendem `FormRequest` direto, 105 `DBFormRequest`, 44 `BaseFormRequest`) |
| Models Eloquent | 690 (os que estendem `Model` direto; subclasses de outros models não entram) |
| Jobs / commands / notifications | 16 / 15 / 6 |
| Funções globais próprias (`app/Helpers`) | nenhuma com nome de helper atual ou removido do Laravel (0 conflitos) |

## 3. Números já medidos em 18/11, conferidos

Mesmos padrões, mesma `base-php74`, repetidos em 20/11:

| Medida de 18/11 | Hoje | Padrão | Explicação |
|---|---|---|---|
| `$dates`: 21 models | **0** (eram 21 em 21 arquivos em 18/11) | `Model "Dates" Property` (10.x) | a troca de `$dates` por `$casts` nos 21 models foi integrada depois; a medida de 18/11 era 21 |
| Carbon: 256 usos | **256** em 100 arquivos | `Carbon 3` (11.x e 12.x, mesmo padrão) | igual. Contar toda menção à palavra `Carbon` dá 343 em 102 arquivos (inclui `use`, comentários e nomes de classe) |
| `DB::raw`: 302 | **302** em 75 arquivos | `Database Expressions` (10.x) | igual |
| `validated()`: 82 | **0** `->validated(` e **82** `->validate(` em 37 arquivos | `Unvalidated Array Keys` (9.x) | o número de 18/11, rotulado `validated()`, na verdade conta `->validate(`; não há nenhum `->validated(` no código |
| datas em JSON: 242 | **242** em 125 arquivos | `serializeDate\|->toArray()\|->toJson()` em `app/` (item 7.x, fora dos guias 9–13) | igual. É sinal: a data só muda se o model tiver atributo de data |
| 1.300 rotas | **1.407** definições `Route::get\|post\|put\|patch\|delete\|any` em 73 arquivos de `routes/`; **1.309** com caminho literal e sem comentário | `Route Precedence` (12.x) | a diferença para 1.300 é de contagem: 98 definições têm caminho não literal ou estão em comentário (11 comentadas com caminho literal), e `resource`/`apiResource` (6 + 2) expandem em várias rotas. O número exato de `route:list` exige subir o kernel, que depende de `vendor/` completo e do banco; **não foi medido** |

Contra o inventário anterior (feito sobre outra base, com 1.259 arquivos em `app/`, 325 models, 86 form requests e 561 rotas), os números subiram porque a `base-php74` tem o dobro de código (2.640 arquivos em `app/`, 690 models, 289 form requests contra 86).

## 4. Itens que o código usa

`Tarefa` é a tarefa dona do item (agrupamento na seção 5). Exemplos: até 3 `arquivo:linha`; a lista completa está em `inventario-8-a-13-ocorrencias.tsv`.

| Guia | Item | Ocorrencias | Arquivos | Exemplos | Tipo | Tarefa |
|---|---|---|---|---|---|---|
| 9.x | Exception Handler Contract Binding | 1 | 1 | `bootstrap/app.php:42` | uso | PHP8-62 |
| 9.x | Belongs To Many firstOrNew, firstOrCreate, and updateOrCreate Methods | 1 | 1 | `app/Domain/Educacao/Secretaria/Repositories/BaseDisciplinaRepository.php:29` | sinal | PHP8-55 |
| 9.x | The FILESYSTEM_DRIVER Environment Variable | 1 | 1 | `configuration/filesystems.php:16` | uso | PHP8-62 |
| 9.x | Flysystem 3.x | 7 | 3 | `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:371` `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:372` `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:377` | uso | PHP8-77 |
| 9.x | Overwriting Existing Files | 2 | 1 | `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:372` `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:384` | uso | PHP8-77 |
| 9.x | Write Exceptions | 2 | 1 | `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:372` `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:384` | uso | PHP8-77 |
| 9.x | Deleting Missing Files | 1 | 1 | `app/Domain/Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php:399` | uso | PHP8-77 |
| 9.x | The when / unless Methods | 231 | 65 | `app/Domain/RecursosHumanos/Pessoal/Model/Jetom/ComissaoServidor.php:238` `app/Domain/RecursosHumanos/Pessoal/Controller/Jetom/SessaoController.php:60` `app/Domain/RecursosHumanos/Pessoal/Controller/Jetom/SessaoController.php:63` | sinal | PHP8-55 |
| 9.x | The opis/closure Library | 1 | 1 | `composer.json:33` | uso | PHP8-62 |
| 9.x | Unvalidated Array Keys | 82 | 37 | `app/Domain/RecursosHumanos/ESocial/Controller/ExameToxicologicoController.php:21` `app/Domain/RecursosHumanos/Pessoal/Controller/ContraChequesController.php:119` `app/Domain/Integracoes/EFDReinf/Controllers/ConfiguracaoController.php:37` | sinal | PHP8-94 |
| 10.x | Minimum Stability | 1 | 1 | `composer.json:96` | config | PHP8-62 |
| 10.x | The registerPolicies Method | 1 | 1 | `app/Providers/AuthServiceProvider.php:29` | uso | PHP8-39 |
| 10.x | Database Expressions | 302 | 75 | `app/Domain/RecursosHumanos/Pessoal/Repository/TipoGuiaPrevidenciaRepository.php:217` `app/Domain/RecursosHumanos/Pessoal/Repository/TipoGuiaPrevidenciaRepository.php:224` `app/Domain/RecursosHumanos/Pessoal/Repository/TipoGuiaPrevidenciaRepository.php:225` | uso | PHP8-77 |
| 10.x | ULID Columns | 1 | 1 | `database/migrations/2022_10_24_103009_create_notifications_table.php:17` | uso | PHP8-55 |
| 10.x | Monolog 3 | 1 | 1 | `configuration/logging.php:3` | uso | PHP8-62 |
| 10.x | The dispatch() Helper Return Value | 12 | 12 | `app/Domain/RecursosHumanos/Pessoal/Services/ContraChequeService.php:50` `app/Domain/Financeiro/Contabilidade/Services/Relatorios/NovaLRF/EmiteControleVersaoService.php:22` `app/Domain/Patrimonial/Protocolo/Services/NoticarAssinanteDocumentoService.php:43` | uso | PHP8-51 |
| 10.x | Middleware Aliases | 1 | 1 | `app/Http/Kernel.php:74` | uso | PHP8-38 |
| 10.x | Service Mocking | 22 | 3 | `tests/TestCase.php:7` `tests/TestCase.php:13` `tests/Unit/RecursosHumanos/Pessoal/Service/ControleRubricasMatriculasServiceTest.php:13` | uso | PHP8-71 |
| 10.x | Closure Validation Rule Messages | 4 | 1 | `app/Domain/Saude/Laboratorio/Requests/TriagemLaboratorialRequest.php:59` `app/Domain/Saude/Laboratorio/Requests/TriagemLaboratorialRequest.php:65` `app/Domain/Saude/Laboratorio/Requests/TriagemLaboratorialRequest.php:80` | uso | PHP8-94 |
| 10.x | Validation Messages and Closure Rules | 4 | 1 | `app/Domain/Saude/Laboratorio/Requests/TriagemLaboratorialRequest.php:59` `app/Domain/Saude/Laboratorio/Requests/TriagemLaboratorialRequest.php:65` `app/Domain/Saude/Laboratorio/Requests/TriagemLaboratorialRequest.php:80` | uso | PHP8-94 |
| 11.x | Application Structure | 4 | 2 | `app/Http/Kernel.php:19` `app/Http/Kernel.php:45` `app/Http/Kernel.php:74` | uso | PHP8-62 |
| 11.x | Password Rehashing | 1 | 1 | `app/Http/Controllers/Auth/RegisterController.php:68` | sinal | PHP8-39 |
| 11.x | The AuthenticationException Class | 4 | 1 | `app/Exceptions/Handler.php:7` `app/Exceptions/Handler.php:19` `app/Exceptions/Handler.php:111` | uso | PHP8-62 |
| 11.x | Cache Key Prefixes | 1 | 1 | `configuration/cache.php:97` | config | PHP8-62 |
| 11.x | Eloquent Model casts Method | 58 | 58 | `app/Domain/Financeiro/Contabilidade/Models/ParametroIntegracaoPatrimonial.php:13` `app/Domain/Financeiro/Contabilidade/Models/EncerramentoPeriodoContabil.php:18` `app/Domain/Financeiro/Contabilidade/Models/Lancamento.php:30` | uso | PHP8-55 |
| 11.x | Modifying Columns | 3 | 2 | `database/migrations/2021_10_25_083540_alter_secret_to_oauth_clients.php:17` `database/migrations/2021_10_25_083540_alter_secret_to_oauth_clients.php:29` `database/migrations/2024_08_13_093320_M28685_ajuste_schema_tabela_mensageriaacordo.php:243` | uso | PHP8-55 |
| 11.x | Floating-Point Types | 14 | 5 | `database/migrations/2024_08_08_094811_m28016_rotina_elaboracao_pca.php:93` `database/migrations/2024_08_08_094811_m28016_rotina_elaboracao_pca.php:94` `database/migrations/2024_08_08_094811_m28016_rotina_elaboracao_pca.php:95` | uso | PHP8-55 |
| 11.x | Doctrine DBAL Removal | 1 | 1 | `composer.json:29` | uso | PHP8-62 |
| 11.x | Carbon 3 | 256 | 100 | `app/Domain/RecursosHumanos/Pessoal/Model/RhDepend.php:5` `app/Domain/RecursosHumanos/Pessoal/Model/RhDepend.php:27` `app/Domain/RecursosHumanos/Pessoal/Services/Relatorios/TipoGuiaPrevidenciaService.php:7` | uso | PHP8-55 |
| 11.x | Synchronous Jobs in Database Transactions | 3 | 1 | `configuration/queue.php:18` `configuration/queue.php:33` `configuration/queue.php:34` | config | PHP8-51 |
| 11.x | Updating Passport | 13 | 9 | `app/User.php:8` `app/Domain/Configuracao/Usuario/Models/Usuario.php:38` `app/Http/Kernel.php:16` | uso | PHP8-39 |
| 12.x | Carbon 3 | 256 | 100 | `app/Domain/RecursosHumanos/Pessoal/Model/RhDepend.php:5` `app/Domain/RecursosHumanos/Pessoal/Model/RhDepend.php:27` `app/Domain/RecursosHumanos/Pessoal/Services/Relatorios/TipoGuiaPrevidenciaService.php:7` | uso | PHP8-55 |
| 12.x | Container Class Dependency Resolution | 8 | 6 | `app/Domain/Patrimonial/Protocolo/Services/ProcessoService.php:629` `app/Domain/Patrimonial/Protocolo/Services/NotificarTransferenciaProcessoService.php:40` `app/Domain/Tributario/Arrecadacao/Repositories/TermoRepository.php:241` | sinal | PHP8-62 |
| 12.x | Nested Array Request Merging | 2 | 2 | `app/Http/Middleware/SessionMiddleware.php:51` `app/Http/Middleware/DBRequestMiddleware.php:30` | sinal | PHP8-38 |
| 12.x | Route Precedence | 1407 | 73 | `routes/web/configuracao/configuracao.php:7` `routes/web/configuracao/configuracao.php:15` `routes/web/configuracao/configuracao.php:19` | sinal | PHP8-12 |
| 12.x | Local Filesystem Disk Default Root Path | 3 | 1 | `configuration/filesystems.php:48` `configuration/filesystems.php:53` `configuration/filesystems.php:60` | config | PHP8-77 |
| 13.x | Cache Prefixes and Session Cookie Names | 7 | 4 | `configuration/database.php:39` `configuration/database.php:52` `configuration/database.php:65` | config | PHP8-62 |
| 13.x | Collection Model Serialization Restores Eager-Loaded Relations | 40 | 20 | `app/Notifications/UserNotificationAcordoVencimento.php:11` `app/Notifications/UserNotificationAcordoVencimento.php:15` `app/Notifications/EmissaoRelatorioLegalNotification.php:10` | uso | PHP8-51 |
| 13.x | Default Password Reset Subject | 1 | 1 | `app/Http/Controllers/Auth/ResetPasswordController.php:8` | uso | PHP8-51 |
| 13.x | Queued Notifications and Missing Models | 18 | 18 | `app/Notifications/UserNotificationAcordoVencimento.php:13` `app/Notifications/EmissaoRelatorioLegalNotification.php:12` `app/Jobs/RequisicaoAPIPixJob.php:21` | uso | PHP8-51 |
| 13.x | withScheduling Registration Timing | 1 | 1 | `app/Console/Kernel.php:51` | uso | PHP8-51 |
| 13.x | Request Forgery Protection | 3 | 2 | `app/Http/Kernel.php:52` `app/Http/Middleware/VerifyCsrfToken.php:5` `app/Http/Middleware/VerifyCsrfToken.php:7` | uso | PHP8-38 |

## 5. Agrupamento por tarefa

Quantidade de itens que o código usa, por tarefa. Cada tarefa fica com a lista da seção 4 (coluna `Tarefa`).

| Tarefa | Itens | Quais |
|---|---|---|
| PHP8-12 | 1 | 12.x Route Precedence |
| PHP8-38 | 3 | 10.x Middleware Aliases; 12.x Nested Array Request Merging; 13.x Request Forgery Protection |
| PHP8-39 | 3 | 10.x The registerPolicies Method; 11.x Password Rehashing; 11.x Updating Passport |
| PHP8-51 | 6 | 10.x The dispatch() Helper Return Value; 11.x Synchronous Jobs in Database Transactions; 13.x Collection Model Serialization Restores Eager-Loaded Relations; 13.x Default Password Reset Subject; 13.x Queued Notifications and Missing Models; 13.x withScheduling Registration Timing |
| PHP8-55 | 8 | 9.x Belongs To Many firstOrNew, firstOrCreate, and updateOrCreate Methods; 9.x The when / unless Methods; 10.x ULID Columns; 11.x Eloquent Model casts Method; 11.x Modifying Columns; 11.x Floating-Point Types; 11.x Carbon 3; 12.x Carbon 3 |
| PHP8-62 | 11 | 9.x Exception Handler Contract Binding; 9.x The FILESYSTEM_DRIVER Environment Variable; 9.x The opis/closure Library; 10.x Minimum Stability; 10.x Monolog 3; 11.x Application Structure; 11.x The AuthenticationException Class; 11.x Cache Key Prefixes; 11.x Doctrine DBAL Removal; 12.x Container Class Dependency Resolution; 13.x Cache Prefixes and Session Cookie Names |
| PHP8-71 | 1 | 10.x Service Mocking |
| PHP8-77 | 6 | 9.x Flysystem 3.x; 9.x Overwriting Existing Files; 9.x Write Exceptions; 9.x Deleting Missing Files; 10.x Database Expressions; 12.x Local Filesystem Disk Default Root Path |
| PHP8-94 | 3 | 9.x Unvalidated Array Keys; 10.x Closure Validation Rule Messages; 10.x Validation Messages and Closure Rules |

Legenda: PHP8-38 middlewares e sessão; PHP8-39 Passport e login; PHP8-51 e-mail, filas, comandos, agendamento; PHP8-55 Eloquent e datas;
PHP8-62 inicialização e configuração; PHP8-77 `DB::raw` e arquivos (Flysystem 3); PHP8-94 validação; PHP8-12 rotas `/v4`;
PHP8-71 testes próprios (item extra: `Service Mocking`, 22 usos em 3 arquivos de `tests/`).

Pontos que merecem atenção do dono (todos medidos acima):
- **PHP8-62:** `app/Http/Kernel.php` ainda usa `$routeMiddleware`/estrutura antiga (aceita no 11, 12 e 13); `bootstrap/app.php:42` faz o binding do handler de exceções; `configuration/filesystems.php:16` lê `FILESYSTEM_DRIVER`; `configuration/filesystems.php:48-60` depende da raiz padrão do disco local (muda no 12); `configuration/logging.php` (Monolog 3).
- **PHP8-55:** `$dates` (removida no 10) já saiu dos 21 models (troca por `$casts` integrada em 20/11), hoje 58 models com `$casts`, 256 usos de Carbon (Carbon 3 muda o retorno de `diffIn*`).
- **PHP8-77:** 302 `DB::raw`/expressões (a partir do 10 devolvem objeto `Expression`, não string); 7 usos de Flysystem em `ApropriacaoDecimoFeriasService.php:371-399` (3.x: sobrescrita, exceções de escrita, arquivo ausente).
- **PHP8-94:** 82 chamadas `->validate(` só em `app/` (0 de `->validated(`; a contagem da PHP8-94 inclui `src/` e dá 104) (a partir do 9 o validador exclui chaves sem regra) e 4 regras com closure em `TriagemLaboratorialRequest.php:59-80`.
- **PHP8-12:** 1.407 definições (precedência de rotas no 12 pode mudar o despacho de caminhos que se sobrepõem).

## 6. Como reproduzir

```bash
python3 scratchpad/inventario_laravel.py contagem                        # seção 2
mkdir /tmp/guias && for v in 9.x 10.x 11.x 12.x 13.x; do curl -sSf -o /tmp/guias/$v.md https://raw.githubusercontent.com/laravel/docs/$v/upgrade.md; done   # rede
python3 scratchpad/inventario_laravel.py itens /tmp/guias > docs/migracao-laravel/inventario-8-a-13-itens.tsv
python3 scratchpad/inventario_laravel.py ocorrencias /tmp/guias > docs/migracao-laravel/inventario-8-a-13-ocorrencias.tsv
python3 scratchpad/inventario_laravel.py md docs/migracao-laravel/inventario-8-a-13-itens.tsv   # tabela da seção 4
python3 scratchpad/inventario_laravel.py helpers                         # funções globais x helpers do Laravel
```

O script (`scratchpad/inventario_laravel.py`) e os padrões (`scratchpad/inventario_laravel_padroes.py`) ficam no repositório. Os guias baixados reproduzem os 238 itens de 20/11/2026; se a documentação mudar, itens novos aparecem como `SEM TRATAMENTO` em stderr.
