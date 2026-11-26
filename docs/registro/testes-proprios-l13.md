# Testes proprios (`ecidade/tests`) com o Laravel 13 no 8.5, sem banco (PHP8-71, T-137, 20/11/2026)

**Resumo:** com o vendor do 8.5 da integracao em Laravel 13.43.0 + Passport 13.12.0 (T-119), a suite sem banco da
`testes-proprios-85.md` da **os mesmos numeros** de antes, com o Laravel 8.73.2: 520 testes nos dois runtimes, 1065
asserc. no 7.4 e 1051 no 8.5, 2 falhas nos dois e 5 erros so no 8.5 (os mesmos `$texto{n}` de `libs/JSON.php:188` e
`Lancamento.php:742`). Nenhum teste e nenhum arquivo do PR foi alterado. O 7.4 nao muda (vendor do PR, Laravel 8).
**Atencao:** numeros iguais aqui mostram que os testes **nao dependem do framework**, nao que o Laravel 13 funciona: nenhum
teste sobe o app nem o kernel (ver "O que a suite exercita"), e o boot do kernel no vendor do Laravel 13 **falha** (lacuna abaixo).

## O que mudou e o que nao mudou no vendor

| Pacote | 7.4 (PR) | 8.5 antes (T-108) | 8.5 agora (T-119) |
|---|---|---|---|
| `laravel/framework` | 8.73.2 | 8.73.2 | **13.43.0** |
| `laravel/passport` | 10.4.2 | 10.4.2 | **13.12.0** |
| `nesbot/carbon` | 2.72.5 | 2.72.5 (mesma trava do PR) | **3.15.1** |
| `phpunit/phpunit` | 8.5.39 | 8.5.39 | 8.5.39 (a trava do 8.5 nao o trocou) |
| `mockery/mockery` | 1.3.0 | 1.3.0 | 1.3.0 |

O PHPUnit continua o 8.5.39 do PR: por isso `setUp(): void`, `Tests\TestCase` e o resto da API dos testes nao precisaram
de ajuste (o PHPUnit 11/12 do Laravel 13 "de fabrica" nao entrou na trava).

## Resultado (mesma suite, `ecidade/tests/suite/rodar.sh`, imagens do projeto)

| Entrada | 7.4 | 8.5 com Laravel 13 |
|---|---|---|
| `tests/Unit/Configuracao` | 12 testes, 24 asserc. | 12, 16, 3 erros |
| `tests/Unit/Core` | 3, 19 | 3, 19 |
| `tests/Unit/Financeiro` | 320, 375 | 320, 369, 2 erros |
| `tests/Unit/Patrimonial` | 13, 110 | 13, 110 |
| `tests/Unit/RecursosHumanos` | 75, 383 | 75, 383 |
| `tests/Unit/Saude` | 18, 24 | 18, 24 |
| `tests/Unit/Std` | 5, 5 | 5, 5 |
| `tests/Unit/Tributario` | 72, 120, 2 falhas, 7 avisos | 72, 120, 2 falhas, 7 avisos |
| `tests/Unit/ExampleTest.php` | 1, 1 | 1, 1 |
| `tests/Unit/ValidateAnexoBase64eAdicionaCaminhoTemporarioTest.php` | 1, 4 | 1, 4 |
| **Total** | **520, 1065, 2 falhas** | **520, 1051, 2 falhas e 5 erros** |

Cada diferenca tem a causa de `testes-proprios-85.md`: `$texto{n}` removido no PHP 8 em `libs/JSON.php:188` (3 testes de
`Configuracao`) e `src/Financeiro/.../Repository/Lancamento.php:742` (2 de `Financeiro`), e 2 testes de `Tributario` com
float sem delta que falham igual nos dois.

## O que a suite exercita do Laravel 13 (e o que nao)

- **Nenhum teste sobe o app nem o kernel.** `Tests\TestCase` (`ecidade/tests/TestCase.php`) estende
  `Mockery\Adapter\Phpunit\MockeryTestCase` e o `setUp()` so ajusta fuso, `error_reporting` e cria o Faker; o trait
  `CreatesApplication` existe, mas nenhum teste o usa (so o proprio arquivo cita `createApplication`). O bootstrap da suite
  (`tests/suite/bootstrap.php`) carrega apenas `vendor/autoload.php` e o `bootstrap.php` do sistema.
- O Laravel 13 so entra pelo autoload e por classes do Illuminate que o codigo testado ou o teste citam (por exemplo
  `Illuminate\Support\Collection` em `ProcedimentoBnafarStrategyTest`). Nenhum teste usa `Carbon` direto; o Carbon 3.15.1
  so seria exercitado se o codigo sob teste o usasse (nao medido por teste).
- **Avisos `Deprecated` do 8.5: 378** (no 7.4: 1). **327 sao do `mockery/mockery` 1.3.0** ("implicitly nullable") e os
  demais do proprio codigo do PR (`src/`, `libs/`, `model/agua/...`, `std/`: `ReflectionParameter::getClass()`/`isArray()`,
  `"parent"` em callables, cast `(integer)`). Nenhum muda resultado.

## Lacuna: o boot do kernel no Laravel 13 falha

Fora da suite, subir o kernel com o vendor do 8.5 em Laravel 13.43.0 + Passport 13.12.0 **nao funciona hoje**:

```
Call to undefined method Laravel\Passport\Passport::routes()      (ecidade/app/Providers/AuthServiceProvider.php:31)
```

O Passport 13 nao tem `routes()`. Reproduzido com `bash docker/composer-85/roda-isolado.sh 8.5 <trecho.php>` (trecho: `require tests/bootstrap.php`,
`require bootstrap/app.php`, `Console\Kernel::bootstrap()`), sem banco e sem rede. A medida do que mais quebra no boot e da
tarefa que trata a inicializacao no Laravel 13; esta suite nao a cobre.

## Como foi medido

```bash
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+    # vendor do 8.5 = Laravel 13.43.0
bash ecidade/tests/suite/rodar.sh [--runtime 74|85|ambos]                                    # VENDOR_74=<pasta> se o vendor do 7.4 nao estiver em ecidade/vendor
```

O `rodar.sh` passou a usar as **imagens do projeto** (`docker/php74-apache` e `docker/php85-apache`, com o `php.ini` e as
extensoes delas), construidas uma vez se faltarem, no lugar das `php:<v>-cli`. O `Dockerfile` da suite deixou de existir.
Medido no 7.4: as imagens do projeto dao os mesmos numeros das `php:7.4-cli` (520 testes, 1065 asserc.).

## Limites

- Sem banco: nenhum dos 520 testes abre conexao; o que depende de banco continua fora (ver `testes-proprios-85.md`).
- Nao ha teste do app no Laravel 13 (rotas, kernel, Passport): a suite atual nao os tem, e o boot falha (lacuna acima).
- O PHPUnit e o 8.5.39; se um dia a trava do 8.5 passar ao PHPUnit 11/12, `setUp()` sem `: void` e `@dataProvider` em
  comentario deixam de funcionar e a suite precisa de ajuste nos arquivos de teste.
