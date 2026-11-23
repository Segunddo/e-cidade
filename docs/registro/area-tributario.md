# Área Tributário: estratégia, receita, núcleo, pilotos e todos os módulos

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

## ESTRATÉGIA ADOTADA: migrar a ÁREA Tributário, módulo a módulo

Decisão tomada após o piloto Cemitério: em vez de módulos isolados, focar numa **área**
inteira — mesma forma do TCC de Educação (trabalho relacionado), o que torna os dois
diretamente comparáveis.

### Por que Tributário

A área é definida no banco por `configuracoes.atendcadarea` + `atendcadareamod`:

| Área | Módulos |
|---|---|
| **DB:TRIBUTÁRIO** | **16** ← esta |
| DB:PATRIMONIAL | 8 |
| DB:SAÚDE | 8 |
| DB:FINANCEIRO | 6 |
| DB:EDUCAÇÃO | 5 ← o TCC de referência |

É a maior área do sistema, **3× a Educação**, e o Cemitério (já portado) pertence a ela.
Seus 16 módulos somam **1.024 telas** no menu.

### A distinção central: PORTAR ≠ ROTEAR

**O menu lista apenas ~1/3 dos arquivos de um módulo.** Medido:

| prefixo | arquivos | no menu | fora do menu |
|---|---|---|---|
| `cem` | 116 | 40 (34%) | **76** |
| `iss` | 400 | 165 (41%) | **235** |
| `fis` | 353 | 92 (26%) | **261** |
| `cad` | 523 | 162 (31%) | **361** |

Os outros dois terços são popups abertos por `window.open`, endpoints `.RPC.php` chamados
por AJAX e subtelas. **No Cemitério isso passou despercebido por sorte**: enumerei por
prefixo, não pelo menu. Com a lista do menu, 76 arquivos teriam ficado sem correção.

Regra que decorre disso:
- **Portar → sempre por prefixo** (`re.IGNORECASE`), senão fica 2/3 do módulo para trás.
- **Rotear → é onde a fronteira da área importa.**

### 3ª LACUNA: arquivos abertos por JavaScript não entram no fecho de dependências

Descoberta no ITBI, reportada pelo usuário (o campo "Forma de Pagamento" não aceitava
digitação). O fecho transitivo só segue `include`/`require`. Mas as telas abrem *lookups* e
subjanelas por **JavaScript**, que é uma requisição HTTP nova, invisível ao analisador:

```javascript
js_OpenJanelaIframe('','db_iframe_...','func_itbiformapagamento.php?funcao_js=...');
```

No ITBI havia **13 arquivos** nessa condição (9 deles quebrados em PHP 8, todos com
`parse_str` de 1 argumento): `func_itbi.php`, `func_itbiformapagamento.php`,
`func_itbiliberado.php`, `func_itbitransacao.php`, `func_matricitbi.php`, `func_tabdesc.php`,
`func_taxasitbi.php`, `func_taxaslancadas.php` e `cad3_conscadastro_002.php`.

**Passo a acrescentar à receita de enumeração** — varrer os scripts do módulo atrás de
nomes de arquivo `.php` citados em strings (o JS os referencia como texto):

```python
alvo = re.compile(rb"([A-Za-z0-9_]+\.(?:RPC\.)?php)")
# para cada script do modulo, coletar os nomes citados que existam em disco
# e NAO casem com o prefixo do modulo -> sao candidatos abertos por JS
```

Detalhe de roteamento: esses `func_*` **continuam servidos pelo 5.6** (o prefixo `func_` é
compartilhado por todos os módulos e não pode ir para o 8.5 isoladamente). Como as correções
são compatíveis com os dois runtimes, isso não é problema — mas eles **precisam ser portados
mesmo assim**, senão quebram quando o módulo que os usa for roteado.

**Lição, terceira da mesma família:** as três lacunas do porte — maiúsculas, menu × prefixo,
e agora JavaScript — têm a mesma raiz. Toda verificação partia da lista que a própria
enumeração gerou, e nenhuma delas podia encontrar o que a enumeração não incluiu. As três
foram descobertas pelo usuário navegando o sistema, não pelas baterias automatizadas.

### Prefixos exclusivos vs. compartilhados

Consulta que revela a colisão:

```sql
SELECT lower(substring(di.funcao from '^[A-Za-z]+')) AS prefixo,
       count(DISTINCT a.at25_descr) AS n_areas
FROM configuracoes.atendcadareamod am
JOIN configuracoes.atendcadarea a ON a.at26_sequencial = am.at26_codarea
JOIN configuracoes.db_modulos m ON m.id_item = am.at26_id_item
JOIN configuracoes.db_menu dm ON dm.modulo = m.id_item
JOIN configuracoes.db_itensmenu di ON di.id_item = dm.id_item_filho
WHERE di.funcao ~ '^[A-Za-z]+[0-9]*_.*\.php$'
GROUP BY 1 HAVING count(DISTINCT a.at25_descr) > 1;
```

**Prefixos de arquivo NÃO respeitam a fronteira das áreas** — `con` aparece em 6 áreas,
`pro` em 5, `cai` em 4, `cad` em 3. "Área" é agrupamento de *menu*, não de *código*.

**EXCLUSIVOS de Tributário — 1.800 arquivos, roteamento trivial por prefixo:**

```
iss 400   fis 353   agu 221   arr 162   div 148   jur 145
cem 116✓  itb 110   mar  35   tri  33   dvr  33   inf  30   not 14
```

**COMPARTILHADOS — 3.244 arquivos, exigem lista explícita:**

```
con 1559   cai 740   cad 523   pro 337   pre 54   amb 31
```

### Plano em fases

**Fase A — os 12 prefixos exclusivos restantes (1.684 arquivos).** Cobre 12 dos 16 módulos:
ISSQN, Fiscal, Água, Arrecadação, Dívida Ativa, Jurídico, ITBI, Marcas e Sinais, Diversos,
Inflat, Notificações — mais o Cemitério pronto. Roteamento em uma linha:

```nginx
location ~* ^(?:/w/[0-9]+)?/(?:cem|iss|fis|agu|arr|div|jur|itb|mar|tri|dvr|inf|not)[0-9]?_
```

**Fase B — os 6 prefixos compartilhados**, só se houver tempo. Aí entra um `map` do nginx
gerado a partir do banco, porque `cad` e `con` não podem ir inteiros para o 8.5 sem arrastar
Financeiro e Patrimonial junto.

**Progresso da Fase A: CONCLUÍDA.** `cem` ✅ · `itb`/`itbi` ✅ · `agu` ✅ · `jur` ✅ · `div` ✅ · `mar` ✅ · `not` ✅ · `fis` ✅ · `iss` ✅ · `dvr` ✅ · `arr` ✅ · `tri` ✅ · `inf` ✅ — 13 de 13 prefixos exclusivos.

### ⚠ ORDEM REVISTA: `jur` antes de `div`, e `arr` por último

A ordem anterior (`arr` → `div` → `jur`) foi herdada da tabela de resíduo original, que era
**anterior aos três portes** e usava um fecho de dependências só de `include`. Recomputada com
a enumeração completa da receita (includes + autoload + citados em strings) e descontando o que
os portes já pagaram, ela se inverte. Analisador: `scratchpad/residuo.py`.

| | `jur` Jurídico | `div` Dívida Ativa | `arr` Arrecadação |
|---|---|---|---|
| Telas (prefixo, IGNORECASE) | 145 | 148 | 162 |
| Itens de menu ligados | 57 de 64 (89%) | 63 de 64 (98%) | 85 de 88 (97%) |
| Dependências no fecho | 170 | 244 | 509 |
| Já pagas (núcleo + portados) | 42 | 53 | 48 |
| Exclusivas do módulo | 35 | 42 | 37 |
| **Resíduo** | **93** | **149** | **424** |
| Resíduo que precisa de alteração | 76 | 124 | 301 |
| **Arquivos a alterar (total)** | **137** | **198** | **343** |

Calibração contra o que já foi feito — arquivos efetivamente alterados por lote: `itb` **105**,
`cem` **124**, `agu` **171**. Ou seja: `jur` (137) cai **dentro da faixa já provada**, `div`
(198) fica acima do maior lote já executado, e `arr` (343) é **o dobro** dele.

O que cada um arrasta de módulos não portados (só os arquivos que precisam de alteração):

```
jur   func:69   cai:52   div:38   arr:36   cad:28
div   func:112  cai:86   iss:63   arr:61   cad:59
arr   func:285  cai:252  con:212  emp:208  pes:203
```

**`arr` é o único que rompe a fronteira da área.** Ele arrasta 212 arquivos de `con`
(Contabilidade, 1.559 scripts) e 203 de `pes` (RH) — módulos de *outras* áreas. `jur` e `div`
arrastam sobretudo `func` (compartilhado por todos, inevitável) e módulos da própria área.

**Efeito de ordem:** a soma é invariante — 559 arquivos para os três, em qualquer ordem. Logo a
ordem **não muda o custo total**, muda o tamanho do primeiro lote e portanto a velocidade do
ciclo de verificação:

```
jur -> div -> arr     137 + 157 + 265
arr -> div -> jur     343 + 132 +  84
```

**Ordem adotada:** `jur` → `div` → `mar`/`tri`/`dvr`/`inf`/`not` → `arr` → `fis` (353) →
`iss` (400). O `arr` desce para perto do fim, junto dos grandes.

**RESSALVA IMPORTANTE — resíduo não é bloqueador.** Os três módulos já portados deixaram
resíduo não portado (`cem` 20, `itb` 24, `agu` 29 arquivos que precisariam de alteração) e
mesmo assim verificam byte-a-byte: 114/116, 116/120 e 222/224. Esses arquivos não estão nos
caminhos exercitados. Resíduo mede **contaminação de escopo** — quanto de outros módulos o
porte encosta —, não risco de quebra.

Os números desta tabela **não são comparáveis** com a tabela de resíduo histórica (onde `tra`
tinha 0 e `cem` tinha 4): aquela usava fecho só de `include`, que não enxerga autoload nem os
arquivos abertos por JavaScript.

### Receita por módulo (validada em `cem`, `itb` e `agu`)

Cada prefixo é um lote independente, com commit próprio e revertível:

```
1. enumerar, em SETE frentes       -> verificar: cada frente fecha (ver abaixo)
2. varrer as categorias conhecidas -> verificar: inventário fechado
3. classificar cada ocorrência     -> verificar: nenhum falso-positivo de JavaScript
4. aplicar (Rector, ver abaixo)    -> verificar: zero remanescentes, REPETINDO ate dar 0
4b. portao de FUNCOES contra o 5.6 -> verificar: nenhuma funcao emitida que falte no 5.6
5. php -l nos DOIS runtimes        -> verificar: 100% OK em 5.6 e 8.5 (com </dev/null!)
6. instanciar as classes           -> verificar: estado idêntico entre runtimes
7. comparar as telas com sessão    -> verificar: byte-a-byte, normalizando ids aleatórios
8. acrescentar o prefixo ao nginx  -> verificar: X-Ecidade-Runtime = PHP-8.5
9. commit
```

**O passo 1 é o que mais falhou.** Sete lacunas distintas já foram encontradas ali, todas
com a mesma assinatura: a verificação partia da lista que a própria enumeração gerou, então
não podia achar o que a enumeração deixou de fora. As sete frentes:

| Frente | Como | Lacuna que fecha |
|---|---|---|
| prefixo | `re.IGNORECASE`, e aceitar sufixos de letra (`itbi`, `agua`) | maiúsculas; sub-prefixos |
| fecho de includes | `include(modification(...))` transitivo | — |
| citados em strings | nomes `*.php` dentro do código (o JS os abre) | 3ª: `window.open` |
| autoload | classes `cl_*` instanciadas **e `db_utils::getDao('x')`**, resolvidas em `classes/` | 4ª: `spl_autoload_register`; 7ª: `getDao()` |
| bibliotecas vendorizadas | `dbagata/`, incluindo `*.class` e `*.inc` | 5ª: `dbagata/` |
| **pasta inteira da lib** | se um arquivo de uma pasta-biblioteca entrou, **varrer a pasta toda** | 6ª: `fpdf151/` (2 de 194 portados) |

Conferir o total contra `ls | grep -iE '^<pref>[0-9]*_'` **antes** de dar o módulo por pronto.

Estimativa da área inteira: **1.804 arquivos no universo, 775 precisando de alteração (43%)**
— 1.823 `split(`, 276 `parse_str` de 1 argumento, 431 arquivos com construtor PHP 4 e 3.040
comparações `0 == ""`. **Nenhuma categoria nova** além das já catalogadas.

### Estado: MÓDULO `jur` (Jurídico) PORTADO ✅ — 4º da área Tributário

**145 telas**, enumeradas por `^jur[0-9]*_` com `re.IGNORECASE`. O módulo tem **seis** variantes
de prefixo: `jur1_`…`jur4_`, mais `jur01_` (4 arquivos) e `jur_` (1). Universo total com as seis
frentes de enumeração: **315 arquivos**, dos quais 42 já pagos pelo núcleo e pelos portes
anteriores. **137 arquivos alterados.**

| Correção | Qtd |
|---|---|
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 517 |
| `split(` → `explode(` (padrão literal) | 239 |
| `parse_str()` com 2º argumento | 62 |
| construtor PHP4 → `__construct` | 60 |
| `ereg*(` → `preg_*(` | 31 |
| `each(` → `foreach` | 10 |
| `sizeof(null)` → `sizeof((array)…)` | 4 |
| guardas `pg_*` contra resultado falso | 3 |
| `split(` com padrão **regex** → `preg_split` / `explode("\|")` | 3 |
| `break` fora de laço removido | 1 |

Verificações: `php -l` **nos dois runtimes** em 137/137 alterados e em 315/315 do universo;
as **84 classes instanciam com estado idêntico**; **144 de 145 telas byte-a-byte idênticas**.

**Zero telas quebrando no 8.5** — o melhor resultado até aqui. A única divergência,
`jur_enviarremessatj.php`, **quebra no 5.6 (500) e funciona no 8.5 (200)**: o código pede
`db_app::load(... "pades.js")` e esse arquivo **não existe no repositório** (só
`scripts/pades-signer-sdk.min.js`). Defeito pré-existente da referência, mesma família de
`cem1_itenserv002` e das 4 telas do ITBI.

Roteamento: `jur` acrescentado ao nginx, e **`[0-9]?` virou `[0-9]*`** — com um dígito só,
as 4 telas `jur01_*` ficariam silenciosamente no 5.6. Mesma família da armadilha de maiúsculas.

### CATEGORIA NOVA (jur): `split()` com padrão REGEX, não literal

Nos três módulos anteriores **todos** os `split()` usavam separador literal (`"#"`, `","`), e a
conversão para `explode()` era mecânica. O `jur` tem três que **não** são:

```php
split(" +", $regs[2])    // POSIX: "um ou mais espacos"  -> preg_split("/ +/", ...)
split("\|", $funcao_js)  // POSIX: pipe escapado = literal -> explode("|", ...)
```

Comprovado no 5.6: `split(" +", "um   dois")` devolve `["um","dois"]`, e
`explode(" +", "um   dois")` devolve `["um   dois"]` — **a string inteira, sem separar**.
Trocar por `explode` aqui produziria dado errado em silêncio, sem erro nenhum.

**Regra:** antes de converter em massa, classificar o primeiro argumento. Se contiver
metacaractere de regex (`+ * ? [ ] ( ) | . ^ $ \`), vai para `preg_split`, não para `explode`.

### CATEGORIA NOVA (jur): `break` fora de laço ou `switch`

Era *warning* no PHP 5.6 e é **erro fatal de COMPILAÇÃO desde o PHP 7.0**.

```
jur1_emiteinicial002.php:114   Fatal error: 'break' not in the 'loop' or 'switch' context
```

Não aparece em varredura textual — só o `php -l` sob 8.5 a revela, como as categorias LSP e
`=& new`. Ali o `break` era **inalcançável** (a linha anterior chama `db_redireciona()`, que
termina em `exit` — `libs/db_stdlib.php:1545`), então removê-lo preserva a semântica exata.

### CATEGORIA NOVA (jur): `sizeof(null)`

No 5.6 era warning e devolvia 0; no PHP 8 é `TypeError: must be of type Countable|array`.
Ocorre quando o array só é atribuído dentro de um `if` que não entrou:

```php
if (isset($dadosini) && $dadosini != "") { $matriz = explode("xx", $dadosini); }
for ($q = 0; $q < sizeof($matriz); $q++) {      // $matriz indefinida -> null
```

Correção: `sizeof((array)$matriz)`. Reproduz o 5.6 nos três casos — `(array)null` = `[]` (0),
`(array)"x"` = `["x"]` (1, que era o que `sizeof` de escalar devolvia), e array continua igual.

### LACUNA DE DETECÇÃO (jur): `parse_str` com chamada aninhada

Duas telas continuaram fatais depois do porte:

```php
parse_str(base64_decode($HTTP_SERVER_VARS['QUERY_STRING']));
```

O regex de detecção era `parse_str\s*\(\s*[^,()]+\)` — o `[^,()]` **não casa com parênteses
internos**, então a chamada aninhada nunca foi detectada, os arquivos não entraram na lista de
alvos, e a transformação nem rodou neles.

**É a mesma falha de método das seis lacunas de enumeração:** agir sobre a lista que a própria
detecção produziu. A detecção correta conta vírgulas **no nível superior**, percorrendo os
parênteses com contador de profundidade.

### ARMADILHA DE FERRAMENTAL: `serialize()` de objeto interno é fatal no PHP 8

O harness que compara o estado das classes usava `md5(serialize($props))`. Três classes do `jur`
guardam um `DOMElement`, e **serializá-lo é fatal no PHP 8** (o 5.6 permitia):

```
Exception: Serialization of 'DOMElement' is not allowed
```

O sintoma foi um falso positivo: três classes "com erro" que instanciam perfeitamente quando
testadas isoladamente. **Era o instrumento que quebrava, não o código medido.** A assinatura
passou a descrever objetos pelo nome da classe em vez de serializá-los
(`scratchpad/instancia_classes.php`).

### Estado: MÓDULO `div` (Dívida Ativa) PORTADO ✅ — 5º da área Tributário

**148 telas** (`^div[0-9]*_`, sem variante de letra). Universo pelas seis frentes: **392
arquivos**, 90 já pagos. **158 alterados.**

| Correção | Qtd |
|---|---|
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 752 + 11 no núcleo |
| `split(` → `explode(` (todos literais) | 381 |
| construtor PHP4 → `__construct` | 80 |
| `parse_str()` com 2º argumento | 62 |
| guardas `pg_*` contra resultado falso | 9 |
| offsets `{}` → `[]` | 2 |
| cast `(int)` em aritmética com string | 1 |
| `date()` com timestamp string → `(int)` | 1 |

**148 de 148 telas byte-a-byte idênticas — o primeiro módulo sem nenhuma divergência.**
As 84+150 classes instanciam com estado idêntico; `php -l` limpo nos dois runtimes em
158/158 alterados e 391/391 do universo.

### ⚠ ACHADO GRAVE: o núcleo `db_cgm_classe.php` estava sem as guardas `0 == ""`

Descoberto pela verificação de remanescentes do `div`: **12 arquivos já tocados por commits
`Porta ...` ainda tinham o idioma perigoso sem guarda — 52 ocorrências.**

| Arquivo | Ocorrências |
|---|---|
| `classes/db_acidentes_classe.php` e mais 10 do `tra` | 42 |
| **`classes/db_cgm_classe.php` — NÚCLEO** | **10** |

Causa: o `tra` e o núcleo foram portados **antes** de a categoria `0 == ""` ser descoberta
(ela apareceu no Cemitério). O `CLAUDE.md` registra `db_cgm_classe.php` apenas sob
"construtor PHP4 → `__construct`" — as comparações nunca foram tratadas.

Gravidade: `db_cgm_classe.php` é o registro de cidadãos, **puxado por qualquer módulo com
pessoas**. O idioma afetado é exatamente o que quebrou o formulário do Cemitério:

```php
$this->z01_numcgm = ($this->z01_numcgm == "" ? @$GLOBALS["HTTP_POST_VARS"]["z01_numcgm"] : ...);
```

**Corrigido** (11 comparações). As 42 do `tra` ficam registradas e **não corrigidas**: o
módulo é órfão no menu, nenhuma tela leva até ele.

**Por que nenhuma bateria pegou isso:** o comparador faz só `GET`, e este idioma só dispara
no `POST`. É o mesmo limite que a dúvida sobre a inclusão de advogados expôs.

### CATEGORIA NOVA (div): `date()` com timestamp em string

```
                     date("Y-m-d", "2024-01-01")
PHP 5.6:             "1969-12-31"   (coage para int)
PHP 8.5:             TypeError: Argument #2 ($timestamp) must be of type ?int
```

Em `libs/db_stdlib.php:1503` (`db_vencimento()`, núcleo). Correção: `date("Y-m-d", (int)$dt)`,
que reproduz o 5.6 **exatamente** — inclusive o resultado sem sentido `1969-12-31`, que é
comportamento pré-existente e não cabe à migração corrigir.

### `(int)` vs `(float)` em aritmética com string

O catálogo registra `(float)` como correção da aritmética com string, escolhida num contexto
monetário. Em `classes/db_divida_classe.php:2373` o valor é um **exercício** (ano) vindo de
`explode("-", ...)`, e ali `(int)` é estritamente mais fiel: o 5.6 devolve `int` para
`"2024" - 1`, e `(float)` preservaria o valor mas mudaria o tipo.

**Regra:** casar o cast com o tipo que o 5.6 produzia naquele ponto, não aplicar `(float)` por
hábito.

### LACUNA DE DETECÇÃO (div): offset `{}` sobre PROPRIEDADE

Meu regex de offset cobria `$v{...}` e `$v[...]{...}`, mas **não `$v->prop{...}`**:

```php
if ($aDebitos[$i]->origem{0} == 'M')      // model/cda.model.php:1226
```

Escapou da varredura e só o `php -l` do 8.5 pegou. O regex do `enumera.py` foi corrigido para
cobrir as quatro formas.

### FERRAMENTAL versionado (`scratchpad/`)

Depois de reescrever as mesmas rotinas em cada módulo — e de perder duas vezes o comparador —
os quatro instrumentos passaram a ser versionados:

| Arquivo | Passos da receita |
|---|---|
| `enumera.py` | 1–3: universo pelas seis frentes + inventário + lista de alvos |
| ~~`porta.py`~~ → `rector-curado.php` + `rector-rules/` | 4: transformações mecânicas. O `porta.py` fica como referência e para comparar resultados; a partir do `iss` quem aplica é o Rector. |
| `instancia_classes.php` | 6: estado das classes nos dois runtimes |
| `cmp.py` | 7: comparação das telas |

`porta.py` **usa a mesma detecção de `enumera.py`** — em especial a de `parse_str`, que conta
vírgulas no nível superior. Foi a divergência entre as duas que deixou duas telas do `jur`
fatais depois do porte. E ele **aborta** diante de caso que exige decisão humana (separador de
`split()` com metacaractere, arquivo com mais de uma classe), em vez de transformar errado.

### Estado: MÓDULO `mar` (Marcas e Sinais) PORTADO ✅ — 6º da área Tributário

**35 telas** (`^mar[0-9]*_`, variantes `mar1_`…`mar4_`, sem sufixo de letra). Universo pelas
seis frentes: **77 arquivos**, 24 já pagos. **19 alterados.**

Módulo de registro de marcas de gado. **17 de 17 itens de menu ligados** — módulo próprio e
inteiramente demonstrável:

```
Marcas e Sinais > Cadastros     > Localidades (Inclusão/Alteração/Exclusão)
                > Procedimentos > Cadastro de Marcas · Cancelamento · Transferência
                > Consultas     > Consulta Marcas · Cancelamentos · Transferências
                > Relatórios    > Marcas por Proprietário · Histórico de Cancelamentos
```

| Correção | Qtd |
|---|---|
| `$this->X == <literal>` → forma que preserva a semântica do 5.6 | 27 |
| `split(` → `explode(` (todos com separador literal `"#"`) | 20 |
| `parse_str()` com 2º argumento | 14 |
| construtor PHP4 → `__construct` | 5 |

Nenhuma categoria nova. Zero `each(`, `ereg*`, offsets `{}`, `=& new`, cast `(real)`.

Verificações — **primeira vez com a receita completa, incluindo o passo 6b**:

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 35 = 35 ✅ |
| 3. classificação dos `split` | 20 literais, 0 regex, 0 dentro de `<script>` |
| 5. `php -l` nos dois runtimes | 19/19 alterados e 76/76 do universo, 0 erros |
| 6. instanciação das classes | 14/14, estado idêntico |
| **6b. caminho de escrita** | **545 linhas, byte-a-byte idênticas** |
| 7. bateria de telas | **35/35 idênticas, 0 divergentes**, 0 fatais no log |

**Segundo módulo sem nenhuma divergência**, depois do `div`.

#### Armadilha de verificação que reapareceu (terceira vez)

O harness do passo 6b produziu 858 linhas e meu `diff` disse "0 divergentes". Antes de aceitar,
conferi se **havia saída** — havia. Mas um segundo teste (`grep $'\t'`) contou **zero linhas
bem formadas**, o que sugeria lixo. Era o `grep` que falhava por aspas no shell: medindo em
Python, são **545 linhas bem formadas cobrindo as 14 classes, byte-a-byte idênticas**.

Lição: **o instrumento de conferência também precisa ser conferido.** Duas verificações
discordando é sinal de que uma delas está quebrada — não de que o dado está ruim.

### Estado: MÓDULO `not` (Notificações) PORTADO ✅ — 7º da área Tributário

**14 telas** (`^not[0-9]*_`, variantes `not1_`/`not2_`/`not4_`). Universo pelas seis frentes:
**92 arquivos**, 47 já pagos. **17 alterados.**

Módulo próprio, **7 de 7 itens de menu ligados**:

```
Notificações > Procedimentos > Notificações por Edital · Parâmetros · Documento da Lista
             > Relatórios    > Emissão de Notificações (TXT Correios / Layout / Geral)
                             > Situação da Notificação
```

| Correção | Qtd |
|---|---|
| `$this->X == <literal>` → forma que preserva a semântica do 5.6 | 60 |
| `split(` → `explode(` (43 com `"#"`, 1 com `" "`) | 44 |
| construtor PHP4 → `__construct` | 11 |
| `parse_str()` com 2º argumento | 6 |

Nenhuma categoria nova.

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 14 = 14 ✅ |
| 3. classificação dos `split` | 44 literais, 0 regex, 0 em `<script>` |
| 5. `php -l` nos dois runtimes | 17/17 alterados e 91/91 do universo, 0 erros |
| 6. instanciação das classes | 40/40, estado idêntico |
| 6b. caminho de escrita | 1.111 linhas, byte-a-byte idênticas |
| 7. bateria de telas | **14/14 idênticas, 0 divergentes**, 0 fatais |

**Terceiro módulo sem nenhuma divergência**, depois de `div` e `mar`.

Dois detalhes verificados em vez de deduzidos, ambos na categoria onde o erro é silencioso:

- **`split(" ", ...)` com espaço único é literal**, não regex — confirmado no próprio 5.6:
  `split(" ","um  dois")` e `explode(" ","um  dois")` devolvem o mesmo array, inclusive o
  elemento vazio do espaço duplo. (Diferente de `split(" +", ...)` do `jur`, que é regex.)
- **O harness de escrita cobriu 39 das 40 classes.** A ausente,
  `classes/db_assinatura_classe.php`, tem **zero propriedades declaradas e nenhum
  `atualizacampos()`** — não é classe de dados, não há caminho de escrita a exercitar.

### Estado: MÓDULO `fis` (Fiscal) PORTADO ✅ — 8º da área Tributário

**353 telas** (`^fis[0-9]*_`, variantes `fis1_`…`fis4_`, sem sufixo de letra e sem maiúsculas).
Universo pelas seis frentes: **682** arquivos — e **699 depois de fechar a 7ª lacuna**, abaixo.
**384 arquivos alterados**, o maior lote do projeto (o anterior era `agu`, 171).

| Correção | Qtd |
|---|---|
| `$this->X == <literal>` → forma que preserva a semântica do 5.6 | 730 |
| `split(` → `explode(` (todos literais: 519 `#`, 16 `-`, 4 `HHH`, 3 `/`, 2 `_sep_`, 2 `,`, 2 `\n`, 1 ` `) | 627 |
| `parse_str()` com 2º argumento | 230 |
| construtor PHP4 → `__construct` | 134 |
| guardas `pg_*` contra resultado falso | 15 |
| casts `(int)`/`(float)` em aritmética e comparação com string | 3 |
| `is_resource()` → `is_resource() \|\| is_object()` (**núcleo**, ver categoria nova) | 2 |
| `break` fora de laço → `exit` | 2 |
| `eregi(` → `preg_match(` | 1 |

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 353 = 353 ✅ |
| 3. classificação dos `split` | 553 em PHP (todos literais), 8 em JavaScript preservados |
| 5. `php -l` nos dois runtimes | **699/699 do universo, 0 erros** em 5.6 e 8.5 |
| 6. instanciação das classes | **205/205, estado idêntico** |
| 6b. caminho de escrita | 4.299 linhas, 204 de 205 classes, **0 divergentes** |
| 7. bateria de telas | **350/353 idênticas** |
| 8. roteamento | `/fis1_*`, `/w/2/fis1_*` e `/Fis1_*` pelo 8.5; `/login.php` pelo 5.6 |

**Zero telas quebrando só no 8.5.** As 3 divergências restantes são defeitos pré-existentes, e
**nenhuma é item de menu** (o módulo tem 109 de 114 itens ligados):

- `fis1_sanitario004.php` — **não tem nenhum `include`**; usa `db_ancora()` e `rotulo->label()`
  sem carregar nada. Quebra nos dois (5.6: `Call to undefined function db_ancora()`; 8.5:
  `No PostgreSQL connection opened yet`, que é o mesmo defeito alcançado mais cedo).
- `fis1_tiafprazoproc002/003.php` — `forms/db_frmtiafprazoproc.php:30` usa `$cltiafprazo`, que
  **não é instanciado em lugar nenhum da cadeia**. O 5.6 renderiza a página de erro (500) e o
  8.5 para antes (200 truncado). Tela quebrada nos dois.

#### Decisão medida: NÃO usar Rector neste módulo

O `CLAUDE.md` registrava que o Rector "vale a pena a partir de `fis` (353) e `iss` (400)". A
recomendação era condicional ao volume; medida **neste** módulo, as duas vantagens concretas que
ele teve no experimento do `div` **não se aplicam**:

| Vantagem do Rector | No `div` | No `fis` |
|---|---|---|
| pega offset `->prop{}` que o regex não cobre | 1 (real) | **0 ocorrências** |
| não edita código comentado | 2 | **1 ocorrência** |

Trocar de instrumento custaria revalidar a *denylist* de 14 regras contra uma população de
arquivos nova e repetir o portão de funções ausentes (`str_starts_with`, `random_int`), sem
cobertura adicional. A recomendação segue de pé para `iss`, mas **tem de ser remedida lá** — o
critério é a presença das construções que o regex erra, não a contagem de telas.

### CATEGORIA NOVA (fis): `is_resource()` sobre resultado do PostgreSQL — NÚCLEO, FALHA SILENCIOSA

A mais grave desde o `0 == ""`, e da mesma família: **o código é válido nas duas versões, não
emite erro, e some com um campo da tela.**

```
                      pg_query(...) devolve
PHP 5.6:              resource    -> is_resource() = true
PHP 8.5:              object      -> is_resource() = FALSE   (PgSql\Result desde o PHP 8.1)
```

Comprovado nos dois runtimes:

```
ecidade_php56   tipo=resource   is_resource=true    is_object=false
ecidade_php85   tipo=object     is_resource=false   is_object=true
```

Onde dói: `dbforms/db_funcoes.php`, função **`db_selectrecord()`** do núcleo. Em modo leitura
(`$db_opcao = 3`) ela emite **dois** inputs — o código e a descrição —, e o segundo só é emitido
se o laço guardado por `is_resource($record)` encontrar a linha correspondente:

```php
if (is_resource($record)) {                     // no 8.5: FALSE, laco nunca roda
    for ($sqli = 0; $sqli < pg_numrows($record); $sqli++) { ... $nomec = pg_fieldname($record,1); }
}
if (!empty($nomec)) { db_input($nomec, ...); }  // no 8.5: $nomec vazio -> campo NAO sai
```

Sintoma observado em `fis1_aidof002/003` e `fis4_aidof005`: HTTP 200 nos dois runtimes, página
renderizando normalmente, e **437 bytes a menos no 8.5** — o input `q09_descr` com valor
`MODELO 1` simplesmente ausente. Nenhum fatal, nenhuma entrada no log.

**Correção: `is_resource($record) || is_object($record)`** — verdadeira nos dois runtimes.
Aplicada no original **e na cópia de `extension/modification/`**, que é a que executa para o
usuário `dbseller`.

Escala na base: **237 ocorrências de `is_resource` em 86 arquivos**. Nem todas são resultado de
PostgreSQL — *handles* de arquivo continuam sendo resource no PHP 8 —, então a varredura exige
classificar o argumento. Fica registrado como estimativa, não como lista de tarefas, seguindo a
mesma decisão tomada para as guardas `pg_*`.

**Por que nenhuma verificação anterior pegou:** `php -l` não vê, o harness de classes não vê (é
código de tela, não de classe), e o harness de escrita não vê (não passa por `atualizacampos()`).
**Só a comparação byte-a-byte entre runtimes encontra** — é o argumento mais forte do projeto a
favor de manter o 5.6 vivo como referência.

### CATEGORIA NOVA (fis): a RFC das comparações também muda `>` dentro do FPDF

Já estava catalogado que a RFC "Saner string to number comparisons" mudou `==` e os operadores
de ordem (o laço infinito do `agu`). Esta é a terceira manifestação, e atinge **o FPDF do
núcleo**, alterando o layout dos relatórios em silêncio.

A assinatura do FPDF é `Cell($w, $h, $txt, $border, $ln, $align, $fill, $link)`. O e-cidade
chama, em `fis3_relatoriosani.php:66`:

```php
$pdf->Cell(90, 6, $RLz01_cgccpf.': '.@$z01_cgccpf, 1, "J", 1, 30);
                                                      ^^^ isto cai em $ln
```

E dentro de `fpdf151/fpdf.php` (linhas 1001 e 2950):

```
              "J" > 0
PHP 5.6:      false      ("J" vira numero: 0 > 0)
PHP 8.5:      TRUE       (0 vira string: "J" > "0")
```

No 8.5 o `Cell` avança uma linha que não deveria avançar. O efeito no PDF gerado:

```
5.6:  Logradouro(y=680.32)  Numero(311.81, 680.32)  Complemento(411.03, 680.32)   <- mesma linha
8.5:  Logradouro(y=663.31)  Numero(311.81, 663.31)  Complemento(311.81, 646.30)   <- quebrou
```

O relatório inteiro desce e um campo muda de coluna. **HTTP 200 nos dois, PDF válido nos dois,
conteúdo diferente** — e o texto está dentro do fluxo `FlateDecode`, invisível a qualquer regex
de normalização. Só descomprimindo o stream dá para ver.

**Correção: `if((float)$ln>0)`** nas duas ocorrências — `(float)"J" > 0` é `false` nos dois
runtimes, reproduzindo o 5.6 exatamente. Passar a `"J"` como `$ln` é defeito pré-existente da
chamada; corrigi-lo mudaria o layout do 5.6, então **não foi tocado**.

### 7ª LACUNA: `db_utils::getDao('x')` instancia classes que nenhuma frente enxergava

A 4ª lacuna acrescentou a resolução de `new cl_*` para cobrir o autoload. Mas o e-cidade tem um
**segundo idioma de instanciação**, que não cita o nome da classe em lugar nenhum:

```php
$clcadtipo = db_utils::getDao('cadtipo');     // carrega classes/db_cadtipo_classe.php
$clcadtipo->rotulo->label();                  // no 8.5: label() on null
```

Como o construtor PHP 4 de `cl_cadtipo` é quem faz `$this->rotulo = new rotulo("cadtipo")`, a
classe não portada deixa `rotulo` em `null` e a tela morre.

Medido no `fis`: **61 DAOs distintos citados por `getDao()`, 16 classes fora do universo, 14
delas com construtor PHP 4** — ou seja, 14 classes que quebrariam em silêncio. O universo foi
de **682 para 699** arquivos e saíram mais 74 `split`, 72 guardas e 15 construtores.

`enumera.py` passou a resolver os dois idiomas na mesma frente.

**É a sétima vez que a mesma falha de método aparece:** a verificação partia da lista que a
própria enumeração gerou. Vale repetir o contraste — as sete lacunas foram encontradas por
*navegação* ou por *comparação de saída*, nunca pelas varreduras.

### LACUNA DE DETECÇÃO: o detector de `0 == ""` casa com a PRÓPRIA correção

O `enumera.py` procura `$this->X == "<literal>"` sobre propriedade inteira. A guarda que ele
mesmo manda aplicar é:

```php
($this->X === 0 || $this->X === 0.0 || $this->X == "")
                                       ^^^^^^^^^^^^^^ o detector casa aqui
```

Logo **essa categoria nunca pode reportar zero**, e "0 remanescentes" era impossível de obter
por ali. A conferência correta conta as ocorrências **sem guarda** — olhando os 120 bytes
anteriores atrás do prefixo `$this->X === 0 || $this->X === 0.0 || `.

Rodando o detector correto na base inteira: **21.019 ocorrências em 3.565 arquivos** (consistente
com as 19.401 registradas, maior porque agora inclui literais não-numéricos). Cruzando com os
746 arquivos já tocados por commits `Porta `, sobram **12** — os 11 do `tra` (órfão, registrados
como não corrigidos) e `classes/db_db_usuarios_classe.php`, que é **falso positivo**: ali a
comparação é `$this->liberalotacao == null || $this->liberalotacao == ''`, e `0 == null` é `true`
nos **dois** runtimes, então o curto-circuito já cobre o caso.

Ou seja: nenhum módulo portado tem buraco nessa categoria. Mas isso só se soube agora, porque o
instrumento não sabia medir o próprio resultado.

### CORREÇÃO ao catálogo: `break` fora de laço é fatal de EXECUÇÃO no 5.6, não warning

A seção do `jur` registra que `break` fora de laço "era *warning* no PHP 5.6". **Está errado** —
medido no próprio runtime:

```
PHP 5.6:  php -l  -> No syntax errors detected
          execucao -> Fatal error: Cannot break/continue 1 level
PHP 8.5:  php -l  -> Fatal error na COMPILACAO (arquivo inteiro nao carrega)
```

A diferença prática é grande: no 5.6 a tela funciona até alcançar aquela linha; no 8.5 ela não
carrega nunca. E muda a correção. No `jur` o `break` era inalcançável (a linha anterior chamava
`db_redireciona()`, que termina em `exit`), então removê-lo era exatamente equivalente.

Em `fis1_vistorias003.php:171` e `:179` ele **é alcançável** — são dois dos seis blocos de erro
idênticos da mesma função, e os outros quatro não têm `break` (é cópia dos dois que estão dentro
de `for`). Como o 5.6 morre ali sem chegar ao `db_fim_transacao($sqlerro)`, a correção fiel é
**`exit;`**, que reproduz esse fluxo nos dois runtimes (ambos terminam em rollback). Remover o
`break` faria o 8.5 seguir e tratar o erro normalmente — é conserto do defeito, não migração.

### ARMADILHA OPERACIONAL: `chmod 777 extension/log` não basta — os ARQUIVOS também

Sintoma: **toda** tela autenticada devolve `HTTP 500` com corpo vazio, nos dois runtimes, e
`login.php` continua respondendo 200. Parece defeito grave de migração; é permissão.

```
extension/log            drwxrwxrwx diego:diego   <- a pasta estava certa
extension/log/error.log  -rw-rw-r-- diego:diego   <- o ARQUIVO nao, e o container e uid 33
```

O Logger lança exceção fatal quando não consegue escrever, antes de qualquer saída. A receita de
subida já trazia `chmod 777 extension/log`; faltava `chmod 666 extension/log/*.log`, que a seção
de uids documentava mas o bloco de comandos não repetia. Acrescentado lá.

Diagnóstico que resolve em um passo: requisitar uma tela de **módulo já verificado** (`cem`,
`not`). Se ela também der 500, o problema é de ambiente, não do porte em andamento.

### Estado: BIBLIOTECA `dbagata/` PORTADA ✅ — pré-requisito do `iss` pago

`dbagata/` tem **602 arquivos**, dos quais **216 são PHP executável** (`.php`, `.class`, `.inc`).
Os outros são dados do Agata: 104 `.agl`, 73 `.agt`, 50 `.htm`, 25 `.rpt`, 15 `.map`, 10 `.lay`
e **74 `.fun`**. Os `.fun` *são* PHP, mas só `AgataInterface.class` — a GUI GTK que nada no
repositório inclui — os carrega; o caminho de relatório não os toca. Ficam registrados (3
`ereg*` em 3 arquivos) e não foram portados.

**5 dos 216 já não parseavam no 5.6** (`pdw_document.php` ×2 do phpdocwriter, `FileBox.class`,
`GtkPopDate.class`, `createwidgets.inc` — todos GTK/doc). Não dá para verificá-los por lint, e
são pré-existentes: ficaram de fora. **Universo portado: 211 arquivos.**

| Correção | Qtd |
|---|---|
| construtor PHP4 → `__construct` | 213 classes |
| `ereg*(` → `preg_match`/`preg_replace`/`str_replace` | 61 |
| offsets `{}` → `[]` | 16 |
| `=& new` → `= new` | 14 |
| `is_resource()` → `is_resource() \|\| is_object()` | 13 |
| chamadas ao construtor antigo (`parent::`, `$this->`, `Classe::Classe(`) | 10 + 62 |
| `split(` → `explode(`/`preg_split(` | 9 |
| assinaturas incompatíveis com a mãe (LSP) | 5 |
| `each(` → ponteiro explícito | 5 |
| `set/get_magic_quotes_runtime()` removidos | 5 |
| `array_merge()` com argumento nulo | 2 |
| `create_function(` → *closure* | 1 |

#### Verificação

| Critério | Antes | Depois |
|---|---|---|
| `php -l` no 5.6 | 0 erros (nos 211) | **0** |
| `php -l` no 8.5 | **11 erros** | **0** |
| `testeagata.php` (pipeline real de relatório) | 5.6 gera PDF, 8.5 dá 500 | **PDF byte-a-byte IDÊNTICO** |
| leitura de `.odt` por pclzip + caminho `BY_EREG` | — | **idêntico nos dois** |

E o ganho que prova o porte: a bateria do Cemitério foi de **114/116 para 115/116**.
`cem2_emitecertisen002.php` — a tela que este arquivo atribuía, desde o piloto, ao "diálogo de
erro do `dbagata/`, cujos construtores PHP 4 não rodam no 8.5" — **ficou idêntica**. Era
exatamente esse o defeito.

As demais sete baterias ficaram **iguais à linha de base** (itb 116/120, agu 222/224, jur
144/145, div 148/148, mar 35/35, not 14/14, fis 350/353): zero regressão a partir das mudanças
no núcleo. Das 1.155 telas dos oito módulos, **11 divergem e nenhuma quebra só no 8.5**.

#### O que ficou deliberadamente intocado

- **`nusoap.php:1731`** — `is_resource($this->fp)` com handle de `fsockopen()`. Diferente dos
  13 de driver de banco: `fsockopen` **continua devolvendo resource** no PHP 8. Mexer ali seria
  mudança sem motivo.
- **`GtkFrame::GtkFrame()`, `GtkButton::GtkButton()`, `GtkCList::GtkCList()`** e afins — são
  classes da extensão GTK, externas, cujos construtores eu não renomeei.
- **Mensagens de erro e comentários** que citam `Graph::Graph()` / `Text::Text()` em
  `jpgraph/lang/{en,de}.inc.php` e `jpgraph.php:2815`.
- As 6 ocorrências de `"\$subfield{$i}_sum"` em `AgataOOParser.class` e `AgataInterface.class`:
  **não são offsets, são interpolação** dentro de string de aspas duplas. Distinguem-se pela
  barra invertida antes do `$`.

### ⚠ 8ª LACUNA: a checagem de `__construct` era por ARQUIVO, e mascarava classes vizinhas

A mais cara até agora, porque **sobreviveu a oito portes** e vive no núcleo.

```python
has5 = re.search(rb'function\s+__construct\s*\(', b)   # <- arquivo INTEIRO
for m in re.finditer(rb'\bclass\s+(\w+)', b):
    if ... and not has5:                                 # <- mascara TODAS as classes
```

Num arquivo com várias classes, **uma** delas com `__construct` fazia o detector ignorar todas
as outras. O mesmo regex ainda contava como construtor um **método homônimo de outra classe**,
por buscar no arquivo inteiro — falso positivo na direção oposta.

Impacto medido na base, com detecção por classe: **42 classes em 5 arquivos, todos já dados
como portados**.

| Arquivo | Classes escondidas |
|---|---|
| `libs/jpgraph/jpgraph.php` | 33 |
| **`libs/db_stdlib.php` — NÚCLEO** | **3** (`cl_download`, `cl_verificaboletim`, `cl_abre_arquivo`) |
| `extension/modification/.../libs/db_stdlib.php` | 3 (a cópia que executa) |
| **`libs/JSON.php` — NÚCLEO** | **2** (`Services_JSON`, `Services_JSON_Error`) |
| `libs/jpgraph/jpgraph_line.php` | 1 |

Comprovado no runtime, com o bootstrap da aplicação:

```
PHP 5.6   cl_download->arquivo = 'rp4576_1791136974'   construtor rodou? SIM
PHP 8.5   cl_download->arquivo = NULL                  construtor rodou? NAO
```

`cl_download` é do núcleo e monta o nome do arquivo temporário de download. No 8.5 ele ficava
**nulo**. Corrigido nos 5 arquivos; `enumera.py` e `porta.py` passaram a fatiar o arquivo em
blocos de classe antes de decidir.

### CATEGORIA NOVA (dbagata): a terceira forma de chamar o construtor antigo

Renomear `function Classe()` para `__construct` quebra quem chamava pelo nome antigo. Já estavam
tratadas `parent::Classe(` e `$this->Classe(`. Faltava a **chamada estática**:

```php
class MyPdf extends FPDF {
    function __construct($o,$u,$f) {
        FPDF::FPDF($o,$u,$f);        // <- vira "Call to undefined method FPDF::FPDF()"
```

Correção: `Classe::Classe(` → `Classe::__construct(`, que preserva a semântica exata (chamada
do método da mãe no contexto do objeto) e funciona nos dois runtimes.

**Duas armadilhas na varredura dessa forma**, ambas encontradas na prática:

1. **Só vale para classes que EU renomeei.** `GtkFrame::GtkFrame()` é a extensão GTK, externa;
   converter quebraria. A lista de alvos tem de sair das classes que agora têm `__construct`
   nos arquivos alterados, não de um regex genérico `(\w+)::\1\(`.
2. **Comentário e string contam como ocorrência.** `jpgraph/lang/en.inc.php` traz
   `'Image width/height argument in Graph::Graph() must be numeric'` numa tabela de mensagens,
   e `jpgraph.php:2815` cita `Text::Text()` dentro de `//`. São 4 das 17 ocorrências.

**Como foi descoberta:** não pela varredura, e sim **exercitando o pipeline real** — o
`testeagata.php` passou a dar 500 no 8.5 *depois* do porte. É a mesma lição das oito lacunas,
com um agravante: aqui a varredura de remanescentes dizia "0" porque eu derivava a lista de
nomes do lugar errado.

### CATEGORIA NOVA (dbagata): `array_merge()` com argumento nulo, e o `@` que não suprime mais

```
                        @array_merge($a, null)
PHP 5.6:                NULL   (warning, suprimido pelo @)
PHP 8.5:                TypeError FATAL   -- o @ NAO suprime TypeError
```

Em `dbagata/classes/reports/AgataReport.class`, linhas 214 e 281. Era o que impedia o
`testeagata.php` de gerar relatório no 8.5.

Correção fiel, que reproduz o 5.6 **inclusive no resultado `NULL`**:

```php
$ClearColumns = (is_array($ClearColumns) && is_array($columns))
              ? array_merge($ClearColumns, $columns) : null;
```

**O ponto que generaliza:** o operador `@` deixou de ser rede de segurança no PHP 8 para toda
construção que passou de *warning* a `TypeError`/`ValueError`. Código legado que usa `@` para
"deixar passar" argumento inválido **falha mesmo com o `@`**. Vale para `array_merge`,
`pg_*`, `date()`, `sizeof()` e todas as outras já catalogadas aqui.

### Estado: MÓDULO `iss` (ISSQN) PORTADO ✅ — 9º da área Tributário, e o 1º feito com Rector

**400 telas** (`^iss[0-9]*_`). O módulo tem **oito** variantes de prefixo: `iss1_`…`iss4_`, mais
`iss01_`, `iss03_`, `iss04_` e **`iss179_`** — esta última derrubaria um `[0-9]?` no nginx, mesma
armadilha do `jur01_`. Universo pelas sete frentes: **819 arquivos**, **280 alterados**.

| Correção | Qtd |
|---|---|
| guarda `$this->X == <literal>` | 711 |
| `split(`/`ereg*(` → `preg_*` | 538 |
| construtor PHP4 → `__construct` | 127 |
| `parse_str()` + `extract()` | 116 |
| guardas `pg_*` contra resultado falso | 26 |
| guardas de divisão por zero | 5 |
| `reset()`/`sizeof()`/`rsort()` sobre null | 5 |
| teste `$txt!=''` do `Cell()` do FPDF | 2 |
| `sprintf('%.f')` → `'%.6f'` | 1 |
| construtor com argumento faltando | 1 |

Mais **6.480 linhas de modernização** que o Rector trouxe junto e que **não** são exigidas pela
versão de destino: 2.973 renomeando alias `pg_*`, 2.432 `var $x` → `public $x`, 1.075
acrescentando `public` a método. Ver a ressalva no fim desta seção.

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 400 = 400 ✅ |
| 5. `php -l` nos dois runtimes | 280/280 alterados, 0 erros em 5.6 e 8.5 |
| portão de funções contra o 5.6 | 0 ausentes |
| 7. bateria de telas | **397/400** (371 → 393 → 395 → 396 → 397) |
| 8. roteamento | `iss1_`, `iss01_`, `iss179_` e `/w/2/iss1_` pelo 8.5 |
| regressão nos 8 módulos anteriores | **zero** — todos na linha de base |

As 3 divergências restantes são bugs **pré-existentes** e ficam como estão, pelo princípio
registrado em *Princípios*:

- `iss1_tabalvara_depto001.php` — `$cltabdesc` é usado na linha 43 e **nunca atribuído** no
  arquivo. Até o PHP 7 isso criava um `stdClass` automaticamente; o 8.0 transformou em `Error`.
- `iss4_issbasecaracteristicas001.php` — `$oGrupo` nulo, mesma família.
- `iss3_emissaoalvaraeventos001.php` — `pg_lo_export($oid, $file, $conn)`, com os argumentos na
  ordem errada. A assinatura é `($connection, $oid, $filename)` **nos dois runtimes**; o 5.6
  tolerava.

### ⚠ DECISÃO: Rector adotado como instrumento do passo 4, a partir do `iss`

O experimento do `div` havia concluído "híbrido: Rector na camada sintática, ferramental próprio
na semântica", e eu medi duas vezes (`fis`, `iss`) que a vantagem da AST era pequena demais para
pagar a troca. **O que mudou a conta foi escrever as duas regras que faltavam.**

`scratchpad/rector-rules/` — 196 linhas, contra 150 do `porta.py` inteiro:

| Regra própria | Linhas | Cobre |
|---|---|---|
| `GuardaComparacaoLiteralRector` | 122 | `$this->X == "<literal>"` → guarda do 5.6 |
| `ParseStrComExtractRector` | 74 | `parse_str` de 1 arg + `extract()` |

Com elas, o Rector faz **100% do porte**. Acordo medido contra o `porta.py`, a partir do mesmo
ponto de partida: **246 de 248 arquivos semanticamente idênticos**, e nos 2 em que divergem **o
Rector está certo** — o `porta.py` editou um `parse_str` que estava dentro de comentário.

Onde a AST ganha do regex, medido e não suposto:

- **comentário**: o regex não distingue código de comentário; a AST sim
- **precedência**: o printer põe parênteses só onde muda o sentido —
  `($this->a === 0 || … ) && $o` leva, `… ? 1 : 2` não leva. O `porta.py` parentiza sempre.

#### Os cinco modos de falha silenciosa que a adoção custou

Nenhum deles aparece em varredura; todos foram achados por verificação cruzada.

1. **O Rector desliga regras em silêncio.** Sem `->withPhpVersion()`, ele resolve a versão alvo
   do `composer.json` do projeto (`">=5.6.4"`) e pula toda regra com *version bonding* —
   `Php4ConstructorRector` (122 arquivos) e `EregToPregMatchRector` (118) entre elas — relatando
   `[OK] N files changed` sem aviso nenhum. **O pin é obrigatório.**
2. **Denylist não é transferível entre módulos.** `StrContainsRector` e `ArrayKeyFirstLastRector`
   nunca dispararam no `div` e dispararam no `iss`, emitindo `str_contains()` (PHP 8.0) e
   `array_key_first()` (PHP 7.3) em arquivos servidos pelo runtime **5.6**. Passam no `php -l`.
   A denylist foi de 14 para 16 regras — e tem de ser reconferida a cada módulo.
3. **O Rector não converge numa passada, e isso é intermitente.** Rodando o mesmo comando sobre
   os mesmos alvos: 163 arquivos, depois mais 83, depois 0. Noutra execução, 246 e depois 0.
   **Repetir até dar zero** é obrigatório; um run não prova nada.
4. **Regra própria que devolve nó contendo o original entra em laço infinito.** O PhpParser
   percorre os filhos do substituto, e o substituto não passa por `enterNode` — então uma
   checagem de forma nunca é alcançada. O processo morre com `Killed`, sem traceback. A barreira
   que funciona é marcar o nó (`setAttribute`) ao embrulhar.
5. **Regra própria que cria nó novo apaga comentários.** Nó novo nasce sem atributos, e os
   comentários ficam presos ao antigo. Três arquivos perderam linhas como `//--- parser POST/GET`.
   Correção: reaproveitar o nó original em vez de criar outro.

#### A ressalva que fica

O Rector traz junto **modernização que a versão de destino não exige** — no `iss`, 6.480 das
8.409 linhas (77%). É o "grupo (c)" da taxonomia do TCC de referência, e infla a revisão. Duas
observações honestas: `pg_numrows()` **é** deprecated desde o 8.0 (confirmado no runtime), então
o rename é grupo (b) e não lixo; e `var $x` → `public $x` é inofensivo nos dois runtimes. Mas o
diff passa de 1.929 linhas de migração para 8.409 no total, e quem revisar precisa saber disso.

**RESOLVIDO a partir do `dvr`:** as quatro regras entraram na denylist. Medido num caso que
exercita todas as categorias do catálogo, desligá-las **não custa nada obrigatório** — `split`,
`spliti`, `ereg*`, offsets `{}`, `create_function` e construtor PHP 4 são convertidos por regras
**dedicadas**, não pelo `RenameFunctionRector`:

| | config anterior | com a denylist |
|---|---|---|
| `split`/`spliti` → `preg_split` | ✓ | ✓ |
| `ereg*` → `preg_*` | ✓ | ✓ |
| offset `{}` → `[]` | ✓ | ✓ |
| construtor PHP4 → `__construct` (+ chamada ao nome antigo) | ✓ | ✓ |
| guarda `== <literal>` e `parse_str`+`extract` (regras próprias) | ✓ | ✓ |
| `pg_numrows` → `pg_num_rows` | ✓ | **não** |
| `var $x` → `public $x` | ✓ | **não** |
| `array()` → `[]` | ✓ | **não** |
| `public` em método | ✓ | **não** |

#### E mais duas, por segurança: as regras de `each()`

A comparação expôs algo que eu não procurava: a config convertia
`while (list($k,$v) = each($arr))` em `foreach`. **O catálogo proíbe exatamente isso** — em
`db_libpessoal.php` há laços que dependem do ponteiro interno já exaurido por um laço anterior e
que por isso *nunca executam*; trocar por `foreach` faz o segundo rodar. O Rector não tem como
enxergar o `reset()` anterior.

`WhileEachToForeachRector` e `ListEachRector` entraram na denylist. `each()` volta a ser tratado
à mão com `key()`/`current()`/`next()`, conferindo o contexto — como sempre foi.

**Denylist: 22 regras.** Ela cresceu 16 → 22 entre o `iss` e o `dvr`, o que confirma a lição do
item 2 acima: *denylist não é transferível, tem de ser reconferida a cada módulo.*

### CATEGORIA NOVA (iss): `DivisionByZeroError`

```
                     10 / 0        10 % 0
PHP 5.6:             false         false      (Warning, suprimivel com @)
PHP 8.0+:            DivisionByZeroError FATAL  -- o @ NAO suprime
```

É da mesma família do `array_merge(null)`: construção que era *warning* e virou `Error`, com o
`@` deixando de ser rede de segurança.

Onde apareceu: cinco pontos, **dois deles no núcleo** (`fpdf151/fpdf.php`, no desenho do gráfico
de pizza, quando `$this->sum` é zero) e três em `iss2_calculadoepago002.php`, quando o relatório
não tem registros.

**Correção fiel:** guardar o denominador produzindo o valor que o 5.6 entregava adiante. O 5.6
devolvia `false`, que as funções seguintes coagiam para 0:

```php
floor(($val * 360) / doubleval($this->sum))
  ->  floor($this->sum ? ($val * 360) / doubleval($this->sum) : 0)

100 - (($qtd_emdia * 100) / $qtd_calcfixo)
  ->  100 - ($qtd_calcfixo ? ($qtd_emdia * 100) / $qtd_calcfixo : 0)
```

Comprovado no 5.6: `floor(false)` = 0 e `100 - false` = 100 — idênticos à guarda.

**Não varrer em massa.** `fpdf151/fpdf.php` tem **25 divisões por variável**, quase todas por
`$this->k` (a escala, nunca zero). Vale a mesma decisão das guardas `pg_*`: corrigir na aparição.

### CATEGORIA NOVA (iss): `sprintf('%.f')` mudou de precisão

```
                     sprintf('%.f', 0)
PHP 5.6:             "0.000000"    (precisao sem digito = padrao 6)
PHP 8.5:             "0"           (precisao sem digito = 0)
```

Não é erro, não é aviso: é **saída diferente**. Em `fpdf151/fpdf.php` isso mudava a legenda do
gráfico de `(0.000000%)` para `(0%)`, e como a largura do texto define o layout, **a geometria
inteira do gráfico se deslocava** — centro, raio e posição de cada rótulo.

**Correção: `'%.f'` → `'%.6f'`**, que torna explícita a precisão que o 5.6 assumia.

Vale a pena registrar como o defeito foi achado, porque nenhum portão o pegaria: `php -l` passa,
não há fatal no log, e os dois runtimes devolvem HTTP 200. Só a **comparação byte-a-byte**, e
mesmo assim só depois de descomprimir o fluxo `FlateDecode` do PDF.

### CATEGORIA NOVA (iss): o `0 == ""` dentro do `Cell()` do FPDF

A RFC "Saner string to number comparisons" já estava catalogada nas formas `==` e de ordem.
Esta é a quarta manifestação, e vive no **núcleo**, no teste que decide se o FPDF escreve o
texto de uma célula:

```php
fpdf151/fpdf.php:965    if($txt!='')      // decide se imprime o texto da celula
```

```
                     0 != ""
PHP 5.6:             false   -> celula fica VAZIA
PHP 8.5:             TRUE    -> imprime "0"
```

Sintoma observado em `iss2_escritctb002.php`: o campo "Total de Registros" saía **em branco** no
5.6 e **`0`** no 8.5. HTTP 200 nos dois, PDF válido nos dois, 41 bytes de diferença.

**Correção:** `if($txt!='' && $txt!==0 && $txt!==0.0)`, aplicada também na linha 866 (o mesmo
teste no sublinhado). Verificada caso a caso nos dois runtimes:

```
          0      0.0     ""      "0"        "abc"      null
5.6:    vazio   vazio   vazio   imprime    imprime    vazio
8.5:    vazio   vazio   vazio   imprime    imprime    vazio
```

Identificada uma terceira ocorrência do mesmo teste em `fpdf151/FpdfMultiCellBorder.php:301`,
**não tocada** — nenhuma tela a exercitou ainda, e vale a decisão de corrigir na aparição.

### Estado: MÓDULO `dvr` (Diversos) PORTADO ✅ — 10º da área Tributário

**33 telas** (`^dvr[0-9]*_`, variantes `dvr2_`/`dvr3_`/`dvr4_`, sem maiúsculas). Universo pelas
sete frentes: **436 arquivos**, **197 alterados** — a razão telas/arquivos mais desproporcional
da área até aqui (33 telas puxando 197 arquivos), porque quase tudo é `classes/` compartilhada
com Contabilidade e Empenho.

| Correção | Qtd |
|---|---|
| guarda `$this->X == <literal>` | 1.199 |
| `split(`/`ereg*(` → `preg_*` (744 `split`, todos com separador literal) | 744 |
| construtor PHP4 → `__construct` | 162 |
| guardas `pg_*` contra resultado falso | 18 |
| `parse_str()` + `extract()` | 3 |
| parâmetro obrigatório depois de opcional → default `null` | 6 arquivos |
| `$$var` → `${$var}` | 2 arquivos |

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 33 = 33 ✅ |
| 3. classificação dos `split` | 744 literais, **0 regex**, 1 em JavaScript preservado |
| 4. Rector | convergiu em **1 passada** (196 arquivos, depois 0) |
| 4b. portão de funções | 2 novas (`extract`, `preg_split`), 0 ausentes no 5.6 |
| 5. `php -l` nos dois runtimes | **436/436 do universo, 0 erros** |
| 6. instanciação das classes | 315 de 316 idênticas (ver abaixo) |
| 6b. caminho de escrita | 6.207 linhas, 299 classes, 2 divergentes (ver abaixo) |
| 7. bateria de telas | **33/33 idênticas, 0 divergentes** |
| 8. roteamento | `dvr2_`, `dvr3_`, `dvr4_` e `/w/2/` pelo 8.5; `div1_` não foi sombreado |
| regressão nos 9 módulos anteriores | **zero** — todos na linha de base |

**Quarto módulo com bateria perfeita**, depois de `div`, `mar` e `not`. O diff ficou em **2.150
linhas** contra as 8.409 do `iss` — efeito direto da denylist de modernização.

As 4 divergências da primeira bateria eram todas `pg_numrows` sobre resultado falso, em
`dvr2_capaloteamento002`, `dvr3_procedper002` e `dvr4_parclote004/005`. Guardadas as 18 chamadas
desses quatro arquivos, a bateria fechou.

#### Divergências do harness que NÃO são defeito de porte

- **`lancamentoContabil` e `ordemPagamento`** aparecem com `ArgumentCountError` no 8.5 e ausentes
  no 5.6. São `.model.php` com `__construct` exigindo argumentos; o harness instancia sem
  nenhum. No 8.5 o erro é capturável e a varredura segue; **no 5.6 o processo morre**. Limitação
  conhecida do instrumento, igual à registrada no `dbagata/`.
- **`classes/empenho.php` → `datausu`** diverge: `'1969-12-31'` no 5.6 e a data de hoje no 8.5.
  É a categoria nova abaixo, e aparece **porque o construtor agora roda no 8.5** — antes nem
  chegava lá. Só se manifesta sem sessão, que é a condição do harness, não de operação.

### CATEGORIA NOVA (dvr): `date($fmt, null)` significa AGORA no PHP 8

Já estava catalogado que `date()` com *string* é `TypeError` no PHP 8. Com **`null`** não há erro
nenhum — e o resultado muda:

```
                     date("Y-m-d", null)
PHP 5.6:             "1969-12-31"    (null coagido para 0)
PHP 8.5:             "2026-10-10"    (null = usar o relogio, como se o argumento fosse omitido)
```

Medido nos dois runtimes com `db_getsession("DB_datausu")` ausente, que devolve `NULL` em ambos.

**É a forma mais perigosa da família**: não há fatal, não há aviso, e o campo de data recebe
**hoje** em vez da época. Num sistema que grava data de empenho e de pagamento, isso é dado
errado gravado em silêncio.

Correção fiel quando aparecer: `date("Y-m-d", (int)$x)` — `(int)null` é 0, reproduzindo o 5.6.

**NÃO foi varrido em massa.** Escala medida só no universo do `dvr`: **183 ocorrências de
`date(<fmt>, <variável>)` em 39 arquivos**, 20 delas em `classes/empenho.php`. Vale a mesma
decisão das guardas `pg_*`: corrigir na aparição. A bateria das 33 telas fechou **33/33**, o que
indica que em operação normal (com sessão) o valor chega preenchido e os dois runtimes
concordam — mas o risco fica registrado, e é o candidato número um a aparecer no `arr`, que
arrasta 208 arquivos de Empenho.

### Denylist do Rector: 22 → 23 (terceira vez que ela cresce)

`IfIssetToCoalescingRector` **nunca disparou no `div` nem no `iss`, e disparou no `dvr`**. Ela
converte

```php
if (isset($GLOBALS["HTTP_POST_VARS"][$c])) { return $GLOBALS["HTTP_POST_VARS"][$c]; }
return null;
          ->  return $GLOBALS["HTTP_POST_VARS"][$c] ?? null;
```

e o `??` é **PHP 7.0 — parse error no 5.6**. Medido: `$x["k"] ?? null` não parseia no 5.6 e
parseia no 8.5.

Outras duas regras novas apareceram e **foram verificadas e mantidas**, porque são seguras nos
dois runtimes:

| Regra | O que faz | 5.6 | 8.5 |
|---|---|---|---|
| `OptionalParametersAfterRequiredRector` | `function f($a="", $b)` → `$b = null` | ok, devolve `null` | idem |
| `WrapVariableVariableNameInCurlyBracesRector` | `$$label` → `${$label}` | ok | idem |

**A conferência por módulo se pagou pela terceira vez.** Sem ela, 1 arquivo iria para a árvore
com sintaxe que derruba o runtime de referência — e o `php -l` do 8.5 não acusaria nada.

**Armadilha nova do instrumento:** com a config contendo erro de sintaxe, o Rector reportou
**`0 arquivos, 0 regras` sem nenhuma mensagem de erro** no formato JSON. Mais uma falha
silenciosa dele: conferir sempre `php -l` na própria config antes de confiar num resultado zero.

### Estado: MÓDULO `arr` (Arrecadação) PORTADO ✅ — 11º da área Tributário

**162 telas** (`^arr[0-9]*_`, variantes `arr1_`…`arr4_`, sem maiúsculas). Universo pelas sete
frentes: **787 arquivos** — e **366 já pagos** pelos dez portes anteriores, restando **137 a
alterar**. Efetivamente alterados: **116**.

| Correção | Qtd |
|---|---|
| guarda `$this->X == <literal>` | 504 |
| `split(`/`ereg*(` → `preg_*` (279 `split`, todos literais) | 281 |
| construtor PHP4 → `__construct` | 70 |
| `parse_str()` + `extract()` | 34 |
| `$$var` → `${$var}` | 10 |
| guarda `pg_*` contra resultado falso | 1 |

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 162 = 162 ✅ |
| 3. classificação dos `split` | 279 literais, **0 regex**, 0 em JavaScript |
| 4. Rector | **5 regras, todas já vetadas**; convergiu em 1 passada |
| 4b. portão de funções | 3 novas, 0 ausentes no 5.6 |
| 5. `php -l` nos dois runtimes | **787/787 do universo, 0 erros** |
| 6. instanciação das classes | 450 de 451 idênticas (artefatos conhecidos do harness) |
| 6b. caminho de escrita | 9.267 linhas, 434 classes, 2 divergentes (os mesmos do `dvr`) |
| 7. bateria de telas | **162/162 idênticas, 0 divergentes** |
| 8. roteamento | `arr1_`…`arr4_` e `/w/2/` pelo 8.5; `agu1_` não foi sombreado |
| regressão nos 10 módulos anteriores | **zero** — todos na linha de base |

**Quinta bateria perfeita**, e no módulo mais acoplado da área. A única divergência da primeira
rodada era `pg_numrows` sobre resultado falso em `arr2_rellistadqd002.php:178`.

#### ⚠ CORREÇÃO: a previsão de contaminação de escopo do `arr` estava muito errada

Este arquivo registrava, com base na tabela de resíduo:

> **`arr` é o único que rompe a fronteira da área.** Ele arrasta 212 arquivos de `con`
> (Contabilidade) e 203 de `pes` (RH) — módulos de *outras* áreas.
> `arr   func:285   cai:252   con:212   emp:208   pes:203`

**Medido no porte real, a distribuição dos 116 arquivos alterados é:**

```
classes/  80      arr_  32      func_  2      model/  1      cai_  1
```

Nenhum arquivo de `con`, `pes` ou `emp` precisou ser tocado. A previsão não estava errada quanto
ao *fecho de dependências* — `arr` de fato alcança aqueles módulos —, e sim quanto ao **custo**:
a tabela foi computada **antes dos portes** e contava como "a alterar" tudo que o `arr` encosta.
Depois de dez módulos, **366 dos 787 arquivos do universo já estavam pagos**, e o que sobrou do
resíduo compartilhado eram classes que `div`, `fis`, `iss` e `dvr` já haviam corrigido.

**Lição para o relatório:** a métrica de resíduo mede contaminação de escopo num instante, e
**envelhece rápido** num porte incremental. O `arr`, previsto como "o dobro do maior lote já
executado" (343 arquivos), saiu com **116** — menor que o `fis` (384), o `iss` (280) e o `dvr`
(197). A ordem adotada (deixar o `arr` por último) foi, por acidente, a que minimizou o custo
dele: cada módulo anterior pré-pagou parte do seu resíduo.

#### A categoria do `date(null)` NÃO se manifestou

O `arr` tem **24 `date(<fmt>, <variável>)`** e eu havia registrado que era "o candidato número
um a aparecer". A bateria fechou **162/162**, o que confirma o raciocínio da seção do `dvr`: com
sessão presente, `db_getsession("DB_datausu")` devolve um timestamp válido e os dois runtimes
concordam. A divergência exige a variável de sessão ausente, que é condição do harness e não de
operação. As 24 ocorrências ficam **não corrigidas**, como as 183 do `dvr`.

### ⚠ CORREÇÃO: `tri` e `inf` NÃO foram cobertos pelos módulos que os hospedam

Este arquivo supunha, desde o plano da Fase A, que `inf` e `tri` entrariam "junto dos módulos
que os hospedam". **Medido depois do `arr`, não entraram:**

| Prefixo | Telas | Universo | Já pago | **A alterar** | Roteado? |
|---|---|---|---|---|---|
| `tri` | 33 | 83 | 25 | **28** | não — responde pelo 5.6 |
| `inf` | 30 | 89 | 42 | **16** | não — responde pelo 5.6 |

São 44 arquivos no total — os dois menores lotes restantes da área, menores que o `mar` (19) e o
`not` (17) só em telas, não em arquivos. A Fase A **não está concluída** até eles entrarem.

### Estado: MÓDULOS `tri` e `inf` PORTADOS ✅ — 12º e 13º, e a FASE A FECHA

Os dois últimos prefixos exclusivos da área, portados no mesmo lote por serem pequenos.

| | `tri` | `inf` |
|---|---|---|
| Telas (`^tri[0-9]*_` / `^inf[0-9]*_`) | 33 (`tri1_`, `tri4_`) | 30 (`inf1_`, `inf2_`, `inf4_`) |
| Universo pelas sete frentes | 83 | 89 |
| Já pago pelos portes anteriores | 25 | 42 |
| **Alterados** | **28** | **16** |
| `php -l` nos dois runtimes | 145/145 no universo combinado, 0 erros | |
| Instanciação das classes | 21/21 idênticas | 28/28 idênticas |
| Caminho de escrita | 616 linhas, 0 divergentes | 720 linhas, 0 divergentes |
| **Bateria de telas** | **33/33** | **30/30** |

Correções somadas nos dois: 63 guardas `== <literal>`, 53 `split`/`ereg` → `preg_*`, 29
`parse_str`+`extract`, 13 construtores, 2 guardas `pg_*`, 1 `${$var}`. Nenhuma categoria nova.
O Rector aplicou 4 regras no `tri` e 5 no `inf`, **todas já vetadas** — a denylist não cresceu.

**Sexta e sétima baterias perfeitas**, e as duas divergências iniciais foram a mesma categoria
de sempre: `pg_numrows` sobre resultado falso, uma em cada módulo.

**O passo novo do log do PostgreSQL funcionou de primeira.** Na bateria do `tri` ele apontou a
consulta culpada antes de eu abrir o log da aplicação:

```
ERRO: erro de sintaxe no fim da entrada no caractere 219
INSTRUÇÃO: select k09_sequencial, k37_descr from cadtipo inner join cadtipoitem ...
```

Confirma a premissa corrigida: a SQL está **truncada** — não é tabela vazia.

### 📊 FASE A CONCLUÍDA — o número que resume o trabalho

| | |
|---|---|
| Prefixos exclusivos portados e roteados | **13 de 13** |
| **Telas servidas pelo PHP 8.5** | **1.813** |
| **Telas comparadas byte-a-byte** | **1.799 idênticas de 1.813 — 99,2%** |
| Divergências remanescentes | **14**, todas caracterizadas |
| Módulos com bateria **perfeita** | **7** — `div`, `mar`, `not`, `dvr`, `arr`, `tri`, `inf` |

As 14 divergências, por módulo: `itb` 4, `fis` 3, `iss` 3, `agu` 2, `cem` 1, `jur` 1. **Nenhuma
é defeito de migração** — são de três tipos já documentados nas seções de cada módulo: telas que
quebram **no 5.6** e funcionam no 8.5 (defeito pré-existente da referência), fragmentos de
include que não são telas, e variáveis/objetos nunca instanciados no próprio código legado.

Ordem em que foram portados, com o tamanho do lote efetivo:

```
cem 187   itb 192   agu 171   jur 137   div 158   mar  19   not  17
fis 384   iss 280   dvr 197   arr 116   tri  28   inf  16      + dbagata 211 e o nucleo
```

**O `arr`, previsto como o maior (343), saiu em 116** — ver a correção na seção dele. A ordem
adotada (grandes no meio, `arr` por último) foi a que minimizou o custo total, porque cada
módulo pré-paga o resíduo compartilhado do seguinte.

### 📐 FASE B DIMENSIONADA — e duas correções ao que este arquivo afirmava

Medido em 10/10/2026, antes de começar. Duas premissas registradas aqui estavam erradas.

#### ⚠ CORREÇÃO 1: "13 de 16 módulos portados" media PREFIXOS, não módulos

O cabeçalho de estado dizia 13 de 16. **Por telas de menu efetivamente roteadas, só 2 dos 16
módulos estão completos** — `Marcas e Sinais` e `Inflat`. Todos os outros 14 têm pelo menos uma
tela atrás de prefixo compartilhado, quase sempre `cai` (Caixa).

| Módulo | Telas | Já no 8.5 | Faltam | Prefixos que faltam |
|---|---|---|---|---|
| Cadastro | 170 | **0** | 170 | `cad` `cai` `pro` |
| Arrecadação | 172 | 92 | 80 | `cai` |
| Projetos | 35 | 1 | 34 | `pro` `rec` |
| Contrib | 31 | **0** | 31 | `cai` `con` |
| Notificações | 25 | 7 | 18 | `cai` |
| ISSQN | 182 | 174 | 8 | `cad` `cai` `pre` |
| Meio Ambiente | 8 | **0** | 8 | `amb` `pro` |
| Dívida Ativa | 57 | 52 | 5 | `cai` |
| Fiscal | 97 | 94 | 3 | `cai` `prot` |
| Cemitério | 43 | 40 | 3 | `cai` `prot` |
| ITBI | 25 | 23 | 2 | `cad` `cai` |
| Diversos | 15 | 13 | 2 | `cai` `dv` |
| Água | 109 | 108 | 1 | `cai` |
| Jurídico | 62 | 61 | 1 | `cai` |
| **Marcas e Sinais** | 17 | **17** | **0** | — |
| **Inflat** | 8 | **8** | **0** | — |
| **Total** | **1.056** | **690 (65%)** | **366** | |

As 1.813 telas servidas pelo 8.5 continuam corretas — são **arquivos por prefixo**, e dois terços
deles não estão no menu. As duas métricas medem coisas diferentes e as duas valem: *arquivos
roteados* mede o porte, *telas de menu cobertas* mede o que o usuário alcança.

#### ⚠ CORREÇÃO 2: os prefixos compartilhados quase NÃO são compartilhados

Este arquivo afirmava que `cad` e `con` "não podem ir inteiros para o 8.5 sem arrastar
Financeiro e Patrimonial". Medido tela a tela, **as telas são quase disjuntas**:

| Prefixo | Só Tributário | Em Tributário **e** outra área | Só outras áreas |
|---|---|---|---|
| `con` | 30 | **0** | 511 |
| `cai` | 77 | **24** | 151 |
| `cad` | 165 | **1** | 1 |
| `pro` | 34 | **1** | 66 |
| `pre` | 6 | **0** | 35 |
| `amb` | 7 | **0** | 14 |
| **Total** | **319** | **26** | **778** |

**26 telas de 345 (7,5%)** são de fato compartilhadas — 24 delas `cai` com Financeiro
(`cai1_receita*`, `cai1_cfautent*`, `cai4_arrecada001`…), 1 `cad`, 1 `pro`. O risco existe e é
pequeno, e **é de roteamento, não de porte**: o código portado roda nos dois runtimes, então
quem cair no 8.5 por essas 26 telas recebe código verificado byte-a-byte.

#### Os dois escopos possíveis, medidos

| | **A — prefixos inteiros** | **B — só as telas de Tributário** |
|---|---|---|
| Telas roteadas | 3.244 arquivos | **351 telas** (345 + 6 de `prot`/`rec`/`dv`) |
| Universo pelas sete frentes | 5.510 | **1.439** |
| Já pago pela Fase A | 1.004 | **413** |
| **Arquivos a alterar** | **2.072** | **428** |
| Roteamento | uma linha no `location` | `map` de 341 nomes (~10 KB), gerado do banco |
| Efeito colateral | migra Contabilidade, RH, Patrimonial junto | 26 telas de Financeiro vão junto |
| Comparável a | **toda a Fase A** (2.113) | **um módulo grande**: entre `iss` (280) e `fis` (384) |

Custo incremental do escopo A, na ordem do menor para o maior — a sobreposição entre os seis é
de 1.064 arquivos, então somar os lotes isolados superestima em 183:

```
amb    28 isolado ->  28 incremental   (acumulado    28)
pre    29            29                            57
pro   235           234                           291
cad   376           365                           656
cai   544           503                         1.159
con  1043           913                         2.072
```

Distribuição dos 428 arquivos do escopo B: `classes/` 202, `cad_` 105, `cai_` 52, `con_` 30,
`pro_` 21, `func_` 9, resto 9. Categorias: 1.156 guardas `== <literal>`, 802 `split(`, 212
`parse_str`, 187 construtores PHP 4, 14 `ereg*`, 5 `each(`, 2 offsets `{}`. **Nenhuma categoria
nova** — o catálogo das 13 já cobre tudo que a varredura encontra.

#### Viabilidade do roteamento por lista, verificada

- **341 nomes distintos**, sem colisão; `map` de ~10 KB no nginx.
- **3 telas em maiúscula** (`Cai1_recreparcori001/002/003.php`) — o `map` tem de ser
  *case-insensitive*, mesma armadilha do `location ~*`.
- **4 itens de menu apontam para arquivo que não existe** (`cad1_iptupadrao001/002.php`,
  `cad4_iptunotificacaolancamento.php`, `cad4_manutencaonotificacaolancamento.php`). Defeito
  pré-existente do cadastro de menu; ficam de fora.
- Os dois terços fora do menu (popups, `.RPC.php`) **continuam no 5.6** e funcionam: são portados
  junto por estarem no universo, e código portado roda nos dois runtimes. O `/tmp` compartilhado
  já resolveu o loop de iframes que isso poderia causar.

#### Recomendação: escopo B

Ele fecha a área (16 de 16 módulos, 1.056 telas de menu) por **428 arquivos** — o tamanho de um
módulo grande, dentro da faixa já provada sete vezes. O escopo A custa 4,8× mais e entrega
Contabilidade, RH e Patrimonial, que **não estão no escopo acordado da disciplina**.

**Duas decisões em aberto, ambas do usuário:**

1. **As 26 telas compartilhadas com Financeiro** — roteá-las (o módulo Arrecadação fica completo,
   e 24 telas de Financeiro passam a ser servidas pelo 8.5) ou deixá-las no 5.6 (Arrecadação fica
   em 92+56 de 172). Recomendo **roteá-las**: o código é o mesmo nos dois runtimes.
2. **Os 6 itens de `prot`/`rec`/`dv`** — prefixos minúsculos nesta área (48, 279 e 2 arquivos em
   disco) que ninguém tinha notado. São 6 telas; incluí-las é barato e evita um 17º resíduo.

### Estado: FASE B INICIADA — `amb` e `pre` PORTADOS ✅, e o `map` funciona

Primeiro lote do escopo B. Escolhidos por serem os menores: validam o mecanismo de
roteamento por lista antes de `cad` (166 telas) e `cai` (101).

**Decisão de escopo tomada aqui:** porta-se o **prefixo inteiro** (57 arquivos), roteia-se
**só as telas de Tributário** (13). Portar mais do que se roteia é inofensivo — todo código
portado roda nos dois runtimes — e evita a lacuna dos 2/3 fora do menu. As telas `amb` de
Saúde e `pre` de Cidadão ficam no 5.6, já portadas para quando essas áreas chegarem.

| | `amb` | `pre` |
|---|---|---|
| Arquivos do prefixo | 31 | 54 |
| Universo pelas sete frentes | 103 | 133 |
| **Alterados** | **28** | **29** |
| Telas roteadas (Tributário) | **7** | **6** |
| `php -l` nos dois runtimes | 207/207 no universo combinado, 0 erros | |
| Instanciação das classes | 60/60 idênticas | |
| Caminho de escrita | 1.601 linhas, 59 classes, 0 divergentes | |
| **Bateria de telas** | **31/31** | **54/54** |
| Regressão nos 13 módulos da Fase A | **zero** — todos na linha de base | |

Correções: 181 guardas `== <literal>`, 89 `split`/`ereg` → `preg_*`, 31 construtores PHP 4,
25 `parse_str`+`extract`, 9 guardas `pg_*`, 1 offset `{}`.

#### O roteamento por `map`, montado e verificado

`docker/proxy/faseb_map.conf` é **gerado do banco** por `scratchpad/gera_map_faseb.py`; o
`nginx.conf` ganhou três `map`:

```nginx
map $uri $ecidade_arquivo {          # tira o prefixo de janela /w/<n>/
    default                         $uri;
    ~^(?:/w/[0-9]+)?/(?<arq>[^/]+)$ $arq;
}
map $ecidade_arquivo $ecidade_upstream {   # hash exato, O(1)
    default php56;
    include /etc/nginx/faseb_map.conf;
}
location / { proxy_pass http://$ecidade_upstream; }
```

Sete casos verificados: tela `amb`/`pre` de Tributário → 8.5; `/w/2/` → 8.5; tela `amb` que
**não** é de Tributário (`amb1_condicionante.RPC.php`) → 5.6; `cad` ainda não portado → 5.6;
prefixo da Fase A → 8.5; `login.php` → 5.6.

**Armadilha do gerador:** `\copy` é meta-comando do psql e **tem de caber em uma linha**.
Quebrado em várias, o psql falha — e a mensagem vem em **LATIN-1**, que o Python não
decodifica: o sintoma é `UnicodeDecodeError`, não erro de SQL. Mesma família da armadilha de
encoding do resto do projeto, num lugar novo.

### Denylist do Rector: 23 → 25 (QUARTA vez que ela cresce)

Duas regras novas dispararam em `amb`/`pre` e **as duas são perigosas**, por motivos distintos.

**1. `StrEndsWithRector`** — irmã da `StrStartsWithRector`, que já estava banida. Escapou só
por nunca ter disparado. Emite `str_ends_with()`, PHP 8.0; medido, **não existe no 5.6**.
Passa no `php -l` e é fatal só em execução — o modo de falha nº 2 do catálogo, de novo.

**2. `BinaryOpBetweenNumberAndStringRector`** — reescreve `$x == ""` para `$x == 0`. Medido
nos dois runtimes, **não reproduz o 5.6**:

| `$x` | 5.6 `== ""` | 8.5 `== 0` | |
|---|---|---|---|
| `""` | true | **false** | diverge |
| `"0"` | false | **true** | diverge |
| `"abc"` | false | false | ok |
| `0` | true | true | ok |

Essa categoria pertence ao `GuardaComparacaoLiteralRector`, que é fiel. A regra do Rector
chega perto e erra em dois dos seis valores — exatamente o tipo de regressão silenciosa que
o projeto existe para evitar.

**A conferência por módulo se pagou pela quarta vez.** Sem ela, um arquivo iria para a árvore
com `str_ends_with()` e outro com uma comparação que muda de resultado.

### CATEGORIA NOVA: a 5ª manifestação do `0 == ""` vive no `db_select()` do NÚCLEO

E foi achada do jeito mais difícil — **duas hipóteses minhas estavam erradas antes da certa**.

Sintoma: `pre4_configdbpref001.php`, HTTP 200 nos dois, 16 bytes de diferença. Um `<select>`
marcava `selected` em **duas** opções no 5.6 e em **nenhuma** no 8.5.

A linha, em `dbforms/db_funcoes.php:1055` (`db_select()`):

```php
@$GLOBALS[$nomevar] == key($db_matriz) || (@$GLOBALS[$nomevar] === "" && key($db_matriz) == 0)
                                                                         ^^^^^^^^^^^^^^^^^^^^
```

Com o global `""` e as chaves `'f'`/`'t'`:

```
              "f" == 0
PHP 5.6:      true    -> marca AS DUAS opcoes
PHP 8.5:      false   -> nao marca NENHUMA
```

Ironia útil: `key($db_matriz) == 0` **é** a guarda que o catálogo registra como acrescentada
para o caso `"" == 0` no `db_select()`. A guarda de ontem virou o defeito de hoje — ela
própria compara string não-numérica com `0`.

**Correção, medida em 9 valores com zero divergência:**

```php
key($db_matriz) == 0
  ->  (is_string(key($db_matriz)) && !is_numeric(key($db_matriz)) ? true : key($db_matriz) == 0)
```

#### As duas hipóteses erradas, e o que as desfez

Vale registrar porque o método é o achado:

1. **"É a linha 761"** — outro emissor de `<option>` no mesmo arquivo. Corrigi, e a bateria
   não mudou. A linha 761 usa o valor como rótulo; a tela mostrava "Não"/"Sim". **Revertida**,
   pela política de corrigir na aparição.
2. **"É a primeira comparação da 1055"** (`$GLOBALS[$nomevar] == key(...)`). Corrigi, e a
   bateria não mudou. **Revertida.**
3. **A sonda decidiu.** Imprimir `var_export()` do valor e da chave dentro do laço mostrou
   `val='' tipo=string key='f'` — o que elimina as duas primeiras hipóteses e aponta a
   segunda metade da expressão.

**Lição:** com três candidatos plausíveis no mesmo arquivo, instrumentar custa um minuto e
decide; deduzir custou duas rodadas de bateria e duas correções revertidas no núcleo.

#### ⚠ CORREÇÃO ao catálogo: é o ORIGINAL que executa, não a cópia do `modification/`

A sonda mostrou outra coisa que este arquivo afirma e não se confirma neste caminho. A seção
*CRÍTICO: `modification()`* diz que as cópias de `extension/modification/.../cache/user/dbseller/`
são as que executam. Para `dbforms/db_funcoes.php` chamado por `pre4_configdbpref001.php`,
**quem executou foi o original** — a sonda instalada na cópia não produziu saída nenhuma, e a
instalada no original produziu.

As duas cópias **diferem**. Mantive as duas corrigidas, que é o lado seguro, mas a afirmação
"a cópia é que executa" não vale para todo caminho e **precisa ser verificada caso a caso**,
não assumida.

### ⚠ CORREÇÃO ao catálogo: `pg_result()` sobre falso devolve NULL no 5.6, não `false`

A seção das guardas `pg_*` diz que "para `pg_result`, o 5.6 devolvia `false`". Medido:

```
PHP 5.6:  @pg_result(false, 0)  ->  NULL
```

A diferença importa sob `===`. A guarda aplicada em `pre4_liberaitbi002.php` usa `null`:

```php
pg_result($result,0,0)  ->  ($result ? pg_result($result,0,0) : null)
```

### CATEGORIA (pre): ternário aninhado sem parênteses — agora com correção medida

`pre3_logs001.php` era um dos **87 arquivos da base que só quebram no 8.5**. Duas ocorrências
de `a ? b : c ? d : e`, fatal de compilação desde o PHP 8.0.

A associatividade do 5.6 é **à esquerda** — confirmada no runtime: `1?"b":"c"?"d":"e"` devolve
`"d"`. Logo a correção fiel é `(a ? b : c) ? d : e`, e os três valores possíveis do campo
produzem saída idêntica nos dois runtimes depois dela.

**O `php -l` dirigiu a correção, e foi preciso:** corrigi a linha 91, reconferi, e o lint
apontou a **104**. Supor que a primeira era a única teria deixado o arquivo quebrado.

### Estado: MÓDULO `cad` (Cadastro) PORTADO ✅ — 2º lote da Fase B, e o maior salto de cobertura

O único módulo da área que estava em **zero telas** no 8.5. Depois dele, a área salta de
66,6% para **82,3%**.

**Decisão de escopo, medida:** o prefixo inteiro custaria **376** arquivos; o universo das
telas que o `map` de fato roteia custa **210**. Escolhi os 210 — os outros 166 seriam
pré-pagamento para Financeiro e Patrimonial, que não estão no escopo. Diferente de `amb`/`pre`,
onde portar tudo custava 57 e não valia a conta separada.

| | |
|---|---|
| Telas do prefixo em disco | 523 |
| **Telas roteadas (Tributário)** | **166** (162 existem em disco) |
| Universo das 7 frentes, a partir delas | 555 |
| Já pago | 413 |
| **Alterados** | **210** |
| `php -l` nos dois runtimes | **555/555, 0 erros** |
| Instanciação das classes | **201/202 idênticas** |
| Caminho de escrita | 2.049 linhas, **byte-a-byte idêntico** |
| **Bateria das telas roteadas** | **166/166** |
| Regressão nos 15 módulos roteados | **zero** |

Correções: 529 guardas `== <literal>`, 328 `split`/`ereg` → `preg_*`, 99 `parse_str`+`extract`,
82 construtores PHP 4, 8 `gettype`→`is_object` e 2 `(float)` (as duas últimas no núcleo).

### Denylist do Rector: 25 → 28 (QUINTA vez), e uma delas APAGAVA SQL

**`RemoveExtraParametersRector` é a regra mais perigosa encontrada até aqui.** Ela remove
argumentos quando a chamada passa mais do que a assinatura declara:

```php
// cad1_ruas003.php
$cllogradcep->excluir("","","j65_lograd=$j14_codigo");
->  $cllogradcep->excluir("","");          // o WHERE do DELETE SUMIU

// cad1_aba2ruas001.php
$cllogradcep->incluir($j14_codigo, $logs_split[$i]);
->  $cllogradcep->incluir();               // os dois argumentos do INSERT
```

**Medido: o PHP 8.5 ainda aceita argumentos extras** em função de usuário — `func_num_args()`
devolve 3 nos dois runtimes. Logo a regra **não é exigida pela versão de destino**; é limpeza,
e limpeza que apaga a cláusula `WHERE` de um `DELETE` em sistema de tributos.

As outras duas:

| Regra | O que fez | Veredito |
|---|---|---|
| `SensitiveConstantNameRector` | transformou a constante indefinida `l` em `\L` | muda o VALOR: no 5.6 a constante indefinida vira `"l"`, não `"L"` |
| `TernaryToElvisRector` | `($x)?$x:' '` → `$x ?: ' '` | equivalente, mas é modernização — fora do foco |

### CATEGORIA NOVA (cad): `gettype($x) == "resource"` — a variante que a varredura de `is_resource` NÃO pega

O catálogo já registra `is_resource()` sobre resultado do PostgreSQL. Esta é a **mesma falha
escrita de outro jeito**, e por isso escapou da medição de 237 ocorrências feita no `fis`:

```php
dbforms/db_funcoes.php:416   if (gettype($recordnsel) == "resource") {
```

```
             pg_query(...) -> gettype
PHP 5.6:     "resource"   -> laco roda, <option> saem
PHP 8.5:     "object"     -> laco NAO roda, o <select> vem VAZIO
```

Sintoma em `cad2_iptulancpago001.php`: HTTP 200 nos dois, 123 bytes a menos, e as três opções
`ZONA FISCAL 1/2/3` simplesmente ausentes. Nenhum fatal, nenhum log.

Escala medida na base: **8 ocorrências em 2 arquivos** — 4 sítios no `db_funcoes.php` mais a
cópia do `modification/`. Corrigidos os 4, porque 416 e 475 são as **duas metades da mesma
chamada** (`db_multiploselect` monta a lista disponível e a selecionada) e 927/984 são o par
equivalente em `db_selectmultiple`. Correção aditiva: `|| is_object($x)`, que não toca o
caminho do 5.6.

**Lição:** varrer por `is_resource` encontra uma grafia da categoria. A pergunta certa é
"quem mais testa o TIPO do resultado?" — e `gettype()` é a resposta que faltava.

### CATEGORIA (cad): a RFC de ordem no `db_inputdata()` do NÚCLEO

```php
dbforms/db_funcoes.php:1157   if (($db_opcao < 3) || ($db_opcao == 4)) {
```

Sondado em execução: `$db_opcao` vale **`'text'`** — uma string não-numérica.

```
             'text' < 3
PHP 5.6:     true    ("text" vira 0)   -> o seletor de data e emitido
PHP 8.5:     false   ("text" < "3")    -> o widget inteiro SOME
```

Em `cad1_ruas003.php` sumiam o `<script>` com `js_comparaDatasj14_dtlei` e o botão do
calendário — 542 bytes, HTTP 200 nos dois.

Correção `(float)$db_opcao < 3`, medida em 13 valores com **zero divergência**. A ocorrência
irmã em `db_ancora()` (linha 355) **não foi tocada**: não se manifestou, e vale a decisão de
corrigir na aparição.

### ⚠ ERRO MEU: transformação em massa dentro de string SQL quebrou 7 arquivos

O princípio deste arquivo diz "**nunca aplicar transformação em massa sem teste de
caracterização antes**". Eu violei, e o preço apareceu em um minuto.

Achei `trim(l)` em `classes/db_averbacao_classe.php` — constante indefinida, *notice* no 5.6
(vira a string `"l"`) e **fatal no 8.5**. Categoria legítima. Varri o universo por
`trim|strlen|strtoupper|...(bareword)`, achei 25 ocorrências, confirmei no runtime que
**nenhum** dos 18 nomes é constante definida, e apliquei aspas nas 25.

**Quebrou 7 arquivos, incluindo `libs/db_stdlib.php` do núcleo:**

```sql
-- o que meu regex "corrigiu":
where trim(funcao) = '" . trim(addslashes(...)) . "'
where trim("funcao") = '" . ...        <- aspas DENTRO de string PHP de aspas duplas
```

As 25 não eram PHP: eram **colunas de banco dentro de strings SQL**. Um regex que lê bytes não
distingue código de string — é a mesma limitação que o catálogo registra para comentários, e
que motivou adotar o Rector. Desfeitas as 25; `php -l` voltou a 555/555.

**Fica só a de `db_averbacao_classe.php`**, que é PHP de verdade (verificado no contexto:
`$sql .= ...` acima e `$this->erro_sql = ...` abaixo), corrigida para `trim("l")`.

**A lição não é "o regex é ruim"** — é que o teste de caracterização tem de vir **antes** da
aplicação, não depois. Rodar o `php -l` nos 555 arquivos custou 40 segundos e teria evitado
tudo, se eu o tivesse rodado em um arquivo antes de aplicar nos 7.

### ⚠ CORREÇÃO: o `map` do nginx É insensível a maiúsculas — emitir as duas grafias QUEBRA o proxy

O gerador emitia cada tela em duas grafias (minúscula e a do disco), por analogia com a
armadilha que obrigou o `location ~*`. O nginx recusou a configuração:

```
[emerg] conflicting parameter "cad4_emiteiptunovo.php" in faseb_map.conf:159
```

As duas linhas eram `cad4_emiteiptuNovo.php` e `cad4_emiteiptunovo.php`. O erro **prova** que
o `map` trata as duas como a mesma chave. Verificado depois: `/Cad1_averbacao002.php` em
maiúscula roteia para o 8.5 com uma única entrada minúscula no arquivo.

**Generalizando:** `location ~` é sensível a caso e exigiu o `~*`; `map` **não é**. Prevenir-se
da armadilha no lugar errado derrubou o proxy.

### FERRAMENTAL: o harness de classes agora sobrevive a fatal (`scratchpad/harness_robusto.sh`)

O `instancia_classes.php` processa a lista num processo só. **Um fatal mata o processo e o
resto da lista nunca é testado** — e, como os dois runtimes morrem no mesmo arquivo, o
resultado aparece como "idêntico".

Medido no `cad`: a lista tinha **202 classes** e a saída trazia **57**. Parava em
`classes/db_classecadastro.php`.

O invólucro roda o harness repetidamente: quando ele morre, registra o culpado, pula para o
seguinte e continua. Resultado: **201 de 202 idênticas**, com um único arquivo pulado — o
mesmo nos dois runtimes.

É a terceira vez que o instrumento de conferência precisa ser conferido (depois do
`serialize()` de `DOMElement` e do `grep` com aspas). **Saída truncada é indistinguível de
saída limpa quando não se conta o que entrou.**

### MÉTODO: como se decide o que é da área — e por que ROTEAR e PORTAR usam fontes diferentes

Registrado porque é o mecanismo central da Fase B, e porque os limites dele importam tanto
quanto o que ele resolve.

#### A fonte é o BANCO, não o código

```
atendcadarea  →  atendcadareamod  →  db_modulos  →  db_menu  →  db_itensmenu
   (área)          (área↔módulo)       (módulo)      (árvore)    funcao = NOME DO ARQUIVO
```

`db_itensmenu.funcao` guarda o nome do arquivo. Uma tela pertence a uma área quando existe
caminho até ela; a classificação é um `bool_or` sobre a junção:

```sql
bool_or(area LIKE 'TRIBUT%')      -- e da area
bool_or(area NOT LIKE 'TRIBUT%')  -- tambem e de outra
```

Exemplo real, que mostra as duas linhas para o mesmo arquivo:

```
  area          | modulo      | tela
  DB:FINANCEIRO | Caixa       | cai1_receita001.php
  DB:TRIBUTÁRIO | Arrecadação | cai1_receita001.php
```

#### Os três limites, medidos

| Prefixo | Em disco | No menu | **Fora do menu** | Menu → arquivo inexistente |
|---|---|---|---|---|
| `cad` | 523 | 193 (37%) | **330** | 9 |
| `cai` | 740 | 264 (36%) | **476** | 9 |
| `con` | 1.570 | 566 (36%) | **1.004** | 21 |
| `pro` | 387 | 134 (35%) | **253** | 0 |

1. **Só ~36% dos arquivos estão no menu.** Os outros 64% — popups, `.RPC.php`, subtelas —
   **não têm atribuição de área nenhuma** no banco. Para eles o mapeamento não responde.
2. **197 entradas fantasma** na base inteira: o menu aponta para arquivo que não existe.
   Defeito pré-existente do cadastro, não da migração.
3. **É dado, não código.** É o menu *desta* prefeitura. Outra instalação teria outra árvore —
   o gerador é reprodutível, a saída é específica da base.

#### A resolução: duas perguntas, duas fontes

| Pergunta | Fonte | No `cad` |
|---|---|---|
| **O que roteio para o 8.5?** | o menu do banco | 166 telas |
| **O que preciso portar?** | fecho de dependências, 7 frentes | 555 arquivos |

Os 330 arquivos do `cad` fora do menu **continuam servidos pelo 5.6**, mas **estão portados**:
a frente "citados em strings" os puxa a partir das telas roteadas, seguindo o `window.open` do
JavaScript. Funcionam nos dois runtimes, que é a invariante do strangler fig.

É por isso que a 3ª lacuna foi cara quando apareceu no ITBI: sem ela eu rotearia telas cujos
popups ninguém havia portado.

### ⚠ DECISÃO REVISTA: a bateria de regressão passa a ser PROPORCIONAL ao risco

A pergunta do usuário — *"é realmente necessária aquela bateria de regressão? se não mexeu nos
outros arquivos, para que verificar?"* — estava **certa em 198 dos 199 arquivos**, e produziu
uma correção de método.

Medido, cruzando os arquivos de cada lote com o universo dos módulos já verificados:

| Lote | Arquivos alterados | **No universo de módulo já verificado** |
|---|---|---|
| `cad` | 199 | **1** — `dbforms/db_funcoes.php` |
| `amb`+`pre` | 64 | **2** — o mesmo, mais uma `classes/` |

**A bateria de 1.898 telas nunca foi por causa do lote** — foi por causa de **um** arquivo.
Os outros 198 do `cad` não são executados por nenhum módulo anterior: ninguém mais os carrega.

Duas honestidades que o número expõe:

- **Em 15 execuções, a bateria de regressão cruzada nunca pegou uma regressão.** Sempre
  reportou linha de base. O valor dela até aqui foi **confirmatório**, não detetivesco.
- Ela só se justificou porque **quase todo lote acabou tocando o núcleo** — e um defeito no
  núcleo alcança as 1.898 telas, então aí a bateria larga é exatamente o teste certo.

**Regra que passa a valer** (custa ~3 segundos computar, contra ~25 minutos de bateria):

```
interseção = arquivos_do_lote  ∩  união(universos dos módulos já verificados)

vazia                      -> NÃO rodar bateria de regressão
só arquivos de um módulo   -> rodar a bateria DAQUELE módulo
arquivo do NÚCLEO          -> rodar a bateria COMPLETA
```

O núcleo, para este fim, é `dbforms/`, `libs/`, `std/`, `fpdf151/`,
`classes/db_cgm_classe.php` e a árvore `extension/modification/`.

**Ressalva que mantém o rigor:** a bateria completa continua obrigatória sempre que o núcleo
for tocado — e isso aconteceu em **todos** os lotes medidos até aqui, porque é lá que os
defeitos silenciosos vivem (`is_resource`, `gettype`, `db_select`, `db_inputdata`). A regra
não afrouxa a verificação: ela deixa de gastar 25 minutos quando a interseção é vazia, o que
até hoje nunca ocorreu, mas vai ocorrer nos lotes pequenos que não encostam no núcleo.

**Valor que fica, mesmo sem nunca ter pego defeito:** as 15 execuções com "zero regressão" são
a evidência de que migração incremental com dois runtimes **não degrada o que já foi migrado**.
Isso é resultado do trabalho, não só um portão de qualidade — e é o que o TCC de referência,
que fez big-bang, não tem como mostrar.

### Estado: MÓDULO `cai` (Caixa) PORTADO ✅ — 3º lote da Fase B

O prefixo com as **24 telas compartilhadas com Financeiro** e com as 3 em maiúscula
(`Cai1_recreparcori001/002/003.php`) — as duas armadilhas documentadas, num lote só.

| | |
|---|---|
| Telas do prefixo em disco | 740 |
| **Telas roteadas (Tributário)** | **101** |
| Universo das 7 frentes | 809 |
| **Alterados** | **150** (o prefixo inteiro custaria **539**) |
| `php -l` nos dois runtimes | **809/809, 0 erros** |
| Instanciação das classes | **462/462**, só os 3 artefatos conhecidos |
| Caminho de escrita | 12.863 linhas, 441 classes |
| **Bateria das telas roteadas** | **101/101** |
| Regressão | **não rodada** — ver a regra proporcional |

Correções: 360 guardas `== <literal>`, 272 `split`/`ereg` → `preg_*`, 64 construtores,
55 `parse_str`+`extract`, 4 guardas `pg_*`, 1 `in_array`, 1 `!= ""`.

**O Rector aplicou 6 regras, todas já vetadas — a denylist não cresceu pela primeira vez
desde o `amb`/`pre`.** Convergiu em 1 passada.

Os 3 artefatos do harness são exatamente os já registrados no `dvr`: `lancamentoContabil` e
`ordemPagamento` (`.model.php` com construtor obrigatório, o 5.6 morre e o 8.5 segue) e
`classes/empenho.php → datausu` (`'1969-12-31'` contra a data de hoje — a categoria
`date($fmt, null)`, que só se manifesta **sem sessão**, condição do harness e não de operação).

### CATEGORIA NOVA (cai): `in_array()` com *haystack* nulo

```
                     in_array("x", null)
PHP 5.6:             NULL    (warning, suprimivel)
PHP 8.5:             TypeError FATAL
```

Em `forms/db_frmarretipo001.php:859`, decidindo se uma caixa vem marcada:

```php
<?= (in_array($item->k195_sequencial, $aOperacoesSalvas) ? "checked" : "") ?>
```

`$aOperacoesSalvas` **nunca é atribuída** naquele caminho. Derrubava as três telas
`cai1_arretipo001/002/003` — ~15 KB a menos cada.

**Correção fiel:** `(is_array($h) && in_array($x, $h))`. Medido: no 5.6 o `in_array` devolve
`NULL` e `NULL ? "checked" : ""` dá `""`; a guarda devolve `false` e dá o mesmo `""`.

É a mesma família de `array_merge(null)`, `sizeof(null)` e `date(null)` — argumento inválido
que era *warning* e virou `TypeError`, com o `@` deixando de proteger.

**Escala no universo do `cai`: 74 ocorrências em 22 arquivos. NÃO varridas** — vale a decisão
de corrigir na aparição, reforçada pelo erro do `trim(bareword)` no `cad`.

### CATEGORIA (cai): o `0 == ""` na forma NEGADA, decidindo se emite JavaScript

Sexta manifestação da RFC, e a primeira em que o 8.5 produz **mais** saída que o 5.6 —
38 bytes a mais, não a menos.

```php
forms/db_frmarrevenc.php:235
if (isset($k00_numpar) && $k00_numpar != "") {
    echo " document.form1.k00_numpar.value = $k00_numpar; ";
}
```

Com `$k00_numpar = 0`:

```
             0 != ""
PHP 5.6:     false  -> NAO emite
PHP 8.5:     true   -> emite ` document.form1.k00_numpar.value = 0;`
```

Isso **preenche um campo do formulário com zero** no 8.5 onde o 5.6 o deixava intacto.

**Correção, medida em 9 valores com zero divergência:**

```php
$k00_numpar != "" && $k00_numpar !== 0 && $k00_numpar !== 0.0
```

**Nota de método:** as guardas que o catálogo registra são todas para `== ""`. Esta é a forma
`!= ""`, e o `GuardaComparacaoLiteralRector` **não a cobre** — ele casa só a comparação
positiva. Por isso escapou de todos os lotes anteriores e só a bateria byte-a-byte a achou.

### ✅ PRIMEIRA APLICAÇÃO da bateria proporcional — e ela se pagou

Computada a interseção do lote com os universos já verificados:

```
arquivos alterados no lote      127
arquivos do NUCLEO tocados        0
modulos cujo universo intersecta  nenhum
-> DECISAO: nao rodar bateria de regressao
```

Primeira vez em 16 lotes que o núcleo **não** foi tocado — e portanto a primeira vez que a
regra dispensa a bateria completa.

**Não aceitei a regra nova de olhos fechados na estreia.** Rodei três baterias baratas como
prova: `not` 14/14, `mar` 35/35, `inf` 30/30 — 79 telas, todas na linha de base, confirmando
a previsão da interseção.

Economia: ~25 minutos de bateria trocados por ~3 segundos de interseção mais 2 minutos de
amostra. E, mais importante que o tempo, a regra **explicita o motivo** de cada verificação
em vez de rodar tudo por hábito.

### Estado: `pro` · `con` · `prot` · `rec` · `dv` PORTADOS ✅ — e a ÁREA TRIBUTÁRIO FECHA

Lote final da Fase B: os cinco prefixos que faltavam, somando **71 telas**.

**É aqui que o escopo B se paga de forma decisiva.** Os prefixos inteiros custariam **1.483**
arquivos; o universo das telas efetivamente roteadas custou **109** — 13,6× menos. O `con`
sozinho custaria 1.019 arquivos para entregar 30 telas.

| | |
|---|---|
| Telas roteadas | **71** (`pro` 35, `con` 30, `prot` 4, `rec` 1, `dv` 1) |
| Universo das 7 frentes | 264 |
| **Alterados** | **109** (prefixos inteiros: 1.483) |
| `php -l` nos dois runtimes | **264/264, 0 erros** |
| Instanciação das classes | **106/106 idênticas** |
| **Bateria** | **71/71** |
| Regressão nos 15 módulos | **zero** |

Correções: 258 guardas `== <literal>`, 218 `split`/`ereg` → `preg_*`, 56 `parse_str`+`extract`,
40 construtores, 6 `${$var}`, 4 `break` → `exit`, 1 guarda `pg_*`.

### Denylist do Rector: 28 → 29 (SEXTA vez), e a regra contrariava uma decisão já medida

**`BreakNotInLoopOrSwitchToReturnRector`** converte `break;` fora de laço em `return;`. O
catálogo **já havia decidido essa categoria** na seção do `fis`, e contra ela:

```
PHP 5.6, break fora de laco:  imprime "antes " e MORRE
                              ("Cannot break/continue 1 level")
com `return;`:                o 8.5 volta e SEGUE -> comportamento novo
```

A correção fiel é **`exit;`** quando o `break` é alcançável; remover só equivale quando ele é
inalcançável. **A escolha depende da alcançabilidade, que a regra não analisa.**

Os 4 sítios (`con1_autoriza001.php`, `con1_edital002.php` ×2, `con1_edital003.php`) estão
todos dentro de blocos `if ($obj->erro_status == '0') { $sqlerro = true; break; }` —
**alcançáveis**, exatamente como `fis1_vistorias003.php`. Corrigidos para `exit;` à mão.

São três dos **87 arquivos da base que só quebram no 8.5**. E de novo o `php -l` dirigiu:
em `con1_edital002.php` ele apontou a linha 83, depois a 92 — e **não** apontou a 72, porque
aquele `break` está dentro de um `for` e é legal. A ferramenta distinguiu o que o olho não
distinguiria sem ler o bloco inteiro.

### Onde o Rector ganha do `porta.py`, agora com caso concreto

Este lote tinha **4 `split()` com separador não-literal** — a categoria que o `porta.py`
**abortava** e que o `jur` documentou como perigosa. O Rector converteu os quatro
corretamente:

```php
split(" +", $regs[2])   ->  preg_split("# +#m", $regs[2])    // POSIX "um ou mais espacos"
split("\|", $valores)   ->  preg_split("#\|#m", $valores)    // pipe escapado = literal
```

É a terceira vantagem da AST listada no experimento do `div`, aparecendo na prática.

### ⚠ A regra proporcional e a interseção medida DISCORDARAM — e vale registrar

```
arquivos alterados               108
NUCLEO tocado                      1  -> fpdf151/pdf4.php
modulos cujo universo intersecta   0  (vazio)
```

A regra manda **bateria completa** quando o núcleo é tocado; a interseção medida dizia que
**nenhum** módulo verificado executa aquele arquivo. Verificado: `fpdf151/pdf4.php` é incluído
por **um** arquivo em toda a base — `pro2_cartahabite002.php`, que está neste próprio lote.

**A interseção estava certa; a heurística "pasta inteira = núcleo" disparou demais.** Rodei a
bateria completa mesmo assim, por ser o lote que fecha a área — e deu linha de base nos 15.

**Refinamento para a regra:** o critério de núcleo deveria ser por **arquivo alcançado**, não
por pasta. `dbforms/db_funcoes.php` é carregado por tudo; `fpdf151/pdf4.php`, por um arquivo.
A interseção com os universos já mede isso corretamente — a lista de pastas é redundante e
mais conservadora do que precisa.

### 🏁 ÁREA TRIBUTÁRIO CONCLUÍDA — os números que resumem o trabalho

| | |
|---|---|
| **Módulos completos** | **16 de 16** |
| **Telas de menu servidas pelo PHP 8.5** | **1.056 de 1.056 (100%)** |
| Arquivos roteados | **2.160** — 1.813 por prefixo (`location`) + 347 por lista (`map`) |
| **Telas comparadas byte-a-byte** | **2.222 idênticas de 2.236 — 99,4%** |
| Divergências | **14**, todas caracterizadas, **nenhuma defeito de migração** |
| Baterias **perfeitas** | **12** — `div`, `mar`, `not`, `dvr`, `arr`, `tri`, `inf`, `amb`, `pre`, `cad`, `cai`, e o lote final |

Cobertura por módulo, todos em 100%:

```
ISSQN 182   Arrecadacao 172   Cadastro 170   Agua 109   Fiscal 97   Juridico 62
Divida 57   Cemiterio 43   Projetos 35   Contrib 31   ITBI 25   Notificacoes 25
Marcas 17   Diversos 15   Inflat 8   Meio Ambiente 8
```

Custo efetivo, por fase:

```
Fase A  13 prefixos exclusivos, roteados por `location`    ~2.113 arquivos alterados
Fase B   9 prefixos compartilhados, roteados por `map`       ~  909 arquivos alterados
         (os prefixos inteiros teriam custado 2.072)
```

**A decisão de escopo da Fase B economizou cerca de 1.160 arquivos** e evitou migrar
Contabilidade, RH e Patrimonial, que estão fora do escopo acordado.

**O que NÃO está feito, e precisa estar claro no relatório:** o 100% é de *telas de menu*. Os
dois terços de cada prefixo que vivem fora do menu — popups, `.RPC.php`, subtelas — continuam
servidos pelo 5.6. Estão **portados** (entram pelo universo das sete frentes) e funcionam nos
dois runtimes, mas não estão roteados. Rotear o resto exigiria estender o `map` com os
arquivos fora do menu, que o banco não sabe classificar por área.

### ⚠ 10ª LACUNA (15/10/2026): 11 telas de menu nunca entraram no `map` — o "100%" valia 1.048/1.059

Achada perguntando ao proxy, tela de menu por tela de menu, qual runtime responde
(`X-Ecidade-Runtime` em `http://localhost:8090/w/2/<tela>`), em vez de confiar nas listas.

**Causa:** em `db_itensmenu.funcao` a tela vem com parâmetro (`con1_manutexto.php?db_opcao=alvara_p1`,
`cad1_iptubase001.php?tipoImovel=1`). O `WHERE funcao ~ '\.php$'` do `gera_map_faseb.py` exigia que
o texto **terminasse** em `.php` e as descartava em silêncio. Só afeta o `map`: o `location` casa o
nome e ignora o parâmetro. Corrigido com `split_part(funcao,'?',1)` no `SELECT` e no `WHERE`.
A 11ª, `sys4_geradorteladinamica001.php`, tinha outra causa: o prefixo `sys` não estava em lista nenhuma.

As 11: `cad1_iptubaixa001`, `cad1_iptubase001/002`, `cad2_relatorios_001`, `cad3_conscadastronovo_001`,
`cai1_arrevenc002`, `cai2_relcaixa_001`, `cai4_baixabanco002`, `cai4_debcontapedaba002`,
`con1_manutexto`, `sys4_geradorteladinamica001`.

| Passo | Resultado |
|---|---|
| Universo (sete frentes, a partir das 11) | 101 arquivos, 48 já pagos |
| **Alterados** | **7** (Rector: 4 `ereg`/`split`, 3 guardas, 3 construtores, 2 `parse_str`, 1 offset `{}`); convergiu na 2ª passada, só regras vetadas |
| Remanescentes (contador por token) | 0 — os 2 de `db_db_config_classe.php` são o falso positivo já registrado |
| Portão de funções contra o 5.6 | 0 ausentes |
| `php -l` nos dois runtimes | 101/101 |
| Classes / caminho de escrita | 39/40 idênticas (a 40ª, `cl_iptuconstr_extends`, foge da convenção de nome do harness nos dois) / 1.516 linhas idênticas |
| **Bateria** | **13/13** sem parâmetro e **88/88 entradas de menu COM o parâmetro** |
| Regressão (interseção com `cad`/`con`/`pro`/`rec`) | `map` inteiro 347/347 |
| **Roteamento conferido pelo proxy** | **1.059 de 1.059** telas de menu existentes no 8.5 (7 entradas apontam para arquivo inexistente) |

Feito com as ferramentas do `scratchpad/` da branch `2educacao-migrado` (versões com TIMEOUT,
`PULAR` e o `re.I` da 9ª lacuna), copiadas para fora da árvore; o `enumera.py` recebeu as telas
por `TELAS=a.php,b.php`. O `paridade-56.ini` (criado na Educação) estava montado, como na linha de
base 2.154/2.160.

**Na Educação (`2educacao-migrado`), as 3 telas `mat1_matestoqueini001/002/003`** (abertas com
`?entrada=true`; também são do Patrimonial, então passam ao 8.5 para as duas áreas, como as `cai`
compartilhadas com Financeiro). Trazida a correção do gerador por *merge* da `1tributario-migrado`
(não rebase: as duas branches já estão publicadas). Universo 137, 94 já pagos, **4 alterados** (Rector:
3 guardas, 3 construtores, 3 `split`, 1 `parse_str`); `php -l` 137/137 nos dois; classes 87/87 (só o
artefato conhecido de `RequisicaoMaterial`); escrita 83 classes idênticas; bateria **6/6** (com e sem
`?entrada=true`); regressão pela interseção com `con` → 31/31. O `enumera.py` ganhou `TELAS=a.php,b.php`
para lotes que não são um prefixo.

**Lição, a décima da mesma família:** a conferência partia da lista que o gerador produziu. Quem
achou foi a conferência independente — perguntar ao sistema em execução, tela por tela.

### ⚠ 13ª LACUNA (21/10/2026, achada no RH): classes de `model/` carregadas por AUTOLOAD, sem `cl_`

A frente de autoload resolvia só `new cl_*` e `db_utils::getDao()` (as classes de `classes/`). Classes de
`model/` e `std/` usadas por `new Classe` ou `Classe::metodo()`, carregadas pelo autoloader sem nenhum
`include`, **não entravam em universo nenhum**. Achada porque o cálculo da folha morreu em
`AjustePrevidencia::…` (RH). Medido no universo verificado do Tributário: **580 arquivos** de `model/`/`std/`
alcançados e fora do universo — mas, por ser código OO mais novo, só **1** precisava de porte:
`model/diversos/ImportacaoDiversosCobrancaAdministrativa.model.php`, `split("#", …)` → `explode` (separador
literal, medido igual no 5.6). Nenhuma LSP nas 157 classes com `extends`. O fecho alcança também um modelo
da Educação (`unset($this)`), corrigido na branch dela.

**Os DAOs que os modelos instanciam (21/10/2026) — PORTADOS.** Com a 8ª frente no `enumera.py`, o fecho segue
dos modelos até `classes/`, e nas três áreas apareceram **316** arquivos não portados (361 menos 45 já pagos
por commits `EXPERIMENTO:`): **315 classes de dados** (`classes/db_<tabela>_classe.php`) e 1 tela
(`com1_pcmater002.php`). Domínios: 168 de Financeiro/Patrimonial (acordos, patrimônio, compras,
contabilidade…), 32 de configurações (endereços), 32 de Tributário, 28 de Educação, 24 de RH, 31 de outras
áreas. **Decisão do usuário: portar todos agora**, não na aparição — os 296 construtores PHP 4 só fazem
`rotulo`/`pagina_retorno` (falha visível), mas as **1.442 guardas `0 == ""`** faltando são a falha silenciosa,
que nunca "aparece". O que importa é a tela migrada alcançar a classe, não a área dona da tabela.

| | |
|---|---|
| Rector | 316 alterados, convergiu na 2ª passada; só regras já vetadas |
| Remanescentes (contador por *token*) | 0 em todas as categorias |
| Portão de funções / `?Tipo` | só `extract`/`preg_split` / nenhum |
| `php -l` | 316/316 nos dois runtimes |
| Classes (uma por processo) | 315/315 idênticas (a 316ª é a tela) — carregar todas no 8.5 também descarta LSP |
| Escrita | 7.432 linhas, **0 divergentes**, 1.678 campos lidos do POST |
| Regressão | interseção com os universos verificados vazia → sem bateria |

Feito nesta branch (a base) e levado por merge a `2educacao-migrado` e `3recursoshumanos-migrado`.

### ✅ NÍVEL 3 EM ESCALA — 18 telas roteadas, 14 módulos, zero divergências

O maior ponto fraco declarado do trabalho era este: **as 6.552 guardas `0 == ""` são 60% de
todas as correções, e só disparam no `POST`** — enquanto a bateria de 2.236 telas é toda
`GET`. O nível 1 (estado do objeto) as cobria em todos os lotes; o nível 3 (POST real,
comparando o SQL emitido) tinha rodado em **uma** tela.

Agora são **18**, cobrindo 14 dos 16 módulos:

```
agu arr cem div jur mar not tri cad cai fis inf iss itb
```

Cada uma submete o mesmo `POST` aos dois runtimes, com snapshot/restore entre eles, e compara
o `INSERT` de negócio campo a campo. **Zero divergências.**

#### FERRAMENTAL NOVO: `scratchpad/payload_auto.py`

O catálogo registrava que "o que limita o nível 3 é montar o payload, não o custo de
execução". Provado na prática: errei **duas vezes seguidas** antes de acertar uma tela —
inventei um nome de arquivo que não existe, e depois usei nomes de campo que não eram os reais
(`cm34_descr` em vez de `cm34_descricao`, `cm34_dtvalidade` em vez de `cm34_datalimite`).

A saída foi ler o formulário que o próprio 5.6 emite e gerar o esqueleto: nomes reais dos
campos, o botão de submit certo (ignorando os `dtjs_*`, que são seletores de calendário), as
opções de cada `<select>` e os `_dia`/`_mes`/`_ano` escondidos. Com ele, **18 das 28 telas
exercitaram de primeira**.

#### ⚠ A primeira rodada deu 5 DIVERGE — e as CINCO eram do instrumento

Vale registrar inteiro, porque é o padrão que se repete neste projeto.

**Defeito 1 — o parser engolia a linha de `ERRO:` do PostgreSQL.** A junção de continuação
colava qualquer linha seguinte ao statement, e as linhas de erro trazem timestamp e PID
próprios:

```
5.6> insert into advog(...) values ( 1 ,'1' ,'1' ) 2026-10-11 15:06:50.952 [8134] ERRO: ...
8.5> insert into advog(...) values ( 1 ,'1' ,'1' ) 2026-10-11 15:06:53.437 [8156] ERRO: ...
```

O `INSERT` é idêntico; divergia **só pelo relógio**. Corrigido distinguindo linha de log
(qualquer nível) de continuação de SQL. Isso sozinho levou 5 DIVERGE para 1.

**Defeito 2 — o nome da sequência não era casado.** O harness procurava só
`<tabela>_%_seq`, mas a convenção do e-cidade tem **três** formas:

```
cemiterioisencao_cm34_sequencial_seq    <tabela>_<campo>_seq
cem_legista_seq                         <modulo>_<tabela>_seq   <- a tabela no MEIO
<tabela>_seq
```

Sem restaurar a de `legista`, o segundo runtime recebia o número seguinte — `values ( 8 ...)`
contra `( 9 ...)`. **É exatamente a divergência benigna que o próprio catálogo previa**, e
que eu não tinha percebido estar acontecendo.

**Defeito 3, o pior — ele APROVAVA quando nada acontecia.** Com os dois lados vazios, imprimia
"SQL de escrita de NEGOCIO IDENTICO". Achado por acidente, ao rodar com um nome de tela
inexistente: 404 nos dois lados, zero statements, veredito positivo. Agora reporta
**`INCONCLUSIVO`** e sai com código 2.

**É a quarta vez que o instrumento de conferência precisa ser conferido** — depois do
`serialize()` de `DOMElement`, do `grep` com aspas e do invólucro que contava linhas de saída.
E o terceiro defeito é o mais grave de todos: *dá impressão de cobertura onde não houve
nenhuma*. Se eu tivesse rodado as 18 telas com o harness anterior e errado payloads, teria
entregue "18 telas verificadas" sem ter verificado nada.

#### ⚠ ERRO DE MÉTODO MEU: testei telas que NÃO estão roteadas

Duas divergências sobreviveram às correções, em `cad1_averba001.php` e `cad1_averbacgm001.php`.
Diagnóstico no 8.5:

```
ArgumentCountError: parse_str() expects exactly 2 arguments, 1 given
  em cad1_averba001.php:34
```

Um `parse_str` de 1 argumento **não portado**. Mas antes de chamar isso de defeito, conferi o
roteamento: **as duas telas não estão no `map`** — são servidas pelo 5.6, onde funcionam.
Testei código que nunca executa no 8.5.

Meu critério de seleção pegava "telas de inclusão por prefixo", não "telas roteadas". Das 33
testadas, **5 não estavam roteadas** e foram descartadas da contagem.

**O achado continua valendo, por outro motivo:** ele é a prova concreta de que a fronteira do
escopo B é real e está no lugar certo. Os arquivos `cad` fora do menu **não** foram portados,
e fatalariam se fossem roteados. O `map` é o que os mantém no runtime onde funcionam.

#### O que fica em aberto

Das 28 telas roteadas testadas: **18 exercitaram**, 6 voltaram `INCONCLUSIVO` (a validação
recusa antes do `INSERT` — payload automático insuficiente), 3 deram erro e 1 não tem
formulário no HTML inicial (é aba carregada por JavaScript).

As 10 que faltam precisam de payload montado à mão, lendo cada formulário. **É o custo que o
catálogo já previa, e ele é real:** ~2 a 4 telas por sessão de trabalho. O ganho marginal de
insistir nelas é baixo — 18 telas em 14 módulos, todas idênticas, já sustentam a afirmação
que faltava.

### ⚠ DECISÃO REVISTA: `tmp/` e `arquivos/` agora são 777

O texto anterior desta seção dizia que `tmp/`, `storage/` e `arquivos/` eram `775 diego`,
"não graváveis por nenhum dos dois containers", e que isso fora **deixado como está** porque
a falha igual nos dois "preserva a comparabilidade".

**O argumento estava errado e custou cobertura de teste.** `tmp/` é bind mount compartilhado e
os dois containers rodam como uid 33 — liberá-lo afeta os dois **igualmente**, exatamente como
deixá-lo travado. A diferença é que travado eles falham antes de executar.

Escala do que isso escondia:

| | |
|---|---|
| Telas da área Tributário que tocam o caminho de relatório | **211 de 1.813 (11%)** |
| Destas, nos três módulos já portados | **40 de 460 (8%)** |

Essas 40 apareciam como "idênticas" nas baterias, mas eram idênticas **no erro**:

```
itbi_situacao002    5.6=18.668 B  8.5=18.669 B   ambos: "Unable to create output file: tmp/..."
agu2_relconsumo002  5.6=18.681 B  8.5=18.681 B   idem
```

Comparabilidade sem cobertura — o tipo mais barato e menos útil de equivalência.

**Depois de `chmod 777 tmp arquivos`:** os relatórios passam a ser gerados de verdade (resposta
termina em `%%EOF`, PDFs reais aparecem em `tmp/`) e as três baterias foram refeitas:

| Módulo | Antes (tmp/ 775) | Depois (tmp/ 777) |
|---|---|---|
| `cem` | 114/116 | **114/116** |
| `itb` | 116/120 | **116/120** |
| `agu` | 222/224 | **222/224** |

**Zero regressões novas no 8.5.** O conjunto de divergências é exatamente o mesmo — o caminho
FPDF do núcleo está correto no PHP 8.5. O ganho não é ter achado defeito; é que agora **existe
prova** onde antes havia só ausência de prova.

`storage/` continua em 777 (necessário para o login do Laravel, ver seção própria).

**Efeito colateral previsto e verificado:** `dbforms/db_classesgenericas.php:522` usa
`tempnam("tmp/", "iframe")` — o `tmp/` **do projeto**, não o `/tmp` do sistema. Enquanto não era
gravável, o PHP caía no diretório temporário do sistema, que foi o que motivou o volume
`ecidade_tmp` compartilhado e a correção do loop infinito de iframes. Agora os temporários caem
no bind mount, que também é compartilhado. Verificado: `itb1_itbitransacao111.php` pelo `:8090`
responde **1 requisição, HTTP 200** (o loop devolvia milhares). O volume `ecidade_tmp` foi
mantido — outros pontos ainda usam o `/tmp` do sistema.

Reversível com `chmod 775 tmp arquivos`; nenhuma alteração de código.

### Estado atual: NÚCLEO PORTADO ✅

Os 24 arquivos do núcleo rodam em PHP 8.5. **A tela de login renderiza byte-a-byte idêntica
nos dois runtimes** (12.009 bytes; única diferença é o id aleatório do captcha).

```
antes:  8085 -> HTTP 500 (ParseError em libs/db_stdlib.php:149)
agora:  8080 -> HTTP 200 | 12.009 bytes
        8085 -> HTTP 200 | 12.009 bytes   <- idêntico
```

Alterações: **9 arquivos, ~70 linhas**. Nenhum fatal da aplicação no log do 8.5.

| Arquivo | Correções |
|---|---|
| `libs/db_stdlib.php` | 2 offsets `{}`, 11 `ereg_replace`→`preg_replace`, 1→`str_replace`, 1 `each`→`foreach` |
| `libs/JSON.php` | 40 offsets `{}` |
| `fpdf151/fpdf.php` | 3 offsets `{}`, remoção de `get_magic_quotes_runtime()` (variável morta) |
| `dbforms/db_classesgenericas.php` | 3 `split`→`explode` |
| `libs/db_libpessoal.php` | 1 `split`→`explode`, 2 `each`→ponteiro explícito |
| `std/DBString.php` | 1 `ereg_replace`→`str_replace` |
| `libs/db_calcula.php`, `libs/db_utils.php`, `classes/db_cgm_classe.php` | construtor PHP4 → `__construct` |

**Restrição descoberta na prática:** os dois containers montam o MESMO diretório, então toda
correção precisa funcionar em PHP 5.6 **e** 8.5. Isso é bom — força o código a ficar
version-agnostic antes de migrar, que é o pré-requisito do strangler fig. Todo arquivo
alterado passa `php -l` nos dois runtimes.

### Estado: MÓDULO PILOTO `tra` PORTADO ✅

96 arquivos (62 scripts da raiz, 13 `libs/`, 11 `classes/`, 10 `forms/`) — **todos passam
`php -l` em 5.6 E em 8.5**. Varredura final: zero construções removidas, zero construtores PHP4.

| Correção | Qtd |
|---|---|
| `split(` → `explode(` (todos com padrão literal `"#"` e `"\n"`) | 50 |
| construtor PHP4 → `__construct` | 23 |
| assinaturas incompatíveis com a classe pai (LSP) | 7 |
| `each(` → `foreach` | 3 |
| offsets `{}` → `[]` | 3 |
| `ereg(` → `preg_match(` | 3 |
| `=& new` → `= new` | 1 |
| `(double)` → `(float)` | 1 |

**Verificação funcional:** as 11 classes do módulo instanciam com estado **byte-a-byte idêntico**
nos dois runtimes (mesmo número de propriedades, mesmo md5 do estado inicializado). Isso valida
diretamente as 23 correções de construtor, que é a mudança de maior risco.

Limitação conhecida: as 62 páginas HTTP só puderam ser comparadas até a checagem de sessão
("Sessão inválida (12)"), idêntica nos dois. Verificação ponta a ponta com sessão autenticada
ainda está pendente — é o próximo passo natural do piloto.

### Estado: PILOTO `cem` (Cemitério) PORTADO ✅

**187 arquivos** — 113 scripts da raiz, 35 `classes/`, 33 `forms/`, 4 `funcoes/`, 1 `libs/`,
1 `model/` (os 24 do núcleo já estavam prontos; zero sobreposição com o `tra`).

| Correção | Qtd |
|---|---|
| `split(` → `explode(` (todas com padrão literal `"#"`) | 136 |
| construtor PHP4 → `__construct` | 36 |
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 198 |

Nenhuma outra categoria apareceu: zero `each(`, zero offsets `{}`, zero `ereg*`, zero
`=& new`, **zero violações de assinatura (LSP)** — as 7 do `tra` estavam todas no jpgraph,
que o `cem` não usa. Nenhum arquivo do `cem` é sobrescrito em `extension/modification/`.

Verificações (todas passaram):

| Critério | Resultado |
|---|---|
| `php -l` nos 187 arquivos, **nos dois runtimes** | 187/187 OK em 5.6 e em 8.5 |
| As 35 classes instanciadas via bootstrap da app | estado **idêntico** (mesmo nº de props, mesmo md5) |
| 113 páginas HTTP comparadas 5.6 × 8.5 | **113 idênticas, 0 divergentes** |
| Fatais no log durante o teste | nenhum |
| Roteamento no proxy | `/cem1_*` responde `X-Powered-By: PHP/8.5.10` |

### Verificação ponta a ponta do `cem` COM sessão autenticada

Metodologia que finalmente encontra defeitos reais: restaurar uma sessão válida antes de
cada requisição e comparar as 113 páginas byte-a-byte entre `:8080` (5.6) e `:8085` (8.5),
**normalizando identificadores aleatórios**. A lista completa de regras, cada uma nascida de
um falso positivo real:

| Regra | Por quê |
|---|---|
| `sid=<hex>` | id de sessão, muda a cada requisição |
| `arquivo=<base64>` | caminho do iframe temporário |
| `wname<n>` | nome da janela do desktop v3 |
| `iframe<rnd>.php` | temporário de `tempnam()` |
| `<hex de 32>` | md5 de nomes de arquivo |
| `tmp/<nome>.pdf` | PDF temporário: o nome carrega **PID e timestamp** |
| `localhost:8080` / `:8085` | a **página de erro** monta URL absoluta a partir de `HTTP_HOST` (ver `$DB_URL_ABS`), então carrega a porta do runtime que a serviu |
| `/CreationDate (D:…)` | data gravada dentro do PDF pelo FPDF; só passou a aparecer quando `tmp/` virou gravável e os relatórios começaram a ser gerados de fato |

**Normalizar não basta: é preciso CONFIRMAR antes de acusar.** Os relatórios carregam um
horário **dentro do fluxo comprimido** (`FlateDecode`) do PDF, fora do alcance de qualquer
regex. Se as duas requisições caírem em segundos diferentes, os bytes mudam — às vezes
mantendo o mesmo tamanho, o que faz a divergência parecer conteúdo diferente. O comparador
refaz o par uma vez antes de registrar: **uma regressão real é persistente, um flake não.**
Sem isso, `agu2_relconsumo002` aparecia e sumia entre execuções.

As duas últimas foram descobertas no `agu` e valem retroativamente: sem elas, telas de
relatório e telas de erro aparecem como divergentes de forma **intermitente**, porque só
divergem quando o PID ou o segundo do relógio mudam entre as duas requisições. Falso positivo
intermitente é o pior tipo — ele some quando se vai investigar.

**Teto de saída obrigatório no comparador.** Uma página com laço infinito (ver a categoria
`-1 >= ""`) devolve centenas de MB e o gerenciador de memória mata o comparador com SIGKILL,
sem traceback. O sintoma é a bateria morrer sempre no mesmo ponto e parecer travamento.
Truncar em ~5 MB resolve: a página truncada perde o marcador de status e cai como divergente,
que é o desfecho correto.

```bash
SID=<sessao com DB_modulo>   # achar com: grep -la DB_modulo /var/lib/php/sessions/sess_*
# restaurar a sessao antes de CADA requisicao: uma requisicao a consome/reescreve
docker exec -u root ecidade_php56 sh -c "cp /tmp/sess.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data ..."
curl -b "ECIDADEWINDOWMAIN=$SID" http://localhost:8080/<pagina>
```

Evolução: **14 divergentes → 4**, com 5 defeitos reais corrigidos no caminho.

| Defeito | Onde | Correção |
|---|---|---|
| `0 == ""` mudou (ver seção própria) | 35 classes do `cem` | 198 comparações |
| `parse_str()` com 1 argumento (obrigatório desde 8.0) | 62 arquivos do `cem` | `parse_str($s,$a); extract($a);` |
| `pg_numfields(false)` → TypeError | `db_fieldsmemory()` no núcleo | retorno antecipado |
| `pg_result(false)` → TypeError | `db_stdlib` 2×, `db_libsys` 1× | operador ternário |
| `"" == 0` no `db_select()` | `dbforms/db_funcoes.php` (núcleo) | condição extra para string vazia |

**Divergências restantes: 2 — 114 de 116 idênticas.**

- `cem1_itenserv002.php` — **quebra no 5.6 (500) e funciona no 8.5 (200)**. Defeito
  pré-existente da referência (`label() on null` em `forms/db_frmitenserv.php:29`), não da migração.
- `cem2_emitecertisen002.php` — ambos falham ao gerar o relatório e redirecionam para a
  **mesma** mensagem; o 5.6 emite antes um `<b>Mensagem: </b>` vazio. Causa: o diálogo de erro
  do `dbagata/`, cujos construtores PHP 4 não rodam no 8.5. Ver *5ª LACUNA*.

`cem3_sepultamentos004.php` e `cem2_renovacoes.php`, antes divergentes, ficaram **idênticas**
— foram resolvidas pelas guardas `pg_*` acrescentadas ao núcleo depois.

### PENDÊNCIA DE DECISÃO: 140 chamadas `pg_*` sem verificação no núcleo

O padrão `$r = db_query(...); pg_numrows($r);` sem checar `$r` é sistêmico. No 5.6 passava
`false` adiante e a função devolvia `false` (que `== 0`); no PHP 8 é `TypeError` fatal.

**⚠ CORREÇÃO (medida depois do `arr`): a causa NÃO é tabela vazia.** Este arquivo registrava
que o defeito "ocorre sempre que a consulta traz zero linhas". Está errado — verificado nos
dois runtimes:

```
consulta VALIDA com zero linhas  ->  resultado normal, pg_numrows() = 0
SQL INVALIDA                     ->  false
```

`pg_query()` só devolve `false` quando **a própria SQL falha**. Os ~112 pontos guardados ao
longo de 11 módulos não são tabelas vazias: são **consultas quebradas**, defeitos
pré-existentes que o 5.6 engolia. Exemplo real, de `arr2_rellistadqd002.php`:

```
ERRO: coluna "declaracaoquitacao.ar30_exercicio" deve aparecer na clausula GROUP BY
```

Esse `GROUP BY` malformado erra no PostgreSQL **independentemente da versão do PHP**; a única
diferença é que o 5.6 passa o `false` adiante e o 8.5 fatala.

| Arquivo do núcleo | Chamadas não protegidas |
|---|---|
| `libs/db_stdlib.php` | 86 |
| `dbforms/db_funcoes.php` | 24 |
| `dbforms/db_classesgenericas.php` | 19 |
| `libs/db_libsys.php` | 11 |
| **Total** | **140** |

Na base inteira: **100.814 chamadas `pg_num*`/`pg_result` sobre variável, em 7.885 arquivos**.

**DECISÃO TOMADA: corrigir conforme os defeitos aparecerem, não em massa.**

Foram corrigidos apenas os pontos que quebraram de fato (4 dos 140). A varredura em massa
(`pg_numrows($x)` → `($x ? pg_numrows($x) : 0)`) foi **descartada deliberadamente**: mexeria
em ~136 pontos sem evidência de que precisavam mudar, e traz risco próprio — para
`pg_result`, o 5.6 devolvia `false` e o substituto devolveria `""`, equivalente sob `==` mas
**não** sob `===`. Uma regressão silenciosa introduzida ao tentar prevenir outra.

O procedimento é: página quebra → ler `extension/log/error.log` → corrigir aquele ponto →
rodar a bateria das 113 páginas para confirmar que nada mais mudou. Os números acima ficam
registrados como estimativa de esforço restante, não como lista de tarefas.

#### ✅ A decisão de não varrer em massa, agora MEDIDA

A pergunta "não dá para automatizar isso?" foi levantada e medida, em vez de respondida por
hábito:

| | |
|---|---|
| Chamadas `pg_num*` sem guarda no universo do `arr` | **1.083** em 526 arquivos |
| Quantas de fato precisaram de guarda | **1** |
| Idem no `dvr` | 685 no universo, 4 necessárias |
| `pg_result`/`pg_fetch_result` na base inteira | **84.077** — 81% do total |
| **Risco da varredura** (resultado comparado com `===` a jusante) | **25 pontos na base** |

A taxa de acerto de uma varredura seria de **~0,1%**. E o risco é concreto, não teórico: em
`con2_razaodespesa002.php:170` há `if ($rows === 0)`. Com a guarda devolvendo `0`, a condição
passa a ser verdadeira onde no 5.6 (`false === 0`) era falsa. **Varrer em massa introduziria
regressão em 25 pontos para prevenir cerca de um por módulo.**

#### ✅ O que DÁ para automatizar: a descoberta, pelo log do PostgreSQL

Como toda falha é erro de SQL, **o PostgreSQL já registra todas**. Uma passada da bateria com o
log capturado lista todos os pontos de uma vez, em vez de descobrir um por rodada:

```bash
docker logs --since 20m ecidade_database 2>&1 | grep -aA1 'ERRO:'
```

**O log está em PORTUGUÊS** (`ERRO:` / `INSTRUÇÃO:`), por causa do locale `pt_BR.ISO-8859-1` do
cluster. Um `grep 'ERROR:'` não acha nada — e falha em silêncio, como as outras armadilhas deste
arquivo. `log_min_error_statement` já vem em `error` e `logging_collector` está `off`, então os
erros saem no stderr do container; não é preciso configurar nada.

Validado ponta a ponta: revertendo a guarda de `arr2_rellistadqd002.php`, a tela volta a dar 500
no 8.5 e o log aponta a consulta exata.

**Ganho medido:** isso troca N rodadas de bateria por 1. O custo real do método nunca foi o
número de guardas, e sim a iteração — `fis` precisou de 2 rodadas, **`iss` de 4**, `dvr` e `arr`
de 1.

**Deixado intencionalmente sem tocar:** `libs/db_libsys.php:180` usa
`session_is_registered("DB_NBASE")`, função removida no PHP 5.4 mas **polyfilled** por
`vendor/dbseller/legacy/bootstrap/PHP_53.php`. Funciona igual nos dois runtimes; alterá-la
seria mudança de comportamento, não migração.

Pendente: validação ponta a ponta no navegador com sessão autenticada, navegando o menu
Cemitério em `http://localhost:8090`.

### Estado: MÓDULO `itb` / `itbi` (ITBI) PORTADO ✅ — 2º da área Tributário

**192 arquivos** — 120 scripts da raiz, 42 `classes/`, 30 `forms/`.

Atenção ao prefixo: o módulo usa **`itb` E `itbi`** (`itb1_*` 110 arquivos, `itbi_*` 10).
Enumerar só `^itb[0-9]*_` deixaria 10 de fora. Regex correta: `^itbi?[0-9]*_` com IGNORECASE.

| Correção | Qtd |
|---|---|
| `split(` → `explode(` (literais `"#"`, `"X"`, `","`, `'-'`) | 143 |
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 264 |
| `parse_str()` com 2º argumento | 54 |
| construtor PHP4 → `__construct` | 36 |
| guardas `pg_*` contra resultado falso | 14 |
| cast `(float)` em aritmética com string | 2 |

Verificações: `php -l` **192/192 nos dois runtimes**; as 42 classes instanciam com estado
idêntico; **116 de 120 telas byte-a-byte idênticas** com sessão autenticada (era 113 antes
das correções de autoload e das guardas do núcleo).

**Zero páginas quebrando no 8.5.** As 2 divergências restantes **quebram no 5.6 e funcionam
no 8.5** — `itb1_itbiavalia002/003` e `itb1_itbidadosimovel003`/`itb1_itbinome011`, todas com
`label() on null` nos `forms/db_frmitbi*.php`: defeito pré-existente da referência, não da
migração. Mesmo padrão visto em `cem1_itenserv002`.

As 3 que estavam "sem caracterização" foram resolvidas: `itbi_simulacaoitbi002` e
`itbi_tipotransacoes002` ficaram **idênticas**, e `itbi_situacao002` era **falso positivo do
comparador** — o nome do PDF temporário (`tmp/rp<pid>_<timestamp>.pdf`) muda a cada
requisição. Os dois runtimes falham igual ali, por `tmp/` não ser gravável.

Sete guardas `pg_*` foram acrescentadas ao núcleo durante este módulo (`db_stdlib` linhas
2017 e 2600 e adjacências, `db_utils` linhas 70 e 185) — sempre replicadas na cópia do
`extension/modification`. Cada uma nasceu de um defeito observado, conforme a decisão
registrada de não varrer em massa.

### ARMADILHA DE DIAGNÓSTICO: tabelas vazias no banco de exemplo

**Já gerou dois alarmes falsos de migração.** O banco de exemplo tem várias tabelas dos
módulos portados sem nenhum registro:

```
itbi                 0        itbitransacao       10
sepultamentos        0        itbiformapagamento   5
ossoario             0        causa                3
renovacoes           0        campas               2
legista              0        cemiterio            1
funerarias           0
```

Uma tela que consulta tabela vazia pode falhar de **duas formas muito diferentes**, e
distinguí-las é o que separa dado de defeito:

**1. Vazio TRATADO — não é defeito.** O código verifica `numrows` e emite mensagem de
negócio. Comporta-se **igual nos dois runtimes**, que é exatamente o critério de migração
fiel. Exemplo: `reciboitbi.php:184` (ITBI → Relatórios → Emite Guia):

```php
$rsItbi = $clitbi->sql_record($clitbi->sql_query(null, "*", null,
    "it01_guia = {$itbi} and it01_coddepto = " . db_getsession("DB_coddepto")));
if ($clitbi->numrows == 0) {
  $sMensagemErro = 'ITBI não encontrada para o departamento!';
```

Com `itbi` vazia, qualquer guia informada cai nesse ramo. O `:8080` e o `:8085` devolvem
**4.048 bytes idênticos**. Nada a corrigir.

**2. Vazio que vira FATAL — é regressão.** O código passa o resultado falso adiante para
`pg_*`, que o 5.6 tolerava e o PHP 8 rejeita com `TypeError`. Foi a causa das 8 telas do
Cemitério que quebravam só no 8.5, e das guardas que fomos acrescentando ao núcleo.

> **Ressalva medida depois do `arr`:** este caso 2 **não é causado por tabela vazia**. Consulta
> válida sobre tabela vazia devolve resultado normal com `numrows = 0`. O `false` vem de **SQL
> inválida** — ver a correção na seção das guardas `pg_*`. A coincidência com tabelas vazias
> neste banco é real, mas o mecanismo é outro.

**Variante: a tabela com UMA linha, e ela é justamente o valor óbvio de teste.** Terceiro
alarme falso vindo dos dados deste banco. Em *Jurídico → Advogados → Inclusão*, a inclusão
recusa o CGM 1 dizendo que já existe. Está correto: `advog` tem **uma única linha**, e é o
CGM 1. A tabela tem `PRIMARY KEY (v57_numcgm)` e `FOREIGN KEY → cgm(z01_numcgm)` — a FK é por
que só se aceita CGM existente, e a PK é por que o 1 é recusado. O banco inteiro tem **3 CGMs**
(1 ocupado, 19 e 20 livres), então o valor mais natural de testar é exatamente o que falha.

A mensagem nem vem do PHP: é a violação de unicidade do PostgreSQL, repassada por
`erro_banco`. Comprovável sem alterar dado, com transação revertida:

```sql
BEGIN;
INSERT INTO advog VALUES (19,'OAB123','M1');   -- INSERT 0 1        (aceito)
SAVEPOINT s1;
INSERT INTO advog VALUES (1,'OAB999','M2');    -- viola advog_numc_pk
ROLLBACK TO s1; ROLLBACK;
```

**Limite da bateria de comparação, que isto expõe:** ela faz só `GET`. Caminhos de escrita —
inclusão, alteração, exclusão — **não são exercitados**, então 144/145 telas idênticas não
dizem nada sobre o `incluir()` das classes. É por isso que estes casos aparecem quando o
usuário navega, e não nas verificações automatizadas.

**Como distinguir, em um passo:** reproduzir a mesma tela no `:8080`.

| Resultado | Conclusão |
|---|---|
| Falha **igual** nos dois | dado ausente ou defeito pré-existente — **não mexer** |
| Falha **só no `:8085`** | regressão de migração — ler `extension/log/error.log` e corrigir |

Corolário para a validação: uma tela "sem erro" cuja tabela está vazia **não foi exercitada
de verdade**. A bateria de comparação prova equivalência entre runtimes, não que o caminho
de dados foi percorrido. Para exercitar de fato é preciso cadastrar registros pelo próprio
sistema.

### Estado: MÓDULO `agu` (Água) PORTADO ✅ — 3º da área Tributário

**224 telas**, enumeradas por `^agua?[0-9]*_` com `re.IGNORECASE`. Atenção ao prefixo: além
de `agu1_`…`agu4_` o módulo tem três arquivos `agua_*.RPC.php`. Uma regex `^agu[0-9]*_` os
deixaria de fora — é a mesma armadilha do `itb`/`itbi`.

| Correção | Qtd |
|---|---|
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 895 |
| `split(` → `explode(` | 285 |
| `parse_str()` com 2º argumento | 83 |
| construtor PHP4 → `__construct` | 74 |
| guardas `pg_*` contra resultado falso | 18 |
| cast `(float)` em aritmética com string | 4 |

Verificações: 171 arquivos alterados passam `php -l` **nos dois runtimes**; **222 de 224
telas byte-a-byte idênticas** com sessão autenticada.

As 2 restantes **não são telas** — são fragmentos de include, ausentes do menu, que nenhuma
navegação requisita diretamente. `agu1_aguaconsumo999.php` é um fragmento de DBtxt incluído
por `agu1_aguaconsumo001/002/003`; `agu4_cancelaleituras_classe.php` define
`cl_cancelaleituras` e é incluído por `agu4_expdadoscoletores_003.php`. O 500 no 8.5 é
artefato do harness, que requisita *todo* arquivo do prefixo.

### CATEGORIA NOVA (agu): argumentos faltando viram fatal

```php
function db_fieldsmemory($recordset, $indice, ...)   // $indice e OBRIGATORIO
...
db_fieldsmemory($resultano);                          // chamada com 1 argumento
```

No PHP 5.6 isso era *Warning: Missing argument 2* e o parâmetro virava `null`; no PHP 8 é
**`ArgumentCountError` fatal**. Escala na base inteira: **4 ocorrências em 3 arquivos**
(`agu2_agualancpago001.php` ×2, `cai4_processadebconta001.php`, `mat2_controlest002.php`).
Corrigidas só as 2 do módulo, conforme a decisão de corrigir na aparição.

Correção: passar explicitamente o valor que o 5.6 produzia. Aqui é `0` — `pg_result()`
coagia o `null` do argumento ausente para a linha 0 —, o que além de fiel evita a
deprecation de `null` em parâmetro inteiro introduzida no PHP 8.1.

### CATEGORIA NOVA (agu): comparação de ORDEM entre número e string — LAÇO INFINITO

A RFC "Saner string to number comparisons" já estava catalogada aqui na forma `==`. **Ela
também mudou `>=`, `<=`, `>` e `<`**, e nessa forma o modo de falha é muito pior.

```
              -1 >= ""
PHP 5.6:      false     (a string vira numero: -1 >= 0)
PHP 8.5:      TRUE      (o numero vira string: "-1" >= "")
```

Manifestação real: a tabela `aguacalc` está **vazia**, então `$anoini`/`$anofim` ficam `""`,
e o idioma do e-cidade para montar um `<select>` de exercícios é

```php
for ($i = $anoini; $i >= $anofim; $i--) {
    echo "<option value=$i>$i</option>\n";
}
```

No 5.6 o laço dá **uma volta** e para (`""--` vira `-1`, e `-1 >= ""` é false). No 8.5 ele
**nunca termina**: a página passou de 200 MB e o comparador foi morto com SIGKILL pelo
gerenciador de memória. Observado contando até `-54590`.

**Isto não é dado errado — é exaustão de memória no servidor.** É o argumento mais forte do
catálogo contra confiar em varredura estática: o código é válido nas duas versões, o defeito
depende do estado do banco em tempo de execução, e a falha é de disponibilidade.

Correção: `(float)$i >= (float)$anofim`, que restaura a comparação numérica nos dois
runtimes. O módulo inteiro tem **apenas 2 laços decrescentes**, ambos corrigidos — os outros
82 laços comparam com `sizeof()`/`numrows`, que são numéricos e não correm risco.

### CATEGORIA NOVA (agu): `fputs`/`fclose` sobre handle falso

`model/configuracao/DBLogTXT.model.php` guarda o retorno de `fopen()` e o usa sem verificar.
Quando o diretório não é gravável — a assimetria de permissões pré-existente deste ambiente —
o handle é `false`. No 5.6 era warning e a execução seguia; no PHP 8 é `TypeError` fatal e a
página é **truncada no meio** (198.643 bytes no 5.6 contra 67.267 no 8.5).

É a mesma família das guardas `pg_*`: valor falso repassado a função que passou a checar tipo.
Corrigido com a guarda que reproduz o retorno do 5.6 (`false`).

### 4ª LACUNA: classes carregadas por AUTOLOAD não aparecem em nenhum `include`

`libs/db_autoload.php` registra `spl_autoload_register('db_autoload')`, que carrega as classes
`cl_*` **sem nenhuma declaração de include**. O fecho transitivo de dependências não as vê, e
a enumeração por prefixo também não — elas ficam em `classes/`.

Impacto medido, e ele alcança módulos que eu já havia declarado concluídos:

| módulo | classes não portadas | com construtor PHP4 |
|---|---|---|
| `agu` | 57 | 4 |
| `itb` | 4 | 3 ← módulo declarado pronto |
| `cem` | 2 | 1 ← módulo declarado pronto |

As 62 foram portadas (30 `split`, 8 construtores, 463 comparações `== ""`), e as baterias de
`cem` e `itb` foram refeitas depois.

**Passo a acrescentar à receita:** para cada script do módulo, resolver também os nomes de
classe `cl_*` instanciados (`new cl_x`) e conferir se o arquivo correspondente em `classes/`
entrou na lista.

### 5ª LACUNA: `dbagata/` nunca foi enumerado — e o NÚCLEO o alcança

`std/db_stdClass.php` (núcleo) chama `$api->parseOpenOffice(...)`, que vive em
`dbagata/classes/core/AgataAPI.class`. Ou seja, `dbagata/` está no fecho de dependências do
núcleo e deveria ter sido portado com ele. **Não foi.**

Medição por `php -l` nos dois runtimes sobre os 216 arquivos de `dbagata/`:

| | Arquivos com erro de sintaxe |
|---|---|
| PHP 5.6 | 5 (pré-existentes) |
| **PHP 8.5** | **16** |
| **Só quebram no 8.5** | **11** |

Os 11: `classes/fpdf151/fpdf.php`, `classes/fpdf151/teste.php`, `classes/util/nusoap.php`,
`classes/util/editor.class`, e sete do `jpgraph` (`gd_image.inc.php`, `jpgraph.php`,
`jpgraph_gantt.php`, `jpgraph_pie.php`, `jpgraph_plotmark.inc.php`, `jpgraph_radar.php`,
`jpgraph_spider.php`). Causa dominante: `=& new`, que é *parse error* no PHP 7+.

Categorias medidas em `dbagata/`: 61 `ereg*`, 22 offsets `{}`, 18 `=& new`, 9 `split(`,
8 `magic_quotes`, 5 `each(`, 1 `create_function(`, e **224 classes com apenas construtor
PHP 4, em 114 arquivos**.

**REFINAMENTO (após liberar `tmp/` e rastrear a alcançabilidade): dos 11, apenas 1 importa.**

Rastreando os includes a partir de `libs/db_libsys.php:108` (`class cl_dbagata`):

| Caminho | Arquivos de `dbagata/` carregados | Algum dos 11? |
|---|---|---|
| `parseOpenOffice` — usado pelo núcleo em `std/db_stdClass.php` | ~22 | **nenhum** |
| `generateReport` — `cl_dbagata` faz `setFormat('pdf')` por padrão | +`reports/AgataPdf.class` | **sim**: `AgataPdf.class:40` inclui `dbagata/classes/fpdf151/fpdf.php` |

Os outros 10 são **inalcançáveis**: jpgraph só entra por `AgataGraph.class` (via
`generateGraph()`, que **nenhuma tela do e-cidade chama**), e `nusoap.php`/`editor.class` só
por `AgataInterface.class`, a GUI GTK do Agata, que **nada no repositório inclui**.

Quem chama `generateReport()` (24 call sites fora de `dbagata/`), por módulo:

```
orc 7   iss 4   cai 3   sys 2   pes 2   pro 1   con 1   model 1
```

**Nenhuma das 460 telas de `cem`+`itb`+`agu` está nessa lista** — por isso as baterias passam
limpas mesmo com `tmp/` liberado. Mas **`iss` está**, com 4 call sites.

**Consequência prática: `dbagata/` não é urgente agora, e é pré-requisito duro do `iss`** —
o último e maior módulo da área (400 arquivos). Portá-lo antes do `iss` evita descobrir o
problema no módulo mais caro.

> **RESOLVIDO.** O `dbagata/` foi portado — ver *Estado: BIBLIOTECA `dbagata/` PORTADA*. Os 11
> arquivos que só quebravam no 8.5 passam `php -l` nos dois runtimes, o pipeline de relatório
> gera **PDF byte-a-byte idêntico**, e `cem2_emitecertisen002.php` — a divergência que esta
> seção previa — ficou idêntica. O refinamento acima estava certo no diagnóstico e **errado na
> contagem do que importava**: não era 1 arquivo alcançável, era a cadeia inteira de
> construtores PHP 4 do diálogo de erro.

Nota: existe um jpgraph **fora** do dbagata, em `libs/jpgraph/` (versão 1.14, contra 1.26.1-dev
do dbagata — são versões diferentes, não cópias). Esse já foi portado no commit `04159b411`.

### 6ª LACUNA: `fpdf151/` do núcleo tem 28 arquivos não portados

O `CLAUDE.md` lista `fpdf151/fpdf.php` e `fpdf151/pdf.php` entre os 24 arquivos do núcleo.
**A pasta tem 194 arquivos**, e eu portei dois.

Medição (`php -l` nos dois runtimes + varredura byte-a-byte):

| | |
|---|---|
| Arquivos em `fpdf151/` | 194 |
| Erro de sintaxe no 5.6 | 0 |
| **Erro de sintaxe no 8.5** | **4** — `impmodelos/mod_imprime{10,12,13,1333}.php` |
| `split(` | 23 ocorrências em 22 arquivos |
| `each(` | 20 em 4 — `pdf1.php`…`pdf4.php` |
| construtor PHP 4 | 4 |
| offsets `{}` | 4 |
| **União a portar** | **28 arquivos** |

`each()` **não aparece no `php -l`** — é fatal só em execução (`Call to undefined function`).
Por isso os 4 arquivos com `each()` passam no lint e quebrariam na tela.

Alcance: `fpdf151/pdf1.php` é incluído por 25 arquivos, `pdf3.php` por 8, `pdf2.php` por 6;
`impmodelos/` é usado por `pes2_analitica002.php`, `pes1_cfpess002.php` e
`pes2_termorescisaomodimprime80.php` — todos do módulo **Pessoal**, ainda não portado.

**Lição, a mesma das cinco anteriores:** a lista do núcleo foi montada pelo grafo de
dependências, que enxerga o que é incluído *estaticamente pelos módulos analisados*. Uma pasta
de biblioteca entra no núcleo pelos dois ou três arquivos que o grafo viu, e os outros 192
ficam invisíveis — até que um módulo que os usa seja portado.

Defeito concreto já observado: em `cem2_emitecertisen002.php`, o 5.6 emite
`<b>Mensagem: </b>` (o diálogo de erro do dbagata) e o 8.5 não. Renomear os construtores de
`MemoArea` e `AgataQuery` **não** resolveu — a cadeia real passa por mais classes —, então as
duas alterações foram revertidas para manter o commit do `agu` cirúrgico. `dbagata/` é um
lote próprio, a ser portado com verificação própria.
