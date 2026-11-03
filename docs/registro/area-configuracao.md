# Área Configuração (branch `7configuracao-migrado`)

### 📐 Dimensionada e dividida em lotes (03/11/2026)

Branch criada a partir da `6saude-migrado`, como as anteriores (o usuário cogitou uma branch unificada; medido que a
`6saude-migrado` já contém as cinco anteriores e o `master` — a cadeia está empilhada —, e decidido manter o esquema de
sempre).

`scratchpad/dimensiona.py` (depois da Saúde): **185 telas de menu faltando** (204 em disco), 1 módulo (Configuração),
**98 a alterar** descontadas as 11 classes do falso positivo. **5 fantasmas:** `con1_leituraformulario001`,
`con1_organograma001/002`, `con2_organograma`, `con4_atualizapatch001`.

| Prefixo | Telas da Configuração | Outras áreas pendentes | A alterar (só as telas) | A alterar (prefixo inteiro) |
|---|---|---|---|---|
| `con` | 156 | Cidadão (4) | 80 | 437 (1.559 arquivos) |
| `sys` | 22 | — | 19 | 53 (86 arquivos) |
| `ate` | 3 | — | 0 | 205 (209 arquivos) |
| `hab` | 2 | Assistência Social (15) | 0 | — |
| `mat` | 1 | — | 2 | — |
| `pro` | 1 | — | 0 | — |

#### Divisão em lotes (aprovada pelo usuário, 03/11/2026)

| Lote | Conteúdo | Roteamento |
|---|---|---|
| 1 | **`sys` inteiro** + as 7 telas soltas (`ate` ×3, `hab` ×2, `mat`, `pro`) | `sys` no `location` (as telas `sys` saem do `map`, como o `cai` no Financeiro); as soltas pelo `map` |
| 2 | `con`, só as 156 telas da Configuração | `map` (o `con` inteiro fica para depois do Cidadão, decisão do Financeiro) |
| 3 | abas e destinos do passo 8b | `map` |

**Decisões do usuário:** `sys` inteiro pelo `location`; 3 lotes. Valem as de sempre: um lote por vez, bateria completa só
no fim da área, envio só depois dela.

**Disco (03/11/2026): 1,3 GB livres.** O log do container `ecidade_database` tem ~2,6 GB (erros de SQL das baterias e o
`log_statement='all'` do nível 3). Não dá para limitar recriando o container (o banco não tem volume de persistência);
pedido ao usuário `sudo truncate -s 0 $(docker inspect -f '{{.LogPath}}' ecidade_database)` antes da próxima bateria.

**Estado:** dimensionada; aguardando o pedido do lote 1.
