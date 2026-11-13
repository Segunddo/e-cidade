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
  │ 4. Rector (40 na denylist) │ → │ 4b. Portão de funções vs 5.6     │
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

A ordem importa: o 8.5 e o proxy dependem da rede que o 5.6 cria.

Na primeira vez, siga a seção *Como rodar o projeto hoje* do `README.md` (clone, banco, senha). Depois disso:

```bash
docker volume create ecidade_sessions && docker volume create ecidade_tmp
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d
# como root DENTRO do container: varios desses arquivos pertencem ao www-data, e um chmod
# no host falha neles (o "; true" no fim impede que uma falha aborte o resto)
docker exec -u root ecidade_php56 sh -c 'chmod 1777 /tmp; cd /var/www/html; chmod -R 777 storage bootstrap/cache; chmod 777 extension/log tmp arquivos; chmod 666 extension/log/*.log; true'
docker compose -f docker-compose.php85.yml up -d
docker compose -f docker-compose.proxy.yml up -d
```

**Depois de reiniciar a máquina** os containers ficam parados — e qualquer comando com `docker exec` falha com
`container ... is not running`. Religue nesta ordem, **sem** `docker compose down` (o banco não tem volume de
persistência: `down` apaga os dados; `--remove-orphans` apaga os quatro containers):

```bash
docker start ecidade_database ecidade_php56
docker start ecidade_php85 ecidade_proxy
docker exec -u root ecidade_php56 chmod 1777 /tmp
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

Pegue uma sessão autenticada e requisite uma tela de módulo **já verificado**:

```bash
SID=$(docker exec -i ecidade_php56 sh -c \
  'grep -la DB_modulo /var/lib/php/sessions/sess_* | head -1' </dev/null | sed 's#.*/sess_##' | tr -d '\r\n')
echo "$SID" > /tmp/sid.txt
docker exec -u root -i ecidade_php56 sh -c \
  "cp /var/lib/php/sessions/sess_$SID /tmp/_d.bak && chmod 666 /tmp/_d.bak" </dev/null

curl -s -o /dev/null -w '%{http_code} %{size_download}\n' \
  -b "ECIDADEWINDOWMAIN=$SID" http://localhost:8080/cem1_campas001.php
```

| Saída | Significa |
| --- | --- |
| `200` e alguns milhares de bytes | ambiente são, pode começar |
| `500` e 0 bytes | problema de **ambiente**, não do seu porte — volte ao passo 2 |

### 5. Duas proibições

- **Nunca alterar `docker-compose.yml`.** É a referência funcional do experimento.
- **Nunca commitar `docker/database/ecidade_base.sql`** — são 314 MB. Já entrou por engano num `git add -- docker/` e precisou ser removido por `amend`.

## O fluxo de uma área — comece por aqui

Os passos 1 a 9 deste guia portam **um lote**. O trabalho, porém, é organizado por **área do menu** (Tributário, Educação,
Saúde…), e uma área vira vários lotes. A moldura em volta dos passos é esta:

```
 A. branch da área ← base-php84
 B. dimensionar a área e dividir em lotes
 C. para cada lote, UM POR VEZ:  passos 1 → 9  (commit local, sem push)
 D. fim da área: bateria completa → conferência pelo proxy → registro → push → PR para base-php84
```

### A. Criar a branch

Cada área nasce da `base-php84`, que já tem todas as áreas concluídas:

```bash
git fetch origin
git checkout -b <area>/migracao origin/base-php84      # ex.: assistencia-social/migracao
```

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

`Menu` são as telas de menu da área, `Faltam` as que ainda vão ao 5.6, `Fant.` as que o menu cita mas não existem em disco
(quebram igual nos dois; só se registram), `A alterar` os arquivos que o lote vai mudar. Para cada prefixo da área, decida
**como ele será roteado** — é o que define o lote:

| Situação do prefixo | Roteamento | Lote |
| --- | --- | --- |
| só esta área usa (ou o resto já foi migrado) | **`location`** por prefixo (passo 8) | o prefixo inteiro: `python3 scratchpad/enumera.py <pref>` |
| outras áreas ainda pendentes também usam | **`map`** por lista, gerada do banco (*Passo D* de *Quando o prefixo serve várias áreas*) | só as telas da área: `TELAS=@/tmp/telas_lote.txt python3 scratchpad/enumera.py <nome-do-lote>` (uma tela por linha, com a grafia do disco e caminho **absoluto** — o script muda para `ecidade/`; o `<nome-do-lote>` vira só o nome dos arquivos de saída) |

A seção *Quando o prefixo serve várias áreas* mostra como medir quantas telas de outras áreas um prefixo arrastaria. Lote
grande (mais de ~300 arquivos a alterar) se divide por subprefixo (`sau1_`, `sau2_`…). Registre a divisão em
`docs/registro/area-<área>.md` antes de começar.

### C. Um lote por vez

Para cada lote: passos 1 a 9. Ao terminar, **commit local** (passo 9) e **pare** — o próximo lote começa limpo.

- **A bateria do passo 7 é só do lote.** Se o lote mexeu no núcleo ou numa classe que muitas telas alcançam, rode também
  uma **bateria dirigida** às telas já roteadas que chegam ao trecho alterado (ver *Preciso refazer a bateria dos outros
  módulos?*).
- **Não envie ao GitHub no meio da área.** Os commits de lote ficam locais até a bateria completa do fim. Se ela achar uma
  regressão, `git bisect` entre os commits de lote acha o culpado.

### D. Fim da área

**1. Bateria completa** — todas as telas do `location` e todas as do `map`. Leva **cerca de 3 horas**; antes, zere o log do
banco, que cresce gigabytes com os erros de SQL das baterias (`sudo truncate -s 0 $(docker inspect -f '{{.LogPath}}' ecidade_database)`).

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
c = {"8.5": 0, "5.6": 0, "fantasma": 0}
for t in telas:
    if t not in disco: c["fantasma"] += 1; continue
    h = subprocess.run(["curl","-sI",f"http://localhost:8090/w/2/{disco[t]}"], capture_output=True).stdout.decode("latin-1")
    rt = "8.5" if "PHP-8.5" in h else "5.6"
    c[rt] += 1
    if rt == "5.6": print("NO_5.6", disco[t])
print(f"{area}: {c['8.5']} no 8.5, {c['5.6']} no 5.6, {c['fantasma']} fantasmas (de {len(telas)})")
PY
```

Saída esperada, na Configuração: `CONFIG: 204 no 8.5, 0 no 5.6, 5 fantasmas (de 209)`. **Tem de dar `0 no 5.6`.** Cada
`NO_5.6` é uma tela de menu que ficou fora do roteamento — rotear (e portar, se não foi) antes de seguir.

**3. Ensinar aos scripts que a área acabou.** `scratchpad/dimensiona.py` tem a tupla `JA` (áreas concluídas) e uma cópia
do regex do `location`; `scratchpad/redirecionamentos.py` tem outra cópia do regex. Acrescente a área a `JA` e os prefixos
novos aos dois regex, senão a próxima medição conta esta área como pendente.

**4. Registrar** (passo 9) — a conclusão em `docs/registro/area-<área>.md` (lotes, bateria completa, proxy) e o estado no
`CLAUDE.md`.

**5. Enviar e abrir a PR:**

```bash
git push -u origin <area>/migracao
```

Abra a PR no GitHub com base **`base-php84`** (não `master`). Depois do merge, a próxima área parte da `base-php84`
atualizada (`git fetch` e passo A).

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
> **`A ALTERAR` é uma cota superior, não o que o Rector vai mudar.** O detector de `$this->X == <literal>` casa com a
> própria guarda já aplicada (ver *As armadilhas*), então arquivos já portados voltam na lista. No `soc` (12/11/2026):
> `A ALTERAR: 20`, e o Rector mudou **3**. Quem diz o número real é o passo 4.

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
cd ecidade && python3 - <<'PY'
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

**A regra que manda em tudo:** os dois containers montam o **mesmo diretório**, então cada arquivo precisa rodar em PHP 5.6 *e* em 8.5. Um arquivo que não parseia no 5.6 derruba o runtime que serve o login e todos os módulos ainda não migrados.

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
> do Laravel 5.4 (Guzzle, PsySH, Zend Diactoros, PHPUnit). Essas bibliotecas antigas declaram parâmetros de um jeito que
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

**2. `Php4ConstructorRector` apareceu na lista?** Se o módulo tem construtores PHP 4 (o passo 1 disse quantos) e essa regra **não** aparece, o pin de versão quebrou. Sem `->withPhpVersion(PhpVersion::PHP_80)` na config, o Rector lê o `composer.json` do projeto (`">=5.6.4"`) e **desliga em silêncio** toda regra com *version bonding*, reportando sucesso.

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
docker exec ecidade_php56 php -r '<a expressao nova>'
docker exec ecidade_php85 php -r '<a expressao nova>'
```

| Se o 5.6… | Veredito |
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

**Quando precisa:** quando a correção não é um *upgrade* de versão, e sim um **shim** que preserva a semântica do 5.6. O Rector não tem regra para isso porque, do ponto de vista dele, o código já está correto nas duas versões.

Este projeto tem duas, em `scratchpad/rector-rules/`:

| Regra | Linhas | Cobre |
| --- | --- | --- |
| `GuardaComparacaoLiteralRector` | 122 | `$this->X == "<literal>"` → guarda do 5.6 |
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

## Passos 4b a 6c — os portões

Cada portão pega uma classe de defeito que os outros não veem. Nenhum é opcional.

### Passo 4b — portão de funções contra o 5.6

**Por quê:** `str_starts_with()` e `random_int()` **compilam** no 5.6 e explodem só em execução. Num teste real foram 93 arquivos com `php -l` limpo que quebrariam na tela.

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
docker cp /tmp/fn.txt ecidade_php56:/tmp/fn.txt
docker exec -i ecidade_php56 php -r '
$f=array_filter(array_map("trim",file("/tmp/fn.txt",FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES)));
$x=array(); foreach($f as $y) if(!function_exists($y)) $x[]=$y;
echo count($f)," novas | AUSENTES: ",count($x); if($x) echo " -> ".implode(", ",$x); echo "\n";' </dev/null
```

**Precisa dar `AUSENTES: 0`.** Qualquer nome na lista significa que o Rector emitiu uma função que o 5.6 não tem → banir a regra que a emitiu e refazer o passo 4.

### Passo 5 — `php -l` nos dois runtimes

**Por quê:** é o único instrumento que acha quatro categorias invisíveis ao `grep` — assinatura incompatível com a classe pai, `=& new`, `break` fora de laço e ternário aninhado sem parênteses.

```bash
cat ecidade/tmp/<pref>_universo.txt | sed '/^$/d' \
  | grep -E '\.(php|class|inc)$' | sed 's#^#/var/www/html/#' > /tmp/uni.txt

for c in ecidade_php56 ecidade_php85; do
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
for v in 56 85; do     # um processo por arquivo: um fatal nao derruba o resto
  docker cp scratchpad/carrega_arquivo.php ecidade_php$v:/tmp/ca.php
  docker exec -i ecidade_php$v sh -c 'while read f; do php /tmp/ca.php "$f" </dev/null 2>/dev/null | tail -1; done' \
    < /tmp/carga.txt > /tmp/carga_$v.txt
done
wc -l /tmp/carga.txt /tmp/carga_56.txt /tmp/carga_85.txt      # os tres TEM de bater
# so interessa o que carrega no 5.6 e NAO no 8.5
join -t$'\t' <(cut -f1,2 /tmp/carga_56.txt | sort) <(cut -f1,2 /tmp/carga_85.txt | sort) | awk -F'\t' '$2=="OK" && $3!="OK"'
```

Cada linha de saída é `arquivo<TAB>OK` ou `arquivo<TAB>FATAL<TAB>mensagem` (no 8.5 o fatal vira `ERRO`). **O `join` precisa
sair vazio.** Arquivos que falham **nos dois** (interface em arquivo que não foi incluído, código morto) são pré-existentes:
anote o número e siga — no universo do `soc` eram 12 de 384, em 12/11/2026 (~30 s nos dois runtimes).

### Passo 6 — instanciar as classes

**Por quê:** valida a alteração de maior risco. No PHP 8 um construtor estilo PHP 4 **nunca executa** — sem erro, sem aviso, sem log. O objeto parece funcionar e produz resultado errado.

```bash
grep -E '^classes/' ecidade/tmp/<pref>_universo.txt | sort -u > /tmp/cls.txt
for c in ecidade_php56 ecidade_php85; do
  docker cp scratchpad/instancia_classes.php $c:/tmp/ic.php >/dev/null
  docker cp /tmp/cls.txt $c:/tmp/cls.txt >/dev/null
  sh scratchpad/harness_robusto.sh $c
done
diff <(sort /tmp/rb_ecidade_php56.txt) <(sort /tmp/rb_ecidade_php85.txt)
```

**Precisa dar diff vazio** — e o número de classes na saída precisa bater com `wc -l /tmp/cls.txt`.

> **Um diff vazio de dois arquivos vazios não é aprovação.** No `cad`, a lista tinha 202 classes e a saída trazia **57**: o processo morria num arquivo e os dois runtimes morriam no mesmo, então o resultado aparecia como "idêntico". O `harness_robusto.sh` registra o culpado, pula e continua — o número foi para 201 de 202.

### Passo 6b — caminho de escrita

**Por quê:** a bateria do passo 7 faz só `GET`. As guardas `0 == ""` — **60% de todas as correções do projeto** — só disparam no `POST`. Sem este passo elas não seriam exercitadas por nada.

```bash
for c in ecidade_php56 ecidade_php85; do
  docker cp scratchpad/escrita.php $c:/tmp/esc.php >/dev/null
  docker exec -i $c php /tmp/esc.php /tmp/cls.txt </dev/null > /tmp/w_$c.txt 2>/dev/null
  printf "%-16s %6s linhas\n" "$c" "$(grep -c . /tmp/w_$c.txt)"
done
diff /tmp/w_ecidade_php56.txt /tmp/w_ecidade_php85.txt
```

**Qualquer linha de diff é defeito** — significa que o 5.6 lê o valor do formulário e o 8.5 mantém `0`. Dado errado gravado em silêncio.

**Três divergências são artefatos conhecidos**, não defeitos: `lancamentoContabil` e `ordemPagamento` (construtor exige argumentos; o 5.6 morre e o 8.5 segue) e `classes/empenho.php → datausu` (`1969-12-31` contra a data de hoje — só acontece **sem sessão**, que é condição do harness, não de operação).

> **Não use o `harness_robusto.sh` aqui.** Ele avança contando *linhas de saída*, o que vale para o passo 6 (uma linha por classe) e não para este (muitas linhas por classe).

> **Com listas grandes, rode UMA classe por processo**, com o `scratchpad/porclasse.sh`: um fatal mata o processo e o resto
> da lista some — no `edu3` a lista inteira cobriu 120 de 404 classes, e os dois lados "concordavam".
>
> ```bash
> for c in ecidade_php56 ecidade_php85; do
>   docker cp scratchpad/porclasse.sh $c:/tmp/pc.sh; docker cp scratchpad/escrita.php $c:/tmp/esc.php
>   docker exec -i $c sh /tmp/pc.sh /tmp/esc.php < /tmp/cls.txt > /tmp/w_$c.txt 2>/dev/null
> done
> ```

### Passo 6c — a forma NEGADA `$this->x != ""`

**Por quê:** o `GuardaComparacaoLiteralRector` só trata `==`. A forma `!=`, com propriedade inteira e **sem `trim()`**,
está sobretudo no bloco de auditoria do `alterar()`:

```php
if (isset($GLOBALS["HTTP_POST_VARS"]["x"]) || $this->x != "")   // 5.6: 0 != "" falso; 8.5: verdadeiro
    insert into db_acount (...)                                  // o 8.5 grava uma alteração para 0
```

O padrão aparece milhares de vezes, mas só muda o resultado quando a propriedade ainda vale o inteiro `0` na comparação.
Por isso **meça antes de corrigir**:

```bash
python3 scratchpad/negada_alvos.py tmp/negada.tsv   # estatico: classe, campo, metodo, auditoria/negocio
cut -f1 ecidade/tmp/negada.tsv | sort -u > ecidade/tmp/negada_cls.txt
for v in 56 85; do
  docker cp scratchpad/negada.php ecidade_php$v:/tmp/negada.php
  # UM arquivo temporario POR RUNTIME: o /tmp e compartilhado entre os containers
  docker exec -i -e V=$v ecidade_php$v sh -c 'cd /var/www/html; while read c; do
      grep -F "$(printf "%s\t" "$c")" tmp/negada.tsv > /tmp/_neg_$V.tsv
      php -d display_errors=0 /tmp/negada.php /tmp/_neg_$V.tsv 2>/dev/null </dev/null; done' \
    < ecidade/tmp/negada_cls.txt > /tmp/neg_$v.txt
done
diff /tmp/neg_56.txt /tmp/neg_85.txt
```

Compare pela chave (classe, campo, método):
- **valor diferente** (5.6 `NULL`, 8.5 `0`): falta a guarda do `==` no `atualizacampos()` — a classe não foi portada. Se ela
  está no universo do lote, é falha do passo 4;
- **mesmo valor `0`, resultado diferente**: é a forma negada. Ponha os pares (classe, campo, método) num TSV e rode
  `python3 scratchpad/negada_corrige.py <tsv>`, que aplica `($this->x != "" && $this->x !== 0 && $this->x !== 0.0)` só
  naqueles pontos. Depois rode o `negada_alvos.py` de novo: os pontos corrigidos têm de sumir (o `negada.php` continua
  acusando, porque mede o estado, não o código).

Medido em 27/10/2026: 7.367 pares, 89 da forma negada, 74 em 28 classes servidas, todos de auditoria. Nos lotes 1 e 2
da Configuração: 2.068 e 2.426 pares, 0 divergências.

### Nível 3 — `POST` de verdade, comparando o SQL emitido

**Quando usar:** o passo 6b compara o **estado do objeto**; o nível 3 compara o **`INSERT` que cada runtime emite**. É a única prova ponta a ponta de que a gravação está idêntica.

Não rode em bateria — **é dirigido**. Umas 15 telas, espalhadas pelos módulos, bastam para sustentar a afirmação.

#### O problema que ele resolve

Os dois runtimes compartilham o banco. Se você mandar o mesmo `POST` para os dois, o primeiro muda o estado que o segundo veria. A saída é comparar o **SQL emitido**, com snapshot e restore entre os dois lados.

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
cd ecidade && grep -aoE "getDao\\(['\"][a-z0-9_]+|new cl_[a-z0-9_]+" <tela>.php | head -3
```

O nome que aparecer é a tabela. Confira que a classe existe: `ls classes/db_<tabela>_classe.php`.

#### Passo 3 — gerar o payload lendo o formulário

**Não invente os nomes dos campos.** Foi assim que eu errei duas vezes seguidas: usei `cm34_descr` quando o campo real era `cm34_descricao`, e `cm34_dtvalidade` quando era `cm34_datalimite`.

```bash
python3 scratchpad/payload_auto.py "$(cat /tmp/sid.txt)" <tela>.php
```

Ele lê o HTML que o 5.6 emite e monta a querystring com os nomes reais, o botão de submit certo e os campos escondidos `_dia`/`_mes`/`_ano`.

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
statements: 5.6=38  8.5=38
destes, INSERT/UPDATE/DELETE: 5.6=9  8.5=9
destes, escrita de NEGOCIO: 5.6=1  8.5=1
  5.6> insert into cemiterioisencao( ... ) values ( 11 ,'TESTE_N3' ,1 , ... )
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
docker exec -u root -i ecidade_php56 sh -c \
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

#### Teste apenas telas ROTEADAS

Erro de método meu: testei 5 telas que **não estão roteadas** para o 8.5. Duas divergiam por `parse_str` não portado — mas elas são servidas pelo 5.6, onde funcionam. Confira antes:

```bash
curl -sI "http://localhost:8090/<tela>.php" | grep -ai 'x-ecidade-runtime'
```

Só vale testar o que responde `PHP-8.5`.

## Passo 7 — a bateria byte-a-byte

**O que é:** pedir cada tela do módulo às duas portas, com a mesma sessão, e comparar as respostas byte a byte. **É este passo que acha o que nenhum outro vê** — catorze das vinte categorias do catálogo saíram daqui ou do `php -l`.

Só é possível porque o PHP 5.6 continua **vivo como referência**. Num *big-bang*, o "antes" deixa de existir no momento em que o Docker sobe de versão.

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
docker exec -u root -i ecidade_php56 sh -c \
  "cp /tmp/_d.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data /var/lib/php/sessions/sess_$SID" </dev/null
curl -s -o /dev/null -b "ECIDADEWINDOWMAIN=$SID" "http://localhost:8085/<tela>.php"; sleep 1
grep -a 'Uncaught\|E_ERROR' ecidade/extension/log/error.log | tail -1
```

Se o log não disser nada, compare o conteúdo:

```bash
for port in 8080 8085; do
  docker exec -u root -i ecidade_php56 sh -c \
    "cp /tmp/_d.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data /var/lib/php/sessions/sess_$SID" </dev/null
  curl -s -b "ECIDADEWINDOWMAIN=$SID" "http://localhost:$port/<tela>.php" > /tmp/o_$port.html
done
diff <(fold -w95 /tmp/o_8080.html) <(fold -w95 /tmp/o_8085.html) | head -12
```

### Tabela de decisão

| Sintoma | Conclusão | Ação |
| --- | --- | --- |
| `200` / `500` — quebra só no 8.5 | **regressão de migração** | corrigir aquele ponto |
| `500` / `200` — quebra só no 5.6 | defeito **pré-existente** da referência | registrar, **não corrigir** |
| `500` / `500` — quebra igual | defeito pré-existente ou dado ausente | **não mexer** |
| `200` / `200` com bytes diferentes | defeito **silencioso** — o mais perigoso | diagnosticar pelo `diff` |
| Não é tela (fragmento de include) | artefato do harness | caracterizar e seguir |

### Os dois ciclos automáticos de guarda `pg_*`

O caso mais comum de "quebra só no 8.5" é uma função `pg_*` recebendo `false` (a SQL falhou) ou pedindo uma coluna que o
resultado não tem. Dois scripts corrigem isso **na aparição, uma linha por vez**: requisitam a tela no 8.5, leem o fatal do
log, aplicam só naquela linha a guarda que reproduz o 5.6 (`($r ? pg_xxx($r…) : null)`; `null` é o que o 5.6 devolvia) e
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

### Arquivos que já não parseavam no 5.6

Ao portar uma biblioteca velha você vai achar arquivos quebrados **antes** da migração. Não tente consertar:

```bash
docker exec -i ecidade_php56 sh -c 'while IFS= read -r f; do
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

O gerador **reescreve o arquivo inteiro**: repita sempre **todos** os lotes já roteados, senão eles voltam para o 5.6 em
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
| tela de **outra** área, mesmo prefixo | `PHP-5.6` — **este é o teste que importa** |
| tela com inicial maiúscula | `PHP-8.5` — o `map` é insensível a caso |
| `login.php` | `PHP-5.6` |

> **O `map` do nginx É insensível a maiúsculas** — ao contrário do `location ~`, que precisou do `~*`. Emitir as duas grafias faz o nginx **recusar a configuração** com `conflicting parameter`. Prevenir-se da armadilha no lugar errado derruba o proxy.

### Passo E — a bateria cobre só o que foi roteado

Não rode a bateria no prefixo inteiro: as telas que ficaram no 5.6 **não foram portadas** e vão divergir por motivo legítimo.

```bash
ONLY=$(grep -i '^<pref>' /tmp/telas.txt | tr '\n' ',' | sed 's/,$//')
ONLY="$ONLY" python3 scratchpad/cmp.py "$(cat /tmp/sid.txt)" '^<pref>[0-9]*_' /tmp/<pref>_div.txt
```

> **Erro de método que eu cometi:** testei telas que não estavam roteadas e achei "defeitos" (`parse_str` não portado) em arquivos servidos pelo 5.6, onde funcionam. **Só teste o que responde `PHP-8.5`.**

### O que o `map` deixa de fora, e você precisa declarar

O banco só sabe classificar **telas do menu**, que são \~36% dos arquivos de um prefixo. Os outros 64% — popups, `.RPC.php`, subtelas — **continuam no 5.6**.

Isso é funcionalmente correto: eles **estão portados** (entram pelo universo das sete frentes, via `window.open`) e rodam nos dois runtimes. Mas significa que "o módulo roda em PHP 8.5" vale para **as telas dele**, não para todos os seus arquivos. Declare isso junto com o número.

## Passos 8 e 9 — rotear e registrar

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

**Saída esperada:** as telas do módulo com `PHP-8.5 (migrado)` e o `login.php` com `PHP-5.6 (referencia)`. Se o `/w/2/...` não migrar, o `(?:/w/[0-9]+)?` está faltando.

> O `nginx.conf` entra por bind mount de **arquivo único**. Editar no host cria um inode novo e o container continua com o antigo — por isso o `--force-recreate`, e por isso um `nginx -s reload` não resolve.

#### Prefixo que serve várias áreas

`con` aparece em 6 áreas do menu, `cai` em 4. Rotear por prefixo arrastaria módulos inteiros de outras áreas — o `con` levaria **511 telas** de Contabilidade, RH e Patrimonial junto. Nesses casos o roteamento é por **lista exata**, gerada do banco:

```bash
python3 scratchpad/gera_map_faseb.py <area>:<pref>,<pref> [<area>:<pref> ...]
docker compose -f docker-compose.proxy.yml up -d --force-recreate
```

> Curiosidade que já derrubou o proxy: `location ~` é sensível a maiúsculas e exigiu o `~*`; o `map` **não é**. Emitir as duas grafias faz o nginx recusar a configuração com `conflicting parameter`.

### Passo 8b — abas e redirecionamentos que voltam ao 5.6 (14ª lacuna)

**Por quê:** rotear a tela do menu **não basta**. Muitas telas são só um contêiner: ao abrir, carregam o formulário num
`<iframe>` (`cad1_face001` → `cad1_face004`) ou redirecionam (`db_redireciona(...)`). Esse destino **não está no menu**,
então o `map` (gerado do banco) não o conhece e ele fica no 5.6. A tela "está no 8.5" e o formulário que o usuário
preenche roda no 5.6. **Nenhuma bateria acusa isso**: as duas telas são idênticas, só que servidas pelo runtime errado.
Em 26/10/2026 eram 158 abas atrás de 90 telas de menu, nas três áreas concluídas até então.

No roteamento por **prefixo** a aba normalmente vai junto com o contêiner; mas rode a verificação sempre — o destino pode
ser de outro prefixo (`eso1_cadastroavaliacoes002` redireciona para `hab1_avaliacao002`).

```bash
# GET no 8.5 de cada tela de menu das areas listadas (e das abas ja roteadas: segundo salto)
python3 scratchpad/redirecionamentos.py "$(cat /tmp/sid.txt)" /tmp/redir.tsv TRIBUT,EDUCA,RECURSOS,PATRIM,FINANC,SA,CONFIG,<SUA_AREA>
grep -P '^NO_5\.6\t' /tmp/redir.tsv | grep -vP '\t(corpo|db_erros)\.php\t'     # TEM de sair vazio
```

Para cada linha `NO_5.6`:

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
desse prefixo como "no 5.6".

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

> O objetivo é **migrar**, não consertar. Quando o PHP 8 transforma em fatal algo que o 5.6 tolerava, a correção certa é a que **reproduz o comportamento do 5.6** — não a que conserta a intenção do autor.

**Critério prático:** se a alteração mudaria a saída do `:8080`, não é migração — é conserto, e fica de fora.

**Como descobrir o que o 5.6 fazia** — pergunte a ele, não à documentação:

```bash
docker exec ecidade_php56 php -r 'var_dump(<a expressao>);'
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
| `pg_result(): ... false given` | idem, mas devolve **`NULL`** no 5.6 | `($r ? pg_result($r,0,0) : null)` |
| Campo some da tela, sem erro | `is_resource()` sobre resultado | `is_resource($r) \|\| is_object($r)` |
| `<select>` vem vazio, sem erro | `gettype($x) == "resource"` | `... \|\| is_object($x)` |
| Widget inteiro some | `$x < 3` com `$x` string | `(float)$x < 3` |
| `Unsupported operand types: string / int` | aritmética com string | `(float)` ou `(int)`, o que o 5.6 produzia |
| `'break' not in the 'loop' or 'switch'` | `break` fora de laço | `exit;` se alcançável, remover se não |
| `Unparenthesized a ? b : c ? d : e` | ternário aninhado | `(a ? b : c) ? d : e` — 5.6 associa à **esquerda** |
| `in_array(): Argument #2 must be of type array` | *haystack* nulo | `is_array($h) && in_array(...)` |
| `sizeof(): must be of type Countable\|array` | `sizeof(null)` | `sizeof((array)$x)` |
| `array_merge(): Argument #2 must be of type array` | argumento nulo | ternario com `is_array()` nos dois |
| `DivisionByZeroError` | divisão por zero | `($d ? $n/$d : 0)` — o 5.6 dava `false` |
| `Undefined constant "l"` | constante indefinida | `"l"` — o 5.6 usava o próprio nome |
| `ArgumentCountError: Too few arguments` | argumento faltando | passar o valor que o 5.6 produzia |
| Data gravada = **hoje** em vez da época | `date($fmt, null)` | `date($fmt, (int)$x)` |
| Layout do PDF deslocado | `"J" > 0` no FPDF | `(float)$ln > 0` — **não** corrigir a chamada |
| `Call to undefined function each()` | `each()` removido no PHP 8 | **à mão**, nunca `foreach` (ver abaixo) |
| `count(): Argument #1 must be of type Countable\|array` | `count(null)`/`count("")` — o 5.6 dava 0 ou 1 | `count((array)$x)` |
| `Call to undefined function get_magic_quotes_gpc()` | removida no PHP 8; no 5.6 do projeto valia `false` | trocar a chamada por `false` |
| `fputs(): Argument #1 ($stream) must be of type resource, bool given` | `fopen` falhou (`tmp/` sem permissão, caminho errado) | `$fd && fputs($fd, ...)` — o 5.6 só avisava |
| `pg_lo_export(): Argument #1 ... PgSql\Connection` | ordem legada `($oid, $arq, $conn)`, que o 5.6 aceitava | `pg_lo_export($conn, $oid, $arq)` — funciona nos dois |
| `Attempt to assign property "x" on null` | o 5.6 criava o objeto sozinho (*auto-vivificação*) | `if (empty($o)) $o = new stdClass();` antes da linha |
| `Non-static method X::m() cannot be called statically` | chamada estática a método sem `$this` | declarar o método `static` (conferir que ele não usa `$this`) |
| `Declaration of Filha::m() must be compatible with Mae::m()` | LSP — em geral depois do `OptionalParametersAfterRequiredRector` | espelhar a assinatura da mãe na filha |

**O `each()` à mão.** O e-cidade tem laços que dependem do ponteiro interno **já exaurido** por um laço anterior e que,
por isso, nunca executam no 5.6. `foreach` faria esses laços rodarem. A forma fiel, que anda no mesmo ponteiro:

```php
// antes:  while (list($k, $v) = each($a)) {
while (is_array($a) && (($k = key($a)) !== null) && ((($v = current($a)) || true) && (next($a) || true))) {
```

Se houver `reset($a)` logo antes do laço, `foreach` é fiel — mas a forma acima também é, e não exige julgar o contexto.

### Dois casos que ensinam o princípio

**O `"J"` do FPDF.** Passar `"J"` como número de linha é defeito de quem chamou. Mas corrigir a chamada **mudaria o layout do relatório no 5.6**. Então o defeito fica, e o contorno vai dentro do FPDF.

**O `1969-12-31`.** `date("Y-m-d", "2024-01-01")` devolve `1969-12-31` no 5.6 — resultado sem sentido. A correção `(int)$dt` **preserva o resultado sem sentido**, porque mudá-lo seria conserto.

### Como aplicar uma correção num arquivo

A tabela acima diz **qual** é a correção. Esta parte diz **como** aplicá-la sem quebrar nada.

#### A regra que não pode ser violada: edite em BYTES

**64% dos arquivos são LATIN-1**, não UTF-8. Abrir como texto e salvar corrompe toda a acentuação — e o `git diff` mostra o arquivo inteiro como alterado. Sempre `"rb"` e `"wb"`.

```bash
cd ecidade && python3 - <<'PY'
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
```

#### Exemplo real: a guarda `pg_*`

Este é o caso mais comum — apareceu em 111 pontos ao longo do projeto. Repare que ele **conta antes, confere o risco, e só então escreve**:

```bash
cd ecidade && python3 - <<'PY'
import re
arq = "cai1_lista001.php"
b = open(arq, "rb").read()

RX = re.compile(rb'(?<!\? )\b(pg_num_rows|pg_numrows)\s*\(\s*(\$\w+)\s*\)')

# ANTES de escrever: o resultado e comparado com === em algum lugar?
# Se for, a guarda MUDA o comportamento -- o 5.6 dava false, a guarda da 0.
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
```

> **O `(?<!\? )` no início do regex evita guardar o que já está guardado.** Sem ele, rodar duas vezes produz `($r ? ($r ? pg_numrows($r) : 0) : 0)`.

#### Depois de aplicar — sempre, nesta ordem

```bash
# 1. o arquivo ainda parseia nos DOIS runtimes?
for c in ecidade_php56 ecidade_php85; do
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
cd ecidade && python3 -c "
import sys
for f in sys.argv[1:]:
    b = open(f,'rb').read()
    open(f,'wb').write(b.replace(b'texto novo', b'texto velho'))
    print(f)" arquivo1.php arquivo2.php
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

Em `con2_razaodespesa002.php:170` há `if ($rows === 0)`. Com a guarda devolvendo `0`, a condição passa a ser verdadeira onde no 5.6 era falsa.

> **Eu violei este princípio uma vez e o preço apareceu em um minuto.** Apliquei aspas em 25 constantes indefinidas e **quebrei 7 arquivos, inclusive `libs/db_stdlib.php` do núcleo**. As 25 não eram PHP — eram colunas de banco dentro de strings SQL. Um regex que lê bytes **não distingue código de string**.

### Ao corrigir arquivo do núcleo: há uma cópia que executa

Todo `include` passa por `modification()`, que devolve uma cópia personalizada se ela existir:

```bash
find ecidade/extension/modification -name '<arquivo>'
docker exec -u root ecidade_php56 chmod 666 /var/www/html/<caminho da copia>
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
PHP 5.6:    true           true           true
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

**Runtime** — a versão do PHP rodando. Aqui são dois ao mesmo tempo: `:8080` é o 5.6 (referência) e `:8085` é o 8.5 (migrado). O `:8090` é o proxy que decide qual atende cada tela.

**Universo** — todos os arquivos que um módulo alcança, não só os que têm o prefixo dele.

**Guarda** — um trecho acrescentado para fazer o PHP 8 se comportar como o 5.6. Não conserta o código: **preserva** o comportamento antigo.

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
| `scratchpad/ns_fecho.py` | 9ª frente da enumeração (classes com namespace); chamado pelo `enumera.py` |
| `scratchpad/carrega_arquivo.php` | passo 5b: carregar cada arquivo (LSP) |
| `scratchpad/porclasse.sh` | passos 6/6b: uma classe por processo |
| `scratchpad/negada_alvos.py`, `negada.php`, `negada_corrige.py` | passo 6c: forma negada |
| `scratchpad/guarda_ciclo.py`, `campo_ciclo.py` | passo 7: guardas `pg_*` na aparição |
| `scratchpad/redirecionamentos.py` | passo 8b: abas e redirecionamentos que voltam ao 5.6 |
| `docker/proxy/faseb_map_abas.txt` | passo 8b: abas e destinos roteados por lista |

**Quando este documento e o registro (`CLAUDE.md` + `docs/registro/`) divergirem, o registro manda** — é ele que é atualizado a cada lote. Se encontrar uma divergência, corrija este guia **e** a skill `migrar-modulo`.
