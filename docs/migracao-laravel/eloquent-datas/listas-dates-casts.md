## $dates (21 models)

| arquivo:linha | atributos |
|---|---|
| app/Domain/Configuracao/Departamento/Models/Departamento.php:66 | limite |
| app/Domain/Educacao/CentralMatriculas/Models/ObservacaoInscricao.php:53 | created_at, updated_at, deleted_at |
| app/Domain/Educacao/Escola/Models/Aluno.php:98 | ed47_d_cadast, ed47_d_dtemissao, ed47_d_dthabilitacao, ed47_d_dtvencimento, ed47_d_nasc, ed47_d_ultalt, ed47_d_identdtexp |
| app/Domain/Educacao/Escola/Models/AtividadeProfissionalEscola.php:11 | ed22_datainicio, ed22_datafim |
| app/Domain/Educacao/Escola/Models/Calendario.php:34 | ed52_d_inicio, ed52_d_fim, ed52_d_resultfinal |
| app/Domain/Educacao/Escola/Models/ExcecaoBloqueioNota.php:26 | ed363_datalimite |
| app/Domain/Educacao/Escola/Models/Matricula.php:39 | ed60_d_datamatricula, ed60_d_datasaida |
| app/Domain/Educacao/Escola/Models/ProfissionalEscola.php:12 | ed75_d_ingresso, ed75_i_saidaescola |
| app/Domain/Educacao/MatriculaOnline/Models/Alocado.php:12 | mo13_data |
| app/Domain/Educacao/MatriculaOnline/Models/Candidato.php:46 | mo01_datacad, mo01_dtnasc |
| app/Domain/Educacao/MatriculaOnline/Models/Ciclo.php:21 | mo09_dtcad |
| app/Domain/Educacao/MatriculaOnline/Models/Fase.php:33 | mo04_datacorte, mo04_dtfim, mo04_dtini |
| app/Domain/Financeiro/Contabilidade/Models/ApropriacaoDecimoFerias.php:31 | pl2_created_at, pl2_updated_at |
| app/Domain/Financeiro/Contabilidade/Models/ApropriacaoDecimoFeriasLancamentos.php:24 | pl2_created_at, pl2_updated_at |
| app/Domain/Financeiro/Contabilidade/Models/EncerramentoPeriodoContabil.php:18 | c99_data |
| app/Domain/Financeiro/Contabilidade/Models/Lancamento.php:30 | c70_data |
| app/Domain/Financeiro/Contabilidade/Models/ParametroIntegracaoPatrimonial.php:13 | c01_data |
| app/Domain/Financeiro/Orcamento/Models/Recurso.php:35 | o15_datalimite |
| app/Domain/Financeiro/Planejamento/Models/Planejamento.php:41 | pl2_created_at, pl2_updated_at |
| app/Domain/Financeiro/Tesouraria/Models/Slip.php:14 | k17_data, k17_dtaut, k17_dtanu, k17_dtestorno |
| app/Domain/Saude/Farmacia/Models/BnafarBatchProtocolo.php:22 | fa76_created_at |

## $casts de data (20 models)

| arquivo:linha | atributo => tipo |
|---|---|
| app/Domain/Assinador/CertificadoUsuario.php:21 | c142_data => DateTime, c142_validade => DateTime |
| app/Domain/Configuracao/Usuario/Models/Usuario.php:77 | datatoken => datetime, dataexpira => datetime |
| app/Domain/Patrimonial/Patrimonio/Models/Bem.php:34 | t52_dtaqu => datetime, t52_dtinlcusao => datetime |
| app/Domain/Patrimonial/Patrimonio/Models/BemPlaca.php:23 | t41_data => datetime |
| app/Domain/Saude/Ambulatorial/Models/ProblemaPaciente.php:32 | s170_data => datetime, s170_data_inicio => datetime, s170_data_fim => datetime |
| app/Domain/Saude/Ambulatorial/Models/ProcedimentoProntuario.php:31 | sd29_d_data => datetime, sd29_d_cadastro => datetime |
| app/Domain/Saude/Ambulatorial/Models/Profissional.php:26 | sd03_d_folgaini => datetime, sd03_d_folgafim => datetime |
| app/Domain/Saude/Ambulatorial/Models/ProfissionalUnidade.php:35 | sd04_d_folgaini => datetime, sd04_d_folgafim => datetime |
| app/Domain/Saude/Ambulatorial/Models/Prontuario.php:52 | sd24_d_cadastro => datetime, sd24_dum => datetime |
| app/Domain/Saude/Ambulatorial/Models/Unidade.php:44 | sd02_d_data_exped => datetime |
| app/Domain/Saude/ESF/Models/CadastroIndividual.php:136 | psf5_profissional_data => datetime, psf5_nascimento_responsavel => datetime, psf5_data_naturalizacao => datetime, psf5_data_entrada => datetime, psf5_data_obito => datetime |
| app/Domain/Saude/ESF/Models/Equipe.php:28 | psf_data_ativacao => datetime, psf_data_desativacao => datetime |
| app/Domain/Saude/ESF/Models/ProfissionalEquipe.php:23 | psf2_data_ativacao => datetime, psf2_data_desativacao => datetime |
| app/Domain/Saude/ESF/Models/ProntuarioEsf.php:25 | sd30_d_data_atendimento => datetime |
| app/Domain/Saude/Farmacia/Models/BnafarBatchProtocolo.php:23 | fa76_created_at => datetime |
| app/Domain/Saude/Farmacia/Models/BnafarConferencia.php:19 | fa72_data => datetime |
| app/Domain/Saude/Farmacia/Models/BnafarEnvio.php:26 | fa70_data => datetime |
| app/Domain/Saude/Farmacia/Models/DemandaReprimida.php:31 | fa67_data_hora => datetime |
| app/Domain/Tributario/ISSQN/Model/Base/IssAlvara.php:26 | q123_dtinclusao => date |
| app/Domain/Tributario/ISSQN/Model/Base/IssMovAlvara.php:26 | q120_dtmov => date |
