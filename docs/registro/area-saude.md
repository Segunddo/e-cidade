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

**Estado:** lote 4 concluído (commit local). Aguardando o pedido do lote 5 (`sau1_`).
