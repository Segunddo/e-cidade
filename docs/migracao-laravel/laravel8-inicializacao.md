# Laravel 8 do PR de pe no 8.5: inicializacao e configuracao (PHP8-62), medicao preliminar

**Situacao:** medicao **preliminar**, feita com o `vendor` do proprio PR (`ecidade/composer.lock`: Laravel 8.73.2, Passport 10, `lcobucci/jwt` 3.4,
Guzzle 7.5.0) nos dois PHP. Nada foi corrigido com base nela: o `vendor` do 8.5 (PHP8-79 + `lcobucci/jwt` PHP8-60 + os 9 pacotes PHP8-87) sera
outro. O aceite e repetir os mesmos comandos com o `vendor` do 8.5 integrado (secao "Repetir com o vendor do 8.5").

Sem banco: conteineres `php:7.4-cli` e `php:8.5-cli` com `--network none`, `.env` vazio, chaves do Passport geradas so para o teste (sem segredo real),
`storage/` e `bootstrap/cache/` gravaveis em pasta nova a cada rodada. O `ecidade/` e montado somente leitura (o 7.4 le o mesmo `./ecidade`).
Defeitos do Laravel 8 do PR e das bibliotecas ficam no registro da PHP8-49; aqui so se mede e se descreve o resultado.

## Como foi montado

- `vendor`: `composer install` da `composer.lock` do PR fora do repositorio (sem rede no passo de execucao) e, depois, `composer dump-autoload` com o
  `composer.json` real, para o autoload incluir `app/Helpers/*`, `database/` e `Fpdf\`. Montado em `ecidade/vendor`, como o desenho da PHP8-79
  (`docs/registro/estrutura-85.md`): o `bootstrap.php`, o `artisan` e o `bootstrap/app.php` rodam **sem alteracao**.
- Script: `scratchpad/laravel_init.php [raiz]` (usa `bootstrap.php`, `bootstrap/app.php` e o Kernel de console, como o `artisan`).
- `php artisan --version` real: `Laravel Framework 8.73.2` nos dois.

## Resultado: 1.932 linhas iguais, 1 diferenca de configuracao

Saida de referencia (7.4): `laravel8-inicializacao/saida-7.4.txt`. Diferenca 7.4 x 8.5: `laravel8-inicializacao/diferenca-7.4-8.5.txt` (6 linhas).

| Criterio | 7.4 | 8.5 |
|---|---|---|
| Versao do framework | 8.73.2 | 8.73.2 |
| Rotas (tabela do roteador: metodos, URI, nome, acao, middleware, dominio) | 1.427 | 1.427, **identicas** |
| Comandos do artisan | 112 | 112, identicos |
| Configuracao efetiva (so chaves e tipos) | 307 chaves em 17 grupos | **308**: so `logging.channels.deprecations` (NULL), criada pelo proprio Laravel quando trata um `Deprecated` (ver abaixo) |
| Providers carregados no boot | 43 (33 em `app.providers`, adiados 0) | 43, identicos (lista na saida) |
| Aliases | 34 | 34 |
| Fuso | config e PHP `America/Sao_Paulo` | igual |
| Handler (`App\Exceptions\Handler`) | excecao simples 500, 404, codigo 403 -> JSON `{"error":true,"message":...}`; validacao -> redirecionamento | igual |

Valores de uma lista sem segredo (`V` na saida): `cache.default=file`, `session.driver=file`, `session.lifetime=120`, `session.cookie=laravel_session`,
`queue.default=sync`, `filesystems.default=local`, `logging.default=stack`, `database.default=mysql`, `hashing.driver=bcrypt`; iguais nos dois.

`php artisan route:list` **nao roda sem banco**: o comando instancia os controllers para ler os middlewares e um deles consulta
`secretariadeeducacao.sec_parametros` ao ser construido (`could not find driver (SQL: ...)`, igual no 7.4 e no 8.5). Por isso a tabela de rotas e lida
direto do roteador (`$app['router']->getRoutes()`), que e o que o comando listaria.

## Pontos conhecidos do criterio 2

| Ponto | Medido | 7.4 x 8.5 |
|---|---|---|
| `env()` fora de `configuration/` | **109 ocorrencias em 105 linhas em 46 arquivos** (`app/` 85 ocorrencias em 82 linhas em 33 arquivos; raiz 7/6/6; `model/` 5/5/1; `fpdf151/` 4/4/4; `extension/` 4/4/1; `src/` 4/4/1) e 78 ocorrencias em 78 linhas em 11 arquivos dentro de `configuration/`. Comando: `python3 scratchpad/conta_laravel_init.py ecidade` (expressao regular, sem `getenv` nem metodos; imprime ocorrencias, linhas e arquivos). Conferencia por linha: `git grep -nE "(^|[^[:alnum:]_>:$])env\(" -- 'ecidade/*.php' ':!ecidade/vendor' ':!ecidade/configuration' | wc -l` = 105 (o `git grep` conta linhas; 4 linhas tem 2 ocorrencias). A especificacao falava em 82 em 33: bate com as **linhas** de `app/` | leitura de `true`, `false`, `null`, `(empty)`, vazio, texto, `0`, texto entre aspas e ausente (com e sem padrao): iguais |
| `Cache::put` (6 pontos, mesmo comando: `AssinadorAPI.php:177`, `LicitaconObrasClient.php:47`, `PNCPClient.php:67`, `BnafarClient.php:234`, `EmissaoContraChequeJob.php:124`, `src/Lib/Request/ProcessoEletronico/ProcessoEletronico.php:209`) | no Laravel 8 o inteiro e **segundos** (como no 7.4): `put(.., 60)` grava expiracao em 60 s; `put(.., DateInterval)` e `remember(.., 30, ..)` funcionam; o ponto de `ProcessoEletronico` passa um `Carbon` (`addMinutes(10)`), sem efeito de unidade | igual; a mudanca de unidade nao existe do 7.4 para o 8.5 (so aparece em saltos posteriores) |
| Dotenv | `\Dotenv\Dotenv::createImmutable()` existe (`bootstrap.php:158`, `emp4_empempenho004.php:1344`) | igual; `.env` vazio carrega sem erro |
| Sessao (Laravel) | driver `file`, `FileSessionHandler`, cookie `laravel_session`, 120 min | igual |
| Cache | store `file` (`FileStore`) | igual |

## So no 8.5: avisos `Deprecated` ao subir o kernel (15 mensagens)

Nada muda na saida acima; sao avisos do PHP 8.x, ate o PHP 8.4. Contagem: `grep -c '^Deprecated' saida-8.5.err` (stderr do `laravel_init.php`).
Origem (arquivo:linha, medido):

- **Vendor do PR (12):** Guzzle promises (6, `functions.php:24,262,263,288,289,310`), `lcobucci/jwt` `Token.php:75,77,289` (3), Opis `functions.php:32`,
  Laravel `helpers.php:184,375` (`optional()` e `with()`). Mudam com o `vendor` do 8.5; nao se mexe aqui.
- **Codigo versionado do e-Cidade (3):** `src/V3/Extension/ParameterBag.php:133` e `:142` (tipo de retorno de `getIterator()` e `count()`) e
  `config/application.default.php:27` (constante `E_STRICT`, descontinuada no 8.4). Nao fazem parte da inicializacao do Laravel; ficam como ponteiro
  para quem faz o lint do 8.5.
- **`config/application.php` nao entra na medicao.** O arquivo e opcional e nao versionado (`ecidade/.gitignore:9`; o `bootstrap.php:77-78` so o carrega se existir) e
  nao existe na base. A primeira rodada rodou com uma copia local antiga dele (de 12/11, de outra base), que acrescentava um `Deprecated` (`application.php:27`, 16 no total);
  a rodada guardada aqui usa so o `config/` versionado (`git archive HEAD ecidade/config`, montado por cima de `ecidade/config`): saida do 7.4 e do 8.5 sem mudanca
  em nenhuma linha em relacao a primeira, 15 `Deprecated` em vez de 16. O comando de repeticao fixa isso.
- Como o Laravel 8 liga o tratamento de `Deprecated` no boot e a configuracao de log nao tem o canal `deprecations`, a chave
  `logging.channels.deprecations` aparece na configuracao do 8.5: e a unica diferenca da tabela.

## Repetir com o vendor do 8.5 (aceite)

```bash
# vendor do 8.5 (PHP8-79): COMPOSER=composer-85.json, via docker/composer-85/composer-85.sh; autoload completo montado em ecidade/vendor
# config/ so com os arquivos versionados (sem config/application.php local):
mkdir -p /tmp/cfg && git archive HEAD ecidade/config | tar -x -C /tmp/cfg
for v in 7.4 8.5; do
  docker run --rm --network none -w /w/ecidade -v $PWD/ecidade:/w/ecidade:ro -v /tmp/vazio:/w/ecidade/.env:ro -v /tmp/cfg/ecidade/config:/w/ecidade/config:ro \
    -v <vendor do $v>:/w/ecidade/vendor:ro -v <storage gravavel>:/w/ecidade/storage -v <cache gravavel>:/w/ecidade/bootstrap/cache \
    -v <tmp gravavel>:/w/ecidade/tmp -v <arquivos gravavel>:/w/ecidade/arquivos -v $PWD/scratchpad:/s:ro \
    -e APP_ENV=production -e APP_KEY=<chave de teste> php:$v-cli php -d display_errors=stderr /s/laravel_init.php /w/ecidade > saida-$v.txt 2> saida-$v.err
done
diff saida-7.4.txt saida-8.5.txt     # a referencia (7.4) e a do PR; o 8.5 vem do vendor novo
```

No 8.5 o `vendor` e o novo; o 7.4 continua com o do PR. Itens a olhar na repeticao: numero de rotas (1.427), providers (43), comandos (112), chaves de
configuracao (307) e o que mudar de `Cache::put`/`env()`/sessao.
