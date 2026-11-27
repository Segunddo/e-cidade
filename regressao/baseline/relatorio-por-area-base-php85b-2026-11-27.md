# Relatorio por area - DIVERGE, INCONCLUSIVO e ERRO_AMBIENTE (base-php85, rodada 2026-11-26/27)

Rodada `base85b` em `ceef42c8d`: PHP 7.4.33 (referencia) contra PHP 8.5.12 (alvo), 11 areas, concluida em 27/11/2026 as 04:59. A lista completa, uma linha por caso, esta em `relatorio-por-area-base-php85b-2026-11-27.tsv` (filtre por `area` e `veredito`). As causas e as correcoes de cada DIVERGE estao em `entrega-migradores-base-php85-2026-11-27.md`.

## Como ler os vereditos

| Veredito | Significa | Conta como aprovado? | O que o migrador faz |
|---|---|---|---|
| IDENTICO | Resposta igual nos dois lados e a tela foi exercitada | Sim | Nada |
| **DIVERGE** | Resposta diferente: o 8.5 se comporta diferente do 7.4 | **Nao** | Corrigir (ver grupo e `onde_corrigir`) |
| **INCONCLUSIVO** | A tela nao foi exercitada de verdade: os dois lados devolvem a mesma pagina de erro, ou resposta vazia, ou a tela foi pulada | **Nao** | Testar a tela a mao, com dados validos; so entao ha veredito |
| **ERRO_AMBIENTE** | O teste nao conseguiu medir (timeout, sessao, banco) | **Nao** | Rodar a tela isolada; nao e defeito de codigo ate prova em contrario |

## 1. Resumo por area

| Area | IDENTICO | DIVERGE | INCONCLUSIVO | ERRO_AMBIENTE | Total |
|---|---|---|---|---|---|
| gestor | 7 | 0 | 0 | 0 | 7 |
| integracoes | 97 | 0 | 1 | 0 | 98 |
| assistenciasocial | 732 | 1 | 38 | 1 | 772 |
| cidadao | 1412 | 22 | 203 | 1 | 1638 |
| educacao | 2018 | 0 | 173 | 8 | 2199 |
| saude | 1476 | 34 | 80 | 0 | 1590 |
| recursoshumanos | 3721 | 30 | 331 | 2 | 4084 |
| patrimonial | 5335 | 57 | 428 | 1 | 5821 |
| tributario | 5512 | 118 | 400 | 2 | 6032 |
| financeiro | 6183 | 90 | 467 | 1 | 6741 |
| configuracao | 4977 | 55 | 461 | 9 | 5502 |
| **Total** | **31470** | **407** | **2582** | **25** | **34484** |

Os totais contam casos (telas, relatorios e POSTs) por area; a mesma tela entra em mais de uma area quando o prefixo do nome e compartilhado (ex.: `con2_*`).

## 2. Detalhe por area

### gestor

IDENTICO 7 | DIVERGE 0 | INCONCLUSIVO 0 | ERRO_AMBIENTE 0

### integracoes

IDENTICO 97 | DIVERGE 0 | INCONCLUSIVO 1 | ERRO_AMBIENTE 0

**INCONCLUSIVO (1)**

- pagina de erro identica nos dois lados (tela nao exercitada): **1**
  <details><summary>lista</summary>

  `eso02_preenchimentoesocial001.php`

  </details>

### assistenciasocial

IDENTICO 732 | DIVERGE 1 | INCONCLUSIVO 38 | ERRO_AMBIENTE 1

**DIVERGE (1)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:soc2_declaracaoinss002.php` | E1 | `` | resposta 200 nos dois lados, conteudo difere: -<script>location.href='db_erros.php?fechar=true&db_erro=Falhou  |

**ERRO_AMBIENTE (1)**

- `tela:rec2_espelhoponto002.php` - timeout: ref=000  85=500 (apos 1 retentativa)

**INCONCLUSIVO (38)**

- pagina de erro identica nos dois lados (tela nao exercitada): **24**
  <details><summary>lista</summary>

  `pro1_cgmdoc002.php`, `pro1_cgmdoc003.php`, `pro1_obras004.php`, `pro1_obrasconstr002.php`, `pro1_obrasconstr003.php`, `pro1_procandamint001.php`, `pro1_procandamint002.php`, `pro1_procandamint003.php`, `pro1_protparamglobal001.php`, `pro1_protparamglobal003.php`, `pro1_protprocesso001.php`, `pro1_protprocesso002.php`, `pro1_protprocesso003.php`, `pro2_relconspro002.php`, `pro3_consultaobra002_habite.php`, `pro4_capaprocesso.php`, `pro4_termorecebimento2.php`, `rec2_espelhopontotela002.php`, `rec2_previsaodedireitos002.php`, `rec4_autorizacaohelote.php`, `rec4_exclusao_lote_assentamento.php`, `soc2_listapresenca002.php`, `soc3_consultacidadao003.php`, `soc3_consultafamilia003.php`

  </details>
- resposta vazia nos dois lados: **14**
  <details><summary>lista</summary>

  `pro1_camposdinamicosandamentopadrao.RPC.php`, `pro4_obrashabiteRPC.php`, `rec1_assentadb_cadattdinamicovalorgrupo001.php`, `rec1_assentadb_cadattdinamicovalorgrupo002.php`, `rec1_assentadb_cadattdinamicovalorgrupo003.php`, `rec1_portariasRPC.php`, `rec1_tipoassedb_cadattdinamico001.php`, `rec1_tipoassedb_cadattdinamico002.php`, `rec1_tipoassedb_cadattdinamico003.php`, `rec2_gradeefetividade003.php`, `rec2_rhestagio003.php`, `rec4_importararquivosporrelogioponto.php`, `rec4_pontoeletronico.RPC.php`, `rec4_rpcexame.php`

  </details>

### cidadao

IDENTICO 1412 | DIVERGE 22 | INCONCLUSIVO 203 | ERRO_AMBIENTE 1

**DIVERGE (22)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:con2_lrflimites002_2015.php` | A6 | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `tela:con2_lrfanexoxvii002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrflimites002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2018.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2012.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo17_002_2011.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_i_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_ii_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_balancoorcamentario_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfbalorc002_2015.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfdemalienataplicrecursos002_2010.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `relatorio:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo11_002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con4_docpadrao010.php` | - | - | ref=200/125613B  85=200/125612B |

**ERRO_AMBIENTE (1)**

- `tela:con4_gerenciadortarefas002.php` - timeout: ref=000  85=500 (apos 1 retentativa)

**INCONCLUSIVO (203)**

- pagina de erro identica nos dois lados (tela nao exercitada): **159**
  <details><summary>lista</summary>

  `con1_autenticaUsuarioMobile.RPC.php`, `con1_codclass001.php`, `con1_codclass002.php`, `con1_codclass003.php`, `con1_codhist001.php`, `con1_codhist002.php`, `con1_codhist003.php`, `con1_codsistema001.php`, `con1_codsistema002.php`, `con1_codsistema003.php`, `con1_conplanorec001.php`, `con1_conplanorec002.php`, `con1_conplanorec003.php`, `con1_db_ordem003.php`, `con1_db_permemp002.php`, `con1_db_permemp003.php`, `con1_db_syscampo001.php`, `con1_db_syscampo002.php`, `con1_db_syscampo003.php`, `con1_db_tarefas001.php`, `con1_db_tarefas003.php`, `con1_db_tarefasit004.php`, `con1_tarefasit001.php`, `con1_tarefasit002.php`, `con1_tarefasit003.php`, `con2_anexo12_002.php`, `con2_anexo12_002_2008.php`, `con2_anexo12rpps_002_2008.php`, `con2_anexo13_002.php`, `con2_anexo13rpps_002.php`, `con2_anexo14_002.php`, `con2_anexo14_002_2011.php`, `con2_anexo14rpps_002.php`, `con2_anexo14rpps_002_2008.php`, `con2_anexo15ee_002.php`, `con2_anexo15lrf_002.php`, `con2_anexo15lrf_002_2011.php`, `con2_anexo17_002.php`, `con2_anexoXIII_002_2011.php`, `con2_anexoXVI_002_2011.php`, `con2_balancdespsint002.php`, `con2_balancetemsc002.php`, `con2_balanceteverificacaocontacorrente002.php`, `con2_balancofinanceiro_2014.php`, `con2_balancopatrimonial_2014.php`, `con2_balancrece002_2008.php`, `con2_balancverificacao002.php`, `con2_confdesppessoal002.php`, `con2_despesacomeducacao003.php`, `con2_despesacomsaude003.php`, `con2_estruturarel.php`, `con2_fluxodecaixa_2014.php`, `con2_imprimeseqelemento002.php`, `con2_indice_educ002.php`, `con2_lfrorcanexoii002_2008.php`, `con2_lfrorcanexoii002_2010.php`, `con2_lrfbalorc002_2008.php`, `con2_lrfbalorc002_2010.php`, `con2_lrfbalorc002_2012.php`, `con2_lrfdemdisponibcaixa002_2010.php`, `con2_lrfdemonstrativorp002_2008.php`, `con2_lrfdesppessoal002.php`, `con2_lrfdesppessoal002_2007.php`, `con2_lrfdesppessoal002_2008.php`, `con2_lrfdesppessoal002_2009.php`, `con2_lrfdesppessoal002_2010.php`, `con2_lrfdesppessoal002_2011.php`, `con2_lrfdesppessoal002_2015.php`, `con2_lrfdispcaixa002.php`, `con2_lrfdivida002.php`, `con2_lrfdivida002_2008.php`, `con2_lrfdivida002_2009.php`, `con2_lrfgarantias002.php`, `con2_lrfgarantias002_2008.php`, `con2_lrfgarantias002_2009.php`, `con2_lrfimpostossaude002.php`, `con2_lrfimpostossaude002_2009.php`, `con2_lrfimpostossaude002_2013.php`, `con2_lrflimites002.php`, `con2_lrflimites002_2008.php`, `con2_lrflimites002_2009.php`, `con2_lrfmdefundeb0001.php`, `con2_lrfmdefundeb001.php`, `con2_lrfnominal002.php`, `con2_lrfnominal002_2009.php`, `con2_lrfprimario002.php`, `con2_lrfprimario002_2008.php`, `con2_lrfprimario002_2010.php`, `con2_lrfprimario002_2015.php`, `con2_lrfrecdesprpps002_2009.php`, `con2_lrfreceitacorrente002.php`, `con2_lrfreceitacorrente002_2008.php`, `con2_lrfreceitacorrente002_2009.php`, `con2_lrfreceitacorrente002_var.php`, `con2_lrfresumido002.php`, `con2_lrfresumido002_2007.php`, `con2_lrfresumido002_2008.php`, `con2_lrfresumido002_2009.php`, `con2_lrfresumido002_2015.php`, `con2_lrfresumido002_2018.php`, `con2_lrfrgfdemrestosapagar002_2010.php`, `con2_opercredito002.php`, `con2_opercredito002_2008.php`, `con2_opercredito002_2009.php`, `con2_razaocontas002.php`, `con2_razaoporcontas003.php`, `con2_rec_desp_extra_002.php`, `con2_relatoriosiconfi011.php`, `con2_reledital004.php`, `con2_variacoespatrimoniais_2014.php`, `con2_varpatrimoniaisrpps_002_2008.php`, `con3_conscontri008.php`, `con3_db_syscampo004.php`, `con4_boletim004.php`, `con4_consacordos003.php`, `con4_parametrosrelatorioslegais001.php`, `con4_processaaberturaexercicio.RPC.php`, `con4_registrasistema.php`, `con4_trabalhos001.php`, `con4_viradadeano002_item001.php`, `con4_viradadeano002_item002.php`, `con4_viradadeano002_item003.php`, `con4_viradadeano002_item004.php`, `con4_viradadeano002_item005.php`, `con4_viradadeano002_item006.php`, `con4_viradadeano002_item007.php`, `con4_viradadeano002_item008.php`, `con4_viradadeano002_item009.php`, `con4_viradadeano002_item010.php`, `con4_viradadeano002_item011.php`, `con4_viradadeano002_item012.php`, `con4_viradadeano002_item013.php`, `con4_viradadeano002_item014.php`, `con4_viradadeano002_item015.php`, `con4_viradadeano002_item016.php`, `con4_viradadeano002_item017.php`, `con4_viradadeano002_item018.php`, `con4_viradadeano002_item019.php`, `con4_viradadeano002_item020.php`, `con4_viradadeano002_item021.php`, `con4_viradadeano002_item022.php`, `con4_viradadeano002_item023.php`, `con4_viradadeano002_item024.php`, `con4_viradadeano002_item025.php`, `con4_viradadeano002_item026.php`, `con4_viradadeano002_item027.php`, `con4_viradadeano002_item028.php`, `con4_viradadeano002_item029.php`, `con4_viradadeano002_item030.php`, `con4_viradadeano002_item031.php`, `con4_viradadeano002_item032.php`, `con4_viradadeano002_item033.php`, `con4_viradadeano002_item034.php`, `con4_viradadeano002_item035.php`, `con4_viradadeano002_item036.php`, `con6_andamentolista.php`, `con6_ordemagendamento002.php`, `con6_ordemandamento002.php`, `con7_ordemandamento002.php`

  </details>
- resposta vazia nos dois lados: **44**
  <details><summary>lista</summary>

  `con1_congrupo004.php`, `con1_conplanogrupoconta004.php`, `con2_anexodemonstrativofuncaosubfuncao002.php`, `con2_planosys002.php`, `con3_versao005.php`, `con4_db_departRPC.php`, `con4_endereco.RPC.php`, `con4_geratcearqRPC.php`, `con4_importadoc001.php`, `con4_importadocpadrao001.php`, `con4_inscreverp002.php`, `con4_mensagems.RPC.php`, `con4_padbal_desp.php`, `con4_padbal_rec.php`, `con4_padbal_ver.php`, `con4_padbrec_ant.php`, `con4_padbrub_ant.php`, `con4_padbver_ant.php`, `con4_padbver_enc.php`, `con4_padbvmovant.php`, `con4_padconverterubrica.php`, `con4_padcredor.php`, `con4_padcta_disp.php`, `con4_padcta_oper.php`, `con4_paddecreto.php`, `con4_padempenho.php`, `con4_padfuncao.php`, `con4_padliquidac.php`, `con4_padorgao.php`, `con4_padpagament.php`, `con4_padprograma.php`, `con4_padprojativ.php`, `con4_padrd_extra.php`, `con4_padrec_ant.php`, `con4_padreceita.php`, `con4_padrecurso.php`, `con4_padrubrica.php`, `con4_padsubfunc.php`, `con4_padsubprog.php`, `con4_padtcelivrodiariogeral.php`, `con4_paduniorcam.php`, `con4_processaconsistencia.php`, `con4_processapad.php`, `pre4_email.php`

  </details>

### educacao

IDENTICO 2018 | DIVERGE 0 | INCONCLUSIVO 173 | ERRO_AMBIENTE 8

**ERRO_AMBIENTE (8)**

- `tela:edu4_atualizacadastrocenso002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_atualizacadastrocenso_2009_002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_exportarsituacaoaluno002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importacaoatualizacaoaluno002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importarcodigoinep002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importarcodigoinep_2009_002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importarmatriculainep002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_verifexportcenso002.php` - timeout: ref=000  85=200 (apos 1 retentativa)

**INCONCLUSIVO (173)**

- pagina de erro identica nos dois lados (tela nao exercitada): **122**
  <details><summary>lista</summary>

  `bib1_exemplar002.php`, `bib1_exemplar003.php`, `bib3_assunto002.php`, `bib3_leitorcons002.php`, `edu1_aprovconselho002.php`, `edu1_atividaderh002.php`, `edu1_atividaderh003.php`, `edu1_atoescola002.php`, `edu1_atoescola003.php`, `edu1_avalcompoeres002.php`, `edu1_avalcompoeres003.php`, `edu1_calendarioescola002.php`, `edu1_calendarioescola003.php`, `edu1_dialetivo002.php`, `edu1_dialetivo003.php`, `edu1_diarioavaliacao001.php`, `edu1_diarioavaliacaoobs001.php`, `edu1_diariofinal001.php`, `edu1_diariofinalcalcfreq001.php`, `edu1_disciplina002.php`, `edu1_disciplina003.php`, `edu1_docaluno002.php`, `edu1_docaluno003.php`, `edu1_encerraraval001.php`, `edu1_escolabase002.php`, `edu1_escolabase003.php`, `edu1_feriado001.php`, `edu1_feriado002.php`, `edu1_feriado003.php`, `edu1_grauensino001.php`, `edu1_grauensino002.php`, `edu1_grauensino003.php`, `edu1_matriculadependecia002.php`, `edu1_matriculadependecia003.php`, `edu1_parametrodependencia002.php`, `edu1_parametrodependencia003.php`, `edu1_pareceraval003.php`, `edu1_parecerresult002.php`, `edu1_parecerresult003.php`, `edu1_parecerturma003.php`, `edu1_periodocalendario002.php`, `edu1_periodocalendario003.php`, `edu1_procescola002.php`, `edu1_procescola003.php`, `edu1_rechumanoescola002.php`, `edu1_rechumanoescola003.php`, `edu1_rechumanohoradisp003.php`, `edu1_regencia003.php`, `edu1_regenciahorario001.php`, `edu1_serieequiv002.php`, `edu1_serieequiv003.php`, `edu1_telefoneescola002.php`, `edu1_telefoneescola003.php`, `edu1_transfescolafora002.php`, `edu1_transfescolarede002.php`, `edu1_turno002.php`, `edu1_turno003.php`, `edu2_atamatricula002.php`, `edu2_ataresultadofinal002.php`, `edu2_ataresultadofinal003.php`, `edu2_atestadofrequencia002.php`, `edu2_avaliacoesperiodo003.php`, `edu2_avaliacoesperiodo004.php`, `edu2_boletim003.php`, `edu2_calendario002.php`, `edu2_declaracaoanosatuais002.php`, `edu2_declaracaoexalunos002.php`, `edu2_declaracaomatricula002.php`, `edu2_diarioclasseconteudodesenvolvido002.php`, `edu2_diarioclasseconteudodesenvolvido002_2019.php`, `edu2_diarioclassenovo002.php`, `edu2_diarioclasseprogressaoparcial002.php`, `edu2_encaminhamentotransferencia002.php`, `edu2_fichaacompanhamento002.php`, `edu2_fichaqualitativa002.php`, `edu2_mapadefrequencia002.php`, `edu2_pardescritivonota002.php`, `edu2_pardescritivonota003.php`, `edu2_registroclasse002.php`, `edu2_relacaonominal002.php`, `edu2_resumoaprovnovo002.php`, `edu3_consultaaluno002.php`, `edu3_consultafuncaoexercida003.php`, `edu3_professorescola003.php`, `edu4_atestadovagafora002.php`, `edu4_notasparciais002.php`, `edu4_notasparciais003.php`, `edu4_notasparciais004.php`, `mat1_matestoque_arq.php`, `mat1_matestoque_arqnota.php`, `mat1_matestoqueitemlancconf_iframe.php`, `mat2_inventariofisicocontabil002.php`, `mat4_processararquivopit002.php`, `mat_aviso_deposito.php`, `mer1_mer_baixamanual001.php`, `mer1_mer_cardapiodia002.php`, `mer1_mer_cardapiodia003.php`, `mer1_mer_cardapionutri002.php`, `mer1_mer_cardapionutri003.php`, `mer1_mer_cardapiorelat.php`, `mer1_mer_cardapioturma002.php`, `mer1_mer_cardapioturma003.php`, `mer1_mer_desper_und003.php`, `mer1_mer_relathistcardapios002.php`, `pro1_cgmdoc002.php`, `pro1_cgmdoc003.php`, `pro1_obras004.php`, `pro1_obrasconstr002.php`, `pro1_obrasconstr003.php`, `pro1_procandamint001.php`, `pro1_procandamint002.php`, `pro1_procandamint003.php`, `pro1_protparamglobal001.php`, `pro1_protparamglobal003.php`, `pro1_protprocesso001.php`, `pro1_protprocesso002.php`, `pro1_protprocesso003.php`, `pro2_relconspro002.php`, `pro3_consultaobra002_habite.php`, `pro4_capaprocesso.php`, `pro4_termorecebimento2.php`, `sec2_escolasativas002.php`

  </details>
- resposta vazia nos dois lados: **50**
  <details><summary>lista</summary>

  `edu1_aluno.RPC.php`, `edu1_aluno004.php`, `edu1_baseRPC.php`, `edu1_baseatoRPC.php`, `edu1_calendario004.php`, `edu1_cursoatoRPC.php`, `edu1_efetividaderhRPC.php`, `edu1_escola004.php`, `edu1_escolaproc004.php`, `edu1_matricula007.php`, `edu1_ordenacaoniveisensinoRPC.php`, `edu1_periodocalendario004.php`, `edu1_procedimento004.php`, `edu1_rechumano004.php`, `edu1_rechumanoRPC.php`, `edu1_rechumanohoradisp002.php`, `edu1_rechumanohorario002.php`, `edu1_regencia002.php`, `edu1_relacaotrabalhoRPC.php`, `edu1_serieordenacaoRPC.php`, `edu1_turma004.php`, `edu1_turmaRPC.php`, `edu1_turmaac004.php`, `edu2_gfcoaprovalugeral002.php`, `edu2_gfcoaprovaluno002.php`, `edu2_gfcoaprovturgeral002.php`, `edu2_gfcoaprovturma002.php`, `edu2_gfcoescfreqseries002.php`, `edu2_gfcofreqaluno002.php`, `edu2_gfcofreqturma002.php`, `edu2_necessidadeEspecial.RPC.php`, `edu3_diarioclasse002.php`, `edu3_rechumanohorario002.php`, `mat1_lancaitens.php`, `mat4_atendsolicitacaoRPC.php`, `mat4_matordemRPC.php`, `mat4_requisicaoRPC.php`, `mer1_mer_cardapio004.php`, `mer1_mer_tipocardapio004.php`, `mer2_mer_refalunoRPC.php`, `mer2_mer_relathorarioRPC.php`, `mer2_quadrodesenvolvimentoRPC.php`, `mer4_mer_baixamanualRPC.php`, `mer4_mer_cardapioalunoRPC.php`, `mer4_mer_cardapiodiaRPC.php`, `mer4_mer_cardapioturma.RPC.php`, `mer4_mer_infalunoRPC.php`, `mer4_mer_subitem_ajax004.php`, `pro1_camposdinamicosandamentopadrao.RPC.php`, `pro4_obrashabiteRPC.php`

  </details>
- pulada (destroi a sessao do harness): **1**
  <details><summary>lista</summary>

  `edu4_informacoesdump.php`

  </details>

### saude

IDENTICO 1476 | DIVERGE 34 | INCONCLUSIVO 80 | ERRO_AMBIENTE 0

**DIVERGE (34)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:lab2_producao002.php` | A1 | `lab2_producao002.php:94` | TypeError: implode(): If argument #1 ($x) is of type string, argument #2 ($x) must be of type array, null give |
| `tela:sau2_bpa001.php` | A3 | `sau2_bpa001.php:42` | ValueError: Path must not be empty |
| `tela:lab2_mapacoletaconsulta.php` | A6 | `lab2_mapacoletaconsulta.php:22` | TypeError: mktime(): Argument #5 ($x) must be of type ?int, string given |
| `tela:sau1_valores001.php` | A6 | `libs/db_stdlib.php:112` | TypeError: pg_query(): Argument #1 ($x) must be of type PgSql\Connection, null given |
| `tela:lab1_lab_laboratorio002.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - // + js_tipo(0); |
| `tela:lab1_lab_laboratorio003.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - // + js_tipo(0); |
| `tela:sau1_cgs_undoutros002.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - new Array( // -new Array("", ''), |
| `tela:far2_distribuicao002.php` | R1 | `far2_distribuicao002.php:282` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:far2_historicopaciente002.php` | R1 | `far2_historicopaciente002.php:140` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:far2_historicoprogmedicamento002.php` | R1 | `far2_historicoprogmedicamento002.php:135` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:far2_historicoprogpaciente002.php` | R1 | `far2_historicoprogpaciente002.php:136` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:far2_mapaconsolidado003.php` | R1 | `far2_mapaconsolidado003.php:58` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:far2_pacienteprogramatica002.php` | R1 | `far2_pacienteprogramatica002.php:120` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_agendaexterna003.php` | R1 | `sau2_agendaexterna003.php:72` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_atendimentos002.php` | R1 | `sau2_atendimentos002.php:76` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_boletim002.php` | R1 | `sau2_boletim002.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_cgscorretos002.php` | R1 | `sau2_cgscorretos002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_especialidades002.php` | R1 | `sau2_especialidades002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_faausuarios002.php` | R1 | `sau2_faausuarios002.php:99` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_grafsaude002.php` | R1 | `sau2_grafsaude002.php:68` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_indicemorb002.php` | R1 | `sau2_indicemorb002.php:80` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_procedimentos002.php` | R1 | `sau2_procedimentos002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_procedimentos003.php` | R1 | `sau2_procedimentos003.php:61` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_procmedicos002.php` | R1 | `sau2_procmedicos002.php:65` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_progmun002.php` | R1 | `sau2_progmun002.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_prontuarios002.php` | R1 | `sau2_prontuarios002.php:53` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_relatorioprocedimentos002.php` | R1 | `sau2_relatorioprocedimentos002.php:163` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_sitagendamentos002.php` | R1 | `sau2_sitagendamentos002.php:52` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau2_unidades002.php` | R1 | `sau2_unidades002.php:117` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau3_consultasaude003.php` | R1 | `sau3_consultasaude003.php:52` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau4_consultamedica004.php` | R1 | `sau4_consultamedica004.php:55` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau4_prontuariomedico002.php` | R1 | `sau4_prontuariomedico002.php:48` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sau4_triagemproc001.php` | R1 | `sau4_triagemproc001.php:90` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:lab2_inconsistenciasimportacaoresultado002.php` | R2 | `src/Saude/Laboratorio/Repository/ImportacaoRequisicaoInconsistenciaRepository.php:117` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

**INCONCLUSIVO (80)**

- pagina de erro identica nos dois lados (tela nao exercitada): **59**
  <details><summary>lista</summary>

  `far1_far_devolucaomed002.php`, `far1_far_devolucaomed003.php`, `far1_far_parametros002.php`, `far1_far_parametros003.php`, `far1_far_retirada002.php`, `far1_far_retirada003.php`, `far2_conflitosintegracaohorus002.php`, `fum1_associadovalorservico001.php`, `fum1_associadovalorservico002.php`, `fum1_associadovalorservico003.php`, `fum4_associadoservicos006.php`, `lab1_lab_paralizacao002.php`, `lab1_lab_paralizacao003.php`, `lab1_lab_requisicao001.php`, `lab1_lab_requisicao002.php`, `lab1_lab_requisicao003.php`, `lab4_bpamagnetico.php`, `lab4_coletamostra001.php`, `lab4_digitacaoexa001.php`, `lab4_resultadomodelo1.php`, `lab4_resultadomodelo3.php`, `mat1_matestoque_arq.php`, `mat1_matestoque_arqnota.php`, `mat1_matestoqueitemlancconf_iframe.php`, `mat2_inventariofisicocontabil002.php`, `mat4_processararquivopit002.php`, `mat_aviso_deposito.php`, `prot1_cadastrocgm.php`, `prot1_cadastrocgmtest.php`, `prot1_pfisica.php`, `prot1_pjuridica.php`, `prot3_consultacgmnovo003.php`, `prot3_consultacgmnovo004.php`, `prot3_consultacgmnovo006.php`, `prot3_consultacgmnovo007.php`, `sau1_ausencias001.php`, `sau1_ausencias003.php`, `sau1_cgs003.php`, `sau1_fechamento001.php`, `sau1_medicos005.php`, `sau1_medicos006.php`, `sau1_sau_lote002.php`, `sau1_unidademedicos002.php`, `sau1_unidademedicos003.php`, `sau2_ag_exames002.php`, `sau2_agendamedica002.php`, `sau2_agendamento005.php`, `sau2_emitirfaa005.php`, `sau2_emitirfaa006.php`, `sau4_consultamedica002.php`, `sau4_prontuariomedico.php`, `tfd2_relatoriodeviagens002.php`, `tfd2_saidas002.php`, `tfd3_pedidoandamento003.php`, `tfd4_tfd_pedidotfd003.php`, `vac1_vac_dependencia002.php`, `vac1_vac_dependencia003.php`, `vac1_vac_vacinadoserestricao002.php`, `vac1_vac_vacinadoserestricao003.php`

  </details>
- resposta vazia nos dois lados: **21**
  <details><summary>lista</summary>

  `far1_far_devolucaomed001_func.php`, `far1_valida001.php`, `far2_medicamentosatend002.php`, `lab4_bpamagnetico002.php`, `lab4_emissaoresultadoloteimpressao.php`, `lab4_emissaoresultnovo002.php`, `mat1_lancaitens.php`, `mat4_atendsolicitacaoRPC.php`, `mat4_matordemRPC.php`, `mat4_requisicaoRPC.php`, `prot1_cadgeralmunic.RPC.php`, `prot1_comparanomes.php`, `prot4_tipo_processo.RPC.php`, `sau2_agendadores001.php`, `sau4_atualizacao002.php`, `sau4_fichaatendabas004_2.php`, `sau4_importsus002.php`, `sau4_procsftriagem001.php`, `tfd1_passagensdestino.RPC.php`, `vac1_vac_campanha002.php`, `vac1_vac_campanha007.php`

  </details>

### recursoshumanos

IDENTICO 3721 | DIVERGE 30 | INCONCLUSIVO 331 | ERRO_AMBIENTE 2

**DIVERGE (30)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:pes4_geraarquivosmanadnovo.php` | A1 | `model/manad.model.php:129` | TypeError: implode(): If argument #1 ($x) is of type string, argument #2 ($x) must be of type array, null give |
| `tela:pes4_geracaoarquivorefeisul.RPC.php` | A5 | `` | E_ERROR - Uncaught exception 'ParseError' with message 'syntax error, unexpected token "{", expecting ")"' in  |
| `tela:con2_lrflimites002_2015.php` | A6 | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `tela:pes2_feriasaviso002.php` | A6 | `pes2_feriasaviso002.php:112` | ValueError: cal_days_in_month(): Argument #2 ($x) must be between 1 and 2147483646 |
| `tela:cai4_relinconsextrato002.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -zhzÒ/PN%)ó*ùð.? // -þv-- |
| `tela:lic1_trocpcorcamtroca001.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -<script> Sfdump = window.Sfdump // (function (doc) { var refSty |
| `tela:pes4_geraarquivosmanad.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - </script><script>js_termo_termometro(0,'Processando Tabela : 0 |
| `tela:pes2_osocontramatricial002.php` | E1 | `` | resposta 200 nos dois lados, conteudo difere: -$HTTP_USER_AGENT = 'curl/7.81.0';<br> // +$HTTP_USER_AGENT = 'c |
| `tela:con2_lrfanexoxvii002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrflimites002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2018.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2012.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo17_002_2011.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_i_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_ii_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_balancoorcamentario_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfbalorc002_2015.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfdemalienataplicrecursos002_2010.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:pes2_rubmesponto002.php` | R1 | `pes2_rubmesponto002.php:214` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cai3_gerfinanc003.php` | R2 | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo11_002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |

**ERRO_AMBIENTE (2)**

- `tela:con4_gerenciadortarefas002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:rec2_espelhoponto002.php` - timeout: ref=000  85=500 (apos 1 retentativa)

**INCONCLUSIVO (331)**

- pagina de erro identica nos dois lados (tela nao exercitada): **246**
  <details><summary>lista</summary>

  `cai1_autenticadora005.php`, `cai1_cadtipoparc006.php`, `cai1_caitransfseq003.php`, `cai1_extratolinha001.php`, `cai1_extratolinha002.php`, `cai1_extratolinha003.php`, `cai1_historico001.php`, `cai1_tabrec003.php`, `cai2_correceitas002.php`, `cai2_digitasaldoextratomanual.php`, `cai2_digitasaldoextratomanuallinha.php`, `cai2_guiaspagasgrm002.php`, `cai2_movimento_extra_financeiro002.php`, `cai2_receisub002.php`, `cai2_relcaixa_002.php`, `cai2_reldescontos002.php`, `cai2_saltes003.php`, `cai3_gerfinanc001.php`, `cai3_gerfinanc002.php`, `cai3_gerfinanc075.php`, `cai3_integracaotjemissao001.php`, `cai3_reemiterecibo.php`, `cai4_abreconciliacao_processa.php`, `cai4_atividadesgrm.RPC.php`, `cai4_baixabanco001_agencia_88888.php`, `cai4_baixabanco001_codcli_19985.php`, `cai4_baixabanco_daeb.php`, `cai4_cancdebitosproc001.php`, `cai4_desmembramentodisbanco001.php`, `cai4_devolucaoadiantamento002.php`, `cai4_relatorioconciliacao_manual.php`, `cai4_relatorioconciliacaomanual002_layout2.php`, `cai4_remissbob003.php`, `con1_autenticaUsuarioMobile.RPC.php`, `con1_codclass001.php`, `con1_codclass002.php`, `con1_codclass003.php`, `con1_codhist001.php`, `con1_codhist002.php`, `con1_codhist003.php`, `con1_codsistema001.php`, `con1_codsistema002.php`, `con1_codsistema003.php`, `con1_conplanorec001.php`, `con1_conplanorec002.php`, `con1_conplanorec003.php`, `con1_db_ordem003.php`, `con1_db_permemp002.php`, `con1_db_permemp003.php`, `con1_db_syscampo001.php`, `con1_db_syscampo002.php`, `con1_db_syscampo003.php`, `con1_db_tarefas001.php`, `con1_db_tarefas003.php`, `con1_db_tarefasit004.php`, `con1_tarefasit001.php`, `con1_tarefasit002.php`, `con1_tarefasit003.php`, `con2_anexo12_002.php`, `con2_anexo12_002_2008.php`, `con2_anexo12rpps_002_2008.php`, `con2_anexo13_002.php`, `con2_anexo13rpps_002.php`, `con2_anexo14_002.php`, `con2_anexo14_002_2011.php`, `con2_anexo14rpps_002.php`, `con2_anexo14rpps_002_2008.php`, `con2_anexo15ee_002.php`, `con2_anexo15lrf_002.php`, `con2_anexo15lrf_002_2011.php`, `con2_anexo17_002.php`, `con2_anexoXIII_002_2011.php`, `con2_anexoXVI_002_2011.php`, `con2_balancdespsint002.php`, `con2_balancetemsc002.php`, `con2_balanceteverificacaocontacorrente002.php`, `con2_balancofinanceiro_2014.php`, `con2_balancopatrimonial_2014.php`, `con2_balancrece002_2008.php`, `con2_balancverificacao002.php`, `con2_confdesppessoal002.php`, `con2_despesacomeducacao003.php`, `con2_despesacomsaude003.php`, `con2_estruturarel.php`, `con2_fluxodecaixa_2014.php`, `con2_imprimeseqelemento002.php`, `con2_indice_educ002.php`, `con2_lfrorcanexoii002_2008.php`, `con2_lfrorcanexoii002_2010.php`, `con2_lrfbalorc002_2008.php`, `con2_lrfbalorc002_2010.php`, `con2_lrfbalorc002_2012.php`, `con2_lrfdemdisponibcaixa002_2010.php`, `con2_lrfdemonstrativorp002_2008.php`, `con2_lrfdesppessoal002.php`, `con2_lrfdesppessoal002_2007.php`, `con2_lrfdesppessoal002_2008.php`, `con2_lrfdesppessoal002_2009.php`, `con2_lrfdesppessoal002_2010.php`, `con2_lrfdesppessoal002_2011.php`, `con2_lrfdesppessoal002_2015.php`, `con2_lrfdispcaixa002.php`, `con2_lrfdivida002.php`, `con2_lrfdivida002_2008.php`, `con2_lrfdivida002_2009.php`, `con2_lrfgarantias002.php`, `con2_lrfgarantias002_2008.php`, `con2_lrfgarantias002_2009.php`, `con2_lrfimpostossaude002.php`, `con2_lrfimpostossaude002_2009.php`, `con2_lrfimpostossaude002_2013.php`, `con2_lrflimites002.php`, `con2_lrflimites002_2008.php`, `con2_lrflimites002_2009.php`, `con2_lrfmdefundeb0001.php`, `con2_lrfmdefundeb001.php`, `con2_lrfnominal002.php`, `con2_lrfnominal002_2009.php`, `con2_lrfprimario002.php`, `con2_lrfprimario002_2008.php`, `con2_lrfprimario002_2010.php`, `con2_lrfprimario002_2015.php`, `con2_lrfrecdesprpps002_2009.php`, `con2_lrfreceitacorrente002.php`, `con2_lrfreceitacorrente002_2008.php`, `con2_lrfreceitacorrente002_2009.php`, `con2_lrfreceitacorrente002_var.php`, `con2_lrfresumido002.php`, `con2_lrfresumido002_2007.php`, `con2_lrfresumido002_2008.php`, `con2_lrfresumido002_2009.php`, `con2_lrfresumido002_2015.php`, `con2_lrfresumido002_2018.php`, `con2_lrfrgfdemrestosapagar002_2010.php`, `con2_opercredito002.php`, `con2_opercredito002_2008.php`, `con2_opercredito002_2009.php`, `con2_razaocontas002.php`, `con2_razaoporcontas003.php`, `con2_rec_desp_extra_002.php`, `con2_relatoriosiconfi011.php`, `con2_reledital004.php`, `con2_variacoespatrimoniais_2014.php`, `con2_varpatrimoniaisrpps_002_2008.php`, `con3_conscontri008.php`, `con3_db_syscampo004.php`, `con4_boletim004.php`, `con4_consacordos003.php`, `con4_parametrosrelatorioslegais001.php`, `con4_processaaberturaexercicio.RPC.php`, `con4_registrasistema.php`, `con4_trabalhos001.php`, `con4_viradadeano002_item001.php`, `con4_viradadeano002_item002.php`, `con4_viradadeano002_item003.php`, `con4_viradadeano002_item004.php`, `con4_viradadeano002_item005.php`, `con4_viradadeano002_item006.php`, `con4_viradadeano002_item007.php`, `con4_viradadeano002_item008.php`, `con4_viradadeano002_item009.php`, `con4_viradadeano002_item010.php`, `con4_viradadeano002_item011.php`, `con4_viradadeano002_item012.php`, `con4_viradadeano002_item013.php`, `con4_viradadeano002_item014.php`, `con4_viradadeano002_item015.php`, `con4_viradadeano002_item016.php`, `con4_viradadeano002_item017.php`, `con4_viradadeano002_item018.php`, `con4_viradadeano002_item019.php`, `con4_viradadeano002_item020.php`, `con4_viradadeano002_item021.php`, `con4_viradadeano002_item022.php`, `con4_viradadeano002_item023.php`, `con4_viradadeano002_item024.php`, `con4_viradadeano002_item025.php`, `con4_viradadeano002_item026.php`, `con4_viradadeano002_item027.php`, `con4_viradadeano002_item028.php`, `con4_viradadeano002_item029.php`, `con4_viradadeano002_item030.php`, `con4_viradadeano002_item031.php`, `con4_viradadeano002_item032.php`, `con4_viradadeano002_item033.php`, `con4_viradadeano002_item034.php`, `con4_viradadeano002_item035.php`, `con4_viradadeano002_item036.php`, `con6_andamentolista.php`, `con6_ordemagendamento002.php`, `con6_ordemandamento002.php`, `con7_ordemandamento002.php`, `eso02_preenchimentoesocial001.php`, `lic4_detalhecomissao001.php`, `lic4_geraautorizacaoprocessos.php`, `pes1_cfpess002.php`, `pes1_pensao001_acoes.php`, `pes1_reajusteprog001.php`, `pes1_reajustesal002.php`, `pes1_rhcadregime001.php`, `pes1_rhcadregime003.php`, `pes1_rhlotavincele002.php`, `pes1_rhlotavincele003.php`, `pes1_rhpagatra002.php`, `pes1_rhpagatra003.php`, `pes1_rhpeslocaltrab002.php`, `pes1_rhpessoalmov002.php`, `pes1_rhpessoalmov003.php`, `pes2_alecontramatricial002.php`, `pes2_arrcontramatricial002.php`, `pes2_carcontramatricial002.php`, `pes2_contramatricial002.php`, `pes2_emissao_csv002.php`, `pes2_emissao_pdf002.php`, `pes2_historicoconsignado002.php`, `pes2_itau240cnabgeracao002.php`, `pes2_layoutideal002.php`, `pes2_termorescisaomodimprime80.php`, `pes3_consponto021_complementar.php`, `pes3_consponto021_salario.php`, `pes3_consponto021_suplementar.php`, `pes3_faixasSalariais002CSV.php`, `pes3_gerfinanc018_salario.php`, `pes4_aberturacomplementar001.php`, `pes4_aberturasuplementar001.php`, `pes4_acertaempenhospcasp.RPC.php`, `pes4_assentamentorra001.php`, `pes4_assentamentosubstituicao001.php`, `pes4_cancelaaberturacomplementar001.php`, `pes4_cancelaaberturasuplementar001.php`, `pes4_cancelafechamentocomplementar001.php`, `pes4_cancelafechamentosalario001.php`, `pes4_cancelafechamentosuplementar001.php`, `pes4_fechamentocomplementar001.php`, `pes4_fechamentosuplementar001.php`, `pes4_implantacaoponto001.php`, `pes4_inicializavt002.php`, `pes4_ipe002.php`, `pes4_ipe003.php`, `pes4_lancamentoassentamento001.php`, `pes4_retornocontratosconsignadosmanual.php`, `pes4_rhfopag91002.php`, `rec2_espelhopontotela002.php`, `rec2_previsaodedireitos002.php`, `rec4_autorizacaohelote.php`, `rec4_exclusao_lote_assentamento.php`

  </details>
- resposta vazia nos dois lados: **85**
  <details><summary>lista</summary>

  `cai1_cairetordemvalida.php`, `cai1_pix002.php`, `cai4_cancelabaixabancoRPC.php`, `cai4_gerazim.php`, `cai4_importatipo001.php`, `cai4_placaixaRPC.php`, `cai4_processaconciliacao.php`, `cai4_processaconciliacao_manual.php`, `cai4_transferenciaNumpre.RPC.php`, `con1_congrupo004.php`, `con1_conplanogrupoconta004.php`, `con2_anexodemonstrativofuncaosubfuncao002.php`, `con2_planosys002.php`, `con3_versao005.php`, `con4_db_departRPC.php`, `con4_endereco.RPC.php`, `con4_geratcearqRPC.php`, `con4_importadoc001.php`, `con4_importadocpadrao001.php`, `con4_inscreverp002.php`, `con4_mensagems.RPC.php`, `con4_padbal_desp.php`, `con4_padbal_rec.php`, `con4_padbal_ver.php`, `con4_padbrec_ant.php`, `con4_padbrub_ant.php`, `con4_padbver_ant.php`, `con4_padbver_enc.php`, `con4_padbvmovant.php`, `con4_padconverterubrica.php`, `con4_padcredor.php`, `con4_padcta_disp.php`, `con4_padcta_oper.php`, `con4_paddecreto.php`, `con4_padempenho.php`, `con4_padfuncao.php`, `con4_padliquidac.php`, `con4_padorgao.php`, `con4_padpagament.php`, `con4_padprograma.php`, `con4_padprojativ.php`, `con4_padrd_extra.php`, `con4_padrec_ant.php`, `con4_padreceita.php`, `con4_padrecurso.php`, `con4_padrubrica.php`, `con4_padsubfunc.php`, `con4_padsubprog.php`, `con4_padtcelivrodiariogeral.php`, `con4_paduniorcam.php`, `con4_processaconsistencia.php`, `con4_processapad.php`, `pes1_rhpessoalpontoRPC.php`, `pes2_consrhfuncao002.php`, `pes2_emitebb200lay002.php`, `pes2_gerabbrasil001.php`, `pes2_guaemitebb200lay002.php`, `pes2_mppiemitearqbanco002.php`, `pes2_sapemitearqbanco002.php`, `pes2_sapemitebb200lay002.php`, `pes3_faixasSalariais002PDF.php`, `pes4_avalferia001.php`, `pes4_avaliaferiasrescisao.php`, `pes4_dadosGrupoRPC.php`, `pes4_emissaochequesRPC.php`, `pes4_geraarqmanadRPC.php`, `pes4_gerafolha003.php`, `pes4_gerafolha004.php`, `pes4_gerafolha004_calculopensao.php`, `pes4_jetomcomissaolancamento001.php`, `pes4_jetomcomissaoprocessamento001.php`, `pes4_manutencaocontratosconsignados.RPC.php`, `rec1_assentadb_cadattdinamicovalorgrupo001.php`, `rec1_assentadb_cadattdinamicovalorgrupo002.php`, `rec1_assentadb_cadattdinamicovalorgrupo003.php`, `rec1_portariasRPC.php`, `rec1_tipoassedb_cadattdinamico001.php`, `rec1_tipoassedb_cadattdinamico002.php`, `rec1_tipoassedb_cadattdinamico003.php`, `rec2_gradeefetividade003.php`, `rec2_rhestagio003.php`, `rec4_importararquivosporrelogioponto.php`, `rec4_pontoeletronico.RPC.php`, `rec4_rpcexame.php`, `rh4_recadastramento.RPC.php`

  </details>

### patrimonial

IDENTICO 5335 | DIVERGE 57 | INCONCLUSIVO 428 | ERRO_AMBIENTE 1

**DIVERGE (57)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:cad2_emissaobic_002.php` | A1 | `cad2_emissaobic_002.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad3_conscadastro_relatorio.php` | A1 | `cad3_conscadastro_relatorio.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad4_recadastramentorelatorio.php` | A1 | `cad4_recadastramentorelatorio.php:106` | TypeError: array_chunk(): Argument #1 ($x) must be of type array, null given |
| `tela:orc2_atividades002.php` | A2 | `fpdf151/fpdf.php:932` | TypeError: Unsupported operand types: int + string |
| `tela:con2_lrflimites002_2015.php` | A6 | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `tela:con4_docpadrao010.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -0*8°÷t}¯íu¨}Àé#Þ3=vËÀÉs¼ÕAosÉæ]ÿ +ÄT1 // +0*8°÷t}¯íu¨ |
| `tela:orc2_receitasDespesasPrevidenciariasServidores002.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -xËnÉ×ÑSYØ©Ü÷,h68D // - |
| `tela:con2_lrfanexoxvii002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrflimites002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2018.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2012.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo17_002_2011.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_i_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_ii_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_balancoorcamentario_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfbalorc002_2015.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfdemalienataplicrecursos002_2010.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `relatorio:cad2_loteam002.php` | R1 | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_carnesiptu002.php` | R1 | `cad2_carnesiptu002.php:57` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_comparaiptu002.php` | R1 | `cad2_comparaiptu002.php:154` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_compcaract002.php` | R1 | `cad2_compcaract002.php:124` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_descconced002.php` | R1 | `cad2_descconced002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_iptulancpago002.php` | R1 | `cad2_iptulancpago002.php:60` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_listaiptucalc_003.php` | R1 | `cad2_listaiptucalc_003.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteam002.php` | R1 | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteamentomatric002.php` | R1 | `cad2_loteamentomatric002.php:80` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteamentos002.php` | R1 | `cad2_loteamentos002.php:77` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_matricnaoproc002.php` | R1 | `cad2_matricnaoproc002.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_posicaoiptu002.php` | R1 | `cad2_posicaoiptu002.php:71` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relaverbacao002.php` | R1 | `cad2_relaverbacao002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_reldemo002.php` | R1 | `cad2_reldemo002.php:108` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relisentos002.php` | R1 | `cad2_relisentos002.php:46` | TypeError: pg_fetch_assoc(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relmassafalida002.php` | R1 | `cad2_relmassafalida002.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_setor002.php` | R1 | `cad2_setor002.php:79` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_conscadastrodetalhesmodelonovo002.php` | R1 | `cad3_conscadastrodetalhesmodelonovo002.php:171` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_iptupago002_original.php` | R1 | `cad3_iptupago002_original.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_relzonafiscal002.php` | R1 | `cad3_relzonafiscal002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_relzonafiscaltaxa002.php` | R1 | `cad3_relzonafiscaltaxa002.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt.php` | R1 | `cad4_geracarneiptutxt.php:754` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_arapiraca.php` | R1 | `cad4_geracarneiptutxt_arapiraca.php:170` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_eldorado.php` | R1 | `cad4_geracarneiptutxt_eldorado.php:167` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_guaiba.php` | R1 | `cad4_geracarneiptutxt_guaiba.php:169` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarnesiptu_geral.php` | R1 | `cad4_geracarnesiptu_geral.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:orc2_desppessoal002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cai3_gerfinanc003.php` | R2 | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo11_002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:orc2_desppessoal002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:lic1_trocpcorcamtroca001.php` | - | - | ref=200/21844B  85=200/21844B |

**ERRO_AMBIENTE (1)**

- `tela:con4_gerenciadortarefas002.php` - timeout: ref=000  85=500 (apos 1 retentativa)

**INCONCLUSIVO (428)**

- pagina de erro identica nos dois lados (tela nao exercitada): **340**
  <details><summary>lista</summary>

  `cad1_cadlote001.php`, `cad1_cadlote002.php`, `cad1_cadlote003.php`, `cad1_cadruas003.php`, `cad1_iptubaixa002.php`, `cad1_iptubasealt.php`, `cad1_reliptuender002.php`, `cad1_setor001.php`, `cad1_setor002.php`, `cad1_setor003.php`, `cad2_relatorios_002.php`, `cad2_relcaixa_002.php`, `cad3_consCadastroIptu.php`, `cad3_conscadastro_agua_002.php`, `cad3_conscadastro_iptu_002.php`, `cad3_conscertforlaud002.php`, `cad3_conscertlanc002.php`, `cad3_conscertvalven002.php`, `cad4_iptuconstr.RPC.php`, `cad4_recadastramentoconsultaiptu.php`, `cai1_autenticadora005.php`, `cai1_cadtipoparc006.php`, `cai1_caitransfseq003.php`, `cai1_extratolinha001.php`, `cai1_extratolinha002.php`, `cai1_extratolinha003.php`, `cai1_historico001.php`, `cai1_tabrec003.php`, `cai2_correceitas002.php`, `cai2_digitasaldoextratomanual.php`, `cai2_digitasaldoextratomanuallinha.php`, `cai2_guiaspagasgrm002.php`, `cai2_movimento_extra_financeiro002.php`, `cai2_receisub002.php`, `cai2_relcaixa_002.php`, `cai2_reldescontos002.php`, `cai2_saltes003.php`, `cai3_gerfinanc001.php`, `cai3_gerfinanc002.php`, `cai3_gerfinanc075.php`, `cai3_integracaotjemissao001.php`, `cai3_reemiterecibo.php`, `cai4_abreconciliacao_processa.php`, `cai4_atividadesgrm.RPC.php`, `cai4_baixabanco001_agencia_88888.php`, `cai4_baixabanco001_codcli_19985.php`, `cai4_baixabanco_daeb.php`, `cai4_cancdebitosproc001.php`, `cai4_desmembramentodisbanco001.php`, `cai4_devolucaoadiantamento002.php`, `cai4_relatorioconciliacao_manual.php`, `cai4_relatorioconciliacaomanual002_layout2.php`, `cai4_remissbob003.php`, `com1_itens001proc.php`, `com1_orcamlancval002.php`, `com1_orcamlancval003.php`, `com1_solicita004_altera.php`, `com1_solicitaregistropreco001.php`, `com1_solicitaregistropreco002.php`, `com1_solicitaregistropreco003.php`, `com1_solicitem002.php`, `com1_solicitem003.php`, `com2_relatorioatasvigentes002.php`, `com4_consabertregistro003.php`, `com4_inserirdotacaosolicitacao.RPC.php`, `con1_autenticaUsuarioMobile.RPC.php`, `con1_codclass001.php`, `con1_codclass002.php`, `con1_codclass003.php`, `con1_codhist001.php`, `con1_codhist002.php`, `con1_codhist003.php`, `con1_codsistema001.php`, `con1_codsistema002.php`, `con1_codsistema003.php`, `con1_conplanorec001.php`, `con1_conplanorec002.php`, `con1_conplanorec003.php`, `con1_db_ordem003.php`, `con1_db_permemp002.php`, `con1_db_permemp003.php`, `con1_db_syscampo001.php`, `con1_db_syscampo002.php`, `con1_db_syscampo003.php`, `con1_db_tarefas001.php`, `con1_db_tarefas003.php`, `con1_db_tarefasit004.php`, `con1_tarefasit001.php`, `con1_tarefasit002.php`, `con1_tarefasit003.php`, `con2_anexo12_002.php`, `con2_anexo12_002_2008.php`, `con2_anexo12rpps_002_2008.php`, `con2_anexo13_002.php`, `con2_anexo13rpps_002.php`, `con2_anexo14_002.php`, `con2_anexo14_002_2011.php`, `con2_anexo14rpps_002.php`, `con2_anexo14rpps_002_2008.php`, `con2_anexo15ee_002.php`, `con2_anexo15lrf_002.php`, `con2_anexo15lrf_002_2011.php`, `con2_anexo17_002.php`, `con2_anexoXIII_002_2011.php`, `con2_anexoXVI_002_2011.php`, `con2_balancdespsint002.php`, `con2_balancetemsc002.php`, `con2_balanceteverificacaocontacorrente002.php`, `con2_balancofinanceiro_2014.php`, `con2_balancopatrimonial_2014.php`, `con2_balancrece002_2008.php`, `con2_balancverificacao002.php`, `con2_confdesppessoal002.php`, `con2_despesacomeducacao003.php`, `con2_despesacomsaude003.php`, `con2_estruturarel.php`, `con2_fluxodecaixa_2014.php`, `con2_imprimeseqelemento002.php`, `con2_indice_educ002.php`, `con2_lfrorcanexoii002_2008.php`, `con2_lfrorcanexoii002_2010.php`, `con2_lrfbalorc002_2008.php`, `con2_lrfbalorc002_2010.php`, `con2_lrfbalorc002_2012.php`, `con2_lrfdemdisponibcaixa002_2010.php`, `con2_lrfdemonstrativorp002_2008.php`, `con2_lrfdesppessoal002.php`, `con2_lrfdesppessoal002_2007.php`, `con2_lrfdesppessoal002_2008.php`, `con2_lrfdesppessoal002_2009.php`, `con2_lrfdesppessoal002_2010.php`, `con2_lrfdesppessoal002_2011.php`, `con2_lrfdesppessoal002_2015.php`, `con2_lrfdispcaixa002.php`, `con2_lrfdivida002.php`, `con2_lrfdivida002_2008.php`, `con2_lrfdivida002_2009.php`, `con2_lrfgarantias002.php`, `con2_lrfgarantias002_2008.php`, `con2_lrfgarantias002_2009.php`, `con2_lrfimpostossaude002.php`, `con2_lrfimpostossaude002_2009.php`, `con2_lrfimpostossaude002_2013.php`, `con2_lrflimites002.php`, `con2_lrflimites002_2008.php`, `con2_lrflimites002_2009.php`, `con2_lrfmdefundeb0001.php`, `con2_lrfmdefundeb001.php`, `con2_lrfnominal002.php`, `con2_lrfnominal002_2009.php`, `con2_lrfprimario002.php`, `con2_lrfprimario002_2008.php`, `con2_lrfprimario002_2010.php`, `con2_lrfprimario002_2015.php`, `con2_lrfrecdesprpps002_2009.php`, `con2_lrfreceitacorrente002.php`, `con2_lrfreceitacorrente002_2008.php`, `con2_lrfreceitacorrente002_2009.php`, `con2_lrfreceitacorrente002_var.php`, `con2_lrfresumido002.php`, `con2_lrfresumido002_2007.php`, `con2_lrfresumido002_2008.php`, `con2_lrfresumido002_2009.php`, `con2_lrfresumido002_2015.php`, `con2_lrfresumido002_2018.php`, `con2_lrfrgfdemrestosapagar002_2010.php`, `con2_opercredito002.php`, `con2_opercredito002_2008.php`, `con2_opercredito002_2009.php`, `con2_razaocontas002.php`, `con2_razaoporcontas003.php`, `con2_rec_desp_extra_002.php`, `con2_relatoriosiconfi011.php`, `con2_reledital004.php`, `con2_variacoespatrimoniais_2014.php`, `con2_varpatrimoniaisrpps_002_2008.php`, `con3_conscontri008.php`, `con3_db_syscampo004.php`, `con4_boletim004.php`, `con4_consacordos003.php`, `con4_parametrosrelatorioslegais001.php`, `con4_processaaberturaexercicio.RPC.php`, `con4_registrasistema.php`, `con4_trabalhos001.php`, `con4_viradadeano002_item001.php`, `con4_viradadeano002_item002.php`, `con4_viradadeano002_item003.php`, `con4_viradadeano002_item004.php`, `con4_viradadeano002_item005.php`, `con4_viradadeano002_item006.php`, `con4_viradadeano002_item007.php`, `con4_viradadeano002_item008.php`, `con4_viradadeano002_item009.php`, `con4_viradadeano002_item010.php`, `con4_viradadeano002_item011.php`, `con4_viradadeano002_item012.php`, `con4_viradadeano002_item013.php`, `con4_viradadeano002_item014.php`, `con4_viradadeano002_item015.php`, `con4_viradadeano002_item016.php`, `con4_viradadeano002_item017.php`, `con4_viradadeano002_item018.php`, `con4_viradadeano002_item019.php`, `con4_viradadeano002_item020.php`, `con4_viradadeano002_item021.php`, `con4_viradadeano002_item022.php`, `con4_viradadeano002_item023.php`, `con4_viradadeano002_item024.php`, `con4_viradadeano002_item025.php`, `con4_viradadeano002_item026.php`, `con4_viradadeano002_item027.php`, `con4_viradadeano002_item028.php`, `con4_viradadeano002_item029.php`, `con4_viradadeano002_item030.php`, `con4_viradadeano002_item031.php`, `con4_viradadeano002_item032.php`, `con4_viradadeano002_item033.php`, `con4_viradadeano002_item034.php`, `con4_viradadeano002_item035.php`, `con4_viradadeano002_item036.php`, `con6_andamentolista.php`, `con6_ordemagendamento002.php`, `con6_ordemandamento002.php`, `con7_ordemandamento002.php`, `emp1_empageconf001.php`, `emp1_empageconf002.php`, `emp1_empageconf003.php`, `emp1_empautidot002.php`, `emp1_empautidot003.php`, `emp1_empautitem002.php`, `emp1_empautitem003.php`, `emp1_empautoriza003.php`, `emp1_empautret002.php`, `emp1_empautret003.php`, `emp1_empempenho003.php`, `emp1_empempitem002.php`, `emp1_empempitem003.php`, `emp1_empempret002.php`, `emp1_empempret003.php`, `emp1_empliquidaarq.php`, `emp1_emppagamento002.php`, `emp1_emppagamentoarq.php`, `emp1_emppagamentoestorna002.php`, `emp1_ordemcompra_liquida003.php`, `emp1_pagordemarq.php`, `emp2_empenhoclassificacaocredor002.php`, `emp2_empenhohistorico002.php`, `emp4_emppagamento002.php`, `emp4_liquidacao004.php`, `emp4_pagarempenho002.php`, `lic4_detalhecomissao001.php`, `lic4_geraautorizacaoprocessos.php`, `mat1_matestoque_arq.php`, `mat1_matestoque_arqnota.php`, `mat1_matestoqueitemlancconf_iframe.php`, `mat2_inventariofisicocontabil002.php`, `mat4_processararquivopit002.php`, `mat_aviso_deposito.php`, `orc1_orcparamrelopcre002.php`, `orc1_orcparamrelopcre003.php`, `orc1_orcppa006.php`, `orc1_orcsuplem005.php`, `orc1_tiporec001.php`, `orc1_tiporec002.php`, `orc1_tiporec003.php`, `orc2_DemRiscosFiscaisProvidencias.php`, `orc2_EstimativaRenunciaReceita002.php`, `orc2_MargemDespesasCaraterContinuado.php`, `orc2_ReceitasDespesasPrevidenciariasServidores.php`, `orc2_acompanhamentocronograma001.php`, `orc2_anexo8002.php`, `orc2_anexodividapublica002.php`, `orc2_anexodotacaogoverno002.php`, `orc2_anexoorcamentofiscal002.php`, `orc2_anexoreceitacorrenteliquida002.php`, `orc2_anexoseguridadesocial002.php`, `orc2_anexosumrecfontesdespfuncaogov002.php`, `orc2_anexotrabalhogoverno002.php`, `orc2_demManutencaoDesenvolvimentoEnsino002.php`, `orc2_demreceitasdespesassaude002.php`, `orc2_despsecretaria002.php`, `orc2_estimativaRenunciaReceita002.php`, `orc2_orcprevmensaldesp002.php`, `orc2_ppaevolucaodemostrativoreceita002.php`, `orc2_recppa002.php`, `orc2_recursorecdesp002.php`, `orc2_reldespesas002.php`, `orc2_reldespesas002txt.php`, `orc2_totaliza002.php`, `orc4_duplicaorcamento001.php`, `orc4_duplicaorcamentorec001.php`, `orc4_ppadotacaoelementos004.php`, `orc4_resumogeralprevreceita002.php`, `ouv1_detalhesdespacho003.php`, `pat1_bens006.php`, `pat1_bensconsulta002.php`, `pat2_histbem002.php`, `pat4_criteriumexportaarquivos002_bem.php`, `pat4_criteriumexportaarquivos002_ccusto.php`, `pat4_criteriumexportaarquivos002_empresa.php`, `pat4_criteriumexportaarquivos002_especie.php`, `pat4_criteriumexportaarquivos002_estado.php`, `pat4_criteriumexportaarquivos002_familia.php`, `pat4_criteriumexportaarquivos002_fornecedor.php`, `pat4_criteriumexportaarquivos002_historico.php`, `pat4_criteriumexportaarquivos002_localizacao.php`, `pat4_criteriumexportaarquivos002_marcas.php`, `pat4_criteriumexportaarquivos002_medida.php`, `pat4_criteriumexportaarquivos002_modelo.php`, `pat4_criteriumexportaarquivos002_ocorrencia.php`, `pat4_criteriumexportaarquivos002_parametros.php`, `pat4_criteriumexportaarquivos002_setor.php`, `pat4_criteriumexportaarquivos002_usuario.php`, `pro1_cgmdoc002.php`, `pro1_cgmdoc003.php`, `pro1_obras004.php`, `pro1_obrasconstr002.php`, `pro1_obrasconstr003.php`, `pro1_procandamint001.php`, `pro1_procandamint002.php`, `pro1_procandamint003.php`, `pro1_protparamglobal001.php`, `pro1_protparamglobal003.php`, `pro1_protprocesso001.php`, `pro1_protprocesso002.php`, `pro1_protprocesso003.php`, `pro2_relconspro002.php`, `pro3_consultaobra002_habite.php`, `pro4_capaprocesso.php`, `pro4_termorecebimento2.php`, `prot1_cadastrocgm.php`, `prot1_cadastrocgmtest.php`, `prot1_pfisica.php`, `prot1_pjuridica.php`, `prot3_consultacgmnovo003.php`, `prot3_consultacgmnovo004.php`, `prot3_consultacgmnovo006.php`, `prot3_consultacgmnovo007.php`, `vei1_veicabast003.php`, `vei1_veicmanutitem001.php`

  </details>
- resposta vazia nos dois lados: **87**
  <details><summary>lista</summary>

  `cad1_buscaexercicio.php`, `cad4_geracarneiptutxtParcelasOpcionais.php`, `cai1_cairetordemvalida.php`, `cai1_pix002.php`, `cai4_cancelabaixabancoRPC.php`, `cai4_gerazim.php`, `cai4_importatipo001.php`, `cai4_placaixaRPC.php`, `cai4_processaconciliacao.php`, `cai4_processaconciliacao_manual.php`, `cai4_transferenciaNumpre.RPC.php`, `con1_congrupo004.php`, `con1_conplanogrupoconta004.php`, `con2_anexodemonstrativofuncaosubfuncao002.php`, `con2_planosys002.php`, `con3_versao005.php`, `con4_db_departRPC.php`, `con4_endereco.RPC.php`, `con4_geratcearqRPC.php`, `con4_importadoc001.php`, `con4_importadocpadrao001.php`, `con4_inscreverp002.php`, `con4_mensagems.RPC.php`, `con4_padbal_desp.php`, `con4_padbal_rec.php`, `con4_padbal_ver.php`, `con4_padbrec_ant.php`, `con4_padbrub_ant.php`, `con4_padbver_ant.php`, `con4_padbver_enc.php`, `con4_padbvmovant.php`, `con4_padconverterubrica.php`, `con4_padcredor.php`, `con4_padcta_disp.php`, `con4_padcta_oper.php`, `con4_paddecreto.php`, `con4_padempenho.php`, `con4_padfuncao.php`, `con4_padliquidac.php`, `con4_padorgao.php`, `con4_padpagament.php`, `con4_padprograma.php`, `con4_padprojativ.php`, `con4_padrd_extra.php`, `con4_padrec_ant.php`, `con4_padreceita.php`, `con4_padrecurso.php`, `con4_padrubrica.php`, `con4_padsubfunc.php`, `con4_padsubprog.php`, `con4_padtcelivrodiariogeral.php`, `con4_paduniorcam.php`, `con4_processaconsistencia.php`, `con4_processapad.php`, `emp4_agendaPagamentoRPC.php`, `emp4_anularpagamentoRPC.php`, `emp4_gerarslipRPC.php`, `emp4_manutencaoPagamentoRPC.php`, `emp4_migracaoNotasRPC.php`, `emp4_ordemPagamentoRPC.php`, `emp4_pagarpagamentoRPC.php`, `emp4_retencaonotaRPC.php`, `mat1_lancaitens.php`, `mat4_atendsolicitacaoRPC.php`, `mat4_matordemRPC.php`, `mat4_requisicaoRPC.php`, `orc1_orcduplicareceita.php`, `orc2_anexo2_resudespesa002.php`, `orc2_orcldorec002.php`, `orc4_ppaRPC.php`, `ouv1_atendimento.RPC.php`, `ouv1_controleatendimento.RPC.php`, `ouv1_localouvidoria.RPC.php`, `ouv1_retornocliente.RPC.php`, `ouv4_solicitacaoprocessoeletronico.RPC.php`, `pat1_retseqplaca.php`, `pro1_camposdinamicosandamentopadrao.RPC.php`, `pro4_obrashabiteRPC.php`, `prot1_cadgeralmunic.RPC.php`, `prot1_comparanomes.php`, `prot4_tipo_processo.RPC.php`, `vei1_veiccadcentraldepart001.php`, `vei1_veiccentralmotoristas001.php`, `vei1_veiccentralveiculos001.php`, `vei1_veicitensobrig001.php`, `vei1_veicmotoristascentral001.php`, `vei1_veicutilizacao001.php`

  </details>
- pulada (destroi a sessao do harness): **1**
  <details><summary>lista</summary>

  `cad4_geracarneiptutxt_cli.php`

  </details>

### tributario

IDENTICO 5512 | DIVERGE 118 | INCONCLUSIVO 400 | ERRO_AMBIENTE 2

**DIVERGE (118)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:agu3_conscadastro_relatorio.php` | A1 | `agu3_conscadastro_relatorio.php:37` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad2_emissaobic_002.php` | A1 | `cad2_emissaobic_002.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad3_conscadastro_relatorio.php` | A1 | `cad3_conscadastro_relatorio.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad4_recadastramentorelatorio.php` | A1 | `cad4_recadastramentorelatorio.php:106` | TypeError: array_chunk(): Argument #1 ($x) must be of type array, null given |
| `tela:iss3_inconsistenciaSimples.php` | A1 | `iss3_inconsistenciaSimples.php:62` | TypeError: rsort(): Argument #1 ($x) must be of type array, null given |
| `tela:jur2_geradoc.php` | A1 | `jur2_geradoc.php:74` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:jur2_inicialquit002.php` | A1 | `jur2_inicialquit002.php:60` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:sys4_listaretornosql001.php` | A1 | `sys4_listaretornosql001.php:67` | TypeError: array_keys(): Argument #1 ($x) must be of type array, null given |
| `relatorio:div2_resumogeraldivida002.php` | A2 | `classes/db_divida_classe.php:2378` | TypeError: Unsupported operand types: string - int |
| `tela:div2_resumogeraldivida002.php` | A2 | `classes/db_divida_classe.php:2378` | TypeError: Unsupported operand types: string - int |
| `tela:iss2_relarrec1002.php` | A2 | `iss2_relarrec1002.php:53` | TypeError: Unsupported operand types: string + int |
| `tela:itbi_simulacaoitbi002.php` | A2 | `itbi_simulacaoitbi002.php:237` | TypeError: Unsupported operand types: string / int |
| `tela:sys4_consultaXML.RPC.php` | A3 | `sys4_consultaXML.RPC.php:39` | ValueError: Path must not be empty |
| `tela:sys4_processa004.php` | A3 | `sys4_processa004.php:111` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `tela:sys4_processa008.php` | A3 | `sys4_processa008.php:100` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `tela:fis1_fis_sanitario004.php` | A4 | `fis1_fis_sanitario004.php:67` | Error: Call to undefined function db_ancora() |
| `tela:fis1_sanitario004.php` | A4 | `fis1_sanitario004.php:67` | Error: Call to undefined function db_ancora() |
| `tela:agu1_aguaconsumo999.php` | A6 | `std/label/RotuloCampoDB.php:37` | Error: No PostgreSQL connection opened yet |
| `tela:agu4_cancelaleituras_classe.php` | A6 | `vendor/dbseller/legacy/src/PHP53/Emulate.php:110` | TypeError: array_key_exists(): Argument #2 ($x) must be of type array, null given |
| `tela:con2_lrflimites002_2015.php` | A6 | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `tela:fis1_fis_procfiscalfinalizacao002.php` | A6 | `` | resposta 200 nos dois lados, conteudo difere: +<br /> // +<b>Deprecated</b>: pg_query(): Automatic fetching of |
| `tela:iss3_emissaoalvaraeventos001.php` | A6 | `model/documentoTemplate.model.php:85` | ArgumentCountError: Requires 2 or 3 arguments, 3 given |
| `tela:con2_anexodemonstrativofuncaosubfuncao002_2018.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -s£K!ôXÅ¾ßíÑE\Á_ákÞÅÚë¿B@åC`ñºí¬ßü!ª Î!°ð¡d£ân_½¯ // + |
| `tela:sys4_libimpmax001.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - </select> </td> // - </tr> |
| `tela:fis3_fis_relatoriosani.php` | E1 | `` | resposta 200 nos dois lados, conteudo difere: -<</Filter /FlateDecode /Length 863>> // +<</Filter /FlateDecode |
| `tela:fis3_relatoriosani.php` | E1 | `` | resposta 200 nos dois lados, conteudo difere: -<</Filter /FlateDecode /Length 889>> // +<</Filter /FlateDecode |
| `tela:con2_lrfanexoxvii002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrflimites002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2018.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2012.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo17_002_2011.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_i_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_ii_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_balancoorcamentario_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfbalorc002_2015.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfdemalienataplicrecursos002_2010.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `relatorio:agu2_relconsumo002.php` | R1 | `agu2_relconsumo002.php:166` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:cad2_loteam002.php` | R1 | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu1_aguahidromatricfichatroca002.php` | R1 | `agu1_aguahidromatricfichatroca002.php:61` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu2_compleituras002.php` | R1 | `agu2_compleituras002.php:161` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu2_hidrometro002.php` | R1 | `agu2_hidrometro002.php:70` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu2_relconsumo002.php` | R1 | `agu2_relconsumo002.php:166` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu2_relimobiliarias002.php` | R1 | `agu2_relimobiliarias002.php:86` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu2_relimoveiscar002.php` | R1 | `agu2_relimoveiscar002.php:72` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu2_situacaohidro002.php` | R1 | `agu2_situacaohidro002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu4_relcorte.php` | R1 | `agu4_relcorte.php:36` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:agu4_relleituras002.php` | R1 | `agu4_relleituras002.php:54` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:arr2_rellistadqd002.php` | R1 | `arr2_rellistadqd002.php:178` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_carnesiptu002.php` | R1 | `cad2_carnesiptu002.php:57` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_comparaiptu002.php` | R1 | `cad2_comparaiptu002.php:154` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_compcaract002.php` | R1 | `cad2_compcaract002.php:124` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_descconced002.php` | R1 | `cad2_descconced002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_iptulancpago002.php` | R1 | `cad2_iptulancpago002.php:60` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_listaiptucalc_003.php` | R1 | `cad2_listaiptucalc_003.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteam002.php` | R1 | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteamentomatric002.php` | R1 | `cad2_loteamentomatric002.php:80` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteamentos002.php` | R1 | `cad2_loteamentos002.php:77` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_matricnaoproc002.php` | R1 | `cad2_matricnaoproc002.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_posicaoiptu002.php` | R1 | `cad2_posicaoiptu002.php:71` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relaverbacao002.php` | R1 | `cad2_relaverbacao002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_reldemo002.php` | R1 | `cad2_reldemo002.php:108` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relisentos002.php` | R1 | `cad2_relisentos002.php:46` | TypeError: pg_fetch_assoc(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relmassafalida002.php` | R1 | `cad2_relmassafalida002.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_setor002.php` | R1 | `cad2_setor002.php:79` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_conscadastrodetalhesmodelonovo002.php` | R1 | `cad3_conscadastrodetalhesmodelonovo002.php:171` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_iptupago002_original.php` | R1 | `cad3_iptupago002_original.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_relzonafiscal002.php` | R1 | `cad3_relzonafiscal002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_relzonafiscaltaxa002.php` | R1 | `cad3_relzonafiscaltaxa002.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt.php` | R1 | `cad4_geracarneiptutxt.php:754` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_arapiraca.php` | R1 | `cad4_geracarneiptutxt_arapiraca.php:170` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_eldorado.php` | R1 | `cad4_geracarneiptutxt_eldorado.php:167` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_guaiba.php` | R1 | `cad4_geracarneiptutxt_guaiba.php:169` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarnesiptu_geral.php` | R1 | `cad4_geracarnesiptu_geral.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cem2_edital002.php` | R1 | `cem2_edital002.php:87` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_diviano002.php` | R1 | `div2_diviano002.php:94` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_exercdivida002.php` | R1 | `div2_exercdivida002.php:392` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_parcel002.php` | R1 | `div2_parcel002.php:151` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_posicaoparc002.php` | R1 | `div2_posicaoparc002.php:247` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_procedexerc_002.php` | R1 | `div2_procedexerc_002.php:130` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:dv02_loteamentos002.php` | R1 | `dv02_loteamentos002.php:48` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:dvr2_capaloteamento002.php` | R1 | `dvr2_capaloteamento002.php:61` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:dvr3_procedper002.php` | R1 | `dvr3_procedper002.php:135` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:dvr4_parclote004.php` | R1 | `dvr4_parclote004.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:dvr4_parclote005.php` | R1 | `dvr4_parclote005.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:fis2_emiteaidof002.php` | R1 | `fis2_emiteaidof002.php:105` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:fis2_fis_levantamentolote002.php` | R1 | `fis2_fis_levantamentolote002.php:245` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:fis2_fis_levantamentomassa002.php` | R1 | `fis2_fis_levantamentomassa002.php:168` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:fis2_fis_termofiscal003.php` | R1 | `fis2_fis_termofiscal003.php:122` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:fis3_fis_consultaautoinf_imp.php` | R1 | `fis3_fis_consultaautoinf_imp.php:57` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:fis3_fis_imprimealvara.php` | R1 | `fis3_fis_imprimealvara.php:64` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:inf2_inflan002.php` | R1 | `inf2_inflan002.php:126` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_calculadoepago002.php` | R1 | `iss2_calculadoepago002.php:113` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_certibaixa002.php` | R1 | `iss2_certibaixa002.php:55` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_inscrescrito002.php` | R1 | `iss2_inscrescrito002.php:81` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_issqnpago002.php` | R1 | `iss2_issqnpago002.php:67` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_listinscrweb002.php` | R1 | `iss2_listinscrweb002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_relatorioruas002.php` | R1 | `iss2_relatorioruas002.php:179` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss3_emissaoalvaraveiculos001.php` | R1 | `iss3_emissaoalvaraveiculos001.php:64` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss3_emissaobicveiculos001.php` | R1 | `iss3_emissaobicveiculos001.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss4_contativ003.php` | R1 | `iss4_contativ003.php:222` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss4_contativ006.php` | R1 | `iss4_contativ006.php:86` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:itb2_relsetorquadralote002.php` | R1 | `itb2_relsetorquadralote002.php:255` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:jur2_relinicial002.php` | R1 | `jur2_relinicial002.php:170` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_processa002.php` | R1 | `sys4_processa002.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_processa007.php` | R1 | `sys4_processa007.php:587` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_verifica002.php` | R1 | `sys4_verifica002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cai3_gerfinanc003.php` | R2 | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo11_002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `post:agu1_aguabasevenc001.php` | - | - | SQL de escrita diverge |

**ERRO_AMBIENTE (2)**

- `tela:con4_gerenciadortarefas002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:rec2_espelhoponto002.php` - timeout: ref=000  85=500 (apos 1 retentativa)

**INCONCLUSIVO (400)**

- pagina de erro identica nos dois lados (tela nao exercitada): **299**
  <details><summary>lista</summary>

  `arr3_histocorrencia001.php`, `arr3_relatoriototaldebitosanalitico001.php`, `arr4_manutencaovinculosnumpre002.php`, `arr4_taxaslancadas004.php`, `cad1_cadlote001.php`, `cad1_cadlote002.php`, `cad1_cadlote003.php`, `cad1_cadruas003.php`, `cad1_iptubaixa002.php`, `cad1_iptubasealt.php`, `cad1_reliptuender002.php`, `cad1_setor001.php`, `cad1_setor002.php`, `cad1_setor003.php`, `cad2_relatorios_002.php`, `cad2_relcaixa_002.php`, `cad3_consCadastroIptu.php`, `cad3_conscadastro_agua_002.php`, `cad3_conscadastro_iptu_002.php`, `cad3_conscertforlaud002.php`, `cad3_conscertlanc002.php`, `cad3_conscertvalven002.php`, `cad4_iptuconstr.RPC.php`, `cad4_recadastramentoconsultaiptu.php`, `cai1_autenticadora005.php`, `cai1_cadtipoparc006.php`, `cai1_caitransfseq003.php`, `cai1_extratolinha001.php`, `cai1_extratolinha002.php`, `cai1_extratolinha003.php`, `cai1_historico001.php`, `cai1_tabrec003.php`, `cai2_correceitas002.php`, `cai2_digitasaldoextratomanual.php`, `cai2_digitasaldoextratomanuallinha.php`, `cai2_guiaspagasgrm002.php`, `cai2_movimento_extra_financeiro002.php`, `cai2_receisub002.php`, `cai2_relcaixa_002.php`, `cai2_reldescontos002.php`, `cai2_saltes003.php`, `cai3_gerfinanc001.php`, `cai3_gerfinanc002.php`, `cai3_gerfinanc075.php`, `cai3_integracaotjemissao001.php`, `cai3_reemiterecibo.php`, `cai4_abreconciliacao_processa.php`, `cai4_atividadesgrm.RPC.php`, `cai4_baixabanco001_agencia_88888.php`, `cai4_baixabanco001_codcli_19985.php`, `cai4_baixabanco_daeb.php`, `cai4_cancdebitosproc001.php`, `cai4_desmembramentodisbanco001.php`, `cai4_devolucaoadiantamento002.php`, `cai4_relatorioconciliacao_manual.php`, `cai4_relatorioconciliacaomanual002_layout2.php`, `cai4_remissbob003.php`, `cem1_itenserv002.php`, `cem1_sepultamentos002.php`, `cem1_sepultamentos007.php`, `con1_autenticaUsuarioMobile.RPC.php`, `con1_codclass001.php`, `con1_codclass002.php`, `con1_codclass003.php`, `con1_codhist001.php`, `con1_codhist002.php`, `con1_codhist003.php`, `con1_codsistema001.php`, `con1_codsistema002.php`, `con1_codsistema003.php`, `con1_conplanorec001.php`, `con1_conplanorec002.php`, `con1_conplanorec003.php`, `con1_db_ordem003.php`, `con1_db_permemp002.php`, `con1_db_permemp003.php`, `con1_db_syscampo001.php`, `con1_db_syscampo002.php`, `con1_db_syscampo003.php`, `con1_db_tarefas001.php`, `con1_db_tarefas003.php`, `con1_db_tarefasit004.php`, `con1_tarefasit001.php`, `con1_tarefasit002.php`, `con1_tarefasit003.php`, `con2_anexo12_002.php`, `con2_anexo12_002_2008.php`, `con2_anexo12rpps_002_2008.php`, `con2_anexo13_002.php`, `con2_anexo13rpps_002.php`, `con2_anexo14_002.php`, `con2_anexo14_002_2011.php`, `con2_anexo14rpps_002.php`, `con2_anexo14rpps_002_2008.php`, `con2_anexo15ee_002.php`, `con2_anexo15lrf_002.php`, `con2_anexo15lrf_002_2011.php`, `con2_anexo17_002.php`, `con2_anexoXIII_002_2011.php`, `con2_anexoXVI_002_2011.php`, `con2_balancdespsint002.php`, `con2_balancetemsc002.php`, `con2_balanceteverificacaocontacorrente002.php`, `con2_balancofinanceiro_2014.php`, `con2_balancopatrimonial_2014.php`, `con2_balancrece002_2008.php`, `con2_balancverificacao002.php`, `con2_confdesppessoal002.php`, `con2_despesacomeducacao003.php`, `con2_despesacomsaude003.php`, `con2_estruturarel.php`, `con2_fluxodecaixa_2014.php`, `con2_imprimeseqelemento002.php`, `con2_indice_educ002.php`, `con2_lfrorcanexoii002_2008.php`, `con2_lfrorcanexoii002_2010.php`, `con2_lrfbalorc002_2008.php`, `con2_lrfbalorc002_2010.php`, `con2_lrfbalorc002_2012.php`, `con2_lrfdemdisponibcaixa002_2010.php`, `con2_lrfdemonstrativorp002_2008.php`, `con2_lrfdesppessoal002.php`, `con2_lrfdesppessoal002_2007.php`, `con2_lrfdesppessoal002_2008.php`, `con2_lrfdesppessoal002_2009.php`, `con2_lrfdesppessoal002_2010.php`, `con2_lrfdesppessoal002_2011.php`, `con2_lrfdesppessoal002_2015.php`, `con2_lrfdispcaixa002.php`, `con2_lrfdivida002.php`, `con2_lrfdivida002_2008.php`, `con2_lrfdivida002_2009.php`, `con2_lrfgarantias002.php`, `con2_lrfgarantias002_2008.php`, `con2_lrfgarantias002_2009.php`, `con2_lrfimpostossaude002.php`, `con2_lrfimpostossaude002_2009.php`, `con2_lrfimpostossaude002_2013.php`, `con2_lrflimites002.php`, `con2_lrflimites002_2008.php`, `con2_lrflimites002_2009.php`, `con2_lrfmdefundeb0001.php`, `con2_lrfmdefundeb001.php`, `con2_lrfnominal002.php`, `con2_lrfnominal002_2009.php`, `con2_lrfprimario002.php`, `con2_lrfprimario002_2008.php`, `con2_lrfprimario002_2010.php`, `con2_lrfprimario002_2015.php`, `con2_lrfrecdesprpps002_2009.php`, `con2_lrfreceitacorrente002.php`, `con2_lrfreceitacorrente002_2008.php`, `con2_lrfreceitacorrente002_2009.php`, `con2_lrfreceitacorrente002_var.php`, `con2_lrfresumido002.php`, `con2_lrfresumido002_2007.php`, `con2_lrfresumido002_2008.php`, `con2_lrfresumido002_2009.php`, `con2_lrfresumido002_2015.php`, `con2_lrfresumido002_2018.php`, `con2_lrfrgfdemrestosapagar002_2010.php`, `con2_opercredito002.php`, `con2_opercredito002_2008.php`, `con2_opercredito002_2009.php`, `con2_razaocontas002.php`, `con2_razaoporcontas003.php`, `con2_rec_desp_extra_002.php`, `con2_relatoriosiconfi011.php`, `con2_reledital004.php`, `con2_variacoespatrimoniais_2014.php`, `con2_varpatrimoniaisrpps_002_2008.php`, `con3_conscontri008.php`, `con3_db_syscampo004.php`, `con4_boletim004.php`, `con4_consacordos003.php`, `con4_parametrosrelatorioslegais001.php`, `con4_processaaberturaexercicio.RPC.php`, `con4_registrasistema.php`, `con4_trabalhos001.php`, `con4_viradadeano002_item001.php`, `con4_viradadeano002_item002.php`, `con4_viradadeano002_item003.php`, `con4_viradadeano002_item004.php`, `con4_viradadeano002_item005.php`, `con4_viradadeano002_item006.php`, `con4_viradadeano002_item007.php`, `con4_viradadeano002_item008.php`, `con4_viradadeano002_item009.php`, `con4_viradadeano002_item010.php`, `con4_viradadeano002_item011.php`, `con4_viradadeano002_item012.php`, `con4_viradadeano002_item013.php`, `con4_viradadeano002_item014.php`, `con4_viradadeano002_item015.php`, `con4_viradadeano002_item016.php`, `con4_viradadeano002_item017.php`, `con4_viradadeano002_item018.php`, `con4_viradadeano002_item019.php`, `con4_viradadeano002_item020.php`, `con4_viradadeano002_item021.php`, `con4_viradadeano002_item022.php`, `con4_viradadeano002_item023.php`, `con4_viradadeano002_item024.php`, `con4_viradadeano002_item025.php`, `con4_viradadeano002_item026.php`, `con4_viradadeano002_item027.php`, `con4_viradadeano002_item028.php`, `con4_viradadeano002_item029.php`, `con4_viradadeano002_item030.php`, `con4_viradadeano002_item031.php`, `con4_viradadeano002_item032.php`, `con4_viradadeano002_item033.php`, `con4_viradadeano002_item034.php`, `con4_viradadeano002_item035.php`, `con4_viradadeano002_item036.php`, `con6_andamentolista.php`, `con6_ordemagendamento002.php`, `con6_ordemandamento002.php`, `con7_ordemandamento002.php`, `div2_certdiv_002.php`, `div2_certid002.php`, `div2_certparc_002.php`, `div2_execfisc_002.php`, `div4_emissaorecibocda.RPC.php`, `div4_movimentacaocda.RPC.php`, `fis1_auto004.php`, `fis1_fis_auto004.php`, `fis1_fis_fiscal004.php`, `fis1_fis_lancamento004.php`, `fis1_fis_lanclevanta001.php`, `fis1_fis_tiafprazoproc002.php`, `fis1_fis_tiafprazoproc003.php`, `fis1_fis_vistorias003.php`, `fis1_fis_vistorias004.php`, `fis1_fiscal004.php`, `fis1_tiafprazoproc002.php`, `fis1_tiafprazoproc003.php`, `fis1_vistorias004.php`, `fis2_fis_autoinf002.php`, `fis2_fis_emiteaidof002.php`, `fis2_fis_notlanc002.php`, `fis2_fis_notlancmassa002.php`, `fis2_fis_taxadiversos002.php`, `fis2_taxadiversos002.php`, `fis3_consfiscalinf002.php`, `fis3_fandam004.php`, `fis3_fandamauto004.php`, `fis3_fandamnoti004.php`, `fis3_fis_consfiscalinf002.php`, `fis3_fis_conslancamento002.php`, `fis3_fis_conslancamento003.php`, `fis3_fis_consulancamento_imp.php`, `fis3_fis_fandam004.php`, `fis3_fis_fandamauto004.php`, `fis3_fis_fandamlancamento004.php`, `fis3_fis_fandamnoti004.php`, `inf2_importacaomultasnaocadastradas002.php`, `inf4_manvalores002.php`, `iss2_imprimetermo001.php`, `iss2_simples002.php`, `iss3_carnesiss.php`, `itb1_itbi004.php`, `itb1_itbiavalia002.php`, `itb1_itbiavalia003.php`, `itb1_itbidadosimovel003.php`, `itb1_itbinome011.php`, `jur_enviarremessatj.php`, `pro1_cgmdoc002.php`, `pro1_cgmdoc003.php`, `pro1_obras004.php`, `pro1_obrasconstr002.php`, `pro1_obrasconstr003.php`, `pro1_procandamint001.php`, `pro1_procandamint002.php`, `pro1_procandamint003.php`, `pro1_protparamglobal001.php`, `pro1_protparamglobal003.php`, `pro1_protprocesso001.php`, `pro1_protprocesso002.php`, `pro1_protprocesso003.php`, `pro2_relconspro002.php`, `pro3_consultaobra002_habite.php`, `pro4_capaprocesso.php`, `pro4_termorecebimento2.php`, `prot1_cadastrocgm.php`, `prot1_cadastrocgmtest.php`, `prot1_pfisica.php`, `prot1_pjuridica.php`, `prot3_consultacgmnovo003.php`, `prot3_consultacgmnovo004.php`, `prot3_consultacgmnovo006.php`, `prot3_consultacgmnovo007.php`, `rec2_espelhopontotela002.php`, `rec2_previsaodedireitos002.php`, `rec4_autorizacaohelote.php`, `rec4_exclusao_lote_assentamento.php`, `sys4_baixatarefa002.php`, `sys4_geradebitos003.php`, `sys4_processarelatorioRPC.php`

  </details>
- resposta vazia nos dois lados: **99**
  <details><summary>lista</summary>

  `agu2_avscortevlrdivida002.php`, `agu3_conscadastro_002_classe.php`, `agu4_impdadoscoletores_classe.php`, `agu4_senhaleiturista.RPC.php`, `arr4_acertaparcelamento.RPC.php`, `arr4_declquitacao.RPC.php`, `arr4_manutencaoAbatimento.RPC.php`, `arr4_numprebloqpag.RPC.php`, `cad1_buscaexercicio.php`, `cad4_geracarneiptutxtParcelasOpcionais.php`, `cai1_cairetordemvalida.php`, `cai1_pix002.php`, `cai4_cancelabaixabancoRPC.php`, `cai4_gerazim.php`, `cai4_importatipo001.php`, `cai4_placaixaRPC.php`, `cai4_processaconciliacao.php`, `cai4_processaconciliacao_manual.php`, `cai4_transferenciaNumpre.RPC.php`, `con1_congrupo004.php`, `con1_conplanogrupoconta004.php`, `con2_anexodemonstrativofuncaosubfuncao002.php`, `con2_planosys002.php`, `con3_versao005.php`, `con4_db_departRPC.php`, `con4_endereco.RPC.php`, `con4_geratcearqRPC.php`, `con4_importadoc001.php`, `con4_importadocpadrao001.php`, `con4_inscreverp002.php`, `con4_mensagems.RPC.php`, `con4_padbal_desp.php`, `con4_padbal_rec.php`, `con4_padbal_ver.php`, `con4_padbrec_ant.php`, `con4_padbrub_ant.php`, `con4_padbver_ant.php`, `con4_padbver_enc.php`, `con4_padbvmovant.php`, `con4_padconverterubrica.php`, `con4_padcredor.php`, `con4_padcta_disp.php`, `con4_padcta_oper.php`, `con4_paddecreto.php`, `con4_padempenho.php`, `con4_padfuncao.php`, `con4_padliquidac.php`, `con4_padorgao.php`, `con4_padpagament.php`, `con4_padprograma.php`, `con4_padprojativ.php`, `con4_padrd_extra.php`, `con4_padrec_ant.php`, `con4_padreceita.php`, `con4_padrecurso.php`, `con4_padrubrica.php`, `con4_padsubfunc.php`, `con4_padsubprog.php`, `con4_padtcelivrodiariogeral.php`, `con4_paduniorcam.php`, `con4_processaconsistencia.php`, `con4_processapad.php`, `div4_buscatipoRPC.php`, `div4_importa002.php`, `fis1_fis_saniatividade001.php`, `fis1_fis_taxagrupo.RPC.php`, `fis1_fis_tipoandam005.php`, `fis1_saniatividade001.php`, `fis1_taxagrupo.RPC.php`, `fis4_fis_autobaixaprociframe.php`, `fis4_fis_autobaixaprociframealt.php`, `iss1_ativid004.php`, `iss2_processaarquivoretencao002.php`, `iss2_relissret002.php`, `iss2_relissvariavel002.php`, `jur3_emiteinicialdebitos.php`, `pre4_email.php`, `pro1_camposdinamicosandamentopadrao.RPC.php`, `pro4_obrashabiteRPC.php`, `prot1_cadgeralmunic.RPC.php`, `prot1_comparanomes.php`, `prot4_tipo_processo.RPC.php`, `rec1_assentadb_cadattdinamicovalorgrupo001.php`, `rec1_assentadb_cadattdinamicovalorgrupo002.php`, `rec1_assentadb_cadattdinamicovalorgrupo003.php`, `rec1_portariasRPC.php`, `rec1_tipoassedb_cadattdinamico001.php`, `rec1_tipoassedb_cadattdinamico002.php`, `rec1_tipoassedb_cadattdinamico003.php`, `rec2_gradeefetividade003.php`, `rec2_rhestagio003.php`, `rec4_importararquivosporrelogioponto.php`, `rec4_pontoeletronico.RPC.php`, `rec4_rpcexame.php`, `sys4_cadastrotemplateRPC.php`, `sys4_consultaviewRPC.php`, `sys4_mostravariaveisdinamica.php`, `sys4_verificaclasse003.php`, `tri4_carregadadosisencao.php`

  </details>
- pulada (destroi a sessao do harness): **1**
  <details><summary>lista</summary>

  `cad4_geracarneiptutxt_cli.php`

  </details>
- pulada (contata servico externo): **1**
  <details><summary>lista</summary>

  `iss4_siss002.php`

  </details>

### financeiro

IDENTICO 6183 | DIVERGE 90 | INCONCLUSIVO 467 | ERRO_AMBIENTE 1

**DIVERGE (90)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:cad2_emissaobic_002.php` | A1 | `cad2_emissaobic_002.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad3_conscadastro_relatorio.php` | A1 | `cad3_conscadastro_relatorio.php:43` | TypeError: sizeof(): Argument #1 ($x) must be of type Countable/array, null given |
| `tela:cad4_recadastramentorelatorio.php` | A1 | `cad4_recadastramentorelatorio.php:106` | TypeError: array_chunk(): Argument #1 ($x) must be of type array, null given |
| `tela:iss3_inconsistenciaSimples.php` | A1 | `iss3_inconsistenciaSimples.php:62` | TypeError: rsort(): Argument #1 ($x) must be of type array, null given |
| `tela:pes4_geraarquivosmanadnovo.php` | A1 | `model/manad.model.php:129` | TypeError: implode(): If argument #1 ($x) is of type string, argument #2 ($x) must be of type array, null give |
| `tela:sys4_listaretornosql001.php` | A1 | `sys4_listaretornosql001.php:67` | TypeError: array_keys(): Argument #1 ($x) must be of type array, null given |
| `relatorio:div2_resumogeraldivida002.php` | A2 | `classes/db_divida_classe.php:2378` | TypeError: Unsupported operand types: string - int |
| `tela:div2_resumogeraldivida002.php` | A2 | `classes/db_divida_classe.php:2378` | TypeError: Unsupported operand types: string - int |
| `tela:iss2_relarrec1002.php` | A2 | `iss2_relarrec1002.php:53` | TypeError: Unsupported operand types: string + int |
| `tela:orc2_atividades002.php` | A2 | `fpdf151/fpdf.php:932` | TypeError: Unsupported operand types: int + string |
| `tela:sys4_consultaXML.RPC.php` | A3 | `sys4_consultaXML.RPC.php:39` | ValueError: Path must not be empty |
| `tela:sys4_processa004.php` | A3 | `sys4_processa004.php:111` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `tela:sys4_processa008.php` | A3 | `sys4_processa008.php:100` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `tela:pes4_geracaoarquivorefeisul.RPC.php` | A5 | `` | E_ERROR - Uncaught exception 'ParseError' with message 'syntax error, unexpected token "{", expecting ")"' in  |
| `tela:con2_lrflimites002_2015.php` | A6 | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `tela:iss3_emissaoalvaraeventos001.php` | A6 | `model/documentoTemplate.model.php:85` | ArgumentCountError: Requires 2 or 3 arguments, 3 given |
| `tela:pes2_feriasaviso002.php` | A6 | `pes2_feriasaviso002.php:112` | ValueError: cal_days_in_month(): Argument #2 ($x) must be between 1 and 2147483646 |
| `tela:con2_lrfanexoxvii002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrflimites002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2018.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2012.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo17_002_2011.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_i_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_ii_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_balancoorcamentario_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfbalorc002_2015.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfdemalienataplicrecursos002_2010.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `relatorio:cad2_loteam002.php` | R1 | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_carnesiptu002.php` | R1 | `cad2_carnesiptu002.php:57` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_comparaiptu002.php` | R1 | `cad2_comparaiptu002.php:154` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_compcaract002.php` | R1 | `cad2_compcaract002.php:124` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_descconced002.php` | R1 | `cad2_descconced002.php:59` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_iptulancpago002.php` | R1 | `cad2_iptulancpago002.php:60` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_listaiptucalc_003.php` | R1 | `cad2_listaiptucalc_003.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteam002.php` | R1 | `cad2_loteam002.php:179` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteamentomatric002.php` | R1 | `cad2_loteamentomatric002.php:80` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_loteamentos002.php` | R1 | `cad2_loteamentos002.php:77` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_matricnaoproc002.php` | R1 | `cad2_matricnaoproc002.php:74` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_posicaoiptu002.php` | R1 | `cad2_posicaoiptu002.php:71` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relaverbacao002.php` | R1 | `cad2_relaverbacao002.php:155` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_reldemo002.php` | R1 | `cad2_reldemo002.php:108` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relisentos002.php` | R1 | `cad2_relisentos002.php:46` | TypeError: pg_fetch_assoc(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_relmassafalida002.php` | R1 | `cad2_relmassafalida002.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad2_setor002.php` | R1 | `cad2_setor002.php:79` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_conscadastrodetalhesmodelonovo002.php` | R1 | `cad3_conscadastrodetalhesmodelonovo002.php:171` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_iptupago002_original.php` | R1 | `cad3_iptupago002_original.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_relzonafiscal002.php` | R1 | `cad3_relzonafiscal002.php:62` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad3_relzonafiscaltaxa002.php` | R1 | `cad3_relzonafiscaltaxa002.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt.php` | R1 | `cad4_geracarneiptutxt.php:754` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_arapiraca.php` | R1 | `cad4_geracarneiptutxt_arapiraca.php:170` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_eldorado.php` | R1 | `cad4_geracarneiptutxt_eldorado.php:167` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarneiptutxt_guaiba.php` | R1 | `cad4_geracarneiptutxt_guaiba.php:169` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cad4_geracarnesiptu_geral.php` | R1 | `cad4_geracarnesiptu_geral.php:60` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_diviano002.php` | R1 | `div2_diviano002.php:94` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_exercdivida002.php` | R1 | `div2_exercdivida002.php:392` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_parcel002.php` | R1 | `div2_parcel002.php:151` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_posicaoparc002.php` | R1 | `div2_posicaoparc002.php:247` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:div2_procedexerc_002.php` | R1 | `div2_procedexerc_002.php:130` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:inf2_inflan002.php` | R1 | `inf2_inflan002.php:126` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_calculadoepago002.php` | R1 | `iss2_calculadoepago002.php:113` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_certibaixa002.php` | R1 | `iss2_certibaixa002.php:55` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_inscrescrito002.php` | R1 | `iss2_inscrescrito002.php:81` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_issqnpago002.php` | R1 | `iss2_issqnpago002.php:67` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_listinscrweb002.php` | R1 | `iss2_listinscrweb002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss2_relatorioruas002.php` | R1 | `iss2_relatorioruas002.php:179` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss3_emissaoalvaraveiculos001.php` | R1 | `iss3_emissaoalvaraveiculos001.php:64` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss3_emissaobicveiculos001.php` | R1 | `iss3_emissaobicveiculos001.php:63` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss4_contativ003.php` | R1 | `iss4_contativ003.php:222` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:iss4_contativ006.php` | R1 | `iss4_contativ006.php:86` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:pes2_rubmesponto002.php` | R1 | `pes2_rubmesponto002.php:214` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_processa002.php` | R1 | `sys4_processa002.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_processa007.php` | R1 | `sys4_processa007.php:587` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_verifica002.php` | R1 | `sys4_verifica002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:orc2_desppessoal002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cai3_gerfinanc003.php` | R2 | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo11_002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:orc2_desppessoal002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:orc2_receitasDespesasPrevidenciariasServidores002.php` | - | - | ref=200/23769B  85=200/23769B |
| `tela:pes2_osocontramatricial002.php` | - | - | ref=200/4196B  85=200/4150B |
| `tela:pes4_geraarquivosmanad.php` | - | - | ref=200/334982B  85=200/2259B |
| `tela:sys4_libimpmax001.php` | - | - | ref=200/7692B  85=200/4669B |

**ERRO_AMBIENTE (1)**

- `tela:con4_gerenciadortarefas002.php` - timeout: ref=000  85=500 (apos 1 retentativa)

**INCONCLUSIVO (467)**

- pagina de erro identica nos dois lados (tela nao exercitada): **367**
  <details><summary>lista</summary>

  `cad1_cadlote001.php`, `cad1_cadlote002.php`, `cad1_cadlote003.php`, `cad1_cadruas003.php`, `cad1_iptubaixa002.php`, `cad1_iptubasealt.php`, `cad1_reliptuender002.php`, `cad1_setor001.php`, `cad1_setor002.php`, `cad1_setor003.php`, `cad2_relatorios_002.php`, `cad2_relcaixa_002.php`, `cad3_consCadastroIptu.php`, `cad3_conscadastro_agua_002.php`, `cad3_conscadastro_iptu_002.php`, `cad3_conscertforlaud002.php`, `cad3_conscertlanc002.php`, `cad3_conscertvalven002.php`, `cad4_iptuconstr.RPC.php`, `cad4_recadastramentoconsultaiptu.php`, `cai1_autenticadora005.php`, `cai1_cadtipoparc006.php`, `cai1_caitransfseq003.php`, `cai1_extratolinha001.php`, `cai1_extratolinha002.php`, `cai1_extratolinha003.php`, `cai1_historico001.php`, `cai1_tabrec003.php`, `cai2_correceitas002.php`, `cai2_digitasaldoextratomanual.php`, `cai2_digitasaldoextratomanuallinha.php`, `cai2_guiaspagasgrm002.php`, `cai2_movimento_extra_financeiro002.php`, `cai2_receisub002.php`, `cai2_relcaixa_002.php`, `cai2_reldescontos002.php`, `cai2_saltes003.php`, `cai3_gerfinanc001.php`, `cai3_gerfinanc002.php`, `cai3_gerfinanc075.php`, `cai3_integracaotjemissao001.php`, `cai3_reemiterecibo.php`, `cai4_abreconciliacao_processa.php`, `cai4_atividadesgrm.RPC.php`, `cai4_baixabanco001_agencia_88888.php`, `cai4_baixabanco001_codcli_19985.php`, `cai4_baixabanco_daeb.php`, `cai4_cancdebitosproc001.php`, `cai4_desmembramentodisbanco001.php`, `cai4_devolucaoadiantamento002.php`, `cai4_relatorioconciliacao_manual.php`, `cai4_relatorioconciliacaomanual002_layout2.php`, `cai4_remissbob003.php`, `com1_itens001proc.php`, `com1_orcamlancval002.php`, `com1_orcamlancval003.php`, `com1_solicita004_altera.php`, `com1_solicitaregistropreco001.php`, `com1_solicitaregistropreco002.php`, `com1_solicitaregistropreco003.php`, `com1_solicitem002.php`, `com1_solicitem003.php`, `com2_relatorioatasvigentes002.php`, `com4_consabertregistro003.php`, `com4_inserirdotacaosolicitacao.RPC.php`, `con1_autenticaUsuarioMobile.RPC.php`, `con1_codclass001.php`, `con1_codclass002.php`, `con1_codclass003.php`, `con1_codhist001.php`, `con1_codhist002.php`, `con1_codhist003.php`, `con1_codsistema001.php`, `con1_codsistema002.php`, `con1_codsistema003.php`, `con1_conplanorec001.php`, `con1_conplanorec002.php`, `con1_conplanorec003.php`, `con1_db_ordem003.php`, `con1_db_permemp002.php`, `con1_db_permemp003.php`, `con1_db_syscampo001.php`, `con1_db_syscampo002.php`, `con1_db_syscampo003.php`, `con1_db_tarefas001.php`, `con1_db_tarefas003.php`, `con1_db_tarefasit004.php`, `con1_tarefasit001.php`, `con1_tarefasit002.php`, `con1_tarefasit003.php`, `con2_anexo12_002.php`, `con2_anexo12_002_2008.php`, `con2_anexo12rpps_002_2008.php`, `con2_anexo13_002.php`, `con2_anexo13rpps_002.php`, `con2_anexo14_002.php`, `con2_anexo14_002_2011.php`, `con2_anexo14rpps_002.php`, `con2_anexo14rpps_002_2008.php`, `con2_anexo15ee_002.php`, `con2_anexo15lrf_002.php`, `con2_anexo15lrf_002_2011.php`, `con2_anexo17_002.php`, `con2_anexoXIII_002_2011.php`, `con2_anexoXVI_002_2011.php`, `con2_balancdespsint002.php`, `con2_balancetemsc002.php`, `con2_balanceteverificacaocontacorrente002.php`, `con2_balancofinanceiro_2014.php`, `con2_balancopatrimonial_2014.php`, `con2_balancrece002_2008.php`, `con2_balancverificacao002.php`, `con2_confdesppessoal002.php`, `con2_despesacomeducacao003.php`, `con2_despesacomsaude003.php`, `con2_estruturarel.php`, `con2_fluxodecaixa_2014.php`, `con2_imprimeseqelemento002.php`, `con2_indice_educ002.php`, `con2_lfrorcanexoii002_2008.php`, `con2_lfrorcanexoii002_2010.php`, `con2_lrfbalorc002_2008.php`, `con2_lrfbalorc002_2010.php`, `con2_lrfbalorc002_2012.php`, `con2_lrfdemdisponibcaixa002_2010.php`, `con2_lrfdemonstrativorp002_2008.php`, `con2_lrfdesppessoal002.php`, `con2_lrfdesppessoal002_2007.php`, `con2_lrfdesppessoal002_2008.php`, `con2_lrfdesppessoal002_2009.php`, `con2_lrfdesppessoal002_2010.php`, `con2_lrfdesppessoal002_2011.php`, `con2_lrfdesppessoal002_2015.php`, `con2_lrfdispcaixa002.php`, `con2_lrfdivida002.php`, `con2_lrfdivida002_2008.php`, `con2_lrfdivida002_2009.php`, `con2_lrfgarantias002.php`, `con2_lrfgarantias002_2008.php`, `con2_lrfgarantias002_2009.php`, `con2_lrfimpostossaude002.php`, `con2_lrfimpostossaude002_2009.php`, `con2_lrfimpostossaude002_2013.php`, `con2_lrflimites002.php`, `con2_lrflimites002_2008.php`, `con2_lrflimites002_2009.php`, `con2_lrfmdefundeb0001.php`, `con2_lrfmdefundeb001.php`, `con2_lrfnominal002.php`, `con2_lrfnominal002_2009.php`, `con2_lrfprimario002.php`, `con2_lrfprimario002_2008.php`, `con2_lrfprimario002_2010.php`, `con2_lrfprimario002_2015.php`, `con2_lrfrecdesprpps002_2009.php`, `con2_lrfreceitacorrente002.php`, `con2_lrfreceitacorrente002_2008.php`, `con2_lrfreceitacorrente002_2009.php`, `con2_lrfreceitacorrente002_var.php`, `con2_lrfresumido002.php`, `con2_lrfresumido002_2007.php`, `con2_lrfresumido002_2008.php`, `con2_lrfresumido002_2009.php`, `con2_lrfresumido002_2015.php`, `con2_lrfresumido002_2018.php`, `con2_lrfrgfdemrestosapagar002_2010.php`, `con2_opercredito002.php`, `con2_opercredito002_2008.php`, `con2_opercredito002_2009.php`, `con2_razaocontas002.php`, `con2_razaoporcontas003.php`, `con2_rec_desp_extra_002.php`, `con2_relatoriosiconfi011.php`, `con2_reledital004.php`, `con2_variacoespatrimoniais_2014.php`, `con2_varpatrimoniaisrpps_002_2008.php`, `con3_conscontri008.php`, `con3_db_syscampo004.php`, `con4_boletim004.php`, `con4_consacordos003.php`, `con4_parametrosrelatorioslegais001.php`, `con4_processaaberturaexercicio.RPC.php`, `con4_registrasistema.php`, `con4_trabalhos001.php`, `con4_viradadeano002_item001.php`, `con4_viradadeano002_item002.php`, `con4_viradadeano002_item003.php`, `con4_viradadeano002_item004.php`, `con4_viradadeano002_item005.php`, `con4_viradadeano002_item006.php`, `con4_viradadeano002_item007.php`, `con4_viradadeano002_item008.php`, `con4_viradadeano002_item009.php`, `con4_viradadeano002_item010.php`, `con4_viradadeano002_item011.php`, `con4_viradadeano002_item012.php`, `con4_viradadeano002_item013.php`, `con4_viradadeano002_item014.php`, `con4_viradadeano002_item015.php`, `con4_viradadeano002_item016.php`, `con4_viradadeano002_item017.php`, `con4_viradadeano002_item018.php`, `con4_viradadeano002_item019.php`, `con4_viradadeano002_item020.php`, `con4_viradadeano002_item021.php`, `con4_viradadeano002_item022.php`, `con4_viradadeano002_item023.php`, `con4_viradadeano002_item024.php`, `con4_viradadeano002_item025.php`, `con4_viradadeano002_item026.php`, `con4_viradadeano002_item027.php`, `con4_viradadeano002_item028.php`, `con4_viradadeano002_item029.php`, `con4_viradadeano002_item030.php`, `con4_viradadeano002_item031.php`, `con4_viradadeano002_item032.php`, `con4_viradadeano002_item033.php`, `con4_viradadeano002_item034.php`, `con4_viradadeano002_item035.php`, `con4_viradadeano002_item036.php`, `con6_andamentolista.php`, `con6_ordemagendamento002.php`, `con6_ordemandamento002.php`, `con7_ordemandamento002.php`, `cus1_parcustos002.php`, `cus1_parcustos003.php`, `div2_certdiv_002.php`, `div2_certid002.php`, `div2_certparc_002.php`, `div2_execfisc_002.php`, `div4_emissaorecibocda.RPC.php`, `div4_movimentacaocda.RPC.php`, `emp1_empageconf001.php`, `emp1_empageconf002.php`, `emp1_empageconf003.php`, `emp1_empautidot002.php`, `emp1_empautidot003.php`, `emp1_empautitem002.php`, `emp1_empautitem003.php`, `emp1_empautoriza003.php`, `emp1_empautret002.php`, `emp1_empautret003.php`, `emp1_empempenho003.php`, `emp1_empempitem002.php`, `emp1_empempitem003.php`, `emp1_empempret002.php`, `emp1_empempret003.php`, `emp1_empliquidaarq.php`, `emp1_emppagamento002.php`, `emp1_emppagamentoarq.php`, `emp1_emppagamentoestorna002.php`, `emp1_ordemcompra_liquida003.php`, `emp1_pagordemarq.php`, `emp2_empenhoclassificacaocredor002.php`, `emp2_empenhohistorico002.php`, `emp4_emppagamento002.php`, `emp4_liquidacao004.php`, `emp4_pagarempenho002.php`, `inf2_importacaomultasnaocadastradas002.php`, `inf4_manvalores002.php`, `iss2_imprimetermo001.php`, `iss2_simples002.php`, `iss3_carnesiss.php`, `orc1_orcparamrelopcre002.php`, `orc1_orcparamrelopcre003.php`, `orc1_orcppa006.php`, `orc1_orcsuplem005.php`, `orc1_tiporec001.php`, `orc1_tiporec002.php`, `orc1_tiporec003.php`, `orc2_DemRiscosFiscaisProvidencias.php`, `orc2_EstimativaRenunciaReceita002.php`, `orc2_MargemDespesasCaraterContinuado.php`, `orc2_ReceitasDespesasPrevidenciariasServidores.php`, `orc2_acompanhamentocronograma001.php`, `orc2_anexo8002.php`, `orc2_anexodividapublica002.php`, `orc2_anexodotacaogoverno002.php`, `orc2_anexoorcamentofiscal002.php`, `orc2_anexoreceitacorrenteliquida002.php`, `orc2_anexoseguridadesocial002.php`, `orc2_anexosumrecfontesdespfuncaogov002.php`, `orc2_anexotrabalhogoverno002.php`, `orc2_demManutencaoDesenvolvimentoEnsino002.php`, `orc2_demreceitasdespesassaude002.php`, `orc2_despsecretaria002.php`, `orc2_estimativaRenunciaReceita002.php`, `orc2_orcprevmensaldesp002.php`, `orc2_ppaevolucaodemostrativoreceita002.php`, `orc2_recppa002.php`, `orc2_recursorecdesp002.php`, `orc2_reldespesas002.php`, `orc2_reldespesas002txt.php`, `orc2_totaliza002.php`, `orc4_duplicaorcamento001.php`, `orc4_duplicaorcamentorec001.php`, `orc4_ppadotacaoelementos004.php`, `orc4_resumogeralprevreceita002.php`, `pes1_cfpess002.php`, `pes1_pensao001_acoes.php`, `pes1_reajusteprog001.php`, `pes1_reajustesal002.php`, `pes1_rhcadregime001.php`, `pes1_rhcadregime003.php`, `pes1_rhlotavincele002.php`, `pes1_rhlotavincele003.php`, `pes1_rhpagatra002.php`, `pes1_rhpagatra003.php`, `pes1_rhpeslocaltrab002.php`, `pes1_rhpessoalmov002.php`, `pes1_rhpessoalmov003.php`, `pes2_alecontramatricial002.php`, `pes2_arrcontramatricial002.php`, `pes2_carcontramatricial002.php`, `pes2_contramatricial002.php`, `pes2_emissao_csv002.php`, `pes2_emissao_pdf002.php`, `pes2_historicoconsignado002.php`, `pes2_itau240cnabgeracao002.php`, `pes2_layoutideal002.php`, `pes2_termorescisaomodimprime80.php`, `pes3_consponto021_complementar.php`, `pes3_consponto021_salario.php`, `pes3_consponto021_suplementar.php`, `pes3_faixasSalariais002CSV.php`, `pes3_gerfinanc018_salario.php`, `pes4_aberturacomplementar001.php`, `pes4_aberturasuplementar001.php`, `pes4_acertaempenhospcasp.RPC.php`, `pes4_assentamentorra001.php`, `pes4_assentamentosubstituicao001.php`, `pes4_cancelaaberturacomplementar001.php`, `pes4_cancelaaberturasuplementar001.php`, `pes4_cancelafechamentocomplementar001.php`, `pes4_cancelafechamentosalario001.php`, `pes4_cancelafechamentosuplementar001.php`, `pes4_fechamentocomplementar001.php`, `pes4_fechamentosuplementar001.php`, `pes4_implantacaoponto001.php`, `pes4_inicializavt002.php`, `pes4_ipe002.php`, `pes4_ipe003.php`, `pes4_lancamentoassentamento001.php`, `pes4_retornocontratosconsignadosmanual.php`, `pes4_rhfopag91002.php`, `pla2_abas_anexos_metas_riscos.php`, `pla2_abas_rreo.php`, `pro1_cgmdoc002.php`, `pro1_cgmdoc003.php`, `pro1_obras004.php`, `pro1_obrasconstr002.php`, `pro1_obrasconstr003.php`, `pro1_procandamint001.php`, `pro1_procandamint002.php`, `pro1_procandamint003.php`, `pro1_protparamglobal001.php`, `pro1_protparamglobal003.php`, `pro1_protprocesso001.php`, `pro1_protprocesso002.php`, `pro1_protprocesso003.php`, `pro2_relconspro002.php`, `pro3_consultaobra002_habite.php`, `pro4_capaprocesso.php`, `pro4_termorecebimento2.php`, `sys4_baixatarefa002.php`, `sys4_geradebitos003.php`, `sys4_processarelatorioRPC.php`

  </details>
- resposta vazia nos dois lados: **98**
  <details><summary>lista</summary>

  `cad1_buscaexercicio.php`, `cad4_geracarneiptutxtParcelasOpcionais.php`, `cai1_cairetordemvalida.php`, `cai1_pix002.php`, `cai4_cancelabaixabancoRPC.php`, `cai4_gerazim.php`, `cai4_importatipo001.php`, `cai4_placaixaRPC.php`, `cai4_processaconciliacao.php`, `cai4_processaconciliacao_manual.php`, `cai4_transferenciaNumpre.RPC.php`, `con1_congrupo004.php`, `con1_conplanogrupoconta004.php`, `con2_anexodemonstrativofuncaosubfuncao002.php`, `con2_planosys002.php`, `con3_versao005.php`, `con4_db_departRPC.php`, `con4_endereco.RPC.php`, `con4_geratcearqRPC.php`, `con4_importadoc001.php`, `con4_importadocpadrao001.php`, `con4_inscreverp002.php`, `con4_mensagems.RPC.php`, `con4_padbal_desp.php`, `con4_padbal_rec.php`, `con4_padbal_ver.php`, `con4_padbrec_ant.php`, `con4_padbrub_ant.php`, `con4_padbver_ant.php`, `con4_padbver_enc.php`, `con4_padbvmovant.php`, `con4_padconverterubrica.php`, `con4_padcredor.php`, `con4_padcta_disp.php`, `con4_padcta_oper.php`, `con4_paddecreto.php`, `con4_padempenho.php`, `con4_padfuncao.php`, `con4_padliquidac.php`, `con4_padorgao.php`, `con4_padpagament.php`, `con4_padprograma.php`, `con4_padprojativ.php`, `con4_padrd_extra.php`, `con4_padrec_ant.php`, `con4_padreceita.php`, `con4_padrecurso.php`, `con4_padrubrica.php`, `con4_padsubfunc.php`, `con4_padsubprog.php`, `con4_padtcelivrodiariogeral.php`, `con4_paduniorcam.php`, `con4_processaconsistencia.php`, `con4_processapad.php`, `div4_buscatipoRPC.php`, `div4_importa002.php`, `emp4_agendaPagamentoRPC.php`, `emp4_anularpagamentoRPC.php`, `emp4_gerarslipRPC.php`, `emp4_manutencaoPagamentoRPC.php`, `emp4_migracaoNotasRPC.php`, `emp4_ordemPagamentoRPC.php`, `emp4_pagarpagamentoRPC.php`, `emp4_retencaonotaRPC.php`, `iss1_ativid004.php`, `iss2_processaarquivoretencao002.php`, `iss2_relissret002.php`, `iss2_relissvariavel002.php`, `orc1_orcduplicareceita.php`, `orc2_anexo2_resudespesa002.php`, `orc2_orcldorec002.php`, `orc4_ppaRPC.php`, `pes1_rhpessoalpontoRPC.php`, `pes2_consrhfuncao002.php`, `pes2_emitebb200lay002.php`, `pes2_gerabbrasil001.php`, `pes2_guaemitebb200lay002.php`, `pes2_mppiemitearqbanco002.php`, `pes2_sapemitearqbanco002.php`, `pes2_sapemitebb200lay002.php`, `pes3_faixasSalariais002PDF.php`, `pes4_avalferia001.php`, `pes4_avaliaferiasrescisao.php`, `pes4_dadosGrupoRPC.php`, `pes4_emissaochequesRPC.php`, `pes4_geraarqmanadRPC.php`, `pes4_gerafolha003.php`, `pes4_gerafolha004.php`, `pes4_gerafolha004_calculopensao.php`, `pes4_jetomcomissaolancamento001.php`, `pes4_jetomcomissaoprocessamento001.php`, `pes4_manutencaocontratosconsignados.RPC.php`, `pro1_camposdinamicosandamentopadrao.RPC.php`, `pro4_obrashabiteRPC.php`, `sys4_cadastrotemplateRPC.php`, `sys4_consultaviewRPC.php`, `sys4_mostravariaveisdinamica.php`, `sys4_verificaclasse003.php`

  </details>
- pulada (destroi a sessao do harness): **1**
  <details><summary>lista</summary>

  `cad4_geracarneiptutxt_cli.php`

  </details>
- pulada (contata servico externo): **1**
  <details><summary>lista</summary>

  `iss4_siss002.php`

  </details>

### configuracao

IDENTICO 4977 | DIVERGE 55 | INCONCLUSIVO 461 | ERRO_AMBIENTE 9

**DIVERGE (55)**

| Caso | Grupo | Onde corrigir | Erro |
|---|---|---|---|
| `tela:sys4_listaretornosql001.php` | A1 | `sys4_listaretornosql001.php:67` | TypeError: array_keys(): Argument #1 ($x) must be of type array, null given |
| `tela:orc2_atividades002.php` | A2 | `fpdf151/fpdf.php:932` | TypeError: Unsupported operand types: int + string |
| `tela:sys4_consultaXML.RPC.php` | A3 | `sys4_consultaXML.RPC.php:39` | ValueError: Path must not be empty |
| `tela:sys4_processa004.php` | A3 | `sys4_processa004.php:111` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `tela:sys4_processa008.php` | A3 | `sys4_processa008.php:100` | TypeError: fputs(): Argument #1 ($x) must be of type resource, false given |
| `tela:con2_lrflimites002_2015.php` | A6 | `libs/db_libcontabilidade.php:5935` | TypeError: explode(): Argument #2 ($x) must be of type string, array given |
| `tela:ate1_tarefa004.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -js_OpenJanelaIframe('CurrentWindow.corpo.iframe_tarefa','db_ifr |
| `tela:ate1_tarefa006.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: -js_OpenJanelaIframe('CurrentWindow.corpo.iframe_tarefa','db_ifr |
| `tela:ate1_tarefaagenda002.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - </center> // -</form> |
| `tela:ate1_tarefalogand002.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - <select name="at48_situacao" id="at48_situacao" // - onchange= |
| `tela:ate3_consultacalendario_agenda.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - <script> // - function js_abre_agendamento(tarefa) { |
| `tela:ate4_atendsup001.php` | C1 | `` | resposta 200 nos dois lados, conteudo difere: - </b> // - </td> |
| `tela:con2_lrfanexoxvii002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfdivida002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfgarantias002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrflimites002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_lrfreceitacorrente002_2018.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2010.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2012.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_opercredito002_2015.php` | P1 | `fpdf151/pdf.php:186` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo17_002_2011.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_i_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_anexo_ii_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_balancoorcamentario_2014.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfbalorc002_2015.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:con2_lrfdemalienataplicrecursos002_2010.php` | P2 | `std/DBDate.php:203` | TypeError: checkdate(): Argument #1 ($x) must be of type int, string given |
| `tela:ate1_clientesmodulosproc002.php` | R1 | `forms/db_frmclientesmodulosproc.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate1_tarefa010.php` | R1 | `ate1_tarefa010.php:78` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate1_tarefaobs001.php` | R1 | `ate1_tarefaobs001.php:106` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate2_relatendnaolanc002.php` | R1 | `ate2_relatendnaolanc002.php:58` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate2_relatorio001.php` | R1 | `ate2_relatorio001.php:126` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate2_relclienteproced002.php` | R1 | `ate2_relclienteproced002.php:242` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate2_reltarefaagenda002.php` | R1 | `ate2_reltarefaagenda002.php:41` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate3_atendimento002.php` | R1 | `ate3_atendimento002.php:133` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate3_constarefaanexos.php` | R1 | `ate3_constarefaanexos.php:159` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate3_consultaacesso002.php` | R1 | `ate3_consultaacesso002.php:179` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate3_consultaacesso003.php` | R1 | `ate3_consultaacesso003.php:64` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate3_consultaacesso004.php` | R1 | `ate3_consultaacesso004.php:60` | TypeError: pg_result(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate4_atend002.php` | R1 | `forms/db_frmatend.php:84` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate4_pesquisatarefacod.RPC.php` | R1 | `ate4_pesquisatarefacod.RPC.php:50` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:ate4_pesquisatarefadescr.RPC.php` | R1 | `ate4_pesquisatarefadescr.RPC.php:50` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_processa002.php` | R1 | `sys4_processa002.php:66` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_processa007.php` | R1 | `sys4_processa007.php:587` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_verifica002.php` | R1 | `sys4_verifica002.php:100` | TypeError: pg_numrows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `relatorio:orc2_desppessoal002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:cai3_gerfinanc003.php` | R2 | `model/regraEmissao.model.php:88` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_anexo11_002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:con2_contasrecdesp002.php` | R2 | `libs/db_libcontabilidade.php:4989` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:orc2_desppessoal002.php` | R2 | `libs/db_libcontabilidade.php:5355` | TypeError: pg_num_rows(): Argument #1 ($x) must be of type PgSql\Result, false given |
| `tela:sys4_indices001.php` | - | - | ref=200/4407B  85=500/6672B |
| `tela:sys4_libimpmax001.php` | - | - | ref=200/7692B  85=200/4669B |

**ERRO_AMBIENTE (9)**

- `tela:con4_gerenciadortarefas002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_atualizacadastrocenso002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_atualizacadastrocenso_2009_002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_exportarsituacaoaluno002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importacaoatualizacaoaluno002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importarcodigoinep002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importarcodigoinep_2009_002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_importarmatriculainep002.php` - timeout: ref=000  85=500 (apos 1 retentativa)
- `tela:edu4_verifexportcenso002.php` - timeout: ref=000  85=200 (apos 1 retentativa)

**INCONCLUSIVO (461)**

- pagina de erro identica nos dois lados (tela nao exercitada): **357**
  <details><summary>lista</summary>

  `ate1_tarefaanexos002.php`, `cai1_autenticadora005.php`, `cai1_cadtipoparc006.php`, `cai1_caitransfseq003.php`, `cai1_extratolinha001.php`, `cai1_extratolinha002.php`, `cai1_extratolinha003.php`, `cai1_historico001.php`, `cai1_tabrec003.php`, `cai2_correceitas002.php`, `cai2_digitasaldoextratomanual.php`, `cai2_digitasaldoextratomanuallinha.php`, `cai2_guiaspagasgrm002.php`, `cai2_movimento_extra_financeiro002.php`, `cai2_receisub002.php`, `cai2_relcaixa_002.php`, `cai2_reldescontos002.php`, `cai2_saltes003.php`, `cai3_gerfinanc001.php`, `cai3_gerfinanc002.php`, `cai3_gerfinanc075.php`, `cai3_integracaotjemissao001.php`, `cai3_reemiterecibo.php`, `cai4_abreconciliacao_processa.php`, `cai4_atividadesgrm.RPC.php`, `cai4_baixabanco001_agencia_88888.php`, `cai4_baixabanco001_codcli_19985.php`, `cai4_baixabanco_daeb.php`, `cai4_cancdebitosproc001.php`, `cai4_desmembramentodisbanco001.php`, `cai4_devolucaoadiantamento002.php`, `cai4_relatorioconciliacao_manual.php`, `cai4_relatorioconciliacaomanual002_layout2.php`, `cai4_remissbob003.php`, `con1_autenticaUsuarioMobile.RPC.php`, `con1_codclass001.php`, `con1_codclass002.php`, `con1_codclass003.php`, `con1_codhist001.php`, `con1_codhist002.php`, `con1_codhist003.php`, `con1_codsistema001.php`, `con1_codsistema002.php`, `con1_codsistema003.php`, `con1_conplanorec001.php`, `con1_conplanorec002.php`, `con1_conplanorec003.php`, `con1_db_ordem003.php`, `con1_db_permemp002.php`, `con1_db_permemp003.php`, `con1_db_syscampo001.php`, `con1_db_syscampo002.php`, `con1_db_syscampo003.php`, `con1_db_tarefas001.php`, `con1_db_tarefas003.php`, `con1_db_tarefasit004.php`, `con1_tarefasit001.php`, `con1_tarefasit002.php`, `con1_tarefasit003.php`, `con2_anexo12_002.php`, `con2_anexo12_002_2008.php`, `con2_anexo12rpps_002_2008.php`, `con2_anexo13_002.php`, `con2_anexo13rpps_002.php`, `con2_anexo14_002.php`, `con2_anexo14_002_2011.php`, `con2_anexo14rpps_002.php`, `con2_anexo14rpps_002_2008.php`, `con2_anexo15ee_002.php`, `con2_anexo15lrf_002.php`, `con2_anexo15lrf_002_2011.php`, `con2_anexo17_002.php`, `con2_anexoXIII_002_2011.php`, `con2_anexoXVI_002_2011.php`, `con2_balancdespsint002.php`, `con2_balancetemsc002.php`, `con2_balanceteverificacaocontacorrente002.php`, `con2_balancofinanceiro_2014.php`, `con2_balancopatrimonial_2014.php`, `con2_balancrece002_2008.php`, `con2_balancverificacao002.php`, `con2_confdesppessoal002.php`, `con2_despesacomeducacao003.php`, `con2_despesacomsaude003.php`, `con2_estruturarel.php`, `con2_fluxodecaixa_2014.php`, `con2_imprimeseqelemento002.php`, `con2_indice_educ002.php`, `con2_lfrorcanexoii002_2008.php`, `con2_lfrorcanexoii002_2010.php`, `con2_lrfbalorc002_2008.php`, `con2_lrfbalorc002_2010.php`, `con2_lrfbalorc002_2012.php`, `con2_lrfdemdisponibcaixa002_2010.php`, `con2_lrfdemonstrativorp002_2008.php`, `con2_lrfdesppessoal002.php`, `con2_lrfdesppessoal002_2007.php`, `con2_lrfdesppessoal002_2008.php`, `con2_lrfdesppessoal002_2009.php`, `con2_lrfdesppessoal002_2010.php`, `con2_lrfdesppessoal002_2011.php`, `con2_lrfdesppessoal002_2015.php`, `con2_lrfdispcaixa002.php`, `con2_lrfdivida002.php`, `con2_lrfdivida002_2008.php`, `con2_lrfdivida002_2009.php`, `con2_lrfgarantias002.php`, `con2_lrfgarantias002_2008.php`, `con2_lrfgarantias002_2009.php`, `con2_lrfimpostossaude002.php`, `con2_lrfimpostossaude002_2009.php`, `con2_lrfimpostossaude002_2013.php`, `con2_lrflimites002.php`, `con2_lrflimites002_2008.php`, `con2_lrflimites002_2009.php`, `con2_lrfmdefundeb0001.php`, `con2_lrfmdefundeb001.php`, `con2_lrfnominal002.php`, `con2_lrfnominal002_2009.php`, `con2_lrfprimario002.php`, `con2_lrfprimario002_2008.php`, `con2_lrfprimario002_2010.php`, `con2_lrfprimario002_2015.php`, `con2_lrfrecdesprpps002_2009.php`, `con2_lrfreceitacorrente002.php`, `con2_lrfreceitacorrente002_2008.php`, `con2_lrfreceitacorrente002_2009.php`, `con2_lrfreceitacorrente002_var.php`, `con2_lrfresumido002.php`, `con2_lrfresumido002_2007.php`, `con2_lrfresumido002_2008.php`, `con2_lrfresumido002_2009.php`, `con2_lrfresumido002_2015.php`, `con2_lrfresumido002_2018.php`, `con2_lrfrgfdemrestosapagar002_2010.php`, `con2_opercredito002.php`, `con2_opercredito002_2008.php`, `con2_opercredito002_2009.php`, `con2_razaocontas002.php`, `con2_razaoporcontas003.php`, `con2_rec_desp_extra_002.php`, `con2_relatoriosiconfi011.php`, `con2_reledital004.php`, `con2_variacoespatrimoniais_2014.php`, `con2_varpatrimoniaisrpps_002_2008.php`, `con3_conscontri008.php`, `con3_db_syscampo004.php`, `con4_boletim004.php`, `con4_consacordos003.php`, `con4_parametrosrelatorioslegais001.php`, `con4_processaaberturaexercicio.RPC.php`, `con4_registrasistema.php`, `con4_trabalhos001.php`, `con4_viradadeano002_item001.php`, `con4_viradadeano002_item002.php`, `con4_viradadeano002_item003.php`, `con4_viradadeano002_item004.php`, `con4_viradadeano002_item005.php`, `con4_viradadeano002_item006.php`, `con4_viradadeano002_item007.php`, `con4_viradadeano002_item008.php`, `con4_viradadeano002_item009.php`, `con4_viradadeano002_item010.php`, `con4_viradadeano002_item011.php`, `con4_viradadeano002_item012.php`, `con4_viradadeano002_item013.php`, `con4_viradadeano002_item014.php`, `con4_viradadeano002_item015.php`, `con4_viradadeano002_item016.php`, `con4_viradadeano002_item017.php`, `con4_viradadeano002_item018.php`, `con4_viradadeano002_item019.php`, `con4_viradadeano002_item020.php`, `con4_viradadeano002_item021.php`, `con4_viradadeano002_item022.php`, `con4_viradadeano002_item023.php`, `con4_viradadeano002_item024.php`, `con4_viradadeano002_item025.php`, `con4_viradadeano002_item026.php`, `con4_viradadeano002_item027.php`, `con4_viradadeano002_item028.php`, `con4_viradadeano002_item029.php`, `con4_viradadeano002_item030.php`, `con4_viradadeano002_item031.php`, `con4_viradadeano002_item032.php`, `con4_viradadeano002_item033.php`, `con4_viradadeano002_item034.php`, `con4_viradadeano002_item035.php`, `con4_viradadeano002_item036.php`, `con6_andamentolista.php`, `con6_ordemagendamento002.php`, `con6_ordemandamento002.php`, `con7_ordemandamento002.php`, `edu1_aprovconselho002.php`, `edu1_atividaderh002.php`, `edu1_atividaderh003.php`, `edu1_atoescola002.php`, `edu1_atoescola003.php`, `edu1_avalcompoeres002.php`, `edu1_avalcompoeres003.php`, `edu1_calendarioescola002.php`, `edu1_calendarioescola003.php`, `edu1_dialetivo002.php`, `edu1_dialetivo003.php`, `edu1_diarioavaliacao001.php`, `edu1_diarioavaliacaoobs001.php`, `edu1_diariofinal001.php`, `edu1_diariofinalcalcfreq001.php`, `edu1_disciplina002.php`, `edu1_disciplina003.php`, `edu1_docaluno002.php`, `edu1_docaluno003.php`, `edu1_encerraraval001.php`, `edu1_escolabase002.php`, `edu1_escolabase003.php`, `edu1_feriado001.php`, `edu1_feriado002.php`, `edu1_feriado003.php`, `edu1_grauensino001.php`, `edu1_grauensino002.php`, `edu1_grauensino003.php`, `edu1_matriculadependecia002.php`, `edu1_matriculadependecia003.php`, `edu1_parametrodependencia002.php`, `edu1_parametrodependencia003.php`, `edu1_pareceraval003.php`, `edu1_parecerresult002.php`, `edu1_parecerresult003.php`, `edu1_parecerturma003.php`, `edu1_periodocalendario002.php`, `edu1_periodocalendario003.php`, `edu1_procescola002.php`, `edu1_procescola003.php`, `edu1_rechumanoescola002.php`, `edu1_rechumanoescola003.php`, `edu1_rechumanohoradisp003.php`, `edu1_regencia003.php`, `edu1_regenciahorario001.php`, `edu1_serieequiv002.php`, `edu1_serieequiv003.php`, `edu1_telefoneescola002.php`, `edu1_telefoneescola003.php`, `edu1_transfescolafora002.php`, `edu1_transfescolarede002.php`, `edu1_turno002.php`, `edu1_turno003.php`, `edu2_atamatricula002.php`, `edu2_ataresultadofinal002.php`, `edu2_ataresultadofinal003.php`, `edu2_atestadofrequencia002.php`, `edu2_avaliacoesperiodo003.php`, `edu2_avaliacoesperiodo004.php`, `edu2_boletim003.php`, `edu2_calendario002.php`, `edu2_declaracaoanosatuais002.php`, `edu2_declaracaoexalunos002.php`, `edu2_declaracaomatricula002.php`, `edu2_diarioclasseconteudodesenvolvido002.php`, `edu2_diarioclasseconteudodesenvolvido002_2019.php`, `edu2_diarioclassenovo002.php`, `edu2_diarioclasseprogressaoparcial002.php`, `edu2_encaminhamentotransferencia002.php`, `edu2_fichaacompanhamento002.php`, `edu2_fichaqualitativa002.php`, `edu2_mapadefrequencia002.php`, `edu2_pardescritivonota002.php`, `edu2_pardescritivonota003.php`, `edu2_registroclasse002.php`, `edu2_relacaonominal002.php`, `edu2_resumoaprovnovo002.php`, `edu3_consultaaluno002.php`, `edu3_consultafuncaoexercida003.php`, `edu3_professorescola003.php`, `edu4_atestadovagafora002.php`, `edu4_notasparciais002.php`, `edu4_notasparciais003.php`, `edu4_notasparciais004.php`, `mat1_matestoque_arq.php`, `mat1_matestoque_arqnota.php`, `mat1_matestoqueitemlancconf_iframe.php`, `mat2_inventariofisicocontabil002.php`, `mat4_processararquivopit002.php`, `mat_aviso_deposito.php`, `orc1_orcparamrelopcre002.php`, `orc1_orcparamrelopcre003.php`, `orc1_orcppa006.php`, `orc1_orcsuplem005.php`, `orc1_tiporec001.php`, `orc1_tiporec002.php`, `orc1_tiporec003.php`, `orc2_DemRiscosFiscaisProvidencias.php`, `orc2_EstimativaRenunciaReceita002.php`, `orc2_MargemDespesasCaraterContinuado.php`, `orc2_ReceitasDespesasPrevidenciariasServidores.php`, `orc2_acompanhamentocronograma001.php`, `orc2_anexo8002.php`, `orc2_anexodividapublica002.php`, `orc2_anexodotacaogoverno002.php`, `orc2_anexoorcamentofiscal002.php`, `orc2_anexoreceitacorrenteliquida002.php`, `orc2_anexoseguridadesocial002.php`, `orc2_anexosumrecfontesdespfuncaogov002.php`, `orc2_anexotrabalhogoverno002.php`, `orc2_demManutencaoDesenvolvimentoEnsino002.php`, `orc2_demreceitasdespesassaude002.php`, `orc2_despsecretaria002.php`, `orc2_estimativaRenunciaReceita002.php`, `orc2_orcprevmensaldesp002.php`, `orc2_ppaevolucaodemostrativoreceita002.php`, `orc2_recppa002.php`, `orc2_recursorecdesp002.php`, `orc2_reldespesas002.php`, `orc2_reldespesas002txt.php`, `orc2_totaliza002.php`, `orc4_duplicaorcamento001.php`, `orc4_duplicaorcamentorec001.php`, `orc4_ppadotacaoelementos004.php`, `orc4_resumogeralprevreceita002.php`, `pat1_bens006.php`, `pat1_bensconsulta002.php`, `pat2_histbem002.php`, `pat4_criteriumexportaarquivos002_bem.php`, `pat4_criteriumexportaarquivos002_ccusto.php`, `pat4_criteriumexportaarquivos002_empresa.php`, `pat4_criteriumexportaarquivos002_especie.php`, `pat4_criteriumexportaarquivos002_estado.php`, `pat4_criteriumexportaarquivos002_familia.php`, `pat4_criteriumexportaarquivos002_fornecedor.php`, `pat4_criteriumexportaarquivos002_historico.php`, `pat4_criteriumexportaarquivos002_localizacao.php`, `pat4_criteriumexportaarquivos002_marcas.php`, `pat4_criteriumexportaarquivos002_medida.php`, `pat4_criteriumexportaarquivos002_modelo.php`, `pat4_criteriumexportaarquivos002_ocorrencia.php`, `pat4_criteriumexportaarquivos002_parametros.php`, `pat4_criteriumexportaarquivos002_setor.php`, `pat4_criteriumexportaarquivos002_usuario.php`, `pro1_cgmdoc002.php`, `pro1_cgmdoc003.php`, `pro1_obras004.php`, `pro1_obrasconstr002.php`, `pro1_obrasconstr003.php`, `pro1_procandamint001.php`, `pro1_procandamint002.php`, `pro1_procandamint003.php`, `pro1_protparamglobal001.php`, `pro1_protparamglobal003.php`, `pro1_protprocesso001.php`, `pro1_protprocesso002.php`, `pro1_protprocesso003.php`, `pro2_relconspro002.php`, `pro3_consultaobra002_habite.php`, `pro4_capaprocesso.php`, `pro4_termorecebimento2.php`, `sys4_baixatarefa002.php`, `sys4_geradebitos003.php`, `sys4_processarelatorioRPC.php`

  </details>
- resposta vazia nos dois lados: **103**
  <details><summary>lista</summary>

  `ate3_calendarioimplanta003.php`, `ate4_tarefaagenda.RPC.php`, `ate4_tarefas.RPC.php`, `cai1_cairetordemvalida.php`, `cai1_pix002.php`, `cai4_cancelabaixabancoRPC.php`, `cai4_gerazim.php`, `cai4_importatipo001.php`, `cai4_placaixaRPC.php`, `cai4_processaconciliacao.php`, `cai4_processaconciliacao_manual.php`, `cai4_transferenciaNumpre.RPC.php`, `con1_congrupo004.php`, `con1_conplanogrupoconta004.php`, `con2_anexodemonstrativofuncaosubfuncao002.php`, `con2_planosys002.php`, `con3_versao005.php`, `con4_db_departRPC.php`, `con4_endereco.RPC.php`, `con4_geratcearqRPC.php`, `con4_importadoc001.php`, `con4_importadocpadrao001.php`, `con4_inscreverp002.php`, `con4_mensagems.RPC.php`, `con4_padbal_desp.php`, `con4_padbal_rec.php`, `con4_padbal_ver.php`, `con4_padbrec_ant.php`, `con4_padbrub_ant.php`, `con4_padbver_ant.php`, `con4_padbver_enc.php`, `con4_padbvmovant.php`, `con4_padconverterubrica.php`, `con4_padcredor.php`, `con4_padcta_disp.php`, `con4_padcta_oper.php`, `con4_paddecreto.php`, `con4_padempenho.php`, `con4_padfuncao.php`, `con4_padliquidac.php`, `con4_padorgao.php`, `con4_padpagament.php`, `con4_padprograma.php`, `con4_padprojativ.php`, `con4_padrd_extra.php`, `con4_padrec_ant.php`, `con4_padreceita.php`, `con4_padrecurso.php`, `con4_padrubrica.php`, `con4_padsubfunc.php`, `con4_padsubprog.php`, `con4_padtcelivrodiariogeral.php`, `con4_paduniorcam.php`, `con4_processaconsistencia.php`, `con4_processapad.php`, `edu1_aluno.RPC.php`, `edu1_aluno004.php`, `edu1_baseRPC.php`, `edu1_baseatoRPC.php`, `edu1_calendario004.php`, `edu1_cursoatoRPC.php`, `edu1_efetividaderhRPC.php`, `edu1_escola004.php`, `edu1_escolaproc004.php`, `edu1_matricula007.php`, `edu1_ordenacaoniveisensinoRPC.php`, `edu1_periodocalendario004.php`, `edu1_procedimento004.php`, `edu1_rechumano004.php`, `edu1_rechumanoRPC.php`, `edu1_rechumanohoradisp002.php`, `edu1_rechumanohorario002.php`, `edu1_regencia002.php`, `edu1_relacaotrabalhoRPC.php`, `edu1_serieordenacaoRPC.php`, `edu1_turma004.php`, `edu1_turmaRPC.php`, `edu1_turmaac004.php`, `edu2_gfcoaprovalugeral002.php`, `edu2_gfcoaprovaluno002.php`, `edu2_gfcoaprovturgeral002.php`, `edu2_gfcoaprovturma002.php`, `edu2_gfcoescfreqseries002.php`, `edu2_gfcofreqaluno002.php`, `edu2_gfcofreqturma002.php`, `edu2_necessidadeEspecial.RPC.php`, `edu3_diarioclasse002.php`, `edu3_rechumanohorario002.php`, `mat1_lancaitens.php`, `mat4_atendsolicitacaoRPC.php`, `mat4_matordemRPC.php`, `mat4_requisicaoRPC.php`, `orc1_orcduplicareceita.php`, `orc2_anexo2_resudespesa002.php`, `orc2_orcldorec002.php`, `orc4_ppaRPC.php`, `pat1_retseqplaca.php`, `pro1_camposdinamicosandamentopadrao.RPC.php`, `pro4_obrashabiteRPC.php`, `sys4_cadastrotemplateRPC.php`, `sys4_consultaviewRPC.php`, `sys4_mostravariaveisdinamica.php`, `sys4_verificaclasse003.php`

  </details>
- pulada (destroi a sessao do harness): **1**
  <details><summary>lista</summary>

  `edu4_informacoesdump.php`

  </details>

## 3. O que e o INCONCLUSIVO e por que ele importa

- **Pagina de erro identica nos dois lados (a maioria):** a tela abriu, mas mostrou a mesma mensagem de erro/aviso no 7.4 e no 8.5 (tipicamente por falta de parametro ou porque a tela exige um fluxo de varios passos; nao verifiquei caso a caso). Como nenhum dos dois lados executou a regra de negocio, nao da para dizer se o 8.5 esta correto. Para ter veredito e preciso um teste com dados validos (preencher o formulario ou usar o fluxo do navegador).
- **Resposta vazia nos dois lados:** a tela devolveu 0 bytes (normalmente um `exit`/redirect logo no inicio). Mesma conclusao.
- **Pulada:** telas que destroem a sessao do teste (`edu4_informacoesdump.php`, `cad4_geracarneiptutxt_cli.php`) ou contatam servico externo (`iss4_siss002.php`). Nao foram executadas.
- Em resumo: **INCONCLUSIVO nao e aprovado.** Sao telas que a bateria automatica nao consegue julgar; o migrador deve testa-las a mao quando alterar o codigo delas.

## 4. Observacoes

- 1 caso DIVERGE da rodada passou ao reexecutar (resposta identica nos dois lados) e por isso nao aparece com causa; esta marcado sem grupo. Em 61 linhas da planilha de causas, a resposta do 7.4 muda entre duas leituras (data/hora no PDF); o 8.5 tambem falha nelas e a coluna 'Est.' do documento de entrega informa quais.
- `financeiro` e `configuracao` foram medidas na mesma rodada, as ultimas a terminar (03:07 e 04:59).
- Para refazer uma area: `cd regressao && .venv/bin/python -m regressao.php.bateria --saida ~/rodadas/x/<area> --area <area> --pular sintaxe --pular classes`.

