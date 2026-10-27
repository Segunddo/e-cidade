# Plano de migracao do e-Cidade

Este plano descreve trabalho futuro. Nenhuma etapa abaixo foi executada. Nao avancar para instalacao ou alteracao de dependencias antes de aprovar as decisoes em [decisoes-pendentes.md](decisoes-pendentes.md).

## Bloqueios antes da resolucao

O conjunto atual nao pode ser instalado como Laravel 12/PHP 8.5 sem resolver pelo menos estes conflitos:

- Laravel 5.4 fixo no manifesto e pacotes Laravel ligados a Illuminate 5/6 (Passport, Tinker e IDE Helper).
- Restricoes Symfony `~3.2` do projeto versus Symfony `^7.2` exigido por Laravel 12.
- Guzzle 6 exigido pelo SDK Pix versus Guzzle 7 exigido por Laravel 12.
- Phinx PostgreSQL → Phinx 0.10 → Symfony ate 4.x.
- Silex 2 → componentes Symfony 2.8/3.x.
- Requisitos PHP travados que excluem PHP 8 em mPDF 7.1.9, PhpSpreadsheet 1.8.2, PHPWord 0.17.0 e `lcobucci/jwt` 3.3.3.
- PHPUnit 5.7 e Faker 1.9 impedem instalar dependencias de desenvolvimento em PHP 8.5.
- `doctrine/dbal` esta no `composer.json`, mas nao no `composer.lock`; o resultado de `composer validate` ainda e desconhecido.

Cada bloqueio precisa de uma decisao de atualizacao, substituicao ou remocao fundamentada no uso real. Nao assumir que pacote antigo/abandonado esta automaticamente inutil ou que requisito PHP aberto prova suporte.

## Fase 1: Preparacao e seguranca

1. Confirmar branch e estado do repositorio antes de qualquer alteracao.
2. Garantir backup e procedimento de retorno para codigo, configuracao e banco conforme o processo da equipe.
3. Criar uma copia de trabalho/ambiente isolado e manter os servicos externos e banco de producao fora dos testes.
4. Localizar e incorporar o levantamento de descobertas da equipe quando estiver disponivel; o arquivo esperado nao foi encontrado na auditoria anterior.
5. Inventariar fluxos usados, extensoes PHP, executaveis externos de conversao, integracoes, jobs e agendamentos.

**Ponto de parada:** nao continuar sem ambiente de teste isolado, estrategia de retorno e levantamento funcional revisado.

## Fase 2: Escolha da versao-alvo

1. Comparar Laravel 12 e Laravel 13 com responsaveis tecnicos e de produto.
2. Considerar o suporte: PHP 8.5 e aceito por ambos segundo a documentacao oficial. Laravel 12 tem correcoes de bugs ate 13/08/2026 e seguranca ate 24/02/2027; Laravel 13 tem correcao de bugs ate Q3/2027 e seguranca ate 17/03/2028.
3. Estimar a distancia da aplicacao Laravel 5.4, custo de atualizacao de pacotes, requisitos de suporte da organizacao e prazo do projeto.
4. Tratar Laravel 12 como possivel etapa intermediaria somente se houver motivo e plano de continuidade; o guia Laravel 13 de 12 para 13 nao substitui guias para sair do Laravel 5.4.

**Dependencia:** decisao humana registrada em `decisoes-pendentes.md`. Nenhum alvo foi escolhido nesta documentacao.

## Fase 3: Resolucao das dependencias

1. Corrigir a divergencia DBAL/lock e executar validacao do manifesto/lock somente apos autorizacao.
2. Para o alvo aprovado, atualizar as restricoes de Laravel, componentes Illuminate/Symfony e ferramentas de desenvolvimento.
3. Resolver Guzzle/Pix, Phinx PostgreSQL e Silex, registrando cada alternativa escolhida antes de alterar requisitos.
4. Escolher versoes modernas ou substitutos para JWT, mPDF, PhpSpreadsheet e PHPWord, confirmando extensoes e formatos necessarios.
5. Avaliar pacotes privados e de suporte sem metadados suficientes com o fornecedor ou por testes controlados.
6. Resolver primeiro em branch/copia isolada e revisar a arvore completa, inclusive dependencias transitivas e licencas.

**Criterio para avancar:** solver sem conflitos para o PHP e Laravel aprovados; nenhuma dependencia desconhecida tratada como aprovada sem evidencias.

## Fase 4: Adaptacao do codigo

1. Planejar migracao em incrementos compativeis com a distancia entre Laravel 5.4 e o alvo; avaliar versoes intermediarias e breaking changes oficiais.
2. Adaptar autenticacao OAuth/Passport, middleware, providers, comandos, jobs, eventos, filas, sessoes e configuracoes conforme os APIs de destino.
3. Adaptar as integracoes que deixarem de ter uma biblioteca compatível: Pix BB, Phinx/PostgreSQL e geradores de PDF, planilha e documento.
4. Rever uso de helpers globais, Reflection, serializacao de closures e APIs PHP alteradas ate PHP 8.5.
5. Revisar migrations e caminhos de schema. Nao executar migrations em banco real durante esta fase.

**Dependencia:** resolucao de dependencias aprovada e inventario de uso concluido.

## Fase 5: Testes

Executar em ambiente isolado, com dados anonimizados/sinteticos e dependencias externas simuladas quando possivel:

- Testes unitarios e de integracao no PHP alvo, atualizando primeiro PHPUnit/Mockery/Faker.
- Login, emissao/renovacao de token, rotas OAuth, middleware e permissoes Passport.
- Integracao Pix Banco do Brasil: autenticacao, criacao/consulta/cancelamento conforme fluxos usados, erros, timeout, TLS e respostas inesperadas. Nao usar credenciais de producao.
- PDFs: fontes, imagens, codigos de barras/QR e caracteres especiais nos documentos realmente emitidos.
- Planilhas: leitura, escrita, formulas, estilos e arquivos representativos.
- Documentos: DOCX/PDF e conversoes externas requeridas.
- Email, chamadas HTTP, filas, agendamentos, sessao, validacao, serializacao e exportacoes relevantes.
- Migrations em copia restauravel de banco PostgreSQL de teste; validar esquema e dados sem atingir producao.
- Testes de regressao para fluxos fiscais, contabeis, folha, arrecadacao e demais areas que o inventario identificar.

**Criterio para avancar:** resultados reproduziveis, falhas triadas e aprovacao dos responsaveis pelos fluxos de negocio. Nenhum teste foi executado nesta etapa documental.

## Fase 6: Validacao final e implantacao

1. Repetir testes automatizados e smoke tests com a mesma versao do lock que sera implantada.
2. Validar extensoes, configuracoes, permissao de arquivos, executaveis externos, filas, cron e conexoes em ambiente de homologacao.
3. Ensaiar backup, restauracao e rollback; medir duracao e revisar logs/monitoramento.
4. Obter aprovacao tecnica e funcional e agendar implantacao controlada.
5. Monitorar erros e integracoes apos liberacao e manter procedimento de retorno.

**Criterio de conclusao:** somente depois da aprovacao e implantacao validada a migracao podera ser considerada concluida. Este documento nao afirma que isso ocorreu.

## Validacoes Composer futuras (nao executadas)

Com autorizacao e em copia/branch apropriada, avaliar comandos somente de diagnostico como `composer validate --no-check-publish`, `composer show --locked --tree`, `composer why` e `composer prohibits`. Para experimentar novas restricoes, usar copia descartavel, scripts desativados e solver em modo de simulacao; conferir previamente que o comando nao escreve no repositorio. Nao rodar `composer install`, `composer update` nem qualquer migration sem autorizacao explicita e ambiente controlado.
