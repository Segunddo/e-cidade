# Rastreador - fase C: conferencia dos pontos fortes de comparacao frouxa (2026-11-28)

Conferi, **um a um e lendo o codigo**, os 51 pontos distintos (linha + expressao; 53 ocorrencias) do nivel forte de `rastro-comparacoes-2026-11-27.md` (variavel que recebeu inteiro no mesmo escopo e e comparada com `''`, texto ou `0`). A classificacao por ponto esta em `rastro-comparacoes-conferencia-2026-11-28.tsv` (efeito observavel e correcao sugerida).

| Veredito | Pontos | Significado |
|---|---|---|
| CONFIRMADO | 4 | confirmado por execucao (`ate1_tarefa004.php`) ou por semantica medida nos dois contêineres (`strlen('') != ''`) |
| PLAUSIVEL | 23 | o `0` chega a comparacao e o resultado muda, com efeito descrito; **nao exercitado**: nao se sabe se a tela passa por esse caminho com 0 |
| IMPROVAVEL | 22 | familia do carne: a conjuncao e falsa nas duas versoes por outros termos (leitura do fluxo, nao execucao) |
| BENIGNO | 2 | o resultado final e o mesmo |

## O que fazer

- **Corrigir ja, sem esperar teste:** `cai3_gerfinanc013.php:339,574` (`strlen($x) != ''` e sempre verdadeiro no 8.x; trocar por `> 0`) e `forms/db_frmtarefa.php:976,992`.
- **Corrigir com a intencao em maos (PLAUSIVEL):** trocar a comparacao frouxa por uma explicita (`=== ''`, `> 0`, `!== null`). Os efeitos visiveis (relatorio PDF com '-' que passa a mostrar 0, mensagem 'Minimo de 0 caracteres', campo que deixa de ser desabilitado) estao descritos por linha.
- **Nao mexer:** a familia do carne e os BENIGNOS.

## Defeitos do detector achados nesta conferencia (corrigidos, com teste)

Alem dos tres da rodada anterior, a conferencia dos 32 restantes achou mais tres, que tiraram **4 pontos** da lista (57 -> 53):

- **`case` diferente do mesmo `switch`:** `libs/db_stdlib.php:1510` comparava `$aux` no `case "date"` com a atribuicao `$aux = 0` do `case "float"`. Cada `case` agora e um ramo exclusivo (fallthrough nao e tratado).
- **Reatribuicao nao numerica:** `pro4_geralayout.php:554,567` faziam `$v = $v * 100; $v = str_pad($v, 8, '0')`: o `str_pad` anula a evidencia. Agora uma atribuicao nao numerica que sempre executa antes anula as anteriores.
- **Calculo sobre data:** `edu4_exportarsituacaoaluno001.php:261` tinha `date('Y') - 1`, que nao e 0.

## Limites

- A classificacao e **leitura do codigo**, nao execucao: so `ate1_tarefa004.php` foi rodada. O banco de teste nao tem debitos nem dados escolares/de RH suficientes para exercitar as demais telas sem semear dados, o que alteraria o banco da bateria.
- `PLAUSIVEL` quer dizer que o efeito e real **se** a variavel chegar ao ponto com `0`; nao prova que chega.
- Variantes do carne: conferi nas 5 que o `dtvenc` e carregado por `db_fieldsmemory` antes do teste da parcela unica. Nao conferi dados reais.
