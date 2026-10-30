# Área Financeiro (branch `5financeiro-migrado`)

### 📐 Dimensionada e dividida em lotes (29/10/2026)

`scratchpad/dimensiona.py` (com as nove frentes, depois de Patrimonial): **926 telas de menu faltando** (1.004 no menu,
12 fantasmas), universo 5.007, 999 já pagos, **601 a alterar**. Ver `dimensionamento.md`.

6 módulos no banco: Contabilidade 341 telas, Orçamento 270, Caixa 233, Empenho 136, Planejamento 30, Custos 16.

| Prefixo | Telas do Financeiro no menu | Em áreas ainda pendentes | Em disco | A alterar (prefixo inteiro, isolado) |
|---|---|---|---|---|
| `con` | 322 | **173** (Cidadão, Configuração) | 1.559 | 706 (só as telas do Financeiro: **200**) |
| `orc` | 269 | 6 (Configuração) | 628 | 384 |
| `cai` | 181 | 1 (Configuração) | 740 | 342 |
| `emp` | 151 | — | 458 | 320 |
| `pla` + `pl` | 31 + 1 | — | 41 + 3 | 21 + 17 |
| `cus` | 16 | — | 48 | 40 |
| `tes` | 1 | — | 7 | 17 |
| `hab` / `sys` / `pro` / `age` / `cad` | 3 / 1 / 1 / 1 / 1 | 19 / 22 / 2 / 1 / — | — | via `map` |
| `com`, `iss`, `inf`, `div`, `pes` | 9, 5, 5, 4, 2 | — | — | já no `location` |

`pl4_` (3 arquivos) é variante própria: não casa `pla[0-9]*_`. As telas que faltam por prefixo, descontando o que já
é servido: `con` 313, `orc` 265, `cai` 153, `emp` 143, `pla` 30, `cus` 15, `hab` 3, `age`/`pl`/`pro`/`tes` 1 cada.

#### Divisão em lotes (aprovada pelo usuário)

| Lote | Prefixos | Telas que faltam | Em disco | A alterar (isolado) | Roteamento |
|---|---|---|---|---|---|
| 1 | `cus`, `pla`, `pl`, `tes` | 47 | 99 | ~60 | `location` |
| 2 | `emp` | 143 | 458 | 320 | `location` |
| 3 | `orc` | 265 | 628 | 384 | `location` (subdividir por `orc1_`/`orc2_`/`orc4_` se a 1ª bateria vier muito divergente) |
| 4 | `cai` **inteiro** | 153 | 740 | 342 | `location` — as telas `cai` saem do `map` |
| 5 | `con`, **só as telas do Financeiro** | 313 | 1.559 | 200 | `map` |
| 6 | `hab`, `age`, `pro` + abas do passo 8b | 5 | — | pequeno | `map` |

As estimativas isoladas se sobrepõem (somadas passam de 1.300, contra 601 da área); o real tende a sair acima (em
Patrimonial, 469 previstos, ~710 reais).

**Decisões do usuário (29/10/2026):**

1. **`cai` vai INTEIRO pelo `location`.** O Financeiro é o dono: das telas `cai`, só 1 é de área pendente
   (Configuração), e vai junto. Os popups e RPCs fora do menu passam a ser servidos pelo 8.5, e as telas `cai` que
   hoje estão no `map` (Tributário, RH, Patrimonial) passam a ser cobertas pelo `location`.
2. **`con` só pelas telas do Financeiro, pelo `map`.** 173 telas `con` são de Configuração e Cidadão, ainda
   pendentes; o prefixo inteiro custaria 706 arquivos em vez de 200. Pode ir inteiro depois dessas duas áreas.
3. **Um lote por vez:** terminar, relatar e esperar o pedido do próximo (anotado no `CLAUDE.md`).
4. **Bateria completa só no fim da área** (decidido depois do lote 1): em cada lote, a do próprio lote e, se tocar o
   núcleo, a dirigida às telas que chegam ao trecho; a completa, e o envio, só no fim do Financeiro.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| 1 `cus`+`pla`+`pl`+`tes` | 1.347 | 45 Rector + 2 à mão (+10 do passo 8b) | 1.347/1.347 | 17/17 | 369 linhas, 0 div. | **99/99** |
| 2 `emp` | 3.409 | 295 Rector + ~30 à mão | 3.409/3.409 | 48/48 | 1.080 linhas, 0 div. | **458/458** |
| 3 `orc` | 3.037 | 345 Rector + ~125 à mão | 3.034/3.037 (as 3 restantes não compilam em nenhum) | 1.032 (diffs só do harness) | 25.379 linhas, diffs só do harness | **626/628** (2 caracterizadas) |
| 4 `cai` inteiro | 3.988 | 273 Rector + ~230 à mão | 3.988/3.988 | 1.256 (diffs só do harness) | diffs só do harness | **739/740** (1 caracterizada) |
| 5 `con` (telas do Financeiro) | 3.053 | 144 Rector + 21 LSP à mão | 3.053/3.053 | 1.010 (diffs só do harness) | diffs só do harness | **313/313** |
| 6 `hab`/`age`/`pro` + abas | 2.535 | 66 Rector + 10 LSP + 1 comentário à mão | 2.513/2.535 (22 não compilam em nenhum) | 941 (diffs só do harness) | diffs só do harness | **91/91** + 6/6 do 2º nível |

**Lote 1 — `cus`, `pla`, `pl`, `tes`** (Custos, Planejamento, Tesouraria; 99 arquivos, roteados no `location`).
Rector em 45 arquivos, só regras já vetadas (28 `parse_str`+`extract`, 17 guardas, 15 construtores, 14 `split`, todos
`"#"`), 0 na 2ª passada. LSP 320/320; passo 6c (forma negada) 1.251 pares, 0 divergentes. Bateria 93/99 → **99/99**,
com 2 guardas `pg_*` (`null`) — as duas sobre SQL que falha sem os parâmetros do formulário, e a variável só limita um
`for` (`$i < null` é falso nos dois):

- `model/linhaRelatorioContabil.model.php:193` (derrubava `pla2_anexos_ldo001`, `pla2_anexos_rreo001`,
  `pla2_anexos_rreo_consolida001`, `pla2_planejamento_previsao_rcl001`);
- **NÚCLEO `libs/db_utils.php:331`**, `db_utils::makeCollectionFromRecord()` (derrubava
  `pla2_fator_correcao_despesa/receita`). Sem cópia no `modification/`.

Núcleo tocado → **bateria completa**: **6.082/6.106** (as 24 caracterizadas) e `map` **822/822**.

Ruído caracterizado: `pla2_anexos_ldo001.php` gera **8.392 erros de SQL por requisição, igual nos dois runtimes** (uma
consulta inválida por linha do relatório aberto sem parâmetros) — pré-existente; a bateria refaz o par, daí 67 mil
erros no log do PostgreSQL numa rodada.

Roteamento: `cus|pla|pl|tes` no `location` e nas três cópias do critério; `teste.php` e `planilha.php` (que não casam)
seguem no 5.6. **Passo 8b** (187 telas do Financeiro no 8.5): 31 telas `pla2_*` de relatórios legais abriam duas
abas de Contabilidade no 5.6, `con2_conrelnotas.php` e `con4_parametrosrelatorioslegais001.php`. O universo delas
tinha porte real a fazer: **10 classes** `orcparam*`/`conrelvalor` (60 guardas `0 == ""`, 6 construtores PHP 4, 28
`split` `"#"`), portadas pelo Rector; lint, classes 10/10 e escrita 220 linhas idênticas; 8/8 telas; fora do universo
servido. As duas abas em `faseb_map_abas.txt`; levantamento refeito: nada indo ao 5.6.

**Lote 2 — `emp`** (Empenho, 458 arquivos, roteados no `location`; `emp1_`…`emp4_`, `emp04_`, `emp_`). Os 2
**`empenhos_*`** (`empenhos_fgts.php`, `empenhos_inss.php`) não casam `emp[0-9]*_` e ficaram de fora: **órfãos**, sem
entrada no menu e sem ninguém que os cite (como o `tra`). Universo 3.409. Rector em 295 arquivos, só regras já vetadas
(231 `parse_str`+`extract`, 95 `ereg`/`split`, 48 guardas, 42 construtores, 17 `${$var}`, 2 parâmetros opcionais, 1
`implode`), 0 na 2ª passada. Separadores de `split` com metacaractere escapado (`"\|"`, `'\.'`, `"\."`) viraram
`preg_split("#\\|#m")` / `("#\\.#m")` — **conferido no 5.6 em 6 casos: idêntico ao `split` POSIX**.

À mão:

- **LSP — as autenticadoras térmicas** registradas desde o RH como "pendentes para o Financeiro":
  `modeloAutentTermicaArrecadacao/Empenho/Slip::imprimir()` sem o `$sStringCorpo` da mãe (sem padrão nela →
  `= null` na filha) e `modeloAutenticadoraElginXprint::imprimir()` sem o `$sImprimir = ''` de `impressao`. Nenhuma
  filha usa o nome. Carregam nos dois.
- **Forma negada** (passo 6c): 2 pontos de auditoria em `db_empnotasuspensao_classe` (`cc36_empnota`,
  `cc36_sequencial`), guardados com o **`scratchpad/negada_corrige.py`, agora versionado** (o script estava no
  temporário da sessão e sumiu); 0 remanescentes.
- 17 guardas `pg_*` (`null`) pelo ciclo, nenhuma variável comparada com `===` — duas delas no **NÚCLEO
  `fpdf151/pdf.php:95/97`** (logo e URL do cabeçalho dos relatórios, quando a consulta a `db_config` falha) e uma em
  `cai3_reemiterecibo.php`; mais uma em `emp2_confereretencoes002:264`.
- `count(null)` → `count((array)…)`: 4 linhas em `emp2_confereretencoes002` (`recursos`, `credores`, `retencoes`,
  `contas`), no mesmo caminho da requisição.
- **`number_format()` com string**, `forms/db_frmempempdot.php:149`: medido no 5.6 — string **não numérica** devolve
  `NULL`; string que **começa** por número usa a parte numérica. No 8.5 as duas são `TypeError`. Guarda que devolve
  `null` na primeira e passa `(float)` na segunda: **idêntica ao 5.6 original em 10 casos, nos dois runtimes**.
- Propriedade sobre `null` em `emp4_inforetencao.php:109` → o `stdClass` que o 5.6 criava.

Bateria 439/458 → **458/458**. LSP: 846 de 863 com `extends` carregam nos dois depois das autenticadoras. Passo 6c:
2.660 pares. Roteamento: `emp` no `location` e nas três cópias do critério; o `map` perdeu as 13 telas `emp` que a
Fase B de Patrimonial tinha posto lá. Passo 8b (360 telas do Financeiro no 8.5): nada indo ao 5.6.

**Regressão:** o `fpdf151/pdf.php` está em quase todo universo já servido, então a bateria dirigida seria a completa.
**Decisão do usuário (29/10/2026): adiada para a bateria completa do fim da área.** A guarda do `pdf.php` só muda
o caminho em que a consulta a `db_config` falha, onde o 8.5 antes parava com fatal; tela já verificada como idêntica
não passava por ali.

**Lote 3 — `orc`** (Orçamento, 628 telas `.php` em disco, `orc1_`…`orc4_`, roteadas no `location`; mais 2 sobras não
executáveis, `orc2_orcprojeto002.php.sap` e `orc2_reldespesas001.php_novo`). Universo 3.037. Separadores de `split`
todos literais (`"#"` 384, `"-"` 44, `'\.'`, `"\_"`…); `"\_"` conferido no 5.6, idêntico. Rector em **345 arquivos**,
0 na 2ª e na 3ª passada; uma regra **nova** apareceu, `RenameCastRector` (`(real)` → `(float)`): **conferida no 5.6 em 7
casos, idêntica**, aceita (fora da denylist). Remanescentes 0; portão de funções 0 ausentes.

`php -l`: 3 forms **não compilam em nenhum dos dois runtimes, já antes do Rector** (`forms/db_frmcronogramabasereceita.php`,
`db_frmorcprojativsubprojeto.php`, `db_frmppadotacao.php`, "unexpected identifier db_input") — pré-existente, intocado.
Dois só quebravam no 8.5, `break`/`continue` fora de laço, alcançáveis → **`exit;`** (catálogo):
`orc2_orcppaval002.php` (3 `continue`, 277/281/285) e `orc4_importaduplicacao001.php` (2 `break`, 165/226).

Classes 1.032 e escrita 25.379 linhas: só os diffs conhecidos do harness (`ArgumentCountError` dos `.model.php` com
construtor obrigatório — `lancamentoContabil`, `ordemPagamento`, `RequisicaoMaterial`, `solicitacaoCompra` —; `empenho →
datausu` sem sessão; `db_avaliacaogruporespostatrabalhointermitente` sem o `.dd.xml`, que lança no 8.5 e mata o 5.6).

À mão:

- **LSP — 7 filhas de `RelatoriosLegaisBase`** (`model/contabilidade/relatorios/Anexo{DemonstrativoReceitaPublica,
  ProgramaObrasPrestacaoServico,QuadroDotacaoGoverno,ReceitaCorrenteLiquida,ReceitaLegislacao,SeguridadeSocial,
  SumarioGeralReceita}`) declaravam `getDados()` sem o `$trazerConfiguracaoPadrao = true` da mãe → acrescentado na
  filha; carregam nos dois. **Há mais 40 filhas com o mesmo defeito fora deste universo** (esperadas no lote 5, `con`).
  LSP: 432 arquivos com `extends`/`implements`.
- **Forma negada** (passo 6c): 2.508 pares; **8 pontos de auditoria** em `db_orcparamseqcoluna` (3) e
  `db_orcparamseqinfocomplementar` (5), corrigidos com o `negada_corrige.py`; o detector caiu de 7.294 para 7.286.
- **98 guardas `pg_*`** (`null`) pelo ciclo, nenhuma seguida de `===`/`!==` (nem a variável atribuída). Duas fora do
  `orc`: `libs/db_libcontabilidade.php` e `classes/db_assinatura_classe.php`.
- `count(null)` → `count((array)…)` ×3 (`orc1_orcprevrec003:242`, `orc2_reservas002:40/46`); `array_key_exists(k, null)`
  → `(array)` ×2 (`orc2_demmetasanuais002:177`, `orc2_mestfisccompexercant002:182`; no 5.6 `NULL`, e o `!` dá o mesmo).
- `stdClass` que o 5.6 criava ×2 (`orc2_cronogramafisicofinanc002` `$oTotal`, `orc2_convenioIRF1B002` `$oSaldoOrigem`).
- `cal_days_in_month()` ×4 (`orc2_convenioIRF1A/B/C002`, `orc2_resumopedidocategorias002`): `try`/`catch (Throwable)` →
  `false`, o padrão da Educação.
- **NÚCLEO `fpdf151/fpdf.php`, `Cell()`**: altura `''` (4 relatórios `orc` passam `cell(25,'',…)`) era 0 no 5.6 e
  `TypeError` no 8.5. `if (!is_numeric($h)) { $h = (float)$h; }` na entrada — o precedente do `(float)$ln`, no núcleo e não
  na chamada. **Com altura numérica é no-op**, então tela já idêntica não muda de caminho. Sem cópia no `modification/`.
- `substr('')` em `orc2_resumodesp002.php:63` e `mktime()` com mês `null` em `orc2_convenioIRF1C002.php:115`: as duas
  **categorias novas** abaixo.

Bateria 572/628 → **626/628**. As 2 caracterizadas:
- `orc1_orcsuplem005.php` — **quebra nos dois**: `forms/db_frmorcsuplem.php:90` chama `$clorcprojeto->sql_record()` sem que
  ninguém instancie `$clorcprojeto`. Saída idêntica até o fatal; o 8.5 só acrescenta a página "Erro interno". Pré-existente.
- `orc2_orcprevmensalrec002.php` — PDF idêntico salvo o **horário do rodapé**, que fica dentro do fluxo comprimido
  (fora do alcance da normalização do `cmp.py`); conferido descomprimindo os fluxos.

Roteamento: `orc` no `location` e nas três cópias do critério (`location` agora **7.262 arquivos**); o `map` perdeu as 2
telas `orc` de Patrimonial. **Passo 8b** (704 telas do Financeiro no 8.5): 3 telas `orc2_*` abriam no 5.6 duas abas de
Contabilidade, `con2_filtrosrelatorios.php` e `con2_estimativaRenunciaReceita011.php`; o universo delas cabe inteiro no do
`orc` (nada a portar), 2/2 idênticas, postas em `faseb_map_abas.txt` → `map` 811 entradas (587 + 229 abas). Levantamento
refeito: nada indo ao 5.6.

**Regressão:** três trechos fora do `orc` — o `Cell()` do núcleo e as guardas de `db_libcontabilidade` e `db_assinatura`
— só mudam o caminho em que o 8.5 antes parava com fatal (ou, no `Cell()`, altura não numérica). Pela decisão do lote 2,
ficam para a **bateria completa do fim da área**.

### CATEGORIA NOVA (orc): `substr()` de string vazia é `false` no 5.6 — e `false == '0'` é verdadeiro

```
                          5.6       8.5
substr(null, 0, 1)        false     ""
substr('',   0, 1)        false     ""
false == '0'              true      —
""    == '0'              —         false
```

`orc2_resumodesp002.php:63`: `$nivelele = substr($nivelele,0,1)`, com `$nivelele` ausente. No 5.6 o `false` casa
`if ($nivelele=='0')` e o relatório vai pelo `$tipo_rel = 1`; no 8.5 vai pelo `$tipo_rel = 2` e o PDF sai com outro layout
(uma linha "Total" a mais) — **saída diferente sem erro nenhum**, só a bateria pega. Correção fiel, só na linha que
divergiu: `((string)$x === "" ? false : substr($x,0,1))`, igual ao 5.6 original em 6 entradas (`null`, `''`, `'0'`, `'3'`,
`'45'`, `0`) nos dois runtimes. Parente da do RH (`substr()` de data vazia → `false` → 0 no `mktime`). **Não varrer em
massa:** só muda resultado quando o `false` é comparado com `'0'`/`0`/`''` ou testado com `===`.

### CATEGORIA NOVA (orc): `mktime()` com argumento `null` significa AGORA no 8.5

```
mktime(0,0,0, null, 0, 2026)     5.6: mes 0 -> 30/11/2025     8.5: mes atual -> 30/09/2026 (em 30/10)
```

Desde o PHP 8.0 os parâmetros do `mktime()` são `?int` e `null` quer dizer "o valor atual" — a mesma família do
`date($fmt, null)` do `dvr`. `orc2_convenioIRF1C002.php:115` (mês do trimestre que o `switch` não preencheu) imprimia
outra data no cabeçalho. Guarda **só para `null`**: `($m === null ? 0 : $m)`. `(int)` não seria fiel, porque `''` no 5.6 faz
o `mktime()` devolver `false`, não tratar como 0. Medido em 4 entradas. **O resultado depende do dia em que roda**, então a
divergência pode sumir num mês e voltar no outro: tela com `mktime`/`date` sobre variável que pode faltar merece desconfiança.

**Estado:** lote 3 concluído.

**Lote 4 — `cai` inteiro** (Caixa, 740 telas `.php` em disco: `cai1_` 274 + **`Cai1_` 6, com maiúscula** — o `location` é
`~*` e o `cmp.py` usa `re.IGNORECASE`, então entram —, `cai2_` 162, `cai3_` 101, `cai4_` 202; mais 5 sobras não executáveis:
`.phpsap`, `.php.orig`, `.php.alterado`, `.php.bk2403`, `.phpant`). Universo 3.988. Separadores de `split` todos literais
(`"#"` 217, `"P"` 36, `","` 25, `"R"` 18, `"N"` 14…); `"\/"` conferido no 5.6 em 5 casos, idêntico.

**Denylist do Rector: 6º crescimento — `MultiExceptionCatchRector`.** Juntou dois `catch` de corpo igual em
`cai4_arrecada007.php` em `catch (BusinessException|Exception $e)`, **sintaxe de PHP 7.1, parse error no 5.6**. Nunca tinha
disparado: é o primeiro arquivo da base com dois `catch` idênticos em sequência. Pego no dry-run, antes de aplicar.
Rector em 273 arquivos, só regras já vetadas depois disso (197 `parse_str`+`extract`, 80 `ereg`/`split`, 57 construtores,
53 guardas, 1 parâmetro opcional, 1 offset `{}`, 1 `${$var}`), 0 na passada seguinte.

`php -l`: 3 arquivos só quebravam no 8.5 (nenhum em nenhum dos dois antes):
- **Octal inválido, 4ª aparição** — `cai2_devedores_002.php:353/355/362`, larguras de coluna `array(090,045,050)`: `090` e
  `085` valem **0** no 5.6 (para no 1º dígito inválido) → escritos `0`, conforme o catálogo (`045`/`050`/`060` são octais
  válidos e ficaram). O Rector **não processava o arquivo** ("Invalid numeric literal") e o `enumera.py` não detecta octal:
  só o `php -l` do 8.5 apontou. Corrigido o octal, o Rector portou o arquivo na passada seguinte.
- `break` fora de laço, alcançável (caminhos de erro) → `exit;`: `cai4_anularslip001.php:160`,
  `cai4_processadebconta001.php:212/338`.
- 2 `while (list() = each())` em `cai2_correceitas002.php` (nenhuma regra converte) → a forma `key`/`current`/`next` +
  `is_array` medida no RH.

Classes 1.256 e escrita: só os diffs conhecidos do harness (`ArgumentCountError`, agora também `planilhaCaixa`;
`empenho → datausu`; o `.dd.xml` do eSocial). LSP 761/761. Forma negada: 3.080 pares, 0 divergentes.

Bateria 660/740 → **739/740**. À mão:
- **~164 guardas `pg_*`** (`null`) pelo ciclo, nenhuma seguida de `===`; fora do `cai`: `forms/db_frmcaitransflanc.php`,
  `forms/db_frmconcbanc.php`, `forms/db_frmconcbanc_manual.php` e **`model/regraEmissao.model.php`** (alcançado pela emissão
  de recibos do Tributário). Mais 3 `pg_result(db_query(...),0,"col")` em `cai3_gerfinanc004` (consulta vai para variável,
  forma de Patrimonial) e 1 `pg_free_result(false)` (`cai3_gerfinanc033:95`; `NULL` no 5.6).
- **CATEGORIA NOVA (abaixo): `pg_result()` com coluna que não existe no resultado** — ~41 linhas em `cai3_gerfinanc004/013`.
- **10ª manifestação da RFC das comparações — `cai4_recibo003.php:182`, `$valor[$i] == 0`** com `$valor = array('')`: no 5.6
  `'' == 0` é verdadeiro e a tela redireciona para "Recibo com valor zerado"; no 8.5 passava reto e tentava um
  `insert into recibo` com valores vazios (que falhou — **sem linha de teste deixada**, conferido; `nextval` não consumido).
  Guarda `(is_string($x) && !is_numeric($x) ? (float)$x == 0 : $x == 0)` — **não** o `? true :` do precedente do `db_select()`:
  em valor monetário `"1,5" == 0` é **falso** no 5.6 (vale a parte numérica inicial), e o `? true` erraria. Medida em 14 valores
  (inclusive `"0,00"`, `"1,5"`, `"1abc"`, `" 1"`, `"f"`): **8.5 com a guarda = 5.6 original em todos**.
- `mktime()` com `substr()` de data vazia → `(int)` em cada `substr` (precedente do RH), só nas linhas que apareceram:
  `cai3_gerfinanc004:44/258/261`, `cai3_gerfinanc013:48`, `cai3_gerfinanc027:36`.
- Divisão por zero (`cai3_gerfinanc063:152`, `round($valtotal/$ultparc)`) → `($ultparc ? … : false)`; `round(false)` = 0 no 5.6.
- `cal_days_in_month()` (`cai4_modelo6delibtcerj002:27`) → `try`/`catch (Throwable)`.
- **Constante indefinida** `@Ik23_obs` (`cai4_processacanc003:90`, o `$` esquecido): no 5.6 vira a string `"Ik23_obs"`
  (medido), no 8.5 é `Error` mesmo com `@` → escrita a string `'Ik23_obs'`.
- `cai3_extrates002.php:42-49`: `db_query(...) . " inner join ..."` — o resultado é **concatenado** a um pedaço de SQL, então no
  5.6 `$des` é sempre string ("Resource id #N …" ou só o pedaço) e o `pg_result($des,0,0)` devolve `NULL`. No 8.5 o objeto
  `PgSql\Result` nem converte para string. Correção: `$des` vira `""` quando objeto e o `pg_result` só roda sobre não-string —
  `NULL` sempre, como no 5.6. Bug pré-existente (a descrição da conta nunca sai no extrato), preservado.

Caracterizada: `cai2_receisub002.php` — **quebra nos dois**: `$clagata->api` com `$clagata` nunca criado (conferido por sonda:
`NULL` nos dois runtimes). O 5.6 morre sem saída; o 8.5 mostra "Erro interno". Pré-existente.

Roteamento: `cai` no `location` e nas três cópias do critério (`location` agora **8.007 arquivos**); o `map` **perdeu as 108
telas `cai`** que Tributário, RH e Patrimonial tinham posto lá (811 → **703**: 479 telas + 229 abas). Elas estão entre as 740
da bateria, idênticas. **Passo 8b** (882 telas do Financeiro no 8.5): nada indo ao 5.6.

**Regressão:** fora do `cai`, as guardas de `regraEmissao.model.php` e dos 3 forms só mudam o caminho em que o 8.5 antes
parava com fatal, e o resto do universo é Rector de regras vetadas. Ficam para a **bateria completa do fim da área**.

### CATEGORIA NOVA (cai): `pg_result()` com nome de coluna que não está no resultado

```
                                 5.6                 8.5
pg_result($r, 0, "inexistente")  false (Warning)     ValueError "Argument #3 must be a field name from this result set"
pg_free_result(false)            NULL (Warning)      TypeError
```

Parente da guarda `pg_*` sobre resultado falso, mas aqui o resultado **é válido**: a consulta devolveu outras colunas (em
`cai3_gerfinanc004/013`, aberta sem parâmetros, o laço percorre um resultado sem `k00_numpre`, `vlrmulta`, `total`...). O
`guarda_ciclo.py` não pega, porque a variável não é falsa. Correção, linha a linha na aparição:
`(pg_field_num($r,"col") >= 0 ? pg_result($r,$l,"col") : false)` — `pg_field_num` devolve `-1` nos dois runtimes; medida igual
ao 5.6 com coluna existente e inexistente. O `false` alimenta `+=`, `!=` e `Cell()` exatamente como no 5.6. Ciclo próprio,
**`scratchpad/campo_ciclo.py`** (versionado), alternado com o `guarda_ciclo.py` até a tela parar de fatalar: uma guarda expõe a próxima.

**Estado:** lote 4 concluído.

**Lote 5 — `con`, só as telas do Financeiro** (pelo `map`). O banco atribui ao Financeiro **322 telas `con`** de menu: 1 já
estava no `map` e **8 não existem em disco** (`con1_conplanoextra001/002/003`, `con4_gerarsicomanual`, `con4_gerarsicommensal`,
`con4_sicomidentificadorunidade`, `con4_sicominformacaocomplementar`, `con4_sicomriscofiscal` — entradas de menu órfãs, como as
`cad1_iptupadrao*` do Tributário) → **313 telas**, o número do plano. Universo 3.053 (`TELAS=@`). Separadores todos literais;
o `"\t"` (tabulação real) conferido no 5.6 em 5 casos, idêntico. Rector em **144 arquivos**, só regras vetadas (104
`parse_str`+`extract`, 37 `ereg`/`split`, 34 guardas, 29 construtores, 1 `${$var}`), 0 nas duas passadas seguintes; portão 0
ausentes; remanescentes 0; `php -l` 3.053/3.053 nos dois. Forma negada: 2.531 pares, 0 divergentes.

**LSP — 21 classes** que carregam no 5.6 e não no 8.5 (614 arquivos com `extends`/`implements`):
- **18 filhas de `RelatoriosLegaisBase`** com `getDados()` sem o `$trazerConfiguracaoPadrao = true` da mãe (as "40 pendentes"
  do lote 3 — as do universo deste lote; `BalancoFinanceiroDCASP2017` herda de `…2015` e se resolveu com ela). Mesma correção.
- `AnexoIVDemonstrativoRPPS::executarBalanceteDaReceita()` e `::executarBalanceteVerificacao()` sem os parâmetros opcionais da
  mãe → copiados (a 2ª só apareceu depois de corrigida a 1ª: uma correção LSP expõe a próxima, porque o PHP para na primeira).
- **CATEGORIA (LSP): a filha ESTREITA o tipo do parâmetro** — `PadArquivoEscritorTXT::criarArquivo(iPadArquivoTXTBase $o)`
  contra `PadArquivoEscritor::criarArquivo(iPadArquivoBase $o)`, com `iPadArquivoTXTBase extends iPadArquivoBase`. No 5.6 é só
  `E_STRICT`; no PHP 8 viola a contravariância e a classe nem é declarada ("Could not check compatibility" quando a interface
  ainda não carregou, "must be compatible" quando já). Quebrava a RPC `con4_processarsigfis.RPC.php` (5.6: `{"status":1,...}`;
  8.5: "Erro interno"). Correção mínima: a filha declara o tipo da mãe. Só muda algo se um objeto `iPadArquivoBase` que não é
  TXT for passado — onde o 5.6 dava erro e o 8.5 aceitaria —, e o único chamador passa sempre classes `Sigfis*` TXT.
  Armadilha à parte: o arquivo é `iPadArquivoTxtBase.interface.php` (`Txt`) e a interface `iPadArquivoTXTBase` (`TXT`) — um
  `grep` sensível a caixa diz que ela não existe.
- Os outros `FATAL` (`ICalculoMediaRubrica`/`ISistemaConta` não encontradas, `DisponibilidadeCaixaRestosPagar`,
  `RubricaMapeador`) falham **nos dois** runtimes: o harness carrega o arquivo isolado. Não são regressão.

Bateria **313/313 na primeira rodada** — nenhuma guarda `pg_*` necessária.

**Roteamento:** `gera_map_faseb.py … financ:con` → `map` **+313, −0 = 1.016 entradas** (800 telas + 229 abas). **O nginx recusou
o `map`**: "could not build map_hash, you should increase map_hash_bucket_size: 64" → `map_hash_bucket_size 128;` no
`nginx.conf`, antes dos `map`. E um tropeço de procedimento: o teste encadeado como `nginx -t | tail -1 && up` recriou o proxy
**com a config quebrada** (o `&&` olhou o status do `tail`) — ~1 min fora do ar, sem efeito na bateria (que usa as portas diretas).
A skill agora traz o teste correto, sem pipe.

**Passo 8b (1.248 telas do Financeiro no 8.5): 77 telas `con` abrem 86 abas/destinos ainda no 5.6** — os iframes de
parâmetros dos relatórios legais (`con2_*011.php`, `con2_conrelinfo001.php`, `con2_conrelparametros.php`), as abas dos cadastros
do plano de contas (`con1_conplano004/011/022/033`, `con1_congrupo*`, `con1_planocontapcasp*`…), `con4_processapad.php` e o
redirecionamento `con2_anexo16_001 → con2_anexoXVI_001`. **Pelo plano aprovado, ficam para o lote 6** ("abas do passo 8b"):
refazer `redirecionamentos.py <SID> out.tsv FINAN` regenera a lista.

**Estado:** lote 5 concluído.

**Lote 6 — `hab`, `age`, `pro` + as abas do passo 8b** (pelo `map`). Restavam do Financeiro, fora do `con`, só **5 telas de
menu**: `hab1_workflow001/002/003`, `age4_atuasam30`, `pro4_parcelamentos001` (as `cad`/`sys` do Financeiro já estavam no `map`
pelo Tributário). Somadas às **86 abas/destinos** do passo 8b do lote 5: **91 telas**, universo 2.535. Separadores literais;
o `"\r\n"` conferido no 5.6 em 5 casos, idêntico. Rector em 66 arquivos, só regras vetadas (38 `parse_str`+`extract`, 48
`ereg`/`split`, 25 construtores, 5 guardas, 2 parâmetros opcionais, 1 `${$var}`), 0 na passada seguinte; portão 0 ausentes;
remanescentes 0.

À mão:
- **CATEGORIA NOVA: comentário `/*` sem fechamento** — `con2_lrfdispcaixa002.php:435`. No 5.6 é só aviso e **o resto do arquivo
  vira comentário** (inclusive o `$pdf->Output()` e o `?>`: o relatório nunca emite o PDF — bug pré-existente); no PHP 7+ é
  parse error, e o Rector nem lia o arquivo ("Unterminated comment"). Correção fiel: fechar o comentário **no fim do arquivo**,
  mantendo comentado exatamente o que o 5.6 ignorava. Idêntico nos dois; depois disso o Rector portou o arquivo.
- **LSP — 10 filhas de `RelatoriosLegaisBase`** com `getDados()` sem o parâmetro da mãe (`AnexoXIII/XIV/XV/XVI/XVIIBalancoGeral`,
  `AnexoXVILRF`, `AnexoIFSICONFI`, `DemonstrativoDespesaEducacao/Saude`; a `AnexoXVI` veio do 2º nível). Com as 7 do lote 3 e as
  18 do lote 5, são **35** corrigidas; as restantes das 47 contadas no lote 3 não estão em universo servido.

`php -l`: **22 relatórios `con2_lrf*`/`con2_anexo16_002`/`con2_opercredito002` não compilam em nenhum dos dois, já antes do
Rector** — passagem por referência na chamada (`assinaturas(&$pdf, …)`, "Call-time pass-by-reference has been removed", fatal
desde o PHP 5.4). Pré-existente, intocado: as abas que os chamam quebram igual nos dois.

Bateria **91/91 na primeira rodada**. Roteamento: lote `financ:con,hab,age,pro` no `gera_map_faseb.py` e as 86 abas em
`faseb_map_abas.txt` → `map` 1.107. **Passo 8b refeito achou um 2º nível**: 5 destinos abertos pelas abas novas e pelas
`hab1_workflow` (`con2_anexoXVI_011`, `hab1_workflow004/005/006`, `hab1_workflowativ001`). O universo deles tinha 3 arquivos
fora do do lote, entre eles mais uma filha LSP (`AnexoXVIBalancoGeral`, corrigida); 6/6 idênticas (com o
`con2_anexoXVI_002_2011` que elas abrem). Postos em `faseb_map_abas.txt` → **`map` 1.112 entradas** (805 telas + 320 abas).
Levantamento refeito (1.344 telas do Financeiro no 8.5): **nada indo ao 5.6**.

**Incidente: DISCO CHEIO (30/10/2026).** Ao gravar este registro, `/` chegou ao limite (66 de 69 GB; o que sobra é a reserva
de 5% do ext4, só para root). Efeitos: (1) **este arquivo foi truncado para 0 bytes** — restaurado do commit e o texto
reaplicado; (2) **o PostgreSQL caiu** ("não foi possível escrever no arquivo base/16391/29243"), mas o container só **parou**, sem
ser removido, então os dados ficaram. Liberado com `docker builder prune` (1,4 GB de cache de build, autorizado pelo usuário; o
`image prune` não liberou nada — as imagens "recuperáveis" têm tag e só sairiam com `-a`). Banco religado: WAL refeito, checkpoint
de fim de recuperação, consultas e telas respondendo nos três endereços. Conferido depois: nenhum arquivo alterado ficou vazio e
o `php -l` deu o mesmo resultado nos dois runtimes. **Lição: o banco sem volume de persistência sobrevive a parar, não a ser
removido — e disco cheio o derruba sem aviso; conferir `df -h /` antes da bateria completa.** Depois, a pedido do usuário, removido o *worktree*
do TCC de referência (`ecidade/tmp/tcc_gerson`, 1,1 GB; ver `trabalho-relacionado.md`) → **2,3 GB livres**.

**Estado:** lote 6 concluído — **todos os lotes do Financeiro portados e roteados** (commits locais). Falta a etapa do fim da
área: bateria completa (todos os prefixos do `location` + o `map` inteiro, com as regressões adiadas dos lotes 2, 3 e 4), a
conferência pelo proxy de todas as telas de menu do Financeiro, e só então o envio. **O usuário pediu para sinalizar e esperar
antes da bateria final.**

**Bateria completa do fim da área (30/10/2026, autorizada pelo usuário):** todos os prefixos do `location` (7.994 telas,
`iss4_siss002` pulada) e o `map` inteiro. **`map` 1.112/1.112.** `location` **7.930/7.994** (62 divergentes + 2 timeouts):
- **28 já registradas**, conferidas nome a nome (ou pelo grupo em que o registro as descreve): as da Educação (`edu1_*002/003`
  que quebram no 5.6, as 8 do Censo/INEP do `edu4`, fragmentos `bib2_comprovantemodelo_*`), as do Tributário (`agu`, `fis`,
  `iss`, `cai2_receisub002`, `cai3_gerfinanc013`), o timeout de `rec2_espelhoponto002` e as 2 do Financeiro registradas no
  lote 3 (`orc1_orcsuplem005`, que quebra nos dois; `orc2_orcprevmensalrec002`, horário no fluxo comprimido do PDF).
- **36 do `tra`** (todas as telas `tra*_` com saída): 500 só no 8.5, `ArgumentCountError: parse_str() expects exactly 2
  arguments` — `parse_str($HTTP_SERVER_VARS["QUERY_STRING"])` com 1 argumento. **Não é regressão do Financeiro:** os
  arquivos não mudam desde a reorganização do repositório (o piloto `tra` foi portado antes de o `parse_str` virar categoria,
  e não tocou estas telas), e nenhum include que roda antes da linha (`db_stdlib`, `db_conecta`, `db_sessoes`) mudou desde
  a base da branch; o resultado não depende do módulo da sessão. É a pendência "o `tra`, órfão" já listada na linha de base
  do Patrimonial — as baterias anteriores não a contavam. Fica para decisão do usuário (órfão no menu).
- Nenhuma regressão nova; as regressões adiadas dos lotes 2, 3 e 4 (`fpdf151/pdf.php`, `Cell()`, `db_libcontabilidade`,
  `db_assinatura`, `regraEmissao`) não apareceram.
