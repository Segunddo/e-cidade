# Os 21 models com `$dates` trocados por `$casts` (PHP8-55)

`$dates` deixa de ser lido no Laravel 10+ (no 13, `getDates()` so devolve `created_at`/`updated_at`). Em vez de copias em `ecidade/app-85/`,
a troca foi feita **no proprio arquivo** de `ecidade/app/`, por prova de que o 7.4 fica igual antes e depois (regra: preferir o proprio arquivo; copia em
`app-85/` so se nao desse). Sem banco: models em memoria em conteineres `php:7.4-cli` e `php:8.5-cli` com `--network none`, com o `vendor` do PR
(Laravel 8.73.2, Carbon 2.72.5, a mesma trava do `composer-85.lock`).

## 1. Os 21 models (arquivo:linha de antes)

| # | arquivo:linha (antes) | atributos | troca |
|---|---|---|---|
| 1 | app/Domain/Configuracao/Departamento/Models/Departamento.php:66 | limite | fundido no `$casts` existente |
| 2 | app/Domain/Educacao/CentralMatriculas/Models/ObservacaoInscricao.php:53 | created_at, updated_at, deleted_at | declaracao trocada |
| 3 | app/Domain/Educacao/Escola/Models/Aluno.php:98 | ed47_d_cadast, ed47_d_dtemissao, ed47_d_dthabilitacao, ed47_d_dtvencimento, ed47_d_nasc, ed47_d_ultalt, ed47_d_identdtexp | declaracao trocada |
| 4 | app/Domain/Educacao/Escola/Models/AtividadeProfissionalEscola.php:11 | ed22_datainicio, ed22_datafim | declaracao trocada |
| 5 | app/Domain/Educacao/Escola/Models/Calendario.php:34 | ed52_d_inicio, ed52_d_fim, ed52_d_resultfinal | fundido no `$casts` existente |
| 6 | app/Domain/Educacao/Escola/Models/ExcecaoBloqueioNota.php:26 | ed363_datalimite | declaracao trocada |
| 7 | app/Domain/Educacao/Escola/Models/Matricula.php:39 | ed60_d_datamatricula, ed60_d_datasaida | declaracao trocada |
| 8 | app/Domain/Educacao/Escola/Models/ProfissionalEscola.php:12 | ed75_d_ingresso, ed75_i_saidaescola | declaracao trocada |
| 9 | app/Domain/Educacao/MatriculaOnline/Models/Alocado.php:12 | mo13_data | declaracao trocada |
| 10 | app/Domain/Educacao/MatriculaOnline/Models/Candidato.php:46 | mo01_datacad, mo01_dtnasc | declaracao trocada |
| 11 | app/Domain/Educacao/MatriculaOnline/Models/Ciclo.php:21 | mo09_dtcad | declaracao trocada |
| 12 | app/Domain/Educacao/MatriculaOnline/Models/Fase.php:33 | mo04_datacorte, mo04_dtfim, mo04_dtini | declaracao trocada |
| 13 | app/Domain/Financeiro/Contabilidade/Models/ApropriacaoDecimoFerias.php:31 | pl2_created_at, pl2_updated_at | declaracao trocada |
| 14 | app/Domain/Financeiro/Contabilidade/Models/ApropriacaoDecimoFeriasLancamentos.php:24 | pl2_created_at, pl2_updated_at | declaracao trocada |
| 15 | app/Domain/Financeiro/Contabilidade/Models/EncerramentoPeriodoContabil.php:18 | c99_data | declaracao trocada |
| 16 | app/Domain/Financeiro/Contabilidade/Models/Lancamento.php:30 | c70_data | declaracao trocada |
| 17 | app/Domain/Financeiro/Contabilidade/Models/ParametroIntegracaoPatrimonial.php:13 | c01_data | declaracao trocada |
| 18 | app/Domain/Financeiro/Orcamento/Models/Recurso.php:35 | o15_datalimite | fundido no `$casts` existente |
| 19 | app/Domain/Financeiro/Planejamento/Models/Planejamento.php:41 | pl2_created_at, pl2_updated_at | fundido no `$casts` existente |
| 20 | app/Domain/Financeiro/Tesouraria/Models/Slip.php:14 | k17_data, k17_dtaut, k17_dtanu, k17_dtestorno | declaracao trocada |
| 21 | app/Domain/Saude/Farmacia/Models/BnafarBatchProtocolo.php:22 | fa76_created_at | `$dates` removido (o `$casts` ja tinha o atributo como `datetime`) |

Resumo: 16 declaracoes trocadas, 4 fundidas num `$casts` que ja existia, 1 removida. 43 atributos; 21 arquivos, 45 linhas a mais e 56 a menos.

## 2. A troca (minima)

So `$dates` -> `$casts`, cada atributo com `'datetime'` (o que o `$dates` fazia: `asDateTime`, hora preservada, serializacao ISO-8601 em UTC). Mesma
aspa e mesma visibilidade (`protected`/`public`) do arquivo, mesmo estilo (uma linha ou varias), arquivo em ISO-8859-1 sem tocar em mais nada.
Nos 4 que ja tinham `$casts`, as datas entram no fim do array, e o `$dates` (com a linha em branco que o separava) sai. Sem `date`: o cast `date` zeraria a hora
que o `$dates` preserva. Feito por `scratchpad/troca_dates_casts.py ecidade` (reexecutavel; `--dry` so lista).

## 3. Prova sem banco (criterio 3)

`scratchpad/models_dates_casts.php <raiz> <vendor>`: para cada um dos 58 models com `$dates` ou `$casts` de data (58 carregados; os 21 e os que ja
usavam `$casts`), cada atributo de data x 7 valores (`2021-03-15`, com hora, com microssegundos, `15/03/2021`, timestamp inteiro, `null`, `''`) x
leitura (`getAttribute`), `attributesToArray()`, `toJson()` e escrita (`setAttribute`, com texto, `Carbon` e `DateTime`), mais o JSON inteiro do
model com todas as datas juntas e as chaves de `attributesToArray()` (acessores/`$appends` incluidos). Relogio fixo, `America/Sao_Paulo`. Atributos em
ordem alfabetica para a saida nao depender de `$dates` x `$casts`.

| Comparacao | Resultado |
|---|---|
| 7.4, antes x depois da troca | **identica byte a byte** (3.204 linhas) |
| 8.5, antes x depois da troca | **identica byte a byte** |
| 7.4 x 8.5 (antes e depois) | identicas (so o prefixo `DateTime::__construct(): ` das mensagens do 7.4 sai, como na PHP8-55 anterior) |

Saida de referencia: `models-dates-casts/saida-7.4-antes-e-depois.txt` (a mesma antes e depois).

Antes de chegar a esse resultado a primeira comparacao diferia em 3 models com `timestamps`: era so a ordem em que o proprio trecho montava os
atributos (`getDates()` vem antes de `getCasts()`); com a ordem fixa a diferenca some, e o JSON inteiro (ordem das chaves) fica igual.

### Laravel 13 (informativo, antecipa a PHP8-55 com Laravel 13)

Mesmo trecho com `illuminate/database` 13.43 + Carbon 3.15.1 no 8.5 (sem `Usuario`, que precisa do pacote de autenticacao): 57 models, 99 atributos de data, **os
mesmos por model que no 7.4** (antes da troca, 18 models / 37 atributos deixavam de converter). A comparacao completa de valores com o 13 fica para quando ele
integrar.

## 4. Ambiguidade de classe (criterio 4)

Nao se aplica: nenhuma classe foi copiada para `ecidade/app-85/`, entao o `composer dump-autoload` do 8.5 nao emite
`Ambiguous class resolution` por causa desta tarefa (0 avisos novos; os avisos esperados da sobreposicao, `docs/registro/estrutura-85.md`, ficam para as classes
que precisarem de copia). Se algum model precisar de copia no futuro, o aviso e esperado e nao e erro.

## Repetir

O `vendor` precisa ser montado em **`/w/ecidade/vendor`** (por cima da pasta `ecidade/vendor`), nao em outra pasta: o autoload do Composer
resolve os `files` do projeto (`app/Helpers/*`) a partir de `dirname(vendor)`, que tem de ser o proprio `ecidade/`. O ponto de montagem `ecidade/vendor`
tem de existir (o `composer-85.sh` o cria; num checkout novo, `mkdir ecidade/vendor`).

- **Vendor do 8.5 da integracao:** `bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+` deixa o vendor em
  **`runtime-85/vendor`** (so `vendor/` dentro de `runtime-85/`); e esse o `<vendor>` abaixo.
- **Vendor do PR (usado nas provas acima):** `composer install` da `ecidade/composer.lock` numa pasta fora do repositorio e depois `composer dump-autoload --no-scripts`
  com o `composer.json` real (`-v $PWD/ecidade:/app:ro -v <pasta do vendor>:/app/vendor -w /app`), para o autoload incluir `app/Helpers/*`, `database/` e `Fpdf\`.

```bash
mkdir -p ecidade/vendor
python3 scratchpad/troca_dates_casts.py ecidade --dry          # lista os 21 arquivos
for v in 7.4 8.5; do
  docker run --rm --network none -v $PWD/ecidade:/w/ecidade:ro -v <vendor>:/w/ecidade/vendor:ro -v $PWD/scratchpad:/s:ro \
    php:$v-cli php -d memory_limit=1G /s/models_dates_casts.php /w/ecidade /w/ecidade/vendor | sed 's/DateTime::__construct(): //' > saida-$v.txt
done
cmp saida-7.4.txt docs/migracao-laravel/models-dates-casts/saida-7.4-antes-e-depois.txt
cmp saida-8.5.txt docs/migracao-laravel/models-dates-casts/saida-7.4-antes-e-depois.txt
```

Conferido neste layout (vendor do PR com autoload completo montado em `/w/ecidade/vendor`): 7.4 e 8.5 saem iguais a `saida-7.4-antes-e-depois.txt`. Com o vendor do 8.5 da integracao
e com o Laravel 13 (PHP8-55 com Laravel 13, T-119), repetir o mesmo comando trocando `<vendor>`.
