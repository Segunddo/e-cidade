# Área Educação

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

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

**⚠ 13ª LACUNA (21/10/2026, achada no RH): classes de `model/` carregadas por autoload, sem `cl_`.**
`new Classe`/`Classe::` de `model/`/`std/` sem `include` não entravam em universo nenhum. No universo da
Educação o fecho alcança **596 arquivos** fora dele; só **1** precisava de porte:
`model/educacao/progressaoparcial/ProgressaoParcialVinculoDisciplina.model.php` — `unset($this)`, erro de
compilação desde o PHP 7.1. No 5.6 só desligava a variável local e era a última instrução do método:
removido. Nenhuma LSP nas 172 classes com `extends`.
