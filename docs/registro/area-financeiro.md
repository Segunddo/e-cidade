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

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| 1 `cus`+`pla`+`pl`+`tes` | 1.347 | 45 Rector + 2 à mão (+10 do passo 8b) | 1.347/1.347 | 17/17 | 369 linhas, 0 div. | **99/99** |

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

**Estado:** lote 1 concluído. Aguardando o pedido do lote 2 (`emp`).
