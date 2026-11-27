# Rastreador de fluxo de dados entre versoes do PHP - design

Data: 2026-11-27. Projeto: regressao do e-Cidade (PHP 7.4 -> 8.5). Local previsto: `regressao/rastro/`.

## 1. Intencao e por que

A bateria diz **qual tela** diverge, nao **onde o dado se separou**. Hoje, para achar a linha, e preciso ler o log de
erro do 8.5 e deduzir. O rastreador deve acompanhar o dado do inicio ao fim da requisicao nos dois PHP e dizer
**a linha exata** em que o comportamento mudou.

Regra de decisao (do dono do projeto):

- Divergiu no meio, mas o **resultado final e igual** nos dois lados: **correto** (divergencia "reconvergente"), so informativa.
- Divergiu e o **resultado final difere**: **defeito**. Apontar a **primeira divergencia que nao reconverge** e a
  **cadeia de atribuicoes** que levou ao valor errado.

## 2. Objetivos, nao-objetivos, anti-objetivos

Objetivos
- Rastro por linha (`arquivo:linha`), com variavel e resumo do valor, em 7.4 e 8.5 para a mesma requisicao.
- Alinhar os dois rastros, classificar cada divergencia (reconvergente / causal) e apontar a causal.
- Instrumentar a arvore **inteira** do `ecidade/` agora e **nunca reinstrumentar o que nao mudou** (cache por hash).
- Capturar tambem **avisos/notices/deprecated** (o 7.4 emite aviso onde o 8.5 lanca excecao: e o sinal mais comum
  nas divergencias da rodada base85b).

Nao-objetivos (v1)
- Nao roda na bateria inteira (e lento); roda nas telas que divergem, ou numa lista escolhida.
- Sem interface grafica; saida em JSON + relatorio Markdown.
- Laravel (`lar12`) fora da v1.
- Nao altera o codigo-fonte do e-Cidade: a arvore instrumentada e uma **copia** em outro diretorio.

Anti-objetivo (falha mesmo que "funcione")
- **A instrumentacao mudar o comportamento.** Uma sonda que altera a saida da tela invalida tudo. Por isso ha um
  portao de equivalencia (secao 6).

## 3. Abordagens consideradas

| | Abordagem | Resultado |
|---|---|---|
| **A** | Reescrever o codigo com sondas (AST), rodar nos dois PHP, comparar rastros | **Escolhida para comecar.** Funciona em qualquer versao, sem extensao. Custo: rastro grande e lento. |
| B | Xdebug em modo trace nos dois contêineres | Fase 2. Hoje nao ha Xdebug; verificar se ha versao para o 8.5 e se registra valores de atribuicao antes de decidir. Evita reinstrumentar. |
| C | Analise estatica de fluxo (ex.: `pg_query` -> `pg_num_rows` sem checar `false`) | Fase 3. Acha candidatos sem executar; nao prova divergencia real. Reaproveita o parser da fase 1. |

O dono do projeto quer as tres; a ordem e A, depois B e C. A cache por hash da fase 1 ja atende o pedido de "nao
reinstrumentar tudo toda vez" para o caso A.

## 4. Arquitetura da fase 1 (A)

Quatro pecas, cada uma com uma responsabilidade.

1. **Instrumentador** (PHP, `nikic/php-parser`, roda no contêiner). Le `.php`, devolve `.php` com sondas e um
   `.map.json` (`id_da_sonda -> arquivo, linha, tipo, variaveis`).
   - Sondas: apos **atribuicao** (variavel e resumo do valor), em **chamadas** de funcoes selecionadas
     (`pg_*`, `db_query`, `mktime`, `checkdate`, `count`/`sizeof`, `implode`, `explode`...; lista em arquivo de
     configuracao) com argumentos e retorno, em **desvios** (`if`/`?:`/`switch`: qual ramo), em **retorno de funcao**,
     em **excecao capturada**.
   - **Preserva a numeracao de linhas**: as sondas entram na mesma linha, sem inserir quebras. O erro do PHP continua
     apontando a linha original.
   - Nao reescreve expressoes (nunca avalia nada duas vezes); a sonda de atribuicao vem **depois** do comando.
2. **Biblioteca de execucao** (`rt.php`, carregada por `auto_prepend_file` so no vhost instrumentado). Escreve eventos
   em memoria e faz flush em `register_shutdown_function` num arquivo `.jsonl` por requisicao. Encadeia o
   `set_error_handler` (sem perder o handler do e-Cidade) para registrar avisos/notices/deprecated com
   `arquivo:linha`, e registra a excecao nao tratada. Compativel com 7.4 e 8.5.
3. **Executor** (Python). Reaproveita da bateria: login, sessao, restauracao de sessao, requisicao nos dois contêineres,
   normalizacao da resposta. Pede o rastro de cada lado e a resposta final.
4. **Alinhador e classificador** (Python). Alinha os dois rastros por (id da sonda + n-esima ocorrencia), acha as
   divergencias, e classifica:
   - **reconvergente**: valores voltam a ser iguais depois e a resposta final normalizada e igual.
   - **causal**: a resposta final difere; a primeira divergencia que nao reconverge e a candidata.
   - Cadeia causal: segue para tras as atribuicoes (def-use) das variaveis que alimentaram o valor.
   - Quando um lado emite **aviso** e o outro **lanca excecao** na mesma linha, isso e a divergencia (ex.:
     `pdf.php:186`, `pg_result()` sobre `false`).

### Resumo de valores (determinismo)
Cada valor vira `{tipo, resumo, hash}`: escalares inteiros; strings longas truncadas + hash; arrays por forma + hash;
objetos por classe + hash das propriedades; `resource` por tipo (`pgsql result`), nunca por numero. **Normaliza** data/hora,
id de sessao, numeros aleatorios, ids de recurso e ordem de arrays cuja ordem o PHP nao garante. Reaproveita
`regressao/nucleo/normaliza.py` para o que ja existe.

### Instrumentacao da arvore inteira e incremental
- Entrada: `ecidade/` (excluindo `vendor/`, `tmp/`, `node_modules/`, como o lint de arvore). Saida: `ecidade-rastro/`
  (copia espelhada, fora do git).
- **Cache**: `manifesto.json` com `sha256(fonte) + versao_do_instrumentador` por arquivo. Rodar de novo reinstrumenta
  **so o que mudou** (ou o que mudou na versao do instrumentador). Remover arquivos apagados.
- Verificacao de sanidade em toda rodada: `php -l` em 7.4 e 8.5 de cada arquivo gerado (reaproveita `arvore.py`).
- Primeira passada na arvore inteira e demorada; as seguintes sao incrementais.

### Implantacao
`ecidade-rastro/` montada somente-leitura nos dois contêineres e servida por um segundo vhost/porta com
`auto_prepend_file=rt.php`. O vhost normal (8074/8185) nao muda. O banco e a sessao sao os mesmos da bateria.

## 5. Saida

- `rastro/<requisicao>/{ref74.jsonl, alvo85.jsonl, resposta_*.bin}`
- `relatorio.md` por tela: veredito (`IDENTICO` / `DIVERGE-RECONVERGENTE` / `DIVERGE-CAUSAL`), primeira divergencia
  causal (`arquivo:linha`, variavel, valor em 7.4, valor em 8.5), cadeia de atribuicoes, e os avisos que so um lado emitiu.
- Integracao futura: ler a lista de telas DIVERGE de uma rodada e rastrear todas, anexando o `onde_corrigir`
  calculado ao relatorio por area.

## 6. Criterios de sucesso

1. **Portao de equivalencia:** em N telas amostradas, a resposta do 7.4 instrumentado e **identica** a do 7.4 sem
   instrumentacao (mesma normalizacao da bateria). Sem isso, o rastreador nao pode ser usado.
2. 100% dos arquivos instrumentados passam em `php -l` nos dois PHP.
3. **Casos conhecidos:** `cad2_setor002.php` (`pg_num_rows` sobre `false`), uma tela de PDF com o `pdf.php:186` e uma
   com `std/DBDate.php:203` (`checkdate` com string vazia): o relatorio aponta a linha correta como causal, sem o
   migrador ler o log.
4. **Reconvergencia:** um caso sintetico em que a divergencia some e a resposta final e igual e classificado como
   reconvergente, nao como defeito.
5. Segunda execucao do instrumentador sem mudancas: 0 arquivos reprocessados.

## 7. Riscos

- **Volume e lentidao** do rastro (por isso so telas escolhidas, e a lista de funcoes com sonda e configuravel).
- **Codigo dinamico** (`extract`, `compact`, variaveis variaveis, `eval`, `include` de caminho calculado, referencias
  `&`, `global`/`static`): a sonda pode nao ver todas as variaveis. A v1 registra onde isso ocorre; nao promete cobrir.
- **Nao determinismo** real (tempo, aleatorio, ordem de resultados do banco) gera divergencias falsas; mitigado pela
  normalizacao e por rodar o 7.4 **duas vezes** para descontar o que ja varia sozinho.
- Parser: o `php-parser` precisa ler a sintaxe 7.4 do e-Cidade (arquivos em ISO-8859-1, `{}` em offsets antigos ja
  corrigidos mas ainda presentes em outras branches). Arquivo que nao parseia e registrado e fica **sem sonda**.

## 7.1 Decisoes tomadas apos a revisao do design

Respondidas pelo proprio projeto:
- **Ambiente existe e e o alvo dos testes.** Contêineres `ecidade74_php74` e `ecidade74_php85`, banco e sessoes compartilhados
  (`/var/lib/php/sessions` e `/tmp` sao o mesmo volume nos dois). Codigo a reutilizar: `regressao/nucleo/normaliza.py`,
  `regressao/php/arvore.py` (lint da arvore), `regressao/php/telas.py` (`login_http`, `restaura_sessao`, `_requisita_status`,
  `containers_do_ambiente`). Os criterios 1 e 3 usam telas reais, nao mocks.
- **Uma unica arvore.** Os dois contêineres montam o mesmo `ecidade/`: o 7.4 roda os **mesmos arquivos** que o 8.5. Logo
  `arquivo:linha` e uma chave de alinhamento valida e basta **um** manifesto/uma arvore `ecidade-rastro/`.
- **Onde fica.** `regressao/rastro/` neste repositorio (Python) + `regressao/rastro/php/` (instrumentador e `rt.php`). O
  instrumentador roda no contêiner **8.5** com `ecidade/vendor/nikic/php-parser` (carregar `vendor/autoload.php`); parsear em
  modo PHP 7 (sintaxe do e-Cidade). A versao instalada deve ser conferida na primeira tarefa; se nao parsear a sintaxe 7.4,
  instalar uma versao compativel num diretorio proprio via `composer`.

Decisoes minhas (podem ser corrigidas):
- **Identificacao do rastro:** cabecalho HTTP `X-Rastro-Id: <id>` em cada requisicao; `rt.php` grava em `/tmp/rastro/<id>.jsonl`
  (volume compartilhado, lido pelo Executor).
- **Matriz de execucao por tela:** instrumentado 7.4 **x2** (descontar ruido), instrumentado 8.5 **x1**. O portao de
  equivalencia (7.4 sem instrumentacao x 7.4 instrumentado) e um comando **separado**, rodado sobre uma amostra, nao em toda tela.
- **Insercao de sondas por emenda de bytes**, nao por reimpressao da AST: usar as posicoes de inicio/fim do `php-parser` para
  inserir texto no arquivo original. Os bytes fora das sondas (inclusive ISO-8859-1) ficam **identicos** e a numeracao de linhas
  nao muda. Arquivo que nao parseia fica sem sonda e e registrado.
- **Volume:** a arvore tem ~36.700 arquivos `.php`; o instrumentador roda em paralelo (um processo por nucleo). O rastro e
  gravado por **flush progressivo** (a cada N eventos e no shutdown), nao so no fim, para sobreviver a `exit`, erro fatal ou
  estouro de memoria; ha teto de eventos por requisicao (marcado como "truncado" no relatorio).
- **"Resultado final igual" na v1:** resposta HTTP normalizada (a mesma da bateria) **mais** o codigo HTTP. Efeitos no banco ficam
  fora da v1; para POSTs vale o que a bateria ja compara (SQL de escrita). Divergencia no estado do banco sem diferenca na resposta
  fica registrada como limitacao, nao como defeito.
- **Qual lado esta certo:** o 7.4 e a referencia; o valor do 7.4 e o esperado. Isso vale porque a regra do projeto e preservar o
  comportamento.
- **Cadeia causal:** feita **so com dados das sondas**: cada sonda de atribuicao registra tambem os **nomes das variaveis lidas**
  na expressao (calculados estaticamente na instrumentacao). O def-use e por nome, dentro da mesma funcao/escopo. Analise de fluxo
  de verdade fica para a fase 3 (C).

## 8. O que fica para quem constroi

Nomes de modulos e testes; formato exato do `.jsonl`; a lista inicial de funcoes com sonda; estrategia de alinhamento
(LCS ou por contador); como montar o segundo vhost (compose ou Apache dentro do contêiner).

## 9. Fases seguintes (fora desta especificacao)

- **Fase 2 (B):** spike para ver se ha Xdebug para 7.4 e 8.5 com valores de atribuicao; se sim, gera o mesmo formato de
  rastro **sem reinstrumentar**.
- **Fase 3 (C):** analise estatica de fluxo sobre o mesmo parser, para listar candidatos antes de executar.
