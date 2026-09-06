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

Critérios de sucesso sólidos permitem que você trabalhe de forma independente. Critérios vagos ("fazer funcionar") exigem esclarecimentos constantes.

# e-cidade — Projeto de Migração

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

Números obtidos com varredura byte-a-byte em Python (`scratchpad/incompat.py`), não com grep.
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
| **Com APENAS construtor PHP4 (quebram em silêncio)** | **3.560** |
| Destas, com chamada explícita ao nome antigo (exigem cuidado extra) | 7 |

Distribuição: `classes/` **3.417**, `dbagata/` 70, `libs/` 37, raiz 28, demais 8.

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

Lista completa de arquivos afetados: `scratchpad/afetados.txt`.

## Bloqueadores duros (não se resolvem com `composer update`)

- **`silex/silex ^2.0`** — projeto morto, sem versão para PHP 8. Precisa ser absorvido pelo Laravel.
- **`doctrine/dbal 2.*`** — incompatível com PHP 8+.
- **`symfony/* ~3.2`** — EOL.
- **`zendframework/zend-eventmanager 2.2.10`** — projeto descontinuado/renomeado.
- **`dbseller/session`** — vem de `git@github.com:DBSeller/Session.git`, **repositório privado**.
  Sem acesso, o `composer install` pode nem completar. *Verificar isso antes de qualquer coisa.*
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

Analisador em `scratchpad/depgraph.py` + `esforco.py`. Extrai includes do idioma legado
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

- **Fase 0 — Linha de base.** Ambiente PHP 8.5 + PG 18 em paralelo (sem tocar no 5.6), medir
  superfície de erro real por módulo. ✅ Grafo de dependências concluído — piloto definido: `tra`.
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

**Assimetria pré-existente conhecida** (não introduzida pela migração): `tmp/`, `storage/` e
`arquivos/` são `775 diego`, portanto **não graváveis por nenhum dos dois containers** (uid 33).
Isso é a linha de base do ambiente e foi deixado como está. Se alguma tela precisar gravar
nesses diretórios, ela falhará **igualmente** nos dois — o que preserva a comparabilidade.

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
**normalizando identificadores aleatórios** (`sid=`, `arquivo=<base64>`, `wname<n>`) — sem
normalizar, nomes de arquivo temporário geram ~6 falsos positivos.

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

**Divergências restantes (4), todas caracterizadas:**

- `cem1_itenserv002.php` — **quebra no 5.6 (500) e funciona no 8.5 (200)**. Defeito
  pré-existente da referência (`label() on null` em `forms/db_frmitenserv.php:29`), não da migração.
- `cem3_sepultamentos004.php` — 8.5 trunca a saída (417 vs 5.566 bytes); `pg_numrows(false)`
  em caminho ainda não coberto.
- `cem2_emitecertisen002.php` — ambos falham ao gerar o relatório; difere só o prefixo
  `<b>Mensagem: </b>` na saída de erro.
- `cem2_renovacoes.php` — saída binária (relatório), diferença não caracterizada.

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
- As cópias em `file/sync/user/<login>/` estão **vazias (0 bytes)** — quem executa é `cache/`.
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
`php -l` sob PHP 8.5 em todos os arquivos — medição ainda não feita.

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

**ARMADILHA `Host $host` vs `$http_host`:** o e-cidade monta URLs absolutas a partir de
`HTTP_HOST` (ver `$DB_URL_ABS` em `libs/db_stdlib.php`). A variável `$host` do nginx
**descarta a porta**; com ela o sistema gerava `http://localhost/skins/estilos.php?...`,
o navegador buscava na porta 80 e **a tela vinha inteira sem CSS, JS nem fontes**. Usar
sempre `proxy_set_header Host $http_host;`, que preserva `localhost:8090`. Sintoma
enganoso: parece falha de migração e é configuração de proxy.

Nota operacional: o nginx.conf entra por bind mount de **arquivo único**; editar o arquivo no
host cria um inode novo e o container continua com o antigo. Depois de editar, use
`docker compose -f docker-compose.proxy.yml up -d --force-recreate` (um `nginx -s reload` não basta).

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

# ambiente de migração (PHP 8.5)
docker compose -f docker-compose.php85.yml up -d --build # :8085
docker compose -f docker-compose.php85.yml down

# erros do runtime 8.5
docker exec ecidade_php85 cat /var/log/php_errors.log
tail -f extension/log/error.log        # log da própria aplicação

composer test                 # vendor/bin/phpunit
npx cypress open              # specs em tests/cypress/integration
```
