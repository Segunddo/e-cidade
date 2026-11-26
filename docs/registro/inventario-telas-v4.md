# Telas e front Vue que chamam `/v4`: inventário (sem banco)

Para saber por onde começar quando as rotas `/v4` forem comparadas entre o 7.4 e o 8.5: quais telas legadas (`*.php` da raiz e `forms/`), scripts (`scripts/`, `extension/`) e componentes Vue (`resources/vue/`) chamam quais rotas,
e quais rotas ninguém chama. **Só leitura de código na `base-php74`: nada foi rodado e não houve banco.** As rotas foram lidas dos arquivos de rotas (sem `route:list`), e as chamadas foram achadas por varredura de texto.

**Resumo:** 1.311 rotas `/v4` (mais 113 `/web` e 4 `/rest`); **935 têm chamador firme**, 81 só um chamador provável, 13 só uma chamada à base do caminho e **282 não têm chamador achado**.
1.337 chamadas em 485 arquivos (234 telas legadas, 233 arquivos Vue, 17 `scripts/`, 1 `extension/`); 52 chamadas em 26 arquivos apontam para rotas que **não existem**.

Arquivos de dados (todos em `docs/registro/`): `inventario-v4-rotas.tsv` (1.428 rotas com situação e exemplos de chamador), `inventario-v4-chamadas.tsv` (1.337 chamadas: arquivo, linha, método, caminho, classe, rotas casadas) e `inventario-v4-lotes.tsv` (62 lotes).

## Como foi feito

Três scripts em `scratchpad/`, rodados em sequência da raiz do repositório:

```bash
python3 scratchpad/inventario_v4_rotas.py rotas.tsv
python3 scratchpad/inventario_v4_chamadas.py rotas.tsv chamadas.tsv rotas-uso.tsv
python3 scratchpad/inventario_v4_lotes.py rotas.tsv rotas-uso.tsv chamadas.tsv inventario-v4-rotas.tsv inventario-v4-lotes.tsv
```

- **Rotas** (`inventario_v4_rotas.py`): parte de `app/Providers/RouteServiceProvider.php` e segue `Route::prefix`, `Route::middleware`, `Route::group`, `->group(closure)`, `->group(base_path('routes/...'))`, `Route::get/post/put/patch/delete/match/resource/apiResource`.
  Resolve as variáveis de caminho e de controller que são só de literais (`$x = '...'`, `$x .= '...'`), **com o valor vigente na linha de cada `Route::`**: vários arquivos reatribuem a variável (`routes/api/tributario/issqn.php` redefine `$routePrefix` e `$controller` 3 vezes), e usar o último valor trocaria as rotas de um bloco pelas de outro.
  Acrescenta as 15 rotas do Passport 10 (`Passport::routes(null, ['prefix' => 'v4/oauth'])`, do pacote) e as 2 de `Broadcast::routes(['prefix' => 'v4'])` (`BroadcastServiceProvider.php:17`, do framework).
- **Chamadas** (`inventario_v4_chamadas.py`): acha `v4/...` dentro de string em `.php`, `.js`, `.vue`, `.html` (fora de `vendor/`, `tmp/`, `public/`, `tests/`, `routes/`, `database/`, `dbagata/`), troca `${x}`, `' + x + '` e `<?= ?>` por `{x}`, tira a query string e detecta o método pela chamada vizinha (`.get(`, `.post(`, `method:`). Classes:
  `exata` (o caminho existe), `composta` (o arquivo define a base e outro literal dele fecha uma rota), `relativa` (`'financeiro/planejamento/x'` com a base vinda de `requestApi`/`urlApi`/`apiUrl`; a tela legada nem escreve `v4/`),
  `provavel` (o literal é o rabo de uma rota, 2 segmentos ou mais), `prefixo` (só a base de um módulo), `base_global` (`/v4` ou `/v4/api` sem o resto) e `sem_rota` (nenhuma rota casa).
  Fora da conta ficam 22 ocorrências em `app/` e `src/`, que são comentários `@api` das próprias rotas, não chamadores.
- **Lotes** (`inventario_v4_lotes.py`): agrupa por `área/módulo` (os 2 primeiros segmentos depois de `v4/api`).

### Conferência da lista de rotas contra o Laravel

A lista foi comparada com a das rotas **registradas pelo próprio Laravel 8** (`docs/registro/php8-12-rotas.tsv`, branch `laravel/T-118-rotas-v4`, commit `cc1f63df3`, gerada com o framework carregado). Normalizando `{parametro}` e separando `PUT,PATCH`,
o conjunto de pares (método, caminho) de `/v4` é **o mesmo nos dois lados: 1.315 pares**. Nessa lista, 1.308 rotas `/v4` estão "vivas" e as demais são marcadas como substituídas ou sombreadas por outra de mesmo caminho; aqui todas entram.
Antes de o leitor passar a usar o valor vigente das variáveis, esta lista tinha 29 pares a menos e 13 a mais que a do Laravel (rotas do bloco errado em `issqn.php`, `condutorauxiliar` e `protocolo.php`); foi a comparação que pegou.
Os arquivos de rotas que nenhum provider carrega são os mesmos nas duas listas (seção 1); a diferença aparente de contagem (7, 29 e 2 lá; 6, 22 e 1 aqui) é que aqui só se contam as linhas `Route::<verbo>`, e lá toda linha `Route::`, inclusive `prefix` e `middleware`.

## 1. Rotas lidas

| Família | Rotas |
|---|---|
| `/v4/api/...` | 1.290 |
| `/v4/oauth/...` (Passport) | 15 |
| `/v4/login`, `/v4/logout`, `/v4/kill`, `/v4/unblock` | 4 |
| `/v4/broadcasting/auth` (`GET` e `POST`) | 2 |
| **`/v4` no total** | **1.311** |
| `/web/...` | 113 |
| `/rest/v1/...` | 4 |
| **Todas** | **1.428** (1.455 registros; 27 pares método+caminho aparecem duas vezes porque o mesmo arquivo de rotas é carregado por dois grupos) |

**Três arquivos de rotas que nenhum provider carrega**, 29 rotas que nunca são registradas: `routes/api/assinador/assinador.php` (6), `routes/api/patrimonial/ouvidoria.php` (22) e `routes/web/Tributario/Arrecadacao.php` (1).
Conferência: `git grep -nE 'assinador/assinador|patrimonial/ouvidoria|Tributario/Arrecadacao' -- ecidade/routes ecidade/app ecidade/bootstrap ecidade/configuration` não acha nenhuma referência.

## 2. Chamadas

| Classe | Chamadas |
|---|---|
| `exata` | 532 |
| `relativa` (+1 com método diferente) | 480 + 1 |
| `provavel` | 124 |
| `composta` | 96 |
| `sem_rota` | 52 |
| `base_global` | 28 |
| `prefixo` | 17 |
| `exata` com método diferente da rota | 7 |
| **Total** | **1.337** |

Por tipo de arquivo: 669 chamadas em telas legadas (234 arquivos), 610 em Vue (233 arquivos), 56 em `scripts/` (17 arquivos) e 2 em `extension/` (1 arquivo).

As 8 chamadas com método diferente da rota (7 `exata` e 1 `relativa`): `forms/db_frmrechumanoativ.php:198` (`atestado-frequencia/salvar-obs-rh`), `Jobs.vue:147` (`jobs/{x}destroy-many`), `AbaFinalizar.vue:188` (`gerador/relatorios/{x}`) e 5 em `ManutencaoParametrosFundeb.vue` (4) e `ProcessamentoRubricaSalario.vue` (1) (`rhcargo/list`, `rhlocaltrab/list`, `tipoasse/list`, `rhrubricas/list`).
O método é inferido da chamada vizinha, então podem ser falso alarme; fica para quem for comparar a rota.

## 3. Rotas × chamadores

De 1.311 rotas `/v4`:

| Situação | Rotas | Significado |
|---|---|---|
| `firme` | 935 | ao menos uma chamada `exata`, `composta` ou `relativa` |
| `provavel` | 81 | só chamadores `provavel` (o rabo da rota aparece num arquivo que usa a API) |
| `so_base` | 13 | só chamadas à base do módulo (`prefixo`) |
| `sem_chamador` | 282 | nenhum chamador achado |

### Chamadas sem rota (52 em 26 arquivos)

O front chama caminhos que **não estão registrados** em `routes/`. Por caminho (a soma fecha em 52):

| Caminho | Chamadas | De onde |
|---|---|---|
| `tributario/cadastro/emissao_ecarta/*` | 11 | Vue de `Tributario/Cadastro/` |
| `tributario/cadastro/decad/*` | 10 | Vue de `Tributario/Cadastro/` |
| `tributario/cadastro/calculo_iput/*` | 3 | Vue de `Tributario/Cadastro/` |
| `tributario/cadastro/arquivo_xml_correios`, `…/emitir` | 2 | Vue de `Tributario/Cadastro/` |
| `tributario/cadastro/matricula/listar` | 1 | Vue de `Tributario/Cadastro/` |
| `tributario/cadastro/grupo-debito/listar` e `…/search` | 2 | `DialogGrupoDebito.vue`, de `Tributario/Arrecadacao/` |
| `tributario/arrecadacao/request-api-pix/*` (`solicitar`, `listar`, `interromper`, `try-again-job`, `concluidos`) | 5 | Vue de `Tributario/Arrecadacao/` (4) e de `Tributario/Cadastro/` (1) |
| `tributario/arrecadacao/cota-unica/search` | 2 | Vue de `Tributario/Arrecadacao/` (1) e de `Tributario/Cadastro/` (1) |
| `tributario/arrecadacao/tipo-debito/search` | 1 | Vue de `Tributario/Arrecadacao/` |
| `educacao/matricula-online/configuracoes/*` (`imagens-personalizadas` 2, `cores-personalizadas` 1, `mensagens-personalizadas` 1) | 4 | Vue de matrícula online |
| `configuracao/arquivo_xml_correios/*` (`data`, `salvar`, `teste`) | 3 | `ArquivoXMLCorreios.vue` |
| `recursos-humanos/pessoal/rhfundlegal/list`, `recursos-humanos/pessoal/rhlotacoes/list` e `recursos-humanos/rh/concessaodireitos/relatoriooncessaoassent` | 3 | 2 Vue e `rec3_gerarconcport001.php` |
| `patrimonial/ouvidoria/atendimento/atendimento-json` | 2 | `AtendimentoJson.vue` (o arquivo de rotas da ouvidoria existe, mas ninguém o carrega) |
| `educacao/central-de-matriculas/processo-inscricao/processo-inscricao` | 1 | `ProcessoInscricaoService.js` |
| `educacao/transporte-escolar/emitir-carteira` | 1 | `EmissaoCarteiraEstudante.vue` |
| `financeiro/tesouraria/contas-tesouraria` | 1 | `index.vue` |
| **Total** | **52** | 26 arquivos |

Em `tributario/cadastro` são 29 chamadas pelo caminho (11 + 10 + 3 + 2 + 1 + 2); para elas não há controller na `base-php74`: `git grep -liE 'emissao_ecarta|calculo_iput|decad/' -- ecidade/app ecidade/routes ecidade/src` não acha nada.
Em `request-api-pix` o `RequisicaoAPIPIXController` existe, mas nenhuma rota aponta para ele. A lista linha a linha é `inventario-v4-chamadas.tsv` com `classe = sem_rota`.
Comando: `awk -F'\t' 'NR>1 && $6=="sem_rota"' docs/registro/inventario-v4-chamadas.tsv | wc -l` dá 52.

## 4. Rotas sem nenhum chamador conhecido (282)

| Por middleware | Rotas |
|---|---|
| `clientCredential` (token de cliente, forma de integração externa) | 43 (de 55 rotas `/v4` com esse middleware) |
| `AuthRedesim` / `AuthSim` (integração) | 1 |
| `auth:api` (usuário logado) | 176 |
| sem middleware de autenticação | 62 |

Por módulo, as que mais têm: `patrimonial/protocolo` 32, `financeiro/contabilidade` 29, `educacao/central-de-matriculas` 25, `tributario/issqn` 25, `recursos-humanos/pessoal` 22, `tributario/cadastro` 15 (todas `clientCredential`), `educacao/escola` 15, `financeiro/planejamento` 14, `tributario/itbi` 14 (`inventario-v4-lotes.tsv`, coluna `sem_chamador`).
Quase todas as `clientCredential` e as `/v4/oauth/*` (inclusive `POST /v4/oauth/token`, que o login novo não chama mais) têm cara de integração externa. As 176 com `auth:api` e as 62 sem autenticação podem ser tela que a varredura não achou ou rota sem uso.

**Esta lista é um limite superior.** Uma amostra de 40 rotas sem chamador achou o rabo do caminho em algum arquivo para 9 (22,5%): a base e o resto do caminho ficam em lugares diferentes, ou há método/parâmetro que o script não casou.
Estimativa: cerca de 22% das 282 (uns 63) já têm chamador; **cerca de 220 sem chamador é o número a esperar**.

## 5. Ordem sugerida dos lotes

Critério: primeiro o que toda sessão usa, depois os módulos com **mais arquivos chamadores distintos** (mais telas afetadas se a rota mudar), e por último o que só tem integração externa ou ninguém. Lotes de até ~60 rotas.

| Ordem | Lote | Rotas | Com chamador firme | Arquivos chamadores | Observação |
|---|---|---|---|---|---|
| 0 | acesso: `/v4/login`, `/logout`, `/kill`, `/unblock`, `/v4/oauth/*` e `/v4/broadcasting/auth` | 21 | 6 | login e Desktop | toda sessão passa por aqui; depende do Passport 13 |
| 1 | `configuracao/*` (16 módulos: `gerador` 15, `jobs` 15, `instituicao` 7, `menu` 7, `usuario` 6, `banco-pix` 5…) | 78 | 50 | 8 (`gerador`), 6, 5, 4, 4 | usadas pelo Desktop e por vários componentes Vue |
| 2 | `financeiro/contabilidade` (3 lotes) | 157 | 116 | 55 | o módulo com mais chamadores (26 Vue) |
| 3 | `educacao/escola` (3 lotes) | 141 | 112 | 42 | |
| 4 | `financeiro/planejamento` (2 lotes) | 118 | 99 | 36 | só telas legadas (`pla*`, `pl4_*`), nenhuma em Vue |
| 5 | `recursos-humanos/pessoal` (2 lotes) | 107 | 74 | 33 | |
| 6 | `patrimonial/pncp` | 54 | 51 | 22 | |
| 7 | `financeiro/orcamento` | 45 | 35 | 22 | |
| 8 | `educacao/secretaria` | 37 | 34 | 18 | |
| 9 | `financeiro/tesouraria` | 27 | 24 | 17 | |
| 10 | `tributario/arrecadacao` | 46 | 35 | 16 | |
| 11 | `tributario/issqn` | 56 | 31 | 16 | |
| 12 | `educacao/matricula-online` | 41 | 36 | 14 | |
| 13 | `patrimonial/protocolo`, `tributario/cadastro` | 54 + 32 | 13 + 17 | 13 + 13 | boa parte é `clientCredential` ou sem chamador |
| 14 | os 27 lotes restantes (`financeiro/empenho`, `recursos-humanos/rh`, `saude/*`, `integracoes/*`…) | 297 | 202 | ≤ 12 cada | tabela completa em `inventario-v4-lotes.tsv` |
| 15 | as 282 rotas sem chamador conhecido (estão dentro dos lotes acima: não somar) | 282 | 0 | 0 | por último, com a lista de integração externa à parte |

Os lotes 2 a 13 somam 915 rotas. A soma dos lotes 0, 1, 2 a 13 e 14 é 21 + 78 + 915 + 297 = 1.311, que é o total de `/v4` e a soma da coluna `rotas` de `inventario-v4-lotes.tsv` (`awk -F'\t' 'NR>1 {s+=$2} END {print s}' docs/registro/inventario-v4-lotes.tsv`). O lote 15 não entra na soma (é um recorte dos outros).

## Conferência das contagens

Da raiz do repositório (`R` = `docs/registro/inventario-v4-rotas.tsv`, `C` = `docs/registro/inventario-v4-chamadas.tsv`):

| Contagem | Comando | Resultado |
|---|---|---|
| rotas (todas) | `tail -n +2 $R \| wc -l` | 1.428 |
| rotas `/v4` | `awk -F'\t' 'NR>1 && $2 ~ /^\/v4\//' $R \| wc -l` | 1.311 |
| `/v4/api`, `/v4/oauth`, `/web`, `/rest` | o mesmo `awk` com `/^\/v4\/api\//`, `/^\/v4\/oauth\//`, `/^\/web\//`, `/^\/rest\//` | 1.290, 15, 113, 4 |
| situação das rotas `/v4` | `awk -F'\t' 'NR>1 && $2 ~ /^\/v4\// {c[$6]++} END {for (k in c) print k, c[k]}' $R` | firme 935, provavel 81, so_base 13, sem_chamador 282 |
| `sem_chamador` com `clientCredential` / `/v4` com `clientCredential` | `awk -F'\t' 'NR>1 && $2 ~ /^\/v4\// && $6=="sem_chamador" && $4 ~ /clientCredential/' $R \| wc -l` (e sem o `$6==...`) | 43 / 55 |
| chamadas | `tail -n +2 $C \| wc -l` | 1.337 |
| arquivos com chamada | `tail -n +2 $C \| cut -f1 \| sort -u \| wc -l` | 485 |
| chamadas por classe | `tail -n +2 $C \| cut -f6 \| sort \| uniq -c` | `exata` 532, `relativa` 480 (+1), `provavel` 124, `composta` 96, `sem_rota` 52, `base_global` 28, `prefixo` 17, `exata(metodo difere)` 7 |
| chamadas por tipo | `tail -n +2 $C \| cut -f3 \| sort \| uniq -c` | `php-legado` 669, `vue` 610, `js` 56, `extension` 2 |
| arquivos com chamada `sem_rota` | `awk -F'\t' 'NR>1 && $6=="sem_rota"' $C \| cut -f1 \| sort -u \| wc -l` | 26 |
| soma dos lotes | `awk -F'\t' 'NR>1 {s+=$2} END {print s}' docs/registro/inventario-v4-lotes.tsv` | 1.311 (62 lotes) |
| linhas `Route::` lidas | `git grep -hE 'Route::(get\|post\|put\|patch\|delete\|any\|match)\(' -- ecidade/routes ecidade/app/Providers/RouteServiceProvider.php \| wc -l` | 1.411 (inclui linhas comentadas e as 29 dos arquivos não carregados; mais 8 `resource`/`apiResource`, que viram várias rotas) |

## Limites

- A varredura é de texto: chamada montada por código (`apiUrl + variavel`) em arquivo diferente da base só entra como `provavel` ou `prefixo`; chamada em arquivo que não foi lido (`dbagata/`, minificados de `public/`) não conta.
- O método do chamador é o da chamada mais próxima da linha; quando não acha, o casamento ignora o método.
- `/web/...` e `/rest/v1/...` foram lidas como rotas, mas não têm chamadores aqui (não são `/v4`).
- O uso real (telas mais acessadas) depende de dados de acesso, que não existem sem banco: a ordem usa o número de arquivos chamadores como aproximação.
