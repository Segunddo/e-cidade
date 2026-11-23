# Cobertura de rotas (Laravel)

Rotas no inventario: **1434**.

| origem | total | cobertas | nao cobertas |
|---|---:|---:|---:|
| laravel | 1423 | 964 | 459 |
| rest | 4 | 0 | 4 |
| silex | 7 | 5 | 2 |

## Resposta da referencia (Laravel 8) nas rotas cobertas

2xx: 250  3xx: 0  4xx: 452  5xx: 267  sem baseline: 0

**5xx na referencia: 267.** Rota quebrada ou que precisa de dados em dev; o caso e IDENTICO nos dois lados mas termina INCONCLUSIVO (500 x 500): a rota nao foi exercitada, so o seu roteamento/erro. Lista:

- `rota:POST:/v4/api/configuracao/assinantes`
- `rota:GET:/v4/api/configuracao/bancos`
- `rota:POST:/v4/api/configuracao/documento-assinado`
- `rota:GET:/v4/api/configuracao/documentos-assinar/assinante`
- `rota:POST:/v4/api/configuracao/documentos-assinar/atualizar-assinado-por`
- `rota:POST:/v4/api/configuracao/documentos-assinar/atualizar-assinantes`
- `rota:POST:/v4/api/configuracao/documentos-assinar/novo-documento`
- `rota:GET:/v4/api/configuracao/gerador/relatorios/create`
- `rota:POST:/v4/api/configuracao/gerador/relatorios/novo`
- `rota:POST:/v4/api/configuracao/jobs`
- `rota:GET:/v4/api/configuracao/jobs/create`
- `rota:POST:/v4/api/configuracao/jobs/failed`
- `rota:POST:/v4/api/configuracao/organograma/filtrar`
- `rota:POST:/v4/api/configuracao/relatorios-legais/upload/template`
- `rota:GET:/v4/api/configuracao/usuario/assinantes`
- `rota:POST:/v4/api/dbpref/dbpref-pix/validar`
- `rota:POST:/v4/api/educacao/censo/tabelas-censo/unidades-curriculares/salvar`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/campos-opcionais`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/configuracoes-gerais`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/cores`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/documentos`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/imagens`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/mensagens`
- `rota:GET:/v4/api/educacao/central-de-matriculas/configuracoes/noticias`
- `rota:GET:/v4/api/educacao/central-de-matriculas/etapas-lista-espera`
- `rota:GET:/v4/api/educacao/central-de-matriculas/listas-impedidas`
- `rota:GET:/v4/api/educacao/central-de-matriculas/processo-inscricao/cor-raca`
- `rota:GET:/v4/api/educacao/central-de-matriculas/processo-inscricao/escolas-origem`
- `rota:GET:/v4/api/educacao/central-de-matriculas/processo-inscricao/escolas-por-bairro`
- `rota:POST:/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao`
- `rota:GET:/v4/api/educacao/central-de-matriculas/processo-inscricao/redes-origem`
- `rota:GET:/v4/api/educacao/central-de-matriculas/processo-inscricao/tem-fase-abeta`
- `rota:POST:/v4/api/educacao/escola/alunoAtendimentosEspecial/atualizar`
- `rota:POST:/v4/api/educacao/escola/alunoAtendimentosEspecial/edita-recursos`
- `rota:POST:/v4/api/educacao/escola/alunoAtendimentosEspecial/salva-recursos`
- `rota:POST:/v4/api/educacao/escola/alunoAtendimentosEspecial/save`
- `rota:POST:/v4/api/educacao/escola/alunoAtendimentosespecial/atendimentos`
- `rota:POST:/v4/api/educacao/escola/alunos/historicos-alunos-transf-fora`
- `rota:POST:/v4/api/educacao/escola/avaliacaoparcial/salvar-formaobtencao`
- `rota:POST:/v4/api/educacao/escola/bases-curriculares/disciplinas/salvar`
- `rota:POST:/v4/api/educacao/escola/bases-curriculares/salvar`
- `rota:POST:/v4/api/educacao/escola/bases-curriculares/salvarBaseContinuacao`
- `rota:GET:/v4/api/educacao/escola/diario-classe/registro-aula/get-conteudos-regente-escola`
- `rota:GET:/v4/api/educacao/escola/diario-classe/registro-aula/get-habilidades-bncc`
- `rota:POST:/v4/api/educacao/escola/diario-classe/registro-aula/salvar-conteudo`
- `rota:POST:/v4/api/educacao/escola/diario-classe/registro-aula/salvar-habilidade-desenvolvida`
- `rota:POST:/v4/api/educacao/escola/diario-classe/registro-aula/update-conteudos-lote`
- `rota:POST:/v4/api/educacao/escola/etapas/etapas-intervalo`
- `rota:POST:/v4/api/educacao/escola/notas-parciais/periodo`
- `rota:GET:/v4/api/educacao/escola/profissionais-geral`
- `rota:POST:/v4/api/educacao/escola/recursos-humanos/buscar-documento-pos-graducao`
- `rota:POST:/v4/api/educacao/escola/recursos-humanos/salvar-documento-pos-graducao`
- `rota:POST:/v4/api/educacao/escola/regencia/adicionar-avaliacoes-periodo`
- `rota:POST:/v4/api/educacao/escola/regencia/avaliacoes-periodo`
- `rota:POST:/v4/api/educacao/escola/relatorios/ata-resultados-finais-siga`
- `rota:POST:/v4/api/educacao/escola/relatorios/emitirRelatorioTurmasAee`
- `rota:POST:/v4/api/educacao/escola/relatorios/espelho-anual`
- `rota:POST:/v4/api/educacao/escola/relatorios/espelho-periodo`
- `rota:POST:/v4/api/educacao/escola/resultado-parcial/fechar-todos`
- `rota:POST:/v4/api/educacao/escola/resultado-parcial/reabrir-todos`
- `rota:POST:/v4/api/educacao/escola/tipoausencia/ausencia`
- `rota:POST:/v4/api/educacao/escola/transposicao/aluno-designado`
- `rota:POST:/v4/api/educacao/escola/transposicao/matriculas-designados`
- `rota:POST:/v4/api/educacao/escola/transposicao/relatorio`
- `rota:POST:/v4/api/educacao/escola/transposicao/salvar-candidatos`
- `rota:POST:/v4/api/educacao/escola/transposicao/salvar-criterios-ordenacao`
- `rota:POST:/v4/api/educacao/escola/transposicao/toggle`
- `rota:POST:/v4/api/educacao/escola/transposicao/vagas`
- `rota:POST:/v4/api/educacao/escola/transposicao/vagas-etapa`
- `rota:POST:/v4/api/educacao/escola/turmas/usuario`
- `rota:GET:/v4/api/educacao/matricula-online/configuracoes/parametros-notificacoes/getParametros`
- `rota:POST:/v4/api/educacao/matricula-online/configuracoes/parametros-notificacoes/salvar`
- `rota:POST:/v4/api/educacao/secretaria/cursos/salvar`
- `rota:POST:/v4/api/educacao/secretaria/parametros/bloqueio-notas/salvar`
- `rota:POST:/v4/api/educacao/secretaria/parametros/notificacoes`
- `rota:POST:/v4/api/educacao/secretaria/relatorios/alunos/alunos-estrangeiros`
- `rota:POST:/v4/api/educacao/secretaria/relatorios/funcionarios-ativos-escola`
- `rota:GET:/v4/api/educacao/secretaria/relatorios/funcoes-atividades`
- `rota:POST:/v4/api/educacao/secretaria/tipos-insturmentos-avaliativos/salvar`
- `rota:POST:/v4/api/financeiro/contabilidade/consulta/lancamento/conta-pcasp/documentos`
- `rota:POST:/v4/api/financeiro/contabilidade/consulta/lancamento/conta-pcasp/info`
- `rota:POST:/v4/api/financeiro/contabilidade/consulta/lancamento/conta-pcasp/recursos`
- `rota:POST:/v4/api/financeiro/contabilidade/conta-corrente/cadastro/configurarSaldoInicialPorRecurso`
- `rota:GET:/v4/api/financeiro/contabilidade/conta-corrente/cadastro/verificaExistenciaExeContaCorrente`
- `rota:POST:/v4/api/financeiro/contabilidade/deliberacao/285/modelo-5`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/ajuste-saldo-contas-msc`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/gera-csv-ajuste-saldo-contas`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/lancamento/conlancamrecurso`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/lancamento/contas-bancarias`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/lancamento/criar-recurso`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/lancamento/documento-142`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/lancamento/estoque-patrimonio`
- `rota:POST:/v4/api/financeiro/contabilidade/fix/lancamento/recurso-empenho`
- `rota:GET:/v4/api/financeiro/contabilidade/historico`
- `rota:POST:/v4/api/financeiro/contabilidade/lancamento-manual`
- `rota:GET:/v4/api/financeiro/contabilidade/lancamento-manual/nota-lancamento`
- `rota:POST:/v4/api/financeiro/contabilidade/lancamento-manual/retificar`
- `rota:POST:/v4/api/financeiro/contabilidade/msc/emitir`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/consulta/orcamentario/despesa/ecidade`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/consulta/orcamentario/receita/ecidade`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/emitir/orcamentario/despesa/mapeamento`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/emitir/orcamentario/receita/mapeamento`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/orcamentario/despesa/vincular`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/orcamentario/receita/vincular`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/orcamentario/receita/vinculo-geral`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/pcasp/editar-estruturais`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/pcasp/salvar-conta-bancaria`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/pcasp/salvar-conta-caixa`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/pcasp/salvar-conta-extra`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/pcasp/salvar-outras-contas`
- `rota:POST:/v4/api/financeiro/contabilidade/plano-contas/pcasp/vincular`
- `rota:POST:/v4/api/financeiro/contabilidade/procedimento/mapeamento-empenho-rp-manual`
- `rota:POST:/v4/api/financeiro/contabilidade/relatorio-legal/emissao/publicar`
- `rota:GET:/v4/api/financeiro/contabilidade/relatorio-legal/emissoes`
- `rota:POST:/v4/api/financeiro/contabilidade/relatorio/atributos-plano-conas`
- `rota:POST:/v4/api/financeiro/contabilidade/relatorio/balancete-receita-plano-padrao`
- `rota:POST:/v4/api/financeiro/contabilidade/relatorio/balancete-receita-por-complemento`
- `auth-sem-token`
- `rota:GET:/v4/api/financeiro/empenho/empenhos/dialog-pesquisa`
- `rota:POST:/v4/api/financeiro/empenho/relatorio/relatorio-subcontratacao`
- `rota:POST:/v4/api/financeiro/empenho/relatorio/retencoesEfdReinf`
- `rota:GET:/v4/api/financeiro/orcamento/buscar-filtros-dotacoes`
- `rota:POST:/v4/api/financeiro/orcamento/cadastro/complemento/salvar`
- `rota:GET:/v4/api/financeiro/orcamento/despesa/dotacoes`
- `rota:GET:/v4/api/financeiro/orcamento/despesa/naturezas-despesas`
- `rota:GET:/v4/api/financeiro/orcamento/receita/natureza-receita`
- `rota:GET:/v4/api/financeiro/orcamento/receita/receitas`
- `rota:GET:/v4/api/financeiro/orcamento/recursos/byFilters`
- `rota:GET:/v4/api/financeiro/orcamento/recursos/confere-vinculo`
- `rota:POST:/v4/api/financeiro/orcamento/relatorios/anexo-2-receita`
- `rota:POST:/v4/api/financeiro/orcamento/relatorios/anexo-3`
- `rota:POST:/v4/api/financeiro/orcamento/relatorios/cotas-despesa`
- `rota:POST:/v4/api/financeiro/orcamento/relatorios/meta-arrecadacao`
- `rota:POST:/v4/api/financeiro/orcamento/relatorios/meta-x-cotas`
- `rota:POST:/v4/api/financeiro/orcamento/relatorios/siconfi-recursos-2022`
- `rota:POST:/v4/api/financeiro/planejamento/configuracao/salvar`
- `rota:POST:/v4/api/financeiro/planejamento/despesa/cronograma/buscar`
- `rota:POST:/v4/api/financeiro/planejamento/iniciativa-vincular-objetivo/buscar`
- `rota:POST:/v4/api/financeiro/planejamento/iniciativa-vincular-objetivo/vincular`
- `rota:POST:/v4/api/financeiro/planejamento/pib`
- `rota:GET:/v4/api/financeiro/planejamento/programas-estrategico`
- `rota:POST:/v4/api/financeiro/planejamento/programas-estrategico/salvar`
- `rota:POST:/v4/api/financeiro/planejamento/projecao/despesa/atualizar/valor-exercicio`
- `rota:POST:/v4/api/financeiro/planejamento/projecao/receita/atualizar/valor-exercicio`
- `rota:POST:/v4/api/financeiro/planejamento/receita/cronograma/buscar`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/acompanhamento-ppa-ldo`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/cotas-despesa`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/planejamento-por-recurso`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/por-elemento`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/programa-estrategico`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/programa-gestao`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/projecao-despesa-agrupado`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/projecao-despesa-agrupado-sintetico`
- `rota:POST:/v4/api/financeiro/planejamento/relatorios/projecao-despesa-conferencia-recurso`
- `rota:POST:/v4/api/financeiro/tesouraria/decendio/gerar-slips`
- `rota:POST:/v4/api/financeiro/tesouraria/decendio/relatorio`
- `rota:POST:/v4/api/financeiro/tesouraria/decendio/tipo-desdobramento`
- `rota:POST:/v4/api/financeiro/tesouraria/relatorio/ExtratoContaBancaria`
- `rota:POST:/v4/api/financeiro/tesouraria/slip/cobertura-recurso-extra/gerar`
- `rota:POST:/v4/api/integracoes/efd-reinf/configuracao/save`
- `rota:GET:/v4/api/integracoes/efd-reinf/retencao/get-retencoes`
- `rota:POST:/v4/api/integracoes/efd-reinf/retencao/save-retencao`
- `rota:POST:/v4/api/patrimonial/contratos/enviar-evento-automatico`
- `rota:POST:/v4/api/patrimonial/licitacoes/itensBloqueados`
- `rota:GET:/v4/api/patrimonial/licitacoes/licitacon/obras/detalhamento-caracteristicas`
- `rota:GET:/v4/api/patrimonial/licitacoes/licitacon/obras/familias`
- `rota:POST:/v4/api/patrimonial/patrimonio/relatorio/transferencia-bens-aberto`
- `rota:POST:/v4/api/patrimonial/pncp/ataRegistroPreco/buscar`
- `rota:POST:/v4/api/patrimonial/pncp/ataRegistroPreco/incluir`
- `rota:POST:/v4/api/patrimonial/pncp/ataRegistroPreco/retificar`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/buscar-documentos`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/buscarAmparosLegais`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/buscarEditais`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/buscarLicitacao`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/buscarModoDisputa`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/buscarSolicitacao`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/incluir-documento`
- `rota:POST:/v4/api/patrimonial/pncp/compraEditalAviso/incluirRespostaItem`
- `rota:POST:/v4/api/patrimonial/pncp/contratos/buscar-documentos`
- `rota:POST:/v4/api/patrimonial/pncp/contratos/buscarContratos`
- `rota:POST:/v4/api/patrimonial/pncp/contratos/incluirDocumento`
- `rota:POST:/v4/api/patrimonial/pncp/integracao/bloquear-unidade-requisitante`
- `rota:POST:/v4/api/patrimonial/pncp/integracao/habilitar`
- `rota:POST:/v4/api/patrimonial/pncp/integracao/orgao`
- `rota:POST:/v4/api/patrimonial/pncp/integracao/verificaIntegracao`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/buscar-elemento-despesa`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/buscar-itens`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/buscar-planos`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/buscar-unidades`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/buscarUnidades`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/editar-item`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/editar-plano`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/elaboracao`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/incluir`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/incluir-item`
- `rota:POST:/v4/api/patrimonial/pncp/planoContratacoes/relatorios/itens-plano`
- `rota:POST:/v4/api/patrimonial/pncp/termos/buscar`
- `rota:POST:/v4/api/patrimonial/pncp/termos/documentos/buscar`
- `rota:POST:/v4/api/patrimonial/pncp/termos/incluir`
- `rota:POST:/v4/api/patrimonial/pncp/termos/retificar`
- `rota:POST:/v4/api/patrimonial/pncp/unidades/buscarEntidade`
- `rota:POST:/v4/api/patrimonial/pncp/unidades/buscarUnidades`
- `rota:POST:/v4/api/patrimonial/protocolo/documentos/atividades-executadas`
- `rota:POST:/v4/api/patrimonial/protocolo/documentos/atribuir-permissao`
- `rota:POST:/v4/api/patrimonial/protocolo/documentos/buscar-por-identificador`
- `rota:POST:/v4/api/patrimonial/protocolo/documentos/conferir`
- `rota:POST:/v4/api/patrimonial/protocolo/documentos/substituir-permissao`
- `rota:GET:/v4/api/patrimonial/protocolo/processo/andamento-padrao/campos-dinamicos/resposta`
- `rota:POST:/v4/api/patrimonial/protocolo/processo/andamento-padrao/campos-dinamicos/resposta`
- `rota:POST:/v4/api/patrimonial/protocolo/processo/criarDespacho`
- `rota:GET:/v4/api/patrimonial/protocolo/processo/search`
- `rota:POST:/v4/api/patrimonial/protocolo/processo/vincularDespachoMensagem`
- `rota:POST:/v4/api/patrimonial/protocolo/salvar-cgm`
- `rota:GET:/v4/api/recursos-humanos/pessoal/ajudacusto/lancamento/create`
- `rota:POST:/v4/api/recursos-humanos/pessoal/ajudacusto/relatorio`
- `rota:GET:/v4/api/recursos-humanos/pessoal/jetom/comissao`
- `rota:GET:/v4/api/recursos-humanos/pessoal/jetom/comissao/servidor/show`
- `rota:POST:/v4/api/recursos-humanos/pessoal/jetom/comissao/servidor/update`
- `rota:POST:/v4/api/recursos-humanos/pessoal/jetom/comissao/tiposessao/update`
- `rota:GET:/v4/api/recursos-humanos/pessoal/jetom/funcao/all`
- `rota:GET:/v4/api/recursos-humanos/pessoal/jetom/funcao/find`
- `rota:POST:/v4/api/recursos-humanos/pessoal/relatorios/previdenciaencargostributarios/emitir`
- `rota:POST:/v4/api/recursos-humanos/pessoal/relatorios/tipoguiaprevidencia/emitir`
- `rota:POST:/v4/api/recursos-humanos/pessoal/rhrubricas/gerar-observacoes`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/assentconcedeconfig`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/assentform`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/assentperc`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/concessaocalculo`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/concessaocalculolog`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/configuracao`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/gravaconcessaoassent`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/gravarconfiguracao`
- `rota:POST:/v4/api/recursos-humanos/rh/concessaodireitos/stopsprocessamento`
- `rota:POST:/v4/api/recursos-humanos/rh/relatorios/configassentperiodo/saveConfig`
- `rota:GET:/v4/api/saude/ambulatorial/consulta/especialidadeprofissionais/ativas`
- `rota:GET:/v4/api/saude/ambulatorial/consulta/setoresambulatoriais`
- `rota:POST:/v4/api/saude/ambulatorial/consulta/statuspaciente`
- `rota:GET:/v4/api/saude/ambulatorial/parametros`
- `rota:POST:/v4/api/saude/ambulatorial/procedimento/unificacao-cgs/listar-unificacoes`
- `rota:POST:/v4/api/saude/farmacia/consulta/bnafar/inconsistencias`
- `rota:POST:/v4/api/saude/farmacia/procedimento/bnafar/salvar-movimentacao`
- `rota:POST:/v4/api/saude/laboratorio/triagem-laboratorial/buscar`
- `rota:POST:/v4/api/saude/laboratorio/triagem-laboratorial/buscar-requisicoes`
- `rota:POST:/v4/api/saude/laboratorio/triagem-laboratorial/exportar-pendencias`
- `rota:POST:/v4/api/tributario/arrecadacao/pix/gerar`
- `rota:GET:/v4/api/tributario/cadastro/buscar-condominios`
- `rota:GET:/v4/api/tributario/cadastro/buscar-logradouro`
- `rota:GET:/v4/api/tributario/cadastro/buscar-loteamento`
- `rota:POST:/v4/api/tributario/divida-ativa/lancamento-historico/dividas`
- `rota:POST:/v4/api/tributario/issqn/buscar-historico-inscricoes`
- `rota:POST:/v4/api/tributario/issqn/buscar-iscr-salao-parceiro`
- `rota:GET:/v4/api/tributario/issqn/buscar-setor-fiscal`
- `rota:GET:/v4/api/tributario/issqn/redesim/dados-estabelecimento`
- `rota:POST:/v4/api/tributario/issqn/redesim/enviar-resposta`
- `rota:GET:/v4/api/tributario/issqn/redesim/eventos`
- `rota:POST:/v4/api/tributario/issqn/redesim/inclusao-inscricao`
- `rota:POST:/v4/api/tributario/issqn/redesim/relatorio-inscricoes`
- `rota:GET:/v4/api/tributario/itbi/benfeitoria/padrao-construtivo`
- `rota:GET:/v4/oauth/authorize`
- `rota:POST:/v4/oauth/authorize`
- `rota:GET:/v4/oauth/clients`
- `rota:POST:/v4/oauth/clients`
- `rota:GET:/v4/oauth/personal-access-tokens`
- `rota:POST:/v4/oauth/personal-access-tokens`
- `rota:GET:/v4/oauth/scopes`
- `rota:POST:/v4/oauth/token/refresh`
- `rota:GET:/v4/oauth/tokens`

## Por caso (explica a diferenca rotas x casos)

Casos carregados: 992; com 5xx na referencia: 276 = 272 que terminam INCONCLUSIVO (500 x 500, nao exercitados) + 4 de rejeicao esperada (`espera_status`: IDENTICO, comportamento documentado da referencia).

- rejeicao esperada: `auth-sem-token`
- rejeicao esperada: `auth-token-invalido`
- rejeicao esperada: `auth-token-expirado`
- rejeicao esperada: `auth-token-revogado`

## Controller quebrado na referencia (console): 101 rota(s)

O controller nao instancia no CONSOLE do Laravel 8 de referencia (classe/funcao que o console nao carrega: modelos `cl_*` do legado, classes inexistentes na base 7.4...): o `route:list` do Laravel 8 nao lista nada por causa delas, e o inventario usa a listagem tolerante. A rota segue no inventario e, se for gerada, vira caso normal: pela HTTP algumas funcionam (o legado e carregado no request) e outras dao 500 (ver a classe de cada caso acima).

- GET|HEAD `/v4/api/educacao/central-de-matriculas/emissao-protocolo`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- GET|HEAD `/v4/api/educacao/central-de-matriculas/observacoes-inscricao/{candidato}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- POST `/v4/api/educacao/central-de-matriculas/observacoes-inscricao/{candidato}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- DELETE `/v4/api/educacao/central-de-matriculas/observacoes-inscricao/{observacao}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- POST `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- GET|HEAD `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/consulta-candidato/{tipo}/{dado}/{nascimento}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- GET|HEAD `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/consulta/{tipo}/{valor}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- GET|HEAD `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/consultaCpf/{cpfAluno}/{tipo}/{valor}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- DELETE `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/{protocolo}`: Error: Call to undefined function App\Domain\Educacao\CentralMatriculas\Controllers\modification()
- DELETE `/v4/api/educacao/escola/diario-classe/registro-aula/excluir-conteudo/{codigo}`: Error: Class 'TraceLog' not found
- GET|HEAD `/v4/api/educacao/escola/diario-classe/registro-aula/get-conteudos-regente-escola`: Error: Class 'TraceLog' not found
- GET|HEAD `/v4/api/educacao/escola/diario-classe/registro-aula/get-dados-regente/{escola}/{user}`: Error: Class 'TraceLog' not found
- GET|HEAD `/v4/api/educacao/escola/diario-classe/registro-aula/get-disciplinas-bncc/{regencia}`: Error: Class 'TraceLog' not found
- GET|HEAD `/v4/api/educacao/escola/diario-classe/registro-aula/get-habilidades-bncc`: Error: Class 'TraceLog' not found
- GET|HEAD `/v4/api/educacao/escola/diario-classe/registro-aula/get-habilidades-desenvolvidas`: Error: Class 'TraceLog' not found
- POST `/v4/api/educacao/escola/diario-classe/registro-aula/salvar-conteudo`: Error: Class 'TraceLog' not found
- POST `/v4/api/educacao/escola/diario-classe/registro-aula/salvar-habilidade-desenvolvida`: Error: Class 'TraceLog' not found
- POST `/v4/api/educacao/escola/diario-classe/registro-aula/update-conteudos-lote`: Error: Class 'TraceLog' not found
- GET|HEAD `/v4/api/educacao/matricula-online/configuracoes/parametros-notificacoes/getParametros`: Error: Class 'ECidade\Educacao\MatriculaOnline\Repository\ConfiguracaoRepository' not found
- POST `/v4/api/educacao/matricula-online/configuracoes/parametros-notificacoes/salvar`: Error: Class 'ECidade\Educacao\MatriculaOnline\Repository\ConfiguracaoRepository' not found
- POST `/v4/api/financeiro/empenho/relatorio/relatorio-subcontratacao`: ErrorException: Use of undefined constant ECIDADE_PATH - assumed 'ECIDADE_PATH' (this will throw an Error in a future version of PHP)
- GET|HEAD `/v4/api/financeiro/orcamento/cadastro/complemento`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_complementofonterecurso] does not exist.
- POST `/v4/api/financeiro/orcamento/cadastro/complemento/excluir`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_complementofonterecurso] does not exist.
- POST `/v4/api/financeiro/orcamento/cadastro/complemento/salvar`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_complementofonterecurso] does not exist.
- POST `/v4/api/financeiro/orcamento/cadastro/especificacao-recurso/excluir`: Error: Class 'ECidade\Financeiro\Orcamento\Service\EspecificacaoService' not found
- POST `/v4/api/financeiro/orcamento/cadastro/especificacao-recurso/salvar`: Error: Class 'ECidade\Financeiro\Orcamento\Service\EspecificacaoService' not found
- POST `/v4/api/financeiro/orcamento/cadastro/recurso/excluir`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- POST `/v4/api/financeiro/orcamento/cadastro/recurso/inativar`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- POST `/v4/api/financeiro/orcamento/cadastro/recurso/salvar`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- POST `/v4/api/financeiro/orcamento/cadastro/recurso/salvar-atualizado`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/cadastro/recurso/{id}/{exercicio}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/cadastro/recursos/depreciados/{exercicio}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/cadastro/recursos/inativar/{exercicio}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/de-para-siconfi/exportar/{exercicio}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- POST `/v4/api/financeiro/orcamento/de-para-siconfi/importar`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/recursos/byFilters`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/recursos/complementos`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_complementofonterecurso] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/recursos/confere-vinculo`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/recursos/{exercicio}/{data?}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- POST `/v4/api/financeiro/orcamento/relatorios/siconfi-recursos-2022`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/orcamento/tipos-detalhamento`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_orctiporec] does not exist.
- GET|HEAD `/v4/api/financeiro/planejamento/configuracao`: Error: Class 'TraceLog' not found
- POST `/v4/api/financeiro/planejamento/configuracao/salvar`: Error: Class 'TraceLog' not found
- POST `/v4/api/financeiro/tesouraria/inconsistente`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Financeiro\Tesouraria\Repository\LinhaTefRepository] does not exist.
- GET|HEAD `/v4/api/financeiro/tesouraria/processar`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Financeiro\Tesouraria\Repository\LinhaTefRepository] does not exist.
- POST `/v4/api/financeiro/tesouraria/processar`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Financeiro\Tesouraria\Repository\LinhaTefRepository] does not exist.
- DELETE `/v4/api/financeiro/tesouraria/processar/{processar}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Financeiro\Tesouraria\Repository\LinhaTefRepository] does not exist.
- GET|HEAD `/v4/api/financeiro/tesouraria/processar/{processar}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Financeiro\Tesouraria\Repository\LinhaTefRepository] does not exist.
- PUT|PATCH `/v4/api/financeiro/tesouraria/processar/{processar}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Financeiro\Tesouraria\Repository\LinhaTefRepository] does not exist.
- POST `/v4/api/integracoes/efd-reinf/configuracao/get`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- POST `/v4/api/integracoes/efd-reinf/configuracao/save`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/andamento-padrao/campos-dinamicos/resposta`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_camposandpadraoresposta] does not exist.
- POST `/v4/api/patrimonial/protocolo/processo/andamento-padrao/campos-dinamicos/resposta`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_camposandpadraoresposta] does not exist.
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/andamento-padrao/campos-dinamicos/{codigo_processo}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_camposandpadrao] does not exist.
- POST `/v4/api/patrimonial/protocolo/processo/arquivar`: Error: Class 'cl_protprocesso' not found
- POST `/v4/api/patrimonial/protocolo/processo/criarDespacho`: Error: Class 'cl_protprocesso' not found
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/departamentos-instituicao`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Patrimonial\Protocolo\Servicos\AndamentoProcessoService] does not exist.
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/despachos-anteriores/{cod_proc}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Patrimonial\Protocolo\Servicos\AndamentoProcessoService] does not exist.
- POST `/v4/api/patrimonial/protocolo/processo/getCgmByCpfCnpj`: Error: Class 'cl_protprocesso' not found
- POST `/v4/api/patrimonial/protocolo/processo/getMensagem`: Error: Class 'cl_protprocesso' not found
- POST `/v4/api/patrimonial/protocolo/processo/getprocesso`: Error: Class 'cl_protprocesso' not found
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/processo`: Error: Class 'cl_protprocesso' not found
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/processodocumento`: Error: Class 'cl_protprocessodocumento' not found
- POST `/v4/api/patrimonial/protocolo/processo/processodocumento/documentosPorNota/{codigo_nota}`: Error: Class 'cl_protprocessodocumento' not found
- POST `/v4/api/patrimonial/protocolo/processo/processodocumento/documentosPorProcAndamInt`: Error: Class 'cl_protprocessodocumento' not found
- POST `/v4/api/patrimonial/protocolo/processo/processodocumento/documentosPorProcesso`: Error: Class 'cl_protprocessodocumento' not found
- POST `/v4/api/patrimonial/protocolo/processo/processodocumento/download`: Error: Class 'cl_protprocessodocumento' not found
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/rotulos`: Error: Class 'cl_protprocesso' not found
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/search`: Error: Class 'cl_protprocesso' not found
- POST `/v4/api/patrimonial/protocolo/processo/sendMensagem`: Error: Class 'cl_protprocesso' not found
- POST `/v4/api/patrimonial/protocolo/processo/transferir`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Patrimonial\Protocolo\Servicos\AndamentoProcessoService] does not exist.
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/usuarios-departamento/{cod_departamento}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Patrimonial\Protocolo\Servicos\AndamentoProcessoService] does not exist.
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/verifica-solicitacoes-assinatura/{id_andamento}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [ECidade\Patrimonial\Protocolo\Servicos\AndamentoProcessoService] does not exist.
- POST `/v4/api/patrimonial/protocolo/processo/vincularDespachoMensagem`: Error: Class 'cl_protprocesso' not found
- DELETE `/v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_camposandpadrao] does not exist.
- GET|HEAD `/v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_camposandpadrao] does not exist.
- POST `/v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos/{ordem}`: Illuminate\Contracts\Container\BindingResolutionException: Target class [cl_camposandpadrao] does not exist.
- POST `/v4/api/recursos-humanos/rh/concessaodireitos/gravaconcessaoassent`: Error: Call to undefined function App\Domain\RecursosHumanos\RH\ConcessaoDireitos\Controllers\modification()
- POST `/v4/api/recursos-humanos/rh/relatorios/certidaotempocontribuicao/gerar`: Error: Class 'ECidade\Pdf\Pdf' not found
- POST `/v4/api/saude/laboratorio/triagem-laboratorial/buscar`: Error: Class 'ECidade\Saude\Laboratorio\Repository\Parametros' not found
- POST `/v4/api/saude/laboratorio/triagem-laboratorial/buscar-requisicoes`: Error: Class 'ECidade\Saude\Laboratorio\Repository\Parametros' not found
- POST `/v4/api/saude/laboratorio/triagem-laboratorial/exportar-pendencias`: Error: Class 'ECidade\Saude\Laboratorio\Repository\Parametros' not found
- POST `/v4/api/saude/laboratorio/triagem-laboratorial/processar`: Error: Class 'ECidade\Saude\Laboratorio\Repository\Parametros' not found
- POST `/v4/api/tributario/arrecadacao/pix/gerar`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- POST `/v4/api/tributario/itbi/arquivoitbi/delete-arquivo`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- POST `/v4/api/tributario/itbi/arquivoitbi/download-arquivo`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- POST `/v4/api/tributario/itbi/arquivoitbi/get-arquivos`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- POST `/v4/api/tributario/itbi/arquivoitbi/processar-arquivo`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- POST `/v4/api/tributario/itbi/arquivoitbi/update-dados-arquivo`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/benfeitoria/especie`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/benfeitoria/padrao-construtivo`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/benfeitoria/tipo`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/benfeitorias`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/cartorios`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/forma-pagamento-tipo-transacao`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/rural/caracter`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/situacao`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/taxas-itbi`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/tipo-transacao`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/tipos`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found
- GET|HEAD `/v4/api/tributario/itbi/transmitente-principal`: Error: Class 'ECidade\Lib\Session\DefaultSession' not found

Notas: rotas GET|HEAD sao exercitadas so por GET (HEAD nao e sondado); PUT|PATCH, se permitido, so por PUT. Rotas com metodo colapsado alem de HEAD: 1.

## Nao cobertas

- caractere fora de [A-Za-z0-9_./-] na uri '/v4/api/educacao/transporte-escolar/emitir-carteira ': 1
- metodo destrutivo sem allowlist: 14
- parametro de caminho {acordoposicao}: 1
- parametro de caminho {acordo}: 2
- parametro de caminho {aluno}: 9
- parametro de caminho {anexo}: 1
- parametro de caminho {assentamento}: 1
- parametro de caminho {base}: 2
- parametro de caminho {batch_id}: 2
- parametro de caminho {calendario}: 3
- parametro de caminho {cancelamento}: 1
- parametro de caminho {candidato}: 2
- parametro de caminho {cgm}: 1
- parametro de caminho {cgs}: 4
- parametro de caminho {client_id}: 2
- parametro de caminho {codFase}: 2
- parametro de caminho {cod_departamento}: 1
- parametro de caminho {cod_proc}: 1
- parametro de caminho {codcon}: 1
- parametro de caminho {codele}: 1
- parametro de caminho {codigoCalendario}: 3
- parametro de caminho {codigoDotacao}: 1
- parametro de caminho {codigoEscola}: 1
- parametro de caminho {codigoMaterial}: 1
- parametro de caminho {codigoTurma}: 1
- parametro de caminho {codigo_nota}: 1
- parametro de caminho {codigo_processo}: 1
- parametro de caminho {codigo}: 31
- parametro de caminho {codtipopix?}: 1
- parametro de caminho {cpfAluno}: 1
- parametro de caminho {cpf}: 2
- parametro de caminho {data}: 2
- parametro de caminho {db90_codban?}: 1
- parametro de caminho {db90_codban}: 3
- parametro de caminho {departamento}: 1
- parametro de caminho {elemento}: 1
- parametro de caminho {ensino}: 1
- parametro de caminho {escola}: 28
- parametro de caminho {esocila}: 1
- parametro de caminho {estado}: 1
- parametro de caminho {estrutural}: 4
- parametro de caminho {etapa}: 3
- parametro de caminho {exercicio}: 8
- parametro de caminho {failed}: 3
- parametro de caminho {fase}: 5
- parametro de caminho {file_id}: 4
- parametro de caminho {grupoId}: 1
- parametro de caminho {grupoLiberacaoId}: 1
- parametro de caminho {grupo}: 1
- parametro de caminho {idRequisicaoExame}: 1
- parametro de caminho {idRequisicao}: 1
- parametro de caminho {idUsuario}: 1
- parametro de caminho {id_andamento}: 1
- parametro de caminho {id}: 31
- parametro de caminho {importar}: 2
- parametro de caminho {instituicao}: 7
- parametro de caminho {instit}: 2
- parametro de caminho {item}: 2
- parametro de caminho {job}: 4
- parametro de caminho {k00_tipo}: 3
- parametro de caminho {k48_sequencial}: 3
- parametro de caminho {laboratorio}: 2
- parametro de caminho {lancamento}: 5
- parametro de caminho {licitacao}: 4
- parametro de caminho {local}: 1
- parametro de caminho {lote}: 1
- parametro de caminho {modulo}: 2
- parametro de caminho {movimentacao}: 1
- parametro de caminho {necessidade}: 1
- parametro de caminho {nomecam}: 1
- parametro de caminho {nome}: 1
- parametro de caminho {numParcelamento}: 2
- parametro de caminho {numcgm}: 1
- parametro de caminho {observacao}: 1
- parametro de caminho {ocupacao}: 1
- parametro de caminho {periodo}: 1
- parametro de caminho {planejamento_id}: 1
- parametro de caminho {processar}: 3
- parametro de caminho {profissionalVacinacao}: 1
- parametro de caminho {profissional}: 2
- parametro de caminho {protocolo}: 1
- parametro de caminho {rechumanoescola}: 1
- parametro de caminho {recurso}: 1
- parametro de caminho {regencia}: 1
- parametro de caminho {relatorio}: 8
- parametro de caminho {rg}: 1
- parametro de caminho {rne}: 1
- parametro de caminho {rubrica}: 1
- parametro de caminho {servidor}: 1
- parametro de caminho {sessao}: 2
- parametro de caminho {tipo?}: 2
- parametro de caminho {tipoPlano}: 1
- parametro de caminho {tipoProcesso}: 1
- parametro de caminho {tipo_processo}: 3
- parametro de caminho {tipo}: 8
- parametro de caminho {token_id}: 2
- parametro de caminho {turmaOrigem}: 1
- parametro de caminho {turma}: 7
- parametro de caminho {usuario_id?}: 1
- parametro de caminho {usuario}: 1
- parametro de caminho {vacina}: 1
- parametro de caminho {viagem}: 3
- parametro de caminho {visto}: 1
- rota perigosa: 160

| origem | metodo | uri | motivo |
|---|---|---|---|
| laravel | DELETE | `/v4/api/configuracao/assinantes/{file_id}` | parametro de caminho {file_id}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/banco-pix/atualizar/{db90_codban}` | parametro de caminho {db90_codban}: nao se envia id real |
| laravel | DELETE | `/v4/api/configuracao/banco-pix/excluir/{db90_codban}` | parametro de caminho {db90_codban}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/banco-pix/validar/{db90_codban?}` | parametro de caminho {db90_codban?}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/banco-pix/{db90_codban}` | parametro de caminho {db90_codban}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/campos/{nomecam}` | parametro de caminho {nomecam}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/documentos-assinar/documento/{file_id}/assinado-por` | parametro de caminho {file_id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/documentos-assinar/documento/{file_id}/assinantes` | parametro de caminho {file_id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/documentos-assinar/{file_id}` | parametro de caminho {file_id}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/entrega-continua/migrate` | rota perigosa (migrate): nao e sondada |
| laravel | POST | `/v4/api/configuracao/gerador/relatorios/importar` | rota perigosa (import): nao e sondada |
| laravel | DELETE | `/v4/api/configuracao/gerador/relatorios/{relatorio}` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/gerador/relatorios/{relatorio}` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | PUT|PATCH | `/v4/api/configuracao/gerador/relatorios/{relatorio}` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/gerador/relatorios/{relatorio}/edit` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/gerador/relatorios/{relatorio}/exportar` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/gerador/relatorios/{relatorio}/template` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/instituicao/departamento-principal` | rota perigosa (provada ao vivo): UPDATE em db_config com corpo vazio (200) |
| laravel | GET|HEAD | `/v4/api/configuracao/instituicao/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/instituicao/{instituicao}/departamento/{departamento}` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/instituicao/{instituicao}/departamentos` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/jobs/destroy-many` | rota perigosa (destroy): nao e sondada |
| laravel | POST | `/v4/api/configuracao/jobs/failed/destroy-many` | rota perigosa (destroy): nao e sondada |
| laravel | DELETE | `/v4/api/configuracao/jobs/failed/{failed}` | parametro de caminho {failed}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/jobs/failed/{failed}` | parametro de caminho {failed}: nao se envia id real |
| laravel | PUT|PATCH | `/v4/api/configuracao/jobs/failed/{failed}` | parametro de caminho {failed}: nao se envia id real |
| laravel | DELETE | `/v4/api/configuracao/jobs/{job}` | parametro de caminho {job}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/jobs/{job}` | parametro de caminho {job}: nao se envia id real |
| laravel | PUT|PATCH | `/v4/api/configuracao/jobs/{job}` | parametro de caminho {job}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/jobs/{job}/edit` | parametro de caminho {job}: nao se envia id real |
| laravel | DELETE | `/v4/api/configuracao/menu/deletar-favorito` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | GET|HEAD | `/v4/api/configuracao/menu/modulos/{modulo}/itens` | parametro de caminho {modulo}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/menu/modulos/{modulo}/itens/{item}` | parametro de caminho {modulo}: nao se envia id real |
| laravel | POST | `/v4/api/configuracao/menu/permissoes/saude/duplicar` | rota perigosa (duplic): nao e sondada |
| laravel | GET|HEAD | `/v4/api/configuracao/organograma/{instit}` | parametro de caminho {instit}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/organograma/{instit}/{departamento}` | parametro de caminho {instit}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/relatorios-legais/periodos/{relatorio}` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | PUT | `/v4/api/configuracao/usuario/notificacoes/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/configuracao/usuario/{idUsuario}/assinantes` | parametro de caminho {idUsuario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/censo/tabelas-censo/cursos-profissionalizantes/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/censo/tabelas-censo/unidades-curriculares/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/candidatos-lista-espera/{etapa}/{escola}/{turno}` | parametro de caminho {etapa}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/escolas-lista-espera/{etapa}` | parametro de caminho {etapa}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/observacoes-inscricao/{candidato}` | parametro de caminho {candidato}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/central-de-matriculas/observacoes-inscricao/{candidato}` | parametro de caminho {candidato}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/central-de-matriculas/observacoes-inscricao/{observacao}` | parametro de caminho {observacao}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/central-de-matriculas/processar-alocacoes` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/aluno/cpf/{cpf}` | parametro de caminho {cpf}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/aluno/escolacpf/{esocila}/{cpf}` | parametro de caminho {esocila}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/aluno/rne/{rne}` | parametro de caminho {rne}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/aluno/visto/{visto}` | parametro de caminho {visto}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/aluno/{escola}/cpf/{cpf}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/estados/{estado}/municipios` | parametro de caminho {estado}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases-interno/{data}` | parametro de caminho {data}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases/{data}` | parametro de caminho {data}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases/{fase}/candidato/cpf/{cpf}` | parametro de caminho {fase}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases/{fase}/candidato/rne/{rne}` | parametro de caminho {fase}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases/{fase}/candidato/visto/{visto}` | parametro de caminho {fase}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases/{fase}/etapas/get-por-data/{data}` | parametro de caminho {fase}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/fases/{fase}/etapas/{etapa}/escolas-disponiveis` | parametro de caminho {fase}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/consulta-candidato/{tipo}/{dado}/{nascimento}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/consulta/{tipo}/{valor}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/consultaCpf/{cpfAluno}/{tipo}/{valor}` | parametro de caminho {cpfAluno}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/central-de-matriculas/processo-inscricao/inscricao/{protocolo}` | parametro de caminho {protocolo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/processo-inscricao/necessidades-especiais/{necessidade}/subdivisoes` | parametro de caminho {necessidade}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/central-de-matriculas/turnos-lista-espera/{etapa}/{escola}` | parametro de caminho {etapa}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunoAtendimentosEspecial/atendimentos/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/escola/alunoAtendimentosEspecial/exclui-recursos/{recurso}` | parametro de caminho {recurso}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/escola/alunoAtendimentosEspecial/excluir/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunoAtendimentosEspecial/recursos/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunoAtendimentosespecial/profissionais-especializados/{turma}` | parametro de caminho {turma}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunos-matriculados/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunos/alunos-por-turma-especial/{turma}` | parametro de caminho {turma}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunos/alunos-por-turma/{turma}` | parametro de caminho {turma}: nao se envia id real |
| laravel | PUT | `/v4/api/educacao/escola/alunos/atualiza-contato-responsavel` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunos/deficiencias/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunos/detalhes-aluno-especial/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/alunos/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/aproveitamento/salvar` | rota perigosa (aprov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/educacao/escola/atestado-frequencia/salvar-obs-rh/{rechumanoescola}` | parametro de caminho {rechumanoescola}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/bases-curriculares/baseEscola/atos/salvar` | rota perigosa (provada ao vivo): INSERT em escola.baseato com valores NULL e corpo vazio (200, Laravel 8) |
| laravel | DELETE | `/v4/api/educacao/escola/bases-curriculares/baseEscola/atos/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/bases-curriculares/baseEscola/{codigo}/atos` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/escola/bases-curriculares/disciplinas/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/bases-curriculares/{base}/etapas/{etapa}/disciplinas` | parametro de caminho {base}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/calendario/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/calendarioaee/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/escola/diario-classe/registro-aula/excluir-conteudo/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/diario-classe/registro-aula/get-dados-regente/{escola}/{user}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/diario-classe/registro-aula/get-disciplinas-bncc/{regencia}` | parametro de caminho {regencia}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/matriculaescolaaluno/{escola}/{aluno}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/matriculaescolaaluno/{escola}/{aluno}/{matricula}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/matriculainicialescolaaluno/{escola}/{aluno}/{matriculainicial}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/matriculas-por-turma/{turma}/{etapa}` | parametro de caminho {turma}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/ocupacao-limpar/{aluno}/{column}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/ocupacao/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/ocupacao/{aluno}/{column}/{value}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/ocupacoes/ocupacao` | rota perigosa (provada ao vivo): INSERT em escola.cboocupacao com titulo NULL e corpo vazio (500, banco v2) |
| laravel | POST | `/v4/api/educacao/escola/ocupacoes/ocupacao/{item}` | parametro de caminho {item}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/ocupacoes/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/ocupacoes/{ocupacao}/deletar` | parametro de caminho {ocupacao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/parametros/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/periodos-calendario/{calendario}` | parametro de caminho {calendario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/periodos-por-calendario/{codigoCalendario}` | parametro de caminho {codigoCalendario}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/profissional/excluir-vacinacao/{profissionalVacinacao}` | parametro de caminho {profissionalVacinacao}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/profissional/{profissional}/salvar-vacinacao` | parametro de caminho {profissional}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/profissional/{profissional}/vacinas` | parametro de caminho {profissional}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/recursos-humanos/excluir-documento-pos-graducao` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/educacao/escola/recursos-humanos/excluir-formacao-superior-profissional` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/educacao/escola/recursos-humanos/profissionais-com-superior/{escola}/{ativos}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/recursos-humanos/profissionais/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/recursos-humanos/profissionais/{escola}/{cgm}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/recursos-humanos/profissionais/{escola}/{cgm}/atividades` | parametro de caminho {escola}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/recursos-humanos/salvar-formacao-superior-profissional` | rota perigosa (provada ao vivo): INSERT DEFAULT VALUES em escola.rhformacaosuperior com corpo vazio (500) |
| laravel | POST | `/v4/api/educacao/escola/regencia/excluir-avaliacao` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/educacao/escola/regencia/turma/{turma}` | parametro de caminho {turma}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/regencias-turmas/{turmaOrigem}/{turmaDestino}/{etapa}` | parametro de caminho {turmaOrigem}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/secretarios/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/tipoausencia/ausencia/{item}` | parametro de caminho {item}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/tipoausencia/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/tipoausencia/{codigo}/deletar` | parametro de caminho {codigo}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/transposicao/cancelar-designacao` | rota perigosa (cancel): nao e sondada |
| laravel | POST | `/v4/api/educacao/escola/transposicao/criterios-ordenacao` | rota perigosa (provada ao vivo): INSERT em escola.criteriostransposicaoordenacao com corpo vazio (500, banco v2) |
| laravel | POST | `/v4/api/educacao/escola/transposicao/processar` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/educacao/escola/turma/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/turma/{codigo}/disciplinas` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/turma/{codigo}/etapas/{etapa}/regencias` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/turmas-por-calendario/{codigoCalendario}` | parametro de caminho {codigoCalendario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/turmas-por-escola-calendarios/{codigoEscola}/{calendarios}` | parametro de caminho {codigoEscola}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/turmas/{codigoTurma}/regencias-por-usuario` | parametro de caminho {codigoTurma}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/escola/turmas/{turma}/periodos-avaliacao` | parametro de caminho {turma}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/turmasMulti/{codigoCalendario}` | parametro de caminho {codigoCalendario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/vacinas/{vacina}` | parametro de caminho {vacina}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/vagas-por-turma/{turma}` | parametro de caminho {turma}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/bases-curriculares` | parametro de caminho {escola}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/escola/{escola}/bases-curriculares/{codigo}/excluir` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/calendario` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/cursos` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/cursos/{codigo}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/diretores` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/etapas/{codigo}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/profissionais` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/regimes-matricula/{codigo}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/regimes-matricula/{codigo}/etapas` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/escola/{escola}/regimes-matricula/{ensino}` | parametro de caminho {escola}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/matricula-online/ciclos/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/matricula-online/configuracoes/duvidas-frequentes/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/matricula-online/configuracoes/imagens-personalizadas/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/matricula-online/configuracoes/imagens-personalizadas/{id}/download` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/matricula-online/configuracoes/mensagens-personalizadas/tipos/{codigo}/mensagem` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/matricula-online/configuracoes/noticias/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/matricula-online/escolas-por-fase-etapa/{codFase}/{codEtapa}` | parametro de caminho {codFase}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/matricula-online/etapas-por-fase/{codFase}` | parametro de caminho {codFase}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/matricula-online/fases/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/bases-curriculares/{base}/etapas/{etapa}/disciplinas` | parametro de caminho {base}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/secretaria/bloqueio-notas/encerrar-excecao/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/secretaria/cursos/excluir/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/cursos/{codigo}/disciplinas` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/cursos/{codigo}/disciplinas/{disciplina}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/emissao-atas/getAlunosAvanco/{calendario}/{turma}` | parametro de caminho {calendario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/emissao-atas/getAlunosClassificacao/{calendario}/{turma}` | parametro de caminho {calendario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/emissao-atas/getAlunosReclassificacao/{escola}/{calendario}/{turma}` | parametro de caminho {escola}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/ensinos/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/modelos-relatorio/getModelosRelatoriosPorTipo/{tipo}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/secretaria/tipo-base/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/educacao/secretaria/tipo-base/salvar` | rota perigosa (provada ao vivo): INSERT em secretariadeeducacao.tipobase com corpo vazio (500) |
| laravel | GET|HEAD | `/v4/api/educacao/secretaria/tipos-insturmentos-avaliativos/byEnsino/{ensino}` | parametro de caminho {ensino}: nao se envia id real |
| laravel | DELETE | `/v4/api/educacao/secretaria/tipos-insturmentos-avaliativos/{codigo}/excluir` | parametro de caminho {codigo}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/transporte-escolar/busca-linhas/{escola}` | parametro de caminho {escola}: nao se envia id real |
| laravel | POST | `/v4/api/educacao/transporte-escolar/emitir-carteira ` | caractere fora de [A-Za-z0-9_./-] na uri '/v4/api/educacao/transporte-escolar/emitir-carteira ' (ex.: espaco no fim, erro do proprio arquivo de rotas): o id do caso seria invalido |
| laravel | POST | `/v4/api/financeiro/contabilidade/BalancetesMensais/balancete-mensal-anexo1` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/fix/lancamento/slips` | rota perigosa (provada ao vivo): DELETE e UPDATE em contabilidade.conlancamrecurso (rotina de correcao em massa) com corpo vazio (200, Laravel 8) |
| laravel | POST | `/v4/api/financeiro/contabilidade/fix/lancamento/suplementacoes` | rota perigosa (provada ao vivo): UPDATE em massa em contabilidade.conlancamrecurso com corpo vazio (200, Laravel 8) |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/lancamento-manual/excluir-lote/{lote}` | parametro de caminho {lote}: nao se envia id real |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/lancamento-manual/{lancamento}` | parametro de caminho {lancamento}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/msc/consistencia/atributoFP/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/msc/importar` | rota perigosa (import): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/consulta/mapeamentos/{tipo}/{exercicio}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/emitir/orcamentario/{tipoPlano}/{origem}/{exercicio}` | parametro de caminho {tipoPlano}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/emitir/pcasp/{tipo}/{exercicio}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/exclusao-geral/orcamentario/despesa` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/exclusao-geral/orcamentario/despesa/{estrutural}/{exercicio}` | parametro de caminho {estrutural}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/exclusao-geral/orcamentario/receita` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/exclusao-geral/orcamentario/receita/{estrutural}/{exercicio}` | parametro de caminho {estrutural}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/exclusao-geral/pcasp` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/exclusao-geral/pcasp/{estrutural}/{exercicio}` | parametro de caminho {estrutural}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/importar/atualizar-pcasp` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/importar/orcamentario/atualizar-despesa` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/importar/orcamentario/atualizar-receita` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/importar/orcamentario/despesa` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/importar/orcamentario/receita` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/importar/pcasp` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/orcamentario/despesa/desvincular` | rota perigosa (desvincul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/orcamentario/despesa/importar-vinculo` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/orcamentario/receita/desvincular` | rota perigosa (desvincul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/orcamentario/receita/importar-vinculo` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/pcasp/conta-corrente/remover` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/pcasp/conta-corrente/{codcon}/{exercicio}` | parametro de caminho {codcon}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/plano-contas/pcasp/estrural-existe/{estrutural}/{exercicio}` | parametro de caminho {estrutural}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/pcasp/importar-vinculo` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/plano-contas/pcasp/remover-reduzido` | rota perigosa (remov): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/procedimento/apropriacao/decimo-ferias/apropriar/processar` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/procedimento/apropriacao/decimo-ferias/estornar/processar` | rota perigosa (estorn): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/procedimento/encerramento-periodo-contabil/{instituicao}` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/procedimento/escrituracao-contabil/implantar-saldo-inicial` | rota perigosa (provada ao vivo): DELETE em contabilidade.conplanoexecontacorrente da instituicao 1 com corpo vazio (200, banco v2) |
| laravel | POST | `/v4/api/financeiro/contabilidade/procedimento/escrituracao-contabil/virada-rp` | rota perigosa (provada ao vivo): INSERT em configuracoes.db_virada e DELETE em empenho.empresto com corpo vazio (500, Laravel 8) |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/procedimento/mapeamento-empenho-rp-conta` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/procedimento/mapeamento-empenho-rp-conta/empenhos` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/procedimento/mapeamento-empenho-rp-manual/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/relatorio-disponibilidade-recurso` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/relatorio-legal/emissao/download/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/relatorio-legal/emissao/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/relatorio-legal/linha/valor-manual/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/relatorio-legal/linhas-manuais/{codigo}/{tipo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | DELETE | `/v4/api/financeiro/contabilidade/relatorio-legal/notas-explicativas/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/relatorio-legal/versoes/anexo/{anexo}/{tipo}` | parametro de caminho {anexo}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/contabilidade/relatorio/anexo17` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/financeiro/contabilidade/relatorio/notificacao-recebimento-recursos-federais` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/contabilidade/tce/rj/sigfis/unidadegestora/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/empenho/retencaosubcontratacao/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/financeiro/orcamento/acompanhamento/cronograma/despesa/recalcular` | rota perigosa (recalcul): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/acompanhamento/cronograma/despesa/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/orcamento/acompanhamento/cronograma/receita/recalcular` | rota perigosa (recalcul): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/acompanhamento/cronograma/receita/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/buscar-dotacoes/{elemento}` | parametro de caminho {elemento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/buscar-saldo-dotacao/{codigoDotacao}` | parametro de caminho {codigoDotacao}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/orcamento/cadastro/complemento/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/orcamento/cadastro/especificacao-recurso/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/orcamento/cadastro/recurso/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/orcamento/cadastro/recurso/inativar` | rota perigosa (inativ): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/cadastro/recurso/{id}/{exercicio}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/cadastro/recursos/depreciados/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/cadastro/recursos/inativar/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/de-para-siconfi/exportar/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/orcamento/de-para-siconfi/importar` | rota perigosa (import): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/get-desdobramento-item/{codele}` | parametro de caminho {codele}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/get-desdobramento/{codigoMaterial}` | parametro de caminho {codigoMaterial}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/recursos/{exercicio}/{data?}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/orcamento/utiliza-decimal/{exercicio}` | parametro de caminho {exercicio}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/abrangencia/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/area-resultado/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/consulta/plano/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/consulta/planos-ativos/{tipo?}` | parametro de caminho {tipo?}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/consulta/planos-em-desenvolvimento/{tipo?}` | parametro de caminho {tipo?}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/consulta/planos/{tipo}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/consulta/planos/{tipo}/{status}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/consulta/situacoes/movimentar/plano/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/despesa/cronograma/recalcular` | rota perigosa (recalcul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/despesa/cronograma/recalcularGeral` | rota perigosa (recalcul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/despesa/detalhamento/remover` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/despesa/detalhamento/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/indicador-programa/remover` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/iniciativa/regionalizacoes/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/iniciativa/remover` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/iniciativa/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/meta-objetivo/remover` | rota perigosa (remov): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/objetivo-estrategico/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/objetivo-programa/remover` | rota perigosa (remov): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/orcamento/cancelar` | rota perigosa (cancel): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/pib/{planejamento_id}` | parametro de caminho {planejamento_id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/programas-estrategico/remover` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/programas-estrategico/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/projecao/despesa/recalcular` | rota perigosa (recalcul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/projecao/receita/recalcular` | rota perigosa (recalcul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/recalcular-valores-sinteticos` | rota perigosa (recalcul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/receita/cronograma/recalcular` | rota perigosa (recalcul): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/receita/previsao/remover` | rota perigosa (remov): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/receita/previsao/removerNaturezas` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/financeiro/planejamento/receita/previsao/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/planejamento/regionalizacao/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/planejamento/remove` | rota perigosa (remov): nao e sondada |
| laravel | POST | `/v4/api/financeiro/tesouraria/decendio/receitas/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/financeiro/tesouraria/importar` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/financeiro/tesouraria/inconsistente` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/financeiro/tesouraria/processar` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/financeiro/tesouraria/processar-implantacao` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/financeiro/tesouraria/processar-implantacao-por-conta` | rota perigosa (processar): nao e sondada |
| laravel | DELETE | `/v4/api/financeiro/tesouraria/processar/{processar}` | parametro de caminho {processar}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/financeiro/tesouraria/processar/{processar}` | parametro de caminho {processar}: nao se envia id real |
| laravel | PUT|PATCH | `/v4/api/financeiro/tesouraria/processar/{processar}` | parametro de caminho {processar}: nao se envia id real |
| laravel | POST | `/v4/api/financeiro/tesouraria/relatorio/tef` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/integracoes/efd-reinf/unidaderesponsavel/delete` | rota perigosa (delete): nao e sondada |
| laravel | DELETE | `/v4/api/patrimonial/contratos/acordo/deletar-dia/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | PUT | `/v4/api/patrimonial/contratos/acordo/salvar-config/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/contratos/acordo/salvar-dias/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/contratos/consulta/buscar-acordo-posicoes/{acordo}` | parametro de caminho {acordo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/contratos/consulta/buscar-itens-posicao/{acordoposicao}` | parametro de caminho {acordoposicao}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/licitacoes/bnc/buscar/{licitacao}` | parametro de caminho {licitacao}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/licitacoes/bnc/excluir/{licitacao}` | parametro de caminho {licitacao}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/licitacoes/bnc/exportar/{licitacao}` | parametro de caminho {licitacao}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/licitacoes/bnc/importar/{licitacao}` | parametro de caminho {licitacao}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/licitacoes/integracaocomprasbr/importar` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/licitacoes/integracaocomprasbr/reprocessar` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/patrimonial/licitacoes/licitacon/obras/buscar-usuario/{instituicao}` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/licitacoes/licitacon/obras/incluir/{acordo}` | parametro de caminho {acordo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/licitacoes/licitacon/obras/orgao-fiscalizado/{instituicao}` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/licitacoes/licitacon/obras/salvar-usuario/{instituicao}` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/licitacoes/tramita/importar` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/material/cadastros/familias/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/patrimonial/material/consulta/fabricante/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/material/implantacao/importar-planilha` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/ataRegistroPreco/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/compraEditalAviso/excluir-documento` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/compraEditalAviso/excluirCompra` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/compraEditalAviso/importarCompraEditalAviso` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/contratos/excluir-documento` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/contratos/excluirContrato` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/planoContratacoes/excluir-plano` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/planoContratacoes/remover-item` | rota perigosa (remov): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/termos/documentos/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/termos/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/pncp/unidades/buscarUnidadesAtivas` | rota perigosa (desativ): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/protocolo/atividades-execucao/excluir-vinculo` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/atividades-execucao/tipo-processo/{tipoProcesso}` | parametro de caminho {tipoProcesso}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/protocolo/documentos/arquivar` | rota perigosa (arquiv): nao e sondada |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/documentos/atividade-em-execucao/usuario/{usuario_id?}` | parametro de caminho {usuario_id?}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/protocolo/documentos/devolver` | rota perigosa (devolv): nao e sondada |
| laravel | POST | `/v4/api/patrimonial/protocolo/documentos/remover-permissao` | rota perigosa (remov): nao e sondada |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/processo/andamento-padrao/campos-dinamicos/{codigo_processo}` | parametro de caminho {codigo_processo}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/protocolo/processo/arquivar` | rota perigosa (arquiv): nao e sondada |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/processo/despachos-anteriores/{cod_proc}` | parametro de caminho {cod_proc}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/protocolo/processo/processodocumento/documentosPorNota/{codigo_nota}` | parametro de caminho {codigo_nota}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/processo/usuarios-departamento/{cod_departamento}` | parametro de caminho {cod_departamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/processo/verifica-solicitacoes-assinatura/{id_andamento}` | parametro de caminho {id_andamento}: nao se envia id real |
| laravel | DELETE | `/v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos` | parametro de caminho {tipo_processo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos` | parametro de caminho {tipo_processo}: nao se envia id real |
| laravel | POST | `/v4/api/patrimonial/protocolo/processo/{tipo_processo}/andamento-padrao/campos-dinamicos/{ordem}` | parametro de caminho {tipo_processo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/e-social/index/{periodo}/{empregador}` | parametro de caminho {periodo}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/e-social/store` | rota perigosa (provada ao vivo): INSERT em recursoshumanos.informacoes_complementares com corpo vazio (500, banco v2) |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/ajudacusto/config-buscar/{instituicao}` | parametro de caminho {instituicao}: nao se envia id real |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/ajudacusto/lancamento/{lancamento}` | parametro de caminho {lancamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/ajudacusto/lancamento/{lancamento}` | parametro de caminho {lancamento}: nao se envia id real |
| laravel | PUT|PATCH | `/v4/api/recursos-humanos/pessoal/ajudacusto/lancamento/{lancamento}` | parametro de caminho {lancamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/ajudacusto/lancamento/{lancamento}/edit` | parametro de caminho {lancamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/ajudacusto/lancamentos/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/ajudacusto/processamento` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/contra-cheques/cancelar-emissao` | rota perigosa (cancel): nao e sondada |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/contra-cheques/falhas/{batch_id}` | parametro de caminho {batch_id}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/contra-cheques/processar-competencia` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/contra-cheques/reprocessar/falha` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/fundeb/rhcargosfundeb/remover` | rota perigosa (remov): nao e sondada |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/fundeb/rhparametrosfundeb/removerAssentamento/{assentamento}` | parametro de caminho {assentamento}: nao se envia id real |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/fundeb/rhparametrosfundeb/removerCargo/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/fundeb/rhparametrosfundeb/removerFuncao/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/fundeb/rhparametrosfundeb/removerLocal/{local}` | parametro de caminho {local}: nao se envia id real |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/fundeb/rhparametrosfundeb/removerRubricaAbatimento/{rubrica}` | parametro de caminho {rubrica}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/comissao/config/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/comissao/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/comissao/funcao/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/comissao/permissao/delete` | rota perigosa (delete): nao e sondada |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/jetom/comissao/permissao/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/comissao/servidor/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/comissao/tiposessao/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/funcao/deletar` | rota perigosa (delete): nao e sondada |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/jetom/importar` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/importar` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/importar/arquivoponto` | rota perigosa (import): nao e sondada |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/jetom/importar/{importar}` | parametro de caminho {importar}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/jetom/importar/{importar}` | parametro de caminho {importar}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/jetom/sessao/processar` | rota perigosa (processar): nao e sondada |
| laravel | DELETE | `/v4/api/recursos-humanos/pessoal/jetom/sessao/{sessao}` | parametro de caminho {sessao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/jetom/sessao/{sessao}` | parametro de caminho {sessao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/lotacao/find/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/pessoal/previdenciacomplementar/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/rhdepend/dependentes/{servidor}` | parametro de caminho {servidor}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/recursos-humanos/pessoal/selecao/find/{codigo}` | parametro de caminho {codigo}: nao se envia id real |
| laravel | POST | `/v4/api/recursos-humanos/rh/concessaodireitos/deleteassentconcedeconfig` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/rh/concessaodireitos/deleteassentform` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/rh/concessaodireitos/deleteassentperc` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/rh/concessaodireitos/deleteconfiguracao` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/recursos-humanos/rh/concessaodireitos/processar` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/saude/ambulatorial/cadastro/unidades-encaminhadoras/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/saude/ambulatorial/cadastro/unidades-origem/delete` | rota perigosa (delete): nao e sondada |
| laravel | GET|HEAD | `/v4/api/saude/ambulatorial/cgs/familiamicroarea/{cgs}` | parametro de caminho {cgs}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/ambulatorial/cgs/{cgs}` | parametro de caminho {cgs}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/ambulatorial/consulta/problemaspaciente/by-paciente/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/ambulatorial/consulta/unidade/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/saude/ambulatorial/procedimento/acompanhamento-acs/delete` | rota perigosa (delete): nao e sondada |
| laravel | GET|HEAD | `/v4/api/saude/ambulatorial/procedimento/acompanhamento-acs/paciente/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/ambulatorial/procedimento/acompanhamento-acs/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | POST | `/v4/api/saude/ambulatorial/procedimento/problemaspaciente/apagar` | rota perigosa (apag): nao e sondada |
| laravel | POST | `/v4/api/saude/ambulatorial/procedimento/unificacao-cgs/excluir` | rota perigosa (exclu): nao e sondada |
| laravel | POST | `/v4/api/saude/ambulatorial/procedimento/unificacao-cgs/processar` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/saude/esf/consulta/equipes/by-unidade/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/esf/vacinas/by-paciente/{cgs}` | parametro de caminho {cgs}: nao se envia id real |
| laravel | POST | `/v4/api/saude/farmacia/cadastro/demanda-reprimida/delete` | rota perigosa (delete): nao e sondada |
| laravel | GET|HEAD | `/v4/api/saude/farmacia/consulta/bnafar/tipos-movimentacoes/{movimentacao}` | parametro de caminho {movimentacao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/farmacia/consulta/demanda-reprimida/by-paciente/{cgs}` | parametro de caminho {cgs}: nao se envia id real |
| laravel | POST | `/v4/api/saude/farmacia/procedimento/bnafar/protocolo/reprocessar` | rota perigosa (processar): nao e sondada |
| laravel | PUT | `/v4/api/saude/laboratorio/cadastro/grupos-liberacao` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/api/saude/laboratorio/cadastro/grupos-liberacao/{grupoId}/exame/{exameId}` | parametro de caminho {grupoId}: nao se envia id real |
| laravel | DELETE | `/v4/api/saude/laboratorio/cadastro/grupos-liberacao/{grupo}` | parametro de caminho {grupo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/consulta/departamentos/{departamento}/laboratorios` | parametro de caminho {departamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/consulta/grupos-liberacao/{grupoLiberacaoId}/exames` | parametro de caminho {grupoLiberacaoId}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/consulta/grupos-liberacao/{usuario}` | parametro de caminho {usuario}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/consulta/laboratorio/{laboratorio}/setores` | parametro de caminho {laboratorio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/consulta/laboratorio/{laboratorio}/setores/{setor}/exames` | parametro de caminho {laboratorio}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/exames/requisicao/{idRequisicao}` | parametro de caminho {idRequisicao}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/laboratorio/exames/resultado/{idRequisicaoExame}` | parametro de caminho {idRequisicaoExame}: nao se envia id real |
| laravel | POST | `/v4/api/saude/laboratorio/triagem-laboratorial/processar` | rota perigosa (processar): nao e sondada |
| laravel | GET|HEAD | `/v4/api/saude/tfd/consulta/viagem/cancelamento/{cancelamento}` | parametro de caminho {cancelamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/tfd/consulta/viagem/{viagem}/lotacao-cancelados` | parametro de caminho {viagem}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/tfd/consulta/viagem/{viagem}/passageiros-cancelados` | parametro de caminho {viagem}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/saude/tfd/consulta/viagem/{viagem}/passageiros-retorno` | parametro de caminho {viagem}: nao se envia id real |
| laravel | POST | `/v4/api/saude/tfd/procedimento/viagem/cancelamento` | rota perigosa (cancel): nao e sondada |
| laravel | POST | `/v4/api/tributario/arrecadacao/controle-parcelamentos-vencidos/agendamento/desativar` | rota perigosa (desativ): nao e sondada |
| laravel | POST | `/v4/api/tributario/arrecadacao/controle-parcelamentos-vencidos/agendamento/salvar` | rota perigosa (provada ao vivo): INSERT em arrecadacao.controleparc_agendamento com corpo vazio (500) |
| laravel | GET|HEAD | `/v4/api/tributario/arrecadacao/controle-parcelamentos-vencidos/buscar/{numParcelamento}` | parametro de caminho {numParcelamento}: nao se envia id real |
| laravel | POST | `/v4/api/tributario/arrecadacao/controle-parcelamentos-vencidos/processar/{numParcelamento}` | parametro de caminho {numParcelamento}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/tributario/arrecadacao/controle-parcelamentos-vencidos/tipo-parcelamento/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | PATCH | `/v4/api/tributario/arrecadacao/data-lancamento-debito/editar-registro` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/api/tributario/arrecadacao/data-lancamento-debito/excluir-registro` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/api/tributario/arrecadacao/grupotaxas/deletar` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | PATCH | `/v4/api/tributario/arrecadacao/grupotaxas/editar` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/api/tributario/arrecadacao/ordenacoes-cgf/apagar` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | POST | `/v4/api/tributario/arrecadacao/procedimentos/cancelparcellista` | rota perigosa (cancel): nao e sondada |
| laravel | POST | `/v4/api/tributario/arrecadacao/regra-emissao/atualizar/{k48_sequencial}` | parametro de caminho {k48_sequencial}: nao se envia id real |
| laravel | DELETE | `/v4/api/tributario/arrecadacao/regra-emissao/excluir/{k48_sequencial}` | parametro de caminho {k48_sequencial}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/tributario/arrecadacao/regra-emissao/{k48_sequencial}` | parametro de caminho {k48_sequencial}: nao se envia id real |
| laravel | POST | `/v4/api/tributario/arrecadacao/tef/baixar-debito` | rota perigosa (baix): nao e sondada |
| laravel | POST | `/v4/api/tributario/arrecadacao/tef/comprovante-desfazimento` | rota perigosa (desfaz): nao e sondada |
| laravel | POST | `/v4/api/tributario/arrecadacao/tef/desfazer-operacao` | rota perigosa (desfaz): nao e sondada |
| laravel | POST | `/v4/api/tributario/arrecadacao/tipo-debito/atualizar/{k00_tipo}` | parametro de caminho {k00_tipo}: nao se envia id real |
| laravel | DELETE | `/v4/api/tributario/arrecadacao/tipo-debito/excluir/{k00_tipo}` | parametro de caminho {k00_tipo}: nao se envia id real |
| laravel | POST | `/v4/api/tributario/arrecadacao/tipo-debito/validar/{codtipopix?}` | parametro de caminho {codtipopix?}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/tributario/arrecadacao/tipo-debito/{k00_tipo}` | parametro de caminho {k00_tipo}: nao se envia id real |
| laravel | GET|HEAD | `/v4/api/tributario/cadastro/dados-isencao/{id}` | parametro de caminho {id}: nao se envia id real |
| laravel | PATCH | `/v4/api/tributario/cemiterio/parametros/alteracao-parametros` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | POST | `/v4/api/tributario/issqn/alvaraeventos/alvaraevento/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/alvaraeventos/ordemservico/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/alvaraeventos/ordemservico/desprocessar` | rota perigosa (desprocess): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/alvaraeventos/ordemservico/processar` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/redesim/processar-evento-alteracao-inscricao` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/redesim/processar-evento-inclusao-inscricao` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/simples-nacional/exporta-arquivo` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/simples-nacional/importa-optantes` | rota perigosa (import): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/veiculos/condutorauxiliar/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/veiculos/veiculo/delete` | rota perigosa (delete): nao e sondada |
| laravel | POST | `/v4/api/tributario/issqn/veiculos/veiculo/desprocessar` | rota perigosa (desprocess): nao e sondada |
| laravel | POST | `/v4/api/tributario/itbi/arquivoitbi/delete-arquivo` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/tributario/itbi/arquivoitbi/download-arquivo` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/tributario/itbi/arquivoitbi/get-arquivos` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/tributario/itbi/arquivoitbi/processar-arquivo` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/tributario/itbi/arquivoitbi/update-dados-arquivo` | rota perigosa (arquiv): nao e sondada |
| laravel | POST | `/v4/api/tributario/juridico/anulacaocda/processar` | rota perigosa (processar): nao e sondada |
| laravel | POST | `/v4/api/tributario/juridico/inclusaoiniciallista/processar` | rota perigosa (processar): nao e sondada |
| laravel | PUT | `/v4/kill` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | PUT | `/v4/logout` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/oauth/authorize` | metodo destrutivo sem allowlist: DELETE/PUT/PATCH nao sao sondados |
| laravel | DELETE | `/v4/oauth/clients/{client_id}` | parametro de caminho {client_id}: nao se envia id real |
| laravel | PUT | `/v4/oauth/clients/{client_id}` | parametro de caminho {client_id}: nao se envia id real |
| laravel | DELETE | `/v4/oauth/personal-access-tokens/{token_id}` | parametro de caminho {token_id}: nao se envia id real |
| laravel | DELETE | `/v4/oauth/tokens/{token_id}` | parametro de caminho {token_id}: nao se envia id real |
| laravel | GET|HEAD | `/web/configuracao/gerador/relatorios/{relatorio}` | parametro de caminho {relatorio}: nao se envia id real |
| laravel | GET|HEAD | `/web/educacao/escola/alunos/historico-escolar/{aluno}` | parametro de caminho {aluno}: nao se envia id real |
| laravel | GET|HEAD | `/web/financeiro/contabilidade/msc/lrf/anexo/{tipo}/{codigo}/{consolida}` | parametro de caminho {tipo}: nao se envia id real |
| laravel | GET|HEAD | `/web/recursos-humanos/pessoal/contra-cheque-app-falhas/{batch_id}` | parametro de caminho {batch_id}: nao se envia id real |
| laravel | GET|HEAD | `/web/tributario/fiscalizacao/vistoria/demostrivo-calculo/{numcgm}` | parametro de caminho {numcgm}: nao se envia id real |
| rest | GET|HEAD | `/rest/v1/enderecopessoa/{cgm}` | parametro de caminho {cgm}: nao se envia id real |
| rest | GET|HEAD | `/rest/v1/pesquisapessoa/nro_cpf/{cpf}` | parametro de caminho {cpf}: nao se envia id real |
| rest | GET|HEAD | `/rest/v1/pesquisapessoa/nro_rg/{rg}` | parametro de caminho {rg}: nao se envia id real |
| rest | GET|HEAD | `/rest/v1/pesquisapessoa/txt_nome/{nome}/{tp_pesquisa?}` | parametro de caminho {nome}: nao se envia id real |
| silex | GET | `/api/v1/configuracao/formulario/{id}/instituicao/{instituicao}` | parametro de caminho {id}: nao se envia id real |
| silex | GET | `/api/v1/protocolo/cgm/{id}` | parametro de caminho {id}: nao se envia id real |
