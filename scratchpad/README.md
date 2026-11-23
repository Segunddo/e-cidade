# Ferramentas da migração (`scratchpad/`)

Scripts e harnesses usados para migrar o e-cidade do PHP 5.6 para o 8.5, na ordem em que entram no trabalho de um lote.
O **como usar** de cada passo está no guia (`docs/migrar-um-modulo.md`); aqui está **o que cada arquivo faz, como faz e
o que ele altera**. Cada arquivo também traz, no topo, um cabeçalho com uso, entradas e saídas.

> **Na `base-php74`** (18/11/2026): a referência é o **PHP 7.4** (`ecidade_php74`, porta 8080), no papel que era
> do 5.6 — as mensagens dos scripts já dizem 7.4 (`NO_7.4` no `redirecionamentos.py`). O `cmp.py` e o
> `escrita_post.py` ficam como na base (o `cmp.py` marca a referência com `56=`) para não conflitar com a
> versão da `regressao-php74`, que o PR #30 traz (marca `ref=` e lê portas do `regressao/nucleo/ambiente.py`);
> o `verifica_lote.py` funciona com as duas, e ele, o `nivel3.py` e o `demo_nivel3.sh` apontam as variáveis
> `REGRESSAO_*` para a pilha da raiz (8080/8085). Onde
> este texto diz 5.6, leia 7.4. Adaptações feitas para esta base: o nome do
> container de referência; a leitura do `location` no `nginx.conf` considera só a linha **ativa** (o bloco nasce
> comentado, e sem linha ativa nada vai ao 8.5); o `rotear.py location` cria o bloco quando ele não existe; o
> `dimensiona.py` começa sem nenhuma área concluída, e as cópias `LOC` começam com o marcador `nenhum_prefixo_no_85`;
> o `gera_map_faseb.py` lê do `nginx.conf` os prefixos do `location` (era uma cópia à mão); o `faseb_map_abas.txt`
> começa vazio; o `NUCLEO` do `enumera.py`/`residuo.py` é vazio (o núcleo desta base não foi portado); o Rector usa
> 2 processos em paralelo (o padrão travou um notebook de 7,4 GB).
> **Exercitadas com o 7.4 em Docker em 19/11/2026:** os testes, `prefixos_area`, `dimensiona`, `nivel3 --candidatas`,
> `rotear` (simulação), `rector_lote soc` (simulação) e `verifica_lote` no `soc` não migrado (reprova, e cada passo
> bate com a conferência manual de *Como provar que o verificador funciona*). Os modos `--aplicar` ainda não.

Todos rodam **da raiz do repositório**. Os `.php` são *harnesses*: são copiados para dentro dos containers e rodados nos
**dois** runtimes (5.6 e 8.5), e o que se compara é a saída de um com a do outro.

A coluna **Altera** diz o que o script muda além de gravar em `ecidade/tmp/`: **nada** (só lê e mede), **código**
(arquivos de `ecidade/`), **banco** (grava e restaura), **proxy** (`nginx.conf`, `faseb_map.conf`) ou **sessão** (o arquivo de
sessão de login usado nos testes).

## Comandos de um passo inteiro

| Arquivo | O que faz | Como faz | Passo | Altera |
| --- | --- | --- | --- | --- |
| `rector_lote.py` | o passo 4 em um comando | junta os alvos, copia a config e as regras para o container, confere a sintaxe da config, simula (`--dry-run`) e classifica cada regra (conhecida, ressalva, nova); com `--aplicar`, aplica e repete até uma rodada alterar 0 arquivos, e recusa se houver regra nova | 4 | código (só com `--aplicar`) |
| `verifica_lote.py` | os passos 4b, 5, 5b, 6, 6b, 6c e 7 de uma vez, com relatório único | roda cada harness nos dois containers sobre a mesma lista, compara, conta entradas e saídas, filtra os artefatos conhecidos e diagnostica cada tela divergente; `--tudo` faz a bateria completa do fim da área | 4b–7 | nada |
| `nivel3.py` | o nível 3 (POST real) em um comando | `--candidatas` lista as telas de inclusão pelo critério do guia; o teste liga o log de SQL (e sempre o desliga), gera o payload, roda o `escrita_post.py` e confere pelo `pg_stat_user_tables` se outra tabela foi escrita, inclusive por gatilho | nível 3 | banco (grava e restaura) |
| `rotear.py` | os passos 8 e 8b em um comando | modos `location`, `map`, `abas` (mostram antes; com `--aplicar` gravam, testam o `nginx -t` num container descartável, recriam o proxy e conferem o runtime das telas) e `8b` (levantamento) | 8, 8b | proxy (só com `--aplicar`) |

## Enumerar e dimensionar (antes do porte)

| Arquivo | O que faz | Como faz | Passo | Altera |
| --- | --- | --- | --- | --- |
| `dimensiona.py` | mede as áreas ainda não migradas | consulta o menu no banco, classifica cada tela (fantasma, já no 8.5, faltando) e roda o `enumera.py` por área | fluxo da área, B | nada |
| `prefixos_area.py` | diz quais prefixos uma área precisa migrar e se vão por `location` ou `map` | cruza o menu da área no banco com o `nginx.conf` e o `faseb_map.conf`, agrupando por prefixo | fluxo da área, B | nada |
| `enumera.py` | monta o universo de um lote e a lista de arquivos a alterar | parte das telas do prefixo (ou de `TELAS=`) e fecha pelas nove frentes (include, `new cl_*`, `getDao`, `model/`/`std/`, namespace); conta as categorias que quebram no PHP 8 | 1–3 | nada |
| `ns_fecho.py` | 9ª frente: classes com namespace em `src/`, `app/` e `api/` | acha nomes por `use`, nome qualificado e serviços do `bootstrap.php` e os resolve pelo mapa PSR-4, até não aparecer arquivo novo | 1–3 (dentro do `enumera.py`) | nada |
| `residuo.py` | mede o resíduo de cada módulo para escolher o próximo | fecho de cada tela e classificação de cada dependência (paga, exclusiva, compartilhada com módulo não portado) | escolha do próximo módulo | nada |
| `conta_tokens.php` | conta, pelo tokenizer, só no código (nunca em comentário ou string), as construções que não sobrevivem ao PHP 8 | tokeniza cada arquivo e conta `split`/`ereg`/`each`, `parse_str` de 1 argumento, construtor PHP 4 e `0 == ""` sem guarda | medições pontuais | nada (só roda no 8.5) |

## Portar (passo 4)

| Arquivo | O que faz | Como faz | Passo | Altera |
| --- | --- | --- | --- | --- |
| `rector-curado.php` | a configuração do Rector | lê os alvos de `ALVOS`, fixa a versão em PHP 8.0, carrega as duas regras próprias e veta 40 regras, cada uma com o motivo | 4 | código (quando o Rector roda) |
| `rector-rules/GuardaComparacaoLiteralRector.php` | regra própria: a guarda do `0 == ""` | troca `$this->X == "literal"` (X iniciada com inteiro) por `($this->X === 0 \|\| $this->X === 0.0 \|\| $this->X == "")` | 4 | código |
| `rector-rules/ParseStrComExtractRector.php` | regra própria: `parse_str` de 1 argumento | troca `parse_str($s);` por `parse_str($s, $__qs); extract($__qs);`, reaproveitando o nó para não perder comentários | 4 | código |
| `porta.py` | o passo 4 antigo, por regex sobre bytes (substituído pelo Rector desde o `iss`) | troca `split`, completa o `parse_str`, renomeia construtores PHP 4 e aplica a guarda; só relata `each`, `ereg`, offset `{}` e `=& new` | referência | código |

## Verificar (passos 5 a 7)

| Arquivo | O que faz | Como faz | Passo | Altera |
| --- | --- | --- | --- | --- |
| `carrega_arquivo.php` | carrega um arquivo com o bootstrap, para pegar assinatura incompatível entre classe mãe e filha (LSP) | inclui o bootstrap e o arquivo; uma função de shutdown relata o fatal | 5b | nada |
| `instancia_classes.php` | instancia cada classe e imprime uma assinatura do estado inicial | `new X()` sem argumentos e md5 das propriedades; o diff entre runtimes mostra construtor que não rodou | 6 | nada |
| `escrita.php` | exercita o `atualizacampos()` com um formulário simulado | preenche `HTTP_POST_VARS` com `1000`, `1001`… e imprime o que cada campo leu; mostra a guarda `0 == ""` faltando | 6b | nada |
| `porclasse.sh` | roda um harness com uma classe por processo | grava cada linha num arquivo e chama o php com `</dev/null`; um fatal derruba só aquela classe; `#TOTAL` no stderr | 6, 6b | nada |
| `harness_robusto.sh` | roda o `instancia_classes.php` pulando a classe que derruba o processo | conta as linhas de saída para achar a culpada e recomeça da seguinte (só serve para harness de uma linha por entrada) | 6 (forma antiga) | nada |
| `negada_alvos.py` | acha as ocorrências de `$this->X != ""` sem guarda | regex sobre bytes em `classes/`, anotando o método, o modo do `atualizacampos()` e se é auditoria ou negócio | 6c | nada |
| `negada.php` | mede se `campo != ""` decide igual nos dois runtimes | com o formulário vazio, instancia, chama o `atualizacampos()` no modo anotado e avalia a comparação | 6c | nada |
| `negada_compara.py` | compara as saídas do `negada.php` e dá o veredito do lote | indexa por (classe, campo, método), classifica as diferenças e separa o lote do resto | 6c | nada |
| `negada_corrige.py` | aplica a guarda da forma negada nos pontos da lista | localiza o método e troca só a forma sem guarda | 6c (correção) | código |
| `cmp.py` | a bateria de telas: compara cada tela entre 5.6 e 8.5 | restaura a sessão antes de cada pedido, normaliza o que muda a cada pedido, compara status e corpo e repete o par antes de acusar | 7 | sessão |
| `guarda_ciclo.py` | corrige, uma linha por vez, `pg_*` recebendo `false` | pede a tela ao 8.5, lê o fatal do `error.log` e envolve só aquela linha em `($r ? pg_xxx(...) : null)`; repete | 7 (correção) | código |
| `campo_ciclo.py` | o mesmo, para `pg_result` com coluna inexistente e `pg_free_result(false)` | mesmo ciclo, outros padrões | 7 (correção) | código |
| `const_ciclo.py` | o mesmo, para constante indefinida | troca por `(defined('X') ? X : 'X')`, o que o 5.6 devolvia | correção pontual (Educação) | código |

## Nível 3 (POST real)

| Arquivo | O que faz | Como faz | Passo | Altera |
| --- | --- | --- | --- | --- |
| `escrita_post.py` | faz o POST nos dois runtimes e compara o SQL de escrita de negócio | fotografa as tabelas e sequências, posta no 5.6, restaura, posta no 8.5, restaura, e compara os `INSERT`/`UPDATE`/`DELETE` lidos do log do PostgreSQL (sem a auditoria) | nível 3 | banco (grava e restaura) |
| `payload.py` | mostra o formulário da tela, para montar o payload à mão | GET da tela no 5.6 e extração dos campos e botões | nível 3 | sessão |
| `payload_auto.py` | gera uma primeira tentativa de payload | o mesmo GET, com valores por heurística sobre o nome do campo | nível 3 | sessão |
| `demo_nivel3.sh` | demonstração do nível 3 (IDÊNTICO, DIVERGE com a guarda desfeita, IDÊNTICO) | roda o `payload_auto.py` e o `escrita_post.py`; na 2ª rodada edita uma classe e a devolve pelo git | demonstração | banco e código (devolvidos no fim) |
| `n3_rh_payloads.tsv` | dados: os payloads montados à mão para as telas de cadastro do RH em que o payload automático não grava | uma linha por tela: tela, tabelas a restaurar (filha antes da mãe) e payload | nível 3 do RH | — |

## Roteamento (passos 8 e 8b)

| Arquivo | O que faz | Como faz | Passo | Altera |
| --- | --- | --- | --- | --- |
| `gera_map_faseb.py` | gera o `docker/proxy/faseb_map.conf` (roteamento por lista) | exporta do banco as telas de cada área, soma o `faseb_map_abas.txt`, descarta o que não existe em disco e reescreve o arquivo inteiro | 8 | proxy |
| `redirecionamentos.py` | acha telas no 8.5 que, ao abrir, mandam a uma tela servida pelo 5.6 | GET de cada tela de menu no 8.5 e procura de redirecionamento e `iframe`; classifica cada destino | 8b | sessão |

## Investigação pontual

| Arquivo | O que faz | Usado em |
| --- | --- | --- |
| `teste_phar.php` | testa o `PHPExcel.phar` (carrega as classes e gera um XLS para comparar o md5 entre os runtimes) | 12ª lacuna, RH |
| `valida_token.php` | confere se um token do Passport antigo é aceito pelo `league/oauth2-server` novo | migração do Laravel |

## Conferência manual do verificador

Caminhos **independentes** do `verifica_lote.py`, para conferir o resultado dele em vez de confiar no veredito
(documento *Como provar que o verificador funciona*). Nenhum altera nada.

| Arquivo | O que faz | Confere o passo |
| --- | --- | --- |
| `e1_lsp.py` | lê o código (sem executar) e lista as heranças que carregam no 7.4 e dão fatal no 8.5; resolve a mãe pelo namespace e pelos `use` | 5b |
| `carga_isolada.php` | carrega um arquivo num PHP de verdade sem o bootstrap da aplicação (autoload do `vendor/` + mapa de classes), em contêiner descartável | confere o `e1_lsp.py` |
| `e1_mapa.py` | gera o mapa classe → arquivo que o `carga_isolada.php` usa | confere o `e1_lsp.py` |
| `sem_guarda.sh` | lista os campos com valor inicial numérico comparados com `""` sem a guarda `=== 0` | 6b |
| `e1_cobertura.py` | compara as classes que a regressão do grupo testa com as que o universo do `enumera.py` alcança | cobertura |

## Defeitos conhecidos nestes scripts

Levantados na revisão de 17/11/2026, que acrescentou os comentários. **Ainda não corrigidos**: a revisão mudou só
comentários.

| Arquivo | Defeito | Efeito |
| --- | --- | --- |
| `redirecionamentos.py`, `payload_auto.py`, `demo_nivel3.sh` | restauram a sessão de um `.bak` que eles mesmos não criam | se o `.bak` for de outra sessão, sobrescreve a sessão atual |
| `demo_nivel3.sh` | acha a sessão com `sess_*` em vez de `sess_?*` | pode pegar o arquivo `sess_` vazio |
| `escrita_post.py` | ABORTADO sai com o mesmo código de DIVERGE; nele, as tabelas `_n3snap_*` ficam no banco; payload com `'` quebra o comando | resultado ambíguo e resíduo no banco |
| `guarda_ciclo.py`, `campo_ciclo.py`, `const_ciclo.py` | a troca vale para **todas** as ocorrências da linha, não só a do fatal | pode guardar mais que o necessário |
| `gera_map_faseb.py` | não confere se o `psql` funcionou | pode reaproveitar sem aviso uma exportação antiga |
| `residuo.py` | usa só as frentes antigas de enumeração | mede um universo menor que o do `enumera.py` |
| `enumera.py` | imprime "universo (6 frentes)", mas percorre nove | só o rótulo está errado |

**Corrigidos em 18/11/2026** (cada um com um teste em `testes/` que falhava antes da correção e passa depois):

| Arquivo | Defeito | Teste |
| --- | --- | --- |
| `verifica_lote.py` | no passo 7, o `if sumiram:` e o `else:` estavam presos ao `if tout_56:`: as conhecidas que voltaram a ficar idênticas só apareciam com timeout no 5.6, e com a lista carregada o relatório podia dizer "sem lista de conhecidas" | `testes/test_verifica_relatorio.py` |
| `rotear.py` | o modo `abas` gravava o `faseb_map_abas.txt` antes de guardar a cópia de segurança: se o `nginx -t` falhasse, ou com "Nada a mudar"/"RECUSADO" sob `--aplicar`, a lista ficava alterada | `testes/test_rotear_abas.py` |
| `rotear.py` | na `base-php74` o `faseb_map.conf` nasce sem o comando do gerador: o modo `map` recusava o primeiro lote, e o `abas` parava deixando a lista alterada. Agora o primeiro `map` começa do zero e o `abas` recusa antes de mexer em qualquer arquivo | `testes/test_rotear_abas.py` (caso 0) |

**Corrigidos em 19/11/2026**, achados ao testar com o 7.4 em Docker:

| Arquivo | Defeito | Como foi conferido |
| --- | --- | --- |
| `docker/proxy/faseb_map_abas.txt` | ainda tinha as 365 abas da `base-php84`: o primeiro `rotear.py map` mandaria ao 8.5 ~360 telas não migradas | `rotear.py map assist:rec,pro`: de 366 entradas para as 4 da área |
| `gera_map_faseb.py` | a lista de prefixos do `location` era uma cópia à mão da `base-php84`: telas `rec`, `cai`, `pes`... nunca entravam no `map` | agora lê o `nginx.conf`; com o da `base-php84` reproduz a lista antiga exatamente |
| `enumera.py`, `residuo.py` | o `NUCLEO` marcava 21 arquivos como já portados, mas na `base-php74` o núcleo não foi portado | coluna "Pago" do `dimensiona.py` vai a 0; o `soc` ganha 5 alvos |
| `rector-curado.php` | o Rector abria um processo por núcleo (até 1,2 GB cada) e travou um notebook de 7,4 GB | `rector_lote.py soc` com 2 processos: no máximo ~470 MB no contêiner |
| `verifica_lote.py` | o artefato `datausu` do `empenho.php` descartava a **classe inteira** e escondia o construtor PHP 4 dela (`sCamposNota` vazio no 8.5) | a conferência manual do passo 6 dava 16 classes e o script 15; com o filtro só na linha do `datausu`, 16 |

## Testes (`testes/`)

Rodam sem Docker e sem banco, sobre cópias temporárias e com dublês no lugar do que é externo; nada real é alterado.

```bash
python3 scratchpad/testes/test_verifica_relatorio.py     # relatório do passo 7: conhecidas x novas
python3 scratchpad/testes/test_verifica_cmp_compat.py    # verifica_lote com o cmp.py da base e o da regressao-php74
python3 scratchpad/testes/test_rotear_abas.py            # rotear.py abas: a lista nunca fica alterada sem aplicar
```

Cada um imprime `OK` (código 0) ou para num `AssertionError` que diz o que quebrou.

## Como conferir que um arquivo mudou só nos comentários

A revisão que acrescentou os comentários foi conferida mecanicamente, comparando cada arquivo com a versão anterior
**sem os comentários**: a árvore sintática no Python (`ast`), os *tokens* do PHP (`token_get_all`) e as linhas sem
comentário no shell. Os 35 arquivos deram iguais, o que prova que nenhuma linha de código mudou. Também foram conferidos
a codificação e os finais de linha (sem mudança) e o `php -l` de cada `.php` antes e depois, nos dois runtimes (o mesmo
resultado). Os `.php` que não compilam no 5.6 (`conta_tokens.php`, `rector-curado.php`, as duas `rector-rules/` e
`valida_token.php`) são ferramentas feitas só para o PHP 8, e já não compilavam antes.
