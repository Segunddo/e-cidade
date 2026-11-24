# Como um módulo do e-cidade é migrado

Oct 11, 2026 · @Diego

**Para quem nunca mexeu com PHP.** Este é um manual de operação: cada passo traz o comando exato, a saída esperada e o que fazer quando ela não vem. Você não precisa saber PHP para executar — precisa saber **conferir**.

A regra que vale mais que todas as outras: **quase toda armadilha aqui se parece com sucesso.** Nada quebra, nada avisa, e o número que aparece na tela é tranquilizador. Por isso cada passo tem uma conferência própria, e por isso elas não são opcionais.

Substitua `<pref>` pelo prefixo do módulo (`jur`, `cad`, `cai`…) em todos os comandos. Rode tudo da **raiz do repositório**, nunca de dentro de `ecidade/`.

> **Revisado em 12/11/2026.** A primeira versão (11–13/10) era de quando se migrava um módulo por vez. Desde então o
> trabalho passou a ser **por área, em lotes** (ver *O fluxo de uma área*, logo depois do ambiente), e entraram cinco
> verificações novas: a carga das classes (LSP), a forma negada (6c), as abas e redirecionamentos (8b), a nona frente da
> enumeração e as guardas automáticas `pg_*`. A skill `migrar-modulo` (`.claude/skills/migrar-modulo/SKILL.md`) é a
> versão condensada deste guia; os dois devem dizer a mesma coisa.

> **Revisado em 22/11/2026, para a `base-php85`.** Três mudanças:
>
> 1. **A referência é o PHP 7.4** (`ecidade_php74`, porta 8080), no papel que era do 5.6. Os comandos e as instruções
>    já dizem 7.4. Onde o texto ainda diz 5.6, é um fato medido naquela época (por exemplo, por que uma regra do Rector
>    foi banida). O 7.4 se comporta igual ao 5.6 em quase tudo o que este guia corrige (`0 == ""`, `count(null)`,
>    constante indefinida, auto-vivificação, `1969-12-31`), com duas exceções medidas: o `??` existe no 7.4, e a
>    divisão por zero dá `INF` em vez de `false`. Na dúvida, pergunte ao 7.4: `docker exec ecidade_php74 php -r '...'`.
> 2. **A branch de cada área sai da `base-php85`** e a PR volta para ela. Antes de mexer, os arquivos são reservados no
>    quadro do MCP (ver *O fluxo de uma área*, A).
> 3. **Os passos têm um comando cada:** `rector_lote.py` (4), `verifica_lote.py` (4b a 7), `nivel3.py` (nível 3) e
>    `rotear.py` (8 e 8b). As seções de cada passo mantêm os comandos à mão, que explicam o que a ferramenta faz e servem
>    para conferi-la. Estas seções tinham sumido do guia ao trazê-lo para a `base-php74` e voltaram nesta revisão.

## A receita, em uma imagem

```
  DESCOBRIR o que existe
  ┌──────────────────────┐   ┌──────────────┐   ┌──────────────────────┐
  │ 1. Enumerar universo │ → │ 2. Inventar. │ → │ 3. Classificar       │
  │ nove frentes         │   │ o que há     │   │ literal? regex? JS?  │
  └──────────────────────┘   └──────────────┘   └──────────────────────┘
                                      ↓
  TRANSFORMAR
  ┌────────────────────────────┐   ┌──────────────────────────────────┐
  │ 4. Rector (40 na denylist) │ → │ 4b. Portão de funções vs 7.4     │
  └────────────────────────────┘   └──────────────────────────────────┘
     ↑__________________________|
     repete até dar 0 arquivos
                                      ↓
  VERIFICAR
  ┌───────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌═════════════┐
  │ 5. php -l │→│5b. Carga │→│ 6. Classes │→│ 6b. Escrita│→│6c. Forma  │→║ 7. Bateria  ║
  │ dois rt.  │ │ (LSP)    │ │ idêntico   │ │ POST memór.│ │ negada    │ ║ byte-a-byte ║
  └───────────┘ └──────────┘ └────────────┘ └────────────┘ └───────────┘ └═════════════┘
     ↑_______________________________________________________________________|
     divergiu → diagnosticar, corrigir e repetir
                                      ↓
  ENTREGAR
  ┌──────────────────────┐   ┌──────────────────────────┐   ┌────────────────────────┐
  │ 8. Rotear no nginx   │ → │ 8b. Abas e redireciona-  │ → │ 9. Registrar e commit  │
  │    (location ou map) │   │     mentos que voltam    │   │    (local, por lote)   │
  └──────────────────────┘   └──────────────────────────┘   └────────────────────────┘
```

> Os **dois laços** são o que distingue isto de uma conversão de sintaxe.
> A versão navegável deste diagrama está no documento vivo:
> https://claude.ai/code/artifact/4b8da755-1649-4453-a133-3cbeacfebea9

Os dois laços tracejados são o que distingue este procedimento de uma conversão de sintaxe. O Rector **não converge numa passada** — já precisou de três —, então o passo 4 repete até relatar zero arquivos alterados. E a bateria do passo 7 não é um relatório final: cada tela divergente vira um diagnóstico, uma correção pontual e uma nova rodada. O módulo `iss` precisou de **quatro**.

## Antes de começar — o ambiente

### 1. Subir os quatro containers

A ordem importa: o 8.5 e o proxy dependem da rede que o 7.4 cria.

Na primeira vez, siga a seção *Como rodar o projeto hoje* do `README.md` (clone, banco, senha). Depois disso:

```bash
docker volume create ecidade_sessions && docker volume create ecidade_tmp
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d
# como root DENTRO do container: varios desses arquivos pertencem ao www-data, e um chmod
# no host falha neles (o "; true" no fim impede que uma falha aborte o resto)
docker exec -u root ecidade_php74 sh -c 'chmod 1777 /tmp; cd /var/www/html; chmod -R 777 storage bootstrap/cache; chmod 777 extension/log tmp arquivos; chmod 666 extension/log/*.log; true'
docker compose -f docker-compose.php85.yml up -d
docker compose -f docker-compose.proxy.yml up -d
```

> **Imagem do 8.5 anterior a 21/11/2026?** Desde essa data o `docker/php85-apache/Dockerfile` instala o LibreOffice
> Writer, como o 7.4: sem ele, os relatórios que viram PDF pelo `soffice` (Agata, `db_stdClass::ex_oo2pdf`) falham só no
> 8.5. Para conferir: `docker exec ecidade_php85 ls /usr/bin/soffice`. Se não existir, reconstrua a imagem:
> `docker compose -f docker-compose.php85.yml up -d --build`.

**Depois de reiniciar a máquina** os containers ficam parados — e qualquer comando com `docker exec` falha com
`container ... is not running`. Religue nesta ordem, **sem** `docker compose down` (o banco não tem volume de
persistência: `down` apaga os dados; `--remove-orphans` apaga os quatro containers):

```bash
docker start ecidade_database ecidade_php74
docker start ecidade_php85 ecidade_proxy
docker exec -u root ecidade_php74 chmod 1777 /tmp
```

### 2. Conferir que está tudo no ar

```bash
docker ps --filter name=ecidade --format '{{.Names}}\t{{.Status}}'   # 4 containers
stat -c '%n %A' ecidade/tmp ecidade/arquivos                         # ambos drwxrwxrwx
stat -c '%n %A' ecidade/extension/log/*.log                          # os ARQUIVOS -rw-rw-rw-
```

> **A linha do `chmod 666` nos arquivos de log não é detalhe.** Se eles pertencerem ao host em modo 664, o Logger lança erro fatal antes de qualquer saída e **toda** tela autenticada devolve HTTP 500 com corpo vazio — nos dois runtimes — enquanto o `login.php` segue respondendo 200. Parece defeito grave de migração e é permissão de arquivo.

> **Sem `tmp/` e `arquivos/` graváveis, 11% das telas falham antes de executar** e passam na bateria por falharem igual nos dois. Comparabilidade sem cobertura — o tipo mais inútil de equivalência.

### 3. Instalar o Rector

Ele vive em `ecidade/tmp/rector/`, que é ignorado pelo git — **não sobrevive a um clone novo**. A configuração e as regras, essas são versionadas em `scratchpad/`.

```bash
docker exec -i ecidade_php85 sh -c '
  mkdir -p /var/www/html/tmp/rector && cd /var/www/html/tmp/rector
  [ -f composer.json ] || composer init --no-interaction --name=ecidade/rector-exp >/dev/null 2>&1
  composer require --no-interaction --quiet rector/rector:^2.0
  ./vendor/bin/rector --version' </dev/null
```

### 4. Prova de fumaça — antes de culpar o seu porte

Pegue uma sessão autenticada e requisite uma tela de módulo **já verificado**. Rode isto **no começo de cada dia de
trabalho** (e depois de reiniciar a máquina): vários passos (nível 3, bateria, ciclos de guarda) leem o `/tmp/sid.txt`, e o
`/tmp` da máquina se apaga ao desligar.

```bash
# a sessao MAIS RECENTE (ls -t). O sess_?* exclui um arquivo "sess_" sem identificador, que aparece
# quando alguem requisita com o cookie vazio -- e que, por ordem alfabetica, vinha primeiro e dava SID vazio
SID=$(docker exec -i ecidade_php74 sh -c \
  'ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_?*) | head -1' </dev/null | sed 's#.*/sess_##' | tr -d '\r\n')
echo "${#SID}"                  # TEM de dar 40; 0 = nao achou sessao
echo "$SID" > /tmp/sid.txt
docker exec -u root -i ecidade_php74 sh -c \
  "cp /var/lib/php/sessions/sess_$SID /tmp/_d.bak && chmod 666 /tmp/_d.bak" </dev/null

curl -s -o /dev/null -w '%{http_code} %{size_download}\n' \
  -b "ECIDADEWINDOWMAIN=$SID" http://localhost:8080/cem1_campas001.php
```

**Na mesma sessão do terminal, aponte o `cmp.py` e o `escrita_post.py` para a pilha da raiz.** Na `base-php85` os dois
são as versões da suíte de regressão e, sem isto, testam as portas 8074/8185 (`ecidade74_*`), não a 8080/8085. O
`verifica_lote.py` e o `nivel3.py` já fazem isso sozinhos; o `export` vale para os comandos à mão deste guia:

```bash
export REGRESSAO_REF_URL=http://localhost:8080 REGRESSAO_PHP_NOVO_URL=http://localhost:8085 \
       REGRESSAO_CONTAINER_REF=ecidade_php74 REGRESSAO_CONTAINER_PHP_NOVO=ecidade_php85 \
       REGRESSAO_CONTAINER_BANCO=ecidade_database
```

| Saída | Significa |
| --- | --- |
| `200` e alguns milhares de bytes | ambiente são, pode começar |
| `500` e 0 bytes | problema de **ambiente**, não do seu porte — volte ao passo 2 |
| `200` e poucas dezenas de bytes | a sessão não vale (vazia ou vencida): entre em `http://localhost:8090` com `dbseller`/`dbseller` e rode de novo |

### 5. Duas proibições

- **Nunca alterar `docker-compose.yml`.** É a referência funcional do experimento.
- **Nunca commitar `docker/database/ecidade_base.sql`** — são 314 MB. Já entrou por engano num `git add -- docker/` e precisou ser removido por `amend`.

## O fluxo de uma área — comece por aqui

Os passos 1 a 9 deste guia portam **um lote**. O trabalho, porém, é organizado por **área do menu** (Tributário, Educação,
Saúde…), e uma área vira vários lotes. A moldura em volta dos passos é esta:

```
 A. branch da área ← base-php85
 B. dimensionar a área e dividir em lotes
 C. para cada lote, UM POR VEZ:  passos 1 → 9  (commit local, sem push)
 D. fim da área: bateria completa → conferência pelo proxy → registro → push → PR para base-php85
```

### A. Criar a branch e reservar os arquivos

Cada área nasce da `base-php85`, para onde as áreas concluídas voltam por PR:

```bash
git fetch origin
git checkout -b <area>/php85-migrado origin/base-php85      # ex.: educacao/php85-migrado
```

**Reserve no quadro antes de mexer.** O grupo coordena quem mexe em qual arquivo pelo quadro do servidor MCP
(`.mcp/README.md`): `reivindicar_arquivo` para cada arquivo do lote, depois que o passo 1 disser quais são. A reserva
vence em 4 horas; chamar de novo renova. O quadro é o arquivo `.mcp/estado/trabalho.json`, versionado: depois de
reservar, faça um commit **só dele**. O MCP recusa arquivo de outra área (`ECIDADE_MCP_AREA`); um prefixo que a tabela do
grupo (`CONTRIBUINDO.md`, *Divisão por área*) não cobre é `sem_area`, e um arquivo de outra área se combina antes com o
dono. No fim da área, `liberar_arquivo` com `concluido=true` marca os arquivos como concluídos (ver D).

**Commits no formato do grupo** (`CONTRIBUINDO.md`): `PHP8-NN: descrição curta`, com `NN` o número da tarefa da área;
`git add` arquivo por arquivo (nunca `-A`); o que o Rector fez num commit, a correção à mão em outro.

### B. Dimensionar e dividir em lotes

```bash
python3 scratchpad/dimensiona.py
```

```
Area                   Mod  Menu Faltam Fant.  Univ.  Pago A alterar
ASSISTÊNCIA SOCIAL       2    68     57     1   1901   726        43
CIDADÃO                  1    40     35     5   1828   709        28
...
```

`Menu` são as telas de menu da área, `Faltam` as que ainda vão ao 7.4, `Fant.` as que o menu cita mas não existem em disco
(quebram igual nos dois; só se registram), `A alterar` os arquivos que o lote vai mudar.

#### Quais prefixos migrar

**O prefixo não se escolhe: ele vem do menu.** Cada tela é um arquivo (`soc1_cidadao001.php`), e o começo do nome antes do
número é o prefixo (`soc`). Os prefixos de uma área são os das telas que o menu dela abre — e o banco sabe quais são
(`atendcadarea` → `db_menu` → `db_itensmenu`). Este script faz a consulta e cruza com o proxy:

```bash
python3 scratchpad/prefixos_area.py ASSIST     # o inicio do nome da area no banco: ASSIST, CIDAD, GESTOR, INTEGRA...
```

```
prefixo  telas no 8.5 faltam em disco  outras areas com telas desse prefixo ainda no 7.4
soc         44      0     44       87  -
hab         19      6     13       52  -
pro          1      1      0      337  -
rec          3      3      0      279  -

faltam 57 telas
```

Como ler (Assistência Social, 12/11/2026):

| Coluna | Significa |
| --- | --- |
| `telas` | telas de menu da área com esse prefixo (as fantasmas não contam) |
| `no 8.5` | as que o proxy já manda ao 8.5 — outra área já as migrou (`pro`, `rec`) ou parte delas (`hab`: 6 vieram com a Configuração) |
| `faltam` | **o que você vai migrar.** Prefixo com `faltam 0` está pronto: ignore |
| `em disco` | os `.php` do prefixo inteiro, de todas as áreas e fora do menu (popups, `.RPC.php`, abas) |
| outras áreas | áreas **ainda não migradas** que também têm telas desse prefixo no 7.4 |

Então, aqui, os prefixos a migrar são **`soc` e `hab`**. A soma de `faltam` tem de bater com o `Faltam` do
`dimensiona.py` (57 = 57).

#### Como cada prefixo será roteado — é o que define o lote

| Situação do prefixo | Roteamento | Lote |
| --- | --- | --- |
| nenhuma outra área pendente **e** `em disco` não muito maior que `telas` (`soc`: 44 de 87; `hab`: 19 de 52) | **`location`** por prefixo (passo 8) | o prefixo inteiro: `python3 scratchpad/enumera.py <pref>` |
| outra área pendente, **ou** `em disco` muito maior que `telas` (`con` no Cidadão: 4 telas, 1.556 arquivos) | **`map`** por lista, gerada do banco (*Passo D* de *Quando o prefixo serve várias áreas*) | só as telas da área: `TELAS=@/tmp/telas_lote.txt python3 scratchpad/enumera.py <nome-do-lote>` (uma tela por linha, com a grafia do disco e caminho **absoluto** — o script muda para `ecidade/`; o `<nome-do-lote>` vira só o nome dos arquivos de saída) |

Na dúvida entre os dois, meça o custo: `python3 scratchpad/enumera.py <pref>` dá o `A ALTERAR` do prefixo inteiro; compare
com o das telas da área (seção *Quando o prefixo serve várias áreas*, Passo C). Rotear pelo `location` manda **todos** os
arquivos do prefixo ao 8.5 — inclusive os de outras áreas —, então todos precisam estar portados.

Vários prefixos pequenos podem ir num lote só (a Assistência Social é um lote: `soc` + `hab`, com
`python3 scratchpad/enumera.py soc` e `python3 scratchpad/enumera.py hab`, e o Rector rodado sobre as duas listas de
alvos). Lote grande (mais de ~300 arquivos a alterar) se divide por subprefixo (`sau1_`, `sau2_`…). Registre a divisão em
`docs/registro/area-<área>.md` antes de começar.

### C. Um lote por vez

Para cada lote: passos 1 a 9. Ao terminar, **commit local** (passo 9) e **pare** — o próximo lote começa limpo.
A verificação (4b a 7) roda de uma vez com `scratchpad/verifica_lote.py` (ver *Verificar o lote de uma vez*).

**Cada passo em uma linha**, na ordem (exemplo do lote `soc` + `hab` da Assistência Social; rode da raiz do repositório e
olhe o resultado de cada um antes de seguir — os que mudam algo só mudam com `--aplicar`):

| Passo | Comando |
| --- | --- |
| prova de fumaça (início do dia) | o `verifica_lote.py` e o `nivel3.py` já fazem; à mão, *Antes de começar*, 4 |
| 1 — enumerar | `python3 scratchpad/enumera.py soc` e `python3 scratchpad/enumera.py hab` |
| 4 — Rector | `python3 scratchpad/rector_lote.py soc hab` → conferir as regras → `... --aplicar` |
| 4b a 7 — verificar | `python3 scratchpad/verifica_lote.py as soc hab` → ler o `RELATORIO.md` |
| corrigir o que apareceu | `guarda_ciclo.py` / `campo_ciclo.py` / `negada_corrige.py` / à mão (receituário) → verificar de novo |
| nível 3 | `python3 scratchpad/nivel3.py --candidatas soc hab` → `python3 scratchpad/nivel3.py soc1_visitatipo001` |
| 8 — rotear | `python3 scratchpad/rotear.py location soc hab` → conferir → `... --aplicar` |
| 8b — abas e redirecionamentos | `python3 scratchpad/rotear.py 8b ASSIST` |
| 9 — commit | `git add` / `git commit` (passo 9) |

- **A bateria do passo 7 é só do lote.** Se o lote mexeu no núcleo ou numa classe que muitas telas alcançam, rode também
  uma **bateria dirigida** às telas já roteadas que chegam ao trecho alterado (ver *Preciso refazer a bateria dos outros
  módulos?*).
- **Não envie ao GitHub no meio da área.** Os commits de lote ficam locais até a bateria completa do fim. Se ela achar uma
  regressão, `git bisect` entre os commits de lote acha o culpado.

### D. Fim da área

**1. Bateria completa** — todas as telas do `location` e todas as do `map`. Leva **cerca de 3 horas**; antes, zere o log do
banco, que cresce gigabytes com os erros de SQL das baterias (`sudo truncate -s 0 $(docker inspect -f '{{.LogPath}}' ecidade_database)`).

**Em um comando:** `python3 scratchpad/verifica_lote.py fim-<area> --tudo --base origin/base-php85` — roda todos os
passos de verificação sobre tudo o que a área alterou, a bateria no `location` e no `map`, separa as divergências novas
das conhecidas e diagnostica as novas (ver *Verificar o lote de uma vez*). **O `--base origin/base-php85` é obrigatório:**
sem ele o script mede contra o `master` e pega a migração de todas as áreas, não só a sua. Na Assistência Social
(21/11/2026): 544 arquivos, 535 classes e 129 telas. Os comandos abaixo são o mesmo, à mão (com o `export` da
*Prova de fumaça*).

```bash
SID=$(cat /tmp/sid.txt)      # ver "Prova de fumaça"
# (a) telas do location: os prefixos sao lidos do proprio nginx.conf
LOC=$(grep -oP 'location ~\* \^\(\?:/w/\[0-9\]\+\)\?/\(\?:\(\?:\K[^)]+' docker/proxy/nginx.conf)
python3 scratchpad/cmp.py "$SID" "^(?:$LOC)[0-9]*_" /tmp/bat_location.txt > /tmp/bat_location.log 2>&1
# (b) telas do map, com a grafia do disco (o map guarda em minuscula)
python3 - > /tmp/map_telas.txt <<'PY'
import os, re
disco = {f.lower(): f for f in os.listdir('ecidade')}
for l in open('docker/proxy/faseb_map.conf'):
    m = re.match(r'\s+(\S+)\s+php85;', l)
    if m and m.group(1) in disco: print(disco[m.group(1)])
PY
ONLY=$(paste -sd, /tmp/map_telas.txt) python3 scratchpad/cmp.py "$SID" '^$' /tmp/bat_map.txt > /tmp/bat_map.log 2>&1
tail -1 /tmp/bat_location.log /tmp/bat_map.log
```

Em 12/11/2026 eram **9.332** telas no `location` (uma pulada: `iss4_siss002`, que contata serviço externo) e **1.312** no `map`.
**Compare as divergentes, nome a nome, com a lista da área anterior** (`docs/registro/area-<área anterior>.md`, seção
*Bateria completa do fim da área*, e `docs/divergencias-conhecidas.md` quando existir). Só interessa o que **entrou**: cada
nome novo é regressão até prova em contrário. Há uma divergência que vai e volta sozinha: `mer_subitem004` diverge só em
fim de semana (`mktime(null)`).

**2. Conferência pelo proxy, tela de menu por tela de menu.** A bateria prova que as telas são iguais; esta conferência
prova que o usuário **chega** ao 8.5. Troque `ASSIST` pelo início do nome da área no banco (`TRIBUT`, `EDUCA`, `SA`,
`CONFIG`, `CIDAD`, `GESTOR`, `INTEGRA`…):

```bash
python3 - ASSIST <<'PY'
import os, subprocess, sys
area = sys.argv[1]
sql = ("SELECT DISTINCT lower(split_part(di.funcao,'?',1)) FROM configuracoes.atendcadareamod am "
       "JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea "
       "JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item "
       "JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item "
       "JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho "
       f"WHERE a.at25_descr ILIKE '%{area}%' AND di.funcao ~* '\\.php'")
telas = subprocess.run(["docker","exec","-i","ecidade_database","psql","-U","postgres","-d","ecidade","-At","-c",sql],
                       capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("latin-1").split()
disco = {f.lower(): f for f in os.listdir("ecidade")}
c = {"8.5": 0, "7.4": 0, "fantasma": 0}
for t in telas:
    if t not in disco: c["fantasma"] += 1; continue
    h = subprocess.run(["curl","-sI",f"http://localhost:8090/w/2/{disco[t]}"], capture_output=True).stdout.decode("latin-1")
    rt = "8.5" if "PHP-8.5" in h else "7.4"
    c[rt] += 1
    if rt == "7.4": print("NO_7.4", disco[t])
print(f"{area}: {c['8.5']} no 8.5, {c['7.4']} no 7.4, {c['fantasma']} fantasmas (de {len(telas)})")
PY
```

Saída esperada, na Configuração: `CONFIG: 204 no 8.5, 0 no 7.4, 5 fantasmas (de 209)`. **Tem de dar `0 no 7.4`.** Cada
`NO_7.4` é uma tela de menu que ficou fora do roteamento — rotear (e portar, se não foi) antes de seguir.

**3. Ensinar aos scripts que a área acabou.** `scratchpad/dimensiona.py` tem a tupla `JA` (áreas concluídas) e uma cópia
do regex do `location`; `scratchpad/redirecionamentos.py` tem outra cópia do regex. O `rotear.py location --aplicar` já
atualiza as duas cópias do regex; a tupla `JA` continua à mão. Sem isso, a próxima medição conta esta área como pendente.

**3b. Marcar os arquivos como concluídos no quadro.** `liberar_arquivo(caminho=..., concluido=true)` para cada arquivo que
a área alterou (`git diff --name-only origin/base-php85... -- ecidade/`). Não sobrescreva um arquivo que já está
concluído por outra pessoa: o `liberar_arquivo` troca o dono do registro. Commit só do `.mcp/estado/trabalho.json`.

**4. Registrar** (passo 9) — a conclusão em `docs/registro/area-<área>.md` (lotes, bateria completa, proxy) e o estado no
`CLAUDE.md`.

**5. Enviar e abrir a PR:**

```bash
git push -u origin <area>/php85-migrado
```

Abra a PR no GitHub com base **`base-php85`** (não `master` nem `base-php74`), com `Closes #NN` da issue da área. Como a
`base-php85` não é a branch padrão do repositório, **o GitHub não fecha a issue sozinho no merge**: feche à mão, com um
comentário apontando a PR. Depois do merge, a próxima área parte da `base-php85` atualizada (`git fetch` e passo A).

## Passo 1 — enumerar o universo

**O que é:** descobrir *todos* os arquivos que o módulo usa. Não são só os que começam com o prefixo — no módulo `fis`, 353 telas puxaram **699 arquivos**.

### Comando

```bash
python3 scratchpad/enumera.py <pref>
```

Gera dois arquivos: `ecidade/tmp/<pref>_universo.txt` (tudo que o módulo alcança) e `ecidade/tmp/<pref>_alvos.txt` (só o que precisa de alteração).

### Saída esperada

```
telas (prefixo fis[0-9]*_) : 353
universo (6 frentes)       : 699   | ja pago: 180
                           | A ALTERAR: 384

  $this->X == <literal>    730 ocorrencias em  210 arquivos
  split(                   627 ocorrencias em  185 arquivos
  parse_str 1 arg          230 ocorrencias em  230 arquivos
  construtor PHP4          134 ocorrencias em  134 arquivos
```

### Conferências obrigatórias

**1. O número de telas bate com o disco?**

```bash
ls ecidade | grep -icE '^<pref>[0-9]*_.*\.php$'
```

Tem de dar **exatamente** o mesmo número que o enumerador reportou. Se der menos, há variante de prefixo escapando.

**2. Existe variante de prefixo?** Já aconteceu três vezes.

```bash
ls ecidade | grep -ioE '^<pref>[a-z]*[0-9]*_' | sort -u
```

| O que aparece | O que significa |
| --- | --- |
| só `fis1_`…`fis4_` | normal |
| `itb1_` **e** `itbi_` | duas variantes — o regex precisa de `itbi?` |
| `jur1_` **e** `jur01_` | dois dígitos — o nginx precisa de `[0-9]*`, não `[0-9]?` |
| `Cem1_` com maiúscula | 29 arquivos assim na base — exige `re.IGNORECASE` e `location ~*` |

**3. Apareceu categoria que não está no catálogo (`docs/registro/`)?** → **PARE e investigue** antes de transformar. Toda categoria nova do projeto veio daí.

> Os números acima são de outubro. O rótulo `(6 frentes)` ficou velho no script: ele já percorre as **nove**. Por isso o
> universo hoje sai bem maior — a 9ª frente segue as classes com namespace de `src/` até `classes/` (no lote 1 de
> Patrimonial, de 1.727 para 2.801 arquivos). É normal: a maior parte já está paga.
>
> **`A ALTERAR` é uma cota superior, não o que o Rector vai mudar.** Até 23/11/2026, o detector de `$this->X == <literal>`
> casava com a própria guarda já aplicada (ver *As armadilhas*), então arquivos já portados voltavam na lista. No `soc`
> (12/11/2026): `A ALTERAR: 20`, e o Rector mudou **3**; no `mer` (22/11/2026), 934 contra 49 de verdade. Desde
> 23/11/2026 ele pula a comparação com a guarda `=== 0` na mesma linha, e grava os alvos por categoria em
> `ecidade/tmp/<pref>_categorias.tsv`. Mesmo assim, quem diz o número real é o passo 4.

### Por que nove frentes, e não só o prefixo

Cada frente nasceu de um defeito real que custou retrabalho:

| Frente | O que acha | A lacuna que fechou |
| --- | --- | --- |
| Prefixo (`IGNORECASE`) | as telas | `Cem1_legista001.php` ficava de fora |
| Includes transitivos | a base do universo | — |
| Nomes citados em strings | o que o JavaScript abre | 13 arquivos do ITBI, 9 quebrados |
| `new cl_*` | classes por autoload | 62 classes, 2 em módulos "prontos" |
| `db_utils::getDao('x')` | classes que não citam o próprio nome | 16 classes no `fis` |
| `dbagata/` com `.class` e `.inc` | biblioteca vendorizada | 216 arquivos invisíveis a `*.php` |
| Pasta inteira da lib | o resto da pasta | `fpdf151/` tinha 194, eu portara 2 |
| Classes de `model/` e `std/` por nome curto | `new Folha…` sem `cl_` | 13ª lacuna (RH): classes do cálculo da folha |
| Classes com namespace (`scratchpad/ns_fecho.py`) | `use ECidade\…`, `new \ECidade\…` e serviços do `bootstrap.php`, em `src/`/`app/`/`api/` | 15ª lacuna (Patrimonial) |

Para medir uma lacuna nova: `TELAS=@arquivo` aceita a lista de partida, e `SEM_NS=1` desliga a 9ª frente (compare os
alvos com e sem).

**Três dessas lacunas nenhuma varredura achou** — apareceram quando alguém navegou o sistema e um campo não aceitou digitação. Se você tiver acesso ao sistema rodando, **navegue o módulo** depois de portar.

## Passos 2 e 3 — classificar antes de transformar

**O que é:** decidir, ocorrência por ocorrência, qual conversão se aplica. **Nem toda ocorrência da mesma categoria tem a mesma correção**, e errar aqui grava dado errado sem erro nenhum.

### Comando — classificar os `split()`

```bash
(cd ecidade && python3 - <<'PY'
import re
alvos=[l.strip() for l in open("tmp/<pref>_alvos.txt") if l.strip()]
lit={}; rgx=[]; js=0
for f in alvos:
    b=open(f,"rb").read()
    scr=[(m.start(),m.end()) for m in re.finditer(rb'<script\b.*?</script>',b,re.I|re.S)]
    for m in re.finditer(rb'(?<![A-Za-z0-9_>$.])split\s*\(\s*(["\'])(.*?)\1',b,re.S):
        if any(a<=m.start()<z for a,z in scr): js+=1; continue
        sep=m.group(2)
        if re.search(rb'[+*?\[\]().^$\\|{}]',sep): rgx.append((f,sep))
        else: lit[sep]=lit.get(sep,0)+1
    for m in re.finditer(rb'(?<![A-Za-z0-9_>$.])split\s*\((?!\s*["\'])', b):
        if not any(a<=m.start()<z for a,z in scr): rgx.append((f,b'<nao-literal>'))
print(f"literais: {sum(lit.values())}  {dict(list(lit.items())[:6])}")
print(f"REGEX/variavel: {len(rgx)}  {rgx[:3]}")
print(f"dentro de <script> (preservar): {js}")
PY
)
```

### Como ler o resultado

| Resultado | O que fazer |
| --- | --- |
| `literais: 627 {b'#': 519, b'-': 16}` | tudo mecânico, pode seguir |
| `REGEX/variavel: 3` | **olhe cada um** antes de transformar |
| `dentro de <script>: 8` | é JavaScript, **não é PHP** — não tocar |

### Por que isso importa

Separador **literal** (`"#"`, `","`) vira `explode`. Separador com metacaractere de regex (`+ * ? [ ] ( ) | . ^ $ \`) vira `preg_split`. Trocar um pelo outro produz dado errado em silêncio:

```
split(" +", "um   dois")    → ["um", "dois"]        (POSIX: um ou mais espaços)
explode(" +", "um   dois")  → ["um   dois"]         A STRING INTEIRA, sem separar
```

> Na prática o Rector resolve isso sozinho — ele converte **sempre** para `preg_split`, preservando a semântica POSIX. Esta classificação serve para você **saber o que esperar** e conferir o resultado dele.

### Uma armadilha do próprio classificador

No `cad`, este script acusou um `split` de separador variável que, olhado de perto, era `split( ",", $x)` — **literal**, com um espaço antes das aspas. O `\s*` casava por *backtracking*. Lembre: quando a ferramenta acusa algo estranho, **abra o arquivo e olhe a linha** antes de agir.

## Passo 4 — transformar com o Rector

**O que é:** aplicar as conversões mecânicas. O Rector usa AST (entende a estrutura do código), então não toca em comentário nem erra parênteses, que é onde um `sed` erraria.

**A regra que manda em tudo:** os dois containers montam o **mesmo diretório**, então cada arquivo precisa rodar em PHP 7.4 *e* em 8.5. Um arquivo que não parseia no 7.4 derruba o runtime que serve o login e todos os módulos ainda não migrados.

### Em um comando — `rector_lote.py`

```bash
python3 scratchpad/rector_lote.py soc hab              # SO SIMULA: mostra as regras que disparariam
python3 scratchpad/rector_lote.py soc hab --aplicar    # aplica e repete ate uma rodada alterar 0 arquivos
```

Ele faz tudo o que os blocos abaixo fazem: junta os alvos dos prefixos, copia a config e as regras para onde o container
lê, confere a sintaxe da config, roda a simulação (com os avisos `Deprecated` num arquivo) e classifica cada regra:

```
SIMULACAO (--dry-run, nada e gravado):
  28 arquivos seriam alterados, 0 erros do Rector
     21  EregToPregMatchRector                         conhecida
     21  GuardaComparacaoLiteralRector                 conhecida
     21  Php4ConstructorRector                         conhecida
      7  ParseStrComExtractRector                      conhecida
```

- **conhecida**: já conferida e aceita em lotes anteriores (a lista e o motivo de cada uma estão no script, `REGRAS_ACEITAS`);
- **RESSALVA**: aceita, mas exige uma conferência depois (o script diz qual — hoje só a `OptionalParametersAfterRequiredRector`);
- **NOVA**: nunca conferida. O script mostra as linhas que ela mudaria e **recusa o `--aplicar`** até você seguir o
  *Protocolo para regra nova* (abaixo) e rodar com `--aceitar NomeDaRegra` — ou bani-la.

Também avisa se há construtor PHP 4 nos alvos e o `Php4ConstructorRector` não apareceu (o pin de versão quebrado). Com
`--aplicar`, repete até zerar e para se surgir regra nova no meio. Saídas em `ecidade/tmp/rector_lote/<data-hora>/`.
As seções abaixo explicam cada etapa e continuam valendo para entender o resultado ou fazer à mão.

> **Não mexa no `withParallel(120, 2, 16)` do `scratchpad/rector-curado.php`.** São 2 processos: o padrão abre um por
> núcleo (até 1,2 GB cada) e travou um notebook de 7,4 GB. E **1 processo não serve**: no lote 1 da Assistência Social
> (20/11/2026), com 1 processo o Rector processou só 144 dos 516 alvos (9 blocos de 16) e terminou sem nenhum erro.
> Cache, *timeout*, `memory_limit` e LATIN-1 foram testados e descartados; a causa era o processo único.

### Comando

```bash
# 1. copiar config e regras para dentro do container (scratchpad/ nao e montado)
cp scratchpad/rector-curado.php ecidade/tmp/rector/rector-curado.php
mkdir -p ecidade/tmp/rector/rector-rules
cp scratchpad/rector-rules/*.php ecidade/tmp/rector/rector-rules/

# 2. conferir que a propria config nao tem erro de sintaxe
docker exec -i ecidade_php85 php -l /var/www/html/tmp/rector/rector-curado.php </dev/null

# 3. SIMULAR primeiro (--dry-run nao grava nada) e ver quais regras disparariam.
#    O 2> manda os avisos "Deprecated" para um arquivo -- ver a nota logo abaixo.
#    Com --dry-run o comando SAI COM CODIGO 2 quando ha mudancas: e o normal, nao e erro.
docker exec -i -e ALVOS=/var/www/html/tmp/<pref>_alvos.txt ecidade_php85 \
  php -d memory_limit=3G /var/www/html/tmp/rector/vendor/bin/rector process --dry-run \
  --config /var/www/html/tmp/rector/rector-curado.php \
  --no-progress-bar --output-format=json </dev/null > /tmp/r1.json 2> /tmp/r1.err

# 4. ver quais regras dispararam
python3 -c "
import json, collections
d=json.load(open('/tmp/r1.json')); fd=d.get('file_diffs',[]) or []
c=collections.Counter()
for f in fd:
    for r in f.get('applied_rectors',[]): c[r.split(chr(92))[-1]]+=1
print('arquivos:', len(fd), ' erros:', len(d.get('errors',[]) or []))
for k,v in c.most_common(): print(f'  {v:5d}  {k}')"

# 5. se so apareceram regras conhecidas (ver "As tres conferencias"), APLICAR:
#    o mesmo comando do passo 3 SEM o --dry-run, e repetir ate dar "arquivos: 0"
```

### Saída esperada

```
arquivos: 196  erros: 0
     99  ParseStrComExtractRector
     96  EregToPregMatchRector
     86  GuardaComparacaoLiteralRector
     80  Php4ConstructorRector
```

Medido no `soc` + `hab` (12/11/2026): `soc` 3 arquivos e `hab` 28, as mesmas quatro regras, `erros: 0`.

> **Os avisos `Deprecated:` são esperados — ignore-os.** O Rector carrega o autoloader do projeto, que traz o `vendor/`
> do Laravel (Guzzle, PsySH, Zend Diactoros, PHPUnit). Essas bibliotecas antigas declaram parâmetros de um jeito que
> o PHP 8.4+ marca como obsoleto, e cada uma imprime uma linha ao ser carregada — umas 15 por execução, sempre as mesmas,
> **antes** de o Rector olhar qualquer arquivo seu:
>
> ```
> Deprecated: GuzzleHttp\Promise\queue(): Implicitly marking parameter $assign as nullable is deprecated ...
> Deprecated: Psy\info(): Implicitly marking parameter $config as nullable is deprecated ...
> ```
>
> Não dizem nada sobre o seu módulo. Se você rodar sem o `2> /tmp/r1.err`, elas cobrem o terminal; com ele, ficam no
> arquivo. O que importa é a contagem do passo 4 (`erros: 0`). Se **outra** coisa aparecer no `/tmp/r1.err` (`Fatal`,
> `Killed`, `SEM ALVOS`), aí sim pare.
>
> Outro erro que parece do Rector e não é: `container ... is not running`. Os containers pararam (reinício da máquina) —
> ver *Antes de começar*.

### As três conferências

**1. Repita até dar zero.** O Rector **não converge numa passada**, e isso é intermitente. Numa execução real: 163 arquivos, depois mais 83, depois 0. Rode o comando de aplicar (o 3 **sem** `--dry-run`) e a contagem do 4 de novo, até `arquivos: 0` — a saída JSON lista os arquivos que ele acabou de mudar.

**2. `Php4ConstructorRector` apareceu na lista?** Se o módulo tem construtores PHP 4 (o passo 1 disse quantos) e essa regra **não** aparece, o pin de versão quebrou. Sem `->withPhpVersion(PhpVersion::PHP_80)` na config, o Rector lê o `composer.json` do projeto (`">=7.4"`; na base antiga era `">=5.6.4"`) e **desliga em silêncio** toda regra com *version bonding*, reportando sucesso.

**3. Apareceu regra que você não conhece?** → siga o protocolo abaixo. **Não aceite.**

### Protocolo para regra nova — obrigatório

A denylist tem **40 regras** (12/11/2026) e já cresceu várias vezes. Toda vez foi uma regra que parecia funcionar.

```bash
# 1. ver EXATAMENTE o que ela fez
python3 -c "
import json
d=json.load(open('/tmp/r1.json'))
for f in d.get('file_diffs',[]):
    rs={r.split(chr(92))[-1] for r in f.get('applied_rectors',[])}
    if 'NomeDaRegraRector' in rs:
        print('###', f['file'])
        for l in f['diff'].split(chr(10)):
            if l[:1] in '+-' and l[:3] not in ('+++','---'): print('  ', l[:150])"

# 2. testar a construcao que ela emite nos DOIS runtimes
docker exec ecidade_php74 php -r '<a expressao nova>'
docker exec ecidade_php85 php -r '<a expressao nova>'
```

| Se o 7.4… | Veredito |
| --- | --- |
| não parseia (`??`, `??=`, `match`) | **banir** — derruba o runtime de referência |
| parseia mas a função não existe | **banir** — fatal só em execução, invisível ao `php -l` |
| dá resultado **diferente** do 8.5 | **banir** — regressão silenciosa |
| dá o mesmo resultado, mas a regra só moderniza | **banir** — o foco não é modernizar |
| dá o mesmo resultado e é exigida pelo PHP 8 | **aceitar** |

As seis que já foram banidas, para você reconhecer o padrão:

| Regra | O que fazia |
| --- | --- |
| `StrContainsRector` | emitia `str_contains()`, inexistente no 5.6 |
| `IfIssetToCoalescingRector` | emitia `??`, *parse error* no 5.6 |
| `WhileEachToForeachRector` | fazia rodar um laço que no 5.6 nunca executa |
| `StrEndsWithRector` | irmã da primeira, escapou por nunca ter disparado |
| `BinaryOpBetweenNumberAndStringRector` | `$x == ""` → `$x == 0`, divergindo em 2 de 6 valores |
| `RemoveExtraParametersRector` | **apagava a cláusula `WHERE` de um `DELETE`** |
| `BreakNotInLoopOrSwitchToReturnRector` | `break` → `return`, onde o 5.6 **mata o script** |
| `ListEachRector` | irmã da `WhileEachToForeach`: o Rector não vê o ponteiro interno já exaurido por um laço anterior. Os `each()` se tratam **à mão** (ver *Receituário*) |

E uma regra que **fica ligada, mas exige conferência**: `OptionalParametersAfterRequiredRector` dá `= null` a parâmetros
de um método e assim **muda a assinatura da classe mãe**. A filha que declara os mesmos parâmetros como obrigatórios deixa
de carregar no 8.5 (`must be compatible`). Para cada método que ela tocar, procure `extends <Classe>` na **base inteira**
(não só no universo) e espelhe os padrões na filha — foi o caso de `cl_cgs_und_ext` no lote 2 da Saúde. O passo 5b pega
o que escapar.

> Se o Rector reportar **`0 arquivos, 0 regras` sem mensagem de erro**, quase sempre a config tem erro de sintaxe. Por isso o passo 2 do comando existe.

### Como banir uma regra — procedimento completo

Seis passos. Já foi executado seis vezes neste projeto.

**1. Achar o nome completo da regra.** O Rector reporta só o nome curto; a config precisa do caminho inteiro.

```bash
F=$(find ecidade/tmp/rector/vendor/rector -name 'NomeDaRegraRector.php' | head -1)
echo "$(grep -am1 '^namespace' "$F" | sed 's/namespace //;s/;//')\\NomeDaRegraRector"
```

Saída, por exemplo: `Rector\Php80\Rector\Identical\StrEndsWithRector`

**2. Desfazer o que o Rector já escreveu.** A regra ruim **já está na árvore** — ele altera os arquivos de verdade.

```bash
git checkout -- ecidade/
git status --porcelain -- ecidade/ | wc -l     # TEM de dar 0
```

**3. Acrescentar a regra à denylist.** Em `scratchpad/rector-curado.php`, dentro do bloco `->withSkip([ ... ])`. Pode editar à mão ou usar este comando:

```bash
python3 - <<'PY'
p="scratchpad/rector-curado.php"; s=open(p,encoding="utf-8").read()
REGRA  = "Rector\\Php80\\Rector\\Identical\\StrEndsWithRector"   # <- do passo 1
MOTIVO = "emite str_ends_with(), medido como inexistente no 5.6"  # <- SEMPRE o porque
i = s.index("->withSkip([")
j = s.index("]);", i)
j = s.rindex("\n", 0, j) + 1                  # insere ANTES da linha do ]);
open(p,"w",encoding="utf-8").write(s[:j] + f"        // {MOTIVO}\n        {REGRA}::class,\n" + s[j:])
print("regra inserida")
PY
```

> **Escreva sempre o motivo medido no comentário.** Daqui a seis meses ninguém vai lembrar por que a regra está ali, e uma denylist sem justificativa é removida por engano na primeira limpeza.

**4. Conferir a sintaxe da própria config.** Este passo não é zelo: com erro de sintaxe nela, o Rector reporta **`0 arquivos, 0 regras` sem nenhuma mensagem de erro**.

```bash
cp scratchpad/rector-curado.php ecidade/tmp/rector/rector-curado.php
docker exec -i ecidade_php85 php -l /var/www/html/tmp/rector/rector-curado.php </dev/null
awk '/->withSkip\(\[/,/^\s*\]\);/' scratchpad/rector-curado.php | grep -c '::class'
```

O `php -l` precisa dizer `No syntax errors detected`, e a contagem precisa ter subido em 1.

**5. Rodar o Rector de novo**, do zero — passo 4, repetindo até `arquivos: 0`.

**6. Conferir que a regra sumiu da lista** de regras aplicadas. Se ainda aparecer, o nome completo está errado (passo 1) ou você editou a cópia dentro do container em vez do original em `scratchpad/`.

> **A config versionada é `scratchpad/rector-curado.php`.** A que o Rector lê é `ecidade/tmp/rector/rector-curado.php`, que é **ignorada pelo git**. Edite sempre a primeira e copie — editar só a segunda faz a correção se perder no próximo clone.

### Escrever uma regra própria

**Quando precisa:** quando a correção não é um *upgrade* de versão, e sim um **shim** que preserva a semântica do 7.4. O Rector não tem regra para isso porque, do ponto de vista dele, o código já está correto nas duas versões.

Este projeto tem duas, em `scratchpad/rector-rules/`:

| Regra | Linhas | Cobre |
| --- | --- | --- |
| `GuardaComparacaoLiteralRector` | 122 | `$this->X == "<literal>"` → guarda do 7.4 |
| `ParseStrComExtractRector` | 74 | `parse_str` de 1 argumento + `extract()` |

#### O esqueleto

```php
final class MinhaRegraRector extends AbstractRector
{
    public function getRuleDefinition(): RuleDefinition { /* descricao + exemplo */ }

    public function getNodeTypes(): array
    {
        return [Node\Stmt\Expression::class];   // em que tipo de no ela atua
    }

    public function refactor(Node $node): ?array
    {
        // null = nao mexe neste no
        // um no, ou array de nos = substitui
    }
}
```

#### Defeito 1 — laço infinito, e o processo morre sem rastro

Se a regra devolve um nó que **contém o original**, o PhpParser percorre os filhos do substituto e reencontra o original lá dentro. E o substituto **não passa por `enterNode`**, então qualquer checagem de forma que você tenha escrito nunca é alcançada.

O sintoma é o processo morrer com **`Killed`**, sem *traceback*, sem mensagem — é o gerenciador de memória do sistema matando o Rector.

**A barreira que funciona é marcar o próprio nó:**

```php
// no INICIO do refactor:
if ($n->getAttribute('ecidade_guardado') === true) {
    return null;
}
// ... e ANTES de embrulhar:
$n->setAttribute('ecidade_guardado', true);
return new BooleanOr(/* ... contendo $n ... */);
```

#### Defeito 2 — apaga comentários, em silêncio

Um nó novo **nasce sem atributos**, e os comentários do código ficam presos ao nó antigo, que você descartou. Nada avisa.

Medido: três arquivos perderam linhas como `//--- parser POST/GET` e blocos inteiros de código comentado.

**A correção é reaproveitar o nó original** em vez de criar outro:

```php
$chamada = $node->expr;        // pega o no que ja existe
$chamada->args[] = /* ... */;  // modifica ELE
$node->expr = $chamada;        // e devolve o mesmo no
```

#### Como saber se a regra está certa

Não confie na leitura. **Compare contra o ferramental antigo**, que ainda está versionado justamente para isso:

```bash
# 1. reconstruir o estado PRE-porte de alguns arquivos
mkdir -p /tmp/antes && cd /tmp/antes
git show <commit>^:ecidade/<arquivo> > <arquivo>

# 2. rodar os dois instrumentos sobre o mesmo ponto de partida
#    (porta.py = regex, rector-curado.php = AST)
# 3. comparar TRES arvores: original, saida do porta.py, saida do Rector
```

Foi assim que as duas regras foram validadas: **246 de 248 arquivos semanticamente idênticos**, e nos 2 em que divergiam **o Rector estava certo** — o `porta.py` tinha editado um `parse_str` que estava dentro de um comentário.

> **Sem a terceira árvore você não sabe quem mudou o quê.** Comparar só as duas saídas mostra que elas diferem, não qual das duas está certa.

## Verificar o lote de uma vez — `verifica_lote.py`

Depois do Rector (passo 4), os passos **4b, 5, 5b, 6, 6b, 6c e 7** rodam com **um comando só**, na ordem, e o resultado
sai num **relatório único**:

```bash
python3 scratchpad/verifica_lote.py <nome-do-lote> <prefixo> [<prefixo> ...]
python3 scratchpad/verifica_lote.py as soc hab                     # o lote soc + hab
python3 scratchpad/verifica_lote.py as soc hab --so 6b,6c          # so alguns passos
python3 scratchpad/verifica_lote.py as soc hab --continuar         # nao parar no primeiro problema
python3 scratchpad/verifica_lote.py as soc hab --base origin/base-php85   # lote ja commitado
```

Pré-requisitos: os containers no ar, o universo de cada prefixo gerado (`enumera.py <prefixo>`, passo 1) e o Rector já
aplicado. O script **não altera código nem banco**. Ele mesmo acha a sessão autenticada mais recente e confere que ela
vale antes da bateria (com sessão vencida, as duas portas devolveriam a mesma página de login e tudo pareceria idêntico).

No terminal sai uma linha por passo; o mesmo vai para o relatório:

```
Lote as-fim-area (TUDO): 544 arquivos, 535 classes, 87 + 42 telas (location + map)
Saida em ecidade/tmp/verif/as-fim-area-20261121-2132/

  4b  funcoes que so existem no PHP 8  OK         1 funcoes do PHP novas no diff, 0 ausentes no 7.4
  5   php -l nos dois runtimes         OK         544 arquivos, 0 erros novos (0 pre-existentes)
  5b  heranca (carga dos arquivos)     OK         10 arquivos, 0 so no 8.5 (0 falham nos dois)
  6   construtor (instanciar classes)  OK         535 classes, so artefatos conhecidos (0)
  6b  formulario lido errado (0 == "") OK         535 classes, so artefatos conhecidos (0)
  6c  forma negada != ""               OK         0 divergencias no lote (2853 fora do lote, ignoradas)
  7   telas byte a byte                INVESTIGAR 128/129 identicas, 1 divergencias novas, 0 timeout

Relatorio: ecidade/tmp/verif/as-fim-area-20261121-2132/RELATORIO.md
```

(Saída real da bateria do fim da Assistência Social, 21/11/2026, com `--tudo --base origin/base-php85`. A tela que
diverge, `soc2_declaracaoinss002`, é defeito da referência: o contêiner do 7.4 não tem o comando `file`.)

**O passo 7 diagnostica cada tela divergente sozinho.** A bateria só sabe *que* uma tela divergiu; o script então pede
cada divergente de novo aos dois runtimes, com os logs limpos, e põe no relatório o **motivo**: o erro fatal do PHP (com
arquivo e linha), os erros de SQL do PostgreSQL daquele pedido e, quando os dois respondem 200, o trecho onde as páginas
começam a diferir. E classifica pela tabela de decisão do passo 7. Duas divergências do `soc` depois do núcleo (21/11/2026), como saíram no relatório:

```
### soc2_beneficiosfamilia002.php
- 7.4: HTTP 200, 99 bytes; 8.5: HTTP 500, 3729 bytes
- Classificacao: REGRESSAO: quebra so no 8.5 -> corrigir
- erro do PHP no 8.5: Uncaught exception 'Error' with message 'Non-static method FamiliaRepository::getInstance()
  cannot be called statically' in model/social/FamiliaRepository.model.php on line 127

### soc2_declaracaoinss002.php
- 7.4: HTTP 200, 115 bytes; 8.5: HTTP 200, 154 bytes
- Classificacao: SILENCIOSA: 200 nos dois, conteudo diferente -> o tipo mais perigoso, ver o trecho
- erro de SQL no 8.5: erro de sintaxe em ou próximo a "\" no caractere 39
- erro de SQL no 7.4: erro de sintaxe em ou próximo a "\" no caractere 39
- as paginas comecam a diferir no byte 63:
```

As classificações possíveis: **REGRESSÃO** (quebra só no 8.5 → corrigir), **PRÉ-EXISTENTE** (quebra só no 7.4 →
registrar, não corrigir), **QUEBRA NOS DOIS** (não mexer; conferir se a causa é a mesma), **SILENCIOSA** (200 nos dois com
conteúdo diferente — a mais perigosa; o relatório mostra o trecho) e **NÃO REPRODUZIU** (identica no segundo pedido:
diferença ocasional). A classificação é um ponto de partida, não um veredito: o erro de SQL acima, por exemplo, acontece
**nos dois** e não é a causa do 500 — a causa é o erro do PHP. As páginas de cada lado ficam na pasta
(`7_corpo_<tela>_74.html` / `_85.html`). Os *timeouts* não são diagnosticados (repetir o pedido custaria mais 60 s cada).

(As duas eram reais: a primeira é do lote; a segunda já estava corrigida na branch `nucleo/correcoes-transversais`.)

**Tudo fica numa pasta só**, `ecidade/tmp/verif/<lote>-<data-hora>/`, e **só o `RELATORIO.md` precisa ser lido**: ele traz o
cabeçalho (branch, commit, quantos arquivos o lote alterou), a tabela-resumo e, para cada passo, o critério, os números e as
linhas que importam (as divergências, os artefatos que apareceram). Os outros arquivos da pasta são a saída bruta de cada
passo, para conferir ou diagnosticar. A pasta fica em `ecidade/tmp/`, ignorada pelo git, e sobrevive ao reinício da máquina.

| Situação | Significa | O que fazer |
| --- | --- | --- |
| `OK` | o critério do passo foi atingido | nada |
| `FALHA` | defeito, ou o teste não rodou inteiro (contagem não bate) | ler a seção do passo no relatório e a seção do passo neste guia |
| `INVESTIGAR` | há divergência a diagnosticar — pode ser regressão ou defeito pré-existente | diagnosticar cada uma (passo 7, *Diagnosticar uma divergência*) |
| `AVISO` | nada a corrigir, mas conferir (ex.: diff vazio — lote já commitado? use `--base`) | conferir |
| `PULADO` | fora do `--so`, ou não rodou porque um passo anterior falhou | — |

Por padrão ele **para no primeiro passo com problema**: se o `php -l` falhou, os resultados seguintes não valem nada. Depois
de corrigir, rode de novo (ou só o que falta, com `--so`). Os critérios de cada passo são os das seções abaixo — o script
apenas os aplica e conta as entradas e saídas de cada um, para que um "OK" nunca venha de um teste que não rodou.

**Para o código inteiro — `--tudo` (a bateria completa do fim da área):**

```bash
python3 scratchpad/verifica_lote.py fim-assist --tudo                    # ~3 h: rode no fim da área
python3 scratchpad/verifica_lote.py teste --tudo --amostra 40            # o mesmo com amostra, para testar antes
python3 scratchpad/verifica_lote.py fim-assist --tudo --conhecidas ecidade/tmp/verif/<anterior>/7_divergentes.txt
```

Em vez de prefixos, o universo são **os arquivos que a migração alterou** (diff contra o `master`) — 7.859 arquivos de código
e 3.142 classes em 16/11/2026 — e a bateria roda em **todas as telas que o proxy manda ao 8.5**, as do `location` e as do
`map`. As classes nunca portadas ficam de fora: são de áreas que o 7.4 ainda serve e divergem por construção.

O que muda no resultado é o critério do passo 7: com uma lista de **divergências conhecidas**, só as que ficarem **fora**
dela contam como possível regressão e são diagnosticadas; as conhecidas aparecem listadas, sem diagnóstico, e as conhecidas
que voltaram a sair idênticas são apontadas (para atualizar a lista). A lista padrão é o `docs/divergencias-conhecidas.md`
(as linhas marcadas "Corrigida" **não** contam: se uma delas voltar a divergir, é regressão); também serve o
`7_divergentes.txt` da bateria completa anterior. Timeout **só no 7.4** (laço eterno da referência) é pré-existente e não
conta. `--telas a,b` roda a bateria só nessas telas — útil para reconferir uma divergência.

**Ficam de fora, de propósito:** o passo 4 (Rector: exige conferir regra nova antes de aplicar), o **nível 3** (POST real:
grava no banco e exige escolher a tela), os passos 8 e 8b (mudam o proxy) e as correções (`guarda_ciclo.py`,
`negada_corrige.py`: exigem olhar caso a caso). As seções abaixo continuam valendo para **entender** cada passo,
**diagnosticar** uma falha e rodar um passo isolado à mão.

## Passos 4b a 6c — os portões

Cada portão pega uma classe de defeito que os outros não veem. Nenhum é opcional.

### Passo 4b — portão de funções contra o 7.4

**Por quê:** uma função que só existe no PHP 8 **compila** no 7.4 e explode só em execução. Num teste real, na época do 5.6, foram 93 arquivos com `php -l` limpo que quebrariam na tela (`str_starts_with()`, `random_int()`).

> **Polyfills no 7.4 (medido em 22/11/2026):** o `vendor/` do 7.4 carrega o `symfony/polyfill-php80` e o
> `polyfill-php81`, que criam `str_contains()`, `str_starts_with()`, `array_is_list()` e outras no próprio 7.4. Numa tela,
> essas funções rodam nos dois runtimes. O portão abaixo pergunta ao PHP **sem** o `vendor/` e as acusa assim mesmo: é
> cauteloso, dá um alarme a mais, nunca um a menos. Para testar o portão com um defeito que quebra de verdade, use uma
> função do 8.3 ou 8.4 sem polyfill, como `array_find()` (8.4): plantada numa tela, ela dá 500 no 7.4.

```bash
python3 - <<'PY'
import subprocess, re
d=subprocess.run(["git","diff","-U0","--","ecidade/"],capture_output=True).stdout
# o (?<!function ) exclui DECLARACOES -- sem ele acusa "__construct" como ausente
RX=re.compile(rb'(?<![\$>:\w])(?<!function )([a-z_][a-z0-9_]{2,})\s*\(')
nov=set(); vel=set()
for l in d.split(b"\n"):
    if l.startswith((b"+++",b"---")): continue
    a = nov if l.startswith(b"+") else (vel if l.startswith(b"-") else None)
    if a is not None: a |= {m.group(1) for m in RX.finditer(l)}
open("/tmp/fn.txt","w").write("\n".join(sorted(x.decode() for x in nov-vel)))
PY
docker cp /tmp/fn.txt ecidade_php74:/tmp/fn.txt
docker exec -i ecidade_php74 php -r '
$f=array_filter(array_map("trim",file("/tmp/fn.txt",FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES)));
$x=array(); foreach($f as $y) if(!function_exists($y)) $x[]=$y;
echo count($f)," novas | AUSENTES: ",count($x); if($x) echo " -> ".implode(", ",$x); echo "\n";' </dev/null
```

**Precisa dar `AUSENTES: 0`.** Qualquer nome na lista significa que o Rector emitiu uma função que o 7.4 não tem → banir a regra que a emitiu e refazer o passo 4.

### Passo 5 — `php -l` nos dois runtimes

**Por quê:** é o único instrumento que acha quatro categorias invisíveis ao `grep` — assinatura incompatível com a classe pai, `=& new`, `break` fora de laço e ternário aninhado sem parênteses.

```bash
cat ecidade/tmp/<pref>_universo.txt | sed '/^$/d' \
  | grep -E '\.(php|class|inc)$' | sed 's#^#/var/www/html/#' > /tmp/uni.txt

for c in ecidade_php74 ecidade_php85; do
  docker cp /tmp/uni.txt $c:/tmp/uni.txt >/dev/null
  printf "%-16s " "$c"
  docker exec -i $c sh -c 'n=0;e=0; while IFS= read -r f; do n=$((n+1));
    php -l "$f" </dev/null >/dev/null 2>&1 || { e=$((e+1)); echo "ERRO $f"; };
  done < /tmp/uni.txt; echo "$n verificados, $e com erro"' </dev/null
done
```

**Precisa dar `0 com erro` nos dois.** Rode no **universo inteiro**, não só nos alterados.

> **O `</dev/null` e o `docker exec -i` não são opcionais.** Sem eles o `php` herda o stdin do laço, consome a lista, o laço dá uma volta só e o resultado é um tranquilizador "0 erros". Foi assim que 11 arquivos quebrados passaram despercebidos.

**Se der erro só no 8.5:** rode com detalhe para ver a linha, corrija, **reconfira**. No `pre3_logs001.php` o lint apontou a linha 91; corrigida, apontou a **104**. Supor que a primeira era a única deixaria o arquivo quebrado.

```bash
docker exec -i ecidade_php85 php -d display_errors=1 -l /var/www/html/<arquivo> </dev/null 2>&1 | grep -a 'on line'
```

### Passo 5b — carregar cada arquivo (LSP)

**Por quê:** o `php -l` olha um arquivo de cada vez. Se a classe filha está num arquivo e a mãe em outro, a incompatibilidade
de assinatura (`Declaration of Filha::m() must be compatible with Mae::m()`) só aparece quando o PHP 8 **declara** a
classe — ou seja, em execução. Foi assim que `FolhaPagamentoSalario` e irmãs não carregavam no 8.5 com lint limpo.

```bash
grep -E '\.(php|class|inc)$' ecidade/tmp/<pref>_universo.txt \
  | while read f; do grep -aqE '\b(extends|implements)\b' "ecidade/$f" </dev/null && echo "$f"; done > /tmp/carga.txt
for v in 74 85; do     # um processo por arquivo: um fatal nao derruba o resto
  docker cp scratchpad/carrega_arquivo.php ecidade_php$v:/tmp/ca.php
  docker exec -i ecidade_php$v sh -c 'while read f; do php /tmp/ca.php "$f" </dev/null 2>/dev/null | tail -1; done' \
    < /tmp/carga.txt > /tmp/carga_$v.txt
done
wc -l /tmp/carga.txt /tmp/carga_74.txt /tmp/carga_85.txt      # os tres TEM de bater
# so interessa o que carrega no 7.4 e NAO no 8.5
join -t$'\t' <(cut -f1,2 /tmp/carga_74.txt | sort) <(cut -f1,2 /tmp/carga_85.txt | sort) | awk -F'\t' '$2=="OK" && $3!="OK"'
```

Cada linha de saída é `arquivo<TAB>OK` ou `arquivo<TAB>FATAL<TAB>mensagem` (no 8.5 o fatal vira `ERRO`). **O `join` precisa
sair vazio.** Arquivos que falham **nos dois** (interface em arquivo que não foi incluído, código morto) são pré-existentes:
anote o número e siga — no universo do `soc` eram 12 de 384, em 12/11/2026 (~30 s nos dois runtimes).

### Passo 6 — instanciar as classes

**Por quê:** valida a alteração de maior risco. No PHP 8 um construtor estilo PHP 4 **nunca executa** — sem erro, sem aviso, sem log. O objeto parece funcionar e produz resultado errado.

```bash
grep -E '^classes/' ecidade/tmp/<pref>_universo.txt | sort -u > /tmp/cls.txt
for c in ecidade_php74 ecidade_php85; do
  docker cp scratchpad/instancia_classes.php $c:/tmp/ic.php >/dev/null
  docker cp /tmp/cls.txt $c:/tmp/cls.txt >/dev/null
  sh scratchpad/harness_robusto.sh $c
done
diff <(sort /tmp/rb_ecidade_php74.txt) <(sort /tmp/rb_ecidade_php85.txt)
```

**Precisa dar diff vazio** — e o número de classes na saída precisa bater com `wc -l /tmp/cls.txt` (`ok` + `pulados` de
cada runtime = o tamanho da lista).

**Exceto por artefatos conhecidos do harness**, que aparecem sempre que a classe está no universo (os três primeiros
registrados em Patrimonial, Financeiro e Saúde; o último na Assistência Social):

| Classe | O que aparece | Por quê |
| --- | --- | --- |
| `RequisicaoMaterial`, `solicitacaoCompra` | `ArgumentCountError` só no 8.5 | o harness faz `new X()` sem argumentos e o construtor exige um; o 7.4 só avisava. O sistema sempre passa o argumento |
| `cl_avaliacaogruporespostatrabalhointermitente` | `ERRO ... .dd.xml não encontrado` só no 8.5, e um "pulado" a mais no 7.4 | o construtor lança exceção por falta de um arquivo da base; o 8.5 a captura, o 7.4 morre. Falha nos dois |
| `empenho` (`classes/empenho.php`) | assinatura diferente, com o mesmo número de propriedades | o construtor faz `date("Y-m-d", db_getsession("DB_datausu"))` e o harness roda sem sessão: o campo `datausu` sai `1969-12-31` no 7.4 e a data de hoje no 8.5. Com usuário logado, os dois dão a mesma data. Conferido em 22/11/2026, é a única diferença da classe. **Resolvido em 23/11/2026:** o `instancia_classes.php` passou a dar ao harness uma data de sessão fixa, e o `empenho` sai igual nos dois. Não se filtra a classe inteira: foi assim que um construtor PHP 4 real dela ficou escondido em 19/11/2026 |

Qualquer **outra** linha no diff é para investigar.

> **Um diff vazio de dois arquivos vazios não é aprovação.** No `cad`, a lista tinha 202 classes e a saída trazia **57**: o processo morria num arquivo e os dois runtimes morriam no mesmo, então o resultado aparecia como "idêntico". O `harness_robusto.sh` registra o culpado, pula e continua — o número foi para 201 de 202.

### Passo 6b — caminho de escrita

**Por quê:** a bateria do passo 7 faz só `GET`. As guardas `0 == ""` — **60% de todas as correções do projeto** — só disparam no `POST`. Sem este passo elas não seriam exercitadas por nada.

Rode **uma classe por processo**, com o `scratchpad/porclasse.sh`. Com a lista inteira num processo só, o primeiro fatal
mata o processo e o resto da lista some: no `soc` (13/11/2026) o 5.6 morreu na classe 119 de 772 e o diff comparou só 103
classes — sem acusar nada, porque nas 103 os dois concordavam. No `edu3` tinha coberto 120 de 404.

```bash
for c in ecidade_php74 ecidade_php85; do
  docker cp scratchpad/porclasse.sh $c:/tmp/pc.sh >/dev/null
  docker cp scratchpad/escrita.php  $c:/tmp/esc.php >/dev/null
  docker exec -i $c sh /tmp/pc.sh /tmp/esc.php < /tmp/cls.txt > /tmp/w_$c.txt    # um runtime de cada vez, nunca em paralelo
done
diff /tmp/w_ecidade_php74.txt /tmp/w_ecidade_php85.txt
```

Leva ~1 min para 772 classes. Ao fim de cada runtime ele imprime `#TOTAL 772 COM_SAIDA 708`: o `TOTAL` **tem de ser** o
tamanho da `/tmp/cls.txt` (`wc -l`). Classes sem nenhum campo para testar saem como `SEM_SAIDA`.

**Como ler a saída.** Cada linha é `arquivo<TAB>campo<TAB>valor`: o harness simula um formulário enviado com um valor
diferente em cada campo (`1000`, `1001`…), chama o `atualizacampos()` da classe e imprime o que ficou em cada campo. No
`diff`, `<` é o 7.4 e `>` é o 8.5.

**O `diff` dificilmente sai vazio: o que se espera é que ele tenha só linhas dos artefatos conhecidos** (tabela abaixo).
Qualquer outra linha é problema.

| No `diff` | Significa |
| --- | --- |
| só linhas das classes da tabela de artefatos (ou nada) | as duas versões leem o formulário igual — **é o resultado esperado** |
| `< ...campo '1003'` / `> ...campo 0`, de outra classe | o 7.4 leu o formulário e o 8.5 manteve `0`: **falta a guarda `0 == ""`** naquela classe. Dado errado gravado em silêncio — investigar |
| `SEM_SAIDA` de um lado e `<ERRO>` do outro, ou `<ERRO>` só no 8.5, de outra classe | investigar |

Para não depender de conferir linha por linha, tire os artefatos do `diff` e veja o que sobra — **tem de sair vazio**:

```bash
diff /tmp/w_ecidade_php74.txt /tmp/w_ecidade_php85.txt | grep -aE '^[<>]' \
  | grep -avE 'requisicaoMaterial\.model|solicitacaocompras\.model|avaliacaogruporespostatrabalhointermitente|lancamentoContabil|ordemPagamento|classes/empenho\.php'
```

O `-a` é obrigatório: há valores em LATIN-1 na saída, e sem ele o `grep` trata o arquivo como binário e não mostra nada —
o que pareceria aprovação.

**`SEM_SAIDA` e a contagem `COM_SAIDA`.** O harness só testa campos declarados com valor inicial (`public $x = ...`).
Classe sem nenhum campo assim não tem o que imprimir e sai como `SEM_SAIDA` — iguais nos dois runtimes, não dizem nada
sobre a migração (no `soc`, 62: 60 sem campo com valor inicial, 2 com campos que o teste não preenche). Para listá-las:
`grep -a '^SEM_SAIDA' /tmp/w_ecidade_php85.txt`. O `COM_SAIDA` é `TOTAL − SEM_SAIDA` e costuma diferir em 2 entre os
runtimes (708 × 710 no `soc`): são os artefatos `…trabalhointermitente` e `solicitacaoCompra`, que no 8.5 imprimem
`<ERRO>` e no 7.4 morrem sem saída.

**Artefatos conhecidos** (não são defeito; aparecem quando a classe está no universo):

| Classe | O que aparece | Por quê |
| --- | --- | --- |
| `RequisicaoMaterial`, `solicitacaoCompra`, `lancamentoContabil`, `ordemPagamento` | `<ERRO> ArgumentCountError` só no 8.5 (no 7.4, valores `NULL` ou `SEM_SAIDA`) | o harness faz `new X()` sem argumentos e o construtor exige um; o sistema sempre passa |
| `cl_avaliacaogruporespostatrabalhointermitente` | `SEM_SAIDA` no 7.4, `<ERRO> Exception` no 8.5 | falta um `.dd.xml` da base: falha nos dois |
| `classes/empenho.php → datausu` | `1969-12-31` contra a data de hoje | só acontece **sem sessão**, condição do harness |

Medido no `soc` (13/11/2026): `#TOTAL 772` nos dois, `diff` com 6 linhas, todas dos três primeiros artefatos; o filtro acima: vazio.

> **Não use o `harness_robusto.sh` aqui.** Ele avança contando *linhas de saída*, o que vale para o passo 6 (uma linha por
> classe) e não para este (muitas linhas por classe).

### Passo 6c — a forma NEGADA `$this->x != ""`

**Por quê:** o `GuardaComparacaoLiteralRector` só trata `==`. A forma `!=`, com propriedade inteira e **sem `trim()`**,
está sobretudo no bloco de auditoria do `alterar()`:

```php
if (isset($GLOBALS["HTTP_POST_VARS"]["x"]) || $this->x != "")   // 7.4: 0 != "" falso; 8.5: verdadeiro
    insert into db_acount (...)                                  // o 8.5 grava uma alteração para 0
```

O padrão aparece milhares de vezes, mas só muda o resultado quando a propriedade ainda vale o inteiro `0` na comparação.
Por isso **meça antes de corrigir**:

```bash
python3 scratchpad/negada_alvos.py tmp/negada.tsv   # estatico: classe, campo, metodo, auditoria/negocio
cut -f1 ecidade/tmp/negada.tsv | sort -u > ecidade/tmp/negada_cls.txt
for v in 74 85; do
  docker cp scratchpad/negada.php ecidade_php$v:/tmp/negada.php
  # UM arquivo temporario POR RUNTIME: o /tmp e compartilhado entre os containers
  docker exec -i -e V=$v ecidade_php$v sh -c 'cd /var/www/html; while read c; do
      grep -F "$(printf "%s\t" "$c")" tmp/negada.tsv > /tmp/_neg_$V.tsv
      php -d display_errors=0 /tmp/negada.php /tmp/_neg_$V.tsv 2>/dev/null </dev/null; done' \
    < ecidade/tmp/negada_cls.txt > /tmp/neg_$v.txt
done
python3 scratchpad/negada_compara.py /tmp/neg_74.txt /tmp/neg_85.txt /tmp/cls.txt    # /tmp/cls.txt: a lista do passo 6
```

O teste roda sobre **todas** as classes de `classes/` (1.848 classes e ~7.300 pares em 13/11/2026; ~5 min), não só as do
lote. Cada arquivo `/tmp/neg_*.txt` tem uma linha por par: `classe  campo  método  modo  tipo  valor  resultado`, em que
`valor` é o que o campo vale quando o formulário vem **vazio** e `resultado` é quanto deu `campo != ""`. Não use `diff`
para ler: ele mostra centenas de linhas de classes que **não são do lote** — classes nunca portadas, de áreas que o 7.4
ainda serve. O `negada_compara.py` separa as duas coisas e dá o veredito:

```
pares medidos: 7.4=7281  8.5=7281
classes do lote: 772

== FORA DO LOTE: 556 pares em 187 classes (areas nao migradas ou classes que o lote nao usa -- nao corrigir aqui)
      552  VALOR_DIFERENTE
        4  FORMA_NEGADA

== DO LOTE: 0 pares

VEREDITO: PASSOU -- nenhuma divergencia nas classes do lote
```

(Saída real do `soc`, 13/11/2026. As 552 de fora caem à medida que as áreas são migradas — boa parte era do `hab`, ainda
sem Rector naquele momento.)

| Veredito | O que fazer |
| --- | --- |
| `PASSOU` | seguir para o nível 3 / passo 7 |
| `INCOMPLETO` | os dois runtimes não mediram o mesmo número de pares: um processo morreu. Rodar de novo |
| `INVESTIGAR` | olhar cada par listado em `DO LOTE`, pelo tipo: |

- **`VALOR_DIFERENTE`** (7.4 `NULL`, 8.5 `0`): falta a guarda do `==` no `atualizacampos()` — a classe do lote ficou sem
  porte. É falha do passo 4: confira se ela estava na lista de alvos e rode o Rector nela;
- **`FORMA_NEGADA`** (mesmo valor `0`, 7.4 `false`, 8.5 `true`): o 8.5 gravaria no histórico (`db_acount`) uma alteração
  que ninguém fez. Ponha os pares (classe, campo, método) num TSV e rode `python3 scratchpad/negada_corrige.py <tsv>`,
  que aplica `($this->x != "" && $this->x !== 0 && $this->x !== 0.0)` só naqueles pontos. Depois rode o
  `negada_alvos.py` de novo: os pontos corrigidos têm de sumir (o `negada.php` continua acusando, porque mede o estado,
  não o código).

Os pares `FORA DO LOTE` não se corrigem no lote: se a classe for de uma área **já migrada**, é regressão — registre e
avise antes de mexer. Uma linha de `<script>alert('Variavel de sessão nao encontrada…')` nos arquivos é artefato (o teste
roda sem login) e o script a ignora.

Medido em 27/10/2026: 7.367 pares, 89 da forma negada, 74 em 28 classes servidas, todos de auditoria (corrigidos). Nos
lotes 1 e 2 da Configuração: 2.068 e 2.426 pares, 0 divergências. No `soc`: 0 no lote.

### Nível 3 — `POST` de verdade, comparando o SQL emitido

**Quando usar:** o passo 6b compara o **estado do objeto**; o nível 3 compara o **`INSERT` que cada runtime emite**. É a única prova ponta a ponta de que a gravação está idêntica.

Não rode em bateria — **é dirigido**. Umas 15 telas, espalhadas pelos módulos, bastam para sustentar a afirmação.

#### Em um comando — `nivel3.py`

```bash
python3 scratchpad/nivel3.py --candidatas soc hab      # quais telas testar (aplica o criterio abaixo)
python3 scratchpad/nivel3.py soc1_visitatipo001        # testa a escolhida
```

O `--candidatas` lista as telas de inclusão dos prefixos com a tabela de cada uma e uma sugestão: **RECOMENDADA** (tabela
simples, família ou classe alterada pelo lote), **boa**, **EVITAR** (cadastro central com gatilhos) ou **não serve** (não
grava direto, é contêiner de abas, ou a classe não corresponde a uma tabela). A tabela vem do código da tela; se ela gravar
outra, ou mais de uma, informe com `--tabelas a,b`.

O teste em si confere que a tela existe (e sugere o nome certo se não existir), acha a sessão e confere que ela vale, liga o
log de SQL e **sempre o desliga no fim**, gera o payload, roda o `escrita_post.py` e, por último, confere pelas
**estatísticas do PostgreSQL** se alguma **outra** tabela recebeu escrita durante o teste. Isso pega o que o log de SQL não
mostra — escrita feita por **gatilho** dentro do banco, que foi o que deixou lixo na amostra da Saúde:

```
tela: soc1_visitatipo001.php
tabelas fotografadas/restauradas: visitatipo
payload: as13_sequencial=&as13_descricao=TESTE_N3&as13_exigeencaminhamento=f&incluir=Incluir

  destes, escrita de NEGOCIO: ref=1  8.5=1
    ref> insert into visitatipo( as13_sequencial ,as13_descricao ,as13_exigeencaminhamento ) values ( 2 ,'TESTE_N3' ,'f' )
    8.5> insert into visitatipo( as13_sequencial ,as13_descricao ,as13_exigeencaminhamento ) values ( 2 ,'TESTE_N3' ,'f' )
  == SQL de escrita de NEGOCIO IDENTICO nos dois runtimes ==

Nenhuma outra tabela recebeu escrita durante o teste (inclusive por gatilho).
log de SQL desligado (RESET log_statement).
```

Os vereditos (`IDENTICO`, `DIVERGE`, `INCONCLUSIVO`) são os explicados abaixo. Cada execução fica registrada em
`ecidade/tmp/nivel3/`. Os passos à mão continuam abaixo, para entender ou ajustar um caso difícil.

Três casos vistos na Assistência Social (21/11/2026):

- **Tela que grava em várias tabelas.** Passe todas em `--tabelas`, em qualquer ordem: o restore apaga as filhas antes
  das mães, pela FK. Antes dessa correção, a mãe primeiro na lista abortava o teste no meio e deixava a linha de teste no
  banco.
- **`INCONCLUSIVO` porque faltou o registro pai.** O payload automático deixa vazios os campos que apontam para outro
  cadastro (na `hab1_workflowativ001.php`, o workflow e o tipo de processo), e a tela recusa antes do `INSERT`. Ache um
  pai que exista no banco e passe o formulário com `--payload`, por exemplo
  `--payload "db112_sequencial=1&p51_codigo=161&db114_descricao=TESTE_N3&...&incluir=Incluir"`.
- **Tela que grava por RPC** (o `--candidatas` ainda a classifica como "boa"): o formulário não grava, o JavaScript chama
  um `.RPC.php`. Sai `INCONCLUSIVO`; troque de tela.

#### Quais telas testar

O critério usado desde a Saúde: **uma tela de inclusão por prefixo do lote**, como amostra.

1. **Inclusão:** arquivo `<pref>1_…001.php` (`1` = cadastro; `001` incluir, `002` alterar, `003` excluir). Comece por ela:
   é a mais segura, porque o harness apaga a linha inserida ao restaurar. Alteração e exclusão mexem em linha existente.
2. **Tabela simples**, de preferência a de uma classe que o lote alterou (`git status`).
3. **Evite cadastros centrais com gatilhos** (CGM, CGS, cidadão). Na Saúde, a CGS deixou dados no banco: um gatilho gravou
   em tabelas que o harness não fotografou (`area-saude.md`, *Nível 3 — amostra da Saúde*).

Para listar as candidatas e a tabela de cada uma:

```bash
for f in ecidade/<pref>1_*001.php; do
  t=$(grep -aoE "getDao\(['\"][a-z0-9_]+|new cl_[a-z0-9_]+" "$f" </dev/null | head -1 | sed -E "s/.*(cl_|['\"])//")
  echo "$(basename $f)  ${t:--}"
done
```

No `soc` (13/11/2026):

```
soc1_cidadao001.php            localatendimentosocial   <- evitar: cadastro central
soc1_cursosocial001.php        -
soc1_localatendimento001.php   -
soc1_matriculacursosocial001.php -
soc1_visitatipo001.php         visitatipo               <- boa escolha: tabela simples, familia que o Rector alterou
```

`-` é tela que não instancia a classe diretamente (usa *model*, RPC ou abas) — não serve para começar.

#### O problema que ele resolve

Os dois runtimes compartilham o banco. Se você mandar o mesmo `POST` para os dois, o primeiro muda o estado que o segundo veria. A saída é comparar o **SQL emitido**, com snapshot e restore entre os dois lados.

**Antes:** o `/tmp/sid.txt` e o `/tmp/_d.bak` da *Prova de fumaça* (seção *Antes de começar*). Se o `cat /tmp/sid.txt`
der `Arquivo ou diretório inexistente`, a máquina reiniciou ou a prova não foi feita hoje — rode-a de novo.

#### Passo 1 — ligar o log de SQL

```bash
docker exec -i ecidade_database psql -U postgres \
  -c "ALTER DATABASE ecidade SET log_statement='all';"
sleep 2
```

**Desligue ao terminar** — com ele ligado o log cresce rapidamente:

```bash
docker exec -i ecidade_database psql -U postgres \
  -c "ALTER DATABASE ecidade RESET log_statement;"
```

#### Passo 2 — descobrir a tabela que a tela grava

```bash
(cd ecidade && grep -aoE "getDao\\(['\"][a-z0-9_]+|new cl_[a-z0-9_]+" <tela>.php | head -3)
```

O nome que aparecer é a tabela. Confira que a classe existe: `ls classes/db_<tabela>_classe.php`.

#### Passo 3 — gerar o payload lendo o formulário

**Não invente os nomes dos campos.** Foi assim que eu errei duas vezes seguidas: usei `cm34_descr` quando o campo real era `cm34_descricao`, e `cm34_dtvalidade` quando era `cm34_datalimite`.

```bash
python3 scratchpad/payload_auto.py "$(cat /tmp/sid.txt)" <tela>.php
```

Ele lê o HTML que o 7.4 emite e monta a querystring com os nomes reais, o botão de submit certo e os campos escondidos `_dia`/`_mes`/`_ano`.

Para ver o formulário em detalhe antes de ajustar à mão:

```bash
python3 scratchpad/payload.py "$(cat /tmp/sid.txt)" <tela>.php
```

#### Passo 4 — rodar

```bash
P=$(python3 scratchpad/payload_auto.py "$(cat /tmp/sid.txt)" <tela>.php </dev/null)
python3 scratchpad/escrita_post.py "$(cat /tmp/sid.txt)" <tela>.php <tabela> "$P"
```

#### Como ler o resultado

```
snapshot: cemiterioisencao=4 linhas  | sequencias=1
statements: ref=38  8.5=38
destes, INSERT/UPDATE/DELETE: ref=9  8.5=9
destes, escrita de NEGOCIO: ref=1  8.5=1
  ref> insert into cemiterioisencao( ... ) values ( 11 ,'TESTE_N3' ,1 , ... )
  8.5> insert into cemiterioisencao( ... ) values ( 11 ,'TESTE_N3' ,1 , ... )
== SQL de escrita de NEGOCIO IDENTICO nos dois runtimes ==
```

| Veredito | Significa | Ação |
| --- | --- | --- |
| `IDENTICO` com **1 ou mais** escritas de negócio | a tela gravou igual nos dois | ✓ próxima tela |
| `INCONCLUSIVO` | **o POST não chegou a gravar** | ajustar o payload — ver abaixo |
| `DIVERGE` | os dois emitiram SQL diferente | investigar — ver abaixo |

> **`sequencias=0` é sinal de alerta.** Sem restaurar a sequência, o segundo runtime recebe o próximo número e o `INSERT` diverge por motivo benigno (`values ( 8 ...)` contra `( 9 ...)`). A convenção de nomes tem três formas e o harness cobre as três; se der zero, procure à mão: `docker exec -i ecidade_database psql -U postgres -d ecidade -c "SELECT sequencename FROM pg_sequences WHERE sequencename ILIKE '%<tabela>%'"`.

#### Se der `INCONCLUSIVO`

O payload não foi aceito. Veja o que a aplicação respondeu:

```bash
SID=$(cat /tmp/sid.txt)
docker exec -u root -i ecidade_php74 sh -c \
  "cp /tmp/_d.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data /var/lib/php/sessions/sess_$SID" </dev/null
curl -s -b "ECIDADEWINDOWMAIN=$SID" -d "$P" "http://localhost:8080/<tela>.php" > /tmp/r.html
python3 -c "
import re
h=open('/tmp/r.html',encoding='latin-1').read()
t=re.sub(r'<script.*?</script>','',h,flags=re.S|re.I)
print(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',t))[:400])"
```

| O que aparece | Causa provável |
| --- | --- |
| "Campo ... não informado" | falta um campo obrigatório no payload |
| "Notificação do Sistema" | a tela recusou antes de gravar |
| página normal, sem mensagem | o botão de submit tem outro nome |
| nada muda | a tela pode ser uma aba carregada por JavaScript — pule |

**Caminho mais barato:** se uma tela resistir, **troque de tela**. O objetivo é cobertura por módulo, não aquela tela específica. De 28 testadas, 18 exercitaram de primeira.

#### Se der `DIVERGE`

**Olhe antes de comemorar.** Na primeira execução deste projeto, 5 divergiram e **as cinco eram defeito do instrumento**, não da migração:

| O que aparecia | Causa real |
| --- | --- |
| mesmo `INSERT` com timestamps diferentes no fim | o parser engolia a linha de `ERRO:` do PostgreSQL |
| `values ( 8 ...)` contra `( 9 ...)` | sequência não restaurada |

Compare os dois `INSERT` **campo a campo**. Se a diferença for só o número da chave ou texto depois do `)`, é artefato. Se um campo de **dado** diferir, ou se um lado estiver `<ausente>`, aí sim é defeito — e provavelmente é a guarda `0 == ""` faltando naquela classe.

#### Teste apenas telas PORTADAS

O harness posta **direto** em `:8080` e `:8085`, sem passar pelo proxy — então a tela do lote **não precisa estar roteada**,
basta o Rector e as correções do lote já estarem aplicados. O que não vale é testar tela de **outro** módulo ainda não
portado. Erro de método meu: testei 5 telas assim; duas divergiam por `parse_str` não portado — mas são servidas pelo 5.6,
onde funcionam. Para saber se uma tela de fora do lote já está no 8.5:

```bash
curl -sI "http://localhost:8090/<tela>.php" | grep -ai 'x-ecidade-runtime'
```

## Passo 7 — a bateria byte-a-byte

**O que é:** pedir cada tela do módulo às duas portas, com a mesma sessão, e comparar as respostas byte a byte. **É este passo que acha o que nenhum outro vê** — catorze das vinte categorias do catálogo saíram daqui ou do `php -l`.

Só é possível porque o PHP 7.4 continua **vivo como referência**. Num *big-bang*, o "antes" deixa de existir no momento em que o Docker sobe de versão.

### Comando

```bash
chmod 666 ecidade/extension/log/*.log
python3 scratchpad/cmp.py "$(cat /tmp/sid.txt)" '^<pref>[0-9]*_' /tmp/<pref>_div.txt

# so um subconjunto de telas:
ONLY="tela1.php,tela2.php" python3 scratchpad/cmp.py "$(cat /tmp/sid.txt)" '^<pref>[0-9]*_' /dev/null
```

### Saída esperada

```
=== 350/353 identicas, 3 divergentes ===
```

O arquivo `/tmp/<pref>_div.txt` lista as divergentes com o código HTTP e o tamanho de cada lado:

```
fis1_aidof002.php     200  200  18637  18200
```

### Antes de diagnosticar uma a uma: o log do PostgreSQL

A maioria das divergências é `pg_*` sobre resultado `false`, e `pg_query()` só devolve `false` quando **a SQL falha** — não quando a tabela está vazia. Logo o banco já registrou todas, e **uma passada da bateria lista todos os pontos de uma vez**:

```bash
docker logs --since 20m ecidade_database 2>&1 | grep -aA1 'ERRO:'
```

> **O log está em PORTUGUÊS** (`ERRO:` / `INSTRUÇÃO:`), por causa do locale `pt_BR.ISO-8859-1` do cluster. `grep 'ERROR:'` não acha nada e falha em silêncio. Nada precisa ser configurado.

Isso troca N rodadas de bateria por 1 — o `iss` precisou de **quatro** antes de este atalho existir.

### Diagnosticar uma divergência

```bash
SID=$(cat /tmp/sid.txt)
: > ecidade/extension/log/error.log; chmod 666 ecidade/extension/log/error.log
docker exec -u root -i ecidade_php74 sh -c \
  "cp /tmp/_d.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data /var/lib/php/sessions/sess_$SID" </dev/null
curl -s -o /dev/null -b "ECIDADEWINDOWMAIN=$SID" "http://localhost:8085/<tela>.php"; sleep 1
grep -a 'Uncaught\|E_ERROR' ecidade/extension/log/error.log | tail -1
```

Se o log não disser nada, compare o conteúdo:

```bash
for port in 8080 8085; do
  docker exec -u root -i ecidade_php74 sh -c \
    "cp /tmp/_d.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data /var/lib/php/sessions/sess_$SID" </dev/null
  curl -s -b "ECIDADEWINDOWMAIN=$SID" "http://localhost:$port/<tela>.php" > /tmp/o_$port.html
done
diff <(fold -w95 /tmp/o_8080.html) <(fold -w95 /tmp/o_8085.html) | head -12
```

### Tabela de decisão

| Sintoma | Conclusão | Ação |
| --- | --- | --- |
| `200` / `500` — quebra só no 8.5 | **regressão de migração** | corrigir aquele ponto |
| `500` / `200` — quebra só no 7.4 | defeito **pré-existente** da referência | registrar, **não corrigir** |
| `500` / `500` — quebra igual | defeito pré-existente ou dado ausente | **não mexer** |
| `200` / `200` com bytes diferentes | defeito **silencioso** — o mais perigoso | diagnosticar pelo `diff` |
| Não é tela (fragmento de include) | artefato do harness | caracterizar e seguir |

### Os dois ciclos automáticos de guarda `pg_*`

O caso mais comum de "quebra só no 8.5" é uma função `pg_*` recebendo `false` (a SQL falhou) ou pedindo uma coluna que o
resultado não tem. Dois scripts corrigem isso **na aparição, uma linha por vez**: requisitam a tela no 8.5, leem o fatal do
log, aplicam só naquela linha a guarda que reproduz o 7.4 (`($r ? pg_xxx($r…) : null)`; `null` é o que o 7.4 devolvia) e
repetem. Eles restauram a sessão a partir do `/tmp/_sess.bak` que o `cmp.py` cria — rode a bateria antes. Não fazem
`php -l`: faça você, nos dois runtimes, sobre os arquivos que eles tocaram.

```bash
SID=$(cat /tmp/sid.txt) python3 scratchpad/guarda_ciclo.py <tela1>.php [<tela2>.php ...]   # resultado false
SID=$(cat /tmp/sid.txt) python3 scratchpad/campo_ciclo.py  <tela1>.php [<tela2>.php ...]   # coluna ausente, pg_free_result(false)
```

Alterne os dois até a tela parar de fatalar — uma guarda expõe a próxima (`cai3_gerfinanc004` precisou de cinco rodadas).
Depois, `git diff` em cada arquivo que eles tocaram: confira que a guarda não está sobre um resultado comparado com `===`
(ver *Corrigir na aparição, nunca em massa*).

### Quando o diagnóstico não fecha: instrumente

Se houver vários candidatos plausíveis no mesmo arquivo, **não deduza** — imprima o valor. Num caso real, duas hipóteses minhas estavam erradas e custaram duas rodadas de bateria e duas correções revertidas no núcleo; uma sonda resolveu em um minuto:

```php
echo "<!--SONDA val=".var_export($a,true)." tipo=".gettype($a)."-->";
```

Coloque antes da linha suspeita, requisite nos dois runtimes, leia, **remova a sonda**.

### Preciso refazer a bateria dos outros módulos?

**Durante a área, não a completa** (decisão de 29/10/2026: ela custa ~3 h e todas as completas desde o Tributário voltaram
na linha de base). A bateria completa roda **uma vez, no fim da área** (*O fluxo de uma área*, D). No lote, a pergunta é
**"algum arquivo que eu alterei é executado por uma tela que já está no 8.5?"** — e se for, rode uma **bateria dirigida**
só a essas telas:

```bash
# 1. quem chama a funcao/metodo/arquivo que voce alterou (grep -a: 64% da base e LATIN-1)
grep -arl --include='*.php' '<nome da funcao ou do arquivo alterado>' ecidade | sed 's#^ecidade/##' > /tmp/chamam.txt
# 2. lotes JA SERVIDOS cujo universo contem algum chamador (os universos estao em ecidade/tmp/<lote>_universo.txt;
#    ignore os dim_*_universo.txt, que sao so de dimensionamento e incluem arquivos nunca portados)
for u in ecidade/tmp/*_universo.txt; do grep -qxFf /tmp/chamam.txt "$u" && echo "$u"; done | grep -v '/dim_'
# 3. rodar o cmp.py nas telas desses lotes: o prefixo de cada um, ou ONLY= com as telas do map
```

| Resultado | Ação |
| --- | --- |
| nenhum lote servido alcança o trecho | não rodar nada além da bateria do lote |
| alguns lotes | bateria dirigida a eles |
| quase tudo (uma função de `libs/db_stdlib.php`, por exemplo) | aí sim, a bateria completa já no lote |

**Compare sempre com a linha de base registrada em `docs/registro/area-<área>.md`.** "115/116" não é defeito se a linha de
base já era 115/116 — as divergências conhecidas estão todas caracterizadas lá (e reunidas em
`docs/divergencias-conhecidas.md`, quando existir).

## Quando o alvo não é um módulo

Duas vezes neste projeto o alvo não foi um prefixo de telas: **o núcleo** (24 arquivos usados por quase tudo) e **a biblioteca `dbagata/`** (211 arquivos de geração de relatório). Não têm telas no menu, então **o passo 7 não existe** — e sem ele você fica sem o instrumento que acha os defeitos silenciosos.

A saída é trocar a bateria por **um caminho real exercitado ponta a ponta**.

### Para o núcleo

A prova é a tela de login, que carrega quase todo o núcleo e não depende de sessão:

```bash
for p in 8080 8085; do
  printf "porta %s: " "$p"
  curl -s -o /tmp/login_$p.html -w '%{http_code} %{size_download} bytes\n' \
    "http://localhost:$p/login.php"
done
diff /tmp/login_8080.html /tmp/login_8085.html
```

**Precisa dar os mesmos bytes nos dois** (aqui: 12.009). A única diferença legítima é o id aleatório do captcha.

Depois disso, a prova de verdade é **refazer as baterias de todos os módulos já portados** — o núcleo alcança todas as telas.

### Para uma biblioteca

Exerça o **pipeline real** que a usa, não as classes isoladamente. No caso do `dbagata/`, um relatório de verdade:

```bash
for p in 8080 8085; do
  curl -s -o /tmp/rel_$p.pdf "http://localhost:$p/testeagata.php"
done
cmp /tmp/rel_8080.pdf /tmp/rel_8085.pdf && echo "PDF byte-a-byte IDENTICO"
```

> **Foi assim que a terceira forma de chamar o construtor antigo apareceu.** A varredura de remanescentes dizia "0", mas o `testeagata.php` passou a dar 500 no 8.5 **depois** do porte: havia `FPDF::FPDF(...)` — chamada estática ao nome antigo, num arquivo diferente do que foi renomeado. As varreduras não viam porque eu derivava a lista de nomes do lugar errado.

### O que muda no procedimento

| Passo | Módulo | Núcleo ou biblioteca |
| --- | --- | --- |
| 1 — enumerar | por prefixo | **a pasta inteira**, com `.php`, `.class` e `.inc` |
| 4 — Rector | igual | igual |
| 5 — `php -l` | igual | igual, e é aqui que mais aparece coisa |
| 6 — classes | igual | igual |
| 7 — bateria | as telas do prefixo | **o pipeline real** (login, relatório) |
| extra | — | **refazer as baterias de todos os módulos** |

### Filtrar por `*.php` esconde bibliotecas inteiras

```bash
find ecidade/<pasta> -type f \( -name '*.php' -o -name '*.class' -o -name '*.inc' \) | wc -l
```

O `dbagata/` usa `.class` e `.inc`. Uma medição anterior que filtrava só `*.php` reportou **70 construtores PHP 4**; com as três extensões, eram **224**.

### Arquivos que já não parseavam no 7.4

Ao portar uma biblioteca velha você vai achar arquivos quebrados **antes** da migração. Não tente consertar:

```bash
docker exec -i ecidade_php74 sh -c 'while IFS= read -r f; do
  php -l "$f" </dev/null >/dev/null 2>&1 || echo "$f"; done < /tmp/uni.txt' </dev/null
```

O que aparecer aqui é **pré-existente** — registre e deixe de fora do universo. No `dbagata/` eram 5 de 216, todos de GUI GTK que nada no repositório carrega.

## Quando o prefixo serve várias áreas

Metade dos módulos deste projeto caiu aqui, e o procedimento muda. **Prefixo de arquivo não respeita a fronteira das áreas:** `con` aparece em 6 áreas do menu, `pro` em 6, `cai` em 5, `cad` em 3.

Rotear `con` por prefixo levaria **511 telas** de Contabilidade, RH e Patrimonial junto — para entregar 30 de Tributário.

### Passo A — medir quanto seria arrastado

```bash
cat > /tmp/q.sql <<'SQL'
WITH ta AS (
  SELECT DISTINCT lower(di.funcao) AS tela,
         lower(substring(di.funcao from '^[A-Za-z]+')) AS pref,
         replace(a.at25_descr,'DB:','') AS area
  FROM configuracoes.atendcadareamod am
  JOIN configuracoes.atendcadarea a  ON a.at26_sequencial = am.at26_codarea
  JOIN configuracoes.db_modulos   m  ON m.id_item        = am.at26_id_item
  JOIN configuracoes.db_menu      dm ON dm.modulo        = m.id_item
  JOIN configuracoes.db_itensmenu di ON di.id_item       = dm.id_item_filho
  WHERE di.funcao ~ '^[A-Za-z]+[0-9]*_.*\.php$'),
cls AS (SELECT tela, pref, bool_or(area LIKE 'TRIBUT%') AS t FROM ta GROUP BY tela, pref)
SELECT pref,
       count(*) FILTER (WHERE t)     AS da_area,
       count(*) FILTER (WHERE NOT t) AS arrastadas
FROM cls WHERE pref = '<pref>' GROUP BY pref;
SQL
docker cp /tmp/q.sql ecidade_database:/tmp/q.sql
docker exec -i ecidade_database psql -U postgres -d ecidade -f /tmp/q.sql
```

| `arrastadas` | Decisão |
| --- | --- |
| 0 ou 1 | **rotear por prefixo** — o `map` não compensa |
| dezenas | rotear **por lista** |
| centenas | rotear por lista, **obrigatoriamente** |

Medido nos seis prefixos: `cad` arrastaria 1, `dv` nenhuma, `pro` 66, `cai` 151, `rec` 158, `con` **511**.

### Passo B — gerar a lista das telas da área

```bash
cat > /tmp/qt.sql <<'SQL'
\copy (WITH ta AS (SELECT DISTINCT lower(di.funcao) AS tela, replace(a.at25_descr,'DB:','') AS area FROM configuracoes.atendcadareamod am JOIN configuracoes.atendcadarea a ON a.at26_sequencial=am.at26_codarea JOIN configuracoes.db_modulos m ON m.id_item=am.at26_id_item JOIN configuracoes.db_menu dm ON dm.modulo=m.id_item JOIN configuracoes.db_itensmenu di ON di.id_item=dm.id_item_filho WHERE di.funcao ~ '^[A-Za-z]+[0-9]*_.*\.php$') SELECT DISTINCT tela FROM ta WHERE area LIKE 'TRIBUT%' ORDER BY 1) TO '/tmp/telas.txt'
SQL
docker cp /tmp/qt.sql ecidade_database:/tmp/qt.sql
docker exec -i ecidade_database psql -U postgres -d ecidade -f /tmp/qt.sql
docker cp ecidade_database:/tmp/telas.txt /tmp/telas.txt
```

> **`\copy` é meta-comando do psql e tem de caber em UMA LINHA.** Quebrado em várias, o psql falha — e a mensagem vem em **LATIN-1**, que o Python não decodifica: o sintoma é `UnicodeDecodeError`, não erro de SQL.

### Passo C — decidir o escopo do porte

Aqui estão **dois custos diferentes**, e medir os dois leva um minuto:

```bash
# custo A: portar o prefixo inteiro
python3 scratchpad/enumera.py <pref>        # veja "A ALTERAR"

# custo B: portar so o universo das telas que serao roteadas
# (adapte o trecho de enumeracao usando /tmp/telas.txt como semente)
```

Medido nos quatro prefixos grandes:

| Prefixo | Prefixo inteiro | Só as telas roteadas | Economia |
| --- | --- | --- | --- |
| `cad` | 376 | **210** | 166 |
| `cai` | 544 | **152** | 392 |
| `pro` | 235 | **60** | 175 |
| `con` | 1.043 | **52** | 991 |

**Escolha o menor quando a diferença for grande.** Os arquivos a mais seriam pré-pagamento para áreas fora do escopo. Para lotes pequenos (dezenas), portar o prefixo inteiro é mais simples e evita a lacuna dos dois terços fora do menu.

### Passo D — rotear por lista

O gerador lê o banco, cruza com o disco e escreve `docker/proxy/faseb_map.conf`. O `nginx.conf` já tem os três `map` que
usam esse arquivo. Cada argumento diz a **área** (início do nome no banco, sem `DB:`) e os prefixos, e só entram as telas
que o banco atribui àquela área. Abas e destinos que não estão no menu entram pela lista `docker/proxy/faseb_map_abas.txt`
(passo 8b), que o gerador também lê.

O gerador **reescreve o arquivo inteiro**: repita sempre **todos** os lotes já roteados, senão eles voltam para o 7.4 em
silêncio. **Não digite o comando de memória:** copie-o da linha 2 do próprio `faseb_map.conf` e acrescente só o argumento do
seu lote no fim.

```bash
sed -n 2p docker/proxy/faseb_map.conf          # "# Reproduzir:  python3 scratchpad/gera_map_faseb.py tribut:... conf:..."
cp docker/proxy/faseb_map.conf /tmp/antes.conf
python3 scratchpad/gera_map_faseb.py <todos os argumentos da linha 2> <area>:<pref>,<pref>
diff /tmp/antes.conf docker/proxy/faseb_map.conf | grep '^< ' | grep -v Reproduzir   # TEM de vir vazio: so pode ACRESCENTAR
grep -c 'php85;' docker/proxy/faseb_map.conf
```

Depois, testar e recriar o proxy como no passo 8 (com o `nginx -t` num container descartável **antes**).

**Conferir o roteamento — cinco casos:**

```bash
for u in <tela-da-area>.php w/2/<tela-da-area>.php <tela-de-OUTRA-area>.php \
         <Tela-Com-Maiuscula>.php login.php; do
  printf "%-40s " "/$u"
  curl -sI "http://localhost:8090/$u" | grep -ai 'x-ecidade-runtime' | tr -d '\r'
done
```

| Caso | Esperado |
| --- | --- |
| tela da área | `PHP-8.5 (migrado - Fase B)` |
| a mesma com `/w/2/` | `PHP-8.5` — senão o `map` do `$uri` está errado |
| tela de **outra** área, mesmo prefixo | `PHP-7.4` — **este é o teste que importa** |
| tela com inicial maiúscula | `PHP-8.5` — o `map` é insensível a caso |
| `login.php` | `PHP-7.4` |

> **O `map` do nginx É insensível a maiúsculas** — ao contrário do `location ~`, que precisou do `~*`. Emitir as duas grafias faz o nginx **recusar a configuração** com `conflicting parameter`. Prevenir-se da armadilha no lugar errado derruba o proxy.

### Passo E — a bateria cobre só o que foi roteado

Não rode a bateria no prefixo inteiro: as telas que ficaram no 7.4 **não foram portadas** e vão divergir por motivo legítimo.

```bash
ONLY=$(grep -i '^<pref>' /tmp/telas.txt | tr '\n' ',' | sed 's/,$//')
ONLY="$ONLY" python3 scratchpad/cmp.py "$(cat /tmp/sid.txt)" '^<pref>[0-9]*_' /tmp/<pref>_div.txt
```

> **Erro de método que eu cometi:** testei telas que não estavam roteadas e achei "defeitos" (`parse_str` não portado) em arquivos servidos pelo 7.4, onde funcionam. **Só teste o que responde `PHP-8.5`.**

### O que o `map` deixa de fora, e você precisa declarar

O banco só sabe classificar **telas do menu**, que são \~36% dos arquivos de um prefixo. Os outros 64% — popups, `.RPC.php`, subtelas — **continuam no 7.4**.

Isso é funcionalmente correto: eles **estão portados** (entram pelo universo das sete frentes, via `window.open`) e rodam nos dois runtimes. Mas significa que "o módulo roda em PHP 8.5" vale para **as telas dele**, não para todos os seus arquivos. Declare isso junto com o número.

## Passos 8 e 9 — rotear e registrar

### Em um comando — `rotear.py`

```bash
python3 scratchpad/rotear.py location soc hab                # SO MOSTRA o que mudaria
python3 scratchpad/rotear.py location soc hab --aplicar      # prefixo inteiro para o 8.5
python3 scratchpad/rotear.py map assist:pre,con --aplicar     # so as telas que o banco da a area
python3 scratchpad/rotear.py 8b ASSIST                       # passo 8b: o que ainda volta ao 7.4
python3 scratchpad/rotear.py abas hab1_avaliacao004 --aplicar # rotear um destino que o 8b achou
```

Qual modo usar é a decisão da parte B do fluxo da área (`prefixos_area.py`): **`location`** quando nenhuma outra área
pendente usa o prefixo, **`map`** quando usa (ou quando o prefixo é muito maior que as telas da área). **Sem `--aplicar`,
nada muda**: o script mostra a linha antes e depois, ou as entradas que o `map` ganharia, e quantas telas passariam ao 8.5:

```
docker/proxy/nginx.conf:
  antes:  ...|lab|far|sau|sys)
  depois: ...|lab|far|sau|sys|soc|hab)
scratchpad/dimensiona.py:            (as duas copias do regex que os scripts usam mudam junto)
  ...
Telas que passam ao 8.5 pelo prefixo: 139 arquivos .php em ecidade/ (hab1_avaliacao001.php, ...)
```

Com `--aplicar`, ele faz o que eram vários blocos deste passo, na ordem e com as proteções que custaram defeito:

1. grava as alterações — no `location`, o `nginx.conf` **e** as cópias do regex em `dimensiona.py` e `redirecionamentos.py`;
   no `map`, reaproveita o comando da linha 2 do `faseb_map.conf` e **recusa** se alguma tela sair do `map`;
2. testa com `nginx -t` num container **descartável**; se falhar, **desfaz tudo** sem tocar no proxy;
3. recria o proxy (`--force-recreate`: *reload* não basta para bind mount de arquivo único);
4. confere o `X-Ecidade-Runtime` de telas novas (com e sem `/w/2/`) e do `login.php`.

O modo **`8b`** roda o `redirecionamentos.py` nas telas de menu da área (com `--todas`, também nas já concluídas) e lista
o que ainda manda o usuário ao 7.4, já sem `corpo.php` e `db_erros.php`, com o comando `abas` pronto para os destinos —
que antes precisam ser portados (passos 4 a 7). Na Configuração (16/11/2026): 257 telas examinadas, nada ao 7.4, ~30 s.

Os arquivos alterados entram no commit do lote (passo 9). As seções abaixo explicam cada etapa e servem para diagnosticar.

### Passo 8 — mandar as telas para o PHP 8.5

Esta é literalmente a linha que avança a migração. Em `docker/proxy/nginx.conf`, acrescente o prefixo à alternativa:

```nginx
location ~* ^(?:/w/[0-9]+)?/(?:cem|itbi?|agua?|jur|div|<novo>|tra)[0-9]*_ {
```

Três detalhes, cada um já causou roteamento silenciosamente errado:

| Detalhe | Por quê |
| --- | --- |
| `~*` e não `~` | há 29 arquivos com prefixo capitalizado (`Cem1_`, `Cai1_`) |
| `[0-9]*` e não `[0-9]?` | existe `jur01_` e `iss179_`, com dois e três dígitos |
| `(?:/w/[0-9]+)?` | na navegação real o desktop prefixa tudo com o id da janela |

```bash
# Testar a config ANTES, num container descartavel, e recriar SO se o nginx -t passou.
# Nao encadeie `nginx -t | tail -1 && up`: o && olharia o status do tail, e uma config
# quebrada derruba o proxy (aconteceu no lote 5 do Financeiro: "could not build map_hash").
IMG=$(docker inspect -f '{{.Config.Image}}' ecidade_proxy)
NET=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' ecidade_proxy)
docker run --rm --network $NET -v $PWD/docker/proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v $PWD/docker/proxy/faseb_map.conf:/etc/nginx/faseb_map.conf:ro $IMG nginx -t \
  && docker compose -f docker-compose.proxy.yml up -d --force-recreate   # reload NAO basta

for u in login.php <pref>1_x.php w/2/<pref>2_y.php; do
  printf "%-34s " "/$u"
  curl -sI "http://localhost:8090/$u" | grep -ai 'x-ecidade-runtime' | tr -d '\r'
done
```

**Saída esperada:** as telas do módulo com `PHP-8.5 (migrado)` e o `login.php` com `PHP-7.4 (referencia)`. Se o `/w/2/...` não migrar, o `(?:/w/[0-9]+)?` está faltando.

> O `nginx.conf` entra por bind mount de **arquivo único**. Editar no host cria um inode novo e o container continua com o antigo — por isso o `--force-recreate`, e por isso um `nginx -s reload` não resolve.

#### Prefixo que serve várias áreas

`con` aparece em 6 áreas do menu, `cai` em 4. Rotear por prefixo arrastaria módulos inteiros de outras áreas — o `con` levaria **511 telas** de Contabilidade, RH e Patrimonial junto. Nesses casos o roteamento é por **lista exata**, gerada do banco:

```bash
python3 scratchpad/gera_map_faseb.py <area>:<pref>,<pref> [<area>:<pref> ...]
docker compose -f docker-compose.proxy.yml up -d --force-recreate
```

> Curiosidade que já derrubou o proxy: `location ~` é sensível a maiúsculas e exigiu o `~*`; o `map` **não é**. Emitir as duas grafias faz o nginx recusar a configuração com `conflicting parameter`.

### Passo 8b — abas e redirecionamentos que voltam ao 7.4 (14ª lacuna)

**Por quê:** rotear a tela do menu **não basta**. Muitas telas são só um contêiner: ao abrir, carregam o formulário num
`<iframe>` (`cad1_face001` → `cad1_face004`) ou redirecionam (`db_redireciona(...)`). Esse destino **não está no menu**,
então o `map` (gerado do banco) não o conhece e ele fica no 7.4. A tela "está no 8.5" e o formulário que o usuário
preenche roda no 7.4. **Nenhuma bateria acusa isso**: as duas telas são idênticas, só que servidas pelo runtime errado.
Em 26/10/2026 eram 158 abas atrás de 90 telas de menu, nas três áreas concluídas até então.

No roteamento por **prefixo** a aba normalmente vai junto com o contêiner; mas rode a verificação sempre — o destino pode
ser de outro prefixo (`eso1_cadastroavaliacoes002` redireciona para `hab1_avaliacao002`).

```bash
# GET no 8.5 de cada tela de menu das areas listadas (e das abas ja roteadas: segundo salto)
python3 scratchpad/redirecionamentos.py "$(cat /tmp/sid.txt)" /tmp/redir.tsv TRIBUT,EDUCA,RECURSOS,PATRIM,FINANC,SA,CONFIG,<SUA_AREA>
grep -P '^NO_5\.6\t' /tmp/redir.tsv | grep -vP '\t(corpo|db_erros)\.php\t'     # TEM de sair vazio
```

Para cada linha `NO_7.4`:

1. **iframe** → portar o universo dos destinos (`TELAS=<destinos com a grafia do disco> python3 scratchpad/enumera.py <nome>`
   e passos 4 a 7, com bateria nos destinos). Depois acrescente o nome, **em minúscula**, a `docker/proxy/faseb_map_abas.txt`
   e regenere o `map` com o comando da linha 2 do `faseb_map.conf` (o gerador lê a lista).
2. **redireciona** → a mesma receita, com dois cuidados: o destino costuma ser **outro contêiner de abas** (ponha no `TELAS=`
   a família inteira: `ls ecidade | grep -i '^hab1_avaliacao'`), e o redirecionamento costuma ser **condicional** (a
   bateria compara os dois ramos: a tela de menu e o destino).
3. **`corpo.php`** (voltar ao início depois de erro ou configuração ausente) e **`db_erros.php`** (página genérica de erro)
   não são formulário nem lacuna.
4. **pasta** (`dbforms/…`) e **inexistente** também não. O proxy não roteia por pasta.

Depois de rotear, **rode o levantamento de novo**: ele abre as telas já roteadas e acusa o segundo salto (as abas do
contêiner que você acabou de rotear). **Limite:** o script só vê o que a tela faz ao abrir, por `GET` sem parâmetros. Abas
criadas por JavaScript ao clicar ficam de fora — na navegação manual, confira o `X-Ecidade-Runtime` dos iframes nas
ferramentas do navegador.

Se você acrescentar um prefixo ao `location`, acrescente-o também à cópia do regex que fica em
`scratchpad/redirecionamentos.py` e em `scratchpad/dimensiona.py` (variável `LOC`), senão os dois classificam as telas
desse prefixo como "no 7.4".

### Passo 9 — commit e registro

Um commit **por lote**, na branch da área, **sem push** (o envio é no fim da área):

```bash
git add -A -- ecidade/ CLAUDE.md docs/ docker/proxy/ scratchpad/ ':!docker/database/ecidade_base.sql' ':!docker/database/ecidade_base.sql.gz'
git diff --cached --name-only | grep -c ecidade_base.sql    # TEM de dar 0
git diff --cached --name-only | grep -c '^ecidade/tmp/'      # TEM de dar 0 (tmp/ e ignorado; se aparecer, algo saiu errado)
git commit
```

A mensagem registra a tabela de correções com quantidades, o resultado da bateria e **cada categoria ou lacuna nova**.

Atualize três coisas: a seção do módulo em `docs/registro/area-<área>.md`, o cabeçalho de estado do `CLAUDE.md` (módulos portados, rota, próximo passo) e qualquer categoria nova.

**Isto não é burocracia.** O registro (hoje `CLAUDE.md` + `docs/registro/`) tinha 4.265 linhas contra 1.271 de ferramental — o conhecimento é três vezes maior que o código, e é ele que torna o processo repetível por quem chegar depois. Registre também **quando este documento ou o catálogo estiverem errados**: várias seções do registro começam com ⚠ CORREÇÃO justamente por isso.

## Receituário — achei este erro, o que eu faço?

**As ferramentas dizem que algo mudou. Nunca dizem qual é a correção certa.** Esta seção é a consulta rápida.

### O princípio, antes da tabela

> O objetivo é **migrar**, não consertar. Quando o PHP 8 transforma em fatal algo que o 7.4 tolerava, a correção certa é a que **reproduz o comportamento do 7.4** — não a que conserta a intenção do autor.

**Critério prático:** se a alteração mudaria a saída do `:8080`, não é migração — é conserto, e fica de fora.

**Como descobrir o que o 7.4 fazia** — pergunte a ele, não à documentação:

```bash
docker exec ecidade_php74 php -r 'var_dump(<a expressao>);'
docker exec ecidade_php85 php -r 'var_dump(<a expressao>);'
```

Faça isso com uma **tabela de valores** (`0`, `""`, `"0"`, `"abc"`, `null`, `false`), não com um caso só. Várias correções deste projeto só se mostraram erradas no terceiro valor.

### Tabela de correções já decididas

| Mensagem de erro, ou sintoma | Categoria | Correção |
| --- | --- | --- |
| Campo preenchido vira "não informado" | `$this->X == ""` com X inteiro | `X === 0 \|\| X === 0.0 \|\| X == ""` |
| `parse_str() expects exactly 2 arguments` | `parse_str` de 1 argumento | `parse_str($s, $a); extract($a);` |
| Objeto "funciona" mas vem vazio | construtor estilo PHP 4 | renomear para `__construct` |
| `Call to undefined function split()` | `split` removido no PHP 7 | `explode` se literal, `preg_split` se regex |
| `pg_numrows(): Argument #1 must be of type PgSql\Result` | `pg_*` sobre `false` | `($r ? pg_numrows($r) : 0)` |
| `pg_result(): ... false given` | idem, mas devolve **`NULL`** no 7.4 | `($r ? pg_result($r,0,0) : null)` |
| Campo some da tela, sem erro | `is_resource()` sobre resultado | `is_resource($r) \|\| is_object($r)` |
| `<select>` vem vazio, sem erro | `gettype($x) == "resource"` | `... \|\| is_object($x)` |
| Widget inteiro some | `$x < 3` com `$x` string | `(float)$x < 3` |
| `Unsupported operand types: string / int` | aritmética com string | `(float)` ou `(int)`, o que o 7.4 produzia |
| `'break' not in the 'loop' or 'switch'` | `break` fora de laço | `exit;` se alcançável, remover se não |
| `Unparenthesized a ? b : c ? d : e` | ternário aninhado | `(a ? b : c) ? d : e` — 7.4 associa à **esquerda**. Com **três ou mais** níveis, **à mão**: a `ParenthesizeNestedTernaryRector` só põe os parênteses de fora (ver abaixo) |
| `in_array(): Argument #2 must be of type array` | *haystack* nulo | `is_array($h) && in_array(...)` |
| `sizeof(): must be of type Countable\|array` | `sizeof(null)` | `sizeof((array)$x)` |
| `array_merge(): Argument #2 must be of type array` | argumento nulo | ternario com `is_array()` nos dois |
| `DivisionByZeroError` | divisão por zero | o 5.6 dava `false` e a correção usada era `($d ? $n/$d : 0)`; o **7.4 dá `INF`** (com aviso), medido em 22/11/2026 — confira no 7.4 o que a tela faz com o resultado antes de escolher o valor |
| `Undefined constant "l"` | constante indefinida | `"l"` — o 7.4 usava o próprio nome |
| `ArgumentCountError: Too few arguments` | argumento faltando | passar o valor que o 7.4 produzia |
| Data gravada = **hoje** em vez da época | `date($fmt, null)` | `date($fmt, (int)$x)` |
| Layout do PDF deslocado | `"J" > 0` no FPDF | `(float)$ln > 0` — **não** corrigir a chamada |
| `Call to undefined function each()` | `each()` removido no PHP 8 | **à mão**, nunca `foreach` (ver abaixo) |
| `count(): Argument #1 must be of type Countable\|array` | `count(null)`/`count("")` — o 7.4 dava 0 ou 1 | `count((array)$x)` |
| `Call to undefined function get_magic_quotes_gpc()` | removida no PHP 8; no 7.4 do projeto valia `false` | trocar a chamada por `false` |
| `fputs(): Argument #1 ($stream) must be of type resource, bool given` | `fopen` falhou (`tmp/` sem permissão, caminho errado) | `$fd && fputs($fd, ...)` — o 7.4 só avisava |
| `pg_lo_export(): Argument #1 ... PgSql\Connection` | ordem legada `($oid, $arq, $conn)`, que o 7.4 aceitava | `pg_lo_export($conn, $oid, $arq)` — funciona nos dois |
| `Attempt to assign property "x" on null` | o 7.4 criava o objeto sozinho (*auto-vivificação*) | `if (empty($o)) $o = new stdClass();` antes da linha |
| `Non-static method X::m() cannot be called statically` | chamada estática a método sem `$this` | declarar o método `static` (conferir que ele não usa `$this`) |
| `Declaration of Filha::m() must be compatible with Mae::m()` | LSP — em geral depois do `OptionalParametersAfterRequiredRector` | espelhar a assinatura da mãe na filha |

**O ternário aninhado de três níveis à mão.** A `ParenthesizeNestedTernaryRector` existe e está entre as regras aceitas,
mas só parentesa o nível de fora: em `a ? b : c ? d : e ? f : g` ela produz `(a ? b : c ? d : e) ? f : g`, que **continua
não compilando no 8.5**, e na passada seguinte diz que não há nada a mudar. Medido em 23/11/2026 no
`src/RecursosHumanos/RH/PontoEletronico/Calculo/Horas/Falta.php`, linha 143. Além disso, o `enumera.py` não tem detector
de ternário aninhado: um arquivo que só tem esse problema nem entra nos alvos do Rector. Quem acusa é o `php -l` do 8.5,
no passo 5. A forma fiel ao 7.4 põe todos os parênteses pela esquerda:

```php
// antes:  $x = a ? b : c ? d : e ? f : g;
$x = ((a ? b : c) ? d : e) ? f : g;
```

Confira sempre com `php -l` nos dois runtimes.

**O `each()` à mão.** O e-cidade tem laços que dependem do ponteiro interno **já exaurido** por um laço anterior e que,
por isso, nunca executam no 7.4. `foreach` faria esses laços rodarem. A forma fiel, que anda no mesmo ponteiro:

```php
// antes:  while (list($k, $v) = each($a)) {
while (is_array($a) && (($k = key($a)) !== null) && ((($v = current($a)) || true) && (next($a) || true))) {
```

Se houver `reset($a)` logo antes do laço, `foreach` é fiel — mas a forma acima também é, e não exige julgar o contexto.

### Dois casos que ensinam o princípio

**O `"J"` do FPDF.** Passar `"J"` como número de linha é defeito de quem chamou. Mas corrigir a chamada **mudaria o layout do relatório no 7.4**. Então o defeito fica, e o contorno vai dentro do FPDF.

**O `1969-12-31`.** `date("Y-m-d", "2024-01-01")` devolve `1969-12-31` no 7.4 — resultado sem sentido. A correção `(int)$dt` **preserva o resultado sem sentido**, porque mudá-lo seria conserto.

### Como aplicar uma correção num arquivo

A tabela acima diz **qual** é a correção. Esta parte diz **como** aplicá-la sem quebrar nada.

#### A regra que não pode ser violada: edite em BYTES

**64% dos arquivos são LATIN-1**, não UTF-8. Abrir como texto e salvar corrompe toda a acentuação — e o `git diff` mostra o arquivo inteiro como alterado. Sempre `"rb"` e `"wb"`.

```bash
(cd ecidade && python3 - <<'PY'
import re
arq = "cai1_lista001.php"
b = open(arq, "rb").read()              # rb = BYTES, nunca "r"

velho = b'texto exato que esta no arquivo'
novo  = b'texto corrigido'

n = b.count(velho)
print(f"ocorrencias: {n}")
assert n > 0, "nao achou -- confira o texto exato, com os espacos"

open(arq, "wb").write(b.replace(velho, novo))   # wb = BYTES
print("aplicado")
PY
)
```

#### Exemplo real: a guarda `pg_*`

Este é o caso mais comum — apareceu em 111 pontos ao longo do projeto. Repare que ele **conta antes, confere o risco, e só então escreve**:

```bash
(cd ecidade && python3 - <<'PY'
import re
arq = "cai1_lista001.php"
b = open(arq, "rb").read()

RX = re.compile(rb'(?<!\? )\b(pg_num_rows|pg_numrows)\s*\(\s*(\$\w+)\s*\)')

# ANTES de escrever: o resultado e comparado com === em algum lugar?
# Se for, a guarda MUDA o comportamento -- o 7.4 dava false, a guarda da 0.
alvos = {m.group(2) for m in RX.finditer(b)}
risco = [v.decode() for v in alvos
         if re.search(rb'===\s*' + re.escape(v) + rb'|' + re.escape(v) + rb'\s*===', b)]
print(f"variaveis: {len(alvos)}   RISCO de '===' a jusante: {len(risco)} {risco}")
assert not risco, "PARE: ha comparacao com === -- tratar a mao"

novo, n = RX.subn(lambda m: b'(' + m.group(2) + b' ? ' + m.group(1)
                            + b'(' + m.group(2) + b') : 0)', b)
open(arq, "wb").write(novo)
print(f"{n} guarda(s) aplicada(s)")
PY
)
```

> **O `(?<!\? )` no início do regex evita guardar o que já está guardado.** Sem ele, rodar duas vezes produz `($r ? ($r ? pg_numrows($r) : 0) : 0)`.

#### Depois de aplicar — sempre, nesta ordem

```bash
# 1. o arquivo ainda parseia nos DOIS runtimes?
for c in ecidade_php74 ecidade_php85; do
  printf "%-16s " "$c"
  docker exec -i $c php -l /var/www/html/<arquivo> </dev/null 2>&1 | tail -1
done

# 2. a tela que divergia fechou?
ONLY="<tela>.php" python3 scratchpad/cmp.py "$(cat /tmp/sid.txt)" '^<pref>[0-9]*_' /dev/null

# 3. a bateria inteira continua boa? (pode ter quebrado outra tela)
python3 scratchpad/cmp.py "$(cat /tmp/sid.txt)" '^<pref>[0-9]*_' /tmp/<pref>_div.txt
```

**Se o passo 1 falhar, desfaça imediatamente** — não tente consertar por cima:

```bash
git checkout -- ecidade/<arquivo>
```

#### Se você quebrou vários arquivos

Aconteceu comigo: uma transformação em massa quebrou 7 arquivos de uma vez. O caminho de volta é o mesmo, e **é melhor desfazer tudo e refazer com cuidado** do que remendar:

```bash
# desfazer TUDO que nao esta commitado (perde o lote inteiro -- so se for isso mesmo)
git checkout -- ecidade/

# ou desfazer so os que voce acabou de quebrar
git checkout -- ecidade/arquivo1.php ecidade/arquivo2.php

# ou, se ja aplicou e quer so reverter SUA substituicao:
(cd ecidade && python3 -c "
import sys
for f in sys.argv[1:]:
    b = open(f,'rb').read()
    open(f,'wb').write(b.replace(b'texto novo', b'texto velho'))
    print(f)" arquivo1.php arquivo2.php)
```

#### A regra de ouro desta seção

**Nunca aplique em mais de um arquivo antes de ter testado em um.** Rodar o `php -l` num arquivo custa 2 segundos e teria evitado o único incidente grave deste projeto — 25 substituições aplicadas de uma vez, 7 arquivos quebrados, inclusive um do núcleo.

### Corrigir na aparição, nunca em massa

Quando achar uma categoria, a tentação é varrer a base. **Não varra.** Medido para as guardas `pg_*`:

|  |  |
| --- | --- |
| Chamadas sem guarda no universo do `arr` | 1.083 |
| Quantas de fato precisaram | **1** |
| Taxa de acerto de uma varredura | \~0,1% |
| Pontos onde a varredura **introduziria** regressão | **25** |

Em `con2_razaodespesa002.php:170` há `if ($rows === 0)`. Com a guarda devolvendo `0`, a condição passa a ser verdadeira onde no 7.4 era falsa.

> **Eu violei este princípio uma vez e o preço apareceu em um minuto.** Apliquei aspas em 25 constantes indefinidas e **quebrei 7 arquivos, inclusive `libs/db_stdlib.php` do núcleo**. As 25 não eram PHP — eram colunas de banco dentro de strings SQL. Um regex que lê bytes **não distingue código de string**.

### Ao corrigir arquivo do núcleo: há uma cópia que executa

Todo `include` passa por `modification()`, que devolve uma cópia personalizada se ela existir:

```bash
find ecidade/extension/modification -name '<arquivo>'
docker exec -u root ecidade_php74 chmod 666 /var/www/html/<caminho da copia>
```

**Corrija as duas.** Mas confirme qual executa de fato, com uma sonda — já houve caso em que o original executava e a cópia não.

### Quando parar e perguntar a alguém

- Categoria de incompatibilidade que **não está no catálogo (`docs/registro/`)**.
- Correção que mudaria **comportamento**, não só compatibilidade.
- Duas verificações discordando — uma delas está quebrada.

## As armadilhas — todas se parecem com sucesso

Se você levar uma coisa só deste documento, leve esta: **quase nenhuma armadilha aqui dá erro.** Elas reportam um número tranquilizador e você segue em frente achando que verificou.

### Armadilhas de medição

| Sintoma | Causa | Antídoto |
| --- | --- | --- |
| Contagem absurdamente baixa | **64% da base é LATIN-1** e o `grep` a trata como binário, pulando em silêncio | `grep -a` sempre, ou ler bytes em Python |
| "0 arquivos com erro" num lote grande | `php -l` dentro de `while read` consome o stdin e o laço dá **uma volta só** | `php -l "$f" </dev/null` e `docker exec -i` |
| `git diff` vazio depois de um `checkout` | `git checkout <commit> -- caminho` **atualiza o índice** | `git diff HEAD` |
| Categoria `0 == ""` nunca chega a zero | o detector casa com a **própria guarda** | contar só ocorrências sem o prefixo da guarda |
| Biblioteca inteira invisível | filtrar por `*.php` — o `dbagata/` usa `.class` e `.inc` | incluir as três extensões |
| `UnicodeDecodeError` ao ler saída do psql | a mensagem de erro vem em **LATIN-1** | decodificar como `latin-1` |

### O instrumento de conferência também erra — quatro vezes até agora

| Defeito | O que ele reportava |
| --- | --- |
| `serialize()` de `DOMElement` | 3 classes "com erro" que funcionavam |
| `grep` com aspas no shell | "zero linhas bem formadas" numa saída válida |
| Invólucro contando linhas de saída | 57 de 202 classes, veredito "idêntico" |
| Harness de escrita com os dois lados vazios | "SQL de escrita de NEGÓCIO IDÊNTICO" |

O último é o pior: ele **aprovava o nada**. Foi achado por acidente, rodando com um nome de tela inexistente — 404 nos dois lados, zero statements, veredito positivo.

> **Duas regras que valem sempre:**
>
> 1. Duas verificações discordando significa que **uma delas está quebrada**, não que o dado está ruim.
> 2. Um resultado que não distingue "igual" de "nada aconteceu" **não é verificação**. Conte sempre quantos itens entraram e quantos saíram.

### A raiz comum

Todas têm a mesma origem: **a verificação parte da lista que a própria ferramenta gerou.** Por isso oito lacunas de enumeração sobreviveram a vários lotes, e por isso três delas só apareceram quando alguém navegou o sistema.

A defesa é sempre **conferir contra uma fonte que a ferramenta não produziu**:

| Para conferir | Use esta fonte independente |
| --- | --- |
| a enumeração | o `ls` do diretório |
| a que área uma tela pertence | o menu no banco |
| se o código está certo | o **outro runtime** |
| por que uma tela quebrou | o log do PostgreSQL |
| se o harness rodou mesmo | contar entradas e saídas |

## O custo medido

Vinte lotes, 2.055 arquivos distintos alterados, área Tributário completa em 16 de 16 módulos.

| Lote | Telas | Arquivos alterados | Bateria |
| --- | --- | --- | --- |
| `cem` | 116 | 187 | 115/116 |
| `itb` | 120 | 192 | 116/120 |
| `agu` | 224 | 171 | 222/224 |
| `jur` | 145 | 137 | 144/145 |
| `div` | 148 | 158 | **148/148** |
| `mar` | 35 | 19 | **35/35** |
| `not` | 14 | 17 | **14/14** |
| `fis` | 353 | 384 | 350/353 |
| `iss` | 400 | 280 | 397/400 |
| `dvr` | 33 | 197 | **33/33** |
| `arr` | 162 | 116 | **162/162** |
| `tri` + `inf` | 63 | 44 | **63/63** |
| `amb` + `pre` | 85 | 57 | **85/85** |
| `cad` | 166 | 210 | **166/166** |
| `cai` | 101 | 150 | **101/101** |
| `pro` `con` `prot` `rec` `dv` | 71 | 109 | **71/71** |
| `dbagata/` + núcleo | — | 220 | — |

O total: **2.222 telas idênticas de 2.236 comparadas (99,4%)**, 14 divergências, todas caracterizadas e **nenhuma defeito de migração** — são telas que quebram no 5.6 e funcionam no 8.5, fragmentos de include que não são telas, e variáveis nunca instanciadas no próprio legado.

As correções, somadas:

| Categoria | Ocorrências |
| --- | --- |
| Guardas `0 == ""` | 6.552 |
| `split` / `ereg` → `preg_*` | 2.105 |
| Construtores PHP 4 | 1.175 |
| `parse_str` + `extract` | 886 |
| Guardas `pg_*` | 111 |

### Duas lições sobre estimativa

**A métrica de resíduo envelhece.** O `arr` foi previsto como o maior lote da área — 343 arquivos, "o dobro do maior já executado". Saiu com **116**, porque dez módulos anteriores já haviam pago 366 dos 787 arquivos do seu universo. Num porte incremental, cada módulo pré-paga o resíduo do seguinte.

**O prefixo não define a fronteira técnica.** Para os prefixos compartilhados, portar tudo custaria 2.072 arquivos; portar só o universo das telas efetivamente roteadas custou **909**. O `con` sozinho custaria 1.019 arquivos para entregar 30 telas — e arrastaria a Contabilidade inteira para o runtime novo.

## O mínimo de PHP que você precisa saber

Você não precisa programar em PHP para executar este manual. Precisa reconhecer **seis construções** e entender **uma mudança de regra**.

### A mudança de regra que explica metade do trabalho

Até o PHP 7, comparar um número com um texto convertia o **texto em número**. A partir do PHP 8, converte o **número em texto**.

```
            0 == ""        0 == "f"       "text" < 3
PHP 7.4:    true           true           true
PHP 8.5:    FALSE          FALSE          FALSE
```

O código é válido nas duas versões. Ninguém avisa. O sistema simplesmente passa a decidir diferente — e no e-cidade isso significa um campo de formulário que **nunca é lido**, gravando zero no lugar do valor digitado.

Esse único fato gerou **6.552 correções**, 60% de todo o trabalho.

### As construções que você vai ver

| Construção | O que é | Por que importa |
| --- | --- | --- |
| `$this->X` | um campo de um objeto | onde vivem as guardas `0 == ""` |
| `function cl_cgm()` dentro de `class cl_cgm` | construtor no estilo antigo | **nunca executa** no PHP 8, sem erro |
| `split("#", $x)` | corta texto em pedaços | função removida no PHP 7 |
| `parse_str($s)` | lê a query string da URL | exige 2 argumentos desde o PHP 8 |
| `pg_numrows($r)` | conta linhas de uma consulta | explode se a consulta falhou |
| `include(modification("x.php"))` | carrega outro arquivo | pode carregar uma **cópia**, não o original |

### Três palavras do projeto

**Runtime** — a versão do PHP rodando. Aqui são dois ao mesmo tempo: `:8080` é o 7.4 (referência) e `:8085` é o 8.5 (migrado). O `:8090` é o proxy que decide qual atende cada tela.

**Universo** — todos os arquivos que um módulo alcança, não só os que têm o prefixo dele.

**Guarda** — um trecho acrescentado para fazer o PHP 8 se comportar como o 7.4. Não conserta o código: **preserva** o comportamento antigo.

## Escolher o próximo módulo

Não siga a ordem registrada sem conferir — ela envelhece. Cada módulo portado **pré-paga** parte do custo do seguinte.

```bash
python3 scratchpad/residuo.py
```

O caso que prova: o `arr` foi previsto como o maior lote da área, 343 arquivos. Saiu com **116**, porque dez módulos anteriores já haviam pago 366 dos 787 arquivos do seu universo.

Dois critérios, e você precisa dos dois:

| Critério | Como medir | O que decide |
| --- | --- | --- |
| **Resíduo** | `residuo.py` | se a fatia é cortável |
| **Alcançabilidade** | itens ligados em `configuracoes.db_menu` | se ela é **demonstrável** |

O módulo `tra` foi escolhido como piloto só pelo resíduo (era zero) e depois se descobriu que **nenhuma tela do menu leva até ele**. O trabalho não foi perdido — validou a receita e revelou quatro categorias — mas o piloto teve de ser refeito.

## Onde está cada coisa

| Arquivo | O que é |
| --- | --- |
| `CLAUDE.md` + `docs/registro/` | **o catálogo** — 4.265 linhas na época, divididas em 26/10/2026: todas as categorias, decisões e correções, com a medição que as comprova |
| `.claude/skills/migrar-modulo/SKILL.md` | o procedimento condensado |
| `scratchpad/enumera.py` | passos 1 a 3 |
| `scratchpad/rector-curado.php` + `rector-rules/` | passo 4 |
| `scratchpad/instancia_classes.php` | passo 6 |
| `scratchpad/escrita.php` | passo 6b |
| `scratchpad/escrita_post.py` | nível 3: POST real comparando o SQL emitido |
| `scratchpad/payload_auto.py` | gera o payload do nível 3 lendo o formulário |
| `scratchpad/cmp.py` | passo 7 |
| `scratchpad/harness_robusto.sh` | faz o passo 6 sobreviver a um fatal |
| `scratchpad/gera_map_faseb.py` | roteamento por lista, gerado do banco |
| `scratchpad/residuo.py` | escolha do próximo módulo |
| `scratchpad/dimensiona.py` | dimensionar as áreas que faltam (*O fluxo de uma área*, B) |
| `scratchpad/prefixos_area.py` | quais prefixos uma área precisa migrar e como rotear cada um (*O fluxo de uma área*, B) |
| `scratchpad/rector_lote.py` | passo 4 em um comando: simula, classifica as regras, aplica até zerar com `--aplicar` |
| `scratchpad/nivel3.py` | nível 3 em um comando: `--candidatas`, POST nos dois, log ligado/desligado, escrita fora das tabelas |
| `scratchpad/rotear.py` | passos 8 e 8b em um comando: `location`, `map`, `abas` (com `--aplicar`) e o levantamento `8b` |
| `scratchpad/verifica_lote.py` | passos 4b a 7 de uma vez, com relatório único em `ecidade/tmp/verif/` |
| `scratchpad/ns_fecho.py` | 9ª frente da enumeração (classes com namespace); chamado pelo `enumera.py` |
| `scratchpad/carrega_arquivo.php` | passo 5b: carregar cada arquivo (LSP) |
| `scratchpad/porclasse.sh` | passos 6/6b: uma classe por processo |
| `scratchpad/negada_alvos.py`, `negada.php`, `negada_compara.py`, `negada_corrige.py` | passo 6c: forma negada (medir, comparar com veredito do lote, corrigir) |
| `scratchpad/guarda_ciclo.py`, `campo_ciclo.py` | passo 7: guardas `pg_*` na aparição |
| `scratchpad/redirecionamentos.py` | passo 8b: abas e redirecionamentos que voltam ao 7.4 |
| `docker/proxy/faseb_map_abas.txt` | passo 8b: abas e destinos roteados por lista |

**Quando este documento e o registro (`CLAUDE.md` + `docs/registro/`) divergirem, o registro manda** — é ele que é atualizado a cada lote. Se encontrar uma divergência, corrija este guia **e** a skill `migrar-modulo`.
