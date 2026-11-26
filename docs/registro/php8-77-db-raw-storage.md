# `DB::raw` e arquivos (Flysystem 3) do PHP 7.4 ao 8.5 (PHP8-77, 20/11/2026)

**Resumo:** das **414** chamadas `DB::raw(` do código (fora de `vendor/`), **23 quebram** no Laravel 10+, porque a
`Expression` deixou de virar texto sozinha. São 19 `DB::select(DB::raw(...))`, 3 `DB::statement(DB::raw(...))` e
1 `selectRaw(implode(', ', $campos))` com `DB::raw` no array. O ajuste tira o `DB::raw(` e o `)` em volta do texto nos
23 pontos (13 arquivos), sem mudar o texto. O SQL gerado fica igual no 7.4 (Laravel 8) antes e depois e igual no
8.5 (Laravel 13) depois. As outras 391 vão para o Builder, que aceita `Expression`, e ficam como estão.

Nos arquivos, as 6 operações que o código usa (`exists`, `put`, `get`, `lastModified`, `path`, `delete` no disco
`local`) e as 4 do `Illuminate\Filesystem\Filesystem` saem iguais no 7.4 e no 8.5, com o mesmo caminho. A exceção é
`Storage::delete` de arquivo que não existe: devolve `false` no 7.4 e `true` no 13. O único chamador ignora o retorno.

Tudo foi medido sem banco: o SQL vem do Grammar (`toSql()`, `compileInsert`/`compileUpdate`) e do `pretend()` da
conexão, numa configuração `pgsql` sem servidor, em contêineres `--network none`.

## Classificação (critério 1)

Lista: `docs/registro/php8-77-db-raw.tsv` (arquivo, linha, categoria, contexto, trecho), tirada da `origin/base-php74`
pelo tokenizador do PHP, só lendo os arquivos. O comando:

```bash
I=php:8.5-cli@sha256:50956f094e90a716d43bea28087d447555ad80510e386ab8c9c10d8c70d781a9
mkdir -p /tmp/base74 && git archive origin/base-php74 ecidade | tar -x -C /tmp/base74
docker run --rm --network none -v /tmp/base74/ecidade:/app:ro -v $PWD/scratchpad:/s:ro $I \
  php /s/php8_77_db_raw.php /app | LC_ALL=C sort | iconv -f latin1 -t utf-8      # 414 linhas
# contagem por categoria (a mesma da tabela abaixo):
tail -n +2 docs/registro/php8-77-db-raw.tsv | cut -f3 | sed 's/VER-array-em-.*/VER-array-em-variavel/' | sort | uniq -c
```

Por pasta: `app/Domain` 360, `src/Financeiro` 42, `database/migrations` 7, `app/Jobs` 3, `routes/api` 1,
`fpdf151/impmodelos` 1. Os 302 do guia do grupo contam outro recorte. Esta lista conta toda chamada `DB::raw(` em
`.php` fora de `vendor/`.

| Categoria | Qtde | O que é | Decisão |
|---|---|---|---|
| `OK-argumento-do-builder` | 292 | argumento de `select`, `where`, `orderBy`, `join`, `table`, `from`, `update`... (direto ou dentro de array) | fica: o Builder chama `getValue()` |
| `OK-whereRaw` | 1 | `ItbinumpreRepository.php:74`, `whereRaw(DB::raw(...))` | fica: medido, o Grammar do 13 aceita `Expression` no `whereRaw` |
| `QUEBRA-conexao-select` | 19 | `DB::select(DB::raw(...))`: a conexão recebe objeto onde espera texto | **ajustado** |
| `QUEBRA-conexao-statement` | 3 | `DB::statement(DB::raw(...))` | **ajustado** |
| `VER-array-em-variavel` | 85 | array guardado em variável | 84 vão a `select()`/`get()`/`first()`/`all()` (fica); **1 vai a `selectRaw(implode(', ', $campos))`** (`ProjecaoDespesaService.php:600`, **ajustado**) |
| `VER-atribuido-ou-devolvido` | 3 | `ReceitaService.php:138` e `RelatorioProjecaoReceitaService.php:146` (vão a `buscarProjecao()` → `select($campos)`); `RelatorioJsonMapper.php:54` (vai a `DB::table($table)`) | fica |
| `VER-argumento-de-wherebetween` | 3 | coluna como `Expression` | fica: medido |
| `VER-argumento-de-setdata(visualizada)` | 3 | `MensageriaService.php:214,227,307`: valor de atributo de model, gravado pelo Eloquent | fica: medido (`insert`/`update` com `Expression` de valor) |
| `VER-argumento-de-getall...` | 3 | `getAllByGuia` (`ItbiRepository.php:134`, `->select($campos)`) e `getAllConfirmadasAutorizadoraByNumnov` (`OperacoesrealizadastefRepository.php:28`, `->get($campos)`) | fica |
| `VER-argumento-de-default` | 2 | `->default(DB::raw(...))` em migration | fica: o `Schema\Grammars\Grammar` do 13 trata `Expression` no valor padrão (lido no código) |
| **Total** | **414** | 391 ficam, 23 ajustados | |

As 99 `VER` foram decididas lendo o destino de cada uma (arquivo:linha acima). Depois do ajuste, o mesmo comando na
branch dá **391** linhas, sem nenhuma `QUEBRA`.

## O ajuste e a prova (critério 2)

`scratchpad/php8_77_ajusta.php` lê a lista dos 23 (arquivo, linha) e remove, em bytes, só os tokens `DB::raw(` (com a
`\` se houver) e o `)` que fecha a chamada. Arquivos ISO-8859-1 ficam como estão. Diff: 13 arquivos, 31 linhas
trocadas por 31 e 2 linhas que ficaram vazias (`AtualizaDataCadastrosRepository.php`) removidas. `php -n -l` (como o
CI do grupo) passou nos 13 arquivos, no 7.4 e no 8.5.

Trecho isolado `scratchpad/php8_77_trecho.php`, sintaxe válida no 7.4. Ele roda com o vendor mínimo de cada lado:

- 7.4: `php:7.4-cli@sha256:620a6b9f…` com `illuminate/database` v8.73.2, que é a versão da trava do PR;
- 8.5: `php:8.5-cli@sha256:50956f09…` com v13.43.0.

Os dois vendors ficam fora do repositório. Cada linha tira um texto real dos pontos (`Concessao.php:87`,
`AtualizaCadastroOptantesSimplesNacionalRepository.php:89`, migration `m24478:22`, `ItbinumpreRepository.php:74`,
`ProjecaoDespesaService.php:600`):

| Caso | 7.4, hoje | 7.4, ajustado | 8.5 (13), hoje | 8.5 (13), ajustado |
|---|---|---|---|---|
| `DB::select(DB::raw($sql))` (2 textos) | SQL = o texto | igual | `TypeError: strlen(): Argument #1 ($string) must be of type string, …Expression given` | igual ao 7.4 |
| `DB::statement(DB::raw(...))` | `CREATE SCHEMA matriculaonline` | igual | o mesmo `TypeError` | igual ao 7.4 |
| `selectRaw(implode(', ', [.., DB::raw(..)]))` | `select pl20_codigo, ( … ) AS inflatores from "detalhamento"` | igual | `Error: Object of class …Expression could not be converted to string` | igual ao 7.4 |
| `whereRaw(DB::raw(...))` | `select * from "itbinumpre" where (CASE …)` | — | igual ao 7.4 | — |
| `select([.., DB::raw])`, `where(DB::raw)`, `orderBy(DB::raw)`, `table(DB::raw)`, `whereBetween(DB::raw)`, `insert`/`update` com `DB::raw` de valor | SQL do Grammar | — | igual ao 7.4 | — |

As 30 linhas de saída são iguais entre o 7.4 e o 8.5, menos os 4 "hoje" que quebram no 13 e o `delete` abaixo. Nenhum
aviso do PHP saiu nos dois (`error_reporting=-1`). Para o `insert`/`update` vale o SQL do Grammar
(`compileInsert`/`compileUpdate`): o log do `pretend()` do 13 já mostra os `?` trocados pelos valores, e o do 8 não.

```bash
S=<pasta descartavel>; mkdir -p $S/l8 $S/l13
# composer.json minimo de cada lado (illuminate/database, filesystem e config; league/flysystem 1.1.10 / ^3), com
# config.platform.php 7.4.33 / 8.5.12; resolvido com a imagem do composer do 8.5 (docker/composer-85)
docker run --rm --network none -u $(id -u):$(id -g) --tmpfs /descartavel:uid=$(id -u) -v $S/l8:/v:ro \
  -v $PWD/scratchpad:/s:ro php:7.4-cli@sha256:620a6b9f4d4feef2210026172570465e9d0c1de79766418d3affd09190a7fda5 \
  php -d error_reporting=-1 /s/php8_77_trecho.php /v/vendor/autoload.php /descartavel        # idem l13 no 8.5
```

## Arquivos (critério 3)

O código usa o `Storage` em 2 pontos, os dois no disco padrão `local`:

- `ApropriacaoDecimoFeriasService.php:371-399`: `exists`, `put`, `lastModified`, `delete` do arquivo de trava;
- `TriagemLaboratorialService.php:271`: `path`.

O `Illuminate\Filesystem\Filesystem` direto aparece em 1 ponto (`TemplatesXlsRelatoriosLegaisService.php:55-79`:
`delete`, `isDirectory`, `makeDirectory`, `move`). O `configuration/filesystems.php` dá a raiz explícita
(`storage_path('app')`), então a mudança da raiz padrão do disco local no Laravel 12 não alcança o código. Medido com
a configuração do disco apontando para uma pasta `tmpfs` descartável, com o texto ISO-8859-1 do código:

| Operação | 7.4 (Flysystem 1.1.10) | 8.5 (Flysystem 3.36.0) |
|---|---|---|
| `exists` antes / `put` / `exists` / `get` = texto | `false` / `true` / `true` / `true` | igual |
| `lastModified` | inteiro, agora | igual |
| `path` | `<pasta>/storage/app/<arquivo>` | igual |
| `delete` / `exists` depois | `true` / `false` | igual |
| `delete` de arquivo inexistente | `false` | **`true`** |
| `Filesystem`: `isDirectory`, `makeDirectory`, `move`, `delete`, `delete` inexistente | `false`, `true`, `true`, `true`, `false` | igual |

O `delete` de arquivo inexistente difere, mas o único chamador (`removeLock()`, linha 399) ignora o retorno: a tela
sai igual. Por isso não houve ajuste.

## Repetição com o Laravel 13 da trava do 8.5

A prova acima usou um vendor mínimo e descartável no 8.5. Ela foi repetida com o vendor completo de cada trava,
pelo `docker/composer-85/roda-isolado.sh`, nas imagens de `docker/php74-apache` (PHP 7.4.33) e
`docker/php85-apache` (PHP 8.5.13):

- **7.4:** o `ecidade/composer.lock` do PR, com Laravel 8.73.2 (`content-hash` `5ef6154f…`);
- **8.5:** o `ecidade/composer-85.lock` da PHP8-62, com Laravel 13.43.0 (`content-hash` `e40f4c67…`).

O resultado é o mesmo da tabela acima. Das 30 linhas, 25 saem iguais. As 5 que diferem são:

- os 4 "hoje" que quebram no 13: 3 `TypeError: strlen()` da conexão e o `Error` do `selectRaw(implode(...))`;
- o `delete` de arquivo inexistente.

As 4 formas ajustadas dão o mesmo SQL do 7.4, e nada sai no stderr dos dois lados.

```bash
# vendor do 7.4: composer install do ecidade/composer.lock numa pasta a parte (mesmo conteiner do composer-85.sh,
# --no-scripts --no-plugins --no-autoloader --ignore-platform-reqs) e dump-autoload com ecidade/ montado em /app
VENDOR=<vendor do 7.4> bash docker/composer-85/roda-isolado.sh 7.4 scratchpad/php8_77_trecho.php /app/vendor/autoload.php /tmp > 74.txt
bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/php8_77_trecho.php /app/vendor/autoload.php /tmp > 85.txt
diff 74.txt 85.txt | grep -c '^<'   # 5
```

## Lacunas

- Nada foi executado contra banco: os 23 pontos mandam ao PostgreSQL o mesmo texto que mandavam (provado pelo SQL
  gerado), mas o resultado das consultas no 8.5 depende das rotas `/v4` e do Laravel 13 de pé.
- As 98 `VER` que ficam foram decididas lendo o código. O `default(DB::raw)` de migration não foi executado (só lido).
- A primeira medição do 8.5 usou o Laravel 13 num vendor descartável, porque o `composer-85.lock` ainda tinha o
  Laravel 8. A repetição acima usa a trava do 8.5 com o Laravel 13 (PHP8-62).
