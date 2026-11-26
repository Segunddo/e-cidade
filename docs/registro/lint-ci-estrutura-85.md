# CI de lint do grupo contra a estrutura do 8.5 (PHP8-79, 20/11/2026)

**Resumo:** o script do CI (`ferramentas/testes-ci/lint_alterados.py` da `origin/testes-ci/lint-incremental-pedromax`,
commit `8a2e43837`) foi rodado localmente, sem GitHub e sem push, com o `php:7.4-cli` e o `php:8.5-cli` descartaveis
(`--network none`, como o proprio script faz). Sobre o diff real `origin/base-php74...laravel/integracao-74` (35b39e7a2)
ele seleciona 2 arquivos `.php` e os dois passam nos dois runtimes. Sobre 4 classes de exemplo em `ecidade/app-85/` com
sintaxe so do 8.x, o job do 7.4 sai com `NOVA_FALHA` (codigo 1) em 2 delas e o do 8.5 passa nas 4. O workflow do CI nao
foi alterado.

## Como foi rodado

```bash
BASE=$(git rev-parse origin/base-php74)      # o script exige o SHA completo da base
python3 lint_alterados.py --base $BASE --php 7.4 --out rel-7.4.json   # idem 8.5; roda dentro do checkout, usa HEAD
```

Os 15 testes do proprio script (`python3 -m unittest discover -s ferramentas/testes-ci -p 'test_*.py'`) passam
(1 pulado: o de Docker real, que so roda com `ECIDADE_LINT_IMAGE`).

## O que o script faz com cada tipo de arquivo

| Arquivo | Selecionado? | Resultado |
|---|---|---|
| `*.php` adicionado/alterado (`--diff-filter=ACM`) | sim, em qualquer pasta (nao ha filtro de caminho) | `php -n -d short_open_tag=1 -l` no runtime; se falha, repete na versao do ancestral |
| `.inc`, `.json`, `.lock`, `.sh`, `.md`, `Dockerfile`, `*.patch` | nao (so o sufixo `.php`, sem diferenciar maiusculas) | ignorado |
| `ecidade/composer-85.json`, `ecidade/composer-85.lock`, `docker/composer-85/*`, `docs/**` | nao | ignorado |
| `runtime-85/` | nao | fica no `.gitignore`, nao entra no diff |
| `ecidade/app-85/**/*.php` (sobreposicao) | sim | lint no 7.4 **e** no 8.5 |

Estados: `PASSOU`; falha com a versao anterior valida ou inexistente = `NOVA_FALHA` (saida 1); falha nos dois =
`INCONCLUSIVO` (saida 2). Arquivo novo que falha e sempre `NOVA_FALHA`.

## Resultado sobre o diff real

`origin/base-php74...laravel/integracao-74` (13 arquivos, so 2 `.php`): `scratchpad/laravel8_validacao_matriz.php` e
`scratchpad/laravel8_validacao_medir.php`, os dois `PASSOU` no 7.4 e no 8.5; status `SEM_NOVA_FALHA`, saida 0. O
`composer-85.json`, a trava, o `composer-85.sh`, o `Dockerfile` e os registros nao entram no lint.

## Sobreposicao `ecidade/app-85/` com sintaxe so do 8.x

Quatro arquivos de exemplo em um commit descartavel (nao versionado aqui):

| Exemplo | 7.4 | 8.5 |
|---|---|---|
| `Exceptions/Handler.php` (sintaxe 7.4, `#[\ReturnTypeWillChange]` em metodo, retorno so em docblock) | PASSOU | PASSOU |
| `Support/Retorno.php` (retorno `: mixed`) | PASSOU | PASSOU |
| `Support/Uniao.php` (`int\|string`, promocao no construtor, `match`) | **NOVA_FALHA** | PASSOU |
| `Support/Enumeracao.php` (`enum`) | **NOVA_FALHA** | PASSOU |

Job do 7.4: status `NOVA_FALHA`, saida 1 (job vermelho). Job do 8.5: `SEM_NOVA_FALHA`, saida 0.

Tabela do que o `php -l` do 7.4 aceita e rejeita (medida, `php:7.4-cli` e `php:8.5-cli`, `-n`):

| Construcao | 7.4 | 8.5 |
|---|---|---|
| retorno `: mixed`, `: never`, propriedade tipada, `fn` | passa | passa |
| `#[Atributo]` de uma linha (vira comentario) | passa | passa |
| `#[Atributo(` em varias linhas | **falha** | passa |
| retorno `: static`, tipo uniao `A\|B`, intersecao `A&B` | **falha** | passa |
| promocao no construtor, `readonly`, `enum`, `match`, `?->` | **falha** | passa |
| argumento nomeado, `new` em valor padrao, `throw` como expressao | **falha** | passa |
| virgula final na lista de parametros, `final const` | **falha** | passa |

## Alinhamento com `estrutura-85.md` (regra e pergunta de la, contra o que foi medido)

`estrutura-85.md` (secao "Lint do grupo (CI) e a pergunta ao coordenador") traz uma regra e uma pergunta. As duas foram
conferidas contra o script do CI e uma parte delas nao confere:

| O que diz `estrutura-85.md` | O que o script do CI faz (medido acima) |
|---|---|
| Regra: em `app-85/` nao vale "tipos `mixed`" de retorno | `: mixed` **passa** no 7.4 (o `php -l` do 7.4 le `mixed` como nome de classe, e o `-l` nao confere se a classe existe) |
| Regra: nao vale "atributos `#[...]` fora de comentario" | `#[Atributo]` de **uma linha** passa no 7.4 (vira comentario); so o atributo em **varias linhas** falha |
| Pergunta: "por exemplo, retorno `mixed` numa interface do framework" deixaria o job do 7.4 vermelho | **nao deixa**: `: mixed` passa. O exemplo nao ilustra o problema |
| Regra: `static`, uniao, `match`, argumentos nomeados, `readonly`, `enum`, promocao no construtor | confere: todos falham no 7.4 |

Conclusao: **a regra do time e mais estrita que o CI.** O que realmente deixa o job do 7.4 vermelho (`NOVA_FALHA`) em
`app-85/`: retorno `static`, tipo uniao `A|B`, intersecao `A&B`, promocao no construtor, `readonly`, `enum`, `match`,
`?->`, argumento nomeado, `new` em valor padrao, `throw` como expressao, virgula final em parametros, `final const` e
atributo em varias linhas. `: mixed`, `: never` e `#[Atributo]` de uma linha passam. A pergunta ao coordenador continua
valida, mas o exemplo dela deve ser um destes (por exemplo, uma assinatura do Laravel 13 com tipo uniao ou `static`
de retorno), nao `mixed`.

Das duas saidas que a pergunta de `estrutura-85.md` oferece, a **sobreposicao fora de `ecidade/`** e a que foi
**descartada**: o script nao filtra por caminho, entao mudar a pasta de lugar nao tira o `.php` do lint. Fica a primeira:
o job do 7.4 pular `ecidade/app-85/` (texto abaixo).

## Proposta de texto para o coordenador e o autor do CI

> **Assunto: lint do job do 7.4 e a sobreposicao so do PHP 8.5 (`ecidade/app-85/`).**
>
> O time do Laravel mantem, para o PHP 8.5, uma pasta `ecidade/app-85/` com classes que sobrepoem as de `ecidade/app/`
> so no 8.5 (o PSR-4 do `composer-85.json` a enxerga; o `composer.json` do 7.4 nao). O 7.4 nunca carrega essa pasta.
> Hoje o `lint_alterados.py` roda `php -l` do 7.4 em todo `.php` alterado, sem filtro de caminho. Por isso uma classe
> de `app-85/` que implemente uma assinatura do Laravel 13 com sintaxe so do PHP 8 (tipo uniao, `static`, promocao no
> construtor etc.) deixa o job do 7.4 vermelho (`NOVA_FALHA`) sem que o 7.4 tenha problema algum.
>
> **Pedido:** no job do 7.4, ignorar os arquivos em `ecidade/app-85/`. O job do 8.5 continua conferindo a pasta
> inteira. Uma forma simples e uma opcao `--exclude <prefixo>` (repetivel) no `lint_alterados.py`, aplicada em
> `select_files`, e o workflow passa `--exclude ecidade/app-85/` so quando `matrix.php == '7.4'`. Sem o pedido, vale
> a regra de hoje do time: classe em `app-85/` precisa ter sintaxe valida no 7.4, e a que nao couber fica pendente.
>
> Nao precisa mudar nada para `composer-85.json`, `composer-85.lock`, `docker/composer-85/` e `runtime-85/`: nao sao
> `.php` (o `runtime-85/` nem e versionado).
>
> **Alternativa descartada:** mover a sobreposicao para fora de `ecidade/` nao resolve, porque o script nao filtra por
> caminho; e renomear a extensao quebra o autoload PSR-4 do Composer.

## Lacunas

- Nao rodado no GitHub: so o script, localmente. O comportamento do job (permissoes, tempo) e o da primeira
  execucao remota do CI.
- O script ignora `.inc`, que o sistema tambem usa; fora do escopo daqui.
- A tabela de sintaxe e de `php -l`: nao mede comportamento de execucao.
