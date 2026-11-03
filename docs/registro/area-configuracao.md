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

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Carga (LSP) | Classes | Escrita | Forma negada | **Bateria** |
|---|---|---|---|---|---|---|---|---|
| 1 `sys` + 7 soltas | 1.897 | 44 Rector + 35 `each()` + 17 guardas `pg_*` + 1 de coluna + 3 de tipo à mão | 1.891/1.897 (6 não compilam em nenhum) | 371/371 (12 falham nos dois) | 776 (diffs só do harness) | diffs só do harness | 2.068 pares, 0 div. | **91/93** (2 caracterizadas) |

**Lote 1 — `sys` inteiro + 7 telas soltas** (93 telas: `sys1_` 11, `sys3_` 7, `sys4_` 69 + `ate1_atendcadarea001/002/003`,
`hab1_avaliacao001/003`, `mat4_reprocessalancamentosaidamaterial001`, `pro4_configuracaotelalogin`; 03/11/2026). 64 alvos, 53
reais. Rector em **44 arquivos**, só regras vetadas (29 `split`, 16 `parse_str`, 12 guardas, 11 construtores), 0 na passada
seguinte. `split()` com escape de regex (`"\\/"`, `'\\('`, `"\\)"`, `"\\|"`, `"#&"`, `"\r\n"`, `" "`, `","`) → `preg_split`:
**medido igual ao `split` do 5.6 em 16 entradas**.

À mão:
- **35 `while (list($k,$v) = each($a))`** em 5 geradores quase idênticos (`sys4_criaestrutura`, `_er`, `_nova`, `_nova_er`,
  `_nova_semer`). As regras `WhileEachToForeach`/`ListEach` estão vetadas (o ponteiro é compartilhado: `$IND` é percorrido
  duas vezes sem `reset()`, e no 5.6 o segundo laço não roda). Forma do RH: `while(is_array($a) && (($k = key($a)) !== null)
  && ((($v = current($a)) || true) && (next($a) || true)))`. **Medida de novo** contra o `each()` do 5.6 em 4 casos (vazio,
  numérico, associativo com `null`/`0`/`''`/`false`, ponteiro no meio), cada um com o segundo laço sem `reset()`: igual nos dois.
- **17 guardas `pg_*`** (`guarda_ciclo.py`) em 10 telas (`sys3_campos001`, `sys3_tabelas001`, `sys4_chaveestrangeira001`,
  `sys4_chaveprim001/002`, `sys4_dumpmenus`, `sys4_indices001`, `sys4_processa002/007`, `sys4_verifica002`) e **1 de coluna
  ausente** (`campo_ciclo.py`, `sys4_indices001:140`: `pg_result(…, "campounico")` → `false`, e `false == "0"` é verdadeiro nos
  dois).
- **`sizeof($usuarios)` com `null`** (`forms/db_frmlibimpmax001.php:138`) → `sizeof((array)…)` (catálogo).
- **`array_keys($aRetornoSQL[0])` com `null`** (`sys4_listaretornosql001.php:67`; o array vem de `unserialize($_SESSION[…])`)
  → `(is_array(…) ? array_keys(…) : null)`. **Não `(array)`:** se a linha for objeto, o 5.6 devolve `NULL` e o `(array)`
  listaria as propriedades.
- **`fputs($fd, …)` com `fopen` falho** (`sys4_processa004.php`, gerador que grava `func_<tabela>.php` na raiz da aplicação,
  não gravável pelo Apache aqui): no 5.6 cada `fputs(false)` avisa e o script segue até "Concluído...", no 8.5 o primeiro é
  fatal → **`$fd && fputs($fd, …)`** nas 125 linhas e `$fd && fclose($fd)` nas 2. Com o `fopen` funcionando, nada muda.

Não compilam em **nenhum** dos dois (pré-existentes, intocados): `sys4_criafontes`, `sys4_criafontes_geral`, `sys4_criafuncao`,
`sys4_criafuncao_geral`, `sys4_geradebitos002`, `sys4_processa008`. **Geradores de código que emitem PHP 5:**
`sys4_criaclasse001` escreve `split("#", …)` nas classes que gera, e `sys4_processa006` escreve `parse_str(…)` de 1 argumento —
o texto gerado é igual nos dois runtimes (mudar seria mudar a saída do 5.6), mas **o código que essas ferramentas produzem só
roda no 5.6**. Registrado para quando o 5.6 for desligado.

Bateria 78/93 → **91/93**. As 2 caracterizadas:
- `sys3_modulos002.php` — PDF de **813 páginas**; 812 diferem só no horário do rodapé ("Data: 19-09-2026 - 17:30:26" ×
  "17:30:31": a geração leva segundos, as duas requisições nunca caem no mesmo segundo). Descomprimidas as páginas: **0
  linhas diferentes fora do rodapé**. Categoria do horário no PDF.
- `sys4_consultaXML.RPC.php` — a bateria o abre sem `sUrl`: `file_get_contents("")` é `ValueError` no 8 (no 5.6, `false`).
  A única chamadora (`scripts/classes/dbXmlEditor.js`) sempre manda `sUrl`; com um `.dd.xml` real, **idêntico**.

Classes e escrita: só os diffs conhecidos do harness. Bateria dirigida: nenhuma tela servida fora do lote usa os 12 arquivos
de `classes/`, o formulário nem o `func_` alterados.

Roteamento: **`sys`** no `location` e nos três scripts (e na `FASE_A`); as 7 soltas pelo `map`, lote **`conf:ate,hab,mat,pro`**
no comando do gerador → **`map` 1.114 entradas** (+7; saiu `sys4_geradorteladinamica001`, agora pelo `location`). Conferido:
`sys1_`, `/w/2/sys4_`, `Sys3_`, as 7 soltas → 8.5; `login`, `con1_` → 5.6.

**Passo 8b achou 5 abas no 5.6** (57 telas da Configuração no 8.5): `ate1_atendcadarea004/005/006` (abas das
`ate1_atendcadarea001/002/003`) e `hab1_avaliacao004/006` (das `hab1_avaliacao001/003`). **Ficam para o lote 3** (abas),
conforme o plano; até lá funcionam pelo 5.6 (sessão compartilhada).

**Estado:** lote 1 concluído (commit local). Aguardando o pedido do lote 2 (as 156 telas `con` da Configuração).
