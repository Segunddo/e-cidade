# Compatibilidade das dependencias Composer: PHP 8.5 e Laravel 12

## Escopo e categorias

Esta revisao classifica cada requisito direto de `require` e `require-dev` em `composer.json` exatamente uma vez. Distingue a versao travada no `composer.lock` da faixa permitida pelo manifesto. A classificacao trata metadados e resolucao, nao garante o funcionamento da aplicacao.

Quando ha lock, a avaliacao parte da versao travada. Se ela estiver bloqueada, mas a restricao permitir outra versao com metadata favoravel ao alvo, a categoria do requisito fica **Desconhecido** ate que essa versao seja efetivamente resolvida; a tabela ainda registra o bloqueio da travada. Sem lock, a avaliacao usa a faixa declarada e as evidencias disponiveis.

- **Compatível**: as restricoes e evidencias consultadas sao coerentes com PHP 8.5 e, quando aplicavel, Laravel 12. Nao significa que houve teste funcional.
- **Incompatível**: uma restricao comprovada impede a versao travada ou toda a faixa permitida de coexistir com PHP 8.5/Laravel 12.
- **Desconhecido**: nao ha evidencia suficiente, ou o lock esta bloqueado mas outra versao permitida pode ser viavel.

`Pendente de teste` e observacao adicional, nao uma quarta classificacao. Um requisito PHP `>=5.x` nao prova suporte testado a PHP 8.5. O manifesto fixa Laravel `5.4.*`; o lock descreve a stack atual, nao uma solucao ja resolvida para Laravel 12. Laravel 12 requer PHP `^8.2`, Guzzle `^7.8.2` e Symfony Console/Process `^7.2`. `composer validate` nao foi executado e seu resultado e desconhecido.

## Producao: `require`

| Requisito direto | Restricao do manifesto | Versao travada | Categoria | Evidencia e proxima verificacao |
|---|---|---|---|---|
| `php` | `>=5.6.4` | Plataforma | Compatível | A restricao raiz inclui PHP 8.5; nao avalia dependencias nem codigo. Confirmar runtime no destino. |
| `ext-bcmath` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-calendar` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-curl` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-dom` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-fileinfo` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-json` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-openssl` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-pgsql` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-simplexml` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-soap` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-xmlwriter` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `ext-zip` | `*` | Plataforma | Compatível | Sem limite de versao declarado. Confirmar extensao instalada no runtime de destino. |
| `aferrandini/phpqrcode` | `^1.0` (>=1.0.0, <2.0.0) | `1.0.1` | Desconhecido | Lock declara PHP >=5.3, sem teto que exclua 8.5, mas sem evidencia de testes nessa versao. Testar QR codes usados. |
| `barryvdh/laravel-ide-helper` | `^2.4` (>=2.4.0, <3.0.0) | `2.4.3` | Incompatível | A travada limita Illuminate a ^5.0,<5.7. A maior 2.x consultada, 2.15.1, aceita Illuminate 9/10, nao 12; a versao 3.x que lista Illuminate 12 fica fora de ^2.4. O bloqueio e Laravel/Illuminate, nao PHP. Confirmar metadata do release 2.x ao atualizar. |
| `dbseller/legacy` | `^1.0` (>=1.0.0, <2.0.0) | `1.1.1` | Desconhecido | Sem requisito PHP no lock; a descricao refere compatibilidade historica PHP 5.3 a 7.0, mas nao prova nem exclui PHP 8.5. Inspecionar codigo/commit e testar usos. |
| `dbseller/phinx_postgres` | `^1.3` (>=1.3.0, <2.0.0) | `1.3.0` | Incompatível | Exige `robmorgan/phinx ^0.10`; lock fixa Phinx 0.10.8, que requer Symfony Console ^2.8, ^3 ou ^4. Laravel 12 requer Console ^7.2. Bloqueio transitivo comprovado. Avaliar substituicao e migrations existentes. |
| `dbseller/sdk-api-pix-bb` | `^1.0` (>=1.0.0, <2.0.0) | `1.0.0` | Incompatível | Metadata exata exige Guzzle ^6.2; Laravel 12 exige ^7.8.2. As faixas nao se cruzam. Confirmar alternativa do fornecedor e testar Pix em sandbox. |
| `dbseller/session` | `dev-master` | `dev-master`, commit `f3020b4…` | Desconhecido | Lock declara somente ext-json; branch mutavel e sem requisito PHP/Illuminate. Inspecionar commit e testar integracao de sessao. |
| `doctrine/dbal` | `2.*` (>=2.0, <3.0) | Ausente do lock | Desconhecido | Requisito direto sem versao resolvida. `composer validate` nao foi executado; causa e resultado desconhecidos. Verificar necessidade e usos antes de definir versao. |
| `dompdf/dompdf` | `^0.8.3` (>=0.8.3, <0.9.0) | `0.8.3` | Desconhecido | Lock declara PHP >=5.4, que nao demonstra PHP 8.5. A faixa nao permite Dompdf 1/2/3. Testar PDFs e avaliar versao/substituto. |
| `guzzlehttp/guzzle` | `^6.2` (>=6.2, <7.0) | `6.5.8` | Incompatível | Laravel 12 requer Guzzle ^7.8.2; o requisito raiz limita a 6.x e o SDK Pix exige 6.x. O motivo nao e o requisito PHP >=5.5. Resolver cliente/SDK. |
| `intervention/image` | `^2.7` (>=2.7.0, <3.0.0) | `2.7.2` | Desconhecido | PHP >=5.4 e provider Laravel nao certificam PHP 8.5 nem Laravel 12. Testar provider e operacoes usadas. |
| `jeremeamia/superclosure` | `^2.0` (>=2.0.0, <3.0.0) | `2.4.0` | Desconhecido | PHP >=5.4 nao certifica Reflection/serializacao em 8.5 ou Laravel 12. Confirmar uso e testar closures serializadas. |
| `laravel/framework` | `5.4.*` (>=5.4.0, <5.5.0) | `5.4.36` | Incompatível | Manifesto e lock fixam Laravel 5.4, nao Laravel 12. Mudar alvo exige alterar restricao e tratar breaking changes. |
| `laravel/passport` | `^4.0` (>=4.0.0, <5.0.0) | `4.0.3` | Incompatível | Metadata travada exige Illuminate ~5.4. O codigo usa Passport no provider, middleware e User. Atualizar pacote/codigo e testar OAuth. |
| `laravel/tinker` | `~1.0` (>=1.0.0, <2.0.0) | `1.0.10` | Incompatível | Metadata exige Illuminate ~5.1 ou ^6.0, nao Illuminate 12. Escolher versao adequada ao alvo. |
| `lcobucci/jwt` | `3.3.3` (exata) | `3.3.3` | Incompatível | Requisito PHP ^5.6 ou ^7.0 exclui 8.5. Avaliar atualizacao e compatibilidade de tokens/claims existentes. |
| `league/fractal` | `0.11.0` (exata) | `0.11.0` | Desconhecido | PHP >=5.3 nao prova PHP 8.5. Nao foi estabelecida dependencia de APIs Laravel; testar transformers/serializers usados. |
| `michelf/php-markdown` | `^1.6` (>=1.6.0, <2.0.0) | `1.9.1` | Desconhecido | PHP >=5.3 nao comprova PHP 8.5. Testar conversoes Markdown usadas. |
| `mormat/php-formula-interpreter` | `1.0.0` (exata) | `1.0.0` | Desconhecido | Lock sem requisito PHP/Laravel. Inspecionar codigo exato e testar formulas de negocio representativas. |
| `mpdf/mpdf` | `v7.1.9` (exata) | `7.1.9` | Incompatível | Metadata exata limita PHP a 5.6 e PHP 7.0-7.3; exclui PHP 8.5. Escolher versao/substituto e testar PDFs. |
| `ncjoes/office-converter` | `^1.0` (>=1.0.0, <2.0.0) | `1.0.3` | Desconhecido | PHP >=5.4.4 nao prova 8.5; depende tambem de executaveis externos. Testar formatos, binarios e configuracao no destino. |
| `nfephp-org/sped-common` | `~5.0.40` (>=5.0.40, <5.1.0) | `5.0.40` | Desconhecido | PHP >=5.6 nao e evidencia de teste em 8.5. Validar fluxos fiscais e dependencias usadas. |
| `phpmailer/phpmailer` | `^6.5` (>=6.5.0, <7.0.0) | `6.9.1` | Desconhecido | PHP >=5.5 nao prova PHP 8.5. Testar transports, TLS e templates usados. |
| `phpoffice/phpspreadsheet` | `^1.08` (>=1.8.0, <2.0.0) | `1.8.2` | Desconhecido | A travada exige PHP ^5.6 ou ^7.0, excluindo 8.5. Mas ^1.08 permite 1.x posteriores: metadata oficial 1.29.2/1.30.0 declara ^7.4 ou ^8.0, faixa Composer que inclui 8.5. Nao se condena a faixa inteira pelo lock. Resolver versao candidata e testar planilhas; funcionalidade pendente. |
| `phpoffice/phpword` | `v0.17.*` (>=0.17.0, <0.18.0) | `0.17.0` | Incompatível | Metadata 0.17.0 declara PHP ^5.3.3 ou ^7.0, excluindo 8.5. A restricao permite apenas 0.17.x. Atualizar/substituir e testar documentos. |
| `proner/phppimaco` | `1.3.0` (exata) | `1.3.0` | Desconhecido | Metadata exata exige PHP >=5.6, endroid/qr-code ^2.5, mPDF ^7.1 e Picqer barcode ^0.2.0. Isso nao prova suporte PHP 8.5. A informacao inicial diz bloqueado, mas mPDF 7.1.9 prova o bloqueio do requisito mPDF direto, nao uma falha propria do Pimaco; ^7.1 aceita outras 7.x. Testar etiquetas com mPDF escolhido. |
| `pusher/pusher-php-server` | `~2.6` (>=2.6.0, <3.0.0) | `2.6.4` | Desconhecido | PHP >=5.2 nao prova 8.5. Laravel 12 apenas sugere SDKs Pusher atuais para driver opcional. Confirmar uso e validar protocolo/autenticacao. |
| `silex/silex` | `^2.0` (>=2.0.0, <3.0.0) | `2.2.4` | Incompatível | Metadata exata limita HttpFoundation, HttpKernel, Routing e EventDispatcher a Symfony 2.8/3.x; Laravel 12 exige HttpFoundation/HttpKernel/Routing ^7.2. Bloqueio comprovado. |
| `symfony/console` | `~3.2` (>=3.2, <4.0) | `3.4.47` | Incompatível | Laravel 12 exige Console ^7.2; a restricao raiz admite somente 3.x. Bloqueio direto. |
| `symfony/filesystem` | `~3.2` (>=3.2, <4.0) | `3.4.47` | Desconhecido | Nao aparece como requisito obrigatorio de Laravel 12 na metadata oficial; e sugerido para links simbolicos relativos. Pode conflitar com outro consumidor, mas cadeia nao comprovada. Testar solver/uso. |
| `symfony/polyfill-php56` | `^1.1` (>=1.1.0, <2.0.0) | `1.19.0` | Desconhecido | PHP >=5.3.3 nao prova funcionamento em 8.5. Confirmar necessidade e versao resolvida. |
| `symfony/polyfill-php70` | `^1.1` (>=1.1.0, <2.0.0) | `1.19.0` | Desconhecido | PHP >=5.3.3 nao prova funcionamento em 8.5. Confirmar necessidade e versao resolvida. |
| `symfony/process` | `~3.2` (>=3.2, <4.0) | `3.4.47` | Incompatível | Laravel 12 exige Process ^7.2; a restricao raiz admite somente 3.x. Bloqueio direto. |
| `symfony/validator` | `~3.2` (>=3.2, <4.0) | `3.4.47` | Desconhecido | Validator nao aparece entre requisitos obrigatorios Laravel 12 na metadata consultada. Pode haver outro consumidor, mas cadeia nao foi comprovada. Testar solver/uso. |
| `symfony/yaml` | `~3.2` (>=3.2, <4.0) | `3.4.47` | Desconhecido | Yaml nao aparece como requisito obrigatorio Laravel 12. Phinx 0.10 aceita 2.8/3/4; seu conflito com Laravel decorre de Console. Verificar outros consumidores/uso YAML. |
| `vlucas/valitron` | `^1.4` (>=1.4.0, <2.0.0) | `1.4.11` | Desconhecido | PHP >=5.3.2 nao comprova 8.5. Testar validacoes usadas pelo projeto. |
| `zendframework/zend-eventmanager` | `2.2.10` (exata) | `2.2.10` | Desconhecido | PHP >=5.3.3 nao prova 8.5; metadata nao declara incompatibilidade Laravel 12. Verificar consumidores/necessidade. Abandono nao prova falha. |

## Desenvolvimento: `require-dev`

| Requisito direto | Restricao do manifesto | Versao travada | Categoria | Evidencia e proxima verificacao |
|---|---|---|---|---|
| `filp/whoops` | `^2.5` (>=2.5.0, <3.0.0) | `2.15.4` | Compatível | Metadata travada declara PHP ^5.5.9, ^7.0 ou ^8.0, faixa Composer que inclui 8.5; sem acoplamento Illuminate declarado. Pendente de teste no ambiente dev. |
| `fzaninotto/faker` | `^1.9` (>=1.9.0, <2.0.0) | `1.9.2` | Incompatível | Metadata limita PHP a ^5.3.3 ou ^7.0, excluindo 8.5 nas instalacoes com dev dependencies. Producoes com `--no-dev` tem impacto distinto. Atualizar e testar factories. |
| `mockery/mockery` | `1.3.0` (exata) | `1.3.0` | Desconhecido | PHP >=5.6 nao prova execucao em 8.5 nem compatibilidade com suite Laravel 12. Validar com os testes. |
| `phpunit/phpunit` | `^5.7` (>=5.7.0, <6.0) | `5.7.27` | Incompatível | Versao travada exige PHP ^5.6 ou ^7.0; a faixa direta nao alcanca PHPUnit moderno. Laravel 12 recomenda PHPUnit 11. Atualizar e adaptar suite. |
| `squizlabs/php_codesniffer` | `^3.5` (>=3.5.0, <4.0) | `3.9.0` | Desconhecido | PHP >=5.4 nao prova execucao em 8.5. Validar PHPCS, regraset e plugins. |

Dependencias em `require-dev` podem ser omitidas em producao com `--no-dev`; seus bloqueios continuam relevantes para desenvolvimento e CI.

## Conflitos comprovados

- **Laravel/Illuminate:** Laravel 12 nao coexiste com Passport 4.0.3 (Illuminate ~5.4), Tinker 1.0.10 (Illuminate ~5.1 ou ^6.0) e IDE Helper 2.x consultado ate Illuminate 10. O requisito raiz do framework continua fixado em 5.4.*.
- **Symfony:** Laravel 12 exige Console, Process, HttpFoundation, HttpKernel e Routing em ^7.2. Os pins diretos Console ~3.2 e Process ~3.2 conflitam. Silex 2.2.4 exige HttpFoundation/HttpKernel/Routing 2.8/3.x. Phinx 0.10.8 exige Console ate 4.x. Nao se afirma que Filesystem, Validator ou Yaml sejam requisitos obrigatorios Laravel 12; essas linhas ficam Desconhecido.
- **Guzzle/Pix:** Laravel 12 → Guzzle ^7.8.2; SDK BB 1.0.0 → Guzzle ^6.2. Faixas sem intersecao.
- **Phinx:** `dbseller/phinx_postgres 1.3.0` → Phinx ^0.10 → Phinx 0.10.8 → Symfony Console ^2.8/^3/^4; Laravel 12 → Console ^7.2.
- **PHP excluido no lock:** `lcobucci/jwt 3.3.3`, mPDF 7.1.9, PhpSpreadsheet 1.8.2 e PHPWord 0.17.0 excluem PHP 8.5. PhpSpreadsheet permanece Desconhecido para a faixa declarada porque 1.x posterior pode aceitar PHP 8.x. Faker 1.9.2 e PHPUnit 5.7.27 bloqueiam dev install. PhPimaco requer mPDF ^7.1; nao deduzir incompatibilidade propria apenas do pin atual mPDF.

Essas sao conclusoes sobre restricoes de resolucao, nao provas de falha funcional. Nenhum teste, instalacao/atualizacao Composer ou migration foi executado. Testes futuros: OAuth/Passport, Pix BB, PDFs, planilhas, documentos, email, conversoes externas, sessoes e fluxos de negocio que usam os pacotes.

## Consistencia e pendencias

- `doctrine/dbal` e requisito direto `2.*`, mas nao tem entrada em `composer.lock`. Divergencia confirmada por leitura. `composer validate` nao foi executado; causa e resultado nao conhecidos.
- Lock registra versoes atuais; nao prova que todas as versoes permitidas tem o mesmo suporte. PhpSpreadsheet demonstra essa diferenca.
- Extensoes, executaveis externos e comportamento funcional no PHP 8.5 nao foram testados.
- PhPimaco foi inicialmente apontado como bloqueado, mas metadata so confirma requisito PHP aberto e dependencia de mPDF ^7.1. Classificacao individual permanece Desconhecido; o mPDF 7.1.9 fixo e Incompatível com PHP 8.5.
- O levantamento de descobertas da equipe nao foi usado como evidencia nova; segue pendente se nao estiver disponivel no repositorio.

## Fontes

Arquivos do projeto: `composer.json` (secoes `require` e `require-dev`), `composer.lock`, `compatibilidade-composer.md` (relatorio original na raiz), `app/Domain/Tributario/Arrecadacao/Pix/Bancos/BancoDoBrasil.php`, `app/Providers/AuthServiceProvider.php` e `app/User.php`.

- Laravel 12, suporte/releases: https://laravel.com/docs/12.x/releases
- Laravel 12, upgrade: https://laravel.com/docs/12.x/upgrade
- Metadata Laravel 12: https://raw.githubusercontent.com/laravel/framework/12.x/composer.json
- Composer, lock/instalacao: https://getcomposer.org/doc/01-basic-usage.md
- Composer, schema: https://getcomposer.org/doc/04-schema.md
- IDE Helper, versoes: https://packagist.org/packages/barryvdh/laravel-ide-helper
- IDE Helper 2.15.1: https://raw.githubusercontent.com/barryvdh/laravel-ide-helper/v2.15.1/composer.json
- IDE Helper 3.x (fora de ^2.4): https://raw.githubusercontent.com/barryvdh/laravel-ide-helper/3.x/composer.json
- Silex 2.2.4: https://raw.githubusercontent.com/silexphp/Silex/v2.2.4/composer.json
- SDK Pix BB 1.0.0: https://raw.githubusercontent.com/DBSeller/sdk-api-pix-bb/1.0.0/composer.json
- Phinx PostgreSQL 1.3.0: https://raw.githubusercontent.com/DBSeller/PhinxPostgres/v1.3.0/composer.json
- Phinx 0.10.8: https://packagist.org/packages/robmorgan/phinx
- mPDF 7.1.9: https://raw.githubusercontent.com/mpdf/mpdf/v7.1.9/composer.json
- PhPimaco 1.3.0: https://raw.githubusercontent.com/PronerInformatica/phppimaco/v1.3.0/composer.json
- PhpSpreadsheet 1.29.2: https://raw.githubusercontent.com/PHPOffice/PhpSpreadsheet/1.29.2/composer.json
- PhpSpreadsheet 1.30.0: https://raw.githubusercontent.com/PHPOffice/PhpSpreadsheet/1.30.0/composer.json
- PHPWord 0.17.0: https://raw.githubusercontent.com/PHPOffice/PHPWord/0.17.0/composer.json

**Resumo:** 54 requisitos diretos: 14 Compatível, 15 Incompatível e 25 Desconhecido. Classificacao de requisitos/metadados nao e aprovacao funcional da aplicacao.
