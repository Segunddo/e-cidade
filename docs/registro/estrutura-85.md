# Estrutura do código só do PHP 8.5 (PHP8-79, 20/11/2026)

**Resumo:** o PHP 8.5 ganha composer, trava e `vendor/` próprios, sem mudar nada que o 7.4 lê. A lista é
`ecidade/composer-85.json`, a trava `ecidade/composer-85.lock`, e o `vendor/` fica em `runtime-85/vendor/`, fora de
`ecidade/` e fora do git. A sobreposição de classes só do 8.5 fica em `ecidade/app-85/`: só o PSR-4 do
`composer-85.json` a enxerga. Hoje o `composer-85.json` é a cópia do `composer.json` do PR com duas diferenças: a
sobreposição no PSR-4 e o `allow-plugins` só com o `cweagans/composer-patches`. O `composer-85.lock` é a cópia byte a byte do `composer.lock` do PR. O `composer install` no 8.5 passa
com 165 pacotes, ignorando só o teto de versão do PHP, que 10 pacotes ainda pedem (lista abaixo). O desenho reaproveita
o do runtime novo da base anterior (`composer-runtime-novo.json`, `app-runtime-novo/`, `vendor/` montado por cima).

Depois desta estrutura, a lista e a trava do 8.5 mudaram em três tarefas:

- PHP8-60: `lcobucci/jwt`;
- PHP8-87: os 9 pacotes, em `docs/migracao-laravel/pacotes-php85.md`;
- PHP8-62: Laravel 13.43.0 e Passport 13.12.0, com 171 pacotes, em `docs/migracao-laravel/composer-85-laravel13.md`.

## Onde fica cada coisa

| O quê | Onde | Quem lê |
|---|---|---|
| lista do 8.5 | `ecidade/composer-85.json` | só o Composer chamado com `COMPOSER=composer-85.json` |
| trava do 8.5 | `ecidade/composer-85.lock` (o Composer dá a ela o nome da lista) | idem |
| `vendor/` do 8.5 | `runtime-85/vendor/` na raiz do repositório (`.gitignore`) | o contêiner do 8.5, montado em `/var/www/html/vendor` |
| sobreposição | `ecidade/app-85/` (PSR-4 `"App\\": ["app-85/", "app/"]`, só no `composer-85.json`) | o autoload do `vendor/` do 8.5 |
| imagem do Composer | `docker/composer-85/Dockerfile` | o comando abaixo |
| comando único | `docker/composer-85/composer-85.sh` | quem mexe na trava do 8.5 |

Os dois arquivos ficam ao lado do `composer.json` do 7.4 para que `autoload` (arquivos de `app/Helpers`, `classmap` de
`database`, `psr-4` de `App\`, `Fpdf\` e `Tests\`) use os mesmos caminhos relativos.

**Como o 8.5 escolhe o autoload:** pela montagem, sem variável e sem mudar código. O código carrega
`vendor/autoload.php` (no `bootstrap.php`, no `artisan` e nas entradas do Laravel). No contêiner do 8.5,
`runtime-85/vendor` é montado sobre `/var/www/html/vendor`. O 7.4 continua montando `./ecidade` com o próprio `vendor/`.
O contêiner que roda o Laravel no 8.5 é da etapa da inicialização (PHP8-62). Para ele, falta acrescentar ao serviço do
8.5:

```yaml
    volumes:
      - ./ecidade:/var/www/html/
      - ./runtime-85/vendor:/var/www/html/vendor
      - ./runtime-85/bootstrap-cache:/var/www/html/bootstrap/cache   # o Laravel novo grava cache em outro formato
      - ./runtime-85/storage:/var/www/html/storage
```

No runtime da base anterior foi assim (`docker-compose.runtime-novo.yml`), inclusive com as duas chaves OAuth de
`ecidade/storage` montadas somente leitura por cima do `storage/` próprio.

**Sobreposição:** uma classe em `ecidade/app-85/` com o mesmo nome de uma de `ecidade/app/` vence no 8.5. O
`composer dump-autoload` do 8.5 põe no classmap o arquivo de `app-85/`, e a de `app/` fica para o 7.4. Para cada
classe sobreposta, o `dump-autoload` avisa (esperado, não é erro):
`Warning: Ambiguous class resolution, "App\Exceptions\Handler" was found in both "/app/app-85/Exceptions/Handler.php"
and "/app/app/Exceptions/Handler.php", the first will be used.` O "first" é o `app-85/`, primeiro da lista do PSR-4. Hoje
a pasta não existe: a primeira classe sobreposta cria a pasta, e depois de criar ou mudar um arquivo nela é preciso
rodar o `dump-autoload` do 8.5 (comando abaixo).

## Comando único (o dono da trava do 8.5 é o time do banco)

Toda mudança de `composer-85.json`/`composer-85.lock` sai deste comando. A imagem é pinada por digest:
`php:8.5-cli@sha256:50956f094e90…` (PHP 8.5.12) mais o binário do `composer:2.11.2@sha256:919efe8e6217…`. As extensões
são as do runtime 8.5 (`docker/php85-apache`): `bcmath calendar gd intl mbstring pgsql pdo_pgsql soap zip exif`. Os
pacotes do sistema (`apt`) da imagem não são pinados, mas a trava depende só da versão do PHP, das extensões e da
versão do Composer, e essas são fixas.

```bash
# gerar/atualizar a trava (resolve no 8.5; nao instala)
bash docker/composer-85/composer-85.sh update --no-install --no-scripts --ignore-platform-req=php+ [pacotes]
# instalar o vendor/ do 8.5 a partir da trava (runtime-85/vendor)
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+
# depois de criar/mudar classe em ecidade/app-85/
bash docker/composer-85/composer-85.sh dump-autoload --no-scripts
# conferir
bash docker/composer-85/composer-85.sh validate --no-check-publish
bash docker/composer-85/composer-85.sh prohibits php 8.5.12 --locked
```

O script monta `ecidade/` em `/app`, `runtime-85/vendor` em `/app/vendor` e `runtime-85/composer-home` como cache.
Ele roda com o uid de quem chama e com `--network host`, porque a rede bridge desta máquina não resolve DNS. A rede
serve só para baixar pacotes: nada se conecta a banco. O `ecidade/vendor` do 7.4 nunca é montado.

**`ecidade/vendor` como ponto de montagem:** a `base-php74` não versiona o `vendor/`, então um checkout novo não tem
essa pasta. Sem ela, o Docker cria `ecidade/vendor` para montar `/app/vendor` por cima, e cria como `root:root 755`.
Depois disso o `composer install` do 7.4 não consegue gravar nela (`Permission denied`), e só `root` a apaga. Por isso
o script cria `ecidade/vendor` antes do `docker run`, vazia e com o dono de quem chama: fica no mesmo estado de um
checkout sem `vendor/`. Se a pasta já existe, nada nela é tocado. Medido num worktree novo, antes e depois da
correção: `root:root 755` × `<usuário>:<grupo> 775`, gravável e vazia, com `validate` rc=0.

**Repositório do `dbseller/session` por HTTPS:** o `composer.json` do PR declara o repositório vcs
`git@github.com:DBSeller/Session.git` (SSH), e a imagem não tem `ssh`. Sem ajuste, o `update` para em
`error: cannot run ssh: No such file or directory`. O script passa ao `git` do contêiner
`GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=url.https://github.com/.insteadOf` e `GIT_CONFIG_VALUE_0=git@github.com:`, e o
clone sai por HTTPS (repositório público), sem mudar o `composer-85.json`. Medido em 20/11: `update dbseller/session
--no-install --dry-run` com rc=0 e o espelho em `composer-home/cache/vcs/git-github.com-DBSeller-Session.git`. O
`update` de todos os pacotes passa do SSH, mas a resolução ainda não fecha com as versões que o PR fixa: o Composer
2.11 recusa algumas delas. Sair dessas versões é das tarefas que trocam pacotes (PHP8-60, PHP8-87, PHP8-91 e
PHP8-62), que regeram a trava.

**Plugins: só o de patches.** Os comandos rodam **sem `--no-plugins`**, para o `cweagans/composer-patches` aplicar os
patches que as tarefas de pacote declaram em `extra.patches` (por exemplo, o patch da dompdf no 8.5). O
`config.allow-plugins` do `composer-85.json` libera só ele: `{"cweagans/composer-patches": true}`. O PR libera
`kylekatarnls/update-helper` e `symfony/flex`, mas nenhum dos dois está na trava, e o 7.4 continua com a lista do PR.
Prova com um patch de teste, num worktree descartável e fora do commit:
- o `composer-85.json` ganhou `cweagans/composer-patches` `^1.7` (resolveu 1.7.3) e um patch de uma linha no
  `Readme.md` do `michelf/php-markdown`;
- `update cweagans/composer-patches michelf/php-markdown` saiu com rc=0 e `Applying patches for michelf/php-markdown`,
  com a linha no arquivo;
- apagado o pacote, o `install` da trava nova saiu com rc=0 e reaplicou o patch.

A imagem tem `patch` e `git`. O `install` real, com a trava de hoje e sem `--no-plugins`, sai com rc=0.

**`--no-scripts` sempre, por enquanto:** os scripts do `composer.json` do PR chamam `$(which php7.4)`, e o
`package:discover` precisa do Laravel de pé. Ligar os scripts no 8.5 é da etapa da inicialização (PHP8-62).

**Revisão:** as tarefas PHP8-60 (`lcobucci/jwt`), PHP8-87 (os 9 pacotes) e a dos documentos mudam a trava com este
comando. O time do banco revisa cada mudança de `composer-85.json`/`.lock`. Ordem dos merges: esta estrutura primeiro,
depois PHP8-60, PHP8-87 e por fim a dos documentos. Cada uma regera a trava sobre a anterior: uma trava não se resolve
por merge de texto.

## `--ignore-platform-req=php+`: os 10 pacotes da trava que excluem o PHP 8.5

`php+` ignora só o teto da versão do PHP; o piso e os `ext-*` continuam conferidos. Saída de
`prohibits php 8.5.12 --locked`, 20/11/2026:

| Pacote (versão na trava) | Exige | Tarefa |
|---|---|---|
| `lcobucci/jwt` 3.4.0 | `^5.6 \|\| ^7.0` | PHP8-60 |
| `bacon/bacon-qr-code` 1.0.3 | `^5.4\|^7.0` | PHP8-87 |
| `dompdf/dompdf` v0.8.6 | `^7.1` | PHP8-87 |
| `ezyang/htmlpurifier` v4.17.0 | `… \|\| ~8.3.0` | PHP8-87 |
| `khanamiryan/qrcode-detector-decoder` 1 | `^5.6\|^7.0` | PHP8-87 |
| `laminas/laminas-escaper` 2.12.0 | `^7.4 \|\| ~8.0.0 \|\| ~8.1.0 \|\| ~8.2.0` | PHP8-87 |
| `mpdf/mpdf` v8.2.4 | `… \|\| ~8.3.0` | PHP8-87 |
| `nette/schema` v1.2.5 | `7.1 - 8.3` | PHP8-87 |
| `nette/utils` v3.2.10 | `>=7.2 <8.4` | PHP8-87 |
| `fzaninotto/faker` v1.9.2 (dev) | `^5.3.3 \|\| ^7.0` | PHP8-87 |

**Atualização (Laravel 13.43, 20/11/2026):** a trava do 8.5 já não tem 8 dos 10; `prohibits php 8.5.12 --locked` lista só `bacon/bacon-qr-code` 1.0.3 e
`khanamiryan/qrcode-detector-decoder` 1, via `endroid/qr-code` 2.5.1 exigido pelo `proner/phppimaco` v1.4.5 (a última). A flag fica; ver
`documentos-74-x-85.md`, seção 8.

Quando essas tarefas tirarem os 10, o `--ignore-platform-req=php+` sai dos comandos acima e o `prohibits` não
lista nada.

## Medidas (20/11/2026)

- **7.4 intacto:** `sha256` antes e depois, iguais aos da `origin/base-php74`.
  ```
  69367bdca80e74f3c799dee85e20d0b6f40a6abbf03c35eef94259af44fc7420  ecidade/composer.json
  38fe5a633ff3ed8169e0d70c0d8301b54812d24ddb3c61ba68cb23adcb02cbf9  ecidade/composer.lock
  ```
  O PSR-4 do 7.4 continua `"App\\": "app/"`, e o classmap otimizado do 7.4 só varre as pastas desse PSR-4. Nenhum
  `.php` do sistema lê `composer*.json` (o único achado, `securimage/securimage.php:68`, é comentário).
- **Trava:** `composer-85.lock` tem o mesmo `sha256` do `composer.lock` (`38fe5a63…`, `content-hash`
  `5ef6154f379714faf53777f1d4c8d0d1`). O `validate` não acusa trava desatualizada: a linha a mais do
  `composer-85.json` é de `autoload`, que não entra no `content-hash`.
- **Instalação:** `install --no-scripts --ignore-platform-req=php+` com rc=0 (medida feita com `--no-plugins`, antes da
  regra dos plugins; sem plugin na trava, o resultado é o mesmo): 165 pacotes (136 + 29 de
  desenvolvimento, os mesmos do 7.4), 3 min 10 s, `runtime-85/vendor` com 264 MB. Os avisos de classe fora do PSR-4
  (`app/` e `tests/`) são os mesmos do 7.4 (código de hoje).
- **Sobreposição:** com uma cópia temporária de `app/Exceptions/Handler.php` em `app-85/Exceptions/Handler.php`
  (apagada depois, fora do commit), o classmap do 8.5 aponta `App\Exceptions\Handler` para `app-85/`, e
  `ReflectionClass` no 8.5 (contêiner `--network none`, código só leitura) devolve `/app/app-85/Exceptions/Handler.php`.
  `App\Http\Kernel`, que não foi sobreposta, continua em `/app/app/Http/Kernel.php`. Sem a pasta, o classmap não cita
  `app-85/`.
- **Carga do `vendor/autoload.php` no 8.5:** 12 `Deprecated` de parâmetro nulo implícito, nos arquivos de funções
  carregados pelo autoload: `guzzlehttp/promises` (6), `lcobucci/jwt` (3), `opis/closure` (1) e `laravel/framework`
  `helpers.php` (2). São pacotes das tarefas seguintes; aqui só se registra.

## Lint do grupo (CI) e a pergunta ao coordenador

O CI do grupo (`.github/workflows/testes-ci-lint.yml` da branch `testes-ci/lint-incremental-pedromax`) roda
`php -n -d short_open_tag=1 -l` no 7.4 e no 8.5 em **todo `.php` adicionado ou alterado** no PR, sem exceção de
caminho. `composer-85.json`/`.lock`, `docker/composer-85/` e este registro não são `.php`. O `runtime-85/` não é
versionado. O que o CI vai alcançar é a sobreposição `ecidade/app-85/`.

Regra adotada até a resposta: **classe em `app-85/` tem sintaxe válida no 7.4.** Ela pode chamar API só do 8.5/Laravel
13, porque o lint não executa, mas não pode usar sintaxe só do PHP 8 (tipos `mixed`/união/`static` de retorno,
`match`, argumentos nomeados, `readonly`, `enum`, promoção no construtor, atributos `#[...]` fora de comentário).

**Pergunta ao coordenador (levar pelo cliente):** quando uma classe sobreposta precisar implementar uma assinatura do
Laravel 13 que exige sintaxe só do PHP 8 (por exemplo, retorno `mixed` numa interface do framework), o job do 7.4 do
lint pode pular `ecidade/app-85/`? O 7.4 nunca carrega essa pasta. Ou o grupo prefere outro caminho (por exemplo, a
sobreposição fora de `ecidade/`, montada só no contêiner do 8.5)? Até a resposta vale a regra acima, e uma classe que
não couber nela fica registrada como pendente.

## Trecho isolado em Docker que falha alto (`roda-isolado.sh`)

`bash docker/composer-85/roda-isolado.sh <7.4|8.5> <trecho.php> [args]` roda um trecho PHP sem rede e sem banco
(`--network none`). **Imagens do projeto**, não as `php:*-cli` oficiais (essas só servem para `php -l`): `ecidade-php74-apache`
(construída de `docker/php74-apache`) e `ecidade-php85-apache` (de `docker/php85-apache`), com as extensões e o `php.ini`
delas. Se a tag local não existir o script constrói (uma vez, precisa de rede); `IMAGEM=<tag>` troca a imagem.

- **Código e vendor:** `ecidade/` em `/app` somente leitura. Vendor: 7.4 = `ecidade/vendor`; 8.5 = `runtime-85/vendor`;
  `VENDOR=<pasta>` monta outro em `/app/vendor` (por exemplo o `composer install` do `ecidade/composer.lock` do PR, quando
  `ecidade/vendor` está desatualizado). Vendor sem `autoload.php` gera aviso nos dois.
- **Gravável só em memória (tmpfs):** `/app/bootstrap/cache`, `/app/storage/logs`, `/app/storage/framework` e `/tmp`. Sem
  isso o kernel do Laravel não sobe (`bootstrap/cache must be present and writable`). Os pontos de montagem são criados vazios,
  como o usuário, se não existirem.
- **Ambiente de teste só no contêiner:** `--env-file` gerado de `ecidade/.env.example` (`APP_ENV=local`, `APP_KEY` de teste,
  `DB_HOST=banco.invalido`). **Nenhum `ecidade/.env` é criado na árvore** e um que já exista não é alterado (as variáveis
  do contêiner prevalecem sobre o arquivo).

**Por que existe:** o `docker run` que monta o código e o vendor falha num checkout novo (`mountpoint ... read-only`; pasta
inexistente vira diretório de `root`), e um script que compara a saída vazia de um lado com a vazia do outro dá "igual"
falso. Apareceu em 4 tarefas. O script **sai com erro** quando:

| Situação | rc |
|---|---|
| argumento inválido, trecho inexistente | 64 |
| imagem ausente (com `IMAGEM=`) ou build falhou | 65 |
| saída do trecho vazia | 66 |
| `docker run` ou o trecho falhar | o próprio rc (nunca 0) |

**`APP_KEY` de teste:** o Laravel exige uma chave de 32 bytes em base64 (`AES-256-CBC`) para subir o kernel e usar o criptografador.
O script gera uma a cada execução (`base64:` + 32 bytes de `/dev/urandom`), só no `--env-file` temporário do contêiner, que é
apagado ao fim: **nunca a chave real**, e o script não lê o `ecidade/.env` de ninguém. Pré-requisito: o trecho que cifra ou
decifra algo só compara com outra execução se a chave for fixa; para isso `ENV_EXTRA` com `APP_KEY=base64:<32 bytes>`
(a última linha vale) fixa uma chave fictícia.

**Opções (variáveis de ambiente; nada de segredo, só valores fictícios):**

| Variável | Efeito |
|---|---|
| `ENV_EXTRA=<arquivo K=V>` | linhas acrescentadas ao `--env-file`, depois das do `.env.example` (ex.: `API_DATA_AVAILABLE_URL=http://api.invalid/`; sem aspas) |
| `EXTRA_RO=<host>:<contêiner>[,...]` | montagens extras **somente leitura** (o caminho do host precisa existir, senão rc 64) |
| `STDIN=1` | repassa o stdin do chamador ao trecho (`docker run -i`): `echo x \| STDIN=1 roda-isolado.sh 7.4 trecho.php`. **Sem `STDIN=1` o trecho recebe `/dev/null` e o stdin do chamador não é consumido**: com `-i` sempre, um `while read` que chama o script rodava 1 vez em vez de 3 |
| avisos | por padrão `php -d display_errors=stderr -d error_reporting=E_ALL -d log_errors=0`: aviso, notice e deprecated saem no **stderr**, nunca no stdout; `AVISOS=0` desliga e vale o `php.ini` da imagem (`display_errors=Off`, `error_log` dentro do contêiner). O `php.ini` da imagem não muda |
| `STDERR_ARQ=<arquivo>` | grava o stderr do trecho nesse arquivo, separado do stderr do script (as mensagens `roda-isolado: ERRO` continuam no stderr do script) |

Com isso os avisos 7.4 × 8.5 se comparam à parte: o mesmo `echo $variavel_inexistente` dá `Notice: Undefined variable` no 7.4 e
`Warning: Undefined variable` no 8.5, que o `display_errors=Off` das imagens escondia.

A saída e o `stderr` do trecho passam para quem chamou. Teste em clone limpo
(`bash docker/composer-85/testa-roda-isolado.sh`; precisa dos vendors em `TESTA_VENDOR74` e `TESTA_VENDOR85`, padrão
`runtime-85/referencia-74/vendor` e `runtime-85/vendor`): 22 casos, 22/22 (os 10 do começo, 7 das opções, a `APP_KEY` e o `while read` de 3 linhas nos dois runtimes + `STDIN=1`: `ENV_EXTRA`, stdin, `EXTRA_RO` somente leitura, aviso só no `STDERR_ARQ`, Notice × Warning, `AVISOS=0`, `EXTRA_RO`/`ENV_EXTRA` inválidos). O 7.4 e o 8.5 imprimem a versão; um trecho sobe o
kernel do Laravel do PR nos dois (`App\Application env=local`, rc 0, nenhum `Deprecated` no stdout); `exit(3)`, trecho vazio,
imagem ausente, `docker run` quebrado, versão e arquivo inválidos falham com `roda-isolado: ERRO`. **Aviso:** tarefa que roda
trecho isolado passa a chamar este script em vez de montar o `docker run` à mão.

## Lacunas

- O contêiner do 8.5 com `runtime-85/vendor` montado ainda não existe: é da inicialização (PHP8-62). O 8.5 de hoje
  (`docker-compose.php85.yml`) continua com o `vendor/` do 7.4.
- Nada do Laravel foi exercitado no 8.5: só a carga do `vendor/autoload.php` e o autoload de uma classe.
- `runtime-85/` não é versionado: quem for usar roda o `install` acima (3 min).
