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

**Estado:** lote 3 concluído. Aguardando o pedido do lote 4 (`cai` inteiro).
