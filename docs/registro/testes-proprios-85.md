# Testes proprios (`ecidade/tests`) no 7.4 e no 8.5, sem banco (PHP8-71, 20/11/2026)

**Resumo:** os 520 testes unitarios que rodam sem banco (PHPUnit 8.5.39 do composer do PR, o mesmo na trava do 8.5)
dao os mesmos 520 testes no 7.4 e no 8.5. No 7.4 passam 518 e falham 2 (float sem delta). No 8.5 falham os mesmos 2 e
mais 5, todos por duas linhas do codigo que usam `$texto{n}`, sintaxe removida no PHP 8 (`libs/JSON.php:188`,
`src/Financeiro/.../Repository/Lancamento.php:742`). Nada do codigo ou dos testes foi alterado. A suite unica
`ecidade/tests/suite/rodar.sh` roda os dois runtimes em conteineres descartaveis `--network none`.

## Como rodar

```bash
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+   # runtime-85/vendor (com o plugin de patches, como em estrutura-85.md)
# vendor do 7.4: composer install do PR em ecidade/vendor (ou VENDOR_74=<pasta>)
bash ecidade/tests/suite/rodar.sh [--runtime 74|85|ambos] [--saida PASTA]
```

Num checkout novo `ecidade/vendor` e `ecidade/tmp` nao existem: o `rodar.sh` os cria (vazios, com o dono de quem roda)
antes dos contêineres, porque `ecidade/` sobe somente leitura e o Docker nao monta em ponto inexistente
(`read-only file system`) nem o cria com o dono certo. O `rodar.sh` sai com erro se o `docker run` falhar ou o PHPUnit
nao imprimir a linha de resultado: saida vazia nao vira "igual".

Cada entrada de `camadas/unitario.lista` roda num `docker run --rm --network none` (imagem `php:<versao>-cli` mais
`bcmath` e `calendar`, `tests/suite/Dockerfile`), com `ecidade/` e o `vendor/` somente leitura e so `tmp/` gravavel (uma
pasta de saida). Bootstrap: `tests/suite/bootstrap.php` (autoload do vendor + `bootstrap.php` do sistema). Saida em
`tests/suite/relatorios/` (fora do git): um `.txt` e um JUnit por entrada, e `resumo-74.txt`/`resumo-85.txt`.

Conferido a partir de um checkout novo (`git worktree add --detach`, sem `ecidade/vendor`), com o vendor 8.5 de
`composer-85.sh install --no-scripts --ignore-platform-req=php+` (plugin de patches ligado): o `rodar.sh` criou
`ecidade/vendor` com o dono de quem rodou e as duas rodadas deram os mesmos numeros da tabela abaixo (520 testes nos dois).

## O que roda sem banco (medido)

| Entrada | 7.4 | 8.5 |
|---|---|---|
| `tests/Unit/Configuracao` | 12 testes, 24 asserc. | 12 testes, 16 asserc., 3 erros |
| `tests/Unit/Core` | 3, 19 | 3, 19 |
| `tests/Unit/Financeiro` | 320, 375 | 320, 369, 2 erros |
| `tests/Unit/Patrimonial` | 13, 110 | 13, 110 |
| `tests/Unit/RecursosHumanos` | 75, 383 | 75, 383 |
| `tests/Unit/Saude` | 18, 24 | 18, 24 |
| `tests/Unit/Std` | 5, 5 | 5, 5 |
| `tests/Unit/Tributario` | 72, 120, 2 falhas, 7 avisos | 72, 120, 2 falhas, 7 avisos |
| `tests/Unit/ExampleTest.php` | 1, 1 | 1, 1 |
| `tests/Unit/ValidateAnexoBase64eAdicionaCaminhoTemporarioTest.php` | 1, 4 | 1, 4 |
| **Total** | **520 testes, 1065 asserc., 2 falhas** | **520 testes, 1051 asserc., 2 falhas e 5 erros** |

## Cada diferenca entre os dois

1. `Configuracao` (3 erros no 8.5, `HashGeneratorTest`): `src/Configuracao/Api/Generator/HashGenerator.php:19` carrega
   `libs/JSON.php`, que no 8.5 nao compila (`ParseError` em `libs/JSON.php:188`: `ord($utf16{0})`). Os outros 2 testes
   da classe dao `Class "JSON" not found`. Faltam 8 asserc. (24 contra 16).
2. `Financeiro` (2 erros no 8.5, `LancamentoRepositoryTest`): `src/Financeiro/Contabilidade/MatrizSaldoContabil/
   Repository/Lancamento.php:742` (`$valor{1}`) nao compila no 8.5. Faltam 6 asserc. (375 contra 369).
3. Mesma causa nas duas: `$texto{n}` foi removido no PHP 8 (no 7.4 so avisa de obsoleto). E codigo de aplicacao
   para portar (a `base-php84` ja tem essas duas linhas corrigidas), nao mudanca dos testes. Fica para o porte dos
   modulos; aqui so se mede.
4. `Tributario` (2 falhas): iguais nos dois runtimes (float sem delta: `42.83999999999999` x `42.84`,
   `19.060000000000002` x `19.06`); defeito do PR, registrado a parte.

Fora disso nao ha diferenca: mesmos testes, mesmas asserc., mesmos avisos. O 8.5 imprime `Deprecated` de
parametro nulo implicito e `E_STRICT` (pacotes e `config/application*.php`), sem efeito no resultado.

## O que a suite nao roda (lacunas)

- `tests/Unit/V3` (14 arquivos) estende `PHPUnit_Framework_TestCase`, inexistente no PHPUnit 8.5: fatal no 7.4 e no 8.5.
  Como o `display_errors` do sistema fica desligado, `vendor/bin/phpunit` com o `phpunit.xml` do PR (que seleciona
  `tests/Unit`) sai com rc=0 e sem imprimir nada. Por isso a suite roda uma pasta por vez e exige a linha de resultado.
- `tests/Unit/Recadastramento.php` (nome sem `Test.php`), `tests/Feature` (so `.gitkeep`) e `tests/cypress` (navegador).
- Testes que abrem conexao com o banco: nenhum dos 520 abre; a camada de integracao da base anterior nao foi trazida.
- Extensoes: a imagem de teste nao tem `pgsql`, `gd`, `soap`, `zip`; nenhum teste de hoje pede.
