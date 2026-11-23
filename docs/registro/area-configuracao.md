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
| 2 `con` (156 telas) | 2.421 | 68 Rector + 4 guardas à mão | 2.421/2.421 | 436/436 (13 falham nos dois) | 975 (diffs só do harness) | diffs só do harness | 2.426 pares, 0 div. | **156/156** |
| 3 abas (42 destinos) | 1.195 | 2 Rector + 1 guarda à mão | 1.195/1.195 | 282/282 (10 falham nos dois) | diffs só do harness | 0 fora dos conhecidos | 1.201 pares, 0 div. | **42/42** |

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

**Lote 2 — as 156 telas `con` da Configuração** (pelo `map`; 03/11/2026). 90 alvos, 79 reais. `split()`: 90 `"#"`, 2 `":"`,
1 `"\\."`, `"\\n"`, `"_"`, `"P"` — literais. Rector em **68 arquivos**, só regras vetadas (42 `parse_str`, 25 `split`, 23 guardas,
23 construtores, 1 `OptionalParametersAfterRequired` em `cl_db_auditoria::sql_query_acessos`, **sem subclasses** na base), 0 na
2ª passada. Remanescentes 0: os 3 `split` que sobram em `con3_usuonline002.php` estão dentro de um comentário `/* … */` (linha
86), e os 2 `each()` de `con4_registrosinconsistentes003.php` são JavaScript (`array.each(function…)`). Lint 2.421/2.421 nos
dois; portão 0; carga 436/436.

**Verificado no caminho: o Rector lê tag curta `<?`** (`short_open_tag` ligado nos dois runtimes) — testado com um arquivo
mínimo nas duas formas. A suspeita veio do `con3_usuonline002`, que só tem `<?`; a causa era o comentário.

Bateria 154/156 → **156/156**. À mão, alternando `campo_ciclo.py` e `guarda_ciclo.py`: `con1_caditens.php:443/444`
(`pg_result(…, "libcliente")` sem a coluna → `false`; `false == "f"`/`"t"` é falso nos dois) e `con3_acount.php:82/101`
(`pg_numrows(false)` em `for`).

Bateria dirigida: **nenhuma tela servida fora do lote** usa as 23 classes alteradas — são de uso restrito (ajuda, versão,
tarefas, regras de acesso, auditoria). Conferido à mão que as de uso geral não estão entre elas: `cl_db_config` (222 telas) e
`cl_db_depart` (132) não mudaram; mudaram só as telas `con1_db_config005/006` e `con1_db_depart002/003`, que são abas.

Roteamento: lote **`conf:ate,hab,mat,pro,con`** no gerador → **`map` 1.270 entradas** (+156). As 156 conferidas pelo proxy
(`/w/2/`): **156/156 no 8.5**; `login` → 5.6.

**Passo 8b (215 telas da Configuração no 8.5): 47 ligações a 42 destinos no 5.6** — as abas `*004/005/006` dos cadastros
`con1_` (`caddocumento`, `db_config`, `db_estrutura`, `db_layouttxt`, `db_sysfuncoes`, `db_sysregrasacesso`, `db_usuarios`,
`db_versao`), `con1_db_depart*`/`con1_db_departender*` (abas de `con1_depart00x`), `con1_db_imagens001`, `con1_workflow005`,
`con3_db_syscampo002`, `con3_usuonline002`, `con4_carnes002`, `con4_docpadrao002/004`, `con4_docparag002/004`,
`func_conspermissaoempenho.php`, `hab1_avaliacao004/006` e as `ate1_atendcadarea004/005/006` do lote 1. Lista em
`ecidade/tmp/conf3_abas.txt`. **São o lote 3**, conforme o plano; até lá funcionam pelo 5.6 (sessão compartilhada).

**Lote 3 — as abas do passo 8b** (42 destinos distintos das 47 ligações dos lotes 1 e 2, todos existentes, nenhum já
servido; 03/11/2026). Universo 1.195; 16 alvos, **5 reais**, e destes só 2 mudaram: Rector em `con1_db_versao004.php`
(`parse_str` + `split("P")`, literal) e `con3_db_syscampo002.php` (`parse_str`); `db_caddocumento`/`db_orcunidade` já
estavam portadas (o Rector não as tocou) e `con3_usuonline002` é o `split` comentado. Remanescentes 0; lint 1.195/1.195; carga
282/282; forma negada 1.201 pares, 0 div.

Bateria 39/42 → **42/42**: `con1_db_depart001/002/003` caíam em `forms/db_frmdb_depart.php:161`, `pg_numrows(false)` →
guarda (`guarda_ciclo.py`). O formulário só é usado pelas abas `con1_db_depart*`/`con1_db_departender*`; os outros dois
alterados, só por telas do próprio lote 2 (`con1_db_versao001/001a`, `con3_db_syscampo001`) — nenhuma bateria dirigida.

Roteamento: os 42 em `faseb_map_abas.txt` → **`map` 1.312 entradas**; as 42 conferidas pelo proxy (`/w/2/`): **42/42 no 8.5**.
**Passo 8b refeito: 257 telas da Configuração no 8.5 (menu + abas), nada indo ao 5.6 — sem segundo salto.** Pelo banco:
**204/204** telas de menu da Configuração em disco no 8.5 (+ 5 fantasmas).

### Bateria completa do fim da área (03/11/2026, terça, autorizada pelo usuário)

Todos os prefixos do `location` (9.331 telas; `iss4_siss002` pulada) e o `map` inteiro. **`map` 1.312/1.312** (inclui as 156
telas `con` e as 42 abas desta área). `location` **9.298/9.331** (30 divergentes + 3 timeouts), conferidas nome a nome contra a
bateria final da Saúde:
- **30 da linha de base da Saúde**, as mesmas.
- **Saiu `mer_subitem004`** — como previsto: só diverge em fim de semana (`mktime(null)` = hoje no 8.5; ver `area-saude.md`).
- **Entraram as 2 caracterizadas no lote 1:** `sys3_modulos002` (horário no rodapé do PDF de 813 páginas) e
  `sys4_consultaXML.RPC` (aberto sem `sUrl`).
- **3 timeouts:** os 2 de sempre (`edu4_verifexportcenso002`, `rec2_espelhoponto002`) e `edu4_importacaoatualizacaoaluno002`,
  uma das 8 do Censo/INEP do Educação (laço eterno **no 5.6**); antes aparecia como divergente com o 5.6 em `000`, agora caiu
  no teto de tempo. Mesma tela, mesma causa.

Nenhuma regressão dos 3 lotes da Configuração.

### 🏁 ÁREA CONFIGURAÇÃO CONCLUÍDA (03/11/2026)

Conferido **pelo proxy, tela de menu por tela de menu** (`X-Ecidade-Runtime` em `/w/2/<tela>`), a partir do banco
(`atendcadareamod` → área CONFIGURAÇÃO → `db_menu` → `db_itensmenu`, sem excluir prefixo; nomes resolvidos para a grafia do
disco): **204 de 204** telas de menu servidas pelo PHP 8.5 (209 entradas, 1 módulo). **5 fantasmas** (arquivo inexistente em
todo o repositório, quebram igual nos dois): `con1_leituraformulario001`, `con1_organograma001/002`, `con2_organograma`,
`con4_atualizapatch001`. Abas e destinos (passo 8b): 257 telas examinadas no lote 3, nada indo ao 5.6.

| | |
|---|---|
| Módulos | **1 de 1** — Configuração |
| Lotes | 3, commits locais na `7configuracao-migrado` |
| Alterados | 44 + 68 + 2 pelo Rector + ~205 pontos à mão (35 `each()`, 125+2 `fputs`/`fclose` guardados, 23 guardas `pg_*`/coluna, 3 de tipo) |
| Bateria completa do fim da área | `map` **1.312/1.312**; `location` **9.298/9.331** (todas caracterizadas) |
| Telas de menu pelo proxy | **204/204** no 8.5 (+ 5 fantasmas) |
| Envio ao GitHub | **feito em 03/11/2026** — `origin/7configuracao-migrado` (`a142f5f49`) |
