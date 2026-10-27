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
