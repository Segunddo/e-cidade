# Rastreador - causas por linha das telas DIVERGE da base-php85 (rodada base85b)

**Regenerado em 2026-11-28** com o backend de sondas por linha sobre a arvore realmente montada nos contêineres (a versao de 2026-11-27 e anterior a correcao da raiz do codigo e do portao de equivalencia). Cada causa foi **cruzada com o backend Xdebug**: coluna `concordancia_xdebug` do TSV (163 telas com a mesma linha pelos dois caminhos; ver `rastro-linhas-todas-2026-11-28.md`).

O rastreador (`python -m regressao.rastro`) reexecutou **cada tela DIVERGE** da rodada nos dois PHP e apontou **onde o dado divergiu**. 182 telas distintas. Planilha completa: `rastro-causas-base-php85b-2026-11-27.tsv`.

| Veredito | Telas |
|---|---|
| DIVERGE-CAUSAL | 177 |
| INCONCLUSIVO | 4 |
| DIVERGE-RECONVERGENTE | 1 |

## 1. Onde corrigir: por linha causal

As 177 telas com causa apontam para **158 linhas distintas**. As que concentram mais telas valem mais; as demais sao a mesma causa repetida em cada tela.

| Linha | Telas | Erro no 8.5 | Como corrigir |
|---|---|---|---|
| `fpdf151/pdf.php:186` | 11 | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given | A consulta falhou e devolveu `false`, usado sem checar. Testar `$rs === false` antes (a cadeia mostra a variavel que ficou `false`). |
| `std/DBDate.php:203` | 6 | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given | `checkdate()` recebe string vazia: converter com `(int)` antes de chamar. |
| `fpdf151/fpdf.php:1448` | 2 |  | A saida da tela muda sem excecao: compare as linhas em 'Onde a resposta difere' e a linha apontada. |
| `libs/db_libcontabilidade.php:5355` | 2 | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given | A consulta falhou e devolveu `false`, usado sem checar. Testar `$rs === false` antes (a cadeia mostra a variavel que ficou `false`). |
| `libs/db_libsession.php:51` | 2 |  | A saida da tela muda sem excecao: compare as linhas em 'Onde a resposta difere' e a linha apontada. |
| `model/manad.model.php:129` | 2 | TypeError: implode(): If argument #1 ($separator) is of type string, argument #2 ($array)  | O 8.x endureceu esse aviso do 7.4 em excecao: corrigir a chamada nesta linha (ver mensagem). |

Mais **152 linhas** com uma tela cada (listadas por area na secao 2).

## 2. Por area (tela, linha causal, ultimo dado antes de quebrar)

### assistenciasocial (1 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `soc2_declaracaoinss002.php` | `soc2_declaracaoinss002.php:47` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$iCodigoNis |

### cidadao (20 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `con2_lrfanexoxvii002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | `libs/db_libcontabilidade.php:4989` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2015.php` | `libs/db_libcontabilidade.php:5935` |  | TypeError: explode(): Argument #2 ($string) must be of type string, array given |
| `con2_anexo17_002_2011.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_i_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_ii_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |

### saude (34 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `lab1_lab_laboratorio002.php` | `dbforms/db_funcoes.php:208` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined global variable $la02_i_codigo |
| `far2_distribuicao002.php` | `far2_distribuicao002.php:282` | result2 = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `far2_historicopaciente002.php` | `far2_historicopaciente002.php:140` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `far2_historicoprogmedicamento002.php` | `far2_historicoprogmedicamento002.php:135` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `far2_historicoprogpaciente002.php` | `far2_historicoprogpaciente002.php:136` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `far2_mapaconsolidado003.php` | `far2_mapaconsolidado003.php:58` | qr = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `far2_pacienteprogramatica002.php` | `far2_pacienteprogramatica002.php:120` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau1_cgs_undoutros002.php` | `forms/db_frmcgs_undoutros.php:99` | conta = string: s0: | TypeError: Unsupported operand types: string + int |
| `lab2_mapacoletaconsulta.php` | `lab2_mapacoletaconsulta.php:22` | data1 = array: [0=>s0:] | TypeError: mktime(): Argument #5 ($day) must be of type ?int, string given |
| `lab2_producao002.php` | `lab2_producao002.php:94` | setores = bool: false | TypeError: implode(): If argument #1 ($separator) is of type string, argument #2 ($array) must  |
| `lab1_lab_laboratorio003.php` | `libs/db_libsession.php:51` |  | `date` (c): 7.4 = string: s8:01:27:08 / 8.5 = string: s8:01:27:09 |
| `sau1_valores001.php` | `libs/db_stdlib.php:112` | dbsql = string: s52:SELECT * FROM valores WHERE procedimento_i_codig | TypeError: pg_query(): Argument #1 ($connection) must be of type PgSql\Connection, null given |
| `sau2_agendaexterna003.php` | `sau2_agendaexterna003.php:72` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_atendimentos002.php` | `sau2_atendimentos002.php:76` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_boletim002.php` | `sau2_boletim002.php:88` | query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_bpa001.php` | `sau2_bpa001.php:42` |  | ValueError: Path must not be empty |
| `sau2_cgscorretos002.php` | `sau2_cgscorretos002.php:59` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_especialidades002.php` | `sau2_especialidades002.php:62` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_faausuarios002.php` | `sau2_faausuarios002.php:99` | query_pront = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_grafsaude002.php` | `sau2_grafsaude002.php:68` | Query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_indicemorb002.php` | `sau2_indicemorb002.php:80` | query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_procedimentos002.php` | `sau2_procedimentos002.php:62` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_procedimentos003.php` | `sau2_procedimentos003.php:61` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_procmedicos002.php` | `sau2_procmedicos002.php:65` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_progmun002.php` | `sau2_progmun002.php:60` | Query_rel = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_prontuarios002.php` | `sau2_prontuarios002.php:53` | Query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_relatorioprocedimentos002.php` | `sau2_relatorioprocedimentos002.php:163` | rs = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_sitagendamentos002.php` | `sau2_sitagendamentos002.php:52` | Query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau2_unidades002.php` | `sau2_unidades002.php:117` | query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau3_consultasaude003.php` | `sau3_consultasaude003.php:52` | query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau4_consultamedica004.php` | `sau4_consultamedica004.php:55` | query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau4_prontuariomedico002.php` | `sau4_prontuariomedico002.php:48` | query = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sau4_triagemproc001.php` | `sau4_triagemproc001.php:90` | result_prontprofatend = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `lab2_inconsistenciasimportacaoresultado002.php` | `src/Saude/Laboratorio/Repository/ImportacaoRequisicaoInconsistenciaRepository.php:117` | postgresObject = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |

### recursoshumanos (28 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `lic1_trocpcorcamtroca001.php` | `forms/db_frmtrocpcorcamtrocalic.php:44` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $l20_codigo |
| `con2_lrfanexoxvii002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | `libs/db_libcontabilidade.php:4989` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2015.php` | `libs/db_libcontabilidade.php:5935` |  | TypeError: explode(): Argument #2 ($string) must be of type string, array given |
| `cai4_relinconsextrato002.php` | `libs/db_libsession.php:51` |  | `date` (c): 7.4 = string: s8:01:22:45 / 8.5 = string: s8:01:22:46 |
| `pes4_geraarquivosmanad.php` | `model/manad.model.php:129` |  | TypeError: implode(): If argument #1 ($separator) is of type string, argument #2 ($array) must  |
| `pes4_geraarquivosmanadnovo.php` | `model/manad.model.php:129` |  | TypeError: implode(): If argument #1 ($separator) is of type string, argument #2 ($array) must  |
| `cai3_gerfinanc003.php` | `model/regraEmissao.model.php:88` | rsConsultaTipoExcessao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `pes2_feriasaviso002.php` | `pes2_feriasaviso002.php:112` | iMesFolha = null: N | ValueError: cal_days_in_month(): Argument #2 ($month) must be between 1 and 2147483646 |
| `pes2_rubmesponto002.php` | `pes2_rubmesponto002.php:214` | rsDados = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `pes4_geracaoarquivorefeisul.RPC.php` | `phar:///var/www/html/ext/php/PHPExcel.phar/PHPExcel/Shared/String.php:529` |  | `excecao_app` (e) acontece **so no 8.5**: excecao: ParseError: syntax error, unexpected token " |
| `con2_anexo17_002_2011.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_i_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_ii_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |

### patrimonial (53 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `cad2_carnesiptu002.php` | `cad2_carnesiptu002.php:57` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_comparaiptu002.php` | `cad2_comparaiptu002.php:154` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_compcaract002.php` | `cad2_compcaract002.php:124` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_descconced002.php` | `cad2_descconced002.php:59` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_emissaobic_002.php` | `cad2_emissaobic_002.php:43` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `cad2_iptulancpago002.php` | `cad2_iptulancpago002.php:60` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_listaiptucalc_003.php` | `cad2_listaiptucalc_003.php:41` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteam002.php` | `cad2_loteam002.php:179` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteamentomatric002.php` | `cad2_loteamentomatric002.php:80` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteamentos002.php` | `cad2_loteamentos002.php:77` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_matricnaoproc002.php` | `cad2_matricnaoproc002.php:74` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_posicaoiptu002.php` | `cad2_posicaoiptu002.php:71` | Result_calc = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relaverbacao002.php` | `cad2_relaverbacao002.php:155` | rsDadosAverbacao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_reldemo002.php` | `cad2_reldemo002.php:108` | rsResult = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relisentos002.php` | `cad2_relisentos002.php:46` | result = bool: false | TypeError: pg_fetch_assoc(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relmassafalida002.php` | `cad2_relmassafalida002.php:84` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_setor002.php` | `cad2_setor002.php:79` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_conscadastro_relatorio.php` | `cad3_conscadastro_relatorio.php:43` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `cad3_conscadastrodetalhesmodelonovo002.php` | `cad3_conscadastrodetalhesmodelonovo002.php:171` | rsSqlConsulta = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_iptupago002_original.php` | `cad3_iptupago002_original.php:64` | result = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_relzonafiscal002.php` | `cad3_relzonafiscal002.php:62` | rsZonasValor = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_relzonafiscaltaxa002.php` | `cad3_relzonafiscaltaxa002.php:63` | rsZonasTaxa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt.php` | `cad4_geracarneiptutxt.php:754` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_arapiraca.php` | `cad4_geracarneiptutxt_arapiraca.php:170` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_eldorado.php` | `cad4_geracarneiptutxt_eldorado.php:167` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_guaiba.php` | `cad4_geracarneiptutxt_guaiba.php:169` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarnesiptu_geral.php` | `cad4_geracarnesiptu_geral.php:60` | rsTaxa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_recadastramentorelatorio.php` | `cad4_recadastramentorelatorio.php:106` | data = null: N | TypeError: array_chunk(): Argument #1 ($array) must be of type array, null given |
| `lic1_trocpcorcamtroca001.php` | `forms/db_frmtrocpcorcamtrocalic.php:44` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $l20_codigo |
| `orc2_atividades002.php` | `fpdf151/fpdf.php:932` |  | TypeError: Unsupported operand types: int + string |
| `con2_lrfanexoxvii002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | `libs/db_libcontabilidade.php:4989` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `orc2_desppessoal002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2015.php` | `libs/db_libcontabilidade.php:5935` |  | TypeError: explode(): Argument #2 ($string) must be of type string, array given |
| `cai3_gerfinanc003.php` | `model/regraEmissao.model.php:88` | rsConsultaTipoExcessao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `orc2_receitasDespesasPrevidenciariasServidores002.php` | `orc2_receitasDespesasPrevidenciariasServidores002.php:108` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$sModelo |
| `con2_anexo17_002_2011.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_i_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_ii_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |

### tributario (111 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `agu4_cancelaleituras_classe.php` | `/var/www/html/vendor/dbseller/legacy/src/PHP53/Emulate.php:110` |  | `excecao_app` (e) acontece **so no 8.5**: excecao: TypeError: array_key_exists(): Argument #2 ( |
| `agu1_aguahidromatricfichatroca002.php` | `agu1_aguahidromatricfichatroca002.php:61` | rSql = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu2_compleituras002.php` | `agu2_compleituras002.php:161` | rSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu2_hidrometro002.php` | `agu2_hidrometro002.php:70` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu2_relconsumo002.php` | `agu2_relconsumo002.php:166` | rSql = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu2_relimobiliarias002.php` | `agu2_relimobiliarias002.php:86` | rSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu2_relimoveiscar002.php` | `agu2_relimoveiscar002.php:72` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu2_situacaohidro002.php` | `agu2_situacaohidro002.php:155` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu3_conscadastro_relatorio.php` | `agu3_conscadastro_relatorio.php:37` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `agu4_relcorte.php` | `agu4_relcorte.php:36` | resultender = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `agu4_relleituras002.php` | `agu4_relleituras002.php:54` | rSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `arr2_rellistadqd002.php` | `arr2_rellistadqd002.php:178` | rsDeclaracaoQuitacao = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_carnesiptu002.php` | `cad2_carnesiptu002.php:57` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_comparaiptu002.php` | `cad2_comparaiptu002.php:154` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_compcaract002.php` | `cad2_compcaract002.php:124` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_descconced002.php` | `cad2_descconced002.php:59` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_emissaobic_002.php` | `cad2_emissaobic_002.php:43` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `cad2_iptulancpago002.php` | `cad2_iptulancpago002.php:60` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_listaiptucalc_003.php` | `cad2_listaiptucalc_003.php:41` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteam002.php` | `cad2_loteam002.php:179` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteamentomatric002.php` | `cad2_loteamentomatric002.php:80` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteamentos002.php` | `cad2_loteamentos002.php:77` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_matricnaoproc002.php` | `cad2_matricnaoproc002.php:74` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_posicaoiptu002.php` | `cad2_posicaoiptu002.php:71` | Result_calc = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relaverbacao002.php` | `cad2_relaverbacao002.php:155` | rsDadosAverbacao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_reldemo002.php` | `cad2_reldemo002.php:108` | rsResult = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relisentos002.php` | `cad2_relisentos002.php:46` | result = bool: false | TypeError: pg_fetch_assoc(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relmassafalida002.php` | `cad2_relmassafalida002.php:84` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_setor002.php` | `cad2_setor002.php:79` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_conscadastro_relatorio.php` | `cad3_conscadastro_relatorio.php:43` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `cad3_conscadastrodetalhesmodelonovo002.php` | `cad3_conscadastrodetalhesmodelonovo002.php:171` | rsSqlConsulta = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_iptupago002_original.php` | `cad3_iptupago002_original.php:64` | result = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_relzonafiscal002.php` | `cad3_relzonafiscal002.php:62` | rsZonasValor = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_relzonafiscaltaxa002.php` | `cad3_relzonafiscaltaxa002.php:63` | rsZonasTaxa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt.php` | `cad4_geracarneiptutxt.php:754` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_arapiraca.php` | `cad4_geracarneiptutxt_arapiraca.php:170` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_eldorado.php` | `cad4_geracarneiptutxt_eldorado.php:167` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_guaiba.php` | `cad4_geracarneiptutxt_guaiba.php:169` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarnesiptu_geral.php` | `cad4_geracarnesiptu_geral.php:60` | rsTaxa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_recadastramentorelatorio.php` | `cad4_recadastramentorelatorio.php:106` | data = null: N | TypeError: array_chunk(): Argument #1 ($array) must be of type array, null given |
| `cem2_edital002.php` | `cem2_edital002.php:87` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_resumogeraldivida002.php` | `classes/db_divida_classe.php:2378` |  | TypeError: Unsupported operand types: string - int |
| `con2_anexodemonstrativofuncaosubfuncao002_2018.php` | `con2_anexodemonstrativofuncaosubfuncao002_2018.php:44` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$sPeriodo |
| `fis1_fis_procfiscalfinalizacao002.php` | `dbforms/db_funcoes.php:201` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined global variable $Msituacao_select_descr |
| `div2_diviano002.php` | `div2_diviano002.php:94` | result_parc = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_exercdivida002.php` | `div2_exercdivida002.php:392` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_parcel002.php` | `div2_parcel002.php:151` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_posicaoparc002.php` | `div2_posicaoparc002.php:247` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_procedexerc_002.php` | `div2_procedexerc_002.php:130` | result2 = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `dv02_loteamentos002.php` | `dv02_loteamentos002.php:48` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `dvr2_capaloteamento002.php` | `dvr2_capaloteamento002.php:61` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `dvr3_procedper002.php` | `dvr3_procedper002.php:135` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `dvr4_parclote004.php` | `dvr4_parclote004.php:74` | totpar = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `dvr4_parclote005.php` | `dvr4_parclote005.php:66` | principal = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `fis1_fis_sanitario004.php` | `fis1_fis_sanitario004.php:67` |  | `excecao_app` (e) acontece **so no 7.4**: excecao: Error: Call to undefined function db_ancora( |
| `fis1_sanitario004.php` | `fis1_sanitario004.php:67` |  | `excecao_app` (e) acontece **so no 7.4**: excecao: Error: Call to undefined function db_ancora( |
| `fis2_emiteaidof002.php` | `fis2_emiteaidof002.php:105` | result_empresa = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `fis2_fis_levantamentolote002.php` | `fis2_fis_levantamentolote002.php:245` | ResulFis = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `fis2_fis_levantamentomassa002.php` | `fis2_fis_levantamentomassa002.php:168` | ResulFis = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `fis2_fis_termofiscal003.php` | `fis2_fis_termofiscal003.php:122` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `fis3_fis_consultaautoinf_imp.php` | `fis3_fis_consultaautoinf_imp.php:57` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `fis3_fis_imprimealvara.php` | `fis3_fis_imprimealvara.php:64` | rsResult = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sys4_libimpmax001.php` | `forms/db_frmlibimpmax001.php:138` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `fis3_fis_relatoriosani.php` | `fpdf151/fpdf.php:1448` |  | `` (r): 7.4 = int: 75 / 8.5 = int: 93 |
| `fis3_relatoriosani.php` | `fpdf151/fpdf.php:1448` |  | `` (r): 7.4 = int: 75 / 8.5 = int: 93 |
| `con2_lrfanexoxvii002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `inf2_inflan002.php` | `inf2_inflan002.php:126` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_calculadoepago002.php` | `iss2_calculadoepago002.php:113` | resultfixo = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_certibaixa002.php` | `iss2_certibaixa002.php:55` | rsTabativBaixa = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_inscrescrito002.php` | `iss2_inscrescrito002.php:81` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_issqnpago002.php` | `iss2_issqnpago002.php:67` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_listinscrweb002.php` | `iss2_listinscrweb002.php:100` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_relarrec1002.php` | `iss2_relarrec1002.php:53` |  | `excecao_app` (e) acontece **so no 8.5**: excecao: TypeError: Unsupported operand types: string |
| `iss2_relatorioruas002.php` | `iss2_relatorioruas002.php:179` | rsSqlDebitos = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss3_emissaoalvaraveiculos001.php` | `iss3_emissaoalvaraveiculos001.php:64` | rsTipoAlvara = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss3_emissaobicveiculos001.php` | `iss3_emissaobicveiculos001.php:63` | rsTipoAlvara = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss3_inconsistenciaSimples.php` | `iss3_inconsistenciaSimples.php:62` |  | TypeError: rsort(): Argument #1 ($array) must be of type array, null given |
| `iss4_contativ003.php` | `iss4_contativ003.php:222` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss4_contativ006.php` | `iss4_contativ006.php:86` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `itb2_relsetorquadralote002.php` | `itb2_relsetorquadralote002.php:255` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `itbi_simulacaoitbi002.php` | `itbi_simulacaoitbi002.php:237` | imposto_avalia = string: s0: | TypeError: Unsupported operand types: string / int |
| `jur2_geradoc.php` | `jur2_geradoc.php:74` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `jur2_inicialquit002.php` | `jur2_inicialquit002.php:60` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `jur2_relinicial002.php` | `jur2_relinicial002.php:170` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | `libs/db_libcontabilidade.php:4989` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2015.php` | `libs/db_libcontabilidade.php:5935` |  | TypeError: explode(): Argument #2 ($string) must be of type string, array given |
| `iss3_emissaoalvaraeventos001.php` | `model/documentoTemplate.model.php:51` | oArquivoSxw = object: stdClass{db82_arquivo=s0:} | `sCaminhoTemplate` (a): 7.4 = string: s34:tmp/docTemplate202611280126401.sxw / 8.5 = string: s3 |
| `cai3_gerfinanc003.php` | `model/regraEmissao.model.php:88` | rsConsultaTipoExcessao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_i_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_ii_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `agu1_aguaconsumo999.php` | `std/label/RotuloCampoDB.php:37` |  | `excecao_app` (e) acontece **so no 8.5**: excecao: Error: No PostgreSQL connection opened yet |
| `sys4_consultaXML.RPC.php` | `sys4_consultaXML.RPC.php:39` | oParam = object: stdClass{} | ValueError: Path must not be empty |
| `sys4_listaretornosql001.php` | `sys4_listaretornosql001.php:67` | aRetornoSQL = bool: false | TypeError: array_keys(): Argument #1 ($array) must be of type array, null given |
| `sys4_processa002.php` | `sys4_processa002.php:66` | campos = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sys4_processa004.php` | `sys4_processa004.php:111` | fd = bool: false | TypeError: fputs(): Argument #1 ($stream) must be of type resource, false given |
| `sys4_processa007.php` | `sys4_processa007.php:587` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |

### financeiro (83 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `cad2_carnesiptu002.php` | `cad2_carnesiptu002.php:57` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_comparaiptu002.php` | `cad2_comparaiptu002.php:154` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_compcaract002.php` | `cad2_compcaract002.php:124` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_descconced002.php` | `cad2_descconced002.php:59` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_emissaobic_002.php` | `cad2_emissaobic_002.php:43` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `cad2_iptulancpago002.php` | `cad2_iptulancpago002.php:60` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_listaiptucalc_003.php` | `cad2_listaiptucalc_003.php:41` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteam002.php` | `cad2_loteam002.php:179` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteamentomatric002.php` | `cad2_loteamentomatric002.php:80` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_loteamentos002.php` | `cad2_loteamentos002.php:77` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_matricnaoproc002.php` | `cad2_matricnaoproc002.php:74` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_posicaoiptu002.php` | `cad2_posicaoiptu002.php:71` | Result_calc = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relaverbacao002.php` | `cad2_relaverbacao002.php:155` | rsDadosAverbacao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_reldemo002.php` | `cad2_reldemo002.php:108` | rsResult = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relisentos002.php` | `cad2_relisentos002.php:46` | result = bool: false | TypeError: pg_fetch_assoc(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_relmassafalida002.php` | `cad2_relmassafalida002.php:84` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad2_setor002.php` | `cad2_setor002.php:79` | rsSql = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_conscadastro_relatorio.php` | `cad3_conscadastro_relatorio.php:43` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `cad3_conscadastrodetalhesmodelonovo002.php` | `cad3_conscadastrodetalhesmodelonovo002.php:171` | rsSqlConsulta = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_iptupago002_original.php` | `cad3_iptupago002_original.php:64` | result = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_relzonafiscal002.php` | `cad3_relzonafiscal002.php:62` | rsZonasValor = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad3_relzonafiscaltaxa002.php` | `cad3_relzonafiscaltaxa002.php:63` | rsZonasTaxa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt.php` | `cad4_geracarneiptutxt.php:754` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_arapiraca.php` | `cad4_geracarneiptutxt_arapiraca.php:170` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_eldorado.php` | `cad4_geracarneiptutxt_eldorado.php:167` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_guaiba.php` | `cad4_geracarneiptutxt_guaiba.php:169` | rsReceitas = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_geracarnesiptu_geral.php` | `cad4_geracarnesiptu_geral.php:60` | rsTaxa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `cad4_recadastramentorelatorio.php` | `cad4_recadastramentorelatorio.php:106` | data = null: N | TypeError: array_chunk(): Argument #1 ($array) must be of type array, null given |
| `div2_resumogeraldivida002.php` | `classes/db_divida_classe.php:2378` |  | TypeError: Unsupported operand types: string - int |
| `div2_diviano002.php` | `div2_diviano002.php:94` | result_parc = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_exercdivida002.php` | `div2_exercdivida002.php:392` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_parcel002.php` | `div2_parcel002.php:151` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_posicaoparc002.php` | `div2_posicaoparc002.php:247` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `div2_procedexerc_002.php` | `div2_procedexerc_002.php:130` | result2 = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sys4_libimpmax001.php` | `forms/db_frmlibimpmax001.php:138` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `orc2_atividades002.php` | `fpdf151/fpdf.php:932` |  | TypeError: Unsupported operand types: int + string |
| `con2_lrfanexoxvii002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `inf2_inflan002.php` | `inf2_inflan002.php:126` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_calculadoepago002.php` | `iss2_calculadoepago002.php:113` | resultfixo = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_certibaixa002.php` | `iss2_certibaixa002.php:55` | rsTabativBaixa = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_inscrescrito002.php` | `iss2_inscrescrito002.php:81` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_issqnpago002.php` | `iss2_issqnpago002.php:67` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_listinscrweb002.php` | `iss2_listinscrweb002.php:100` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss2_relarrec1002.php` | `iss2_relarrec1002.php:53` |  | `excecao_app` (e) acontece **so no 8.5**: excecao: TypeError: Unsupported operand types: string |
| `iss2_relatorioruas002.php` | `iss2_relatorioruas002.php:179` | rsSqlDebitos = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss3_emissaoalvaraveiculos001.php` | `iss3_emissaoalvaraveiculos001.php:64` | rsTipoAlvara = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss3_emissaobicveiculos001.php` | `iss3_emissaobicveiculos001.php:63` | rsTipoAlvara = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss3_inconsistenciaSimples.php` | `iss3_inconsistenciaSimples.php:62` |  | TypeError: rsort(): Argument #1 ($array) must be of type array, null given |
| `iss4_contativ003.php` | `iss4_contativ003.php:222` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `iss4_contativ006.php` | `iss4_contativ006.php:86` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | `libs/db_libcontabilidade.php:4989` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `orc2_desppessoal002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2015.php` | `libs/db_libcontabilidade.php:5935` |  | TypeError: explode(): Argument #2 ($string) must be of type string, array given |
| `iss3_emissaoalvaraeventos001.php` | `model/documentoTemplate.model.php:51` | oArquivoSxw = object: stdClass{db82_arquivo=s0:} | `sCaminhoTemplate` (a): 7.4 = string: s34:tmp/docTemplate202611280126401.sxw / 8.5 = string: s3 |
| `pes4_geraarquivosmanad.php` | `model/manad.model.php:129` |  | TypeError: implode(): If argument #1 ($separator) is of type string, argument #2 ($array) must  |
| `pes4_geraarquivosmanadnovo.php` | `model/manad.model.php:129` |  | TypeError: implode(): If argument #1 ($separator) is of type string, argument #2 ($array) must  |
| `cai3_gerfinanc003.php` | `model/regraEmissao.model.php:88` | rsConsultaTipoExcessao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `orc2_receitasDespesasPrevidenciariasServidores002.php` | `orc2_receitasDespesasPrevidenciariasServidores002.php:108` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$sModelo |
| `pes2_feriasaviso002.php` | `pes2_feriasaviso002.php:112` | iMesFolha = null: N | ValueError: cal_days_in_month(): Argument #2 ($month) must be between 1 and 2147483646 |
| `pes2_rubmesponto002.php` | `pes2_rubmesponto002.php:214` | rsDados = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `pes4_geracaoarquivorefeisul.RPC.php` | `phar:///var/www/html/ext/php/PHPExcel.phar/PHPExcel/Shared/String.php:529` |  | `excecao_app` (e) acontece **so no 8.5**: excecao: ParseError: syntax error, unexpected token " |
| `con2_anexo17_002_2011.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_i_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_ii_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `sys4_consultaXML.RPC.php` | `sys4_consultaXML.RPC.php:39` | oParam = object: stdClass{} | ValueError: Path must not be empty |
| `sys4_listaretornosql001.php` | `sys4_listaretornosql001.php:67` | aRetornoSQL = bool: false | TypeError: array_keys(): Argument #1 ($array) must be of type array, null given |
| `sys4_processa002.php` | `sys4_processa002.php:66` | campos = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sys4_processa004.php` | `sys4_processa004.php:111` | fd = bool: false | TypeError: fputs(): Argument #1 ($stream) must be of type resource, false given |
| `sys4_processa007.php` | `sys4_processa007.php:587` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |

### configuracao (50 telas)

| Tela | Corrigir em | Dado que quebrou | Erro no 8.5 |
|---|---|---|---|
| `ate1_tarefa004.php` | `ate1_tarefa004.php:346` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $tipo |
| `ate1_tarefa010.php` | `ate1_tarefa010.php:78` | resulttarefa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate1_tarefaobs001.php` | `ate1_tarefaobs001.php:106` | res = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate2_relatendnaolanc002.php` | `ate2_relatendnaolanc002.php:58` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate2_relatorio001.php` | `ate2_relatorio001.php:126` | result1 = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate2_relclienteproced002.php` | `ate2_relclienteproced002.php:242` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate2_reltarefaagenda002.php` | `ate2_reltarefaagenda002.php:41` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate3_atendimento002.php` | `ate3_atendimento002.php:133` | result = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate3_constarefaanexos.php` | `ate3_constarefaanexos.php:159` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate3_consultaacesso002.php` | `ate3_consultaacesso002.php:179` | result_cli = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate3_consultaacesso003.php` | `ate3_consultaacesso003.php:64` | result_cli = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate3_consultaacesso004.php` | `ate3_consultaacesso004.php:60` | result_cli = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate4_pesquisatarefacod.RPC.php` | `ate4_pesquisatarefacod.RPC.php:50` | rsTarefa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate4_pesquisatarefadescr.RPC.php` | `ate4_pesquisatarefadescr.RPC.php:50` | rsTarefa = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate4_atend002.php` | `forms/db_frmatend.php:84` | result_usucliente = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate4_atendsup001.php` | `forms/db_frmatendsup.php:330` | resultmot = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate1_clientesmodulosproc002.php` | `forms/db_frmclientesmodulosproc.php:66` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate1_tarefalogand002.php` | `forms/db_frmcontarefalogand.php:420` | ressit = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sys4_libimpmax001.php` | `forms/db_frmlibimpmax001.php:138` |  | TypeError: sizeof(): Argument #1 ($value) must be of type Countable/array, null given |
| `ate1_tarefa006.php` | `forms/db_frmtarefa.php:63` |  | `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $abrefunc |
| `ate1_tarefaagenda002.php` | `forms/db_frmtarefaagenda.php:153` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `orc2_atividades002.php` | `fpdf151/fpdf.php:932` |  | TypeError: Unsupported operand types: int + string |
| `con2_lrfanexoxvii002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | `fpdf151/pdf.php:186` | rsMenuAcess = bool: false | TypeError: pg_result(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `ate3_consultacalendario_agenda.php` | `func_calendario_atendimento_consulta.php:145` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | `libs/db_libcontabilidade.php:4989` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `orc2_desppessoal002.php` | `libs/db_libcontabilidade.php:5355` | result = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2015.php` | `libs/db_libcontabilidade.php:5935` |  | TypeError: explode(): Argument #2 ($string) must be of type string, array given |
| `cai3_gerfinanc003.php` | `model/regraEmissao.model.php:88` | rsConsultaTipoExcessao = bool: false | TypeError: pg_num_rows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_i_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_anexo_ii_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | `std/DBDate.php:203` | dia = string: s0: | TypeError: checkdate(): Argument #1 ($month) must be of type int, string given |
| `sys4_consultaXML.RPC.php` | `sys4_consultaXML.RPC.php:39` | oParam = object: stdClass{} | ValueError: Path must not be empty |
| `sys4_listaretornosql001.php` | `sys4_listaretornosql001.php:67` | aRetornoSQL = bool: false | TypeError: array_keys(): Argument #1 ($array) must be of type array, null given |
| `sys4_processa002.php` | `sys4_processa002.php:66` | campos = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |
| `sys4_processa004.php` | `sys4_processa004.php:111` | fd = bool: false | TypeError: fputs(): Argument #1 ($stream) must be of type resource, false given |
| `sys4_processa007.php` | `sys4_processa007.php:587` | result = bool: false | TypeError: pg_numrows(): Argument #1 ($result) must be of type PgSql\Result, false given |

## 3. Sem causa apontada (precisam de olhar manual)

- `con4_docpadrao010.php` (INCONCLUSIVO): rastro truncado (teto de eventos): nao da para concluir; a tela repete muito (laco longo)
- `pes2_osocontramatricial002.php` (INCONCLUSIVO): a resposta difere sem excecao e as divergencias do rastro sao so de infraestrutura (src/V3, src/Core, vendor), que nao explicam a diferenca: compare as linhas da resposta
    - `-$HTTP_USER_AGENT = 'curl/7.81.0';<br>`
    - `+$HTTP_USER_AGENT = 'curl/8.14.1';<br>`
    - `-$HTTP_X_RASTRO_ID = 'r74a_pes2_osocontramatricial002.php';<br>`
- `sys4_indices001.php` (DIVERGE-RECONVERGENTE): resposta igual apos divergencias intermediarias (reconvergente)
- `sys4_processa008.php` (INCONCLUSIVO): rastro truncado (teto de eventos): nao da para concluir; a tela repete muito (laco longo)
- `sys4_verifica002.php` (INCONCLUSIVO): rastro truncado (teto de eventos): nao da para concluir; a tela repete muito (laco longo)

## 4. Causas sem excecao (a saida muda, sem erro)

Estas telas nao quebram: a resposta e diferente. O rastreador aponta a primeira divergencia de valor do codigo da tela (nao e infraestrutura) e a tabela `Onde a resposta difere` do relatorio completo mostra a linha da saida. Confianca **menor** que as causas com excecao.

- `agu1_aguaconsumo999.php` -> `std/label/RotuloCampoDB.php:37`: `excecao_app` (e) acontece **so no 8.5**: excecao: Error: No PostgreSQL connection opened yet
- `agu4_cancelaleituras_classe.php` -> `/var/www/html/vendor/dbseller/legacy/src/PHP53/Emulate.php:110`: `excecao_app` (e) acontece **so no 8.5**: excecao: TypeError: array_key_exists(): Argument #2 ($array) must be of type array, null given
- `ate1_tarefa004.php` -> `ate1_tarefa004.php:346`: `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $tipo
- `ate1_tarefa006.php` -> `forms/db_frmtarefa.php:63`: `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $abrefunc
- `cai4_relinconsextrato002.php` -> `libs/db_libsession.php:51`: `date` (c): 7.4 = string: s8:01:22:45 | 8.5 = string: s8:01:22:46
- `con2_anexodemonstrativofuncaosubfuncao002_2018.php` -> `con2_anexodemonstrativofuncaosubfuncao002_2018.php:44`: `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$sPeriodo
- `fis1_fis_procfiscalfinalizacao002.php` -> `dbforms/db_funcoes.php:201`: `warning` (w) acontece **so no 8.5**: aviso: Undefined global variable $Msituacao_select_descr
- `fis1_fis_sanitario004.php` -> `fis1_fis_sanitario004.php:67`: `excecao_app` (e) acontece **so no 7.4**: excecao: Error: Call to undefined function db_ancora()
- `fis1_sanitario004.php` -> `fis1_sanitario004.php:67`: `excecao_app` (e) acontece **so no 7.4**: excecao: Error: Call to undefined function db_ancora()
- `fis3_fis_relatoriosani.php` -> `fpdf151/fpdf.php:1448`: `` (r): 7.4 = int: 75 | 8.5 = int: 93
- `fis3_relatoriosani.php` -> `fpdf151/fpdf.php:1448`: `` (r): 7.4 = int: 75 | 8.5 = int: 93
- `iss2_relarrec1002.php` -> `iss2_relarrec1002.php:53`: `excecao_app` (e) acontece **so no 8.5**: excecao: TypeError: Unsupported operand types: string + int
- `iss3_emissaoalvaraeventos001.php` -> `model/documentoTemplate.model.php:51`: `sCaminhoTemplate` (a): 7.4 = string: s34:tmp/docTemplate202611280126401.sxw | 8.5 = string: s34:tmp/docTemplate202611280126411.sxw
- `lab1_lab_laboratorio002.php` -> `dbforms/db_funcoes.php:208`: `warning` (w) acontece **so no 8.5**: aviso: Undefined global variable $la02_i_codigo
- `lab1_lab_laboratorio003.php` -> `libs/db_libsession.php:51`: `date` (c): 7.4 = string: s8:01:27:08 | 8.5 = string: s8:01:27:09
- `lic1_trocpcorcamtroca001.php` -> `forms/db_frmtrocpcorcamtrocalic.php:44`: `warning` (w) acontece **so no 8.5**: aviso: Undefined variable $l20_codigo
- `orc2_receitasDespesasPrevidenciariasServidores002.php` -> `orc2_receitasDespesasPrevidenciariasServidores002.php:108`: `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$sModelo
- `pes4_geracaoarquivorefeisul.RPC.php` -> `phar:///var/www/html/ext/php/PHPExcel.phar/PHPExcel/Shared/String.php:529`: `excecao_app` (e) acontece **so no 8.5**: excecao: ParseError: syntax error, unexpected token "{", expecting ")"
- `soc2_declaracaoinss002.php` -> `soc2_declaracaoinss002.php:47`: `warning` (w) acontece **so no 8.5**: aviso: Undefined property: stdClass::$iCodigoNis

## 4b. Correcoes manuais (o rastreador nao acerta estes)

- `ate1_tarefa004.php`: a causa real e `forms/db_frmtarefa.php:976,992` (`$aut = 0` e `$aut=='t'`: `0=='t'` mudou no PHP 8); a linha apontada acima (`:346`, aviso `Undefined variable $tipo`) e verdadeira mas nao explica a diferenca. Ver `rastro-casos-2026-11-27.md` e `rastro-comparacoes-conferencia-2026-11-28.md`.
- `pes2_osocontramatricial002.php`: a resposta difere so porque a pagina imprime `$HTTP_USER_AGENT` (`curl/7.81.0` num contêiner, `curl/8.14.1` no outro): **artefato do ambiente, nao defeito de PHP**.
- Telas em que o backend Xdebug aponta `libs/db_stdlib.php`: e ruido de inicializacao do trace; vale a linha desta tabela (sondas).

## 5. Como reproduzir

```bash
cd regressao && python -m regressao.rastro rastreia <tela>.php --saida rastro-saida   # relatorio.md com cadeia e diff
python -m regressao.rastro rastreia --de-rodada ~/rodadas/base85b --area patrimonial --saida rastro-patrimonial
```
