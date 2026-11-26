# Configuração efetiva de erros: PHP e Laravel, 7.4 × 8.5 (o que aparece na tela e o que vai para o log)

Vários achados dependem de "o aviso aparece na tela ou não" (por exemplo, `Notice` no 7.4 e `Warning` no 8.5 no SDK do Pix). Esta medição mostra, nas imagens do grupo, **qual `error_reporting`, `display_errors` e log valem em cada caminho** (tela legada, Laravel, CLI) e **o que um Notice, um Warning e um Deprecated fazem na resposta e no log**.
**Só leitura de código e trechos isolados: nada de banco, nada de rede** (`--network none`); o Apache da imagem sobe dentro do contêiner e é chamado por `localhost`.

## 1. Resumo

| | PHP 7.4 | PHP 8.5 |
|---|---|---|
| `error_reporting` da imagem (Apache) | `E_ALL & ~E_DEPRECATED & ~E_STRICT` (22527) | `E_ALL` (30719) |
| `display_errors` / `log_errors` / `error_log` da imagem | Off / On / `/var/log/php_errors.log` | Off / On / `/var/log/php_errors.log` |
| Tela legada, depois do `bootstrap.php` | `E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED & ~E_STRICT` (22517), `display_errors` Off | o mesmo valor |
| Rota do Laravel (`/v4`, `/web`), depois do `bootstrap()` do kernel | `error_reporting(-1)`, `display_errors` Off; todo erro vira `ErrorException`, depreciação vai para o log do Laravel | o mesmo mecanismo |
| Mensagem de variável ou índice indefinido | `Notice: Undefined variable: x` / `Undefined index: k` | `Warning: Undefined variable $x` / `Undefined array key "k"` |

**Diferenças com causa (seção 6):** 7 pontos. Os que mudam o que o usuário ou o log recebe: no 8.5 o tratador de erros da tela legada **lança `ArgumentCountError` para todo `E_USER_*`** (`trigger_error`), em vez de registrar e seguir, **mesmo nas telas que zeram o `error_reporting()`** (no 7.4 essas telas ficam em silêncio); o 8.5 escreve **110 entradas** no `storage/logs/laravel.log` na primeira requisição de uma rota do Laravel (o 7.4 escreve 2); e o 8.5 acrescenta **12 linhas de depreciação de carga** (15 com o vendor do `composer.lock` do PR) em `/var/log/php_errors.log` por requisição fria de tela legada (o 7.4 escreve 0).

## 2. Como foi medido

As imagens do grupo: `docker/php74-apache/Dockerfile` (Ubuntu 22.04, `libapache2-mod-php7.4`, PHP 7.4.33; o `php.ini` de produção do pacote com `short_open_tag`, `date.timezone`, `session.gc_maxlifetime` e `error_log` ajustados por `sed`) e `docker/php85-apache/Dockerfile` (`php:8.5-apache`, PHP 8.5.12, sem `php.ini`, com `conf.d/zz-ecidade.ini` que fixa `error_reporting = E_ALL`, `display_errors = Off`, `log_errors = On`, `error_log`). O `docker-compose.php85.yml` ainda monta `paridade-56.ini` (só `output_buffering = 4096`, sem efeito em erros).

`scratchpad/erros_roda.sh` sobe cada imagem num contêiner `--network none`, com `ecidade/` montado só leitura em `/e`, o vendor do Laravel 8.73.2 em `/e/vendor` (o do 7.4: `composer install` do `composer.lock` do PR; o do 8.5: o do `composer-85.lock`, com `lcobucci/jwt` 4.1.5, instalado por `docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+`), um `.env` de teste (`APP_ENV=local`, `APP_DEBUG=true`, host de banco inexistente) e `/e/extension/log` e `/e/storage` graváveis em pasta de saída. O `config/application.php` local (não versionado) é coberto por um arquivo vazio: **só vale o `config/application.default.php`**.
Para cada caminho, chama `scratchpad/erros_probe.php` por HTTP em `localhost`, duas vezes: a primeira com o Apache recém-iniciado (opcache frio) e a segunda logo depois (opcache quente), e guarda a resposta e os três logs.

```bash
bash scratchpad/erros_roda.sh ecidade <vendor 7.4> <vendor 8.5> <imagem 7.4> <imagem 8.5> <env de teste> <pasta de saida>
```

O `erros_probe.php` roda em 3 camadas (parâmetro `camada`): `a` só com o `php.ini` da imagem; `b` depois de `require bootstrap.php` (o que toda tela legada carrega, mais o registro dos ouvintes de erro que o `app.php` faz com `loadEvents()`); `c` depois de `bootstrap/app.php` + `Http\Kernel::bootstrap()` do Laravel do PR (com um `Request` em memória). Em cada uma lê as diretivas e dispara 7 eventos: variável indefinida, índice indefinido, `file_get_contents` de arquivo inexistente (os três de motor), `trigger_error` com `E_USER_NOTICE`, `E_USER_WARNING` e `E_USER_DEPRECATED`, e `utf8_encode()` (depreciada desde o 8.2).
`?exibir=on` liga `display_errors` depois do bootstrap, para ver o formato do que sairia na tela; `?er=<texto>` reproduz `ini_set('error_reporting', <texto>)`.

## 3. Camada A: o `php.ini` da imagem

| Diretiva (Apache, `mod_php`) | 7.4 | 8.5 |
|---|---|---|
| arquivo `php.ini` carregado | `/etc/php/7.4/apache2/php.ini` | nenhum (só `conf.d/*.ini`) |
| `error_reporting` | 22527 = `E_ALL & ~E_DEPRECATED & ~E_STRICT` | 30719 = `E_ALL` |
| `display_errors` | Off | Off |
| `display_startup_errors` | Off | **On** (padrão do 8.x sem `php.ini`) |
| `log_errors` / `error_log` | On / `/var/log/php_errors.log` | On / `/var/log/php_errors.log` |
| `html_errors` | On | On |
| `ignore_repeated_errors` | Off | Off |

CLI (por exemplo `artisan`, cron): 7.4 com `/etc/php/7.4/cli/php.ini`, `error_reporting` 22527, `display_errors` vazio (Off), `log_errors` On, `html_errors` Off; 8.5 sem `php.ini`, `error_reporting` 30719, `display_errors` vazio, `log_errors` On, `html_errors` Off.

**`ecidade/.user.ini` não vale.** Ele define `error_reporting = E_ALL & ~E_NOTICE & ~E_DEPRECATED & ~E_STRICT`, `display_errors = Off`, `log_errors = On` e `error_log`, mas só é lido por CGI/FastCGI; com `mod_php` (as duas imagens) é ignorado. Prova: o probe foi servido de uma pasta com uma cópia desse arquivo e o `error_reporting` efetivo ficou em 22527 (7.4) e 30719 (8.5), os valores da imagem.

## 4. Camada B: o que o código legado muda em tempo de execução

| Onde | O quê |
|---|---|
| `config/application.default.php:22`, `:27` | `php.display_errors = false`; `php.error_reporting = E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED & ~E_STRICT` (= 22517: sobram `E_ERROR`, `E_PARSE`, os `E_CORE_*` e `E_COMPILE_*`, `E_USER_ERROR`, `E_USER_WARNING`, `E_USER_NOTICE`, `E_RECOVERABLE_ERROR` e `E_USER_DEPRECATED`) |
| `bootstrap.php:87-89` | aplica os dois com `ini_set` e `error_reporting()` (e `app.php:43-45` repete para requisições de extensão). Se existir `config/application.php`, ele é lido por cima do default (`bootstrap.php:75-79`) |
| `bootstrap.php:142-144` | com `app.error.handler = 'Default'` (`config/application.default.php:97`) instala `Error::register()`, `Exception::register()` e `Shutdown::register()`; o `set_error_handler` usa a mesma máscara (`src/V3/Error/Handler/Error.php:14`) |
| `app.php:143` | `loadEvents()` registra o ouvinte `app.error` (`ECidade\V3\Error\EventHandler`), que grava em `extension/log/error.log` (`app.error.log.path`, `config/application.default.php:109`) |
| telas que fazem `ini_set('error_reporting', ...)` | 68 arquivos (`git grep -lE "ini_set\(\s*['\"]error_reporting['\"]" -- 'ecidade/*.php' ':!ecidade/vendor'`); 57 linhas passam um **texto** como `"E_ALL & ~NOTICE"` |

Efeito medido de `ini_set('error_reporting', "E_ALL & ~NOTICE")` (texto, como nas telas; 61 dos 68 arquivos estão na raiz de `ecidade/`): o `error_reporting` fica **0** nos dois PHPs (o valor do `ini_set` é lido como número e o texto vira 0); `ini_set('error_reporting', 0)` dá o mesmo.
O que acontece depois **não é igual**: no 7.4 a tela fica em silêncio (`php_errors.log` e `extension/log/error.log` com 0 linha); no 8.5 os disparos de motor ficam em silêncio, mas **`E_USER_NOTICE`, `E_USER_WARNING` e `E_USER_DEPRECATED` lançam `ArgumentCountError`** (seção 7, diferença 4), porque a máscara do `set_error_handler` é fixada no `register()` (22517, `Error.php:14`) e o PHP chama o tratador mesmo com `error_reporting()` em 0. No 7.4 o `handle()` sai em `error_reporting() === 0` (`Error.php:27-30`); no 8.5 o erro de argumentos acontece na chamada, antes dessa linha.

## 5. Camada C: o Laravel do PR

| Onde | O quê |
|---|---|
| `vendor/laravel/framework/.../Foundation/Bootstrap/HandleExceptions.php:42`, `:50-51` | `error_reporting(-1)`; `display_errors = Off` (a menos que `APP_ENV=testing`) |
| `HandleExceptions.php:69-75` | erro de nível ativo vira `ErrorException`; depreciação (`E_DEPRECATED`/`E_USER_DEPRECATED`) vai para `handleDeprecation` (`:86`) |
| `HandleExceptions.php:86-118` | grava no canal `deprecations`; se `logging.deprecations` não existe, usa o canal `null` |
| `configuration/logging.php:36-75` | canais `stack`, `single`, `daily`, `slack`, `stderr`, `syslog`, `errorlog`; **sem `null` nem `deprecations`** |
| `configuration/app.php:41`, `.env.example:4` | `app.debug = env('APP_DEBUG', true)`; `.env.example` traz `APP_DEBUG=true` |
| `app/Exceptions/Handler.php` | fora de `/web`, devolve JSON `{error, message}` com o código do status |

Como não há canal `null` nem `deprecations`, cada depreciação gera **duas entradas** em `storage/logs/laravel.log`: `laravel.EMERGENCY: Unable to create configured logger. Using emergency logger.` (por `InvalidArgumentException: Log [deprecations] is not defined`) e o `laravel.WARNING` com o texto da depreciação.

## 6. O que cada disparo faz

Resposta com `display_errors` ligado (`exibir=on`), por camada; log com o padrão da camada.

| Camada | Disparo | 7.4 | 8.5 |
|---|---|---|---|
| A (só a imagem) | variável/índice indefinido | Notice, na resposta (682 B no total) e em `/var/log/php_errors.log` | **Warning** (texto `Undefined variable $x`, `Undefined array key "k"`), na resposta (879 B no total) e no log |
| A | `file_get_contents` inexistente | Warning (`failed to open stream`) | Warning (`Failed to open stream`, com maiúscula) |
| A | `E_USER_NOTICE`, `E_USER_WARNING`, `E_USER_DEPRECATED` | Notice, Warning, Deprecated | Notice, Warning, Deprecated |
| A | `utf8_encode()` | silencioso (`E_DEPRECATED` fora do `error_reporting`) | `Deprecated: Function utf8_encode() is deprecated since 8.2`, na resposta e no log |
| B (tela legada) | os 3 de motor (Notice/Warning) | **nada**, nem na resposta nem no log (mascarados) | nada (mascarados) |
| B | `E_USER_NOTICE`, `E_USER_WARNING`, `E_USER_DEPRECATED` | passam pelo tratador do ecidade, vão para `extension/log/error.log` **e** para `/var/log/php_errors.log`; com `display_errors` ligado saem 305 B na resposta | **`ArgumentCountError`** nos 3: nada em `extension/log/error.log`, nada em `/var/log/php_errors.log` e, na tela real, exceção não tratada |
| B | `utf8_encode()` | silencioso | silencioso (`E_DEPRECATED` mascarado depois do bootstrap) |
| C (rota Laravel) | variável/índice indefinido, arquivo inexistente, `E_USER_NOTICE`, `E_USER_WARNING` | `ErrorException` (`Undefined variable: x`...), resposta vazia do probe | `ErrorException` (`Undefined variable $x`, `Undefined array key "k"`...) |
| C | `E_USER_DEPRECATED`, `utf8_encode()` | `E_USER_DEPRECATED` só em `laravel.log` (WARNING); `utf8_encode` silencioso | os dois em `laravel.log` (cada um com uma linha `EMERGENCY` antes) |

## 7. Diferenças 7.4 × 8.5, com causa

| # | Diferença | Causa |
|---|---|---|
| 1 | `error_reporting` da imagem: 22527 (7.4) × 30719 (8.5) | o 7.4 usa o `php.ini` de produção do pacote (`E_ALL & ~E_DEPRECATED & ~E_STRICT`); a imagem 8.5 não tem `php.ini` e o `zz-ecidade.ini` fixa `E_ALL` |
| 2 | no 8.5 `display_startup_errors` = On | padrão do PHP 8.x sem `php.ini`; o 7.4 vem Off do `php.ini` de produção. Só aparece se `display_errors` for ligado |
| 3 | variável e índice indefinidos: Notice no 7.4, Warning no 8.5, com texto novo (`Undefined variable $x`, `Undefined array key "k"`) | mudança do PHP 8.0 (o nível e a mensagem). Na tela legada o `php.error_reporting` mascara `E_NOTICE` **e** `E_WARNING`, então os dois continuam invisíveis; quem usar só `~E_NOTICE` numa máscara numérica passaria a ver esses avisos no 8.5 (como Warning) e não os via no 7.4 |
| 4 | **tratador de erros da tela legada**: no 8.5 todo `E_USER_*` (e `E_RECOVERABLE_ERROR`) que casa com a **máscara do `set_error_handler`** (fixada no `register()`, 22517, `Error.php:14`; vale também nas telas que zeraram o `error_reporting()`) lança `ArgumentCountError: Too few arguments to function ECidade\V3\Error\Handler\Error::_handle(), 4 passed and exactly 5 expected` | `src/V3/Error/Handler/Error.php:20` declara `_handle($type, $message, $file, $line, $context)`; o PHP 8.0 deixou de passar `$context` ao tratador. No 7.4 o erro é registrado em `extension/log/error.log` e segue para o log do PHP (e, com `error_reporting()` em 0, o `handle()` sai em silêncio: `Error.php:27-30`); no 8.5 vira exceção nos dois casos. Há 29 chamadas a `trigger_error` em 5 arquivos de `ecidade/` fora de `vendor/` (`git grep -nE "\btrigger_error\(" -- 'ecidade/*.php' ':!ecidade/vendor' ':!ecidade/fpdf151' ':!ecidade/dbagata' ':!ecidade/libs/PHPMailer*' ':!ecidade/tests'`), por exemplo `libs/db_stdlibwebseller.php:4413` e `pes4_gerafolha002.php:443` (`E_USER_ERROR`) |
| 5 | depreciações no log do PHP por requisição de tela legada: **12** (frio; 9 do vendor, 3 do código do PR) e 3 (quente) no 8.5 com o vendor do `composer-85.lock` × 0 no 7.4. Com o vendor do `composer.lock` do PR (`lcobucci/jwt` 3.4) são 15 (12 do vendor, 3 do PR), porque o `Token` 3.4 acrescenta 3 | as do vendor (`Implicitly marking parameter ... as nullable`: `guzzlehttp/promises` 6, `laravel/framework` 2, `opis/closure` 1 no 8.5; mais `lcobucci/jwt` 3 com o vendor do PR) são geradas ao carregar o autoload, **antes** de o `bootstrap.php` baixar o `error_reporting`; as 3 do PR repetem em toda requisição: `ParameterBag::getIterator()` e `ParameterBag::count()` (`Return type ... should either be compatible`) e `Constant E_STRICT is deprecated since 8.4` em `config/application.default.php:27` (se existir `config/application.php` com a mesma linha, a mensagem sai de novo) |
| 6 | no Laravel, `storage/logs/laravel.log` por requisição: 110 entradas (frio) e 8 (quente) no 8.5 × 2 no 7.4 | cada depreciação gera `EMERGENCY` + `WARNING` (seção 5); o 8.5 tem 55 depreciações na primeira requisição (53 do vendor, por arquivo de origem: `laravel/framework` 31, `nesbot/carbon` 15, `symfony/console` 4, `laravel/passport` 3; mais as 2 do probe; `guzzlehttp/promises`, `lcobucci/jwt` e `opis/closure` não entram aqui: são carregados antes do `HandleExceptions` e vão para o `php_errors.log`, diferença 5) e 4 depois (`Carbon::createFromTimestamp`, `CarbonImmutable::createFromTimestamp` e as 2 do probe: 8 entradas). O php.ini do Laravel (`display_errors` Off) não muda: a resposta não ganha nada |
| 7 | `utf8_encode()` (usada por `DBString::utf8_encode_all`, `app/Exceptions/Handler.php` e pelas notificações) deixa de ser silenciosa fora da tela legada | depreciada desde o 8.2: aparece no `php_errors.log` quando `E_DEPRECATED` está ativo (camada A) e no `laravel.log` (camada C); na tela legada continua mascarada |

Nada disto foi corrigido: é o registro da configuração e do efeito para o grupo decidir.

## 8. Limites

- **Para repetir.** O `erros_roda.sh` exige, dentro de `ecidade/`, um `.env` (de teste: copia do `.env.example` com `APP_ENV=local`, `APP_DEBUG=true`, host de banco inexistente) e um `vendor/` (o `composer install` do `composer.lock` do PR, Laravel 8.73.2; o 8.5 usa o do `composer-85.lock`, que traz `lcobucci/jwt` 4.1.5; os números deste registro, no 8.5, são os dele. Com o vendor do `composer.lock` do PR no 8.5 (jwt 3.4) a carga fria da tela legada tem 15 linhas, não 12, e o `laravel.log` fica igual): são os pontos de montagem do contêiner, e sem eles o `docker run` falha (`read-only file system`). O `erros_roda.sh` agora aborta com mensagem se faltar um deles ou se o contêiner falhar.
- **Imagens.** A de 7.4 é a construída de `docker/php74-apache` (`t102-php74-ref`) e a de 8.5 a construída de `docker/php85-apache` (`ecidade-login-php85`, que traz o `zz-ecidade.ini` atual). Imagens de teste só de CLI, sem `php.ini`, **não** representam o ambiente: com elas todo `error_reporting` sai vazio.
- **`config/application.php` local.** Fica de fora (vale o `application.default.php`); uma instalação com cópia local pode sobrepor `php.error_reporting` e `php.display_errors`.
- **Camada C sem requisição real.** O bootstrap do kernel é executado, mas nenhuma rota e nenhum banco; erros de aplicação dentro de controllers (JSON do `Handler`) não foram exercitados.
- **Opcache.** "Frio" é a primeira requisição após reiniciar o Apache; "quente" é a seguinte. Depreciações de compilação (parâmetro nulo implícito) saem só na frio; as de vinculação de classe (`Return type`) e a de constante saem em toda requisição.
- **Whoops.** O ramo `app.error.handler = 'Whoops'` do `bootstrap.php:122-139` não é o padrão (`'Default'`) e não foi medido.
- **`php-fpm`.** Não há; o `.user.ini` só valeria nele.
