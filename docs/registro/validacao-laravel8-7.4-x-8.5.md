# Validação do Laravel 8 do PR: PHP 7.4 × 8.5 (form requests, `validated()`, `only()`)

Mede, sem banco e sem rede, se a validação do Laravel 8 dá o mesmo resultado no PHP 7.4 e no 8.5 com as regras reais da `base-php74`.
**Resultado:** com `laravel/framework` 8.73.2, 1.350 casos de form requests e 348 combinações regra × valor dão o mesmo resultado (mesmas mensagens, mesmos dados validados) nos dois PHPs,
**exceto a regra `digits` com valor array** (`TypeError` no 8.5), e o 8.5 acusa 49 `Deprecated` que o 7.4 não acusa.

## 1. Inventário na `base-php74` (`app/` e `src/`)

| Item | Contagem |
|---|---|
| Declarações de form request (`class X extends FormRequest`, `DBFormRequest` ou `BaseFormRequest`) | **289** em 289 arquivos: 140 de `FormRequest`, 105 de `DBFormRequest`, 44 de `BaseFormRequest` |
| …nomes de classe distintos | **288**: o nome completo `App\Domain\Tributario\ITBI\Requests\AutenticacaoRequest` está declarado em 2 arquivos (registrado em `defeitos-laravel8-do-pr.md`); 1 das 288 é abstrata (`DBFormRequest`) |
| …medidas: 288 = 270 com `rules()` + 3 sem `rules()` com conteúdo + 14 que não carregam isoladas + 1 abstrata | as 3 sem regras: `BaseFormRequest`, `InfoComplementarCreateRequest` e `ConcessaoRequest` |
| …com regra que depende de banco (`exists`/`unique`) | 54 classes, 82 regras (79 `exists`, 3 `unique`); lista em `validacao-regras-de-banco.tsv` |
| `->validated()` e `->safe()` | **0** |
| `->only(...)` | 5 (`ExameToxicologicoController.php:35`, `RelatorioFuncionariosController.php:32`, `CalculoVistoriaController.php:26,43,60`); `->except(...)`: 1 |
| `->validate(...)` | 104 chamadas em 50 arquivos (97 por `$this->validate($request, ...)` nos controllers; regras escritas na própria chamada) |
| `Validator::make(...)` | 18 chamadas em 15 arquivos |
| `exists:`/`unique:` escritos em string em qualquer arquivo de `app/` e `src/` | 107 ocorrências |
| `digits:` | 11 ocorrências em 5 arquivos |

Como o código usa `validated()` zero vezes, o comportamento de `validated()` com chave ausente ou `null` só vale se alguém passar a usar.

## 2. Medida: mesmo vendor, 7.4 × 8.5

`laravel/framework` 8.73.2 (a versão do PR), instalado com `composer install` e `config.platform.php` = 7.4.33; **o mesmo `vendor/` roda nos dois PHPs**, para isolar o efeito do PHP.
O composer do 8.5 ainda não existe: a medição deve ser refeita quando houver. Contêineres descartáveis `php:7.4-cli` e `php:8.5-cli`, `--network none`, sem banco.

- **Form requests reais** (`scratchpad/laravel8_validacao_medir.php`; 288 nomes de classe, 270 com regras): para cada uma das 270 classes com regras lê `rules()`, `messages()` e `attributes()` e valida com o `Validator` e os arquivos de idioma `pt-br` do próprio `resources/lang`,
  com 5 entradas: vazia, válida (montada pelas regras), chave obrigatória ausente, todos os campos vazios e todos os campos array. Regras `exists`/`unique` são tiradas (listadas no `.tsv`).
  **1.350 casos: 1.347 iguais; 3 diferentes**, os três com a regra `digits` e entrada array: `ConfiguracaoReceitasDecendioRequest`, `GetDetalhamentoDecendioRequest` e `GetLancamentosDecendioRequest` (`Financeiro/Tesouraria/Requests`).
  14 classes não carregam sem o resto do sistema (`ECidade\Enum\…`, `ECidade\Lib\Session\DefaultSession` e `_M()` do legado, conexão do Eloquent, container de `request`, `rules()` com argumentos); falham pela mesma causa nos dois (só muda a aspa da mensagem do PHP: `Class 'X'` no 7.4, `Class "X"` no 8.5).
- **Matriz regra × valor** (`scratchpad/laravel8_validacao_matriz.php`): as 29 variantes de regra que o código usa (27 nomes; `date_format` e `digits` entram com 2 parâmetros cada) (`required`, `nullable`, `sometimes`, `filled`, `present`, `integer`, `numeric`, `string`, `boolean`, `array`, `json`, `email`, `url`, `ip`, `date`, `date_format`, `digits`,
  `max`, `min`, `in`, `regex`, `different`, `required_if`, `required_with`, `required_without`, `file`, `mimes`) contra 12 valores (texto, número em texto, data, int, float, booleano, `''`, `null`, array, array aninhado, `'0'`, texto de 300 caracteres).
  **348 combinações: 344 iguais; 4 diferentes**, todas `digits:N` com valor array.

### A diferença: `digits` com array

`validateDigits` (`Validation/Concerns/ValidatesAttributes.php:536`) faz `preg_match('/[^0-9]/', $value)`. Com `$value` array:

| | PHP 7.4 | PHP 8.5 |
|---|---|---|
| resultado | `Warning: preg_match() expects parameter 2 to be string`, a regra falha ("deve ter 4 dígitos") | `TypeError: preg_match(): Argument #2 ($subject) must be of type string, array given` |

No 7.4 o `Warning` vira `ErrorException` no `HandleExceptions` do Laravel quando o erro está habilitado, então o efeito prático pode ser o mesmo nos dois (não medido: o tratador de erros não roda nesta medição sem banco).
A regra `digits` aparece em 11 linhas de 5 arquivos. Só falha quando o cliente envia um array no lugar de um número. Situação de cada arquivo:

| Arquivo | Linhas | Medido por | Resultado |
|---|---|---|---|
| `Financeiro/Tesouraria/Requests/ConfiguracaoReceitasDecendioRequest.php` | 12 (`exercicio`, `digits:4`) | form request real (1.350 casos) | difere: `TypeError` no 8.5 |
| `Financeiro/Tesouraria/Requests/GetDetalhamentoDecendioRequest.php` | 12 (`exercicio`, `digits:4`) | form request real | difere |
| `Financeiro/Tesouraria/Requests/GetLancamentosDecendioRequest.php` | 12 (`exercicio`, `digits:4`) | form request real | difere |
| `Financeiro/Contabilidade/Controllers/MapeamentoEmpenhoRPContaController.php` | 45, 106, 141, 175, 236 (`$this->validate`, `exercicio`, `digits:4`) | só pela matriz (`digits:4` com array: 4 combinações diferentes); as regras estão na chamada, não em form request | exposto ao mesmo `TypeError` |
| `Saude/Ambulatorial/Requests/FindOrCreateCgsRequest.php` | 35 (`cns`, `digits:15`), 36 (`cpf`, `digits:11`), 44 (`municipio`, `digits:7`) | **não medido**: é uma das 14 classes que não carregam isoladas (`ECidade\Enum\Saude\Ambulatorial\RacaCorEnum`) | exposto ao mesmo `TypeError` pela leitura da regra (o mesmo `validateDigits`), sem medida própria |

### `Deprecated` só no 8.5 (49 mensagens distintas, 0 no 7.4)

| Origem | Mensagens | Exemplo |
|---|---|---|
| Laravel 8.73.2 (`Illuminate\…`) | 46 | `Container::afterResolving(): Implicitly marking parameter $callback as nullable is deprecated` (também `FormRequest::safe()`, `InteractsWithInput::whenFilled()`, `Model::replicate()`) |
| `BaseFormRequest::messages()` (`app/Http/Requests/BaseFormRequest.php`, 44 form requests herdam) | 1 | `Function utf8_encode() is deprecated since 8.2` |
| outras | 2 | `DateTime::createFromFormat(): Passing null to parameter #2 ($datetime)`; `str_getcsv(): the $escape parameter must be provided` |

Os 46 do Laravel 8.73.2 vêm do próprio framework (tipos anuláveis implícitos) e dependem da versão que o composer do 8.5 instalar. Os 3 restantes são do código do PR.

## 3. Regras que dependem de banco

`validacao-regras-de-banco.tsv` (classe, campo, regra): 54 form requests, 82 regras (79 `exists`, 3 `unique`). Mais 107 ocorrências de `exists:`/`unique:` em strings de `app/` e `src/` (controllers com regras escritas na chamada).
Não foram medidas: o verificador de presença consulta o banco. Ficam para quando houver decisão sobre o uso de banco.

## 4. Defeitos do PR vistos na leitura

Os defeitos do Laravel 8 do PR que já existem no 7.4 (a resposta 406 do `DBFormRequest::response()`, que o Laravel 8 não chama, e o nome de classe duplicado `AutenticacaoRequest`) estão no registro único `defeitos-laravel8-do-pr.md` (seções 4 e 6); não se repetem aqui.

## Conferência das contagens

Rodar da raiz do repositório (`P` = `-- ecidade/app ecidade/src`):

| Contagem | Comando | Resultado |
|---|---|---|
| declarações de form request | `git grep -hE '^(abstract )?class \w+ extends (FormRequest\|DBFormRequest\|BaseFormRequest)\b' $P \| wc -l` | 289 (140 de `FormRequest` + 105 + 44) |
| `validated()` e `safe()` | `git grep -nE '\->(validated\|safe)\(' $P \| wc -l` | 0 |
| `->only(` / `->except(` | `git grep -nE '\->only\(' $P \| wc -l` / `... '\->except\(' ...` | 5 / 1 |
| `->validate(` (linhas / arquivos) | `git grep -nE '\->validate\(' $P \| wc -l` / `git grep -lE ... \| wc -l` | 104 / 50 (97 por `$this->validate(`) |
| `Validator::make` (linhas / arquivos) | `git grep -nE 'Validator::make' $P \| wc -l` / `git grep -lE ... \| wc -l` | 18 / 15 |
| `exists:`/`unique:` em string | `git grep -nE "['\"\|](exists\|unique):" $P \| wc -l` | 107 |
| `digits:` (linhas / arquivos) | `git grep -nE 'digits:' $P \| wc -l` / `git grep -lE ... \| wc -l` | 11 / 5 |

As contagens de casos (1.350, 348) e de classes medidas saem da execução dos dois scripts (abaixo).

## Como reproduzir

```bash
# vendor do Laravel 8.73.2 resolvido para o PHP 7.4 (precisa de rede só nesta etapa)
mkdir l8 && cd l8 && echo '{"require":{"laravel/framework":"8.73.2"},"config":{"platform":{"php":"7.4.33"},"audit":{"block-insecure":false}}}' > composer.json
composer install --no-scripts --no-interaction
# nos dois PHPs, sem rede e sem banco
for v in 7.4 8.5; do
  docker run --rm --network none -v $PWD/vendor:/work/vendor:ro -v <repo>/scratchpad/laravel8_validacao_medir.php:/work/m.php:ro \
    -v <repo>/ecidade:/ecidade:ro -v $PWD/saida:/out -w /work php:$v-cli php -d memory_limit=1G m.php /ecidade /out/val-$v.json
done
cmp saida/val-7.4.json saida/val-8.5.json     # a matriz: laravel8_validacao_matriz.php, mesmos argumentos
```
