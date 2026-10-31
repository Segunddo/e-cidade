# Área Saúde (branch `6saude-migrado`)

### 📐 Dimensionada e dividida em lotes (31/10/2026)

`scratchpad/dimensiona.py` (depois do Financeiro): **489 telas de menu faltando**, 0 fantasmas, **530 a alterar** pela
estimativa a partir das telas. Ver `dimensionamento.md`.

8 módulos no banco (telas faltando por módulo; uma tela pode estar em mais de um): Ambulatorial 206, Farmácia 102,
Laboratório 74, Agendamento 38, TFD 37, Vacinas 33, fumam 15, Hiperdia 7.

| Prefixo | Telas da Saúde faltando | Telas de outras áreas pendentes | Em disco | A alterar (prefixo inteiro, isolado) |
|---|---|---|---|---|
| `sau` | 221 | — | 629 (`sau1_` 355, `sau2_` 116, `sau3_` 34, `sau4_` 121, `sau_` 3) | 533 |
| `far` | 100 | — | 192 | 228 |
| `lab` | 71 | — | 195 | 171 |
| `tfd` | 34 | — | 84 | 118 |
| `vac` | 30 | — | 80 | 136 |
| `fum` | 15 | — | 24 | 22 |
| `amb` | 13 | 1 (Configuração) | 31 (inclui 6 `Amb1_`) | 31 |
| `age` | 1 | — | 14 | 24 |
| `hip` | 1 | — | 2 | 13 |
| `mat` | 3 | 1 (Configuração) | (prefixo do Patrimonial) | via `map` |

Variantes conferidas (`ls | grep -ioE '^<pref>[a-z]*[0-9]*_'`): só `sau_`, `far_` e `Amb1_`, todas cobertas por `[0-9]*_` com `~*`.
**União dos alvos dos prefixos inteiros: 903** (130 arquivos em mais de um prefixo) — bem acima dos 530 da estimativa por
telas, porque o prefixo inteiro alcança popups, RPCs e relatórios fora do menu. O real tende a sair acima (Financeiro: 601
previstos, 1.168 pelo Rector + ~420 à mão).

#### Divisão em lotes (aprovada pelo usuário, 31/10/2026)

| Lote | Prefixos | Em disco | A alterar (isolado) | Roteamento |
|---|---|---|---|---|
| 1 | `fum`, `hip`, `age`, `amb` | 71 | ~90 | `location` (a tela `amb` da Configuração vai junto) |
| 2 | `tfd`, `vac` | 164 | ~250 | `location` |
| 3 | `lab` | 195 | 171 | `location` |
| 4 | `far` | 192 | 228 | `location` |
| 5 | `sau1_` | 355 | parte dos 533 | `location` (`sau1_`) |
| 6 | `sau2_`, `sau3_`, `sau4_`, `sau_` | 274 | resto dos 533 | `location` (`sau` inteiro ao fim) |
| 7 | as 3 telas `mat` + abas do passo 8b | — | pequeno | `map` |

**Decisões do usuário (31/10/2026):** `sau` em **dois lotes** (`sau1_` separado); ordem **do menor para o maior**, como no
Financeiro. Valem as regras de sempre: um lote por vez (relatar e esperar o pedido do próximo), bateria completa só no fim
da área, envio só depois dela.

**Estado:** dimensionada; aguardando o pedido do lote 1.
