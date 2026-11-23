# Regressão da migração (base PHP 7.4/Laravel 8 → PHP 8.5 e Laravel 13)

> **Primeira vez aqui?** Leia [`COMO-USAR.md`](COMO-USAR.md) (o que é, o que prova, rodar em 3 comandos, como ler o
> relatório). Este arquivo é a referência técnica. Atalhos: `regressao/bin/regressao` (`ambiente-sobe`,
> `ambiente-para`, `rodada-pequena`, `rodada-completa`, `comparar ANTES DEPOIS`, `ver-ultimo`).

Baterias que dizem, com evidência, se o e-Cidade migrado **se comporta como o de referência**. Tudo roda
da raiz do repositório, dentro do WSL/Linux, contra o ambiente Docker **isolado** `e74`
(`regressao/lab/docker-compose.e74.yml`). O alvo do grupo é PHP 8.5 com **Laravel 13 + Passport 13** (guia do grupo,
`.mcp/docs/regras-do-grupo.md`); o laboratório Laravel (`ecidade74_lar12`, nome histórico) existe enquanto ele não.

| Bateria | Pergunta que responde | Como compara |
|---|---|---|
| **PHP** (`regressao/php`) | PHP 8.5 (:8185) responde como a referência PHP 7.4 (:8074)? | roda a mesma coisa nos dois runtimes sobre o mesmo banco: lint, classes, telas (GET), POSTs reais, relatórios (PDF/CSV/HTML por conteúdo), hashes e cobertura |
| **Laravel** (`regressao/laravel`) | o Laravel novo responde como o Laravel 8 de referência? | *golden master*: grava as respostas da referência em `regressao/baseline/laravel/` e compara o alvo novo contra elas (rotas `/v4`, `rest/v1`, Silex, token Passport, escritas com SQL de negócio) |
| **Fluxos de navegador** (`regressao/completa/fluxos.py`) | o usuário, no navegador, vê o mesmo? | Playwright pelo proxy `:8190`: login → módulo → telas → inclusão → relatório → sair; golden master em `regressao/baseline/fluxos/` |
| **Completa** (`regressao/completa/orquestra.py`) | tudo junto, e antes × depois | roda as três, agrega num relatório só e compara duas rodadas completas |

> **Base 7.4.** A suíte veio da branch `regressao`, onde o gabarito era PHP 5.6/Laravel 5.4 (:8080/:8085/:8090).
> Nesta branch o gabarito é a **base PHP 7.4/Laravel 8** e os padrões são os do ambiente `e74` (tabela abaixo). A
> **bateria PHP já está adaptada** (referência 7.4 × 8.5; containers e portas só em `regressao/nucleo/ambiente.py`,
> inclusive para `scratchpad/cmp.py` e `scratchpad/escrita_post.py`; catálogos reverificados ao vivo em 2026-11-18).
> A **bateria Laravel também está adaptada** (2026-11-18): inventário pelo `route:list --json` do Laravel 8, baseline
> `regressao/baseline/laravel/` **regravada contra a referência :8074** e laboratório `ecidade74_lar12` (:8187); detalhes
> na seção 9 ("Laravel"). Os **fluxos** de navegador passam pelo **Desktop** do PR (login → MENU → área → módulo →
> janela da tela) e a **completa** traz os avisos da base 7.4 (2026-11-18). O banco de partida é o **dump v2** (seção 2):
> com o de instalação o menu do Desktop não monta.

### Versões medidas (ambiente `e74`, 2026-11-17)

| Papel | Container | URL / porta | Versões |
|---|---|---|---|
| **Referência** (gabarito) | `ecidade74_php74` | http://localhost:8074 | PHP 7.4.33 (Ubuntu 22.04, ppa ondrej, Apache 2.4.52), Laravel 8.73.2, Passport 10.4.2, league/oauth2-server 8.3.2, PHPUnit 8.5.39 |
| **Alvo PHP** | `ecidade74_php85` | http://localhost:8185 | PHP 8.5.12 (imagem `php:8.5-apache`, mesmo Dockerfile da branch antiga), `regressao/lab/php85/paridade-74.ini` |
| **Alvo Laravel** (laboratório) | `ecidade74_lar12` | http://localhost:8187 | mesmo runtime do PHP 8.5 acima sobre `LAR12_CODIGO` (padrão `./ecidade`, Laravel 8): ainda não existe o Laravel 13 do e-Cidade, alvo do grupo (`regressao/lab/README.md`) |
| **Proxy** (uma origem) | `ecidade74_proxy` | http://localhost:8190 | nginx 1.27; hoje manda **tudo** para a referência (`regressao/lab/proxy/map-e74.conf` vazio) |
| **Banco** | `ecidade74_database` | sem porta publicada | PostgreSQL 16.16 (`docker/database`), LATIN1/pt_BR, dump `ecidade/docker/ecidade_base.sql.gz` |

Variáveis (lidas a cada chamada, em `regressao/nucleo/ambiente.py`): `REGRESSAO_REF_URL`, `REGRESSAO_PHP_NOVO_URL`
(apelido: `REGRESSAO_NOVO_URL`), `REGRESSAO_LARAVEL_NOVO_URL`, `REGRESSAO_PROXY_URL`, e os containers
`REGRESSAO_CONTAINER_REF`, `REGRESSAO_CONTAINER_PHP_NOVO`, `REGRESSAO_CONTAINER_BANCO`, `REGRESSAO_CONTAINER_PROXY`,
`REGRESSAO_CONTAINER_LARAVEL_NOVO` (padrão `ecidade74_lar12`).

**Trava do banco:** toda bateria recria o banco (`DROP DATABASE ecidade` + `pg_restore`, `regressao/nucleo/banco.py`).
Ela só faz isso em contêiner do ambiente da regressão: nome com prefixo `ecidade74_` ou label do projeto compose `e74`.
Com `REGRESSAO_CONTAINER_BANCO` apontando para outro contêiner, a restauração é recusada (ERRO_AMBIENTE) a não ser que
`REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74=sim` esteja exportada, o que **apaga** o banco desse contêiner.

## 1. Pré-requisitos

- Docker com Compose v2 e WSL Ubuntu (ou Linux). O ambiente é o projeto Compose **`e74`**, com rede (`e74_ecidade74`),
  volumes (`e74_sessions`, `e74_tmp`), nomes (`ecidade74_*`) e portas próprios: ele **não** para nem reusa os
  containers da pilha antiga (`ecidade_*`) nem de outros projetos do host (o :8080 pode estar ocupado por outro
  serviço; por isso a referência fica em :8074).

  ```bash
  # imagens: banco e PHP 7.4 a partir dos Dockerfiles da base (docker/), PHP 8.5 de regressao/lab/php85.
  # Para reaproveitar a imagem PHP 8.5 da branch antiga sem rebuild: docker tag e-cidade-ecidade_php85 ecidade74-php85:latest
  docker compose -p e74 -f regressao/lab/docker-compose.e74.yml build
  docker compose -p e74 -f regressao/lab/docker-compose.e74.yml up -d ecidade74_database ecidade74_php74
  ```

- **Banco** (o que o `ecidade/docker/install.sh` faz na seção "Criando Banco de Dados", ≈ 6 min, ~1 GB), direto no
  container do banco e sem descompactar o `.sql.gz` no disco:

  ```bash
  cd ecidade
  docker exec -i ecidade74_database psql -U postgres -v ON_ERROR_STOP=1 < docker/init.sql      # roles ecidade, plugin, dbseller + banco
  zcat docker/ecidade_base.sql.gz | sed -e 's/^SET default_with_oids = true;$/SET default_with_oids = false;/' \
      -e '/^GRANT SELECT ON TABLE pg_catalog.pg_pltemplate TO plugin;$/d' \
      -e '/^CREATE AGGREGATE public.array_accum(anyelement)/,/^);$/ { s/anyelement/anycompatible/g; s/anyarray/anycompatiblearray/g; }' \
      -e 's/^ALTER AGGREGATE public.array_accum(anyelement)/ALTER AGGREGATE public.array_accum(anycompatible)/' \
    | docker exec -i ecidade74_database psql -q -v ON_ERROR_STOP=1 -U postgres ecidade
  docker exec -i ecidade74_database psql -U postgres -v ON_ERROR_STOP=1 ecidade < docker/pos.sql
  cd ..
  ```

  O dump da base 7.4 já traz a senha do `dbseller` como **`sha1(md5("dbseller"))`** (o que o login web confere) e os
  clientes OAuth (inclusive o `9999999` usado pela bateria Laravel). Por isso **não** rode `php artisan passport:install`:
  ele falha (chave duplicada em `oauth_clients`) e não acrescenta nada. Conferir a senha sem imprimir o hash:

  ```bash
  H=$(printf dbseller | md5sum | cut -d' ' -f1 | tr -d '\n' | sha1sum | cut -d' ' -f1)
  docker exec ecidade74_database psql -U postgres -d ecidade -Atc "select senha = '$H' from configuracoes.db_usuarios where login = 'dbseller'"   # t
  ```

- **Arquivos locais do app** (todos **ignorados pelo git**; sem eles o login dá 404/500). Grave-os como o seu usuário
  (não como root) e com `LC_ALL=C`: no locale UTF-8 o `.*` do `sed` para no primeiro byte LATIN1 do `db_conn.php.dist`
  e deixa lixo depois do `;` (erro de sintaxe no PHP). É o que o `install.sh` faz dentro do container:

  ```bash
  cd ecidade
  export LC_ALL=C
  cp -a .env.example .env
  sed -i 's/DB_HOST=.*/DB_HOST=ecidade74_database/; s/DB_DATABASE=.*/DB_DATABASE=ecidade/; s/DB_PORT=.*/DB_PORT=5432/; s/DB_USERNAME=.*/DB_USERNAME=postgres/; s/DB_PASSWORD=.*/DB_PASSWORD=postgres/' .env
  cp -a libs/db_conn.php.dist libs/db_conn.php
  sed -i 's/\$DB_BASE.*/$DB_BASE = "ecidade";/; s/\$DB_SERVIDOR.*/$DB_SERVIDOR = "ecidade74_database";/; s/\$DB_PORTA.*/$DB_PORTA = "5432";/; s/\$DB_USUARIO.*/$DB_USUARIO = "postgres";/; s/\$DB_SENHA.*/$DB_SENHA = "postgres";/; s/DB_VALIDA_REQUISITOS.*/DB_VALIDA_REQUISITOS = false;/' libs/db_conn.php
  cp config/require_extensions.xml.dist config/require_extensions.xml
  cp libs/db_acessa.php.dist            libs/db_acessa.php
  mkdir -p extension/log && chmod 777 extension/log
  touch extension/log/error.log extension/log/application.log && chmod 666 extension/log/*.log
  cd ..
  # dependencias e chaves (uid 1000 = seu usuario no WSL; nada de root na worktree)
  E="docker exec -u 1000:1000 -e HOME=/tmp/e74-composer -e COMPOSER_HOME=/tmp/e74-composer -w /var/www/html ecidade74_php74"
  $E composer install --no-interaction
  $E composer configure-desktop                 # copia os demais *.dist (plugins.json, application.php, ecidade_config.php)
  docker exec -u root -w /var/www/html ecidade74_php74 sh -c 'chgrp -R www-data storage bootstrap/cache tmp && chmod -R g+rwX storage bootstrap/cache tmp && find storage bootstrap/cache tmp -type d -exec chmod g+s {} +'
  $E php artisan key:generate --force
  $E php artisan passport:keys --force
  docker exec -u root -w /var/www/html ecidade74_php74 sh -c 'chgrp www-data storage/oauth-*.key && chmod 640 storage/oauth-*.key'
  ```

  (`php artisan cache:clear` diz "Failed to clear cache" com o cache vazio: inofensivo.) Só então gere o dump da seção 2.

- Python 3.12 e o venv do projeto (não versionado):

  ```bash
  python3 -m venv regressao/.venv
  regressao/.venv/bin/pip install -r regressao/requirements.txt
  regressao/.venv/bin/python -m pytest regressao/tests -q                # unitarios, sem Docker
  regressao/.venv/bin/python -m playwright install chromium          # ~700 MB em ~/.cache/ms-playwright
  wsl -u root -- /caminho/e-cidade/regressao/.venv/bin/python -m playwright install-deps chromium   # bibliotecas do sistema (apt), se faltarem
  ```

- Depois do dump, suba o resto e confira: `docker compose -p e74 -f regressao/lab/docker-compose.e74.yml up -d`;
  `curl -sI http://localhost:8190/login.php | grep -i x-ecidade` deve dizer `PHP-7.4 (referencia)`.
- O PHP 8.5 lê `regressao/lab/php85/paridade-74.ini` (bind mount): as diretivas do php.ini da referência 7.4 que mudam
  saída (output_buffering, default_charset, error_reporting, memory_limit, max_execution_time, variables_order,
  expose_php, zend.assertions, GC de sessão...). O motivo de cada uma está no próprio arquivo.
- Parar só este ambiente: `docker compose -p e74 -f regressao/lab/docker-compose.e74.yml stop`.

## 2. A baseline do banco (o dump)

Todas as baterias começam **restaurando** `regressao/baseline/baseline.dump` (sha256 em
`baseline.dump.sha256`, conferido a cada rodada). Isso dá o mesmo estado inicial sempre e apaga qualquer resíduo
de rodada anterior (um POST abortado deixa lixo no banco). Para (re)criar, com o ambiente recém-instalado e **antes de
qualquer teste ao vivo** (um simples GET já grava auditoria/sessão no banco):

```bash
regressao/.venv/bin/python -c "from regressao.nucleo.banco import ARQ_DUMP, gera_dump; print(gera_dump(ARQ_DUMP))"
```

Trocar o dump invalida as baselines do Laravel e dos fluxos (elas guardam o sha256 e as baterias recusam rodar
com outro): regrave-as (seção 6). Restaurar leva **≈ 3–5 min** (`DROP DATABASE` + `pg_restore --create`).

**Guarde uma cópia do `baseline.dump` fora do git** (disco/backup do time). `pg_dump -Fc` **não reproduz o mesmo
sha256** ao ser rodado de novo (metadados e ordem mudam): se o arquivo se perder, um dump novo é outra baseline e
obriga a regravar Laravel e fluxos.

**Restaurar num container de banco NOVO** exige o que o dump não leva: as *roles* são globais ao cluster. As roles do
ambiente `e74` (`\du`) são `dbseller` (sem atributos), `ecidade` e `plugin` (superusuários) e `postgres`; crie-as antes
do `pg_restore` com `ecidade/docker/init.sql` **sem** a linha `CREATE DATABASE` (o `pg_restore --create` cria o banco).

**Dump v2 (atual, 2026-11-18): instalação + migrations Laravel do PR.** sha256 `97251574…0fad`, cópia fora do git em
`<seu-diretorio>/ecidade74-baseline-v2.dump`. Motivo: com o dump de instalação (v1) o Desktop do PR **não monta o menu
de módulos** (`Menu/getItensMenu` → 500: faltam `itens_menu_usuario_favoritos`, `notifications` e `db_itensmenu.api`),
como o guia do grupo previa. Aplicada a decisão 1(a) do guia: banco descartável (o `ecidade74_database`) restaurado do
v1, as 736 migrations pendentes rodadas **uma a uma** (`migrate --path`, a que falha fica pendente: **712 aplicadas,
24 falharam**, todas defeitos do PR com o banco de instalação, p.ex. `\'` em SQL com `standard_conforming_strings=on`),
dump gerado logo depois, runtimes parados (sem HTTP). Procedimento, lista das 24 e efeito (funções `fc_issqn`/IPTU
ficam na versão do dump) em [`baseline/banco-referencia-v2.md`](baseline/banco-referencia-v2.md). As linhas de base
Laravel e de fluxos foram **regravadas** sobre o v2 na referência, e os catálogos PHP reconferidos.

**Dump v1 (histórico, 2026-11-17)**: gerado com os runtimes **parados** (o healthcheck do `ecidade74_php74` faz `GET /` a
cada 5 s), logo depois da carga do `ecidade_base.sql.gz`, sem nenhum acesso HTTP antes. sha256 `15cd994a…444d`, cópia
em `<seu-diretorio>/ecidade74-baseline.dump`. É o ponto de partida do v2. O `search_path` real é
configurado **por banco** (`ALTER DATABASE ecidade SET search_path = "$user", public, teleatend, acordos, …` com ~70
schemas) e vem no dump porque ele é gerado com `--create`; não há `ALTER ROLE … SET`. Confira com
`psql -c '\du'` e `select * from pg_db_role_setting`.

## 3. Rodar

Sempre da raiz do repositório, com `regressao/.venv/bin/python -m …`. Cada comando escreve uma pasta de saída com
`resultado.json`, `resumo.md` e `diffs/`.

```bash
# PHP: referencia 7.4 x 8.5. Rodada completa de telas leva HORAS (~0,83 s/tela; a rodada real da base 7.4 teve 13.036 telas e o PHP levou 5 h 05): para fumaça use --area/--prefixo
python -m regressao.php.bateria --saida /tmp/php --prefixo '^arr1_(procjurtipo|grupotaxa)001\.php$'
python -m regressao.php.bateria --saida /tmp/php --area tributario            # uma área (≈ 5,5 mil telas)
# opções: --sem-normalizar, --incluir-nao-verificados, --sem-restaurar (só desenvolvimento: rodada NÃO comparável)

# Laravel (a baseline é gravada na referência Laravel 8 e comparada com o alvo novo)
python -m regressao.laravel.rotas                                              # inventário (route:list --json na referência)
python -m regressao.laravel.gerador                                            # casos/rotas_*.yml a partir do inventário
python -m regressao.laravel.bateria gravar   --saida /tmp/lar-g                # no :8074 (referência); recusa sobrescrever (seção 6)
python -m regressao.laravel.bateria gravar   --saida /tmp/lar-g --alvo http://localhost:8074 --confirmo-sobrescrever   # regravar
python -m regressao.laravel.bateria gravar   --saida /tmp/lar-g --apenas-novos --confirmo-sobrescrever   # só casos novos (11b)
python -m regressao.laravel.cobertura                                          # baseline/laravel/_cobertura.{json,md}
python -m regressao.laravel.bateria comparar --saida /tmp/lar                  # alvo = REGRESSAO_LARAVEL_NOVO_URL (padrão :8187, laboratório)
python -m regressao.laravel.bateria comparar --saida /tmp/lar --alvo http://localhost:8074   # prova de estabilidade (referência contra ela mesma)

# Fluxos de navegador (pelo proxy :8190; gravar sempre com o proxy mandando tudo para a referência)
python -m regressao.completa.fluxos gravar   --saida /tmp/fl-g --confirmo-sobrescrever
python -m regressao.completa.fluxos comparar --saida /tmp/fl [--fluxo navegacao --fluxo incluir-registro --fluxo emitir-relatorio]

# Completa (PHP -> Laravel -> fluxos, cada uma com a própria restauração)
python -m regressao.completa.orquestra --saida /tmp/completa [--area A ...] [--prefixo RX ...] [--sem-fluxos] [--alvo-laravel URL]
python -m regressao.completa.orquestra --comparar /tmp/antes /tmp/depois

# Os mesmos, pelos atalhos (rodadas em ~/rodadas, em segundo plano, uma por vez)
regressao/bin/regressao rodada-pequena | rodada-completa [args do orquestra] | comparar ANTES DEPOIS | ver-ultimo
```

O `resumo.md`/`relatorio.md` da completa começa com `Resultado: VERDE (saída 0) | VERMELHO (saída 1) | ERRO (saída 2)`
e traz sempre os avisos: referência = PHP 7.4/Laravel 8; INCONCLUSIVO e ERRO_AMBIENTE nunca são aprovação; escopo da
bateria PHP; e, quando `--alvo-laravel` é a própria referência, que a bateria Laravel mediu auto-consistência, não a
migração.

URLs dos alvos vêm de `REGRESSAO_REF_URL` (:8074), `REGRESSAO_PHP_NOVO_URL` (:8185), `REGRESSAO_LARAVEL_NOVO_URL`
(:8187) e `REGRESSAO_PROXY_URL` (:8190); containers de `REGRESSAO_CONTAINER_*` (seção acima). A bateria PHP loga **na
referência** (o login direto no 8.5 quebra em `abrir.php`, achado da migração) e usa a mesma sessão nos dois runtimes
(volume de sessões compartilhado). Nas saídas, `ref` é a referência 7.4 e `85`/`8.5` o alvo.

### Fluxos de navegador (o que cobrem)

Na base 7.4 o login abre o **Desktop** (`POST /v4/login` → `/extension/desktop`): o fluxo clica em MENU, escolhe a
instituição (`1 - PREFEITURA DBSELLER`), a área e o módulo (textos do menu: `Arrecadação`, `Orçamento`, `ISSQN`,
`Protocolo`), acha o item de menu pela **action** exata nos dados do menu e clica em cada nível; o item abre uma
**janela** do Desktop (`/w/<n>/extension/desktop/window/index/?action=...`) cujo frame `corpo` é a tela.
`navegacao` (login → menu → área → módulo Arrecadação → tela de cadastro `arr1_grupotaxa001` → tela de relatório
`cai2_relcaixa_001` → sair pelo menu do usuário), `incluir-registro` (preenche `arr1_grupotaxa001`
pela UI, inclui, confere o alerta e o **efeito no banco**: `hash_tabelas` de `arrecadacao.grupotaxa` e contagem de
linhas) e `emitir-relatorio` (clica *Imprimir* em `cai2_relcaixa_001?db_opcao=tabrecjm`, confere status, tipo e texto
do PDF). Por passo: DOM normalizado do frame `corpo` da janela (antes de abrir uma tela, o DOM do MENU do Desktop),
status das requisições principais, alertas, valores digitados e banco. O *ping* periódico do Desktop
(`/extension/desktop/Window/ping/`) não entra (cai em qualquer passo conforme o relógio). No passo `sair`, o clique em
*Logout* não gera requisição na referência (Chromium headless): o passo registra `saiu_do_desktop: false`, que é o
comportamento gravado. O cabeçalho **`X-Ecidade-Runtime` é registrado e mostrado como INFO, nunca é falha** (ele vai mudar na
migração: telas hoje no 7.4 passarão ao 8.5). Erros de console e requisições com falha só viram veredito se
**diferirem da baseline**; `net::ERR_ABORTED` (cancelamento por navegação/download) é ignorado. Limite de 120 s por
fluxo; passo que estoura vira falha com mensagem. Senha, SID e tokens nunca vão para a baseline (a gravação é barrada
se aparecerem). Fluxos por área crítica (rodada pós-entrega A): **`financeiro`** (área Financeiro, módulo Orçamento:
inclui uma função orçamentária em `orc1_orcfuncao001`, efeito em `orcamento.orcfuncao`), **`tributario`** (módulo
ISSQN: abre `iss2_tipcalc001` e emite o PDF `iss2_tipcalc002`) e **`cadastros`** (módulo Protocolo: CPF → formulário
→ inclui um CGM pessoa física em `prot1_cadcgm001`, efeito em `cgm`, `cgmfisico`, `db_cgmcpf`, `cgmendereco`,
`personacgm`). **Não cobertos**: telas fora desses módulos, upload, impressão fora de `cai2_relcaixa`/`iss2_tipcalc`,
alteração/exclusão (só inclusão), navegadores além do Chromium headless, o fluxo "com o login recusado". Achado dos
fluxos: o PNG `/228358.png` do formulário de Orçamento responde HTTP 500 (visível em `falhas`).

## 4. Ler os resultados

> **ESCOPO DA BATERIA PHP (leia antes de confiar no verde).** `./ecidade` é montado nos **dois** runtimes
> (`ecidade74_php74` e `ecidade74_php85`, `regressao/lab/docker-compose.e74.yml`): o mesmo código roda em 7.4 e em 8.5.
> A bateria PHP prova **paridade referência 7.4 × 8.5 sobre o código ATUAL**; ela **não detecta** uma regressão introduzida num código comum aos dois
> (um bug que apareça igual nos dois lados dá IDENTICO). Só o **Laravel** e os **fluxos de navegador** são *golden master*
> contra uma gravação anterior. O `compara_hashes` das telas **não** entra no `--comparar`. Esse aviso fixo também sai no
> `resumo.md` da completa.

| Veredito | Significa |
|---|---|
| `IDENTICO` | os dois lados responderam igual (depois de normalizar o que é volátil) |
| `DIVERGE` | respostas diferentes: **achado real** da migração (diff em `diffs/`). Se já existia antes, entra em `regressao/conhecidas.tsv` **com prova** |
| `INCONCLUSIVO` | o caso **não foi exercitado** (ex.: 5xx nos dois lados, sem escrita capturada, payload sem linha-semente). **NÃO é aprovação**: é lacuna de cobertura e vem listado com o motivo |
| `ERRO_AMBIENTE` | a rodada não pôde ser feita (container fora, banco/baseline diferente, alvo inexistente, sessão inválida). Nada se conclui |

Código de saída (de cada bateria e da completa): **2** se houver `ERRO_AMBIENTE`; **1** se houver `DIVERGE` que não seja
conhecida; **0** caso contrário. Na completa vale o **pior** das três. Um 0 com INCONCLUSIVO não é "tudo certo": leia a
seção *INCONCLUSIVO por motivo* e a *Cobertura* do `resumo.md` (catálogos PHP verificados × não, rotas Laravel
cobertas × não, passos de fluxo). O resumo também mostra git, versões, sha256 da baseline e tempos por fase;
`meta.comparavel=false` marca rodadas que **não** servem para antes×depois (ex.: `--sem-restaurar`).

Detalhes de leitura: `telas_com_dados` é um **limite superior** (a heurística `tem_dados` conta qualquer `<td` fora do
cabeçalho, e o e-Cidade usa `<td>` em layout). Tela cuja resposta é uma **página de erro** (Notificação do Sistema/Erro
interno, Fatal/Parse error) igual nos dois lados vira INCONCLUSIVO, não IDENTICO. O **lint** só cobre as telas
selecionadas por `--area/--prefixo`, **não** classes, `libs/` nem models. `--sem-normalizar` só existe na bateria PHP e
**não chega ao `cmp.py`** (que normaliza por conta própria).

`git_sujo` olha o repositório inteiro (costuma ser `true` por causa do ambiente Docker); **`git_sujo_regressao`** olha só
`regressao/`: se for `true`, o código da bateria que rodou não é o do commit registrado.

## 5. Adicionar casos

- **POST real (PHP)**: uma linha em `regressao/php/catalogo_posts.tsv`: `tela<TAB>tabelas (filhas antes da mãe, separadas por
  vírgula)<TAB>campos (querystring)<TAB>area<TAB>verificado|nao-verificado`. Use os campos reais do formulário
  (nomes dos `input`). Rode a linha ao vivo: `verificado` quer dizer *"o caso é válido e o veredito é confiável"* (a
  referência 7.4 respondeu com conteúdo real), **qualquer que seja o veredito**: um `verificado` que dá `DIVERGE` é
  achado e deixa a rodada vermelha. `nao-verificado` é pulado (a menos de `--incluir-nao-verificados`).
  Cuidado com as tabelas filhas: um POST que aborta numa FK deixa resíduo (o próximo restore limpa).
- **Relatório (PHP)**: `regressao/php/catalogo_relatorios.tsv` (`tela<TAB>query<TAB>pdf|xls|html|doc<TAB>area<TAB>status`).
  Mesma semântica de `verificado`. No e-Cidade, "xls" é CSV via `db_download.php`.
- **Telas / lint / classes** não precisam de cadastro: vêm do que existe em `ecidade/` (`--area`/`--prefixo` escolhem).
- **Laravel**: o inventário vem de `python -m regressao.laravel.rotas` (`php artisan route:list --json` no container de
  referência; se um controller da própria referência não instancia, o `route:list` do Laravel 8 cai inteiro e o
  inventário usa a listagem tolerante de mesmo formato, que grava o erro na coluna `erro_controller` de
  `casos/_inventario.tsv`). O gerador cria um caso por rota (GET autenticado; sonda `{}` nas demais) a partir do
  inventário: `python -m regressao.laravel.gerador` (regera `casos/rotas_*.yml`); a cobertura sai de
  `python -m regressao.laravel.cobertura`. Casos escritos à mão ficam em `casos/auth.yml` e `casos/escrita.yml`.
  `casos/_ajustes.yml` guarda o que a regeneração preserva: `volateis` (campos JSON mascarados), `instaveis`,
  `perigosas` (sondas que **escreveram** ao vivo: deixam de ser geradas) e `permitidas` (allowlist de
  DELETE/PUT/PATCH, vazia por padrão). `espera_status: N` declara que uma rejeição é esperada (ex.: 500 de rota
  protegida na referência): o caso vira IDENTICO só se a **referência** confirmar esse status na gravação.
  Depois de mudar casos, **regrave** a baseline (abaixo).
- **Fluxo de navegador**: uma função em `regressao/completa/fluxos.py` (lista de passos `(nome, função, tira_snapshot)`)
  registrada em `FLUXOS`; rode `gravar --fluxo <id> --confirmo-sobrescrever`.

## 6. Proteção da baseline

As baselines (`regressao/baseline/laravel/`, `regressao/baseline/fluxos/`, o dump) são a **referência pré-migração**.
Regravá-las com o sistema já migrado destrói a comparação. Por isso:

- `gravar` **recusa** (saída 2) sobrescrever baseline existente, e gravar contra um alvo que não seja a referência
  Laravel 8 (`REGRESSAO_REF_URL`, :8074), sem `--confirmo-sobrescrever` (e `--alvo` explícito para outro alvo). Só use a
  flag para regravar **na referência, que não é migrada** (o `_meta.json` registra `"alvo": "ref"`), depois de mudar
  casos ou o dump.
- `gravar` não produz "casos IDENTICO": nada foi comparado; o resumo diz `GRAVACAO ... nao e comparacao`.
- `comparar` recusa baseline gravada com outro sha256 de dump.
- O repositório no GitHub (`Segunddo/e-cidade`) é **PÚBLICO** e as baselines contêm **dados do banco de desenvolvimento**
  (nome e telefones da instituição, usuários, textos de telas etc.; o campo `senha` de `/v4/api/user` é mascarado).
  A branch `regressao-php74` já está publicada com essas baselines; antes de publicar novas gravações (ou outra
  branch), decida se esses dados podem ficar num repositório público. Senhas, SIDs e tokens nunca são gravados.

## 7. Migração: antes × depois

> Lembrete de escopo (§4): como `./ecidade` é compartilhado pelos dois runtimes, a rodada PHP "antes" **não** é uma
> fotografia do comportamento pré-migração; só Laravel e fluxos guardam referência gravada. Para PHP, o "antes × depois"
> mede a paridade referência 7.4 × 8.5 em cada momento.

**ANTES de migrar** (no sistema de referência, ambiente recém-subido, nada rodado ao vivo antes do dump):

1. Gerar o dump (seção 2) e commitar `baseline.dump.sha256`.
2. `python -m regressao.laravel.bateria gravar --saida /tmp/lar-g` (Laravel 8 de referência em :8074) e
   `python -m regressao.completa.fluxos gravar --saida /tmp/fl-g`; commitar as baselines.
3. Rodada completa de referência, arquivada: `python -m regressao.completa.orquestra --saida ~/regressao/antes
   --alvo-laravel http://localhost:8074` (o Laravel 8 contra ele mesmo: todos IDENTICO/INCONCLUSIVO).

**DEPOIS de migrar** (Laravel 13 de pé em `REGRESSAO_LARAVEL_NOVO_URL`):

4. `python -m regressao.completa.orquestra --saida ~/regressao/depois` (e `--area/--prefixo` se quiser reduzir o PHP).
5. `python -m regressao.completa.orquestra --comparar ~/regressao/antes ~/regressao/depois` → `comparacao.md/.json`:
   **regressões** (IDENTICO/INCONCLUSIVO → DIVERGE/ERRO_AMBIENTE, e a *perda de verificação* IDENTICO → INCONCLUSIVO),
   **correções** (DIVERGE/ERRO → IDENTICO), casos **adicionados** e **removidos**, e diferenças de meta (commit, sha da
   baseline, versões). A saída é o **pior** entre a comparação e o estado de DEPOIS: 1 se houver regressão ou caso
   removido **ou** DEPOIS tiver `DIVERGE` não conhecida (mesmo igual a ANTES); 2 se alguma rodada for inválida ou
   `comparavel=false` **ou** DEPOIS tiver `ERRO_AMBIENTE`. `AVISOS` no `comparacao.md/.json` dizem isso. Transições
   `DIVERGE/ERRO_AMBIENTE → INCONCLUSIVO` aparecem em **Lacunas** (não são correção: o caso deixou de ser verificado).

## 8. Custos, tempos e memória

- **Restauração ≈ 3,5–4,5 min** cada. A completa restaura **3 vezes** (PHP, Laravel, fluxos): ≈ 12 min só de restore.
  A rodada pequena do atalho (3 prefixos PHP + Laravel inteiro + 6 fluxos) leva ≈ 23 min (PHP 4,2, Laravel 14,2,
  fluxos 4,4); resultado em 2026-11-18: VERMELHO, PHP 15/15/0/0, Laravel 719/0/273/0, fluxos 32 IDENTICO.
- PHP: ~0,83 s/tela, POSTs 4–17 s cada, relatórios ~1 s; uma rodada de fumaça (`--prefixo`) leva ~5–6 min no total. Áreas
  inteiras levam **horas**. Laravel (base 7.4): ≈ 10,5–11 min de casos (992 casos) + ≈ 3,2 min de restore. Fluxos: ≈ 1 min + restore.
- A memória do host é apertada: antes de rodadas longas, solte o cache de arquivos do WSL
  (`wsl -d Ubuntu-24.04 -u root -- sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'`). Um `.wslconfig` com `memory=6GB` e
  `autoMemoryReclaim=gradual` ajuda; fica a critério do usuário. Os fluxos usam um Chromium só, fechado ao fim.
- **Estado do banco**: cada bateria assume banco recém-restaurado e o **deixa sujo**; os fluxos (que rodam por último na
  completa) deixam um registro de teste em `grupotaxa`. Nada precisa ser limpo à mão: a próxima rodada restaura.

## 9. Limitações conhecidas

- **A bateria PHP só prova paridade referência 7.4 × 8.5 sobre o código atual** (código compartilhado, ver §4); não detecta regressão
  de código comum aos dois runtimes.
- **Laravel na base 7.4 (o que a bateria mede hoje).** Referência = `ecidade74_php74` (:8074): PHP 7.4.33, Laravel
  8.73.2, Passport 10.4.2 (league/oauth2-server 8.3.2). Baseline `regressao/baseline/laravel/` **regravada no banco v2**
  (§2) em 2026-11-18 com `gravar --alvo http://localhost:8074 --confirmo-sobrescrever` (`_meta.json`: `alvo: ref`, dump
  `97251574…`, **992 casos**; os 2 registros com campo volátil novo refeitos com `caso remove` + `gravar --apenas-novos`).
  Os números abaixo marcados "v1" são da primeira gravação, no dump de instalação; o que mudou no v2 está em cada item.
  - **Inventário**: o `route:list --json` do Laravel 8 instancia cada controller e **cai inteiro** na base 7.4
    (`ParametrosEnvioNotificacoesController` usa `ECidade\Educacao\MatriculaOnline\Repository\ConfiguracaoRepository`,
    que não existe). `rotas.py` então usa a listagem tolerante de mesmo formato: **1434 rotas** (laravel 1423, rest 4,
    silex 7), **101** com `erro_controller` (o controller não instancia no console: modelos `cl_*` do legado, classes
    `TraceLog`, `DefaultSession`, `ECidade\Pdf\Pdf`… inexistentes; pela HTTP 16 delas respondem 2xx, 19 4xx e 26 5xx).
  - **Cobertura** (`_cobertura.md`, banco v2): **969 rotas com caso** (laravel 964/1423, silex 5/7, rest 0/4) + 23 casos
    escritos à mão (12 auth, 3 escrita, 8 integração). Fora: 290 rotas com parâmetro de caminho, 160 perigosas por nome
    ou provadas ao vivo (12 sondas que escreveram com corpo vazio: 4 na branch antiga; 4 no banco v1 da base 7.4,
    `baseEscola/atos/salvar`, `fix/lancamento/slips`, `fix/lancamento/suplementacoes`, `escrituracao-contabil/virada-rp`;
    e 4 no banco v2, cujas tabelas novas as fazem chegar ao INSERT/DELETE: `ocupacoes/ocupacao`,
    `transposicao/criterios-ordenacao`, `escrituracao-contabil/implantar-saldo-inicial`, `e-social/store`),
    14 DELETE/PUT/PATCH e 1
    rota com espaço no fim da URI (`emitir-carteira `, erro do arquivo de rotas). As 108 rotas `GET /web/...` respondem
    404 à bateria (não exercitadas além do roteamento). Na referência (v2): 250 casos 2xx, 452 4xx, 267 5xx (v1: 199,
    450, 333): as migrations fizeram ~60 rotas saírem do 500. Um achado: `GET contratos/acordo/buscar-configuracoes`
    **grava** (cria a configuração padrão na primeira chamada; o INSERT entra no `sql_negocio` comparado).
  - **Passport 10 se comporta como o 5.4 nos casos de auth**: rota protegida sem token, com token inválido, expirado
    (JWT re-assinado com a chave local) ou revogado → **HTTP 500** `{"error":true,"message":"Unauthenticated."}` (handler
    da aplicação); token expirado só em `oauth_access_tokens.expires_at` continua aceito; `dbseller` com senha errada
    continua recebendo token; usuário inexistente → 500 "The user credentials were incorrect.".
  - **Estabilidade**: três gravações independentes da referência (duas exploratórias + a oficial) só diferiram em 3
    casos, todos tratados em `_ajustes.yml`: `volateis` (timestamp unix no nome do CSV de `ddr/template` e da tabela
    `w_ajuste_conlancamrecurso_<ts>` na mensagem de erro de `fix/lancamento/conlancamrecurso`) e o novo **`sem_ordem`**
    (`postgres/views` faz `select … from pg_views` sem ORDER BY: mesmas 20 views em ordens diferentes; a lista é comparada
    como conjunto ordenado, conteúdo diferente continua DIVERGE). No banco v2, a gravação exploratória × a oficial
    acharam mais 2 `volateis` (`contratos/acordo/buscar-configuracoes`: `data.created_at/updated_at`;
    `transposicao/relatorio-inscritos`: `data.path/url` com timestamp). **Prova (banco v2)**: duas comparações seguidas
    da referência contra a baseline (`comparar --alvo http://localhost:8074`, cada uma restaurando o dump) deram
    exatamente o mesmo resultado, caso a caso: **719 IDENTICO, 0 DIVERGE, 273 INCONCLUSIVO (272 "5xx nos dois lados", 1
    "resposta sem conteúdo"), 0 ERRO_AMBIENTE**, saída 0 (v1: 666/0/330/0).
- **Baselines Laravel guardam `file`/`line`/stacktrace absolutos** (cerca de 12 dos 992 registros da base 7.4 trazem caminhos do
  servidor, p.ex. `/var/www/html/...` e números de linha). **Decisão (implementada em `laravel/mascara.py::normaliza_erro`,
  aplicada só na comparação; a baseline bruta guarda o registro inteiro) — **escopo estreito**: só em **respostas de erro**
  (status >= 400 ou objeto com `exception`), só no `json` (e no `texto` de respostas 5xx); nunca em `sql_negocio`,
  cabeçalhos, tipos, hashes de tabela nem em respostas de sucesso. Em objetos com cara de erro (têm `exception`/`trace`/
  `stacktrace`, ou o envelope do app `error: true`) os campos `file`, `line`, `trace`, `stacktrace`/`stack_trace` viram
  `<X>`; um objeto de negócio `{message, file, line}` **não** é tocado. Caminhos absolutos só com **raiz conhecida do
  servidor** (`/var/www/html`, `/var/www`, `/app`, `/srv/<x>`) seguida de `vendor/`, `app/`, `bootstrap/`, `storage/`,
  `ecidade/`, `libs/`… viram `<caminho>` e `on line N` vira `on line <N>`; URLs como `/storage/a.pdf` ou `/public/x.png`
  continuam comparadas. A classe da exceção (`exception`) e a `message` **continuam comparadas**: mudar a exceção é
  DIVERGE real. Consequência: um erro que só muda de arquivo/linha entre o Laravel 8 e o 12 não aparece como divergência.

- **Não existe Laravel 13 do e-Cidade** (alvo do grupo): o laboratório `ecidade74_lar12` (:8187, `regressao/lab/docker-compose.lar12.yml`,
  projeto `e74-lar12`) roda o runtime do `ecidade74_php85` (mesma imagem e `paridade-74.ini`) sobre o código de
  `LAR12_CODIGO` (padrão: o `./ecidade` atual, Laravel 8). O Laravel 8 **sobe** no PHP 8.5 (boot e console funcionam),
  mas `comparar` no alvo padrão devolve **um** `ERRO_AMBIENTE` (`laravel:banco`, saída 2, depois de restaurar o banco):
  `POST /v4/oauth/token` dá 500 porque o `lcobucci/jwt` 3.4.0 testa a chave com `is_resource()` e no PHP 8 ela é um
  `OpenSSLAsymmetricKey` (nenhum JWT é emitido nem validado). Causa exata e próximos passos em
  `regressao/baseline/lab-lar12-resultado.md`.
- **Integrações (11b), o que existe e o que não existe** (`laravel/integracao.py`, `laravel/stubs/`,
  `laravel/casos/integracao.yml`):
  - **Arquivo gerado por conteúdo**: 5 casos (`arquivo-vacinacao-pdf-*` x3, `arquivo-siconfi-csv`,
    `arquivo-pcasp-csv`): a rota devolve JSON com o caminho do arquivo (`data.path`/`data.csv`), a bateria o baixa e
    compara o **texto extraído** (pypdf/CSV/openpyxl/xlrd), nunca os bytes; o nome com timestamp é mascarado. Das 77
    rotas que parecem gerar arquivo, só estas devolveram arquivo com corpo mínimo conhecido; as demais pedem dados de
    domínio (planejamento existente, instituição na sessão legada `DB_instit`, filtros) que o banco de dev não tem
    (`Undefined index: DB_instit`/`planejamento_id`...). Nenhum caso XLSX real: o app serve CSV.
  - **Console**: 3 casos (`console-list` só pelos nomes dos comandos, `console-env`, `console-migrate-status`),
    executados com `docker exec ... php artisan` (Laravel 8). **O container acompanha o alvo** (nomes em
    `nucleo/ambiente.py`): na referência é sempre `REGRESSAO_CONTAINER_REF` (`ecidade74_php74`); no laboratório
    (`REGRESSAO_LARAVEL_NOVO_URL`) é `REGRESSAO_CONTAINER_LARAVEL_NOVO` (`ecidade74_lar12`); em qualquer outro alvo
    `REGRESSAO_LARAVEL_CONSOLE_CONTAINER` é **obrigatória**, e um alvo que não é a referência nunca pode cair no container
    de referência (o caso vira `ERRO_AMBIENTE` em vez de falso IDENTICO). Falha do `docker exec` (125/126/127, "No such
    container") também é `ERRO_AMBIENTE`; só `list`, `env` e `migrate:status` passam pela allowlist.
    `console-migrate-status` compara o **conjunto completo** de migrations (contagem + sha256 + lista, sem truncar; o
    `Yes`/`No` do Laravel 8 e o `Y`/`N` do 5.4 viram o mesmo `Y`/`N`): na base 7.4 são 1191 migrations; rodadas: 455 no banco v1, 1168 no banco v2 (§2).
    Comandos de domínio (`agendamento:inativarvinculoprofessor`,
    `matriculaonline:alteracaoinscricao`, `payroll:*`) **escrevem** no banco e não foram incluídos.
  - **SMTP de teste e stub PIX**: servidores locais (`SmtpStub`, `PixStub`), sobem e param por `com_stubs()`; o
    SMTP captura a mensagem e `compara_email` normaliza `Date`, `Message-ID` e fronteiras MIME (testado com
    `smtplib`). **Mas nenhum caso os exercita**, por inviabilidade comprovada: (a) nenhum código de Laravel/Silex
    (`app/`, `src/`) usa `Mail::`, PHPMailer ou Swift (o `.env` aponta `smtp.mailtrap.io:2525`; o envio de e-mail vive
    no PHP legado e nenhuma rota `/v4` ou `/api/v1` o dispara); (b) as URLs do Banco do Brasil estão fixas em
    constantes HTTPS (`BancoDoBrasil::BASE_URL`/`BASE_AUTH_URL`), `POST pix/gerar` exige sessão legada + recibo com
    código de barras + CGM com CPF/CNPJ válido, e redirecionar o app ao stub exigiria DNS/TLS dentro do container,
    o que não é permitido alterar aqui. Quando o Laravel 13 tiver um ponto de configuração para a URL do PSP, o
    stub já está pronto para receber o caso.
  - **Adicionar sem regravar**: `python -m regressao.laravel.bateria gravar --saida DIR --apenas-novos
    --confirmo-sobrescrever` roda só os casos **ausentes do `_meta`** (restaurando o dump) e acrescenta à baseline; os
    registros existentes não são tocados. Recusa: alvo que não seja a referência Laravel 8, dump diferente, registros
    **perdidos** (id no `_meta` sem arquivo) e arquivo órfão. Para refazer um registro: `python -m regressao.laravel.caso
    remove <id>` (apaga o arquivo e tira o id do `_meta`) e depois `--apenas-novos`.
- Laravel: cobre 969 de 1434 rotas (números acima); `rest/v1` só com rotas parametrizadas (nenhum caso gerado);
  `PATCH`/`HEAD` colapsam em `PUT`/`GET`. Os casos de rota protegida dão HTTP 500 (não 401) na referência e usam
  `espera_status`; ~270 casos (banco v2; ~330 no v1) são `INCONCLUSIVO` (5xx nos dois lados): **não são aprovação**, são rotas que com corpo
  vazio/sem dados de domínio não chegam à regra de negócio. `dbseller` com senha errada recebe token (achado do app,
  gravado como referência).
- PHP, catálogos **reverificados ao vivo na base 7.4** (2026-11-18, linha a linha, dump restaurado; cabeçalho de cada
  `.tsv` traz o detalhe). **POSTs**: 52 linhas, 47 `verificado` (13 IDENTICO, 34 DIVERGE) e 5 `nao-verificado` (a
  referência 7.4 não gravou nada com o payload atual: `pes1_pensao001`, `rec1_assentamentos.RPC`, `rec4_rpcexame`,
  `rec1_rhestagioresultado001`, `cai1_caiparametro001`). Quase todo DIVERGE é "o 8.5 não grava" ou "grava 0 no lugar do
  valor" (o idioma `$this->campo == "" ? POST : $this->campo` com `0 == ""`, que mudou no PHP 8). O CGM continua fora
  (o `DELETE` em `cgm` falha fora do app pelo trigger `tg_atualiza_issbaseintegracaoexterna`, e o restore por diferença do
  `escrita_post.py` aborta). Cadastros que não restauram a `sequence` (ex.: `cai1_bancoshistmovcategoria001`) ficaram de fora.
  **Relatórios**: 42 linhas, 37 `verificado` (36 DIVERGE: referência 200 com PDF × 8.5 500; `func_orcfuncao` IDENTICO) e 5
  `nao-verificado` (os 3 `db_download.php` dão 302 porque os CSVs não existem em `ecidade/tmp/` desta base;
  `orc2_despsecretaria002` dá 500 na própria referência; `func_cgm` só devolve a página de pesquisa). `cem2_renovacoes` é
  `verificado` com evidência fraca (modelo de PDF em branco).
  **Reconferido no banco v2** (2026-11-18, as 94 linhas, 767 s): 93 com o mesmo resultado; `rec1_assentamentos.RPC`
  passou a gravar na referência (3 statements de negócio × 0 no 8.5: DIVERGE) e virou `verificado`. POSTs hoje: **48
  `verificado` (13 IDENTICO, 35 DIVERGE) e 4 `nao-verificado`**; relatórios sem mudança.
- **Login HTTP da bateria PHP no banco v2.** `abrir.php` da referência termina em `ArgumentCountError`
  (`db_verifica_ip_banco()` chamada sem argumento, linha 372) **depois** de gravar a sessão; o resto do login
  (`inicio`/`topo`/área/módulo) funciona e as telas abrem. Numa rodada (2026-11-18, logo depois do restore) a sessão
  saiu sem conexão com o banco: toda tela da referência respondeu `Erro:(27) inserindo arquivo em db_usuariosonline`
  (50 B), que passava pela sonda de sessão. Desde então essa página conta como **sessão inválida** (`telas._INVALIDA`):
  a bateria renova o login em vez de medir com ela. Causa da sessão sem conexão não isolada (não se repetiu).
- **Os PDFs dão HTTP 500 no PHP 8.5** e funcionam na referência 7.4: a causa comum é `ParseError` em
  `fpdf151/fpdf.php:614` (offset de string com chaves, removido no PHP 8); alguns também chamam `parse_str()` com 1
  argumento. São regressões **reais** da migração e mantêm a bateria PHP vermelha (saída 1) até serem corrigidas ou
  aceitas em `conhecidas.tsv`.
- O PHP não cobre ainda a rodada de **área inteira** quanto à memória (corpos ficam em memória por prefixo): prefixos
  enormes (`con`, `edu`) usam mais RAM.
- Fluxos: 6 fluxos (Arrecadação, Orçamento, ISSQN, Protocolo/CGM), 26 passos, só inclusão e emissão, todos pelo
  Desktop do PR. Baseline regravada no banco v2 contra a referência (proxy :8190 com tudo no 7.4, `_meta.json` com o
  dump `97251574…` e o commit do código dos fluxos); **prova**: duas comparações seguidas, cada uma restaurando o dump,
  deram **32 IDENTICO** (26 passos + 6 `eventos`), 0 DIVERGE/INCONCLUSIVO/ERRO_AMBIENTE, iguais caso a caso. O console
  registra em todos os fluxos `Permissions policy violation: unload is not allowed` (Chromium recente com o Desktop) e,
  no CGM, `Failed to execute 'select' on 'HTMLInputElement'` (JS da tela): estão na baseline, só viram veredito se
  mudarem. DOM compara estrutura (scripts inline e estilos são removidos),
  então erro de JS que não mude o DOM só aparece pelo console; PDF vem de um GET idêntico com a sessão do navegador
  (o Chromium headless trata o PDF como download). Banco de dev pode mudar o conteúdo de telas como "últimos acessos
  ao módulo": por isso os fluxos restauram o dump antes de cada rodada.
