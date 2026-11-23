<!-- Guia do grupo convertido de migracao-php74-para-85.html (18/11/2026) para Markdown pelo servidor MCP.
     Conteudo fiel ao original; so a formatacao mudou. -->

e-Cidade · migração para o PHP 8.5 · 18/11/2026

# Migração do PHP 7.4 para o 8.5 a partir do PR #8

O PR #8 da DBSeller levou o e-Cidade oficial do PHP 5.6 para o **PHP 7.4** e do Laravel 5.4 para o **Laravel 8**. A `base-php74` do grupo nasce desse PR e passa a ser o ponto de partida de todos. Este documento diz o que muda, o que medimos na nova base, o que cada frente precisa fazer até o **PHP 8.5** e as regras de trabalho.

## Resumo

- **36.683** arquivos PHP do sistema (fora `vendor/`)

- **32** compilam no 7.4 e quebram no 8.5

- **13** já não compilam nem no 7.4

- **134** pontos do código Laravel que mudam até o 13

- **A referência agora é o 7.4.** "Funciona igual" quer dizer igual ao 7.4 do PR, não mais ao 5.6. Onde o PR mudou o comportamento, vale o PR.
- **O que o PR já fez e roda no 8.5 fica como o PR fez.** Não se troca a solução da DBSeller pela da `base-php84` nem por uma nossa, mesmo que a nossa pareça melhor. A base mudou: mexe-se só no mínimo que o 8.5 exige, por cima do código do PR.
- **O PHP é mais fácil do que parece no lint:** só 32 arquivos quebram na compilação. O risco maior está nas **mudanças silenciosas**, que não dão erro: comparação de texto com número (36.729 pontos), construtores no estilo antigo (152 classes) e funções removidas que só falham quando a tela roda.
- **O Laravel 8 do PR não roda oficialmente no PHP 8.5.** Só o 12 e o 13 têm suporte. O alvo é **Laravel 13 + Passport 13**, com bibliotecas próprias no 8.5, e o 7.4 fica intacto com o Laravel 8.
- **O sistema do PR precisa de 737 migrations no banco** para abrir o menu. Isso exige decidir qual banco usar como referência (decisões).
- **A API V1 (Silex) ficou desligada no PR**: o código está lá, a biblioteca não.
- **Ninguém começou ainda sobre a `base-php74`.** O commit de ferramentas do grupo foi montado sem Docker e não foi testado: a primeira tarefa é subir o ambiente e confirmar que abre.

## A nova base

| Peça | Base antiga (master) | Nova base (PR #8) | Alvo |
| --- | --- | --- | --- |
| PHP | 5.6 | 7.4 | 8.5 |
| Laravel | 5.4 | 8.73 | 13 |
| Passport (token da API) | 4 | 10.4 | 13 |
| Guzzle (chamadas HTTP) | 6 | 7.5.0 (versão fixa) | 7 ou 8 |
| API V1 (Silex) | no ar | código presente, biblioteca removida | decisão em aberto |
| Phinx (migrations antigas) | no composer | removido; 1.511 arquivos ficam como histórico | nada a fazer |
| Banco | PostgreSQL 11/12 | PostgreSQL 16 (instalação do zero) | igual ao PR |
| Contêiner de referência | `ecidade_php56` | `ecidade_php74` (porta 8080) | 8.5 na 8085, proxy na 8090 |

### Novidades do PR que mexem no comportamento

- **Desktop e menu:** o Desktop foi ligado à força (`ECIDADE_DESKTOP=true`). O menu passa a ler favoritos (`configuracoes.itens_menu_usuario_favoritos`) e a coluna nova `db_itensmenu.api`.
- **Login:** a tela `login.php` quase não mudou e ainda abre a janela `abrir.php`. O PR acrescenta `POST /v4/login`, `unblock`, `kill` e `logout` (`LoginController`/`AuthService`). `libs/db_conecta.php` agora inicia o Eloquent.
- **API `/v4`:** passou de 537 para 1.300 rotas em `routes/api` (68 arquivos), mais 115 rotas web. Há favoritos e notificações em `/v4/api/configuracao/menu/*` e `/usuario/notificacoes`. O grupo `assinador` deixou de ser carregado em `routes/api.php`.
- **Permissões:** `storage`, `bootstrap/cache` e `tmp` passam a `chgrp www-data` + `g+rwX`.
- **Perfilador (XHProf):** só liga com `APP_ENV=local` e o cookie `_profile`.

## PHP: do 7.4 ao 8.5

Medido sobre a `origin/base-php74`: `php -l` nos 36.683 arquivos, no PHP 7.4 e no 8.5, mais busca de padrões no código. Nada foi executado no sistema.

### 1. O que nem compila no 8.5 (32 arquivos)

| Causa | Arquivos | Correção típica |
| --- | --- | --- |
| Chaves para pegar letra de texto: `$s{0}` (removido no 8.0) | 20 | `$s[0]` |
| Ternário encadeado sem parênteses: `a ? b : c ? d : e` | 3 | pôr os parênteses na ordem que o 7.4 usa (da esquerda) |
| Nome com barra invertida que virou um único token no 8.0 (`\CamposDinamicosResposta`, `AndamentoPadrao\…`) | 4 | ajustar o nome/uso do namespace |
| Assinatura de método incompatível com a da classe-mãe (jpgraph: `PiePlotC`, `RotImage`, `TextPropertyBelow`) | 4 | igualar a assinatura (padrão já usado pelo grupo no jpgraph) |
| Conversão `(real)` removida | 1 | `(float)` |

Por pasta: raiz 4, `app` 3, `dbagata` 6, `ext` 2, `fpdf151` 5, `integracao_externa` 1, `libs` 4, `model` 2, `securimage` 2, `src` 3. Outros **13 arquivos já falham no 7.4** (código quebrado hoje, ex.: `pes1_reajusteprog001.php` com `}` sobrando): pela regra, ficam como estão e são registrados.

### 2. O que compila mas quebra quando a tela roda

| Mudança | Tamanho | Efeito no 8.5 |
| --- | --- | --- |
| `each()` removida (8.0) | 84 usos / 28 arq | erro fatal na hora que a linha roda |
| `pg_lo_export`/`pg_lo_import` com a conexão no fim (ordem antiga removida no 8.0) | 40 usos / 33 arq | erro de tipo; a exportação do arquivo não acontece |
| `create_function` removida | 1 arq | erro fatal |
| `get_magic_quotes_*` removidas | 2 arq | erro fatal |
| `count()` de algo que não é lista (ex.: `null`, `false`) | amplo | no 7.4 é aviso; no 8.0+ é erro fatal (`TypeError`) |

### 3. Mudanças silenciosas (não dão erro, dão resultado diferente)

**São as mais perigosas: a tela abre, mas faz outra coisa.** A comparação de telas por bytes só pega quando o caminho é exercitado.

- **Comparação de texto com número (8.0):** no 7.4, `0 == ""` é verdadeiro; no 8.0+ é falso. O padrão `$this->x == ""`, usado nas classes de dados para decidir se lê o valor do formulário, aparece **36.729 vezes em 4.054 arquivos**. Com `$x` inteiro, no 8.5 o valor do formulário deixa de ser lido. O grupo já tem uma regra Rector para isso: `scratchpad/rector-rules/GuardaComparacaoLiteralRector.php`.
- **Construtor no estilo antigo (8.0):** método com o mesmo nome da classe deixa de ser construtor. **152 classes em 143 arquivos** não têm `__construct`. No 8.5 o objeto nasce sem a inicialização, sem erro nenhum.
- **Funções com `null` onde se espera texto (8.1):** geram aviso de obsoleto hoje e mudam de comportamento em versões futuras. Precisam de atenção onde o aviso aparece na tela.

### 4. Avisos de obsoleto (funcionam no 8.5, mas sujam a tela se o aviso estiver ligado)

| Função/forma | Desde | Tamanho |
| --- | --- | --- |
| `utf8_encode`/`utf8_decode` | 8.2 | 1.832 usos / 376 arq |
| `"${var}"` dentro de texto | 8.2 | 113 arq |
| `strftime`/`gmstrftime` | 8.1 | 12 arq |
| `FILTER_SANITIZE_STRING` | 8.1 | 3 arq |

Pela regra "funciona igual", aviso que não aparece na tela e não muda o resultado não precisa de correção. Confira a configuração de `error_reporting`/`display_errors` do 8.5 contra a do 7.4.

## Cuidado ao usar a `base-php84` como guia

O `CONTRIBUINDO.md` sugere usar a `base-php84` como guia (`git diff origin/base-php74 origin/base-php84 -- <arquivos>`). Vale, com uma ressalva importante: **parte do que foi corrigido lá era diferença entre o 5.6 e o 7, que o 7.4 do PR já tem.** Copiar essas correções agora muda o comportamento em relação à nova referência.

| Correção na base-php84 | Ainda vale do 7.4 ao 8.5? |
| --- | --- |
| `$$x[$i]` e `$o->$p[$i]` (mudaram de sentido no PHP 7.0) | **não**: o 7.4 já lê do jeito novo; mexer agora mudaria o resultado |
| `split()` (removido no 7.0, coberto por função de compatibilidade) | **não**, se a mesma função de compatibilidade estiver no 7.4 e no 8.5 |
| `break` fora de laço | **não**: já é erro de compilação no 7.4; se compila no 7.4, não existe |
| `$s{i}` → `$s[i]` | **sim**: removido no 8.0 |
| `pg_lo_export` com a conexão no fim | **sim**: removido no 8.0 |
| Construtor do jpgraph e assinaturas compatíveis | **sim**: 8.0 |
| Comparação `== ""` com inteiro | **sim**: 8.0 |
| `each()`, `create_function`, `count(null)` | **sim**: 8.0 |

### A prioridade é o código do PR

- **Se o PR já resolveu e funciona no 8.5, fica o do PR.** Mesmo que a `base-php84` tenha resolvido o mesmo ponto de outro jeito, não se substitui. O PR é de um dos donos do sistema e é a nova base.
- **Se o PR resolveu, mas não roda no 8.5,** ajusta-se o código do PR no mínimo para rodar, mantendo a estrutura e o jeito dele. Não se reescreve com a versão da `base-php84`.
- **Se o PR não mexeu e o ponto quebra no 8.5,** aí sim a `base-php84` serve de modelo, adaptada ao código atual do arquivo, que o PR pode ter reformatado. Não se copia o arquivo inteiro de lá.
- **Nunca** se copia um arquivo inteiro da `base-php84` por cima do da `base-php74`: isso desfaz as mudanças funcionais do PR (Financeiro, Patrimonial, Tributário, Folha, Educação, Saúde).

Regra prática: antes de aplicar uma correção vinda da `base-php84`, rode o trecho no 7.4 e no 8.5. Se o 8.5 já se comporta como o 7.4, não mexa. Se precisa mexer, parta do arquivo da `base-php74` e mude só as linhas necessárias.

## Laravel, bibliotecas e APIs

Frente do grupo Laravel. Pela regra 6 do `CONTRIBUINDO.md`, `composer.json`, `composer.lock` e `vendor/` são do grupo Laravel: ninguém mexe sem combinar.

### Estratégia

- O Laravel 13 exige PHP 8.3 ou mais e não roda no 7.4. Então o **7.4 fica com o Laravel 8 do PR, intacto**, e o **8.5 ganha bibliotecas próprias** (um `composer` só dele, com Laravel 13 e Passport 13). Assim a referência nunca muda e dá para comparar os dois lado a lado.
- Os degraus 9, 10 e 11 não ajudam: nenhum tem suporte oficial no 8.5. O 12 serviria de parada, mas o suporte de segurança dele acaba em 02/2027.

### Bibliotecas que travam o PHP 8.5

- **10 pacotes do `composer.lock` do PR excluem o 8.5:** `lcobucci/jwt` 3.4, `dompdf` 0.8.6, `mpdf` 8.2.4, `laminas-escaper`, `htmlpurifier`, `nette/schema`, `nette/utils`, `bacon-qr-code`, `qrcode-detector-decoder` e `faker` (desenvolvimento). `phpspreadsheet ^1.08` resolve para 1.30.x, que declara `<8.5`. A maioria sai ao atualizar o pacote que a puxa.
- **Com Laravel 12 ou 13 e as versões liberadas, sobram 2 bloqueios** (testado no Composer com PHP 8.5.12):
  - `dbseller/sdk-api-pix-bb` 2.0.0, que exige o Guzzle 7.5.0 exato. A solução já medida é um ajuste mínimo aplicado na instalação, só no 8.5, com prova contra dublê de que os pedidos saem idênticos.
  - `proner/phppimaco` 1.4.5, que puxa `endroid/qr-code ^2.5` e `bacon-qr-code` 1.0.3. A solução já medida mantém a etiqueta com o mesmo tamanho impresso.

### Defeitos que o Laravel 8 do PR já tem hoje (também no 7.4)

- **Tempo de cache:** desde o 5.8, `Cache::put` conta em segundos. `AssinadorAPI.php:177` e `EmissaoContraChequeJob.php:124` (provavelmente também `LicitaconObrasClient.php:47`) guardavam 5 e 10 **minutos** e agora guardam 5 e 10 **segundos**.
- **Funções removidas:** `array_pluck` (`ComissaoController.php:75`, e também na tela `edu4_cancelaprogressao001.php:96`) e `str_random` (`ModelFactory.php:22`) sem o pacote `laravel/helpers`.
- **Configuração lida fora do lugar:** 82 `env()` fora de `configuration/` em 33 arquivos; com a configuração em cache, devolvem `null`.

Como estão no 7.4 (a referência), a regra manda registrar e avisar quem cuida da área. Corrigir é decisão do grupo.

### O que muda do Laravel 8 ao 13 (contado na nova base)

| Assunto | Tamanho | O que muda |
| --- | --- | --- |
| Inicialização e configuração | esqueleto 5.4 mantido | `bootstrap/app.php`, `Kernel`, `Handler`, providers e `configuration/` seguem a estrutura antiga (o 11+ aceita) |
| Passport 13 e login | `/v4/login` + tabelas `oauth_*` | login por senha precisa ser ativado (`enablePasswordGrant()`); o model de usuário precisa de `OAuthenticatable`; `Passport::ignoreRoutes()`; ids inteiros dos clientes |
| Datas | 21 models com `$dates`; 256 usos do Carbon; 242 pontos que geram JSON | `$dates` sai no 10; Carbon 2 → 3 |
| Consultas | 302 usos de `DB::raw` | no 10 a expressão não vira texto sozinha |
| Validação | 82 pontos com `validated()` | chaves sem regra deixam de voltar |
| E-mail | SwiftMailer | trocado pelo Symfony Mailer no 9 |
| Arquivos | 3 arquivos de configuração | Flysystem 3; raiz padrão do disco local muda no 12 |
| Rotas | 1.300 rotas | ordem de precedência no 12 |
| Documentos | mPDF, dompdf, PhpSpreadsheet, PHPWord | versões novas; conferir PDF, planilha e Word contra o 7.4 |

No total, 134 itens dos guias oficiais de atualização aparecem em uso no código; nenhum deixou de ser usado em relação à base antiga. O inventário completo, com arquivo e linha, está em `docs/migracao-laravel/inventario-codigo-proprio.md` e no `.tsv` ao lado. Ele vai ser regravado sobre a nova base.

### APIs

- **`/v4`**: as 1.300 rotas são conferidas em lotes contra a linha de base do 7.4 (status, corpo e tipo de conteúdo).
- **API V1 (Silex):** 33 arquivos e 7 rotas idênticos ao que era, mas `silex/silex` saiu do composer, o Symfony está na 5.4 e o `FrontController.php` não encaminha mais `api/vN/`. No 7.4 do PR ela não responde. Ver decisões.

## Banco de dados

- As "migrações necessárias" do PR são **737 migrations Laravel** (2022-12 a 2024-12), não Phinx. Elas gravam no banco: criam a tabela de favoritos, a coluna `db_itensmenu.api` e `notifications`, inserem itens em `db_itensmenu`/`db_menu`, mexem nas funções de auditoria e na fila, e alteram `oauth_clients` (`secret` opcional, coluna `provider`).
- O `install.sh` restaura o dump sem rodar `artisan migrate`, e o dump não tem essas migrations em `public.migrations` (vai até 2022-12-27). **Sem elas, o Desktop do PR não monta o menu.**
- Uma das migrations apaga os tokens do Passport.
- PostgreSQL 16: só a instalação do zero mudou (ajuste no dump e `pos.sql`).

## Regras de trabalho

### Do grupo (`CONTRIBUINDO.md`)

1. Nunca `git add .` nem `git add -A`: arquivo por arquivo.
1. Trabalhar no WSL/Linux, não em `C:\` (107 grupos de arquivos que só diferem em maiúsculas).
1. Não salvar em UTF-8: o código é ISO-8859-1.
1. Separar mudança automática (Rector) de manual: um commit para cada.
1. Cada pessoa mexe só na sua área; arquivo de outra área, pedir ao dono.
1. `composer.json`, `composer.lock` e `vendor/` são do grupo Laravel.
1. Nunca `git push --force` nem `git reset --hard` sem avisar.
1. Pull request pequeno; com centenas de arquivos, dividir.

Fluxo: `git checkout base-php74 && git pull && git checkout -b area/assunto` → commits → `git pull origin base-php74` → pull request para `base-php74` (aceito pelo coordenador). A `base-php84` está congelada e não recebe mais trabalho.

### De método (usadas pela frente Laravel; propostas para todos)

| Regra | O que quer dizer na prática |
| --- | --- |
| **Não repetir trabalho** | Antes de começar, procure nas branches do grupo e na `base-php74` se alguém já fez. |
| **Funciona igual ao 7.4** | Se o 8.5 já se comporta exatamente como o 7.4, não se mexe. Só muda o que difere ou não roda, com prova antes e depois. |
| **O código do PR tem prioridade** | O que o PR implementou e roda no 8.5 fica como está. Ninguém troca pela versão da `base-php84` nem por uma própria. Onde o 8.5 exige mudança, mexe-se o mínimo no arquivo do PR, sem copiar arquivo inteiro de outra base. |
| **Só atualizar** | Não acrescentar função, não mudar o que o sistema faz, não "aproveitar para corrigir". Defeito encontrado (inclusive de segurança) é **registrado** e avisado ao dono da área, não corrigido na migração. |
| **O 7.4 fica intacto** | Mudança num arquivo que o 7.4 também usa só com prova de que o 7.4 continua igual (bateria antes/depois), ou então vai para algo que só o 8.5 lê. |
| **Não tocar no banco** | Testes com banco só leitura sempre que der. Telas que gravam rodam num contêiner próprio, com o vigia do banco conferindo que só gravou o que o sistema grava sozinho (log de acesso, sessão, usuários on-line, tokens). Relatórios só depois de ler o código e confirmar que não gravam. |
| **Não limpar registros de auditoria** | Gravação de auditoria feita pelo próprio sistema durante o teste fica como está. |
| **Seguir precedente** | Se o grupo já resolveu um caso igual de um jeito, siga o mesmo jeito e registre a diferença medida (ex.: `break` fora de laço virou `exit`). |
| **Regressão em área de outro** | Só documentar e avisar o dono. |
| **Commits** | Assunto começando com verbo no presente, sem acento, com números (ex.: `Troca $s{i} por $s[i] em 20 arquivos (20 linhas)`); corpo dizendo o que foi medido. O `CONTRIBUINDO.md` pede o prefixo `PHP8-NN:`, mas o histórico do grupo não usa (ver decisões). **Atualização de 19/11/2026: decidido o formato do `CONTRIBUINDO.md`, `PHP8-NN: descrição curta` (NN = número da tarefa do grupo).** |
| **Documentos autocontidos** | Cada registro em `docs/registro/` se explica sozinho, sem citar ferramentas internas nem nomes de quem fez. Falha de segurança **nunca** vai para o repositório. |

## Como provar que ficou igual

- **Sintaxe:** `php -l` no 7.4 e no 8.5 em todo arquivo mexido.
- **Telas:** a mesma requisição no 7.4 e no 8.5 e a comparação dos bytes da resposta (`scratchpad/cmp.py`, `docs/como-testamos.md`). Telas com JavaScript: navegador automático, comparando o que aparece depois do script.
- **Escrita:** nível 1 em memória (`escrita.php`); gravação real só em contêiner próprio com o vigia do banco.
- **Documentos:** PDF, planilha e Word comparados pelo conteúdo (páginas, texto, imagens), porque datas internas mudam a cada emissão.
- **APIs:** status, corpo normalizado e tipo de conteúdo, rota por rota, contra a linha de base do 7.4.
- **Integrações externas** (Pix, bancos): sempre contra dublê local, sem rede, nunca chamada real.
- **Linhas de base:** as gravadas no 5.6 viram histórico. Todas são gravadas de novo no 7.4.

## Plano em fases

### Fase 0: Ambiente da nova base

*todos · antes de qualquer porte*

- Subir 7.4 (8080), 8.5 (8085) e proxy (8090) da `base-php74` e confirmar que abrem: o commit de ferramentas não foi testado.
- Decidir o banco de referência.
- Trazer para a nova base as ferramentas que faltam: suíte única de testes (`ecidade/tests/suite/`), capturas de telas com JavaScript, documentos, token e login, vigia do banco.

### Fase 1: Linha de base do 7.4

*todos, por área*

- Gravar no 7.4 a resposta das telas de menu, documentos, rotas `/v4`, token e login.
- Essa é a régua de tudo que vem depois.

### Fase 2: PHP: compilar e rodar no 8.5

*grupos de área*

- Os 32 arquivos que não compilam.
- As quebras em tempo de execução: `each()`, `pg_lo_export`, `count()`, `create_function`.
- As mudanças silenciosas: `== ""` com a regra Rector do grupo e os construtores antigos (152 classes).
- Cada área compara as suas telas 7.4 × 8.5.

### Fase 3: Laravel 13 no 8.5

*grupo Laravel*

- Bibliotecas próprias do 8.5 (os 2 bloqueios: Pix e Pimaco).
- Inicialização e configuração; Passport 13 sobre as tabelas `oauth_*` de hoje; `/v4/login`.
- Depois: middlewares, validação, Eloquent, datas, `DB::raw`, e-mail, filas.

### Fase 4: APIs e documentos

*grupo Laravel + áreas donas das telas*

- 1.300 rotas `/v4` em lotes.
- API V1 conforme decisão.
- PDF, planilha, Word, etiquetas e QR iguais ao 7.4.
- Pix contra dublê.

### Fase 5: Entrega

*cada grupo*

- Pull requests pequenos por assunto para a `base-php74`, com o registro do que foi medido.

## Decisões em aberto

### 1. Qual banco serve de referência

O 7.4 do PR só monta o menu com as 737 migrations aplicadas, e elas gravam no banco.

**Opções:** (a) banco **descartável**, restaurado do dump de instalação, com as migrations rodando só nele; (b) a DBSeller fornece um dump já migrado; (c) seguir sem as telas que dependem das tabelas novas.

Proposta: (a), com cópia guardada antes de migrar.

### 2. API V1 (Silex)

Desligada no PR: o código ficou, a biblioteca e o roteamento saíram.

**Opções:** (a) seguir o PR e deixar desligada; (b) mantê-la num contêiner separado com as versões antigas (já existe um pronto e medido); (c) perguntar à DBSeller se foi de propósito.

Proposta: (c), seguindo (a) enquanto não houver resposta.

### 3. Formato do commit

O `CONTRIBUINDO.md` pede `PHP8-NN: …`; o histórico real do grupo usa verbo no presente, sem prefixo.

Proposta: o coordenador escolhe um e o `CONTRIBUINDO.md` passa a dizer o mesmo que o histórico.

> **Atualização de 19/11/2026 (decisão 11, tomada):** vale o formato do `CONTRIBUINDO.md`, `PHP8-NN: descrição curta`,
> com NN = número da tarefa do grupo (ex.: `PHP8-31: troca $str{i} por $str[i] em db_stdlib.php`). O histórico
> anterior fica como está. Pergunta aberta: quem distribui os números das tarefas (o documento só dá o exemplo 31).

### 4. Defeitos que o PR trouxe no Laravel 8

Tempo de cache, funções removidas e `env()` estão no 7.4, que é a referência.

Proposta: registrar, avisar a DBSeller e decidir em grupo se o 8.5 replica o defeito ou corrige.

## O que se aproveita da base antiga

A frente Laravel trabalhou sobre a `base-php84` até 17/11. Esse trabalho está todo guardado (branches `laravel/*` no fork e marcos no git) e foi reavaliado contra a nova base:

| Classe | Tarefas | O que significa |
| --- | --- | --- |
| aproveita | 12 | aplica limpo e o assunto ainda existe |
| refazer | 20 | o problema continua, mas o PR reescreveu os arquivos (ex.: inicialização e configuração do Laravel 13, Passport 13, Dotenv, documentos) |
| método | 25 | ficam as ferramentas e o jeito de medir; os números são medidos de novo no 7.4 |
| obsoleta | 5 | eram sobre a base antiga |

Dos 667 arquivos tocados, 377 aplicam limpo. Dos 290 restantes, 149 só dependem da ordem, 60 são documentos e listas, e 81 são conflitos reais. Os 4 arquivos que existem nos dois lados com conteúdo diferente são mesclados à mão: `scratchpad/cmp.py`, `docker/proxy/*`, `CLAUDE.md` e `docs/migrar-um-modulo.md`.

## Glossário

**PHP 7.4 / 8.5**: Versões da linguagem do e-Cidade. O 7.4 é a do PR e a nova referência; o 8.5 é o destino.

**Referência**: A versão que serve de gabarito: o 8.5 tem que responder igual a ela.

**Lint (`php -l`)**: Checagem de sintaxe: diz se o arquivo compila, sem rodar.

**Mudança silenciosa**: Mudança da linguagem que não dá erro, mas faz o código dar outro resultado.

**Obsoleto (deprecated)**: Recurso que ainda funciona, mas gera aviso e vai sumir numa versão futura.

**Rector**: Ferramenta que reescreve código PHP automaticamente seguindo regras. O grupo tem regras próprias em `scratchpad/rector-rules/`.

**Laravel**: O "esqueleto pronto" da parte nova do sistema (a API `/v4`): rotas, banco, login, filas.

**Passport / token / OAuth**: O Passport é a peça do Laravel que entrega o "crachá" (token) aos sistemas que usam a API, seguindo o protocolo padrão OAuth.

**API `/v4` e API V1**: Portas pelas quais outros programas conversam com o e-Cidade. A `/v4` é feita no Laravel; a V1 é a antiga, feita com o Silex.

**Composer / `vendor/` / pacote**: Pacotes são bibliotecas de terceiros. O composer é a lista que diz quais versões instalar, e `vendor/` é onde elas ficam.

**Bibliotecas próprias do 8.5**: Um segundo composer só para o 8.5, com o Laravel 13, para que o 7.4 continue com o Laravel 8 e sirva de comparação.

**Contêiner / Docker**: Uma "caixa" isolada que roda um ambiente completo (PHP, servidor web) sem misturar com o resto.

**Migration**: Roteiro que muda a estrutura do banco (cria tabela, acrescenta coluna). Rodar é escrever no banco.

**Dump**: Cópia completa de um banco num arquivo, usada para restaurar.

**Linha de base**: A "foto" de como a referência responde, usada para provar que o novo responde igual.

**Vigia do banco**: Ferramenta que conta as gravações no banco antes e depois de um teste e acusa qualquer gravação fora do esperado.

**Dublê**: Um servidor falso local que responde como o externo (banco, Pix), para testar sem chamada real.

**Branch / commit / pull request**: Branch é uma linha de trabalho separada; commit é um passo salvo; pull request é o pedido para juntar uma branch na principal.

**ISO-8859-1**: A codificação de caracteres (acentos) usada no código do e-Cidade. Salvar em UTF-8 estraga os acentos.

Medições feitas em 18/11/2026 sobre a `origin/base-php74` (PR `c2c9af06a` + ferramentas do grupo `c8775865b`): lint nos PHP 7.4 e 8.5 em contêineres descartáveis sem rede, busca de padrões no código e resolução de dependências no Composer com PHP 8.5.12. Nada foi executado no sistema nem no banco.
