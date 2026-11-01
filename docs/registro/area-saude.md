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
| 2 `tfd`+`vac` | 2.194 | 157 Rector + 1 LSP + 1 forma negada à mão | 2.194/2.194 | 375/375 depois da LSP (13 falham nos dois) | 892 (diffs só do harness) | 22.712 linhas, diffs só do harness | 2.541 pares, 1 div. → corrigida | **164/164** |
| 3 `lab` | 1.578 | 105 Rector + 4 guardas `pg_*` + 1 forma negada (formulário) à mão | 1.577/1.578 (1 não compila em nenhum) | 293/293 (12 falham nos dois) | 493 (diffs só do harness) | 12.886 linhas, diffs só do harness | 1.546 pares, 0 div. | **193/195** (2 caracterizadas) |
| 4 `far` | 2.223 | 161 Rector + 1 `magic_quotes` + 1 `break` + 6 guardas `pg_*` à mão | 2.223/2.223 | 389/389 (12 falham nos dois) | 895 (diffs só do harness) | 22.649 linhas, diffs só do harness | 2.511 pares, 0 div. | **192/192** |
| 5 `sau1_` | 2.516 | 306 Rector + 2 `(int)` + 3 guardas de conexão à mão | 2.516/2.516 | 391/391 (12 falham nos dois) | 950 (diffs só do harness) | 23.965 linhas, diffs só do harness | 2.483 pares, 0 div. | **355/355** + dirigida 15/15 + aba 3/3 |
| 6 `sau2_`+`sau3_`+`sau4_`+`sau_` | 2.759 | 107 Rector + 2 ternários + 1 `break` + 22 guardas `pg_*` à mão | 2.759/2.759 | 510/510 (14 falham nos dois) | 1.143 (diffs só do harness) | 28.584 linhas, diffs só do harness | 2.948 pares, 0 div. | **273/274** (1 caracterizada) |
| 7 `mat` (3 telas) | 1.079 | 3 Rector | 1.079/1.079 | 1/1 | 1 classe, 0 div. | 21 linhas, 0 div. | 4 pares, 0 div. | **3/3** |

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

**Lote 2 — `tfd`, `vac`** (164 arquivos, roteados no `location`; 31/10/2026). 177 alvos (os 11 do falso positivo entre
eles, intocados). `split()`: 411 `"#"`, 8 `'#'`, 1 `"/"` — todos literais (um `split('/')` a mais é JavaScript, em
`forms/db_frmtfd_agendaprestsaida.php`). Rector em **157 arquivos**, só regras vetadas (105 guardas, 93 construtores, 86
`split`, 49 `parse_str`, 3 `OptionalParametersAfterRequired` — todas sem tipo, então sem o `?Tipo` do RH), 0 na 2ª passada.
Remanescentes 0; portão de funções 0 ausentes; lint 2.194/2.194 nos dois.

À mão:
- **LSP criada pelo próprio Rector:** a `OptionalParametersAfterRequiredRector` deu `= null` a `$sd04_i_medico` e
  `$sd04_i_unidade` em `cl_cgs_und::sql_query_cgs_profissional` (vinham depois de `$z01_i_cgsund=null`). A filha
  `cl_cgs_und_ext` (`classes/db_cgs_und_ext_classe.php`) declara os dois **obrigatórios** e passou a não carregar no 8.5
  ("must be compatible"). Antes da regra era compatível: no PHP 8 um opcional antes de obrigatórios conta como obrigatório.
  Corrigido espelhando a mãe (`= null` nos dois); as 2 chamadas (`func_cgs_und.php`) passam todos os argumentos. **Lição
  para a skill: a `OptionalParametersAfterRequired` muda a assinatura da MÃE — conferir filhas fora do universo** (a carga
  pegou porque a filha estava nele). As outras 2 ocorrências (`db_impcarne::muda_pag` em `fpdf151/impfarmacia.php`,
  `cl_vac_aplica::sql_query_vacinasnaoaplicadas`) não têm subclasses.
- **Forma negada, o caso de NEGÓCIO previsto:** `cl_cgs_und::alterarExt`, `z01_b_faleceu != ""` — o único dos 89 pares
  medidos no Patrimonial que está no SQL de negócio, registrado então como "Saúde, não servida". Agora no universo:
  `negada.php` 1 divergente em 2.541 (no 8.5 o `UPDATE` incluiria `z01_b_faleceu = '0'`). Guarda da categoria
  (`negada_corrige.py`), decisão já tomada pelo usuário em 29/10; `negada_alvos.py` deixou de listar o par.

Classes e escrita: só os diffs conhecidos do harness. Bateria **164/164 na primeira rodada**. Bateria dirigida (telas
servidas fora do lote que usam algum dos 106 arquivos de `classes/` alterados ou `libs/db_dbf_class.php` /
`fpdf151/impfarmacia.php`): só `amb4_acompanhamentoacs` (lote 1), **1/1**; os dois arquivos de `libs`/`fpdf151` só são usados
por `far` (ainda no 5.6) e pelo próprio lote.

Roteamento: `tfd|vac` no `location` e nos três scripts; `map` regenerado sem mudança (1.104; nenhuma tela `tfd`/`vac`
estava nele). Conferido: `tfd1_`, `/w/2/vac1_` → 8.5; `login`, `far1_`, `sau1_` → 5.6. Passo 8b (131 telas da Saúde no
8.5): nada indo ao 5.6 (4 iframes de pasta).

**Lote 3 — `lab`** (195 arquivos, roteados no `location`; 31/10/2026). 121 alvos. `split()`: 136 `"#"`, 2 `'#'`. Rector em
**105 arquivos**, só regras vetadas (72 `parse_str`, 31 guardas, 28 `split`, 27 construtores, 2
`OptionalParametersAfterRequired`), 0 na passada seguinte. As 2 da regra de parâmetro opcional caíram numa mãe e na filha
(`cl_sau_proccbo::sql_query_procedimento_especialidade`/`sql_query_func` e `cl_sau_proccbo_ext::sql_query_ext`, métodos
diferentes): a carga confirmou que as duas continuam compatíveis — a conferência que a skill passou a pedir no lote 2.
Remanescentes 0; portão 0 ausentes; carga 293/293 nos dois.

- **`lab1_lab_labresp002.php` não compila em nenhum dos dois** (linha 69: `db_botao = true;`, sem o `$`) — o Rector não
  lê o arquivo e o `parse_str` dele fica sem porte. Pré-existente, intocado: a tela quebra igual nos dois.

Bateria 189/195 → **193/195**. À mão:
- **4 guardas `pg_*`** (`guarda_ciclo.py`): `src/Saude/Laboratorio/Repository/ImportacaoRequisicaoInconsistenciaRepository.php`
  117/122 (a 117 compara com `=== 0`: o 5.6 devolve `null` e a guarda também, então `null === 0` é falso nos dois — fiel) e
  `lab2_producao001.php:96`.
- **Forma negada num formulário** (categoria do Patrimonial): `forms/db_frmlab_laboratorio.php:149`,
  `if(@$la02_i_tipo!="")` com `$la02_i_tipo = 0` emitia `js_tipo(0);` só no 8.5 (`lab1_lab_laboratorio002/003`). Guarda do
  catálogo (`!== 0 && !== 0.0`).

As 2 caracterizadas, nenhuma defeito de migração:
- `lab2_mapacoletaconsulta.php` — a bateria a chama **sem parâmetros**: `mktime()` recebe `""` (no 5.6, `false` com aviso;
  no 8, `TypeError`). O formulário (`lab2_mapacoleta001.php`) exige período e laboratório. Pelo caminho real, **5 casos
  idênticos** (dois modelos, setor vazio e preenchido, dois períodos, laboratório vazio). Mesmo caso do `bib1_emprestimo002`
  do Educação. Base sem dados: `laboratorio.lab_laboratorio` e `lab_labsetor` vazias, então o relatório com dados não foi
  exercitado.
- `lab4_resultadomodelo1.php` — fragmento incluído por `lab4_emissaoresultnovo002.php:603` (idêntica), que define
  `$oDadosEstrutura`; aberto sozinho, atribui propriedade em `null`. Mesmo caso dos `bib2_comprovantemodelo_*`.

**DEFEITO DO HARNESS, corrigido: o `cmp.py` cortava a URL no primeiro `&`.** O `curl` roda dentro de `bash -lc` com a URL sem
aspas, e o `&` mandava o resto para segundo plano: `ONLY="tela.php?a=1&b=2"` comparava só `?a=1`. Achado aqui, porque os
casos com parâmetros saíam divergentes pelo `cmp.py` e idênticos pelo `curl` direto. Corrigido com `shlex.quote`. Nenhum
resultado registrado usou `ONLY` com mais de um parâmetro (conferido no registro); a bateria por prefixo não usa parâmetros.

Bateria dirigida: nenhuma tela servida fora do lote usa os 32 arquivos de `classes/`, o repositório de `src/` nem o
formulário alterados. Roteamento: `lab` no `location` e nos três scripts; `map` sem mudança (1.104). Conferido: `lab1_`,
`/w/2/lab4_` → 8.5; `login`, `far1_`, `sau1_` → 5.6. Passo 8b (213 telas da Saúde no 8.5): nada indo ao 5.6.

**Lote 4 — `far`** (192 arquivos, roteados no `location`; 31/10/2026). 184 alvos. `split()`: 254 `"#"`, 2 `'#'`. Rector em
**161 arquivos**, só regras vetadas (95 `parse_str`, 66 guardas, 61 construtores, 56 `split`), 0 na 2ª passada. Remanescentes 0
(um `parse_str` a mais em `far3_consultapaciente002.php:36` está comentado). Portão 0 ausentes; carga 389/389 nos dois.

À mão:
- **`get_magic_quotes_gpc()`** (removida no PHP 8; no 5.6 sempre `false` desde o 5.4, medido): `far2_mapaconsolidado003.php:51`
  → `(false)`. O Rector não a trata.
- **`break` fora de laço** (catálogo): `far4_far_cadacomppachiperdia001.php:587` não compilava no 8.5 (no 5.6 compila e morre
  ao executar; medido: imprime o que veio antes e para) → **`exit;`**, como no `fis` e no `orc`.
- **6 guardas `pg_*`** (`guarda_ciclo.py`), uma por tela: `far2_distribuicao002:282`, `far2_historicopaciente002:140`,
  `far2_historicoprogmedicamento002:135`, `far2_historicoprogpaciente002:136`, `far2_mapaconsolidado003:59`,
  `far2_pacienteprogramatica002:120`. Todas comparadas com `== 0` ou usadas como limite de `for` (`null` nos dois); nenhum `===`.

Classes e escrita: só os diffs conhecidos do harness. Bateria 186/192 → **192/192**. Bateria dirigida: nenhuma tela servida fora
do lote usa os 66 arquivos de `classes/` alterados. Roteamento: `far` no `location` e nos três scripts; `map` sem mudança
(1.104). Conferido: `far1_`, `/w/2/far2_`, `lab1_` → 8.5; `login`, `sau1_` → 5.6. Passo 8b (327 telas da Saúde no 8.5): nada
indo ao 5.6 (9 iframes de pasta).

**Lote 5 — `sau1_`** (355 arquivos, roteados no `location` como `sau1`; 31/10/2026). 328 alvos. `split()`: 384 `"#"`, 2 `'#'`,
4 `"\\|"`, 1 `","`, 1 `"_"` — todos literais; o `"\\|"` (string PHP `\|`, pipe escapado em POSIX) vira
`preg_split("#\\|#m")`, medido idêntico ao `split` do 5.6 em 4 entradas (`a|b||c`, vazio, sem separador, só o separador). Rector
em **306 arquivos**, só regras vetadas (204 `parse_str`, 100 `split`, 92 construtores, 91 guardas, 4 `${$var}`, 4
`OptionalParametersAfterRequired`), 0 na 2ª passada. Conferência das filhas (skill, desde o lote 2): das 3 classes cujas
assinaturas mudaram, só `cl_sau_agendaexames` tem filha (`cl_sau_agendaexames_ext`), que não sobrescreve o método e carrega nos
dois. Remanescentes 0; portão 0 ausentes; lint 2.516/2.516; carga 391/391.

Bateria 353/355 → **355/355**. À mão:
- **Aritmética com string** (catálogo): `forms/db_frmcgs_undoutros.php:99` e `:120`, contadores iniciados com `""` e somados a 1
  (`$conta`, `$conta_sub`) — `TypeError` no 8. **`(int)`**, porque o 5.6 produzia inteiro ali (regra `(int)` × `(float)` do
  Tributário). Só `sau1_cgs_undoutros002` usa o formulário.
- **`pg_query()` com conexão `null`**: `sau1_valores001.php` chama `@db_query($conexao, …)` em 3 pontos, e `$conexao` nunca é
  definida; dentro de `db_query()` (`libs/db_stdlib.php:107`) vira `pg_query(null, …)` — no 5.6 aviso e `NULL`, no 8
  `TypeError`. **Corrigido na tela, não no núcleo:** `($conexao ? @db_query($conexao, …) : null)`. Das 54 chamadas
  `db_query($<conexao>, …)` da base, só esta usa variável indefinida (as outras usam `$conn`, que o `db_conecta.php` define);
  a guarda no `db_query()` cobriria casos futuros, mas é a `db_stdlib`, que quase tudo alcança, e exigiria a bateria completa
  no lote. Os efeitos colaterais do `db_query()` depois do `pg_query` dependem de `DB_traceLog`/`DB_premenus`, ausentes na
  sessão. Opção registrada para quando outro caso aparecer.

Bateria dirigida: **15 telas servidas fora do lote** (Tributário, Educação, Patrimonial, Recursos Humanos e Saúde: `cai2_`,
`edu1_rechumano*`, `ouv*.RPC`, `pro4_*`, `vac2_aerograma002`…) usam algum dos 99 arquivos de `classes/` alterados — **15/15**.

Roteamento: **`sau1`** no `location` (e no `LOC` do `dimensiona.py` e do `redirecionamentos.py`; a `FASE_A` do gerador compara
só as letras do prefixo, então `sau` entra nela no lote 6). Não existe `sau1[0-9]+_`. Conferido: `sau1_`, `/w/2/sau1_` → 8.5;
`sau2_`, `sau4_`, `sau_`, `login` → 5.6. `sau4_importsus002.php` foi alterado neste lote (está no universo) e continua servido
pelo 5.6 até o lote 6 — o código portado roda nos dois.

**Passo 8b achou uma aba no 5.6:** `sau1_medicos000.php` (3 entradas de menu, `db_opcao` 1/22/33) abre `pro1_cgmdoc001.php`
como aba `a2`. `pro` é prefixo compartilhado, roteado por `map`. Universo da aba: 12 alvos, os 11 do falso positivo e
`classes/db_cgmdoc_classe.php`, já portada pela passada principal (estava no universo do lote). Instância e escrita
idênticas (75 linhas), forma negada sem pares; a aba **3/3** (sem parâmetro, com `z01_numcgm`, com `db_opcao`). Posta em
`faseb_map_abas.txt` → **`map` 1.105 entradas**; levantamento refeito: nada indo ao 5.6 (16 iframes de pasta), sem 2º salto.

**Lote 6 — `sau2_`, `sau3_`, `sau4_`, `sau_`** (274 arquivos: 116 + 34 + 121 + 3; o prefixo `sau` passa INTEIRO ao `location`;
31/10/2026). 134 alvos. `split()`: 140 `"#"`, 1 `"XX"` — literais. Rector em **107 arquivos**, só regras vetadas (61 `parse_str`,
41 guardas, 40 construtores, 37 `split`, 1 `${$var}`), 0 na 2ª passada; nenhuma `OptionalParametersAfterRequired`. Remanescentes
0; portão 0 ausentes; carga 510/510.

`php -l`: 3 arquivos compilavam no 5.6 e não no 8.5, todos de categoria do catálogo:
- **Ternário aninhado sem parênteses** (`sau2_sau_encaminhamentos002.php:387`, `sau2_sau_encaminhamentos003.php:682`):
  `empty($sexo) ? '' : $sexo == 'M' ? 'Masculino' : 'Feminino'`. No 5.6 associa à esquerda → parênteses à esquerda. Fiel ao
  ponto de manter o defeito: sexo vazio sai **"Feminino"** nos dois (medido, 3 entradas).
- **`break` fora de laço** (`sau4_ambulatorial.RPC.php:477`, ramo `duplicarCotas` sem grade de horário) → **`exit;`**. No 8.5
  o RPC **inteiro** não compilava, derrubando todas as outras operações (`exec`) do arquivo, não só esse ramo.

Bateria 251/274 → **273/274**. **22 guardas `pg_*`** em 22 telas (`sau2_*002/003` de relatório, `sau3_consultasaude003`,
`sau4_agendamento001`, `sau4_agendamento_simplificado001`, `sau4_consultamedica004`, `sau4_prontuariomedico002`,
`sau4_triagemproc001`): 21 pelo `guarda_ciclo.py`, e `sau2_cgscorretos002.php:60` à mão, porque o ciclo não casa
`pg_numrows ( $result )` com espaço antes do parêntese. Nenhuma das 9 variáveis guardadas é comparada com `===`. Os
`@pg_num_rows` viraram `@(... ? pg_num_rows(...) : null)`, equivalente.

A 1 caracterizada: **`sau2_bpa001.php`** — a bateria a abre sem `?bpa=`, e `file("")` é `ValueError` no 8 (no 5.6, aviso e
`false`; o `foreach` não itera). As 3 chamadoras (`model/saudeBPA.model.php`, `lab4_bpamagnetico002.php`,
`libs/db_stdlibwebseller.php`) abrem sempre `sau2_bpa001.php?bpa=<arquivo de validação recém-gravado>`. Pelo caminho real,
**idêntica** com 2 arquivos (linhas soltas; formato `tipo:campo,campo` com dois tipos, que exercita a troca de página e os
totais).

Classes e escrita: só os diffs conhecidos do harness (os do Financeiro: `empenho → datausu` sem sessão, `lancamentoContabil`,
`ordemPagamento`; e os de sempre). Bateria dirigida: nenhuma tela servida fora do lote usa os 46 arquivos de `classes/` nem
o formulário (`db_frmcgserrado`) alterados.

Roteamento: **`sau1` → `sau`** no `location` e nos dois scripts; `sau` na `FASE_A` do gerador; `map` sem mudança (1.105).
Conferido: `sau1_`, `sau2_`, `sau3_`, `/w/2/sau4_…RPC`, `Sau_` → 8.5; `login` → 5.6. Passo 8b: nada indo ao 5.6 (19 iframes de
pasta).

**Lote 7 — as 3 telas `mat` da Saúde + abas** (01/11/2026). Levantamento pelo banco depois do lote 6: das 493 telas de menu
da Saúde em disco, faltavam só `mat1_matmaterconteudomaterial001/002/003` (Ambulatorial). Universo 1.079; 14 alvos, dos quais
11 são o falso positivo conhecido. Rector em **3 arquivos** (`classes/db_matmaterconteudomaterial_classe.php` e as telas 002/003),
só regras vetadas (2 `parse_str`, guardas, 1 construtor) — conferidas pelo diff, porque a simulação não gravou a saída: **o
`/tmp` da máquina é limpo no reinício e levou a pasta de rascunho da sessão**, então recriá-la antes de usar. Remanescentes 0;
lint 1.079/1.079; portão 0; carga, instância, escrita e forma negada (4 pares) idênticas. A classe só é usada pelas 3 telas e
por `func_matmaterconteudomaterial.php` (não servida). Bateria **3/3**.

Roteamento: `mat` é prefixo compartilhado (Patrimonial), então pelo `map`: lote **`sa:mat`** acrescentado ao comando do
`gera_map_faseb.py` (a área casa pelo começo do nome; só a Saúde começa com "SA") → **`map` 1.108 entradas**. `nginx -t` antes
de recriar. Conferido: as 3 telas (inclusive `/w/2/`) → 8.5; `login` → 5.6. **Passo 8b sobre a área inteira: 601 telas no
8.5 examinadas (menu + abas), nada indo ao 5.6** (19 iframes de pasta).

### Nível 3 (POST real) — amostra da Saúde (01/11/2026, pedido do usuário)

Até aqui a Saúde só tinha o caminho de escrita verificado nos níveis 1–2 (`escrita.php`, forma negada); POST real só houve no
Tributário e em RH. Amostra de uma tela de inclusão por prefixo (`scratchpad/demo_nivel3.sh` / `escrita_post.py`):

| Tela | Tabela | Resultado |
|---|---|---|
| `far1_far_programa001` | `far_programa` | **IDÊNTICO** (INSERT de negócio e as demais escritas: 2 = 2) |
| `lab1_lab_setor001` | `lab_setor` | **IDÊNTICO** (6 = 6 escritas) |
| `tfd1_tfd_destino001` | `tfd_destino` | **IDÊNTICO** (10 = 10) |
| `fum1_associadotiposservicos001` | `associadotiposservicos` | **IDÊNTICO** (2 = 2) |
| `vac1_vac_sala001` | `vac_sala` | **IDÊNTICO** em 3 rodadas; a contagem de *statements* oscilou (30/31, 32/30, 30/30) trocando de lado — ruído de outras conexões no log compartilhado, não do runtime |
| `sau1_unidades001` | `unidades` | **IDÊNTICO**, com payload à mão (`sd02_i_codigo=1` — a chave é o departamento, digitada — e CNES de 7 dígitos); o automático era inconclusivo |
| `sau1_cgs_und002` (alteração de CGS) | `cgs_und` | **NÃO MEDIDO** — ver abaixo |
| `sau1_cgs_und001` (inclusão de CGS) | `cgs*` | **NÃO MEDIDO** — ver abaixo |

**`cl_cgs_und::alterarExt` é código morto:** nenhum arquivo o chama, e a coluna `z01_b_faleceu` nem existe em `cgs_und` (está em
`cgs_und_ext`). A guarda da forma negada posta nele no lote 2 não muda o comportamento do sistema; não há POST que a exercite.

**CGS: o harness não serve, e deixou dados no banco (limpos).** Duas causas, ambas do instrumento, não do porte:
1. **"ABORTADO" NÃO significa "nada foi enviado".** O `escrita_post.py` restaura **entre** os runtimes: o POST do 5.6 já gravou
   quando a restauração falha. A doc do `demo_nivel3.sh` dizia o contrário. Na alteração, a restauração apaga a linha mudada e a
   reinsere, e a única CGS da base (a 0, "NAO INFORMADO") é referenciada por `cgs_undendereco` → abortou com a linha 0 alterada.
2. **Gatilho que escreve fora das tabelas informadas:** `tg_cgs_endereco_inc_alt` (`fc_cgs_endereco_inc_alt`), em INSERT e
   UPDATE de `cgs_und`, cria a cadeia de endereço (`cadendermunicipio`, `cadenderbairro`, `cadenderrua`, `cadenderruaruastipo`,
   `cadenderbairrocadenderrua`, `cadenderlocal`, `endereco`, `cgs_undendereco`). Escrita de gatilho **não aparece no log**
   (`log_statement` só registra o que o cliente manda), então nem a separação negócio/infra do harness a vê. O próprio UPDATE de
   restauração que fiz na linha 0 disparou o gatilho e criou mais uma cadeia.

Limpeza, com a prova de que cada linha era do teste: a linha 0 de `cgs_und` reposta coluna a coluna a partir da cópia do harness
(23 colunas; conferida `row_to_json` igual); apagadas `cgs`/`cgs_und` 4, `cgs_cartaosus` 6, `cgs_und_ext` da CGS 0,
`cgs_undendereco` 2–3, `endereco` 4–6, `cadenderlocal` 4–5, `cadenderbairrocadenderrua` 1.250.465–466, `cadenderrua` e
`cadenderruaruastipo` 1.139.456–457, `cadenderbairro` 61.452, `cadendermunicipio` 31.179. Prova: **tudo acima do maior id do dump
original** (`docker/database/ecidade_base.sql`, de 05/09), com os valores do payload (`'1'`, `'TESTE_N3'`), **cada sequência
avançada exatamente pelo número de linhas novas**, e nenhuma referência fora da cadeia (agência bancária, CGM, itinerário/ponto de
parada, CEP, parâmetros). Sequências devolvidas ao valor do dump (`cgs_undendereco` e `cgs_und_ext` ao estado "nunca chamada",
`last_value` 1 com `is_called` falso, coerente com tabelas vazias no dump). Contagens finais iguais às do dump. Ficaram só os
lançamentos de auditoria (`db_acount` 88.957–88.965), como nas rodadas de nível 3 anteriores (88.901–88.956 são de RH e Veículos).

**Outro erro meu, no mesmo dia:** uma sondagem com `curl -X POST` direto ao 5.6, para ler a mensagem de validação de
`sau1_unidades001`, **gravou de verdade** (uma linha em `unidades`) fora do harness, e a comparação seguinte saiu com chave
duplicada nos dois lados. Linha apagada (CNES `'1'`, do payload da sondagem) e teste refeito. **Regra: nunca mandar POST a uma
tela fora do `escrita_post.py`.**

**Para medir a CGS** o harness precisaria (a) restaurar linha alterada por UPDATE em vez de DELETE+INSERT e (b) enxergar escrita
de gatilho (comparar as tabelas por conteúdo, antes e depois, em vez de depender do log). Fica para decisão do usuário.

**Estado:** os 7 lotes da Saúde concluídos (commits locais). Falta a etapa do fim da área: bateria completa (todos os prefixos
do `location` + o `map` inteiro), a conferência pelo proxy das telas de menu da Saúde e o envio — cada uma só com o pedido do
usuário.
