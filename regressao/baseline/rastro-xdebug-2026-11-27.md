# Rastreador - teste do backend B (Xdebug, sem instrumentar) - 2026-11-27

**Pergunta:** o trace do Xdebug alcanca o que as sondas alcancam, sem reescrever nem reinstrumentar o codigo?
**Resposta curta:** nos casos de alta confianca, **sim**: das 146 telas em que o backend A (sondas) achou uma excecao, o B aponta
**exatamente o mesmo arquivo:linha em 146 (100%)**. Nos casos sem excecao (33) os dois concordam menos, e nestes a causa e incerta
para os dois.

## Ambiente

| | PHP 7.4 | PHP 8.5 |
|---|---|---|
| Xdebug | 3.1.6 (`php7.4-xdebug`, apt/sury) | 3.5.3 (`pecl install xdebug`) |
| Formato do trace | 4 (computer readable) | 4 |
| Modo | `trace`, `start_with_request=trigger`, `collect_assignments=1`, `collect_return=1` | idem |

O trace so e gravado quando a requisicao traz o cookie `XDEBUG_TRACE=1`. **`xdebug.mode` e lido na inicializacao do PHP**: tentar ligar por
vhost (`php_admin_value`) muda o texto do ini mas nao o modo ativo. Por isso o rastreio liga o modo globalmente (reinicia o Apache) e
**sempre desliga ao terminar**.

## Resultado nas 179 telas DIVERGE da rodada base85b (3 inconclusivas do A ficaram de fora)

Tempo: **878 s** (3 requisicoes por tela, ~5 s/tela) - parecido com o backend A, mas **sem nada para instrumentar**.

| Comparacao com o backend A | Telas |
|---|---|
| A achou excecao -> **mesma linha** no B | **146 de 146** |
| A sem excecao -> mesma linha | 7 |
| A sem excecao -> mesmo arquivo, outra linha | 11 |
| A sem excecao -> arquivo diferente (B aponta `libs/db_stdlib.php:818` em varias) | 14 |
| A sem excecao -> B sem causa (reconvergente) | 1 |

Os 4 casos reais (`cad2_setor002.php:79`, `cad2_loteam002.php:179`, `std/DBDate.php:203`, `fpdf151/pdf.php:186`) saem iguais nos dois
backends, com o dado que quebrou (`rsSql = FALSE`, `mes = ''`...) na cadeia.

## Custo

- Trace de `cad2_setor002.php`: ~9,4 MB e ~48 mil linhas por requisicao (o backend A grava ~6 mil eventos). O arquivo e apagado depois de lido.
- Python: ~200 MB de memoria para 4 telas x 3 requisicoes.
- Com o Xdebug **carregado**, mesmo com `mode=off` ou sem gatilho, o `login.php` custa alguns ms a mais (6 -> 11 ms no 7.4, 6 -> 7 ms no 8.5).
  Por isso `modo off` **descarrega a extensao** (8.5: tira a linha `zend_extension`; 7.4: `phpdismod`). Medido depois: 4,4 ms (7.4) e 5,3 ms (8.5),
  iguais ao de antes de instalar. **Fora do rastreio nao ha custo.**

## O que o B nao tem (e o A tem)

- Sem sondas de **condicao** (`if`/`while`): o ramo escolhido so aparece pela diferenca nas chamadas seguintes.
- Sem a lista de **variaveis lidas** por linha: a cadeia do B e um *contexto por proximidade* (as ultimas atribuicoes do arquivo nas 12 linhas antes do
  sintoma), nao uma cadeia por dependencia de dados.
- Sem o **aviso do 7.4** (o Xdebug nao registra avisos): o par "aviso no 7.4 x excecao no 8.5" aparece como "excecao so no 8.5".
- Trace gigante em tela com laco enorme (limitado a 60 s por requisicao e 3 milhoes de linhas lidas; nao testei uma tela de 2 milhoes de eventos).
- A versao 3.5.3 tem um defeito conhecido no nome de variavel de atribuicoes a `$GLOBALS`/`$_SERVER` (`$_path$key_path = ...`), irrelevante aqui.

## Conclusao e proximo passo

- Para **nao reinstrumentar nunca**, o B resolve: nao ha arvore, cache nem versao do instrumentador. A instalacao e repetivel
  (`xdebug.prepara`) e o custo fora do rastreio e zero.
- O A continua melhor onde precisa de **condicoes**, **variaveis lidas** e **aviso do 7.4**. Recomendacao: **B como padrao**, A para aprofundar
  as telas sem excecao (as 33), onde os dois discordam.
- A fase C (analise estatica) pode fornecer ao B o que lhe falta: as variaveis lidas em cada linha, sem executar nada.

## Uso

```bash
python -m regressao.rastro rastreia cad2_setor002.php --backend xdebug --saida rastro-saida
python -m regressao.rastro rastreia --de-rodada ~/rodadas/base85b --area patrimonial --backend xdebug
```
