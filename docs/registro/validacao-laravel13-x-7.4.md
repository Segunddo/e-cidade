# Validação com o Laravel 13: a medição da validação do Laravel 8 repetida (7.4 × 8.5), sem banco

Repete, com o `laravel/framework` 13.43.0 do composer do 8.5, os 1.350 casos de form request e as 348 combinações regra × valor medidos com o Laravel 8.73.2 em `validacao-laravel8-7.4-x-8.5.md`. **Nenhum banco e nenhuma rede** (`--network none`).

**Resultado:** com o Laravel 13 no PHP 8.5 contra o Laravel 8 do PR no PHP 7.4, as **348 combinações regra × valor são iguais** (o `TypeError` do `digits` com array some). Nos form requests, **23 dos 1.350 casos diferiam em 3 causas** (seção 3); a causa **(a)**, 21 casos em 6 classes (o Laravel 13 passa a usar as mensagens de `messages()` escritas só com o nome do campo, que o Laravel 8 ignora), foi **resolvida no próprio arquivo, sem mudar o 7.4** (seção 4). Sobram **2 casos, só registrados**: **(b)** `after_or_equal` com o campo de referência ausente deixa de reprovar; **(c)** `validated()` deixa de devolver chaves que nenhuma regra nomeia dentro de um campo `array`. Em nenhum dos 23 muda se a requisição passa ou falha.

## 1. Como foi medido

Contêineres descartáveis, `--network none`, nas imagens construídas de `docker/php74-apache` (`t102-php74-ref`, PHP 7.4.33) e `docker/php85-apache` (`ecidade-login-php85`, PHP 8.5.12), com `ecidade/` montado só leitura em `/app`, o vendor em `/app/vendor` e `VENDOR=/app/vendor` (os dois scripts aceitam `$VENDOR`; sem a variável usam o `vendor/` ao lado deles, como antes).

| Execução | PHP | Vendor | Arquivos de saída |
|---|---|---|---|
| `l8-74` (referência) | 7.4.33 | `composer install` do `ecidade/composer.lock` do PR: `laravel/framework` 8.73.2 | `medir-l8-74.json`, `matriz-l8-74.json` |
| `l8-85` (controle: só muda o PHP) | 8.5.12 | vendor 8.5 anterior à T-119: `laravel/framework` 8.73.2 | `medir-l8-85.json`, `matriz-l8-85.json` |
| `l13-85` | 8.5.12 | `composer-85.lock` com Laravel 13: `laravel/framework` 13.43.0, `laravel/passport` 13.12.0, `nesbot/carbon` 3.15.1 (`composer-85.sh install --no-scripts --ignore-platform-req=php+`) | `medir-l13-85.json`, `matriz-l13-85.json` |

```bash
# da raiz do repositorio; D = pasta com os dois scripts (cp scratchpad/laravel8_validacao_*.php $D/) e $D/out gravavel
mkdir -p ecidade/vendor   # ponto de montagem do vendor: sem ele o docker falha (rc 125, "read-only file system") num checkout novo
for sc in medir matriz; do
  docker run --rm --network none -v $D:/s:ro -v $PWD/ecidade:/app:ro -v <vendor>:/app/vendor:ro -v $D/out:/o -e VENDOR=/app/vendor -w /app \
    <imagem> php -d memory_limit=1G /s/laravel8_validacao_$sc.php /app /o/$sc-<execucao>.json
done
python3 scratchpad/laravel13_validacao_compara.py $D/out/medir-l8-74.json $D/out/medir-l13-85.json   # idem para a matriz
```
O laco roda os dois scripts para **uma** execucao; repita-o 3 vezes (`l8-74`, `l8-85` e `l13-85`), cada uma com a imagem e o vendor da tabela acima: 6 `docker run` ao todo. Os scripts gravam o JSON no arquivo dado como 2o argumento (`/o`, gravavel); por isso o bloco usa `docker run` direto em vez do `docker/composer-85/roda-isolado.sh`, que so devolve a saida padrao.

O inventário é o mesmo da medição do Laravel 8: 288 nomes de form request, 270 com regras, 54 com regra de banco (`exists`/`unique`, tiradas e listadas), 14 que não carregam isoladas (`ECidade\Enum\…`, `ECidade\Lib\Session\DefaultSession`; falham pela mesma causa nas três execuções, só muda a aspa: `Class 'X'` no 7.4, `Class "X"` no 8.5). As 5 entradas por classe (vazia, válida, chave obrigatória ausente, campos vazios, campos array) e os 12 valores da matriz são os de antes.

## 2. Controle: o que muda só pelo PHP

`l8-74` × `l8-85` (mesmo Laravel 8.73.2): 3 casos de 1.350 e 4 combinações de 348 diferem, todos `digits` com array (`TypeError: preg_match(): Argument #2 ($subject) must be of type string, array given` no 8.5), o resultado já registrado. O 8.5 acusa 66 `Deprecated` com este vendor (0 no 7.4).

## 3. Laravel 8 (7.4) × Laravel 13 (8.5)

| | `l8-74` × `l13-85` |
|---|---|
| combinações regra × valor da matriz | **348 de 348 iguais** |
| casos de form request, antes da correção da causa (a) | 1.327 de 1.350 iguais; 23 diferentes |
| casos de form request, **depois** da correção da causa (a) | **1.348 de 1.350 iguais; 2 diferentes** (causas (b) e (c)) |
| classes, regras sem `rules()`, regras de banco, classes que não leram | iguais |
| `Deprecated` no 8.5 | 1 (`utf8_encode()`, `std/DBString.php` via `BaseFormRequest::messages()`); 0 do framework |

A lista dos 23 (classe, entrada, causa, campos que mudam) está em `validacao-laravel13-diferencas.tsv`.

### `digits` com array deixa de falhar

Na matriz, `digits:2` e `digits:4` com array e array aninhado dão o mesmo resultado que no 7.4 (reprova com "deve ter N dígitos"). Causa: `Validation/Concerns/ValidatesAttributes.php:757-763` do Laravel 13 só chama `preg_match` quando `is_numeric($value) || is_string($value)`; o 8.73.2 chamava sempre. Com isso as 3 classes de `Financeiro/Tesouraria/Requests` e a regra de `MapeamentoEmpenhoRPContaController` deixam de lançar `TypeError`.

### Causa (a): chave de mensagem que o Laravel 13 passa a casar com o campo (21 casos, 6 classes)

`messages()` com chave igual ao nome do campo, sem a regra (`'exercicio' => 'Você deve informar o exercício.'`), e uma segunda forma, o curinga `'receitas.*'` quando o campo que falha é um item (`receitas.0`):

- Laravel 8.73.2 (`FormatsMessages::getFromLocalArray`, `:94`): procura `campo.regra` e `regra` (o curinga vira `([^.]*)` para um nível). A chave só do campo **nunca vale** (o usuário vê `O campo exercicio é obrigatório.`, `exercicio deve ter 4 dígitos.`). O curinga `'campo.*'` **vale** para as regras do próprio campo (`exercicio.*` dá a mensagem do autor para `exercicio` com `digits`) e **não** casa com `campo.0.regra`.
- Laravel 13 (`:104`): a lista de chaves ganha `$attribute` (e `campo.regra_curta`): a mensagem escrita só com o nome do campo vale para **qualquer regra** que falhe nele, e o curinga `'receitas.*'` passa a casar com o item `receitas.0` (a chave do campo).

| Classe (`App\Domain\…`) | Chaves só do campo | Entradas que mudam |
|---|---|---|
| `Financeiro\Empenho\Requests\ConferenciaExtraOrcamentariaRequest` | `tipo` | arrays, vazia, vazios |
| `Financeiro\Tesouraria\Requests\ConfiguracaoReceitasDecendioRequest` | `receitas.*` (curinga que passa a casar com o item `receitas.0`) | arrays, vazios |
| `Financeiro\Tesouraria\Requests\GetDetalhamentoDecendioRequest` | `exercicio`, `instituicao`, `dataInicial`, `dataFinal`, … | arrays, ausente, vazia, vazios |
| `Financeiro\Tesouraria\Requests\GetLancamentosDecendioRequest` | as mesmas | arrays, ausente, vazia, vazios |
| `Saude\Ambulatorial\Requests\UnidadesEncaminhadorasRequest` | `ativo`, `descricao` | arrays, ausente, vazia, vazios |
| `Saude\Ambulatorial\Requests\UnidadesOrigemRequest` | `ativo`, `descricao` | arrays, ausente, vazia, vazios |

Só o **texto** da mensagem muda (os campos `passa` e os nomes dos campos com erro ficam iguais). Em cinco das seis classes as mensagens do autor nunca apareciam no Laravel 8 e no 13 passam a aparecer; em `ConfiguracaoReceitasDecendioRequest` as três chaves (`receitas.*`, `desdobramentos.*`, `exercicio.*`) já valiam no 8 para as regras do próprio campo, e só `receitas.*` muda no 13, para os itens `receitas.0`, `receitas.1`.
O 7.4 não muda. Resolvida na seção 4.

### Causa (b): `after_or_equal` com o campo de referência ausente (1 caso)

`PeriodoSlipRequest`, entrada `ausente` (`dataInicial` omitido; `dataFinal` => `sometimes|date_format:Y-m-d|after_or_equal:dataInicial`):
no Laravel 8 `dataFinal` também reprova ("deve ser uma data posterior ou igual a data inicial"); no 13 só `dataInicial` reprova ("Deve ser informada."). Causa: `ValidatesAttributes.php:334-336` do Laravel 13: `checkDateTimeOrder()` devolve `true` quando o campo de referência é `null`; o 8.73.2 (`:267-271`) devolvia falso. A requisição continua inválida (`dataInicial` é `required`).

### Causa (c): `validated()` e chaves sem regra sob um campo `array` (1 caso)

`RelatorioRequest`, entrada `valida` (dados montados pela medição: `layout` = `[1, nome, versao, …]`, com a chave `0` que nenhuma regra nomeia): o `validated()` do Laravel 8 devolve `layout[0]` e `layout.margem[0]`; o do 13 não.
Causa: `Validation/Factory.php:74` (`excludeUnvalidatedArrayKeys = true` no Laravel 13; sem valor, falso, no 8.73.2) e `Validator.php:679-689`, que pula o campo pai `array` quando há regras aninhadas e monta o resultado só das regras filhas. O código do PR chama `validated()` 0 vezes (`validacao-laravel8-7.4-x-8.5.md`), então hoje não há efeito; vale se alguém passar a usar.

## 4. Correção da causa (a): tirar de `messages()` as chaves só de atributo

No próprio arquivo, nas 6 classes:
- `ConferenciaExtraOrcamentariaRequest`: tirada a chave `'tipo'`;
- `GetDetalhamentoDecendioRequest`, `GetLancamentosDecendioRequest`, `UnidadesEncaminhadorasRequest` e `UnidadesOrigemRequest`: todas as chaves eram só de campo, então `messages()` passa a `return [];`;
- `ConfiguracaoReceitasDecendioRequest`: `'receitas.*'` virou `'receitas.required'`, `'receitas.array'` e `'receitas.min'` (as três regras de `receitas`), com o mesmo texto. No Laravel 8 o curinga já valia para essas três regras e não para `receitas.0`; no 13 passava a valer também para `receitas.0` (a chave do campo). `'desdobramentos.*'` e `'exercicio.*'` não casam com o campo sozinho e ficam como estão.

**Prova (sem banco, imagens do projeto, mesmos 1.350 casos):** o 7.4 antes e depois: **0 casos diferentes** (`medir-l8-74.json` antes × depois; as mesmas 270 classes, 54 regras de banco, 14 que não leram). Depois, `l8-74` × `l13-85`: **2 casos diferentes** (as causas (b) e (c)); a matriz continua em 348 de 348. O controle `l8-85` × `l8-74` segue com os mesmos 3 casos de `digits`.

**O que se perdeu e fica para o grupo decidir.** O autor escreveu mensagens que o Laravel 8 nunca mostrou, e agora elas não existem no código. Reativá-las é decisão do grupo (com a chave `campo.regra`, o que muda o 7.4). Textos tirados:

| Classe | Campo | Texto |
|---|---|---|
| `ConferenciaExtraOrcamentariaRequest` | `tipo` | O tipo da conferencia deve ser informada. |
| `GetDetalhamentoDecendioRequest` | `exercicio` / `instituicao` / `dataInicial` / `dataFinal` / `reduzidos` / `desdobramento` / `conta_pagadora` | Você deve informar o exercício. / a instituição. / a data inicial. / a data final. / o(s) reduzido(s). / o desdobramento. / a conta pagadora. |
| `GetLancamentosDecendioRequest` | `exercicio` / `instituicao` / `dataInicial` / `dataFinal` | os quatro primeiros do item acima |
| `UnidadesEncaminhadorasRequest`, `UnidadesOrigemRequest` | `ativo` / `descricao` | O campo ativo é obrigatório e deve ser um logico / O campo descrição é obrigatório e deve ser uma string |

As causas **(b)** e **(c)** não foram corrigidas: são comportamento novo do framework em casos em que a requisição já é inválida (b) ou que o código não usa (c); o Laravel 13 é o gabarito delas.
Os dois scripts de medição passam a aceitar `$VENDOR` (sem a variável, o mesmo comportamento de antes).

## Limites

- Regras `exists`/`unique` (54 classes, 82 regras) e as 14 classes que não carregam isoladas continuam sem medição (mesmos limites da medição do Laravel 8).
- Mede o validador isolado (`Validator` e as regras reais), não a requisição HTTP inteira: o `FormRequest` do Laravel 13 também mudou (`failedValidation`, `prepareForValidation`), mas isso depende de container e sessão e fica para a medição com a aplicação de pé.
- O vendor `l8-85` do controle é o do 8.5 anterior à troca para o Laravel 13 (Laravel 8.73.2), só para separar o efeito do PHP do efeito do framework.
