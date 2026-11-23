# Triagem das divergências da rodada "antes" (referência PHP 7.4 × PHP 8.5)

Rodada de 18/11/2026 sobre a `base-php74` (PR #8) com o banco de referência v2. O gabarito é o **PHP 7.4**: toda
divergência abaixo é o 8.5 respondendo diferente do 7.4 **sobre o mesmo código**. Decisões e ordem de trabalho:
[`decisoes-migracao.md`](decisoes-migracao.md).

## Resumo (10 linhas)

1. **Bateria PHP (consolidada): 28.783 casos = 18.958 IDENTICO, 9.206 DIVERGE, 609 INCONCLUSIVO, 10 ERRO_AMBIENTE.** Laravel (comparado com a própria referência) 719/0/273/0; fluxos 31 IDENTICO e 1 DIVERGE intermitente (7.4 contra 7.4).
2. **Três causas mecânicas explicam 90% das 6.635 telas e relatórios que divergem:** `parse_str()` com 1 argumento **3.577** (54%), `fpdf151/fpdf.php:614` (`$s{$i}`) **1.425** (21%) e `libs/JSON.php:188` (`$utf16{0}`) **980** (15%).
3. A 4ª é **SQL que falha** e o `false` vai para `pg_*()`: **428** telas (6%). No 7.4 a tela seguia vazia em silêncio; no 8.5 aborta.
4. **Construtor no estilo antigo:** 101 telas (`Call to a member function label() on null` nos `forms/`), 53 classes e 1 cadastro.
5. **`0 == ""` (silencioso):** 2.478 das 2.532 classes divergentes, 19 dos 35 cadastros (POST) e 21 telas (`db_select`). A tela abre igual, mas o 8.5 ignora o valor digitado e não grava. Não aparece em log nenhum.
6. O resto são **54 telas em 10 causas pequenas** (assinatura incompatível 13, funções de lista com `null` 8, `pg` sem conexão 7, `count(null)` 6…) e **49 telas que divergem sem deixar erro no log** (causa não isolada).
7. `each()` não é a primeira quebra de nenhuma tela (6 telas com `each` dão IDENTICO só porque a linha não roda sem parâmetros); `pg_lo_export` derruba 1 (`std/DBLargeObject.php:101`); `create_function`/`get_magic_quotes`: 0.
8. **Guia do grupo:** o lint bate exatamente (32 quebram só no 8.5, 13 já no 7.4), mas o guia **não cita `parse_str` de 1 argumento**, a causa nº 1 (7.645 chamadas em 7.560 arquivos), e "só 32 arquivos" esconde que 2 deles derrubam 2.405 telas e relatórios.
9. **Fora do radar:** 3.154 janelas de pesquisa `func_*` (2.920 com `parse_str` de 1 argumento; amostra viva: 8 de 8 quebram), 287 telas sem área, 609 INCONCLUSIVO, 10 telas que estouram o tempo **no 7.4**, POST/relatórios só do catálogo, telas abertas sem parâmetros.
10. **Nada entrou em `conhecidas.tsv`:** nenhuma destas divergências tem prova de que já existia antes da migração (o 7.4 responde certo em todas).

## Fonte e método

- Rodadas (fora do git, no WSL): `~/rodadas/antes74` (completa: PHP todas as áreas, Laravel com
  `--alvo-laravel http://localhost:8074`, fluxos; 08:16–13:41, 5 h 26 min, saída 2) e `~/rodadas/antes74-complemento`
  (as 11 telas ERRO_AMBIENTE de novo e o fluxo `incluir-registro` 2 vezes). Painel: `~/rodadas/antes74-consolidado.md`.
  Commit medido `26a96f432`, dump v2 (sha256 `97251574…0fad`), PHP 7.4.33 × 8.5.12, nenhuma renovação de sessão.
- **Causa ao vivo de cada tela e relatório DIVERGE (6.635 de 6.635)**: depois da rodada, cada um foi aberto de novo
  **só no 8.5** (mesma sessão da referência, restaurada antes de cada GET) e lidas as linhas novas do log da aplicação
  (`ecidade/extension/log/error.log`) e do log do PHP do 8.5 (`/var/log/php_errors.log`), sem mais nada rodando.
  Conta-se a **primeira** quebra de cada página. Dados brutos: `~/e74-logs/task6/sonda.jsonl`.
- Telas 200 × 200 e 500 × 500 (287): corpo dos **dois** lados de novo e o primeiro trecho diferente
  (`~/e74-logs/task6/ambos.jsonl`; as 287 continuam diferentes).
- Classes e POSTs: o detalhe da própria bateria (campos e SQL gravado) e o código.
- Varredura estática de `ecidade/` com o catálogo de padrões do MCP (`~/e74-logs/task6/padroes.json`) e `php -l` em
  **todos** os 36.713 `.php` (fora `vendor/`) nos dois contêineres (`~/e74-logs/task6/lint_*.txt`).

## Totais

| bateria | casos | IDENTICO | DIVERGE | INCONCLUSIVO | ERRO_AMBIENTE |
|---|---|---|---|---|---|
| PHP, consolidado | 28.783 | 18.958 | **9.206** | 609 | 10 |
| ↳ sintaxe (`php -l` das telas) | 13.033 | 13.023 | 4 | 6 | 0 |
| ↳ classes (`atualizacampos()`) | 2.629 | 38 | 2.532 | 59 | 0 |
| ↳ telas (GET sem parâmetros) | 13.036 | 5.883 | 6.599 | 544 | 10 |
| ↳ cadastros POST do catálogo | 48 | 13 | 35 | 0 | 0 |
| ↳ relatórios do catálogo | 37 | 1 | 36 | 0 | 0 |
| Laravel (contra a **própria** referência) | 992 | 719 | 0 | 273 | 0 |
| fluxos (proxy manda tudo ao 7.4) | 32 | 31 | 1 | 0 | 0 |

Status HTTP das 6.599 telas DIVERGE (7.4 × 8.5): 200 × 500 **6.307**, 500 × 500 152, 200 × 200 135, 302 × 500 2,
resposta truncada em 5 MB 3.

## Por causa raiz (cada divergência contada uma vez, pela primeira quebra)

| # | Causa | Telas | Relat. | Classes | POSTs | Sintaxe | **Total** | Amostra ao vivo (log do 8.5) |
|---|---|---|---|---|---|---|---|---|
| 1 | `parse_str()` com 1 argumento (removido no 8.0) | 3.576 | 1 | – | 8 | – | **3.585** | `ArgumentCountError: parse_str() expects exactly 2 arguments, 1 given` em `cem1_cemiterio003.php:38`, `hab1_cadastroavaliacao001.php:38` |
| 2 | `fpdf151/fpdf.php:614`: `$cw[$s{$i}]` (chaves para letra de texto, removidas no 8.0) | 1.391 | 34 | – | – | – | **1.425** | `ParseError: syntax error, unexpected token "{", expecting "]"` em `fpdf151/fpdf.php` linha 614 (`hab2_inscricoes002`, `con2_balancrece002`) |
| 3 | `libs/JSON.php:188`: `ord($utf16{0})` (idem) | 980 | – | – | 5 | – | **985** | `ParseError … expecting ")"` em `libs/JSON.php` linha 188 (`hab1_workflowativ.RPC.php`; também o **login no 8.5**) |
| 4 | `0 == ""` e afins: comparação texto × número (8.0), **silenciosa** | 21 | – | 2.478 | 19 | – | **2.518** | sem log (não é erro). Bateria: `ar37_sequencial: ref='1012' 8.5=0`; POST `pes1_pesdiver001`: 7.4 grava, 8.5 não; `db_select` deixa de marcar a opção `0` (`dbforms/db_funcoes.php:1055`) |
| 5 | SQL que falha → `pg_*(false)` (`TypeError` no 8.0) | 427 | 1 | – | – | – | **428** | `pg_num_fields(): Argument #1 ($result) must be of type PgSql\Result, false given` em `libs/db_stdlib.php:146` (`pro1_obrastec004`) |
| 6 | Construtor no estilo antigo (método com o nome da classe) | 101 | – | 53 | 1 | – | **155** | `Call to a member function label() on null` em `forms/db_frmcadtipo.php:29` (`cai1_cadtipo004`); classe: `rotulo`/`pagina_retorno` NULL |
| 7 | Assinatura de método incompatível com a da classe-mãe (só aparece ao carregar as duas) | 13 | – | – | – | – | **13** | `FluxoCaixaDCASP2017::getDados() must be compatible with RelatoriosLegaisBase::getDados(...)` (`con2_relatoriosdcasp011`) |
| 8 | `pg_query` sem conexão aberta (aviso no 7.4, `Error` no 8.0) | 7 | – | – | – | – | **7** | `No PostgreSQL connection opened yet` em `std/label/RotuloCampoDB.php:37` |
| 9 | Funções de lista com `null` (`in_array`, `reset`, `array_key_exists`, `implode`) | 8 | – | – | – | – | **8** | `in_array(): Argument #2 ($haystack) must be of type array, null given` em `forms/db_frmdepusur.php:65` |
| 10 | `count()`/`sizeof()` de algo que não é lista | 6 | – | – | – | – | **6** | `count(): Argument #1 ($value) must be of type Countable\|array, null given` em `cai3_gerfinanc053.php:132` |
| 11 | Tipo de argumento (`mktime` com texto, `pg_fetch_assoc` com linha texto) | 5 | – | – | – | – | **5** | `mktime(): Argument #4 ($month) must be of type ?int, string given` em `bib1_emprestimo002.php:95` |
| 12 | Operação com tipos incompatíveis | 4 | – | – | – | – | **4** | `Unsupported operand types: string + int` em `forms/db_frmserieequiv.php:42` |
| 13 | Constante não definida (aviso no 7.4, `Error` no 8.0) | 3 | – | – | – | – | **3** | `Undefined constant "DB_VERSION"` em `libs/db_app.utils.php:39` |
| 14 | Outros arquivos que não compilam no 8.5 (chaves, ternário encadeado, `(real)`) | 6 | – | – | – | 4 | **10** | `model/dbGeradorRelatorio.model.php:602`; `Unparenthesized a ? b : c ? d : e` em `edu2_certconclusao002.php:733`; `(real) cast has been removed` em `orc1_orcduplicacao001.php:46` |
| 15 | `pg_lo_export` com a conexão no fim (ordem removida no 8.0) | 1 | – | – | – | – | **1** | `Requires 2 or 3 arguments, 3 given` em `std/DBLargeObject.php:101` (`cad4_certidaoexistencia003`) |
| 16 | Propriedade atribuída em `null` | 1 | – | – | – | – | **1** | `Attempt to assign property "sql_marca" on null` |
| 17 | 200 × 200 sem erro no log, conteúdo diferente (listas, campos): **causa não isolada** | 47 | – | – | 1 | – | **48** | ex.: `pes1_rhgeraemppatroprev001` (o 8.5 não lista a opção INSS), `fis1_aidof002` (campos a menos) |
| 18 | Resposta truncada em 5 MB, sem erro no log | 2 | – | – | – | – | **2** | `agu2_agualancpago001`, `agu2_relreceitabairro001` |
| 19 | Classe que lança `Error` no 8.5 | – | – | 1 | – | – | **1** | `classes/db_iptuconstr_classe.php` |
| 20 | Cadastro que no 8.5 grava outra tabela | – | – | – | 1 | – | **1** | `cai1_arretipo001`: o 8.5 grava `configuracoesteftipodebito` (tabela não restaurada pela bateria), o 7.4 grava `arretipo` |
| | **Total** | **6.599** | **36** | **2.532** | **35** | **4** | **9.206** | |

Observações:
- **Telas 500 × 500 (152)** também são DIVERGE reais: o 7.4 mostra uma mensagem de negócio ("Esta rotina não está
  ativa", "Tabela de parâmetro (numpref) não configurada") e o 8.5 quebra antes (135 delas em `parse_str`).
- **Telas 200 × 200 (135):** 65 têm erro no log do 8.5 (a página quebra no meio, depois de começar a sair: 30 `pg_*`,
  29 `parse_str`, 5 `JSON.php`…); 21 são o `db_select` (`@$GLOBALS[$nome] == key($matriz)`: com o campo vazio, a opção
  de chave `0` vinha marcada no 7.4 e no 8.5 não vem); 49 não deixam erro no log (linhas 17 e 18; investigar uma a uma).
- **POSTs (35):** 32 "o 8.5 não grava nada" e 3 "grava diferente" (`pes1_relrub004`: `rh45_selecao` 1 × 0;
  `pes1_padroes001`; `cai1_arretipo001`). Dos 35, 19 têm a tela **idêntica** no GET: a quebra é só no caminho de
  gravação (`atualizacampos()`, regra `0 == ""`, conferido a fundo em `pes1_pesdiver001` na task 2 e ao vivo hoje em
  `arr1_grupotaxa001` pelo MCP). Os outros 16 morrem antes de gravar (8 `parse_str`, 5 RPC com `JSON.php`, 3 outros).
- **Relatórios (36):** 34 PDFs são o `fpdf.php:614`; `con2_relinstituicoes002`, `con2_balancrece002` e os outros
  balancetes saem no 7.4 e dão "Notificação do Sistema / Erro interno" no 8.5.
- **Efeito cebola:** das 1.425 telas que quebram no `fpdf.php`, **760 têm `parse_str` de 1 argumento no próprio
  arquivo**; corrigida só a linha 614, elas passam a quebrar no `parse_str`. Das 3.577 de `parse_str`, 2 têm `split`
  logo abaixo. Telas com `parse_str` no arquivo: 4.287 DIVERGE, 136 INCONCLUSIVO (a página já falha igual no 7.4) e 17
  IDENTICO (a linha não roda sem parâmetros).
- **Login direto no 8.5** (fora da bateria; ao vivo): o 8.5 não chega à lista de módulos por causa do `libs/JSON.php:188`.
  No 7.4 o `abrir.php:372` chama `db_verifica_ip_banco()` sem argumento e lança `ArgumentCountError` **também no 7.4**
  (o login segue funcionando): defeito do PR, registrado e não corrigido (regra "só atualizar").

## Comparação com as medições do guia do grupo

| Guia (`migracao-php74-para-85.html`) | O que a rodada viu | Por que diverge |
|---|---|---|
| 32 arquivos compilam no 7.4 e quebram no 8.5; 13 já falham no 7.4 | `php -l` em todos os 36.713 `.php`: **32 e 13, exatamente**. A bateria (só telas da raiz) vê 4 DIVERGE e 6 INCONCLUSIVO | a etapa de sintaxe só faz lint das telas; 28 dos 32 são bibliotecas. **Dois deles (`fpdf151/fpdf.php`, `libs/JSON.php`) são a 2ª e a 3ª causa: 2.405 telas e relatórios** (1.633 arquivos da raiz citam `fpdf151/`, 899 citam `libs/JSON.php`). "Só 32 arquivos" é certo na contagem e enganoso no alcance |
| (não cita `parse_str`) | **causa nº 1:** 3.585 divergências; 7.645 chamadas em 7.560 arquivos (4.531 telas + 2.920 `func_*`); nenhuma tela da base usa ainda `parse_str(x, $v); extract($v)` | o guia mediu lint e uma lista de padrões; `parse_str` de 1 argumento **compila** no 8.5 (o lint não pega) e não estava na lista |
| `each()` 84 usos / 28 arquivos | 85 / 28 na busca do MCP; **0** telas com `each` como primeira quebra (6 IDENTICO porque a linha não roda; 1 DIVERGE por outra causa) | a bateria abre as telas sem parâmetros: o `each` fica nos laços de processamento. Continua sendo quebra certa quando a linha rodar |
| `pg_lo_export`/`import` 40 usos / 33 arquivos | 1 tela ao vivo (`std/DBLargeObject.php:101`, classe usada por 36 arquivos); a busca do MCP aponta 15 com a conexão no fim | só roda ao exportar/gravar arquivo; o número do guia conta todas as chamadas |
| `create_function` 1, `get_magic_quotes_*` 2 | 0 como primeira quebra | mesma razão (caminho não exercitado) |
| `count()` de não-lista: "amplo" | 6 telas (`count`/`sizeof`) + 8 com outras funções de lista e `null` | a primeira quebra esconde as seguintes; a busca estática (24.117 pontos) não diz quais rodam com `null` |
| `== ""`: 36.729 pontos em 4.054 arquivos | 2.478 classes + 19 POSTs + 21 telas (`db_select`) | o GET não passa por `atualizacampos()`; só a etapa de classes e os POSTs exercitam. A busca do MCP conta 57.682/5.356 (regra mais larga) |
| Construtor antigo: 152 classes em 143 arquivos | 53 classes + 101 telas + 1 POST | a bateria instancia 2.629 classes de `classes/`; as de `libs/`, `dbagata/` e afins não; a busca do MCP acha 253/202 (inclui `.class`/`.inc`) |
| Obsoletos (`utf8_*` 1.832, `"${var}"` 113, `strftime` 12, `FILTER_SANITIZE_STRING` 3) | nenhuma divergência | `display_errors` desligado nos dois lados (paridade): o aviso não aparece; confirma a regra do guia |
| (não cita) SQL que falha | 428 telas | mudança do 8.0 (`pg_*` recebendo `false`); no 7.4 era aviso escondido |
| (não cita) assinatura incompatível em tempo de execução | 13 telas (`RelatoriosLegaisBase::getDados`, `FolhaPagamento::hasFolhaAberta`) | só quebra quando a classe-mãe e a filha são carregadas juntas; o lint de um arquivo por vez não vê. O guia lista as 4 do jpgraph, que quebram no lint |

## O que NÃO foi exercitado (nada disto é aprovação)

- **INCONCLUSIVO 609 (PHP):** 454 telas com a mesma página de erro nos dois lados (exigem parâmetros; 136 delas têm
  `parse_str` de 1 argumento escondido), 87 telas vazias nos dois lados, 57 classes sem saída, 2 classes com a mesma
  exceção (`ParameterException`), 6 telas que não compilam em nenhum runtime (`pes1_reajusteprog001` e outras: já
  quebradas no 7.4), 2 telas puladas por destruírem a sessão, 1 que chama serviço externo.
- **ERRO_AMBIENTE 10:** `rec2_espelhoponto002`, `con4_gerenciadortarefas002`, 7 `edu4_*` de importação/censo e
  `edu4_verifexportcenso002` estouram 60 s **na referência 7.4** (duas vezes, em duas rodadas). No 8.5 respondem em
  segundos (8 com `fpdf.php:614`). Sem gabarito, nada se conclui. (`mer3_mer_nutriitem002` rodou no complemento: DIVERGE.)
- **Fora da bateria:** 3.441 `.php` da raiz: **3.154 janelas `func_*`** (as "lupas"; 2.920 com `parse_str` de 1
  argumento; amostra ao vivo: 8 de 8 com `parse_str` dão 200 × 500, 6 de 8 sem ele saem iguais e 2 dão
  `pg_fetch_result(false)`) e 287 telas de prefixos sem área (`tra` 62, `ipa` 24, `db` 24, `pncp` 16…).
- **28 dos 32 arquivos que não compilam** só aparecem se uma tela os incluir: `securimage/` (captcha), `jpgraph`
  (gráficos), `Michelf/Markdown`, `libs/mail/func.php`, `model/cda.model.php`, `integracao_externa/gissonline`, as
  classes `app/…/CamposDinamicos*` e `src/Patrimonial/Protocolo/Container.php` (namespace), `fpdf151/impmodelos/*`.
- **Profundidade:** GET sem parâmetros prova que a tela "abre igual", não que os números batem. POSTs: só os 48
  verificados do catálogo (4 não verificados ficaram de fora); relatórios: 37 (5 não verificados).
- **Laravel:** comparado com a própria referência (estabilidade). A migração do Laravel não foi medida: o Laravel 13
  do grupo não existe e o laboratório (:8187) não emite token (`lcobucci/jwt` 3.4, ver `lab-lar12-resultado.md`).
  272 rotas dão 5xx nos dois lados com o corpo vazio da sonda.
- **Fluxos:** o proxy manda tudo ao 7.4, então medem a referência contra a gravação dela, não o 8.5. O DIVERGE
  `fluxo:incluir-registro:salvar` (a chamada de ajuda `con4_dbhelp.RPC.php?json` não aconteceu) não se repetiu em 2
  execuções seguidas: instabilidade da medição, registrada como DIVERGE intermitente, não como aprovada.
- **Avisos e obsoletos:** com `display_errors` desligado, o que só gera aviso não aparece em nenhuma bateria.

## `conhecidas.tsv`

Continua vazio. A regra do arquivo aceita só divergência **preexistente com prova**; aqui o gabarito é o próprio 7.4
e ele responde certo em todos os 9.206 casos. Os defeitos do 7.4 achados no caminho (`abrir.php:372`
`db_verifica_ip_banco()` sem argumento; `GET …/acordo/buscar-configuracoes` que grava; os do Laravel 8 citados no guia)
não são divergências 7.4 × 8.5: ficam registrados para o dono da área.

## Como reproduzir

```bash
regressao/bin/regressao rodada-completa --alvo-laravel http://localhost:8074   # ~5 h 30 min, em segundo plano
regressao/bin/regressao rodada-pequena                                         # ~25 min, 3 grupos de telas
regressao/.venv/bin/python -m regressao.php.bateria --saida /tmp/x --prefixo '^cem1_cemiterio00'
```
