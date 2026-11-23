# Documentacao da migracao Laravel

Esta pasta organiza o trabalho de avaliacao e planejamento para migrar o e-Cidade da stack legada atual para uma versao moderna do Laravel e do PHP. Os documentos registram evidencias, riscos, decisoes que ainda precisam de responsavel e as validacoes futuras. Eles nao significam que a migracao foi iniciada ou concluida.

## Como navegar

- [Auditoria revisada do Composer](auditoria/composer-compatibilidade-revisada.md): resumo dos bloqueios de resolucao ja identificados, das dependencias sem compatibilidade demonstrada e dos testes ainda necessarios.
- [Plano de migracao](plano-de-migracao.md): fases propostas, dependencias entre atividades e criterios para avancar.
- [Decisoes pendentes](decisoes-pendentes.md): alternativas e evidencias necessarias antes de escolher um alvo ou substituir bibliotecas.

## Documentos de referencia

O arquivo [`compatibilidade-composer.md`](../../compatibilidade-composer.md), na raiz do repositorio, e o relatorio anterior. Ele deve ser preservado como referencia historica e **nao deve ser substituido** pela auditoria revisada desta pasta. A versao revisada registra correcoes de classificacao e contexto da auditoria posterior.

O levantamento de descobertas feito por outro integrante da equipe ainda precisa ser incorporado. Na auditoria anterior, o documento esperado `docs/migracao-laravel/levantamento/descobertas-do-projeto.md` nao foi encontrado no workspace. Seu conteudo nao foi presumido; a integracao dessas descobertas permanece pendente ate que o arquivo ou seu conteudo seja disponibilizado.

## Estado

Esta pasta documenta uma avaliacao e um plano. Nenhuma instalacao ou atualizacao de dependencia, alteracao de codigo, migracao de banco ou execucao de testes foi realizada como parte desta documentacao.
