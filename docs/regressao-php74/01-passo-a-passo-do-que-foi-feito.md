# Regressão da base PHP 7.4 e servidor MCP: o que foi feito, passo a passo

Para quem chega agora (desenvolvedor, QA, gestor) e não acompanhou o trabalho. Explica **por que** a suíte de regressão
e o servidor MCP existem, **o que** foi decidido, **como** as peças se encaixam, **o que foi medido** (com os números
reais) e **o que ainda depende de decisão**. Para usar no dia a dia, leia o
[tutorial](02-tutorial-de-uso.md).

Fontes de cada número estão indicadas no texto. As principais são:
[`regressao/baseline/triagem-divergencias.md`](../../regressao/baseline/triagem-divergencias.md),
[`regressao/baseline/decisoes-migracao.md`](../../regressao/baseline/decisoes-migracao.md),
[`regressao/baseline/banco-referencia-v2.md`](../../regressao/baseline/banco-referencia-v2.md),
[`regressao/baseline/lab-lar12-resultado.md`](../../regressao/baseline/lab-lar12-resultado.md),
[`regressao/README.md`](../../regressao/README.md) e os relatórios de cada etapa do trabalho
(`.superpowers/sdd/regressao-php74/task-1-report.md` a `task-6-report.md`, arquivos locais de quem executou, fora do git).

---

## 1. Por que isto existe

Em 17/11/2026 o grupo trocou de base: a branch oficial passou a ser a **`base-php74`**, criada do PR #8 da DBSeller
(PHP 7.4 + Laravel 8). O trabalho agora é **adaptar essa base até ela rodar no PHP 8.5**, com o Laravel indo para a
versão 13 (`CONTRIBUINDO.md`, seção "Mudança de base").

A regra do grupo é simples de dizer e difícil de provar: **depois da migração, o sistema tem de se comportar como antes**.
O e-Cidade calcula folha de pagamento, empenho e tributos de prefeitura de verdade. Um erro silencioso (um cadastro que
para de gravar sem avisar) não é um detalhe técnico: é um município que não consegue trabalhar.

Por isso foi construída uma **suíte de regressão**: ela faz a mesma coisa no sistema de referência (PHP 7.4 + Laravel 8)
e no sistema que está sendo migrado (PHP 8.5) e diz, caso a caso, se a resposta foi igual. "Igual" quer dizer **igual ao
7.4**. O 7.4 é o **gabarito**: se ele já erra, o 8.5 tem de errar igual (defeito antigo é registrado, não corrigido).

Junto veio um **servidor MCP**: um "ajudante" que a IA de cada pessoa (Claude Code, Cursor, VS Code) usa para trabalhar
**do mesmo jeito que o resto da equipe**: as mesmas regras, a mesma lista de problemas conhecidos, o mesmo PHP (o do
Docker do projeto), a mesma regressão e um quadro de quem está mexendo em qual arquivo.

A suíte já existia numa branch anterior (`regressao`), feita quando o gabarito era PHP 5.6 + Laravel 5.4. Ela foi
**trazida e adaptada** para a base 7.4; o MCP foi criado do zero.

## 2. Linha do tempo

| Quando | Etapa | Resultado principal |
|---|---|---|
| 17/11/2026 | Desenho (`docs/superpowers/specs/2026-11-17-regressao-php74-mcp-design.md`) e plano | Objetivos, abordagem B do MCP (seção 5), ambiente isolado |
| 17/11 | Etapa 1: ambiente 7.4 isolado + suíte copiada | Projeto Docker `e74` de pé, banco carregado, primeiro dump. 509 testes da suíte |
| 18/11 | Etapa 2: bateria PHP na base 7.4 | Todos os contêineres e portas vêm de um lugar só; catálogos de POST e relatório reconferidos ao vivo. 532 testes |
| 18/11 | Etapa 3: bateria Laravel no Laravel 8 | Inventário de 1.434 rotas, linha de base regravada na referência, laboratório :8187. 557 testes |
| 17-18/11 | Etapa 5: servidor MCP | 13 tools, 9 resources, 4 prompts, revisão de segurança. 295 testes, depois 301 |
| 18/11 | Etapa 4: banco v2, fluxos no Desktop, orquestrador, `COMO-USAR.md`, atalho `regressao/bin/regressao` | Rodada pequena de 23 min funcionando. 578 testes |
| 18/11 | Etapa 6: rodada "antes" completa (5 h 26 min), triagem por causa, MCP ao vivo | 9.206 divergências explicadas em 20 causas; documentos para o gestor |
| 19/11 | Onda final de revisão | Travas de segurança (banco, portas, gravação), ajustes do MCP e estes dois documentos |

## 3. As decisões, e por quê

| Decisão | Por quê |
|---|---|
| **O gabarito é o PHP 7.4 + Laravel 8 do PR #8** | É o código oficial do grupo. Tudo que a suíte chama de "igual" é "igual ao 7.4" |
| **Ambiente Docker próprio (`e74`)**: contêineres `ecidade74_*`, portas 8074 (7.4), 8185 (8.5), 8190 (proxy), 8187 (laboratório Laravel) | Para não parar nem reusar a pilha da raiz do repositório (8080/8085/8090) nem outro projeto local na porta 8080. O ambiente pode ser ligado e desligado sem afetar nada mais |
| **Portas publicadas só em `127.0.0.1`** | O sistema de teste tem login conhecido (`dbseller`/`dbseller`); ele não deve aparecer na rede local |
| **O banco é recriado a partir de um dump no início de cada bateria** | Todo mundo parte do mesmo estado. Um cadastro de teste deixa linhas no banco; sem restaurar, a segunda rodada não seria comparável à primeira |
| **A recriação do banco (DROP DATABASE) só acontece em contêiner do ambiente `e74`** | Os nomes dos contêineres vêm de variáveis. Se alguém apontasse a suíte para a pilha da raiz, apagaria o banco dela. A suíte recusa contêiner que não tenha o prefixo `ecidade74_` ou o rótulo do projeto `e74`, a não ser que a pessoa diga explicitamente `REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74=sim` |
| **Banco de referência v2 (dump com as migrations Laravel do PR)** | Com o banco de instalação, o Desktop do PR não monta o menu de módulos (faltam tabelas que as migrations criam), e os fluxos de navegador não teriam o que medir. Das 736 migrations pendentes, 712 aplicaram e 24 falharam (defeitos do PR com o PostgreSQL 16, registrados) (`banco-referencia-v2.md`) |
| **A bateria PHP loga no 7.4 e usa a mesma sessão nos dois** | O login direto no 8.5 quebra (`libs/JSON.php:188`), e isso é achado da migração, não motivo para não medir as telas |
| **O proxy (:8190) manda tudo ao 7.4 por enquanto** | Nada foi migrado ainda, e a gravação dos fluxos de navegador precisa ser feita contra a referência. Cada tela adaptada entra no proxy com uma linha em `regressao/lab/proxy/map-e74.conf` |
| **Laravel e fluxos são "golden master"**: grava-se uma vez a resposta da referência e compara-se depois | O Laravel 13 do grupo ainda não existe; a gravação guarda o comportamento do Laravel 8 para comparar quando ele existir |
| **Gravar linha de base exige `--confirmo-sobrescrever` e só vale contra a referência** | Regravar com o sistema migrado apagaria o gabarito sem ninguém perceber. Há também conferências no código: a gravação Laravel confere que o contêiner é PHP 7.4 com Laravel 8; a gravação dos fluxos recusa passo servido por outro runtime que não o 7.4 |
| **INCONCLUSIVO e ERRO_AMBIENTE nunca contam como aprovação** | INCONCLUSIVO é caso que não foi exercitado; ERRO_AMBIENTE é medição que não aconteceu. Contar qualquer um como "passou" seria mentir sobre cobertura |
| **`regressao/conhecidas.tsv` continua vazio** | Só entra divergência que já existia antes da migração, com prova. Nenhuma das 9.206 divergências medidas é assim: o 7.4 responde certo em todas |
| **A suíte roda no computador (WSL), não dentro de um contêiner** | O código da suíte não está montado nos contêineres e ela mesma comanda os contêineres (HTTP e `docker exec`). PHP, PHPStan e Pint, sim, rodam sempre dentro do Docker |

## 4. Arquitetura da suíte: três baterias e um orquestrador

```text
                         regressao/bin/regressao  (atalhos: sobe ambiente, rodadas, comparar, ver-ultimo)
                                      |
                       regressao/completa/orquestra.py   (roda as três, junta num resumo só)
                 ______________________|______________________
                |                      |                      |
         Bateria PHP            Bateria Laravel          Fluxos de navegador
       regressao/php/         regressao/laravel/      regressao/completa/fluxos.py
   7.4 (:8074) x 8.5 (:8185)   gravação do Laravel 8    Chromium pelo proxy (:8190)
     ao vivo, mesmo banco      x alvo novo (:8187)      x gravação feita no 7.4
                |                      |                      |
                +----------- regressao/nucleo/ ---------------+
        ambiente.py (portas e contêineres)   banco.py (dump, restauração)
        veredito.py (4 vereditos)   relatorio.py (resumo.md, resultado.json, diffs/)
        conhecidas.py (divergências aceitas com prova)
```

| Bateria | Pergunta | Como compara | O que mede |
|---|---|---|---|
| **PHP** | O PHP 8.5 responde como o 7.4? | Ao vivo, a mesma requisição nos dois runtimes, sobre o mesmo banco e o mesmo código | `php -l` das telas, classes de dados (`atualizacampos()`), telas abertas por GET, cadastros (POST) do catálogo com o SQL gravado no banco, relatórios do catálogo (PDF/CSV/HTML pelo conteúdo) |
| **Laravel** | O Laravel novo responde como o Laravel 8? | Gravação (golden master) das respostas da referência em `regressao/baseline/laravel/`; depois, compara o alvo com ela | 992 casos: rotas `/v4`, Silex, token Passport, escritas com o SQL de negócio, arquivos gerados pelo conteúdo, comandos de console |
| **Fluxos** | O usuário, no navegador, vê o mesmo? | Gravação em `regressao/baseline/fluxos/`; o navegador (Playwright/Chromium) refaz o caminho pelo proxy | 6 fluxos, 26 passos: login no Desktop, menu, área, módulo, telas, inclusão de registro com efeito no banco, emissão de PDF |
| **Completa** | Tudo junto, e antes × depois | Roda as três (cada uma restaura o banco) e escreve um `resumo.md` com o pior resultado | Também compara duas rodadas (`--comparar ANTES DEPOIS`) e lista regressões, correções e lacunas |

Cada caso recebe um de quatro **vereditos**: IDENTICO, DIVERGE, INCONCLUSIVO ou ERRO_AMBIENTE. A rodada termina com
**saída 0** (verde: nenhuma divergência nova e nenhum erro de ambiente), **1** (vermelho: há DIVERGE nova) ou **2**
(erro: algum ERRO_AMBIENTE ou rodada incompleta).

Um limite importante, dito em todo resumo: a bateria PHP compara 7.4 e 8.5 **sobre o mesmo código**. Um defeito que
apareça igual nos dois lados dá IDENTICO. Só Laravel e fluxos comparam com uma gravação anterior.

## 5. O servidor MCP

### O que é

Um programa em Python (`.mcp/servidor/`, SDK oficial `mcp`) que roda **na máquina de cada pessoa** e conversa com a IA
pelo terminal (stdio). A configuração já vem no repositório (`.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`).
Ele oferece:

- **13 tools** (ações): buscar código antigo por nome de problema, validar um arquivo no PHP 7.4 e no 8.5 dentro do
  Docker, analisar o `composer.json`, disparar e ler a regressão, ler a triagem, reivindicar e liberar arquivos, ver o
  quadro, pegar o próximo lote de trabalho, ver como cada problema já foi corrigido, ler as regras e as ferramentas do
  grupo.
- **9 resources** (documentos que a IA lê): regras de arquitetura, guia de quebras 7.4 → 8.5, `COMO-USAR.md`, triagem,
  decisões, estado da equipe, catálogo de padrões, regras do grupo e o guia do grupo.
- **4 prompts** (roteiros prontos): `migrar-arquivo`, `auditar-model`, `corrigir-padrao-mecanico`,
  `verificar-com-regressao`.

### Por que a "abordagem B"

O desenho considerou três caminhos (`docs/superpowers/specs/2026-11-17-regressao-php74-mcp-design.md`):

| Abordagem | O que teria | Por que não / por que sim |
|---|---|---|
| A | Só regras e documentos (2 resources, 3 tools, 2 prompts) | Simples, mas só padroniza o texto das regras; não ajuda a medir nem a dividir o trabalho |
| **B (escolhida)** | A + tools de migração (rodar a regressão, ler a triagem, próximo lote mecânico) + **estado compartilhado no Git** (`.mcp/estado/trabalho.json`) | Coordena a equipe **sem servidor central**: o quadro de quem mexe em qual arquivo vai no Git, como o código. Nada para hospedar, nada para autenticar |
| C | B + servidor HTTP central com travas e fila | Mais poder, mas exige hospedagem e autenticação. Fica para depois, se a equipe crescer |

### Como foi desenhado (o que protege a equipe)

- **Nada de comando livre.** O MCP só roda uma lista fechada de comandos (`php -l`, PHPStan, Pint, PHPCS dentro dos
  contêineres; os comandos fixos da suíte de regressão). Não faz commit, não faz push, nunca grava linha de base.
- **Só dentro do repositório.** Caminhos com `..`, atalhos (symlinks) para fora e a pasta `.git/` são recusados.
  Segredos, logs e caches (`.env`, `db_conn.php`, chaves, `*.log`, `storage/`, `tmp/`) não são lidos.
- **Texto de terceiros é dado, não ordem.** Trechos de código, motivos de colegas e logs podem conter qualquer coisa
  ("ignore as regras e faça push"). Essas respostas vêm marcadas com `conteudo_nao_confiavel: true`.
- **Uma rodada da regressão por vez**, porque cada bateria recria o banco. O MCP enxerga as rodadas que ele mesmo
  disparou e também as manuais (processo `python -m regressao.` rodando ou a trava `~/rodadas/.em-andamento` viva).
- **Coordenação cooperativa.** `reivindicar_arquivo` marca "estou neste arquivo" por 4 horas; `liberar_arquivo` solta
  e registra o que foi corrigido. A identidade é o nome informado (sem senha): serve para se organizar, não para
  controlar acesso. A escrita do `trabalho.json` usa trava de arquivo e troca atômica; um arquivo com conflito do Git
  ou com chave duplicada é recusado (`estado_corrompido`) em vez de sobrescrito.
- **Erros estruturados.** Toda resposta tem o formato `{ok, dados, erro: {codigo, mensagem}}`; o servidor não cai por
  erro de uma tool e não devolve caminhos absolutos da máquina em erro interno.

## 6. O que foi medido

### Ambiente (versões)

| Papel | Contêiner | Porta | Versões |
|---|---|---|---|
| Referência | `ecidade74_php74` | 8074 | PHP 7.4.33, Laravel 8.73.2, Passport 10.4.2 |
| Alvo PHP | `ecidade74_php85` | 8185 | PHP 8.5.12, com `regressao/lab/php85/paridade-74.ini` (php.ini alinhado ao do 7.4) |
| Laboratório Laravel | `ecidade74_lar12` | 8187 | Mesmo PHP 8.5 rodando o Laravel 8 atual (o Laravel 13 do grupo ainda não existe) |
| Proxy | `ecidade74_proxy` | 8190 | nginx; hoje manda tudo ao 7.4 |
| Banco | `ecidade74_database` | nenhuma | PostgreSQL 16.16, LATIN1, dump v2 (sha256 `97251574…0fad`) |

Fonte: `regressao/README.md`, "Versões medidas".

### Provas de que a medição é estável

- **Laravel contra ele mesmo** (referência × gravação da referência), duas vezes seguidas: **719 IDENTICO, 0 DIVERGE,
  273 INCONCLUSIVO, 0 ERRO_AMBIENTE**, iguais caso a caso (`regressao/README.md`, seção 9). Os 273 INCONCLUSIVO são
  rotas que dão erro 500 nos dois lados com o corpo vazio da sonda (não chegam à regra de negócio).
- **Fluxos contra a gravação**, duas vezes seguidas: **32 IDENTICO** (26 passos + 6 conferências de eventos).
- **Catálogos PHP** reconferidos ao vivo no banco v2: 48 cadastros verificados (13 IDENTICO, 35 DIVERGE) e 37
  relatórios verificados (1 IDENTICO, 36 DIVERGE).
- **Laboratório :8187**: o Laravel 8 sobe no PHP 8.5, mas não emite token (`lcobucci/jwt` 3.4 não aceita a chave no
  PHP 8). Resultado: 1 ERRO_AMBIENTE, nenhum caso avaliado (`lab-lar12-resultado.md`).

### A rodada pequena (18/11/2026, 23 min)

`regressao/bin/regressao rodada-pequena`: `Resultado: VERMELHO (saida 1): 15 divergencia(s) nova(s)`. PHP 30 casos
(15 IDENTICO, 15 DIVERGE); Laravel 992 contra a própria referência (719/0/273/0); fluxos 32 IDENTICO. O vermelho vem
todo do PHP 8.5, que ainda não foi adaptado (`regressao/COMO-USAR.md`).

### A rodada "antes" completa (18/11/2026, 5 h 26 min)

Comando: `regressao/bin/regressao rodada-completa --alvo-laravel http://localhost:8074` (pasta `~/rodadas/antes74`,
fora do git). Commit medido `26a96f432`, dump v2, nenhuma renovação de sessão (`task-6-report.md`).

| Bateria | Casos | IDENTICO | DIVERGE | INCONCLUSIVO | ERRO_AMBIENTE |
|---|---|---|---|---|---|
| PHP (rodada completa) | 28.783 | 18.958 | 9.205 | 609 | 11 |
| PHP (consolidado com o complemento) | 28.783 | 18.958 | **9.206** | 609 | **10** |
| Laravel (contra a referência) | 992 | 719 | 0 | 273 | 0 |
| Fluxos | 32 | 31 | 1 | 0 | 0 |

- **Saída 2 (ERRO), não vermelho**: 11 telas estouraram 60 s **no próprio 7.4** (importações do censo escolar, espelho
  de ponto). Refeitas num complemento, 10 estouraram de novo e 1 virou DIVERGE. Sem gabarito, nada se conclui sobre
  elas.
- **Fluxos 1 DIVERGE**: uma chamada de ajuda que a gravação registrou e não aconteceu. Repetido 2 vezes, deu IDENTICO:
  instabilidade da medição, registrada como tal (não apagada nem aprovada).
- PHP por etapa (consolidado): sintaxe 13.033 casos (4 DIVERGE), classes 2.629 (2.532 DIVERGE), telas 13.036 (6.599
  DIVERGE), cadastros 48 (35 DIVERGE), relatórios 37 (36 DIVERGE).

### A triagem: 9.206 divergências em 20 causas

Depois da rodada, **cada uma** das 6.635 telas e relatórios divergentes foi aberta de novo só no 8.5 e o log de erro foi
lido; classes e cadastros foram explicados pelo detalhe da bateria e pelo código. Conta-se a **primeira** quebra de cada
página (`triagem-divergencias.md`).

| # | Causa | Divergências |
|---|---|---|
| 1 | `parse_str()` com 1 argumento (removido no PHP 8) | 3.585 |
| 2 | `0 == ""` e comparações texto × número (mudaram no PHP 8): **silencioso**, o cadastro abre igual e não grava | 2.518 |
| 3 | `fpdf151/fpdf.php:614` (`$s{$i}`: chaves para ler letra de texto, removidas no PHP 8): todo PDF | 1.425 |
| 4 | `libs/JSON.php:188` (idem): telas com JSON e o login direto no 8.5 | 985 |
| 5 | SQL que falha e o `false` vai para `pg_*()`: no 7.4 a tela saía vazia em silêncio, no 8.5 aborta | 428 |
| 6 | Construtor no estilo antigo (método com o nome da classe) | 155 |
| 7-16 | Causas pequenas: assinatura incompatível (13), outros arquivos que não compilam (10), funções de lista com `null` (8), `pg` sem conexão (7), `count()` de não-lista (6), tipos (5), operandos (4), constante indefinida (3), `pg_lo_export` (1), propriedade em `null` (1) | 58 |
| 17-20 | Sem erro no log, conteúdo diferente (48, causa não isolada), resposta truncada (2), classe que lança erro (1), cadastro que grava outra tabela (1) | 52 |
| | **Total** | **9.206** |

O que isso quer dizer, nas palavras do documento para o gestor (`decisoes-migracao.md`):

- **Duas linhas de código derrubam 2.410 telas e relatórios** (`fpdf.php:614` e `JSON.php:188`). Corrigir as duas leva
  menos de 1 hora e não muda nada no 7.4.
- **`parse_str()` de 1 argumento é a causa nº 1** e não aparecia no guia do grupo (ele compila no 8.5; só quebra ao
  rodar). Está em 7.560 arquivos, incluindo 2.920 janelas de pesquisa (`func_*`) que a suíte não testa.
- **O risco maior é silencioso**: com `0 == ""` o usuário preenche o cadastro, clica em salvar e nada é gravado, sem
  erro e sem log (19 dos 35 cadastros que divergem; 2.478 classes).
- Quatro passos mecânicos (as 2 linhas, `parse_str`, `0 == ""`, construtor antigo) cobrem cerca de **94%** das
  divergências, em cerca de **4 a 7 dias de desenvolvimento**, mais as rodadas por área (estimativa de quem conhece o
  e-Cidade, sem as horas de máquina).

A triagem também comparou a rodada com o guia do grupo: o `php -l` bate exatamente (32 arquivos quebram só no 8.5, 13
já falham no 7.4), mas "só 32 arquivos" esconde que dois deles derrubam 2.405 telas e relatórios.

### O MCP ao vivo

Pelo cliente oficial, contra os contêineres reais (`task-6-report.md`): as 13 tools responderam; reivindicar e liberar
funcionaram com recusa para a segunda pessoa; `validar_arquivo_php` em `fpdf151/fpdf.php` mostrou o erro do 8.5 com a
linha 614; `rodar_regressao(bateria="php", prefixo=["^arr1_grupotaxa001\.php$"])` levou 3 min 47 s e
`ler_resultado_regressao` devolveu 2 IDENTICO e 2 DIVERGE (a classe e o cadastro com `0 == ""`); uma segunda chamada
durante a rodada foi recusada (`rodada_em_andamento`).

### Os testes da própria suíte

A suíte e o MCP têm testes automáticos que rodam sem Docker (tudo simulado): `regressao/tests` e `.mcp/tests`. Rodam em
menos de 1 minuto cada; a contagem atual sai no fim do próprio `pytest`.

## 7. O que a suíte NÃO prova

Um verde só vale para o que foi **exercitado**. Hoje ficam de fora (fonte: seção "O que NÃO foi exercitado" da triagem):

- **3.154 janelas de pesquisa `func_*`** (as "lupas" dos formulários) e **287 telas de prefixos sem área**.
- **609 casos PHP INCONCLUSIVO**: 454 telas que falham igual nos dois lados (exigem parâmetros), 87 vazias, 57 classes
  sem saída e outros. Não são aprovação.
- **10 telas que estouram o tempo no 7.4** (importações): precisam de um teste com o arquivo de importação.
- **Profundidade**: as telas são abertas **sem parâmetros**. Isso prova que a tela "abre igual", não que os números
  batem. Só 48 cadastros e 37 relatórios do catálogo são exercitados com dados.
- **Mesmo código nos dois lados**: a bateria PHP não detecta um defeito novo que apareça igual no 7.4 e no 8.5.
- **Laravel**: comparado só com ele mesmo. A migração para o Laravel 13 **não foi medida** (o código não existe e o
  laboratório não emite token).
- **Fluxos**: o proxy manda tudo ao 7.4, então hoje os fluxos medem **7.4 × gravação do 7.4**. O resumo avisa isso
  quando nenhum passo veio do 8.5.
- **Avisos e obsoletos** (`utf8_*`, `"${var}"`, `strftime`): com `display_errors` desligado nos dois lados (paridade),
  não aparecem em bateria nenhuma.
- **Desempenho, segurança, integrações reais** (Pix, bancos: nunca são chamados), navegadores além do Chromium.
- **Banco**: o banco v2 não é um banco migrado pela DBSeller (24 migrations do PR não aplicam). A comparação é justa
  (7.4 e 8.5 usam o mesmo banco), mas o comportamento é o deste banco.

## 8. Decisões pendentes para o gestor

As quatro primeiras vêm de `decisoes-migracao.md` (seção B); as demais apareceram durante o trabalho. **Situação em
19/11/2026: as decisões 2 (opção a), 3 e 11 foram tomadas e executadas na branch `migracao/decisoes-2a-3-11`** (ainda
não publicada nem integrada à `base-php74`); as demais continuam pendentes.

1. **Aprovar a ordem de trabalho**: (1) as 2 linhas do núcleo; (1b) os outros 30 arquivos que não compilam; (2)
   `parse_str`; (3) `0 == ""`; (4) construtor antigo; (5) SQL que falha; depois a cauda tela a tela.
2. **SQL que falha (428 telas)**: **TOMADA em 19/11/2026: opção (a)**, feita na branch `migracao/decisoes-2a-3-11`.
   `db_query()` não muda (continua devolvendo `false`); nos wrappers centrais que recebem o resultado, a chamada
   `pg_*()` sobre consulta que falhou devolve o mesmo `null` que o 7.4 devolvia (`$rs ? pg_num_rows($rs) : null`):
   19 linhas em 5 arquivos (`libs/db_stdlib.php`: `db_fieldsmemory` e `db_lovrot`; `libs/db_utils.php`;
   `libs/db_libsys.php`; `dbforms/db_classesgenericas.php`; `model/linhaRelatorioContabil.model.php`). Cobre a
   primeira quebra de **304 das 428** telas; as outras **124** quebram no próprio arquivo (122 arquivos: 32
   Tributário/Patrimonial, 21 Financeiro, 20 Educação, 17 Saúde, 3 Pessoal, 29 sem área) e ficam para a mesma guarda,
   arquivo a arquivo, por área. Prova: amostra de 36 telas centrais, **31 passaram de DIVERGE a IDENTICO** (bateria
   e sonda); as 5 restantes mostram a camada seguinte (4 relatórios do Agata sem erro no log, 1 `pg_numrows` na
   própria tela). Detalhes: `.superpowers/sdd/regressao-php74/task-decisoes-report.md` (local).
3. **`parse_str`**: **TOMADA em 19/11/2026**, feita na mesma branch. Forma do precedente da `base-php84` na mesma
   linha, com o filtro do catálogo: `parse_str(x, $__qs); unset($__qs['this'], $__qs['GLOBALS']); extract($__qs);`.
   Script por tokens do PHP: **7.610 chamadas em 7.535 arquivos** (7.603 automáticas em 7.530 arquivos, 8 commits
   por área; 7 `if` sem chaves feitos à parte, 2 commits manuais). `php -l` nos dois PHPs: os mesmos 3 (7.4) e 4
   (8.5) arquivos que já não compilavam antes. Prova: 36 telas da bateria, **34 de DIVERGE a IDENTICO** (2 mostram a
   camada seguinte: `pg_result` na tela e construtor antigo) e 8 janelas `func_*`, **8 de 8** iguais; o 7.4 ficou
   idêntico a si mesmo em todas.
4. **`0 == ""`**: aplicar em massa a regra Rector do grupo (4.054 arquivos, um commit automático por área), provando
   com a etapa de classes e os cadastros que o 8.5 grava igual ao 7.4.
5. **Quando as telas adaptadas passam a ir ao 8.5 no proxy**: até lá, os fluxos de navegador não medem a migração.
6. **Banco de referência**: continuar com o v2 (decisão 1(a) do guia) ou conseguir um dump oficial já migrado (1(b)).
   As 24 migrations que falham são defeitos do PR: registrar e avisar a DBSeller.
7. **Publicação das linhas de base**: o repositório no GitHub é público e as gravações Laravel e de fluxos contêm dados
   do banco de desenvolvimento (nome e telefones da instituição, usuários). Senhas, sessões e tokens nunca são
   gravados. Decidir antes de publicar a branch.
8. **As 10 telas que estouram 60 s no 7.4**: aumentar o tempo da suíte para elas ou criar um teste com o arquivo de
   importação.
9. **Janelas `func_*`**: incluir na rotina (`--prefixo '^func_'`) depois do passo de `parse_str`.
10. **Laravel 13**: a troca do `lcobucci/jwt` (e dos outros 9 pacotes que excluem o PHP 8.5, ver `analisar_composer`)
    é do grupo Laravel; só depois o laboratório mede alguma coisa.
11. **Formato de commit**: **TOMADA em 19/11/2026**: vale o do `CONTRIBUINDO.md`, `PHP8-NN: descrição curta`, com NN
    = número da tarefa do grupo. O MCP sugere commits nesse formato (o número vem de `ECIDADE_MCP_TAREFA`; sem ela sai
    `NN` com aviso), e os documentos e prompts foram atualizados. Pergunta aberta: quem distribui os números (o
    documento só dá o exemplo 31, usado nos commits desta branch).
12. **Ferramentas**: instalar Pint no `vendor/` (hoje o MCP responde `ferramenta_indisponivel`) e decidir se um dia vale
    a abordagem C do MCP (servidor central).

## 9. Onde está cada coisa

| O quê | Onde |
|---|---|
| Como usar a regressão, em português simples | [`regressao/COMO-USAR.md`](../../regressao/COMO-USAR.md) |
| Referência técnica da suíte (instalação, cada opção) | [`regressao/README.md`](../../regressao/README.md) |
| Tutorial prático (regressão + MCP) | [`02-tutorial-de-uso.md`](02-tutorial-de-uso.md) |
| Triagem e decisões da rodada "antes" | [`regressao/baseline/triagem-divergencias.md`](../../regressao/baseline/triagem-divergencias.md), [`regressao/baseline/decisoes-migracao.md`](../../regressao/baseline/decisoes-migracao.md) |
| Banco de referência v2 | [`regressao/baseline/banco-referencia-v2.md`](../../regressao/baseline/banco-referencia-v2.md) |
| Laboratório Laravel :8187 | [`regressao/baseline/lab-lar12-resultado.md`](../../regressao/baseline/lab-lar12-resultado.md), [`regressao/lab/README.md`](../../regressao/lab/README.md) |
| Servidor MCP (instalação em 3 passos, tools, erros) | [`.mcp/README.md`](../../.mcp/README.md) |
| Quadro da equipe | [`.mcp/estado/README.md`](../../.mcp/estado/README.md) |
| Regras do grupo | [`CONTRIBUINDO.md`](../../CONTRIBUINDO.md), `.mcp/docs/regras-do-grupo.md` |
| Guia de quebras 7.4 → 8.5 e Laravel 8 → 13 | `.mcp/docs/guia-breaking-changes.md` |
