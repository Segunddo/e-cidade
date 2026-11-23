# Decisões da migração PHP 7.4 → 8.5: o que corrigir primeiro (rodada "antes", 18/11/2026)

Para: gestor / coordenador do grupo. Base: rodada "antes" completa e consolidada (`~/rodadas/antes74-consolidado.md`)
e a triagem por causa ([`triagem-divergencias.md`](triagem-divergencias.md)), com a causa de **cada** tela divergente
lida ao vivo no log do PHP 8.5. Referência (gabarito): **PHP 7.4 + Laravel 8 do PR #8**. Nada foi alterado no código
do e-Cidade nem nas linhas de base.

## Resumo (10 linhas)

1. **Hoje o 8.5 diverge do 7.4 em 9.206 de 28.783 casos medidos**: 6.599 telas, 36 relatórios em PDF, 2.532 classes de dados, 35 cadastros e 4 arquivos que não compilam. É o esperado: a `base-php74` ainda não foi adaptada.
2. **Duas linhas de código derrubam 2.405 telas e relatórios**: `fpdf151/fpdf.php:614` (todo PDF) e `libs/JSON.php:188` (toda tela que usa JSON, inclusive o **login direto no 8.5**). Corrigir as duas leva menos de 1 hora; é o primeiro passo.
3. **`parse_str()` com 1 argumento é a maior causa (3.585 casos)** e o guia do grupo não a cita. Está em 7.560 arquivos, incluindo 2.920 das janelas de pesquisa (`func_*`) que a suíte não testa. Correção mecânica: 2 a 3 dias, dividida por área.
4. **O risco maior é silencioso**: com `0 == ""` o 8.5 abre o cadastro igual, o usuário digita, clica em salvar e **nada é gravado** (19 dos 35 cadastros testados; 2.478 classes). Não dá erro nem log. Há regra Rector do grupo para isso: 1 a 2 dias.
5. **Quatro passos mecânicos** (2 linhas, `parse_str`, `0 == ""`, construtor antigo em 152 classes) cobrem cerca de **94%** das divergências, em cerca de **4 a 7 dias de desenvolvimento**, mais as rodadas da bateria por área.
6. **SQL que falha (428 telas) pede decisão**: o 7.4 mostra a tela vazia sem avisar; a regra "funciona igual ao 7.4" manda reproduzir isso no 8.5 (1 a 2 dias, num ponto central). Mostrar erro claro é mudança de comportamento e precisa de decisão do grupo.
7. Sobra uma cauda de **cerca de 100 telas** com causas pequenas ou não isoladas (1 a 3 h cada; 2 a 3 semanas no total, por área).
8. **"Aceitar" não conserta nada**: pôr as divergências em `conhecidas.tsv` deixa a rodada verde e manda para produção relatórios que dão "Erro interno" e cadastros que não gravam. Contraria a regra do arquivo (só divergência anterior à migração, com prova). **Não recomendado para nenhuma.**
9. **A suíte não vê tudo**: 3.154 janelas de pesquisa, 287 telas sem área, 609 casos INCONCLUSIVO, 10 telas que estouram o tempo já no 7.4, telas abertas sem parâmetros (prova que "abre igual", não que os valores batem) e o Laravel 13, que ainda não existe.
10. **Defeitos do próprio 7.4** achados no caminho (`abrir.php:372` no login, uma consulta que grava, os do Laravel 8 do guia) são **registrados e avisados ao dono**, não corrigidos na migração.

---

## A. O que corrigir primeiro (ordem do grupo: não compila → quebra ao rodar → silencioso)

| Passo | O quê | Casos que saem da 1ª causa | Esforço | Risco de mudar o comportamento | Área (dono) |
|---|---|---|---|---|---|
| **1** | `fpdf151/fpdf.php:614` e `libs/JSON.php:188`: `$s{$i}` → `$s[$i]` (2 linhas) | **2.410** (1.425 PDF, 985 JSON) + login no 8.5 | < 1 h + rodada da bateria | **nenhum**: o 7.4 aceita as duas formas e lê igual | núcleo (`fpdf151/`, `libs/`) |
| 1b | os outros 30 arquivos que não compilam no 8.5 (18 com chaves, um deles só porque inclui outro; 3 ternários encadeados, 4 nomes com `\`, 4 assinaturas do jpgraph, 1 `(real)`) | 10 diretos + o que os incluir (captcha, gráficos, Markdown, e-mail) | 0,5 a 1 dia | baixo (ternário: pôr os parênteses na ordem que o 7.4 usa, da esquerda) | várias |
| **2** | `parse_str(X)` → `parse_str(X, $__qs); extract($__qs);` (com `unset($__qs['this'], $__qs['GLOBALS'])`) | **3.585** + cerca de 760 telas de PDF que hoje quebram antes + 2.920 lupas fora da suíte | 0,5 dia de script + revisão por amostra; 2 a 3 dias com as rodadas por área | baixo: variáveis da URL continuam no escopo local, como no 7.4 (conferir chaves com `.`/espaço e arrays) | todas (cada área nas suas telas) |
| **3** | `0 == ""`: regra Rector do grupo `GuardaComparacaoLiteralRector` nas classes (`atualizacampos()`) e no `db_select` (`dbforms/db_funcoes.php:761` e `:1055`) | **2.518** (2.478 classes, 19 cadastros, 21 telas) | 1 a 2 dias + rodada de classes e POSTs | **médio**: a guarda tem de reproduzir exatamente a comparação do 7.4 (não "corrigir"); 4.054 arquivos | núcleo (`dbforms/`) + cada área nas `classes/` |
| **4** | Construtor antigo: acrescentar `__construct()` que chama o método antigo (152 classes em 143 arquivos) | **155** (101 telas, 53 classes, 1 cadastro) | 0,5 dia | baixo: devolve a inicialização que o 7.4 fazia | cada área |
| **5** | SQL que falha (`pg_*(false)`): **decisão** (ver B) | **428** | (a) 1 a 2 dias num ponto central; (b) 1 a 3 h por tela | (a) nenhum; (b) muda o que o usuário vê | núcleo (`libs/db_stdlib.php`) |
| 6 | Cauda: assinatura incompatível (13, quase todas em `RelatoriosLegaisBase`), funções de lista e `count` com `null` (14), `pg` sem conexão (7), tipos (9), constante indefinida (3), `pg_lo_export` (1), outros (4) | **54** telas | 1 a 3 h por causa; várias telas por correção | baixo a médio | por área |
| 7 | 49 telas que divergem **sem erro no log** (listas e campos a menos no 8.5) + `cai1_arretipo001` (grava outra tabela) | **50** | 1 a 2 h por tela, para achar a causa | ? | por área |

Ordem de grandeza (faixas, por causa do **efeito cebola**: cada correção pode revelar a quebra seguinte da mesma tela):

| Depois de | DIVERGE esperados (de 9.206) | O que sobra |
|---|---|---|
| hoje | 9.206 | — |
| passo 1 | cerca de 7.500 a 7.900 | as 760 telas de PDF passam a quebrar no `parse_str` |
| passos 1 + 2 | cerca de 3.600 a 4.700 | classes e cadastros (`0 == ""`), SQL que falha, construtor, cauda e as camadas reveladas |
| passos 1 a 4 | cerca de 1.000 a 1.700 | SQL que falha (428), cauda (cerca de 100) e o que as correções revelarem |
| passos 1 a 5 (opção a) | cerca de 500 a 1.300 | cauda caso a caso |
| tudo em `conhecidas.tsv` | 0 (rodada verde) | **tudo continua quebrado em produção** |

Os números do passo 2 em diante são estimativas (a 2ª camada só aparece rodando). Corrigir também pode **mover**
casos de INCONCLUSIVO para DIVERGE (136 telas com `parse_str` hoje falham igual nos dois lados): é a suíte vendo
mais, não regressão nova.

## B. As decisões que dependem do grupo

1. **SQL que falha (428 telas).** O que acontece: a consulta dá erro no banco (em geral porque a tela foi aberta sem
   parâmetros ou falta dado no banco de teste); no 7.4 a função `pg_*` recebe `false`, avisa em silêncio e a tela sai
   vazia; no 8.5 a página aborta com "Erro interno".
   - (a) **Paridade**: um ponto central (`libs/db_stdlib.php`) devolve "nenhuma linha" quando a consulta falha, como
     o 7.4. Segue a regra "funciona igual ao 7.4"; o usuário continua sem saber que houve erro. 1 a 2 dias.
   - (b) **Erro claro** tela por tela. É mudança de comportamento: pela regra "só atualizar", só com decisão do grupo.
   - Recomendação: (a) agora; (b), se o grupo quiser, como melhoria registrada fora da migração.
2. **`parse_str`: seguir o precedente da `base-php84`.** O PR não mexeu nessas telas (nenhuma usa ainda
   `parse_str(x, $v); extract($v)`). Pela regra do guia ("se o PR não mexeu e quebra no 8.5, a `base-php84` serve de
   modelo"), use a forma de lá, adaptada ao arquivo do PR, em commit separado do Rector/script.
3. **`0 == ""`: a regra Rector do grupo** já existe; a decisão é aplicá-la em massa (4.054 arquivos, um commit
   automático por área) e provar com a etapa de classes e os POSTs que o 8.5 grava igual ao 7.4.
4. **Fluxos de navegador**: hoje o proxy manda tudo ao 7.4. Decidir quando as telas corrigidas passam a ir ao 8.5,
   para os fluxos medirem a migração.

## C. O que "aceitar" significaria

"Aceitar" = acrescentar a linha `<id>	<motivo>` em `regressao/conhecidas.tsv`. A rodada deixa de ficar vermelha (saída 0),
mas:

- relatórios em PDF (balancetes, CGM, instituições…) continuam dando "Notificação do Sistema / Erro interno";
- cadastros continuam **sem gravar e sem avisar** (o pior caso: o usuário acha que salvou);
- o login direto no 8.5 continua quebrado;
- o arquivo diz que só entra divergência **preexistente com prova**. Aqui o gabarito é o próprio 7.4 e ele responde
  certo em todos os 9.206 casos: nenhuma é preexistente. **Nada foi posto em `conhecidas.tsv`.**

## D. O que a suíte NÃO vê (o verde futuro só vale para o que foi exercitado)

- **3.154 janelas de pesquisa `func_*`** (as "lupas" de quase todos os formulários): fora da bateria. 2.920 têm
  `parse_str` de 1 argumento; ao vivo, 8 de 8 dão 200 no 7.4 e 500 no 8.5. Recomenda-se rodar `--prefixo '^func_'`
  depois do passo 2 (é mudança de uso da suíte, não de código).
- **287 telas de prefixos sem área** (`tra`, `ipa`, `db`, `pncp`, `fim`…).
- **609 INCONCLUSIVO**: 454 telas que falham igual nos dois lados (exigem parâmetros), 87 vazias, 57 classes sem
  saída, 6 que não compilam nem no 7.4, 3 puladas. Não são aprovação.
- **10 ERRO_AMBIENTE**: importações e processamentos (`edu4_*` do censo, espelho de ponto, gerenciador de tarefas) que
  estouram 60 s **no 7.4**. Precisam de um teste com o arquivo de importação.
- **Profundidade**: as telas são abertas sem parâmetros; os balancetes saem só com o cabeçalho. O catálogo tem 48
  cadastros e 37 relatórios; números de balancete com parâmetros reais não foram comparados.
- **28 dos 32 arquivos que não compilam** (captcha, gráficos, Markdown, e-mail, `cda.model.php`, GISS Online) só
  aparecem se alguma tela os carregar.
- **Laravel**: comparado só com ele mesmo (a medição é estável: 719 iguais, 0 diferentes). A migração para o
  Laravel 13 não foi medida (o código não existe; o laboratório não emite token).
- **Avisos de obsoleto** (`utf8_*`, `"${var}"`, `strftime`): com `display_errors` desligado nos dois lados, não
  aparecem. Pela regra do guia, não precisam de correção enquanto não mudarem o resultado.

## E. Ordem recomendada (seguindo as regras do grupo)

1. **Núcleo, passo 1** (as 2 linhas) em um pull request pequeno, com `php -l` nos dois runtimes e a bateria antes e
   depois (`regressao/bin/regressao comparar`). Prova de que o 7.4 continua igual: as mesmas telas no 7.4 antes e depois.
2. **Passo 1b** (os outros 30 que não compilam), cada um pelo dono da área do arquivo.
3. **Passo 2 (`parse_str`)** por área, script/Rector num commit e ajustes manuais em outro (regra 4), arquivos em
   ISO-8859-1, incluindo as `func_*` da área; rodada da área depois de cada lote.
4. **Passos 3 e 4** (`0 == ""` e construtor antigo) por área, com a etapa de classes e os POSTs como prova.
5. **Decisão B.1** e o passo 5.
6. **Cauda** (passos 6 e 7) tela a tela, com o diff da bateria.
7. **Registrar, não corrigir**: `abrir.php:372` (`db_verifica_ip_banco()` sem argumento: lança erro no 7.4 depois de
   gravar a sessão), `GET patrimonial/contratos/acordo/buscar-configuracoes` (grava ao consultar), os 13 arquivos que
   não compilam nem no 7.4, e os defeitos do Laravel 8 já listados no guia. Avisar o dono de cada área.
8. Depois de cada passo, **rodar a suíte da área** (`regressao/bin/regressao rodada-completa --area <area>`) e
   comparar com esta rodada "antes" (`~/rodadas/antes74`).

## Incertezas

- A causa de cada tela é a **primeira** quebra lida no log; a segunda só aparece depois de corrigir a primeira.
- 49 telas divergem sem erro no log: a causa não foi isolada.
- Os esforços são de quem conhece o e-Cidade e não incluem as horas de máquina (a rodada completa leva 5 h 30 min;
  por área, de minutos a 1 h).
- O banco de referência v2 não é um banco migrado pela DBSeller (24 migrations do PR não aplicam em PG 16); 7.4 e 8.5
  usam o mesmo banco, então a comparação é justa, mas o comportamento é o deste banco.
