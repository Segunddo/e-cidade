# Rastreador de fluxo de dados entre versoes do PHP

Acompanha o dado do inicio ao fim de uma requisicao no PHP 7.4 (referencia) e no PHP 8.5 (alvo) e diz **em que linha o dado
se separou**. A bateria (`regressao/php/bateria.py`) diz *qual tela* diverge; o rastreador diz *onde* e *por que*.

Especificacao: `docs/superpowers/specs/2026-11-27-rastreador-fluxo-dados-design.md`. Plano: `docs/superpowers/plans/2026-11-27-rastreador-fluxo-dados.md`.

## Regra de decisao

- Divergiu no meio, mas o **resultado final e igual** nos dois lados: **correto** (`DIVERGE-RECONVERGENTE`, so informativo).
- Divergiu e o **resultado final difere**: **defeito** (`DIVERGE-CAUSAL`). O relatorio aponta a *primeira divergencia que nao
  reconverge* (`arquivo:linha`, variavel, valor no 7.4 e no 8.5) e a cadeia de atribuicoes que levou ao valor errado.
- Rastro truncado, ou resposta diferente com rastro igual (a diferenca esta em codigo sem sonda): `INCONCLUSIVO`, nunca aprovado.

## Como usar

```bash
cd regressao
# 1) instrumenta ecidade/ inteiro (copia em ecidade/tmp/ecidade-rastro/) e liga o vhost 8091 nos dois contêineres.
#    A primeira vez leva ~6 min (36.7k arquivos); as seguintes reprocessam SO o que mudou (cache por hash, ~3 s sem mudancas).
python -m regressao.rastro instrumenta
# 2) portao de equivalencia: a arvore instrumentada responde IGUAL a normal? (sem isso o rastro nao vale nada)
python -m regressao.rastro equivalencia --amostra 200
# 3) rastreia telas (ou as DIVERGE de uma rodada da bateria)
python -m regressao.rastro rastreia cad2_setor002.php con2_anexo_i_2014.php --saida rastro-saida
python -m regressao.rastro rastreia --de-rodada ~/rodadas/base85b --area patrimonial --saida rastro-patrimonial

# Tudo num comando: instrumenta (incremental) + sondas + Xdebug + cruzamento, nas telas DIVERGE de TODAS as areas da rodada
python -m regressao.rastro analisa --de-rodada ~/rodadas/base85b --saida analise-base85b
#   -> analise-base85b/{sondas,xdebug}/relatorio.md e analise-base85b/cruzamento/cruzamento.{md,tsv}
```

Saida: `<saida>/relatorio.md` e `<saida>/rastro/<tela>/{ref74,ref74_2,alvo85}.jsonl`.

Rodada de 2026-11-28 (182 telas DIVERGE, os dois backends): **163 com a mesma linha causal**; as discordancias estao explicadas em
`regressao/baseline/rastro-linhas-todas-2026-11-28.md`. Cada tela tem limite de 300 s (`LIMITE_POR_TELA`): se estourar vira `INCONCLUSIVO` e a corrida segue.

## Dois backends (mesmo classificador e relatorio)

| | `--backend sondas` (padrao) | `--backend xdebug` |
|---|---|---|
| Como | arvore instrumentada na porta 8091 | trace do Xdebug no codigo original (porta 80) |
| Reinstrumentar | so o que mudou (cache por hash); mudar o instrumentador reprocessa tudo | **nunca** |
| Condicoes, variaveis lidas, aviso do 7.4 | sim | nao (cadeia por proximidade) |
| Custo fora do rastreio | zero | zero (a extensao e descarregada ao terminar) |

No teste com as 179 telas DIVERGE da base85b o B apontou **a mesma linha causal que o A em 146 de 146** telas com excecao
(`regressao/baseline/rastro-xdebug-2026-11-27.md`). O Xdebug e instalado e ligado/desligado sozinho pelo comando (`rastro/xdebug.py`).

## Como funciona (backend de sondas)

1. **Instrumentador** (`php/instrumentador.php`, `nikic/php-parser`): reescreve cada `.php` por **emenda de bytes** (nunca reimprime),
   inserindo sondas na mesma linha, entre marcadores ` /*R*/ ... /*R*/` (remover os marcadores devolve o original byte a byte).
   Sondas: depois de atribuicao a variavel simples, em volta de chamadas de funcoes listadas em `funcoes.txt`, em volta de condicoes
   (`if`/`elseif`/`while`/`do`/ternario: registra o ramo escolhido), em volta de `return` e no inicio de `catch`.
   O mapa de cada arquivo (`linha`, `tipo`, `nome`, variaveis lidas) fica em `tmp/ecidade-rastro-mapas/<arq>.json`, **fora** da arvore.
2. **`rt.php`** (carregado por `auto_prepend_file` so no vhost 8091): grava `/tmp/rastro/<id>.jsonl` quando a requisicao traz
   `X-Rastro-Id`. Registra tambem avisos/notices (encadeando o handler de erros da aplicacao, so para os tipos da mascara dela)
   e erros fatais. Fica **fora** da arvore (`tmp/rastro-rt.php`).
3. **Executor** (`executor.py`): login proprio, backup de sessao proprio por SID, requisicao nos dois contêineres; le tambem as linhas
   novas do log da aplicacao (`extension/log/error.log`), onde ficam as excecoes que o e-Cidade trata sozinho ("Erro interno").
4. **Alinhador e classificador** (`alinha.py`, `classifica.py`): alinham por (sonda, n-esima ocorrencia); o que ja difere entre duas
   execucoes do 7.4 e ruido; aviso so no 7.4 + excecao so no 8.5 na mesma linha e uma divergencia (`aviso_x_excecao`).

## Limites conhecidos (v1)

- **Estado do banco fora do escopo:** "resultado final igual" = codigo HTTP + resposta normalizada. Uma tela que grave dado diferente
  mas mostre a mesma resposta nao e detectada.
- **Codigo dinamico** (`extract`, `$$x`, `eval`): variaveis criadas assim nao tem sonda. **Atribuicoes a propriedades e a posicoes de
  array** (`$o->p = ...`, `$a[] = ...`) tambem nao: so variaveis simples. **Ramos sem chaves** nao tem sonda de atribuicao (o comando
  nao fica numa lista de comandos); a condicao que os governa e a sonda de ramo.
- **Cadeia causal** por nome de variavel dentro do mesmo arquivo; nao e analise de fluxo de dados (fase 3).
- **Resumo de valor** limitado a 300 bytes (+ hash); divergencia so alem disso pode vir de ruido (data) e e filtrada pela segunda
  execucao do 7.4.
- Excecoes tratadas pelo e-Cidade so aparecem se o log da aplicacao as registrar.
- Laravel (`lar12`) nao e coberto.

## Achados do proprio desenvolvimento

- Divisao sem espaco antes de uma chamada instrumentada (`$a/count($b)`) virava `//*R*/`, comentario de linha. Por isso o marcador
  comeca com um espaco.
- O handler de erros do e-Cidade e registrado com a mascara `php.error_reporting` (`E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED
  & ~E_STRICT` = 22517) e tem assinatura `_handle($type, $message, $file, $line, $context)`: o PHP 8 nao passa mais `$context`
  (so 4 argumentos), entao qualquer erro dentro da mascara chegando a ele no 8.5 e `ArgumentCountError`. Em execucao normal quase
  nao dispara; fica registrado como risco latente em `src/V3/Error/Handler/Error.php:20`.
- A tela `pre1_leis001.php` confere o modo (0754) dos arquivos de `bin/`: a copia instrumentada precisa preservar modo e nao ter
  arquivos a mais nos diretorios. O portao de equivalencia achou isso.
- **Fase C (analise estatica):** `python -m regressao.rastro estatica [--modo candidatos|comparacoes]` le o codigo sem executar nada. `candidatos` = usos de resultado de consulta sem checagem (`false` vira TypeError no 8.x); `comparacoes` = `==`/`!=`/switch com literal (`0 == 't'` mudou no 8.x). Resultados em `baseline/rastro-estatica-*.md` e `baseline/rastro-comparacoes-*.md`.
- **A raiz do codigo e o que o contêiner monta, nao onde o pacote esta.** `T.DIR_TELAS` e `<pacote>/ecidade`; rodando de um worktree isso e um snapshot
  diferente do `/var/www/html` servido (no caso: 11.692 arquivos com conteudo diferente e 29 a mais). O teste de existencia do cache olhava a outra
  arvore, entao `instrumenta` reprocessava tudo (6 min) em vez de 3 s, e os hashes podiam dar por atual um arquivo que mudou. `raiz.py` resolve a raiz pelo
  ponto de montagem (`docker inspect`). Se voce rodar a ferramenta de outro lugar, confira `python -c "from regressao.rastro.raiz import raiz_montada; print(raiz_montada())"`.
- **`extension/log` e link de diretorio inteiro**, nao arquivo a arquivo: a aplicacao cria `error.log` em execucao; num diretorio real da arvore
  instrumentada (criado pelo root, sem permissao para o `www-data`) o Logger do e-Cidade lanca excecao e a resposta vira 500 sem corpo. O portao de
  equivalencia pegou (37 de 40 telas diferentes). `liga.php` troca um diretorio real que so tem links pelo link do diretorio.
- Erros do PHP vao para `/var/log/php_errors.log`, nao para `/var/log/apache2/error.log` (que e um stream: `tail` nele trava).
- O backend Xdebug pode apontar como causa uma chamada interna que aparece so num dos traces (`substr` em `libs/db_stdlib.php:818` no caso `ate1_tarefa004.php`); nas telas sem excecao confira a linha antes de agir.
