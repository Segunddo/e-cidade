# Eloquent e datas com o Laravel 13 (PHP8-55): repetir a T-117/T-124

Repete a prova dos 58 models em memoria (`models-dates-casts.md`, script `scratchpad/models_dates_casts.php`: 7 valores x leitura, `toArray()`, `toJson()`, escrita, mais o JSON com todas as datas juntas) com o
**vendor do 8.5 da integracao** (Laravel 13.43.0 = Eloquent 13, Carbon 3.15.1, Passport 13.12.0) contra o 7.4 com o vendor do PR, pelo `docker/composer-85/roda-isolado.sh` (imagens do projeto, `pt_BR`, sem rede, falha alto). Sem banco.
Runner: `bash scratchpad/roda_models_l13.sh` (compara com a referencia da T-124 e com as saidas guardadas). Saidas: `eloquent-laravel13/`.

## Resultado

| Comparacao | Resultado |
|---|---|
| 7.4 (vendor do PR) x referencia da T-124 | **identica** (3.204 linhas) |
| 8.5 com Laravel 13, **sem** sobreposicao | 57 dos 58 models **identicos ao 7.4**; 1 model difere (abaixo) - `saida-8.5-laravel13-sem-sobreposicao.txt`, `diferenca-sem-sobreposicao.txt` |
| 8.5 com Laravel 13, **com** a sobreposicao do item abaixo | **identica ao 7.4 byte a byte** (3.204 linhas, 0 linhas de diferenca: leitura, `toArray()`, `toJson()`, JSON inteiro **e escrita**) - `saida-8.5-laravel13.txt`; `diferenca-7.4-8.5.txt` vazia |

Os 57 models (inclusive os 21 que a T-124 passou de `$dates` para `$casts` `datetime`) saem **iguais ao 7.4 byte a byte** no Eloquent 13 + Carbon 3: `Illuminate\Support\Carbon`, JSON em ISO-8601 UTC com microssegundos
(`2021-03-15T13:20:30.000000Z`), data so com dia (`...T03:00:00.000000Z`), valor gravado (`Y-m-d H:i:s`), `''` = agora, `15/03/2021` = `InvalidFormatException`, `null`. A troca `$dates` -> `$casts` da T-124 e o que faz isso valer no 13
(antes dela, 18 models/37 atributos deixavam de converter, medido na PHP8-55). O `getDates()` do 13 so devolve `created_at`/`updated_at`.

## A unica quebra: cast `DateTime` (maiusculas) em `Assinador/CertificadoUsuario`

`app/Domain/Assinador/CertificadoUsuario.php:22-23` declara `'c142_data' => 'DateTime'` e `'c142_validade' => 'DateTime'`.

- **7.4 (Laravel 8 do PR):** a **leitura** funciona (o `getCastType` baixava o nome para `datetime`); a **escrita lanca** `Error: Call to undefined method DateTime::set()` (o Laravel 8 trata a classe `DateTime` como cast
  personalizado ao gravar); um valor que nao e data (`15/03/2021`) lanca antes `InvalidFormatException`, porque o Laravel 8 converte a data primeiro. Caminho alcancavel: `CertificadoPfxService.php:114-119` grava `c142_data` e `c142_validade` e chama `save()`; `:47` le `c142_validade`.
- **8.5 com o Laravel 13, sem sobreposicao:** a **leitura tambem falha** (`Call to undefined method DateTime::get()`: o `getCastType` do 13, `HasAttributes.php:978`, testa `class_exists($castType)` e trata `DateTime` como classe, sem baixar o nome).

Regra do projeto (referencia = 7.4; so atualizar): o 8.5 repete o 7.4 e nao habilita no 8.5 uma gravacao que o 7.4 nao faz. Correcao **por sobreposicao do 8.5**: `ecidade/app-85/Domain/Assinador/CertificadoUsuario.php` (o 7.4 le o `app/` e fica intacto):

- `$casts` com `'datetime'` nas duas colunas: a **leitura** volta a sair como no 7.4;
- `setAttribute()` para `c142_data`/`c142_validade`: converte o valor como o Laravel 8 (`fromDateTime`, que lanca `InvalidFormatException` para data invalida) e **lanca o mesmo** `Error: Call to undefined method DateTime::set()`: a **escrita** repete o 7.4.

`bash docker/composer-85/composer-85.sh dump-autoload --no-scripts` avisa, como esperado: `Ambiguous class resolution, "App\Domain\Assinador\CertificadoUsuario" was found in both "/app/app-85/..." and "/app/app/...", the first will be used.` (1 aviso; o do 8.5 vence).
Prova sem banco: os 9 valores de entrada (`d`, `dh`, `us`, `br`, `ts`, `nulo`, `vazio`, objeto `Carbon` e objeto `DateTime`) x escrita de `c142_data` e `c142_validade` saem iguais ao 7.4 (mesma classe de erro e mesma mensagem). O defeito do 7.4 (a gravacao do certificado do usuario nunca funciona)
e do Laravel do PR e entra no registro unico da PHP8-49 (`defeitos-laravel8-do-pr.md`, da T-105/T-148); aqui so se aponta, sem corrigir.

## Fora do que esta prova mede

- Os usos de Carbon (`formatLocalized`, `createFromTimestamp`, `diffIn*`, `->age`): ja medidos na PHP8-55 (`carbon3-usos.md`, patches).
- Acessores (`$appends`) dos models entram no `toArray()`/`toJson()` medidos; nao ha acessor `get*Attribute` sobre atributo de data nos 21 models.
- O que precisa de banco fica como na T-117: ler linhas reais por tipo de coluna, escrita com `save()`/`created_at`, bindings de data, fuso da sessao do PostgreSQL.
- A inicializacao do app no Laravel 13 (`Passport::routes()` no `AuthServiceProvider`) e da T-143/T-135; este trecho carrega so os models.

## Repetir

```bash
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+      # vendor do 8.5 (Laravel 13)
bash docker/composer-85/composer-85.sh dump-autoload --no-scripts                          # depois de criar/mudar classe em ecidade/app-85/ (avisa a ambiguidade esperada)
# vendor do PR (runtime-85/referencia-74/vendor): passos em docs/migracao-laravel/middlewares-laravel13.md
bash scratchpad/roda_models_l13.sh                                                         # 7.4 e 8.5 pelo roda-isolado.sh; compara com as referencias
```
