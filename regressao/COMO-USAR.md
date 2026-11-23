# Como usar a suíte de regressão

Para quem vai rodar ou ler a regressão sem ter participado do projeto: desenvolvedor, QA ou gestor. O detalhe técnico
(cada bateria, cada opção) está em [`regressao/README.md`](README.md); aqui está o necessário para usar e entender.
O histórico e as decisões estão em [`docs/regressao-php74/01-passo-a-passo-do-que-foi-feito.md`](../docs/regressao-php74/01-passo-a-passo-do-que-foi-feito.md);
um tutorial passo a passo (regressão + MCP), em [`docs/regressao-php74/02-tutorial-de-uso.md`](../docs/regressao-php74/02-tutorial-de-uso.md).

## Em uma frase

A suíte faz a **mesma coisa** no e-Cidade de referência (**PHP 7.4 + Laravel 8**, o código do PR #8 da DBSeller, a
`base-php74` do grupo) e no e-Cidade que está sendo migrado (**PHP 8.5**) e diz, caso a caso, se a resposta foi
igual. "Igual" quer dizer **igual ao 7.4**: ele é o gabarito.

## O que ela prova e o que NÃO prova

| Prova | NÃO prova |
|---|---|
| Que as telas, os cadastros (POST), os relatórios e as rotas `/v4` que ela exercita respondem no 8.5 como no 7.4 | Que o sistema inteiro funciona: só vale o que foi **exercitado** (a seção *Cobertura* do relatório diz quanto) |
| Que um defeito novo apareceu (DIVERGE), com o diff para investigar | Que o 7.4 está certo: se o 7.4 já erra, o 8.5 tem de errar igual (defeito do PR é **registrado**, não corrigido) |
| Que o usuário, no navegador, vê o mesmo nos 6 caminhos gravados (login, menu, cadastro, relatório) | Regressão num código usado igual pelos dois lados: a bateria PHP compara 7.4 × 8.5 **sobre o mesmo código**; um erro comum aos dois dá IDENTICO (só Laravel e fluxos comparam com uma gravação anterior) |
| Que o banco recebeu as mesmas gravações (SQL de negócio) nos POSTs do catálogo | Desempenho, segurança, integrações reais (Pix, bancos: nunca são chamadas), navegadores além do Chromium |

Um caso **INCONCLUSIVO** ou **ERRO_AMBIENTE** nunca é aprovação. Leia "Os quatro vereditos" abaixo.

## Pré-requisitos

- **Windows com WSL (Ubuntu 24.04)** ou Linux. O repositório fica **dentro do WSL** (ex.: `~/e-cidade`), nunca em
  `C:\`: há arquivos que só diferem em maiúsculas e o Windows não guarda os dois (regra 2 do `CONTRIBUINDO.md`).
- **Docker Desktop** com a integração do WSL ligada (ou Docker Engine no Linux), Compose v2.
- **Memória:** os contêineres usam pouco parados (~0,5 GB), mas a restauração do banco, o PHP sob carga e o navegador
  dos fluxos somam alguns GB e o cache de arquivos do WSL cresce; numa máquina de 16 GB, o Docker já caiu por falta de
  memória: feche o que puder antes de uma rodada longa (veja "Problemas comuns"). **Disco:** ~10 GB (imagens, banco de
  ~1 GB, Chromium, rodadas).
- **Python 3.12** (`sudo apt install python3.12-venv`).
- O arquivo **`regressao/baseline/baseline.dump`** (o banco de partida, ~90 MB). Ele não vai para o git: peça a
  cópia ao time (o `sha256sum` dele tem de bater com `regressao/baseline/baseline.dump.sha256`).

### Preparar uma vez

```bash
python3 -m venv regressao/.venv
regressao/.venv/bin/pip install -r regressao/requirements.txt
regressao/.venv/bin/python -m playwright install chromium     # navegador dos fluxos (~700 MB)
regressao/.venv/bin/python -m pytest regressao/tests -q       # testes da própria suíte (sem Docker, ~30 s)
```

A instalação do ambiente (imagens, banco, arquivos locais do e-Cidade) está passo a passo em
[`README.md`, seção 1](README.md#1-pré-requisitos). É feita uma vez; depois só se sobe e desce.

## Rodar em 3 comandos

Sempre da raiz do repositório, no WSL:

```bash
regressao/bin/regressao ambiente-sobe      # 1. sobe 7.4 (:8074), 8.5 (:8185), proxy (:8190), laboratório (:8187) e banco
regressao/bin/regressao rodada-pequena     # 2. ~25 min, em segundo plano: confere que tudo funciona
regressao/bin/regressao ver-ultimo         #    andamento; quando acabar, mostra o resumo
regressao/bin/regressao rodada-completa    # 3. a rodada de verdade: HORAS (todas as telas), em segundo plano
```

- `rodada-pequena` mede 3 grupos de telas PHP (cadastros da Arrecadação, Cemitério e dois relatórios), a bateria
  Laravel inteira **contra a própria referência** (prova de que a medição é estável) e os 6 fluxos de navegador.
- `rodada-completa` mede todas as telas PHP e compara o Laravel com o laboratório do 8.5 (`--alvo-laravel URL` troca o
  alvo). Aceita as opções do orquestrador, por exemplo `regressao/bin/regressao rodada-completa --area tributario`.
- `regressao/bin/regressao comparar ANTES DEPOIS` compara duas rodadas (ex.: antes e depois de uma correção).
- `regressao/bin/regressao ambiente-para` para só os contêineres da regressão (`ecidade74_*`); nada é apagado.

As rodadas ficam em `~/rodadas/<data>-<tipo>/` (troque com `REGRESSAO_RODADAS`). Só uma rodada por vez: cada
bateria **recria o banco** a partir do dump no início.

Sem o atalho, o comando equivalente é
`regressao/.venv/bin/python -m regressao.completa.orquestra --saida DIR [--prefixo RX ...] [--alvo-laravel URL]`.

## Como ler o resultado

Cada rodada tem `resumo.md` (e uma cópia idêntica, `relatorio.md`) e as pastas `php/`, `laravel/` e `fluxos/`, cada uma
com o próprio `resumo.md`, `resultado.json` e `diffs/`.

1. **Primeira linha — `Resultado:`** `VERDE (saída 0)`, `VERMELHO (saída 1)` ou `ERRO (saída 2)`.
2. **AVISOS** — leia sempre. Dizem que a referência é o 7.4, que INCONCLUSIVO não é aprovação, o limite da bateria PHP
   (mesmo código nos dois lados), quando o Laravel foi comparado com ele mesmo, quando nenhum passo dos fluxos veio do
   8.5 (`FLUXOS 7.4 x 7.4`: o proxy mandou tudo ao 7.4, os fluxos não mediram a migração) e cada ERRO_AMBIENTE.
3. **Totais por bateria** — quantos casos deram cada veredito, por bateria, e o tempo.
4. **Cobertura** — o que foi exercitado: telas selecionadas, POSTs e relatórios do catálogo, rotas Laravel cobertas ×
   não cobertas, passos de fluxo. Um verde com pouca cobertura vale pouco.
5. **INCONCLUSIVO por motivo** — por que cada grupo não foi verificado.
6. **Divergências novas / conhecidas** e **ERRO_AMBIENTE** — a lista do que olhar. O diff de cada divergência está em
   `<bateria>/diffs/`.

Exemplo real (rodada pequena de 18/11/2026, 23 min): `Resultado: VERMELHO (saida 1): 15 divergencia(s) nova(s)`.
PHP 30 casos: 15 IDENTICO, 15 DIVERGE (classes com `0 == ""`, `cem1_cemiterio003` com `parse_str`, 2 PDFs que dão 500
no 8.5, 2 cadastros que o 8.5 não grava). Laravel 992 casos contra a própria referência: 719 IDENTICO, 273 INCONCLUSIVO,
0 DIVERGE (a medição é estável). Fluxos: 32 IDENTICO (o proxy ainda manda tudo ao 7.4). Ou seja: o vermelho vem todo do
PHP 8.5, que ainda não foi adaptado.

### Exemplo: a rodada "antes" completa (18/11/2026, 5 h 26 min)

`regressao/bin/regressao rodada-completa --alvo-laravel http://localhost:8074` (`~/rodadas/antes74`). O começo do
`resumo.md`:

```text
Resultado: ERRO (saida 2): a rodada nao pode ser concluida (ERRO_AMBIENTE ou sub-rodada nao comparavel); ...
- ERRO_AMBIENTE php:tela:rec2_espelhoponto002.php: timeout: ref=000  85=500 (apos 1 retentativa)
  ... (11 telas)
| bateria | casos | IDENTICO | DIVERGE | INCONCLUSIVO | ERRO_AMBIENTE | novas | conhecidas | saida | tempo (s) |
| php     | 28783 | 18958    | 9205    | 609          | 11            | 9205  | 0          | 2     | 18273.4   |
| laravel | 992   | 719      | 0       | 273          | 0             | 0     | 0          | 0     | 988.0     |
| fluxos  | 32    | 31       | 1       | 0            | 0             | 1     | 0          | 1     | 293.1     |
```

Como ler:

- **ERRO (saída 2)**, não VERMELHO: 11 telas estouraram 60 s **na referência 7.4** (importações do censo, espelho de
  ponto). Sem gabarito nada se conclui sobre elas; refeitas num complemento (`--prefixo` só com elas e
  `--pular sintaxe --pular classes`), 10 estouraram de novo e 1 virou DIVERGE. Elas continuam ERRO_AMBIENTE: não se
  "aprova" uma tela porque o 7.4 é lento.
- **PHP 9.205 DIVERGE** é o retrato da base 7.4 no 8.5: 3 causas mecânicas explicam 90% das telas (`parse_str` de
  1 argumento, `fpdf151/fpdf.php:614` e `libs/JSON.php:188`). A causa de cada uma está em
  [`baseline/triagem-divergencias.md`](baseline/triagem-divergencias.md); o que fazer primeiro, em
  [`baseline/decisoes-migracao.md`](baseline/decisoes-migracao.md).
- **Laravel 719/0/273** com `ALVO LARAVEL = REFERENCIA` no aviso: prova que a medição é estável, não mede migração.
- **Fluxos 1 DIVERGE**: um pedido de ajuda que a gravação registrou e não aconteceu (proxy → 7.4 nos dois). Repetido
  2 vezes, deu IDENTICO: é instabilidade da medição. Registre assim; não apague nem "aprove".
- Juntar a completa e os complementos num painel (`~/rodadas/antes74-consolidado.md`) é leitura, não aprovação:
  o veredito do complemento só substitui o do mesmo caso.

## Os quatro vereditos (com exemplos reais deste projeto)

| Veredito | Quer dizer | Exemplo real (base 7.4 × 8.5, novembro/2026) |
|---|---|---|
| **IDENTICO** | Os dois lados responderam igual (depois de tirar o que muda sozinho: datas, horas, ids de sessão) | A tela `arr1_grupotaxa001.php` abre igual no 7.4 e no 8.5; as 9 telas da amostra compilam nos dois (`php -l`) |
| **DIVERGE** | Respostas diferentes: **achado** da migração, com diff | `cem1_cemiterio003.php`: 7.4 responde 200, 8.5 responde 500 (`parse_str()` com 1 argumento, removido no PHP 8). Relatórios em PDF: 7.4 gera o PDF, 8.5 dá 500 (`fpdf151/fpdf.php:614`, `$s{i}`). POST de `arr1_grupotaxa001`: o 7.4 grava, o 8.5 não grava nada (`0 == ""` mudou no PHP 8) |
| **INCONCLUSIVO** | O caso **não foi exercitado**. Não é aprovação nem reprovação: é lacuna | 272 casos Laravel dão erro 500 **nos dois lados** com o corpo vazio da sonda (não chegam à regra de negócio); POSTs do catálogo em que a referência não grava nada (`pes1_pensao001`); um passo de fluxo que não rodou porque o anterior falhou |
| **ERRO_AMBIENTE** | A medição não pôde ser feita. Nada se conclui | O laboratório Laravel no 8.5 (:8187) não emite token (`lcobucci/jwt` 3.4 não aceita a chave no PHP 8): toda a bateria Laravel nele vira um `laravel:banco`. Também: contêiner parado, banco/dump diferente do registrado, proxy fora |

Divergência já conhecida e aceita (com prova) vai para `regressao/conhecidas.tsv` e aparece separada, sem deixar a
rodada vermelha.

## Quando é verde e quando é vermelho

| Saída | Resultado | O que fazer |
|---|---|---|
| **0** | VERDE: nenhuma divergência nova e nenhum erro de ambiente | Ainda assim leia **Cobertura** e **INCONCLUSIVO**: verde só vale para o que foi exercitado |
| **1** | VERMELHO: há DIVERGE que não está em `conhecidas.tsv` | Abra o diff; é defeito do 8.5 (corrigir no mínimo, regra do grupo) ou diferença esperada (registrar com prova) |
| **2** | ERRO: algum ERRO_AMBIENTE ou rodada incompleta | Corrija o ambiente (ver "Problemas comuns") e rode de novo. **Não** conclua nada |

Na rodada completa vale o **pior** das três baterias. **Hoje a rodada é vermelha**, e isso é esperado: o código da
`base-php74` ainda não foi adaptado ao 8.5 (relatórios em PDF, `parse_str`, `0 == ""`...). O trabalho do grupo é fazer
essas divergências sumirem uma a uma, sem criar outras.

### Antes e depois de uma correção

```bash
regressao/bin/regressao rodada-pequena          # ANTES (ou use uma rodada que já existe)
# ... aplica a correção ...
regressao/bin/regressao rodada-pequena          # DEPOIS (mesmos prefixos)
regressao/bin/regressao comparar ~/rodadas/<antes> ~/rodadas/<depois>
```

O `comparacao.md` lista **Regressões** (algo que era IDENTICO/INCONCLUSIVO e virou DIVERGE/ERRO, ou que deixou de ser
verificado), **Correções** (DIVERGE → IDENTICO), casos novos/removidos e **Lacunas** (DIVERGE → INCONCLUSIVO: saiu do
vermelho sem ser verificado, **não** é correção). Para valer a comparação, as duas rodadas precisam medir a mesma coisa
(mesmos prefixos/áreas).

## Perguntas frequentes

**A rodada demora horas. Preciso esperar?** Não: os atalhos rodam em segundo plano (a completa levou 5 h 26 min em
18/11/2026: PHP 5 h 05, Laravel 16 min, fluxos 5 min). `ver-ultimo` mostra o andamento.
Para o dia a dia use `--prefixo`/`--area` (só as telas da sua área) ou a `rodada-pequena`.

**Por que o banco é recriado em cada bateria?** Para todo mundo partir do mesmo estado: um cadastro de teste deixa
linhas no banco. Cada bateria restaura o dump (~4 min). Nunca rode duas rodadas ao mesmo tempo.

**A suíte grava no banco de alguém?** Não. O banco é o contêiner `ecidade74_database`, só da regressão, recriado a cada
bateria; a restauração recusa contêiner de fora do ambiente `e74` (veja "Usar com a pilha do grupo"). Nenhum serviço
externo é chamado.

**Por que o login do 8.5 não é usado?** O login direto no 8.5 ainda quebra (`abrir.php`, achado da migração). A bateria
loga no 7.4 e usa a mesma sessão nos dois (as sessões são compartilhadas). Quando o login do 8.5 for corrigido, a
bateria continua igual.

**O que é o "laboratório" :8187?** O Laravel 13 do grupo (alvo da migração) ainda não existe. O laboratório roda o
Laravel 8 da base no PHP 8.5 e mostra o que quebra (hoje: o token). Quando houver o código do Laravel 13, ele entra por
`LAR12_CODIGO` (ver [`lab/README.md`](lab/README.md)).

**Por que o banco de referência tem as "migrations"?** O sistema do PR só monta o menu do Desktop com as migrations
Laravel do PR aplicadas no banco (decisão 1(a) do guia do grupo: banco descartável, migrations rodadas só nele). O dump
da regressão já vem assim (versão 2; ver [`README.md`, seção 2](README.md#2-a-baseline-do-banco-o-dump)).

**Posso usar com a pilha do grupo (o `docker-compose.yml` da raiz)?** Veja a seção abaixo.

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ambiente-sobe` falha com "port is already allocated" | Outro serviço usa 8074/8185/8187/8190 | `docker ps` e `ss -ltnp \| grep 81` para achar quem usa; pare o serviço seu que ocupa a porta (não os de outras pessoas/projetos) ou troque a porta no compose e a variável `REGRESSAO_*_URL` correspondente |
| Tudo vira ERRO_AMBIENTE, "Cannot connect to the Docker daemon" | O Docker Desktop caiu (costuma ser falta de memória) | Abra o Docker Desktop de novo, espere ficar verde, `regressao/bin/regressao ambiente-sobe`, rode de novo |
| Máquina lenta, Docker cai no meio da rodada | Memória curta no WSL | Antes da rodada: `wsl -d Ubuntu-24.04 -u root -- sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'`; feche navegador/IDE pesados; prefira `--prefixo`/`--area` |
| `ERRO_AMBIENTE ... baseline de outro dump` / `sha256 do dump ... != registrado` | O `baseline.dump` local não é o do repositório | Pegue a cópia certa com o time (confira com `sha256sum`); nunca gere um dump novo sem regravar Laravel e fluxos |
| Muitos casos com "Sessão inválida" / sessão expirada | A sessão do login caiu no meio (tela que faz logout, contêiner reiniciado) | A bateria PHP renova a sessão sozinha; se persistir, rode de novo a rodada. Telas que destroem a sessão já são puladas |
| Login no 8.5 dá "Erro interno" | Defeito real do 8.5 (`abrir.php`, `libs/JSON.php`) | Esperado hoje; a suíte loga no 7.4 |
| `ver-ultimo` diz "ainda em andamento" há muito tempo | Rodada completa (horas) ou travada | `tail -f ~/rodadas/<pasta>/execucao.log`; se o processo morreu, apague `~/rodadas/.em-andamento` e rode de novo |
| `falta o venv da regressao` | Preparação não feita | Seção "Preparar uma vez" |
| `a rodada terminou logo ao iniciar` | Atalho chamado de fora (`wsl -- regressao/bin/regressao ...` no PowerShell) e o WSL encerrou a sessão junto | Rode de dentro de um terminal do WSL; veja `execucao.log` da pasta da rodada |
| Todas as telas da referência com "Erro:(27) inserindo arquivo em db_usuariosonline" | A sessão do login não abriu conexão com o banco (visto uma vez logo depois de restaurar) | A bateria trata isso como sessão inválida e faz login de novo; se ainda aparecer, rode de novo |

## Usar com a pilha do grupo

Os contêineres, portas e o banco vêm de variáveis lidas a cada execução (`regressao/nucleo/ambiente.py`). O padrão é o
ambiente isolado `e74`. A pilha da raiz do repositório (a do `CLAUDE.md`/guia do grupo) usa outros nomes:

| Variável | Ambiente da regressão (padrão) | Pilha da raiz (grupo) |
|---|---|---|
| `REGRESSAO_REF_URL` / `REGRESSAO_CONTAINER_REF` | `http://localhost:8074` / `ecidade74_php74` | `http://localhost:8080` / `ecidade_php74` |
| `REGRESSAO_PHP_NOVO_URL` / `REGRESSAO_CONTAINER_PHP_NOVO` | `http://localhost:8185` / `ecidade74_php85` | `http://localhost:8085` / `ecidade_php85` |
| `REGRESSAO_PROXY_URL` / `REGRESSAO_CONTAINER_PROXY` | `http://localhost:8190` / `ecidade74_proxy` | `http://localhost:8090` / `ecidade_proxy` |
| `REGRESSAO_CONTAINER_BANCO` | `ecidade74_database` | `ecidade_database` |

Com essas variáveis, `scratchpad/cmp.py` (comparar as telas de um módulo) e `scratchpad/escrita_post.py` (um POST nos
dois lados) medem a pilha do grupo. **Cuidado:** as baterias (`rodada-*`, `python -m regressao...`) **recriam o banco**
do contêiner configurado a partir do dump. Contra a pilha da raiz isso apagaria o banco dela: rode as baterias só no
ambiente `e74`. O código trava isso: a restauração só roda em contêiner `ecidade74_*` (ou do projeto compose `e74`); com
outro, a bateria dá ERRO_AMBIENTE "restauracao recusada". Só `REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74=sim` libera, e aí o
banco daquele contêiner **é apagado e recriado**.

## Adicionar um caso

- **Uma tela (GET):** nada a cadastrar; ela entra pelo `--prefixo`/`--area`.
- **Um cadastro (POST) ou relatório:** uma linha em `regressao/php/catalogo_posts.tsv` ou `catalogo_relatorios.tsv`,
  rodada ao vivo antes de marcar `verificado` ([`README.md`, seção 5](README.md#5-adicionar-casos)).
- **Uma rota `/v4`:** os casos vêm do inventário de rotas; depois de mudar, a linha de base Laravel é regravada **na
  referência 7.4** (nunca no sistema migrado).
- **Um caminho de navegador:** uma função em `regressao/completa/fluxos.py` e `gravar --fluxo <id>` na referência.

Gravar ou regravar uma linha de base exige `--confirmo-sobrescrever` e é sempre feito **contra a referência 7.4**. O
código confere: o `gravar` dos fluxos recusa se algum passo veio com `X-Ecidade-Runtime` diferente de `PHP-7.4`.

## Pelo MCP (para quem usa IA)

O servidor MCP do repositório (`.mcp/`) tem as tools `rodar_regressao` (dispara uma rodada em segundo plano, nunca
grava linha de base), `ler_resultado_regressao` e `ler_triagem` (a triagem e as decisões da rodada "antes", sempre com
o resumo do topo), e este guia como resource (`ecidade://regressao/como-usar`). Testado ao vivo em 18/11/2026: uma
rodada `rodar_regressao(bateria="php", prefixo=["^arr1_grupotaxa001\\.php$"])` levou 3 min 47 s e
`ler_resultado_regressao` devolveu 2 IDENTICO e 2 DIVERGE (a classe e o cadastro com `0 == ""`).
Instalação em 3 passos: [`.mcp/README.md`](../.mcp/README.md). O MCP só lê rodadas de dentro do repositório (as que
ele mesmo dispara); as do atalho `regressao/bin/regressao` ficam em `~/rodadas`, fora dele. O `rodar_regressao` recusa
(`rodada_em_andamento`) quando há rodada disparada fora dele: a trava `~/rodadas/.em-andamento` com processo vivo ou
qualquer processo `python -m regressao.` (o mesmo `pgrep` que o atalho usa).

## Glossário

- **Referência / gabarito:** o e-Cidade PHP 7.4 + Laravel 8 (PR #8). O 8.5 tem de responder igual a ele.
- **Alvo:** o que está sendo migrado: PHP 8.5 (telas) e, no futuro, Laravel 13 (API `/v4`).
- **Bateria:** um conjunto de casos de um tipo: **PHP** (telas, cadastros, relatórios, 7.4 × 8.5 ao vivo), **Laravel**
  (rotas `/v4` contra uma gravação) e **fluxos** (navegador de verdade, contra uma gravação).
- **Rodada:** uma execução das baterias, numa pasta com `resumo.md`.
- **Linha de base (baseline):** a "foto" das respostas da referência, gravada uma vez e usada para comparar depois.
- **Dump:** o arquivo com o banco inteiro; toda bateria recria o banco a partir dele.
- **Proxy:** a porta única (:8190) que manda cada tela para o 7.4 ou para o 8.5, como o usuário vai usar.
- **Fluxo:** um caminho de usuário no navegador (login, menu, tela, cadastro, relatório).
- **Diff:** o trecho que mudou entre as duas respostas.
- **Prefixo/área:** filtro de quais telas PHP entram (ex.: `^arr1_`; `tributario`).
- **Divergência conhecida:** DIVERGE já investigada e aceita, em `regressao/conhecidas.tsv`.
- **Migration:** roteiro que muda a estrutura do banco; rodar é escrever no banco.
