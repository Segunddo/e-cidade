## Direcionamentos para o Claude

1. Pense antes de escrever o código

**Não faça suposições, não esconda dúvidas e diga os trade-offs**

Antes de implementar algo:
- Declare suas suposições explicitamente, se tiver alguma dúvida pergunte
- Se houver várias maneiras de fazer, mostre-as e não escolha em silêncio
- Se existir alguma abordagem mais simples, apresente-a. Questione quando for pertinente
- Se algo não estiver claro, pare, identifique o que está confuso e pergunte

2. Simplicidade em primeiro lugar

**O código mínimo para resolver o problema, nada de especulações**

- Sem funcionalidades além do que foi pedido
- Sem abstrações para código de uso único
- Sem "flexibilidade" ou "configurabilidade" não solicitadas
- Sem tratamento de erros para cenários impossíveis.
- Se você escrever 200 linhas e o código puder ter 50, reescreva-o.

Pergunte a si mesmo: "Um engenheiro sênior diria que isso está excessivamente complexo?" Se a resposta for sim, simplifique.

## 3. Alterações Cirúrgicas

**Toque apenas no que for necessário. Limpe apenas a bagunça que você mesmo criou.**

Ao editar código existente:
- Não tente "melhorar" código, comentários ou formatação adjacentes.
- Não refatore o que não está quebrado.
- Siga o estilo existente, mesmo que você o fizesse de outra forma.
- Se encontrar código morto não relacionado, mencione-o — não o exclua.

Quando suas alterações criarem elementos órfãos:
- Remova importações, variáveis ​​ou funções que se tornaram inúteis devido às SUAS alterações.
- Não remova código morto preexistente, a menos que solicitado.

O critério: Cada linha alterada deve estar diretamente ligada à solicitação do usuário.

## 4. Execução Orientada a Objetivos

**Defina critérios de sucesso. Itere até a verificação.**

Transforme tarefas em objetivos verificáveis:
- "Adicionar validação" → "Escrever testes para entradas inválidas e fazê-los passar"
- "Corrigir o bug" → "Escrever um teste que o reproduza e fazê-lo passar"
- "Refatorar X" → "Garantir que os testes passem antes e depois"

Para tarefas com múltiplas etapas, descreva um plano conciso:
```
1. [Etapa] → verificar: [critério]
2. [Etapa] → verificar: [critério]
3. [Etapa] → verificar: [critério]
```

## 5. Memória

Documente tudo que seja importante para a conclusão do projeto nesse arquivo. Não deixe
tópicos importantes de fora

Critérios de sucesso sólidos permitem que você trabalhe de forma independente. Critérios vagos ("fazer funcionar") exigem esclarecimentos constantes.

# e-cidade — Projeto de Migração

## ⏱ ESTADO ATUAL — leia primeiro ao retomar

**Onde paramos:** **ÁREAS TRIBUTÁRIO E EDUCAÇÃO CONCLUÍDAS** (branch `2educacao-migrado`).
Conferido pelo proxy, tela de menu por tela de menu (15/10/2026): **Tributário 1.059/1.059** e **Educação
480/480** arquivos de menu existentes servidos pelo PHP 8.5 — depois de fechar a *10ª LACUNA* (14 telas
que o `map` não roteava). Ver *🏁 ÁREA EDUCAÇÃO CONCLUÍDA*.
**Comparação com o TCC de referência FEITA** — ver *⚖️ COMPARAÇÃO MEDIDA COM O TCC DE REFERÊNCIA*. Portados e roteados `tre`, `esc`, `rel`, `sec`, `bib`, `mer` (+ 20 telas `mat`/`pro` por
`map`) `edu3_` + variantes `edu0x_`/`edu_`, `edu2_`, `edu4_` e os 4 sublotes do `edu1_` — todo o prefixo `edu` (1.211 arquivos). Ver *ÁREA EDUCAÇÃO*.

| | |
|---|---|
| Módulos portados | **16 de 16** — todos com 100% das telas de menu servidas pelo PHP 8.5 |
| Também portado | `tra` — órfão no menu, sem uso prático |
| Núcleo (24 arq.) | portado, com guardas `pg_*` acrescentadas conforme os defeitos aparecem |
| Bibliotecas | **`dbagata/` portado** (211 arquivos executáveis, 213 construtores) — ver seção própria |
| Rota no nginx | `location ~* ^(?:/w/[0-9]+)?/(?:cem\|itbi?\|agua?\|jur\|div\|mar\|not\|fis\|iss\|dvr\|arr\|tri\|inf\|tra\|tre\|esc\|rel\|sec\|bib\|mer\|edu\|rh\|eso\|rec\|pes)[0-9]*_)` — **4.872 arquivos** + 367 por `map` |
| **Próximo passo** | **Área RECURSOS HUMANOS em andamento** (branch `3recursoshumanos-migrado`, ver *ÁREA RECURSOS HUMANOS*): Fase A concluída (`rh`, `eso`, `rec`, `pes` inteiros); próximo: Fase B (~10 telas pelo `map`) (ver *PARA RETOMAR* na seção). |
| **php.ini do 8.5** | `docker/php85-apache/paridade-56.ini`, montado pelo compose: **`output_buffering = 4096`**, igual ao 5.6. Ver *CATEGORIA NOVA: AMBIENTE*. |
| **Dívida técnica aberta** | `fpdf151/` da raiz (28 arquivos, ver *6ª LACUNA*). O `dbagata/` **saiu da lista**. |
| Frentes de enumeração | **sete**, todas insensíveis a maiúsculas desde a **9ª lacuna** (`getdao`) |
| **Instrumento do passo 4** | **MUDOU: Rector** (`scratchpad/rector-curado.php` + 2 regras próprias) substituiu o `porta.py` a partir do `iss`. Ver *DECISÃO: Rector adotado*. |

**Como subir o ambiente** (a ordem importa — 8.5 e proxy dependem da rede criada pelo 5.6):

```bash
docker volume create ecidade_sessions && docker volume create ecidade_tmp
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d
docker exec ecidade_php56 chmod 1777 /tmp      # o volume nasce root:root 755
chmod -R 777 ecidade/storage ecidade/bootstrap/cache 2>/dev/null; chmod 777 ecidade/extension/log   # SEM && : o -R falha em cache do container e abortaria o resto
chmod 666 ecidade/extension/log/*.log   # os ARQUIVOS, nao so a pasta -- senao TODA tela autenticada da 500
chmod 777 ecidade/tmp ecidade/arquivos        # SEM isto, 11% das telas falham antes de executar
docker compose -f docker-compose.php85.yml up -d
docker compose -f docker-compose.proxy.yml up -d
```

**Use `http://localhost:8090`** (origem única). Login `dbseller`/`dbseller`. O cabeçalho
`X-Ecidade-Runtime` em cada resposta diz qual runtime a serviu.

**Para migrar o próximo módulo:** invocar a skill **`migrar-modulo`**
(`.claude/skills/migrar-modulo/SKILL.md`) — ela traz o procedimento executável com os
comandos, as verificações e as armadilhas. Este arquivo continua sendo o catálogo e o
*porquê*; a skill é o *como*. A receita de 9 passos também está resumida na seção
*ESTRATÉGIA ADOTADA*.

**Regime de permissões (MUDOU):** `tmp/` e `arquivos/` agora são **777**. Antes eram 775 e
nenhum container conseguia escrever, o que fazia **11% das telas da área falharem antes de
executar** — e aparecerem como "idênticas" nas baterias por falharem igual. Toda medição
anterior a esta mudança carrega esse ponto cego; as posteriores, não.

**Pendências conhecidas:** todas as divergências de `cem`, `itb` e `agu` estão caracterizadas
(ver as seções de cada módulo). As que restam são de três tipos, nenhum deles defeito de
migração: telas que quebram **no 5.6** e funcionam no 8.5 (defeito pré-existente da
referência), fragmentos de include que não são telas, e relatórios que falham **igualmente**
nos dois runtimes por `tmp/` não ser gravável. A dívida real aberta é `dbagata/`.

**Fora de escopo até aqui:** Laravel continua 5.4 (não roda em PHP 8, por isso o login fica
no runtime 5.6) e PostgreSQL continua 16 em LATIN1. São as Fases 1-3 do workflow.

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

## ESTRATÉGIA ADOTADA: migrar a ÁREA Tributário, módulo a módulo

Decisão tomada após o piloto Cemitério: em vez de módulos isolados, focar numa **área**
inteira — mesma forma do TCC de Educação (trabalho relacionado), o que torna os dois
diretamente comparáveis.

### Por que Tributário

A área é definida no banco por `configuracoes.atendcadarea` + `atendcadareamod`:

| Área | Módulos |
|---|---|
| **DB:TRIBUTÁRIO** | **16** ← esta |
| DB:PATRIMONIAL | 8 |
| DB:SAÚDE | 8 |
| DB:FINANCEIRO | 6 |
| DB:EDUCAÇÃO | 5 ← o TCC de referência |

É a maior área do sistema, **3× a Educação**, e o Cemitério (já portado) pertence a ela.
Seus 16 módulos somam **1.024 telas** no menu.

### A distinção central: PORTAR ≠ ROTEAR

**O menu lista apenas ~1/3 dos arquivos de um módulo.** Medido:

| prefixo | arquivos | no menu | fora do menu |
|---|---|---|---|
| `cem` | 116 | 40 (34%) | **76** |
| `iss` | 400 | 165 (41%) | **235** |
| `fis` | 353 | 92 (26%) | **261** |
| `cad` | 523 | 162 (31%) | **361** |

Os outros dois terços são popups abertos por `window.open`, endpoints `.RPC.php` chamados
por AJAX e subtelas. **No Cemitério isso passou despercebido por sorte**: enumerei por
prefixo, não pelo menu. Com a lista do menu, 76 arquivos teriam ficado sem correção.

Regra que decorre disso:
- **Portar → sempre por prefixo** (`re.IGNORECASE`), senão fica 2/3 do módulo para trás.
- **Rotear → é onde a fronteira da área importa.**

### 3ª LACUNA: arquivos abertos por JavaScript não entram no fecho de dependências

Descoberta no ITBI, reportada pelo usuário (o campo "Forma de Pagamento" não aceitava
digitação). O fecho transitivo só segue `include`/`require`. Mas as telas abrem *lookups* e
subjanelas por **JavaScript**, que é uma requisição HTTP nova, invisível ao analisador:

```javascript
js_OpenJanelaIframe('','db_iframe_...','func_itbiformapagamento.php?funcao_js=...');
```

No ITBI havia **13 arquivos** nessa condição (9 deles quebrados em PHP 8, todos com
`parse_str` de 1 argumento): `func_itbi.php`, `func_itbiformapagamento.php`,
`func_itbiliberado.php`, `func_itbitransacao.php`, `func_matricitbi.php`, `func_tabdesc.php`,
`func_taxasitbi.php`, `func_taxaslancadas.php` e `cad3_conscadastro_002.php`.

**Passo a acrescentar à receita de enumeração** — varrer os scripts do módulo atrás de
nomes de arquivo `.php` citados em strings (o JS os referencia como texto):

```python
alvo = re.compile(rb"([A-Za-z0-9_]+\.(?:RPC\.)?php)")
# para cada script do modulo, coletar os nomes citados que existam em disco
# e NAO casem com o prefixo do modulo -> sao candidatos abertos por JS
```

Detalhe de roteamento: esses `func_*` **continuam servidos pelo 5.6** (o prefixo `func_` é
compartilhado por todos os módulos e não pode ir para o 8.5 isoladamente). Como as correções
são compatíveis com os dois runtimes, isso não é problema — mas eles **precisam ser portados
mesmo assim**, senão quebram quando o módulo que os usa for roteado.

**Lição, terceira da mesma família:** as três lacunas do porte — maiúsculas, menu × prefixo,
e agora JavaScript — têm a mesma raiz. Toda verificação partia da lista que a própria
enumeração gerou, e nenhuma delas podia encontrar o que a enumeração não incluiu. As três
foram descobertas pelo usuário navegando o sistema, não pelas baterias automatizadas.

### Prefixos exclusivos vs. compartilhados

Consulta que revela a colisão:

```sql
SELECT lower(substring(di.funcao from '^[A-Za-z]+')) AS prefixo,
       count(DISTINCT a.at25_descr) AS n_areas
FROM configuracoes.atendcadareamod am
JOIN configuracoes.atendcadarea a ON a.at26_sequencial = am.at26_codarea
JOIN configuracoes.db_modulos m ON m.id_item = am.at26_id_item
JOIN configuracoes.db_menu dm ON dm.modulo = m.id_item
JOIN configuracoes.db_itensmenu di ON di.id_item = dm.id_item_filho
WHERE di.funcao ~ '^[A-Za-z]+[0-9]*_.*\.php$'
GROUP BY 1 HAVING count(DISTINCT a.at25_descr) > 1;
```

**Prefixos de arquivo NÃO respeitam a fronteira das áreas** — `con` aparece em 6 áreas,
`pro` em 5, `cai` em 4, `cad` em 3. "Área" é agrupamento de *menu*, não de *código*.

**EXCLUSIVOS de Tributário — 1.800 arquivos, roteamento trivial por prefixo:**

```
iss 400   fis 353   agu 221   arr 162   div 148   jur 145
cem 116✓  itb 110   mar  35   tri  33   dvr  33   inf  30   not 14
```

**COMPARTILHADOS — 3.244 arquivos, exigem lista explícita:**

```
con 1559   cai 740   cad 523   pro 337   pre 54   amb 31
```

### Plano em fases

**Fase A — os 12 prefixos exclusivos restantes (1.684 arquivos).** Cobre 12 dos 16 módulos:
ISSQN, Fiscal, Água, Arrecadação, Dívida Ativa, Jurídico, ITBI, Marcas e Sinais, Diversos,
Inflat, Notificações — mais o Cemitério pronto. Roteamento em uma linha:

```nginx
location ~* ^(?:/w/[0-9]+)?/(?:cem|iss|fis|agu|arr|div|jur|itb|mar|tri|dvr|inf|not)[0-9]?_
```

**Fase B — os 6 prefixos compartilhados**, só se houver tempo. Aí entra um `map` do nginx
gerado a partir do banco, porque `cad` e `con` não podem ir inteiros para o 8.5 sem arrastar
Financeiro e Patrimonial junto.

**Progresso da Fase A: CONCLUÍDA.** `cem` ✅ · `itb`/`itbi` ✅ · `agu` ✅ · `jur` ✅ · `div` ✅ · `mar` ✅ · `not` ✅ · `fis` ✅ · `iss` ✅ · `dvr` ✅ · `arr` ✅ · `tri` ✅ · `inf` ✅ — 13 de 13 prefixos exclusivos.

### ⚠ ORDEM REVISTA: `jur` antes de `div`, e `arr` por último

A ordem anterior (`arr` → `div` → `jur`) foi herdada da tabela de resíduo original, que era
**anterior aos três portes** e usava um fecho de dependências só de `include`. Recomputada com
a enumeração completa da receita (includes + autoload + citados em strings) e descontando o que
os portes já pagaram, ela se inverte. Analisador: `scratchpad/residuo.py`.

| | `jur` Jurídico | `div` Dívida Ativa | `arr` Arrecadação |
|---|---|---|---|
| Telas (prefixo, IGNORECASE) | 145 | 148 | 162 |
| Itens de menu ligados | 57 de 64 (89%) | 63 de 64 (98%) | 85 de 88 (97%) |
| Dependências no fecho | 170 | 244 | 509 |
| Já pagas (núcleo + portados) | 42 | 53 | 48 |
| Exclusivas do módulo | 35 | 42 | 37 |
| **Resíduo** | **93** | **149** | **424** |
| Resíduo que precisa de alteração | 76 | 124 | 301 |
| **Arquivos a alterar (total)** | **137** | **198** | **343** |

Calibração contra o que já foi feito — arquivos efetivamente alterados por lote: `itb` **105**,
`cem` **124**, `agu` **171**. Ou seja: `jur` (137) cai **dentro da faixa já provada**, `div`
(198) fica acima do maior lote já executado, e `arr` (343) é **o dobro** dele.

O que cada um arrasta de módulos não portados (só os arquivos que precisam de alteração):

```
jur   func:69   cai:52   div:38   arr:36   cad:28
div   func:112  cai:86   iss:63   arr:61   cad:59
arr   func:285  cai:252  con:212  emp:208  pes:203
```

**`arr` é o único que rompe a fronteira da área.** Ele arrasta 212 arquivos de `con`
(Contabilidade, 1.559 scripts) e 203 de `pes` (RH) — módulos de *outras* áreas. `jur` e `div`
arrastam sobretudo `func` (compartilhado por todos, inevitável) e módulos da própria área.

**Efeito de ordem:** a soma é invariante — 559 arquivos para os três, em qualquer ordem. Logo a
ordem **não muda o custo total**, muda o tamanho do primeiro lote e portanto a velocidade do
ciclo de verificação:

```
jur -> div -> arr     137 + 157 + 265
arr -> div -> jur     343 + 132 +  84
```

**Ordem adotada:** `jur` → `div` → `mar`/`tri`/`dvr`/`inf`/`not` → `arr` → `fis` (353) →
`iss` (400). O `arr` desce para perto do fim, junto dos grandes.

**RESSALVA IMPORTANTE — resíduo não é bloqueador.** Os três módulos já portados deixaram
resíduo não portado (`cem` 20, `itb` 24, `agu` 29 arquivos que precisariam de alteração) e
mesmo assim verificam byte-a-byte: 114/116, 116/120 e 222/224. Esses arquivos não estão nos
caminhos exercitados. Resíduo mede **contaminação de escopo** — quanto de outros módulos o
porte encosta —, não risco de quebra.

Os números desta tabela **não são comparáveis** com a tabela de resíduo histórica (onde `tra`
tinha 0 e `cem` tinha 4): aquela usava fecho só de `include`, que não enxerga autoload nem os
arquivos abertos por JavaScript.

### Receita por módulo (validada em `cem`, `itb` e `agu`)

Cada prefixo é um lote independente, com commit próprio e revertível:

```
1. enumerar, em SETE frentes       -> verificar: cada frente fecha (ver abaixo)
2. varrer as categorias conhecidas -> verificar: inventário fechado
3. classificar cada ocorrência     -> verificar: nenhum falso-positivo de JavaScript
4. aplicar (Rector, ver abaixo)    -> verificar: zero remanescentes, REPETINDO ate dar 0
4b. portao de FUNCOES contra o 5.6 -> verificar: nenhuma funcao emitida que falte no 5.6
5. php -l nos DOIS runtimes        -> verificar: 100% OK em 5.6 e 8.5 (com </dev/null!)
6. instanciar as classes           -> verificar: estado idêntico entre runtimes
7. comparar as telas com sessão    -> verificar: byte-a-byte, normalizando ids aleatórios
8. acrescentar o prefixo ao nginx  -> verificar: X-Ecidade-Runtime = PHP-8.5
9. commit
```

**O passo 1 é o que mais falhou.** Sete lacunas distintas já foram encontradas ali, todas
com a mesma assinatura: a verificação partia da lista que a própria enumeração gerou, então
não podia achar o que a enumeração deixou de fora. As sete frentes:

| Frente | Como | Lacuna que fecha |
|---|---|---|
| prefixo | `re.IGNORECASE`, e aceitar sufixos de letra (`itbi`, `agua`) | maiúsculas; sub-prefixos |
| fecho de includes | `include(modification(...))` transitivo | — |
| citados em strings | nomes `*.php` dentro do código (o JS os abre) | 3ª: `window.open` |
| autoload | classes `cl_*` instanciadas **e `db_utils::getDao('x')`**, resolvidas em `classes/` | 4ª: `spl_autoload_register`; 7ª: `getDao()` |
| bibliotecas vendorizadas | `dbagata/`, incluindo `*.class` e `*.inc` | 5ª: `dbagata/` |
| **pasta inteira da lib** | se um arquivo de uma pasta-biblioteca entrou, **varrer a pasta toda** | 6ª: `fpdf151/` (2 de 194 portados) |

Conferir o total contra `ls | grep -iE '^<pref>[0-9]*_'` **antes** de dar o módulo por pronto.

Estimativa da área inteira: **1.804 arquivos no universo, 775 precisando de alteração (43%)**
— 1.823 `split(`, 276 `parse_str` de 1 argumento, 431 arquivos com construtor PHP 4 e 3.040
comparações `0 == ""`. **Nenhuma categoria nova** além das já catalogadas.

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

## Princípios ao trabalhar neste repositório

- **Nunca aplicar transformação em massa sem teste de caracterização antes.** O e-cidade roda
  folha de pagamento, empenho contábil e tributos de prefeitura real. Regressão silenciosa em
  cálculo não é bug — é município que não paga servidor.
- **Medir antes de decidir.** Este arquivo só contém números verificados no código; manter assim.
- **O objetivo é MIGRAR, não consertar.** Bug pré-existente não se corrige: documenta-se e
  deixa-se como está. Quando o PHP 8 transforma em fatal algo que o 5.6 tolerava, a correção
  certa é a que **reproduz o comportamento do 5.6** — não a que conserta a intenção do autor.
  Exemplos já decididos assim: o `break` fora de laço do `fis` virou `exit` (o 5.6 morria ali)
  em vez de ser removido; o `"J"` passado como `$ln` ao FPDF foi contornado com `(float)$ln`
  em vez de corrigido na chamada; o `1969-12-31` do `db_vencimento()` foi preservado.
  **Critério:** se a alteração mudaria a saída do `:8080`, não é migração — é conserto, e fica
  de fora. Uma tela que quebra **igual nos dois** não é problema nosso; uma que quebra **só no
  8.5** é, e a correção tem de ser a mínima que restaure a paridade.
- O ambiente PHP 5.6 existente (`docker-compose.yml`) é a referência funcional — **não alterá-lo**.
  Ambientes novos entram em arquivos separados (ex.: `docker-compose.php85.yml`).

## Ambientes (dois runtimes em paralelo)

| | Referência | Migração |
|---|---|---|
| Arquivo | `docker-compose.yml` (**não alterar**) | `docker-compose.php85.yml` |
| Imagem | `docker/php56-apache` | `docker/php85-apache` |
| PHP | 5.6 | **8.5.10** |
| URL | http://localhost:8080 | http://localhost:8085 |
| Banco | `ecidade_database` (PG 16 / LATIN1) | o **mesmo** `ecidade_database` |

O banco é compartilhado de propósito: mantém-se constante para que a única variável do
experimento seja a versão do PHP. Migrar PostgreSQL é a Fase 3, separada.

Extensões `interbase` e `xmlrpc` **não** foram instaladas (removidas do core do PHP em 7.4
e 8.0); as outras 15 exigidas pelo `composer.json` estão todas presentes.

### ARMADILHA (resolvida): uids no mesmo bind mount

Os dois containers montam o mesmo diretório. **Ambos rodam `www-data` como uid 33** — isso é
deliberado e precisa continuar assim: garante que a única variável entre os ambientes seja a
versão do PHP.

Houve uma tentativa de remapear o 8.5 para uid 1000 (para casar com o dono dos arquivos no
host). **Foi revertida**, porque criou duas quebras reais e enganosas:

1. Criar `extension/log/` pelo host (uid 1000) derrubou o **5.6** — o Logger lança exceção
   fatal quando não consegue escrever ali, e o :8080 passou a dar erro.
2. Depois, `application.log` criado pelo 5.6 (uid 33, modo 664) ficou ilegível para o 8.5
   (uid 1000), derrubando o :8085 numa tela do `tra` — sintoma que parecia falha de migração
   e era permissão de arquivo.

Requisito para as pastas de runtime:
```bash
chmod 777 extension/log && chmod 666 extension/log/*.log
```

### FERRAMENTAL: só `scratchpad/cmp.py` é versionado — o resto se perdeu

`scratchpad/` **não está no `.gitignore`, mas também nunca foi commitado**. Os scripts que
produziram os números deste arquivo — `incompat.py`, `depgraph.py`, `esforco.py`,
`afetados.txt` — **não existem mais em disco**. As medições continuam válidas (estão
registradas aqui), mas não são reproduzíveis sem reescrever as ferramentas.

O comparador de telas foi reescrito do zero **duas vezes** pelo mesmo motivo. Como as regras de
normalização dele *são* a metodologia acumulada — cada uma nasceu de um falso positivo real —
ele passou a ser versionado em **`scratchpad/cmp.py`**:

```bash
# restaura a sessao antes de cada requisicao e compara as duas portas
cd /home/diego/e-cidade
python3 scratchpad/cmp.py <SID> '^agua?[0-9]*_' divergentes.txt
ONLY="tela1.php,tela2.php" python3 scratchpad/cmp.py <SID> '^x_'   # subconjunto
```

Quem for regerar as outras ferramentas: commitá-las também.

### Estado: MÓDULO `jur` (Jurídico) PORTADO ✅ — 4º da área Tributário

**145 telas**, enumeradas por `^jur[0-9]*_` com `re.IGNORECASE`. O módulo tem **seis** variantes
de prefixo: `jur1_`…`jur4_`, mais `jur01_` (4 arquivos) e `jur_` (1). Universo total com as seis
frentes de enumeração: **315 arquivos**, dos quais 42 já pagos pelo núcleo e pelos portes
anteriores. **137 arquivos alterados.**

| Correção | Qtd |
|---|---|
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 517 |
| `split(` → `explode(` (padrão literal) | 239 |
| `parse_str()` com 2º argumento | 62 |
| construtor PHP4 → `__construct` | 60 |
| `ereg*(` → `preg_*(` | 31 |
| `each(` → `foreach` | 10 |
| `sizeof(null)` → `sizeof((array)…)` | 4 |
| guardas `pg_*` contra resultado falso | 3 |
| `split(` com padrão **regex** → `preg_split` / `explode("\|")` | 3 |
| `break` fora de laço removido | 1 |

Verificações: `php -l` **nos dois runtimes** em 137/137 alterados e em 315/315 do universo;
as **84 classes instanciam com estado idêntico**; **144 de 145 telas byte-a-byte idênticas**.

**Zero telas quebrando no 8.5** — o melhor resultado até aqui. A única divergência,
`jur_enviarremessatj.php`, **quebra no 5.6 (500) e funciona no 8.5 (200)**: o código pede
`db_app::load(... "pades.js")` e esse arquivo **não existe no repositório** (só
`scripts/pades-signer-sdk.min.js`). Defeito pré-existente da referência, mesma família de
`cem1_itenserv002` e das 4 telas do ITBI.

Roteamento: `jur` acrescentado ao nginx, e **`[0-9]?` virou `[0-9]*`** — com um dígito só,
as 4 telas `jur01_*` ficariam silenciosamente no 5.6. Mesma família da armadilha de maiúsculas.

### CATEGORIA NOVA (jur): `split()` com padrão REGEX, não literal

Nos três módulos anteriores **todos** os `split()` usavam separador literal (`"#"`, `","`), e a
conversão para `explode()` era mecânica. O `jur` tem três que **não** são:

```php
split(" +", $regs[2])    // POSIX: "um ou mais espacos"  -> preg_split("/ +/", ...)
split("\|", $funcao_js)  // POSIX: pipe escapado = literal -> explode("|", ...)
```

Comprovado no 5.6: `split(" +", "um   dois")` devolve `["um","dois"]`, e
`explode(" +", "um   dois")` devolve `["um   dois"]` — **a string inteira, sem separar**.
Trocar por `explode` aqui produziria dado errado em silêncio, sem erro nenhum.

**Regra:** antes de converter em massa, classificar o primeiro argumento. Se contiver
metacaractere de regex (`+ * ? [ ] ( ) | . ^ $ \`), vai para `preg_split`, não para `explode`.

### CATEGORIA NOVA (jur): `break` fora de laço ou `switch`

Era *warning* no PHP 5.6 e é **erro fatal de COMPILAÇÃO desde o PHP 7.0**.

```
jur1_emiteinicial002.php:114   Fatal error: 'break' not in the 'loop' or 'switch' context
```

Não aparece em varredura textual — só o `php -l` sob 8.5 a revela, como as categorias LSP e
`=& new`. Ali o `break` era **inalcançável** (a linha anterior chama `db_redireciona()`, que
termina em `exit` — `libs/db_stdlib.php:1545`), então removê-lo preserva a semântica exata.

### CATEGORIA NOVA (jur): `sizeof(null)`

No 5.6 era warning e devolvia 0; no PHP 8 é `TypeError: must be of type Countable|array`.
Ocorre quando o array só é atribuído dentro de um `if` que não entrou:

```php
if (isset($dadosini) && $dadosini != "") { $matriz = explode("xx", $dadosini); }
for ($q = 0; $q < sizeof($matriz); $q++) {      // $matriz indefinida -> null
```

Correção: `sizeof((array)$matriz)`. Reproduz o 5.6 nos três casos — `(array)null` = `[]` (0),
`(array)"x"` = `["x"]` (1, que era o que `sizeof` de escalar devolvia), e array continua igual.

### LACUNA DE DETECÇÃO (jur): `parse_str` com chamada aninhada

Duas telas continuaram fatais depois do porte:

```php
parse_str(base64_decode($HTTP_SERVER_VARS['QUERY_STRING']));
```

O regex de detecção era `parse_str\s*\(\s*[^,()]+\)` — o `[^,()]` **não casa com parênteses
internos**, então a chamada aninhada nunca foi detectada, os arquivos não entraram na lista de
alvos, e a transformação nem rodou neles.

**É a mesma falha de método das seis lacunas de enumeração:** agir sobre a lista que a própria
detecção produziu. A detecção correta conta vírgulas **no nível superior**, percorrendo os
parênteses com contador de profundidade.

### ARMADILHA DE FERRAMENTAL: `serialize()` de objeto interno é fatal no PHP 8

O harness que compara o estado das classes usava `md5(serialize($props))`. Três classes do `jur`
guardam um `DOMElement`, e **serializá-lo é fatal no PHP 8** (o 5.6 permitia):

```
Exception: Serialization of 'DOMElement' is not allowed
```

O sintoma foi um falso positivo: três classes "com erro" que instanciam perfeitamente quando
testadas isoladamente. **Era o instrumento que quebrava, não o código medido.** A assinatura
passou a descrever objetos pelo nome da classe em vez de serializá-los
(`scratchpad/instancia_classes.php`).

### Estado: MÓDULO `div` (Dívida Ativa) PORTADO ✅ — 5º da área Tributário

**148 telas** (`^div[0-9]*_`, sem variante de letra). Universo pelas seis frentes: **392
arquivos**, 90 já pagos. **158 alterados.**

| Correção | Qtd |
|---|---|
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 752 + 11 no núcleo |
| `split(` → `explode(` (todos literais) | 381 |
| construtor PHP4 → `__construct` | 80 |
| `parse_str()` com 2º argumento | 62 |
| guardas `pg_*` contra resultado falso | 9 |
| offsets `{}` → `[]` | 2 |
| cast `(int)` em aritmética com string | 1 |
| `date()` com timestamp string → `(int)` | 1 |

**148 de 148 telas byte-a-byte idênticas — o primeiro módulo sem nenhuma divergência.**
As 84+150 classes instanciam com estado idêntico; `php -l` limpo nos dois runtimes em
158/158 alterados e 391/391 do universo.

### ⚠ ACHADO GRAVE: o núcleo `db_cgm_classe.php` estava sem as guardas `0 == ""`

Descoberto pela verificação de remanescentes do `div`: **12 arquivos já tocados por commits
`Porta ...` ainda tinham o idioma perigoso sem guarda — 52 ocorrências.**

| Arquivo | Ocorrências |
|---|---|
| `classes/db_acidentes_classe.php` e mais 10 do `tra` | 42 |
| **`classes/db_cgm_classe.php` — NÚCLEO** | **10** |

Causa: o `tra` e o núcleo foram portados **antes** de a categoria `0 == ""` ser descoberta
(ela apareceu no Cemitério). O `CLAUDE.md` registra `db_cgm_classe.php` apenas sob
"construtor PHP4 → `__construct`" — as comparações nunca foram tratadas.

Gravidade: `db_cgm_classe.php` é o registro de cidadãos, **puxado por qualquer módulo com
pessoas**. O idioma afetado é exatamente o que quebrou o formulário do Cemitério:

```php
$this->z01_numcgm = ($this->z01_numcgm == "" ? @$GLOBALS["HTTP_POST_VARS"]["z01_numcgm"] : ...);
```

**Corrigido** (11 comparações). As 42 do `tra` ficam registradas e **não corrigidas**: o
módulo é órfão no menu, nenhuma tela leva até ele.

**Por que nenhuma bateria pegou isso:** o comparador faz só `GET`, e este idioma só dispara
no `POST`. É o mesmo limite que a dúvida sobre a inclusão de advogados expôs.

### CATEGORIA NOVA (div): `date()` com timestamp em string

```
                     date("Y-m-d", "2024-01-01")
PHP 5.6:             "1969-12-31"   (coage para int)
PHP 8.5:             TypeError: Argument #2 ($timestamp) must be of type ?int
```

Em `libs/db_stdlib.php:1503` (`db_vencimento()`, núcleo). Correção: `date("Y-m-d", (int)$dt)`,
que reproduz o 5.6 **exatamente** — inclusive o resultado sem sentido `1969-12-31`, que é
comportamento pré-existente e não cabe à migração corrigir.

### `(int)` vs `(float)` em aritmética com string

O catálogo registra `(float)` como correção da aritmética com string, escolhida num contexto
monetário. Em `classes/db_divida_classe.php:2373` o valor é um **exercício** (ano) vindo de
`explode("-", ...)`, e ali `(int)` é estritamente mais fiel: o 5.6 devolve `int` para
`"2024" - 1`, e `(float)` preservaria o valor mas mudaria o tipo.

**Regra:** casar o cast com o tipo que o 5.6 produzia naquele ponto, não aplicar `(float)` por
hábito.

### LACUNA DE DETECÇÃO (div): offset `{}` sobre PROPRIEDADE

Meu regex de offset cobria `$v{...}` e `$v[...]{...}`, mas **não `$v->prop{...}`**:

```php
if ($aDebitos[$i]->origem{0} == 'M')      // model/cda.model.php:1226
```

Escapou da varredura e só o `php -l` do 8.5 pegou. O regex do `enumera.py` foi corrigido para
cobrir as quatro formas.

### FERRAMENTAL versionado (`scratchpad/`)

Depois de reescrever as mesmas rotinas em cada módulo — e de perder duas vezes o comparador —
os quatro instrumentos passaram a ser versionados:

| Arquivo | Passos da receita |
|---|---|
| `enumera.py` | 1–3: universo pelas seis frentes + inventário + lista de alvos |
| ~~`porta.py`~~ → `rector-curado.php` + `rector-rules/` | 4: transformações mecânicas. O `porta.py` fica como referência e para comparar resultados; a partir do `iss` quem aplica é o Rector. |
| `instancia_classes.php` | 6: estado das classes nos dois runtimes |
| `cmp.py` | 7: comparação das telas |

`porta.py` **usa a mesma detecção de `enumera.py`** — em especial a de `parse_str`, que conta
vírgulas no nível superior. Foi a divergência entre as duas que deixou duas telas do `jur`
fatais depois do porte. E ele **aborta** diante de caso que exige decisão humana (separador de
`split()` com metacaractere, arquivo com mais de uma classe), em vez de transformar errado.

### Estado: MÓDULO `mar` (Marcas e Sinais) PORTADO ✅ — 6º da área Tributário

**35 telas** (`^mar[0-9]*_`, variantes `mar1_`…`mar4_`, sem sufixo de letra). Universo pelas
seis frentes: **77 arquivos**, 24 já pagos. **19 alterados.**

Módulo de registro de marcas de gado. **17 de 17 itens de menu ligados** — módulo próprio e
inteiramente demonstrável:

```
Marcas e Sinais > Cadastros     > Localidades (Inclusão/Alteração/Exclusão)
                > Procedimentos > Cadastro de Marcas · Cancelamento · Transferência
                > Consultas     > Consulta Marcas · Cancelamentos · Transferências
                > Relatórios    > Marcas por Proprietário · Histórico de Cancelamentos
```

| Correção | Qtd |
|---|---|
| `$this->X == <literal>` → forma que preserva a semântica do 5.6 | 27 |
| `split(` → `explode(` (todos com separador literal `"#"`) | 20 |
| `parse_str()` com 2º argumento | 14 |
| construtor PHP4 → `__construct` | 5 |

Nenhuma categoria nova. Zero `each(`, `ereg*`, offsets `{}`, `=& new`, cast `(real)`.

Verificações — **primeira vez com a receita completa, incluindo o passo 6b**:

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 35 = 35 ✅ |
| 3. classificação dos `split` | 20 literais, 0 regex, 0 dentro de `<script>` |
| 5. `php -l` nos dois runtimes | 19/19 alterados e 76/76 do universo, 0 erros |
| 6. instanciação das classes | 14/14, estado idêntico |
| **6b. caminho de escrita** | **545 linhas, byte-a-byte idênticas** |
| 7. bateria de telas | **35/35 idênticas, 0 divergentes**, 0 fatais no log |

**Segundo módulo sem nenhuma divergência**, depois do `div`.

#### Armadilha de verificação que reapareceu (terceira vez)

O harness do passo 6b produziu 858 linhas e meu `diff` disse "0 divergentes". Antes de aceitar,
conferi se **havia saída** — havia. Mas um segundo teste (`grep $'\t'`) contou **zero linhas
bem formadas**, o que sugeria lixo. Era o `grep` que falhava por aspas no shell: medindo em
Python, são **545 linhas bem formadas cobrindo as 14 classes, byte-a-byte idênticas**.

Lição: **o instrumento de conferência também precisa ser conferido.** Duas verificações
discordando é sinal de que uma delas está quebrada — não de que o dado está ruim.

### Estado: MÓDULO `not` (Notificações) PORTADO ✅ — 7º da área Tributário

**14 telas** (`^not[0-9]*_`, variantes `not1_`/`not2_`/`not4_`). Universo pelas seis frentes:
**92 arquivos**, 47 já pagos. **17 alterados.**

Módulo próprio, **7 de 7 itens de menu ligados**:

```
Notificações > Procedimentos > Notificações por Edital · Parâmetros · Documento da Lista
             > Relatórios    > Emissão de Notificações (TXT Correios / Layout / Geral)
                             > Situação da Notificação
```

| Correção | Qtd |
|---|---|
| `$this->X == <literal>` → forma que preserva a semântica do 5.6 | 60 |
| `split(` → `explode(` (43 com `"#"`, 1 com `" "`) | 44 |
| construtor PHP4 → `__construct` | 11 |
| `parse_str()` com 2º argumento | 6 |

Nenhuma categoria nova.

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 14 = 14 ✅ |
| 3. classificação dos `split` | 44 literais, 0 regex, 0 em `<script>` |
| 5. `php -l` nos dois runtimes | 17/17 alterados e 91/91 do universo, 0 erros |
| 6. instanciação das classes | 40/40, estado idêntico |
| 6b. caminho de escrita | 1.111 linhas, byte-a-byte idênticas |
| 7. bateria de telas | **14/14 idênticas, 0 divergentes**, 0 fatais |

**Terceiro módulo sem nenhuma divergência**, depois de `div` e `mar`.

Dois detalhes verificados em vez de deduzidos, ambos na categoria onde o erro é silencioso:

- **`split(" ", ...)` com espaço único é literal**, não regex — confirmado no próprio 5.6:
  `split(" ","um  dois")` e `explode(" ","um  dois")` devolvem o mesmo array, inclusive o
  elemento vazio do espaço duplo. (Diferente de `split(" +", ...)` do `jur`, que é regex.)
- **O harness de escrita cobriu 39 das 40 classes.** A ausente,
  `classes/db_assinatura_classe.php`, tem **zero propriedades declaradas e nenhum
  `atualizacampos()`** — não é classe de dados, não há caminho de escrita a exercitar.

### Estado: MÓDULO `fis` (Fiscal) PORTADO ✅ — 8º da área Tributário

**353 telas** (`^fis[0-9]*_`, variantes `fis1_`…`fis4_`, sem sufixo de letra e sem maiúsculas).
Universo pelas seis frentes: **682** arquivos — e **699 depois de fechar a 7ª lacuna**, abaixo.
**384 arquivos alterados**, o maior lote do projeto (o anterior era `agu`, 171).

| Correção | Qtd |
|---|---|
| `$this->X == <literal>` → forma que preserva a semântica do 5.6 | 730 |
| `split(` → `explode(` (todos literais: 519 `#`, 16 `-`, 4 `HHH`, 3 `/`, 2 `_sep_`, 2 `,`, 2 `\n`, 1 ` `) | 627 |
| `parse_str()` com 2º argumento | 230 |
| construtor PHP4 → `__construct` | 134 |
| guardas `pg_*` contra resultado falso | 15 |
| casts `(int)`/`(float)` em aritmética e comparação com string | 3 |
| `is_resource()` → `is_resource() \|\| is_object()` (**núcleo**, ver categoria nova) | 2 |
| `break` fora de laço → `exit` | 2 |
| `eregi(` → `preg_match(` | 1 |

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 353 = 353 ✅ |
| 3. classificação dos `split` | 553 em PHP (todos literais), 8 em JavaScript preservados |
| 5. `php -l` nos dois runtimes | **699/699 do universo, 0 erros** em 5.6 e 8.5 |
| 6. instanciação das classes | **205/205, estado idêntico** |
| 6b. caminho de escrita | 4.299 linhas, 204 de 205 classes, **0 divergentes** |
| 7. bateria de telas | **350/353 idênticas** |
| 8. roteamento | `/fis1_*`, `/w/2/fis1_*` e `/Fis1_*` pelo 8.5; `/login.php` pelo 5.6 |

**Zero telas quebrando só no 8.5.** As 3 divergências restantes são defeitos pré-existentes, e
**nenhuma é item de menu** (o módulo tem 109 de 114 itens ligados):

- `fis1_sanitario004.php` — **não tem nenhum `include`**; usa `db_ancora()` e `rotulo->label()`
  sem carregar nada. Quebra nos dois (5.6: `Call to undefined function db_ancora()`; 8.5:
  `No PostgreSQL connection opened yet`, que é o mesmo defeito alcançado mais cedo).
- `fis1_tiafprazoproc002/003.php` — `forms/db_frmtiafprazoproc.php:30` usa `$cltiafprazo`, que
  **não é instanciado em lugar nenhum da cadeia**. O 5.6 renderiza a página de erro (500) e o
  8.5 para antes (200 truncado). Tela quebrada nos dois.

#### Decisão medida: NÃO usar Rector neste módulo

O `CLAUDE.md` registrava que o Rector "vale a pena a partir de `fis` (353) e `iss` (400)". A
recomendação era condicional ao volume; medida **neste** módulo, as duas vantagens concretas que
ele teve no experimento do `div` **não se aplicam**:

| Vantagem do Rector | No `div` | No `fis` |
|---|---|---|
| pega offset `->prop{}` que o regex não cobre | 1 (real) | **0 ocorrências** |
| não edita código comentado | 2 | **1 ocorrência** |

Trocar de instrumento custaria revalidar a *denylist* de 14 regras contra uma população de
arquivos nova e repetir o portão de funções ausentes (`str_starts_with`, `random_int`), sem
cobertura adicional. A recomendação segue de pé para `iss`, mas **tem de ser remedida lá** — o
critério é a presença das construções que o regex erra, não a contagem de telas.

### CATEGORIA NOVA (fis): `is_resource()` sobre resultado do PostgreSQL — NÚCLEO, FALHA SILENCIOSA

A mais grave desde o `0 == ""`, e da mesma família: **o código é válido nas duas versões, não
emite erro, e some com um campo da tela.**

```
                      pg_query(...) devolve
PHP 5.6:              resource    -> is_resource() = true
PHP 8.5:              object      -> is_resource() = FALSE   (PgSql\Result desde o PHP 8.1)
```

Comprovado nos dois runtimes:

```
ecidade_php56   tipo=resource   is_resource=true    is_object=false
ecidade_php85   tipo=object     is_resource=false   is_object=true
```

Onde dói: `dbforms/db_funcoes.php`, função **`db_selectrecord()`** do núcleo. Em modo leitura
(`$db_opcao = 3`) ela emite **dois** inputs — o código e a descrição —, e o segundo só é emitido
se o laço guardado por `is_resource($record)` encontrar a linha correspondente:

```php
if (is_resource($record)) {                     // no 8.5: FALSE, laco nunca roda
    for ($sqli = 0; $sqli < pg_numrows($record); $sqli++) { ... $nomec = pg_fieldname($record,1); }
}
if (!empty($nomec)) { db_input($nomec, ...); }  // no 8.5: $nomec vazio -> campo NAO sai
```

Sintoma observado em `fis1_aidof002/003` e `fis4_aidof005`: HTTP 200 nos dois runtimes, página
renderizando normalmente, e **437 bytes a menos no 8.5** — o input `q09_descr` com valor
`MODELO 1` simplesmente ausente. Nenhum fatal, nenhuma entrada no log.

**Correção: `is_resource($record) || is_object($record)`** — verdadeira nos dois runtimes.
Aplicada no original **e na cópia de `extension/modification/`**, que é a que executa para o
usuário `dbseller`.

Escala na base: **237 ocorrências de `is_resource` em 86 arquivos**. Nem todas são resultado de
PostgreSQL — *handles* de arquivo continuam sendo resource no PHP 8 —, então a varredura exige
classificar o argumento. Fica registrado como estimativa, não como lista de tarefas, seguindo a
mesma decisão tomada para as guardas `pg_*`.

**Por que nenhuma verificação anterior pegou:** `php -l` não vê, o harness de classes não vê (é
código de tela, não de classe), e o harness de escrita não vê (não passa por `atualizacampos()`).
**Só a comparação byte-a-byte entre runtimes encontra** — é o argumento mais forte do projeto a
favor de manter o 5.6 vivo como referência.

### CATEGORIA NOVA (fis): a RFC das comparações também muda `>` dentro do FPDF

Já estava catalogado que a RFC "Saner string to number comparisons" mudou `==` e os operadores
de ordem (o laço infinito do `agu`). Esta é a terceira manifestação, e atinge **o FPDF do
núcleo**, alterando o layout dos relatórios em silêncio.

A assinatura do FPDF é `Cell($w, $h, $txt, $border, $ln, $align, $fill, $link)`. O e-cidade
chama, em `fis3_relatoriosani.php:66`:

```php
$pdf->Cell(90, 6, $RLz01_cgccpf.': '.@$z01_cgccpf, 1, "J", 1, 30);
                                                      ^^^ isto cai em $ln
```

E dentro de `fpdf151/fpdf.php` (linhas 1001 e 2950):

```
              "J" > 0
PHP 5.6:      false      ("J" vira numero: 0 > 0)
PHP 8.5:      TRUE       (0 vira string: "J" > "0")
```

No 8.5 o `Cell` avança uma linha que não deveria avançar. O efeito no PDF gerado:

```
5.6:  Logradouro(y=680.32)  Numero(311.81, 680.32)  Complemento(411.03, 680.32)   <- mesma linha
8.5:  Logradouro(y=663.31)  Numero(311.81, 663.31)  Complemento(311.81, 646.30)   <- quebrou
```

O relatório inteiro desce e um campo muda de coluna. **HTTP 200 nos dois, PDF válido nos dois,
conteúdo diferente** — e o texto está dentro do fluxo `FlateDecode`, invisível a qualquer regex
de normalização. Só descomprimindo o stream dá para ver.

**Correção: `if((float)$ln>0)`** nas duas ocorrências — `(float)"J" > 0` é `false` nos dois
runtimes, reproduzindo o 5.6 exatamente. Passar a `"J"` como `$ln` é defeito pré-existente da
chamada; corrigi-lo mudaria o layout do 5.6, então **não foi tocado**.

### 7ª LACUNA: `db_utils::getDao('x')` instancia classes que nenhuma frente enxergava

A 4ª lacuna acrescentou a resolução de `new cl_*` para cobrir o autoload. Mas o e-cidade tem um
**segundo idioma de instanciação**, que não cita o nome da classe em lugar nenhum:

```php
$clcadtipo = db_utils::getDao('cadtipo');     // carrega classes/db_cadtipo_classe.php
$clcadtipo->rotulo->label();                  // no 8.5: label() on null
```

Como o construtor PHP 4 de `cl_cadtipo` é quem faz `$this->rotulo = new rotulo("cadtipo")`, a
classe não portada deixa `rotulo` em `null` e a tela morre.

Medido no `fis`: **61 DAOs distintos citados por `getDao()`, 16 classes fora do universo, 14
delas com construtor PHP 4** — ou seja, 14 classes que quebrariam em silêncio. O universo foi
de **682 para 699** arquivos e saíram mais 74 `split`, 72 guardas e 15 construtores.

`enumera.py` passou a resolver os dois idiomas na mesma frente.

**É a sétima vez que a mesma falha de método aparece:** a verificação partia da lista que a
própria enumeração gerou. Vale repetir o contraste — as sete lacunas foram encontradas por
*navegação* ou por *comparação de saída*, nunca pelas varreduras.

### LACUNA DE DETECÇÃO: o detector de `0 == ""` casa com a PRÓPRIA correção

O `enumera.py` procura `$this->X == "<literal>"` sobre propriedade inteira. A guarda que ele
mesmo manda aplicar é:

```php
($this->X === 0 || $this->X === 0.0 || $this->X == "")
                                       ^^^^^^^^^^^^^^ o detector casa aqui
```

Logo **essa categoria nunca pode reportar zero**, e "0 remanescentes" era impossível de obter
por ali. A conferência correta conta as ocorrências **sem guarda** — olhando os 120 bytes
anteriores atrás do prefixo `$this->X === 0 || $this->X === 0.0 || `.

Rodando o detector correto na base inteira: **21.019 ocorrências em 3.565 arquivos** (consistente
com as 19.401 registradas, maior porque agora inclui literais não-numéricos). Cruzando com os
746 arquivos já tocados por commits `Porta `, sobram **12** — os 11 do `tra` (órfão, registrados
como não corrigidos) e `classes/db_db_usuarios_classe.php`, que é **falso positivo**: ali a
comparação é `$this->liberalotacao == null || $this->liberalotacao == ''`, e `0 == null` é `true`
nos **dois** runtimes, então o curto-circuito já cobre o caso.

Ou seja: nenhum módulo portado tem buraco nessa categoria. Mas isso só se soube agora, porque o
instrumento não sabia medir o próprio resultado.

### CORREÇÃO ao catálogo: `break` fora de laço é fatal de EXECUÇÃO no 5.6, não warning

A seção do `jur` registra que `break` fora de laço "era *warning* no PHP 5.6". **Está errado** —
medido no próprio runtime:

```
PHP 5.6:  php -l  -> No syntax errors detected
          execucao -> Fatal error: Cannot break/continue 1 level
PHP 8.5:  php -l  -> Fatal error na COMPILACAO (arquivo inteiro nao carrega)
```

A diferença prática é grande: no 5.6 a tela funciona até alcançar aquela linha; no 8.5 ela não
carrega nunca. E muda a correção. No `jur` o `break` era inalcançável (a linha anterior chamava
`db_redireciona()`, que termina em `exit`), então removê-lo era exatamente equivalente.

Em `fis1_vistorias003.php:171` e `:179` ele **é alcançável** — são dois dos seis blocos de erro
idênticos da mesma função, e os outros quatro não têm `break` (é cópia dos dois que estão dentro
de `for`). Como o 5.6 morre ali sem chegar ao `db_fim_transacao($sqlerro)`, a correção fiel é
**`exit;`**, que reproduz esse fluxo nos dois runtimes (ambos terminam em rollback). Remover o
`break` faria o 8.5 seguir e tratar o erro normalmente — é conserto do defeito, não migração.

### ARMADILHA OPERACIONAL: `chmod 777 extension/log` não basta — os ARQUIVOS também

Sintoma: **toda** tela autenticada devolve `HTTP 500` com corpo vazio, nos dois runtimes, e
`login.php` continua respondendo 200. Parece defeito grave de migração; é permissão.

```
extension/log            drwxrwxrwx diego:diego   <- a pasta estava certa
extension/log/error.log  -rw-rw-r-- diego:diego   <- o ARQUIVO nao, e o container e uid 33
```

O Logger lança exceção fatal quando não consegue escrever, antes de qualquer saída. A receita de
subida já trazia `chmod 777 extension/log`; faltava `chmod 666 extension/log/*.log`, que a seção
de uids documentava mas o bloco de comandos não repetia. Acrescentado lá.

Diagnóstico que resolve em um passo: requisitar uma tela de **módulo já verificado** (`cem`,
`not`). Se ela também der 500, o problema é de ambiente, não do porte em andamento.

### Estado: BIBLIOTECA `dbagata/` PORTADA ✅ — pré-requisito do `iss` pago

`dbagata/` tem **602 arquivos**, dos quais **216 são PHP executável** (`.php`, `.class`, `.inc`).
Os outros são dados do Agata: 104 `.agl`, 73 `.agt`, 50 `.htm`, 25 `.rpt`, 15 `.map`, 10 `.lay`
e **74 `.fun`**. Os `.fun` *são* PHP, mas só `AgataInterface.class` — a GUI GTK que nada no
repositório inclui — os carrega; o caminho de relatório não os toca. Ficam registrados (3
`ereg*` em 3 arquivos) e não foram portados.

**5 dos 216 já não parseavam no 5.6** (`pdw_document.php` ×2 do phpdocwriter, `FileBox.class`,
`GtkPopDate.class`, `createwidgets.inc` — todos GTK/doc). Não dá para verificá-los por lint, e
são pré-existentes: ficaram de fora. **Universo portado: 211 arquivos.**

| Correção | Qtd |
|---|---|
| construtor PHP4 → `__construct` | 213 classes |
| `ereg*(` → `preg_match`/`preg_replace`/`str_replace` | 61 |
| offsets `{}` → `[]` | 16 |
| `=& new` → `= new` | 14 |
| `is_resource()` → `is_resource() \|\| is_object()` | 13 |
| chamadas ao construtor antigo (`parent::`, `$this->`, `Classe::Classe(`) | 10 + 62 |
| `split(` → `explode(`/`preg_split(` | 9 |
| assinaturas incompatíveis com a mãe (LSP) | 5 |
| `each(` → ponteiro explícito | 5 |
| `set/get_magic_quotes_runtime()` removidos | 5 |
| `array_merge()` com argumento nulo | 2 |
| `create_function(` → *closure* | 1 |

#### Verificação

| Critério | Antes | Depois |
|---|---|---|
| `php -l` no 5.6 | 0 erros (nos 211) | **0** |
| `php -l` no 8.5 | **11 erros** | **0** |
| `testeagata.php` (pipeline real de relatório) | 5.6 gera PDF, 8.5 dá 500 | **PDF byte-a-byte IDÊNTICO** |
| leitura de `.odt` por pclzip + caminho `BY_EREG` | — | **idêntico nos dois** |

E o ganho que prova o porte: a bateria do Cemitério foi de **114/116 para 115/116**.
`cem2_emitecertisen002.php` — a tela que este arquivo atribuía, desde o piloto, ao "diálogo de
erro do `dbagata/`, cujos construtores PHP 4 não rodam no 8.5" — **ficou idêntica**. Era
exatamente esse o defeito.

As demais sete baterias ficaram **iguais à linha de base** (itb 116/120, agu 222/224, jur
144/145, div 148/148, mar 35/35, not 14/14, fis 350/353): zero regressão a partir das mudanças
no núcleo. Das 1.155 telas dos oito módulos, **11 divergem e nenhuma quebra só no 8.5**.

#### O que ficou deliberadamente intocado

- **`nusoap.php:1731`** — `is_resource($this->fp)` com handle de `fsockopen()`. Diferente dos
  13 de driver de banco: `fsockopen` **continua devolvendo resource** no PHP 8. Mexer ali seria
  mudança sem motivo.
- **`GtkFrame::GtkFrame()`, `GtkButton::GtkButton()`, `GtkCList::GtkCList()`** e afins — são
  classes da extensão GTK, externas, cujos construtores eu não renomeei.
- **Mensagens de erro e comentários** que citam `Graph::Graph()` / `Text::Text()` em
  `jpgraph/lang/{en,de}.inc.php` e `jpgraph.php:2815`.
- As 6 ocorrências de `"\$subfield{$i}_sum"` em `AgataOOParser.class` e `AgataInterface.class`:
  **não são offsets, são interpolação** dentro de string de aspas duplas. Distinguem-se pela
  barra invertida antes do `$`.

### ⚠ 8ª LACUNA: a checagem de `__construct` era por ARQUIVO, e mascarava classes vizinhas

A mais cara até agora, porque **sobreviveu a oito portes** e vive no núcleo.

```python
has5 = re.search(rb'function\s+__construct\s*\(', b)   # <- arquivo INTEIRO
for m in re.finditer(rb'\bclass\s+(\w+)', b):
    if ... and not has5:                                 # <- mascara TODAS as classes
```

Num arquivo com várias classes, **uma** delas com `__construct` fazia o detector ignorar todas
as outras. O mesmo regex ainda contava como construtor um **método homônimo de outra classe**,
por buscar no arquivo inteiro — falso positivo na direção oposta.

Impacto medido na base, com detecção por classe: **42 classes em 5 arquivos, todos já dados
como portados**.

| Arquivo | Classes escondidas |
|---|---|
| `libs/jpgraph/jpgraph.php` | 33 |
| **`libs/db_stdlib.php` — NÚCLEO** | **3** (`cl_download`, `cl_verificaboletim`, `cl_abre_arquivo`) |
| `extension/modification/.../libs/db_stdlib.php` | 3 (a cópia que executa) |
| **`libs/JSON.php` — NÚCLEO** | **2** (`Services_JSON`, `Services_JSON_Error`) |
| `libs/jpgraph/jpgraph_line.php` | 1 |

Comprovado no runtime, com o bootstrap da aplicação:

```
PHP 5.6   cl_download->arquivo = 'rp4576_1791136974'   construtor rodou? SIM
PHP 8.5   cl_download->arquivo = NULL                  construtor rodou? NAO
```

`cl_download` é do núcleo e monta o nome do arquivo temporário de download. No 8.5 ele ficava
**nulo**. Corrigido nos 5 arquivos; `enumera.py` e `porta.py` passaram a fatiar o arquivo em
blocos de classe antes de decidir.

### CATEGORIA NOVA (dbagata): a terceira forma de chamar o construtor antigo

Renomear `function Classe()` para `__construct` quebra quem chamava pelo nome antigo. Já estavam
tratadas `parent::Classe(` e `$this->Classe(`. Faltava a **chamada estática**:

```php
class MyPdf extends FPDF {
    function __construct($o,$u,$f) {
        FPDF::FPDF($o,$u,$f);        // <- vira "Call to undefined method FPDF::FPDF()"
```

Correção: `Classe::Classe(` → `Classe::__construct(`, que preserva a semântica exata (chamada
do método da mãe no contexto do objeto) e funciona nos dois runtimes.

**Duas armadilhas na varredura dessa forma**, ambas encontradas na prática:

1. **Só vale para classes que EU renomeei.** `GtkFrame::GtkFrame()` é a extensão GTK, externa;
   converter quebraria. A lista de alvos tem de sair das classes que agora têm `__construct`
   nos arquivos alterados, não de um regex genérico `(\w+)::\1\(`.
2. **Comentário e string contam como ocorrência.** `jpgraph/lang/en.inc.php` traz
   `'Image width/height argument in Graph::Graph() must be numeric'` numa tabela de mensagens,
   e `jpgraph.php:2815` cita `Text::Text()` dentro de `//`. São 4 das 17 ocorrências.

**Como foi descoberta:** não pela varredura, e sim **exercitando o pipeline real** — o
`testeagata.php` passou a dar 500 no 8.5 *depois* do porte. É a mesma lição das oito lacunas,
com um agravante: aqui a varredura de remanescentes dizia "0" porque eu derivava a lista de
nomes do lugar errado.

### CATEGORIA NOVA (dbagata): `array_merge()` com argumento nulo, e o `@` que não suprime mais

```
                        @array_merge($a, null)
PHP 5.6:                NULL   (warning, suprimido pelo @)
PHP 8.5:                TypeError FATAL   -- o @ NAO suprime TypeError
```

Em `dbagata/classes/reports/AgataReport.class`, linhas 214 e 281. Era o que impedia o
`testeagata.php` de gerar relatório no 8.5.

Correção fiel, que reproduz o 5.6 **inclusive no resultado `NULL`**:

```php
$ClearColumns = (is_array($ClearColumns) && is_array($columns))
              ? array_merge($ClearColumns, $columns) : null;
```

**O ponto que generaliza:** o operador `@` deixou de ser rede de segurança no PHP 8 para toda
construção que passou de *warning* a `TypeError`/`ValueError`. Código legado que usa `@` para
"deixar passar" argumento inválido **falha mesmo com o `@`**. Vale para `array_merge`,
`pg_*`, `date()`, `sizeof()` e todas as outras já catalogadas aqui.

### Estado: MÓDULO `iss` (ISSQN) PORTADO ✅ — 9º da área Tributário, e o 1º feito com Rector

**400 telas** (`^iss[0-9]*_`). O módulo tem **oito** variantes de prefixo: `iss1_`…`iss4_`, mais
`iss01_`, `iss03_`, `iss04_` e **`iss179_`** — esta última derrubaria um `[0-9]?` no nginx, mesma
armadilha do `jur01_`. Universo pelas sete frentes: **819 arquivos**, **280 alterados**.

| Correção | Qtd |
|---|---|
| guarda `$this->X == <literal>` | 711 |
| `split(`/`ereg*(` → `preg_*` | 538 |
| construtor PHP4 → `__construct` | 127 |
| `parse_str()` + `extract()` | 116 |
| guardas `pg_*` contra resultado falso | 26 |
| guardas de divisão por zero | 5 |
| `reset()`/`sizeof()`/`rsort()` sobre null | 5 |
| teste `$txt!=''` do `Cell()` do FPDF | 2 |
| `sprintf('%.f')` → `'%.6f'` | 1 |
| construtor com argumento faltando | 1 |

Mais **6.480 linhas de modernização** que o Rector trouxe junto e que **não** são exigidas pela
versão de destino: 2.973 renomeando alias `pg_*`, 2.432 `var $x` → `public $x`, 1.075
acrescentando `public` a método. Ver a ressalva no fim desta seção.

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 400 = 400 ✅ |
| 5. `php -l` nos dois runtimes | 280/280 alterados, 0 erros em 5.6 e 8.5 |
| portão de funções contra o 5.6 | 0 ausentes |
| 7. bateria de telas | **397/400** (371 → 393 → 395 → 396 → 397) |
| 8. roteamento | `iss1_`, `iss01_`, `iss179_` e `/w/2/iss1_` pelo 8.5 |
| regressão nos 8 módulos anteriores | **zero** — todos na linha de base |

As 3 divergências restantes são bugs **pré-existentes** e ficam como estão, pelo princípio
registrado em *Princípios*:

- `iss1_tabalvara_depto001.php` — `$cltabdesc` é usado na linha 43 e **nunca atribuído** no
  arquivo. Até o PHP 7 isso criava um `stdClass` automaticamente; o 8.0 transformou em `Error`.
- `iss4_issbasecaracteristicas001.php` — `$oGrupo` nulo, mesma família.
- `iss3_emissaoalvaraeventos001.php` — `pg_lo_export($oid, $file, $conn)`, com os argumentos na
  ordem errada. A assinatura é `($connection, $oid, $filename)` **nos dois runtimes**; o 5.6
  tolerava.

### ⚠ DECISÃO: Rector adotado como instrumento do passo 4, a partir do `iss`

O experimento do `div` havia concluído "híbrido: Rector na camada sintática, ferramental próprio
na semântica", e eu medi duas vezes (`fis`, `iss`) que a vantagem da AST era pequena demais para
pagar a troca. **O que mudou a conta foi escrever as duas regras que faltavam.**

`scratchpad/rector-rules/` — 196 linhas, contra 150 do `porta.py` inteiro:

| Regra própria | Linhas | Cobre |
|---|---|---|
| `GuardaComparacaoLiteralRector` | 122 | `$this->X == "<literal>"` → guarda do 5.6 |
| `ParseStrComExtractRector` | 74 | `parse_str` de 1 arg + `extract()` |

Com elas, o Rector faz **100% do porte**. Acordo medido contra o `porta.py`, a partir do mesmo
ponto de partida: **246 de 248 arquivos semanticamente idênticos**, e nos 2 em que divergem **o
Rector está certo** — o `porta.py` editou um `parse_str` que estava dentro de comentário.

Onde a AST ganha do regex, medido e não suposto:

- **comentário**: o regex não distingue código de comentário; a AST sim
- **precedência**: o printer põe parênteses só onde muda o sentido —
  `($this->a === 0 || … ) && $o` leva, `… ? 1 : 2` não leva. O `porta.py` parentiza sempre.

#### Os cinco modos de falha silenciosa que a adoção custou

Nenhum deles aparece em varredura; todos foram achados por verificação cruzada.

1. **O Rector desliga regras em silêncio.** Sem `->withPhpVersion()`, ele resolve a versão alvo
   do `composer.json` do projeto (`">=5.6.4"`) e pula toda regra com *version bonding* —
   `Php4ConstructorRector` (122 arquivos) e `EregToPregMatchRector` (118) entre elas — relatando
   `[OK] N files changed` sem aviso nenhum. **O pin é obrigatório.**
2. **Denylist não é transferível entre módulos.** `StrContainsRector` e `ArrayKeyFirstLastRector`
   nunca dispararam no `div` e dispararam no `iss`, emitindo `str_contains()` (PHP 8.0) e
   `array_key_first()` (PHP 7.3) em arquivos servidos pelo runtime **5.6**. Passam no `php -l`.
   A denylist foi de 14 para 16 regras — e tem de ser reconferida a cada módulo.
3. **O Rector não converge numa passada, e isso é intermitente.** Rodando o mesmo comando sobre
   os mesmos alvos: 163 arquivos, depois mais 83, depois 0. Noutra execução, 246 e depois 0.
   **Repetir até dar zero** é obrigatório; um run não prova nada.
4. **Regra própria que devolve nó contendo o original entra em laço infinito.** O PhpParser
   percorre os filhos do substituto, e o substituto não passa por `enterNode` — então uma
   checagem de forma nunca é alcançada. O processo morre com `Killed`, sem traceback. A barreira
   que funciona é marcar o nó (`setAttribute`) ao embrulhar.
5. **Regra própria que cria nó novo apaga comentários.** Nó novo nasce sem atributos, e os
   comentários ficam presos ao antigo. Três arquivos perderam linhas como `//--- parser POST/GET`.
   Correção: reaproveitar o nó original em vez de criar outro.

#### A ressalva que fica

O Rector traz junto **modernização que a versão de destino não exige** — no `iss`, 6.480 das
8.409 linhas (77%). É o "grupo (c)" da taxonomia do TCC de referência, e infla a revisão. Duas
observações honestas: `pg_numrows()` **é** deprecated desde o 8.0 (confirmado no runtime), então
o rename é grupo (b) e não lixo; e `var $x` → `public $x` é inofensivo nos dois runtimes. Mas o
diff passa de 1.929 linhas de migração para 8.409 no total, e quem revisar precisa saber disso.

**RESOLVIDO a partir do `dvr`:** as quatro regras entraram na denylist. Medido num caso que
exercita todas as categorias do catálogo, desligá-las **não custa nada obrigatório** — `split`,
`spliti`, `ereg*`, offsets `{}`, `create_function` e construtor PHP 4 são convertidos por regras
**dedicadas**, não pelo `RenameFunctionRector`:

| | config anterior | com a denylist |
|---|---|---|
| `split`/`spliti` → `preg_split` | ✓ | ✓ |
| `ereg*` → `preg_*` | ✓ | ✓ |
| offset `{}` → `[]` | ✓ | ✓ |
| construtor PHP4 → `__construct` (+ chamada ao nome antigo) | ✓ | ✓ |
| guarda `== <literal>` e `parse_str`+`extract` (regras próprias) | ✓ | ✓ |
| `pg_numrows` → `pg_num_rows` | ✓ | **não** |
| `var $x` → `public $x` | ✓ | **não** |
| `array()` → `[]` | ✓ | **não** |
| `public` em método | ✓ | **não** |

#### E mais duas, por segurança: as regras de `each()`

A comparação expôs algo que eu não procurava: a config convertia
`while (list($k,$v) = each($arr))` em `foreach`. **O catálogo proíbe exatamente isso** — em
`db_libpessoal.php` há laços que dependem do ponteiro interno já exaurido por um laço anterior e
que por isso *nunca executam*; trocar por `foreach` faz o segundo rodar. O Rector não tem como
enxergar o `reset()` anterior.

`WhileEachToForeachRector` e `ListEachRector` entraram na denylist. `each()` volta a ser tratado
à mão com `key()`/`current()`/`next()`, conferindo o contexto — como sempre foi.

**Denylist: 22 regras.** Ela cresceu 16 → 22 entre o `iss` e o `dvr`, o que confirma a lição do
item 2 acima: *denylist não é transferível, tem de ser reconferida a cada módulo.*

### CATEGORIA NOVA (iss): `DivisionByZeroError`

```
                     10 / 0        10 % 0
PHP 5.6:             false         false      (Warning, suprimivel com @)
PHP 8.0+:            DivisionByZeroError FATAL  -- o @ NAO suprime
```

É da mesma família do `array_merge(null)`: construção que era *warning* e virou `Error`, com o
`@` deixando de ser rede de segurança.

Onde apareceu: cinco pontos, **dois deles no núcleo** (`fpdf151/fpdf.php`, no desenho do gráfico
de pizza, quando `$this->sum` é zero) e três em `iss2_calculadoepago002.php`, quando o relatório
não tem registros.

**Correção fiel:** guardar o denominador produzindo o valor que o 5.6 entregava adiante. O 5.6
devolvia `false`, que as funções seguintes coagiam para 0:

```php
floor(($val * 360) / doubleval($this->sum))
  ->  floor($this->sum ? ($val * 360) / doubleval($this->sum) : 0)

100 - (($qtd_emdia * 100) / $qtd_calcfixo)
  ->  100 - ($qtd_calcfixo ? ($qtd_emdia * 100) / $qtd_calcfixo : 0)
```

Comprovado no 5.6: `floor(false)` = 0 e `100 - false` = 100 — idênticos à guarda.

**Não varrer em massa.** `fpdf151/fpdf.php` tem **25 divisões por variável**, quase todas por
`$this->k` (a escala, nunca zero). Vale a mesma decisão das guardas `pg_*`: corrigir na aparição.

### CATEGORIA NOVA (iss): `sprintf('%.f')` mudou de precisão

```
                     sprintf('%.f', 0)
PHP 5.6:             "0.000000"    (precisao sem digito = padrao 6)
PHP 8.5:             "0"           (precisao sem digito = 0)
```

Não é erro, não é aviso: é **saída diferente**. Em `fpdf151/fpdf.php` isso mudava a legenda do
gráfico de `(0.000000%)` para `(0%)`, e como a largura do texto define o layout, **a geometria
inteira do gráfico se deslocava** — centro, raio e posição de cada rótulo.

**Correção: `'%.f'` → `'%.6f'`**, que torna explícita a precisão que o 5.6 assumia.

Vale a pena registrar como o defeito foi achado, porque nenhum portão o pegaria: `php -l` passa,
não há fatal no log, e os dois runtimes devolvem HTTP 200. Só a **comparação byte-a-byte**, e
mesmo assim só depois de descomprimir o fluxo `FlateDecode` do PDF.

### CATEGORIA NOVA (iss): o `0 == ""` dentro do `Cell()` do FPDF

A RFC "Saner string to number comparisons" já estava catalogada nas formas `==` e de ordem.
Esta é a quarta manifestação, e vive no **núcleo**, no teste que decide se o FPDF escreve o
texto de uma célula:

```php
fpdf151/fpdf.php:965    if($txt!='')      // decide se imprime o texto da celula
```

```
                     0 != ""
PHP 5.6:             false   -> celula fica VAZIA
PHP 8.5:             TRUE    -> imprime "0"
```

Sintoma observado em `iss2_escritctb002.php`: o campo "Total de Registros" saía **em branco** no
5.6 e **`0`** no 8.5. HTTP 200 nos dois, PDF válido nos dois, 41 bytes de diferença.

**Correção:** `if($txt!='' && $txt!==0 && $txt!==0.0)`, aplicada também na linha 866 (o mesmo
teste no sublinhado). Verificada caso a caso nos dois runtimes:

```
          0      0.0     ""      "0"        "abc"      null
5.6:    vazio   vazio   vazio   imprime    imprime    vazio
8.5:    vazio   vazio   vazio   imprime    imprime    vazio
```

Identificada uma terceira ocorrência do mesmo teste em `fpdf151/FpdfMultiCellBorder.php:301`,
**não tocada** — nenhuma tela a exercitou ainda, e vale a decisão de corrigir na aparição.

### Estado: MÓDULO `dvr` (Diversos) PORTADO ✅ — 10º da área Tributário

**33 telas** (`^dvr[0-9]*_`, variantes `dvr2_`/`dvr3_`/`dvr4_`, sem maiúsculas). Universo pelas
sete frentes: **436 arquivos**, **197 alterados** — a razão telas/arquivos mais desproporcional
da área até aqui (33 telas puxando 197 arquivos), porque quase tudo é `classes/` compartilhada
com Contabilidade e Empenho.

| Correção | Qtd |
|---|---|
| guarda `$this->X == <literal>` | 1.199 |
| `split(`/`ereg*(` → `preg_*` (744 `split`, todos com separador literal) | 744 |
| construtor PHP4 → `__construct` | 162 |
| guardas `pg_*` contra resultado falso | 18 |
| `parse_str()` + `extract()` | 3 |
| parâmetro obrigatório depois de opcional → default `null` | 6 arquivos |
| `$$var` → `${$var}` | 2 arquivos |

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 33 = 33 ✅ |
| 3. classificação dos `split` | 744 literais, **0 regex**, 1 em JavaScript preservado |
| 4. Rector | convergiu em **1 passada** (196 arquivos, depois 0) |
| 4b. portão de funções | 2 novas (`extract`, `preg_split`), 0 ausentes no 5.6 |
| 5. `php -l` nos dois runtimes | **436/436 do universo, 0 erros** |
| 6. instanciação das classes | 315 de 316 idênticas (ver abaixo) |
| 6b. caminho de escrita | 6.207 linhas, 299 classes, 2 divergentes (ver abaixo) |
| 7. bateria de telas | **33/33 idênticas, 0 divergentes** |
| 8. roteamento | `dvr2_`, `dvr3_`, `dvr4_` e `/w/2/` pelo 8.5; `div1_` não foi sombreado |
| regressão nos 9 módulos anteriores | **zero** — todos na linha de base |

**Quarto módulo com bateria perfeita**, depois de `div`, `mar` e `not`. O diff ficou em **2.150
linhas** contra as 8.409 do `iss` — efeito direto da denylist de modernização.

As 4 divergências da primeira bateria eram todas `pg_numrows` sobre resultado falso, em
`dvr2_capaloteamento002`, `dvr3_procedper002` e `dvr4_parclote004/005`. Guardadas as 18 chamadas
desses quatro arquivos, a bateria fechou.

#### Divergências do harness que NÃO são defeito de porte

- **`lancamentoContabil` e `ordemPagamento`** aparecem com `ArgumentCountError` no 8.5 e ausentes
  no 5.6. São `.model.php` com `__construct` exigindo argumentos; o harness instancia sem
  nenhum. No 8.5 o erro é capturável e a varredura segue; **no 5.6 o processo morre**. Limitação
  conhecida do instrumento, igual à registrada no `dbagata/`.
- **`classes/empenho.php` → `datausu`** diverge: `'1969-12-31'` no 5.6 e a data de hoje no 8.5.
  É a categoria nova abaixo, e aparece **porque o construtor agora roda no 8.5** — antes nem
  chegava lá. Só se manifesta sem sessão, que é a condição do harness, não de operação.

### CATEGORIA NOVA (dvr): `date($fmt, null)` significa AGORA no PHP 8

Já estava catalogado que `date()` com *string* é `TypeError` no PHP 8. Com **`null`** não há erro
nenhum — e o resultado muda:

```
                     date("Y-m-d", null)
PHP 5.6:             "1969-12-31"    (null coagido para 0)
PHP 8.5:             "2026-10-10"    (null = usar o relogio, como se o argumento fosse omitido)
```

Medido nos dois runtimes com `db_getsession("DB_datausu")` ausente, que devolve `NULL` em ambos.

**É a forma mais perigosa da família**: não há fatal, não há aviso, e o campo de data recebe
**hoje** em vez da época. Num sistema que grava data de empenho e de pagamento, isso é dado
errado gravado em silêncio.

Correção fiel quando aparecer: `date("Y-m-d", (int)$x)` — `(int)null` é 0, reproduzindo o 5.6.

**NÃO foi varrido em massa.** Escala medida só no universo do `dvr`: **183 ocorrências de
`date(<fmt>, <variável>)` em 39 arquivos**, 20 delas em `classes/empenho.php`. Vale a mesma
decisão das guardas `pg_*`: corrigir na aparição. A bateria das 33 telas fechou **33/33**, o que
indica que em operação normal (com sessão) o valor chega preenchido e os dois runtimes
concordam — mas o risco fica registrado, e é o candidato número um a aparecer no `arr`, que
arrasta 208 arquivos de Empenho.

### Denylist do Rector: 22 → 23 (terceira vez que ela cresce)

`IfIssetToCoalescingRector` **nunca disparou no `div` nem no `iss`, e disparou no `dvr`**. Ela
converte

```php
if (isset($GLOBALS["HTTP_POST_VARS"][$c])) { return $GLOBALS["HTTP_POST_VARS"][$c]; }
return null;
          ->  return $GLOBALS["HTTP_POST_VARS"][$c] ?? null;
```

e o `??` é **PHP 7.0 — parse error no 5.6**. Medido: `$x["k"] ?? null` não parseia no 5.6 e
parseia no 8.5.

Outras duas regras novas apareceram e **foram verificadas e mantidas**, porque são seguras nos
dois runtimes:

| Regra | O que faz | 5.6 | 8.5 |
|---|---|---|---|
| `OptionalParametersAfterRequiredRector` | `function f($a="", $b)` → `$b = null` | ok, devolve `null` | idem |
| `WrapVariableVariableNameInCurlyBracesRector` | `$$label` → `${$label}` | ok | idem |

**A conferência por módulo se pagou pela terceira vez.** Sem ela, 1 arquivo iria para a árvore
com sintaxe que derruba o runtime de referência — e o `php -l` do 8.5 não acusaria nada.

**Armadilha nova do instrumento:** com a config contendo erro de sintaxe, o Rector reportou
**`0 arquivos, 0 regras` sem nenhuma mensagem de erro** no formato JSON. Mais uma falha
silenciosa dele: conferir sempre `php -l` na própria config antes de confiar num resultado zero.

### Estado: MÓDULO `arr` (Arrecadação) PORTADO ✅ — 11º da área Tributário

**162 telas** (`^arr[0-9]*_`, variantes `arr1_`…`arr4_`, sem maiúsculas). Universo pelas sete
frentes: **787 arquivos** — e **366 já pagos** pelos dez portes anteriores, restando **137 a
alterar**. Efetivamente alterados: **116**.

| Correção | Qtd |
|---|---|
| guarda `$this->X == <literal>` | 504 |
| `split(`/`ereg*(` → `preg_*` (279 `split`, todos literais) | 281 |
| construtor PHP4 → `__construct` | 70 |
| `parse_str()` + `extract()` | 34 |
| `$$var` → `${$var}` | 10 |
| guarda `pg_*` contra resultado falso | 1 |

| Passo | Resultado |
|---|---|
| 1. enumeração × `ls` | 162 = 162 ✅ |
| 3. classificação dos `split` | 279 literais, **0 regex**, 0 em JavaScript |
| 4. Rector | **5 regras, todas já vetadas**; convergiu em 1 passada |
| 4b. portão de funções | 3 novas, 0 ausentes no 5.6 |
| 5. `php -l` nos dois runtimes | **787/787 do universo, 0 erros** |
| 6. instanciação das classes | 450 de 451 idênticas (artefatos conhecidos do harness) |
| 6b. caminho de escrita | 9.267 linhas, 434 classes, 2 divergentes (os mesmos do `dvr`) |
| 7. bateria de telas | **162/162 idênticas, 0 divergentes** |
| 8. roteamento | `arr1_`…`arr4_` e `/w/2/` pelo 8.5; `agu1_` não foi sombreado |
| regressão nos 10 módulos anteriores | **zero** — todos na linha de base |

**Quinta bateria perfeita**, e no módulo mais acoplado da área. A única divergência da primeira
rodada era `pg_numrows` sobre resultado falso em `arr2_rellistadqd002.php:178`.

#### ⚠ CORREÇÃO: a previsão de contaminação de escopo do `arr` estava muito errada

Este arquivo registrava, com base na tabela de resíduo:

> **`arr` é o único que rompe a fronteira da área.** Ele arrasta 212 arquivos de `con`
> (Contabilidade) e 203 de `pes` (RH) — módulos de *outras* áreas.
> `arr   func:285   cai:252   con:212   emp:208   pes:203`

**Medido no porte real, a distribuição dos 116 arquivos alterados é:**

```
classes/  80      arr_  32      func_  2      model/  1      cai_  1
```

Nenhum arquivo de `con`, `pes` ou `emp` precisou ser tocado. A previsão não estava errada quanto
ao *fecho de dependências* — `arr` de fato alcança aqueles módulos —, e sim quanto ao **custo**:
a tabela foi computada **antes dos portes** e contava como "a alterar" tudo que o `arr` encosta.
Depois de dez módulos, **366 dos 787 arquivos do universo já estavam pagos**, e o que sobrou do
resíduo compartilhado eram classes que `div`, `fis`, `iss` e `dvr` já haviam corrigido.

**Lição para o relatório:** a métrica de resíduo mede contaminação de escopo num instante, e
**envelhece rápido** num porte incremental. O `arr`, previsto como "o dobro do maior lote já
executado" (343 arquivos), saiu com **116** — menor que o `fis` (384), o `iss` (280) e o `dvr`
(197). A ordem adotada (deixar o `arr` por último) foi, por acidente, a que minimizou o custo
dele: cada módulo anterior pré-pagou parte do seu resíduo.

#### A categoria do `date(null)` NÃO se manifestou

O `arr` tem **24 `date(<fmt>, <variável>)`** e eu havia registrado que era "o candidato número
um a aparecer". A bateria fechou **162/162**, o que confirma o raciocínio da seção do `dvr`: com
sessão presente, `db_getsession("DB_datausu")` devolve um timestamp válido e os dois runtimes
concordam. A divergência exige a variável de sessão ausente, que é condição do harness e não de
operação. As 24 ocorrências ficam **não corrigidas**, como as 183 do `dvr`.

### ⚠ CORREÇÃO: `tri` e `inf` NÃO foram cobertos pelos módulos que os hospedam

Este arquivo supunha, desde o plano da Fase A, que `inf` e `tri` entrariam "junto dos módulos
que os hospedam". **Medido depois do `arr`, não entraram:**

| Prefixo | Telas | Universo | Já pago | **A alterar** | Roteado? |
|---|---|---|---|---|---|
| `tri` | 33 | 83 | 25 | **28** | não — responde pelo 5.6 |
| `inf` | 30 | 89 | 42 | **16** | não — responde pelo 5.6 |

São 44 arquivos no total — os dois menores lotes restantes da área, menores que o `mar` (19) e o
`not` (17) só em telas, não em arquivos. A Fase A **não está concluída** até eles entrarem.

### Estado: MÓDULOS `tri` e `inf` PORTADOS ✅ — 12º e 13º, e a FASE A FECHA

Os dois últimos prefixos exclusivos da área, portados no mesmo lote por serem pequenos.

| | `tri` | `inf` |
|---|---|---|
| Telas (`^tri[0-9]*_` / `^inf[0-9]*_`) | 33 (`tri1_`, `tri4_`) | 30 (`inf1_`, `inf2_`, `inf4_`) |
| Universo pelas sete frentes | 83 | 89 |
| Já pago pelos portes anteriores | 25 | 42 |
| **Alterados** | **28** | **16** |
| `php -l` nos dois runtimes | 145/145 no universo combinado, 0 erros | |
| Instanciação das classes | 21/21 idênticas | 28/28 idênticas |
| Caminho de escrita | 616 linhas, 0 divergentes | 720 linhas, 0 divergentes |
| **Bateria de telas** | **33/33** | **30/30** |

Correções somadas nos dois: 63 guardas `== <literal>`, 53 `split`/`ereg` → `preg_*`, 29
`parse_str`+`extract`, 13 construtores, 2 guardas `pg_*`, 1 `${$var}`. Nenhuma categoria nova.
O Rector aplicou 4 regras no `tri` e 5 no `inf`, **todas já vetadas** — a denylist não cresceu.

**Sexta e sétima baterias perfeitas**, e as duas divergências iniciais foram a mesma categoria
de sempre: `pg_numrows` sobre resultado falso, uma em cada módulo.

**O passo novo do log do PostgreSQL funcionou de primeira.** Na bateria do `tri` ele apontou a
consulta culpada antes de eu abrir o log da aplicação:

```
ERRO: erro de sintaxe no fim da entrada no caractere 219
INSTRUÇÃO: select k09_sequencial, k37_descr from cadtipo inner join cadtipoitem ...
```

Confirma a premissa corrigida: a SQL está **truncada** — não é tabela vazia.

### 📊 FASE A CONCLUÍDA — o número que resume o trabalho

| | |
|---|---|
| Prefixos exclusivos portados e roteados | **13 de 13** |
| **Telas servidas pelo PHP 8.5** | **1.813** |
| **Telas comparadas byte-a-byte** | **1.799 idênticas de 1.813 — 99,2%** |
| Divergências remanescentes | **14**, todas caracterizadas |
| Módulos com bateria **perfeita** | **7** — `div`, `mar`, `not`, `dvr`, `arr`, `tri`, `inf` |

As 14 divergências, por módulo: `itb` 4, `fis` 3, `iss` 3, `agu` 2, `cem` 1, `jur` 1. **Nenhuma
é defeito de migração** — são de três tipos já documentados nas seções de cada módulo: telas que
quebram **no 5.6** e funcionam no 8.5 (defeito pré-existente da referência), fragmentos de
include que não são telas, e variáveis/objetos nunca instanciados no próprio código legado.

Ordem em que foram portados, com o tamanho do lote efetivo:

```
cem 187   itb 192   agu 171   jur 137   div 158   mar  19   not  17
fis 384   iss 280   dvr 197   arr 116   tri  28   inf  16      + dbagata 211 e o nucleo
```

**O `arr`, previsto como o maior (343), saiu em 116** — ver a correção na seção dele. A ordem
adotada (grandes no meio, `arr` por último) foi a que minimizou o custo total, porque cada
módulo pré-paga o resíduo compartilhado do seguinte.

### 📐 FASE B DIMENSIONADA — e duas correções ao que este arquivo afirmava

Medido em 10/10/2026, antes de começar. Duas premissas registradas aqui estavam erradas.

#### ⚠ CORREÇÃO 1: "13 de 16 módulos portados" media PREFIXOS, não módulos

O cabeçalho de estado dizia 13 de 16. **Por telas de menu efetivamente roteadas, só 2 dos 16
módulos estão completos** — `Marcas e Sinais` e `Inflat`. Todos os outros 14 têm pelo menos uma
tela atrás de prefixo compartilhado, quase sempre `cai` (Caixa).

| Módulo | Telas | Já no 8.5 | Faltam | Prefixos que faltam |
|---|---|---|---|---|
| Cadastro | 170 | **0** | 170 | `cad` `cai` `pro` |
| Arrecadação | 172 | 92 | 80 | `cai` |
| Projetos | 35 | 1 | 34 | `pro` `rec` |
| Contrib | 31 | **0** | 31 | `cai` `con` |
| Notificações | 25 | 7 | 18 | `cai` |
| ISSQN | 182 | 174 | 8 | `cad` `cai` `pre` |
| Meio Ambiente | 8 | **0** | 8 | `amb` `pro` |
| Dívida Ativa | 57 | 52 | 5 | `cai` |
| Fiscal | 97 | 94 | 3 | `cai` `prot` |
| Cemitério | 43 | 40 | 3 | `cai` `prot` |
| ITBI | 25 | 23 | 2 | `cad` `cai` |
| Diversos | 15 | 13 | 2 | `cai` `dv` |
| Água | 109 | 108 | 1 | `cai` |
| Jurídico | 62 | 61 | 1 | `cai` |
| **Marcas e Sinais** | 17 | **17** | **0** | — |
| **Inflat** | 8 | **8** | **0** | — |
| **Total** | **1.056** | **690 (65%)** | **366** | |

As 1.813 telas servidas pelo 8.5 continuam corretas — são **arquivos por prefixo**, e dois terços
deles não estão no menu. As duas métricas medem coisas diferentes e as duas valem: *arquivos
roteados* mede o porte, *telas de menu cobertas* mede o que o usuário alcança.

#### ⚠ CORREÇÃO 2: os prefixos compartilhados quase NÃO são compartilhados

Este arquivo afirmava que `cad` e `con` "não podem ir inteiros para o 8.5 sem arrastar
Financeiro e Patrimonial". Medido tela a tela, **as telas são quase disjuntas**:

| Prefixo | Só Tributário | Em Tributário **e** outra área | Só outras áreas |
|---|---|---|---|
| `con` | 30 | **0** | 511 |
| `cai` | 77 | **24** | 151 |
| `cad` | 165 | **1** | 1 |
| `pro` | 34 | **1** | 66 |
| `pre` | 6 | **0** | 35 |
| `amb` | 7 | **0** | 14 |
| **Total** | **319** | **26** | **778** |

**26 telas de 345 (7,5%)** são de fato compartilhadas — 24 delas `cai` com Financeiro
(`cai1_receita*`, `cai1_cfautent*`, `cai4_arrecada001`…), 1 `cad`, 1 `pro`. O risco existe e é
pequeno, e **é de roteamento, não de porte**: o código portado roda nos dois runtimes, então
quem cair no 8.5 por essas 26 telas recebe código verificado byte-a-byte.

#### Os dois escopos possíveis, medidos

| | **A — prefixos inteiros** | **B — só as telas de Tributário** |
|---|---|---|
| Telas roteadas | 3.244 arquivos | **351 telas** (345 + 6 de `prot`/`rec`/`dv`) |
| Universo pelas sete frentes | 5.510 | **1.439** |
| Já pago pela Fase A | 1.004 | **413** |
| **Arquivos a alterar** | **2.072** | **428** |
| Roteamento | uma linha no `location` | `map` de 341 nomes (~10 KB), gerado do banco |
| Efeito colateral | migra Contabilidade, RH, Patrimonial junto | 26 telas de Financeiro vão junto |
| Comparável a | **toda a Fase A** (2.113) | **um módulo grande**: entre `iss` (280) e `fis` (384) |

Custo incremental do escopo A, na ordem do menor para o maior — a sobreposição entre os seis é
de 1.064 arquivos, então somar os lotes isolados superestima em 183:

```
amb    28 isolado ->  28 incremental   (acumulado    28)
pre    29            29                            57
pro   235           234                           291
cad   376           365                           656
cai   544           503                         1.159
con  1043           913                         2.072
```

Distribuição dos 428 arquivos do escopo B: `classes/` 202, `cad_` 105, `cai_` 52, `con_` 30,
`pro_` 21, `func_` 9, resto 9. Categorias: 1.156 guardas `== <literal>`, 802 `split(`, 212
`parse_str`, 187 construtores PHP 4, 14 `ereg*`, 5 `each(`, 2 offsets `{}`. **Nenhuma categoria
nova** — o catálogo das 13 já cobre tudo que a varredura encontra.

#### Viabilidade do roteamento por lista, verificada

- **341 nomes distintos**, sem colisão; `map` de ~10 KB no nginx.
- **3 telas em maiúscula** (`Cai1_recreparcori001/002/003.php`) — o `map` tem de ser
  *case-insensitive*, mesma armadilha do `location ~*`.
- **4 itens de menu apontam para arquivo que não existe** (`cad1_iptupadrao001/002.php`,
  `cad4_iptunotificacaolancamento.php`, `cad4_manutencaonotificacaolancamento.php`). Defeito
  pré-existente do cadastro de menu; ficam de fora.
- Os dois terços fora do menu (popups, `.RPC.php`) **continuam no 5.6** e funcionam: são portados
  junto por estarem no universo, e código portado roda nos dois runtimes. O `/tmp` compartilhado
  já resolveu o loop de iframes que isso poderia causar.

#### Recomendação: escopo B

Ele fecha a área (16 de 16 módulos, 1.056 telas de menu) por **428 arquivos** — o tamanho de um
módulo grande, dentro da faixa já provada sete vezes. O escopo A custa 4,8× mais e entrega
Contabilidade, RH e Patrimonial, que **não estão no escopo acordado da disciplina**.

**Duas decisões em aberto, ambas do usuário:**

1. **As 26 telas compartilhadas com Financeiro** — roteá-las (o módulo Arrecadação fica completo,
   e 24 telas de Financeiro passam a ser servidas pelo 8.5) ou deixá-las no 5.6 (Arrecadação fica
   em 92+56 de 172). Recomendo **roteá-las**: o código é o mesmo nos dois runtimes.
2. **Os 6 itens de `prot`/`rec`/`dv`** — prefixos minúsculos nesta área (48, 279 e 2 arquivos em
   disco) que ninguém tinha notado. São 6 telas; incluí-las é barato e evita um 17º resíduo.

### Estado: FASE B INICIADA — `amb` e `pre` PORTADOS ✅, e o `map` funciona

Primeiro lote do escopo B. Escolhidos por serem os menores: validam o mecanismo de
roteamento por lista antes de `cad` (166 telas) e `cai` (101).

**Decisão de escopo tomada aqui:** porta-se o **prefixo inteiro** (57 arquivos), roteia-se
**só as telas de Tributário** (13). Portar mais do que se roteia é inofensivo — todo código
portado roda nos dois runtimes — e evita a lacuna dos 2/3 fora do menu. As telas `amb` de
Saúde e `pre` de Cidadão ficam no 5.6, já portadas para quando essas áreas chegarem.

| | `amb` | `pre` |
|---|---|---|
| Arquivos do prefixo | 31 | 54 |
| Universo pelas sete frentes | 103 | 133 |
| **Alterados** | **28** | **29** |
| Telas roteadas (Tributário) | **7** | **6** |
| `php -l` nos dois runtimes | 207/207 no universo combinado, 0 erros | |
| Instanciação das classes | 60/60 idênticas | |
| Caminho de escrita | 1.601 linhas, 59 classes, 0 divergentes | |
| **Bateria de telas** | **31/31** | **54/54** |
| Regressão nos 13 módulos da Fase A | **zero** — todos na linha de base | |

Correções: 181 guardas `== <literal>`, 89 `split`/`ereg` → `preg_*`, 31 construtores PHP 4,
25 `parse_str`+`extract`, 9 guardas `pg_*`, 1 offset `{}`.

#### O roteamento por `map`, montado e verificado

`docker/proxy/faseb_map.conf` é **gerado do banco** por `scratchpad/gera_map_faseb.py`; o
`nginx.conf` ganhou três `map`:

```nginx
map $uri $ecidade_arquivo {          # tira o prefixo de janela /w/<n>/
    default                         $uri;
    ~^(?:/w/[0-9]+)?/(?<arq>[^/]+)$ $arq;
}
map $ecidade_arquivo $ecidade_upstream {   # hash exato, O(1)
    default php56;
    include /etc/nginx/faseb_map.conf;
}
location / { proxy_pass http://$ecidade_upstream; }
```

Sete casos verificados: tela `amb`/`pre` de Tributário → 8.5; `/w/2/` → 8.5; tela `amb` que
**não** é de Tributário (`amb1_condicionante.RPC.php`) → 5.6; `cad` ainda não portado → 5.6;
prefixo da Fase A → 8.5; `login.php` → 5.6.

**Armadilha do gerador:** `\copy` é meta-comando do psql e **tem de caber em uma linha**.
Quebrado em várias, o psql falha — e a mensagem vem em **LATIN-1**, que o Python não
decodifica: o sintoma é `UnicodeDecodeError`, não erro de SQL. Mesma família da armadilha de
encoding do resto do projeto, num lugar novo.

### Denylist do Rector: 23 → 25 (QUARTA vez que ela cresce)

Duas regras novas dispararam em `amb`/`pre` e **as duas são perigosas**, por motivos distintos.

**1. `StrEndsWithRector`** — irmã da `StrStartsWithRector`, que já estava banida. Escapou só
por nunca ter disparado. Emite `str_ends_with()`, PHP 8.0; medido, **não existe no 5.6**.
Passa no `php -l` e é fatal só em execução — o modo de falha nº 2 do catálogo, de novo.

**2. `BinaryOpBetweenNumberAndStringRector`** — reescreve `$x == ""` para `$x == 0`. Medido
nos dois runtimes, **não reproduz o 5.6**:

| `$x` | 5.6 `== ""` | 8.5 `== 0` | |
|---|---|---|---|
| `""` | true | **false** | diverge |
| `"0"` | false | **true** | diverge |
| `"abc"` | false | false | ok |
| `0` | true | true | ok |

Essa categoria pertence ao `GuardaComparacaoLiteralRector`, que é fiel. A regra do Rector
chega perto e erra em dois dos seis valores — exatamente o tipo de regressão silenciosa que
o projeto existe para evitar.

**A conferência por módulo se pagou pela quarta vez.** Sem ela, um arquivo iria para a árvore
com `str_ends_with()` e outro com uma comparação que muda de resultado.

### CATEGORIA NOVA: a 5ª manifestação do `0 == ""` vive no `db_select()` do NÚCLEO

E foi achada do jeito mais difícil — **duas hipóteses minhas estavam erradas antes da certa**.

Sintoma: `pre4_configdbpref001.php`, HTTP 200 nos dois, 16 bytes de diferença. Um `<select>`
marcava `selected` em **duas** opções no 5.6 e em **nenhuma** no 8.5.

A linha, em `dbforms/db_funcoes.php:1055` (`db_select()`):

```php
@$GLOBALS[$nomevar] == key($db_matriz) || (@$GLOBALS[$nomevar] === "" && key($db_matriz) == 0)
                                                                         ^^^^^^^^^^^^^^^^^^^^
```

Com o global `""` e as chaves `'f'`/`'t'`:

```
              "f" == 0
PHP 5.6:      true    -> marca AS DUAS opcoes
PHP 8.5:      false   -> nao marca NENHUMA
```

Ironia útil: `key($db_matriz) == 0` **é** a guarda que o catálogo registra como acrescentada
para o caso `"" == 0` no `db_select()`. A guarda de ontem virou o defeito de hoje — ela
própria compara string não-numérica com `0`.

**Correção, medida em 9 valores com zero divergência:**

```php
key($db_matriz) == 0
  ->  (is_string(key($db_matriz)) && !is_numeric(key($db_matriz)) ? true : key($db_matriz) == 0)
```

#### As duas hipóteses erradas, e o que as desfez

Vale registrar porque o método é o achado:

1. **"É a linha 761"** — outro emissor de `<option>` no mesmo arquivo. Corrigi, e a bateria
   não mudou. A linha 761 usa o valor como rótulo; a tela mostrava "Não"/"Sim". **Revertida**,
   pela política de corrigir na aparição.
2. **"É a primeira comparação da 1055"** (`$GLOBALS[$nomevar] == key(...)`). Corrigi, e a
   bateria não mudou. **Revertida.**
3. **A sonda decidiu.** Imprimir `var_export()` do valor e da chave dentro do laço mostrou
   `val='' tipo=string key='f'` — o que elimina as duas primeiras hipóteses e aponta a
   segunda metade da expressão.

**Lição:** com três candidatos plausíveis no mesmo arquivo, instrumentar custa um minuto e
decide; deduzir custou duas rodadas de bateria e duas correções revertidas no núcleo.

#### ⚠ CORREÇÃO ao catálogo: é o ORIGINAL que executa, não a cópia do `modification/`

A sonda mostrou outra coisa que este arquivo afirma e não se confirma neste caminho. A seção
*CRÍTICO: `modification()`* diz que as cópias de `extension/modification/.../cache/user/dbseller/`
são as que executam. Para `dbforms/db_funcoes.php` chamado por `pre4_configdbpref001.php`,
**quem executou foi o original** — a sonda instalada na cópia não produziu saída nenhuma, e a
instalada no original produziu.

As duas cópias **diferem**. Mantive as duas corrigidas, que é o lado seguro, mas a afirmação
"a cópia é que executa" não vale para todo caminho e **precisa ser verificada caso a caso**,
não assumida.

### ⚠ CORREÇÃO ao catálogo: `pg_result()` sobre falso devolve NULL no 5.6, não `false`

A seção das guardas `pg_*` diz que "para `pg_result`, o 5.6 devolvia `false`". Medido:

```
PHP 5.6:  @pg_result(false, 0)  ->  NULL
```

A diferença importa sob `===`. A guarda aplicada em `pre4_liberaitbi002.php` usa `null`:

```php
pg_result($result,0,0)  ->  ($result ? pg_result($result,0,0) : null)
```

### CATEGORIA (pre): ternário aninhado sem parênteses — agora com correção medida

`pre3_logs001.php` era um dos **87 arquivos da base que só quebram no 8.5**. Duas ocorrências
de `a ? b : c ? d : e`, fatal de compilação desde o PHP 8.0.

A associatividade do 5.6 é **à esquerda** — confirmada no runtime: `1?"b":"c"?"d":"e"` devolve
`"d"`. Logo a correção fiel é `(a ? b : c) ? d : e`, e os três valores possíveis do campo
produzem saída idêntica nos dois runtimes depois dela.

**O `php -l` dirigiu a correção, e foi preciso:** corrigi a linha 91, reconferi, e o lint
apontou a **104**. Supor que a primeira era a única teria deixado o arquivo quebrado.

### Estado: MÓDULO `cad` (Cadastro) PORTADO ✅ — 2º lote da Fase B, e o maior salto de cobertura

O único módulo da área que estava em **zero telas** no 8.5. Depois dele, a área salta de
66,6% para **82,3%**.

**Decisão de escopo, medida:** o prefixo inteiro custaria **376** arquivos; o universo das
telas que o `map` de fato roteia custa **210**. Escolhi os 210 — os outros 166 seriam
pré-pagamento para Financeiro e Patrimonial, que não estão no escopo. Diferente de `amb`/`pre`,
onde portar tudo custava 57 e não valia a conta separada.

| | |
|---|---|
| Telas do prefixo em disco | 523 |
| **Telas roteadas (Tributário)** | **166** (162 existem em disco) |
| Universo das 7 frentes, a partir delas | 555 |
| Já pago | 413 |
| **Alterados** | **210** |
| `php -l` nos dois runtimes | **555/555, 0 erros** |
| Instanciação das classes | **201/202 idênticas** |
| Caminho de escrita | 2.049 linhas, **byte-a-byte idêntico** |
| **Bateria das telas roteadas** | **166/166** |
| Regressão nos 15 módulos roteados | **zero** |

Correções: 529 guardas `== <literal>`, 328 `split`/`ereg` → `preg_*`, 99 `parse_str`+`extract`,
82 construtores PHP 4, 8 `gettype`→`is_object` e 2 `(float)` (as duas últimas no núcleo).

### Denylist do Rector: 25 → 28 (QUINTA vez), e uma delas APAGAVA SQL

**`RemoveExtraParametersRector` é a regra mais perigosa encontrada até aqui.** Ela remove
argumentos quando a chamada passa mais do que a assinatura declara:

```php
// cad1_ruas003.php
$cllogradcep->excluir("","","j65_lograd=$j14_codigo");
->  $cllogradcep->excluir("","");          // o WHERE do DELETE SUMIU

// cad1_aba2ruas001.php
$cllogradcep->incluir($j14_codigo, $logs_split[$i]);
->  $cllogradcep->incluir();               // os dois argumentos do INSERT
```

**Medido: o PHP 8.5 ainda aceita argumentos extras** em função de usuário — `func_num_args()`
devolve 3 nos dois runtimes. Logo a regra **não é exigida pela versão de destino**; é limpeza,
e limpeza que apaga a cláusula `WHERE` de um `DELETE` em sistema de tributos.

As outras duas:

| Regra | O que fez | Veredito |
|---|---|---|
| `SensitiveConstantNameRector` | transformou a constante indefinida `l` em `\L` | muda o VALOR: no 5.6 a constante indefinida vira `"l"`, não `"L"` |
| `TernaryToElvisRector` | `($x)?$x:' '` → `$x ?: ' '` | equivalente, mas é modernização — fora do foco |

### CATEGORIA NOVA (cad): `gettype($x) == "resource"` — a variante que a varredura de `is_resource` NÃO pega

O catálogo já registra `is_resource()` sobre resultado do PostgreSQL. Esta é a **mesma falha
escrita de outro jeito**, e por isso escapou da medição de 237 ocorrências feita no `fis`:

```php
dbforms/db_funcoes.php:416   if (gettype($recordnsel) == "resource") {
```

```
             pg_query(...) -> gettype
PHP 5.6:     "resource"   -> laco roda, <option> saem
PHP 8.5:     "object"     -> laco NAO roda, o <select> vem VAZIO
```

Sintoma em `cad2_iptulancpago001.php`: HTTP 200 nos dois, 123 bytes a menos, e as três opções
`ZONA FISCAL 1/2/3` simplesmente ausentes. Nenhum fatal, nenhum log.

Escala medida na base: **8 ocorrências em 2 arquivos** — 4 sítios no `db_funcoes.php` mais a
cópia do `modification/`. Corrigidos os 4, porque 416 e 475 são as **duas metades da mesma
chamada** (`db_multiploselect` monta a lista disponível e a selecionada) e 927/984 são o par
equivalente em `db_selectmultiple`. Correção aditiva: `|| is_object($x)`, que não toca o
caminho do 5.6.

**Lição:** varrer por `is_resource` encontra uma grafia da categoria. A pergunta certa é
"quem mais testa o TIPO do resultado?" — e `gettype()` é a resposta que faltava.

### CATEGORIA (cad): a RFC de ordem no `db_inputdata()` do NÚCLEO

```php
dbforms/db_funcoes.php:1157   if (($db_opcao < 3) || ($db_opcao == 4)) {
```

Sondado em execução: `$db_opcao` vale **`'text'`** — uma string não-numérica.

```
             'text' < 3
PHP 5.6:     true    ("text" vira 0)   -> o seletor de data e emitido
PHP 8.5:     false   ("text" < "3")    -> o widget inteiro SOME
```

Em `cad1_ruas003.php` sumiam o `<script>` com `js_comparaDatasj14_dtlei` e o botão do
calendário — 542 bytes, HTTP 200 nos dois.

Correção `(float)$db_opcao < 3`, medida em 13 valores com **zero divergência**. A ocorrência
irmã em `db_ancora()` (linha 355) **não foi tocada**: não se manifestou, e vale a decisão de
corrigir na aparição.

### ⚠ ERRO MEU: transformação em massa dentro de string SQL quebrou 7 arquivos

O princípio deste arquivo diz "**nunca aplicar transformação em massa sem teste de
caracterização antes**". Eu violei, e o preço apareceu em um minuto.

Achei `trim(l)` em `classes/db_averbacao_classe.php` — constante indefinida, *notice* no 5.6
(vira a string `"l"`) e **fatal no 8.5**. Categoria legítima. Varri o universo por
`trim|strlen|strtoupper|...(bareword)`, achei 25 ocorrências, confirmei no runtime que
**nenhum** dos 18 nomes é constante definida, e apliquei aspas nas 25.

**Quebrou 7 arquivos, incluindo `libs/db_stdlib.php` do núcleo:**

```sql
-- o que meu regex "corrigiu":
where trim(funcao) = '" . trim(addslashes(...)) . "'
where trim("funcao") = '" . ...        <- aspas DENTRO de string PHP de aspas duplas
```

As 25 não eram PHP: eram **colunas de banco dentro de strings SQL**. Um regex que lê bytes não
distingue código de string — é a mesma limitação que o catálogo registra para comentários, e
que motivou adotar o Rector. Desfeitas as 25; `php -l` voltou a 555/555.

**Fica só a de `db_averbacao_classe.php`**, que é PHP de verdade (verificado no contexto:
`$sql .= ...` acima e `$this->erro_sql = ...` abaixo), corrigida para `trim("l")`.

**A lição não é "o regex é ruim"** — é que o teste de caracterização tem de vir **antes** da
aplicação, não depois. Rodar o `php -l` nos 555 arquivos custou 40 segundos e teria evitado
tudo, se eu o tivesse rodado em um arquivo antes de aplicar nos 7.

### ⚠ CORREÇÃO: o `map` do nginx É insensível a maiúsculas — emitir as duas grafias QUEBRA o proxy

O gerador emitia cada tela em duas grafias (minúscula e a do disco), por analogia com a
armadilha que obrigou o `location ~*`. O nginx recusou a configuração:

```
[emerg] conflicting parameter "cad4_emiteiptunovo.php" in faseb_map.conf:159
```

As duas linhas eram `cad4_emiteiptuNovo.php` e `cad4_emiteiptunovo.php`. O erro **prova** que
o `map` trata as duas como a mesma chave. Verificado depois: `/Cad1_averbacao002.php` em
maiúscula roteia para o 8.5 com uma única entrada minúscula no arquivo.

**Generalizando:** `location ~` é sensível a caso e exigiu o `~*`; `map` **não é**. Prevenir-se
da armadilha no lugar errado derrubou o proxy.

### FERRAMENTAL: o harness de classes agora sobrevive a fatal (`scratchpad/harness_robusto.sh`)

O `instancia_classes.php` processa a lista num processo só. **Um fatal mata o processo e o
resto da lista nunca é testado** — e, como os dois runtimes morrem no mesmo arquivo, o
resultado aparece como "idêntico".

Medido no `cad`: a lista tinha **202 classes** e a saída trazia **57**. Parava em
`classes/db_classecadastro.php`.

O invólucro roda o harness repetidamente: quando ele morre, registra o culpado, pula para o
seguinte e continua. Resultado: **201 de 202 idênticas**, com um único arquivo pulado — o
mesmo nos dois runtimes.

É a terceira vez que o instrumento de conferência precisa ser conferido (depois do
`serialize()` de `DOMElement` e do `grep` com aspas). **Saída truncada é indistinguível de
saída limpa quando não se conta o que entrou.**

### MÉTODO: como se decide o que é da área — e por que ROTEAR e PORTAR usam fontes diferentes

Registrado porque é o mecanismo central da Fase B, e porque os limites dele importam tanto
quanto o que ele resolve.

#### A fonte é o BANCO, não o código

```
atendcadarea  →  atendcadareamod  →  db_modulos  →  db_menu  →  db_itensmenu
   (área)          (área↔módulo)       (módulo)      (árvore)    funcao = NOME DO ARQUIVO
```

`db_itensmenu.funcao` guarda o nome do arquivo. Uma tela pertence a uma área quando existe
caminho até ela; a classificação é um `bool_or` sobre a junção:

```sql
bool_or(area LIKE 'TRIBUT%')      -- e da area
bool_or(area NOT LIKE 'TRIBUT%')  -- tambem e de outra
```

Exemplo real, que mostra as duas linhas para o mesmo arquivo:

```
  area          | modulo      | tela
  DB:FINANCEIRO | Caixa       | cai1_receita001.php
  DB:TRIBUTÁRIO | Arrecadação | cai1_receita001.php
```

#### Os três limites, medidos

| Prefixo | Em disco | No menu | **Fora do menu** | Menu → arquivo inexistente |
|---|---|---|---|---|
| `cad` | 523 | 193 (37%) | **330** | 9 |
| `cai` | 740 | 264 (36%) | **476** | 9 |
| `con` | 1.570 | 566 (36%) | **1.004** | 21 |
| `pro` | 387 | 134 (35%) | **253** | 0 |

1. **Só ~36% dos arquivos estão no menu.** Os outros 64% — popups, `.RPC.php`, subtelas —
   **não têm atribuição de área nenhuma** no banco. Para eles o mapeamento não responde.
2. **197 entradas fantasma** na base inteira: o menu aponta para arquivo que não existe.
   Defeito pré-existente do cadastro, não da migração.
3. **É dado, não código.** É o menu *desta* prefeitura. Outra instalação teria outra árvore —
   o gerador é reprodutível, a saída é específica da base.

#### A resolução: duas perguntas, duas fontes

| Pergunta | Fonte | No `cad` |
|---|---|---|
| **O que roteio para o 8.5?** | o menu do banco | 166 telas |
| **O que preciso portar?** | fecho de dependências, 7 frentes | 555 arquivos |

Os 330 arquivos do `cad` fora do menu **continuam servidos pelo 5.6**, mas **estão portados**:
a frente "citados em strings" os puxa a partir das telas roteadas, seguindo o `window.open` do
JavaScript. Funcionam nos dois runtimes, que é a invariante do strangler fig.

É por isso que a 3ª lacuna foi cara quando apareceu no ITBI: sem ela eu rotearia telas cujos
popups ninguém havia portado.

### ⚠ DECISÃO REVISTA: a bateria de regressão passa a ser PROPORCIONAL ao risco

A pergunta do usuário — *"é realmente necessária aquela bateria de regressão? se não mexeu nos
outros arquivos, para que verificar?"* — estava **certa em 198 dos 199 arquivos**, e produziu
uma correção de método.

Medido, cruzando os arquivos de cada lote com o universo dos módulos já verificados:

| Lote | Arquivos alterados | **No universo de módulo já verificado** |
|---|---|---|
| `cad` | 199 | **1** — `dbforms/db_funcoes.php` |
| `amb`+`pre` | 64 | **2** — o mesmo, mais uma `classes/` |

**A bateria de 1.898 telas nunca foi por causa do lote** — foi por causa de **um** arquivo.
Os outros 198 do `cad` não são executados por nenhum módulo anterior: ninguém mais os carrega.

Duas honestidades que o número expõe:

- **Em 15 execuções, a bateria de regressão cruzada nunca pegou uma regressão.** Sempre
  reportou linha de base. O valor dela até aqui foi **confirmatório**, não detetivesco.
- Ela só se justificou porque **quase todo lote acabou tocando o núcleo** — e um defeito no
  núcleo alcança as 1.898 telas, então aí a bateria larga é exatamente o teste certo.

**Regra que passa a valer** (custa ~3 segundos computar, contra ~25 minutos de bateria):

```
interseção = arquivos_do_lote  ∩  união(universos dos módulos já verificados)

vazia                      -> NÃO rodar bateria de regressão
só arquivos de um módulo   -> rodar a bateria DAQUELE módulo
arquivo do NÚCLEO          -> rodar a bateria COMPLETA
```

O núcleo, para este fim, é `dbforms/`, `libs/`, `std/`, `fpdf151/`,
`classes/db_cgm_classe.php` e a árvore `extension/modification/`.

**Ressalva que mantém o rigor:** a bateria completa continua obrigatória sempre que o núcleo
for tocado — e isso aconteceu em **todos** os lotes medidos até aqui, porque é lá que os
defeitos silenciosos vivem (`is_resource`, `gettype`, `db_select`, `db_inputdata`). A regra
não afrouxa a verificação: ela deixa de gastar 25 minutos quando a interseção é vazia, o que
até hoje nunca ocorreu, mas vai ocorrer nos lotes pequenos que não encostam no núcleo.

**Valor que fica, mesmo sem nunca ter pego defeito:** as 15 execuções com "zero regressão" são
a evidência de que migração incremental com dois runtimes **não degrada o que já foi migrado**.
Isso é resultado do trabalho, não só um portão de qualidade — e é o que o TCC de referência,
que fez big-bang, não tem como mostrar.

### Estado: MÓDULO `cai` (Caixa) PORTADO ✅ — 3º lote da Fase B

O prefixo com as **24 telas compartilhadas com Financeiro** e com as 3 em maiúscula
(`Cai1_recreparcori001/002/003.php`) — as duas armadilhas documentadas, num lote só.

| | |
|---|---|
| Telas do prefixo em disco | 740 |
| **Telas roteadas (Tributário)** | **101** |
| Universo das 7 frentes | 809 |
| **Alterados** | **150** (o prefixo inteiro custaria **539**) |
| `php -l` nos dois runtimes | **809/809, 0 erros** |
| Instanciação das classes | **462/462**, só os 3 artefatos conhecidos |
| Caminho de escrita | 12.863 linhas, 441 classes |
| **Bateria das telas roteadas** | **101/101** |
| Regressão | **não rodada** — ver a regra proporcional |

Correções: 360 guardas `== <literal>`, 272 `split`/`ereg` → `preg_*`, 64 construtores,
55 `parse_str`+`extract`, 4 guardas `pg_*`, 1 `in_array`, 1 `!= ""`.

**O Rector aplicou 6 regras, todas já vetadas — a denylist não cresceu pela primeira vez
desde o `amb`/`pre`.** Convergiu em 1 passada.

Os 3 artefatos do harness são exatamente os já registrados no `dvr`: `lancamentoContabil` e
`ordemPagamento` (`.model.php` com construtor obrigatório, o 5.6 morre e o 8.5 segue) e
`classes/empenho.php → datausu` (`'1969-12-31'` contra a data de hoje — a categoria
`date($fmt, null)`, que só se manifesta **sem sessão**, condição do harness e não de operação).

### CATEGORIA NOVA (cai): `in_array()` com *haystack* nulo

```
                     in_array("x", null)
PHP 5.6:             NULL    (warning, suprimivel)
PHP 8.5:             TypeError FATAL
```

Em `forms/db_frmarretipo001.php:859`, decidindo se uma caixa vem marcada:

```php
<?= (in_array($item->k195_sequencial, $aOperacoesSalvas) ? "checked" : "") ?>
```

`$aOperacoesSalvas` **nunca é atribuída** naquele caminho. Derrubava as três telas
`cai1_arretipo001/002/003` — ~15 KB a menos cada.

**Correção fiel:** `(is_array($h) && in_array($x, $h))`. Medido: no 5.6 o `in_array` devolve
`NULL` e `NULL ? "checked" : ""` dá `""`; a guarda devolve `false` e dá o mesmo `""`.

É a mesma família de `array_merge(null)`, `sizeof(null)` e `date(null)` — argumento inválido
que era *warning* e virou `TypeError`, com o `@` deixando de proteger.

**Escala no universo do `cai`: 74 ocorrências em 22 arquivos. NÃO varridas** — vale a decisão
de corrigir na aparição, reforçada pelo erro do `trim(bareword)` no `cad`.

### CATEGORIA (cai): o `0 == ""` na forma NEGADA, decidindo se emite JavaScript

Sexta manifestação da RFC, e a primeira em que o 8.5 produz **mais** saída que o 5.6 —
38 bytes a mais, não a menos.

```php
forms/db_frmarrevenc.php:235
if (isset($k00_numpar) && $k00_numpar != "") {
    echo " document.form1.k00_numpar.value = $k00_numpar; ";
}
```

Com `$k00_numpar = 0`:

```
             0 != ""
PHP 5.6:     false  -> NAO emite
PHP 8.5:     true   -> emite ` document.form1.k00_numpar.value = 0;`
```

Isso **preenche um campo do formulário com zero** no 8.5 onde o 5.6 o deixava intacto.

**Correção, medida em 9 valores com zero divergência:**

```php
$k00_numpar != "" && $k00_numpar !== 0 && $k00_numpar !== 0.0
```

**Nota de método:** as guardas que o catálogo registra são todas para `== ""`. Esta é a forma
`!= ""`, e o `GuardaComparacaoLiteralRector` **não a cobre** — ele casa só a comparação
positiva. Por isso escapou de todos os lotes anteriores e só a bateria byte-a-byte a achou.

### ✅ PRIMEIRA APLICAÇÃO da bateria proporcional — e ela se pagou

Computada a interseção do lote com os universos já verificados:

```
arquivos alterados no lote      127
arquivos do NUCLEO tocados        0
modulos cujo universo intersecta  nenhum
-> DECISAO: nao rodar bateria de regressao
```

Primeira vez em 16 lotes que o núcleo **não** foi tocado — e portanto a primeira vez que a
regra dispensa a bateria completa.

**Não aceitei a regra nova de olhos fechados na estreia.** Rodei três baterias baratas como
prova: `not` 14/14, `mar` 35/35, `inf` 30/30 — 79 telas, todas na linha de base, confirmando
a previsão da interseção.

Economia: ~25 minutos de bateria trocados por ~3 segundos de interseção mais 2 minutos de
amostra. E, mais importante que o tempo, a regra **explicita o motivo** de cada verificação
em vez de rodar tudo por hábito.

### Estado: `pro` · `con` · `prot` · `rec` · `dv` PORTADOS ✅ — e a ÁREA TRIBUTÁRIO FECHA

Lote final da Fase B: os cinco prefixos que faltavam, somando **71 telas**.

**É aqui que o escopo B se paga de forma decisiva.** Os prefixos inteiros custariam **1.483**
arquivos; o universo das telas efetivamente roteadas custou **109** — 13,6× menos. O `con`
sozinho custaria 1.019 arquivos para entregar 30 telas.

| | |
|---|---|
| Telas roteadas | **71** (`pro` 35, `con` 30, `prot` 4, `rec` 1, `dv` 1) |
| Universo das 7 frentes | 264 |
| **Alterados** | **109** (prefixos inteiros: 1.483) |
| `php -l` nos dois runtimes | **264/264, 0 erros** |
| Instanciação das classes | **106/106 idênticas** |
| **Bateria** | **71/71** |
| Regressão nos 15 módulos | **zero** |

Correções: 258 guardas `== <literal>`, 218 `split`/`ereg` → `preg_*`, 56 `parse_str`+`extract`,
40 construtores, 6 `${$var}`, 4 `break` → `exit`, 1 guarda `pg_*`.

### Denylist do Rector: 28 → 29 (SEXTA vez), e a regra contrariava uma decisão já medida

**`BreakNotInLoopOrSwitchToReturnRector`** converte `break;` fora de laço em `return;`. O
catálogo **já havia decidido essa categoria** na seção do `fis`, e contra ela:

```
PHP 5.6, break fora de laco:  imprime "antes " e MORRE
                              ("Cannot break/continue 1 level")
com `return;`:                o 8.5 volta e SEGUE -> comportamento novo
```

A correção fiel é **`exit;`** quando o `break` é alcançável; remover só equivale quando ele é
inalcançável. **A escolha depende da alcançabilidade, que a regra não analisa.**

Os 4 sítios (`con1_autoriza001.php`, `con1_edital002.php` ×2, `con1_edital003.php`) estão
todos dentro de blocos `if ($obj->erro_status == '0') { $sqlerro = true; break; }` —
**alcançáveis**, exatamente como `fis1_vistorias003.php`. Corrigidos para `exit;` à mão.

São três dos **87 arquivos da base que só quebram no 8.5**. E de novo o `php -l` dirigiu:
em `con1_edital002.php` ele apontou a linha 83, depois a 92 — e **não** apontou a 72, porque
aquele `break` está dentro de um `for` e é legal. A ferramenta distinguiu o que o olho não
distinguiria sem ler o bloco inteiro.

### Onde o Rector ganha do `porta.py`, agora com caso concreto

Este lote tinha **4 `split()` com separador não-literal** — a categoria que o `porta.py`
**abortava** e que o `jur` documentou como perigosa. O Rector converteu os quatro
corretamente:

```php
split(" +", $regs[2])   ->  preg_split("# +#m", $regs[2])    // POSIX "um ou mais espacos"
split("\|", $valores)   ->  preg_split("#\|#m", $valores)    // pipe escapado = literal
```

É a terceira vantagem da AST listada no experimento do `div`, aparecendo na prática.

### ⚠ A regra proporcional e a interseção medida DISCORDARAM — e vale registrar

```
arquivos alterados               108
NUCLEO tocado                      1  -> fpdf151/pdf4.php
modulos cujo universo intersecta   0  (vazio)
```

A regra manda **bateria completa** quando o núcleo é tocado; a interseção medida dizia que
**nenhum** módulo verificado executa aquele arquivo. Verificado: `fpdf151/pdf4.php` é incluído
por **um** arquivo em toda a base — `pro2_cartahabite002.php`, que está neste próprio lote.

**A interseção estava certa; a heurística "pasta inteira = núcleo" disparou demais.** Rodei a
bateria completa mesmo assim, por ser o lote que fecha a área — e deu linha de base nos 15.

**Refinamento para a regra:** o critério de núcleo deveria ser por **arquivo alcançado**, não
por pasta. `dbforms/db_funcoes.php` é carregado por tudo; `fpdf151/pdf4.php`, por um arquivo.
A interseção com os universos já mede isso corretamente — a lista de pastas é redundante e
mais conservadora do que precisa.

### 🏁 ÁREA TRIBUTÁRIO CONCLUÍDA — os números que resumem o trabalho

| | |
|---|---|
| **Módulos completos** | **16 de 16** |
| **Telas de menu servidas pelo PHP 8.5** | **1.056 de 1.056 (100%)** |
| Arquivos roteados | **2.160** — 1.813 por prefixo (`location`) + 347 por lista (`map`) |
| **Telas comparadas byte-a-byte** | **2.222 idênticas de 2.236 — 99,4%** |
| Divergências | **14**, todas caracterizadas, **nenhuma defeito de migração** |
| Baterias **perfeitas** | **12** — `div`, `mar`, `not`, `dvr`, `arr`, `tri`, `inf`, `amb`, `pre`, `cad`, `cai`, e o lote final |

Cobertura por módulo, todos em 100%:

```
ISSQN 182   Arrecadacao 172   Cadastro 170   Agua 109   Fiscal 97   Juridico 62
Divida 57   Cemiterio 43   Projetos 35   Contrib 31   ITBI 25   Notificacoes 25
Marcas 17   Diversos 15   Inflat 8   Meio Ambiente 8
```

Custo efetivo, por fase:

```
Fase A  13 prefixos exclusivos, roteados por `location`    ~2.113 arquivos alterados
Fase B   9 prefixos compartilhados, roteados por `map`       ~  909 arquivos alterados
         (os prefixos inteiros teriam custado 2.072)
```

**A decisão de escopo da Fase B economizou cerca de 1.160 arquivos** e evitou migrar
Contabilidade, RH e Patrimonial, que estão fora do escopo acordado.

**O que NÃO está feito, e precisa estar claro no relatório:** o 100% é de *telas de menu*. Os
dois terços de cada prefixo que vivem fora do menu — popups, `.RPC.php`, subtelas — continuam
servidos pelo 5.6. Estão **portados** (entram pelo universo das sete frentes) e funcionam nos
dois runtimes, mas não estão roteados. Rotear o resto exigiria estender o `map` com os
arquivos fora do menu, que o banco não sabe classificar por área.

### ⚠ 10ª LACUNA (15/10/2026): 11 telas de menu nunca entraram no `map` — o "100%" valia 1.048/1.059

Achada perguntando ao proxy, tela de menu por tela de menu, qual runtime responde
(`X-Ecidade-Runtime` em `http://localhost:8090/w/2/<tela>`), em vez de confiar nas listas.

**Causa:** em `db_itensmenu.funcao` a tela vem com parâmetro (`con1_manutexto.php?db_opcao=alvara_p1`,
`cad1_iptubase001.php?tipoImovel=1`). O `WHERE funcao ~ '\.php$'` do `gera_map_faseb.py` exigia que
o texto **terminasse** em `.php` e as descartava em silêncio. Só afeta o `map`: o `location` casa o
nome e ignora o parâmetro. Corrigido com `split_part(funcao,'?',1)` no `SELECT` e no `WHERE`.
A 11ª, `sys4_geradorteladinamica001.php`, tinha outra causa: o prefixo `sys` não estava em lista nenhuma.

As 11: `cad1_iptubaixa001`, `cad1_iptubase001/002`, `cad2_relatorios_001`, `cad3_conscadastronovo_001`,
`cai1_arrevenc002`, `cai2_relcaixa_001`, `cai4_baixabanco002`, `cai4_debcontapedaba002`,
`con1_manutexto`, `sys4_geradorteladinamica001`.

| Passo | Resultado |
|---|---|
| Universo (sete frentes, a partir das 11) | 101 arquivos, 48 já pagos |
| **Alterados** | **7** (Rector: 4 `ereg`/`split`, 3 guardas, 3 construtores, 2 `parse_str`, 1 offset `{}`); convergiu na 2ª passada, só regras vetadas |
| Remanescentes (contador por token) | 0 — os 2 de `db_db_config_classe.php` são o falso positivo já registrado |
| Portão de funções contra o 5.6 | 0 ausentes |
| `php -l` nos dois runtimes | 101/101 |
| Classes / caminho de escrita | 39/40 idênticas (a 40ª, `cl_iptuconstr_extends`, foge da convenção de nome do harness nos dois) / 1.516 linhas idênticas |
| **Bateria** | **13/13** sem parâmetro e **88/88 entradas de menu COM o parâmetro** |
| Regressão (interseção com `cad`/`con`/`pro`/`rec`) | `map` inteiro 347/347 |
| **Roteamento conferido pelo proxy** | **1.059 de 1.059** telas de menu existentes no 8.5 (7 entradas apontam para arquivo inexistente) |

Feito com as ferramentas do `scratchpad/` da branch `2educacao-migrado` (versões com TIMEOUT,
`PULAR` e o `re.I` da 9ª lacuna), copiadas para fora da árvore; o `enumera.py` recebeu as telas
por `TELAS=a.php,b.php`. O `paridade-56.ini` (criado na Educação) estava montado, como na linha de
base 2.154/2.160.

**Na Educação (`2educacao-migrado`), as 3 telas `mat1_matestoqueini001/002/003`** (abertas com
`?entrada=true`; também são do Patrimonial, então passam ao 8.5 para as duas áreas, como as `cai`
compartilhadas com Financeiro). Trazida a correção do gerador por *merge* da `1tributario-migrado`
(não rebase: as duas branches já estão publicadas). Universo 137, 94 já pagos, **4 alterados** (Rector:
3 guardas, 3 construtores, 3 `split`, 1 `parse_str`); `php -l` 137/137 nos dois; classes 87/87 (só o
artefato conhecido de `RequisicaoMaterial`); escrita 83 classes idênticas; bateria **6/6** (com e sem
`?entrada=true`); regressão pela interseção com `con` → 31/31. O `enumera.py` ganhou `TELAS=a.php,b.php`
para lotes que não são um prefixo.

**Lição, a décima da mesma família:** a conferência partia da lista que o gerador produziu. Quem
achou foi a conferência independente — perguntar ao sistema em execução, tela por tela.

### ✅ NÍVEL 3 EM ESCALA — 18 telas roteadas, 14 módulos, zero divergências

O maior ponto fraco declarado do trabalho era este: **as 6.552 guardas `0 == ""` são 60% de
todas as correções, e só disparam no `POST`** — enquanto a bateria de 2.236 telas é toda
`GET`. O nível 1 (estado do objeto) as cobria em todos os lotes; o nível 3 (POST real,
comparando o SQL emitido) tinha rodado em **uma** tela.

Agora são **18**, cobrindo 14 dos 16 módulos:

```
agu arr cem div jur mar not tri cad cai fis inf iss itb
```

Cada uma submete o mesmo `POST` aos dois runtimes, com snapshot/restore entre eles, e compara
o `INSERT` de negócio campo a campo. **Zero divergências.**

#### FERRAMENTAL NOVO: `scratchpad/payload_auto.py`

O catálogo registrava que "o que limita o nível 3 é montar o payload, não o custo de
execução". Provado na prática: errei **duas vezes seguidas** antes de acertar uma tela —
inventei um nome de arquivo que não existe, e depois usei nomes de campo que não eram os reais
(`cm34_descr` em vez de `cm34_descricao`, `cm34_dtvalidade` em vez de `cm34_datalimite`).

A saída foi ler o formulário que o próprio 5.6 emite e gerar o esqueleto: nomes reais dos
campos, o botão de submit certo (ignorando os `dtjs_*`, que são seletores de calendário), as
opções de cada `<select>` e os `_dia`/`_mes`/`_ano` escondidos. Com ele, **18 das 28 telas
exercitaram de primeira**.

#### ⚠ A primeira rodada deu 5 DIVERGE — e as CINCO eram do instrumento

Vale registrar inteiro, porque é o padrão que se repete neste projeto.

**Defeito 1 — o parser engolia a linha de `ERRO:` do PostgreSQL.** A junção de continuação
colava qualquer linha seguinte ao statement, e as linhas de erro trazem timestamp e PID
próprios:

```
5.6> insert into advog(...) values ( 1 ,'1' ,'1' ) 2026-10-11 15:06:50.952 [8134] ERRO: ...
8.5> insert into advog(...) values ( 1 ,'1' ,'1' ) 2026-10-11 15:06:53.437 [8156] ERRO: ...
```

O `INSERT` é idêntico; divergia **só pelo relógio**. Corrigido distinguindo linha de log
(qualquer nível) de continuação de SQL. Isso sozinho levou 5 DIVERGE para 1.

**Defeito 2 — o nome da sequência não era casado.** O harness procurava só
`<tabela>_%_seq`, mas a convenção do e-cidade tem **três** formas:

```
cemiterioisencao_cm34_sequencial_seq    <tabela>_<campo>_seq
cem_legista_seq                         <modulo>_<tabela>_seq   <- a tabela no MEIO
<tabela>_seq
```

Sem restaurar a de `legista`, o segundo runtime recebia o número seguinte — `values ( 8 ...)`
contra `( 9 ...)`. **É exatamente a divergência benigna que o próprio catálogo previa**, e
que eu não tinha percebido estar acontecendo.

**Defeito 3, o pior — ele APROVAVA quando nada acontecia.** Com os dois lados vazios, imprimia
"SQL de escrita de NEGOCIO IDENTICO". Achado por acidente, ao rodar com um nome de tela
inexistente: 404 nos dois lados, zero statements, veredito positivo. Agora reporta
**`INCONCLUSIVO`** e sai com código 2.

**É a quarta vez que o instrumento de conferência precisa ser conferido** — depois do
`serialize()` de `DOMElement`, do `grep` com aspas e do invólucro que contava linhas de saída.
E o terceiro defeito é o mais grave de todos: *dá impressão de cobertura onde não houve
nenhuma*. Se eu tivesse rodado as 18 telas com o harness anterior e errado payloads, teria
entregue "18 telas verificadas" sem ter verificado nada.

#### ⚠ ERRO DE MÉTODO MEU: testei telas que NÃO estão roteadas

Duas divergências sobreviveram às correções, em `cad1_averba001.php` e `cad1_averbacgm001.php`.
Diagnóstico no 8.5:

```
ArgumentCountError: parse_str() expects exactly 2 arguments, 1 given
  em cad1_averba001.php:34
```

Um `parse_str` de 1 argumento **não portado**. Mas antes de chamar isso de defeito, conferi o
roteamento: **as duas telas não estão no `map`** — são servidas pelo 5.6, onde funcionam.
Testei código que nunca executa no 8.5.

Meu critério de seleção pegava "telas de inclusão por prefixo", não "telas roteadas". Das 33
testadas, **5 não estavam roteadas** e foram descartadas da contagem.

**O achado continua valendo, por outro motivo:** ele é a prova concreta de que a fronteira do
escopo B é real e está no lugar certo. Os arquivos `cad` fora do menu **não** foram portados,
e fatalariam se fossem roteados. O `map` é o que os mantém no runtime onde funcionam.

#### O que fica em aberto

Das 28 telas roteadas testadas: **18 exercitaram**, 6 voltaram `INCONCLUSIVO` (a validação
recusa antes do `INSERT` — payload automático insuficiente), 3 deram erro e 1 não tem
formulário no HTML inicial (é aba carregada por JavaScript).

As 10 que faltam precisam de payload montado à mão, lendo cada formulário. **É o custo que o
catálogo já previa, e ele é real:** ~2 a 4 telas por sessão de trabalho. O ganho marginal de
insistir nelas é baixo — 18 telas em 14 módulos, todas idênticas, já sustentam a afirmação
que faltava.

### ⚠ DECISÃO REVISTA: `tmp/` e `arquivos/` agora são 777

O texto anterior desta seção dizia que `tmp/`, `storage/` e `arquivos/` eram `775 diego`,
"não graváveis por nenhum dos dois containers", e que isso fora **deixado como está** porque
a falha igual nos dois "preserva a comparabilidade".

**O argumento estava errado e custou cobertura de teste.** `tmp/` é bind mount compartilhado e
os dois containers rodam como uid 33 — liberá-lo afeta os dois **igualmente**, exatamente como
deixá-lo travado. A diferença é que travado eles falham antes de executar.

Escala do que isso escondia:

| | |
|---|---|
| Telas da área Tributário que tocam o caminho de relatório | **211 de 1.813 (11%)** |
| Destas, nos três módulos já portados | **40 de 460 (8%)** |

Essas 40 apareciam como "idênticas" nas baterias, mas eram idênticas **no erro**:

```
itbi_situacao002    5.6=18.668 B  8.5=18.669 B   ambos: "Unable to create output file: tmp/..."
agu2_relconsumo002  5.6=18.681 B  8.5=18.681 B   idem
```

Comparabilidade sem cobertura — o tipo mais barato e menos útil de equivalência.

**Depois de `chmod 777 tmp arquivos`:** os relatórios passam a ser gerados de verdade (resposta
termina em `%%EOF`, PDFs reais aparecem em `tmp/`) e as três baterias foram refeitas:

| Módulo | Antes (tmp/ 775) | Depois (tmp/ 777) |
|---|---|---|
| `cem` | 114/116 | **114/116** |
| `itb` | 116/120 | **116/120** |
| `agu` | 222/224 | **222/224** |

**Zero regressões novas no 8.5.** O conjunto de divergências é exatamente o mesmo — o caminho
FPDF do núcleo está correto no PHP 8.5. O ganho não é ter achado defeito; é que agora **existe
prova** onde antes havia só ausência de prova.

`storage/` continua em 777 (necessário para o login do Laravel, ver seção própria).

**Efeito colateral previsto e verificado:** `dbforms/db_classesgenericas.php:522` usa
`tempnam("tmp/", "iframe")` — o `tmp/` **do projeto**, não o `/tmp` do sistema. Enquanto não era
gravável, o PHP caía no diretório temporário do sistema, que foi o que motivou o volume
`ecidade_tmp` compartilhado e a correção do loop infinito de iframes. Agora os temporários caem
no bind mount, que também é compartilhado. Verificado: `itb1_itbitransacao111.php` pelo `:8090`
responde **1 requisição, HTTP 200** (o loop devolvia milhares). O volume `ecidade_tmp` foi
mantido — outros pontos ainda usam o `/tmp` do sistema.

Reversível com `chmod 775 tmp arquivos`; nenhuma alteração de código.

### 🗺️ DIMENSIONAMENTO DAS PRÓXIMAS ÁREAS (13/10/2026)

Medido no banco (mesma cadeia `atendcadarea → … → db_itensmenu`), descontando o que já é
servido pelo 8.5 e o que os commits `Porta …` já pagaram. Arquivos a alterar = fecho das sete
frentes a partir das telas de menu (estimativa: na Fase B, 428 previstos viraram ~526).

| Área | Módulos | Telas que faltam | Universo | Já pago | A alterar |
|---|---|---|---|---|---|
| Financeiro | 6 | 910 | 2.568 | 340 | 788 |
| Patrimonial | 8 | 713 | 2.224 | 344 | 674 |
| Recursos Humanos | 4 | 685 | 1.925 | 300 | 492 |
| Saúde | 8 | 474 | 1.192 | 84 | 507 |
| Educação | 5 | 467 | 1.617 | 296 | 514 |
| Configuração | 1 | 203 | 905 | 298 | 219 |
| Assistência Social | 2 | 65 | 305 | 102 | 73 |
| Cidadão | 1 | 34 | 108 | 35 | 13 |
| Gestor / Integrações | 1+1 | 7+8 | 41+60 | — | 8+5 |

Somadas isoladas dão 3.293; a união é 2.783 — a ordem pré-paga o resíduo da seguinte. Cinco
áreas cadastradas não têm módulo ligado (Geoprocessamento, Administração, DBLeis, Comercial,
Implantação). Contando telas distintas, Tributário tem 1.031 (o 1.056 conta por módulo).

**Escolhida: Educação** — não a maior nem a mais barata, mas a única que permite comparar as
duas estratégias (big-bang 8.4 do TCC de referência × strangler fig 8.5) **sobre o mesmo módulo**.

#### Refeito em 18/10/2026, depois da Educação — `scratchpad/dimensiona.py`

Mesmo método, agora reproduzível: telas de menu existentes em disco que o 8.5 ainda não serve
(nem pelo `location` nem pelo `map`), fecho das sete frentes pelo `enumera.py` (`TELAS=`).
Conferência do instrumento: Tributário e Educação saem com **0 faltando** (1.066 − 7 fantasmas
= 1.059 e 481 − 1 = 480, os mesmos números conferidos pelo proxy em 15/10).

| Área | Módulos | Telas que faltam | Universo | Já pago | **A alterar** | em 13/10 |
|---|---|---|---|---|---|---|
| Financeiro | 6 | 949 | 2.674 | 401 | **771** | 788 |
| Patrimonial | 8 | 713 | 2.239 | 419 | **622** | 674 |
| Saúde | 8 | 492 | 1.322 | 165 | **505** | 507 |
| Recursos Humanos | 4 | 700 | 1.989 | 337 | **486** | 492 |
| Configuração | 1 | 203 | 920 | 361 | **173** | 219 |
| Assistência Social | 2 | 67 | 323 | 131 | **62** | 73 |
| Cidadão | 1 | 35 | 109 | 35 | **13** | 13 |
| Integrações / Gestor | 1+1 | 13+7 | 77+41 | 39+21 | **9+8** | 5+8 |

União: **2.358** (era 2.783). A Educação pré-pagou ~425 arquivos das outras áreas, sobretudo
Patrimonial (−52, as `mat`) e Configuração (−46). Saúde e RH quase não mudaram: são as áreas com
menos código em comum com as já feitas. "Telas que faltam" no Financeiro subiu de 910 para 949
porque a correção da 10ª lacuna passou a contar as entradas de menu com parâmetro.

Ressalvas de leitura: "a alterar" é estimativa estática — nas duas áreas feitas o real saiu
13–23% acima (correções à mão e lacunas) — e não conta os commits `EXPERIMENTO:` como pagos.

### 📐 ÁREA EDUCAÇÃO — dimensionada e INICIADA

Ao contrário do Tributário, quase não tem prefixo compartilhado:

| Prefixo | Telas no menu | Em outra área? | Em disco | A alterar (prefixo inteiro) |
|---|---|---|---|---|
| `edu` | 340 | não | **1.211** (= as 1.211 da monografia) | 740 |
| `mer` | 43 | não | 187 | 182 |
| `bib` | 39 | não | 98 | 85 |
| `sec` / `rel` / `esc` | 8 / 1 / 3 | não | 12 / 1 / 3 | 15 / 9 / 4 |
| `tre` | 14 | não | 19 | 3 |
| `mat` | 19 | **sim** — as 19 também são do Patrimonial | 280 | via `map` |
| `pro` | 1 | sim — prefixo da Fase B | 341 | via `map` |

**Escopo adotado: A** — os 7 prefixos exclusivos portados **inteiros** e roteados por
`location` (969 arquivos contra 514 do escopo "só menu"), porque é a regra da Fase A e porque é
o único escopo comparável ao do TCC de referência, que migrou os 1.211 `edu`. `mat` e `pro` vão
por `map`. `rel` casa só `rel_escola_gestor.php`: `relatorio_*` e `release_*` não casam
`^rel[0-9]*_`. Ordem: `tre` → `esc`/`rel`/`sec` → `bib` → `mer` (+`mat`/`pro`) → `edu`.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| `tre` | 60 | 3 | 60/60 | 13/13 | 655 linhas, 0 div. | **19/19** (depois do ini) |
| `esc`+`rel`+`sec` | 84 | 19 | 84/84 | 35/35 | 1.368 linhas, 0 div. | **16/16** |
| `bib` | 232 | 79 | 232/232 | 75/75 | 2.632 linhas, 0 div. | **95/98** |
| `mer` + 20 `mat`/`pro` | 507 | 198 | 506/507 | 163/164 | 3.270 linhas, 0 div. | **207/207** |
| `edu3_` + 13 variantes | 591 | 100 + 24 da 9ª lacuna + 9 à mão | 591/591 | 402/404 | 11.451 linhas, 402 classes | **71/71** |
| `edu2_` | 813 | 67 (38 Rector + 29 à mão) | 813/813 | 430/432 | 12.262 linhas, 414 classes | **259/259** |
| `edu4_` | 793 | 110 (101 Rector + 9 à mão) | 793/793 | 501/503 | 13.626 linhas, 483 classes | **140/148** + 8 caracterizadas |
| `edu1_` A (a–c) | 819 | 127 Rector + 15 à mão | 819/819 | 449/451 | 12.436 linhas, 433 classes | **194/196** |
| `edu1_` B (d–m) | 482 | 115 Rector + ~16 à mão | 482/482 | 158/158 | 5.081 linhas, 156 classes | **203/205** |
| `edu1_` C (n–p) | 312 | 82 Rector + 4 à mão | 312/312 | 101/101 | 3.259 linhas, 100 classes | **130/132** |
| `edu1_` D (q–z) | 545 | 118 Rector + 8 à mão | 545/545 | 222/222 | 6.911 linhas, 220 classes | **200/200** |

**`bib`** — 76 pelo Rector (242 guardas, 152 `split` todos `#`, 39 construtores, 33
`parse_str`+`extract`, 3 parâmetros opcionais antes de obrigatórios, 1 `${$var}`), mais 3 à mão:
4 guardas `pg_*` (`bib1_leitor005` ×2, `bib2_racervos002`, `bib2_rmaisempres002`) e o octal
abaixo. As guardas devolvem **`null`**, o valor medido no 5.6 — `bib2_racervos002.php:120`
compara com `=== 0`, exatamente o caso que proíbe a guarda de devolver `0`.

As 3 divergências restantes são **artefatos da bateria**, verificados no caminho real:

- `bib1_emprestimo002.php` — iframe que calcula a data de devolução; a bateria o chama sem
  `ano/mes/dia` e o `mktime()` recebe `"--"`. No uso real o JS manda a data com zeros à
  esquerda e recusa campo vazio. Com 5 datas reais (dia útil, sábado, domingo, Páscoa,
  31/12) a saída é **idêntica** nos dois runtimes. Registro: no 5.6 `mktime()` com string
  NÃO numérica devolve `false` (não coage), então `(int)` **não** seria correção fiel.
- `bib2_comprovantemodelo_80mm/a4.php` — fragmentos incluídos por `bib2_emprestimo002.php`
  (idêntico), que lança exceção antes do include quando não há acervos; `aAcervos` chega
  sempre como array no caminho real.

Regra proporcional: núcleo intocado; a interseção com os universos verificados deu só
`classes/db_aluno_classe.php` × `con` → bateria das 30 telas `con` roteadas: **30/30**.
Os universos de `cem`, `itb`, `agu`, `jur`, `div`, `mar` não estavam em `tmp/` (são
gitignored) e tiveram de ser regerados — universo ausente é *desconhecido*, não *vazio*.

**`mer` + `mat`/`pro`** — universo montado do prefixo `mer` inteiro **mais** as 20 telas
`mat`/`pro` que o banco atribui a Educação (as `mat` também são do Patrimonial: rotear por
prefixo levaria 261 telas de Almoxarifado junto). Rector em 193 arquivos (104 `parse_str`+
`extract`, 88 guardas, 84 `split`, 84 construtores, 2 parâmetros opcionais), só regras vetadas.
À mão, 12 guardas `pg_*` devolvendo `null` em 10 telas — as SQLs falham por colunas que **não
existem** no banco (`me07_i_codmater`, `me22_i_cardapio`), defeito pré-existente.

- `mer1_mer_desper_und003.php` **não compila nem no 5.6** (chave aberta na linha 57). Fora do
  lote, como os 5 do `dbagata/`. O Rector o acusa como `errors: 1` no dry-run — conferir o
  campo `errors`, não só `changed_files`.
- `RequisicaoMaterial` (`.model.php`) diverge no harness de classes: construtor com argumento
  obrigatório, mesmo artefato de `lancamentoContabil`. `db_mer_requiitem_classe_ext.php`
  derruba os dois runtimes igual (o `harness_robusto.sh` o pulou nos dois).
- Regressão: núcleo intocado; interseção com `con` (28 classes) e `pro` (1) → 65/65 telas
  roteadas idênticas.

**Roteamento por `map` agora é por ÁREA.** `gera_map_faseb.py` recebe `<area>:<prefixos>`
(`tribut:amb,pre,… educa:mat,pro`). Ele **reescreve o arquivo inteiro** — repetir todos os
lotes; conferido por diff que só houve 20 linhas acrescentadas e nenhuma removida.

**`edu3_` + variantes** — `edu02_`, `edu03_`, `edu04_` e `edu_` (13 arquivos) não casam
`^edu3[0-9]*_` nem `^edu2[0-9]*_`: mesma armadilha do `jur01_`, por isso entraram no primeiro
lote. Regex usado: `(?:edu(?:3|0)|edu(?=_))` — qualquer alternativa **vazia** (`edu(?:3|)`)
casaria todos os `edu1_`. No nginx idem: a lookahead `edu(?=_)` é o que impede `edu` sozinho de
rotear os subprefixos ainda não portados (verificado: `edu1_aluno001.php` segue no 5.6).

À mão: 13 guardas `pg_*` (`null`) em 6 telas — SQLs sobre relações que **não existem** no banco
(`alunofora`, `alunopassagem`) — e `array_unique(null)`/`natsort(null)` em
`edu3_quadrogeraldehorarioshtml002.php`: no 5.6 devolvem `NULL` e deixam a variável nula; no
8.5 são `TypeError` (o `@` não protege). Corrigido com `is_array()`, que reproduz os dois.

Onze alvos o Rector não tocou: estavam portados pelos commits `EXPERIMENTO: …` do `iss`, que o
`enumera.py` não conta como pagos (só `^Porta `). **Não** passei a contá-los: um experimento
revertido faria arquivo não portado ser pulado — o erro no sentido perigoso. O custo é só
superestimar "a alterar".

**O harness de escrita precisa de UM PROCESSO POR CLASSE.** Com a lista toda num processo só,
cobriu 120 de 404 classes (um fatal o matou) — e o `harness_robusto.sh` não serve para ele,
que emite várias linhas por classe. Em laço, uma classe por `php`: 402 de 404.

**`edu2_`** — 28 divergências na primeira bateria, a maior leva até aqui; todas fechadas:

- **60 guardas `pg_*`** (`null`) aplicadas pelo ciclo automatizado, 18 delas só no
  `edu2_censoescolar002.php` (2.700 linhas). O ciclo passou a cobrir `pg_fetch_assoc/object/
  array/row` (no 5.6 todos devolvem `NULL` sobre `false`) e espaço dentro dos parênteses
  (`pg_numrows( $result )` escapava). Nenhuma linha guardada é seguida de `===`.
- **Divisão por zero** em `EstatisticaAlunosMatriculados.model.php` (9 linhas do total geral, a
  mesma aparição) e `edu2_horarioprofessor002.php`. As 16 linhas iguais por ensino/etapa
  (412–444) **não** foram tocadas: só falham com ensino de zero matrículas, que não apareceu.
- **`cal_days_in_month()` no NÚCLEO** (`std/DBDate.php`): medido em 10 entradas, o 5.6 devolve
  `false` exatamente onde o 8.5 lança `ValueError`/`TypeError` (mês 0, 13, -1, `""`, `null`,
  ano 0…). Correção: `try { … } catch (Throwable $e) { return false; }`. **Catch único**:
  `catch (A | B $e)` é PHP 7.1 e não compila no 5.6; `Throwable` não existe no 5.6, mas o
  `catch` só é avaliado quando algo é lançado, e lá nada é.
- **`file_get_contents("")`**: `false` no 5.6, `ValueError` no 8.5. Guarda por string vazia.
- **`continue` fora de laço** (`edu2_historico002.php:716`): mesma categoria do `break` —
  fatal de execução no 5.6 ("Cannot break/continue 1 level"), de compilação no 8.5. Alcançável
  → **`exit;`**. O `continue` dentro de `switch` da linha 669 equivale a `break` nas duas
  versões (o 8.5 só avisa) e ficou intocado.
- **Ternário aninhado** (`edu2_certconclusao002.php:733`): parênteses à esquerda, conferido nas
  4 combinações de entrada.
- **7ª manifestação da RFC das comparações**, a mais sutil até aqui — num laço de PDF:

  ```php
  $hora = substr($hora,0,2).":".substr($hora,2,2);   // "1:", "2:" ... para os minutos
  if ($hora <= $horafinal) { ... $tt += 1; if ($tt == 60) $t += 40; }
  ```
  `"1:" <= 100` é `true` no 5.6 e **`false`** no 8.5 (string não numérica → comparação de
  string, `':' > '0'`). O laço dá mais voltas, o cursor desce 0,22 pt por volta, e o rótulo
  `01:00` sai **25 pt mais baixo** no PDF. HTTP 200, PDF válido, mesmo tamanho em bytes — só
  descomprimindo o fluxo aparece. Correção `(float)$hora`, conferida em 14 casos.
- `cmp.py` ganhou regra para `tmp/<nome>_<timestamp>.csv|txt` (dentro de JSON a barra vem
  escapada, `tmp\/`): falso positivo em `edu2_relatorioinfradaescolaprocessamento001.php`.

Núcleo tocado (`std/DBDate.php`, `libs/db_stdlibwebseller.php`) → **bateria completa**: Fase A
1.807/1.813, `map` 367/367, Educação anterior 388/391 — todas na linha de base.

**`edu4_`** — à mão: 2 `break` inalcançáveis removidos (logo depois de `db_redireciona()`, que
termina em `exit` — conferido no original **e** na cópia do `modification/`, com `grep -a`), 2
ternários aninhados em linhas de concatenação (o `.` liga antes do `==`; a associação à esquerda
do 5.6 preserva até o bug de "ESTADUAL" nunca aparecer, conferido em 4 entradas), 13 guardas
`pg_*` pelo ciclo, 2 `file_get_contents("")`, 1 `count((array))` (só a linha que apareceu; há
outras 4 iguais no arquivo) e **`pg_last_error()` sem conexão** — `false` no 5.6, `Error` no
8.5 — com o mesmo `try/catch (Throwable)` do `DBDate`. Regressão: núcleo intocado; `con`+`pro`+
`prot` roteadas 70/70.

**`edu1_`: 733 telas, 454 a alterar — o maior lote do projeto, quebrado em 4 sublotes por
letra inicial** (A a–c 196, B d–m 205, C n–p 132, D q–v 200). Cada sublote tem porte,
verificação, roteamento e commit próprios. Enumeração por `edu1(?=_[a-c])` — a lookahead
mantém o `[0-9]*_` que o `enumera.py` acrescenta. No nginx, a faixa entra como alternativa
**fora** do grupo que exige `[0-9]*_`: `(?:(?:cem|…|edu(?=_))[0-9]*_|edu1_[a-c])`. A config nova
foi testada num container descartável **antes** do recreate (o container em execução enxerga o
inode antigo do bind mount e aprova a config velha).

**Sublote A** — 26 divergências na 1ª bateria, 24 fechadas:

- 17 guardas `pg_*` pelo ciclo (+3 à mão: `pg_result(null)`, que o ciclo não reconhecia — ele
  casava só "false given").
- **Constante indefinida** em `forms/db_frmbase.php` e `forms/db_frmalunodados.php`
  (`@Ted31_i_regimemat`, `$GLOBALS[Sed47_c_emailresp]`). **Indefinida também no 5.6** —
  conferido: ele imprime `title="Ted31_i_regimemat"`. Correção fiel em qualquer contexto:
  `(defined('X') ? X : 'X')` — se algum `label()` a definir, usa o valor; senão, o nome, como o
  5.6. Aplicada por ciclo (`const_ciclo`), uma linha por vez.
- **Propriedade sobre `null`** (`edu1_alunoturma002.php:47`): o 5.6 cria `stdClass` sozinho
  para `null`/`false`/`""` (medido; para `0` e array não). Guarda com exatamente essa condição.
- **NÚCLEO `dbforms/db_classesgenericas.php`** (e a cópia do `modification/`): `reset()`,
  `sizeof()` e `key()` sobre `$this->identifica` nulo, em 3 pontos do desenho de abas — no 5.6
  devolvem `NULL`/0 com warning; no 8.5, `TypeError`. `is_array()` + `(array)`.
- `edu1_calendarioescola002/003` **quebram também no 5.6** (500, página truncada no mesmo
  ponto) — caracterizadas.

Núcleo tocado → bateria completa: Fase A 1.806/1.813 (+1 pulada, abaixo), `map` 367/367,
Educação 317/320 e 470/478 (os 8 timeouts do `edu4`) — linha de base.

**Sublote B** — 18 divergências na 1ª bateria, 16 fechadas:

- 11 guardas `pg_*` + `pg_num_fields` (que o ciclo passou a cobrir; `NULL` no 5.6) e 3
  constantes indefinidas pelos dois ciclos.
- **Regra nova do Rector, ACEITA depois de medida:** `ParenthesizeNestedTernaryRector` põe os
  parênteses **à esquerda** — a associação do 5.6, a mesma correção feita à mão até aqui.
  Conferida em 4 entradas (inclusive o bug pré-existente de `NOTA` cair em `valorconceito`).
  Emite só parênteses; não entra na denylist.
- **`break 2` com um laço só** (`edu1_matricula003.php:312`): fatal de compilação no 8.5;
  no 5.6, fatal de execução ("Cannot break/continue 2 levels", medido). Bloco de erro
  alcançável → **`exit;`**, como o `break` do `fis`/`con`. O `break 2` da linha 271 está dentro
  de dois laços e é legal.
- **8ª manifestação da RFC das comparações — NÚCLEO `db_select()`, nos DOIS ramos**
  (`dbforms/db_funcoes.php` + cópia). A correção do `pre` cobria só a segunda metade do teste de
  `selected`. Agora:
  - ramo **somente leitura** (`$db_opcao = 3`): `if (key($db_matriz) == $$nome)` escolhe a
    descrição; com valor `""` e chaves `'' / 0 / 1 / 2`, o 5.6 casa `0 == ""` e mostra
    "NÃO CREDENCIADA", o 8.5 deixa vazio — **campo de formulário em branco, HTTP 200**
    (`edu1_escola003`);
  - ramo **editável**: `$GLOBALS[$nomevar] == key()` deixava de marcar `selected`
    (`edu1_escola002`, 8 bytes).

  Correção nos dois: comparar número com string convertendo a string com `(float)`, que é
  exatamente a conversão do 5.6 (`""`, `"abc"`, `"1x"`), e `==` nos demais casos. **Medido em 12
  combinações de tipos: o emulado no 8.5 = o nativo do 5.6 em todas** (o `==` puro errava 5).
  Inline, sem função auxiliar — o arquivo é incluído por tudo.
- `edu1_escolabase002/003` quebram também no 5.6 (500; `$clescolabase` nunca instanciado, a
  página do 5.6 é cortada antes do trecho que o usa). **Ressalva:** a mensagem do 5.6 não foi
  lida — a aplicação suprime o fatal em todos os logs dela, e uma sonda com `display_errors`
  também não a expôs. Vale igual para `calendarioescola002/003` do sublote A.

Núcleo tocado → bateria completa: Fase A 1.806/1.812 (+1 pulada), `map` 367/367, `edu1` A
194/196, demais Educação na linha de base. Duas "novas" na 1ª passada eram do instrumento:

**Sublote C** — o mais limpo do `edu1`: Rector só com regras vetadas, nenhum erro de lint
prévio, 9 divergências na 1ª bateria fechadas por 6 guardas `pg_*` (as duas restantes,
`edu1_procescola002/003`, quebram também no 5.6 — `$clprocescola` nunca instanciado, mesmo
padrão de `escolabase`/`calendarioescola`). **Interseção com todos os universos verificados
vazia e núcleo intocado → sem bateria de regressão**, pela regra proporcional — a segunda vez
desde o `cai`.

**Sublote D** — faixa `q-z`, não `q-v`, para não depender de não haver letra depois do `v`
(196+205+132+200 = **733**, todas as telas `edu1_`). 7 divergências, todas fechadas — **bateria
perfeita**: 10 guardas `pg_*` (o ciclo passou a casar também "null given"), 1 constante
indefinida, e **contador iniciado com `""`** (`$conta = ""; $conta = $conta + 1`) — `1` no 5.6,
`TypeError` no 8.5; `(int)$conta + 1` reproduz o 5.6 com o tipo certo (é a manifestação que o
TCC de referência corrigiu no PHP8-20 trocando `""` por `0`). Regressão: núcleo intocado;
interseção só com `rec` (1 classe) → a tela `rec` roteada idêntica.

Com o `edu` inteiro portado, o `location` voltou a ter **um `edu` só** no grupo principal, no
lugar de `edu2|edu3|edu4|edu0|edu(?=_)` + a faixa `edu1_[a-p]`. Conferido: `^edu[0-9]*_` casa
exatamente os 1.211 arquivos, e não há outro arquivo começando por `edu` na raiz.

### 🏁 ÁREA EDUCAÇÃO CONCLUÍDA

| | |
|---|---|
| **Módulos completos** | **5 de 5** — Escola 226, Secretaria 214, Alimentação Escolar 62, Biblioteca 39, Transporte Escolar 14 |
| **Telas de menu servidas pelo PHP 8.5** | **555 de 555** (o menu tem 556; uma entrada aponta para arquivo inexistente). ⚠ Contagem por módulo; conferida pelo proxy em 15/10, eram 477 de 480 arquivos distintos — as 3 `mat1_matestoqueini` da *10ª LACUNA*, agora portadas: **480/480** |
| Arquivos roteados | 1.533 por prefixo (`edu` 1.211, `mer` 187, `bib` 98, `tre` 19, `sec` 12, `esc` 3, `rel` 1) + 20 por `map` |
| **Telas comparadas byte-a-byte** | **1.534 idênticas de 1.551 — 98,9%** |
| Divergências | **17, todas caracterizadas, nenhuma defeito de migração** |
| Baterias perfeitas | `tre`, `esc`+`rel`+`sec`, `mer`, `edu3_`, `edu2_`, `edu1_` D |

As 17: **8** telas de importação do `edu4` que entram em laço eterno no 5.6 (`feof(false)`) e dão
500 no 8.5; **6** telas do `edu1` que quebram também no 5.6 (objeto nunca instanciado —
`calendarioescola`, `escolabase`, `procescola`, 002/003 de cada); **3** artefatos da bateria no
`bib` (iframe sem parâmetros e dois fragmentos de include).

Custo efetivo, em arquivos alterados por lote:

```
tre 3   esc/rel/sec 19   bib 79   mer+mat/pro 198   edu3+var 133 (inclui os 24 da 9a lacuna)
edu2 67   edu4 110   edu1 A 142   B 128   C 86   D 126              ~1.091 arquivos
```

O dimensionamento previa **969** para o escopo A (prefixos inteiros); saiu em ~1.091 — +13%, na
mesma direção da Fase B (428 previstos, ~526 reais). A diferença vem das lacunas descobertas no
caminho (9ª lacuna: +30 arquivos) e das correções à mão, que a estimativa estática não enxerga.

**Núcleo tocado na área:** `std/DBDate.php` (`cal_days_in_month`), `dbforms/db_classesgenericas.php`
(`reset/sizeof/key` sobre nulo), `dbforms/db_funcoes.php` (os dois ramos do `db_select`) e
`libs/db_stdlibwebseller.php` — todas com bateria completa na linha de base.

**⚠ 11ª LACUNA (18/10/2026, achada no RH): duas classes da área não CARREGAVAM no 8.5.**
`ImportacaoCenso2012` e `importacaoCodigoInep2010` (universo do `edu4`) tinham assinatura
incompatível com a mãe `importacaoCenso` — LSP entre ARQUIVOS, que o `php -l` não vê (olha um
arquivo por vez) e o harness de classes não vê (só `classes/`). Entram só nas importações do
Censo/INEP com arquivo enviado — as mesmas telas que, por GET sem parâmetro, são os laços
eternos do 5.6. Corrigidas como o catálogo manda (parâmetro da mãe, opcional, na filha):
`getDadosAluno($oLinha, $lPesquisaInep = false)` e `atualizaDadosTurma($oLinha, $iAnoCenso = null)`.
Detector novo: `scratchpad/carrega_arquivo.php` (na branch do RH). Bateria `edu4`: 140/148, linha de base.

### 📐 ÁREA RECURSOS HUMANOS — dimensionada e INICIADA (branch `3recursoshumanos-migrado`)

4 módulos no banco: Pessoal 507 telas, RH 138, eSocial 39, Estágio Probatório 26. Os
prefixos principais são praticamente exclusivos da área:

| Prefixo | Telas de RH no menu | Em outra área | Em disco | A alterar (prefixo inteiro) |
|---|---|---|---|---|
| `pes` | 499 | 2 (Financeiro) | 1.155 | 684 |
| `rec` | 159 | 3 (Assist. Social) + 1 (Tributário, já no `map`) | 279 | 147 |
| `eso` | 33 | 3 (Integrações) | 85 | 27 |
| `rh` | 4 | — | 9 | 2 |
| `es`, `con`, `cai`, `lic`, `sped` | ~10 | compartilhados | — | via `map` |

**Escopo, o mesmo das duas áreas anteriores:** Fase A = `pes`/`rec`/`eso`/`rh` inteiros
(1.528 arquivos, universo 2.687, ~826 a alterar), roteados por `location`; Fase B = as ~10
telas compartilhadas, pelo `map`. Ordem: `rh`+`eso` → `rec` → `pes` (em sublotes).

**Nível 3 e a folha:** a base de exemplo tem **1 servidor** (`rhpessoal`), 3 funções, 2
lotações e **zero** linhas de cálculo (`gerfsal`, `gerfcom`, `gerfres`) e de ponto (`pontofs`,
`pontofx`). Decisão do usuário: nível 3 nos **cadastros** durante o porte; o cenário de
**cálculo** (cadastrar servidores e ponto pelo 5.6 e comparar o SQL do cálculo) fica como etapa
separada, ao fim da área. Atenção: o banco não tem volume de persistência — o cenário teria de
ser salvo em dump.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Classes | Escrita | **Bateria** |
|---|---|---|---|---|---|---|
| `rh`+`eso` | 239 | 29 (Rector, 1 passada + confirmação) | 239/239 | 74/74 | 2.213 linhas, 53 classes, 0 div. | **94/94** |
| `rec` | 568 | 134 Rector + 15 à mão | 568/568 | 171/172 | 4.893 linhas, 139 classes, 0 div. | **278/279** + 1 caracterizada |
| `pes3`+`pes4` | 900 | 148 Rector + ~30 à mão | 900/900 | 440/443 (3 artefatos conhecidos) | 12.839 linhas, 0 div. além dos artefatos | **269/270** + 1 pendente (`.phar`) |
| `pes1` | 1.142 | 256 Rector + 3 à mão | 1.142/1.142 | 482/485 (3 artefatos conhecidos) | 13.257 linhas, 0 div. além dos artefatos | **370/370** |
| `pes2` | 775 | 233 Rector + ~200 à mão | 766/766 portáveis (9 já não compilam no 5.6) | 170/170 | 6.276 linhas, 0 div. | **515/515** |

**`rh`+`eso`** — nenhum arquivo de tela precisou mudar: os 29 são 16 `classes/` e 13 `func_`.
Rector só com regras já vetadas (16 guardas, 13 `parse_str`+`extract`, 10 construtores, 4
`split` todos `"#"`, 2 parâmetros opcionais); portão de funções: só `extract`/`preg_split`. As 21
classes sem saída no harness de escrita não têm `atualizacampos()` nem propriedade inteira — as
mesmas nos dois runtimes. Das 94 telas, 93 dão 200; `eso02_preenchimentoesocial001.php` dá 500
**nos dois** (exceção de negócio "Nenhum tipo de formulário selecionado", tela aberta sem
parâmetro). Log do PostgreSQL: nenhum erro de SQL na bateria. Regressão: núcleo intocado;
interseção só com o universo do `con` (`db_rhpesrescisao_classe.php`) → as 31 telas `con`
roteadas: **31/31**.

**`rec`** — Rector em 134 arquivos, só regras vetadas (66 guardas, 61 `split`/`ereg` com 2
`"\|"`, 61 `parse_str`+`extract`, 61 construtores, 2 parâmetros opcionais, 1 `${$var}`). À mão:

- **Octal inválido, segunda aparição** — `rec2_certcomprobatorio002.php` e `rec2_vantagens002.php`
  (bloco copiado): `$mar1[08]`/`[09]`. No 5.6 os dois valem `0`, então `wv_protel` é
  **sobrescrito** por `wv_inf` — bug pré-existente, preservado com `[0]` (medido: mesmas chaves,
  mesma ordem, mesmos valores). O Rector acusou o primeiro como `errors: 1`; o segundo **não
  estava nos alvos** — o `enumera.py` não detecta octal — e só o `php -l` do 8.5 sobre o
  universo o pegou. Rodar o lint no universo, não só nos alterados, se pagou de novo.
- 10 guardas `pg_*` (`null`) em 9 telas, pelo ciclo; o log do PostgreSQL confirma SQL quebrada
  (erros de sintaxe em `and`/`group`). Nenhuma variável guardada é comparada com `===`.
- 2 `count(null)` → `count((array)…)`.
- **NÚCLEO `libs/db_libpessoal.php`, `db_val()`**: `$string+0` com string totalmente não
  numérica — `0` no 5.6, `TypeError` no 8.5 (medido em 9 entradas; `"12abc"`, `"1.5"`, `null`
  são iguais nos dois). Correção: `try { return $string+0; } catch (TypeError $e) { if
  (is_string($string)) return 0; throw $e; }` — idêntica nas 9 entradas, inclusive no tipo, e
  qualquer outro erro segue como antes. Não há cópia no `modification/`.
- **`is_resource()` sobre resultado do PostgreSQL, de novo** — `forms/db_frmtipoasse.php`: o
  `<select>` de natureza saía **vazio** no 8.5 (9 opções a menos, HTTP 200 nos dois).
  `|| is_object(…)`.
- **CATEGORIA NOVA: método NÃO estático chamado estaticamente** — `JSON::stringify($x)` em
  `rec4_agendaassentamento.RPC.php`. No 5.6 era aviso E_STRICT e funcionava (o método não usa
  `$this`); no 8 é `Error`. A base usa `JSON::create()->stringify(…)` em 680 pontos e a forma
  estática em **3** (esta + 2 em `pes4_eventofinanceiroautomatico.RPC.php`, do lote `pes`).
  Corrigido no ponto de chamada, para a forma das outras 680 — sem mexer na classe do núcleo.
- **Caracterizada, não corrigida:** `rec2_espelhoponto002.php` — `fopen()` de
  `tmp/dados_espelho_ponto_{id}.txt` sem o `id` devolve `false`, e o `while (!feof(false))` da
  linha 71 é **laço eterno no 5.6** (um worker ficou 11 min a ~45% de CPU e segurou o lock da
  sessão); no 8.5 é 500 no `fgets`. Mesma decisão das 8 telas do `edu4`.

Regressão: o núcleo foi tocado, mas **só o corpo de `db_val()` mudou**, e a forma da correção
garante que toda entrada que não era fatal devolve o mesmo valor — logo nenhum módulo já
verificado (todos sem fatal em `db_val`) pode mudar. `db_val` só é chamada por `pes`, `rec`,
`model/pessoal/` e o próprio `db_libpessoal.php`. Rodadas: interseção real (universo do `cai`,
`db_afasta_classe.php` + o núcleo) → 105/105 telas `cai` roteadas; amostra `not`+`mar`+`inf`
79/79. **Não** rodada a bateria completa de ~3.700 telas — decisão consciente, pelo argumento acima.

**`pes3`+`pes4`** (primeiro sublote do `pes`, 270 telas) — 21 divergências na 1ª bateria → 1.

- **11ª LACUNA: LSP entre ARQUIVOS — classes que nem CARREGAM no 8.5.** `FolhaPagamentoSalario`,
  `…Adiantamento` e `…Suplementar` tinham 3 métodos incompatíveis com a mãe `FolhaPagamento`
  (`getProximoNumero`, `getFolhasFechadasCompetencia`, `hasFolhaAberta`), e `PontoFerias::
  adicionarRegistro(RegistroPontoFerias …)` restringia o tipo da mãe `Ponto`. Fatal ao declarar
  a classe; o `php -l` não vê (um arquivo por vez) e o harness de classes não vê (só `classes/`).
  Correção do catálogo — parâmetro da mãe como **opcional** na filha, como a própria
  `FolhaPagamentoComplementar` já fazia; em `hasFolhaAberta` o 1º parâmetro perdeu o *hint*
  `DBCompetencia`, mas o corpo o repassa à mãe, que mantém o *hint* (a checagem continua um nível
  abaixo). Em `PontoFerias` o tipo virou `RegistroPonto` — a única diferença para o 5.6 é aceitar
  um `RegistroPonto` que não seja de férias, que lá era *catchable fatal*; os 2 chamadores reais
  passam `RegistroPontoFerias`.
  **Detector novo, versionado: `scratchpad/carrega_arquivo.php`** — inclui um arquivo com o
  bootstrap da aplicação e diz `OK` ou o fatal; rodar um por processo nos dois runtimes sobre os
  arquivos com `extends`/`implements`. Validado contra a versão antiga de `FolhaPagamentoSalario`.
  Varrido também nos universos já verificados: **2 classes da Educação** (corrigidas na
  `2educacao-migrado`, ver a nota na área Educação) e **10 fora de escopo** — só nos universos de
  prefixo inteiro de `con`/`cai` (relatórios DCASP/RREO, autenticadoras térmicas,
  `PadArquivoEscritorTXT`), de Financeiro/Patrimonial: **pendentes para quando essas áreas vierem**.
- **A denylist cresceu para 30 (SÉTIMA vez):** `AddParamBasedOnParentClassMethodRector` copia o
  parâmetro da mãe como **obrigatório** — quebraria `FolhaPagamentoSuplementar::getProximoNumero()`
  chamado sem argumento — e só vê os alvos, deixando as irmãs fatais.
- **`OptionalParametersAfterRequiredRector`, conferida no `dvr`, falhou aqui:** com parâmetro
  **tipado** ela emite `?FolhaPagamento $x = null` (PHP 7.1 — *parse error* no 5.6), em
  `classes/db_rhhistoricocalculo_classe.php`. Corrigido para `FolhaPagamento $x = null` (aceito
  nos dois; idêntico em 3 entradas). Achado pelo `php -l` **no 5.6 sobre o universo**. A regra
  fica (é segura sem tipo), mas o lint do 5.6 sobre o universo é obrigatório depois dela.
- **Duas regras novas ACEITAS, medidas:** `ConsistentImplodeRector` (`implode($a, ',')` → ordem
  nova; a antiga é fatal no 8) e `ReplaceEachAssignmentWithKeyCurrentRector` (`$x = each($a)` →
  `key`/`current`/`next`, que é a correção do catálogo; o caso tinha `reset()` antes e depois).
- **4 `each()` à mão** (2 `while (list(…) = each(…))` nos modelos de folha, 2 `list() = each()`
  em `pes4_relinconsistenciasiprev002.php`) com `key`/`current`/`next` + `is_array` — medido
  idêntico ao `each()` do 5.6 em 5 casos (vazio, nulo, numérico, associativo com `null`,
  ponteiro no meio), e o 8.5 com a forma nova igual ao 5.6 com a original.
- **Octal, terceira aparição, com bug latente que muda dado:** `pes4_rhfopag91002.php`,
  `db_substr($cLinha, 08, 15)` — no 5.6 `08` vale **0**, então a matrícula da importação do FOPAG
  é lida da coluna 0, não da 8 (o layout pede 8: o PIS começa em 23 = 8+15). Preservado com `0`.
- **NÚCLEO `libs/db_app.utils.php`:** `DB_VERSION` indefinida (telas que chamam `db_app` antes de
  `db_conecta`, que a define) → `(defined('DB_VERSION') ? DB_VERSION : 'DB_VERSION')` nas 4
  ocorrências; com a constante definida o valor é idêntico. Sem cópia no `modification/`.
- Restante: guardas `pg_*` (`null`) em 9 telas pelo ciclo; `count`/`implode`/`array_reverse`/
  `ksort`/`array_walk` sobre nulo com `is_array`/`(array)` **só na linha que apareceu** (há linhas
  iguais não tocadas em `pes4_differias002` e `model/manad.model.php`); `(int)` em `"" + 1`;
  `stdClass` onde o 5.6 o criava sozinho (posto na linha da 1ª escrita, não no `decode`); as 2
  últimas chamadas estáticas `JSON::parse`/`stringify` da base.
- **12ª LACUNA, PENDENTE: biblioteca dentro de `.phar`.** `ext/php/PHPExcel.phar` — **19 de 189**
  arquivos não compilam no 8.5 (0 no 5.6); nenhuma das sete frentes enxerga dentro de um `.phar`.
  Usado só por `pes4_geracaoarquivorefeisul.RPC.php`, que **fica no 5.6** por uma `location` de
  exceção no nginx (antes da regra geral). Portar = extrair, portar como o `dbagata/`, reempacotar.

Regressão: interseção real com universos verificados = 1 classe do `prot` + o núcleo
`db_app.utils.php` (que só muda onde `DB_VERSION` não existe — antes fatal no 8.5) → `prot`
roteadas 4/4, amostra `not`+`mar`+`inf`+`tre` 98/98. Roteamento: `pes3` e `pes4` no `location`;
`pes1_`/`pes2_` seguem no 5.6.

**`pes1`** (370 telas, 2º sublote) — **369/370 já na 1ª bateria**, o melhor do RH; a única era
uma guarda `pg_*` (`null` numa comparação `== 0`, que dá o mesmo resultado nos dois). Rector só com
regras vetadas, convergiu na 2ª passada. À mão, 3 pontos:

- **`split()` com o padrão numa VARIÁVEL digitada pelo usuário** (`pes1_importainfla001.php`,
  `split($separador, …)`, separador vindo do formulário, padrão `;`). O Rector gera
  `preg_split('#' . preg_quote($separador) . '#m', …)` — **literal** —, mas o `split()` POSIX tratava o
  separador como **regex**. Medido no 5.6: com `.` ele quebra em todo caractere, com `\|` separa no
  pipe, e com `|` sozinho (alternativa vazia, erro em POSIX) devolve **`false`**; a forma do Rector
  erra os três. Corrigido para a forma regex mais o caso da alternativa vazia — **idêntica ao `split()`
  do 5.6 em 13 separadores**, nos dois runtimes. Lição: a vantagem do Rector no `split` (converte
  regex certo) vale para padrão **literal no código**; com padrão em variável ele chuta "literal".
- 1 `while (list() = each())` com `key`/`current`/`next` + `is_array` (forma já medida).
- 1 guarda `pg_*`.

`libs/db_libgertxtfolha.php` foi tocado, mas só os universos do `pes` o alcançam — não pede bateria.
Regressão: interseção só com o `prot` (`classes/db_solicita_classe.php`) → 4/4. Detector de LSP:
nada novo nas 70 classes com `extends` do universo. Roteamento: `pes1` no `location`.

**FERRAMENTAL:** `scratchpad/porclasse.sh` (uma classe por processo para os harnesses de classes e de
escrita) agora é versionado — a cópia fora do repositório sumiu entre sessões e só sobreviveu por
estar no `/tmp` compartilhado dos containers. O portão de funções passou a ignorar comentários de
linha (era a origem do falso positivo `mae` do sublote anterior).

**`pes2`** (515 telas, último sublote — quase todo de relatórios) — 344/515 na 1ª bateria → **515/515**.

- **185 guardas `pg_*` (`null`) pelo ciclo, em 145 arquivos** — o maior volume do projeto. Causa medida no log
  do PostgreSQL: as telas `*002.php` são relatórios que a bateria abre **sem os parâmetros** do formulário
  anterior, e a SQL sai com buracos (`… = and …`: 615 erros de sintaxe perto de `and`, 131 perto de
  `join`). O 5.6 seguia com `false`, caía no "sem dados" e redirecionava (~110 bytes); o 8.5 parava no
  `pg_numrows`. Revisão: **nenhuma** das variáveis guardadas é comparada com `===`/`!==` nos 145 arquivos.
- **9 arquivos que já NÃO compilam no 5.6**, deixados intocados como os do `dbagata/`: as 8 telas de
  **geração de arquivo bancário da folha** (`pes2_*emitearqbanco*`, `*contramatricial002`,
  `emitebb200lay002`, `emitearqbancocnab240_002`) — passagem por referência na **chamada**
  (`db_setaPropriedadesLayoutTxt(&$x, …)`), erro de compilação desde o PHP 5.4 — e
  `pes2_arrcontramatricial001.php`. Os `split`/`parse_str` que sobram no universo estão todos neles
  (contador por *token* sobre os 766 portáveis: zero).
- **Denylist 30 → 31 (OITAVA vez): `RemoveReferenceFromCallRector`.** Remove o `&` dessas chamadas — só
  pode agir em código que já não compila no 5.6, então toda aplicação dela é **conserto**.
- **`break` fora de laço**: `pes2_relcad001.php` — 6 blocos de erro alcançáveis → `exit;`, com o `php -l` do
  8.5 dirigindo um a um (os 6 `break` restantes estão em laços); `pes2_relfichafinanceiratxt002.php` —
  logo depois de `db_redireciona()` (que termina em `exit` no original e na cópia) → removido.
- **5 `each()` em `fpdf151/pdf2.php`** (parte da dívida da *6ª lacuna*): forma `key`/`current`/`next` dentro
  da condição do `while`, medida idêntica ao `each()` do 5.6 inclusive com `break` e na posição do
  ponteiro depois do laço. O `pdf4.php` ainda tem 5 `each()`, não alcançados.
- Família "argumento inválido virou `TypeError`/`ValueError`", na linha que apareceu: `mktime()` com
  `substr()` de data vazia (o 5.6 recebia `false` → 0 → `mktime(0,0,0,0,0,0)` = 943927200; `(int)` em cada
  `substr` reproduz), `file("")`, `fputs`/`fclose(null)`, `count`/`sizeof(false)` (= 1 no 5.6, igual a
  `(array)false`), `cal_days_in_month` (`try`/`catch`), `db_formatar()` com 1 argumento (o `null` explícito),
  `pg_result` aninhado e `stdClass` sobre `null`.
- **9ª manifestação da RFC das comparações — NÚCLEO `fpdf151/fpdf.php:967`, `Cell()`:** `if($align=='R')`
  com o alinhamento passado como inteiro `0`. No 5.6 `0 == 'R'` é verdadeiro e a célula saía **à direita**;
  no 8.5, à esquerda. HTTP 200, PDF válido, 2 bytes de diferença — só descomprimindo o `FlateDecode` se via
  o `x` da célula mudar de 35,79 para 17,01. Correção `|| $align===0 || $align===0.0`, igual ao 5.6 em 10
  valores. As irmãs `=='J'` (l. 1157) e `=='U'/'D'` (l. 2907–2932) têm a mesma forma e **não** foram tocadas
  (não apareceram). Sem cópia no `modification/`.

Regressão: o núcleo foi tocado (`fpdf.php`), mas a mudança só altera o caso em que o 8.5 já gerava PDF
diferente do 5.6 — e todas as baterias anteriores comparam bytes de PDF. Rodada mesmo assim a bateria dos
lotes de RH já verificados + relatórios `iss2_`: **1.084/1.086**, exatamente as duas caracterizadas (`.phar` e
`rec2_espelhoponto002`). Roteamento: com os 1.155 `pes*_` portados, o `location` voltou a um `pes` só; a
exceção do `.phar` continua antes dele.

#### 🏁 FASE A DA ÁREA RH CONCLUÍDA — `rh`, `eso`, `rec`, `pes` inteiros

| | |
|---|---|
| Telas roteadas por `location` | **1.528** (`pes` 1.155, `rec` 279, `eso` 85, `rh` 9), menos 1 exceção do `.phar` |
| **Bateria** | **1.526 / 1.528** — as 2 restantes são o laço eterno do 5.6 (`rec2_espelhoponto002`) e a pendente do `.phar`. Entre as idênticas estão `eso02_preenchimentoesocial001` (o mesmo 500 de negócio nos dois) e as 9 do `pes2` que não compilam no 5.6 (falham igual) |
| Arquivos alterados | **849** nos cinco lotes (contados pelo git) |

**PARA RETOMAR:** a Fase B
(as ~10 telas de `es`/`con`/`cai`/`lic`/`sped` pelo `map`), o `.phar`, o nível 3 nos cadastros e o
cenário de cálculo. A sessão autenticada usada foi `98d016cc…`; os ciclos de guarda precisam de
`/tmp/_sess.bak` no 5.6 (o `cmp.py` o cria ao rodar).

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

##### ⚠ O instrumento, de novo: resposta cortada pelo `curl -m 60` virava divergência

`mer3_mer_nutriitem002.php` leva **~53 s nos dois runtimes** (495 alimentos, uma consulta por
item). Sob a carga da bateria passa de 60 s, o `curl` corta a resposta — **com código 200** — e
cada lado corta num ponto diferente: 1,3 MB contra 1,3 MB, depois 2,65 MB contra 2,48 MB.
Isolada, dá 2.652.582 bytes idênticos nas duas portas. O `cmp.py` passou a registrar o
`time_total` e trata resposta que bate no limite como `TIMEOUT`. `bib2_reditoras002` (1 byte) é
o horário dentro do PDF comprimido: idêntica em 4 repetições isoladas.

##### ⚠ CORREÇÃO ao catálogo: por que é o ORIGINAL que executa, e não a cópia do `modification/`

A seção *CRÍTICO: `modification()`* diz que as cópias executam; a sonda do `pre` mostrou o
original executando, sem explicação. **O mecanismo, lido em `definitions.php` e
`src/V3/Modification/Data/FileSync.php`:**

1. se o arquivo de sincronia é **mais novo** que o original → usa a cópia;
2. se o original é **mais novo** (toda vez que edito um arquivo do núcleo) → tenta **regenerar**
   a cópia reaplicando as modificações XML sobre o original;
3. a regeneração **falha** — `extension/modification/log` não é gravável pelos containers — e o
   `catch` devolve **o original**. O `application.log` registra isso: **225 mil** linhas
   `modification() - update file: … Não foi possível abrir o arquivo para escrita`.

Consequências: neste ambiente, para todo arquivo editado depois da sincronia, **os dois
runtimes executam o original** — a comparação continua válida, mas as correções replicadas nas
cópias **não estão sendo exercitadas**. Num ambiente com a pasta gravável, as cópias seriam
**regeneradas a partir do original já portado** (o desejado), desde que as modificações XML
ainda se apliquem. Manter as cópias corrigidas continua sendo o lado seguro.

##### ⚠ A bateria contatava um servidor EXTERNO real: `iss4_siss002.php`

Apareceu como `TIMEOUT` nos dois runtimes, numa tela antes idêntica. É um script de lote (lê
`$argv`) com **IP de terceiro fixo no código**: `$DB_SERVIDOR_SISS = "200.192.137.56"`
(`colocation.sissbr.com.br`). Cada execução da bateria disparava um `pg_connect` a esse
servidor; hoje ele leva **134 s** para desistir, igual nos dois — antes a rede recusava na hora.
Não é regressão; é rede. Mas **testes automatizados não podem contatar serviço real de
terceiros**: o `cmp.py` ganhou a lista `PULAR`, reportada como `PULADA`.

##### ⚠ CATEGORIA NOVA (edu4): `while (!feof(false))` — LAÇO ETERNO no 5.6, 500 no 8.5

```php
$ponteiro = fopen($arquivo_erro, "r");     // GET sem parametros: "" -> false
while (!feof($ponteiro)) { ... }           // 5.6: feof(false) = false -> NUNCA termina
                                           // 8.5: fopen("") e ValueError -> 500 imediato
```

**8 telas** (`exportarsituacaoaluno002`, `importacaoatualizacaoaluno002`, `importarcodigoinep002`,
`importarcodigoinep_2009_002`, `importarmatriculainep002`, `atualizacadastrocenso002`,
`atualizacadastrocenso_2009_002`, `verifexportcenso002`). Um worker do 5.6 ficou **32 minutos a
100% de CPU** antes de eu encerrá-lo. **Não corrigidas, e é decisão:** a correção "fiel"
reproduziria um laço infinito. Quebram nos dois — o 5.6 pendurando um worker, o 8.5 com um
500 —, e cabem em *"uma tela que quebra igual nos dois não é problema nosso"*. Só disparam com
o `GET` sem parâmetros; no uso real a tela anterior passa o caminho do arquivo.

##### ⚠ O INSTRUMENTO, de novo: timeout nos dois contava como IDÊNTICO — e travava o resto

O `cmp.py` desistia em 60 s, mas **o PHP seguia rodando** no servidor, segurando o `flock` do
arquivo de sessão. Como a sessão é compartilhada, **toda tela seguinte travava nos dois
runtimes** — e "000 nos dois" era contado como idêntico. Sintoma: bateria de 148 telas passando
de 10 minutos, e duas telas inocentes (`exportarsituacaoalunonovo001`, `…aluno.RPC.php`)
aparecendo como "travadas" por virem logo depois de um órfão.

Corrigido no `cmp.py`: `000` em qualquer lado vira **`TIMEOUT`**, contado à parte, e o worker
órfão (estado `R`) daquele container é encerrado. Refeita a bateria: 132 idênticas, 10
divergentes, 6 timeouts — e as duas inocentes ficaram idênticas.

Duas armadilhas no diagnóstico, as duas da família *verificação que falha em silêncio*:

- **`ls -l /proc/<pid>/fd` dá `Permission denied`** dentro do container (restrição de
  ptrace), e com `2>/dev/null` o resultado vazio pareceu "nenhum processo segura a sessão".
  Duas hipóteses descartadas com base numa checagem que não enxergava nada.
- **`grep` sem `-a`** sobre `libs/db_stdlib.php` (LATIN-1) não achou o `exit` do
  `db_redireciona` — o arquivo foi tratado como binário.

**Baterias anteriores:** nenhuma teve duração anormal, que é o sintoma deste defeito; o risco
de "timeout contado como idêntico" existia, mas não há sinal de que tenha ocorrido.

#### ⚠ 9ª LACUNA: `getdao` em minúsculas — a enumeração era sensível a maiúsculas no MÉTODO

`edu3_atolegal001.php` morria com `label() on null`:

```php
$oDaoAtoLegal = db_utils::getdao('atolegal');   // minusculas
$oDaoAtoLegal->rotulo->label();                 // rotulo nulo: o construtor PHP 4 nao rodou
```

A 7ª frente procurava `getDao` com regex sensível a caso; PHP não diferencia maiúsculas em nome
de método. Escala na base: `getDao` 4.020 chamadas, **`getdao` 766, `getDAO` 13, `GetDao` 2 —
781 chamadas em 244 arquivos invisíveis**. As frentes de `include`/`require` e `new cl_*`
tinham a mesma fraqueza; as três passaram a `re.I`, e a resolução do nome tenta também o
arquivo em minúsculas.

Impacto medido **retroativamente** (universo novo − universo antigo, por lote): Tributário
**+1 arquivo** (`iss`); Educação **+30**, porque o `getdao` minúsculo é idioma do código de
Educação. Dos 30, **24 ainda precisavam de porte** (17 construtores PHP 4, 21 com guardas
faltando) — 16 deles nos lotes `rel`/`sec`/`bib`/`mer` já commitados, e
`db_issmovalvaraprocesso_classe.php` no `iss`. Portados neste lote; baterias refeitas de todos
os lotes afetados: `tre` 19/19, `esc`+`rel`+`sec` 16/16, `bib` 95/98, `mer` 187/187, `map`
20/20, `iss` 397/400, `con`+`rec` roteadas 31/31 — **todas na linha de base**.

É a nona vez da mesma falha de método, e a segunda de maiúsculas (a primeira foi `Cem1_` no
nome do arquivo). Achada como as outras: por uma tela que quebrou, não por varredura.

#### ARMADILHA DE FERRAMENTAL: o opcache do 8.5 revalida a cada 2 s

Automatizei o ciclo "requisitar → ler o fatal → guardar a linha → repetir". Ele aplicou a
mesma guarda **15 vezes aninhada** na mesma linha: o 8.5 tem `opcache.revalidate_freq = 2`, e
a requisição seguinte chegava antes da revalidação, executando o código antigo e acusando o
mesmo fatal. Desfeito (uma guarda por linha, diff conferido). **Esperar 3 s depois de editar e
antes de requisitar.** O 5.6 não tem opcache, então o sintoma só aparece de um lado.

#### CATEGORIA (bib): octal inválido — a correção fiel PRESERVA o bug

`bib1_reserva004.php:64`, fatal de compilação no 8.5 (*Invalid numeric literal*), arquivo que
nenhuma regra do Rector tocou:

```php
if($mes == 04 || $mes == 06 || $mes == 09 || $mes == 11){   // meses de 30 dias
```

```
PHP 5.6:  var_dump(09, 08, 019)  ->  int(0) int(0) int(1)   (para no 1o digito invalido)
PHP 7+:   parse error
```

No 5.6 `$mes == 09` é `$mes == 0`: **setembro nunca entra no ramo dos meses de 30 dias** —
bug pré-existente no cálculo da data da reserva. Corrigido para `0`, com comentário, e não
para `9`: escrever `9` mudaria a saída do `:8080`.

Correções: 104 guardas `== <literal>`, 34 `split` → `preg_split` (todos `#`), 17 construtores,
4 `parse_str`+`extract`. O Rector aplicou só regras já vetadas — **denylist inalterada (29)**.
Entre os alvos estão `db_turma_classe.php` e `db_matricula_classe.php`, duas das quatro classes
em que a branch do TCC de referência deixou as guardas `0 == ""` de fora.

### ⚠ CATEGORIA NOVA: AMBIENTE — o php.ini do 8.5 não reproduzia o do 5.6

Achada em `tre2_linha001.php`: HTTP 200 nos dois, **1 byte** no 8.5, nenhum fatal em log
nenhum. O arquivo começa com um **espaço antes do `<?php`**:

```
5.6  output_buffering = 4096  (php.ini do Ubuntu)  -> o espaco fica no buffer, a sessao abre
8.5  output_buffering = 0     (imagem sem php.ini) -> o espaco sai, os cabecalhos ja foram,
                                                      a sessao nao abre e a tela encerra
```

Corrigir no código mudaria a saída do `:8080` (é conserto, não migração). A correção fiel é de
**ambiente**: `docker/php85-apache/paridade-56.ini`, montado em `conf.d` por
`docker-compose.php85.yml`. **Não por rebuild**: o rebuild falhou sem rede para o
`deb.debian.org` e, pior, a camada do `apt` não estava em cache — reconstruir reinstalaria todos
os pacotes em versão nova, outra variável. Com o bind mount o binário segue **8.5.10**.

Comparadas as 228 diretivas dos dois runtimes web, há mais quatro que mudam saída e **não**
foram alinhadas, por falta de defeito observado (regra de corrigir na aparição):

| Diretiva | 5.6 | 8.5 | Risco |
|---|---|---|---|
| `serialize_precision` | 17 | -1 | `json_encode(0.1)` → `0.10000000000000001` × `0.1`; `.RPC.php` com dinheiro |
| `request_order` | GP | (vazio) | `$_REQUEST` passa a incluir cookies |
| `variables_order` | GPCS | EGPCS | `$_ENV` preenchido |
| `default_charset` | UTF-8 | ISO-8859-1 | só o cabeçalho HTTP |

Escala da forma achada: **3 scripts na raiz** com saída antes do `<?php` (`tre`, um `emp`, um
`sau`) — nenhum no Tributário, por isso nenhuma bateria anterior a viu.

#### ⚠ CORREÇÃO: 8 das 14 divergências "caracterizadas" do Tributário eram ESTA causa

Bateria completa depois do ini: **Fase A 1.807/1.813, Fase B 347/347 — 2.154/2.160**. Antes
eram 14 divergências; sobraram **6** (2 fragmentos do `agu`, `fis1_sanitario004`, as 3 do
`iss`). As 8 que sumiram — as 4 do `itb`, `cem1_itenserv002`, `jur_enviarremessatj`,
`fis1_tiafprazoproc002/003` — **quebram nos dois** e agora devolvem a **mesma** página de erro
(ex.: 500/4.558 B nos dois). O defeito é da referência, como estava registrado; mas a
*divergência* era o buffer: no 5.6 o tratador de erro descartava a saída retida e emitia o 500,
no 8.5 a saída já tinha ido e restava um 200 truncado.

**Lição:** "quebra no 5.6 e funciona no 8.5" era leitura errada do sintoma — o 8.5 não
funcionava, só não conseguia mais *dizer* que falhou. Paridade de ambiente faz parte da
invariante "a única variável é a versão do PHP", e ela nunca tinha sido medida diretiva a
diretiva.

### FERRAMENTAL: duas armadilhas de hoje

- **O harness não está no container.** `scratchpad/` fica na raiz, fora do bind mount
  (`./ecidade`). Chamado como `/var/www/html/scratchpad/escrita.php`, o php não acha o arquivo,
  a saída sai **vazia nos dois** e o diff vazio parece aprovação. Copiar com `docker cp` (a skill
  foi corrigida; o manual já fazia assim).
- **Lista sem `\n` final perde o último arquivo no `while read`.** O `enumera.py` gravava sem;
  o lint do `tre` verificou 59 de 60. Corrigido na origem.

### Estado atual: NÚCLEO PORTADO ✅

Os 24 arquivos do núcleo rodam em PHP 8.5. **A tela de login renderiza byte-a-byte idêntica
nos dois runtimes** (12.009 bytes; única diferença é o id aleatório do captcha).

```
antes:  8085 -> HTTP 500 (ParseError em libs/db_stdlib.php:149)
agora:  8080 -> HTTP 200 | 12.009 bytes
        8085 -> HTTP 200 | 12.009 bytes   <- idêntico
```

Alterações: **9 arquivos, ~70 linhas**. Nenhum fatal da aplicação no log do 8.5.

| Arquivo | Correções |
|---|---|
| `libs/db_stdlib.php` | 2 offsets `{}`, 11 `ereg_replace`→`preg_replace`, 1→`str_replace`, 1 `each`→`foreach` |
| `libs/JSON.php` | 40 offsets `{}` |
| `fpdf151/fpdf.php` | 3 offsets `{}`, remoção de `get_magic_quotes_runtime()` (variável morta) |
| `dbforms/db_classesgenericas.php` | 3 `split`→`explode` |
| `libs/db_libpessoal.php` | 1 `split`→`explode`, 2 `each`→ponteiro explícito |
| `std/DBString.php` | 1 `ereg_replace`→`str_replace` |
| `libs/db_calcula.php`, `libs/db_utils.php`, `classes/db_cgm_classe.php` | construtor PHP4 → `__construct` |

**Restrição descoberta na prática:** os dois containers montam o MESMO diretório, então toda
correção precisa funcionar em PHP 5.6 **e** 8.5. Isso é bom — força o código a ficar
version-agnostic antes de migrar, que é o pré-requisito do strangler fig. Todo arquivo
alterado passa `php -l` nos dois runtimes.

### Estado: MÓDULO PILOTO `tra` PORTADO ✅

96 arquivos (62 scripts da raiz, 13 `libs/`, 11 `classes/`, 10 `forms/`) — **todos passam
`php -l` em 5.6 E em 8.5**. Varredura final: zero construções removidas, zero construtores PHP4.

| Correção | Qtd |
|---|---|
| `split(` → `explode(` (todos com padrão literal `"#"` e `"\n"`) | 50 |
| construtor PHP4 → `__construct` | 23 |
| assinaturas incompatíveis com a classe pai (LSP) | 7 |
| `each(` → `foreach` | 3 |
| offsets `{}` → `[]` | 3 |
| `ereg(` → `preg_match(` | 3 |
| `=& new` → `= new` | 1 |
| `(double)` → `(float)` | 1 |

**Verificação funcional:** as 11 classes do módulo instanciam com estado **byte-a-byte idêntico**
nos dois runtimes (mesmo número de propriedades, mesmo md5 do estado inicializado). Isso valida
diretamente as 23 correções de construtor, que é a mudança de maior risco.

Limitação conhecida: as 62 páginas HTTP só puderam ser comparadas até a checagem de sessão
("Sessão inválida (12)"), idêntica nos dois. Verificação ponta a ponta com sessão autenticada
ainda está pendente — é o próximo passo natural do piloto.

### Estado: PILOTO `cem` (Cemitério) PORTADO ✅

**187 arquivos** — 113 scripts da raiz, 35 `classes/`, 33 `forms/`, 4 `funcoes/`, 1 `libs/`,
1 `model/` (os 24 do núcleo já estavam prontos; zero sobreposição com o `tra`).

| Correção | Qtd |
|---|---|
| `split(` → `explode(` (todas com padrão literal `"#"`) | 136 |
| construtor PHP4 → `__construct` | 36 |
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 198 |

Nenhuma outra categoria apareceu: zero `each(`, zero offsets `{}`, zero `ereg*`, zero
`=& new`, **zero violações de assinatura (LSP)** — as 7 do `tra` estavam todas no jpgraph,
que o `cem` não usa. Nenhum arquivo do `cem` é sobrescrito em `extension/modification/`.

Verificações (todas passaram):

| Critério | Resultado |
|---|---|
| `php -l` nos 187 arquivos, **nos dois runtimes** | 187/187 OK em 5.6 e em 8.5 |
| As 35 classes instanciadas via bootstrap da app | estado **idêntico** (mesmo nº de props, mesmo md5) |
| 113 páginas HTTP comparadas 5.6 × 8.5 | **113 idênticas, 0 divergentes** |
| Fatais no log durante o teste | nenhum |
| Roteamento no proxy | `/cem1_*` responde `X-Powered-By: PHP/8.5.10` |

### Verificação ponta a ponta do `cem` COM sessão autenticada

Metodologia que finalmente encontra defeitos reais: restaurar uma sessão válida antes de
cada requisição e comparar as 113 páginas byte-a-byte entre `:8080` (5.6) e `:8085` (8.5),
**normalizando identificadores aleatórios**. A lista completa de regras, cada uma nascida de
um falso positivo real:

| Regra | Por quê |
|---|---|
| `sid=<hex>` | id de sessão, muda a cada requisição |
| `arquivo=<base64>` | caminho do iframe temporário |
| `wname<n>` | nome da janela do desktop v3 |
| `iframe<rnd>.php` | temporário de `tempnam()` |
| `<hex de 32>` | md5 de nomes de arquivo |
| `tmp/<nome>.pdf` | PDF temporário: o nome carrega **PID e timestamp** |
| `localhost:8080` / `:8085` | a **página de erro** monta URL absoluta a partir de `HTTP_HOST` (ver `$DB_URL_ABS`), então carrega a porta do runtime que a serviu |
| `/CreationDate (D:…)` | data gravada dentro do PDF pelo FPDF; só passou a aparecer quando `tmp/` virou gravável e os relatórios começaram a ser gerados de fato |

**Normalizar não basta: é preciso CONFIRMAR antes de acusar.** Os relatórios carregam um
horário **dentro do fluxo comprimido** (`FlateDecode`) do PDF, fora do alcance de qualquer
regex. Se as duas requisições caírem em segundos diferentes, os bytes mudam — às vezes
mantendo o mesmo tamanho, o que faz a divergência parecer conteúdo diferente. O comparador
refaz o par uma vez antes de registrar: **uma regressão real é persistente, um flake não.**
Sem isso, `agu2_relconsumo002` aparecia e sumia entre execuções.

As duas últimas foram descobertas no `agu` e valem retroativamente: sem elas, telas de
relatório e telas de erro aparecem como divergentes de forma **intermitente**, porque só
divergem quando o PID ou o segundo do relógio mudam entre as duas requisições. Falso positivo
intermitente é o pior tipo — ele some quando se vai investigar.

**Teto de saída obrigatório no comparador.** Uma página com laço infinito (ver a categoria
`-1 >= ""`) devolve centenas de MB e o gerenciador de memória mata o comparador com SIGKILL,
sem traceback. O sintoma é a bateria morrer sempre no mesmo ponto e parecer travamento.
Truncar em ~5 MB resolve: a página truncada perde o marcador de status e cai como divergente,
que é o desfecho correto.

```bash
SID=<sessao com DB_modulo>   # achar com: grep -la DB_modulo /var/lib/php/sessions/sess_*
# restaurar a sessao antes de CADA requisicao: uma requisicao a consome/reescreve
docker exec -u root ecidade_php56 sh -c "cp /tmp/sess.bak /var/lib/php/sessions/sess_$SID; chown www-data:www-data ..."
curl -b "ECIDADEWINDOWMAIN=$SID" http://localhost:8080/<pagina>
```

Evolução: **14 divergentes → 4**, com 5 defeitos reais corrigidos no caminho.

| Defeito | Onde | Correção |
|---|---|---|
| `0 == ""` mudou (ver seção própria) | 35 classes do `cem` | 198 comparações |
| `parse_str()` com 1 argumento (obrigatório desde 8.0) | 62 arquivos do `cem` | `parse_str($s,$a); extract($a);` |
| `pg_numfields(false)` → TypeError | `db_fieldsmemory()` no núcleo | retorno antecipado |
| `pg_result(false)` → TypeError | `db_stdlib` 2×, `db_libsys` 1× | operador ternário |
| `"" == 0` no `db_select()` | `dbforms/db_funcoes.php` (núcleo) | condição extra para string vazia |

**Divergências restantes: 2 — 114 de 116 idênticas.**

- `cem1_itenserv002.php` — **quebra no 5.6 (500) e funciona no 8.5 (200)**. Defeito
  pré-existente da referência (`label() on null` em `forms/db_frmitenserv.php:29`), não da migração.
- `cem2_emitecertisen002.php` — ambos falham ao gerar o relatório e redirecionam para a
  **mesma** mensagem; o 5.6 emite antes um `<b>Mensagem: </b>` vazio. Causa: o diálogo de erro
  do `dbagata/`, cujos construtores PHP 4 não rodam no 8.5. Ver *5ª LACUNA*.

`cem3_sepultamentos004.php` e `cem2_renovacoes.php`, antes divergentes, ficaram **idênticas**
— foram resolvidas pelas guardas `pg_*` acrescentadas ao núcleo depois.

### PENDÊNCIA DE DECISÃO: 140 chamadas `pg_*` sem verificação no núcleo

O padrão `$r = db_query(...); pg_numrows($r);` sem checar `$r` é sistêmico. No 5.6 passava
`false` adiante e a função devolvia `false` (que `== 0`); no PHP 8 é `TypeError` fatal.

**⚠ CORREÇÃO (medida depois do `arr`): a causa NÃO é tabela vazia.** Este arquivo registrava
que o defeito "ocorre sempre que a consulta traz zero linhas". Está errado — verificado nos
dois runtimes:

```
consulta VALIDA com zero linhas  ->  resultado normal, pg_numrows() = 0
SQL INVALIDA                     ->  false
```

`pg_query()` só devolve `false` quando **a própria SQL falha**. Os ~112 pontos guardados ao
longo de 11 módulos não são tabelas vazias: são **consultas quebradas**, defeitos
pré-existentes que o 5.6 engolia. Exemplo real, de `arr2_rellistadqd002.php`:

```
ERRO: coluna "declaracaoquitacao.ar30_exercicio" deve aparecer na clausula GROUP BY
```

Esse `GROUP BY` malformado erra no PostgreSQL **independentemente da versão do PHP**; a única
diferença é que o 5.6 passa o `false` adiante e o 8.5 fatala.

| Arquivo do núcleo | Chamadas não protegidas |
|---|---|
| `libs/db_stdlib.php` | 86 |
| `dbforms/db_funcoes.php` | 24 |
| `dbforms/db_classesgenericas.php` | 19 |
| `libs/db_libsys.php` | 11 |
| **Total** | **140** |

Na base inteira: **100.814 chamadas `pg_num*`/`pg_result` sobre variável, em 7.885 arquivos**.

**DECISÃO TOMADA: corrigir conforme os defeitos aparecerem, não em massa.**

Foram corrigidos apenas os pontos que quebraram de fato (4 dos 140). A varredura em massa
(`pg_numrows($x)` → `($x ? pg_numrows($x) : 0)`) foi **descartada deliberadamente**: mexeria
em ~136 pontos sem evidência de que precisavam mudar, e traz risco próprio — para
`pg_result`, o 5.6 devolvia `false` e o substituto devolveria `""`, equivalente sob `==` mas
**não** sob `===`. Uma regressão silenciosa introduzida ao tentar prevenir outra.

O procedimento é: página quebra → ler `extension/log/error.log` → corrigir aquele ponto →
rodar a bateria das 113 páginas para confirmar que nada mais mudou. Os números acima ficam
registrados como estimativa de esforço restante, não como lista de tarefas.

#### ✅ A decisão de não varrer em massa, agora MEDIDA

A pergunta "não dá para automatizar isso?" foi levantada e medida, em vez de respondida por
hábito:

| | |
|---|---|
| Chamadas `pg_num*` sem guarda no universo do `arr` | **1.083** em 526 arquivos |
| Quantas de fato precisaram de guarda | **1** |
| Idem no `dvr` | 685 no universo, 4 necessárias |
| `pg_result`/`pg_fetch_result` na base inteira | **84.077** — 81% do total |
| **Risco da varredura** (resultado comparado com `===` a jusante) | **25 pontos na base** |

A taxa de acerto de uma varredura seria de **~0,1%**. E o risco é concreto, não teórico: em
`con2_razaodespesa002.php:170` há `if ($rows === 0)`. Com a guarda devolvendo `0`, a condição
passa a ser verdadeira onde no 5.6 (`false === 0`) era falsa. **Varrer em massa introduziria
regressão em 25 pontos para prevenir cerca de um por módulo.**

#### ✅ O que DÁ para automatizar: a descoberta, pelo log do PostgreSQL

Como toda falha é erro de SQL, **o PostgreSQL já registra todas**. Uma passada da bateria com o
log capturado lista todos os pontos de uma vez, em vez de descobrir um por rodada:

```bash
docker logs --since 20m ecidade_database 2>&1 | grep -aA1 'ERRO:'
```

**O log está em PORTUGUÊS** (`ERRO:` / `INSTRUÇÃO:`), por causa do locale `pt_BR.ISO-8859-1` do
cluster. Um `grep 'ERROR:'` não acha nada — e falha em silêncio, como as outras armadilhas deste
arquivo. `log_min_error_statement` já vem em `error` e `logging_collector` está `off`, então os
erros saem no stderr do container; não é preciso configurar nada.

Validado ponta a ponta: revertendo a guarda de `arr2_rellistadqd002.php`, a tela volta a dar 500
no 8.5 e o log aponta a consulta exata.

**Ganho medido:** isso troca N rodadas de bateria por 1. O custo real do método nunca foi o
número de guardas, e sim a iteração — `fis` precisou de 2 rodadas, **`iss` de 4**, `dvr` e `arr`
de 1.

**Deixado intencionalmente sem tocar:** `libs/db_libsys.php:180` usa
`session_is_registered("DB_NBASE")`, função removida no PHP 5.4 mas **polyfilled** por
`vendor/dbseller/legacy/bootstrap/PHP_53.php`. Funciona igual nos dois runtimes; alterá-la
seria mudança de comportamento, não migração.

Pendente: validação ponta a ponta no navegador com sessão autenticada, navegando o menu
Cemitério em `http://localhost:8090`.

### Estado: MÓDULO `itb` / `itbi` (ITBI) PORTADO ✅ — 2º da área Tributário

**192 arquivos** — 120 scripts da raiz, 42 `classes/`, 30 `forms/`.

Atenção ao prefixo: o módulo usa **`itb` E `itbi`** (`itb1_*` 110 arquivos, `itbi_*` 10).
Enumerar só `^itb[0-9]*_` deixaria 10 de fora. Regex correta: `^itbi?[0-9]*_` com IGNORECASE.

| Correção | Qtd |
|---|---|
| `split(` → `explode(` (literais `"#"`, `"X"`, `","`, `'-'`) | 143 |
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 264 |
| `parse_str()` com 2º argumento | 54 |
| construtor PHP4 → `__construct` | 36 |
| guardas `pg_*` contra resultado falso | 14 |
| cast `(float)` em aritmética com string | 2 |

Verificações: `php -l` **192/192 nos dois runtimes**; as 42 classes instanciam com estado
idêntico; **116 de 120 telas byte-a-byte idênticas** com sessão autenticada (era 113 antes
das correções de autoload e das guardas do núcleo).

**Zero páginas quebrando no 8.5.** As 2 divergências restantes **quebram no 5.6 e funcionam
no 8.5** — `itb1_itbiavalia002/003` e `itb1_itbidadosimovel003`/`itb1_itbinome011`, todas com
`label() on null` nos `forms/db_frmitbi*.php`: defeito pré-existente da referência, não da
migração. Mesmo padrão visto em `cem1_itenserv002`.

As 3 que estavam "sem caracterização" foram resolvidas: `itbi_simulacaoitbi002` e
`itbi_tipotransacoes002` ficaram **idênticas**, e `itbi_situacao002` era **falso positivo do
comparador** — o nome do PDF temporário (`tmp/rp<pid>_<timestamp>.pdf`) muda a cada
requisição. Os dois runtimes falham igual ali, por `tmp/` não ser gravável.

Sete guardas `pg_*` foram acrescentadas ao núcleo durante este módulo (`db_stdlib` linhas
2017 e 2600 e adjacências, `db_utils` linhas 70 e 185) — sempre replicadas na cópia do
`extension/modification`. Cada uma nasceu de um defeito observado, conforme a decisão
registrada de não varrer em massa.

### ARMADILHA DE DIAGNÓSTICO: tabelas vazias no banco de exemplo

**Já gerou dois alarmes falsos de migração.** O banco de exemplo tem várias tabelas dos
módulos portados sem nenhum registro:

```
itbi                 0        itbitransacao       10
sepultamentos        0        itbiformapagamento   5
ossoario             0        causa                3
renovacoes           0        campas               2
legista              0        cemiterio            1
funerarias           0
```

Uma tela que consulta tabela vazia pode falhar de **duas formas muito diferentes**, e
distinguí-las é o que separa dado de defeito:

**1. Vazio TRATADO — não é defeito.** O código verifica `numrows` e emite mensagem de
negócio. Comporta-se **igual nos dois runtimes**, que é exatamente o critério de migração
fiel. Exemplo: `reciboitbi.php:184` (ITBI → Relatórios → Emite Guia):

```php
$rsItbi = $clitbi->sql_record($clitbi->sql_query(null, "*", null,
    "it01_guia = {$itbi} and it01_coddepto = " . db_getsession("DB_coddepto")));
if ($clitbi->numrows == 0) {
  $sMensagemErro = 'ITBI não encontrada para o departamento!';
```

Com `itbi` vazia, qualquer guia informada cai nesse ramo. O `:8080` e o `:8085` devolvem
**4.048 bytes idênticos**. Nada a corrigir.

**2. Vazio que vira FATAL — é regressão.** O código passa o resultado falso adiante para
`pg_*`, que o 5.6 tolerava e o PHP 8 rejeita com `TypeError`. Foi a causa das 8 telas do
Cemitério que quebravam só no 8.5, e das guardas que fomos acrescentando ao núcleo.

> **Ressalva medida depois do `arr`:** este caso 2 **não é causado por tabela vazia**. Consulta
> válida sobre tabela vazia devolve resultado normal com `numrows = 0`. O `false` vem de **SQL
> inválida** — ver a correção na seção das guardas `pg_*`. A coincidência com tabelas vazias
> neste banco é real, mas o mecanismo é outro.

**Variante: a tabela com UMA linha, e ela é justamente o valor óbvio de teste.** Terceiro
alarme falso vindo dos dados deste banco. Em *Jurídico → Advogados → Inclusão*, a inclusão
recusa o CGM 1 dizendo que já existe. Está correto: `advog` tem **uma única linha**, e é o
CGM 1. A tabela tem `PRIMARY KEY (v57_numcgm)` e `FOREIGN KEY → cgm(z01_numcgm)` — a FK é por
que só se aceita CGM existente, e a PK é por que o 1 é recusado. O banco inteiro tem **3 CGMs**
(1 ocupado, 19 e 20 livres), então o valor mais natural de testar é exatamente o que falha.

A mensagem nem vem do PHP: é a violação de unicidade do PostgreSQL, repassada por
`erro_banco`. Comprovável sem alterar dado, com transação revertida:

```sql
BEGIN;
INSERT INTO advog VALUES (19,'OAB123','M1');   -- INSERT 0 1        (aceito)
SAVEPOINT s1;
INSERT INTO advog VALUES (1,'OAB999','M2');    -- viola advog_numc_pk
ROLLBACK TO s1; ROLLBACK;
```

**Limite da bateria de comparação, que isto expõe:** ela faz só `GET`. Caminhos de escrita —
inclusão, alteração, exclusão — **não são exercitados**, então 144/145 telas idênticas não
dizem nada sobre o `incluir()` das classes. É por isso que estes casos aparecem quando o
usuário navega, e não nas verificações automatizadas.

**Como distinguir, em um passo:** reproduzir a mesma tela no `:8080`.

| Resultado | Conclusão |
|---|---|
| Falha **igual** nos dois | dado ausente ou defeito pré-existente — **não mexer** |
| Falha **só no `:8085`** | regressão de migração — ler `extension/log/error.log` e corrigir |

Corolário para a validação: uma tela "sem erro" cuja tabela está vazia **não foi exercitada
de verdade**. A bateria de comparação prova equivalência entre runtimes, não que o caminho
de dados foi percorrido. Para exercitar de fato é preciso cadastrar registros pelo próprio
sistema.

### Estado: MÓDULO `agu` (Água) PORTADO ✅ — 3º da área Tributário

**224 telas**, enumeradas por `^agua?[0-9]*_` com `re.IGNORECASE`. Atenção ao prefixo: além
de `agu1_`…`agu4_` o módulo tem três arquivos `agua_*.RPC.php`. Uma regex `^agu[0-9]*_` os
deixaria de fora — é a mesma armadilha do `itb`/`itbi`.

| Correção | Qtd |
|---|---|
| `$this->X == ""` → forma que preserva a semântica do 5.6 | 895 |
| `split(` → `explode(` | 285 |
| `parse_str()` com 2º argumento | 83 |
| construtor PHP4 → `__construct` | 74 |
| guardas `pg_*` contra resultado falso | 18 |
| cast `(float)` em aritmética com string | 4 |

Verificações: 171 arquivos alterados passam `php -l` **nos dois runtimes**; **222 de 224
telas byte-a-byte idênticas** com sessão autenticada.

As 2 restantes **não são telas** — são fragmentos de include, ausentes do menu, que nenhuma
navegação requisita diretamente. `agu1_aguaconsumo999.php` é um fragmento de DBtxt incluído
por `agu1_aguaconsumo001/002/003`; `agu4_cancelaleituras_classe.php` define
`cl_cancelaleituras` e é incluído por `agu4_expdadoscoletores_003.php`. O 500 no 8.5 é
artefato do harness, que requisita *todo* arquivo do prefixo.

### CATEGORIA NOVA (agu): argumentos faltando viram fatal

```php
function db_fieldsmemory($recordset, $indice, ...)   // $indice e OBRIGATORIO
...
db_fieldsmemory($resultano);                          // chamada com 1 argumento
```

No PHP 5.6 isso era *Warning: Missing argument 2* e o parâmetro virava `null`; no PHP 8 é
**`ArgumentCountError` fatal**. Escala na base inteira: **4 ocorrências em 3 arquivos**
(`agu2_agualancpago001.php` ×2, `cai4_processadebconta001.php`, `mat2_controlest002.php`).
Corrigidas só as 2 do módulo, conforme a decisão de corrigir na aparição.

Correção: passar explicitamente o valor que o 5.6 produzia. Aqui é `0` — `pg_result()`
coagia o `null` do argumento ausente para a linha 0 —, o que além de fiel evita a
deprecation de `null` em parâmetro inteiro introduzida no PHP 8.1.

### CATEGORIA NOVA (agu): comparação de ORDEM entre número e string — LAÇO INFINITO

A RFC "Saner string to number comparisons" já estava catalogada aqui na forma `==`. **Ela
também mudou `>=`, `<=`, `>` e `<`**, e nessa forma o modo de falha é muito pior.

```
              -1 >= ""
PHP 5.6:      false     (a string vira numero: -1 >= 0)
PHP 8.5:      TRUE      (o numero vira string: "-1" >= "")
```

Manifestação real: a tabela `aguacalc` está **vazia**, então `$anoini`/`$anofim` ficam `""`,
e o idioma do e-cidade para montar um `<select>` de exercícios é

```php
for ($i = $anoini; $i >= $anofim; $i--) {
    echo "<option value=$i>$i</option>\n";
}
```

No 5.6 o laço dá **uma volta** e para (`""--` vira `-1`, e `-1 >= ""` é false). No 8.5 ele
**nunca termina**: a página passou de 200 MB e o comparador foi morto com SIGKILL pelo
gerenciador de memória. Observado contando até `-54590`.

**Isto não é dado errado — é exaustão de memória no servidor.** É o argumento mais forte do
catálogo contra confiar em varredura estática: o código é válido nas duas versões, o defeito
depende do estado do banco em tempo de execução, e a falha é de disponibilidade.

Correção: `(float)$i >= (float)$anofim`, que restaura a comparação numérica nos dois
runtimes. O módulo inteiro tem **apenas 2 laços decrescentes**, ambos corrigidos — os outros
82 laços comparam com `sizeof()`/`numrows`, que são numéricos e não correm risco.

### CATEGORIA NOVA (agu): `fputs`/`fclose` sobre handle falso

`model/configuracao/DBLogTXT.model.php` guarda o retorno de `fopen()` e o usa sem verificar.
Quando o diretório não é gravável — a assimetria de permissões pré-existente deste ambiente —
o handle é `false`. No 5.6 era warning e a execução seguia; no PHP 8 é `TypeError` fatal e a
página é **truncada no meio** (198.643 bytes no 5.6 contra 67.267 no 8.5).

É a mesma família das guardas `pg_*`: valor falso repassado a função que passou a checar tipo.
Corrigido com a guarda que reproduz o retorno do 5.6 (`false`).

### 4ª LACUNA: classes carregadas por AUTOLOAD não aparecem em nenhum `include`

`libs/db_autoload.php` registra `spl_autoload_register('db_autoload')`, que carrega as classes
`cl_*` **sem nenhuma declaração de include**. O fecho transitivo de dependências não as vê, e
a enumeração por prefixo também não — elas ficam em `classes/`.

Impacto medido, e ele alcança módulos que eu já havia declarado concluídos:

| módulo | classes não portadas | com construtor PHP4 |
|---|---|---|
| `agu` | 57 | 4 |
| `itb` | 4 | 3 ← módulo declarado pronto |
| `cem` | 2 | 1 ← módulo declarado pronto |

As 62 foram portadas (30 `split`, 8 construtores, 463 comparações `== ""`), e as baterias de
`cem` e `itb` foram refeitas depois.

**Passo a acrescentar à receita:** para cada script do módulo, resolver também os nomes de
classe `cl_*` instanciados (`new cl_x`) e conferir se o arquivo correspondente em `classes/`
entrou na lista.

### 5ª LACUNA: `dbagata/` nunca foi enumerado — e o NÚCLEO o alcança

`std/db_stdClass.php` (núcleo) chama `$api->parseOpenOffice(...)`, que vive em
`dbagata/classes/core/AgataAPI.class`. Ou seja, `dbagata/` está no fecho de dependências do
núcleo e deveria ter sido portado com ele. **Não foi.**

Medição por `php -l` nos dois runtimes sobre os 216 arquivos de `dbagata/`:

| | Arquivos com erro de sintaxe |
|---|---|
| PHP 5.6 | 5 (pré-existentes) |
| **PHP 8.5** | **16** |
| **Só quebram no 8.5** | **11** |

Os 11: `classes/fpdf151/fpdf.php`, `classes/fpdf151/teste.php`, `classes/util/nusoap.php`,
`classes/util/editor.class`, e sete do `jpgraph` (`gd_image.inc.php`, `jpgraph.php`,
`jpgraph_gantt.php`, `jpgraph_pie.php`, `jpgraph_plotmark.inc.php`, `jpgraph_radar.php`,
`jpgraph_spider.php`). Causa dominante: `=& new`, que é *parse error* no PHP 7+.

Categorias medidas em `dbagata/`: 61 `ereg*`, 22 offsets `{}`, 18 `=& new`, 9 `split(`,
8 `magic_quotes`, 5 `each(`, 1 `create_function(`, e **224 classes com apenas construtor
PHP 4, em 114 arquivos**.

**REFINAMENTO (após liberar `tmp/` e rastrear a alcançabilidade): dos 11, apenas 1 importa.**

Rastreando os includes a partir de `libs/db_libsys.php:108` (`class cl_dbagata`):

| Caminho | Arquivos de `dbagata/` carregados | Algum dos 11? |
|---|---|---|
| `parseOpenOffice` — usado pelo núcleo em `std/db_stdClass.php` | ~22 | **nenhum** |
| `generateReport` — `cl_dbagata` faz `setFormat('pdf')` por padrão | +`reports/AgataPdf.class` | **sim**: `AgataPdf.class:40` inclui `dbagata/classes/fpdf151/fpdf.php` |

Os outros 10 são **inalcançáveis**: jpgraph só entra por `AgataGraph.class` (via
`generateGraph()`, que **nenhuma tela do e-cidade chama**), e `nusoap.php`/`editor.class` só
por `AgataInterface.class`, a GUI GTK do Agata, que **nada no repositório inclui**.

Quem chama `generateReport()` (24 call sites fora de `dbagata/`), por módulo:

```
orc 7   iss 4   cai 3   sys 2   pes 2   pro 1   con 1   model 1
```

**Nenhuma das 460 telas de `cem`+`itb`+`agu` está nessa lista** — por isso as baterias passam
limpas mesmo com `tmp/` liberado. Mas **`iss` está**, com 4 call sites.

**Consequência prática: `dbagata/` não é urgente agora, e é pré-requisito duro do `iss`** —
o último e maior módulo da área (400 arquivos). Portá-lo antes do `iss` evita descobrir o
problema no módulo mais caro.

> **RESOLVIDO.** O `dbagata/` foi portado — ver *Estado: BIBLIOTECA `dbagata/` PORTADA*. Os 11
> arquivos que só quebravam no 8.5 passam `php -l` nos dois runtimes, o pipeline de relatório
> gera **PDF byte-a-byte idêntico**, e `cem2_emitecertisen002.php` — a divergência que esta
> seção previa — ficou idêntica. O refinamento acima estava certo no diagnóstico e **errado na
> contagem do que importava**: não era 1 arquivo alcançável, era a cadeia inteira de
> construtores PHP 4 do diálogo de erro.

Nota: existe um jpgraph **fora** do dbagata, em `libs/jpgraph/` (versão 1.14, contra 1.26.1-dev
do dbagata — são versões diferentes, não cópias). Esse já foi portado no commit `04159b411`.

### 6ª LACUNA: `fpdf151/` do núcleo tem 28 arquivos não portados

O `CLAUDE.md` lista `fpdf151/fpdf.php` e `fpdf151/pdf.php` entre os 24 arquivos do núcleo.
**A pasta tem 194 arquivos**, e eu portei dois.

Medição (`php -l` nos dois runtimes + varredura byte-a-byte):

| | |
|---|---|
| Arquivos em `fpdf151/` | 194 |
| Erro de sintaxe no 5.6 | 0 |
| **Erro de sintaxe no 8.5** | **4** — `impmodelos/mod_imprime{10,12,13,1333}.php` |
| `split(` | 23 ocorrências em 22 arquivos |
| `each(` | 20 em 4 — `pdf1.php`…`pdf4.php` |
| construtor PHP 4 | 4 |
| offsets `{}` | 4 |
| **União a portar** | **28 arquivos** |

`each()` **não aparece no `php -l`** — é fatal só em execução (`Call to undefined function`).
Por isso os 4 arquivos com `each()` passam no lint e quebrariam na tela.

Alcance: `fpdf151/pdf1.php` é incluído por 25 arquivos, `pdf3.php` por 8, `pdf2.php` por 6;
`impmodelos/` é usado por `pes2_analitica002.php`, `pes1_cfpess002.php` e
`pes2_termorescisaomodimprime80.php` — todos do módulo **Pessoal**, ainda não portado.

**Lição, a mesma das cinco anteriores:** a lista do núcleo foi montada pelo grafo de
dependências, que enxerga o que é incluído *estaticamente pelos módulos analisados*. Uma pasta
de biblioteca entra no núcleo pelos dois ou três arquivos que o grafo viu, e os outros 192
ficam invisíveis — até que um módulo que os usa seja portado.

Defeito concreto já observado: em `cem2_emitecertisen002.php`, o 5.6 emite
`<b>Mensagem: </b>` (o diálogo de erro do dbagata) e o 8.5 não. Renomear os construtores de
`MemoArea` e `AgataQuery` **não** resolveu — a cadeia real passa por mais classes —, então as
duas alterações foram revertidas para manter o commit do `agu` cirúrgico. `dbagata/` é um
lote próprio, a ser portado com verificação própria.

### ARMADILHA DE MEDIÇÃO: `php -l` dentro de `while read` engole a lista

```bash
while read f; do php -l "$f" | grep -q "No syntax errors" || echo "$f"; done < lista.txt
```

**Isto não verifica a lista.** O `php` (e o `docker exec`) herdam o stdin do laço e consomem
o resto do arquivo. O laço dá uma volta só, e o resultado é um tranquilizador "0 arquivos com
erro" — foi exatamente o que a primeira medição de `dbagata/` devolveu, escondendo os 11.

Correção: `php -l "$f" </dev/null` (e `docker exec -i` com o redirecionamento explícito).

Mesma família das outras armadilhas deste arquivo: **uma verificação que falha em silêncio é
pior que verificação nenhuma**, porque encerra a investigação.

### CRÍTICO: `modification()` troca o arquivo executado em tempo de execução

**O arquivo que você edita em `libs/` pode NÃO ser o que roda.**

Todo include legado passa por `include(modification("caminho"))`. A função `modification()`
(definida em `definitions.php`) consulta o usuário logado (`$_SESSION['DB_login']`) e, se
existir uma cópia personalizada, **devolve o caminho dela em vez do original**:

```
extension/modification/data/cache/user/<login>/<caminho original>
```

Hoje há **23 arquivos sobrescritos para o usuário `dbseller`** — entre eles quatro do núcleo:
`libs/db_stdlib.php`, `libs/db_conecta.php`, `libs/db_sessoes.php`,
`dbforms/db_classesgenericas.php` e `dbforms/db_funcoes.php`.

**Isso causou uma lacuna real no porte:** o núcleo foi corrigido nos originais, mas o runtime
de `dbseller` continuava carregando as cópias em `cache/`, que tinham exatamente as mesmas
incompatibilidades. Foram portadas depois (mesma receita); a árvore inteira (46 arquivos)
passa `php -l` no 8.5.

Detalhes operacionais:
- **A árvore é versionada** (desde o commit `88c53b8`). Só `extension/modification/log`
  segue no `.gitignore`. O motivo: as correções feitas nas cópias de `cache/` se perderiam
  numa limpeza da pasta, e o sistema voltaria a quebrar em PHP 8 mesmo com o porte aplicado.
- As cópias em `file/sync/user/<login>/` estão **vazias (0 bytes)** — quem executa é `cache/`,
  e ele **não é reproduzível** a partir do `sync`: é a única cópia dessas customizações.
- Os arquivos de `cache/` pertencem a `root`; para editá-los:
  `docker exec -u root ecidade_php56 chmod 666 /var/www/html/<caminho>`
- **Toda varredura e todo porte precisam incluir `extension/modification/`.** Medir só a
  árvore principal subestima o trabalho e deixa o runtime real sem correção.
- `vendor/dbseller/legacy/bootstrap/PHP_53.php` fornece polyfills (ex.: `session_is_registered`,
  removida no PHP 5.4). Por isso código que falha em teste CLI isolado funciona na web —
  **teste sempre pelo bootstrap da aplicação**, nunca com `php -r` puro.

### BLOQUEADOR DO LOGIN: Laravel 5.4 não roda em PHP 8

Descoberto ao tentar autenticar no ambiente 8.5. O login **não é** código legado do e-cidade —
ele passa pelo stack do Laravel:

```
login.php  → POST /v4/oauth/token   (Laravel Passport)
           → window.open('abrir.php?sAuth=base64(DB_login=..&DB_senha=md5(..))')
```

No PHP 8.5 esse endpoint devolve **HTTP 500 com corpo vazio**. Os fatais estão todos dentro
de `vendor/`, não no código da prefeitura:

```
ReflectionParameter::getClass() is deprecated since 8.0
   -> vendor/laravel/framework/.../Illuminate/Container/
Zend\Stdlib\PriorityQueue::count() return type ...
   -> vendor/zendframework/zend-stdlib/
```

Detalhe do mecanismo: `config/application.php:27` já exclui `E_DEPRECATED`, mas as rotas
`/v4/*` rodam pelo **handler do Laravel**, que converte qualquer erro — deprecations
inclusive — em `ErrorException` fatal. Por isso uma simples deprecation derruba a requisição.

**Consequência para o projeto:** não existe "logar no :8085" enquanto o Laravel não subir a
escada de versões (Fase 1/2). Isso **valida a arquitetura strangler fig** em vez de contradizê-la:
autenticação e rotas `/v4/*` permanecem no runtime 5.6, os módulos migrados vão para o 8.5, e os
dois compartilham sessão. O proxy reverso deixa de ser desenho e passa a ser requisito.

### DIMENSIONAMENTO DO LARAVEL — o problema é menor do que parece

Medido, e desfaz duas impressões erradas:

| | |
|---|---|
| `app/` (código Laravel de verdade) | 1.259 arquivos, **771 usam Laravel (61%)** |
| `src/` (framework V3 **próprio** deles) | 2.651 arquivos, **apenas 44 usam Laravel (1%)** |
| Rotas servidas pelo Laravel | **138** (60 web + 78 api) |
| Núcleo legado que toca Laravel | **1 arquivo**: `libs/db_conecta.php:83` |

**Achado central: `illuminate/database` (o Capsule do Eloquent) JÁ FUNCIONA em PHP 8.5.**
Verificado conectando e consultando pelo runtime 8.5:

```bash
docker exec ecidade_php85 php -r '
require "/var/www/html/vendor/autoload.php";
$c = new Illuminate\Database\Capsule\Manager;
$c->addConnection(["driver"=>"pgsql","host"=>"ecidade_database","port"=>5432,
  "database"=>"ecidade","username"=>"postgres","password"=>"postgres"]);
$c->setAsGlobal(); $c->bootEloquent();
print_r($c->getConnection()->select("select count(*) from configuracoes.db_modulos"));'
```

Isso separa o "migrar o Laravel" em **dois problemas independentes**:

1. **Eloquent/Capsule** — usado pelo núcleo legado (`db_conecta.php`). **Já funciona no 8.5**,
   não bloqueia nada. É por isso que os módulos migrados funcionam.
2. **O stack HTTP do Laravel** — serve só as 138 rotas `/v4/*` e o login. É o único que falha
   em PHP 8 (`ReflectionParameter::getClass()`, `PriorityQueue::count()`).

**Consequência estratégica: o Laravel não bloqueia a migração dos módulos.** Ele só bloqueia
"desligar o container 5.6", que é o último passo de todos. Por isso está corretamente nas
Fases 1/2, depois dos módulos — e não antes.

Dois caminhos possíveis quando chegar a hora:

- **Escada de versões** 5.4→5.5→…→12: ~8 saltos, cada um com guia oficial de upgrade. Caminho
  "correto", mas cada degrau é um projeto, e arrasta a substituição de `silex`, `doctrine/dbal 2`,
  `symfony ~3.2`, `zend-eventmanager`, `passport 4`, `lcobucci/jwt 3.3.3` e `fractal 0.11`.
- **Reescrever a camada HTTP**: são 138 rotas e 771 arquivos sobre um Laravel novo. Como o
  legado **não depende** do stack HTTP (só do Eloquent, que já funciona), pode sair mais barato
  que oito degraus de upgrade. Exige decisão de escopo, não é trabalho de disciplina.

Pendência para demonstrar o piloto no navegador: **sessão compartilhada entre os dois runtimes**
(hoje 5.6 grava em `/var/lib/php/sessions` e 8.5 em `/tmp`, isolados). O cookie não é obstáculo —
cookies de `localhost` são compartilhados entre portas.

### ✅ MEDIÇÃO (14/10/2026): o Laravel pode migrar em PARALELO — com `vendor/` separado

**A dependência:** nenhuma versão do Laravel roda no 5.6 **e** no 8.5 (5.4 é a última do 5.6 e
não roda no 8; a 12 exige 8.2–8.5, a 13 exige 8.3–8.5). Como os dois containers montam o mesmo
`vendor/`, atualizar o Laravel ali derruba o 5.6. **A saída é um `vendor/` próprio do 8.5**, montado
por cima de `/var/www/html/vendor` só no lado 8.5 — o 5.6 não é tocado.

Montagem da medição (nada na árvore versionada mudou além de `cmp.py`):
`ecidade/tmp/lar12/` (gitignored) com `composer.json` = o atual com `laravel/framework ^12.0` e o
resto `*`; 4º container `ecidade_lar12` na porta **8087**, mesma imagem do 8.5, com o vendor novo,
`bootstrap/cache` e `storage/` também sobrepostos (o Laravel 12 escreveria cache no formato dele e
quebraria os runtimes 5.4).

| Medição | Resultado |
|---|---|
| Pacotes que **não resolvem** com Laravel 12 | **4**: `silex/silex`, `proner/phppimaco` (mpdf 7, PHP ≤ 7.3), `dbseller/phinx_postgres` (phinx 0.10 / symfony antigo), `dbseller/sdk-api-pix-bb` (guzzle 6, ou 7.5.0 com alertas de segurança) |
| Resolvidos | 135 pacotes; Laravel 12.70, Passport 13.10, symfony 7/8, guzzle 7, phpspreadsheet 5, dompdf 3, mpdf 8 |
| **Legado sobre o vendor novo** | **3.294 telas** (Fase A + Educação): **3.271 idênticas ao 5.6**; as 15 divergentes + 8 timeouts são **exatamente** as 23 da linha de base. **Zero regressão.** |
| Classes de `app/`+`src/` que deixam de carregar | **29 de 3.910** (21 `src/Console`: `execute()` sem `: int` do symfony 7; 8 `app/`: `Handler::report(Exception)`, `BaseDeferredProvider::register()`, traits de Auth removidas, Pimaco) |
| Boot do Laravel 12 | **não inicializa** — morre no 1º provider (`BaseDeferredProvider`); `/v4/oauth/token` dá 500 |
| APIs removidas (estático) | 50 `DB::raw` em `app/` (10.0), 10 helpers `str_*`/`array_*` (6.0), 5 `$dates` (10.0), 1 `Passport::routes()` (11.0), 105 usos de PhpOffice (1.8 → 5) |
| Uso do Silex | só a API REST `api/V1` (20 arquivos); o `use Silex\Application` do `app.php` é import sem uso |

**⚠ O Passport 13 NÃO convive com o 5.6 no banco compartilhado:** a migração dele apaga
`user_id`, `redirect`, `personal_access_client`, `password_client` de `oauth_clients` (usados
pelo Passport 4) e passa a exigir segredo com hash. **Usar Passport 12.4** — aceita Laravel 12 e
só acrescenta colunas opcionais (`secret` nullable, `provider`), o que o Passport 4 tolera. O
password grant (o login usa) vem desligado no 12: `Passport::enablePasswordGrant()`.

**Conclusão:** o legado não depende do Laravel novo nem é afetado por ele — 3.294 telas iguais.
O custo está todo na camada HTTP (`app/` + `api/V1`), que hoje nem inicializa. A ordem certa é
trocar o vendor do 8.5 **cedo** (cada área migrada depois disso não precisa ser reverificada) e
portar `app/` em paralelo, com o login e o `/v4/*` ficando no 5.6 até o boot funcionar.

**Três falhas do instrumento nesta medição**, mesma família de sempre: o laço de eliminação do
Composer tratava erro de clone SSH como "resolveu" (corrigido: sucesso = existir `composer.lock`);
o `xargs` aborta a lista inteira quando um `php` sai com 255 (fatal) — 574 de 3.910 testados até
o invólucro `exit 0`; e o `cmp.py` não normalizava `localhost:8087`, gerando 129 falsos positivos.

Remover: `docker rm -f ecidade_lar12` e `rm -rf ecidade/tmp/lar12`.

### 📐 LARAVEL SÓ PARA O TRIBUTÁRIO (16/10/2026) — o que a área usa, medido

| | |
|---|---|
| Rotas de API do domínio | **74**, em 4 módulos: ISSQN 27, Arrecadação 25, ITBI 14, Cadastro 8 (os outros 12 arquivos de rota estão vazios; `routes/web/tributario/*` também) |
| Código Laravel do domínio | `app/Domain/Tributario`: **220 arquivos** (Arrecadação 71, ITBI 64, ISSQN 50, Cadastro 35) + `app/Domain/Core` 12 |
| **Telas legadas que chamam a API por JavaScript** | **14**: TEF (`arr2_operacoespendentestef00*`, `cai3_gerfinanc075`), PIX (`cai3_gerfinanc001`, `cai1_pix002`), parcelamentos vencidos (`arr4_*parc_venc`), alvará por eventos e ordem de serviço (`iss4_*`), Redesim (`iss179_inscricaoredesim`), veículos do ISSQN (2 `forms/`), tipo de débito (`forms/db_frmarretipo002`), parâmetros do número cadastral (`cad4_*`) |
| Telas legadas que usam classes de `app/` | 18 (precisam continuar compatíveis com as duas versões do Laravel) |
| Rotas do ITBI | middleware `clientCredential` = **aplicação externa** (ITBI online); nenhuma tela legada as chama |
| API Silex `api/V1` | 1 rota do Tributário (`TributarioControllerProvider`: `post recibo`) |
| Pacote travado que o Tributário usa | **`dbseller/sdk-api-pix-bb`** — `app/Domain/Tributario/Arrecadacao/Pix/Bancos/BancoDoBrasil.php` (`Swagger\Client`) |

**Ponto cego que isto revela, válido JÁ:** as 14 telas são servidas pelo 8.5, mas o AJAX delas
vai a `/v4/api/tributario/*`, que o proxy manda ao **5.6**. A bateria (`curl`, sem JS) nunca
exercitou essas chamadas. E sem o proxy, abertas no `:8085`, a chamada iria ao Laravel 5.4 sob
PHP 8.5 e falharia.

**Pontos a verificar antes de estimar:** (1) ~~se o Passport 12 do 8.5 aceita o token emitido
pelo Passport 4 do 5.6~~ **TESTADO (16/10/2026): aceita** — ver abaixo; (2) PIX e TEF chamam serviços reais de terceiros (banco, adquirente)
— testes automáticos não podem contatá-los, exigem sandbox ou dublê.

#### ✅ TESTE: o token do Passport 4 (5.6) vale no Passport novo (8.5)

Token **real**, pedido a `POST :8080/v4/oauth/token` com o cliente `9999999` e o usuário
`dbseller` (HTTP 200; JWT RS256, `aud`=9999999, `sub`=1). Conferido com `ResourceServer` do
`league/oauth2-server` — a classe que o Passport usa para validar o *bearer* —, com a chave
`storage/oauth-public.key` e a revogação lida de `oauth_access_tokens` no banco compartilhado:

| `league/oauth2-server` | token real | controle: `sub` adulterado | controle: revogado |
|---|---|---|---|
| **8.5.5** (o do Passport 12.4) + `lcobucci/jwt` 5.6.1 | **ACEITO** (usuário 1, cliente 9999999) | RECUSADO | RECUSADO |
| **9.4.1** (o do Passport 13) | **ACEITO** | RECUSADO | RECUSADO |

5.6 usa `league/oauth2-server` 6.1.1 + `lcobucci/jwt` 3.3.3. **Consequência: o login pode ficar
no 5.6 e as rotas `/v4/api/tributario/*` irem para o 8.5** — o login vira a última peça.

**O que o teste NÃO cobre:** a camada do Passport acima do `ResourceServer` (o `TokenGuard`
carrega o cliente de `oauth_clients` e o usuário pelo *provider* de autenticação), que só roda
com o Laravel 12 inicializando. As colunas de `oauth_access_tokens` são as mesmas nas duas
versões; `oauth_clients` muda no 13, por isso a escolha do 12.4 continua valendo.

**Armadilha do instrumento:** a primeira execução deu `Invalid key supplied` nas duas versões —
o container `ecidade_lar12` sobrepõe `storage/` com uma pasta vazia, e a chave não estava lá.
Era o teste, não a compatibilidade. Verificador versionado: `scratchpad/valida_token.php <vendor/autoload.php> <token> <oauth-public.key>`.

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

### PERMISSÕES: `storage/` bloqueava o login nos DOIS ambientes

`storage/` e `bootstrap/cache` eram `775 diego`, e nenhum container (uid 33) conseguia escrever.
O Laravel falhava com `storage/logs/laravel.log ... Permission denied` e `/v4/oauth/token`
devolvia 500 **também no 5.6**. Corrigido com `chmod -R 777 storage bootstrap/cache`; depois
disso o 5.6 passou a emitir token válido (HTTP 200). Ambiente novo precisa desse passo.

### DUAS CATEGORIAS NOVAS descobertas no piloto

Nenhuma das duas aparece em varredura de texto; **só o `php -l` do PHP 8.5 as revela**.

**1. Assinatura incompatível com a classe pai (LSP)** — E_STRICT no PHP 5.6, **fatal desde o
PHP 7.0**. Ex.: `SuperScriptText::GetWidth(&$aImg)` sobrescrevendo `Text::GetWidth($aImg)`
(por referência vs. por valor), ou filha com menos parâmetros que a mãe. Regra de correção:
o **pai manda** na passagem por referência e nos defaults; o **filho mantém os nomes** dos
parâmetros (o corpo os usa) e herda os parâmetros extras opcionais.

**2. `=& new` (atribuição por referência de objeto novo)** — removida no PHP 7.0, gera
*parse error*. Base inteira: **8 arquivos / 25 ocorrências**. Desde o PHP 5 objetos já são
manipulados por handle, então remover o `&` é equivalente.

Como não são detectáveis por grep, a forma de medi-las na base inteira é rodar
`php -l` sob PHP 8.5 em todos os arquivos.

### ✅ MEDIÇÃO FEITA: `php -l` nos dois runtimes, na base inteira

**33.057 arquivos PHP** (excluindo `vendor/`, `node_modules/`, `.git`), com `</dev/null` para
o `php` não engolir a lista:

| | Arquivos com erro de sintaxe |
|---|---|
| PHP 5.6 | 101 (pré-existentes) |
| PHP 8.5 | 187 |
| **Só quebram no 8.5** | **87 — 0,26% da base** |

Distribuição: raiz **51**, `dbagata/` 10, `app/` 5, `src/` 4, `fpdf151/` 4, `model/` 3,
`libs/` 3, demais 7. Apenas **2** são da área Tributário ainda não portada.

Causas:

| Causa | Arquivos |
|---|---|
| `unexpected token "{"` — offset de string com chaves | 26 |
| `Invalid numeric literal` — octal inválido (`08`, `09`) | 6 |
| `unexpected token ";"` / `"["` | 9 |
| nome totalmente qualificado / `namespace` inesperado | 6 |
| **`Unparenthesized a ? b : c ? d : e`** — associatividade removida no PHP 8.0 | 3 |
| **`The (real) cast has been removed`** — PHP 8.0 | 1 |
| `Unterminated comment` | 1 |
| demais | 35 |

**Este número é o argumento central do trabalho, em uma linha.** A incompatibilidade que uma
ferramenta de sintaxe encontra na base inteira são **87 arquivos**. As categorias que
realmente custam — `0 == ""` (19.401 ocorrências), construtores PHP 4 (3.587 classes),
`sizeof(null)`, comparação de ordem com string — **não aparecem em nenhuma delas**. Um
`php -l` limpo em 100% da base não diria nada sobre o sistema calcular tributo errado.

Duas categorias novas apareceram só aqui, ambas fatais de compilação no PHP 8.0 e invisíveis
ao grep: **ternário aninhado sem parênteses** (`a ? b : c ? d : e`) e **cast `(real)`**.

### ✅ EXPERIMENTO: Rector 2.6.7 medido contra o porte manual do `div`

A pergunta "por que não usar o Rector?" era legítima e eu a respondia por raciocínio, não por
medição — violando o princípio do próprio projeto. O experimento: reconstruir o estado
**pré-porte** dos 163 arquivos que o commit do `div` alterou, rodar o Rector sobre eles, e
comparar três árvores — original, saída do Rector, meu resultado.

Config: `withPhpSets(php80: true)` — só os conjuntos de upgrade de versão, que é o "grupo (a)"
da taxonomia do TCC de referência. Rodou em 1m12s e parseou os short tags sem problema
(136 dos 163 arquivos usam `<?`).

#### Cobertura por categoria

| | ANTES | RECTOR | MEU |
|---|---|---|---|
| guarda `0 == ""` | 0 | **0** | **763** |
| `split(` restante | 381 | 1 | 0 |
| `parse_str` de 1 arg restante | 62 | 2 | 0 |
| construtor PHP 4 restante | 80 | 0 | 0 |
| offset `{}` restante | 2 | **0** | 0 |

#### Onde o Rector é melhor que o meu ferramental — e não é pouco

1. **Ele não toca em comentário.** Dois dos três "restantes" dele eram código comentado
   (`// $arr = split("-", ...)`). **Meu regex editou os dois**, porque não distingue código de
   comentário. Inofensivo aqui, mas é ruído no diff e revela a natureza do instrumento.
2. **Ele pegou o offset `$aDebitos[$i]->origem{0}`**, que meu regex não cobria — a lacuna de
   detecção que registrei na seção do `div` e que só o `php -l` tinha achado.
3. **Ele converte `split()` sempre para `preg_split`**, preservando a semântica POSIX do
   separador. Meu `porta.py` converte para `explode` e **aborta** quando o separador tem
   metacaractere. A solução dele é mais geral e dispensa a classificação manual.

#### Onde ele não serve — e por que isso decide a questão

**1. Zero guardas `0 == ""`.** As 763 correções — **58% do trabalho** — estão inteiramente
fora do alcance dele. Não é limitação da ferramenta: a guarda não é um upgrade, é um *shim*
que preserva a semântica do 5.6, e o código é válido nas duas versões.

**2. A saída dele NÃO roda em PHP 5.6.**

| | PHP 5.6 | PHP 8.5 |
|---|---|---|
| Saída do Rector | **19 de 163 com erro de sintaxe** | 0 |
| Meu resultado | **0** | 0 |

Causa: regras que emitem sintaxe de PHP 7+. Exemplo literal em `cai3_gerfinanc001.php:1753`:

```php
ANTES   if (!isset($certidao)) { ... }
RECTOR  $certidao ??= "";            // ??= e PHP 7.4 -> parse error no 5.6
MEU     if (!isset($certidao)) { ... }
```

Regras responsáveis: `IfToNullCoalescingAssignRector` (6), `ClosureToArrowFunctionRector` (4),
`TernaryToNullCoalescingRector` (3), `NullCoalescingOperatorRector` (3). **Isso quebra a
restrição central do strangler fig**: os dois containers montam o mesmo diretório, então um
arquivo que não parseia no 5.6 derruba a referência — que serve o login e todos os módulos
ainda não migrados.

**3. A regra de `parse_str` descarta variáveis do escopo, em silêncio.**

```
parse_str($s);            -> $foo existe em escopo        (comportamento do 5.6)
parse_str($s, $result);   -> $foo NAO existe; so $result  (verificado no proprio 5.6)
```

O Rector criou **60 chamadas com 2º argumento e acrescentou `extract()` em zero delas**
(24 `extract` antes, 24 depois). Nos 60 casos, as variáveis que o código legado importava do
query string deixam de existir — sem erro, sem aviso. Se quebra ou não depende de o código
adiante lê-las, o que exige análise caso a caso. Minha correção acrescenta
`extract($__qs)` nas 62, restaurando o escopo mecanicamente.

**4. Ele trocou `$HTTP_*_VARS` por `$_SERVER`/`$_POST` — 317 ocorrências em 67 arquivos.**
Exatamente a mudança registrada aqui como **não-mudança deliberada**: nesse ambiente os
`$HTTP_*_VARS` estão indefinidos (removidos no PHP 5.4) e o código se protege disso; trocá-los
**popula valores hoje vazios**. É mudança de comportamento, não migração.

#### SEGUNDA RODADA: a lista curada funciona — e o custo dela está medido

A pergunta seguinte era "então o Rector com regras escolhidas seria melhor?". Também medi.

Partindo dos conjuntos por versão e **excluindo 14 regras**, uma a uma com motivo:

| Motivo da exclusão | Regras | Efeito no 5.6 |
|---|---|---|
| emitem sintaxe de PHP 7+ | `IfToNullCoalescingAssign`, `ClosureToArrowFunction`, `TernaryToNullCoalescing`, `NullCoalescingOperator`, `ListToArrayDestruct`, `ClassPropertyAssignToConstructorPromotion`, `ChangeSwitchToMatch`, `ClassOnObject`, `StringableForToString`, `RemoveUnusedVariableInCatch` | *parse error* |
| emitem **função** que não existe no 5.6 | `StrStartsWithRector` (`str_starts_with`), `RandomFunctionRector` (`random_int`) | **fatal só em execução** |
| mudam comportamento | `ReplaceHttpServerVarsByServerRector`, `ParseStrWithResultArgumentRector` | silencioso |

Resultado: **129 arquivos alterados, 0 erro de sintaxe no 5.6 e no 8.5, 0 função ausente.**
A lista curada **satisfaz a restrição de dois runtimes.** A resposta é sim.

#### O que a lista curada cobre, e o que sobra

| | ANTES | CURADO | MEU |
|---|---|---|---|
| `split(` restante | 381 | **1** (é comentário) | 0 |
| construtor PHP 4 | 80 | **0** | 0 |
| offset `{}` | 2 | **0** | 0 |
| `parse_str` de 1 arg | 62 | **62** | 0 |
| guarda `0 == ""` | 0 | **0** | 763 |

Equivalência verificada nos dois runtimes para as 381 conversões — o Rector gera
`preg_split("#\##m", $x)` onde eu gero `explode("#", $x)`, e o resultado é `===` idêntico.

#### O custo que a pergunta esconde

**1. Duas das regras perigosas são invisíveis ao `php -l`.** `str_starts_with` e `random_int`
compilam no 5.6 e explodem em execução. Achei-as não por inspeção, mas perguntando ao próprio
runtime quais funções ele não conhece — **passo de verificação novo**, hoje na skill:

```bash
# funcoes que aparecem SO na saida do Rector, conferidas contra o 5.6
docker exec ecidade_php56 php -r 'foreach(file("lista.txt",2) as $f)
  if(!function_exists(trim($f))) echo trim($f),"\n";'
```

Sem ele, o lint diria "0 erros" e 93 arquivos quebrariam na tela.

**2. A exclusão é uma *denylist*, e denylist é frágil.** Uma atualização do Rector pode
acrescentar regras aos conjuntos por versão e reintroduzir o problema **em silêncio**. Um
`withRules()` (allowlist) seria mais seguro, mas exige reconfigurar regras como
`RenameFunctionRector`, que os conjuntos alimentam com o mapa de funções removidas.

**3. Uma das regras não é só desabilitável — precisa ser substituída.** Com
`ParseStrWithResultArgumentRector` excluída, os 62 `parse_str` ficam **intocados**: o
ferramental próprio continua necessário para eles. A ferramenta não sai de cena.

#### Resposta à pergunta, com o escopo certo

**SUPERADO — ver *DECISÃO: Rector adotado*.** Esta conclusão valia enquanto faltavam as regras
da camada semântica. Escritas (196 linhas), o Rector passou a fazer 100% do porte, e a resposta
deixou de ser "só a camada sintática".

*Texto original:* **Sim, para a camada sintática, e vale a pena a partir de `fis` (353) e `iss` (400)** — onde
o volume paga a montagem da lista. Para os sete prefixos pequenos restantes, montar e validar
a lista custa mais do que as poucas dezenas de correções sintáticas que ela faria.

E não substitui nada da camada semântica: as 763 guardas `0 == ""`, as guardas `pg_*`, os
casts e o `sizeof(null)` continuam sem regra equivalente.

**Portão de verificação obrigatório ao usar o Rector aqui**, nesta ordem: `php -l` nos dois
runtimes → conferência de funções contra o 5.6 → bateria byte-a-byte. O segundo é o que
nenhuma ferramenta de sintaxe faz por você.

#### Ressalva honesta: isto não prova que o Rector é inútil aqui

Os problemas 2 e 4 vêm dos **conjuntos por versão**, que misturam o que é exigido com o que é
opcional — a mesma queixa que o TCC de referência registrou. Uma configuração por **lista
explícita de regras** evitaria os dois. O problema 3 é defeito da regra em si e exige
desabilitá-la. O problema 1 é estrutural e nenhuma configuração resolve.

Das 14 regras mais aplicadas, só 5 eram exigidas pela versão de destino; as outras 9
(`StrStartsWithRector` 93, `ExplicitPublicClassMethodRector` 89, `VarToPublicPropertyRector` 86,
`LongArrayToShortArrayRector` 27…) são modernização, e inflam o diff sem necessidade.

#### Conclusão: o desenho correto é híbrido

| Camada | Instrumento | Por quê |
|---|---|---|
| Sintática (1.927 das 4.641 correções) | **Rector, com lista explícita de regras** | AST não erra onde regex erra: comentários, chamada aninhada, `->prop{}` |
| Semântica (2.714) | ferramental próprio | `0 == ""`, guardas `pg_*`, casts, `sizeof(null)` — não existem como regra |
| Verificação | comparação byte-a-byte entre runtimes | nenhuma ferramenta substitui |

**Não refiz os cinco módulos já portados** — eles estão verificados byte-a-byte, e trocar o
instrumento agora custaria mais do que ganha. A recomendação vale para os sete prefixos
restantes, e principalmente para `fis` (353) e `iss` (400), onde o volume justifica montar a
lista de regras.

Reproduzir: a montagem está em `tmp/rector/` (gitignored). O passo que importa é reconstruir o
estado pré-porte com `git show <commit>^:<arquivo>` e comparar **três** árvores, não duas —
sem a original não dá para saber quem mudou o quê.

### ✅ COBERTURA DOS CAMINHOS DE ESCRITA — o maior ponto cego, agora medido

A bateria de telas faz só `GET`. O idioma `$this->X == "" ? POST : $this->X` vive em
`atualizacampos()`, que lê `HTTP_POST_VARS` — **nunca populado num GET**. Resultado: **763 das
837 correções** que sobram ao ferramental próprio nunca eram exercitadas por nenhuma
verificação. Era o maior risco em aberto do projeto.

Três níveis possíveis de cobertura, com custos muito diferentes:

| Nível | O que faz | Custo | Cobre |
|---|---|---|---|
| **1. Estado do objeto** | popula `HTTP_POST_VARS`, chama `atualizacampos()`, compara o estado entre runtimes | trivial — extensão do harness que já existia | as 763 guardas (**91%** do que falta) |
| 2. SQL gerado | compara o SQL que cada runtime montaria, sem executar | médio — o método que monta SQL varia por classe | + validações da classe |
| 3. POST real | requisição de verdade nos dois, comparando resposta **e** efeito no banco | alto — exige restaurar o estado do banco entre os dois lados | tudo, inclusive guardas `pg_*` e validação da tela |

**Nível 1 implementado e provado** — `scratchpad/escrita.php`:

```bash
php scratchpad/escrita.php <arquivo com a lista de classes>   # nos DOIS runtimes, depois diff
```

Prova de conceito contra o defeito já conhecido de `classes/db_cgm_classe.php`:

```
versao ANTES das 11 guardas  ->  18 linhas divergentes entre 5.6 e 8.5
versao DEPOIS                ->  0 divergentes

    z01_numcgm='1012'   |   z01_numcgm=0        <- 5.6 le o POST, 8.5 mantem 0
```

**Ele teria apanhado esse defeito do núcleo automaticamente** — eu o encontrei por acaso, na
verificação de remanescentes do `div`.

#### O que ele achou na primeira execução real

Rodado sobre as **311 classes** dos cinco módulos portados, **9.817 campos** comparados:
**64 linhas divergentes em 12 classes**. Onze são do `tra` (órfão, já registradas como não
corrigidas). A décima segunda era nova — e revelou uma **variante do idioma que o catálogo não
tinha**:

```php
var $k40_tipoanulacao = 0;                                    // INTEIRO
$this->k40_tipoanulacao = ($this->k40_tipoanulacao == "f" ? POST : $this->k40_tipoanulacao);
```

Compara com **`"f"`**, não com `""`. Mesma falha:

```
0 == "f"      PHP 5.6: true        PHP 8.5: false
```

Causa: no 5.6 a string **não-numérica** era coagida para 0 e casava com a propriedade inteira;
no PHP 8 vira comparação de string. Vale para **qualquer literal não-numérico** — literal
numérico (`"0"`, `"5"`) é seguro nos dois.

Escala na base inteira: **13 ocorrências em 5 arquivos**.

| Arquivo | Literal | Módulo |
|---|---|---|
| `classes/db_rechumano_classe.php` (8) | `" "` | Educação |
| `classes/db_aluno_classe.php` (2) | `" "` | Educação |
| `classes/db_cadtipoparc_classe.php` | `"f"` | Caixa — **corrigido** (estava no universo do `div`) |
| `classes/db_tipoproc_classe.php` | `"f"` | Protocolo |
| `classes/db_inscricaorestosapagar_classe.php` | `"f"` | Contabilidade |

Duas delas são de **Educação** — o módulo do TCC de referência, mais um defeito que o critério
deles ("a tela carrega") não encontraria.

`enumera.py` e `porta.py` foram estendidos para tratar qualquer literal não-numérico, não só `""`.

#### ✅ NÍVEL 3 IMPLEMENTADO — `scratchpad/escrita_post.py`

**O problema central:** os dois runtimes compartilham o banco, então o primeiro `POST` muda o
estado que o segundo veria. A saída não é comparar o estado final — é comparar **o SQL que
cada runtime emite**, que é exatamente onde o defeito se manifesta, com snapshot/restore entre
os dois lados.

```bash
# exige log_statement ligado:
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade SET log_statement='all';"

python3 scratchpad/escrita_post.py <SID> <tela.php> <tabelas,virgula> '<payload>'

# e desligar ao terminar:
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade RESET log_statement;"
```

Fluxo: snapshot das tabelas **e das sequências** → `POST` no `:8080`, captura o SQL do log →
restore → `POST` no `:8085`, captura → restore → compara.

**Prova no defeito original do catálogo** (`cm34_tipo`, Cemitério → Tipos de isenção):

```
COM a guarda:
  5.6> insert into cemiterioisencao(...) values ( 11 ,'TESTE_N3' ,2 ,'2026-12-31' ,'X' )
  8.5> insert into cemiterioisencao(...) values ( 11 ,'TESTE_N3' ,2 ,'2026-12-31' ,'X' )
  == IDENTICO ==

SEM a guarda:
  5.6> insert into cemiterioisencao(...) values ( 11 ,'TESTE_N3' ,2 ,... )
  8.5> <ausente>                      <- nao insere nada: cm34_tipo fica 0 e a validacao recusa
  == DIVERGE ==
```

É o sintoma exato que o usuário reportou quando a categoria foi descoberta.

#### Três detalhes que o nível 3 obrigou a resolver

**1. Restaurar a tabela não basta — tem que restaurar a SEQUÊNCIA.** Sem isso o segundo
runtime recebe o próximo número e o `INSERT` diverge por motivo benigno (`values ( 6 ...)`
contra `( 7 ...)`). E `pg_get_serial_sequence` **não enxerga** as sequências do e-cidade,
porque elas são criadas sem `OWNED BY` — o harness casa pelo nome (`<tabela>_%_seq`).

**2. `DELETE`, nunca `TRUNCATE CASCADE`.** O `DELETE` respeita a chave estrangeira e **falha**
se alguém referencia a tabela — que é a rede de segurança. `TRUNCATE CASCADE` apagaria as
tabelas vizinhas em silêncio. Quando a FK barra, a resposta é acrescentar a tabela filha ao
conjunto (apagar filho→pai, repovoar pai→filho), não forçar.

**3. Separar escrita de NEGÓCIO da de INFRAESTRUTURA.** Cada requisição emite ~36 statements,
dos quais ~10 são de escrita, e quase todos são auditoria (`db_acount*`, `db_logsacessa`) ou
sessão (`db_usuariosonline`). Esses carregam sequência e relógio e divergem **por construção**.
Filtrados, sobra 1 statement — o que importa.

#### A limitação real do nível 3: o payload

O harness está pronto; o custo que resta é **construir um `POST` válido por tela**. Não é
mecânico:

- o botão de submit muda de nome conforme a operação (`incluir`/`alterar`/`excluir`), não é
  `db_opcao` como o código sugere;
- campos obrigatórios não aparecem no `db_input` do form (a data do exemplo é montada de
  `_dia`/`_mes`/`_ano`);
- a chave costuma vir como **argumento** de `incluir($chave)`, não pelo idioma do POST — por
  isso `advog` e `aguahidromarca` não exercitam o defeito, mesmo tendo guardas.

**Consequência prática:** o que limita o nível 3 é **montar o payload**, não o custo de
execução. Medido: **5 s por ciclo** (2 POSTs + 2 restores), o que daria **~12 min** para as
148 telas de um módulo — viável como bateria, não só como teste dirigido. O nível 1
(`escrita.php`) continua sendo o filtro barato que aponta a classe e o campo onde dirigi-lo
primeiro.

#### Por que NÃO um banco por runtime

Pergunta levantada e medida, em vez de respondida por intuição.

| | DB compartilhado + restore (adotado) | DB por runtime |
|---|---|---|
| Custo por tela | **5 s** | ~2 s |
| Disco extra | 0 | 1.075 MB |
| Configuração | `log_statement`, um toggle | override de `libs/db_conn.php` por container |
| Invariante do GET | preservada de graça | exige ressincronizar os dois bancos |
| Observável | SQL emitido — **completo** com `log_statement='all'` | linhas + SQL |
| Modo de falha | restore barrado por FK → **aborta** | bancos derivam em silêncio |

Três razões para ficar com o compartilhado:

1. **O observável não melhora.** Com `log_statement='all'` todo SQL é capturado; comparar
   linhas não acrescenta cobertura.
2. **Quebraria a invariante da bateria GET.** Hoje "mesmos dados, só o PHP difere" é garantido
   por construção; com dois bancos vira uma condição que pode derivar sem aviso.
3. **`libs/db_conn.php` fixa `$DB_BASE`, está no `.gitignore` e é lido pelos dois containers
   pelo mesmo bind mount.** Separar exige editar arquivo não versionado ou acrescentar bind
   mount de arquivo único ao compose do 8.5.

Medição que sustenta a escolha: **as tabelas de negócio do Tributário têm no máximo 252
linhas** — o restore é barato. As tabelas de milhão de linhas (`ceplogradouros`,
`cadenderrua*`) são dados de referência de endereço, que nenhum formulário escreve e que
portanto nunca entram num conjunto de restore.

**Quando dois bancos seria melhor:** tabelas de negócio grandes, ou bateria de escrita rodando
continuamente em CI. Nenhuma das duas é o caso aqui.

#### O que o nível 1 NÃO cobre

As outras 74 correções — `parse_str`, guardas `pg_*`, casts, `sizeof(null)` — vivem no código
**da tela**, não da classe, e só o nível 3 as exercita. Continua valendo a regra: *uma tela
"sem erro" cuja tabela está vazia não foi exercitada de verdade*.

### Decisões de porte tomadas (e o porquê)

- **`each()` → ponteiro explícito, não `foreach`.** Em `db_libpessoal.php` há dois laços
  sobre o mesmo array; o segundo depende do ponteiro interno já exaurido pelo primeiro e
  por isso **nunca executa**. Trocar por `foreach` faria o segundo laço rodar — mudança
  silenciosa de comportamento. Usou-se `key()`/`current()`/`next()`, que reproduz `each()`
  exatamente nos dois runtimes.
- **`$HTTP_*_VARS` NÃO foram tocados.** Removidos no PHP 5.4, já estão indefinidos no
  ambiente 5.6 atual (o código se protege com `if (!empty($HTTP_SERVER_VARS))`). Trocar por
  `$_SERVER` popularia valores hoje vazios — mudança de comportamento, não migração.
  Em PHP 8 geram apenas *Warning*. Tarefa separada e deliberada.
- **Acentos LATIN-1 em classes de regex** (`preg_replace("/[ÁÀÂÃ]/", ...)`): editados em
  nível de **byte**, via Python. Editar como texto UTF-8 corromperia os bytes. Sem o
  modificador `/u`, o PCRE é byte-a-byte igual ao POSIX `ereg` original — equivalência
  confirmada por teste de caracterização.
- **JavaScript embutido preservado.** `dbforms/db_classesgenericas.php` linhas 1682/1736
  contêm `str.split()` — é JS dentro do HTML, não PHP. Varreduras automáticas por `split(`
  **precisam excluir esses casos**.

### Bugs latentes encontrados (pré-existentes, NÃO corrigidos)

Não foram tocados por serem mudança de comportamento, não migração. Valem menção no relatório:

- `libs/db_libpessoal.php:113-114` — `strtoupper(split(...))` aplica `strtoupper` a um array,
  e a linha seguinte usa `$count($cmp_)` com `$count` indefinido (chamada de função variável
  em variável nula). **Esse ramo já falha no PHP 5.6**; é código morto.
- `std/DBString.php:661` — o `ereg_replace(",", "\.", ...)` insere uma barra invertida
  literal (`1234,56` → `1234\.56`), que depois vai para `number_format()`. Comportamento
  preservado fielmente com `str_replace`, mas o resultado provavelmente não é o pretendido.

## Comandos úteis

### PROXY REVERSO — origem única (montado e verificado) ⭐

**Use `http://localhost:8090`.** É o endereço do sistema durante a migração.

```
http://localhost:8090
   /tra1_*, /tra_*  ->  PHP 8.5   (módulo migrado)
   /*               ->  PHP 5.6   (login, /v4/* do Laravel, demais módulos)
```

Arquivos: `docker/proxy/nginx.conf` + `docker-compose.proxy.yml`. Cada resposta traz o
cabeçalho `X-Ecidade-Runtime` dizendo qual runtime a serviu — útil para demonstrar em banca
que a mesma sessão navega entre dois PHPs. Verificado: `/tra1_acidentes001.php` responde com
`X-Powered-By: PHP/8.5.10` e `/login.php` com o 5.6.

**Por que origem única é obrigatório, não conveniência:** a sessão do e-cidade é *por janela*
e presa à origem. Com 5.6 em :8080 e 8.5 em :8085 são origens distintas, e a janela aberta
pelo login não encontra a sessão do outro lado — o sintoma é "Sessão inválida (12)". Sob uma
origem só, o navegador envia os mesmos cookies para ambos.

**Para migrar o próximo módulo:** acrescente o prefixo dele à alternância `(?:cem|tra)` do
`location` no nginx. Essa linha é literalmente o avanço da migração.

**ARMADILHA `/w/<n>/` — o prefixo de janela do desktop v3.** Na navegação real pelo menu, as
URLs **não** são `/cem1_campas001.php` e sim `/w/2/cem1_campas001.php` — o desktop prefixa
tudo com o id da janela (ver `ECIDADE_REQUEST_PATH`). Um `location ~ ^/(cem|tra)_` casa só
o acesso direto ao arquivo e **nunca dispara na navegação real**: o sintoma é o módulo
continuar respondendo pelo 5.6 mesmo com o roteamento "verificado" por curl. O padrão correto
aceita o prefixo como opcional:

```nginx
location ~ ^(?:/w/[0-9]+)?/(?:cem|tra)[0-9]?_ { ... }
```

Verificado: `/cem1_campas001.php`, `/w/1/cem1_...` e `/w/2/cem1_...` respondem pelo 8.5,
enquanto `/w/2/extension/desktop/...` e `/w/2/skins/estilos.php` continuam no 5.6.

Para descobrir as URLs reais de um módulo, o log do proxy é a fonte definitiva:
`docker logs ecidade_proxy 2>&1 | grep -aoE '"(GET|POST) [^ ]+'`

**ARMADILHA MAIÚSCULAS — vale para o roteamento E para a enumeração.** O e-cidade tem
arquivos com o prefixo de módulo **capitalizado**: `Cem1_legista001.php`, `Con1_*`, `Cai1_*`,
`Amb1_*`, `Cus1_*`. São **29 na raiz** (Con1 9, Cai1 6, Amb1 6, Cus1 5, Cem1 3), de 15.694.

Poucos, mas causam duas falhas silenciosas distintas:

1. **Roteamento:** `location ~ ` é sensível a caso, então essas telas continuam no 5.6
   mesmo com o módulo portado — sem erro, só o `X-Ecidade-Runtime` denunciando. Corrigido
   usando **`location ~*`** (insensível a caso).
2. **Enumeração:** o levantamento do módulo com `re.match(r"^cem[0-9]*_", f)` também é
   sensível a caso e **deixou 3 arquivos fora do porte** — dois deles ainda com `parse_str`
   de 1 argumento. Detectado pelo usuário navegando a tela, não pelas verificações.

**Ao enumerar um módulo, usar sempre `re.IGNORECASE`:**
```python
re.match(r"^cem[0-9]*_", f, re.IGNORECASE)
```

Lição: uma verificação que só testa os nomes que a própria enumeração gerou nunca encontra
o que a enumeração deixou de fora. Vale conferir `ls | grep -iE '^<prefixo>[0-9]*_'` contra
a lista enumerada antes de dar o módulo por concluído.

**ARMADILHA `Host $host` vs `$http_host`:** o e-cidade monta URLs absolutas a partir de
`HTTP_HOST` (ver `$DB_URL_ABS` em `libs/db_stdlib.php`). A variável `$host` do nginx
**descarta a porta**; com ela o sistema gerava `http://localhost/skins/estilos.php?...`,
o navegador buscava na porta 80 e **a tela vinha inteira sem CSS, JS nem fontes**. Usar
sempre `proxy_set_header Host $http_host;`, que preserva `localhost:8090`. Sintoma
enganoso: parece falha de migração e é configuração de proxy.

Nota operacional: o nginx.conf entra por bind mount de **arquivo único**; editar o arquivo no
host cria um inode novo e o container continua com o antigo. Depois de editar, use
`docker compose -f docker-compose.proxy.yml up -d --force-recreate` (um `nginx -s reload` não basta).

### `/tmp` COMPARTILHADO — obrigatório, como a sessão (montado e verificado)

Volume Docker externo `ecidade_tmp`, montado em `/tmp` nos **dois** containers.

**Por que:** `dbforms/db_classesgenericas.php` usa `tempnam()` para gerar
`/tmp/iframe<aleatório>.php` e devolve ao navegador um iframe apontando para
`dbforms/db_classes_iframe_alterar_excluir.php?arquivo=<base64 do caminho>`.

Com dois runtimes isso quebra de forma espetacular: a tela do módulo migrado é servida pelo
**8.5** e grava o temporário no `/tmp` dele, mas `dbforms/` **não casa com o regex do proxy**
e a requisição do iframe vai para o **5.6**, que não encontra o arquivo. O iframe erra e
repete — **loop infinito de POSTs**.

Sintomas medidos antes da correção:

```
6.717 requisições a itb1_itbitransacao111.php no log do proxy
7.847 arquivos /tmp/iframe*.php órfãos no container 8.5   (contra 69 no 5.6)
```

No navegador: primeira requisição GET com iniciador `subdocument`, seguida de dezenas de
POSTs com iniciador `db_classes_iframe_alterar_excluir.php`. **Não acontece no :8080 puro** —
só na origem mista, o que o torna um falso "defeito da migração do módulo".

Verificado depois da correção: o mesmo fluxo devolve **HTTP 200 / 3.057 bytes idênticos**
pelo `:8080` (puro 5.6) e pelo `:8090` (misto).

**Regra geral que decorre disso:** os dois runtimes precisam compartilhar **todo estado de
runtime**, não só o banco. Já são três: banco, sessão (`/var/lib/php/sessions`) e agora
`/tmp`. Ao encontrar comportamento estranho que só ocorre no `:8090`, suspeitar primeiro de
estado não compartilhado, antes de procurar defeito de porte.

### Sessão compartilhada entre os runtimes (montada e verificada)

Volume Docker externo `ecidade_sessions`, montado em `/var/lib/php/sessions` nos **dois**
containers; o 8.5 tem `session.save_path` apontado para lá. Verificado: o 5.6 grava uma
sessão e o 8.5 a lê com o conteúdo correto.

Como o login roda no Laravel 5.4 (que não funciona em PHP 8), o fluxo do piloto é:
**autenticar em :8080 e navegar o módulo migrado em :8085 com a mesma sessão.** Cookies de
`localhost` não distinguem porta, então o navegador envia a sessão para as duas.

Detalhe da sessão do e-cidade: ela é **por janela**. O cookie `ECIDADEWINDOWMAIN` é o *nome*
da sessão (`session_name()`) e seu valor é o *id* (`session_id()`) — ver `src/V3/Window/Session.php`.
Não é `PHPSESSID`. Uma requisição consome/reescreve a sessão, então testes com curl precisam
recriá-la a cada chamada.

```bash
# ambiente de referência (PHP 5.6) + volume de sessão compartilhada
docker volume create ecidade_sessions
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d   # :8080

# permissões exigidas por Laravel e pelo logger (senão /v4/oauth/token dá 500)
chmod -R 777 storage bootstrap/cache
chmod 777 extension/log
# sem isto os relatórios não são gerados e 11% das telas falham antes de executar
chmod 777 tmp arquivos

# ambiente de migração (PHP 8.5)
docker compose -f docker-compose.php85.yml up -d --build # :8085
docker compose -f docker-compose.php85.yml down

# erros do runtime 8.5
docker exec ecidade_php85 cat /var/log/php_errors.log
tail -f extension/log/error.log        # log da própria aplicação

composer test                 # vendor/bin/phpunit
npx cypress open              # specs em tests/cypress/integration
```
