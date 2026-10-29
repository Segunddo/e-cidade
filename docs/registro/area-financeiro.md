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

**Estado:** nenhum lote iniciado. Aguardando o pedido do lote 1.
