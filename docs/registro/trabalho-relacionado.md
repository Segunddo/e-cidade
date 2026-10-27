# Trabalho relacionado: o TCC de referência (monografia, commits e comparação medida)

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

## TRABALHO RELACIONADO — A MONOGRAFIA (lida na íntegra)

ARAUJO, Gerson Junior Fragoso de. **Relato de experiência da migração assistida por
inteligência artificial generativa do módulo de educação do E-Cidade do PHP 5.6 para
PHP 8.4.** TCC (Graduação em Ciência da Computação) — UFPB, João Pessoa, 2026.
Orientador: Prof. Dr. Alan Kelon Oliveira de Moraes. 20 f.

**Método:** estudo de caso único (RUNESON; HÖST, 2009), no formato relato de experiência.
Duas questões de pesquisa: quais passos foram necessários (QP1) e qual o papel do
ferramental automatizado e da IA generativa (QP2). Sem grupo de controle e sem migração
equivalente sem IA — o autor declara explicitamente que **não mede ganho de produtividade**.

**Números do trabalho dele:**

| | |
|---|---|
| Período | 24/mai a 07/jul de 2026 · **31 commits** (9 deles *hotfixes*) |
| Telas do módulo (`edu*.php`) | 1.211 |
| Escopo inicial do Rector (por diretório) | 532 arquivos, 279 modificados |
| **Escopo após descobrir dependências transitivas** | **4.073 arquivos, 3.073 modificados** |
| Validação | `php -l` + catálogo de 11 verificações de regressão + **520 telas navegadas à mão** |
| Ferramenta construída | `rector-helper` (descobre dependências, aplica correções, registra regressões) |

### Convergências — validação independente do nosso catálogo

As categorias que ele lista no Quadro 1 são exatamente as nossas: marcadores curtos,
`parse_str` de 1 argumento, construtores estilo PHP 4, acesso a string com chaves, regex
POSIX. A correção de `parse_str` dele é idêntica à nossa, com `EXTR_SKIP` a mais.

Três achados dele batem com lacunas que descobrimos de forma independente:

1. **"O prefixo do módulo não define sua fronteira técnica"** (Conclusão). O escopo dele
   cresceu **7,7×** (532 → 4.073) ao seguir inclusões dinâmicas. É a mesma descoberta que nos
   custou três lacunas (maiúsculas, menu × prefixo, JavaScript).
2. **A variante em maiúsculas escapou**: "uma variante em maiúsculas ainda falhou", sobre
   `<?PHP`. Mesma família da nossa armadilha de `Cem1_legista001.php`.
3. **Deriva de enumeração**: "os 225 usos restantes de `split` ocorreram porque arquivos de
   Alimentação Escolar foram adicionados após a última execução do Rector".

### A diferença central: o critério de validação

O critério dele, nas palavras do próprio texto:

> "Uma tela atingiu o critério técnico quando carregou sem erro fatal, tela em branco, código
> exibido ou interrupção visível. **Isso não comprova regras de negócio.**"

E na seção 5.3:

> "O critério verificou compatibilidade visível, **não equivalência**, uma tela pode carregar
> e produzir dados errados. Avançar requer base mínima, **cenários iguais antes e depois** e
> participação de especialista no domínio."

**"Cenários iguais antes e depois" é precisamente o que este trabalho construiu.** A
comparação byte-a-byte entre os dois runtimes só é possível porque o strangler fig mantém o
5.6 **vivo como referência** — no big-bang dele, o "antes" deixou de existir no momento em que
o Docker subiu para 8.4.

E é essa diferença que produz o achado do `0 == ""`: a tela carrega, não dá erro, e grava
dado errado. Passa no critério dele; falha no nosso.

### A conclusão dele descreve nossa agenda

> "Trabalhos futuros devem **migrar o Laravel**, **preparar dados e testes executáveis** e
> **aplicar o processo a outros módulos**."

Os três itens são o que estamos fazendo: o dimensionamento do Laravel está medido, a
comparação de 113/120 telas é o teste executável, e a área Tributário é a aplicação a outros
módulos.

### O que vale adotar do trabalho dele

1. **Separar as regras em três grupos** (seção 5.1): (a) exigidas pela versão de destino,
   (b) construções depreciadas, (c) modernizações opcionais. Ele misturou os três na
   configuração cumulativa do Rector e relata que isso "ampliou o volume de alterações e
   dificultou a identificação das causas das regressões". **Nós só aplicamos o grupo (a)** —
   convergência que vale registrar como decisão validada por evidência externa.
2. **"Versão configurada, runtime e regras habilitadas devem ser verificados juntos."** O caso
   `#[\Override]` dele: ambiente em 8.4, Rector declarando 8.5, atributo aplicado a
   propriedades, classes interrompidas — e o diagnóstico inicial, apoiado pela IA, culpou a
   ferramenta errada.
3. **Catálogo nomeado de regressões.** Ele manteve 11 verificações repetíveis. Nossa bateria
   de 113 telas é mais forte, mas não é um catálogo nomeado — nomear cada classe de regressão
   facilita o relatório.

### Requisito formal do curso

O TCC traz uma seção **"7 DECLARAÇÃO DE USO DE FERRAMENTAS DE INTELIGÊNCIA ARTIFICIAL"**,
nomeando os modelos usados, para quê (investigação de erros, implementação, organização e
revisão de código, análise de resultados, revisão gramatical) e declarando que todo o conteúdo
foi analisado, testado, revisado e editado pelo autor, que assume responsabilidade integral.
**Este trabalho precisará de uma seção equivalente.**

## Análise inicial pelos commits (anterior à leitura da monografia)

`https://github.com/ltdufpb/e-cidade` — branch **`tcc-gerson-banca`**, fork de
`DBSeller/e-cidade`, **32 commits** à frente do `master` deles. Outro TCC do mesmo
laboratório, migrando o módulo **Educação**. Analisado pela API do GitHub (o repositório tem
488 MB; não vale clonar — `curl` na API de comparação e nos arquivos crus resolve).

### Convergência: chegaram às mesmas categorias, por outro caminho

Validação independente do nosso catálogo. Os commits deles mostram:

```
PHP8-10-hotfix3    construtores PHP 4 -> __construct
PHP8-11            construtores PHP 4 remanescentes (27 arquivos, 2a passada)
PHP8-15 / PHP8-18  parse_str de 1 argumento
PHP8-16 / 19 / 20  guardas pg_num*/pg_fetch_array contra resultado false
PHP8-17            acesso a string por chaves {} -> []
PHP8-21            restaura acentos ISO-8859-1 corrompidos por editor UTF-8 (7 arquivos)
```

O PHP8-21 é exatamente a armadilha de encoding documentada aqui — eles foram mordidos por
ela. A guarda de `pg_num*` deles é equivalente à nossa, só mais explícita:

```php
$numrows = ($result === false || $result === null) ? 0 : pg_numrows($result);
```

### Evidência empírica contra transformação em massa

Eles usaram **Rector** intensivamente. A sequência de hotfixes que se seguiu é o argumento
mais concreto a favor da decisão de corrigir pontualmente — e vem de fora deste projeto:

```
hotfix2   remove #[Override] aplicado erroneamente em propriedades
PHP8-12   remove use duplicado FATAL introduzido pelo withImportNames
PHP8-14   restaura shim de superglobais REESCRITO pelo Rector
hotfix9   corrige bug CATASTROFICO do shim - parou de sobrescrever $_SESSION
```

Quatro quebras causadas pela própria ferramenta de automação, incluindo a reescrita do shim
que eles mesmos haviam criado.

### Estratégia oposta — material direto para o capítulo de comparação

| | TCC Educação | Este trabalho |
|---|---|---|
| Alvo | PHP **8.4** | PHP **8.5** |
| Abordagem | **big-bang**: Docker atualizado de 5.6 → 8.4 | **strangler fig**: dois runtimes convivendo |
| Short tags | convertidas em **11.108 arquivos / 37.345 tags** | mantido `short_open_tag = On` (zero arquivos) |
| `$HTTP_*_VARS` | shim de superglobais (causou o bug catastrófico) | intocados (já emulados por `emulateRegisterLongArrays`) |
| Compatibilidade | roda só em 8.4 | roda em 5.6 **e** 8.5 |
| Verificação | não documentada nos commits | 113 páginas comparadas byte-a-byte entre runtimes |

### Achado nosso ausente no trabalho deles: `0 == ""` nas classes de dados

Medido na branch `tcc-gerson-banca` — reproduzível com:

```bash
curl -sf "https://raw.githubusercontent.com/ltdufpb/e-cidade/tcc-gerson-banca/classes/db_turma_classe.php" -o /tmp/t.php
python3 -c '
import re
b=open("/tmp/t.php","rb").read()
props={m.group(1) for m in re.finditer(rb"(?:var|public)\s+\$(\w+)\s*=\s*-?\d+\s*;", b)}
print("props int:", len(props),
      "| com == \"\":", sum(len(re.findall(rb"\$this->"+re.escape(p)+rb"\s*==\s*[\"\x27]{2}", b)) for p in props),
      "| corrigidas:", len(re.findall(rb"===\s*0\s*\|\|", b)))'
```


| Classe | Props inteiras | Comparadas com `== ""` | Corrigidas |
|---|---|---|---|
| `classes/db_turma_classe.php` | 17 | 14 | **0** |
| `classes/db_matricula_classe.php` | 11 | 9 | **0** |
| `classes/db_alunoalt_classe.php` | 9 | 7 | **0** |
| `classes/db_calendario_classe.php` | 11 | 9 | **0** |

O idioma `$this->ed57_i_escola == "" ? le_do_POST : mantem` continua intacto, com a
propriedade declarada como `public $ed57_i_escola = 0;`. É o mesmo defeito que travou a
inclusão em "Cemitério → Tipos de isenção": no PHP 8 o valor do formulário **nunca é lido**
e a validação seguinte acusa "campo não informado".

Eles corrigiram uma manifestação vizinha — contadores locais `$conta = ""` → `0` no PHP8-20 —
mas não a das classes de dados. Como é o mesmo laboratório, vale comunicar: são formulários
de Educação gravando dado errado em silêncio.

### ⚖️ COMPARAÇÃO MEDIDA COM O TCC DE REFERÊNCIA (branch `tcc-gerson-banca`)

Feita sobre **o mesmo universo** (os ~2.795 arquivos que as sete frentes alcançam a partir das
telas da área Educação) e **o mesmo critério**: comparação byte-a-byte contra o 5.6 vivo.

#### Como foi montada

- `git fetch` da branch dele para `refs/remotes/gerson/tcc-gerson-banca` (só leitura, sem mexer
  nos remotos). Estrutura **anterior** à reorganização (arquivos na raiz, não em `ecidade/`).
- *worktree* dele em `ecidade/tmp/tcc_gerson/` (gitignored, 1,1 GB) + as configurações locais
  não versionadas (`.env`, `config/*.php`, `libs/db_conn.php`, `extension/data/`…).
- **Terceiro container**, `ecidade_tcc_gerson` na porta **8086**: mesma imagem do nosso 8.5,
  mesmos volumes de sessão e `/tmp`, mesmo `paridade-56.ini`, mesmo `vendor/` (ele não alterou
  `composer.json`/`.lock`). **Só o código difere** do nosso 8085.
- `cmp.py` ganhou `PORTA_B` (8085 = nosso, 8086 = dele) e `NORM_MENU` (abaixo).
- **Limitação declarada:** ele mirou PHP **8.4**; rodou aqui no **8.5.10**. Os fatais encontrados
  são todos de categorias que quebram desde o 8.0 (valem para o 8.4); nenhum veio de algo
  exclusivo do 8.5.

#### 1. Estático — por *token* (`scratchpad/conta_tokens.php`), só código, nunca comentário

| Universo de Educação (~2.795 arq.) | Antes | Gerson | **Nosso** |
|---|---|---|---|
| **guarda `0 == ""` faltando** | 3.685 em 730 arq. | **3.685 em 730 arq.** | **0** |
| construtor PHP 4 | 646 | 0 | 0 |
| `parse_str` de 1 argumento | 545 | 0 | 0 (1 em arquivo que não compila nem no 5.6) |
| `split()` | 2.759 | 776 | 0 |
| `ereg*()` / `each()` | 13 / 3 | 0 / 0 | 0 / 0 |

**Duas correções que esta medição impôs a afirmações anteriores:**

1. **`split()` tem polyfill.** `vendor/dbseller/legacy/bootstrap/PHP_56.php` define `split()` no
   PHP ≥ 7 — e a implementação é **`explode()`**. Os 776 que ele deixou usam todos separador
   literal (`"#"` 775, `"_"` 1), nenhum com `limit`: **equivalentes**, não defeito. O mesmo vale
   contra nós: as milhares de conversões `split` → `preg_split` **não eram necessárias para
   rodar** — só nos separadores com regex (o caso do `jur`, onde o polyfill `explode` daria dado
   errado) e para não depender de um `vendor/` não versionado. O polyfill também ignora o 3º
   argumento do `split` original.
2. O contador de bytes do `enumera.py` acusou 2 guardas faltando do nosso lado
   (`db_db_config_classe.php:755-756`, `$x == "null" || (guarda…)`): **falso positivo** — o
   único valor em que `0 == "null"` muda (o inteiro `0`) é coberto pela guarda à direita do `||`.
   E 4 `split` "restantes" estavam dentro de `/* */` (o Rector, com razão, não os tocou).

#### 2. Caminho de escrita (nível 1) — o efeito das 3.685 guardas, medido

`escrita.php` sobre as 756 classes de Educação, uma classe por processo, contra o 5.6:

| | Campos com valor diferente do 5.6 | Classes |
|---|---|---|
| **Gerson** | **3.606** | **730** |
| **Nosso** | **0** (1 linha: artefato conhecido de `RequisicaoMaterial`) | 0 |

```
5.6:     ed80_i_codigo='1012'  ed80_i_diarioavaliacao='1013'  ed80_i_justificativa='1014'
Gerson:  ed80_i_codigo=0       ed80_i_diarioavaliacao=0       ed80_i_justificativa=0
```

É o `0 == ""` em escala: o valor digitado no formulário **não é lido**; o campo fica `0` e a
validação recusa ("campo não informado") ou o `0` é gravado. **Nenhuma tela "carrega com erro"
por isso** — passa no critério dele ("carregou sem erro fatal") e falha no nosso.

#### 3. Dinâmico — as 1.551 telas da área, 5.6 × código dele

Bruto: **424 idênticas** (nosso: 1.534). Classificadas as 1.087 divergências:

| Categoria | Telas | É defeito da migração dele? |
|---|---|---|
| idêntica depois de recortar o `db_menu()` | 482 | **sim, um único** — ver abaixo |
| só espaço em branco (a quebra de linha final do documento) | 294 | não (efeito da conversão de *short tags* no `?>` final) |
| quebram nos dois, só muda a mensagem de erro | 85 | não (pré-existente; ele exibe a exceção, a referência diz "Erro interno") |
| **500 só no código dele** | **175** | **sim** |
| **página truncada / conteúdo faltando** | **26** | **sim** |
| outra diferença de conteúdo | 22 | provável — não verificadas uma a uma |
| **acentuação corrompida** (`vínculo` → `vÃ­nculo`) | **2** | **sim** (arquivo LATIN-1 salvo como UTF-8 — o problema do PHP8-21 dele) |
| timeout (os 8 laços eternos do `edu4`, iguais aos nossos, + 1) | 9 | não |

**As causas dos 175 fatais são as categorias do nosso catálogo**, sem tratamento no código dele:

```
81  pg_num_fields(false)       libs/db_stdlib.php:1330 (db_fieldsmemory) -- corrigido por nos no piloto cem
44  pg_num_rows(false)
24  get_magic_quotes_runtime()  fpdf151/fpdf.php:1375 -- removida no PHP 8.0; corrigida por nos no nucleo
 4  reset(null)   3 count(null)   3 Path must not be empty   2 cal_days_in_month   ...
```

**105 dos 175 vêm de dois pontos do núcleo** — corrigidos uma vez aqui, quebram dezenas de telas
lá. Os pontos `pg_*` só disparam quando a SQL falha (a categoria "consulta quebrada" do catálogo),
o que explica por que 520 telas navegadas à mão não os encontraram.

**O defeito sistemático, único:** no código dele a camada V3 (`Request->session()->get()`)
devolve **`NULL`** para o login, enquanto o `db_getsession()` legado lê `dbseller` normalmente —
no mesmo container, mesma sessão. Consequência: `ECIDADE_DESKTOP` dá `false` e o `db_menu()`
emite o **menu clássico** (~400 linhas) no lugar do estilo/script do desktop, em **toda** tela.
Provado que é do código (8085 e 8086 diferem só no código; `isEnabled('Desktop','dbseller')` dá
`true` nos dois). **A linha exata não foi localizada** — ele alterou 21.967 arquivos. Para medir
os defeitos *por tela* sem que esse um esconda os outros, `NORM_MENU=1` recorta só as partes
**exclusivas** de cada ramo do `db_menu()` (três regex independentes; a parte comum, o tooltip,
continua comparada). Verificado: com ela o **nosso** lado continua 40/40 na amostra.

#### Síntese, sobre o mesmo universo e o mesmo critério

| | TCC de referência | Este trabalho |
|---|---|---|
| Telas da área equivalentes ao 5.6 | 1.316 de 1.551 (84,8%) — contando as 294 só-espaço e as 85 que quebram nos dois | **1.534 de 1.551 (98,9%)** |
| Telas com defeito de migração | **≥ 203** (175 fatais + 26 truncadas + 2 acentuação; + até 22) | **0** (17 caracterizadas, todas pré-existentes ou artefato) |
| Defeito sistemático em toda tela | 1 (camada V3 sem login → menu clássico) | 0 |
| Campos de formulário não lidos (POST) | **3.606 em 730 classes** | **0** |
| Roda no 5.6 também | não (big-bang) | sim |

**A leitura correta não é "o trabalho dele está errado".** Ele declarou o próprio critério —
"carregou sem erro fatal… isso não comprova regras de negócio" — e o cumpriu nas 520 telas que
navegou. A diferença é **de critério de verificação**, e é exatamente a que este trabalho existe
para mostrar: com o 5.6 vivo como referência, a comparação byte-a-byte e o caminho de escrita
encontram o que a navegação não encontra — 3.606 campos que gravariam dado errado em silêncio, e
~200 telas que só quebram nos caminhos de dado incomum.

**Pendências honestas:** as 22 "outras diferenças" não foram verificadas uma a uma; a causa do
defeito da camada V3 não foi localizada; o runtime foi 8.5, não o 8.4 dele. O container
`ecidade_tcc_gerson` e a worktree ficam para reprodução (remover com
`docker rm -f ecidade_tcc_gerson && git worktree remove ecidade/tmp/tcc_gerson`).
