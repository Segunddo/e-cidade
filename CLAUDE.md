## Direcionamentos para o Claude

1. Pense antes de escrever o código

**Não faça suposições, não esconda dúvidas e diga os trade-offs**

Antes de implementar algo:
- Declare suas suposições explicitamente, se tiver alguma dúvida pergunte
- Se houver várias maneiras de fazer, mostre-as e não escolha em silêncio
- Se existir alguma abordagem mais simples, apresente-a. Questione quando for pertinente
- Se algo não estiver claro, pare, identifique o que está confuso e pergunte

2. Simplicidade em primeiro lugar

**O código mínimo para resolver o problema, nada de especulações**

- Sem funcionalidades além do que foi pedido
- Sem abstrações para código de uso único
- Sem "flexibilidade" ou "configurabilidade" não solicitadas
- Sem tratamento de erros para cenários impossíveis.
- Se você escrever 200 linhas e o código puder ter 50, reescreva-o.

Pergunte a si mesmo: "Um engenheiro sênior diria que isso está excessivamente complexo?" Se a resposta for sim, simplifique.

## 3. Alterações Cirúrgicas

**Toque apenas no que for necessário. Limpe apenas a bagunça que você mesmo criou.**

Ao editar código existente:
- Não tente "melhorar" código, comentários ou formatação adjacentes.
- Não refatore o que não está quebrado.
- Siga o estilo existente, mesmo que você o fizesse de outra forma.
- Se encontrar código morto não relacionado, mencione-o — não o exclua.

Quando suas alterações criarem elementos órfãos:
- Remova importações, variáveis ​​ou funções que se tornaram inúteis devido às SUAS alterações.
- Não remova código morto preexistente, a menos que solicitado.

O critério: Cada linha alterada deve estar diretamente ligada à solicitação do usuário.

## 4. Execução Orientada a Objetivos

**Defina critérios de sucesso. Itere até a verificação.**

Transforme tarefas em objetivos verificáveis:
- "Adicionar validação" → "Escrever testes para entradas inválidas e fazê-los passar"
- "Corrigir o bug" → "Escrever um teste que o reproduza e fazê-lo passar"
- "Refatorar X" → "Garantir que os testes passem antes e depois"

Para tarefas com múltiplas etapas, descreva um plano conciso:
```
1. [Etapa] → verificar: [critério]
2. [Etapa] → verificar: [critério]
3. [Etapa] → verificar: [critério]
```

## 5. Memória

Documente tudo que seja importante para a conclusão do projeto. Não deixe tópicos importantes
de fora. **Onde:** o registro detalhado (cada módulo, categoria, lacuna, medição) vai no arquivo
correspondente de `docs/registro/` (ver *Onde está cada coisa*, no fim deste arquivo); aqui ficam
só o estado atual, os princípios, o ambiente, as armadilhas operacionais e o índice. Este arquivo
tem limite de 150 mil caracteres — passou de 300 mil e foi dividido em 26/10/2026, sem perda de
conteúdo.

Critérios de sucesso sólidos permitem que você trabalhe de forma independente. Critérios vagos ("fazer funcionar") exigem esclarecimentos constantes.

# e-cidade — Projeto de Migração

> **⚠ MUDANÇA DE BASE (17/11/2026) — leia antes do resto.** A branch principal passou a ser a
> **`base-php74`**, criada do PR #8 da DBSeller (https://github.com/DBSeller/e-cidade/pull/8: PHP 7.4 +
> Laravel 8, com funcionalidades que a `base-php84` não tem). Motivo: pull requests à DBSeller precisam
> partir do código dela. O trabalho agora é **adaptar a `base-php74` até ela rodar no 8.5 como a
> `base-php84` já roda**, usando a `base-php84` como guia (`git diff origin/base-php74 origin/base-php84 -- <arquivos>`).
>
> - **O 7.4 faz o papel que era do 5.6:** é o runtime de referência (`ecidade_php74`, porta 8080) e o gabarito
>   das baterias. Onde este arquivo e os guias dizem `ecidade_php56`/5.6, leia `ecidade_php74`/7.4. Os
>   scripts de `scratchpad/`, o overlay de sessão e o proxy já foram trocados para o 7.4.
> - **O proxy começa sem nada no 8.5** (`docker/proxy/nginx.conf`, `faseb_map.conf`): cada módulo volta à
>   lista quando for adaptado na `base-php74`.
> - **Nem toda diferença entre as duas bases é para copiar:** o PR #8 traz funcionalidade nova da DBSeller.
> - O estado, os números e as medições abaixo são **da `base-php84`** e ficam como histórico e guia.

## ⏱ ESTADO ATUAL — leia primeiro ao retomar

**Onde paramos (18/11/2026): na `base-php74`, NENHUM módulo foi adaptado ao PHP 8.5 ainda.** O código em `ecidade/`
é o 7.4 da DBSeller (PR #8), e o proxy manda **tudo** ao 7.4. A migração das áreas precisa ser **refeita** sobre esta
base. O que a `base-php84` concluiu (as 7 áreas, 16 de 16 módulos) **não vale aqui**: é histórico e guia (ver abaixo).

| | |
|---|---|
| Base | `base-php74` = PR #8 da DBSeller (PHP 7.4 + Laravel 8) + ferramentas e documentação trazidas da `base-php84` (PR #12, 17/11/2026) |
| Módulos adaptados ao 8.5 nesta base | **0 de 16** |
| Rota no nginx | **nenhuma**: o bloco do `location` está comentado e o `faseb_map.conf` está vazio; tudo vai ao `ecidade_php74` |
| Referência (gabarito) | o **PHP 7.4** (`ecidade_php74`, porta 8080), no papel que era do 5.6 |
| Tamanho do trabalho (medido em 16/11/2026 no código do PR #8, com os detectores do `enumera.py`) | **11.726 arquivos a alterar**. Por categoria: guarda `0 == ""` **22.954** ocorrências (intacta: no 7.4 ainda funciona); `parse_str` de 1 argumento **7.645**; `each(` 85; construtor PHP 4 **252** (o PR #8 já tinha resolvido 3.528 de 3.780); `split(` **368** em 86 arquivos |
| Atenção | os **86 arquivos que ainda chamam `split()`** quebram no **próprio 7.4** (a função não existe desde o PHP 7.0): divergências que aparecerem neles são do gabarito, não da migração (ex.: `classes/db_disciplina_classe.php:441`) |
| Ferramentas | `scratchpad/` (lista e o que cada uma altera: `scratchpad/README.md`); ainda **não exercitadas** com o 7.4 em Docker |
| **Próximo passo** | subir 7.4 + 8.5 + proxy e validar as ferramentas no 7.4; depois dimensionar as áreas nesta base (`scratchpad/dimensiona.py`, `prefixos_area.py`) e refazer a migração por área e lote, como no guia (`docs/migrar-um-modulo.md`) — um lote por vez |
| **php.ini do 8.5** | `docker/php85-apache/paridade-56.ini`, montado pelo compose: **`output_buffering = 4096`**, igual à referência. Ver *CATEGORIA NOVA: AMBIENTE*. |
| Frentes de enumeração | **nove** — a 8ª (classes de `model/`/`std/`, 13ª lacuna) e a 9ª (classes com namespace em `src/`/`app/`/`api/` e serviços do `bootstrap.php`, **15ª lacuna**, `scratchpad/ns_fecho.py`); todas insensíveis a maiúsculas desde a 9ª lacuna (`getdao`) |
| **Instrumento do passo 4** | **Rector** (`scratchpad/rector-curado.php` + 2 regras próprias; em um comando: `scratchpad/rector_lote.py`). Ver *DECISÃO: Rector adotado*. |

**Histórico: o que a `base-php84` concluiu (até 03/11/2026).** Sobre o código antigo (PHP 5.6), as áreas Tributário,
Educação, Recursos Humanos, Patrimonial, Financeiro, Saúde e Configuração foram migradas — 16 de 16 módulos com 100% das
telas de menu servidas pelo 8.5, 9.344 arquivos pelo `location` e 1.312 pelo `map`. Os números de cada área, as lacunas
e as decisões estão em `docs/registro/` e valem como **guia**: o que deu certo, as categorias de defeito e as correções
que reproduzem o comportamento antigo. O estado completo daquela base: `git show origin/base-php84:CLAUDE.md`.

**Como subir o ambiente** (a ordem importa — 8.5 e proxy dependem da rede criada pelo 7.4):

```bash
docker volume create ecidade_sessions && docker volume create ecidade_tmp
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d
docker exec ecidade_php74 chmod 1777 /tmp      # o volume nasce root:root 755
chmod -R 777 ecidade/storage ecidade/bootstrap/cache 2>/dev/null; chmod 777 ecidade/extension/log   # SEM && : o -R falha em cache do container e abortaria o resto
chmod 666 ecidade/extension/log/*.log   # os ARQUIVOS, nao so a pasta -- senao TODA tela autenticada da 500
chmod 777 ecidade/tmp ecidade/arquivos        # SEM isto, 11% das telas falham antes de executar
docker compose -f docker-compose.php85.yml up -d
docker compose -f docker-compose.proxy.yml up -d
```

**Use `http://localhost:8090`** (origem única). Login `dbseller`/`dbseller`. O cabeçalho
`X-Ecidade-Runtime` em cada resposta diz qual runtime a serviu.

**Para migrar o próximo módulo:** invocar a skill **`migrar-modulo`**
(`.claude/skills/migrar-modulo/SKILL.md`) — ela traz o procedimento executável com os
comandos, as verificações e as armadilhas. Este arquivo continua sendo o catálogo e o
*porquê*; a skill é o *como*. A receita de 9 passos também está resumida na seção
*ESTRATÉGIA ADOTADA*.

**Regime de permissões (MUDOU):** `tmp/` e `arquivos/` agora são **777**. Antes eram 775 e
nenhum container conseguia escrever, o que fazia **11% das telas da área falharem antes de
executar** — e aparecerem como "idênticas" nas baterias por falharem igual. Toda medição
anterior a esta mudança carrega esse ponto cego; as posteriores, não.

**Fora de escopo até aqui:** o Laravel do PR #8 é o **8** (a `base-php84` tinha o 5.4) e o PostgreSQL continua 16 em
LATIN1. A migração do Laravel tem registro próprio (`docs/registro/laravel.md`, `docs/migrar-laravel.md`), escrito
sobre o 5.4: confira o que mudou antes de seguir.

## Princípios ao trabalhar neste repositório

- **Nunca aplicar transformação em massa sem teste de caracterização antes.** O e-cidade roda
  folha de pagamento, empenho contábil e tributos de prefeitura real. Regressão silenciosa em
  cálculo não é bug — é município que não paga servidor.
- **Medir antes de decidir.** Este arquivo só contém números verificados no código; manter assim.
- **O objetivo é MIGRAR, não consertar.** Bug pré-existente não se corrige: documenta-se e
  deixa-se como está. Quando o PHP 8 transforma em fatal algo que o 5.6 tolerava, a correção
  certa é a que **reproduz o comportamento do 5.6** — não a que conserta a intenção do autor.
  Exemplos já decididos assim: o `break` fora de laço do `fis` virou `exit` (o 5.6 morria ali)
  em vez de ser removido; o `"J"` passado como `$ln` ao FPDF foi contornado com `(float)$ln`
  em vez de corrigido na chamada; o `1969-12-31` do `db_vencimento()` foi preservado.
  **Critério:** se a alteração mudaria a saída do `:8080`, não é migração — é conserto, e fica
  de fora. Uma tela que quebra **igual nos dois** não é problema nosso; uma que quebra **só no
  8.5** é, e a correção tem de ser a mínima que restaure a paridade.
- O ambiente PHP 5.6 existente (`docker-compose.yml`) é a referência funcional — **não alterá-lo**.
  Ambientes novos entram em arquivos separados (ex.: `docker-compose.php85.yml`).

## Ambientes (dois runtimes em paralelo)

| | Referência | Migração |
|---|---|---|
| Arquivo | `docker-compose.yml` (**não alterar**; é o da DBSeller) | `docker-compose.php85.yml` |
| Imagem | `docker/php74-apache` (container `ecidade_php74`) | `docker/php85-apache` |
| PHP | 7.4 | **8.5.10** |
| URL | http://localhost:8080 | http://localhost:8085 |
| Banco | `ecidade_database` (PG 16 / LATIN1) | o **mesmo** `ecidade_database` |

O banco é compartilhado de propósito: mantém-se constante para que a única variável do
experimento seja a versão do PHP. Migrar PostgreSQL é a Fase 3, separada.

Extensões `interbase` e `xmlrpc` **não** foram instaladas (removidas do core do PHP em 7.4
e 8.0); as outras 15 exigidas pelo `composer.json` estão todas presentes.


## ⚠ Armadilhas operacionais — resumo (o detalhe está em `docs/registro/`)

Regras que valem em toda sessão. Cada uma custou um defeito ou um alarme falso; a história está no
arquivo indicado.

- **UM LOTE POR VEZ (pedido do usuário, 29/10/2026):** terminar o lote (porte, verificação, roteamento, registro,
  commit local), relatar e **ESPERAR o usuário pedir o próximo**. Não emendar um lote no outro, nem começar o
  primeiro lote de uma área nova sem o pedido. Vale também para correções que surgirem no meio: relatar e
  perguntar antes de abrir uma frente nova.
- **BATERIA COMPLETA SÓ NO FIM DA ÁREA (decisão do usuário, 29/10/2026):** em cada lote, a bateria **do próprio
  lote** sempre; se o lote mexer no núcleo (ou numa classe que quase tudo alcança), uma **bateria dirigida** às telas
  que chegam ao trecho alterado (como montar: skill, passo 7). A bateria **completa** (todos os prefixos do
  `location` + o `map` inteiro) roda **uma vez, no fim da área**, e o **envio ao GitHub só depois dela**: até lá os
  commits de lote ficam locais. Achando regressão no fim, `git bisect` entre os commits de lote. Motivo: todas as
  baterias completas desde o Tributário voltaram na linha de base, e cada uma já custa ~3 h.

- **Git:** nunca commitar `docker/database/ecidade_base.sql` (314 MB) nem encenar a remoção do `.gz`:
  `git add -A -- ':!docker/database/ecidade_base.sql' ':!docker/database/ecidade_base.sql.gz'`.
  Commit/push só quando o usuário pedir. Correções de área em branch própria, cadeia de merge
  `1tributario-migrado` → `2educacao-migrado` → `3recursoshumanos-migrado` (merge, não rebase).
- **Docker:** nunca `--remove-orphans` — apagaria 5.6, 8.5 e o banco, que **não tem volume de
  persistência**. O `nginx.conf` é bind mount de arquivo único: depois de editar,
  `up -d --force-recreate` (ver `ambiente.md`).
- **Encoding:** 64% da base é LATIN-1; `grep` sem `-a` pula esses arquivos em silêncio. Editar
  acentos em nível de byte (ver `contexto.md`).
- **Listas:** `php`/`docker exec` dentro de `while read` engolem a lista — usar `</dev/null`
  (ver `catalogo-e-metodo.md`). Lista sem `\n` final perde o último item.
- **Harnesses:** `scratchpad/` está fora do bind mount — copiar com `docker cp` (saída vazia nos
  dois lados parece aprovação). Um processo por classe (`porclasse.sh`). Opcache do 8.5 revalida a
  cada 2 s: esperar 3 s entre editar e requisitar.
- **Sessão para testes:** achar o SID com `ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_*)`
  e restaurá-la antes de cada requisição. O log do PostgreSQL é em **português** (`ERRO:`).
- **Nível 3:** `ALTER DATABASE ecidade SET log_statement='all'` antes, `RESET` depois; tabelas
  filhas antes da mãe; ABORTADO ou ATENCAO deixam linha de teste — limpar e repor sequências
  (ver `area-recursos-humanos.md` e `catalogo-e-metodo.md`).
- **Rector:** pin de versão obrigatório, repetir até zero, denylist reconferida a cada lote,
  `php -l` nos **dois** runtimes sobre o **universo**, portão de funções contra o 5.6 (ver
  *DECISÃO: Rector adotado* em `area-tributario.md`).
- **`extension/modification/`:** a cópia pode ou não ser a que executa — corrigir original **e**
  cópia (ver `catalogo-e-metodo.md` e `trabalho-relacionado.md`).
- **Testes automatizados não contatam serviço real de terceiros** (lista `PULAR` do `cmp.py`).
  Não exibir o segredo do cliente da API. Credenciais: `dbseller`/`dbseller`; postgres
  `postgres`/`postgres`; pgAdmin no IP do `ecidade_database` (o `.2` é o php56).

## 🗂 Onde está cada coisa

Guias (para pessoas): `docs/migrar-um-modulo.md`, `docs/como-testamos.md`, `docs/migrar-laravel.md`,
`docs/comparacao-tcc-referencia.md`. Procedimento executável: skill `migrar-modulo`.

Registro (o que antes ficava todo aqui), em `docs/registro/`:

| Arquivo | Conteúdo |
|---|---|
| `contexto.md` | reorganização `ecidade/`, contexto, stack, números da base, armadilha do `grep`, superfície de incompatibilidade (`0 == ""`, aritmética com string, construtores PHP 4), bloqueadores, strangler fig, mapa de módulos, grafo de dependências e piloto, workflow das fases, pontos levados ao orientador |
| `area-tributario.md` | estratégia por área, portar ≠ rotear, prefixos exclusivos × compartilhados, ordem, **receita de 9 passos e as sete frentes**; núcleo, pilotos `tra`/`cem`, cada módulo da Fase A e da Fase B com suas categorias novas, denylist do Rector, bateria proporcional, 3ª–10ª e 13ª lacunas, nível 3 em escala, `tmp/` 777, guardas `pg_*` |
| `area-educacao.md` | Educação: lotes, sublotes do `edu1`, 9ª e 11ª lacunas, conclusão |
| `area-recursos-humanos.md` | RH: lotes, `.phar` (12ª lacuna), nível 3 nos cadastros e estágio, cálculo da folha, 13ª lacuna; **14ª lacuna** (telas de menu que mandam ao 5.6, decisão: tratar na aparição) |
| `area-patrimonial.md` | Patrimonial (**concluída**, branch `4patrimonial-migrado`): dimensionamento por prefixo, lotes; **15ª lacuna** (classes com namespace em `src/`/`app/`, 9ª frente, correção pela cadeia de branches) |
| `area-financeiro.md` | Financeiro (**concluída**, branch `5financeiro-migrado`): módulos, prefixos, divisão em lotes e as decisões do usuário (`cai` inteiro, `con` só pelas telas) |
| `area-saude.md` | Saúde (**concluída**, branch `6saude-migrado`): módulos, prefixos, divisão em 7 lotes e as decisões do usuário |
| `area-configuracao.md` | Configuração (**concluída**, branch `7configuracao-migrado`): prefixos, divisão em 3 lotes e as decisões do usuário |
| `dimensionamento.md` | dimensionamento das áreas restantes (13/10, 18/10, 22/10, 29/10, 30/10, 01/11 e 03/11) |
| `trabalho-relacionado.md` | monografia do TCC de referência, análise dos commits e a comparação medida sobre o mesmo universo |
| `catalogo-e-metodo.md` | `while read`, `modification()`, LSP e `=& new`, `php -l` na base inteira, experimento do Rector, cobertura dos caminhos de escrita (níveis 1–3), decisões de porte, bugs latentes |
| `laravel.md` | login bloqueado, dimensionamento, migração em paralelo com `vendor/` próprio, Tributário × API, token do Passport, **pontos de contato telas × Laravel** (5 relatórios que sobem o kernel na página, 30 chamadas `/v4/`) |
| `estrutura-85.md` | PHP8-79: código só do PHP 8.5 sem tocar o 7.4: `ecidade/composer-85.json`/`.lock` (cópia do PR + sobreposição `app-85/` no PSR-4), `vendor/` em `runtime-85/` montado sobre `vendor/` só no 8.5, comando único pinado `docker/composer-85/composer-85.sh` (dono da trava: time do banco), os 10 pacotes que excluem o 8.5, regra e pergunta do lint do grupo |
| `php8-77-db-raw-storage.md` | PHP8-77: os 414 `DB::raw(` classificados (`php8-77-db-raw.tsv`, comando no registro); 23 quebram no Laravel 10+ (`DB::select`/`statement` com `DB::raw`, `selectRaw(implode)`) e foram ajustados tirando o `DB::raw` (SQL igual 7.4 x 8.5 pelo Grammar, sem banco); `Storage`/`Filesystem` iguais em pasta descartável, menos `delete` de inexistente (retorno ignorado) |
| `php8-77-storage-laravel13.md` | PHP8-77: Storage com os 4 discos do PR (`configuration/filesystems.php`) 7.4 (Flysystem 1) × 8.5 (Laravel 13, Flysystem 3) pelo `roda-isolado.sh`: 75 de 88 linhas iguais; as 13 que diferem (`get`/`copy`/`delete`/`deleteDirectory` em caso de falha, e o `s3` sem adaptador nos dois) o código não alcança |
| `php8-12-rotas-v4.md` | PHP8-12: as 1.454 rotas da base-php74 sem banco (`php8-12-rotas.tsv`, arquivo:linha): 1.425 vivas, 27 pares método+URI repetidos (vence a última no 8 e no 12+), nome `jobs.` que muda no 12+ (sem uso), 125 closures, 5 arquivos de `routes/` não carregados, 460 GET `/v4` que só leem para o lote 1 |
| `ambiente.md` | uids, ferramental versionado, php.ini de paridade, armadilhas de ferramental, permissões do `storage/`, proxy reverso, `/tmp` e sessão compartilhados, comandos úteis |
| `defeitos-laravel8-do-pr.md` | PHP8-49: defeitos do Laravel 8 do PR #8 já presentes no 7.4, medidos por trecho isolado sem banco: `Cache::put` com TTL em minutos (5 das 6 chamadas expiram em segundos), `array_pluck`/`str_random` sem `laravel/helpers` (2 chamadas), `env()` fora de `configuration/` (105 chamadas em 46 arquivos PHP), `DBFormRequest::response()` sem efeito (105 form requests), tela sem rota (`con4_manutencaoformulario001`), `AutenticacaoRequest` declarado em 2 arquivos a factory legada `ModelFactory.php` sem o pacote que a carrega e dois comandos do `artisan` que não funcionam (`schedule:list` com erro, `list --format=json` sem saída por 3 descrições em ISO-8859-1); cada contagem com o comando que a confere |
| `inventario-telas-v4.md` | PHP8-12: telas legadas, `scripts/` e front Vue que chamam `/v4`, sem banco: 1.428 rotas lidas (1.311 `/v4`, conferidas contra as 1.315 registradas pelo Laravel), 1.337 chamadas em 485 arquivos, 935 rotas com chamador firme, 282 sem chamador (limite superior, ~220 esperadas), 52 chamadas a rotas que não existem, 3 arquivos de rotas que ninguém carrega e a ordem sugerida dos lotes; dados em `inventario-v4-*.tsv` |
| `validacao-laravel8-7.4-x-8.5.md` | PHP8-94: validação do Laravel 8 do PR no 7.4 × 8.5 sem banco: inventário (289 declarações de form request, 0 `validated()`, 5 `only()`, 104 `validate()`), 1.350 casos de form request e 348 regra × valor iguais salvo `digits` com array (`TypeError` no 8.5), 49 `Deprecated` só no 8.5, 54 form requests com regra de banco (`.tsv`); comandos que conferem as contagens |
| `validacao-laravel13-x-7.4.md` | PHP8-94: a medição da validação repetida com o Laravel 13.43 no 8.5 contra o Laravel 8 do PR no 7.4, sem banco: matriz 348 de 348 iguais (o `TypeError` do `digits` com array some), 1.350 casos de form request com 23 diferenças em 3 causas (21 por chave de mensagem só de campo, resolvidas tirando as chaves de 6 `messages()` com o 7.4 idêntico; 2 só registradas: `after_or_equal` sem referência e `validated()`); `validacao-laravel13-diferencas.tsv` |
| `api-v1-levantamento.md` | PHP8-15: API V1 (Silex) no PR #8: o que o PR mudou (`FrontController.php`, `composer.json`, 1 linha em `api/`), as 7 rotas e quem as usa (1 consumidor interno já migrado, externos desconhecidos), as 3 opções (seguir o PR, container separado, perguntar à DBSeller) e o texto da pergunta |
| `passport13-leitura-e-plano.md` | PHP8-39: Passport 13 e `/v4/login` sobre o código do PR (Passport 10.4.2) só por leitura: 14 pontos com arquivo:linha (6 mudam, 3 a conferir, 5 compatíveis), esquema `oauth_*` do PR × migrations do 13, o que o medido na base antiga ainda vale e o plano das provas P0-P9 para quando houver banco |
| `email-notificacoes-74-x-85.md` | PHP8-51: e-mails e notificações do PR (2 Mailables, 4 Notifications, 12 pontos de chamada, configuração `driver=smtp`) renderizados com o mailer `array`, sem banco e sem envio: 7.4 × 8.5 idênticos com o Laravel 8.73.2 (76 depreciações no 8.5, 2 em código do PR), Laravel 13 igual salvo a ordem dos cabeçalhos; resultados em `email-notificacoes-resultados/` |
| `configuracao-de-erros-74-x-85.md` | PHP8-62: configuração efetiva de erros do PHP e do Laravel nas imagens do grupo (`php74-apache`, `php85-apache`), sem banco: `error_reporting`/`display_errors`/log por camada (imagem, tela legada, Laravel) e o efeito de Notice/Warning/Deprecated na resposta e no log; 7 diferenças 7.4 × 8.5 com causa (`E_USER_*` lança `ArgumentCountError` no tratador legado do 8.5, 110 entradas no `laravel.log` por requisição fria no 8.5, `.user.ini` ignorado pelo `mod_php`) |
| `documentos-74-x-85.md` | PHP8-70: documentos (dompdf, mPDF, PhpSpreadsheet, PhpWord, Pimaco, QR) gerados pelo código próprio sem banco, 7.4 × 8.5: 39 de 39 iguais (páginas, texto, posições, imagens, pixels), ajustes mínimos em `Parser.php` e nos 2 `EtiquetaModelo0xBuilder`, avisos que sobram no 8.5, comando que reproduz |
| `emails-74-x-85.md` | PHP8-51: e-mails do PR (2 `Mailable`, `toMail`, `Mail::raw`) no Laravel 8/SwiftMailer × Laravel 13/Symfony Mailer, sem enviar: 4 de 4 iguais em conteúdo, `configuration/mail.php` do PR lida pelo 13 (8 cenários), diferença do `tls` 587 (STARTTLS obrigatório × oportunista), comando que reproduz |
| `traducoes-74-x-85.md` | PHP8-94: traduções pt-BR do PR (auth, paginação, senhas, validação) no Laravel 8 × 13: 73 de 73 chaves iguais, 27 regras do PR iguais, diferenças só em regras que o PR não usa (`uuid`, `gt`…) e no assunto dos e-mails `ResetPassword`/`VerifyEmail`, comando que reproduz |

Referências cruzadas antigas do tipo "ver *Seção X*" continuam valendo: a seção existe com o mesmo
título num desses arquivos (`grep -rn "Seção X" docs/registro/`).

## Suíte de regressão e servidor MCP (base 7.4)

- **Suíte de regressão** (`regressao/`): compara a referência PHP 7.4/Laravel 8 com o PHP 8.5 (telas, POSTs,
  relatórios, rotas `/v4`, fluxos de navegador). Como usar, em português simples: `regressao/COMO-USAR.md`;
  detalhe técnico: `regressao/README.md`. Roda num ambiente próprio (projeto compose `e74`, contêineres
  `ecidade74_*`, portas 8074/8185/8190/8187), que não mexe na pilha da raiz (8080/8085/8090).
- **Servidor MCP** (`.mcp/`): regras do grupo, busca de padrões legados, validação no 7.4 e no 8.5, regressão e
  coordenação de quem mexe em qual arquivo, para qualquer IA. Instalação em 3 passos: `.mcp/README.md`.
- As regras do grupo (`CONTRIBUINDO.md`) valem igual para a suíte e o MCP: arquivo por arquivo no `git add`,
  ISO-8859-1, cada um na sua área. Um veredito INCONCLUSIVO ou ERRO_AMBIENTE da suíte nunca conta como aprovação.
