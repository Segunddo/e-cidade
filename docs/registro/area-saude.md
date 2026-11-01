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

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Carga (LSP) | Classes | Escrita | Forma negada | **Bateria** |
|---|---|---|---|---|---|---|---|---|
| 1 `fum`+`hip`+`age`+`amb` | 1.896 | 26 Rector | 1.896/1.896 | 364/364 (11 falham nos dois) | 785 (diffs só do harness) | 19.640 linhas, diffs só do harness | 2.216 pares, 0 div. | **71/71** |

**Lote 1 — `fum`, `hip`, `age`, `amb`** (71 arquivos, roteados no `location`; 31/10/2026). Enumerador: 57 alvos, dos
quais **11 são o falso positivo já registrado** no `tra` (`cgm*`, `db_db_uf`, `db_db_userinst`…: portados por commits
`EXPERIMENTO`, que o `PAGO` não reconhece) — o Rector não tocou nenhum. Os 22 `split()` são todos `"#"` literal.
Rector em **26 arquivos**, só regras vetadas (15 `GuardaComparacaoLiteral`, 10 `ParseStrComExtract`, 6 `EregToPregMatch`
— que converte `split("#")` em `preg_split("#\\##m")`, a forma das classes já portadas —, 6 `Php4Constructor`), 0 na 2ª
passada. Remanescentes 0 pelo critério da própria regra (propriedade com padrão inteiro, literal não numérico): uma
contagem sobre **todo** `$this->X == "…"` dá 251, mas são campos de texto, que não precisam de guarda. Portão de funções:
0 ausentes. Nada à mão.

Classes e escrita: só os diffs conhecidos do harness (`RequisicaoMaterial`/`solicitacaoCompra` com construtor obrigatório;
`db_avaliacaogruporespostatrabalhointermitente` sem o `.dd.xml`). Bateria **71/71 na primeira rodada**.

Roteamento: `fum|hip|age|amb` no `location` (e na `FASE_A` do `gera_map_faseb.py`, no `LOC` do `dimensiona.py` e do
`redirecionamentos.py`); `map` regenerado → **1.104 entradas** (saíram `age4_atuasam30` e as 7 `amb`, agora pelo
`location`). `nginx -t` num container descartável antes de recriar. Conferido: `fum1_`, `/w/2/hip2_`, `age4_`, `Amb1_`,
`amb1_` → 8.5; `login.php` e `sau1_` → 5.6. Passo 8b (44 telas da Saúde no 8.5): nada indo ao 5.6 (1 iframe de pasta).

Bateria dirigida: das 16 classes alteradas, 2 (`db_sau_atualiza`, `db_sau_procedimento`) estão no universo do `verif15`
(tudo o que o 8.5 servia na 15ª lacuna), mas só porque 20 classes/modelos citam essas tabelas em SQL; nenhuma tela servida
fora do lote usa as classes alteradas nem esses 20 arquivos (a única é `age4_municipiocotamensalexame001`, do lote).
Nenhuma bateria dirigida a fazer.

**Estado:** lote 1 concluído (commit local). Aguardando o pedido do lote 2 (`tfd`, `vac`).
