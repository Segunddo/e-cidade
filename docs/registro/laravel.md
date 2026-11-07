# Laravel: bloqueador do login, dimensionamento e medições

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

### BLOQUEADOR DO LOGIN: Laravel 5.4 não roda em PHP 8

Descoberto ao tentar autenticar no ambiente 8.5. O login **não é** código legado do e-cidade —
ele passa pelo stack do Laravel:

```
login.php  → POST /v4/oauth/token   (Laravel Passport)
           → window.open('abrir.php?sAuth=base64(DB_login=..&DB_senha=md5(..))')
```

No PHP 8.5 esse endpoint devolve **HTTP 500 com corpo vazio**. Os fatais estão todos dentro
de `vendor/`, não no código da prefeitura:

```
ReflectionParameter::getClass() is deprecated since 8.0
   -> vendor/laravel/framework/.../Illuminate/Container/
Zend\Stdlib\PriorityQueue::count() return type ...
   -> vendor/zendframework/zend-stdlib/
```

Detalhe do mecanismo: `config/application.php:27` já exclui `E_DEPRECATED`, mas as rotas
`/v4/*` rodam pelo **handler do Laravel**, que converte qualquer erro — deprecations
inclusive — em `ErrorException` fatal. Por isso uma simples deprecation derruba a requisição.

**Consequência para o projeto:** não existe "logar no :8085" enquanto o Laravel não subir a
escada de versões (Fase 1/2). Isso **valida a arquitetura strangler fig** em vez de contradizê-la:
autenticação e rotas `/v4/*` permanecem no runtime 5.6, os módulos migrados vão para o 8.5, e os
dois compartilham sessão. O proxy reverso deixa de ser desenho e passa a ser requisito.

### DIMENSIONAMENTO DO LARAVEL — o problema é menor do que parece

Medido, e desfaz duas impressões erradas:

| | |
|---|---|
| `app/` (código Laravel de verdade) | 1.259 arquivos, **771 usam Laravel (61%)** |
| `src/` (framework V3 **próprio** deles) | 2.651 arquivos, **apenas 44 usam Laravel (1%)** |
| Rotas servidas pelo Laravel | **138** (60 web + 78 api) |
| Núcleo legado que toca Laravel | **1 arquivo**: `libs/db_conecta.php:83` |

**Achado central: `illuminate/database` (o Capsule do Eloquent) JÁ FUNCIONA em PHP 8.5.**
Verificado conectando e consultando pelo runtime 8.5:

```bash
docker exec ecidade_php85 php -r '
require "/var/www/html/vendor/autoload.php";
$c = new Illuminate\Database\Capsule\Manager;
$c->addConnection(["driver"=>"pgsql","host"=>"ecidade_database","port"=>5432,
  "database"=>"ecidade","username"=>"postgres","password"=>"postgres"]);
$c->setAsGlobal(); $c->bootEloquent();
print_r($c->getConnection()->select("select count(*) from configuracoes.db_modulos"));'
```

Isso separa o "migrar o Laravel" em **dois problemas independentes**:

1. **Eloquent/Capsule** — usado pelo núcleo legado (`db_conecta.php`). **Já funciona no 8.5**,
   não bloqueia nada. É por isso que os módulos migrados funcionam.
2. **O stack HTTP do Laravel** — serve só as 138 rotas `/v4/*` e o login. É o único que falha
   em PHP 8 (`ReflectionParameter::getClass()`, `PriorityQueue::count()`).

**Consequência estratégica: o Laravel não bloqueia a migração dos módulos.** Ele só bloqueia
"desligar o container 5.6", que é o último passo de todos. Por isso está corretamente nas
Fases 1/2, depois dos módulos — e não antes.

Dois caminhos possíveis quando chegar a hora:

- **Escada de versões** 5.4→5.5→…→12: ~8 saltos, cada um com guia oficial de upgrade. Caminho
  "correto", mas cada degrau é um projeto, e arrasta a substituição de `silex`, `doctrine/dbal 2`,
  `symfony ~3.2`, `zend-eventmanager`, `passport 4`, `lcobucci/jwt 3.3.3` e `fractal 0.11`.
- **Reescrever a camada HTTP**: são 138 rotas e 771 arquivos sobre um Laravel novo. Como o
  legado **não depende** do stack HTTP (só do Eloquent, que já funciona), pode sair mais barato
  que oito degraus de upgrade. Exige decisão de escopo, não é trabalho de disciplina.

Pendência para demonstrar o piloto no navegador: **sessão compartilhada entre os dois runtimes**
(hoje 5.6 grava em `/var/lib/php/sessions` e 8.5 em `/tmp`, isolados). O cookie não é obstáculo —
cookies de `localhost` são compartilhados entre portas.

### ✅ MEDIÇÃO (14/10/2026): o Laravel pode migrar em PARALELO — com `vendor/` separado

**A dependência:** nenhuma versão do Laravel roda no 5.6 **e** no 8.5 (5.4 é a última do 5.6 e
não roda no 8; a 12 exige 8.2–8.5, a 13 exige 8.3–8.5). Como os dois containers montam o mesmo
`vendor/`, atualizar o Laravel ali derruba o 5.6. **A saída é um `vendor/` próprio do 8.5**, montado
por cima de `/var/www/html/vendor` só no lado 8.5 — o 5.6 não é tocado.

Montagem da medição (nada na árvore versionada mudou além de `cmp.py`):
`ecidade/tmp/lar12/` (gitignored) com `composer.json` = o atual com `laravel/framework ^12.0` e o
resto `*`; 4º container `ecidade_lar12` na porta **8087**, mesma imagem do 8.5, com o vendor novo,
`bootstrap/cache` e `storage/` também sobrepostos (o Laravel 12 escreveria cache no formato dele e
quebraria os runtimes 5.4).

| Medição | Resultado |
|---|---|
| Pacotes que **não resolvem** com Laravel 12 | **4**: `silex/silex`, `proner/phppimaco` (mpdf 7, PHP ≤ 7.3), `dbseller/phinx_postgres` (phinx 0.10 / symfony antigo), `dbseller/sdk-api-pix-bb` (guzzle 6, ou 7.5.0 com alertas de segurança) |
| Resolvidos | 135 pacotes; Laravel 12.70, Passport 13.10, symfony 7/8, guzzle 7, phpspreadsheet 5, dompdf 3, mpdf 8 |
| **Legado sobre o vendor novo** | **3.294 telas** (Fase A + Educação): **3.271 idênticas ao 5.6**; as 15 divergentes + 8 timeouts são **exatamente** as 23 da linha de base. **Zero regressão.** |
| Classes de `app/`+`src/` que deixam de carregar | **29 de 3.910** (21 `src/Console`: `execute()` sem `: int` do symfony 7; 8 `app/`: `Handler::report(Exception)`, `BaseDeferredProvider::register()`, traits de Auth removidas, Pimaco) |
| Boot do Laravel 12 | **não inicializa** — morre no 1º provider (`BaseDeferredProvider`); `/v4/oauth/token` dá 500 |
| APIs removidas (estático) | 50 `DB::raw` em `app/` (10.0), 10 helpers `str_*`/`array_*` (6.0), 5 `$dates` (10.0), 1 `Passport::routes()` (11.0), 105 usos de PhpOffice (1.8 → 5) |
| Uso do Silex | só a API REST `api/V1` (20 arquivos); o `use Silex\Application` do `app.php` é import sem uso |

**⚠ O Passport 13 NÃO convive com o 5.6 no banco compartilhado:** a migração dele apaga
`user_id`, `redirect`, `personal_access_client`, `password_client` de `oauth_clients` (usados
pelo Passport 4) e passa a exigir segredo com hash. **Usar Passport 12.4** — aceita Laravel 12 e
só acrescenta colunas opcionais (`secret` nullable, `provider`), o que o Passport 4 tolera. O
password grant (o login usa) vem desligado no 12: `Passport::enablePasswordGrant()`.

**Conclusão:** o legado não depende do Laravel novo nem é afetado por ele — 3.294 telas iguais.
O custo está todo na camada HTTP (`app/` + `api/V1`), que hoje nem inicializa. A ordem certa é
trocar o vendor do 8.5 **cedo** (cada área migrada depois disso não precisa ser reverificada) e
portar `app/` em paralelo, com o login e o `/v4/*` ficando no 5.6 até o boot funcionar.

**Três falhas do instrumento nesta medição**, mesma família de sempre: o laço de eliminação do
Composer tratava erro de clone SSH como "resolveu" (corrigido: sucesso = existir `composer.lock`);
o `xargs` aborta a lista inteira quando um `php` sai com 255 (fatal) — 574 de 3.910 testados até
o invólucro `exit 0`; e o `cmp.py` não normalizava `localhost:8087`, gerando 129 falsos positivos.

Remover: `docker rm -f ecidade_lar12` e `rm -rf ecidade/tmp/lar12`.

### 📐 LARAVEL SÓ PARA O TRIBUTÁRIO (16/10/2026) — o que a área usa, medido

| | |
|---|---|
| Rotas de API do domínio | **74**, em 4 módulos: ISSQN 27, Arrecadação 25, ITBI 14, Cadastro 8 (os outros 12 arquivos de rota estão vazios; `routes/web/tributario/*` também) |
| Código Laravel do domínio | `app/Domain/Tributario`: **220 arquivos** (Arrecadação 71, ITBI 64, ISSQN 50, Cadastro 35) + `app/Domain/Core` 12 |
| **Telas legadas que chamam a API por JavaScript** | **14**: TEF (`arr2_operacoespendentestef00*`, `cai3_gerfinanc075`), PIX (`cai3_gerfinanc001`, `cai1_pix002`), parcelamentos vencidos (`arr4_*parc_venc`), alvará por eventos e ordem de serviço (`iss4_*`), Redesim (`iss179_inscricaoredesim`), veículos do ISSQN (2 `forms/`), tipo de débito (`forms/db_frmarretipo002`), parâmetros do número cadastral (`cad4_*`) |
| Telas legadas que usam classes de `app/` | 18 (precisam continuar compatíveis com as duas versões do Laravel) |
| Rotas do ITBI | middleware `clientCredential` = **aplicação externa** (ITBI online); nenhuma tela legada as chama |
| API Silex `api/V1` | 1 rota do Tributário (`TributarioControllerProvider`: `post recibo`) |
| Pacote travado que o Tributário usa | **`dbseller/sdk-api-pix-bb`** — `app/Domain/Tributario/Arrecadacao/Pix/Bancos/BancoDoBrasil.php` (`Swagger\Client`) |

**Ponto cego que isto revela, válido JÁ:** as 14 telas são servidas pelo 8.5, mas o AJAX delas
vai a `/v4/api/tributario/*`, que o proxy manda ao **5.6**. A bateria (`curl`, sem JS) nunca
exercitou essas chamadas. E sem o proxy, abertas no `:8085`, a chamada iria ao Laravel 5.4 sob
PHP 8.5 e falharia.

**Pontos a verificar antes de estimar:** (1) ~~se o Passport 12 do 8.5 aceita o token emitido
pelo Passport 4 do 5.6~~ **TESTADO (16/10/2026): aceita** — ver abaixo; (2) PIX e TEF chamam serviços reais de terceiros (banco, adquirente)
— testes automáticos não podem contatá-los, exigem sandbox ou dublê.

#### ✅ TESTE: o token do Passport 4 (5.6) vale no Passport novo (8.5)

Token **real**, pedido a `POST :8080/v4/oauth/token` com o cliente `9999999` e o usuário
`dbseller` (HTTP 200; JWT RS256, `aud`=9999999, `sub`=1). Conferido com `ResourceServer` do
`league/oauth2-server` — a classe que o Passport usa para validar o *bearer* —, com a chave
`storage/oauth-public.key` e a revogação lida de `oauth_access_tokens` no banco compartilhado:

| `league/oauth2-server` | token real | controle: `sub` adulterado | controle: revogado |
|---|---|---|---|
| **8.5.5** (o do Passport 12.4) + `lcobucci/jwt` 5.6.1 | **ACEITO** (usuário 1, cliente 9999999) | RECUSADO | RECUSADO |
| **9.4.1** (o do Passport 13) | **ACEITO** | RECUSADO | RECUSADO |

5.6 usa `league/oauth2-server` 6.1.1 + `lcobucci/jwt` 3.3.3. **Consequência: o login pode ficar
no 5.6 e as rotas `/v4/api/tributario/*` irem para o 8.5** — o login vira a última peça.

**O que o teste NÃO cobre:** a camada do Passport acima do `ResourceServer` (o `TokenGuard`
carrega o cliente de `oauth_clients` e o usuário pelo *provider* de autenticação), que só roda
com o Laravel 12 inicializando. As colunas de `oauth_access_tokens` são as mesmas nas duas
versões; `oauth_clients` muda no 13, por isso a escolha do 12.4 continua valendo.

**Armadilha do instrumento:** a primeira execução deu `Invalid key supplied` nas duas versões —
o container `ecidade_lar12` sobrepõe `storage/` com uma pasta vazia, e a chave não estava lá.
Era o teste, não a compatibilidade. Verificador versionado: `scratchpad/valida_token.php <vendor/autoload.php> <token> <oauth-public.key>`.
