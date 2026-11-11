# Área Assistência Social (branch `assistencia-social/migracao`)

### 📐 Dimensionada (11/11/2026)

Primeira área depois que as sete anteriores entraram na `base-php84` (PRs #2–#8). A branch **nasce da `base-php84`** (não da
área anterior) e segue o formato `area/assunto` do `CONTRIBUINDO.md` — decisão do usuário.

`scratchpad/dimensiona.py` (depois da Configuração): **57 telas de menu faltando** (68 no menu), 2 módulos (**Social** 44,
**Habitação** 13), **32 a alterar** só pelas telas (descontadas as 11 classes do falso positivo). **1 fantasma:**
`soc1_cidadao003.php`.

| Prefixo | Telas da área faltando | Outras áreas pendentes | Em disco | A alterar (só as telas) | A alterar (prefixo inteiro) |
|---|---|---|---|---|---|
| `soc` | 44 | — | 87 (`soc1_` 8, `soc2_` 42, `soc3_` 17, `soc4_` 20) | 4 | **9** |
| `hab` | 13 | — | 52 (`hab1_` 41, `hab2_` 2, `hab4_` 9) | 28 | **33** |

Nenhuma outra área pendente (Cidadão, Integrações, Gestor) usa `soc` ou `hab`. Hoje há **13 telas/abas `hab` no `map`**
(`hab1_workflow*` do Financeiro, `hab1_avaliacao*` da Configuração); com o prefixo inteiro no `location`, saem do `map`.

#### Divisão (aprovada pelo usuário, 11/11/2026)

**Um lote só: `soc` e `hab` inteiros pelo `location`** (~42 a alterar; 139 telas na bateria). As abas desses prefixos vão junto
com o `location`. Valem as regras de sempre: bateria do lote, bateria completa no fim da área, conferência pelo proxy, e o envio
(PR para a `base-php84`) só depois.

**Estado:** dimensionada; aguardando o pedido do lote.
