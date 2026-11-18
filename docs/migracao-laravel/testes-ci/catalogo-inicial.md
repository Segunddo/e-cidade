# Primeira entrega de Testes/CI e catalogo

## Objetivo

Documentar como a equipe vai verificar equivalencia entre PHP 7.4/Laravel 8 e PHP 8.5/Laravel 13. A preparacao reutiliza a suite e os catalogos existentes e registra suas dependencias da base antiga.

## Pipeline minimo proposto

O primeiro incremento pode verificar a sintaxe dos arquivos PHP alterados em cada pull request. A selecao de arquivos deve usar o diff contra `base-php74`, processar os caminhos preservando espacos e excluir arquivos removidos. Os dois runtimes recebem a mesma lista. A leitura de stdin deve ficar isolada da execucao do PHP, conforme a armadilha documentada no catalogo do grupo.

| Resultado | Interpretacao no relatorio |
| --- | --- |
| Compila nos dois | Sintaxe compativel, fluxo funcional ainda precisa de teste. |
| Compila no 7.4 e falha no 8.5 | Incompatibilidade de migracao a tratar pelo responsavel. |
| Falha no 7.4 | Comparar com o arquivo anterior na base e registrar se a falha ja existia. |
| Nao foi possivel executar | Marcar erro de ambiente e preservar o diagnostico. |

O criterio de bloqueio do pull request precisa ser combinado com o grupo, pois ha falhas pre-existentes relatadas. O pipeline deve mostrar as falhas e a origem delas. A etapa funcional entra depois que o ambiente de referencia estiver acordado e a suite aceitar 7.4. Migrations e restauracao do banco exigem o ambiente especifico definido pela equipe.

## Arquivos desta entrega

- [Casos detalhados](casos-iniciais.tsv), com oito casos planejados e passos propostos.
- [Modelo de execucao](modelo-execucao.md), para o responsavel registrar a rodada e as evidencias.

## Estrutura do catalogo

Cada caso deve ter ID, fluxo, prioridade, origem no codigo, pre-condicoes, passos, resultado da referencia 7.4, resultado do alvo 8.5, efeito esperado no banco, evidencia e veredito. O responsavel pela execucao preenche resultados e data apos rodar o caso. Falha nas duas versoes, timeout ou tela vazia exigem investigacao e classificacao propria.

## Casos iniciais para alinhar com a regressao

Todos os casos abaixo estao **planejados**, com execucao pendente. As rotas e parametros precisam ser conferidos na nova base e no ambiente antes da medicao.

| ID | Fluxo | Comparacao proposta | Preparacao necessaria |
| --- | --- | --- | --- |
| CI-01 | Sintaxe do lote | Resultado do lint 7.4 e 8.5 por arquivo alterado | Lista exata do diff e runtimes identificados. |
| REG-01 | Boot do Laravel | Inicializacao e resposta de uma rota de leitura | Vendor proprio do 8.5 e configuracao de teste. |
| REG-02 | Login `/v4/login` | Status, estrutura de resposta e efeito de sessao/token | Usuario de teste e conteiner apropriado para a escrita do login. |
| REG-03 | Autenticacao OAuth | Sucesso e rejeicoes com cliente de teste | Decisao de Passport e rotas da base 7.4 conferidas. |
| REG-04 | Menu e favoritos | Itens disponiveis e comportamento do usuario | Banco de referencia decidido e pre-requisitos de schema resolvidos pela equipe. |
| REG-05 | Endpoint `/v4` de leitura | Status, Content-Type e corpo, preservando tipos JSON | Rota selecionada no inventario e autenticacao de teste. |
| REG-06 | Documento emitido | Texto, paginas e elementos relevantes | Ler a rotina para determinar efeitos e usar dados de teste. |
| REG-07 | Integracao externa | Pedidos e respostas contra duble local | Contrato e duble existentes identificados. |

## Evidencia para apresentar

Mostrar o mapa dos instrumentos existentes, a proposta do lint nos dois runtimes e estes casos com estado planejado. Depois da primeira execucao, anexar commit, versoes, comando reproduzivel e relatorio do caso. Isso permite distinguir a documentacao de preparacao dos resultados efetivamente medidos.

## Ferramentas atualizadas da equipe

A branch nucleo/ferramentas-php74-atualizadas, no commit 6228f6b127f0bb0ebb7229921699d8aa8f67e75e, adapta as ferramentas ao container de referencia PHP 7.4. O README registra que a execucao delas nesse runtime com Docker ainda esta pendente. Conferir sua integracao antes de portar ferramentas ou criar um executor paralelo.

## Sequencia de implementacao

1. Colocar a documentacao em uma branch derivada da nova base e confirmar a divisao com o responsavel pela regressao.
2. Conferir o ambiente 7.4 e 8.5 e a decisao de banco com a coordenacao.
3. Implementar o lint do lote em CI com relatorio por runtime.
4. Avaliar o porte de `ecidade/tests/suite/` da branch existente para a nova referencia, sem copiar alteracoes de aplicacao junto.
5. Regravar o primeiro caso no 7.4 e comparar o mesmo fluxo no 8.5.

Sugestao de assunto para o primeiro commit documental, apos atribuicao do numero da tarefa pelo grupo: `PHP8-NN: Documenta CI e catalogo inicial de regressao`. No corpo, registrar quais branches e commits foram consultados e que a execucao esta pendente.
