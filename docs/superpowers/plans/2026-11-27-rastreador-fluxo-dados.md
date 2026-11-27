# Rastreador de fluxo de dados (fase 1, abordagem A) - plano de implementacao

> **Para quem executa:** use superpowers:executing-plans (ou subagent-driven-development). Passos com `- [ ]`.

**Meta:** instrumentar o `ecidade/` inteiro com sondas, rodar a mesma requisicao no PHP 7.4 e no 8.5 e apontar a primeira linha em que o dado diverge e nao reconverge.

**Arquitetura:** instrumentador PHP (`nikic/php-parser` v4.19.1, emenda de bytes) + `rt.php` (execucao) rodando nos contêineres; Executor, alinhador, classificador, relatorio e CLI em Python dentro de `regressao/rastro/`.

**Stack:** PHP 7.4/8.5 (contêineres `ecidade74_php74`, `ecidade74_php85`), Python 3 + pytest (`regressao/.venv`), `php-parser` ja em `ecidade/vendor/nikic/php-parser`.

**Especificacao:** `docs/superpowers/specs/2026-11-27-rastreador-fluxo-dados-design.md` (secoes 4, 6, 7.1).

## Restricoes globais

- Branch de trabalho: `regressao-php74` (worktree `~/wt74doc`). Commits sem trailer de co-autoria; sem push sem pedido; o autor dos commits e o do git local (KauaBAG).
- Nunca editar `ecidade/` (o codigo do e-Cidade). Saida instrumentada vai para `ecidade/tmp/ecidade-rastro/` (git-ignored, dentro do volume que os dois contêineres ja montam).
- Os dois PHP rodam os **mesmos arquivos**: `arquivo:linha` e a chave de alinhamento.
- Sondas **nao alteram** a numeracao de linhas, nem os bytes fora delas (ISO-8859-1 preservado). Cada sonda e delimitada por `/*R*/` ... `/*R*/` para que um teste a remova e recupere o original byte a byte.
- Nao tocar no projeto Evolution (Docker, porta 8080). Nao ligar monitor.
- Nada de `git add -A`: adicionar caminhos.
- Scripts shell vao em arquivo e rodam por `wsl -d Ubuntu-24.04 -- bash <arquivo>`; processos longos com `setsid nohup ... & disown`.

## Revisao (casos que a especificacao implica e nenhuma tarefa isolada cobre)

1. **Laco com contagem diferente** nos dois lados: o alinhador nao pode descalibrar o resto; alinhar por (sonda, n-esima ocorrencia). Teste na tarefa 7.
2. **Aviso no 7.4 x excecao no 8.5 na mesma linha**: e a divergencia causal mais comum; tem que aparecer como tal. Teste na tarefa 7 e caso real na 8.
3. **Arquivo que nao parseia / codigo dinamico** (`extract`, `$$x`, `eval`): nao pode quebrar a instrumentacao; fica sem sonda e registrado. Teste na tarefa 2.
4. **Rastro truncado** (teto de eventos, `exit`, fatal): o relatorio diz "truncado" e nao conclui "reconvergente". Testes nas tarefas 3 e 7.
5. **Ruido do proprio 7.4** (data/hora, ids): divergencia que tambem aparece entre duas execucoes do 7.4 nao e culpa da migracao. Teste na tarefa 7.

---

### Tarefa 1: Verificar o parser e medir a taxa de parse da arvore

**Arquivos:**
- Criar: `regressao/rastro/__init__.py`, `regressao/rastro/php/parse_todos.php`, `regressao/rastro/parse.py`
- Teste: `regressao/tests/test_rastro_parse.py`
- Saida: `regressao/baseline/rastro-parse-2026-11-27.md`

**Interfaces:**
- Produz: `regressao.rastro.parse.roda_parse(arquivos: list[str]) -> dict` com `{"ok": int, "falhas": [{"arquivo": str, "msg": str}]}` (usa `docker exec ecidade74_php85 php parse_todos.php`, lista por stdin como `arvore._falhas`).
- Consome: `regressao.php.arvore.lista_arvore(excluir=set(), diretorio=Path)`.

- [ ] **Passo 1: teste** `test_parse_arquivo_valido_e_invalido`: com `_docker` simulado devolvendo a saida do script, `roda_parse` devolve `ok == 1` e `falhas == [{"arquivo": "ruim.php", ...}]`.
- [ ] **Passo 2:** implementar `parse_todos.php`: carrega `/var/www/html/vendor/autoload.php`, `(new ParserFactory)->create(ParserFactory::PREFER_PHP7)`, le cada caminho de stdin, imprime `OK\t<arq>` ou `FALHA\t<arq>\t<msg>`. Implementar `parse.py` espelhando `arvore._falhas`.
- [ ] **Passo 3:** rodar de verdade nos ~36.7k arquivos; gravar em `regressao/baseline/rastro-parse-2026-11-27.md` taxa de parse, lista das falhas e tempo.
- [ ] **Passo 4:** conferir que o parser v4.19.1 roda no 8.5 sem erro fatal; se houver, registrar e ajustar (instalar versao compativel via `composer` em diretorio proprio).
- [ ] **Passo 5: commit.**

### Tarefa 2: Instrumentador (nucleo)

**Arquivos:**
- Criar: `regressao/rastro/php/instrumentador.php`, `regressao/rastro/php/sondas.php` (visitor), `regressao/tests/fixtures/rastro/*.php`
- Teste: `regressao/tests/test_rastro_instrumentador.py`

**Interfaces:**
- Produz: CLI `php instrumentador.php --raiz=<dir> --saida=<dir> --versao=<n>`, caminhos relativos em stdin; para cada arquivo imprime uma linha JSON `{"arquivo":..,"status":"ok|sem_parse","sondas":N}` e grava `<saida>/<arquivo>` e `<saida>/<arquivo>.map.json` (`{"id": {"linha":N,"tipo":"atrib|chamada|ramo|retorno|excecao","nome":..,"le":[vars]}}`).
- Sondas (funcoes de `rt.php`): `__rt_a($id,'var',$var)` apos atribuicao a variavel simples/propriedade; `__rt_c($id,'funcao',[args-simples],<chamada>)` em volta de chamadas das funcoes de `regressao/rastro/funcoes.txt` (devolve o proprio valor da chamada, sem avaliar nada duas vezes); `__rt_b($id,'ramo')` no inicio de cada ramo de `if`/`else`/`switch case`/`?:`; `__rt_r($id,<expr>)` em volta de `return`; `__rt_x($id,$e)` no inicio de `catch`.
- Cada sonda e escrita `/*R*/...;/*R*/` na **mesma linha** do ponto de insercao (nunca quebra de linha).

- [ ] **Passo 1: testes** (Python, rodam o instrumentador no 8.5 via `docker exec`; pulam se o docker nao estiver ativo): `test_remover_sondas_devolve_o_arquivo_original_byte_a_byte` (cada fixture, inclusive uma em ISO-8859-1 com acento); `test_numero_de_linhas_nao_muda`; `test_arquivo_instrumentado_passa_em_lint_74_e_85`; `test_arquivo_que_nao_parseia_fica_sem_sonda_e_e_registrado` (`status == "sem_parse"`, saida identica ao original); `test_codigo_dinamico_nao_quebra` (fixture com `extract`, `$$x`, `eval`); `test_chamada_nao_e_avaliada_duas_vezes` (funcao com efeito colateral; resultado igual ao original); `test_if_sem_chaves_e_com_chaves`.
- [ ] **Passo 2:** implementar usando `startFilePos`/`endFilePos` do `php-parser` para **emendar texto** no original (nunca `PrettyPrinter`). Ramos com sintaxe alternativa (`if: endif`) ficam sem sonda de ramo e entram no `.map.json` como `nao_instrumentado`.
- [ ] **Passo 3:** testes passando. **Passo 4: commit.**

### Tarefa 3: Biblioteca de execucao `rt.php`

**Arquivos:**
- Criar: `regressao/rastro/php/rt.php`
- Teste: `regressao/tests/test_rastro_rt.py`

**Interfaces:**
- Produz as funcoes `__rt_a/__rt_c/__rt_b/__rt_r/__rt_x` (assinaturas da tarefa 2). O cabecalho `X-Rastro-Id` define o arquivo `/tmp/rastro/<id>.jsonl`; sem o cabecalho nada e gravado.
- Evento: `{"s":seq,"p":id_sonda,"f":arquivo,"l":linha,"k":"a|c|b|r|x|w|e|t","n":nome,"v":{"t":tipo,"r":repr(<=300 bytes, UTF-8),"h":md5 do valor completo}}`. `k:"w"` = aviso/notice/deprecated capturado por `set_error_handler` **encadeado** (chama o handler anterior); `k:"e"` = excecao nao tratada ou erro fatal (`register_shutdown_function` + `error_get_last`); `k:"t"` = truncado.
- Resumo de valores: escalares por valor; string longa truncada + hash; array por forma + hash (ordem de chaves preservada); objeto por classe + hash das propriedades; `resource` por tipo (`pgsql result`), nunca pelo numero.
- Flush progressivo a cada 500 eventos e no shutdown; teto de 2.000.000 eventos, ao atingir grava `k:"t"`.

- [ ] **Passo 1: testes** (rodam `php` no contêiner com um script que usa o `rt.php`): `test_evento_de_atribuicao_tem_tipo_repr_e_hash`; `test_resource_nao_vaza_o_numero`; `test_aviso_do_php_vira_evento_w_com_arquivo_e_linha`; `test_handler_anterior_continua_sendo_chamado`; `test_excecao_nao_tratada_vira_evento_e_nao_perde_o_rastro_ja_gravado`; `test_exit_no_meio_preserva_o_flush`; `test_teto_gera_marca_de_truncado`; `test_mesmo_script_gera_rastro_igual_em_74_e_85` (valores escalares/arrays).
- [ ] **Passo 2:** implementar; compativel com 7.4 e 8.5 (sem tipos de propriedade, sem `match`, sem `never`). **Passo 3:** testes passando. **Passo 4: commit.**

### Tarefa 4: Instrumentar a arvore inteira, com cache

**Arquivos:**
- Criar: `regressao/rastro/instrumenta.py`, `regressao/rastro/funcoes.txt`
- Teste: `regressao/tests/test_rastro_instrumenta.py`

**Interfaces:**
- Produz: `instrumenta_arvore(raiz: Path, saida: Path, forcar: bool = False, versao: int = VERSAO) -> Resumo` com `Resumo(total:int, reprocessados:int, ignorados_cache:int, sem_parse:list[str], removidos:int, falhas_lint:list[str])`. Manifesto `<saida>/manifesto.json`: `{arquivo: {"sha256": str, "versao": int}}`.
- Consome: `arvore.lista_arvore`, `instrumentador.php` (em lotes, em paralelo), `arvore._falhas` para o `php -l` nos dois PHP.
- Copia para `saida` todo arquivo **nao** `.php` da arvore (e os `.php` excluidos, como `vendor/`), para a arvore instrumentada funcionar sozinha (links simbolicos preservados).

- [ ] **Passo 1: testes** (instrumentador simulado): `test_primeira_execucao_instrumenta_tudo`; `test_segunda_execucao_sem_mudanca_reprocessa_zero`; `test_arquivo_alterado_e_o_unico_reprocessado`; `test_mudar_a_versao_do_instrumentador_reprocessa_tudo`; `test_arquivo_removido_some_da_saida_e_do_manifesto`; `test_nao_instrumenta_vendor_tmp_node_modules`.
- [ ] **Passo 2:** implementar; paralelismo por `ThreadPool` sobre lotes de 200 arquivos; `php -l` de todos os gerados nos dois PHP, falhas em `falhas_lint`.
- [ ] **Passo 3:** rodar na arvore real (em segundo plano); registrar tempo, `sem_parse` e `falhas_lint` em `regressao/baseline/rastro-arvore-2026-11-27.md`. Meta: `falhas_lint == []`.
- [ ] **Passo 4:** repetir a execucao e confirmar `reprocessados == 0`. **Passo 5: commit.**

### Tarefa 5: Servir a arvore instrumentada

**Arquivos:**
- Criar: `regressao/rastro/servidor.py`, `regressao/rastro/php/vhost-rastro.conf`
- Teste: `regressao/tests/test_rastro_servidor.py`

**Interfaces:**
- Produz: `liga_vhost(container: str) -> None` (idempotente; escreve o vhost `Listen 8091`, `DocumentRoot /var/www/html/tmp/ecidade-rastro`, `php_value auto_prepend_file /var/www/html/tmp/ecidade-rastro/rt.php`, habilita e recarrega o Apache) e `url_rastro(container) -> str` = `http://localhost:8091`. O vhost normal nao muda. Sem publicar porta no host: as requisicoes sao `curl` por `docker exec`, como `telas._requisita_status`.

- [ ] **Passo 1: teste** `test_liga_vhost_e_idempotente` (docker simulado: a segunda chamada nao reescreve nem recarrega). **Passo 2:** implementar para os dois contêineres.
- [ ] **Passo 3 (aceite real):** `cad2_setor002.php` servida em `:8091` pelos dois contêineres devolve a **mesma resposta normalizada** que a servida em `:80`. Se a arvore copiada quebrar por caminho absoluto, corrigir a copia (nao o e-Cidade) e registrar.
- [ ] **Passo 4: commit.**

### Tarefa 6: Executor e portao de equivalencia

**Arquivos:**
- Criar: `regressao/rastro/executor.py`, `regressao/rastro/equivalencia.py`
- Teste: `regressao/tests/test_rastro_executor.py`

**Interfaces:**
- Produz: `roda_requisicao(sid: str, tela: str, id_rastro: str, container: str, instrumentado: bool = True) -> Execucao` com `Execucao(status:int, corpo:bytes, rastro:list[str])` (linhas do `.jsonl` lidas por `docker exec cat`; envia `-H "X-Rastro-Id: <id>"`; restaura a sessao antes, como `telas.busca_corpo`, usando **backup de sessao proprio** `/tmp/_sess_rastro.bak`, nunca o `/tmp/_sess.bak` da bateria).
- Produz: `confere_equivalencia(sid: str, telas: list[str]) -> list[str]` -> telas em que o 7.4 instrumentado difere do 7.4 sem instrumentacao (resposta normalizada com `nucleo.normaliza.normaliza` + codigo HTTP). Lista vazia = portao aprovado.
- Login de sessao propria: `telas.login_http()`.

- [ ] **Passo 1: testes** (docker simulado): `test_envia_cabecalho_e_le_o_rastro`; `test_usa_backup_de_sessao_proprio`; `test_equivalencia_aponta_a_tela_que_difere`.
- [ ] **Passo 2:** implementar. **Passo 3 (aceite real):** `confere_equivalencia` em amostra de 200 telas (aleatoria, semente fixa, de todas as areas); lista vazia. Falha aqui bloqueia as tarefas seguintes: corrigir o instrumentador.
- [ ] **Passo 4: commit.**

### Tarefa 7: Alinhador e classificador (Python puro)

**Arquivos:**
- Criar: `regressao/rastro/evento.py`, `regressao/rastro/alinha.py`, `regressao/rastro/classifica.py`
- Teste: `regressao/tests/test_rastro_alinha.py`, `regressao/tests/test_rastro_classifica.py`

**Interfaces:**
- `Evento(seq:int, sonda:int, arquivo:str, linha:int, tipo:str, nome:str, valor:dict|None)` e `le_rastro(linhas: list[str]) -> list[Evento]`.
- `alinha(ref: list[Evento], alvo: list[Evento]) -> list[Divergencia]`, `Divergencia(sonda:int, ocorrencia:int, arquivo:str, linha:int, nome:str, valor_ref:dict|None, valor_alvo:dict|None, motivo:str)`; `motivo` em `{"valor", "so_ref", "so_alvo", "aviso_x_excecao"}`. Alinha por (sonda, n-esima ocorrencia).
- `classifica(ref: list[Evento], alvo: list[Evento], ref2: list[Evento], resp_ref: tuple[int,bytes], resp_alvo: tuple[int,bytes]) -> Resultado` com `Resultado(veredito: "IDENTICO|DIVERGE-RECONVERGENTE|DIVERGE-CAUSAL|INCONCLUSIVO", causal: Divergencia|None, cadeia: list[Evento], reconvergentes: list[Divergencia], ruido: list[Divergencia], truncado: bool)`. `ref2` e a segunda execucao do 7.4: divergencias que ja existem entre `ref` e `ref2` vao para `ruido` e nao contam. Resposta final igual = `normaliza` + codigo HTTP.
- Cadeia causal: a partir da causal, seguir **para tras** os eventos de atribuicao cujas variaveis aparecem em `le` da sonda causal (mesmo arquivo/escopo, por nome).

- [ ] **Passo 1: testes** (rastros sinteticos): `test_rastros_iguais_dao_identico`; `test_divergencia_que_reconverge_com_resposta_igual`; `test_divergencia_com_resposta_diferente_e_causal_e_aponta_a_primeira_que_nao_reconverge`; `test_aviso_no_ref_e_excecao_no_alvo_na_mesma_linha_e_causal` (motivo `aviso_x_excecao`); `test_laco_com_mais_iteracoes_nao_desalinha_o_resto`; `test_divergencia_presente_tambem_entre_ref_e_ref2_e_ruido`; `test_rastro_truncado_nunca_e_reconvergente` (veredito `INCONCLUSIVO`); `test_cadeia_causal_segue_as_variaveis_lidas`.
- [ ] **Passo 2:** implementar. **Passo 3:** testes passando. **Passo 4: commit.**

### Tarefa 8: Relatorio, CLI e casos reais

**Arquivos:**
- Criar: `regressao/rastro/relatorio.py`, `regressao/rastro/__main__.py`, `regressao/rastro/README.md`
- Teste: `regressao/tests/test_rastro_relatorio.py`, `regressao/tests/test_rastro_casos_reais.py` (usa docker)

**Interfaces:**
- CLI: `python -m regressao.rastro instrumenta [--forcar]`; `python -m regressao.rastro equivalencia --amostra N`; `python -m regressao.rastro rastreia <tela>... [--saida DIR]`; `python -m regressao.rastro rastreia --de-rodada <dir_da_rodada> --area <area>` (le as telas `DIVERGE` do `resultado.json`).
- `escreve_relatorio(resultados: dict[str, Resultado], destino: Path) -> Path` -> `relatorio.md` (veredito por tela; linha causal `arquivo:linha`, variavel, valor 7.4 e 8.5; cadeia; avisos exclusivos de um lado; reconvergentes em secao propria) e `rastro/<tela>/{ref74.jsonl,ref74_2.jsonl,alvo85.jsonl}`.

- [ ] **Passo 1: testes** de formato (resultados sinteticos): causal aparece com `arquivo:linha`; reconvergente em secao separada; truncado aparece como `INCONCLUSIVO`.
- [ ] **Passo 2:** implementar CLI e relatorio.
- [ ] **Passo 3 (casos reais):** `rastreia cad2_setor002.php` aponta o `pg_num_rows` sobre `false`; uma tela de PDF aponta `fpdf151/pdf.php:186`; `con2_anexo_i_2014.php` aponta `std/DBDate.php:203`. Gravar os tres relatorios em `regressao/baseline/rastro-casos-2026-11-27.md`.
- [ ] **Passo 4:** fixture sintetica em que a divergencia some e a resposta e igual vira `DIVERGE-RECONVERGENTE`.
- [ ] **Passo 5:** `README.md` curto (como instrumentar, como rastrear, limites: banco fora da v1, codigo dinamico). **Passo 6: commit.**

---

## Auto-revisao

- **Cobertura da especificacao:** criterio 1 = tarefa 6; 2 = tarefa 4; 3 = tarefa 8; 4 = tarefas 7 e 8; 5 = tarefa 4. Cache por hash = tarefa 4; avisos = tarefas 3 e 7; sondas na mesma linha = tarefa 2; rastro truncado = tarefas 3 e 7.
- **Fora desta fase:** B (Xdebug) e C (analise estatica), estado do banco, Laravel.
