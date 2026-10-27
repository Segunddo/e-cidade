---
name: migrar-modulo
description: Porta um módulo legado do e-cidade de PHP 5.6 para 8.5 mantendo compatibilidade com os dois runtimes. Use ao migrar um prefixo de módulo (jur, div, arr, fis, iss, mar, tri, dvr, inf, not...), ao retomar um porte interrompido, ou ao diagnosticar uma tela que quebra no 8.5 e não no 5.6. Cobre a receita de 9 passos, o ferramental versionado em scratchpad/ e as armadilhas que já custaram defeito.
---

# Migrar um módulo para PHP 8.5

O contexto, os números e o **porquê** de cada decisão estão no `CLAUDE.md` da raiz e em `docs/registro/`
(índice no fim do `CLAUDE.md`). Este arquivo é só o **procedimento**. Quando os dois divergirem,
o registro manda.

**Critério de sucesso do módulo:** todas as telas do prefixo respondem byte-a-byte idêntico
entre `:8080` (5.6) e `:8085` (8.5), com sessão autenticada — e cada divergência restante está
*caracterizada*, não apenas tolerada.

## Antes de começar

O ambiente precisa estar no ar (ver *Como subir o ambiente* no `CLAUDE.md`). Confira:

```bash
docker ps --filter name=ecidade --format '{{.Names}}\t{{.Status}}'   # 4 containers
stat -c '%n %A' ecidade/tmp ecidade/arquivos                         # ambos 777
stat -c '%n %A' ecidade/extension/log/*.log                          # os ARQUIVOS 666
```

**O Rector precisa ser instalado** — ele vive em `ecidade/tmp/rector/`, que é gitignored, então
não sobrevive a um clone novo. A config e as regras **são** versionadas (`scratchpad/`):

```bash
docker exec -i ecidade_php85 sh -c '
  mkdir -p /var/www/html/tmp/rector && cd /var/www/html/tmp/rector
  [ -f composer.json ] || composer init --no-interaction --name=ecidade/rector-exp >/dev/null 2>&1
  composer require --no-interaction --quiet rector/rector:^2.0
  ./vendor/bin/rector --version' </dev/null
```

**Prova de fumaça antes de culpar o porte:** requisite uma tela de módulo já verificado
(`cem1_campas001.php`) com a sessão. Se ela der 500, o problema é de ambiente. O caso mais comum
é `extension/log/*.log` pertencer ao host em 664 — o Logger lança fatal antes de qualquer saída
e **toda** tela autenticada devolve 500 com corpo vazio, nos dois runtimes, enquanto o
`login.php` segue respondendo 200.

**O projeto vive em `ecidade/`.** O compose monta `./ecidade` em `/var/www/html`, então os
caminhos DENTRO do container não mudam. Os scripts do `scratchpad/` já fazem `chdir` para lá —
rode-os sempre da raiz do repositório, nunca de dentro de `ecidade/`.

Sem `tmp/` gravável, 11% das telas falham **antes de executar** e passam na bateria por
falharem igual nos dois. Comparabilidade sem cobertura.

**Nunca alterar `docker-compose.yml`** — é a referência funcional.
**Nunca commitar** `docker/database/ecidade_base.sql` (314 MB) nem encenar a remoção do `.gz`.

## Passo 1-3 — Enumerar, inventariar, classificar

```bash
python3 scratchpad/enumera.py <prefixo>      # gera tmp/<pref>_universo.txt e _alvos.txt
ls | grep -icE '^<prefixo>[0-9]*_.*\.php$'   # DEVE bater com "telas" do enumerador
```

O enumerador cobre **nove frentes** (prefixo, includes transitivos, nomes citados em
strings que o JavaScript abre, autoload — `new cl_*` **e** `db_utils::getDao('x')` —,
bibliotecas vendorizadas, pasta inteira da lib, classes de `model/`/`std/` por nome curto, e
**classes com namespace**: `use ECidade\…;`, `new \ECidade\…` e os serviços que o `bootstrap.php`
registra por chave de texto, resolvidos em `src/`/`app/`/`api/` por `scratchpad/ns_fecho.py`).
Cada uma nasceu de uma lacuna que deixou arquivo sem porte. A 9ª (15ª lacuna) faz o universo
crescer bastante, porque o fecho segue de `src/` até `classes/`: no lote 1 de Patrimonial ele foi
de 1.727 para 2.801 arquivos.

Arquivos de `src/`/`app/` têm duas armadilhas próprias, as duas medidas:
- **o `php -l` não basta**: a classe filha pode não *carregar* no 8.5 por assinatura incompatível
  com a mãe em outro arquivo (LSP). Rode `scratchpad/carrega_arquivo.php` nos dois runtimes sobre os
  que têm `extends`/`implements`, e compare só o que dá OK no 5.6 e falha no 8.5;
- **método homônimo em classe com namespace não é construtor**, nem no 5.6 (PHP 5.3.3). Não renomeie.

Para medir uma lacuna nova retroativamente: `TELAS=@arquivo` aceita a lista de partida (ex.: tudo o
que o 8.5 serve), e `SEM_NS=1` desliga a 9ª frente. Compare os alvos com e sem, e passe o
`conta_tokens.php` só na diferença. O detector por bytes casa com a própria guarda.

**Variantes de prefixo matam o porte em silêncio.** Já aconteceu três vezes:

```bash
ls | grep -ioE '^<prefixo>[a-z]*[0-9]*_' | sort -u    # itbi? agua? jur01_? jur_?
```

**O detector de `0 == ""` casa com a PRÓPRIA guarda** — a correção termina em
`|| $this->X == ""`, então essa categoria **nunca reporta zero**. Para conferir remanescentes,
contar só as ocorrências cujos 120 bytes anteriores NÃO trazem
`$this->X === 0 || $this->X === 0.0 || `. Ocorrência precedida de `== null ||` no mesmo `if` é
segura: `0 == null` é `true` nos dois runtimes.

**Se precisar reenumerar no meio do porte** (uma lacuna nova apareceu), o `porta.py` **não é
idempotente** — ele reaplicaria guarda sobre guarda nos arquivos do primeiro lote, que ainda não
estão commitados e portanto não contam como "já pagos". Rodar só sobre os novos:

```bash
git status --porcelain | awk '{print $NF}' | sed 's#^ecidade/##' | sort -u > /tmp/ja.txt
sort -u ecidade/tmp/<pref>_alvos.txt > /tmp/all.txt
comm -23 /tmp/all.txt /tmp/ja.txt > /tmp/novos.txt     # substituir _alvos.txt por este
```

**Renomear construtor exige varrer TRÊS formas de chamada ao nome antigo** — `parent::Classe(`,
`$this->Classe(` e a estática `Classe::Classe(`. O `porta.py` faz as três, mas só para classes
do **mesmo arquivo**: uma chamada cruzada (`MyPdf.class` chamando `FPDF::FPDF()`) escapa. Depois
de portar uma biblioteca, conferir na base inteira, restringindo aos nomes que viraram
`__construct` e pulando comentário e string:

```bash
git grep -nE '([A-Za-z_][A-Za-z0-9_]*)::\1\(' -- ecidade/
```

Classes de extensão externa (`GtkFrame::GtkFrame()`) **não** entram: ninguém as renomeou.

**A checagem de `__construct` é por CLASSE, nunca pelo arquivo.** Um arquivo com várias classes
em que só uma tem `__construct` mascarava as outras — foi assim que 42 classes do núcleo
passaram por oito portes sem serem renomeadas (8ª lacuna).

**Classificar os `split()` antes de converter.** Separador literal vira `explode`; separador
com metacaractere de regex (`+ * ? [ ] ( ) | . ^ $ \`) vira `preg_split`. Converter um regex
para `explode` devolve a string inteira sem separar — **dado errado, sem erro nenhum**:

```
split(" +", "um   dois")   -> ["um","dois"]      explode(" +", ...) -> ["um   dois"]
```

Se o inventário trouxer categoria que não está no catálogo (`docs/registro/`), **pare e investigue** antes de
transformar. Toda categoria nova até hoje veio daí.

## Passo 4 — Aplicar (Rector, desde o `iss`)

O instrumento **mudou**: o `porta.py` foi substituído pelo Rector com lista curada mais duas
regras próprias. Ele cobre 100% das categorias e erra menos que o regex (não toca comentário,
acerta a precedência). O `porta.py` fica como referência e para comparar resultados.

```bash
# o scratchpad/ nao esta no bind mount: copiar config e regras para dentro
docker exec ecidade_php85 mkdir -p /var/www/html/tmp/rector/scratch/rector-rules
docker cp scratchpad/rector-curado.php      ecidade_php85:/var/www/html/tmp/rector/scratch/
docker cp scratchpad/rector-rules/.         ecidade_php85:/var/www/html/tmp/rector/scratch/rector-rules/

# REPETIR ate dizer "0 files changed" -- ele NAO converge numa passada, e isso e intermitente
docker exec -i ecidade_php85 sh -c 'cd /var/www/html;
  ALVOS=/var/www/html/tmp/<pref>_alvos.txt tmp/rector/vendor/bin/rector process \
    --config tmp/rector/scratch/rector-curado.php --no-progress-bar' </dev/null
```

**Quatro armadilhas, todas medidas e todas silenciosas:**

1. **O pin de versão é obrigatório.** Sem `->withPhpVersion(PhpVersion::PHP_80)`, o Rector lê a
   versão alvo do `composer.json` do projeto (`">=5.6.4"`) e **pula toda regra com version
   bonding** — inclusive `Php4ConstructorRector` e `EregToPregMatchRector` — reportando `[OK]`
   sem aviso. Conferir sempre: `Php4ConstructorRector` **tem** de aparecer na lista de regras
   aplicadas se o módulo tiver construtor PHP 4.
2. **Rodar até dar zero.** Uma passada deixou 85 `parse_str` por converter; a segunda, com o
   comando idêntico, converteu 83. Um run não prova que acabou.
3. **A denylist não é transferível entre módulos.** Já cresceu três vezes: 14 → 16 (`iss`) →
   22 (modernização) → 23 (`dvr`, `IfIssetToCoalescingRector`, que emite `??` e é parse error
   no 5.6). **Antes de aplicar, rode um `--dry-run --output-format=json` e confira a lista de
   regras aplicadas**; para cada regra que você ainda não vetou, teste a construção que ela
   emite nos DOIS runtimes antes de aceitar. E confira `php -l` na própria config: com erro de
   sintaxe nela, o Rector reporta `0 arquivos` sem mensagem de erro. Regras que nunca dispararam antes podem
   disparar agora e emitir função que não existe no 5.6. Daí o passo 4b, abaixo, ser obrigatório.
4. **O Rector traz modernização junto** (~77% do diff no `iss`): alias `pg_*`, `var` → `public`.
   Inofensiva nos dois runtimes, mas infla a revisão. Se incomodar, entra na denylist.

### Passo 4b — portão de FUNÇÕES contra o 5.6 (nenhum `php -l` faz isto)

```bash
python3 - <<'EOF'
import subprocess, re
d=subprocess.run(["git","diff","-U0","--","ecidade/"],capture_output=True).stdout
nov=set(); vel=set()
for l in d.split(b"\n"):
    if l.startswith((b"+++",b"---")): continue
    alvo = nov if l.startswith(b"+") else (vel if l.startswith(b"-") else None)
    if alvo is not None:
        # o (?<!function ) exclui DECLARACOES: sem ele o portao acusa "__construct"
        # como funcao ausente no 5.6, que e falso positivo
        alvo |= {m.group(1) for m in re.finditer(rb'(?<![\$>:\w])(?<!function )([a-z_][a-z0-9_]{2,})\s*\(', l)}
open("/tmp/fn.txt","w").write("\n".join(sorted(x.decode() for x in nov-vel)))
EOF
docker cp /tmp/fn.txt ecidade_php56:/tmp/fn.txt
docker exec -i ecidade_php56 php -r '
$f=array_filter(array_map("trim", file("/tmp/fn.txt", FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES)));
$falta=array(); foreach($f as $x) if(!function_exists($x)) $falta[]=$x;
echo count($falta)," ausentes: ",implode(", ",$falta),"\n";' </dev/null
```

Já pegou `str_contains()` e `array_key_first()` emitidos em arquivos servidos pelo 5.6.

### Escrever uma regra própria? Dois defeitos esperam por você

- **Laço infinito**: se a regra devolve um nó que **contém** o original, o PhpParser percorre os
  filhos do substituto e o reencontra. O substituto não passa por `enterNode`, então
  `DONT_TRAVERSE_CHILDREN` nunca é alcançado. O processo morre com `Killed`, sem traceback.
  Marque o nó: `$n->setAttribute('ja_tratado', true)`.
- **Perda de comentários**: nó novo nasce sem atributos, e os comentários ficam presos ao antigo.
  Reaproveite o nó original (`$node->expr = $novo;`) em vez de criar outro.

As categorias que exigem decisão caso a caso continuam tratadas à mão, verificando o
comportamento do 5.6 antes:

```bash
docker exec ecidade_php56 php -r '<expressão>'    # a referência é o 5.6, não a documentação
```

Para `each()`: se houver `reset()` antes do laço, `foreach` é fiel; **sem** `reset()`, o
ponteiro interno é compartilhado entre laços e `foreach` muda o comportamento — use
`key()`/`current()`/`next()`.

### Verificar zero remanescentes — com consciência da guarda

A forma corrigida `($this->X === 0 || $this->X === 0.0 || $this->X == "")` **contém**
`$this->X == ""`. Um verificador ingênuo acusa tudo de novo. A checagem precisa olhar para
trás e confirmar que a guarda precede a comparação.

## Passo 5 — `php -l` nos dois runtimes

```bash
git status --porcelain | awk '{print $NF}' | grep '\.php$' | sed 's|^|/var/www/html/|' > /tmp/alt.txt
for v in 56 85; do
  docker exec -i ecidade_php$v bash -c \
    'while read f; do php -l "$f" </dev/null 2>&1 | grep -q "No syntax errors" || echo "$f"; done' \
    < /tmp/alt.txt
done
```

**O `</dev/null` e o `docker exec -i` não são opcionais.** Sem eles o `php` herda o stdin do
laço, consome a lista, o laço dá uma volta só e o resultado é um tranquilizador "0 erros" —
foi assim que 11 arquivos quebrados de `dbagata/` passaram despercebidos.

### Se usar Rector: conferir FUNÇÕES, não só sintaxe

`php -l` não pega função que não existe no runtime. O Rector pode emitir `str_starts_with`
(PHP 8) e `random_int` (PHP 7), que compilam no 5.6 e explodem em execução — foram 93 arquivos
num teste real, todos com lint limpo. Perguntar ao próprio 5.6:

```bash
# coletar as funcoes que aparecem SO na saida transformada, depois:
docker exec ecidade_php56 php -r 'foreach(file("/var/www/html/tmp/fn.txt",2) as $f)
  if(!function_exists(trim($f))) echo trim($f),"\n";'
```

Rodar também no **universo inteiro**, não só nos alterados: pega erro pré-existente e as
categorias que nenhuma varredura textual encontra (LSP, `=& new`, `break` fora de laço,
ternário aninhado, cast `(real)`).

## Passo 6 — Instanciar as classes

```bash
# o scratchpad/ fica FORA do bind mount (que monta so ecidade/): copiar o harness.
# Com o caminho /var/www/html/scratchpad/ o php nao acha o arquivo, a saida sai
# VAZIA nos dois runtimes e o diff vazio parece aprovacao.
grep '^classes/' tmp/<pref>_universo.txt > tmp/<pref>_classlist.txt
for v in 56 85; do
  docker cp scratchpad/instancia_classes.php ecidade_php$v:/tmp/ic.php
  docker exec ecidade_php$v php -d display_errors=0 \
    /tmp/ic.php /var/www/html/tmp/<pref>_classlist.txt \
    2>/dev/null | sort > /tmp/cls$v.txt
done
diff /tmp/cls56.txt /tmp/cls85.txt
```

Valida diretamente a renomeação dos construtores, que é a alteração de maior risco: no PHP 8
um construtor estilo PHP 4 **nunca executa**, sem erro nem aviso.

**Um diff vazio de dois arquivos vazios não é aprovação.** Confirme que houve saída antes de
declarar equivalência.

## Passo 6b — Exercitar o CAMINHO DE ESCRITA

A bateria do passo 7 faz só `GET`, e o idioma `$this->X == <literal> ? POST : $this->X` só
dispara no `POST`. Sem este passo, a maior categoria de correções do porte fica sem verificação.

```bash
grep '^classes/' tmp/<pref>_universo.txt > tmp/<pref>_classlist.txt
for v in 56 85; do
  docker cp scratchpad/escrita.php ecidade_php$v:/tmp/esc.php
  docker exec ecidade_php$v php -d display_errors=0 \
    /tmp/esc.php /var/www/html/tmp/<pref>_classlist.txt \
    2>/dev/null | sort > /tmp/esc$v.txt
done
diff /tmp/esc56.txt /tmp/esc85.txt      # qualquer linha e defeito
```

**Com listas grandes, rodar UMA classe por processo** (`while read c; do echo "$c" > /tmp/um.txt;
php /tmp/esc.php /tmp/um.txt; done`): um fatal mata o processo e o resto da lista some — no
`edu3` a lista inteira cobriu 120 de 404 classes. Conferir quantas classes aparecem na saída.

**Depois de editar um arquivo, esperar 3 s antes de requisitá-lo no 8.5** — o opcache revalida
a cada 2 s e executa o código antigo (um ciclo automatizado aplicou a mesma guarda 15 vezes).

Ele popula `HTTP_POST_VARS`, chama `atualizacampos()` e compara o estado — sem HTTP e sem
tocar no banco. Divergência significa que o 5.6 lê o valor do formulário e o 8.5 mantém `0`:
**dado errado gravado em silêncio**.

Atenção ao literal: além de `== ""` existe `== "f"` e `== " "`. Qualquer literal
**não-numérico** tem o mesmo defeito, porque o 5.6 o coagia para 0.

### Nível 3: POST real (dirigido, não em bateria)

Quando o passo 6b apontar uma classe com campo inteiro não-chave, vale confirmar com um `POST`
de verdade, que compara o **SQL emitido** pelos dois runtimes:

```bash
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade SET log_statement='all';"
python3 scratchpad/escrita_post.py <SID> <tela.php> <tabelas,virgula> '<payload>'
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade RESET log_statement;"
```

Ele faz snapshot das tabelas **e das sequências**, roda nos dois lados restaurando entre eles,
e separa escrita de negócio da de auditoria. Se a FK barrar o `DELETE` do restore, acrescente
a tabela filha ao conjunto (ordem: filho→pai) — nunca force `TRUNCATE CASCADE`.

Montar o payload é a parte cara: o botão se chama `incluir`/`alterar`/`excluir` (não
`db_opcao`), e há campos obrigatórios que não aparecem no form.

## Passo 7 — Comparar as telas

```bash
# achar uma sessao autenticada
docker exec -u root ecidade_php56 sh -c 'grep -la DB_modulo /var/lib/php/sessions/sess_* | head -3'
python3 scratchpad/cmp.py <SID> '^<prefixo>[0-9]*_' /tmp/<pref>_div.txt
ONLY="a.php,b.php" python3 scratchpad/cmp.py <SID> '^x_' /dev/null    # subconjunto
```

O comparador restaura a sessão antes de **cada** requisição (uma requisição a consome),
normaliza os identificadores aleatórios e **confirma a divergência refazendo o par** antes de
acusar — relatório em PDF carrega horário dentro do fluxo comprimido, fora do alcance de
qualquer regex, e gera falso positivo intermitente.

### Antes de diagnosticar: o log do PostgreSQL lista TODAS as falhas de uma vez

A maioria das divergências "quebra só no 8.5" é `pg_*` sobre resultado `false`. E `pg_query()`
só devolve `false` quando **a SQL falha** — não quando a tabela está vazia. Logo o PostgreSQL
já registrou todas, e uma passada da bateria basta:

```bash
# ANTES de rodar a bateria, anote o horario; DEPOIS:
docker logs --since 20m ecidade_database 2>&1 | grep -aA1 'ERRO:'
```

**O log está em PORTUGUES** (`ERRO:` / `INSTRUÇÃO:`) por causa do locale `pt_BR.ISO-8859-1`.
`grep 'ERROR:'` não acha nada e falha em silêncio. Nada precisa ser configurado:
`log_min_error_statement` já é `error` e os erros saem no stderr do container.

Cada par `ERRO:` + `INSTRUÇÃO:` aponta uma consulta quebrada — e o ponto de chamada que precisa
de guarda. Isso troca N rodadas de bateria por 1 (o `iss` precisou de 4).

**Não varra `pg_*` em massa.** Medido: 1.083 chamadas sem guarda no universo do `arr`, e só 1
precisava. E há 25 pontos na base onde o resultado é comparado com `===` — a guarda devolve `0`
onde o 5.6 devolvia `false`, e `false === 0` é falso. A varredura introduziria regressão em 25
pontos para prevenir cerca de um por módulo.

### Diagnosticar cada divergência

```bash
: > extension/log/error.log
# requisitar a tela no :8085, depois:
grep -a 'E_ERROR\|Uncaught' extension/log/error.log | sed 's/\[20[^]]*\] //' | sort -u
```

| Resultado | Conclusão |
|---|---|
| Falha **igual** nos dois | defeito pré-existente ou dado ausente — **não mexer** |
| Falha **só no `:8085`** | regressão — corrigir aquele ponto |
| Quebra **no `:8080`** e funciona no 8.5 | defeito da referência — registrar, não corrigir |
| Não é tela (fragmento de include) | artefato do harness — caracterizar e seguir |

**Corrigir na aparição, não em massa.** Decisão registrada do projeto: a varredura preventiva
das ~140 chamadas `pg_*` foi descartada de propósito. Cada correção nasce de um defeito
observado.

**Ao corrigir arquivo do núcleo, replicar em `extension/modification`** — é a cópia que de
fato executa para o usuário logado:

```bash
find extension/modification -name '<arquivo>'     # existe copia?
docker exec -u root ecidade_php56 chmod 666 /var/www/html/<caminho da copia>
```

Depois de alterar núcleo, **refazer as baterias dos módulos já portados**, não só a do atual.

## Passo 8 — Roteamento

Acrescentar o prefixo à alternância em `docker/proxy/nginx.conf`:

```nginx
location ~* ^(?:/w/[0-9]+)?/(?:cem|itbi?|agua?|jur|div|<novo>|tra)[0-9]*_ {
```

Três detalhes, cada um já causou roteamento silenciosamente errado:
- **`~*`**, não `~` — existem arquivos com prefixo capitalizado (`Cem1_`, `Con1_`, `Cai1_`).
- **`[0-9]*`**, não `[0-9]?` — existe `jur01_`, com dois dígitos.
- **`(?:/w/[0-9]+)?`** — na navegação real o desktop prefixa tudo com o id da janela.

```bash
docker compose -f docker-compose.proxy.yml up -d --force-recreate   # reload nao basta
for u in login.php <pref>1_x.php w/2/<pref>2_y.php; do
  curl -s -D - -o /dev/null "http://localhost:8090/$u" | grep -i x-ecidade-runtime
done
```

### Passo 8b — abas e redirecionamentos que voltam ao 5.6 (14ª lacuna)

Rotear a tela do menu **não basta**. Muitas telas são só um contêiner: ao abrir, carregam o
formulário num `<iframe>` (`cad1_face001` → `cad1_face004`) ou redirecionam
(`db_redireciona(...)`). Esse destino **não está no menu**. Por isso o `map`, gerado do banco,
não o conhece, e ele fica no 5.6. A tela "está no 8.5" e o formulário que o usuário preenche
roda no 5.6. Nenhuma bateria acusa isso: as duas telas são idênticas, só que servidas pelo
runtime errado. Em 26/10/2026 eram **158 abas** atrás de 90 telas de menu e **3 destinos de
redirecionamento** atrás de 5 telas de menu, nas três áreas concluídas. Os dois são a mesma lacuna e
se corrigem do mesmo jeito.

O problema só aparece no roteamento por **lista** (`map`). No roteamento por **prefixo**
(`location`) a aba vai junto com o contêiner. Mas rode a verificação sempre: o destino pode ser de
outro prefixo.

```bash
# GET no 8.5 de cada tela de menu da area (e das abas ja roteadas: segundo salto),
# classificando cada iframe/redirecionamento pelo mesmo criterio do nginx
python3 scratchpad/redirecionamentos.py <SID> /tmp/redir.tsv TRIBUT,EDUCA,RECURSOS,<NOVA_AREA>
# grep e nao awk de proposito: o carregador da skill troca cifrao+numero pelos argumentos
grep -P '^NO_5\.6\t' /tmp/redir.tsv | grep -vP '\t(corpo|db_erros)\.php\t'   # TEM de sair vazio
```

Para cada linha `NO_5.6`:

1. **iframe** → portar o universo dos destinos. Use `TELAS=<destinos com a grafia do disco>`
   no `enumera.py` e siga os passos 4 a 7, com bateria nos destinos. Depois acrescente o nome,
   em minúscula, a `docker/proxy/faseb_map_abas.txt` e regenere o `map` com o mesmo comando do
   cabeçalho de `faseb_map.conf`. O gerador lê a lista.
2. **redireciona** → mesma receita do iframe, com dois cuidados:
   - **o destino costuma ser um contêiner de abas.** `eso1_cadastroavaliacoes002` redireciona
     para `hab1_avaliacao002`, que abre as abas `hab1_avaliacao005`, `…grupopergunta001` etc. O
     `enumera.py` não segue essas abas a partir do destino. Ponha no `TELAS=` a **família
     inteira** (`ls | grep -i '^hab1_avaliacao'`) e os arquivos que as abas citam;
   - **o redirecionamento costuma ser condicional.** `cai4_lista001` só redireciona quando a
     prefeitura não usa o sistema de água; `pro1_obras00x` só redireciona sem o parâmetro `abas`.
     A bateria compara os dois ramos: a tela de menu (que redireciona por GET sem parâmetros) e
     o destino.

   Ponha na lista só o destino direto. Depois de rotear, **rode o levantamento de novo**: ele
   abre as telas já roteadas e acusa o segundo salto (as abas do contêiner), se ficou algum.
3. **`corpo.php`** é o "voltar ao início" depois de erro ou de configuração ausente
   (`numpref` não configurado, rotina desativada), e **`db_erros.php?db_erro=…`** é a página
   genérica de mensagem de erro (dois `lic1_*` caem nela por configuração ausente na base). Não
   são formulário nem lacuna.
4. **pasta** (`dbforms/…`) e **inexistente** não são lacuna. O proxy não roteia por pasta, e o
   `/tmp` compartilhado resolve. Ignore.

Os destinos são, em geral, compartilhados: `func_selinstit.php` e `verifica.php` são abertos
também por telas do 5.6, que passam a recebê-los do 8.5. É seguro porque o código portado roda
nos dois runtimes, e é por isso que o porte e a bateria vêm **antes** de acrescentá-los à lista.

**Limite:** o script só vê o que a tela faz **ao abrir, por GET sem parâmetros**. Abas criadas
por JavaScript ao clicar e redirecionamentos que dependem de dado ficam de fora. O resultado é
uma cota inferior. Na navegação manual, confira o `X-Ecidade-Runtime` dos iframes nas
ferramentas do navegador.

## Passo 9 — Commit

Um commit por módulo, revertível. A mensagem registra a tabela de correções com quantidades,
o resultado da bateria, e **cada categoria ou lacuna nova** encontrada. Antes:

```bash
git add -A -- ':!docker/database/ecidade_base.sql' ':!docker/database/ecidade_base.sql.gz'
```

Atualizar o registro: seção do módulo no `docs/registro/area-<área>.md`, cabeçalho de estado do
`CLAUDE.md` (módulos portados, rota, próximo módulo) e qualquer categoria nova.

## Limites que precisam ser declarados junto com o número

- **A bateria faz só `GET`.** Caminhos de escrita — incluir, alterar, excluir — não são
  exercitados. "148/148 idênticas" não afirma nada sobre o `incluir()` das classes, e o
  defeito mais perigoso do catálogo (`0 == ""`) vive exatamente ali.
- **Tela cuja tabela está vazia não foi exercitada de verdade.** Prova equivalência entre
  runtimes, não que o caminho de dados foi percorrido.
- **`grep` pula 64% da base em silêncio** (LATIN-1 lido como binário). Usar `grep -a` ou ler
  bytes em Python. Número obtido com `grep` puro aqui é suspeito.

## Quando parar e perguntar

- Categoria de incompatibilidade que não está no catálogo (`docs/registro/`).
- Correção que mudaria **comportamento**, não só compatibilidade (ex.: consertar um bug
  pré-existente que o 5.6 também tem).
- `porta.py` abortou com caso ambíguo.
- A escolha do próximo módulo: rodar `scratchpad/residuo.py` e comparar candidatos pelo
  resíduo e pelo tamanho do lote, em vez de seguir a ordem registrada sem conferir.
