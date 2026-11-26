# Collections, `Str::`, `Arr::` e helpers com o Laravel 13 nos usos do codigo (PHP8-62)

Mede, com entradas no formato dos usos reais, o que o codigo do PR chama de `Illuminate\Support` (Collection, `Str::`, `Arr::`, helpers globais) no 7.4 com o Laravel 8 e no 8.5 com o Laravel 13.43. Sem banco, sem rede, pelo `docker/composer-85/roda-isolado.sh`
(imagens do projeto). Scripts: `scratchpad/colecoes_str_arr.php` (111 casos), runner `scratchpad/roda_colecoes.sh`, contagens `scratchpad/conta_colecoes_usos.py`. Saidas e diferencas em `colecoes-str-arr/`.

Para separar o que e do **PHP** do que e do **Laravel**, o trecho roda em tres combinacoes: 7.4 + Laravel 8, 8.5 + Laravel 8 (vendor do PR na imagem 8.5) e 8.5 + Laravel 13.

## Resultado

| Comparacao | Diferenca |
|---|---|
| 8.5 + Laravel 8 x 8.5 + **Laravel 13** (so o Laravel muda) | **0 linhas** (111 casos iguais) |
| 7.4 + Laravel 8 x 8.5 + Laravel 8 (so o PHP muda) | 5 casos, 10 linhas `<`/`>` (abaixo) |
| 7.4 + Laravel 8 x 8.5 + Laravel 13 (o que o 8.5 entrega) | os mesmos 5 casos, 10 linhas `<`/`>` |

**Do Laravel 8 para o 13 nada muda no que o codigo usa.** Os 5 casos diferentes sao do PHP 8, nao do Laravel.

## O que o codigo usa (`python3 scratchpad/conta_colecoes_usos.py ecidade`)

| Uso | Ocorrencias | Medido com |
|---|---|---|
| `collect(...)` | 114 (`map`, `filter`, `each`, `reduce`, `implode(chave, ', ')`, `max()`, `count`, `shift`, `first`, `push`, `merge`, `contains`, `diff`, `search`, `groupBy`, `whereIn`...) | arrays de arrays e objetos `stdClass` de `DB::select`/`pg_fetch_object`, com numeros em texto |
| `->sortBy(` / `->sortByDesc(` | 10 (9 + 1): `MetasArrecadacaoService.php:134,171,227`, `RecursoController.php:102`, `RecursoAntes2022Service.php:152`, `AcompanhamentoPpaService.php:139`, `TemplateDdr.php:45`, `ClassificacaoFonteRecursoController.php:36`, `PdfToImage.php:202` | 40 linhas com empates e 12 linhas |
| `Arr::get` | 62 | chave simples, com ponto, ausente, `null`, objeto, `ArrayObject`, `Collection`, valor padrao e `Closure` |
| `Str::replaceFirst` | 1 (`api/V1/Middleware/Session/MenuAcessadoSessionMiddleware.php:59`) | 6 casos (busca vazia, ausente, troca vazia...) |
| `Str::random` | 1 (`database/migrations/2022_03_02_130549_m20063_cria_client_id_central_de_matriculas.php:14`) | tamanho e alfabeto |
| `tap(model)->update(...)` | 11 | objeto e array |
| `str_contains` | 16 | PHP 8 nativo no 8.5, polyfill no 7.4 (mesmas respostas, inclusive busca vazia) |
| `dispatch(...)` | 13 | fila: ver T-145 |
| `array_pluck` | 1 (`ComissaoController.php:75`) | nao existe no 7.4 nem no 13 (`function_exists` falso): defeito ja no registro da PHP8-49, nao corrigido |

O que as outras tarefas ja cobrem fica la: `where`/`get`/`first` de **query builder** e Eloquent (SQL: T-111/T-125, resultados exigem banco) e `when`/`unless` (sem efeito: `cobertura-inventario-8-a-13.md`).

## As 5 diferencas (todas do PHP, nao do Laravel)

1. **`sortBy`/`sortByDesc` com empates em mais de 16 linhas** (4 casos). O `sort` do PHP 7 so e estavel para ate 16 elementos; o do PHP 8.0+ e sempre estavel. Com 40 linhas e 3 valores de `grupo`, o 7.4 devolve os empates embaralhados
   (`21,9,18,27,15,...`) e o 8.5 os devolve na ordem original (`3,6,9,12,15,...`). Com 12 linhas, ou sem empates, as saidas sao iguais. Os 10 `sortBy` do codigo ordenam por colunas que podem repetir (`fonte_recurso`, `natureza`, `pl12_orcprojativ`...),
   entao, onde houver empate e mais de 16 linhas, a ordem das linhas empatadas muda. A ordem do 7.4 e um efeito do algoritmo instavel; nao ha correcao minima que a reproduza. Causa: PHP 8.0 (ordenacao estavel), nao ha item no guia do Laravel.
2. **`collect([...misto...])->sort()`** com texto numerico, inteiro, `'1e1'` e `'abc'` (1 caso): a comparacao texto x numero mudou no PHP 8.0. O codigo nao chama `->sort()` em colecao.

**Fora do escopo desta tarefa, mesmo efeito:** as funcoes de ordenacao do proprio PHP (`usort`, `uasort`, `asort`, `sort`, `ksort`, `array_multisort`...) sao **385 chamadas** no codigo (fora de `dbagata`, `fpdf`, `ext`, `jpgraph`, `tests`, `database`) e sofrem a mesma
mudanca de estabilidade com empates em arrays grandes. Nao ha tarefa no quadro que meca isso: e do grupo do lint/silenciosas do PHP 8.5.

## O que precisa de banco

Metodos de `Illuminate\Database\Eloquent\Collection` (`contains($model)`, `find`, `load`, `fresh`, `toQuery`) so existem com models lidos do banco; os 114 `collect()` acima recebem arrays/objetos e foram medidos sem banco.

## Repetir

```bash
python3 scratchpad/conta_colecoes_usos.py ecidade     # contagens da tabela de usos
bash scratchpad/roda_colecoes.sh                      # 3 combinacoes pelo roda-isolado.sh; compara com colecoes-str-arr/
# vendor do 8.5 (Laravel 13): bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+
# vendor do PR em runtime-85/referencia-74/vendor: passos em docs/migracao-laravel/middlewares-laravel13.md
```
