# Contexto, medições de base, arquitetura e grafo de dependências

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

## ⚠ ESTRUTURA: o projeto vive em `ecidade/` desde a reorganização upstream

Em **22/07/2026** a DBSeller reorganizou o repositório (`2169884a8`, PR #5): **44.053 arquivos
foram movidos para dentro de `ecidade/`**, para a página do GitHub não listar 15 mil fontes.
O clone local era de **29/08/2025** e seguiu na estrutura antiga — a divergência só apareceu
quando se foi publicar o trabalho.

```
RAIZ HOJE:  .claude/  CLAUDE.md  docker/  docker-compose*.yml  ecidade/  README.md  scratchpad/
                                                               └── todo o sistema aqui
```

**O ponto de montagem NÃO mudou:** o compose monta `./ecidade` em `/var/www/html`. Por isso
tudo que roda **dentro do container** (os harnesses PHP, os caminhos em `include`) atravessou a
mudança sem alteração. Só o que roda **no host** precisou saber onde o projeto está — os quatro
scripts Python do `scratchpad/`, com um `chdir` cada.

Reconciliação feita por merge: **zero conflitos**, porque o git seguiu as 44 mil renomeações
sozinho. O que ele não podia seguir eram os arquivos **criados depois** da reorganização e os
**ignorados pelo git**, que ficaram órfãos na raiz e tiveram de ser movidos à mão:

| Órfão na raiz | Por quê | Destino |
|---|---|---|
| `vendor/` (13.046) | gitignored | `ecidade/vendor/` |
| `libs/db_conn.php`, `config/*.php` | gitignored (config local) | `ecidade/` |
| `extension/modification/` (59) | criados por mim **depois** da reorganização | `ecidade/extension/` |
| `storage/`, `bootstrap/`, `tmp/`, `.env` | runtime e config | `ecidade/` |

**Sem mover `vendor/` e `libs/db_conn.php` a aplicação não sobe** — não há autoload nem conexão.

Dois arquivos o merge **deletou** e precisaram ser restaurados de `13da3de45`, porque a
reorganização os removeu do versionamento (são gitignored) mas a aplicação os exige:

- `libs/db_acessa.php` — incluído por `db_conecta.php` e `db_stdlib.php`, do núcleo
- `config/require_extensions.xml` — sem ele `login.php:103` redireciona para `index.php`
  com "Instalação de extensões pendentes". O sintoma parece defeito de migração e é arquivo
  de configuração faltando.

Verificado depois da adoção: `login.php` volta aos **12.009 bytes** idênticos, a bateria do
`not` fecha **14/14**, e o enumerador reporta **0 a alterar** nos módulos já portados.

**Armadilha para o próximo módulo:** os commits de porte anteriores registram `classes/x.php`;
os próximos registrarão `ecidade/classes/x.php`. Como o universo é relativo a `ecidade/`,
`enumera.py` e `residuo.py` normalizam o prefixo — sem isso o módulo seguinte veria tudo como
não-pago e o `porta.py` **re-aplicaria guardas já aplicadas**.

## Contexto do trabalho

Projeto final da disciplina **Engenharia de Software** (Ciência da Computação, UFPB).
Objetivo declarado: migrar o e-cidade (GRP municipal open source da DBSeller) de PHP 5.6 /
Laravel 5.4 para **PHP 8.5 + Laravel mais recente + PostgreSQL mais recente**.

O idioma de trabalho do projeto é **português**.

**Conclusão já estabelecida:** migrar o sistema inteiro não é viável no escopo de uma
disciplina — é trabalho de vários anos-pessoa. O escopo acordado é **provar o caminho e
medir o custo do restante**: piloto de um módulo ponta a ponta + roadmap quantificado.

## Stack atual (medido, não presumido)

| Camada | Estado |
|---|---|
| Runtime | **PHP 5.6** (`docker/php56-apache`, Ubuntu 22.04 + PPA ondrej) |
| Framework | `laravel/framework 5.4.*` (2017) |
| Banco | PostgreSQL com cluster em **LATIN1**, locale `pt_BR.ISO-8859-1` |
| Frontend | Vue 2 **e** Vue 3 misturados; Laravel Mix + Webpack 5 |
| E2E | Cypress 9 |
| `vendor/` | **está no `.gitignore`** (não versionado) |

## Números que importam

```
32.908      arquivos PHP
8.691.371   linhas de PHP (excl. vendor/, node_modules/, .git/)
15.694      scripts PHP soltos na raiz (procedurais, *.RPC.php)
46          arquivos *Test.php  +  4 specs Cypress
```

**A cobertura de testes é efetivamente zero.** Este é o principal fator de risco do
projeto — não a sintaxe. Qualquer transformação em massa é inverificável sem antes
escrever testes de caracterização.

## ARMADILHA METODOLÓGICA: 64% da base é ilegível para o `grep`

**Leia isto antes de medir qualquer coisa neste repositório.**

**21.125 dos 32.922 arquivos PHP (64,2%) não são decodificáveis como UTF-8** — são LATIN-1
com acentuação. O `grep` classifica esses arquivos como *binários* e os **pula em silêncio**,
sem aviso, retornando contagens drasticamente subestimadas.

Exemplo real medido em `classes/`: `grep` sem `-a` encontra **39** ocorrências de `split(`;
com `-a`, encontra **12.884**. Erro de 330×. O `grep` enxergava só 300 dos 4.106 arquivos.

Consequências práticas, válidas para todo o projeto:
- Sempre usar `grep -a` (ou ferramenta que leia bytes) nesta base.
- Rector, PHPStan e PHP_CodeSniffer precisam ser configurados com ciência do encoding.
- A conversão de encoding **não é só do banco**: são também ~21 mil arquivos-fonte.
- Qualquer número obtido com `grep` puro neste repositório deve ser considerado suspeito.

## Superfície de incompatibilidade com PHP 8 (medição corrigida)

Números obtidos com varredura byte-a-byte em Python, não com grep (o script `incompat.py` que
os produziu **não sobreviveu** — ver a nota sobre `scratchpad/` abaixo).
**Uma medição anterior feita com grep subestimou tudo isso em uma ordem de grandeza.**

| Construção removida | Removida em | Arquivos | Ocorrências |
|---|---|---|---|
| `split(` | PHP 7.0 | **3.987** | 15.725 |
| `each(` | PHP 8.0 | **720** | 1.850 |
| `$var{...}` (offset com chaves) | PHP 8.0 | 29 | 150 |
| `ereg_replace(` | PHP 7.0 | 15 | 65 |
| `ereg(` | PHP 7.0 | 13 | 75 |
| `eregi(` | PHP 7.0 | 5 | 8 |
| `set_magic_quotes_runtime(` | PHP 7.0 | 4 | 7 |
| `get_magic_quotes_*(` | PHP 8.0 | 3 | 4 |
| `convert_cyr_string(` | PHP 8.0 | 2 | 4 |
| `mysql_*(` | PHP 7.0 | 1 | 4 |
| `create_function(` | PHP 8.0 | 1 | 1 |
| **Arquivos distintos afetados** | | **4.638** | **14,1% da base** |

### O MAIOR RISCO DE TODOS: `0 == ""` mudou de resultado no PHP 8

**Silencioso, sem aviso, e produz dado errado.** Descoberto quando o formulário
"Cemitério → Tipos de isenção → Inclusão" passou a recusar um campo preenchido, no 8.5,
funcionando normalmente no 5.6.

```
PHP 5.6:  0 == ""  ->  true
PHP 8.5:  0 == ""  ->  FALSE     (RFC "Saner string to number comparisons")
```

O idioma onipresente do e-cidade nas classes de dados é:

```php
var $cm34_tipo = 0;                                   // inicializada com INTEIRO
...
$this->cm34_tipo = ($this->cm34_tipo == ""            // no 5.6 da true  -> le do POST
                     ? @$GLOBALS["HTTP_POST_VARS"]["cm34_tipo"]
                     : $this->cm34_tipo);             // no 8.5 da false -> MANTEM 0
```

No PHP 8 o valor do formulário **nunca é lido**, o campo permanece `0`, e a validação
seguinte (`== null`) acusa "Campo não Informado". Propriedades inicializadas com `null`
escapam, porque `null == ""` continua true nos dois — por isso o bug atinge alguns campos
do mesmo formulário e outros não, o que confunde o diagnóstico.

Escala medida na base inteira:

| | |
|---|---|
| Propriedades `var $x = <inteiro>;` | 25.887 em 3.505 arquivos |
| Comparações `== ""` | 72.959 em 7.330 arquivos |
| **Padrão de risco (propriedade numérica comparada com `""`)** | **19.401 ocorrências em 3.412 arquivos** |

**Correção adotada (opção A — corrigir a comparação, não o dado):**

```php
$this->X == ""   ->   ($this->X === 0 || $this->X === 0.0 || $this->X == "")
```

Reproduz exatamente a semântica do PHP 5.6 (`== ""` era true para `null`, `false`, `""`,
`0` e `0.0`, mas não para `"0"`), funciona nos dois runtimes e **não altera nenhum dado**.

*Alternativa considerada e descartada (opção B):* trocar `var $x = 0;` por `var $x = null;`.
Resolve na origem com menos edições, mas muda o valor padrão da propriedade e pode afetar
código que a usa antes do `atualizacampos()` (geração de SQL, aritmética). Se um dia for
adotada, exige validação caso a caso.

**Nenhuma varredura de sintaxe encontra isso** — o código é válido em ambas as versões.
Só aparece exercitando o caminho de escrita da aplicação. É a justificativa mais forte
para o piloto vertical: um `php -l` limpo em 100% dos arquivos não diz nada sobre este bug.

### CATEGORIA NOVA (descoberta no ITBI): aritmética com string não-numérica

No PHP 5.6 a string era coagida para número; no PHP 8 é **TypeError fatal**:

```
              ""/100      "abc"/100    "12,5"/100
PHP 5.6:      0           0            0.12
PHP 8.5:      TypeError   TypeError    0.12
```

Mensagens: `Unsupported operand types: string / int`, `string - float` etc. Apareceu em
`itbi_simulacaoitbi002.php` nas linhas 237 e 271, onde um valor vindo de `str_replace()`
podia chegar vazio.

**Correção: cast explícito `(float)`.** Reproduz a coerção do 5.6 exatamente nos três casos
(`(float)""` = 0, `(float)"abc"` = 0, `(float)"12,5"` = 12) e funciona nos dois runtimes.

Como só dispara quando o valor chega vazio ou não-numérico em tempo de execução, **nenhuma
varredura estática encontra** — apareceu exercitando a tela.

### O MAIOR RISCO: construtores estilo PHP 4 (falha SILENCIOSA)

Descoberto ao portar o núcleo — **não aparece em nenhuma varredura de sintaxe** porque
não gera erro algum. Um método homônimo da classe (`class cl_cgm { function cl_cgm() {...} }`)
era o construtor até o PHP 7.4. **O PHP 8.0 removeu esse comportamento**: o método vira um
método comum e o construtor simplesmente **nunca executa** — sem erro, sem aviso, sem log.

Comprovado empiricamente nos dois runtimes:

```
PHP 5.6  ->  construtor rodou? SIM
PHP 8.5  ->  construtor rodou? NAO
```

| | Classes |
|---|---|
| Com construtor PHP4 **e** `__construct` (já seguras) | 12 |
| **Com APENAS construtor PHP4 (quebram em silêncio)** | **3.587** |
| Destas, com chamada explícita ao nome antigo (exigem cuidado extra) | 7 |

Distribuição: `classes/` **3.417**, `dbagata/` **224**, `libs/` 37, raiz 28, demais 8.

**Correção de medição:** o número aqui era 3.560 e a fatia do `dbagata/` era 70, porque a
varredura só olhava `*.php`. O `dbagata/` usa as extensões **`.class` e `.inc`**, invisíveis
para aquele filtro. Incluindo-as, são **3.587 classes em 3.436 arquivos** (+59 classes em
45 arquivos). Vale para qualquer medição nova: filtrar por `*.php` nesta base deixa
`dbagata/` inteiro de fora.

Ou seja: **praticamente toda a camada de acesso a dados** instancia objetos não
inicializados no PHP 8. Objetos que parecem funcionar e produzem resultado errado —
exatamente o modo de falha mais perigoso para um sistema que calcula folha e tributos.

Correção mecânica e segura nos dois runtimes: renomear `function <NomeDaClasse>(` para
`function __construct(`. Funciona em PHP 5.6 (que já dá precedência a `__construct`) e em 8.5.
Os 7 arquivos com chamada explícita ao nome antigo precisam ser tratados à mão.

Outros padrões legados de grande escala (não são erro fatal, mas afetam a migração):

| Padrão | Arquivos | Ocorrências |
|---|---|---|
| short tag `<?` | 19.660 | 80.953 |
| `pg_*` direto (fora do Eloquent) | 5.185 | 87.446 |
| `$HTTP_*_VARS` (removidos no PHP 5.4) | 10.355 | 22.042 |
| `var $prop` (sintaxe de classe pré-PHP5) | 3.629 | 70.916 |

Lista completa de arquivos afetados: `afetados.txt` — **arquivo perdido**, precisa ser regerado.

## Bloqueadores duros (não se resolvem com `composer update`)

- **`silex/silex ^2.0`** — projeto morto, sem versão para PHP 8. Precisa ser absorvido pelo Laravel.
- **`doctrine/dbal 2.*`** — incompatível com PHP 8+.
- **`symfony/* ~3.2`** — EOL.
- **`zendframework/zend-eventmanager 2.2.10`** — projeto descontinuado/renomeado.
- ~~**`dbseller/session`** — repositório privado~~ **VERIFICADO: NÃO é bloqueador.**
  O `composer.json` o declara por SSH (`git@github.com:DBSeller/Session.git`), o que dá
  aparência de privado, mas o repositório **é público por HTTPS** (`git ls-remote` responde).
  Além disso o `composer.lock` existe (340 KB) e o pacote já está em `vendor/`. A escada de
  versões do Laravel pode começar quando se quiser.
- Outros pacotes DBSeller: `dbseller/legacy`, `dbseller/phinx_postgres`, `dbseller/sdk-api-pix-bb`.
- **Banco em LATIN1** → conversão para UTF-8 é trilha de risco própria (acentuação pt-BR).

## Arquitetura da migração: Strangler Fig

**Restrição física central:** versão de PHP é *por runtime*, não por módulo. Não existe rodar
um módulo em 8.5 e o resto em 5.6 no mesmo processo. Migração incremental exige dois runtimes:

```
        nginx (proxy reverso)
        ├── /<modulo_migrado>/*  ──►  container PHP 8.5 + Laravel atual
        └── /*                   ──►  container PHP 5.6 legado
                                       (ambos no mesmo PostgreSQL)
```

Cada módulo migrado move suas rotas de um container para o outro. Esse proxy é o artefato
de engenharia central do trabalho.

## Mapa de módulos

Os scripts da raiz são consistentemente prefixados por módulo:

| Prefixo | Arquivos | Módulo |
|---|---|---|
| `func_` | 2.993 | **compartilhado — não é módulo** |
| `edu1_` / `edu2_` | 992 | Educação |
| `con1_` `con2_` `con4_` | 1.469 | Contabilidade |
| `pes1_` `pes2_` `pes4_` | 1.105 | Pessoal (RH) |
| `sau1_` | 355 | Saúde |
| `orc1_` / `orc2_` | 544 | Orçamento |
| `cai1_` | 274 | Caixa / Tesouraria |
| `cad1_` | 258 | Cadastros |
| `fis1_` | 242 | Fiscal |

**Porém a camada de dados NÃO é modular** — está organizada por tabela/entidade e é
compartilhada entre módulos:

| Pasta | Arquivos | Organização |
|---|---|---|
| `classes/` | 4.106 | por tabela (`db_abatimento_classe.php`) |
| `forms/` | 2.361 | misto |
| `model/` | 1.658 | por entidade (`AcordoGarantia.model.php`) |
| `funcoes/` | 2.114 | funções |
| `libs/` | 86 | **núcleo**: `db_conecta.php`, `db_stdlib.php`, `db_sessoes.php`, `db_usuariosonline.php` |
| `dbforms/` | 47 | `db_funcoes.php`, `db_classesgenericas.php` |

Consequência: fatias verticais não são gratuitas. Cada módulo arrasta classes/models, e
parte deles é compartilhada → vira núcleo comum a migrar antes ou duplicar temporariamente.

Código já modernizado (parcialmente) convive na mesma árvore: `app/` (Laravel MVC,
`app/Domain/` por domínio de negócio), `src/` (por domínio), `tests/Unit`, `tests/Feature`.

## Grafo de dependências (CONCLUÍDO)

Analisador em `depgraph.py` + `esforco.py` (**ambos perdidos**, ver a nota sobre `scratchpad/`).
Extraía includes do idioma legado
`include(modification("caminho"))`, faz fecho transitivo por script e agrupa por prefixo
de módulo. Cobertura: **5.310 arquivos alcançados**, apenas 54 includes dinâmicos e
121 caminhos não resolvidos (~97% de precisão). 41 módulos com ≥40 scripts.

### O núcleo é pequeno — esta é a boa notícia do projeto

**24 arquivos / 22.007 linhas** são usados por ≥35 dos 41 módulos. É o kernel que precisa
ser portado primeiro; depois dele, cada módulo seguinte fica progressivamente mais barato.

```
libs/db_stdlib.php      libs/db_conecta.php      libs/db_sessoes.php
libs/db_usuariosonline.php  libs/db_acessa.php   libs/db_calcula.php
libs/db_libpessoal.php  libs/db_utils.php        libs/db_sql.php
libs/db_app.utils.php   libs/JSON.php            libs/exceptions/*.php (4)
dbforms/db_funcoes.php  dbforms/db_classesgenericas.php
std/DBString.php        std/db_stdClass.php      config/ecidade_config.php
fpdf151/fpdf.php        fpdf151/pdf.php
model/pessoal/std/DBPessoal.model.php   model/configuracao/mensagem/DBMensagem.model.php
classes/db_cgm_classe.php  (24/41 — registro de cidadãos, puxado por qualquer módulo com pessoas)
```

### Métrica de acoplamento residual

O número que decide o piloto **não** é o % de exclusividade, e sim o **resíduo**: dependências
que não são exclusivas do módulo *nem* fazem parte do núcleo. Resíduo é o que impede a fatia
vertical de ser cortada limpa.

| Mód | Nome | Scripts | LOC total | Deps | Exclus. | Núcleo | **Resíduo** |
|---|---|---|---|---|---|---|---|
| `tra` | Trânsito | 62 | 27.090 | 54 | 34 | 20 | **0** |
| `cem` | Cemitério | 113 | 36.086 | 98 | 70 | 24 | **4** |
| `tfd` | TFD (Saúde) | 84 | 39.002 | 86 | 47 | 24 | 15 |
| `itb` | ITBI | 110 | 38.476 | 97 | 56 | 23 | 18 |
| `vei` | Frota | 172 | 55.539 | 133 | 89 | 24 | 20 |
| `hab` | Habitação | 52 | 27.847 | 98 | 44 | 24 | 30 |
| `bib` | Biblioteca | 98 | 29.362 | 99 | 44 | 23 | 32 |
| `vac` | Vacinação | 80 | 29.234 | 106 | 48 | 23 | 35 |

Módulos grandes descartados como piloto: `con` Contabilidade (1.550 scripts), `pes` RH (1.155),
`edu` Educação (1.211), `cai` Caixa (734). Módulos inviáveis por acoplamento: `pla` (0% exclusivo),
`aco` (14,6%), `soc` (17,3%), `arr` Arrecadação (20,0%).

### ⚠ CORREÇÃO: `tra` é código ÓRFÃO — não serve como piloto demonstrável

O módulo `tra` foi escolhido só pela métrica de acoplamento. **Faltou validar se ele é
alcançável na interface** — e não é. Consulta ao banco:

```sql
-- itens de menu do modulo vs. quantos estao ligados na arvore
SELECT substring(i.funcao from '^[a-z]+') AS prefixo, count(*) AS cadastrados,
       count(m.id_item_filho) AS ligados
FROM configuracoes.db_itensmenu i
LEFT JOIN configuracoes.db_menu m ON m.id_item_filho = i.id_item
WHERE i.funcao ~ '^[a-z]+[0-9]*_.*\.php$' GROUP BY 1;
```

| Módulo | Itens cadastrados | Ligados no menu | Resíduo | LOC |
|---|---|---|---|---|
| **`cem` Cemitério** | 37 | **37 (100%)** | **4** | 36.086 |
| `tfd` TFD | 37 | 31 | 15 | 39.002 |
| `itb` ITBI | 24 | 20 | 18 | 38.476 |
| `vei` Veículos | 118 | 112 | 20 | 55.539 |
| `bib` Biblioteca | 39 | 39 | 32 | 29.362 |
| `vac` Vacinação | 37 | 28 | 35 | 29.234 |
| **`tra`** | 7 | **0 — ÓRFÃO** | 0 | 27.090 |

Não existe módulo "Trânsito" em `configuracoes.db_modulos`; "Transporte Escolar" é outro
módulo. O `tra` é o **único** da lista sem nenhuma ligação na árvore de menu: existe em
código, mas nenhuma tela leva até ele.

**Lição metodológica:** acoplamento decide se a fatia é *cortável*; alcançabilidade no menu
decide se ela é *demonstrável*. Um piloto precisa das duas. A escolha de piloto deve cruzar
a métrica de resíduo COM a contagem de itens ligados em `configuracoes.db_menu`.

**O trabalho no `tra` não foi perdido:** validou a receita de porte ponta a ponta e revelou
quatro categorias de incompatibilidade que nenhuma varredura textual encontra (construtores
PHP4, assinaturas LSP, `=& new`, e a árvore `extension/modification/`), além de motivar toda
a infraestrutura — proxy reverso, sessão compartilhada e correções de permissão.

### NOVO PILOTO: `cem` (Cemitério)

Resíduo 4, **100% dos itens de menu ligados**, módulo real em `db_modulos` (id 289579),
domínio de negócio autocontido. 113 scripts / 98 deps / 36.086 LOC.

### Registro histórico: por que `tra` havia sido escolhido

**Resíduo zero.** Todas as 54 dependências do módulo são exclusivas dele (34) ou pertencem ao
núcleo universal (20). É uma fatia vertical provadamente limpa — não existe nenhum arquivo
"meio compartilhado" a resolver. É também o menor em LOC entre os candidatos.

Escopo do piloto = **núcleo (22.007 linhas) + `tra` (27.090 linhas) ≈ 49k linhas**, ~0,6% da base.
Segunda opção, caso `tra` se mostre pobre em regras de negócio: `cem` (resíduo 4).

## Workflow acordado

- **Fase 0 — Linha de base.** ✅ **CONCLUÍDA.** Ambiente PHP 8.5 paralelo, grafo de
  dependências, catálogo de incompatibilidades medido. (O piloto foi `tra`, depois
  descartado por ser código órfão — ver a correção na seção do grafo.)
- **Fase 1 — Escada PHP + Laravel.** 5.6→7.4 com Rector, Laravel 5.4→5.5→…→8; depois
  PHP 7.4→8.2+ e Laravel 8→atual. Um major por vez, suíte rodando a cada passo.
- **Fase 2 — Substituir dependências mortas** (silex, dbal 2.x, symfony 3.2, zend-eventmanager).
- **Fase 3 — Banco.** Upgrade do PostgreSQL + conversão LATIN1→UTF-8 (trilha separada, alto risco).
- **Fase 4 — Módulos legados** via strangler fig, priorizados por uso real.
- **Fase 5 — Frontend.** Consolidar Vue 3, Laravel Mix → Vite.
- **Fase 6 — CI/CD** para a migração seguir incremental após o fim da disciplina.

### 🗣️ PONTOS LEVADOS AO ORIENTADOR (15/10/2026) — decisão pendente

**1. O nginx é necessário?** Para **medir** a migração, não: `cmp.py`, harness de classes,
caminho de escrita e nível 3 falam direto com `:8080` e `:8085`, e nenhum número do trabalho
passa pelo proxy. Para **operar** o sistema migrado, sim: o login só roda no 5.6 (Laravel),
os links relativos mantêm o usuário na porta em que entrou, e duas portas são duas origens
para o navegador (as janelas do desktop param de conversar — "Sessão inválida (12)"). Sem a
fachada não há *strangler fig*, só dois sistemas lado a lado. Se o escopo for só medir, o
passo 8 da receita (rotear), o `nginx.conf`, o `map` e o `gera_map_faseb.py` saem do
escopo, e a métrica principal passa a ser **equivalência** (telas idênticas ao 5.6), não
roteamento. A regra de "rodar nos dois PHPs" continua: ela vem do código compartilhado.

**2. Como se compara sem login no 8.5?** O login é feito uma vez no 5.6; a sessão é um
arquivo no volume `ecidade_sessions`, que os dois containers leem; as telas legadas leem o
usuário por `db_getsession()`, sem Laravel. O `cmp.py` restaura a sessão antes de cada
requisição e usa o mesmo cookie nas duas portas.

**3. "A tela funciona?" ≠ "a tela é equivalente".** O que está provado com força é a
equivalência. Limites declarados: GET sem parâmetros; "idêntica no erro" conta como
equivalente; tabela vazia não exercita nada; o JS não é executado; fluxos de escrita reais só
em 18 telas (nível 3); nenhuma validação de regra de negócio por especialista. Opções
oferecidas para verificação humana: (A) roteiro de teste funcional navegando pelo `:8090`,
(B) relatório HTML da bateria com as duas versões renderizadas lado a lado, (C) capturas
de tela com o Firefox *headless* (mais frágil por causa da sessão).

**4. Como o TCC de referência fazia login sem o Laravel.** Commit `bc51ef4d5` (PHP8-1):
reescreveu `templates/template_login_e-cidade.php` com `js_acessar_jquery()`, que **pula o
`POST /v4/oauth/token`** e abre `abrir.php?sAuth=base64(DB_login=..&DB_senha=md5(..))` direto
— quem valida a senha e abre a sessão é o `abrir.php`, legado. Sem token, a API `/v4/*` fica
fora da verificação dele. É mudança de comportamento do login, viável só no big-bang. Para nós,
sugere entrar direto no `:8085` pelo mesmo `abrir.php?sAuth=…`, **sem alterar arquivo** —
**não testado**: falta ver se o `abrir.php` abre a sessão no 8.5 e o que fazem as telas não
migradas servidas pelo 8.5.
