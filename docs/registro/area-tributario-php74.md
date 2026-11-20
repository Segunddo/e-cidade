# Área Tributário — migração do PHP 7.4 (PR #8) para o 8.5

Branch `tributario/8.5`, criada da `migracao/parse-str-e-guardas-sql` (que já traz o `parse_str` de 1 argumento
convertido em todas as áreas e as guardas `pg_*` dos wrappers do núcleo). Referência: PHP 7.4 do PR, porta 8080.
O histórico da migração anterior, feita sobre o código antigo, continua em `area-tributario.md`.

## 1. Escopo

Os 14 prefixos que o menu do sistema põe na área Tributário e que não são de outra área:
`cad`, `iss`, `fis`, `arr`, `div`, `itb`/`itbi`, `cem`, `jur`, `mar`, `not`, `dvr`, `tri`, `inf`, `agu`/`agua`.
Telas avulsas de `cai`, `pro`, `con`, `pre`, `prot`, `amb`, `rec` e `sys` que também aparecem no menu do
Tributário ficam com as áreas donas desses prefixos.

**Posse dos arquivos fora dos prefixos** (classes, formulários, models), para mexer só no que é da área:
- classes de dados: pelas tabelas dos módulos do dicionário (`db_sysarqmod`) `agua`, `arrecadacao`, `cadastro`,
  `cemiterio`, `diversos`, `divida`, `fiscal`, `inflatores`, `issqn`, `itbi`, `juridico`, `marcas`,
  `notificacoes` e `tributario`, descartando tabela que também esteja em módulo de outra área — o mesmo critério
  usado no Financeiro;
- demais arquivos: só os citados exclusivamente por telas dos 14 prefixos (janelas `func_*` e arquivos sem prefixo
  de módulo, como `reciboitbi*.php`, contam como neutros);
- ficam de fora as 35 classes já concluídas pelo Financeiro (`arre*`, `tabrec*`, `notificacao`), que o
  Tributário também usa.

## 2. Linha de base (19/11/2026)

`php -l` nos 2.807 arquivos dos prefixos: 1 não compila (`fis1_fis_vistorias003.php`), **igual no 7.4** —
defeito pré-existente, não é migração.

Bateria GET 7.4 × 8.5 (`scratchpad/cmp.py`, sessão autenticada), 2.805 telas: **2.234 idênticas, 571 divergentes**.

| Prefixo | Telas | Divergentes | | Prefixo | Telas | Divergentes |
|---|---|---|---|---|---|---|
| `cem` | 117 | 8 | | `div` | 148 | 38 |
| `itb`/`itbi` | 123 | 34 | | `arr` | 166 | 47 |
| `mar` | 35 | 4 | | `agu`/`agua` | 224 | 51 |
| `not` | 14 | 4 | | `iss` | 400 | 93 |
| `tri` | 35 | 9 | | `fis` | 792 | 106 |
| `inf` | 30 | 7 | | `cad` | 540 | 123 |
| `dvr` | 33 | 14 | | `jur` | 148 | 33 |

Causa da primeira quebra de cada divergente, lida no `extension/log/error.log` ao abrir a tela no 8.5:

| Causa | Telas | Onde |
|---|---|---|
| `ParseError` — offset de string com chaves (`$s{i}`, removido no 8.0) | **248** | `fpdf151/fpdf.php:614` (núcleo): todo relatório em PDF |
| o mesmo | **130** | `libs/JSON.php:188` (núcleo): todo RPC que usa o JSON antigo |
| `Call to a member function label() on null` — construtor estilo PHP 4 que não roda no 8 | ~70 | classes da área |
| `pg_*(): ... false given` — consulta que falhou | ~40 | telas e formulários da área |
| avulsas: assinatura incompatível com a mãe, `reset(null)`, `sizeof(null)`, `array_key_exists` em objeto, `DBLargeObject` | ~20 | área e núcleo |
| sem erro fatal (diferença de saída) | 23 | caso a caso |

**378 das 571 divergências (66%) dependem só de dois arquivos do núcleo**, que não são desta frente.

## 3. Lotes

Do menor para o maior, um por vez:

| Lote | Prefixos | Telas | Divergentes na linha de base |
|---|---|---|---|
| 1 | `cem`, `itb`/`itbi`, `mar`, `not`, `tri`, `inf`, `dvr` | 387 | 80 |
| 2 | `jur`, `div`, `arr` | 462 | 118 |
| 3 | `agu`/`agua` | 224 | 51 |
| 4 | `iss` | 400 | 93 |
| 5 | `fis` | 792 | 106 |
| 6 | `cad` | 540 | 123 |

## 4. Lote 1 — `cem`, `itb`/`itbi`, `mar`, `not`, `tri`, `inf`, `dvr` (20/11/2026)

| Commit | O quê | Prova |
|---|---|---|
| construtores (manual) | `__construct` em 15 classes: `cl_diverimporta`, `cl_isencao`, `cl_isencaotipo`, `cl_isscalc`, `cl_itbialt`, `cl_itbiconstr`, `cl_itbidadosimovel`, `cl_itbinome`, `cl_itbinomecgm`, `cl_itbiruralcaract`, `cl_itburbano`, `cl_itenserv`, `cl_parissqn`, `cl_parreciboitbi`, `cl_setorloc`. Só a linha da declaração; nenhuma filha nem chamada ao nome antigo na base | estado inicial das 15 (instanciação): antes 7.4 ≠ 8.5; depois 8.5 = 7.4 e 7.4 = 7.4 |
| `0 == ""` (Rector, automático) | regra do grupo `GuardaComparacaoLiteralRector`, sozinha, PHP 8.0 fixado, em 104 classes (tabelas dos módulos do lote 1); 559 linhas, só inserção | caminho de escrita (`atualizacampos` com POST): antes 104 classes ≠; depois 1 |
| construtor de `cl_diversos` (manual) | a 1 que restou; tabela do módulo Diversos, usada também pelo Caixa, não tocada pelo Financeiro | escrita: 104/104 iguais; 7.4 = 7.4 |
| `pg_*` (script, automático) | `($rs ? pg_x($rs) : null)` em `itb2_relresumoitbi002`, `itb4_consultacancelamento001`, `tri4_carregadadosisencao` (decisão 2a) | resposta do 7.4 igual antes/depois; 3/3 idênticas |

`php -l` nos dois runtimes em todo arquivo alterado: 0 erros. Nenhum byte ISO-8859-1 alterado.

**Resultado:** bateria do lote **307/387 → 346/387** idênticas. As **41** que divergem dependem só do núcleo:
- 40: `fpdf151/fpdf.php` e `libs/JSON.php` (offset com chaves);
- 1: `cem2_emitecertisen002.php` — os dois runtimes terminam em "Falha ao gerar relatório", mas o 7.4 imprime
  antes `<b>Mensagem: </b><br>`: a mensagem vem de `dbagata/classes/util/Dialog.class`, cujo construtor
  `Dialog()` é estilo PHP 4 e não roda no 8.5. O `dbagata/` tem 128 classes com construtor estilo PHP 4.

## 4b. Lote 2 — `jur`, `div`, `arr` (20/11/2026)

| Commit | O quê | Prova |
|---|---|---|
| construtores (manual) | `__construct` em `cl_divida`, `cl_parjuridico`, `cl_taxa`, `cl_termoanu`, `cl_termoreparc`; sem filha nem chamada ao nome antigo | instanciação: antes 5 ≠; depois 8.5 = 7.4 e 7.4 = 7.4 |
| `0 == ""` (Rector, automático) | mesma regra e config do lote 1 em 140 classes (tabelas dos módulos juridico, divida e arrecadacao; 200 tabelas, 169 classes não tratadas antes); 911 linhas, só inserção | caminho de escrita: antes 140 classes ≠ (1.240 linhas); depois 0 |
| `pg_*` (script, automático) | `arr2_exercproced001`, `arr2_gerardiscorelatorioconsolidado001`, `div2_exercproced001`, `div2_resumogeraldivida001`, `jur1_emiteinicial011` (10 chamadas) | 7.4 igual antes/depois; 5/5 idênticas |
| `sizeof()` de não contável (manual) | `jur2_trocapropriiframe`: `sizeof($matriz1/2)` → `sizeof((array)...)` nas 8 chamadas; no 7.4 os dois dão o mesmo para null, "", 0, texto e arrays | 7.4 igual antes/depois; idêntica |

`split()` em `db_divida_classe` e `db_termoinscrreg_classe` mantido: a função de compatibilidade existe nos dois
runtimes (regra do grupo).

**Resultado:** bateria do lote **344/462 → 360/462**. As **102** restantes dependem só do núcleo: 100 de
`fpdf151/fpdf.php` e `libs/JSON.php`; `arr3_condeclquitacaoanual002` (o `Dialog` do Agata, como no lote 1); e
`div4_alteracda001`, em que a opção "Selecione" (chave 0) sai marcada só no 7.4 — `db_select()` em
`dbforms/db_funcoes.php:761` compara `@$GLOBALS[$nome] == $chave` e a tela inicia a variável com `""`
(`"" == 0`: verdadeiro no 7.4, falso no 8).

## 4c. Lote 3 — `agu`/`agua` (20/11/2026)

Sem construtor estilo PHP 4, `each()` nem offset com chaves nos arquivos da Água.

| Commit | O quê | Prova |
|---|---|---|
| `0 == ""` (Rector, automático) | 58 classes (tabelas do módulo agua; 60 tabelas, 59 classes); 387 linhas, só inserção | caminho de escrita: antes 54 classes ≠ (528 linhas); depois 0 |
| `pg_*` (script, automático) | `forms/db_frmaguacortematnumpre.php` (formulário das 3 telas `agu1_aguacortematnumpre00x`) e `agu4_emissaoparcial_cliente59_001.php` | 7.4 igual antes/depois; 4/4 idênticas |
| laço de exercícios (manual) | `agu2_agualancpago001` e `agu2_relreceitabairro001` com `aguacalc` vazia: os anos chegam como `""`, e depois do `$i--` o 8 compara `-1 >= ""` como texto (verdadeiro): laço infinito. Na condição do `for`, só número × texto não numérico volta a converter o texto em número, como no 7.4 | caracterizado em 196 pares: corrigida no 7.4 e no 8.5 = original no 7.4; 2/2 idênticas |

**Resultado:** bateria do lote **173/224 → 179/224**. As 45 restantes: 43 dependem só do núcleo (`fpdf151/fpdf.php`,
`libs/JSON.php`) e 2 não são telas — `agu1_aguaconsumo999.php` (fragmento incluído por `agu1_aguaconsumo001/002/003`)
e `agu4_cancelaleituras_classe.php` (classe incluída por `agu4_expdadoscoletores_003`). Abertos sozinhos, falham nos dois
runtimes de jeitos diferentes (sem conexão / sem sessão); as 4 telas que os incluem são idênticas.

## 4d. Lote 4 — `iss` (20/11/2026)

| Commit | O quê | Prova |
|---|---|---|
| construtores (manual) | `__construct` em `cl_isscadsimples`, `cl_issconfiguracaogruposervico`, `cl_meiimporta` | instanciação: antes 3 ≠; depois 8.5 = 7.4 e 7.4 = 7.4 |
| `0 == ""` (Rector, automático) | 144 classes (tabelas do módulo issqn; 190 tabelas, 159 classes não tratadas antes); 844 linhas, só inserção | caminho de escrita: antes 144 classes ≠ (1.046 linhas); depois 0 |
| `pg_*` (script, automático) | 10 arquivos (`forms/db_frmissnotaavulsaservico.php` e 9 telas), 29 chamadas | 7.4 igual antes/depois nas 12 telas; 12/12 idênticas |
| objeto criado antes da atribuição (manual) | `iss1_tabalvara_depto001:43` e `iss4_issbasecaracteristicas001:125`: `$x->p = v` sobre variável inexistente criava `stdClass` no 7.4 e é `Error` no 8. Na mesma linha, `if (!isset($x) \|\| $x === false \|\| $x === '') { $x = new stdClass(); }` (condicional: com dados, `$oGrupo` é o último grupo do laço) | caracterizado (nulo, false, "", objeto): corrigida no 7.4 e no 8.5 = original no 7.4; 2/2 idênticas |

As telas `iss4_meicompetenciasemmovimento001/003` e `iss1_parissqn` passaram com os construtores dos lotes 1 e 4.

**Resultado:** bateria do lote **307/400 → 328/400**. As **72** restantes dependem só do núcleo: 66 de
`fpdf151/fpdf.php` e `libs/JSON.php`; 4 do Agata (`iss1_inscr002` gera PDF no 7.4 e nada no 8.5;
`iss2_relatorioinscricoes002`, `iss2_relinconsistenciassimples` e `iss4_relinconsistenciassimples` mostram a
mensagem do `Dialog` só no 7.4); 2 de `db_select()` com lista nula (`iss2_calculadoepago001`, `iss2_issqnpago001`).

**Ressalva do quadro:** `iss4_siss002.php` ficou marcada como concluída por engano: a bateria do grupo a pula de
propósito (contata o servidor externo do SISS) e ela não foi comparada. O quadro não tem operação para desmarcar e não
deve ser editado à mão; quem for testá-la, com dublê local do serviço, deve conferir antes de confiar na marca.

## 4e. Lote 5 — `fis` (20/11/2026)

| Commit | O quê | Prova |
|---|---|---|
| construtor (manual) | `__construct` em `cl_vistorias` | instanciação: antes ≠; depois 8.5 = 7.4 e 7.4 = 7.4 |
| assinaturas (manual) | `cl_fis_procfiscal_estendida` não carregava no 8: `incluir($y100_sequencial)` → `= null` (os dois chamadores passam `null`) e `sql_query` com um parâmetro a menos que a mãe → `$dbwhere = ""` sem uso no corpo (precedente do Financeiro) | a classe carrega no 8.5 com o estado do 7.4; 4/5 telas idênticas (a 5ª mostrou a camada seguinte) |
| `0 == ""` (Rector, automático) | 121 classes (tabelas do módulo fiscal; 126 tabelas); 643 linhas, só inserção | caminho de escrita: antes 121 classes ≠ (702 linhas); depois 0 |
| `pg_*` (script, automático) | 26 arquivos (15 telas, 11 formulários), 65 chamadas; depois mais 3 em `forms/db_frm_fis_levvalor.php` (camada seguinte) | 7.4 igual antes/depois nas 36 telas; 36/36 idênticas |
| aritmética com texto vazio (manual) | `(int)$x` em `fis1_fis_deflacionar001:33` e no `$i<$fim+1` de `forms/db_frm_fis_levvalor.php` (2 laços) e `forms/db_frmlevvalor.php` — precedente do Financeiro | caracterizado com 7 valores: igual ao 7.4 nos dois |
| `substr()` e divisão (manual) | `fis1_fis_deflacionar001`: `substr($data, 6, 10)` de data vazia é `false` no 7.4 e `""` no 8 (muda `0 == false` x `0 == ""` e o laço dos meses passava a rodar) → `(strlen((string)$x) < N ? false : substr(...))`, forma do catálogo, só nas 4 linhas; `$v / $cValor` com `$cValor` `""` → a forma da `DivisaoComoNo74Rector`, escrita à mão (o Rector também apagava espaços de linhas em branco) | `substr` com 10 entradas e divisão com 6 pares: iguais ao 7.4 nos dois; tela idêntica |

`split()` em 12 arquivos do Fiscal mantido (função de compatibilidade nos dois runtimes).

**Resultado:** bateria do lote **686/792 → 727/792**. As **65** restantes:
- 54 de `fpdf151/fpdf.php` e `libs/JSON.php`;
- 6 telas de AIDOF (`fis1_aidof002/003`, `fis1_fis_aidof002/003`, `fis4_aidof005`, `fis4_fis_aidof005`): o campo de descrição
  do tipo de nota some no 8.5 porque `db_selectrecord()` (`dbforms/db_funcoes.php:859`) testa `is_resource($record)`, falso
  para o objeto `PgSql\Result` do 8 — núcleo;
- 1, `fis1_fis_procfiscalfinalizacao002`: a tela liga `display_errors` e `error_reporting(-1)` (linhas 2–4) e mostra os
  `Deprecated` do 8.1+ que o núcleo emite (`pg_query()`/`pg_escape_string()` sem a conexão em `libs/db_stdlib.php:100` e
  `libs/db_libsession.php:63`) — núcleo;
- 2, `fis4_importalevan001` e `fis4_fis_importalevan001`: construtor estilo PHP 4 de `cl_cadtipo` (módulo caixa), já
  corrigido na branch do Financeiro, ainda não integrada a esta base;
- 2, `fis1_sanitario004` e `fis1_fis_sanitario004`: respondem 500 **no 7.4** — defeito da referência, não corrigido.

## 4f. Lote 6 — `cad` (20/11/2026)

| Commit | O quê | Prova |
|---|---|---|
| construtores (manual) | `__construct` em 12 classes: `cl_averbacao`, `cl_averbacgm`, `cl_averbacgmold`, `cl_condominio`, `cl_condominiocgm`, `cl_iptutaxacalvold`, `cl_iptutaxanumpold`, `cl_promitente`, `cl_propri`, `cl_ruasbairro`, `cl_ruascep`, `cl_tesinteroutros` | instanciação: antes 12 ≠; depois 8.5 = 7.4 e 7.4 = 7.4 |
| `0 == ""` (Rector, automático) | 151 classes (tabelas do módulo cadastro; 179 tabelas, 164 classes não tratadas antes); 951 linhas, só inserção. `cl_ruastipo` ficou de fora pela própria regra (propriedades sem padrão inteiro) e já era igual | caminho de escrita: antes 167 ≠ (1.225 linhas); depois só `cl_iptuconstr`, que no harness sem conexão consulta o banco (no 7.4 `pg_query()` sem conexão avisa, no 8.5 é `Error`) — artefato; as telas que a usam são idênticas |
| `pg_*` (script, automático) | 10 telas, 57 chamadas | 7.4 igual antes/depois; 9/10 idênticas |
| `pg_fetch_object(db_query(...))` aninhado (manual) | `cad4_calciptu:703`: resultado numa variável nova e a mesma guarda | 7.4 igual; idêntica |
| forma negada (manual) | `cad4_constr002:212`: `if($num!="")` com `$num` inteiro → `($num!="" && $num !== 0 && $num !== 0.0)` (idioma do catálogo) | caracterizado com 7 valores: igual ao 7.4 nos dois; idêntica |

`split()` mantido (função de compatibilidade nos dois). O inventário apontou "offset com chaves" em 6 arquivos
(`cad4_geracarneiptutxt*.php`, `src/Tributario/Cadastro/Iptu/EmissaoTXT.php`): falso positivo, é interpolação
`"$x{$y}"` dentro de texto; o `php -l` passa nos dois.

**Resultado:** bateria do lote **417/540 → 456/540**. As **84** restantes:
- 76 de `fpdf151/fpdf.php` e `libs/JSON.php`;
- `cad1_aba1ruas002` e `cad1_ruas003`: `forms/db_frmruas.php:160` chama `db_inputdata()` com os argumentos deslocados
  (defeito pré-existente, igual nos dois: `'text'` cai em `$db_opcao`); dentro do núcleo, `$db_opcao < 3` com `'text'`
  é verdadeiro no 7.4 e falso no 8, e o script do calendário só sai no 7.4 — núcleo;
- `cad1_lote002` e `cad1_lote003`: `db_select('j54_ponto', ...)` com chave `'0'` e chaves de texto — comparação `==` do
  núcleo;
- `cad2_iptulancpago001`: `db_multiploselect()` testa `gettype($rs) == "resource"` (`dbforms/db_funcoes.php:416`),
  `"object"` no 8 — núcleo;
- `cad4_certidaoexistencia003`: `std/DBLargeObject.php:101`, `pg_lo_export()` na ordem antiga de argumentos — núcleo;
- `cad1_reliptuender002` e `cad2_emissaobic_002`: respondem 500 **no 7.4** — defeito da referência, não corrigido.

## 4g. Bateria completa do fim da área (20/11/2026)

Os 14 prefixos de novo, depois dos 6 lotes: **2.396 de 2.805 telas idênticas** (linha de base: 2.234). O conjunto das 409
divergentes é **exatamente** o das baterias finais de cada lote — nenhum lote regrediu outro.

| Prefixo | Linha de base | Fim | | Prefixo | Linha de base | Fim |
|---|---|---|---|---|---|---|
| `cem` | 109/117 | 112/117 | | `div` | 110/148 | 119/148 |
| `itb`/`itbi` | 89/123 | 114/123 | | `arr` | 119/166 | 123/166 |
| `mar` | 31/35 | 31/35 | | `agu`/`agua` | 173/224 | 179/224 |
| `not` | 10/14 | 10/14 | | `iss` | 307/400 | 328/400 |
| `tri` | 26/35 | 32/35 | | `fis` | 686/792 | 727/792 |
| `inf` | 23/30 | 23/30 | | `cad` | 417/540 | 456/540 |
| `dvr` | 19/33 | 24/33 | | `jur` | 115/148 | 118/148 |

Das 409 que divergem: **379 dependem só de `fpdf151/fpdf.php` e `libs/JSON.php`**; as outras 30 são as pendências da seção 5
(núcleo e `cl_cadtipo` do Financeiro), 6 telas que já quebram no 7.4 e 2 arquivos que não são tela (lote 3).

Uma única divergente não estava na linha de base: `fis2_emiteaidof002.php`. Conferido voltando o código ao ponto de
partida (antes de qualquer commit desta frente): lá ela já diverge igual (7.4 gera o PDF, 8.5 quebra no
`fpdf151/fpdf.php`). Não é regressão; a medição da linha de base dessa tela foi instável.

## 5. Pendências do núcleo (avisar o dono)

| Arquivo | Defeito no 8.5 | Telas do Tributário afetadas |
|---|---|---|
| `fpdf151/fpdf.php:614` | `ParseError`: offset de string com chaves | 248 (todos os relatórios em PDF) |
| `libs/JSON.php:188` | o mesmo | 130 (RPCs) |
| `dbagata/` (128 classes) | construtor estilo PHP 4 não roda | relatórios do Agata (1 no lote 1, 1 no lote 2, 4 no lote 4) |
| `dbforms/db_funcoes.php:761` (`db_select`) | `@$GLOBALS[$nome] == $chave` com variável `""` e chave `0`: marcada no 7.4, não no 8 | todo select com opção de chave 0 (1 no lote 2) |
| `dbforms/db_funcoes.php:1051` (`db_select`) | `reset($db_matriz)` com lista nula: aviso no 7.4, `TypeError` no 8 | 2 no lote 4 |
| `dbforms/db_funcoes.php:859` (`db_selectrecord`, somente leitura) | `is_resource($record)` é falso para `PgSql\Result`: a descrição do registro não aparece | todo select somente leitura (6 no lote 5) |
| `libs/db_stdlib.php:100`, `libs/db_libsession.php:63` | `pg_query()`/`pg_escape_string()` sem conexão: `Deprecated` no 8.1+ (aparece em tela que liga `display_errors`) | 1 no lote 5 |
| `dbforms/db_funcoes.php:1157` (`db_inputdata`) | `$db_opcao < 3` com texto não numérico: verdadeiro no 7.4, falso no 8 (só ocorre porque o formulário passa os argumentos deslocados) | 2 no lote 6 |
| `dbforms/db_funcoes.php:416` (`db_multiploselect`) | `gettype($rs) == "resource"`: `"object"` no 8, a lista sai vazia | 1 no lote 6 |
| `std/DBLargeObject.php:101` | `pg_lo_export()` com a conexão no fim (ordem removida no 8.0): `ArgumentCountError` | 1 no lote 6 |
| `cl_cadtipo` (módulo caixa, do Financeiro) | construtor estilo PHP 4 — já corrigido na branch do Financeiro, ainda não integrada | 2 no lote 5 |
| `classes/db_db_logsacessa_classe.php` | construtor estilo PHP 4 | usada pela Configuração e por webservices |
| `abrir.php:372` | `db_verifica_ip_banco()` chamada sem o argumento que o PR passou a exigir; quebra **igual no 7.4** (depois de gravar a sessão) | login direto pelo `abrir.php` |

## 6. Ambiente

- O login pelo formulário confere `sha1(md5(senha))`; o dump desta base já vem assim. O `update` do
  `CONTRIBUINDO.md` (`sha1('dbseller')`) quebra esse login: não rodar nesta base.
- `passport:install` falha no `install.sh` porque o banco não tem as migrations do PR (lacuna já registrada para o
  ambiente 7.4). Não impede as telas.
- Máquina Windows: o repositório tem de ficar no sistema de arquivos do Linux (WSL), por causa dos arquivos que só
  diferem em maiúsculas — vários são do Tributário (`cem1_legista00*`, model `Tabrec`, rota de arrecadação, model
  de ISSQN, manual do ITBI).

## 7. Telas expostas pelas correções do núcleo (20/11/2026)

Com o núcleo corrigido (branch `nucleo/8.5`), algumas telas desta área deixaram de parar no núcleo e passaram a parar
no próprio código. Três foram corrigidas aqui:

| Tela | Problema no 8.5 | Forma |
|---|---|---|
| `div2_certtermo_002.php` | `pg_num_rows` sobre consulta que falhou | guarda da decisão 2a, pelo mesmo script dos lotes (commit automático) |
| `fis2_fis_autolote002.php`, `fis2_fis_notlanclote002.php` | a tela faz `pg_close()` e inclui de novo `libs/db_conecta.php`, que não reabre a conexão. No 7.4 o resto da tela segue com as consultas falhando em silêncio. No 8.x: `pg_num_rows` sobre a consulta que falhou, e `@pg_last_error()` sem conexão em `cl_fis_parfiscal::sql_record` (`Error`) | guarda da decisão 2a nas telas; na classe, `try`/`catch` só desse `Error`, com o texto vazio que o 7.4 produzia |

Prova (medida sobre a `nucleo/8.5`, que contém esta branch):
- `php -l` nos dois runtimes.
- As 3 telas ficaram idênticas no 7.4 e no 8.5.
- Nas 37 telas que usam a classe ou incluem essas telas: **8 → 5 divergentes, nenhuma nova**.
- 7.4 igual antes e depois. Dois PDFs diferem só na hora, com o texto idêntico.

Sozinha, esta branch não muda o resultado dessas telas: elas ainda param antes, no núcleo (`fpdf151/fpdf.php`,
`libs/db_stdlib.php:100`), que é corrigido na `nucleo/8.5`. As 5 que continuam divergentes são `fis2_fis_levantamentolote002`,
`fis2_fis_levantamentomassa002`, `fis2_fis_termofiscal003`, `fis3_fis_imprimealvara` e `fis4_fis_importalevan001`.
