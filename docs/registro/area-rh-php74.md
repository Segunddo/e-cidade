# Área Recursos Humanos na base-php74 — dimensionamento da migração para o PHP 8.5

> Branch: `pessoal/rh-php85` (a partir da `base-php74`). Data do dimensionamento: 18/11/2026.
> Guia: `base-php84`. Referência funcional: PHP 7.4. **Nenhum código foi alterado nesta fase** — só medição.
> Escopo: prefixos `rh`, `eso`, `rec`, `pes` (`[0-9]*_`) e `src/RecursosHumanos`. O registro da migração anterior
> (sobre o 5.6) continua em `area-recursos-humanos.md`.

## Decisões do usuário (18/11/2026) — valem para toda a área

1. **c2:** critério = **manter a 74 e acrescentar só o que o 8.5 exigir**, usando a 84 como referência de *como* corrigir.
   `pes1_reajusteprog001.php` **não se altera**: não compila em PHP algum, é defeito pré-existente da DBSeller — fica
   **caracterizado e para reportar** (ver *Defeitos caracterizados*).
2. **c1:** a regra "manter a 74 (`explode`)" vale **só para separador literal**. Separador com metacaractere de regex
   (`+ * ? [ ] ( ) | . ^ $ \`) fica com `preg_split`, como manda a skill. Os 51 foram conferidos um a um (ver *c1*).
3. **`src/RecursosHumanos`:** aprovado como **lote 1B**, logo depois de rh+eso.
4. **`esocial_externo.RPC.php` e `rhpessoalmov001.RPC.php`:** entram no lote rh+eso.
5. **Pedidos ao núcleo:** a divisão de quem porta o quê (RH × núcleo × DAOs) **ainda será decidida com o coordenador**; as
   contagens abaixo servem a essa conversa.

## Método

Três vias, com a base comum `e640eb485` (merge-base das duas branches = `master`):

- **mudança da DBSeller** = `diff(e640eb485, base-php74)`; **mudança da migração** = `diff(e640eb485, base-php84)`;
- por arquivo: só uma das duas → classificação direta; as duas → `git merge-file` (limpo ou com conflito);
- cada conflito foi conferido de novo **normalizando espaço no fim da linha e `<?` → `<?php`** (a DBSeller reformatou os
  arquivos): só 2 de 81 eram formatação; os outros 79 são conflitos reais;
- `php -l` no 8.5 (imagem `e-cidade-ecidade_php85`, PHP 8.5.12, `docker run --rm` com `./ecidade` somente leitura, sem banco);
- universo fora da área por `scratchpad/enumera.py` (nove frentes) nos quatro prefixos, sobre a base-php74.

Universo da área: **2.129 arquivos** (`(rh|eso|rec|pes)[0-9]*_*` + `src/RecursosHumanos`; este tem 585). Das alterações
na área, a **DBSeller mexeu em 1.343** arquivos (34 novos), a **migração anterior em 517**; **476 foram tocados pelos dois**;
745 arquivos não foram tocados por nenhum.

## Classes usadas

| Classe | Significado | Ação |
|---|---|---|
| **a1** | só a base-php84 mudou (a 74 não tem) | trazer a versão da 84 |
| **a2** | os dois mudaram, `merge-file` **limpo** | aplicar a mudança da 84 por 3 vias, mantendo a da DBSeller |
| **b** | só a base-php74 mudou (funcionalidade DBSeller; inclui 34 arquivos novos) | **preservar**; ainda passa pelo Rector e `php -l` do lote |
| **c1** | conflito só de `split()` **literal**: a 74 já converteu para `explode()`, a 84 usou `preg_split("#,#m")` | manter a da 74; aplicar o resto da 84 |
| **c2** | conflito real, ou fora da regra do c1 | manter a 74 e acrescentar só o que o 8.5 exigir (decisão 1) |

## Tabela por prefixo

| Grupo | Arquivos | a1 | a2 | b | c1 | c2 | Sem mudança |
|---|---:|---:|---:|---:|---:|---:|---:|
| rh + eso | 94 | 0 | 0 | 31 | 0 | 0 | 63 |
| rec | 283 | 13 | 50 | 121 | 6 | 7 | 86 |
| pes3 + pes4 | 273 | 6 | 35 | 151 | 4 | 5 | 72 |
| pes1 | 370 | 11 | 129 | 159 | 9 | 5 | 57 |
| pes2 | 524 | 10 | 183 | 269 | 29 | 13 | 20 |
| src/RecursosHumanos | 585 | 1 | 0 | 136 | 0 | 1 | 447 |
| **Total** | **2.129** | **41** | **397** | **867** | **48** | **31** | **745** |

`pes1_reajusteprog001.php` está contado em *b* (a DBSeller o alterou), mas não compila: *Defeitos caracterizados*. c1 e c2 já
reúnem a reclassificação de 18/11/2026 (3 arquivos de c1 para c2).

Achados que mudam o plano:

1. **A DBSeller já fez parte da migração para o 7.x** (`split()` → `explode()`). Por isso 120 trechos em conflito são "os dois
   converteram"; o trabalho real é menor que o diff da 84 sugere.
2. **`rh` e `eso` não tiveram nenhuma mudança na migração anterior**: o lote 1 é validar (`php -l` ok) e passar o Rector
   sobre os 31 arquivos *b*.
3. **Os 867 arquivos *b* nunca passaram pelo Rector.** Preservar a funcionalidade não dispensa o porte: eles têm de ser varridos
   pelas categorias do 8.5 (`$this->X == literal`, `parse_str` de 1 argumento, `each`, construtor PHP 4…). O inventário do
   `enumera.py` sobre a 74, no universo do `pes`, dá 4.279 arquivos e 1.497 a alterar (6.931 ocorrências de `$this->X == literal`,
   421 de `parse_str`, 111 de `split(`, 24 de `each(`, 22 construtores PHP 4, 1 `{}` em string). O número inclui o fecho em
   `classes/`/`libs/`, **fora da área** (ver *Pedidos ao núcleo*). Para os outros prefixos: `rh` 2.402 arquivos/856 a alterar,
   `eso` 2.647/877, `rec` 2.921/1.000.
4. A DBSeller mudou o **modo** de arquivos (755 → 644) e reformatou (`<?` → `<?php`, espaço no fim da linha): diffs de 3 vias têm
   ruído; conferir com `git diff --ignore-cr-at-eol -w`. O código segue em ISO-8859-1.

## php -l no 8.5 (base-php74)

2.126 arquivos `.php` da área verificados; **2 não compilam**:

| Arquivo | Erro | Classe | Observação |
|---|---|---|---|
| `src/RecursosHumanos/RH/PontoEletronico/Calculo/Horas/Falta.php` | l. 143: *Unparenthesized `a ? b : c ? d : e` is not supported* | a1 | a 84 já corrige (parênteses à esquerda, associação do 5.6) e compila no 8.5 |
| `pes1_reajusteprog001.php` | l. 132: *Unmatched '}'* | c2 | **defeito introduzido pela DBSeller**: a base antiga e a 84 têm o arquivo sem a edição; o bloco novo do eSocial deixou chaves desbalanceadas. Não compila em versão alguma do PHP |

`php -l` não pega fatal de **carga** (LSP) nem *TypeError* de execução: o passo `carrega_arquivo.php` nos arquivos de `src/` com
`extends`/`implements` continua necessário no lote.

## Lista (c) — precisa de decisão

### c2 — 31 conflitos que exigem leitura (28 reais + 3 vindos de c1) — critério: manter a 74, acrescentar só o que o 8.5 exigir

`pes1_relac002.php`, `pes1_rhcontasrec003.php`, `pes1_rhteutri002.php`, `pes1_rhteutri003.php`, `pes2_admitidos002.php`, `pes2_analitica002.php`, `pes2_bb240cnabgeracao002.php`, `pes2_func_e_depend002.php`, `pes2_pensalim002.php`, `pes2_relcad001.php`, `pes2_relfichafinanceira002.php`, `pes2_relfichafinanceiratxt002.php`, `pes2_resumorecursoempenhos002.php`, `pes2_rhteutri002.php`, `pes2_sapestagioprob002.php`, `pes2_termorescisao002.php`, `pes2_valetransp_anual002.php`, `pes3_consponto001.php`, `pes3_conspontoregistro002.php`, `pes3_gerfinanc001.php`, `pes3_gerfinanc018.php`, `pes4_rhfopag91002.php`, `rec1_protelac002.php`, `rec1_protelac003.php`, `rec2_certcomprobatorio002.php`, `rec2_relassentaporperiodo002.php`, `rec2_vantagens002.php`, `src/RecursosHumanos/ESocial/Integracao/Formatter/AlteracaoDadosServidorFormatter.php`, **mais os 3 vindos de c1:** `pes1_importainfla001.php`, `rec1_leis001.php`, `rec1_leis002.php`.

Conflito real = a 84 e a 74 alteraram as mesmas linhas de forma **diferente**. Nos 79 arquivos em conflito havia 43 trechos que não são
`split` nem guarda `0==""` e 7 de guarda `0==""`. **Decisão (item 1):** mantém-se a 74 e acrescenta-se só o que o 8.5 exigir, usando a 84
como referência de *como* corrigir. Cada arquivo ainda precisa ser lido no lote; não há resolução automática.

### c1 — 48 conflitos só de `split` com separador literal (resolução aprovada: manter a 74, `explode`)

`pes1_pontoRfx0011.php`, `pes1_pontoRfx0011_iframe.php`, `pes1_rhbases004.php`, `pes1_rhcadcalend002.php`, `pes1_rhempexcluirsol001.php`, `pes1_rhrubricas004.php`, `pes1_rhrubricas005.php`, `pes1_virafolha001.php`, `pes1_virafolha003.php`, `pes2_acountcadastro001.php`, `pes2_acountponto001.php`, `pes2_aleemitearqbanco002.php`, `pes2_bagemitearqbanco002.php`, `pes2_banrisul240cnab002.php`, `pes2_banrisul240cnabgeracao002.php`, `pes2_bb240cnab002.php`, `pes2_caremitearqbanco002.php`, `pes2_cef240cnabgeracao002.php`, `pes2_daeemitearqbanco002.php`, `pes2_emitearquivobancario_banrisul002.php`, `pes2_gerabbrasil001.php`, `pes2_guaemitearqbanco002.php`, `pes2_guaemitebb200lay002.php`, `pes2_impactoorc001.php`, `pes2_itaemitearqbanco002.php`, `pes2_itau240cnab002.php`, `pes2_itau240cnabgeracao002.php`, `pes2_liquido001.php`, `pes2_osoemitearqbanco002.php`, `pes2_osoemitebb200lay002.php`, `pes2_relfuncaolotacaoorgao001.php`, `pes2_relrub002.php`, `pes2_retconsig002.php`, `pes2_retconsigfolha002.php`, `pes2_sapconfcaixa002.php`, `pes2_sapemitebb200lay002.php`, `pes2_sapretconsig002.php`, `pes2_valetransp_anual001.php`, `pes4_cadferia004.php`, `pes4_contratosemergenciais.RPC.php`, `pes4_implantaferias001.php`, `pes4_rhpesrescis004.php`, `rec1_assentamdia002.php`, `rec1_assentamdia003.php`, `rec1_portlotecolexc003.php`, `rec2_gradeefetividade002.php`, `rec2_tabcurritipo001.php`, `rec4_bancohoras.RPC.php`.

**Conferência um a um (feita em 18/11/2026):** nos 51 arquivos há 107 trechos em conflito com `split(` no lado da base (a conferência leu o lado da base de cada trecho). Separadores:
110 chamadas, **todas literais** (72 × `-`, 33 × `,`, 4 × `/`, 1 × `_`), onde `explode` equivale. Fogem da regra **3 arquivos** (113 chamadas ao todo), que
passaram para c2:

| Arquivo | Separador | O que fez a 74 | O que fez a 84 | Proposta |
|---|---|---|---|---|
| `rec1_leis001.php` (l. 40) | `"\|"` (regex: pipe escapado) | `explode("|", …)` | `preg_split("#\\|#m", …)` | pela regra, **preg_split** (84). O `explode("|")` da 74 é equivalente (pipe escapado = pipe literal), então pode-se manter a 74 se o usuário preferir |
| `rec1_leis002.php` (l. 42) | `"\|"` | idem | idem | idem |
| `pes1_importainfla001.php` (l. 67) | **variável** `$separador` | `explode($separador, …)` | `preg_split` com guarda que devolve `false` para separadores com `\|` | não dá para provar literal; manter a 84 (guarda) até ver a origem de `$separador` |

Observação: `pes1_pontoRfx0011_iframe.php` ainda tem 4 chamadas `split(` **não convertidas** na 74 (fora do trecho em conflito); são trabalho do Rector no lote.

### Outras decisões (resolvidas em 18/11/2026)

- `src/RecursosHumanos` → **lote 1B**, após rh+eso (aprovado).
- `esocial_externo.RPC.php` e `rhpessoalmov001.RPC.php` → **lote rh+eso** (aprovado; a DBSeller alterou os dois, a 84 não: classe *b*).
- `pes2_sapguiapatronal002.sal` e `pes4_gerafolha004_modificado.php.dist` (não-PHP) ficam de fora.

### Defeitos caracterizados (não se corrigem; reportar à DBSeller)

- `pes1_reajusteprog001.php`: `Unmatched '}'` na linha 132 — bloco novo do eSocial deixou chaves desbalanceadas. A base antiga e a 84
  têm o arquivo sem a edição. **Não compila em PHP algum**; pré-existente da DBSeller. **Não se altera** (decisão do usuário). A tela
  fica fora da bateria até a DBSeller corrigir; reportar.

## Lotes propostos (um por vez; commit local por lote)

| Lote | Escopo | Arquivos | Trazer (a1+a2) | Decidir (c1+c2) | Preservar (b) |
|---|---|---:|---:|---:|---:|
| 1 | `rh` + `eso` + 2 `.RPC.php` (aprovado) | 96 | 0 | 0 | 33 |
| 1B | `src/RecursosHumanos` (aprovado) | 585 | 1 | 1 | 136 |
| 2 | `rec` (rec1–rec4) | 283 | 63 | 13 | 121 |
| 3 | `pes3` + `pes4` | 273 | 41 | 9 | 151 |
| 4 | `pes1` | 370 | 140 | 14 | 159 |
| 5 | `pes2` | 524 | 193 | 42 | 269 |

Cada lote: enumerar (`enumera.py <prefixo>`) → `php -l` no 7.4 e no 8.5 sobre o **universo** → Rector (pin de versão, repetir até
zero) → `carrega_arquivo.php` nos de `src/` → bateria do lote. **Bloqueio de ambiente:** a bateria por proxy (7.4 × 8.5, `cmp.py`)
só roda com o ambiente do 7.4 de pé (o build falha hoje com 503 no Launchpad; Fase 1 pendente). Até lá, cada lote termina em
`php -l` + revisão do diff.

## PEDIDOS AO NÚCLEO

Arquivos **fora da área** que a migração anterior alterou, que o RH alcança (universo do `enumera.py` nos quatro prefixos: 4.979
arquivos, 2.929 fora da área) e que a base-php74 **ainda não tem corrigidos**. Dos 1.218 que a 84 alterou, a 74 já tem o
equivalente em 2. São pedidos ao dono do núcleo (CONTRIBUINDO, regra 5); nenhum foi alterado aqui.

### P1 — a 74 não tem nenhuma das correções (141: só a 84 mudou)

- `libs/db_app.utils.php` (`DB_VERSION` indefinida);
- `model/pessoal/std/DBPessoal.model.php` (`$F032 - $F031` com string vazia; cálculo da folha);
- `model/pessoal/folhapagamento/FolhaPagamento.model.php`, `FolhaPagamentoSalario.model.php`, `FolhaPagamentoSuplementar.model.php`,
  `model/pessoal/PontoFerias.model.php`, `model/linhaRelatorioContabil.model.php`;
- raiz: `corpo.php` e 12 `func_*.php`: `corpo.php`, `func_avaliacaogruporespostacat.php`, `func_avaliacaogruporespostamonitoramentosaude.php`, `func_avaliacaogruporespostaobras.php`, `func_avaliacaogruporespostaprocesso.php`, `func_desligamentoservidor.php`, `func_desligamentotrabalhadorsemvinculo.php`, `func_fonterecurso.php`, `func_orctiporec.php`, `func_rhdepend.php`, `func_rhlotacaotributaria.php`, `func_rhpessoaladmiss.php`, `func_rhrubricas.php`;
- 121 DAOs `classes/db_*_classe.php`.

### P2 — mudança da DBSeller e da 84 convivem: 3 vias limpa (71)

29 fora de `classes/db_*_classe`: `emp2_emitenotaemp002.php`, `forms/db_frmimplantacaoponto.php`, `forms/db_frmrhempemitesolfolha.php`, `forms/db_frmrhempexcluirsol.php`, `forms/db_frmrhempgerasolfolha.php`, `forms/db_frmrhpesdoc.php`, `fpdf151/fpdf.php`, `fpdf151/impcarne.php`, `fpdf151/pdf.php`, `func_bases.php`, `func_cgmjuridico.php`, `func_db_bancos.php`, `func_db_layouttxt.php`, `func_db_usuarios.php`, `func_grupomotivoafastamentoesocial.php`, `func_nome.php`, `func_operadorasaude.php`, `func_orcorgao.php`, `func_rhcargo.php`, `func_rhemissaochequeitem.php`, `func_rhlocaltrab.php`, `func_rhlota.php`, `func_rhlotaestrutinstit.php`, `func_rubricas.php`, `func_selecao.php`, `func_tipoasse.php`, `model/manad.model.php`, `src/Financeiro/Contabilidade/MatrizSaldoContabil/Repository/Lancamento.php`, `std/DBDate.php`; mais 42 DAOs.
Os de maior risco para a folha: `fpdf151/fpdf.php` e `fpdf151/pdf.php` (`Cell()`, `$align=='R'`), `std/DBDate.php`.

### P3 — conflito de 3 vias (1.004: 29 não-DAO + 975 DAOs)

Não-DAO: `buscaBasesClientes.RPC.php`, `classes/empenho.php`, `classes/estagioAvaliacoes.classe.php`, `dbforms/db_classesgenericas.php`, `dbforms/db_funcoes.php`, `dbforms/db_geraformulario.php`, `dbforms/db_layouttxt.php`, `forms/db_frmaturubricas.php`, `forms/db_frmpensao.php`, `forms/db_frmtipoasse.php`, `fpdf151/pdf1.php`, `fpdf151/pdf2.php`, `func_rhfuncao.php`, `libs/db_libcontabilidade.php`, `libs/db_liborcamento.php`, `libs/db_libparagrafo.php`, `libs/db_libparagrafoCodPhp.php`, `libs/db_libParagrafoTabela.php`, `libs/db_libparagrafoText.php`, `libs/db_libpessoal.php`, `libs/db_libpostgres.php`, `libs/db_libsys.php`, `libs/db_stdlib.php`, `libs/db_stdlibwebseller.php`, `libs/db_utils.php`, `libs/JSON.php`, `model/dbGeradorRelatorio.model.php`, `model/pontoFolha.model.php`, `std/DBString.php`.

Destaque: **`libs/db_libpessoal.php`**. A 84 mudou 9 linhas (`each()` em dois laços → `key/current/next`; `split` → `explode`;
**`db_val()`: `try { return $string+0; } catch (TypeError)` devolve 0**, ponto da folha). A 74 reformatou o arquivo inteiro
(+1.713/−1.681 linhas), então o merge conflita; os trechos precisam ser reaplicados à mão. Idem `libs/db_stdlib.php`
(84: +47/−36; 74: +1.083/−996) e `libs/db_utils.php`. Nos não-DAO **não** repeti a normalização de espaço.

#### Recontagem dos 975 DAOs ignorando espaço, quebra de linha e equivalências triviais

Normalização aplicada aos três lados (base, 74, 84) antes do `git merge-file`, em três níveis cumulativos:

| Nível | Normalização | DAOs sem conflito | Conflito restante |
|---|---|---:|---:|
| 0 | nenhuma (`merge-file` cru) | 0 | 975 |
| 1 | só espaço no fim da linha, CRLF e `<?` → `<?php` | 10 | 965 |
| 2 | + todo espaço dentro/ao redor das linhas (≈ `git diff -w`) | 14 | 961 |
| 3 | + equivalências do 7.x: `public`/`private` antes de `function` (a 74 já escreveu `public function __construct()`), `preg_split("#X#m")` ≡ `explode("X")` para `X` literal | **890** | **85** |

**Sobram 85 DAOs com conflito de verdade (8,7%).** A causa dos 961 que o nível 2 não resolvia era a migração em duplicidade:
a DBSeller já renomeou o construtor (`function cl_x()` → `public function __construct()`) e converteu `split("#")` em `explode("#")`,
e a 84 fez o mesmo de outro jeito (`function __construct()`, `preg_split("#\\##m")`). Os 85 restantes misturam: (i) trechos com
`explode` de aspas simples × duplas e chaves em linhas diferentes (cosméticos, ainda não absorvidos pela normalização),
(ii) trechos de guarda `$this->X == ""` em que a DBSeller editou a mesma linha (aparecem na amostra, não recontei após o nível 3), e (iii) **mudança real da DBSeller** na `sql_query`
de alguns DAOs (vista nas amostras) (`order by {$ordem}` em vez do laço sobre `explode("#")` da base) — esta *não* é migração e deve ser preservada.
Ressalva: a normalização é heurística; "sem conflito" significa que o merge se aplica sem sobreposição, não que o resultado foi executado.

#### P1 + P3 separados por quem usa

Critério (heurístico, por nome da tabela): **RH** = `rh*`, `pes*`, `gerf*`, `ponto*`, `eso*`, `cfpess`, `assenta*`, `tipoasse*`, `afasta*`,
`inssirf`, `bases*`, `selecao*`, `cadferia`, `pensao*`, `previden*`, `relrub`, `rubricas*`, `vtf*`, `rescisao`, `portaria` e afins.
**Compartilhado-referenciado** = DAO que não é do RH mas que alguma tela/classe da área instancia direto (`cl_x` ou `getDao('x')`, 480
nomes referenciados nos 2.126 `.php` da área). **Compartilhado** = só entra pelo fecho do `enumera.py`. Não é o dono da tabela no banco:
é a decisão a levar ao coordenador. `rec*` não entrou como critério: os 8 DAOs `rec*` do universo são `rechumano*` (Educação) e `recibo*` (arrecadação).

| Grupo | Total | DAOs do RH | Compartilhados referenciados pela área | Compartilhados (só fecho) |
|---|---:|---:|---:|---:|
| P1 (só a 84 mudou) | 121 | 50 | 18 | 53 |
| P3 (conflito cru) | 975 | 221 | 101 | 653 |
| P3 — os 85 **conflitos reais** (nível 3) | 85 | 14 | 11 | 60 |
| **P1 + P3 (conflito cru)** | **1.096** | **271** | **119** | **706** |
| **P1 + os 85 reais** | **206** | **64** | **29** | **113** |

- DAOs do RH com conflito real (14): `pensaocontabancaria`, `pensaoretencao`, `portaria`, `rescisao`, `rhcontasrec`, `rhdirfgeracao`,
  `rhempenhofolhaempenho`, `rhpesdoc`, `rhpessoal`, `rhrubricasadiantamento`, `rhslipfolha`, `rhteutri`, `selecao`, `servidoroperadorasaudedependente`.
- Compartilhados referenciados pela área com conflito real (11): `admissao`, `assinatura`, `cgm`, `operadorasaude`, `orcdotacao`,
  `orcprojativ`, `orctiporec`, `orcunidade`, `protelac`, `protprocesso`, `relac`.
- DAOs do RH em P1 (50, só a 84 mudou): `afastaassenta`, `assenta`, `assentadb_cadattdinamicovalorgrupo`, `assentamentorra`,
  `assentamentosencerramentoefetividade`, `assentamentosubstituicao`, `folhafiltros`, `inssirf`, `rhcedencia`, `rhcontratoemergencialrenovacao`,
  `rhemitecontracheque`, `rhferiasassenta`, `rhferiasperiodoassentamento`, `rhfuncaooutrosdados`, `rhlocaltrabequipamentoprotecao`,
  `rhlocaltrabequipamentoprotecaoepi`, `rhlocaltrabregistroambiental`, `rhlotacaotributaria`, `rhlotavincrubrica`, `rhpescargo`, `rhpespadrao`,
  os 25 `rhpessoalprocesso*`/`rhprocesso*`, `rhreajusteparidade`, `rhsindicato`, `rubricasusuario`, `tipoasseexterno`.
- Compartilhados de P1 referenciados pela área (18): `avaliacaogruporesposta*` (8), `contribuicaosindical*` (2), `controleafastamento`,
  `db_cadattdinamicoatributosvalor`, `db_uf`, `db_usuarios`, `pcparam`, `siopequalificacao`, `siopesegmentoatuacao`, `siopesituacao`.

#### Arquivos de `model/pessoal/`

O universo do RH tem 48 arquivos em `model/pessoal/`; a 84 alterou 6:

| Arquivo | Situação | Pedido |
|---|---|---|
| `model/pessoal/std/DBPessoal.model.php` | **P1**: a 74 não tem a correção (`$F032 - $F031` com string vazia; cálculo da folha) | trazer a da 84 |
| `model/pessoal/folhapagamento/FolhaPagamento.model.php` | **P1** | trazer a da 84 |
| `model/pessoal/folhapagamento/FolhaPagamentoSalario.model.php` | **P1** | trazer a da 84 |
| `model/pessoal/folhapagamento/FolhaPagamentoSuplementar.model.php` | **P1** | trazer a da 84 |
| `model/pessoal/PontoFerias.model.php` | **P1** | trazer a da 84 |
| `model/pessoal/ReajustePadroes.php` | **P4**: a 74 já é equivalente | nada |

Nenhum de `model/pessoal/` está em P2 (limpo) nem P3 (conflito): são os 5 de aplicação direta. Também em `model/` e relevante à folha,
mas **fora** de `model/pessoal/`: `model/pontoFolha.model.php` (P3, conflito) e `model/manad.model.php` (P2, limpo).

### P4 — já equivalente na 74 (nada a pedir)

`libs/db_libgertxtfolha.php`, `model/pessoal/ReajustePadroes.php`.

### P5 — bloqueadores achados pela bateria do lote 1 (19/11/2026)

Medidos pela bateria; cada um derruba telas da área no 8.5 e **não foi alterado aqui**:

- `libs/JSON.php` (l. 188, `$utf16{0}`/`{1}`): derruba **37** `.RPC.php` de `eso*`/`rh*`;
- `fpdf151/fpdf.php` (l. 614, `$s{$i}`): derruba todo relatório PDF que o carrega (aqui, `eso3_qualificacaocadastral002.php`);
- `dbforms/db_funcoes.php` (`db_multiploselect`, l. 416 e 475; ainda 859, 927 e 984): `gettype() == "resource"` perde dado em silêncio no 8.5;
- (lote 1B) `fpdf151/fpdf.php:614` derruba 8 relatórios do ponto/DIRF e `libs/JSON.php:188` 9 RPC de `pes4`/`rec`; `func_tipoasse.php:36` (`parse_str` de 1 argumento, fora da área);
- (lote 2) `dbforms/db_funcoes.php` (`db_inputdata` l. 1096 perde o calendário; `db_select` l. 1023 perde o `selected` de `0`), `libs/db_utils.php:70` e `libs/db_stdlib.php:1929` (`pg_*` com resultado `false`), `classes/db_protelac_classe.php` (construtor PHP 4);
- `model/dbGeradorRelatorio.model.php` e `src/Financeiro/Contabilidade/MatrizSaldoContabil/Repository/Lancamento.php`: não compilam no 8.5 (`php -l`);
- DAOs de `classes/`: 864 das 876 classes com campos leem o formulário no 7.4 e mantêm `0` no 8.5 (caminho de escrita, passo 6b); 883 alvos do Rector do universo estão fora da área
  (865 `classes/`, 12 `func_*.php`: `func_avaliacaogruporespostacat`, `..monitoramentosaude`, `..obras`, `..processo`, `func_desligamentoservidor`,
  `func_desligamentotrabalhadorsemvinculo`, `func_grupomotivoafastamentoesocial`, `func_rhlota`, `func_rhlotacaotributaria`, `func_rhpessoaladmiss`, `func_selecao`, `func_tipoasse`;
  `model/dbGeradorRelatorio.model.php`, `FolhaPagamento.model.php`, `FolhaPagamentoSuplementar.model.php`; `pro2_despachointer002.php`).
  `db_cursoedu_classe.php` (Educação) declara `cl_curso` de novo: sai com código diferente nos dois runtimes (7.4: fatal; 8.5: `exit` 0).

Depois que o núcleo trouxer esses arquivos, rodar de novo a bateria das 39 telas (as 96 do lote menos as 57 do bloco `Lote 1 do RH` do `faseb_map.conf`, via `ONLY=`) e acrescentá-las ao `faseb_map.conf`.

### Observações

- `libs/db_calcula.php` foi alterado pelos dois, mas **não** está no universo do RH.
- Sem P1–P3, a bateria do lote mede o núcleo, não a tela. Sugestão: o núcleo trata P1 e os 29 não-DAO de P2/P3 antes do lote 2;
  os DAOs (42 limpos + 975, dos quais só 85 têm conflito real) são o maior volume: ver a divisão RH × compartilhado em P3.

## Lote 1 (rh + eso + 2 `.RPC.php`): resultado (19/11/2026)

Branch `pessoal/rh-php85`. Referência: 7.4 (`:8080`); runtime migrado: 8.5 (`:8085`). **O lote não alterou nenhum arquivo de código**:
as 96 telas já estavam sem as categorias do 8.5, e tudo o que falha vem de arquivo fora da área (núcleo).

| Passo | Resultado |
|---|---|
| 1-3 Enumerar (`enumera.py`, `TELAS=@lista`, 96 telas: 94 `(rh\|eso)[0-9]*_` + `esocial_externo.RPC.php` + `rhpessoalmov001.RPC.php`) | universo **2.701** arquivos; **883 a alterar, todos fora da área** (865 `classes/`, 12 `func_*`, 3 `model/`, 1 `src/Financeiro`, 1 `pro2`); **0 das 96 telas** tem `$this->X == literal`, `split`, `each`, `parse_str`, `ereg` ou construtor PHP 4 |
| 4 Rector (`rector-curado.php`, pin `PHP_80` conferido, config com `php -l` limpo) | dry-run sobre as 96: **0 arquivos**. Controle positivo (`func_rhlota.php`): 1 arquivo, `ParseStrComExtractRector`. **Não houve commit do Rector** (nada a commitar). 4b (portão de funções) n/a: sem diff |
| 5 `php -l` sobre o universo (2.701) | **7.4: 0 erros. 8.5: 6**, nenhum na área: `fpdf151/fpdf.php`, `libs/JSON.php`, `model/dbGeradorRelatorio.model.php` (2 caminhos do mesmo arquivo), `src/Financeiro/.../Lancamento.php`, `src/RecursosHumanos/.../Falta.php` (lote 1B) |
| 6 Instanciar classes (948 de `classes/`, `ic`) | 7.4: 951 linhas; 8.5: 949. Divergem **17 DAOs** (estado inicial): `arrenumcgm`, `concilia`, `conparametro`, `db_logsacessa`, `empnotasigfistipodocliquidacao`, `historicompsfora`, `liclicitem`, `liclicitemlote`, `matestoqueitemfabric`, `padroes`, `parissqn`, `pcproc`, `recibopaga`, `rhpesrescisao`, `taxa`, `empenho.php` + `db_cursoedu_classe.php` (declara `cl_curso` de novo: sai com fatal no 7.4 e com código 0 no 8.5). **Todos em `classes/`: dependem do núcleo** |
| 6b Caminho de escrita (`escrita.php`) | 876 classes com campos; **864 divergem**: o 7.4 lê o valor do formulário e o 8.5 mantém `0` (idioma `$this->X == ""`). **Todas são DAOs de `classes/`, não portados na 74 (P1/P3): dependem do núcleo.** Os 12 que não divergem não têm campo inteiro |
| 6c Forma negada `!=` | não rodado: nenhuma classe foi alterada no lote |
| 7 Bateria (`cmp.py`, 96 telas) | **57/96 idênticas, 39 divergentes, 0 timeout**. As 57 respondem 200 nos dois. Causa das 39: ver abaixo |
| 8 Roteamento | 57 telas acrescentadas a `docker/proxy/faseb_map.conf` (lista exata; `nginx -t` ok; proxy recriado; `X-Ecidade-Runtime` conferido). O `location` por prefixo **não foi tocado**. As 39 ficam no 7.4 |
| 8b Abas/redirecionamentos (`redirecionamentos.py`) | **não rodado** neste lote; fica para o fim da área |

### As 39 divergências: todas dependem do núcleo (nenhuma é defeito de arquivo da área)

| Qtd | Tela(s) | Causa | Arquivo do núcleo | A 84 |
|---:|---|---|---|---|
| 37 | `.RPC.php` de `eso*`/`rh*`, incl. `rhpessoalmov001.RPC.php` | `ParseError` em `libs/JSON.php:188` (`$utf16{0}`): 7.4 responde 200, 8.5 responde 500 de ~3,7 KB | `libs/JSON.php` | `$utf16[0]` |
| 1 | `eso3_qualificacaocadastral002.php` | `ParseError` em `fpdf151/fpdf.php:614` (`$cw[$s{$i}]`) | `fpdf151/fpdf.php` | `$cw[$s[$i]]` |
| 1 | `rh4_gerarempenhosfolha001.php` | 200 nos dois, 32 B de diferença: a opção `<option value='3'>INSS</option>` some do `<select>`. `db_multiploselect()` testa `gettype($rs) == "resource"` e no 8.5 o resultado do `pg_*` é objeto | `dbforms/db_funcoes.php` (l. 416 e 475) | `(gettype(...) == "resource" \|\| is_object(...))` |

Esse último é silencioso (a tela abre, perde uma opção): a mesma troca vale para `gettype($record) == "resource"` nas linhas 927, 984 e para
`is_resource` na 859 da 84.

### Ferramental: `cmp.py` falhava em silêncio no Windows (corrigido neste lote)

O `bash` que o Python acha no PATH do Windows é o do WSL, sem distribuição: toda requisição voltava vazia nos dois lados e a bateria
dizia **"96/96 idênticas" sem ter requisitado nada** (a primeira rodada deste lote caiu nisso; foi descartada). Correções em
`scratchpad/cmp.py`: variável `BASH_BIN` (caminho do Git Bash) e aborto quando o código volta `???`. Como rodar no Windows:
`BASH_BIN="$(cygpath -w /usr/bin/bash.exe)" MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf-8 python scratchpad/cmp.py ...` (usar `python`, não `python3`).
O cookie de sessão é `ECIDADEWINDOWMAIN=<SID>`, não `PHPSESSID`.
`scratchpad/runner_resumivel.sh` roda `instancia_classes.php`/`escrita.php` numa lista inteira, dentro do contêiner, e retoma depois de fatal ou
`exit` (marca a classe como `FATAL_RC<n>`/`SAIU_RC0`); substitui o `porclasse.sh` (um processo por classe levou ~65 min por passada).
O `/tmp` é compartilhado entre os contêineres: não rodar duas passadas ao mesmo tempo.

### Numeração dos commits

`git log --all`: o maior `PHP8-NN` é o **31** (`origin/migracao/parse-str-e-guardas-sql` e outras). O `PHP8-25` do commit de dimensionamento
**não colide** com nenhum outro (só ele usa o 25). Este lote usa o **`PHP8-32`**.

## Lote 1B (`src/RecursosHumanos`): resultado (20/11/2026)

Dois commits `PHP8-95`: Rector (6 arquivos) e à mão (`Falta.php` + registro). O lote não tem telas; a verificação é `php -l`, carga das
classes (LSP) e uma bateria dirigida às telas que chegam aos arquivos alterados. Medições reaproveitadas do lote 1 (arquivos fora da área já medidos)
e guardadas em `ecidade/tmp/medidas/` (gitignored) para os próximos lotes.

| Passo | Resultado |
|---|---|
| Enumerar (`TELAS=@lista`, 584 `.php`; o `README.md` de `Templates/` não é PHP) | universo 2.749 (2.610 únicos); 880 alvos, **0 dentro de `src/RecursosHumanos`**; 224 arquivos ainda não medidos no lote 1 (169 da área + 55 de fora) |
| 4 Rector (pin `PHP_80` conferido; blocos de 60: o modo paralelo estoura 120 s) | **7 arquivos**, 2ª e 3ª passadas = 0: `ConsistentImplode` (`Dirf.php:68`, `implode($array, 'union')` seria TypeError no 8.x), `OptionalParametersAfterRequired` (3 construtores: `Evento`, `HoraEvento`, `HoraTrabalhada`, mãe e filhas juntas), `ThisCallOnStaticMethodToStaticCall` (`EspelhoPonto`), `FinalPrivateToPrivateVisibility` (`Layout`), `ParenthesizeNestedTernary` (`Falta.php`) |
| Correção à mão | **`Falta.php`**: a saída do Rector deixava o ternário de 3 níveis associado à direita; o 7.4 associa à esquerda. Reescrito como na 84 (`((a ? x : b) ? y : c) ? z : ''`), com comentário. Bug da regra, não do código |
| 4b portão de funções | n/a: o diff só traz `implode` (existe no 7.4) |
| 5 `php -l` nos 224 não medidos | **0 erros no 7.4 e 0 no 8.5** (`Falta.php` agora compila) |
| LSP (`carrega_arquivo.php`, 218 arquivos com `extends`/`implements`, um por processo) | **218/218 `OK` nos dois runtimes** |
| 6/6b classes (23 de `classes/` novas no universo) | instanciar: 23 idênticas; escrita: 20 de 21 DAOs divergem (7.4 lê o POST, 8.5 mantém `0`): **depende do núcleo** (já registrado) |
| 6c forma negada | n/a: nenhuma classe de dados alterada |
| Bateria dirigida (40 telas da raiz que citam `PontoEletronico`, `Layout`, `Dirf`, `EspelhoPonto`) | **20 idênticas**, 19 divergentes, 1 timeout. Causas, todas fora de `src/RecursosHumanos`: `libs/JSON.php:188` (9), `fpdf151/fpdf.php:614` (8), `func_tipoasse.php:36` (`parse_str` de 1 argumento: `func_*`, fora da área), `rec4_pontoeletronicoimportacaoarquivo002.php:116` (`count(null)`: tela do lote rec) + `rec2_espelhoponto002.php` (timeout) e `pes1_rhpessoal005.php` (200/200, 436 B de diferença): ficam para os lotes rec e pes1 |
| 8 Roteamento | **nada a rotear**: o lote não tem telas. As 20 idênticas são de `eso`/`pes`/`rec`/`func`; entram quando o lote delas for portado (lista em `ecidade/tmp/medidas/cmp_dirigida_1B_identicas.txt`) |

Limite: as telas que de fato executam o `Falta.php`, o `Evento` e o `EspelhoPonto` (ponto eletrônico) respondem 500 no 8.5 por `libs/JSON.php`/`fpdf151/fpdf.php`;
o efeito das 7 alterações só fica comprovado por `php -l` e carga, não por execução. Reexecutar `rec2_espelhoponto*`/`rec4_pontoeletronico*` depois que o núcleo trouxer P5.

## Lote 2 (`rec`): resultado (20/11/2026)

Dois commits `PHP8-96`: Rector (4 arquivos) e à mão (63 arquivos da 84 + resolução dos 13 conflitos + roteamento + registro). Como os 76 arquivos que a 84
também alterou entram por 3 vias (`git merge-file`, base `e640eb485`, ours = 74, theirs = 84), o Rector do 1º commit só pegou os arquivos fora desse conjunto;
depois da mesclagem o Rector rodou de novo sobre os 76 (1 arquivo: `rec1_protelac002.php`, do trecho mantido da 74) e esse resultado está no 2º commit.

| Passo | Resultado |
|---|---|
| Enumerar (`rec`, 283 telas) | universo 2.924; 1.000 alvos, **58 na área, todos nos 76 arquivos vindos da 84**; os 942 restantes são de fora (`classes/` etc.); 436 arquivos ainda não medidos |
| Classificação (base × 74 × 84) | sem mudança 86; só 84 (a1) **13**; só 74 (b) 121; as duas (63): mesclagem limpa (a2) **50**, conflito **13**. Igual ao dimensionamento |
| 1º commit (Rector nos 207 arquivos fora do conjunto da 84) | 4 arquivos: `WrapVariableVariableNameInCurlyBraces` (2: `rec1_admissao002`, `rec1_leis_iframe001`), `ConsistentImplode` (2: `rec1_rhestagioresultado001/002`) |
| a1 (13) e a2 (50) | trazidos da 84 / mesclados sem conflito |
| 13 conflitos (decisão c2/c1: manter a 74, acrescentar só o que o 8.5 exige) | **todos ficaram com a versão da 74** nos trechos em conflito (`explode`, `parse_str($_SERVER['QUERY_STRING'], $query)`, reformatação, e a numeração `$mar1[1]`..`[9]` da DBSeller em `rec2_certcomprobatorio002`/`rec2_vantagens002`, que corrige o octal inválido `08`/`09` da base). Acrescentados à mão: `preg_split("#\|#m")` nas 2 linhas de separador `\|` (`rec1_leis001`/`002`, regra da decisão 2) e a guarda `($result ? pg_num_rows($result) : null)` em `rec2_relassentaporperiodo002` (a 84 a trouxe; sem ela `pg_num_rows(false)` é TypeError no 8.5, e o 7.4 só avisa e redireciona) |
| 4 Rector sobre os 76 depois da mesclagem | 1 arquivo (`rec1_protelac002`), 2ª passada = 0. **Alvos na área depois: 0** |
| 4b portão de funções (contra o 7.4) | 2 funções novas, **0 ausentes** |
| 5 `php -l` nos 436 não medidos | **0 erros no 7.4 e 0 no 8.5** |
| LSP (4 arquivos de `src/` novos com `extends`) | 4/4 `OK` nos dois |
| 6/6b classes (83 de `classes/`) | instanciar: 82 de 83 idênticas, `db_protelac_classe.php` difere; escrita: 65 de 68 divergem: **depende do núcleo** |
| 6c forma negada | n/a: nenhuma classe de dados alterada |
| 7 Bateria (`cmp.py`, 283 telas) | **213 idênticas, 69 divergentes, 1 timeout** (`rec2_espelhoponto002`, 500 no 8.5). Causas abaixo |
| 8 Roteamento | 213 telas no `faseb_map.conf` (bloco `Lote 2 do RH`); `nginx -t` ok; proxy recriado; cabeçalho conferido |

### As 70 que não são idênticas: todas dependem do núcleo

| Qtd | Sintoma | Arquivo do núcleo |
|---:|---|---|
| 30 | `ParseError` em `libs/JSON.php:188` (500 no 8.5, 200 no 7.4) | `libs/JSON.php` |
| 30 | `ParseError` em `fpdf151/fpdf.php:614` (relatórios PDF) | `fpdf151/fpdf.php` |
| 3 | `rec1_protelac001/002/003`: `label() on null` em `forms/db_frmprotelac.php:32`: o DAO `cl_protelac` não executa o construtor (PHP 4) | `classes/db_protelac_classe.php` |
| 2 | `rec3_rhestagioavaliacoes003`, `rec4_avaliacaocancelamento002`: `pg_num_fields(false)` | `libs/db_utils.php:70` |
| 1 | `rec2_rhestagioBoletim001`: `pg_fetch_result(false)` | `libs/db_stdlib.php:1929` |
| 3 | `rec1_rhestagioagenda004/005/006` (200/200): o bloco do calendário (`db_inputdata`) some | `dbforms/db_funcoes.php` (`db_inputdata`, l. 1096) |
| 1 | `rec2_rhestagio001` (200/200): `<option value="0" selected>` perde o `selected` (`db_select`, `0 == ""`) | `dbforms/db_funcoes.php` (`db_select`, l. 1023) |

Os `.RPC.php` e relatórios que só falham por JSON/fpdf contam como não verificados: a sua lógica de `rec` só fica comprovada por `php -l` e pelo merge com a 84,
até o núcleo trazer P5. Reexecutar as 70 depois (`ONLY=` com `ecidade/tmp/medidas/rec_naoidenticas.txt`, gitignored) e acrescentar ao `faseb_map.conf`.
Limite: a bateria faz só `GET`; o caminho de escrita das classes do `rec` não pôde ser comprovado porque os DAOs não estão portados (P1/P3).

## Lote 3 (`pes3` + `pes4`): resultado (22/11/2026)

Commit `PHP8-97` (único: a mesclagem com a 84 e o Rector convergido foram feitos na mesma árvore antes do commit, então não há commit separado só do Rector).
45 arquivos alterados (+148/−110): os 41 a1/a2 trazidos da 84 e os conflitos c1/c2 resolvidos pelo critério (manter a 74, acrescentar só o que o 8.5 exige).

| Passo | Resultado |
|---|---|
| Classificação | a1 6, a2 35, b 151, c1 4, c2 5, sem mudança 72 (igual ao dimensionamento) |
| 4 Rector (pin `PHP_80`, até zero) | convergido antes do commit |
| 4b portão de funções (contra o 7.4) | feito, sem função ausente |
| 5 `php -l` (7.4 e 8.5) | nos 45 alterados: **0 erros nos dois runtimes** (reconferido em 22/11/2026) |
| 6/6b classes | instanciação e escrita já feitas; DAOs de `classes/` seguem "depende do núcleo" |
| 7 Bateria (`cmp.py`) | **INCOMPLETA**: interrompida duas vezes por falta de memória da máquina; chegou até `pes3_relchequesemitidos002`. **Fica para a verificação final** |
| 8 Roteamento | **não feito** (o proxy não foi tocado; depende da bateria) |

## Lote 4 (`pes1`): resultado (22/11/2026)

Commit `PHP8-98` (único: mesclagem com a 84 e Rector na mesma árvore). 151 arquivos alterados (+431/−290). **Modo estático**: bateria não rodada (memória da máquina).
`pes1_reajusteprog001.php` **não foi alterado** (defeito da DBSeller, ver *Defeitos caracterizados*).

| Passo | Resultado |
|---|---|
| Classificação (base `e640eb485` × 74 × 84) | sem mudança 57; a1 **11**; a2 **129** (mesclagem limpa); b 159; conflito **14** (9 c1 + 5 c2). Igual ao dimensionamento |
| a1/a2 | a1 trazidos da 84; a2 por `git merge-file` (ours = 74); 140 arquivos |
| 14 conflitos | **todos com a versão da 74** nos trechos em conflito (`explode` literal; `parse_str` 2 argumentos; `js_tabulacaoforms` só de formatação; `db_postmemory($_POST)`), exceto `pes1_importainfla001.php` (ver DECISÕES A REVISAR) |
| 4 Rector (pin `PHP_80` conferido; 7 blocos de 60 sobre os 369 `.php` da área; repetido até zero) | 7 arquivos alterados pelo Rector, passada seguinte = 0 em todos os blocos. Sem ternário aninhado novo no diff |
| 4b portão de funções (contra o 7.4) | 9 funções novas no diff, 0 ausentes (`erro` é texto de comentário) |
| 5 `php -l` | 151 alterados: **0 erros no 7.4 e no 8.5**; universo ainda não medido (599 arquivos, 9 deles de `model\...` com barra invertida): **0 erros nos dois** |
| LSP (`carrega_arquivo.php`, 6 arquivos com `extends`/`implements` no universo novo) | 6/6 `OK` nos dois runtimes |
| Alvos do Rector dentro da área depois | 0 reais (o detector acusa `pes1_importainfla001` e `pes1_rhrubricas007` por casar com a própria correção/comentário) |
| 6/6b classes | **n/a**: nenhuma classe de dados alterada na área (só telas); os DAOs de `classes/` seguem "depende do núcleo" |
| 7 Bateria | **NÃO RODADA** (limite de memória). Pendente |
| 8 Roteamento | **não feito** |

## DECISÕES A REVISAR

Casos (c) resolvidos sem parar, pelo critério (manter a 74 + mínimo para o 8.5):

| Arquivo | Trecho | Decisão | Motivo |
|---|---|---|---|
| `pes1_importainfla001.php` | `split($separador, …)` com separador **digitado** (regex) | ficou a linha da **84** (`preg_split` com guarda que devolve `false` para `\|`); o `explode("/")` ao lado ficou o da 74 | não dá para provar que `$separador` é literal; `explode` mudaria o resultado se ele tiver metacaractere. Rever a origem de `$separador` |
| `pes1_relac002.php`, `pes1_rhteutri002/003.php` | `parse_str($_SERVER['QUERY_STRING'], $query)` da 74 × `parse_str(…,$__qs); extract($__qs)` da 84 | **74** | a DBSeller já passou para 2 argumentos; manter. Conferir se o restante da tela usa `$query`/`$queryString` ou variáveis extraídas |
| `pes1_rhcontasrec003.php` | `parse_str($_SERVER["QUERY_STRING"])` (1 argumento) + `db_postmemory($_POST)` | **74**; o Rector converteu o `parse_str` | a 84 usa `$HTTP_POST_VARS`; manter `$_POST` da 74 |
| `pes1_pontoRfx0011*.php`, `pes1_rhbases004`, `pes1_rhcadcalend002`, `pes1_rhempexcluirsol001`, `pes1_rhrubricas004/005`, `pes1_virafolha001/003` | `explode` (74) × `preg_split("#X#m")` (84) | **74** | separadores literais (`,` `-` `/` `_`): equivalentes |
| `pes2_admitidos002.php`, `pes2_rhteutri002.php`, `pes2_relfichafinanceiratxt002.php` | 3 + 2 + 1 trechos em que a 74 **reescreveu o relatório** (exporta CSV, remove blocos e o `$pdf->Output()` final) | **74** | funcionalidade da DBSeller; o que a 84 alterou nesses trechos não existe mais na 74 |
| `pes2_relcad001.php` | `break` fora de laço: 74 `return false;` × 84 `exit;` (6 trechos) | **74** | compila e roda no 8.5; **mudança de comportamento da DBSeller em relação ao 5.6** (o `return false` encerra só o include), não exigida pelo 8.5. Rever se o relatório deve parar |
| `pes2_relcad001.php` | `$$variavelteste` (74) × `${$variavelteste}` (84) | **74** | variável variável simples, mesma semântica; `explode("#")` literal |
| `pes2_analitica002`, `pes2_func_e_depend002`, `pes2_pensalim002`, `pes2_relfichafinanceira002`, `pes2_resumorecursoempenhos002`, `pes2_rhteutri002`, `pes2_termorescisao002` | `pg_num_rows($res)` (74) × `($res ? pg_num_rows($res) : null)` (84) | **74 + guarda da 84** só nessa chamada | `pg_num_rows(false)` é TypeError no 8.5 e o 7.4 só avisa e segue (`null == 0`): a guarda preserva o comportamento. Mensagens e textos da 74 mantidos (a 84 trocou acentos) |
| `pes2_sapestagioprob002.php` | `db_formatar($datai,'d')` (74) × `db_formatar($datai, null)` (84) | **74** | a 84 mudou o argumento, o que muda a saída; não é exigência do 8.5 |
| `pes2_admitidos002`, `pes2_func_e_depend002`, `pes2_rhteutri002`, `pes2_termorescisao002`, `pes2_relfichafinanceira002` | `parse_str($_SERVER[...], $query)`/`db_postmemory($_POST)` (74) × `$HTTP_SERVER_VARS`/`extract` (84) | **74** (o Rector converte o `parse_str` de 1 argumento) | conferir se a tela usa `$query` ou variáveis extraídas |

## Lote 5 (`pes2`): resultado (22/11/2026)

Commit `PHP8-99` (único). 238 arquivos alterados (+856/−638). **Modo estático**: bateria não rodada (memória da máquina).

| Passo | Resultado |
|---|---|
| Classificação (base `e640eb485` × 74 × 84) | sem mudança 20; a1 **10**; a2 **183**; b 269; conflito **42** (29 c1 + 13 c2). Igual ao dimensionamento |
| a1/a2 | a1 trazidos da 84; a2 por `git merge-file` (ours = 74) |
| 42 conflitos (111 trechos) | 55 trechos só de `explode` (74) × `preg_split("#X#m")` (84) com separador literal e 2 só de formatação: **74**. Os 54 restantes lidos um a um: ver DECISÕES A REVISAR |
| 4 Rector (pin `PHP_80`; 9 blocos de 60 sobre os 523 `.php`; até zero) | 12 arquivos alterados pelo Rector em 6 blocos; passada seguinte = 0 em todos. Nenhum ternário aninhado novo no diff |
| 4b portão de funções (contra o 7.4) | 3 nomes novos no diff, 0 ausentes (`catch` é palavra reservada) |
| 5 `php -l` | 238 alterados: **0 erros no 7.4 e no 8.5**; universo não medido (589 arquivos): **0 erros nos dois** |
| LSP (4 arquivos com `extends`/`implements`) | `fpdf151/pdf1.php` e `fpdf151/pdf2.php` falham **igual nos dois** (carregados fora do contexto: `redirect()` em null; `db_debug_backtrace()` redeclarada); os outros 2 `OK` |
| Alvos do Rector dentro da área depois | 0 |
| 6/6b classes | **n/a**: nenhuma classe de dados alterada (só telas) |
| 7 Bateria | **NÃO RODADA** (limite de memória). Pendente |
| 8 Roteamento | **não feito** |

## PROGRESSO

| Lote | Escopo | Estado | Commit | Observações |
|---|---|---|---|---|
| 0 | Dimensionamento, decisões (c), conferência do c1, recontagem dos DAOs | **feito** (18/11/2026) | este commit | só documentação |
| 1 | `rh` + `eso` + 2 `.RPC.php` | **feito** (19/11/2026) | `PHP8-32` (a mão; o Rector não alterou nada) | 96 telas, 0 alterações de código na área; bateria **57/96 idênticas**, 39 dependem do núcleo; 57 roteadas no `faseb_map.conf`. Ver *Lote 1: resultado* |
| 1B | `src/RecursosHumanos` (aprovado) | **feito** (20/11/2026) | `PHP8-95` (Rector + à mão) | 584 `.php`; Rector em 7 arquivos; `Falta.php` compila; LSP 218/218. Ver *Lote 1B: resultado* |
| 2 | `rec` | **feito** (20/11/2026) | `PHP8-96` (Rector + à mão) | 283 telas; 63 trazidas da 84 + 13 conflitos resolvidos; bateria **213/283 idênticas**, 70 dependem do núcleo; 213 roteadas. Ver *Lote 2 (rec): resultado* |
| 3 | `pes3` + `pes4` | **feito, modo estático** (22/11/2026) | `PHP8-97` | 45 arquivos; `php -l` 0 erros nos dois; **bateria incompleta** (memória; até `pes3_relchequesemitidos002`); sem roteamento |
| 4 | `pes1` | **feito, modo estático** (22/11/2026) | `PHP8-98` | 151 arquivos; `php -l` 0 erros nos dois; **bateria não rodada** (memória); sem roteamento; `pes1_reajusteprog001.php` intacto (não compila: reportar) |
| 5 | `pes2` | **feito, modo estático** (22/11/2026) | `PHP8-99` | 238 arquivos; `php -l` 0 erros nos dois; **bateria não rodada** (memória); sem roteamento |
| Pedidos ao núcleo (P1–P3) | fora da área | pendente | — | aguardam o dono do núcleo |
| Bateria completa (7.4 × 8.5) | área toda | pendente | — | ambiente do 7.4 ainda não está de pé |

## PENDENTE PARA ANTES DO MERGE

Esta branch (`pessoal/rh-php85`) entrega os lotes 1, 1B, 2, 3, 4 e 5 da área RH. Os três últimos (`pes3`+`pes4`, `pes1`, `pes2`) foram feitos em **modo estático** por limite de memória da máquina: **nenhuma bateria de telas rodou neles**.

1. **Bateria de `pes3` + `pes4`** (parcial): a rodada foi interrompida duas vezes por memória e chegou só até `pes3_relchequesemitidos002`. Rodar o restante (`cmp.py`, `ONLY=` com `ecidade/tmp/medidas/p34_restantes.txt`) e então rotear no `faseb_map.conf` as idênticas.
2. **Bateria de `pes1`** (369 telas): não rodada. Não há roteamento.
3. **Bateria de `pes2`** (523 telas): não rodada. Não há roteamento.
4. **Bateria completa da área** (7.4 × 8.5, todos os prefixos do RH) depois do item 1–3, e só com o núcleo (P1–P5) já trazido: sem ele a bateria mede o núcleo, não a tela.
5. **Cenário de cálculo da folha** (6 tipos de folha), 7.4 × 8.5, conferindo valor a valor. **Não fazer merge antes dessa verificação.**
6. **Levantamento de abas e redirecionamentos (passo 8b)**: `redirecionamentos.py` não foi rodado em nenhum lote da área. Precisa do 7.4 de pé e de uma sessão autenticada.
7. **Pedidos ao núcleo** (P1–P5, acima): nenhum atendido. Sem `libs/JSON.php`, `fpdf151/fpdf.php`, `dbforms/db_funcoes.php`, `libs/db_utils.php`, `libs/db_stdlib.php` e os DAOs de `classes/`, as telas que dependem deles falham no 8.5.
8. **Roteamento**: o proxy (`faseb_map.conf`) só tem as telas idênticas dos lotes 1 e 2 (57 + 213). `pes1`, `pes2` e `pes3`/`pes4` ainda não entraram.
9. **Revisar** a seção DECISÕES A REVISAR (casos (c) resolvidos sem consulta, em especial `pes1_importainfla001.php` e `pes2_relcad001.php`).
10. **Reportar à DBSeller**: `pes1_reajusteprog001.php` não compila em PHP algum (`Unmatched '}'`, linha 132); fica intacto.
