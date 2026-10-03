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

**Onde paramos:** migrando a **área Tributário** módulo a módulo. 3 de 16 concluídos.

| | |
|---|---|
| Módulos portados | `cem` · `itb`/`itbi` · `agu` · `jur` · `div` Dívida Ativa — **5 de 16** |
| Também portado | `tra` — órfão no menu, sem uso prático |
| Núcleo (24 arq.) | portado, com guardas `pg_*` acrescentadas conforme os defeitos aparecem |
| Rota no nginx | `location ~* ^(?:/w/[0-9]+)?/(?:cem\|itbi?\|agua?\|jur\|div\|tra)[0-9]*_` |
| **Próximo módulo** | os pequenos (`mar` 35, `tri` 33, `dvr` 33, `inf` 30, `not` 14) → `arr` → `fis` → `iss`. Ver *ORDEM REVISTA*. |
| **Dívida técnica aberta** | `dbagata/` (1 arquivo alcançável, pré-requisito do `iss`) e `fpdf151/` (28 arquivos). Ver *6ª LACUNA*. |

**Como subir o ambiente** (a ordem importa — 8.5 e proxy dependem da rede criada pelo 5.6):

```bash
docker volume create ecidade_sessions && docker volume create ecidade_tmp
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d
docker exec ecidade_php56 chmod 1777 /tmp      # o volume nasce root:root 755
chmod -R 777 storage bootstrap/cache && chmod 777 extension/log
chmod 777 tmp arquivos                        # SEM isto, 11% das telas falham antes de executar
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

**Progresso da Fase A:** `cem` ✅ · `itb`/`itbi` ✅ · `agu` ✅ · `jur` ✅ · `div` ✅ — restam 7 prefixos.

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
1. enumerar, em SEIS frentes       -> verificar: cada frente fecha (ver abaixo)
2. varrer as categorias conhecidas -> verificar: inventário fechado
3. classificar cada ocorrência     -> verificar: nenhum falso-positivo de JavaScript
4. aplicar em nível de byte        -> verificar: zero remanescentes
5. php -l nos DOIS runtimes        -> verificar: 100% OK em 5.6 e 8.5 (com </dev/null!)
6. instanciar as classes           -> verificar: estado idêntico entre runtimes
7. comparar as telas com sessão    -> verificar: byte-a-byte, normalizando ids aleatórios
8. acrescentar o prefixo ao nginx  -> verificar: X-Ecidade-Runtime = PHP-8.5
9. commit
```

**O passo 1 é o que mais falhou.** Seis lacunas distintas já foram encontradas ali, todas
com a mesma assinatura: a verificação partia da lista que a própria enumeração gerou, então
não podia achar o que a enumeração deixou de fora. As seis frentes:

| Frente | Como | Lacuna que fecha |
|---|---|---|
| prefixo | `re.IGNORECASE`, e aceitar sufixos de letra (`itbi`, `agua`) | maiúsculas; sub-prefixos |
| fecho de includes | `include(modification(...))` transitivo | — |
| citados em strings | nomes `*.php` dentro do código (o JS os abre) | 3ª: `window.open` |
| autoload | classes `cl_*` instanciadas, resolvidas em `classes/` | 4ª: `spl_autoload_register` |
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
| `porta.py` | 4: transformações mecânicas |
| `instancia_classes.php` | 6: estado das classes nos dois runtimes |
| `cmp.py` | 7: comparação das telas |

`porta.py` **usa a mesma detecção de `enumera.py`** — em especial a de `parse_str`, que conta
vírgulas no nível superior. Foi a divergência entre as duas que deixou duas telas do `jur`
fatais depois do porte. E ele **aborta** diante de caso que exige decisão humana (separador de
`split()` com metacaractere, arquivo com mais de uma classe), em vez de transformar errado.

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
Ocorre sempre que a consulta traz **zero linhas** — por isso aparece muito neste banco de
exemplo, que tem várias tabelas do Cemitério vazias.

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
