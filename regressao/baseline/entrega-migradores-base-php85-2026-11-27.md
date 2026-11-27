# Entrega aos migradores - divergencias que restam na base-php85 (2026-11-27)

Rodada: bateria por area em `base-php85` (`ceef42c8d`), PHP 7.4.33 (referencia) contra PHP 8.5.12 (alvo). Cada linha abaixo e uma tela que **responde diferente** nos dois lados. Esta versao cobre as 11 areas da rodada, concluida em 27/11/2026 as 04:59.

## 1. Onde estamos

| Area | DIVERGE antes (111125fb5) | DIVERGE agora (ceef42c8d) |
|---|---|---|
| gestor | 0 | 0 |
| integracoes | 0 | 0 |
| assistenciasocial | 35 | 1 |
| cidadao | 22 | 22 |
| educacao | 125 | 0 |
| saude | 54 | 34 |
| recursoshumanos | 244 | 30 |
| patrimonial | 125 | 57 |
| tributario | 159 | 118 |
| financeiro | 317 | 90 |
| configuracao | 181 | 55 |
| **Total (11 areas)** | **1262** | **407** |

As 383 linhas da planilha cobrem **181 telas distintas** (a mesma tela aparece em mais de uma area quando o prefixo do nome e compartilhado). Fora das telas, ha 5 relatorios, 1 POST (ver secao 4) e 25 timeouts de ambiente em 10 telas (secao 5).

## 2. O que corrigir (por causa, nao por tela)

A maior parte das telas quebra por **poucas causas**. Duas correcoes em arquivos compartilhados (P1 e P2) tratam 17 telas de uma vez; o grosso restante (R1, 110 telas) e o mesmo padrao repetido, tela a tela.

| Grupo | Causa | Telas | Como corrigir |
|---|---|---|---|
| **P1** | pdf.php:186 - menu do rodape do PDF | 11 | fpdf151/pdf.php:186 faz pg_result() sobre uma consulta que falhou (provavel causa, pela leitura do SQL: DB_itemmenu_acessado vazio na sessao de teste gera `where id_item_filho = ` invalido; nao confirmado na sessao). No 7.4 era aviso; no 8.5 e TypeError. UM ajuste resolve todas: so ler o menu se `$rsMenuAcess` for valido e tiver linha; senao usar string vazia. |
| **P2** | DBDate::validaData - checkdate() com string | 6 | std/DBDate.php:203 chama checkdate($mes,$dia,$ano) com string vazia. No 7.4 virava 0 e caia na mensagem 'Data ... inexistente'; no 8.5 e TypeError. UM ajuste resolve todas: `checkdate((int)$mes,(int)$dia,(int)$ano)`. |
| **R2** | pg_* recebe false em biblioteca compartilhada | 5 | Mesma causa de R1, mas num arquivo de biblioteca usado por varias telas (coluna 'onde corrigir'). Corrigir uma vez na biblioteca. |
| **R1** | pg_* recebe false (erro de SQL) na propria tela | 110 | A consulta devolveu false e o resultado vai direto para pg_num_rows/pg_numrows/pg_fetch_assoc/pg_result. Correcao por tela: `if ($rs === false) { db_redireciona/erro }` antes de usar. Ver `Error::getMessage()` com pg_last_error() para saber por que a consulta falha. |
| **A1** | Argumento null onde se espera array | 10 | sizeof/count/array_chunk/implode/rsort/array_keys/array_key_exists recebem null. Inicializar a variavel como array antes (`$x = array()`) ou proteger com `is_array()`/`(array)`. |
| **A2** | Aritmetica com string nao numerica | 4 | Operacao entre string vazia/nao numerica e numero. No 7.4 era aviso e valia 0; no 8.5 e TypeError. Converter com (int)/(float) antes da conta. |
| **A3** | Caminho de arquivo vazio / fopen falhou | 4 | file_exists/fopen/fputs com caminho vazio ou handle false. Validar o caminho/handle. Em sys4_processa004/008 pode ser permissao de escrita do contêiner 8.5 (umask(74)); conferir antes de mexer no codigo. |
| **A4** | Funcao nao carregada (db_ancora) | 2 | Tela chama db_ancora() sem incluir o arquivo que a define. Incluir libs/db_stdlib.php (ou o que a define) na tela. |
| **A5** | ParseError / require de arquivo inexistente | 1 | Erro de sintaxe do PHPExcel.phar (versao antiga no PHP 8) ou require_once de arquivo com caminho/caixa errados. Corrigir o arquivo ou o caminho. |
| **A6** | Assinatura de funcao mudou no PHP 8 | 8 | pg_lo_export() em model/documentoTemplate.model.php:85 usa a ordem antiga (oid, caminho, conn); o PHP 8 exige (conn, oid, caminho). Outros: mktime com string, cal_days_in_month com mes invalido, explode com array, pg_query sem conexao (deprecated), $_SESSION nulo em Emulate.php:110. |
| **C1** | Conteudo difere com 200 nos dois lados | 16 | Sem excecao. Abrir a tela nos dois lados e comparar o trecho indicado na coluna 'mensagem'. |
| **E1** | Diferenca de ambiente (nao e codigo) | 4 | Nao e trabalho do migrador: o contêiner PHP 8.5 nao tem `soffice` (LibreOffice), que existe no 7.4; ou a diferenca e do proprio harness (user-agent `curl/7.81.0` vs `curl/8.14.1`, tamanho do stream Flate de PDF 1199 vs 1198). Tratar na infra/harness. |

### Por que o PHP 7.4 nao falhava

Nos dados de teste (formularios enviados sem preencher), o 7.4 costuma devolver 'Nenhum registro encontrado' ou 'Data inexistente'. O que muda e que o 7.4 transformava o erro em **aviso** e seguia, e o 8.5 transforma em **excecao** (`TypeError`/`ValueError`), que o e-Cidade mostra como 'Notificacao do Sistema - Erro interno' (HTTP 500). Ou seja, o defeito ja existia; o PHP 8 deixou de esconde-lo. Em uso real, com todos os parametros preenchidos, muitas dessas telas podem nao falhar - mas qualquer erro de SQL ou campo vazio derruba a tela inteira, e e isso que a correcao evita.

### Primeiro: os dois ajustes que valem mais

1. `ecidade/fpdf151/pdf.php:186` (P1) - protege **11 telas** de relatorio em PDF de uma vez.
```php
$rsMenuAcess = db_query($conn, $sSqlMenuAcess);
$sMenuAcess  = ($rsMenuAcess && pg_num_rows($rsMenuAcess) > 0)
    ? substr(pg_result($rsMenuAcess, 0, "menu"), 0, 50)
    : '';
```

2. `ecidade/std/DBDate.php:203` (P2) - **6 telas**.
```php
if (!checkdate((int)$mes, (int)$dia, (int)$ano)) {
```

Depois desses dois, rode de novo as areas afetadas: varias telas passam a mostrar o proximo erro (P1 esconde o seguinte), entao a lista encolhe em etapas.

## 3. Lista por area (cada tela com o motivo e onde corrigir)

Coluna **Est.**: `estavel` = a referencia 7.4 responde igual nas duas leituras; `ref-instavel` = a propria resposta do 7.4 muda entre leituras (data/hora no PDF), mas o 8.5 tambem falha, entao entra na lista.

### assistenciasocial (1 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `soc2_declaracaoinss002.php` | E1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: -<script>location.href='db_erros.php?fechar=true&db_erro=Falhou ao determinar o tipo |

### cidadao (20 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `con2_lrflimites002_2015.php` | A6 | estavel | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `con2_lrfanexoxvii002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_i_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_ii_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo11_002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | R2 | estavel | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

### saude (34 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `lab2_producao002.php` | A1 | estavel | `lab2_producao002.php:94` | TypeError: implode(): If argument #1 ($x) is of type string, argument #2 ($x) must be of type array, null given |
| `sau2_bpa001.php` | A3 | estavel | `sau2_bpa001.php:42` | ValueError: Path must not be empty |
| `lab2_mapacoletaconsulta.php` | A6 | estavel | `lab2_mapacoletaconsulta.php:22` | TypeError: mktime(): Argument #5 ($x) must be of type ?int, string given |
| `sau1_valores001.php` | A6 | estavel | `libs/db_stdlib.php:112` | TypeError: pg_query(): Argument #1 ($x) must be of type PgSql\Connection, null given |
| `lab1_lab_laboratorio002.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - // + js_tipo(0); |
| `lab1_lab_laboratorio003.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - // + js_tipo(0); |
| `sau1_cgs_undoutros002.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - new Array( // -new Array("", ''), |
| `far2_distribuicao002.php` | R1 | estavel | `far2_distribuicao002.php:282` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `far2_historicopaciente002.php` | R1 | estavel | `far2_historicopaciente002.php:140` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `far2_historicoprogmedicamento002.php` | R1 | estavel | `far2_historicoprogmedicamento002.php:135` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `far2_historicoprogpaciente002.php` | R1 | estavel | `far2_historicoprogpaciente002.php:136` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `far2_mapaconsolidado003.php` | R1 | estavel | `far2_mapaconsolidado003.php:58` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `far2_pacienteprogramatica002.php` | R1 | estavel | `far2_pacienteprogramatica002.php:120` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_agendaexterna003.php` | R1 | estavel | `sau2_agendaexterna003.php:72` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_atendimentos002.php` | R1 | estavel | `sau2_atendimentos002.php:76` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_boletim002.php` | R1 | estavel | `sau2_boletim002.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_cgscorretos002.php` | R1 | ref-instavel | `sau2_cgscorretos002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_especialidades002.php` | R1 | estavel | `sau2_especialidades002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_faausuarios002.php` | R1 | estavel | `sau2_faausuarios002.php:99` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_grafsaude002.php` | R1 | estavel | `sau2_grafsaude002.php:68` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_indicemorb002.php` | R1 | estavel | `sau2_indicemorb002.php:80` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_procedimentos002.php` | R1 | estavel | `sau2_procedimentos002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_procedimentos003.php` | R1 | estavel | `sau2_procedimentos003.php:61` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_procmedicos002.php` | R1 | estavel | `sau2_procmedicos002.php:65` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_progmun002.php` | R1 | estavel | `sau2_progmun002.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_prontuarios002.php` | R1 | estavel | `sau2_prontuarios002.php:53` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_relatorioprocedimentos002.php` | R1 | estavel | `sau2_relatorioprocedimentos002.php:163` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_sitagendamentos002.php` | R1 | estavel | `sau2_sitagendamentos002.php:52` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau2_unidades002.php` | R1 | estavel | `sau2_unidades002.php:117` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau3_consultasaude003.php` | R1 | estavel | `sau3_consultasaude003.php:52` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau4_consultamedica004.php` | R1 | estavel | `sau4_consultamedica004.php:55` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau4_prontuariomedico002.php` | R1 | estavel | `sau4_prontuariomedico002.php:48` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sau4_triagemproc001.php` | R1 | estavel | `sau4_triagemproc001.php:90` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `lab2_inconsistenciasimportacaoresultado002.php` | R2 | estavel | `src/Saude/Laboratorio/Repository/ImportacaoRequisicaoInconsistenciaRepository.php:117` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

### recursoshumanos (29 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `pes4_geraarquivosmanadnovo.php` | A1 | estavel | `model/manad.model.php:129` | TypeError: implode(): If argument #1 ($x) is of type string, argument #2 ($x) must be of type array, null given |
| `pes4_geracaoarquivorefeisul.RPC.php` | A5 | estavel | `` | E_ERROR - Uncaught exception 'ParseError' with message 'syntax error, unexpected token "{", expecting ")"' in phar://ext/php/PHPEx |
| `con2_lrflimites002_2015.php` | A6 | estavel | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `pes2_feriasaviso002.php` | A6 | estavel | `pes2_feriasaviso002.php:112` | ValueError: cal_days_in_month(): Argument #2 ($x) must be between 1 and 2147483646 |
| `cai4_relinconsextrato002.php` | C1 | ref-instavel | `` | resposta 200 nos dois lados, conteudo difere: -zhzÒ/PN%)ó*ùð.? // -þv-- |
| `lic1_trocpcorcamtroca001.php` | C1 | ref-instavel | `` | resposta 200 nos dois lados, conteudo difere: -<script> Sfdump = window.Sfdump // (function (doc) { var refStyle = doc.createEleme |
| `pes4_geraarquivosmanad.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - </script><script>js_termo_termometro(0,'Processando Tabela : 0000')</script> // -L |
| `pes2_osocontramatricial002.php` | E1 | ref-instavel | `` | resposta 200 nos dois lados, conteudo difere: -$HTTP_USER_AGENT = 'curl/7.81.0';<br> // +$HTTP_USER_AGENT = 'curl/8.14.1';<br> |
| `con2_lrfanexoxvii002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_i_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_ii_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `pes2_rubmesponto002.php` | R1 | estavel | `pes2_rubmesponto002.php:214` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cai3_gerfinanc003.php` | R2 | estavel | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | R2 | estavel | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

### patrimonial (53 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `cad2_emissaobic_002.php` | A1 | estavel | `cad2_emissaobic_002.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad3_conscadastro_relatorio.php` | A1 | estavel | `cad3_conscadastro_relatorio.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad4_recadastramentorelatorio.php` | A1 | estavel | `cad4_recadastramentorelatorio.php:106` | TypeError: array_chunk(): Argument #1 ($x) must be of type array, null given |
| `orc2_atividades002.php` | A2 | estavel | `fpdf151/fpdf.php:932` | TypeError: Unsupported operand types: int + string |
| `con2_lrflimites002_2015.php` | A6 | estavel | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `con4_docpadrao010.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: -0*8°÷t}¯íu¨}Àé#Þ3=vËÀÉs¼ÕAosÉæ]ÿ +ÄT1 // +0*8°÷t}¯íu¨}ÀõG¼g2,zì?çx«Þæ |
| `orc2_receitasDespesasPrevidenciariasServidores002.php` | C1 | ref-instavel | `` | resposta 200 nos dois lados, conteudo difere: -xËnÉ×ÑSYØ©Ü÷,h68D // - |
| `con2_lrfanexoxvii002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_i_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_ii_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `cad2_carnesiptu002.php` | R1 | estavel | `cad2_carnesiptu002.php:57` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_comparaiptu002.php` | R1 | ref-instavel | `cad2_comparaiptu002.php:154` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_compcaract002.php` | R1 | estavel | `cad2_compcaract002.php:124` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_descconced002.php` | R1 | estavel | `cad2_descconced002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_iptulancpago002.php` | R1 | estavel | `cad2_iptulancpago002.php:60` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_listaiptucalc_003.php` | R1 | estavel | `cad2_listaiptucalc_003.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteam002.php` | R1 | estavel | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteamentomatric002.php` | R1 | estavel | `cad2_loteamentomatric002.php:80` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteamentos002.php` | R1 | estavel | `cad2_loteamentos002.php:77` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_matricnaoproc002.php` | R1 | estavel | `cad2_matricnaoproc002.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_posicaoiptu002.php` | R1 | estavel | `cad2_posicaoiptu002.php:71` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relaverbacao002.php` | R1 | estavel | `cad2_relaverbacao002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_reldemo002.php` | R1 | estavel | `cad2_reldemo002.php:108` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relisentos002.php` | R1 | estavel | `cad2_relisentos002.php:46` | TypeError: pg_fetch_assoc(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relmassafalida002.php` | R1 | estavel | `cad2_relmassafalida002.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_setor002.php` | R1 | estavel | `cad2_setor002.php:79` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_conscadastrodetalhesmodelonovo002.php` | R1 | estavel | `cad3_conscadastrodetalhesmodelonovo002.php:171` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_iptupago002_original.php` | R1 | estavel | `cad3_iptupago002_original.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_relzonafiscal002.php` | R1 | ref-instavel | `cad3_relzonafiscal002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_relzonafiscaltaxa002.php` | R1 | estavel | `cad3_relzonafiscaltaxa002.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt.php` | R1 | estavel | `cad4_geracarneiptutxt.php:754` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_arapiraca.php` | R1 | estavel | `cad4_geracarneiptutxt_arapiraca.php:170` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_eldorado.php` | R1 | estavel | `cad4_geracarneiptutxt_eldorado.php:167` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_guaiba.php` | R1 | ref-instavel | `cad4_geracarneiptutxt_guaiba.php:169` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarnesiptu_geral.php` | R1 | estavel | `cad4_geracarnesiptu_geral.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cai3_gerfinanc003.php` | R2 | estavel | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | R2 | estavel | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `orc2_desppessoal002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

### tributario (113 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `agu3_conscadastro_relatorio.php` | A1 | estavel | `agu3_conscadastro_relatorio.php:37` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad2_emissaobic_002.php` | A1 | estavel | `cad2_emissaobic_002.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad3_conscadastro_relatorio.php` | A1 | estavel | `cad3_conscadastro_relatorio.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad4_recadastramentorelatorio.php` | A1 | ref-instavel | `cad4_recadastramentorelatorio.php:106` | TypeError: array_chunk(): Argument #1 ($x) must be of type array, null given |
| `iss3_inconsistenciaSimples.php` | A1 | estavel | `iss3_inconsistenciaSimples.php:62` | TypeError: rsort(): Argument #1 ($x) must be of type array, null given |
| `jur2_geradoc.php` | A1 | ref-instavel | `jur2_geradoc.php:74` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `jur2_inicialquit002.php` | A1 | estavel | `jur2_inicialquit002.php:60` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `sys4_listaretornosql001.php` | A1 | estavel | `sys4_listaretornosql001.php:67` | TypeError: array_keys(): Argument #1 ($x) must be of type array, null given |
| `div2_resumogeraldivida002.php` | A2 | estavel | `classes/db_divida_classe.php:2378` | TypeError: Unsupported operand types: string - int |
| `iss2_relarrec1002.php` | A2 | estavel | `iss2_relarrec1002.php:53` | TypeError: Unsupported operand types: string + int |
| `itbi_simulacaoitbi002.php` | A2 | estavel | `itbi_simulacaoitbi002.php:237` | TypeError: Unsupported operand types: string / int |
| `sys4_consultaXML.RPC.php` | A3 | estavel | `sys4_consultaXML.RPC.php:39` | ValueError: Path must not be empty |
| `sys4_processa004.php` | A3 | estavel | `sys4_processa004.php:111` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `sys4_processa008.php` | A3 | estavel | `sys4_processa008.php:100` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `fis1_fis_sanitario004.php` | A4 | estavel | `fis1_fis_sanitario004.php:67` | Error: Call to undefined function db_ancora() |
| `fis1_sanitario004.php` | A4 | estavel | `fis1_sanitario004.php:67` | Error: Call to undefined function db_ancora() |
| `agu1_aguaconsumo999.php` | A6 | estavel | `std/label/RotuloCampoDB.php:37` | Error: No PostgreSQL connection opened yet |
| `agu4_cancelaleituras_classe.php` | A6 | estavel | `vendor/dbseller/legacy/src/PHP53/Emulate.php:110` | TypeError: array_key_exists(): Argument #2 ($x) must be of type array, null given |
| `con2_lrflimites002_2015.php` | A6 | estavel | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `fis1_fis_procfiscalfinalizacao002.php` | A6 | estavel | `` | resposta 200 nos dois lados, conteudo difere: +<br /> // +<b>Deprecated</b>: pg_query(): Automatic fetching of PostgreSQL connecti |
| `iss3_emissaoalvaraeventos001.php` | A6 | estavel | `model/documentoTemplate.model.php:85` | ArgumentCountError: Requires 2 or 3 arguments, 3 given |
| `con2_anexodemonstrativofuncaosubfuncao002_2018.php` | C1 | ref-instavel | `` | resposta 200 nos dois lados, conteudo difere: -s£K!ôXÅ¾ßíÑE\Á_ákÞÅÚë¿B@åC`ñºí¬ßü!ª Î!°ð¡d£ân_½¯ // +s£K!ôXÅ¾ßíÑE\Á_h |
| `sys4_libimpmax001.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - </select> </td> // - </tr> |
| `fis3_fis_relatoriosani.php` | E1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: -<</Filter /FlateDecode /Length 863>> // +<</Filter /FlateDecode /Length 860>> |
| `fis3_relatoriosani.php` | E1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: -<</Filter /FlateDecode /Length 889>> // +<</Filter /FlateDecode /Length 887>> |
| `con2_lrfanexoxvii002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_i_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_ii_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `agu1_aguahidromatricfichatroca002.php` | R1 | estavel | `agu1_aguahidromatricfichatroca002.php:61` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu2_compleituras002.php` | R1 | estavel | `agu2_compleituras002.php:161` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu2_hidrometro002.php` | R1 | estavel | `agu2_hidrometro002.php:70` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu2_relconsumo002.php` | R1 | estavel | `agu2_relconsumo002.php:166` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu2_relimobiliarias002.php` | R1 | estavel | `agu2_relimobiliarias002.php:86` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu2_relimoveiscar002.php` | R1 | estavel | `agu2_relimoveiscar002.php:72` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu2_situacaohidro002.php` | R1 | estavel | `agu2_situacaohidro002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu4_relcorte.php` | R1 | ref-instavel | `agu4_relcorte.php:36` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `agu4_relleituras002.php` | R1 | estavel | `agu4_relleituras002.php:54` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `arr2_rellistadqd002.php` | R1 | estavel | `arr2_rellistadqd002.php:178` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_carnesiptu002.php` | R1 | estavel | `cad2_carnesiptu002.php:57` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_comparaiptu002.php` | R1 | ref-instavel | `cad2_comparaiptu002.php:154` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_compcaract002.php` | R1 | estavel | `cad2_compcaract002.php:124` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_descconced002.php` | R1 | estavel | `cad2_descconced002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_iptulancpago002.php` | R1 | estavel | `cad2_iptulancpago002.php:60` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_listaiptucalc_003.php` | R1 | estavel | `cad2_listaiptucalc_003.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteam002.php` | R1 | estavel | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteamentomatric002.php` | R1 | estavel | `cad2_loteamentomatric002.php:80` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteamentos002.php` | R1 | estavel | `cad2_loteamentos002.php:77` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_matricnaoproc002.php` | R1 | estavel | `cad2_matricnaoproc002.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_posicaoiptu002.php` | R1 | estavel | `cad2_posicaoiptu002.php:71` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relaverbacao002.php` | R1 | estavel | `cad2_relaverbacao002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_reldemo002.php` | R1 | estavel | `cad2_reldemo002.php:108` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relisentos002.php` | R1 | estavel | `cad2_relisentos002.php:46` | TypeError: pg_fetch_assoc(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relmassafalida002.php` | R1 | estavel | `cad2_relmassafalida002.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_setor002.php` | R1 | estavel | `cad2_setor002.php:79` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_conscadastrodetalhesmodelonovo002.php` | R1 | estavel | `cad3_conscadastrodetalhesmodelonovo002.php:171` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_iptupago002_original.php` | R1 | estavel | `cad3_iptupago002_original.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_relzonafiscal002.php` | R1 | estavel | `cad3_relzonafiscal002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_relzonafiscaltaxa002.php` | R1 | estavel | `cad3_relzonafiscaltaxa002.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt.php` | R1 | estavel | `cad4_geracarneiptutxt.php:754` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_arapiraca.php` | R1 | estavel | `cad4_geracarneiptutxt_arapiraca.php:170` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_eldorado.php` | R1 | estavel | `cad4_geracarneiptutxt_eldorado.php:167` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_guaiba.php` | R1 | estavel | `cad4_geracarneiptutxt_guaiba.php:169` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarnesiptu_geral.php` | R1 | estavel | `cad4_geracarnesiptu_geral.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cem2_edital002.php` | R1 | estavel | `cem2_edital002.php:87` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_diviano002.php` | R1 | estavel | `div2_diviano002.php:94` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_exercdivida002.php` | R1 | estavel | `div2_exercdivida002.php:392` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_parcel002.php` | R1 | estavel | `div2_parcel002.php:151` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_posicaoparc002.php` | R1 | estavel | `div2_posicaoparc002.php:247` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_procedexerc_002.php` | R1 | ref-instavel | `div2_procedexerc_002.php:130` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `dv02_loteamentos002.php` | R1 | estavel | `dv02_loteamentos002.php:48` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `dvr2_capaloteamento002.php` | R1 | estavel | `dvr2_capaloteamento002.php:61` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `dvr3_procedper002.php` | R1 | ref-instavel | `dvr3_procedper002.php:135` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `dvr4_parclote004.php` | R1 | estavel | `dvr4_parclote004.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `dvr4_parclote005.php` | R1 | estavel | `dvr4_parclote005.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `fis2_emiteaidof002.php` | R1 | estavel | `fis2_emiteaidof002.php:105` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `fis2_fis_levantamentolote002.php` | R1 | estavel | `fis2_fis_levantamentolote002.php:245` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `fis2_fis_levantamentomassa002.php` | R1 | ref-instavel | `fis2_fis_levantamentomassa002.php:168` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `fis2_fis_termofiscal003.php` | R1 | estavel | `fis2_fis_termofiscal003.php:122` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `fis3_fis_consultaautoinf_imp.php` | R1 | estavel | `fis3_fis_consultaautoinf_imp.php:57` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `fis3_fis_imprimealvara.php` | R1 | estavel | `fis3_fis_imprimealvara.php:64` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `inf2_inflan002.php` | R1 | estavel | `inf2_inflan002.php:126` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_calculadoepago002.php` | R1 | estavel | `iss2_calculadoepago002.php:113` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_certibaixa002.php` | R1 | estavel | `iss2_certibaixa002.php:55` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_inscrescrito002.php` | R1 | estavel | `iss2_inscrescrito002.php:81` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_issqnpago002.php` | R1 | estavel | `iss2_issqnpago002.php:67` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_listinscrweb002.php` | R1 | estavel | `iss2_listinscrweb002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_relatorioruas002.php` | R1 | estavel | `iss2_relatorioruas002.php:179` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss3_emissaoalvaraveiculos001.php` | R1 | estavel | `iss3_emissaoalvaraveiculos001.php:64` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss3_emissaobicveiculos001.php` | R1 | estavel | `iss3_emissaobicveiculos001.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss4_contativ003.php` | R1 | estavel | `iss4_contativ003.php:222` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss4_contativ006.php` | R1 | estavel | `iss4_contativ006.php:86` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `itb2_relsetorquadralote002.php` | R1 | estavel | `itb2_relsetorquadralote002.php:255` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `jur2_relinicial002.php` | R1 | estavel | `jur2_relinicial002.php:170` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_processa002.php` | R1 | estavel | `sys4_processa002.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_processa007.php` | R1 | estavel | `sys4_processa007.php:587` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_verifica002.php` | R1 | estavel | `sys4_verifica002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cai3_gerfinanc003.php` | R2 | estavel | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | R2 | estavel | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

### financeiro (82 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `cad2_emissaobic_002.php` | A1 | estavel | `cad2_emissaobic_002.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad3_conscadastro_relatorio.php` | A1 | ref-instavel | `cad3_conscadastro_relatorio.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `cad4_recadastramentorelatorio.php` | A1 | estavel | `cad4_recadastramentorelatorio.php:106` | TypeError: array_chunk(): Argument #1 ($x) must be of type array, null given |
| `iss3_inconsistenciaSimples.php` | A1 | estavel | `iss3_inconsistenciaSimples.php:62` | TypeError: rsort(): Argument #1 ($x) must be of type array, null given |
| `pes4_geraarquivosmanadnovo.php` | A1 | estavel | `model/manad.model.php:129` | TypeError: implode(): If argument #1 ($x) is of type string, argument #2 ($x) must be of type array, null given |
| `sys4_listaretornosql001.php` | A1 | estavel | `sys4_listaretornosql001.php:67` | TypeError: array_keys(): Argument #1 ($x) must be of type array, null given |
| `div2_resumogeraldivida002.php` | A2 | ref-instavel | `classes/db_divida_classe.php:2378` | TypeError: Unsupported operand types: string - int |
| `iss2_relarrec1002.php` | A2 | estavel | `iss2_relarrec1002.php:53` | TypeError: Unsupported operand types: string + int |
| `orc2_atividades002.php` | A2 | ref-instavel | `fpdf151/fpdf.php:932` | TypeError: Unsupported operand types: int + string |
| `sys4_consultaXML.RPC.php` | A3 | estavel | `sys4_consultaXML.RPC.php:39` | ValueError: Path must not be empty |
| `sys4_processa004.php` | A3 | estavel | `sys4_processa004.php:111` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `sys4_processa008.php` | A3 | estavel | `sys4_processa008.php:100` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `pes4_geracaoarquivorefeisul.RPC.php` | A5 | estavel | `` | E_ERROR - Uncaught exception 'ParseError' with message 'syntax error, unexpected token "{", expecting ")"' in phar://ext/php/PHPEx |
| `con2_lrflimites002_2015.php` | A6 | estavel | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `iss3_emissaoalvaraeventos001.php` | A6 | estavel | `model/documentoTemplate.model.php:85` | ArgumentCountError: Requires 2 or 3 arguments, 3 given |
| `pes2_feriasaviso002.php` | A6 | estavel | `pes2_feriasaviso002.php:112` | ValueError: cal_days_in_month(): Argument #2 ($x) must be between 1 and 2147483646 |
| `con2_lrfanexoxvii002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_i_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_ii_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `cad2_carnesiptu002.php` | R1 | estavel | `cad2_carnesiptu002.php:57` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_comparaiptu002.php` | R1 | ref-instavel | `cad2_comparaiptu002.php:154` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_compcaract002.php` | R1 | estavel | `cad2_compcaract002.php:124` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_descconced002.php` | R1 | estavel | `cad2_descconced002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_iptulancpago002.php` | R1 | estavel | `cad2_iptulancpago002.php:60` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_listaiptucalc_003.php` | R1 | estavel | `cad2_listaiptucalc_003.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteam002.php` | R1 | estavel | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteamentomatric002.php` | R1 | estavel | `cad2_loteamentomatric002.php:80` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_loteamentos002.php` | R1 | estavel | `cad2_loteamentos002.php:77` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_matricnaoproc002.php` | R1 | estavel | `cad2_matricnaoproc002.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_posicaoiptu002.php` | R1 | estavel | `cad2_posicaoiptu002.php:71` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relaverbacao002.php` | R1 | estavel | `cad2_relaverbacao002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_reldemo002.php` | R1 | estavel | `cad2_reldemo002.php:108` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relisentos002.php` | R1 | estavel | `cad2_relisentos002.php:46` | TypeError: pg_fetch_assoc(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_relmassafalida002.php` | R1 | estavel | `cad2_relmassafalida002.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad2_setor002.php` | R1 | estavel | `cad2_setor002.php:79` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_conscadastrodetalhesmodelonovo002.php` | R1 | estavel | `cad3_conscadastrodetalhesmodelonovo002.php:171` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_iptupago002_original.php` | R1 | estavel | `cad3_iptupago002_original.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_relzonafiscal002.php` | R1 | estavel | `cad3_relzonafiscal002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad3_relzonafiscaltaxa002.php` | R1 | ref-instavel | `cad3_relzonafiscaltaxa002.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt.php` | R1 | estavel | `cad4_geracarneiptutxt.php:754` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_arapiraca.php` | R1 | estavel | `cad4_geracarneiptutxt_arapiraca.php:170` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_eldorado.php` | R1 | estavel | `cad4_geracarneiptutxt_eldorado.php:167` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarneiptutxt_guaiba.php` | R1 | estavel | `cad4_geracarneiptutxt_guaiba.php:169` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cad4_geracarnesiptu_geral.php` | R1 | estavel | `cad4_geracarnesiptu_geral.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_diviano002.php` | R1 | estavel | `div2_diviano002.php:94` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_exercdivida002.php` | R1 | estavel | `div2_exercdivida002.php:392` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_parcel002.php` | R1 | estavel | `div2_parcel002.php:151` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_posicaoparc002.php` | R1 | estavel | `div2_posicaoparc002.php:247` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `div2_procedexerc_002.php` | R1 | estavel | `div2_procedexerc_002.php:130` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `inf2_inflan002.php` | R1 | estavel | `inf2_inflan002.php:126` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_calculadoepago002.php` | R1 | estavel | `iss2_calculadoepago002.php:113` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_certibaixa002.php` | R1 | estavel | `iss2_certibaixa002.php:55` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_inscrescrito002.php` | R1 | ref-instavel | `iss2_inscrescrito002.php:81` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_issqnpago002.php` | R1 | estavel | `iss2_issqnpago002.php:67` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_listinscrweb002.php` | R1 | estavel | `iss2_listinscrweb002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss2_relatorioruas002.php` | R1 | estavel | `iss2_relatorioruas002.php:179` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss3_emissaoalvaraveiculos001.php` | R1 | estavel | `iss3_emissaoalvaraveiculos001.php:64` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss3_emissaobicveiculos001.php` | R1 | estavel | `iss3_emissaobicveiculos001.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss4_contativ003.php` | R1 | estavel | `iss4_contativ003.php:222` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `iss4_contativ006.php` | R1 | estavel | `iss4_contativ006.php:86` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `pes2_rubmesponto002.php` | R1 | estavel | `pes2_rubmesponto002.php:214` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_processa002.php` | R1 | estavel | `sys4_processa002.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_processa007.php` | R1 | estavel | `sys4_processa007.php:587` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_verifica002.php` | R1 | estavel | `sys4_verifica002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cai3_gerfinanc003.php` | R2 | estavel | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | R2 | estavel | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `orc2_desppessoal002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

### configuracao (51 telas)

| Tela | Grupo | Est. | Onde corrigir | Erro |
|---|---|---|---|---|
| `sys4_listaretornosql001.php` | A1 | estavel | `sys4_listaretornosql001.php:67` | TypeError: array_keys(): Argument #1 ($x) must be of type array, null given |
| `orc2_atividades002.php` | A2 | estavel | `fpdf151/fpdf.php:932` | TypeError: Unsupported operand types: int + string |
| `sys4_consultaXML.RPC.php` | A3 | estavel | `sys4_consultaXML.RPC.php:39` | ValueError: Path must not be empty |
| `sys4_processa004.php` | A3 | estavel | `sys4_processa004.php:111` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `sys4_processa008.php` | A3 | estavel | `sys4_processa008.php:100` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `con2_lrflimites002_2015.php` | A6 | estavel | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `ate1_tarefa004.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: -js_OpenJanelaIframe('CurrentWindow.corpo.iframe_tarefa','db_iframe_tarefa','func_ta |
| `ate1_tarefa006.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: -js_OpenJanelaIframe('CurrentWindow.corpo.iframe_tarefa','db_iframe_tarefa','func_ta |
| `ate1_tarefaagenda002.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - </center> // -</form> |
| `ate1_tarefalogand002.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - <select name="at48_situacao" id="at48_situacao" // - onchange="js_ProcCod_at48_sit |
| `ate3_consultacalendario_agenda.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - <script> // - function js_abre_agendamento(tarefa) { |
| `ate4_atendsup001.php` | C1 | estavel | `` | resposta 200 nos dois lados, conteudo difere: - </b> // - </td> |
| `con2_lrfanexoxvii002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfdivida002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfgarantias002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrflimites002_2010.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_lrfreceitacorrente002_2018.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2010.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2012.php` | P1 | estavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_opercredito002_2015.php` | P1 | ref-instavel | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo17_002_2011.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_i_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_anexo_ii_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_balancoorcamentario_2014.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfbalorc002_2015.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `con2_lrfdemalienataplicrecursos002_2010.php` | P2 | estavel | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `ate1_clientesmodulosproc002.php` | R1 | estavel | `forms/db_frmclientesmodulosproc.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate1_tarefa010.php` | R1 | estavel | `ate1_tarefa010.php:78` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate1_tarefaobs001.php` | R1 | estavel | `ate1_tarefaobs001.php:106` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate2_relatendnaolanc002.php` | R1 | ref-instavel | `ate2_relatendnaolanc002.php:58` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate2_relatorio001.php` | R1 | estavel | `ate2_relatorio001.php:126` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate2_relclienteproced002.php` | R1 | estavel | `ate2_relclienteproced002.php:242` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate2_reltarefaagenda002.php` | R1 | estavel | `ate2_reltarefaagenda002.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate3_atendimento002.php` | R1 | estavel | `ate3_atendimento002.php:133` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate3_constarefaanexos.php` | R1 | estavel | `ate3_constarefaanexos.php:159` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate3_consultaacesso002.php` | R1 | estavel | `ate3_consultaacesso002.php:179` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate3_consultaacesso003.php` | R1 | estavel | `ate3_consultaacesso003.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate3_consultaacesso004.php` | R1 | estavel | `ate3_consultaacesso004.php:60` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate4_atend002.php` | R1 | estavel | `forms/db_frmatend.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate4_pesquisatarefacod.RPC.php` | R1 | estavel | `ate4_pesquisatarefacod.RPC.php:50` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `ate4_pesquisatarefadescr.RPC.php` | R1 | estavel | `ate4_pesquisatarefadescr.RPC.php:50` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_processa002.php` | R1 | estavel | `sys4_processa002.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_processa007.php` | R1 | estavel | `sys4_processa007.php:587` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `sys4_verifica002.php` | R1 | estavel | `sys4_verifica002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `cai3_gerfinanc003.php` | R2 | estavel | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_anexo11_002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `con2_contasrecdesp002.php` | R2 | estavel | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `orc2_desppessoal002.php` | R2 | estavel | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

## 4. Relatorios e POST que tambem divergem

- Relatorios (PDF) com HTTP 200 no 7.4 e **500** no 8.5, mesma familia de P1/R2: `con2_contasrecdesp002.php`, `cad2_loteam002.php`, `orc2_desppessoal002.php`, `div2_resumogeraldivida002.php`, `agu2_relconsumo002.php`.
- POST `agu1_aguabasevenc001.php`: **SQL de escrita diverge** (os dois lados gravam SQL diferente). Esse e o unico caso que escreve no banco; comparar o SQL gravado nos dois lados antes de mexer.

## 5. O que nao e codigo (nao conta como aprovado nem como defeito)

- **25 ERRO_AMBIENTE por timeout (10 telas distintas; a mesma tela conta em varias areas)** (a referencia 7.4 passa de 60 s): `con4_gerenciadortarefas002.php`, `rec2_espelhoponto002.php`, e as 8 telas `edu4_*` do censo/INEP. Nao ha veredito; precisam de rodada manual.
- **Lacuna do contêiner 8.5:** falta `soffice` (LibreOffice). Afeta `soc2_declaracaoinss002.php`. O 7.4 tem. Instalar na imagem do 8.5 antes de julgar a tela.
- **INCONCLUSIVO** (telas que respondem vazio ou com pagina de erro identica nos dois lados): cerca de 2.580 nas 11 areas. Nao foram exercitadas; o veredito e 'nao sei', nunca 'aprovado'.

## 6. Como reproduzir e verificar

```bash
# uma area (o 8.5 e comparado com o 7.4 ao vivo)
cd regressao && .venv/bin/python -m regressao.php.bateria --saida ~/rodadas/x/<area> --area <area> --pular sintaxe --pular classes
# resultado: <saida>/resultado.json (veredito por tela), resumo.md, diffs/
```
Depois de corrigir, rodar a area de novo: a tela some da lista quando passa a IDENTICO. Os logs de erro reais do 8.5 ficam em `ecidade/extension/log/error.log` dentro do contêiner `ecidade74_php85` (o log do PHP, `/var/log/php_errors.log`, nao mostra esses erros).

## 7. Pendente neste documento

- Esta lista foi gerada reexecutando cada tela divergente uma vez em cada lado (e duas vezes no 7.4, para detectar instabilidade). Nao foi feita revisao tela a tela do codigo: os grupos vem da mensagem de erro do proprio PHP 8.

