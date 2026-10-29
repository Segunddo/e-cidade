# Área Patrimonial (branch `4patrimonial-migrado`)

### 📐 Dimensionada e INICIADA (27/10/2026)

`scratchpad/dimensiona.py` refeito: **712 telas de menu faltando** (749 no menu, 6 fantasmas), universo 3.075,
873 já pagos, **469 a alterar** — os mesmos números de 22/10 (as 165 abas da 14ª lacuna não tocaram o universo de
Patrimonial).

8 módulos no banco: Compras 143 telas, Patrimônio 132, Protocolo 113, Veículos 113, Material 101, Licitações 84,
Contratos 63, Ouvidoria 32.

| Prefixo | Telas de Patrimonial no menu | Em outra área | Em disco | A alterar (prefixo inteiro) |
|---|---|---|---|---|
| `com` | 120 | 9 (Financeiro) | 372 | 204 |
| `pat` | 126 | 1 (Configuração) | 261 | 115 |
| `vei` | 113 | — | 172 | 155 |
| `lic` | 74 | 1 (RH, já no `map`) | 163 | 82 |
| `aco` / `ac` | 40 / 9 | — | 64 / 16 | 38 / 22 |
| `ouv` | 28 | — | 88 | 51 |
| `mat` | 95 | 26 (Configuração, Educação, Saúde) | 280 | via `map` |
| `pro` / `prot` | 69 / 16 | 39 / 7 | 337 / 48 | via `map` |
| `con` / `emp` / `cai` / `orc` / `cad` | 35 / 13 / 3 / 2 / 1 | Financeiro, Tributário… | — | via `map` |
| `func` / `processo` | 4 / 1 | — | — | via `map` |

**Escopo, o mesmo das três áreas anteriores:** Fase A = `ac`, `aco`, `ouv`, `lic`, `vei`, `pat`, `com` inteiros,
roteados por `location` (as poucas telas compartilhadas vão junto); Fase B = as telas de menu dos prefixos
compartilhados, pelo `map`. Ordem: do menor para o maior.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| `ac`+`aco`+`ouv` | 1.727 | 60 Rector + 8 à mão | 1.727/1.727 | 892, só artefatos conhecidos | 22.684 linhas, só artefatos conhecidos | **168/168** |
| `lic` | 2.586 (9 frentes) | 65 Rector | 2.586/2.586 | 26/26 | 588 linhas, 0 div. | **163/163** |
| `vei` | 2.062 | 134 Rector + 2 à mão | 2.062/2.062 | 43/43 | 935 linhas, 0 div. | **172/172** |
| `pat` | 2.165 | 98 Rector + 13 à mão | 2.165/2.165 | 24/24 | 519 linhas, 0 div. | **261/261** |
| `com` | 2.297 | 181 Rector + 11 à mão | 2.297/2.297 | 44/44 | 1.012 linhas, 0 div. | **372/372** |

**Lote 1 — `ac`+`aco`+`ouv`** (Contratos e Ouvidoria, 168 telas, roteadas no `location`). Rector só com regras já vetadas (37 guardas,
37 construtores, 32 `ereg`/`split` — os 143 `split` literais: 142 `"#"`, 1 `"/"` —, 23 `parse_str`+`extract`),
0 na 2ª passada. À mão:

- **`ouv1_cidadao.RPC.php`: 7 `break` fora de laço** (fatal de compilação no 8.5), todos no ramo de erro depois de
  `incluir()`/`alterar()` falhar — alcançáveis → **`exit;`** (o 5.6 morria ali). O `php -l` do 8.5 dirigiu um a um;
  os outros 6 `break` do arquivo estão dentro de `for` e ficaram.
- 4 guardas `pg_*` (`null`) pelo `guarda_ciclo.py`, em telas cujas SQL saem truncadas sem parâmetros (log do
  PostgreSQL: "erro de sintaxe no fim da entrada"); nenhuma variável guardada é comparada com `===`.
- `count(null)` → `count((array)…)` em `ouv1_prorrogacaoprazo003.php`.
- **`src/Patrimonial/Protocolo/Container.php:21`: `\ ECidade\V3\...`** (espaço depois da barra) — legal no 5.6,
  *parse error* no 8 (nome qualificado virou um token só). Espaço removido, mesmo significado. Achado pela
  bateria (`ouv4_solicitacaoprocessoeletronico.RPC.php`), **não** pelo `php -l` do universo — o arquivo não estava
  em universo nenhum: ver a **15ª lacuna** abaixo.

Classes: artefatos conhecidos (`lancamentoContabil`, `ordemPagamento`, `RequisicaoMaterial`, `empenho.php`
sem sessão) e um novo da mesma família, `solicitacaoCompra` (`.model.php` com argumento obrigatório no
construtor: o 5.6 segue com aviso, o 8.5 lança `ArgumentCountError` no harness). LSP entre arquivos
(`carrega_arquivo.php`, 215 com `extends`/`implements`): 204 OK nos dois, 11 falham igual nos dois.

Regressão: núcleo intocado; interseção com `con`/`prot`/`pro`/`cai` → as 244 telas desses prefixos no `map`:
**244/244**.

**Lote 2 — `lic`** (Licitações, 163 telas, roteadas no `location`; variantes `lic1_`…`lic4_`). Primeiro lote
enumerado com as **nove frentes**: universo 2.586 (o lote 1, com oito, tinha 1.727). Rector em 65 arquivos, só
regras já vetadas (33 `parse_str`+`extract`, 30 `ereg`/`split`, 26 guardas, 24 construtores, 3 `${$var}`), 0 na
2ª passada; `split` todos literais (`"#"` 92, `","` 13, `"_"` 6, `":"` 1). **Nenhuma correção à mão** e **bateria
perfeita na primeira rodada**, a primeira da área. LSP: 717 de 733 com `extends` carregam nos dois, 0 só no 5.6.

Regressão: interseção dos 65 alterados com o universo do que o 8.5 já serve **vazia**, núcleo intocado → sem
bateria, pela regra proporcional. Roteamento: `lic` no `location` e nas três cópias do critério
(`gera_map_faseb.py`, `dimensiona.py`, `redirecionamentos.py`); o `map` regenerado perdeu
`lic4_geracaoeditais001` (a tela compartilhada da Fase B do RH, agora coberta pelo `location`).

**Passo 8b sobre Patrimonial** (256 telas roteadas): `ouv1_tipoproc001/002` abriam a aba
`pro1_andpadrao001.php` no 5.6 (a 14ª lacuna, contêiner de Ouvidoria, aba de Protocolo). Nada a portar — a aba e
o universo dela já estavam portados (os 11 "alvos" eram o falso positivo do detector por bytes, 0 pelo contador
por *token*) —, aba idêntica nos dois, acrescentada a `faseb_map_abas.txt`. Os dois `lic1_*` que redirecionam
para `db_erros.php?db_erro=…` caem na página genérica de mensagem de erro: não é lacuna. Levantamento refeito:
nada indo ao 5.6.

**Lote 3 — `vei`** (Veículos, 172 telas, roteadas no `location`; `vei1_`…`vei4_`). Universo 2.062. Rector em 134
arquivos, só regras já vetadas (90 `parse_str`+`extract`, 43 guardas, 43 construtores, 40 `ereg`/`split` — 175
`split` com `"#"`, 3 com `","`), 0 na 2ª passada. À mão, 2 guardas `pg_*` (`null`) pelo `guarda_ciclo.py`, em
`vei2_relcentralveiculoso002` e `vei2_veiccentral002` (relatórios abertos sem os parâmetros do formulário;
`$result_central` não é comparado com `===`). Bateria 170/172 → **172/172**. LSP: 367 de 379 com `extends` carregam
nos dois, 0 só no 5.6. Regressão: interseção com o universo servido e com o do `lic` vazia, núcleo intocado → sem
bateria. Passo 8b depois de rotear (391 telas de Patrimonial no 8.5): nada indo ao 5.6.

**Lote 4 — `pat`** (Patrimônio, 261 telas, roteadas no `location`; variantes `pat1_`…`pat4_` e **`pat_`** sem dígito,
`pat_campanha_publicitaria.php`, que o `[0-9]*` cobre). Universo 2.165. Rector em 98 arquivos, só regras já vetadas
(71 `parse_str`+`extract`, 23 guardas, 23 construtores, 23 `ereg`/`split`, 2 `${$var}`). Os 8 `ereg_replace` com
classes de acentos LATIN-1 que o detector por bytes apontou em `pat4_imprimeetiquetas002.php` estão **comentados**
(`//`) — o Rector, corretamente, não os tocou.

À mão:

- **LSP:** `model/impressao.argoxOS214.php` e `…OS214_plus.php` declaravam `rodarComandos()` sem o parâmetro opcional
  da mãe `impressao::rodarComandos($sFinalizadorComando = '')` — não carregavam no 8.5. Parâmetro da mãe acrescentado;
  a primeira linha do corpo já **atribui** `$sFinalizadorComando` (`"\n"` / `chr(13)`), então o padrão não muda nada.
- **`break` fora de laço** em `pat1_bens005.php:228`, no ramo de erro de `incluir()`, alcançável → **`exit;`**.
- **NÚCLEO `db_mascara()`** (`dbforms/db_classesgenericas.php` + cópia do `modification/`): `pg_num_rows(false)` quando a
  SQL termina em `where db77_codestrut=` (código vazio; 20 "erro de sintaxe no fim da entrada" no log do PostgreSQL).
  `($result ? pg_num_rows($result) : null)`: no 5.6 `NULL > 0` é falso e a tela segue para "Não existe estrutural…" +
  `exit`, o mesmo caminho. Derrubava `pat1_clabens001/002/003` e `pat2_bensdepart001`.
- 6 guardas `pg_*` (`null`) pelo ciclo — uma delas em **`src/Patrimonial/Patrimonio/Bem/Model/Bem.php:116`**, alcançado
  só pela 9ª frente —, e 2 `count(null)` → `count((array)…)`.
- **6 telas truncadas SEM fatal no log** (`pat1_bens004/005`, `pat1_bensaltlote001/005`, `pat1_bensglobal001`,
  `pat2_classifbens001`): o **`0 != ""` na forma NEGADA** (6ª manifestação da RFC, a mesma do `cai`). Com `cfpatri`
  vazia o formulário faz `$t06_codcla = 0`, e `if (isset($t06_codcla) && $t06_codcla != "")` é falso no 5.6 (mostra
  "Estrutural não cadastrado no parâmetro.") e **verdadeiro no 8.5** (chama `db_mascara(0)`, que encerra a página).
  Guarda do catálogo, `$x != "" && $x !== 0 && $x !== 0.0`, nas 5 linhas (`forms/db_frmbens.php`,
  `db_frmbensaltlote.php`, `db_frm_bensglobal.php`, `pat2_classifbens001.php` ×2).

Bateria 245/261 → **261/261**. LSP: 371 de 387 com `extends` carregam nos dois (antes das impressoras: 2 só no 5.6).
Núcleo tocado → **bateria completa**: **5.350/5.374** (as 24 caracterizadas; uma das telas de laço eterno do `edu4` saiu
como TIMEOUT em vez de DIVERGE, mesma tela e mesma causa) e `map` **555/555**. Passo 8b depois de rotear (540 telas de
Patrimonial no 8.5): nada indo ao 5.6.

**Lote 5 — `com`** (Compras, 372 telas, roteadas no `location`; `com1_`…`com4_`). Universo 2.297. Rector em 181
arquivos, só regras já vetadas (107 `parse_str`+`extract`, 80 `ereg`/`split`, 44 guardas, 43 construtores, 8
`${$var}`), 0 na 2ª passada; `split` todos literais (`"#"`, `"_"`, `"-"`, `","`, `"XX"`, `"valor_"`…). Passo 6c (forma
negada) nas classes do universo: 2.132 pares, **0 divergentes**. LSP: 372 de 386 com `extends` carregam nos dois, 0 só
no 5.6. Bateria 363/372 → **372/372**. À mão:

- 7 guardas `pg_*` (`null`): 6 pelo ciclo (`db_frmpcfornecon`, `com2_procreservasaldo002`, `com2_solorc002`,
  `com3_pcforne006`, `com4_altdotacsol001`, `db_frmdespsol` — este compara com `== 0`, e `null == 0` é verdadeiro
  nos dois) e 1 à mão em `com1_pcfornemov001.php:87`, `pg_result(db_query(…), 0, 0)` com a consulta direto no
  argumento, que o ciclo não trata: a consulta vai para uma variável e o `pg_result` só roda se ela não for falsa
  (`null` no outro caso, o valor do 5.6).
- **Aritmética com `null`/`""`** em `forms/db_frmseldotac.php:53-54` (`$pc11_quant - $pc13_quantmax`, com a soma vazia
  do banco chegando como `""`): `TypeError` no 8.5. Medido no 5.6 em 6 casos: `(float)` acerta o valor mas troca o
  tipo onde o 5.6 dava inteiro; a forma do precedente do RH, `($x === null || $x === '' ? 0 : $x)` em cada operando,
  reproduz **valor e tipo** nos 6.
- **A forma negada, de novo, fora das classes:** `forms/db_frmsolicitemiframe.php`, `if (isset($pc11_vlrun) &&
  $pc11_vlrun != "")` com `0` — o 5.6 emite o JavaScript que lê o campo da tela, o 8.5 fixava `valor = '0'`. Guarda do
  catálogo. O `negada_alvos.py` só olha `classes/`; em formulário e tela ela só aparece pela bateria.
- `com1_solicitemiframe001` chama `isParaiba()`, que existe em `app/Helpers/Configuracao/VerificaEstado.php` mas **nada
  carrega** (nem o Composer nem a base legada): quebra **igual nos dois**, como `pes1_rhfuncao001` no RH. Pré-existente.

Regressão: interseção dos 187 alterados com o universo servido **vazia**, núcleo intocado → sem bateria. `com` no
`location` e nas três cópias do critério; o `map` não tinha entradas `com`. Passo 8b depois de rotear (713 telas de
Patrimonial no 8.5): nada indo ao 5.6.

#### 🏁 FASE A DE PATRIMONIAL CONCLUÍDA — `ac`, `aco`, `ouv`, `lic`, `vei`, `pat`, `com`

| | |
|---|---|
| Telas roteadas por `location` | **1.136** (`com` 372, `pat` 261, `vei` 172, `lic` 163, `ouv` 88, `aco` 64, `ac` 16) |
| Bateria | **1.136/1.136** |
| Arquivos alterados | ~600 (Rector 538 + à mão ~45) |
| Lacunas e categorias | **15ª lacuna** (classes com namespace, 9ª frente, corrigida pela cadeia); a **forma negada** do `0 == ""` (medida, 74 pontos de auditoria corrigidos pela cadeia, e 6 linhas em formulários) |

Falta a **Fase B**: as telas de menu de Patrimonial nos prefixos compartilhados (`mat`, `pro`, `con`, `prot`, `emp`, `func`,
`cai`, `orc`, `cad`, `processo`), pelo `map`.

#### ✅ A forma negada `$this->campo != ""` nas classes de dados — MEDIDA e CORRIGIDA

O `GuardaComparacaoLiteralRector` só cobre `==`. A forma `!=`, com propriedade inteira e **sem `trim()`**, aparece
**7.372 vezes em 1.865 classes** — 7.338 no bloco de **auditoria** do `alterar()`
(`if (isset(POST[x]) || $this->x != "") insert into db_acount …`) e **34 no SQL de negócio** (`SET` do `alterar()`,
`WHERE` do `excluir()`). Nenhuma bateria a veria: o nível 1 não executa `alterar()`, e o nível 3 descarta a auditoria.

**Ressalva, não medida ainda:** em quase todo fluxo o `alterar()` roda depois do `atualizacampos()`, que já com a
guarda do `==` troca o `0` de campo ausente do formulário pelo `null` do POST — e `null != ""` é falso **nos dois**.
A forma negada só dispara quando a propriedade ainda vale o inteiro `0` na comparação. Os 7.372 contam onde o padrão
existe, não onde muda resultado.

**MEDIDO e CORRIGIDO (27/10/2026).** Instrumento: `scratchpad/negada_alvos.py` (estático: classe, campo, método,
modo do `atualizacampos()` que vem antes no mesmo método, auditoria × negócio) e `scratchpad/negada.php` (reproduz o
estado com POST vazio, campo ausente, e imprime `valor != ""`), nos dois runtimes. Passo 6c da skill.

| | Pares | |
|---|---|---|
| medidos | 7.367 | |
| mesmo resultado nos dois | 5.274 | |
| valor diferente (5.6 `NULL`, 8.5 `0`): falta a guarda do `==` | 2.004 | **0 nas classes servidas**; são classes de áreas ainda não migradas, e a regra própria corrige quando a área vier |
| **mesmo valor `0`, só a forma negada muda** | 89 | **74 em 28 classes servidas, todos de auditoria**; 15 em classes não servidas |
| dos 89, no SQL de negócio | 1 | `db_cgs_und_classe::alterarExt` (Saúde), não servida |

Das 34 ocorrências de negócio que a contagem estática apontava, 33 não divergem: o `atualizacampos()` neutraliza.
**Impacto real, então:** nenhum valor de negócio diferente. Só a trilha de auditoria (`db_acount`) das 28 classes,
que no 8.5 registrava uma alteração para 0 que o 5.6 não registrava.

**Decisão do usuário: corrigir.** Guarda `($this->x != "" && $this->x !== 0 && $this->x !== 0.0)` nos 74 pontos, só
dentro do método medido, pela cadeia: **25 classes na branch 1** (`d2674aa3c`), as 2 portadas no RH
(`db_agrupamentorubrica`, `db_rhfolhapagamento`) na branch 3 (`4fdaecd2a`) e `db_veicmanut` (lote 3) na branch 4.
Verificado: lint nos dois runtimes; remanescentes 0 (o `negada_alvos.py` passou a ignorar a ocorrência já guardada,
senão casaria com a própria guarda, como o detector do `==`); classes e escrita idênticas.
Bateria completa sobre o código unido (branch 4): **5.611/5.635** (as 24 caracterizadas, conferidas nome a nome)
e `map` **555/555**.

**Limite do instrumento, registrado:** o `negada.php` mede o estado, não executa o código. Depois da correção ele
continua acusando os mesmos pares; quem prova a correção é o detector de remanescentes. Na primeira rodada, os dois
runtimes, rodando em paralelo, escreveram o mesmo `/tmp/_neg1.tsv` (o `/tmp` é **compartilhado**) e metade das
linhas sumiu de um lado. Corrigido com um arquivo por runtime.

### ⚠ 15ª LACUNA (27/10/2026, achada no lote 1): classes COM NAMESPACE, fora de todos os universos

**Como apareceu:** `ouv4_solicitacaoprocessoeletronico.RPC.php` dava `ParseError` no 8.5 dentro de
`src/Patrimonial/Protocolo/Container.php`, um arquivo que **nenhum universo listava**, nem o do lote nem o
das áreas já entregues. As oito frentes resolvem `include`, `new cl_*`, `getDao()` e as classes de
`model/`/`std/` por nome curto. Não resolvem nomes com namespace (`use ECidade\…;`, `new \ECidade\…`),
carregados pelo autoloader de `bootstrap.php` (`ECidade\` → `src/`, `ECidade\Api\` → `api/`) e pelo do
Composer (`App\` → `app/`). Também não resolvem os serviços que o `bootstrap.php` registra por **chave de
texto** (`Registry::get('app.container')->get('patrimonial.container')`). O RPC chegava ao `Container` por
esse segundo caminho.

**Instrumento:** `scratchpad/ns_fecho.py`, que também roda sozinho, é chamado pelo `enumera.py` como a
**9ª frente**, dentro de `diretas()`. Assim o fecho segue de `src/` até `classes/`. Junto com ele vieram:
`SEM_NS=1` para medir sem a frente, e `TELAS=@arquivo` para listas grandes.

**Medido em duas etapas.** A primeira medição parou nos arquivos com namespace e subestimou:

| | |
|---|---|
| Arquivos de `src/`/`app/`/`api/` alcançados pelas áreas e nunca verificados | **2.304** |
| Destes, que **não compilam** no 8.5 | 3: `Horas/Falta.php` (RH, ternário aninhado), `MatrizSaldoContabil/Repository/Lancamento.php` (`$valor{1}`), `Protocolo/Container.php` (espaço depois da barra do nome qualificado) |
| Que **não carregam** no 8.5 (LSP, mãe em outro arquivo) | 18: 12 `getDados()` de relatórios DCASP/RGF/RREO, `Loteamento::get`, `ArretipoRepository::find`, `ReciboCollection::add`, `AlteracaoDadosServidorFormatter::formatar` |
| **Dado errado em silêncio** | `src/Tributario/Cadastro/Iptu/EmissaoTXT.php:768`: `split('\.', …)`. No 8.5 o polyfill do `vendor/` faz `explode('\.')` e **não separa** (`'01.02.003'` vira um elemento só). → `explode('.')`, idêntico ao `split` do 5.6 em 7 casos |
| Falso alarme conferido | `Importar::Importar()` em classe com namespace **não** é construtor nem no 5.6 (regra do PHP 5.3.3, medida). Renomear mudaria o 5.6; o detector agora ignora arquivo com `namespace` |

A segunda medição, com o fecho seguindo de `src/` até `classes/`, foi feita sobre os **5.654 arquivos que o
8.5 serve hoje** (prefixos do `location` + `map`): o universo foi de 10.380 para **12.343**, com **73
arquivos novos a portar**. São 71 classes de dados com **354 guardas `0 == ""` faltando** e 15 construtores
PHP 4, mais `pro4_capaprocesso.php` (`parse_str`). A mesma medição achou **3 classes de Água** que já estavam
no universo servido e nunca tinham sido portadas (`db_aguadescarrecad`, `db_aguadescarrehist`,
`db_declaracaoquitacaocarneagua`). As demais pendências da linha de base são as já registradas: os 9 do
`pes2` e o `mer1_mer_desper_und003`, que não compilam no 5.6, e o `tra`, órfão.

**Onde foi corrigida:** na branch da área mais antiga que alcança os arquivos, **`1tributario-migrado`**, que
já alcança todos (`arr`, `cad`, `cai`, `dvr`, `jur`, o fecho da 13ª lacuna do Tributário). Depois desceu
pela cadeia por merge, sem conflito.

| Commit (branch 1) | Conteúdo | Verificação |
|---|---|---|
| `4669105ab` | o `split`, os 3 que não compilavam, as 18 LSP | lint nos dois; carga dos 2.304: **2.291 OK nos dois** (os 13 restantes falham igual, sem sessão no harness); Tributário 1.807/1.813, `map` 358/358 |
| `318904a08` | os 76 arquivos de `classes/` (Rector, só regras vetadas) | remanescentes 0; funções 0 ausentes; lint 76/76; classes 75/75; escrita **1.943 linhas idênticas** — **antes do porte, 338 campos em 74 classes divergiam do 5.6** |

Baterias depois de cada merge: Educação 1.514/1.531 + 1 timeout e `map` 381/381; RH 1.527/1.528 e `map`
555/555. Todas na linha de base.

**Bateria completa sobre o código unido** (branch 4, depois dos três merges): todos os prefixos do `location`
das quatro áreas e o `map` inteiro. **5.015/5.039 idênticas** (22 divergentes + 2 timeouts) e `map` **555/555**.
As 24 são exatamente as já caracterizadas: 6 do Tributário, 17 da Educação e 1 de RH, cada uma no registro da
sua área. As 168 telas do lote 1 de Patrimonial: todas idênticas.

**Lição, a 15ª da mesma família:** a verificação partia da lista que a enumeração produziu, e a enumeração não
conhecia um terceiro mecanismo de carga de classe. Quem achou foi a bateria: uma tela que quebrou.
