# Compatibilidade de dependencias Composer

## Escopo e criterio

Este relatorio avalia todos os requisitos diretos de `require` e `require-dev` do `composer.json` para PHP 8.5 e Laravel 12. Quando existe uma versao resolvida em `composer.lock`, ela e a versao analisada; caso contrario, considera-se a restricao declarada e registra-se a falta de evidencias. A avaliacao e estatica, baseada nas restricoes Composer e nos metadados disponiveis, nao substitui testes de integracao da aplicacao.

- **Compatível**: o requisito de plataforma admite PHP 8.5, ou os metadados do pacote incluem PHP 8.5 e nao declaram dependencia de APIs de uma versao Laravel incompatível.
- **Incompatível**: existe uma restricao de PHP/Laravel que exclui o alvo, ou a incompatibilidade foi informada como conhecida.
- **Desconhecido**: as informacoes disponiveis nao demonstram suporte ou incompatibilidade; nao deve ser interpretado como aprovado.

Laravel 12 requer PHP 8.2 ou superior e usa componentes Symfony 7.2. Portanto, as restricoes Symfony `~3.2` do projeto e os pacotes que exigem `Illuminate 5.x` nao podem compor a stack alvo. O arquivo de lock tambem nao contem entrada resolvida para `doctrine/dbal`, embora ele esteja declarado como requisito direto.

## Dependencias de producao

| Dependencia | Restricao no `composer.json` | Versao travada (se disponivel) | Classificacao | Justificativa tecnica |
|---|---|---|---|---|
| `php` | `>=5.6.4` | — | Compatível | A restricao nao tem limite superior e inclui PHP 8.5. Sozinha, porem, nao garante a compatibilidade das bibliotecas nem da aplicacao. |
| `ext-bcmath` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-calendar` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-curl` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-dom` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-fileinfo` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-json` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-openssl` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-pgsql` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-simplexml` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-soap` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-xmlwriter` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `ext-zip` | `*` | Plataforma | Compatível | Requisito de extensao nativa sem limite de versao; PHP 8.5 pode fornece-la. E necessario que esteja instalada/ativada no ambiente. |
| `aferrandini/phpqrcode` | `^1.0` | `1.0.1` | Desconhecido | A versao travada e de 2013 e esta marcada como abandonada. O requisito PHP `>=5.3.0` nao exclui 8.5, mas nao comprova que o codigo antigo funciona nessa versao. Nao ha integracao Laravel declarada. |
| `barryvdh/laravel-ide-helper` | `^2.4` | `2.4.3` | Incompatível | A versao travada exige `illuminate/console`, `filesystem` e `support` `^5.0,<5.7`; Laravel 12 fornece Illuminate 12. A restricao impede a resolucao conjunta. |
| `dbseller/legacy` | `^1.0` | `1.1.1` | Desconhecido | Pacote especifico do fornecedor sem restricao PHP ou Illuminate no lock. O nome/versao nao e evidencia suficiente de suporte a PHP 8.5 ou Laravel 12. |
| `dbseller/phinx_postgres` | `^1.3` | `1.3.0` | Incompatível | Incompatibilidade ja conhecida para o alvo PHP 8.5/Laravel 12. A versao travada e antiga e declara apenas PHP `>=5.6.4`, o que nao constitui suporte comprovado a PHP 8.5. |
| `dbseller/sdk-api-pix-bb` | `^1.0` | `1.0.0` | Incompatível | Incompatibilidade ja conhecida para o alvo. A versao travada e antiga e declara apenas PHP `>=5.5`; essa faixa aberta nao valida o codigo em PHP 8.5 nem a integracao com Laravel 12. |
| `dbseller/session` | `dev-master` | `dev-master` | Desconhecido | Pacote privado em branch mutavel e sem requisito PHP ou Illuminate registrado no lock. E necessario inspecionar o commit efetivamente instalado e testar a integracao. |
| `doctrine/dbal` | `2.*` | Nao consta no lock | Desconhecido | O projeto restringe a linha 2.x, mas nao ha versao resolvida para verificar. A compatibilidade em Laravel 12 depende dos usos de schema/migracao e do suporte da versao concreta; a declaracao isolada nao prova compatibilidade com PHP 8.5. |
| `dompdf/dompdf` | `^0.8.3` | `0.8.3` | Desconhecido | A versao travada e antiga e declara apenas PHP `>=5.4.0`, sem teto que prove ou exclua 8.5. Sem teste do parser/renderizador nesta versao, nao e possivel assegurar PHP 8.5. Nao exige APIs Laravel. |
| `guzzlehttp/guzzle` | `^6.2` | `6.5.8` | Desconhecido | A linha 6 e anterior ao alvo e declara PHP `>=5.5`, mas isso nao comprova testes em PHP 8.5. E uma biblioteca HTTP independente, sem restricao Laravel direta; verificar chamadas e dependencias efetivamente utilizadas. |
| `intervention/image` | `^2.7` | `2.7.2` | Desconhecido | A versao travada declara PHP `>=5.4.0`, mas a faixa nao comprova funcionamento em PHP 8.5. A compatibilidade do adaptador/integracao Laravel tambem precisa ser validada na versao concreta. |
| `jeremeamia/superclosure` | `^2.0` | `2.4.0` | Desconhecido | Biblioteca antiga de serializacao de closures; o requisito PHP `>=5.4` nao garante compatibilidade com mudancas de Reflection/runtime em PHP 8.5. Nenhuma compatibilidade Laravel 12 e declarada. |
| `laravel/framework` | `5.4.*` | `5.4.36` | Incompatível | A restricao fixa o framework na linha 5.4, enquanto o alvo e Laravel 12. Ela tambem fixa uma geracao anterior do ecossistema PHP e nao permite instalar Laravel 12. |
| `laravel/passport` | `^4.0` | `4.0.3` | Incompatível | A versao travada exige componentes `illuminate/*` `~5.4`; Laravel 12 fornece Illuminate 12. A restricao impede a resolucao conjunta. |
| `laravel/tinker` | `~1.0` | `1.0.10` | Incompatível | A versao travada exige Illuminate Console/Contracts/Support `~5.1\|^6.0`, incompatíveis com Illuminate 12. |
| `lcobucci/jwt` | `3.3.3` | `3.3.3` | Incompatível | O lock declara PHP `^5.6 \|\| ^7.0`, faixa que exclui PHP 8.5. |
| `league/fractal` | `0.11.0` | `0.11.0` | Desconhecido | O lock declara PHP `>=5.3`, sem teto ou garantia de testes em PHP 8.5. Nao ha dependencia Laravel declarada; o metadado nao basta para certificar o comportamento em runtime. |
| `michelf/php-markdown` | `^1.6` | `1.9.1` | Desconhecido | A versao travada declara PHP `>=5.3`, mas nao informa suporte testado a PHP 8.5. E independente de Laravel; requer teste do uso real para aprovar. |
| `mormat/php-formula-interpreter` | `1.0.0` | `1.0.0` | Desconhecido | O lock nao registra requisitos PHP nem Laravel. Sem metadados de suporte ou testes do interpretador em PHP 8.5, a classificacao nao pode ser afirmativa. |
| `mpdf/mpdf` | `v7.1.9` | `7.1.9` | Incompatível | O lock limita PHP a `^5.6 \|\| ~7.0 \|\| ~7.1 \|\| ~7.2 \|\| ~7.3`, excluindo PHP 8.5. |
| `ncjoes/office-converter` | `^1.0` | `1.0.3` | Desconhecido | O requisito PHP `>=5.4.4` nao exclui 8.5, mas nao e prova de suporte. O pacote tambem depende de executaveis externos de conversao, e nao declara compatibilidade Laravel. |
| `nfephp-org/sped-common` | `~5.0.40` | `5.0.40` | Desconhecido | A versao travada declara PHP `>=5.6`, sem faixa testada para PHP 8.5. A compatibilidade depende do codigo fiscal e de suas dependencias transitivas; Laravel nao e declarado como requisito. |
| `phpmailer/phpmailer` | `^6.5` | `6.9.1` | Desconhecido | A versao travada declara PHP `>=5.5`, mas essa faixa nao comprova suporte especifico a 8.5. O pacote e independente do framework; e preciso validar envio e configuracao no runtime alvo. |
| `phpoffice/phpspreadsheet` | `^1.08` | `1.8.2` | Incompatível | O lock declara PHP `^5.6\|^7.0`, excluindo PHP 8.5. |
| `phpoffice/phpword` | `v0.17.*` | `0.17.0` | Incompatível | O lock declara PHP `^5.3.3 \|\| ^7.0`, excluindo PHP 8.5. |
| `proner/phppimaco` | `1.3.0` | `1.3.0` | Incompatível | Incompatibilidade ja conhecida para o alvo. A versao travada e antiga e declara PHP `>=5.6`, requisito que nao demonstra suporte a PHP 8.5. |
| `pusher/pusher-php-server` | `~2.6` | `2.6.4` | Desconhecido | A versao travada declara PHP `>=5.2`, mas nao comprova funcionamento em PHP 8.5. O SDK e independente de Laravel; validar chamadas e protocolos usados pela aplicacao. |
| `silex/silex` | `^2.0` | `2.2.4` | Incompatível | Incompatibilidade ja conhecida. Alem de ser um framework descontinuado, a linha 2.2 nao e uma base compatível com Laravel 12 e a versao travada e anterior ao suporte moderno de PHP. |
| `symfony/console` | `~3.2` | `3.4.47` | Incompatível | `~3.2` restringe o pacote a Symfony 3.x; Laravel 12 requer Symfony Console 7.2. O Composer nao consegue satisfazer simultaneamente as duas restricoes. |
| `symfony/filesystem` | `~3.2` | `3.4.47` | Incompatível | `~3.2` restringe o pacote a Symfony 3.x, enquanto Laravel 12 depende da linha Symfony 7.2. |
| `symfony/polyfill-php56` | `^1.1` | `1.19.0` | Desconhecido | O lock declara PHP `>=5.3.3`, mas e uma versao antiga sem garantia explicita para PHP 8.5. Nao declara dependencia Laravel; verificar se ainda e necessaria e se a arvore de dependencias atual a resolve. |
| `symfony/polyfill-php70` | `^1.1` | `1.19.0` | Desconhecido | O lock declara PHP `>=5.3.3`, mas e uma versao antiga sem garantia explicita para PHP 8.5. Nao declara dependencia Laravel; verificar se ainda e necessaria e se a arvore de dependencias atual a resolve. |
| `symfony/process` | `~3.2` | `3.4.47` | Incompatível | `~3.2` restringe o pacote a Symfony 3.x, em conflito com a linha 7.2 exigida por Laravel 12. |
| `symfony/validator` | `~3.2` | `3.4.47` | Incompatível | `~3.2` restringe o pacote a Symfony 3.x, em conflito com a linha 7.2 exigida por Laravel 12. |
| `symfony/yaml` | `~3.2` | `3.4.47` | Incompatível | `~3.2` restringe o pacote a Symfony 3.x, em conflito com a linha 7.2 exigida por Laravel 12. |
| `vlucas/valitron` | `^1.4` | `1.4.11` | Desconhecido | O lock declara PHP `>=5.3.2`, sem teto que exclua 8.5 nem evidencia de testes nessa versao. Nao ha integracao Laravel obrigatoria declarada. |
| `zendframework/zend-eventmanager` | `2.2.10` | `2.2.10` | Desconhecido | O pacote legado declara PHP `>=5.3.3` e esta abandonado em favor de Laminas. A faixa nao comprova PHP 8.5; nao ha dependencia Laravel declarada. |

## Dependencias de desenvolvimento

| Dependencia | Restricao no `composer.json` | Versao travada | Classificacao | Justificativa tecnica |
|---|---|---|---|---|
| `filp/whoops` | `^2.5` | `2.15.4` | Compatível | O lock declara PHP `^5.5.9 \|\| ^7.0 \|\| ^8.0`, que inclui PHP 8.5. E uma ferramenta de tratamento de erros sem acoplamento de versao a Illuminate. |
| `fzaninotto/faker` | `^1.9` | `1.9.2` | Incompatível | O lock declara PHP `^5.3.3 \|\| ^7.0`, excluindo PHP 8.5; o pacote tambem esta marcado como abandonado. |
| `mockery/mockery` | `1.3.0` | `1.3.0` | Desconhecido | O lock declara PHP `>=5.6.0`, mas nao confirma suporte da versao 1.3.0 a PHP 8.5. Como framework de mocks, pode precisar de atualizacao para rodar a suite sobre as APIs atuais. |
| `phpunit/phpunit` | `^5.7` | `5.7.27` | Incompatível | O lock declara PHP `^5.6 \|\| ^7.0`, excluindo PHP 8.5. PHPUnit 5 tambem e anterior a versoes adequadas para a suite de Laravel 12. |
| `squizlabs/php_codesniffer` | `^3.5` | `3.9.0` | Desconhecido | O lock declara apenas PHP `>=5.4.0`; isso nao garante execucao em PHP 8.5. E uma ferramenta sem acoplamento a Laravel, mas deve ser executada no interpretador alvo para validar. |

## Conclusao

O `composer.json` atual nao pode ser usado como base instalavel para PHP 8.5 e Laravel 12: fixa Laravel 5.4, Passport/Tinker e ferramentas Laravel vinculados ao Illuminate 5/6, Symfony 3.x em conflito com Symfony 7.2, e varias bibliotecas com restricoes que excluem PHP 8. Tambem permanecem dependencias sem evidencia suficiente, especialmente os pacotes privados e bibliotecas antigas.

Antes de qualquer migracao, sera necessario atualizar/remover as dependencias classificadas como **Incompatível**, resolver novamente o lock para os alvos e validar os pacotes **Desconhecido** com testes automatizados e smoke tests nos fluxos usados pelo projeto. A classificacao **Compatível** para requisitos de plataforma pressupoe que as extensoes estejam instaladas; nao representa validacao funcional da aplicacao inteira.