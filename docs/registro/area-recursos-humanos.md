# Área Recursos Humanos (e a 14ª lacuna, achada nela)

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

### 📐 ÁREA RECURSOS HUMANOS — dimensionada e INICIADA (branch `3recursoshumanos-migrado`)

4 módulos no banco: Pessoal 507 telas, RH 138, eSocial 39, Estágio Probatório 26. Os
prefixos principais são praticamente exclusivos da área:

| Prefixo | Telas de RH no menu | Em outra área | Em disco | A alterar (prefixo inteiro) |
|---|---|---|---|---|
| `pes` | 499 | 2 (Financeiro) | 1.155 | 684 |
| `rec` | 159 | 3 (Assist. Social) + 1 (Tributário, já no `map`) | 279 | 147 |
| `eso` | 33 | 3 (Integrações) | 85 | 27 |
| `rh` | 4 | — | 9 | 2 |
| `es`, `con`, `cai`, `lic`, `sped` | ~10 | compartilhados | — | via `map` |

**Escopo, o mesmo das duas áreas anteriores:** Fase A = `pes`/`rec`/`eso`/`rh` inteiros
(1.528 arquivos, universo 2.687, ~826 a alterar), roteados por `location`; Fase B = as ~10
telas compartilhadas, pelo `map`. Ordem: `rh`+`eso` → `rec` → `pes` (em sublotes).

**Nível 3 e a folha:** a base de exemplo tem **1 servidor** (`rhpessoal`), 3 funções, 2
lotações e **zero** linhas de cálculo (`gerfsal`, `gerfcom`, `gerfres`) e de ponto (`pontofs`,
`pontofx`). Decisão do usuário: nível 3 nos **cadastros** durante o porte; o cenário de
**cálculo** (cadastrar servidores e ponto pelo 5.6 e comparar o SQL do cálculo) fica como etapa
separada, ao fim da área. Atenção: o banco não tem volume de persistência — o cenário teria de
ser salvo em dump.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| `rh`+`eso` | 239 | 29 (Rector, 1 passada + confirmação) | 239/239 | 74/74 | 2.213 linhas, 53 classes, 0 div. | **94/94** |
| `rec` | 568 | 134 Rector + 15 à mão | 568/568 | 171/172 | 4.893 linhas, 139 classes, 0 div. | **278/279** + 1 caracterizada |
| `pes3`+`pes4` | 900 | 148 Rector + ~30 à mão | 900/900 | 440/443 (3 artefatos conhecidos) | 12.839 linhas, 0 div. além dos artefatos | **269/270** + 1 pendente (`.phar`) |
| `pes1` | 1.142 | 256 Rector + 3 à mão | 1.142/1.142 | 482/485 (3 artefatos conhecidos) | 13.257 linhas, 0 div. além dos artefatos | **370/370** |
| `pes2` | 775 | 233 Rector + ~200 à mão | 766/766 portáveis (9 já não compilam no 5.6) | 170/170 | 6.276 linhas, 0 div. | **515/515** |

**`rh`+`eso`** — nenhum arquivo de tela precisou mudar: os 29 são 16 `classes/` e 13 `func_`.
Rector só com regras já vetadas (16 guardas, 13 `parse_str`+`extract`, 10 construtores, 4
`split` todos `"#"`, 2 parâmetros opcionais); portão de funções: só `extract`/`preg_split`. As 21
classes sem saída no harness de escrita não têm `atualizacampos()` nem propriedade inteira — as
mesmas nos dois runtimes. Das 94 telas, 93 dão 200; `eso02_preenchimentoesocial001.php` dá 500
**nos dois** (exceção de negócio "Nenhum tipo de formulário selecionado", tela aberta sem
parâmetro). Log do PostgreSQL: nenhum erro de SQL na bateria. Regressão: núcleo intocado;
interseção só com o universo do `con` (`db_rhpesrescisao_classe.php`) → as 31 telas `con`
roteadas: **31/31**.

**`rec`** — Rector em 134 arquivos, só regras vetadas (66 guardas, 61 `split`/`ereg` com 2
`"\|"`, 61 `parse_str`+`extract`, 61 construtores, 2 parâmetros opcionais, 1 `${$var}`). À mão:

- **Octal inválido, segunda aparição** — `rec2_certcomprobatorio002.php` e `rec2_vantagens002.php`
  (bloco copiado): `$mar1[08]`/`[09]`. No 5.6 os dois valem `0`, então `wv_protel` é
  **sobrescrito** por `wv_inf` — bug pré-existente, preservado com `[0]` (medido: mesmas chaves,
  mesma ordem, mesmos valores). O Rector acusou o primeiro como `errors: 1`; o segundo **não
  estava nos alvos** — o `enumera.py` não detecta octal — e só o `php -l` do 8.5 sobre o
  universo o pegou. Rodar o lint no universo, não só nos alterados, se pagou de novo.
- 10 guardas `pg_*` (`null`) em 9 telas, pelo ciclo; o log do PostgreSQL confirma SQL quebrada
  (erros de sintaxe em `and`/`group`). Nenhuma variável guardada é comparada com `===`.
- 2 `count(null)` → `count((array)…)`.
- **NÚCLEO `libs/db_libpessoal.php`, `db_val()`**: `$string+0` com string totalmente não
  numérica — `0` no 5.6, `TypeError` no 8.5 (medido em 9 entradas; `"12abc"`, `"1.5"`, `null`
  são iguais nos dois). Correção: `try { return $string+0; } catch (TypeError $e) { if
  (is_string($string)) return 0; throw $e; }` — idêntica nas 9 entradas, inclusive no tipo, e
  qualquer outro erro segue como antes. Não há cópia no `modification/`.
- **`is_resource()` sobre resultado do PostgreSQL, de novo** — `forms/db_frmtipoasse.php`: o
  `<select>` de natureza saía **vazio** no 8.5 (9 opções a menos, HTTP 200 nos dois).
  `|| is_object(…)`.
- **CATEGORIA NOVA: método NÃO estático chamado estaticamente** — `JSON::stringify($x)` em
  `rec4_agendaassentamento.RPC.php`. No 5.6 era aviso E_STRICT e funcionava (o método não usa
  `$this`); no 8 é `Error`. A base usa `JSON::create()->stringify(…)` em 680 pontos e a forma
  estática em **3** (esta + 2 em `pes4_eventofinanceiroautomatico.RPC.php`, do lote `pes`).
  Corrigido no ponto de chamada, para a forma das outras 680 — sem mexer na classe do núcleo.
- **Caracterizada, não corrigida:** `rec2_espelhoponto002.php` — `fopen()` de
  `tmp/dados_espelho_ponto_{id}.txt` sem o `id` devolve `false`, e o `while (!feof(false))` da
  linha 71 é **laço eterno no 5.6** (um worker ficou 11 min a ~45% de CPU e segurou o lock da
  sessão); no 8.5 é 500 no `fgets`. Mesma decisão das 8 telas do `edu4`.

Regressão: o núcleo foi tocado, mas **só o corpo de `db_val()` mudou**, e a forma da correção
garante que toda entrada que não era fatal devolve o mesmo valor — logo nenhum módulo já
verificado (todos sem fatal em `db_val`) pode mudar. `db_val` só é chamada por `pes`, `rec`,
`model/pessoal/` e o próprio `db_libpessoal.php`. Rodadas: interseção real (universo do `cai`,
`db_afasta_classe.php` + o núcleo) → 105/105 telas `cai` roteadas; amostra `not`+`mar`+`inf`
79/79. **Não** rodada a bateria completa de ~3.700 telas — decisão consciente, pelo argumento acima.

**`pes3`+`pes4`** (primeiro sublote do `pes`, 270 telas) — 21 divergências na 1ª bateria → 1.

- **11ª LACUNA: LSP entre ARQUIVOS — classes que nem CARREGAM no 8.5.** `FolhaPagamentoSalario`,
  `…Adiantamento` e `…Suplementar` tinham 3 métodos incompatíveis com a mãe `FolhaPagamento`
  (`getProximoNumero`, `getFolhasFechadasCompetencia`, `hasFolhaAberta`), e `PontoFerias::
  adicionarRegistro(RegistroPontoFerias …)` restringia o tipo da mãe `Ponto`. Fatal ao declarar
  a classe; o `php -l` não vê (um arquivo por vez) e o harness de classes não vê (só `classes/`).
  Correção do catálogo — parâmetro da mãe como **opcional** na filha, como a própria
  `FolhaPagamentoComplementar` já fazia; em `hasFolhaAberta` o 1º parâmetro perdeu o *hint*
  `DBCompetencia`, mas o corpo o repassa à mãe, que mantém o *hint* (a checagem continua um nível
  abaixo). Em `PontoFerias` o tipo virou `RegistroPonto` — a única diferença para o 5.6 é aceitar
  um `RegistroPonto` que não seja de férias, que lá era *catchable fatal*; os 2 chamadores reais
  passam `RegistroPontoFerias`.
  **Detector novo, versionado: `scratchpad/carrega_arquivo.php`** — inclui um arquivo com o
  bootstrap da aplicação e diz `OK` ou o fatal; rodar um por processo nos dois runtimes sobre os
  arquivos com `extends`/`implements`. Validado contra a versão antiga de `FolhaPagamentoSalario`.
  Varrido também nos universos já verificados: **2 classes da Educação** (corrigidas na
  `2educacao-migrado`, ver a nota na área Educação) e **10 fora de escopo** — só nos universos de
  prefixo inteiro de `con`/`cai` (relatórios DCASP/RREO, autenticadoras térmicas,
  `PadArquivoEscritorTXT`), de Financeiro/Patrimonial: **pendentes para quando essas áreas vierem**.
- **A denylist cresceu para 30 (SÉTIMA vez):** `AddParamBasedOnParentClassMethodRector` copia o
  parâmetro da mãe como **obrigatório** — quebraria `FolhaPagamentoSuplementar::getProximoNumero()`
  chamado sem argumento — e só vê os alvos, deixando as irmãs fatais.
- **`OptionalParametersAfterRequiredRector`, conferida no `dvr`, falhou aqui:** com parâmetro
  **tipado** ela emite `?FolhaPagamento $x = null` (PHP 7.1 — *parse error* no 5.6), em
  `classes/db_rhhistoricocalculo_classe.php`. Corrigido para `FolhaPagamento $x = null` (aceito
  nos dois; idêntico em 3 entradas). Achado pelo `php -l` **no 5.6 sobre o universo**. A regra
  fica (é segura sem tipo), mas o lint do 5.6 sobre o universo é obrigatório depois dela.
- **Duas regras novas ACEITAS, medidas:** `ConsistentImplodeRector` (`implode($a, ',')` → ordem
  nova; a antiga é fatal no 8) e `ReplaceEachAssignmentWithKeyCurrentRector` (`$x = each($a)` →
  `key`/`current`/`next`, que é a correção do catálogo; o caso tinha `reset()` antes e depois).
- **4 `each()` à mão** (2 `while (list(…) = each(…))` nos modelos de folha, 2 `list() = each()`
  em `pes4_relinconsistenciasiprev002.php`) com `key`/`current`/`next` + `is_array` — medido
  idêntico ao `each()` do 5.6 em 5 casos (vazio, nulo, numérico, associativo com `null`,
  ponteiro no meio), e o 8.5 com a forma nova igual ao 5.6 com a original.
- **Octal, terceira aparição, com bug latente que muda dado:** `pes4_rhfopag91002.php`,
  `db_substr($cLinha, 08, 15)` — no 5.6 `08` vale **0**, então a matrícula da importação do FOPAG
  é lida da coluna 0, não da 8 (o layout pede 8: o PIS começa em 23 = 8+15). Preservado com `0`.
- **NÚCLEO `libs/db_app.utils.php`:** `DB_VERSION` indefinida (telas que chamam `db_app` antes de
  `db_conecta`, que a define) → `(defined('DB_VERSION') ? DB_VERSION : 'DB_VERSION')` nas 4
  ocorrências; com a constante definida o valor é idêntico. Sem cópia no `modification/`.
- Restante: guardas `pg_*` (`null`) em 9 telas pelo ciclo; `count`/`implode`/`array_reverse`/
  `ksort`/`array_walk` sobre nulo com `is_array`/`(array)` **só na linha que apareceu** (há linhas
  iguais não tocadas em `pes4_differias002` e `model/manad.model.php`); `(int)` em `"" + 1`;
  `stdClass` onde o 5.6 o criava sozinho (posto na linha da 1ª escrita, não no `decode`); as 2
  últimas chamadas estáticas `JSON::parse`/`stringify` da base.
- **12ª LACUNA (RESOLVIDA depois — ver *PHPExcel.phar PORTADO*): biblioteca dentro de `.phar`.** `ext/php/PHPExcel.phar` — **19 de 189**
  arquivos não compilam no 8.5 (0 no 5.6); nenhuma das sete frentes enxerga dentro de um `.phar`.
  Usado só por `pes4_geracaoarquivorefeisul.RPC.php`, que **fica no 5.6** por uma `location` de
  exceção no nginx (antes da regra geral). Portar = extrair, portar como o `dbagata/`, reempacotar.

Regressão: interseção real com universos verificados = 1 classe do `prot` + o núcleo
`db_app.utils.php` (que só muda onde `DB_VERSION` não existe — antes fatal no 8.5) → `prot`
roteadas 4/4, amostra `not`+`mar`+`inf`+`tre` 98/98. Roteamento: `pes3` e `pes4` no `location`;
`pes1_`/`pes2_` seguem no 5.6.

**`pes1`** (370 telas, 2º sublote) — **369/370 já na 1ª bateria**, o melhor do RH; a única era
uma guarda `pg_*` (`null` numa comparação `== 0`, que dá o mesmo resultado nos dois). Rector só com
regras vetadas, convergiu na 2ª passada. À mão, 3 pontos:

- **`split()` com o padrão numa VARIÁVEL digitada pelo usuário** (`pes1_importainfla001.php`,
  `split($separador, …)`, separador vindo do formulário, padrão `;`). O Rector gera
  `preg_split('#' . preg_quote($separador) . '#m', …)` — **literal** —, mas o `split()` POSIX tratava o
  separador como **regex**. Medido no 5.6: com `.` ele quebra em todo caractere, com `\|` separa no
  pipe, e com `|` sozinho (alternativa vazia, erro em POSIX) devolve **`false`**; a forma do Rector
  erra os três. Corrigido para a forma regex mais o caso da alternativa vazia — **idêntica ao `split()`
  do 5.6 em 13 separadores**, nos dois runtimes. Lição: a vantagem do Rector no `split` (converte
  regex certo) vale para padrão **literal no código**; com padrão em variável ele chuta "literal".
- 1 `while (list() = each())` com `key`/`current`/`next` + `is_array` (forma já medida).
- 1 guarda `pg_*`.

`libs/db_libgertxtfolha.php` foi tocado, mas só os universos do `pes` o alcançam — não pede bateria.
Regressão: interseção só com o `prot` (`classes/db_solicita_classe.php`) → 4/4. Detector de LSP:
nada novo nas 70 classes com `extends` do universo. Roteamento: `pes1` no `location`.

**FERRAMENTAL:** `scratchpad/porclasse.sh` (uma classe por processo para os harnesses de classes e de
escrita) agora é versionado — a cópia fora do repositório sumiu entre sessões e só sobreviveu por
estar no `/tmp` compartilhado dos containers. O portão de funções passou a ignorar comentários de
linha (era a origem do falso positivo `mae` do sublote anterior).

**`pes2`** (515 telas, último sublote — quase todo de relatórios) — 344/515 na 1ª bateria → **515/515**.

- **185 guardas `pg_*` (`null`) pelo ciclo, em 145 arquivos** — o maior volume do projeto. Causa medida no log
  do PostgreSQL: as telas `*002.php` são relatórios que a bateria abre **sem os parâmetros** do formulário
  anterior, e a SQL sai com buracos (`… = and …`: 615 erros de sintaxe perto de `and`, 131 perto de
  `join`). O 5.6 seguia com `false`, caía no "sem dados" e redirecionava (~110 bytes); o 8.5 parava no
  `pg_numrows`. Revisão: **nenhuma** das variáveis guardadas é comparada com `===`/`!==` nos 145 arquivos.
- **9 arquivos que já NÃO compilam no 5.6**, deixados intocados como os do `dbagata/`: as 8 telas de
  **geração de arquivo bancário da folha** (`pes2_*emitearqbanco*`, `*contramatricial002`,
  `emitebb200lay002`, `emitearqbancocnab240_002`) — passagem por referência na **chamada**
  (`db_setaPropriedadesLayoutTxt(&$x, …)`), erro de compilação desde o PHP 5.4 — e
  `pes2_arrcontramatricial001.php`. Os `split`/`parse_str` que sobram no universo estão todos neles
  (contador por *token* sobre os 766 portáveis: zero).
- **Denylist 30 → 31 (OITAVA vez): `RemoveReferenceFromCallRector`.** Remove o `&` dessas chamadas — só
  pode agir em código que já não compila no 5.6, então toda aplicação dela é **conserto**.
- **`break` fora de laço**: `pes2_relcad001.php` — 6 blocos de erro alcançáveis → `exit;`, com o `php -l` do
  8.5 dirigindo um a um (os 6 `break` restantes estão em laços); `pes2_relfichafinanceiratxt002.php` —
  logo depois de `db_redireciona()` (que termina em `exit` no original e na cópia) → removido.
- **5 `each()` em `fpdf151/pdf2.php`** (parte da dívida da *6ª lacuna*): forma `key`/`current`/`next` dentro
  da condição do `while`, medida idêntica ao `each()` do 5.6 inclusive com `break` e na posição do
  ponteiro depois do laço. O `pdf4.php` ainda tem 5 `each()`, não alcançados.
- Família "argumento inválido virou `TypeError`/`ValueError`", na linha que apareceu: `mktime()` com
  `substr()` de data vazia (o 5.6 recebia `false` → 0 → `mktime(0,0,0,0,0,0)` = 943927200; `(int)` em cada
  `substr` reproduz), `file("")`, `fputs`/`fclose(null)`, `count`/`sizeof(false)` (= 1 no 5.6, igual a
  `(array)false`), `cal_days_in_month` (`try`/`catch`), `db_formatar()` com 1 argumento (o `null` explícito),
  `pg_result` aninhado e `stdClass` sobre `null`.
- **9ª manifestação da RFC das comparações — NÚCLEO `fpdf151/fpdf.php:967`, `Cell()`:** `if($align=='R')`
  com o alinhamento passado como inteiro `0`. No 5.6 `0 == 'R'` é verdadeiro e a célula saía **à direita**;
  no 8.5, à esquerda. HTTP 200, PDF válido, 2 bytes de diferença — só descomprimindo o `FlateDecode` se via
  o `x` da célula mudar de 35,79 para 17,01. Correção `|| $align===0 || $align===0.0`, igual ao 5.6 em 10
  valores. As irmãs `=='J'` (l. 1157) e `=='U'/'D'` (l. 2907–2932) têm a mesma forma e **não** foram tocadas
  (não apareceram). Sem cópia no `modification/`.

Regressão: o núcleo foi tocado (`fpdf.php`), mas a mudança só altera o caso em que o 8.5 já gerava PDF
diferente do 5.6 — e todas as baterias anteriores comparam bytes de PDF. Rodada mesmo assim a bateria dos
lotes de RH já verificados + relatórios `iss2_`: **1.084/1.086**, exatamente as duas caracterizadas (`.phar` e
`rec2_espelhoponto002`). Roteamento: com os 1.155 `pes*_` portados, o `location` voltou a um `pes` só; a
exceção do `.phar` continua antes dele.

#### 🏁 FASE A DA ÁREA RH CONCLUÍDA — `rh`, `eso`, `rec`, `pes` inteiros

| | |
|---|---|
| Telas roteadas por `location` | **1.528** (`pes` 1.155, `rec` 279, `eso` 85, `rh` 9), menos 1 exceção do `.phar` |
| **Bateria** | **1.526 / 1.528** — as 2 restantes são o laço eterno do 5.6 (`rec2_espelhoponto002`) e a pendente do `.phar`. Entre as idênticas estão `eso02_preenchimentoesocial001` (o mesmo 500 de negócio nos dois) e as 9 do `pes2` que não compilam no 5.6 (falham igual) |
| Arquivos alterados | **849** nos cinco lotes (contados pelo git) |

#### Fase B da área RH — as 10 telas de prefixo compartilhado, pelo `map`

Medido pelo banco depois da Fase A: **10 telas** de menu de RH ainda no 5.6 — `cai2_relslip001`,
`cai3_reemiteplanilha001` (também de Financeiro), 5 `con4_*` (eSocial e Pessoal), `es04_s1299fechamentoeventos001`,
`lic4_geracaoeditais001` (também de Patrimonial) e `sped04_retornoevento001` (também de Integrações).
Mesma decisão da Fase B do Tributário: as compartilhadas vão junto — o código é o mesmo nos dois runtimes.

| | |
|---|---|
| Universo (sete frentes, `TELAS=`) | 76 arquivos, 42 já pagos |
| **Alterados** | **3** classes (Rector: guardas, `split`, construtores; só regras vetadas, 1 passada) |
| `php -l` / remanescentes / funções / LSP | 76/76 nos dois · 0 · só `preg_split` · 0 de 7 |
| Classes / escrita | 24/24 · 1.277 linhas idênticas |
| **Bateria** | **10/10**, todas 200 com conteúdo real |
| Regressão | interseção com universos verificados **vazia**, núcleo intocado → não rodada |

`gera_map_faseb.py` passou a conhecer `rh`/`eso`/`rec`/`pes` como prefixos do `location`, e recebe o lote
`recurs:cai,con,es,lic,sped`. Diff do `map`: **+10 entradas, −1** (`rec4_avaliacao001`, a tela `rec` do
Tributário, que o `location` agora cobre). Reproduzir: `python3 scratchpad/gera_map_faseb.py
tribut:amb,pre,cad,cai,pro,con,prot,rec,dv,sys educa:mat,pro recurs:cai,con,es,lic,sped`.

### 🏁 ÁREA RECURSOS HUMANOS — TELAS DE MENU CONCLUÍDAS

Conferido **pelo proxy, tela de menu por tela de menu** (`X-Ecidade-Runtime` em `/w/2/<tela>`), não pelas
listas: **701 de 701** telas de menu existentes em disco servidas pelo PHP 8.5 (705 entradas, 4 fantasmas:
`pes1_cadastropensoes001/002`, `rec1_libbasecalculo`, `rec2_folhaponto01`).

| | |
|---|---|
| Módulos | **4 de 4** — Pessoal, RH, eSocial, Estágio Probatório |
| Telas comparadas byte-a-byte | **1.537 / 1.538** (Fase A 1.527/1.528 + Fase B 10/10) |
| Divergências | **1**, caracterizada: o laço eterno do 5.6 em `rec2_espelhoponto002` |
| Arquivos alterados | **852** (849 na Fase A + 3 na Fase B) |
| Lacunas novas | **11ª** (LSP entre arquivos — detector `carrega_arquivo.php`) e **12ª** (biblioteca em `.phar`, resolvida) |
| Denylist do Rector | 29 → **39** |

#### ✅ `ext/php/PHPExcel.phar` PORTADO — a 12ª lacuna fecha

Extraído (228 arquivos, 189 PHP) para `ecidade/tmp/phar_porte/`, portado e **reempacotado com o PHP 5.6**
(o runtime de referência), com o mesmo *stub* e assinatura SHA-1 — mesma lista de 228 arquivos.

- Rector: 30 arquivos (19 offsets `{}`, 10 parâmetros opcionais, 2 `implode`, 1 construtor) + 8 `?Tipo`
  removidos à mão + 1 `break` inalcançável (depois de `return`) removido. `php -l` **189/189 nos dois**.
- **A biblioteca de terceiros disparou NOVE regras inéditas**, e **oito foram vetadas** (denylist 31 → **39**):
  - **`RemoveParentCallWithoutParentRector` apagou `parent::__construct()` LEGÍTIMO** nas duas classes do
    escritor Excel5 — a mãe `BIFFwriter` **tem** `__construct`, o Rector não a resolveu. O construtor da mãe
    deixaria de rodar no 8.5, em silêncio — e o Excel5 é exatamente o escritor que a tela usa. A mais
    perigosa da rodada.
  - `IfToSpaceshipRector` (`<=>`) e `ArrayKeysToArrayKeyFirstLastRector` (`array_key_first`): não existem no 5.6.
  - `StringifyStrNeedlesRector`: `(string)` na agulha do `strpos`. O 8 já trata agulha inteira como string,
    então a regra não muda o 8.5 — mas **muda o 5.6**, onde agulha inteira era código de caractere.
  - `ContinueToBreakInSwitch`, `ClassConstantToSelfClass`, `DirNameFileConstantToDirConstant`, `PowToExp`:
    modernização equivalente, não exigida.
  - **Armadilha do instrumento:** 4 dos 8 nomes de classe que escrevi na denylist estavam no namespace
    errado; com o nome errado a regra simplesmente não seria vetada. Conferido arquivo a arquivo (39/39).
- **Teste funcional** (`scratchpad/teste_phar.php`): carrega as 170 classes de nome convencional pelo
  autoloader do próprio PHPExcel (pega LSP, construtores, declaração) e gera um XLS pelo escritor
  **Excel5** com texto, número, data, moeda e acento. **5.6 com o `.phar` original = 5.6 com o novo = 8.5
  com o novo**, byte a byte, descontados os 16 bytes do carimbo de hora do contêiner OLE — que diferem
  entre duas execuções do próprio original. O original no 8.5 dá *parse error* (`String.php:529`).
- A tela `pes4_geracaoarquivorefeisul.RPC.php` ficou idêntica (também com a ação real `gerarArquivo`, que
  nos dois para na mesma mensagem de configuração ausente) e **a exceção do nginx foi removida**.

#### ✅ NÍVEL 3 (POST real) nos cadastros de RH

As **77** telas de inclusão do menu de RH; **70** mapeadas para a tabela pela convenção de nome
(`pes1_rhfuncao001` → `rhfuncao`, só quando a classe `db_<tabela>_classe.php` existe).

| Veredito | Telas |
|---|---|
| | 1ª rodada (payload automático) | **Depois dos payloads à mão (22/10/2026)** |
|---|---|---|
| **IDÊNTICO** — o mesmo SQL de negócio gravado nos dois runtimes | 37 | **68** |
| **DIVERGE** | 0 | **0** |
| INCONCLUSIVO / ABORTADO | 31 / 2 | — |
| quebram **também no 5.6** (caracterizadas) | — | 2 |

**O harness mudou, porque em RH a restauração não funcionava:** ela apagava a tabela **inteira** e a
repovoava, e em RH quase todo cadastro auxiliar é referenciado pelo `rhpessoal` — o `DELETE` esbarrava na
FK já no primeiro teste (`rhestcivil`). Agora a cópia fica numa tabela auxiliar no banco e a restauração é
**por diferença**, comparando a linha inteira: apaga só o que não estava no snapshot e reinsere o que
sumiu, e confere a contagem no fim. A FK continua sendo a rede de segurança. Validado na demonstração do
Cemitério (idêntico → diverge → idêntico, tabela intacta).

**⚠ Os dois ABORTADOS deixaram dado de teste no banco** — a tela gravou também numa tabela FILHA fora do
conjunto (`pensaoretencao`, `rhipenumcgm`/`rhiperegist`), a FK barrou o `DELETE` do pai e o harness parou
sem apagar nada às cegas (correto), mas as linhas ficaram. Limpas à mão numa transação (5 linhas, todas de
tabelas que estavam vazias no snapshot) e as 3 sequências devolvidas ao valor anterior. Para não depender
de conferência manual, o harness agora **avisa** quando o SQL de negócio grava numa tabela fora do conjunto
restaurado (o único caso entre os IDÊNTICOS, `rec1_tipoasse001` → `tipoassedb_cadattdinamico`, não deixou
nada: o `INSERT` extra falhou pela FK e a transação da tela desfez tudo, nos dois).

**Os 33 que não gravaram na 1ª rodada (22/10/2026): 29 resolvidos, todos IDÊNTICOS.** Os payloads que
funcionaram estão versionados em **`scratchpad/n3_rh_payloads.tsv`** (tela, tabelas restauradas, payload).
As causas, que valem como receita para as próximas áreas:

| Causa | Telas | O que resolveu |
|---|---|---|
| **chave digitada** — a tabela não tem sequência; o gerador deixa a chave vazia e a classe recusa ("Chave Primaria zerada") | 10 (`pesdiver`, `rhempresavt`, `vtfempr`, `areas`, `flegal`, `rharqbanco`, `curric`, `rhcontasrec`, `rhsindicato`, `padroes`) | valor livre, conferido antes no banco |
| **tela com abas** — a tela do menu é só o contêiner; o formulário está no iframe `*004.php`/`*005.php` | 13 | gerar o payload e postar **na tela interna** (todas roteadas pelo 8.5 pelo prefixo) |
| **grava por RPC** — o JavaScript monta um JSON e chama um `.RPC.php` | 4 | postar no RPC com o JSON (`json={…}`) ou os campos + `acao=…` |
| **tabela filha fora do conjunto** — a restauração esbarra na FK e aborta | 4 (`pensao`, `rhipe`, `relrub`, `assenta`) | acrescentar a filha, antes da mãe, no 2º argumento |
| a convenção de nome errou a tabela (`rhbases` grava em `bases`) | 1 | o aviso `ATENCAO` do harness apontou |

Três exigiram **semear dado ausente** na base ou ficaram com cobertura parcial: `regraponto` exige uma
`selecao` (FK) e a tabela está vazia, então foi semeada 1 linha e apagada depois; em
`rhempenhofolhaexcecaorubrica` só a gravação da **regra** foi exercitada, porque as exceções por rubrica
exigem orçamento de 2026 (`orcunidade` vai até 2015, `orctiporec` vazia); `rhpessoal004` deu DIVERGE na 1ª
tentativa só pelo sequencial de `registrapontoeletronicohistorico`, que não estava no conjunto. Com a tabela
incluída, IDÊNTICO.

**As 2 que restam, e por quê:**

- `pes1_rhfuncao001` e `pes1_rhcadregime001` **quebram também no 5.6**, com a mesma resposta nos dois
  runtimes. `rhfuncao` chama `isParaiba()`, que não existe em lugar nenhum, e a página para antes do botão;
  `rhcadregime` dá "Erro interno" já no GET. É impossível incluir pelo 5.6: defeito pré-existente, intocado.
**Estágio probatório — CENÁRIO montado (22/10/2026), as 2 telas IDÊNTICAS.** Avaliação e resultado dependem
da cadeia agenda → pergunta do quesito → avaliação → resultado, e a base tinha essas tabelas vazias. Foram
semeadas **8 linhas** (id 901, `SEMENTE_N3`): critério, pergunta e resposta possível do quesito 1, agenda e
data agendada da matrícula 1, comissão, período do estágio e um `portariatipo` para o tipo de assentamento
de aprovação. Todas foram apagadas no fim; o banco voltou ao original.

- **Avaliação**: grava por `rec4_rpcexame.php` em **três requisições na mesma sessão** — abrir o exame,
  `salvarResposta` (a resposta fica em `$_SESSION["avaliacao"]`) e `salvarExame`, que grava. O
  `escrita_post.py` passou a aceitar vários POSTs separados por `|||`, restaurando a sessão só antes do
  primeiro. Resultado: `rhestagioavaliacao` + `rhestagioavaliacaoresposta`, **idênticos**.
- **Resultado**: um POST que grava em cadeia `portaria` → `assenta` → `portariaassenta` →
  `rhestagioresultado`, **idênticos** nos quatro.

**Limpeza:** quatro execuções abortaram ou gravaram fora do conjunto restaurado e deixaram linhas de teste
(`pensao`/`rhipe` de novo, `relrub`, `bases`, `assenta`). Todas foram removidas numa transação, conferindo
pelo log do PostgreSQL o que cada uma gravou, e as sequências voltaram ao valor anterior. O valor anterior
foi deduzido do próprio log: se o `INSERT` recebeu 1, a sequência estava em (1, não chamada). Ao fim, o banco
está como no início, e nenhuma tabela `_n3snap_*` ficou para trás.

#### ✅ CENÁRIO DE CÁLCULO DA FOLHA — os 6 tipos idênticos nos dois runtimes

A competência da folha da base é **02/2013** e a matrícula 1 tem movimento nela — o cenário usa o servidor
existente. O cálculo é disparado por `pes4_gerafolha002.php` em modo automático
(`lAutomatico=1&iPonto=<tipo>&iMatricula=1`) e comparado pelo nível 3 (SQL de negócio emitido).

| Tipo (`iPonto`) | Resultado |
|---|---|
| 1 Salário, **com ponto semeado** (`0001` qtd 30 → fórmula `F010/30` pelo `eval`; `0002` valor 150,50) | **IDÊNTICO** — 139 statements, 8 escritas, incluindo o `INSERT` em `gerfsal` |
| 2 Adiantamento · 3 Férias · 4 Rescisão · 5 13º · 8 Complementar | **IDÊNTICOS** |

O ponto foi semeado direto no banco (2 linhas em `pontofs`), tomado pelo snapshot do harness e **apagado no
fim** — o banco voltou ao estado original (folha e ponto vazios, sequências intactas).

**Antes das correções, o cálculo de salário PARAVA no meio no 8.5** — 59 statements contra 89, sem gravar o
resultado. Nenhuma bateria GET chegaria aqui. As causas, uma a uma, pelo ciclo de diagnóstico:

- **NÚCLEO `model/pessoal/std/DBPessoal.model.php`**: `$F032 = $F032 - $F031` com `$F031 = ''` (sonda: dias
  trabalhados vindos do ponto eletrônico vazio). `'28' - ''` = 28 no 5.6, `TypeError` no 8.5. Correção
  `($x === '' ? 0 : $x)`, medida igual ao 5.6 em 6 casos inclusive no tipo.
- **`pes4_gerafolha004.php` (o motor, ~10 mil linhas)**: o total líquido `$tot_prov + $salfamilia - $tot_desc`
  com `$tot_desc = ''` — mesma correção; e 4 `count(null)` → `(array)`. A comparação `'150.5' > ''`, logo
  acima, é string com string nos dois runtimes (verdadeira nos dois) — não precisou de nada.
- `CalculoPensao.model.php`: 2 `count(null)`.
- **e a 13ª lacuna** (abaixo): o cálculo morreu em `AjustePrevidencia::…`, num arquivo que não estava em
  universo nenhum.

Regressão: bateria completa do `pes` **1.155/1.155** (5 PDFs divergiram sob carga pelo horário dentro do
fluxo comprimido e ficaram idênticos isolados).

#### ⚠ 13ª LACUNA — classes carregadas por AUTOLOAD fora de `classes/`

`AjustePrevidencia` é chamada como `AjustePrevidencia::ajustar(…)` pelo motor, carregada pelo autoloader, sem
`include`. A frente de autoload só resolvia `new cl_*` e `getDao()`. Medido no universo de RH: **557**
arquivos de `model/`/`std/` alcançados por `new Classe`/`Classe::` e fora do universo. Neles: **5 classes que
nem carregavam no 8.5** (LSP — `FolhaPagamento13o` e `FolhaPagamentoRescisao`, irmãs das três já corrigidas;
`ProcessamentoPontoConsignadosCaixa`), **6 `each()`** em 3 modelos de folha. Corrigidos e verificados (lint e
carga nos dois runtimes). Nas áreas concluídas: 1 `split` no Tributário e 1 `unset($this)` na Educação,
corrigidos **nas branches delas** e trazidos por merge (`c1a450c78`, `448bd26fb`, `7f4efcb32`).

**`enumera.py` ganhou a oitava frente** (mapa classe → arquivo de `model/`/`std/`). Com ela, o fecho segue dos
modelos até `classes/` — e mostrou que a medição acima **subestimava**: os modelos instanciam classes de dados
que também nunca entraram em universo. **União nas três áreas: 361 arquivos a alterar, 357 em `classes/`**
(296 com construtor PHP 4, 357 com guarda `0 == ""` faltando, 205 com `split`). Mecânico para o Rector,
mas o construtor PHP 4 que não roda é a falha silenciosa mais grave do catálogo.

**DECIDIDO E FEITO (21/10/2026):** portados na branch do Tributário e trazidos por merge — dos 361, 45 já
estavam pagos por commits `EXPERIMENTO:`; os **316** restantes estão na seção *Os DAOs que os modelos
instanciam* (área Tributário): `php -l` 316/316 nos dois, classes 315/315 e escrita 0 divergentes.

**O que NÃO está feito na área:** os 9 arquivos do
`pes2` que não compilam nem no 5.6 (defeito da referência, intocados).

### ⚠ 14ª LACUNA (25/10/2026, achada testando à mão no RH): tela de menu no 8.5 que manda o navegador ao 5.6

Achada pelo usuário em eSocial → Cadastro de Formulários → Alteração: `eso1_cadastroavaliacoes002.php` é
servida pelo 8.5, mas só faz `db_redireciona('hab1_avaliacao002.php…')`, e `hab*` não é migrado — o
formulário real roda no 5.6. A contagem "telas de menu no 8.5" conferia **o arquivo do menu**, não para onde
ele leva o navegador.

**Medido** com `scratchpad/redirecionamentos.py <SID> <saida>`: GET no 8.5 de cada uma das **2.418** entradas
de menu das três áreas que o proxy manda ao 8.5, capturando o redirecionamento imediato (cabeçalho
`Location` ou o `<script>location.href=…</script>` do `db_redireciona`) e os `<iframe src>` carregados na
abertura, classificados pelo mesmo critério do nginx.

| Tipo | Telas de menu | Destinos | O que é |
|---|---|---|---|
| **iframe para tela no 5.6** | **87** | 162 distintos (com os redirecionamentos) | as **abas** das telas da Fase B: o contêiner (`cad1_face001`) está no `map`, a aba com o formulário (`cad1_face004`) não está no menu e por isso ficou no 5.6. `cad` 38, `cai` 32, `mat` 11, `con` 3, `pro` 2, `prot` 1 |
| **redireciona para tela no 5.6** | **5** | `hab1_avaliacao002`, `cai4_lista01`, `pro1_obras005` | `eso1_cadastroavaliacoes002`; `cai4_lista001` (quando não usa o sistema de água); `pro1_obras001/002/003` (sem `abas`, que é como o menu abre) |
| redireciona para `corpo.php` | 4 | — | **não é lacuna**: é o "voltar ao início" depois de erro de configuração ou exceção (`numpref` não configurado, rotina desativada) |
| iframe para `dbforms/…` | 66 | 4 | o proxy não roteia por pasta; já documentado (*`/tmp` COMPARTILHADO*) |

**Os prefixos da Fase A não aparecem**: lá o roteamento é por prefixo, e a aba `*004.php` vai junto. A lacuna
é própria do roteamento por lista (`map`), que só conhece o que está no menu.

**Os destinos já estão quase todos portados** — vieram pela frente "citados em strings": os 162 passam no
`php -l` do 8.5, sem guarda `0 == ""` faltando nem construtor PHP 4 (contador por *token*). Sobram **8**
com incompatibilidade, que dariam fatal no 8.5 se fossem roteados: `parse_str` de 1 argumento em
`cad1_aba2ruas002`, `cai1_debcontapedido002`, `con1_editalrua004`, `func_selinstit`, `mat1_matdevolveitens001`,
`pro1_obras005`, `prot1_comparanomes`, e 2 `split` em `con1_editalrua004`. A cadeia `hab1_avaliacao*` não
entrou na medição de porte (o redirecionamento leva a ela, e a aba dela, `hab1_avaliacao005`, é um segundo
salto que o levantamento não segue).

**Limites do levantamento:** só o que a página faz **ao abrir, por GET sem parâmetros**. Abas carregadas por
JavaScript ao clicar, redirecionamentos condicionais a dado e o segundo salto não entram. É uma cota inferior.

**Consequência para os números:** "1.059/1.059" (Tributário), "480/480" (Educação) e "701/701" (RH) continuam
verdadeiros como *arquivos de menu servidos pelo 8.5*, mas em **92** deles o formulário que o usuário
preenche roda no 5.6.

**DECIDIDO (26/10/2026, usuário): tratar na aparição, não agora.** Nada está quebrado: o formulário roda no 5.6,
que funciona. Ressalva que muda *onde* eles aparecem: as migrações das próximas áreas **não** os pegam
sozinhas. O `map` é gerado do menu, e as abas `*004.php` não estão em menu nenhum. Só entram por um destes
caminhos:

- o prefixo inteiro passar ao `location`. Isso vale para `hab1_avaliacao*`, se `hab` for prefixo exclusivo da
  área que o trouxer, e para `cai`/`con`/`mat`/`pro` quando todas as áreas que os usam estiverem migradas;
- o desligamento do 5.6, que obriga a rotear tudo.

Os 8 arquivos com `parse_str`/`split` entram no porte quando o prefixo dono for portado inteiro. Ao migrar a
próxima área, rodar `redirecionamentos.py` (com o `SQL` estendido à área) junto da conferência pelo proxy.

**REVISTO no mesmo dia (26/10/2026, usuário): os IFRAMES foram migrados agora.** Os redirecionamentos ficam
para a aparição.

| | |
|---|---|
| Destinos de iframe no 5.6 | **158** (`cad` 83, `cai`/`Cai` 45, `mat` 17, `pro` 9, `con` 1, `prot` 1, `func_selinstit`, `verifica.php`), atrás de 90 entradas de menu |
| Universo (`enumera.py`, `TELAS=`) | 1.402 arquivos, 747 já pagos, **62 a alterar** |
| Rector | **37** alterados (26 `parse_str`+`extract`, 15 `ereg`/`split`, 11 guardas, 11 construtores, 2 `${$var}`, 1 `implode`), só regras já vetadas; 0 na 2ª passada. Os outros 25 alvos já não tinham remanescente (contador por *token*: 0 em todas as categorias) |
| À mão | `mat2_controlest011.php:93`: `$cliframe_seleciona_grupo->sql_marca = …` sobre variável **nunca atribuída** (erro de digitação do original: o objeto é `$cliframe_seleciona`). O 5.6 criava `stdClass` com aviso, o 8.5 lança `Error`. Correção fiel do catálogo: criar o `stdClass` quando a variável é indefinida, `null`, `false` ou `""` |
| Portão de funções / `php -l` | só `extract`/`preg_split` · 1.402/1.402 nos dois runtimes |
| Classes / escrita | 11/11 idênticas · 203 linhas idênticas |
| **Bateria das abas** | **158/158** |
| Regressão (interseção com `cad`/`cai`/`con`/`pro`/`prot`/`mer`) | `map` inteiro 390/390, `mer` 187/187 |
| Roteamento | `docker/proxy/faseb_map_abas.txt` (versionado), lido pelo `gera_map_faseb.py`: **+158 entradas, −0** no `map` (548). Config testada em container descartável antes do recreate |
| **Levantamento refeito** | 2.841 telas no 8.5 examinadas (menu + 423 abas já roteadas, para pegar o **segundo salto**): **0 iframes ao 5.6**. Sobram 9 redirecionamentos: os 5 conhecidos (`hab1_avaliacao002`, `cai4_lista01`, `pro1_obras005` ×3) e 4 para `corpo.php` (não é lacuna) |

`func_selinstit.php` e `verifica.php` são abertos também por telas do 5.6, que agora os recebem do 8.5. Isso é
seguro porque o código portado roda nos dois runtimes. A verificação entrou na skill como **passo 8b**.
