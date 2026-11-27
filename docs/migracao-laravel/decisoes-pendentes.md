# Decisoes pendentes da migracao

Situacao atualizada em 27/11/2026, conferida na `base-php85` em `ceef42c8d` (PR #58 integrado). O texto
original de cada item (auditoria feita sobre a base com Laravel 5.4) ficou em "Problema original", como
historico. A versao anterior deste arquivo esta no commit `c8775865b`.

Referencias de versao: 7.4 = `ecidade/composer.json` / `composer.lock` (PR #8, intocados);
8.5 = `ecidade/composer-85.json` / `composer-85.lock`.

## Resumo

| Item | Situacao |
|---|---|
| Laravel 12 versus Laravel 13 | Feito: Laravel 13 |
| SDK Pix Banco do Brasil e Guzzle | Parcial |
| Phinx PostgreSQL | Nao se aplica mais |
| Bibliotecas antigas para arquivos | Feito |
| Doctrine DBAL e lockfile | Feito |
| Pacotes especificos do fornecedor | Parcial |
| Dependencias de desenvolvimento | Feito |
| Levantamento de descobertas da equipe | Nao feito |

## Laravel 12 versus Laravel 13

**Situacao: FEITO - Laravel 13.** `composer-85.lock`: `laravel/framework v13.43.0`, `laravel/passport v13.12.0`.
O 7.4 continua no Laravel 8.73 / Passport 10.4 do PR #8.

**Problema original:** o projeto atual fixa Laravel 5.4. PHP 8.5 e oficialmente suportado tanto por Laravel 12
como por Laravel 13, mas os periodos de suporte diferem.

## SDK Pix Banco do Brasil e Guzzle

**Situacao: PARCIAL.** O sistema funciona no 8.5, mas o SDK nao foi atualizado.

- O `dbseller/sdk-api-pix-bb 2.0.0` (o PR #8 ja trocou a 1.0.0) exige Guzzle exatamente `7.5.0`; o Laravel 13
  exige `^7.8.2`.
- Contorno no 8.5: `"guzzlehttp/guzzle": "7.16.3 as 7.5.0"` no `composer-85.json` (alias de versao: o
  Composer instala a 7.16.3 e a apresenta ao SDK como 7.5.0). O 7.4 segue com a 7.5.0.
- Prova: os pedidos HTTP do SDK foram comparados byte a byte entre 7.4 e 8.5 com um duble de HTTP local,
  sem rede (guia da demonstracao 04).
- Falta: versao do SDK que declare Guzzle `^7.8` (fornecedor ou fork mantido) e teste ponta a ponta em
  sandbox do banco. Enquanto isso, o alias depende de a API do Guzzle 7 continuar compativel.

**Problema original:** SDK `dbseller/sdk-api-pix-bb 1.0.0` requer Guzzle `^6.2`; Laravel 12 requer Guzzle
`^7.8.2`. As faixas nao se sobrepoem. O codigo usa classes do SDK no fluxo Pix.

## Phinx PostgreSQL

**Situacao: NAO SE APLICA MAIS.** O PR #8 retirou o Phinx: `robmorgan/phinx` e `dbseller/phinx_postgres`
nao aparecem no `composer.lock` nem no `composer-85.lock`, e nenhum arquivo de `ecidade/app`,
`ecidade/config`, `ecidade/configuration` ou `ecidade/database` usa `Phinx\`. O conflito com o Symfony
deixou de existir. Se o grupo voltar a usar Phinx, o item precisa ser reaberto.

**Problema original:** `dbseller/phinx_postgres 1.3.0` requer Phinx `^0.10`; a versao travada 0.10.8
restringe Symfony a versoes ate 4.x, contra Symfony 7.2 do Laravel 12.

## Bibliotecas antigas para arquivos

**Situacao: FEITO.** `composer-85.lock`: `mpdf/mpdf v8.2.6`, `phpoffice/phpspreadsheet 1.29.1`,
`phpoffice/phpword 0.18.3`, `dompdf/dompdf v0.8.6` com o patch `ecidade/patches/dompdf-0.8.6-php85.patch`
(aplicado pelo `cweagans/composer-patches 1.7.3`). Documentos comparados entre 7.4 e 8.5 no guia da
demonstracao 13.

**Problema original:** mPDF 7.1.9, PhpSpreadsheet 1.8.2 e PHPWord 0.17.0 possuem requisitos PHP que excluem
PHP 8.5. Dompdf 0.8.3, `proner/phppimaco`, `aferrandini/phpqrcode` e conversores externos nao foram aprovados
funcionalmente pela auditoria.

## Doctrine DBAL e lockfile

**Situacao: FEITO.** O `composer.lock` do PR #8 tem `doctrine/dbal 2.13.9`; no 8.5 o pacote saiu do
`composer-85.json` (o Laravel 11+ altera colunas sem DBAL) e nao ha uso direto de `Doctrine\DBAL` no codigo.

**Problema original:** `doctrine/dbal` esta em `require` como `2.*`, mas nao tem entrada em `composer.lock`.

## Pacotes especificos do fornecedor

**Situacao: PARCIAL.** Os pacotes instalam e o sistema sobe no 8.5, mas o suporte nao foi confirmado pelo
fornecedor.

- O 8.5 instala os mesmos commits do 7.4: `dbseller/legacy v1.1.1` (`205b87f316`) e
  `dbseller/session dev-master` (`f3020b4630`). O lock trava o commit, entao o `dev-master` nao muda sozinho
  numa instalacao a partir do lock; muda num `composer update`.
- O repositorio do `dbseller/session` e declarado por SSH; a instalacao no 8.5 usa HTTPS
  (`docs/registro/estrutura-85.md`).
- Falta: declaracao de suporte ao PHP 8.5 pelo fornecedor (nenhum dos dois declara requisito de PHP),
  versao com tag no lugar do `dev-master` e prova de sessao/autenticacao com banco no alvo.

**Problema original:** `dbseller/legacy` e `dbseller/session` nao apresentam evidencias suficientes no lock
para aprovar PHP 8.5/Laravel 12 ou 13; a branch `dev-master` de Session e mutavel.

## Dependencias de desenvolvimento

**Situacao: FEITO.** `composer-85.lock`: `phpunit/phpunit 8.5.39`, `fakerphp/faker v1.10.0` (no lugar do
`fzaninotto/faker 1.9.2` do 7.4), `mockery/mockery 1.3.0`, `squizlabs/php_codesniffer 3.10.2`. A suite
propria roda nos dois PHP (`bash ecidade/tests/suite/rodar.sh --runtime ambos`).

**Problema original:** PHPUnit 5.7 e Faker 1.9 excluem PHP 8.5 pelas restricoes travadas. Mockery 1.3 e
PHPCS 3.9 nao foram demonstrados em execucao no alvo.

## Levantamento de descobertas da equipe

**Situacao: NAO FEITO.** O arquivo `docs/migracao-laravel/levantamento/descobertas-do-projeto.md` continua
ausente: nao existe em nenhuma branch do fork (conferido em 27/11/2026).

**Proximo passo:** pedir o arquivo ou o conteudo ao integrante que fez o levantamento e comparar cada
descoberta com os arquivos e evidencias do repositorio. Nenhum conteudo foi presumido.
