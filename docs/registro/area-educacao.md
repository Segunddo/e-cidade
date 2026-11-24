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

## Movido de `trabalho-relacionado.md` em 27/10/2026

> Estas subseções estavam fisicamente depois da comparação com o TCC no `CLAUDE.md` antigo, e a divisão de
> 26/10 as levou junto. Texto sem alteração.

##### ⚠ O instrumento, de novo: resposta cortada pelo `curl -m 60` virava divergência

`mer3_mer_nutriitem002.php` leva **~53 s nos dois runtimes** (495 alimentos, uma consulta por
item). Sob a carga da bateria passa de 60 s, o `curl` corta a resposta — **com código 200** — e
cada lado corta num ponto diferente: 1,3 MB contra 1,3 MB, depois 2,65 MB contra 2,48 MB.
Isolada, dá 2.652.582 bytes idênticos nas duas portas. O `cmp.py` passou a registrar o
`time_total` e trata resposta que bate no limite como `TIMEOUT`. `bib2_reditoras002` (1 byte) é
o horário dentro do PDF comprimido: idêntica em 4 repetições isoladas.


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

## 🔁 Refeita sobre a `base-php74` (19/11/2026)

Com o PR #8 da DBSeller, a referência passou a ser o **PHP 7.4** (`:8080`), não mais o 5.6. A
área foi refeita do zero a partir de `982a95fb5` (`base-php74`), mantendo a regra de sempre: **reproduzir o 7.4, não corrigir bugs antigos**.

### Escopo

Universo de 3.028 arquivos da Educação: telas `edu/esc/rel/sec/tre/bib/mer`, classes, `forms` e
`func_` das tabelas dos esquemas `escola`, `merenda`, `biblioteca` e `transporteescolar`,
`model/educacao` e `src/Educacao`. Núcleo (`std/`, `libs/`, `dbforms/`, `fpdf151/`, classes
compartilhadas), `scratchpad/`, `composer*`, `vendor/` e Laravel ficaram de fora — o que
apareceu neles virou anotação para o dono (abaixo).

### Commits e pull requests

Um único PR para `base-php85` (a branch que recebe o código migrado), ligado à issue da área, a partir da branch
`educacao/php85-migrado`. Ela parte da `base-php85` de 21/11/2026 (`111125fb5`, que já traz o núcleo migrado e os PRs
do Tributário, Financeiro, Gestor, Cidadão, Integrações e Assistência Social, além da correção de `parse_str` do grupo
para todas as áreas). Commits do Rector e manuais nunca misturados: primeiro vêm os do Rector, depois os manuais, para
que a revisão possa ir commit a commit.

| Grupo de commits (em ordem) | Conteúdo | Arquivos |
| --- | --- | --- |
| Rector nas classes | classes das tabelas; classes que ficaram fora dos alvos (guarda `0 == ""`); 50 classes `ed*`/`bi*` achadas pela regressão | 343 |
| Rector em telas, `model` e `src` | `model/educacao` e `src/Educacao`; ternário aninhado em 2 telas; `$$x` → `${$x}` em 11 telas | 23 |
| Correções manuais | correções fiéis ao 7.4; guardas achadas na regressão final; este registro. **Revisar linha a linha** | 104 |

No total são 464 arquivos. Os três grupos foram preparados antes como PRs separados e independentes, cada um aplicando
direto na base. Depois foram juntados num PR só sem mudar nenhum arquivo: a árvore final é a mesma.

O trabalho foi feito sobre `982a95fb5`. Nas telas e nas `func_`, `parse_str` com um argumento usava a forma decidida
pelo grupo em 19/11/2026 (decisão 3): `parse_str(x, $__qs); unset($__qs['this'], $__qs['GLOBALS']); extract($__qs);`,
numa linha, com o espaçamento original de `x`, igual byte a byte à correção do grupo. Quando essa correção entrou na
`base-php85`, 509 telas e todas as 258 janelas `func_` da Educação ficaram **idênticas** às nossas, e 4 classes
ficaram idênticas pelo PR do Financeiro. Depois, o PR da Assistência Social levou à base mais 134 classes de dados que
as telas `soc` usam, com o mesmo Rector: ficaram **idênticas** às nossas, sem conflito. Esses arquivos saíram do PR,
incluindo todas as `func_`. No `edu2_certconclusao002.php` ficou só a linha do ternário: o Rector tinha tirado os espaços do fim de 64 linhas em
branco, sem efeito na saída.

### O que o 7.4 faz e o 8.5 não (medido nos dois containers)

| Expressão | 7.4 | 8.5 | Correção fiel |
| --- | --- | --- | --- |
| `pg_num_rows(false)` e afins | aviso, `NULL` | `TypeError` | `($r ? pg_x($r) : null)` — 148 linhas, 65 arquivos |
| `x / 0` | aviso, `INF`/`-INF`/`NAN` | `DivisionByZeroError` | devolve o mesmo `INF`/`-INF`/`NAN` (2 arquivos) |
| `0 != ""` | `false` | `true` | `($x != "" && $x !== 0 && $x !== 0.0)` (5 classes BNCC) |
| `file_get_contents("")` | `false` | `ValueError` | guarda (3) |
| propriedade em `null` | cria `stdClass` | `Error` | `new stdClass` explícito (1) |
| `count(null)` | 0 com aviso | `TypeError` | `count((array)$x)` (1) |
| `array_unique(null)` / `natsort(null)` | aviso, `NULL` | `TypeError` | `is_array` antes (1) |
| `"" + 1`, `"07:30" <= 1800` | aviso; converte o número inicial | `TypeError` / compara como texto | cast `(int)`/`(float)` (2) |
| `pg_last_error()` sem conexão | `false` | erro | `try/catch` (1) |
| assinatura incompatível com a mãe | aviso | fatal | parâmetros opcionais iguais aos da mãe (4) |

Mantida a versão da DBSeller (sem portar a correção antiga): `bib1_reserva004` (octal),
`edu1_matricula003`, `edu1_avaliacaoestruturanota001`, `edu4_avaliacaoestruturafrequencia001/002`,
`edu2_historico002`, `ProgressaoParcialVinculoDisciplina` e os `forms` com constante indefinida.

### Verificação

Verificação por lote, contra `982a95fb5` (universo de 3.029 arquivos, 437 classes):

| Passo | Antes das correções | Final | Observação |
| --- | --- | --- | --- |
| 5 `php -l` nos dois runtimes | 0 erros novos | 0 erros novos | 4 pré-existentes, falham também no 7.4 |
| 5b carga (LSP) | 7 só no 8.5 | 5 só no 8.5 | os 5 são `RelatorioDiarioClasse*`, que herdam de `fpdf151/pdf.php` (núcleo) |
| 6 instanciar classes | OK | OK | 437 classes |
| 6b caminho de escrita | 110 linhas | 6 linhas | as 6 são de `db_linhacolunavalorinformacaocomplementar` (Financeiro) |
| 6c forma negada | 30 | 3 | as 3 são da mesma classe do Financeiro |

Além disso: HTML inline idêntico ao da base em 1.279 arquivos (`token_get_all`, `T_INLINE_HTML`),
codificação ISO-8859-1 preservada, fim de arquivo restaurado onde o Rector acrescentou uma quebra de linha.
A conferência de funções novas acusa `extract`, `is_array` e `preg_split` porque ainda compara com o 5.6; as
três existem no 7.4. A bateria byte a byte (passo 7) não rodou: depende do núcleo portado.

### Regressão no ambiente `e74` (19/11/2026)

Bateria PHP da suíte `regressao/` (branch `regressao-php74`), referência 7.4 (:8074) × alvo 8.5 (:8185), sobre as
1.570 telas `bib/edu/esc/mer/rel/sec/tre`, as classes que elas usam e a sintaxe. Mesma baseline do banco nas duas
rodadas (dump local gerado pela seção 2 do README da regressão, não o v2 do time: os números valem como comparação
antes × depois, não como baseline oficial).

| Bloco | Antes (base) idêntico / diverge | Depois (4 PRs) idêntico / diverge |
| --- | --- | --- |
| Classes (320) | 1 / 317 | 279 / 39 |
| Sintaxe (1.569) | 1.563 / 2 | 1.565 / 0 |
| Telas (1.570) | 650 / 851 | 1.064 / 382 |

**Nenhum caso que era idêntico passou a divergir.** 694 casos passaram de "diverge" para "idêntico". Das 39 classes
que ainda divergiam, 36 são de outras áreas (material, RH, CGM, configuração, saúde, veículos) usadas pelas telas da
Educação; as outras 3 levaram à correção das 51 classes `ed*`/`bi*` (commit próprio no PR `educacao/classes`). Das
telas que ainda divergem, quase todas são HTTP 500 só no 8.5, o padrão dos defeitos do núcleo listados abaixo.

### Telas `mat` e `pro` do menu da Educação (20/11/2026)

A issue da área lista, além dos prefixos próprios, 22 telas `mat` (almoxarifado: requisição, estoque, transferência)
e 1 `pro` (`pro1_tipoarq002.php`) que o menu da Educação também abre. As `mat` são compartilhadas com o Patrimonial
(uma também com a Saúde). Medido sobre os PRs da Educação:

- Rector do grupo (`rector-curado.php`): **0 arquivos** a alterar nas 23; `php -l` limpo no 7.4 e no 8.5.
- Regressão do grupo (e74), 7.4 × 8.5: **21 idênticas**. As outras 2 (`mat1_atendrequi001.php` e
  `mat1_matestoquesai001.php`) dão 500 só no 8.5 por `pg_num_rows(false)` em `libs/db_utils.php:186`
  (`getCollectionByRecord`), ou seja, no núcleo, não na tela. Com a guarda dos wrappers do núcleo da decisão 2a
  (`PHP8-31`, branch do `parse_str`) as duas ficam **idênticas** ao 7.4. Essa guarda já está na `base-php85`.

Conclusão: nenhuma das 23 precisa de alteração da Educação; nenhum arquivo delas entra nos PRs.

### Regressão final e causa de cada tela que ainda diverge (20/11/2026)

Nova rodada completa da bateria do grupo (e74, mesmo universo de 1.570 telas) com o código final, seguida da
classificação **tela a tela** das que ainda divergiam: para cada uma, a mensagem real do erro no 8.5 foi lida com o
modo de depuração ligado só na sessão de teste, e o 7.4 foi lido com a sessão restaurada, como faz a bateria.

| Bloco | Antes (base) idêntico / diverge | Final idêntico / diverge |
| --- | --- | --- |
| Classes (320) | 1 / 317 | 282 / 36 |
| Sintaxe (1.569) | 1.563 / 2 | 1.565 / 0 |
| Telas (1.570) | 650 / 851 | 1.072 / 420 |

**Nenhum caso que era idêntico passou a divergir.** A classificação achou 23 arquivos da Educação que ainda lançavam
erro só no 8.5, onde o 7.4 só avisava e seguia (alguns só apareciam como página cortada no meio, com HTTP 200).
Corrigidos num commit próprio, cada forma medida nos dois runtimes:

| Expressão | 7.4 | 8.5 | Correção fiel | Arquivos |
| --- | --- | --- | --- | --- |
| `pg_num_rows`/`pg_result`/`pg_fetch_assoc` recebendo `false` | aviso, `NULL` | `TypeError` | forma da decisão 2a; chamada aninhada `pg_x(db_query(...))` ganha uma variável | 18 (29 linhas) |
| `count(null)` | 0 com aviso | `TypeError` | `count((array)$x)` | 3 |
| `mktime` com `substr` de data vazia | aviso, `false` | `TypeError` | `(is_numeric(ano) ? mktime((int)...) : false)` | 1 (5 linhas) |
| `$GLOBALS[Sed47_x]` fora de string | aviso, usa o texto | `Error` (constante indefinida) | chave entre aspas | 1 (2 linhas) |

**Prova com o núcleo corrigido** (só no ambiente de teste, desfeita no fim): aplicando as correções de núcleo que já
existem em outras branches — guardas da decisão 2a em `libs/db_stdlib.php` e `libs/db_utils.php` (`PHP8-31`), e
`fpdf151/fpdf.php`, `libs/JSON.php`, `dbforms/db_funcoes.php`, `dbforms/db_classesgenericas.php` da
`nucleo/correcoes-transversais` — mais a assinatura do tratador de erros (abaixo), **347 das 428 telas que divergiam
ficam idênticas**. Das 20 que sobram, **nenhuma é da Educação**:

- 16 quebram **também no 7.4** (bug antigo, registrado e não corrigido): `bib3_leitorcons002`,
  `edu1_diarioavaliacao001`, `edu1_diarioavaliacaoobs001`, `mer1_mer_desper_und003` (não compilam);
  `edu1_grauensino001/002/003` (classe `cl_grauensino` inexistente); `edu1_matriculadependecia002/003` (arquivo de
  classe inexistente); `edu2_avaliacoesperiodo004`; `edu2_relacaonominal002` (classe de exceção inexistente em
  `src/Educacao`); `edu3_consultafuncaoexercida003`; `mer1_mer_cardapionutri002/003`; `mer1_mer_cardapioturma002/003`.
  Divergem só porque a página de erro tem tamanho diferente.
- 4 param no núcleo: `libs/db_libsys.php:146` e `libs/db_stdlibwebseller.php:437` (`pg_*` com `false`) e
  `std/DBDate.php:497` (`cal_days_in_month` com mês 0: aviso no 7.4, `ValueError` no 8.5), em 2 telas.

As 61 restantes são inconclusivas (página de erro idêntica nos dois lados ou resposta vazia): a tela não foi exercitada.

Estas medições foram feitas sobre `982a95fb5`. Desde então a `base-php85` recebeu as guardas da decisão 2a em
`libs/db_stdlib.php`, `libs/db_utils.php`, `libs/db_libsys.php` e `dbforms/db_classesgenericas.php`. Os PRs foram
refeitos sobre ela sem mudar nenhuma linha de código da Educação (fora os espaços do `edu2_certconclusao002.php`).
`php -l` dos 597 arquivos alterados, já juntos com a base nova: 0 erros no 7.4 e no 8.5.

### Regressão sobre a `base-php85` nova (20/11/2026)

A bateria foi repetida duas vezes sobre `6d881031b`, no mesmo ambiente e universo: a base sozinha (referência) e a
base com os 3 PRs juntos.

| Bloco | `base-php85` idêntico / diverge | `base-php85` + 3 PRs idêntico / diverge |
| --- | --- | --- |
| Classes (320) | 12 / 306 | 291 / 27 |
| Sintaxe (1.569) | 1.563 / 2 | 1.565 / 0 |
| Telas (1.570) | 1.095 / 390 | 1.164 / 320 |

- **350 casos de diverge → idêntico** com os PRs; **nenhum caso que era idêntico na base passou a divergir**.
- Um caso foi de diverge para inconclusivo (`mer4_mer_subitem_ajax004.php`: resposta vazia nos dois lados).
- As 27 classes que ainda divergem são de outras áreas (`mat`, `rh`, `veic`, `sau`, `lab`, `tfd`, `cidadao`, `db_uf`),
  todas com o mesmo padrão (código gerado vira `0` no 8.5); ficam para os donos.
- Comparado com a rodada final sobre a base antiga (mesmo código da Educação): mais 101 casos idênticos, graças às
  guardas de núcleo que entraram na base, e nenhum caso que era idêntico deixou de ser.

Em 21/11/2026 a `base-php85` foi para `111125fb5` (núcleo migrado e mais quatro áreas). Os 3 PRs foram refeitos sobre
ela, de novo sem mudar nenhuma linha de código da Educação: só saíram as 134 classes que já chegaram idênticas.
Nenhum arquivo dos PRs foi tocado de forma diferente pela base. `php -l` dos 463 arquivos `.php`, já juntos com a
base: 0 erros no 7.4 e no 8.5.

### Regressão sobre a `base-php85` de 21/11/2026 (`111125fb5`)

Bateria repetida em 23/11/2026 no mesmo ambiente e universo: a base sozinha e a base com os 3 PRs juntos (a mesma
árvore do PR único de `educacao/php85-migrado`).

| Bloco | `base-php85` idêntico / diverge | `base-php85` + 3 PRs idêntico / diverge |
| --- | --- | --- |
| Classes (320) | 112 / 206 | 310 / 8 |
| Sintaxe (1.569) | 1.563 / 2 | 1.565 / 0 |
| Telas (1.570) | 1.322 / 111 | 1.415 / 16 |

- **293 casos de diverge → idêntico** com os PRs; **nenhum caso que era idêntico na base passou a divergir**.
- As **16 telas** que ainda divergem são exatamente as 16 da regressão final que quebram **também no 7.4** (HTTP 500
  nos dois lados; só o tamanho da página de erro muda). Bug antigo, registrado e não corrigido. As 4 que paravam no
  núcleo deixaram de divergir com o núcleo da base.
- As **8 classes** que ainda divergem são de outras áreas (`lab`, `rh`, `sau`, `tfd`, `veic`).
- Duas telas foram de diverge para inconclusivo (resposta vazia nos dois lados): `edu2_gfcoescfreqseries002.php` e
  `mer4_mer_subitem_ajax004.php`.
- Comparado com a rodada de 20/11 com os PRs: mais 270 casos idênticos, e nenhum que era idêntico deixou de ser. Os
  inconclusivos subiram de 78 para 131 telas: são telas que agora dão a mesma página de erro (ou resposta vazia) nos
  dois runtimes, ou seja, o 8.5 passou a responder como o 7.4, mas a bateria não consegue exercitá-las.

### Fora da Educação (anotado para os donos)

- `libs/db_app.utils.php:39` (`DB_VERSION` indefinida com a sessão da API) e o retorno
  antecipado do `db_conecta` — núcleo; a `base-php85` já usa `defined()` desde 21/11.
- `fpdf151/fpdf.php`: `ParseError` no 8.5 — derrubava **todo** relatório em PDF (inclusive os
  `RelatorioDiarioClasse*` da Educação, que só falham por herdarem dele). Corrigido na `base-php85` em 21/11.
- Tabela `configuracoes.itens_menu_usuario_favoritos` ausente no banco de teste.
- Sessão de login real recusada pelas telas legadas na `base-php74`; só a sessão da API serve.
- A verificação por lote ainda confere as funções novas contra o 5.6 (`extract`, `is_array`, `preg_split`
  existem no 7.4: falso alarme).
- Rector por lote: em máquina com pouca RAM a execução paralela estoura o tempo (lotes de 80
  resolvem) e duas execuções no mesmo minuto sobrescrevem a pasta de saída.
- A enumeração dos alvos deixa arquivos de fora (ternário aninhado, classes sem a guarda, arquivos só
  com correção manual) — achados pela sintaxe e pelos testes de escrita.
- Sugestão para a configuração oficial do Rector: banir `ThisCallOnStaticMethodToStaticCallRector` e aceitar
  `FinalPrivateToPrivateVisibilityRector` na configuração oficial.
- `db_linhacolunavalorinformacaocomplementar_classe.php` (Financeiro): divergências no 6c.
- 4 arquivos não compilam nem no 7.4 (pré-existentes): `bib3_leitorcons002`,
  `edu1_diarioavaliacao001` (`<?php` duplicado), `edu1_diarioavaliacaoobs001`,
  `mer1_mer_desper_und003`.
- `src/V3/Error/Handler/Error.php`: `_handle` e `handle` exigem 5 parâmetros (`$context`), mas o PHP 8 chama o
  tratador de erros com 4. Todo aviso vira `ArgumentCountError` e a página para no meio (HTTP 200 cortado ou 500).
  Ainda sem correção na `base-php85` de 21/11; com `$context = null` o comportamento volta ao do 7.4.
- `libs/db_stdlibwebseller.php:437`, `std/DBDate.php:497` e `libs/db_libsys.php:146`: ver a regressão final acima.
  Os três já estão corrigidos na `base-php85`.
- Bateria byte a byte (passo 7) bloqueada até o núcleo ser portado; roteamento no nginx
  deliberadamente **não** feito.
