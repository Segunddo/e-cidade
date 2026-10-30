# Decisoes pendentes da migracao

Nenhuma decisao abaixo foi tomada nesta documentacao. Para cada item, registrar responsavel, data, escolha, justificativa e riscos antes de alterar dependencias ou codigo.

## Laravel 12 versus Laravel 13

**Problema:** o projeto atual fixa Laravel 5.4. PHP 8.5 e oficialmente suportado tanto por Laravel 12 como por Laravel 13, mas os periodos de suporte diferem.

**Alternativas a investigar:**

- Laravel 12 como alvo final ou etapa intermediaria. PHP suportado 8.2–8.5; correcoes de bugs ate 13/08/2026 e de seguranca ate 24/02/2027.
- Laravel 13 como alvo final. PHP minimo 8.3, inclui PHP 8.5; correcoes de bugs ate Q3/2027 e de seguranca ate 17/03/2028.
- Planejar uma migracao por versoes intermediarias, sem presumir que o salto de Laravel 5.4 seja simples.

**Evidencias necessarias:** janela operacional e de suporte exigida, inventario de breaking changes, estimativa de retrabalho e matriz de dependencias resolvivel para cada alvo. Os guias oficiais de Laravel 12/13 nao eliminam a necessidade de analisar o codigo legado.

## SDK Pix Banco do Brasil e Guzzle

**Problema:** SDK `dbseller/sdk-api-pix-bb 1.0.0` requer Guzzle `^6.2`; Laravel 12 requer Guzzle `^7.8.2`. As faixas nao se sobrepoem. O codigo usa classes do SDK no fluxo Pix.

**Alternativas a investigar:** atualizar/forkar o SDK, substituir pelo cliente/API mantido, adaptar a integracao usando Guzzle 7, ou desacoplar temporariamente a integracao em processo/servico separado.

**Evidencias necessarias:** suporte oficial do fornecedor, contrato/API vigente, seguranca, requisitos de autenticacao/certificado, teste ponta a ponta em sandbox e prova de que a alternativa mantem os fluxos de negocio.

## Phinx PostgreSQL

**Problema:** `dbseller/phinx_postgres 1.3.0` requer Phinx `^0.10`; a versao travada 0.10.8 restringe Symfony a versoes ate 4.x, contra Symfony 7.2 do Laravel 12.

**Alternativas a investigar:** versao atualizada do adaptador, substituicao por mecanismo de migrations compatível, ou separacao/retirada caso o inventario prove que nao e utilizado. Nao presumir que migrations existentes podem ser descartadas.

**Evidencias necessarias:** pontos de entrada e configuracoes em uso, inventario de migrations, suporte de fornecedor/Phinx a Symfony e PHP alvo, e ensaio em copia descartavel de PostgreSQL restauravel.

## Bibliotecas antigas para arquivos

**Problema:** mPDF 7.1.9, PhpSpreadsheet 1.8.2 e PHPWord 0.17.0 possuem requisitos PHP que excluem PHP 8.5. Dompdf 0.8.3, `proner/phppimaco`, `aferrandini/phpqrcode` e conversores externos nao foram aprovados funcionalmente pela auditoria.

**Alternativas a investigar:** atualizar para versoes com requisitos adequados, substituir biblioteca, manter formatos por outro fluxo, ou retirar somente quando o inventario funcional confirmar que nao ha uso.

**Evidencias necessarias:** versoes e requisitos oficiais, formatos efetivamente gerados/consumidos, amostras anonimizadas, fontes, imagens, formulas e codigos de barras usados, requisitos de licenca e testes de regressao visual/estrutural.

## Doctrine DBAL e lockfile

**Problema:** `doctrine/dbal` esta em `require` como `2.*`, mas nao tem entrada em `composer.lock`. O resultado de `composer validate` e desconhecido, pois o comando nao foi executado.

**Alternativas a investigar:** confirmar se o pacote e realmente requerido; corrigir a sincronizacao do lock quando autorizado; ou escolher uma versao compativel com o Laravel e o uso de migrations/schema, se a dependencia continuar necessaria.

**Evidencias necessarias:** validacao Composer autorizada, motivo da ausencia no lock, buscas por uso direto/indireto, migrations que alteram colunas e requisitos do Laravel alvo.

## Pacotes especificos do fornecedor

**Problema:** `dbseller/legacy` e `dbseller/session` nao apresentam evidencias suficientes no lock para aprovar PHP 8.5/Laravel 12 ou 13; a branch `dev-master` de Session e mutavel.

**Alternativas a investigar:** obter versoes/releases mantidas, solicitar declaracao de suporte ao fornecedor, atualizar/forkar com responsabilidade interna ou substituir.

**Evidencias necessarias:** codigo do commit efetivamente travado, metadados Composer completos, suite de testes no PHP/Laravel alvo, seguranca e compatibilidade de sessao/autenticacao.

## Dependencias de desenvolvimento

**Problema:** PHPUnit 5.7 e Faker 1.9 excluem PHP 8.5 pelas restricoes travadas. Mockery 1.3 e PHPCS 3.9 nao foram demonstrados em execucao no alvo.

**Alternativas a investigar:** atualizar PHPUnit/Faker/Mockery/PHPCS, ajustar testes legados e determinar o que e necessario no pipeline. A instalacao de producao com `--no-dev` tem impacto distinto, mas nao resolve a necessidade de executar a suite de desenvolvimento.

**Evidencias necessarias:** requisitos oficiais das versoes candidatas, resolucao do grafo para Laravel escolhido, execucao da suite completa e verificacao de plugins/configuracoes de CI.

## Levantamento de descobertas da equipe

**Problema:** o arquivo esperado `docs/migracao-laravel/levantamento/descobertas-do-projeto.md` nao foi encontrado no workspace durante a auditoria anterior.

**Alternativas a investigar:** solicitar o arquivo ao integrante ou receber o conteudo e a localizacao corretos; depois comparar cada descoberta com os arquivos e evidencias do repositorio.

**Evidencias necessarias:** documento original acessivel, autoria/data/escopo e verificacao de cada afirmacao. Nenhum conteudo foi inventado ou incorporado como fato.
