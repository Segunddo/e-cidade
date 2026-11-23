# Tutorial: usar a regressão e o servidor MCP

Passo a passo prático, do computador vazio até ler um resultado e trabalhar em equipe com a IA. Não precisa ter
participado do projeto. O porquê de cada decisão está em [`01-passo-a-passo-do-que-foi-feito.md`](01-passo-a-passo-do-que-foi-feito.md);
o detalhe técnico de cada opção, em [`regressao/README.md`](../../regressao/README.md).

Convenções deste texto:

- Todo comando roda **dentro do WSL (Ubuntu)**, na **raiz do repositório** (a pasta que tem `regressao/` e `.mcp/`).
  Onde aparece `<seu-diretorio>`, use o caminho do seu clone (por exemplo `/home/voce/e-cidade`).
- "Referência" ou "7.4" é o sistema de gabarito (PHP 7.4 + Laravel 8). "Alvo" ou "8.5" é o sistema sendo migrado.

---

## 1. Preparar a máquina (uma vez)

**O que você precisa**

| Item | Detalhe |
|---|---|
| Windows com WSL (Ubuntu 24.04) ou Linux | O repositório fica **dentro do WSL**, nunca em `C:\`: há arquivos cujo nome só difere em maiúsculas e o Windows não guarda os dois (regra 2 do `CONTRIBUINDO.md`) |
| Docker Desktop com integração WSL ligada (ou Docker Engine no Linux), Compose v2 | `docker compose version` tem de responder |
| Python 3.12 com `venv` | `sudo apt install python3.12-venv` |
| Memória e disco | Numa máquina de 16 GB o Docker já caiu por falta de memória em rodada longa; feche o que puder. Disco: ~10 GB |
| O arquivo `regressao/baseline/baseline.dump` (~90 MB) | Não vai para o git. Peça a cópia ao time e confira: `sha256sum regressao/baseline/baseline.dump` tem de bater com `regressao/baseline/baseline.dump.sha256` |

**Passos**

```bash
# 1. clone dentro do WSL
cd ~
git clone https://github.com/Segunddo/e-cidade.git
cd e-cidade
git checkout regressao-php74            # a branch que traz regressao/ e .mcp/ (troque se o grupo usar outra)

# 2. ambiente Python da suíte de regressão
python3 -m venv regressao/.venv
regressao/.venv/bin/pip install -r regressao/requirements.txt
regressao/.venv/bin/python -m playwright install chromium     # navegador dos fluxos (~700 MB)

# 3. confira que a suíte está inteira (sem Docker, menos de 1 minuto)
regressao/.venv/bin/pytest regressao/tests -q
```

Se o Chromium reclamar de bibliotecas do sistema, instale-as como root:
`sudo <seu-diretorio>/regressao/.venv/bin/python -m playwright install-deps chromium`.

## 2. Montar o ambiente `e74` (primeira vez) e subir no dia a dia

O ambiente da regressão é um projeto Docker próprio, chamado **`e74`**: contêineres `ecidade74_*`, portas próprias e
publicadas **só em `127.0.0.1`** (não aparecem na rede local). Ele não toca a pilha da raiz do repositório
(8080/8085/8090) nem outro projeto local na porta 8080.

| Papel | Contêiner | Endereço |
|---|---|---|
| Referência PHP 7.4 + Laravel 8 | `ecidade74_php74` | http://localhost:8074 |
| Alvo PHP 8.5 | `ecidade74_php85` | http://localhost:8185 |
| Proxy (uma porta só, como o usuário vai usar) | `ecidade74_proxy` | http://localhost:8190 |
| Laboratório Laravel no PHP 8.5 | `ecidade74_lar12` | http://localhost:8187 |
| Banco PostgreSQL 16 | `ecidade74_database` | sem porta (a suíte usa `docker exec`) |

**Primeira vez**: siga a [seção 1 do `regressao/README.md`](../../regressao/README.md#1-pré-requisitos). Ela constrói
as imagens, carrega o banco (~6 min) e cria os arquivos locais do e-Cidade que não vão para o git (`.env`,
`libs/db_conn.php` etc.). Feito uma vez, depois só se sobe e desce.

**No dia a dia**:

```bash
regressao/bin/regressao ambiente-sobe     # sobe tudo e espera a referência responder; no fim diz "ambiente ok"
regressao/bin/regressao ambiente-para     # para só os contêineres ecidade74_* (nada é apagado)
regressao/bin/regressao ajuda             # lista os atalhos
```

Para conferir à mão: `curl -sI http://localhost:8190/login.php | grep -i x-ecidade` deve mostrar
`X-Ecidade-Runtime: PHP-7.4 (referencia)`. O login no navegador é `dbseller` / `dbseller`.

## 3. Rodar um teste pequeno

Há dois tamanhos de "teste pequeno".

**a) Só algumas telas PHP (5 a 6 minutos, a maior parte é restaurar o banco):**

```bash
regressao/.venv/bin/python -m regressao.php.bateria --saida /tmp/fumaca --prefixo '^cem1_cemiterio00'
```

`--prefixo` é uma expressão regular sobre o nome do arquivo da tela (pode repetir). `--area tributario` pega uma área
inteira (horas). As áreas válidas aparecem em `regressao/.venv/bin/python -m regressao.php.bateria --help`.

**b) A rodada pequena (cerca de 25 minutos, em segundo plano):**

```bash
regressao/bin/regressao rodada-pequena
regressao/bin/regressao ver-ultimo        # andamento; quando terminar, mostra o resumo
```

Ela mede 3 grupos de telas PHP (cadastros da Arrecadação, Cemitério e dois relatórios), a bateria Laravel inteira
**contra a própria referência** (prova de que a medição é estável) e os 6 fluxos de navegador. A rodada fica em
`~/rodadas/<data>-<hora>-pequena/` (troque a pasta com a variável `REGRESSAO_RODADAS`).

`ver-ultimo` mostra a rodada em andamento (pela trava `~/rodadas/.em-andamento`) ou, se nada está rodando, a mais
recente pela data de modificação entre as pastas com nome no padrão `AAAAMMDD-HHMMSS-<tipo>`. Pastas com outro nome
(por exemplo uma `antes74` copiada à mão) são ignoradas.

**Só uma rodada por vez.** Cada bateria **recria o banco** a partir do dump no início. O atalho recusa uma segunda
rodada, e o MCP também.

Importante: chame o atalho **de um terminal do WSL**. Chamado do PowerShell com `wsl -- regressao/bin/regressao ...`, o
WSL pode encerrar a sessão e matar a rodada junto (o atalho espera 5 s e avisa).

## 4. Rodar a rodada completa

```bash
regressao/bin/regressao rodada-completa                               # todas as telas PHP, Laravel contra o laboratório, fluxos
regressao/bin/regressao rodada-completa --alvo-laravel http://localhost:8074   # Laravel contra a referência (estabilidade)
regressao/bin/regressao rodada-completa --area tributario             # só uma área no PHP
regressao/bin/regressao rodada-completa --sem-fluxos                  # sem os fluxos de navegador
```

A completa levou **5 h 26 min** em 18/11/2026 (PHP 5 h 05, Laravel 16 min, fluxos 5 min). Antes de uma rodada longa,
solte o cache de arquivos do WSL (pode ser no PowerShell):
`wsl -d Ubuntu-24.04 -u root -- sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'`.

Os argumentos extras vão para o orquestrador; o comando equivalente sem atalho é
`regressao/.venv/bin/python -m regressao.completa.orquestra --saida DIR [--area A] [--prefixo RX] [--sem-fluxos] [--alvo-laravel URL]`.

**Refazer só alguns casos** (por exemplo as telas que deram ERRO_AMBIENTE), sem repetir as etapas longas:

```bash
regressao/.venv/bin/python -m regressao.php.bateria --saida /tmp/complemento \
  --prefixo '^rec2_espelhoponto002\.php$' --pular sintaxe --pular classes
```

## 5. Ler o relatório

Cada rodada tem `resumo.md` (e uma cópia idêntica, `relatorio.md`) e as pastas `php/`, `laravel/` e `fluxos/`, cada uma
com o próprio `resumo.md`, `resultado.json` e `diffs/`. Leia nesta ordem:

1. **Primeira linha, `Resultado:`** `VERDE (saida 0)`, `VERMELHO (saida 1)` ou `ERRO (saida 2)`.
2. **AVISOS**, sempre. Eles dizem, por exemplo:
   - que o gabarito é o 7.4 e que INCONCLUSIVO e ERRO_AMBIENTE **nunca** são aprovação;
   - que a bateria PHP compara 7.4 e 8.5 **sobre o mesmo código** (um defeito comum aos dois dá IDENTICO);
   - `ALVO LARAVEL = REFERENCIA` quando o Laravel foi comparado com ele mesmo (mede estabilidade, não migração);
   - que **nenhum passo dos fluxos veio do PHP 8.5** (o proxy ainda manda tudo ao 7.4, então os fluxos mediram 7.4 × 7.4;
     para mandar uma tela ao 8.5, acrescente `<arquivo.php> php85;` em `regressao/lab/proxy/map-e74.conf` e recrie o
     proxy);
   - cada ERRO_AMBIENTE, com o motivo.
3. **Totais por bateria**: quantos casos de cada veredito e o tempo.
4. **Cobertura**: o que foi exercitado (telas, cadastros e relatórios do catálogo, rotas Laravel cobertas × não
   cobertas, passos de fluxo). Verde com pouca cobertura vale pouco.
5. **INCONCLUSIVO por motivo**: por que cada grupo não foi verificado.
6. **Divergências novas / conhecidas e ERRO_AMBIENTE**: a lista do que olhar. O diff de cada uma está em
   `<bateria>/diffs/`.

Exemplo real, o começo do `resumo.md` da rodada "antes" (18/11/2026):

```text
Resultado: ERRO (saida 2): a rodada nao pode ser concluida (ERRO_AMBIENTE ou sub-rodada nao comparavel); ...
| bateria | casos | IDENTICO | DIVERGE | INCONCLUSIVO | ERRO_AMBIENTE | novas | conhecidas | saida | tempo (s) |
| php     | 28783 | 18958    | 9205    | 609          | 11            | 9205  | 0          | 2     | 18273.4   |
| laravel | 992   | 719      | 0       | 273          | 0             | 0     | 0          | 0     | 988.0     |
| fluxos  | 32    | 31       | 1       | 0            | 0             | 1     | 0          | 1     | 293.1     |
```

Leitura: é **ERRO** (não vermelho) porque 11 telas estouraram o tempo **no 7.4**; o PHP tem 9.205 DIVERGE, o retrato da
base ainda não adaptada (causas em `regressao/baseline/triagem-divergencias.md`); o Laravel foi comparado com ele mesmo;
o DIVERGE dos fluxos foi uma instabilidade que não se repetiu.

## 6. Os quatro vereditos e o que fazer com cada um

| Veredito | Quer dizer | Exemplo real | O que fazer |
|---|---|---|---|
| **IDENTICO** | Os dois lados responderam igual (depois de tirar datas, horas, ids de sessão) | `arr1_grupotaxa001.php` abre igual no 7.4 e no 8.5 | Nada. Mas vale só para o que foi exercitado |
| **DIVERGE** | Respostas diferentes: **achado** da migração | `cem1_cemiterio003.php`: 7.4 responde 200, 8.5 responde 500 (`parse_str()` com 1 argumento). Cadastro `arr1_grupotaxa001`: o 7.4 grava, o 8.5 não (`0 == ""`) | Abrir o diff em `diffs/`, achar a causa (`ler_triagem` no MCP mostra se já é conhecida) e corrigir o mínimo no 8.5 |
| **INCONCLUSIVO** | O caso **não foi exercitado** | 272 rotas Laravel dão 500 nos dois lados com o corpo vazio da sonda; um passo de fluxo que não rodou porque o anterior falhou | **Não é aprovação.** É lacuna de cobertura: anote |
| **ERRO_AMBIENTE** | A medição não pôde ser feita | Contêiner parado, dump diferente do registrado, tela que estoura 60 s no 7.4, laboratório que não emite token | Corrigir o ambiente e rodar de novo. **Nada se conclui** |

Saída da rodada: **0** = nenhuma DIVERGE nova e nenhum ERRO_AMBIENTE (ainda assim leia Cobertura e INCONCLUSIVO);
**1** = há DIVERGE que não está em `regressao/conhecidas.tsv`; **2** = algum ERRO_AMBIENTE ou rodada incompleta. Na
completa vale o pior das três baterias.

Hoje a rodada é vermelha, e isso é esperado: a `base-php74` ainda não foi adaptada ao 8.5. O trabalho do grupo é fazer
essas divergências sumirem uma a uma, sem criar outras. **Não** ponha divergência em `conhecidas.tsv` para deixar a
rodada verde: o arquivo só aceita divergência que já existia antes da migração, com prova.

### Antes e depois de uma correção

```bash
regressao/bin/regressao rodada-pequena          # ANTES (ou use uma rodada que já existe)
# ... aplica a correção ...
regressao/bin/regressao rodada-pequena          # DEPOIS (mesmos prefixos)
regressao/bin/regressao comparar ~/rodadas/<antes> ~/rodadas/<depois>
```

O `comparacao.md` (escrito na pasta DEPOIS) lista **Regressões**, **Correções** (DIVERGE → IDENTICO), casos novos e
removidos e **Lacunas** (DIVERGE → INCONCLUSIVO: saiu do vermelho sem ser verificado, **não** é correção). As duas
rodadas precisam medir a mesma coisa (mesmos prefixos/áreas).

## 7. Gravar linha de base com segurança

Linha de base (baseline) é a "foto" das respostas da referência. Existem três: o **dump** do banco, a gravação
**Laravel** (`regressao/baseline/laravel/`) e a dos **fluxos** (`regressao/baseline/fluxos/`). Regravá-las com o
sistema já migrado destrói a comparação sem ninguém perceber. Por isso:

**Quando regravar**: só depois de mudar os casos (rotas, fluxos) ou o dump, e **sempre contra a referência 7.4**. Nunca
para "fazer passar" uma rodada.

**Proteções que já estão no código** (você vai encontrá-las):

- `gravar` recusa (saída 2) sobrescrever uma linha de base existente sem `--confirmo-sobrescrever`.
- A gravação Laravel confere que o contêiner da referência roda **PHP 7.4 e Laravel 8** antes de gravar; gravar contra
  outro endereço exige `--alvo` explícito **e** `--confirmo-sobrescrever`.
- A gravação dos fluxos recusa se algum passo veio com `X-Ecidade-Runtime` diferente de `PHP-7.4` (proxy mandando tela
  ao 8.5) e se algum passo falhou.
- A gravação Laravel recusa se uma sonda **escreveu** no banco com corpo vazio (ela deve ir para `perigosas` em
  `regressao/laravel/casos/_ajustes.yml`).
- Senha, sessão e token nunca são gravados: a gravação é barrada se aparecerem.
- O MCP nunca grava linha de base.

**Comandos**

```bash
# Laravel: regravar tudo na referência
regressao/.venv/bin/python -m regressao.laravel.bateria gravar --saida /tmp/lar-g --alvo http://localhost:8074 --confirmo-sobrescrever
# Laravel: só acrescentar casos novos, sem tocar nos existentes
regressao/.venv/bin/python -m regressao.laravel.bateria gravar --saida /tmp/lar-g --apenas-novos --confirmo-sobrescrever
# Laravel: refazer um registro (apaga o arquivo e tira o id do _meta; depois grave com --apenas-novos)
regressao/.venv/bin/python -m regressao.laravel.caso remove <id> --confirmo-sobrescrever
# Laravel: tirar da linha de base os registros que não têm mais caso
regressao/.venv/bin/python -m regressao.laravel.caso poda --confirmo-sobrescrever

# Fluxos: com o proxy mandando TUDO ao 7.4 (map-e74.conf vazio)
regressao/.venv/bin/python -m regressao.completa.fluxos gravar --saida /tmp/fl-g --confirmo-sobrescrever
regressao/.venv/bin/python -m regressao.completa.fluxos gravar --saida /tmp/fl-g --fluxo navegacao --confirmo-sobrescrever
```

**Checklist antes de gravar**

1. `curl -sI http://localhost:8190/login.php | grep -i x-ecidade` diz `PHP-7.4 (referencia)`.
2. `regressao/lab/proxy/map-e74.conf` não manda nenhuma tela ao 8.5 (para os fluxos).
3. O `baseline.dump` local é o registrado (`sha256sum` igual ao `.sha256`).
4. Depois de gravar, compare **duas vezes seguidas** contra a referência e confira que os dois resultados são iguais caso
   a caso (é a prova de estabilidade usada até aqui):
   `regressao/.venv/bin/python -m regressao.laravel.bateria comparar --saida /tmp/lar1 --alvo http://localhost:8074`.
5. Commit só dos arquivos da linha de base (`git add regressao/baseline/laravel/...`), nunca `git add -A`.

**Trocar o dump** invalida as linhas de base Laravel e de fluxos (elas guardam o sha256 do dump). Gerar um dump novo
está na [seção 2 do `regressao/README.md`](../../regressao/README.md#2-a-baseline-do-banco-o-dump) e obriga a regravar
as duas. Guarde uma cópia do dump fora do git: um `pg_dump` novo nunca tem o mesmo sha256.

**A suíte recria o banco só no ambiente `e74`.** A restauração faz `DROP DATABASE` no contêiner configurado em
`REGRESSAO_CONTAINER_BANCO` e só aceita contêiner com nome `ecidade74_*` ou do projeto compose `e74`. Para outro
contêiner é preciso exportar `REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74=sim`, e isso **apaga o banco dele**. Não faça isso
na pilha da raiz do grupo.

## 8. Usar o MCP em 3 passos

O servidor MCP é um ajudante que a sua IA usa para seguir as regras do grupo, achar código antigo, validar no PHP 7.4 e
no 8.5, rodar a regressão e dividir o trabalho. Roda na sua máquina, não faz push, não roda comando livre.

**Passo 1. Instale (uma vez)**

```bash
python3 -m venv .mcp/.venv
.mcp/.venv/bin/pip install -r .mcp/requirements.txt
```

**Passo 2. Suba o ambiente** (para validar PHP e rodar a regressão; o resto funciona sem ele):
`regressao/bin/regressao ambiente-sobe`.

Defina também quem você é e a sua área (no `~/.bashrc` do WSL):

```bash
export ECIDADE_MCP_USUARIO="Seu Nome"
export ECIDADE_MCP_AREA=financeiro     # nucleo, educacao, pessoal, financeiro, tributario_patrimonial, saude_demais ou sem_area
export ECIDADE_MCP_TAREFA=31           # número da tarefa do grupo: as sugestões de commit saem como "PHP8-31: ..."
```

**Passo 3. Abra o repositório na sua IA** (a configuração já está no repositório):

| IA | Arquivo | O que fazer |
|---|---|---|
| **Claude Code** | `.mcp.json` | Rode `claude` na raiz do repositório, dentro do WSL. Na primeira vez ele pergunta se confia no servidor `ecidade`: aceite. `/mcp` mostra o status |
| **Cursor** | `.cursor/mcp.json` | Abra a pasta pelo WSL (*Connect to WSL*). Em *Settings → MCP*, ative `ecidade` |
| **VS Code** (Copilot Chat) | `.vscode/mcp.json` | Abra a pasta pelo WSL (`code .` dentro do WSL). No Chat, modo **Agent** → ícone de ferramentas → `ecidade` → *Start* |

Teste pedindo: *"use a tool quadro do servidor ecidade"*. Se a IA roda no Windows (fora do WSL), a configuração com
`wsl.exe` vai na configuração **do seu usuário**, nunca no repositório; o exemplo está no
[`.mcp/README.md`](../../.mcp/README.md#como-cada-ia-conecta).

**Revise como código** qualquer mudança em `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` e nas variáveis
`ECIDADE_MCP_RAIZ`/`ECIDADE_MCP_DOCKER`: elas decidem que programa a sua IA executa.

### Cada tool, com um pedido de exemplo

Você pode pedir em linguagem natural; a IA escolhe a tool. Entre parênteses, a chamada que ela faz.

| Tool | Para que serve | Exemplo de pedido à IA |
|---|---|---|
| `quadro` | Quem está mexendo em quê, o que já foi concluído, últimas rodadas | "Mostre o quadro da equipe." (`quadro()`) |
| `reivindicar_arquivo` | "Estou neste arquivo" por 4 horas (chamar de novo renova). Recusa se outra pessoa pegou ou se é de outra área | "Reivindique `ecidade/mat2_cadunidade002.php` para corrigir parse_str." |
| `liberar_arquivo` | Solta o arquivo; com `concluido=true` registra o que foi corrigido | "Libere `ecidade/mat2_cadunidade002.php` como concluído, padrão parse_str_1_arg." |
| `proximo_trabalho` | Próximo lote da sua área, na ordem do grupo (não compila > quebra ao rodar > silencioso), pulando o que é de outros | "Pegue os próximos 10 arquivos com parse_str de 1 argumento na minha área e reivindique." |
| `buscar_codigo_legado` | Procura código antigo por nome de problema (`parse_str_1_arg`, `construtor_php4`, `each`...) ou por regex | "Procure todos os padrões legados em `ecidade/con2_balancrece002.php`." |
| `padroes_ja_corrigidos` | Como cada problema é corrigido no repositório, o que já foi feito e quanto falta | "Como o grupo corrige parse_str de 1 argumento? Quantos faltam em `ecidade/classes`?" |
| `validar_arquivo_php` | `php -l`, PHPStan, Pint ou PHPCS dentro do Docker, no 7.4, no 8.5 ou nos dois | "Valide `ecidade/fpdf151/fpdf.php` nas duas versões do PHP." |
| `analisar_composer` | O que no `composer.json`/`composer.lock` trava o PHP 8.5/Laravel 13 | "O que no composer impede o PHP 8.5?" |
| `rodar_regressao` | Dispara a regressão em segundo plano (uma por vez; **restaura o banco de teste**) | "Rode a regressão PHP só para `^arr1_grupotaxa001\.php$`." |
| `ler_resultado_regressao` | Andamento e resultado de uma rodada (sem id, lista as rodadas) | "Como está a rodada `20261118-081044-php-77d2`? Mostre só as DIVERGE." |
| `ler_triagem` | A triagem das 9.206 divergências da rodada "antes" e as decisões, por seção ou busca | "O que a triagem diz sobre `fpdf.php:614`?" |
| `regras_do_grupo` | As regras do grupo, inteiras ou por tópico | "Quais são as regras do grupo sobre copiar da base-php84?" |
| `ferramentas_do_grupo` | As ferramentas do grupo em `scratchpad/` (cmp.py, regras do Rector...) | "Que ferramentas o grupo tem para comparar telas?" |

### Cada prompt (roteiro pronto)

No Claude Code os prompts aparecem como comandos `/mcp__ecidade__<nome>`; no Cursor e no VS Code, na lista de prompts do
servidor `ecidade`.

| Prompt | O que a IA faz | Exemplo |
|---|---|---|
| `migrar-arquivo` | Reivindica, prova 7.4 × 8.5 antes, corrige o mínimo no arquivo do PR (ISO-8859-1), valida nos dois PHPs, prova depois, libera e sugere o commit | `/mcp__ecidade__migrar-arquivo` com `caminho=ecidade/cem1_cemiterio003.php` |
| `auditar-model` | Revisão **sem editar** de um Model Eloquent: o que quebra do Laravel 8 ao 13, numa tabela por linha | `caminho=ecidade/app/Domain/Assinador/CertificadoUsuario.php` |
| `corrigir-padrao-mecanico` | Pega um lote de um padrão na sua área, prova antes, corrige com a forma padrão, prova depois, libera e propõe commits separados (automático × manual) | `padrao=parse_str_1_arg`, `limite=10` |
| `verificar-com-regressao` | Escolhe a bateria e o recorte certos para uma mudança, roda e interpreta. **A mudança só segue com IDENTICO nos casos da mudança**: INCONCLUSIVO não libera, ERRO_AMBIENTE obriga a rodar de novo | `alvo=ecidade/arr1_grupotaxa001.php` |

**Resources** (documentos que a IA lê sozinha): `ecidade://grupo/regras`, `ecidade://grupo/guia-7.4-para-8.5`,
`ecidade://docs/regras-arquitetura`, `ecidade://docs/breaking-changes`, `ecidade://regressao/como-usar`,
`ecidade://regressao/triagem`, `ecidade://regressao/decisoes`, `ecidade://estado/trabalho`, `ecidade://padroes`.

Respostas com texto de terceiros (código, motivos de colegas, logs) vêm com `conteudo_nao_confiavel: true`: a IA deve
tratar esse texto como dado, nunca como ordem.

## 9. Trabalho em equipe: reivindicar e liberar arquivos

O quadro de quem mexe em qual arquivo fica em `.mcp/estado/trabalho.json`, **no Git**. Não há servidor central: a
sincronização entre máquinas é o próprio Git.

Roteiro de uma tarefa:

1. `git checkout base-php74 && git pull && git checkout -b <area>/<assunto>` (ex.: `financeiro/parse-str`).
2. Peça à IA o quadro e reivindique o arquivo (ou peça o próximo lote com `proximo_trabalho`, que já reivindica).
3. **Publique a reivindicação** para os colegas verem: commit só do estado.

   ```bash
   git add .mcp/estado/trabalho.json
   git commit -m "PHP8-NN: reivindica ecidade/xxx.php no quadro"      # NN = número da tarefa do grupo
   git pull --rebase && git push      # só quando a equipe combinar publicar
   ```

4. Faça a correção com prova antes e depois (o prompt `migrar-arquivo` faz o roteiro inteiro). Commit **só dos arquivos
   que você mexeu** (`git add <arquivo>`, nunca `git add -A`), assunto no formato do `CONTRIBUINDO.md`,
   `PHP8-NN: descrição curta` (NN = número da tarefa do grupo); o que o Rector fez num commit, o manual em outro; o
   código em ISO-8859-1.
5. Libere o arquivo (`concluido=true` se terminou) e faça commit do `trabalho.json` de novo, separado do código.
6. `git pull origin base-php74` e abra o pull request para `base-php74`.

Regras que o MCP aplica:

- A reivindicação **expira em 4 horas** (`ECIDADE_MCP_EXPIRA_HORAS`); expirada, outra pessoa pode pegar. Quem ainda
  está trabalhando renova chamando `reivindicar_arquivo` de novo.
- Arquivo de outra área: o MCP recusa (`outra_area`); peça ao dono. Só com combinado: `combinado_com_dono=true`.
- **Conflito no Git no `trabalho.json`**: o arquivo tem uma entrada por caminho, em ordem alfabética. Mantenha as
  entradas dos dois lados, apague as marcas `<<<<<<<`, `=======`, `>>>>>>>` e faça commit. Se o merge deixar a **mesma
  chave duas vezes**, o MCP também responde `estado_corrompido`: deixe uma entrada só para aquele caminho. Enquanto o
  arquivo estiver assim, as tools recusam em vez de sobrescrever (de propósito).
- Não edite o `trabalho.json` à mão fora desses consertos de conflito.

## 10. Problemas comuns (todos já vistos neste projeto)

**Regressão**

| Sintoma | Causa | O que fazer |
|---|---|---|
| `ambiente-sobe` falha com "port is already allocated" | Outro serviço usa 8074/8185/8187/8190 | `docker ps` e `ss -ltnp \| grep 81` para achar quem usa; pare o seu serviço que ocupa a porta (não o de outras pessoas) ou troque a porta no compose e a variável `REGRESSAO_*_URL` correspondente |
| Tudo vira ERRO_AMBIENTE, "Cannot connect to the Docker daemon" | O Docker Desktop caiu (em geral, falta de memória) | Abra o Docker Desktop, espere ficar verde, `regressao/bin/regressao ambiente-sobe`, rode de novo |
| Máquina lenta, Docker cai no meio da rodada | Memória curta no WSL | Antes da rodada, `drop_caches` (seção 4); feche navegador/IDE pesados; prefira `--prefixo`/`--area` |
| `sha256 do dump ... != registrado` | O `baseline.dump` local não é o do repositório | Pegue a cópia certa com o time; nunca gere um dump novo sem regravar Laravel e fluxos |
| Restauração recusada: contêiner fora do ambiente `e74` | `REGRESSAO_CONTAINER_BANCO` aponta para outro banco | Volte ao padrão (`ecidade74_database`). Só use `REGRESSAO_CONFIRMO_BANCO_FORA_DO_E74=sim` se puder **apagar** aquele banco |
| `falta o venv da regressao` | Preparação não feita | Seção 1 |
| `a rodada terminou logo ao iniciar` | Atalho chamado do PowerShell (`wsl -- regressao/bin/regressao ...`) e o WSL encerrou junto | Rode de dentro de um terminal do WSL; veja `execucao.log` da pasta da rodada |
| `ja ha uma rodada em andamento` / `ha uma bateria da regressao rodando` | Outra rodada (sua, de outra IA ou do MCP) usa o banco | Espere (`ver-ultimo`). Se o processo morreu, apague `~/rodadas/.em-andamento` |
| `ver-ultimo` diz "ainda em andamento" há muito tempo | Rodada completa (horas) ou travada | `tail -f ~/rodadas/<pasta>/execucao.log`; se o processo morreu, apague `~/rodadas/.em-andamento` |
| Muitas telas com "Sessão inválida" | A sessão do login caiu (tela que faz logout, contêiner reiniciado) | A bateria renova sozinha; se persistir, rode de novo |
| Todas as telas da referência com `Erro:(27) inserindo arquivo em db_usuariosonline` | A sessão do login veio sem conexão com o banco (visto uma vez logo depois de restaurar) | A bateria trata como sessão inválida e faz login de novo; se ainda aparecer, rode de novo |
| Login no 8.5 dá "Erro interno" | Defeito real do 8.5 (`libs/JSON.php:188`) | Esperado hoje; a suíte loga no 7.4 |
| Fluxo `incluir-registro:salvar` deu DIVERGE uma vez | A chamada de ajuda `con4_dbhelp.RPC.php?json` às vezes não acontece | Repita o fluxo (`--fluxo incluir-registro`); se der IDENTICO, registre como instabilidade. Não apague nem "aprove" |
| Aviso "nenhum passo veio do PHP 8.5" nos fluxos | O proxy manda tudo ao 7.4 | Normal até as telas migradas entrarem em `regressao/lab/proxy/map-e74.conf` |
| `fluxos gravar` recusado por runtime diferente de 7.4 | Há tela mandada ao 8.5 no proxy | Esvazie `map-e74.conf`, recrie o proxy e grave de novo |
| `gravar` Laravel recusado porque a referência não é PHP 7.4/Laravel 8 | Variáveis apontando para outro contêiner | Confira `REGRESSAO_REF_URL` e `REGRESSAO_CONTAINER_REF` |
| `gravar` Laravel recusado porque uma sonda escreveu | Uma rota grava no banco quando chamada com corpo vazio | Ponha a rota em `perigosas` (`regressao/laravel/casos/_ajustes.yml`), regere os casos e grave de novo |
| Laboratório :8187: um ERRO_AMBIENTE `laravel:banco` | O `lcobucci/jwt` 3.4 não aceita a chave no PHP 8 (nenhum token é emitido) | Esperado até o grupo Laravel trocar o pacote. Para estabilidade, use `--alvo-laravel http://localhost:8074` |
| Login de tudo dá erro de sintaxe na instalação | `sed` do `db_conn.php` rodado em locale UTF-8 deixou lixo depois do `;` | Refaça com `export LC_ALL=C` (seção 1 do `regressao/README.md`) |
| `php artisan passport:install` falha com chave duplicada | O dump já traz os clientes OAuth | Não rode; não é necessário |
| Volume `e74_sessions` com milhares de arquivos | O healthcheck da referência cria uma sessão a cada 5 s | Inofensivo; `docker volume rm e74_sessions` limpa com o ambiente parado |

**MCP** (o campo `erro.codigo` da resposta)

| Código | O que fazer |
|---|---|
| `conteiner_indisponivel` / `conteiner_parado` | Suba o ambiente (`regressao/bin/regressao ambiente-sobe`) |
| `docker_indisponivel` | O Docker não está no PATH desta sessão (no WSL: integração do Docker Desktop ligada) |
| `venv_regressao_ausente` | Seção 1 (criar `regressao/.venv`) |
| `quem_desconhecido` | Passe `quem="seu nome"` ou defina `ECIDADE_MCP_USUARIO` |
| `ja_reivindicado` | Outra pessoa está no arquivo até `detalhes.expira`; escolha outro (`proximo_trabalho`) |
| `outra_area` | Peça ao dono da área |
| `rodada_em_andamento` | Já há uma rodada (do MCP ou manual, pelo atalho ou `python -m regressao.`); espere |
| `confirmacao_necessaria` | A rodada pedida é longa: restrinja com `prefixo`/`fluxo` ou confirme com `confirmo_rodada_longa=true` |
| `estado_corrompido` | `trabalho.json` com conflito do Git, chave duplicada ou formato inválido (seção 9); ou pasta de rodada estragada em `.mcp/rodadas/` (apague a pasta) |
| `caminho_proibido` / `caminho_fora_da_raiz` | O arquivo é segredo, log, cache ou está fora do repositório: o MCP não lê |
| `ferramenta_indisponivel` | Pint/PHPCS não estão no `vendor/` (instalar é decisão da equipe) |
| `config_phpstan_recusada` | O `phpstan.neon` manda carregar arquivo fora do repositório: revise o arquivo |
| `resposta_grande` | Restrinja `caminho`, `limite` ou `max_itens` |
| `erro_interno` | Erro inesperado de uma tool; o servidor continua de pé. O detalhe está no log do servidor (stderr). Se `ECIDADE_MCP_LOG` tiver um valor inválido, o log volta para `INFO` |
| A IA não lista o servidor `ecidade` | Abra o repositório **pelo WSL**, na raiz; no Claude Code, aceite a confiança do servidor e veja `/mcp` |

## 11. Glossário

- **Referência / gabarito**: o e-Cidade PHP 7.4 + Laravel 8 do PR #8. O 8.5 tem de responder igual a ele.
- **Alvo**: o que está sendo migrado: PHP 8.5 (telas) e, no futuro, Laravel 13 (API `/v4`).
- **Ambiente `e74`**: o projeto Docker isolado da regressão (contêineres `ecidade74_*`, portas 8074/8185/8190/8187).
- **Bateria**: conjunto de casos de um tipo: **PHP** (telas, cadastros, relatórios, 7.4 × 8.5 ao vivo), **Laravel**
  (rotas contra uma gravação) e **fluxos** (navegador de verdade, contra uma gravação).
- **Rodada**: uma execução das baterias, numa pasta com `resumo.md`. **Pequena** (~25 min) ou **completa** (horas).
- **Caso**: uma coisa medida (uma tela, um cadastro, uma rota, um passo de fluxo), com um veredito.
- **Veredito**: IDENTICO, DIVERGE, INCONCLUSIVO ou ERRO_AMBIENTE (seção 6).
- **Linha de base (baseline)**: a "foto" das respostas da referência, gravada uma vez para comparar depois.
- **Golden master**: o jeito de testar comparando com uma gravação anterior (Laravel e fluxos).
- **Dump**: o arquivo com o banco inteiro; toda bateria recria o banco a partir dele.
- **Proxy**: a porta única (:8190) que manda cada tela para o 7.4 ou o 8.5, como o usuário vai usar. O cabeçalho
  `X-Ecidade-Runtime` diz quem respondeu.
- **Laboratório**: o :8187, o PHP 8.5 rodando o Laravel 8 atual, enquanto o Laravel 13 não existe.
- **Diff**: o trecho que mudou entre as duas respostas (`diffs/` de cada bateria).
- **Prefixo / área**: filtro de quais telas PHP entram (ex.: `^arr1_`; `tributario`).
- **Divergência conhecida**: DIVERGE já investigada e aceita com prova, em `regressao/conhecidas.tsv` (hoje vazio).
- **Triagem**: a explicação, por causa, de cada divergência da rodada "antes" (`regressao/baseline/triagem-divergencias.md`).
- **Efeito cebola**: corrigir a primeira quebra de uma tela pode revelar a seguinte.
- **MCP**: protocolo que deixa a IA usar ferramentas; aqui, o servidor `ecidade` em `.mcp/`.
- **Tool / resource / prompt**: ação que a IA executa / documento que ela lê / roteiro pronto que ela segue.
- **Reivindicar / liberar**: marcar no quadro "estou neste arquivo" / soltar o arquivo (e registrar o que foi feito).
- **Migration**: roteiro que muda a estrutura do banco; rodar é escrever no banco.
- **ISO-8859-1 (LATIN1)**: a codificação dos arquivos do e-Cidade. Salvar em UTF-8 estraga os acentos.
