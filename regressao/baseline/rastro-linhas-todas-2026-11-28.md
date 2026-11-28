# Rastreador - linha causal nas 182 telas DIVERGE, pelos dois backends (2026-11-28)

Rodada `base85b`, as 182 telas DIVERGE (uniao das 11 areas), rastreadas pelos **dois backends** e cruzadas com `python -m regressao.rastro cruza`:

- **A - sondas por linha:** a arvore inteira instrumentada (36.712 arquivos; incremental, so reprocessa o que mudou: 3,5 s sem mudancas) e o portao de equivalencia (a arvore instrumentada responde igual a normal) em **0 diferencas em 60 telas**. 619 s para as 182 telas.
- **B - Xdebug, sem instrumentar nada:** trace + a analise estatica da fase C para a cadeia por dependencia de dados. ~24 min para as 182 telas.

## Concordancia

| Resultado | Telas |
|---|---|
| mesma-linha | 163 |
| mesmo-arquivo | 2 |
| arquivo-diferente | 12 |
| so-B | 3 |
| so-A | 0 |
| sem-causa | 2 |

**163 de 182 telas (90%) com a MESMA linha causal** pelos dois caminhos independentes (165 se contar o mesmo arquivo). Vereditos de A: {'DIVERGE-CAUSAL': 177, 'INCONCLUSIVO': 4, 'DIVERGE-RECONVERGENTE': 1}. Vereditos de B: {'DIVERGE-CAUSAL': 180, 'INCONCLUSIVO': 1, 'DIVERGE-RECONVERGENTE': 1}.

Onde os dois concordam a confianca na linha e alta. A lista por tela esta em `rastro-linhas-concordancia-2026-11-28.tsv` (colunas: tela, veredito e causa de A, veredito e causa de B, concordancia).

## Onde discordam (e por que)

- **14 telas em que B aponta `libs/db_stdlib.php`** (linhas 815-832): e **ruido de inicializacao do trace do Xdebug**, nao a causa. Duas fontes, ambas medidas: (1) o Xdebug do 8.5 nao registra `substr`/`strpos`/`strrpos` (funcoes sem frame desde o PHP 8.4); (2) a mesma atribuicao de varias linhas e registrada na ULTIMA linha pelo 7.4 e na PRIMEIRA pelo 8.5; (3) restou uma diferenca de **contagem** de ocorrencia em `db_verfPostGet` (`$tam_vetor`), nao de valor. Os dois primeiros filtros estao no codigo (`xdebug.SEM_FRAME_NO_85`, `artefato_sem_frame`); o terceiro nao foi tratado. **Nessas telas use a linha de A.**
- **`ate1_tarefa004.php`:** a causa real (confirmada a mao) e `forms/db_frmtarefa.php:976,992` (`0 == 't'`). **Nenhum dos dois backends a aponta**: A escolhe `ate1_tarefa004.php:346` (aviso `Undefined variable $tipo`, so no 8.5: um aviso verdadeiro, mas que nao explica a diferenca na resposta) e B o ruido de `db_stdlib`. Uma **comparacao que muda de resultado nao deixa divergencia no rastro** quando os dois lados seguem o mesmo ramo ate a saida: so o detector estatico de comparacao frouxa (`rastro-comparacoes-*`) a acha. Os dois instrumentos sao complementares, nao substitutos.
- **`sys4_processa008.php` e `sys4_verifica002.php`:** A fica INCONCLUSIVO (rastro truncado no teto de 300 mil eventos: laco longo); B conclui `:100` de cada uma.
- **`pes2_osocontramatricial002.php`:** a resposta difere so porque a pagina imprime `$HTTP_USER_AGENT`: `curl/7.81.0` num contêiner e `curl/8.14.1` no outro. **E artefato do ambiente, nao defeito de PHP**: a tela deveria sair da lista de DIVERGE.
- **`con4_docpadrao010.php`:** inconclusivo nos dois por motivos diferentes: A estourou o teto de eventos (laco longo) e B passou de 300 s.
- **`sys4_indices001.php`:** reconvergente nos dois (correto: divergiu no meio e o resultado final e igual).

## O que isso entrega ao objetivo

- **A nivel de linha:** o backend A instrumenta o codigo inteiro uma vez e depois so reprocessa o que mudou.
- **Data flow sem instrumentar linha a linha:** o backend B (Xdebug) mais a analise estatica de variaveis lidas por linha; concorda com A em 90% das telas e as discordancias sao conhecidas e documentadas acima.
- **Os dois se cobrem:** A acha o que B perde por artefato do trace; B conclui onde A estoura o teto de eventos.

## Limites

- Os resultados valem para a **arvore montada nos contêineres em 2026-11-28** (`raiz_montada()`), com 11.692 arquivos diferentes do snapshot do worktree.
- 'Mesma linha' prova que os dois caminhos concordam, nao que a linha seja o defeito: a regra e a **primeira divergencia que nao reconverge**.
- Uma tela passou do limite de 300 s no B e ficou INCONCLUSIVO com o motivo (o laco segue).
