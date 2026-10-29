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

## ⏱ ESTADO ATUAL — leia primeiro ao retomar

**Onde paramos:** **ÁREAS TRIBUTÁRIO, EDUCAÇÃO, RECURSOS HUMANOS E PATRIMONIAL CONCLUÍDAS** — Patrimonial com
**743/743 telas de menu no 8.5** conferidas pelo proxy (branch `4patrimonial-migrado`, 29/10/2026; ver `area-patrimonial.md`).
RH com 701/701 (branch `3recursoshumanos-migrado`; cálculo da folha verificado; 13ª lacuna fechada).
Conferido pelo proxy, tela de menu por tela de menu (15/10/2026): **Tributário 1.059/1.059** e **Educação
480/480** arquivos de menu existentes servidos pelo PHP 8.5 — depois de fechar a *10ª LACUNA* (14 telas
que o `map` não roteava). Ver *🏁 ÁREA EDUCAÇÃO CONCLUÍDA*.
**Comparação com o TCC de referência FEITA** — ver *⚖️ COMPARAÇÃO MEDIDA COM O TCC DE REFERÊNCIA*. Portados e roteados `tre`, `esc`, `rel`, `sec`, `bib`, `mer` (+ 20 telas `mat`/`pro` por
`map`) `edu3_` + variantes `edu0x_`/`edu_`, `edu2_`, `edu4_` e os 4 sublotes do `edu1_` — todo o prefixo `edu` (1.211 arquivos). Ver *ÁREA EDUCAÇÃO*.

| | |
|---|---|
| Módulos portados | **16 de 16** — todos com 100% das telas de menu servidas pelo PHP 8.5 |
| Também portado | `tra` — órfão no menu, sem uso prático |
| Núcleo (24 arq.) | portado, com guardas `pg_*` acrescentadas conforme os defeitos aparecem |
| Bibliotecas | **`dbagata/` portado** (211 arquivos executáveis, 213 construtores) — ver seção própria |
| Rota no nginx | `location ~* ^(?:/w/[0-9]+)?/(?:cem\|itbi?\|agua?\|jur\|div\|mar\|not\|fis\|iss\|dvr\|arr\|tri\|inf\|tra\|tre\|esc\|rel\|sec\|bib\|mer\|edu\|rh\|eso\|rec\|pes\|ac\|aco\|ouv\|lic\|vei\|pat\|com\|cus\|pla\|pl\|tes\|emp)[0-9]*_)` — **6.632 arquivos** + 811 por `map` (582 telas de menu + 229 abas e destinos da 14ª lacuna, `faseb_map_abas.txt`) |
| **Próximo passo** | **Área FINANCEIRO dimensionada e dividida em 6 lotes** (branch `5financeiro-migrado`; ver `area-financeiro.md`). **Lotes 1 e 2 (`emp`) concluídos; aguardando o usuário pedir o lote 3 (`orc`)** — um lote por vez. |
| **php.ini do 8.5** | `docker/php85-apache/paridade-56.ini`, montado pelo compose: **`output_buffering = 4096`**, igual ao 5.6. Ver *CATEGORIA NOVA: AMBIENTE*. |
| **Dívida técnica aberta** | `fpdf151/` da raiz (28 arquivos, ver *6ª LACUNA*). O `dbagata/` **saiu da lista**. |
| Frentes de enumeração | **nove** — a 8ª (classes de `model/`/`std/`, 13ª lacuna) e a 9ª (classes com namespace em `src/`/`app/`/`api/` e serviços do `bootstrap.php`, **15ª lacuna**, `scratchpad/ns_fecho.py`); todas insensíveis a maiúsculas desde a 9ª lacuna (`getdao`) |
| **Instrumento do passo 4** | **MUDOU: Rector** (`scratchpad/rector-curado.php` + 2 regras próprias) substituiu o `porta.py` a partir do `iss`. Ver *DECISÃO: Rector adotado*. |

**Como subir o ambiente** (a ordem importa — 8.5 e proxy dependem da rede criada pelo 5.6):

```bash
docker volume create ecidade_sessions && docker volume create ecidade_tmp
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d
docker exec ecidade_php56 chmod 1777 /tmp      # o volume nasce root:root 755
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

**Pendências conhecidas:** todas as divergências de `cem`, `itb` e `agu` estão caracterizadas
(ver as seções de cada módulo). As que restam são de três tipos, nenhum deles defeito de
migração: telas que quebram **no 5.6** e funcionam no 8.5 (defeito pré-existente da
referência), fragmentos de include que não são telas, e relatórios que falham **igualmente**
nos dois runtimes por `tmp/` não ser gravável. A dívida real aberta é `dbagata/`.

**Fora de escopo até aqui:** Laravel continua 5.4 (não roda em PHP 8, por isso o login fica
no runtime 5.6) e PostgreSQL continua 16 em LATIN1. São as Fases 1-3 do workflow.

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
| Arquivo | `docker-compose.yml` (**não alterar**) | `docker-compose.php85.yml` |
| Imagem | `docker/php56-apache` | `docker/php85-apache` |
| PHP | 5.6 | **8.5.10** |
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
| `area-financeiro.md` | Financeiro (em andamento, branch `5financeiro-migrado`): módulos, prefixos, divisão em lotes e as decisões do usuário (`cai` inteiro, `con` só pelas telas) |
| `dimensionamento.md` | dimensionamento das áreas restantes (13/10, 18/10 e 22/10) |
| `trabalho-relacionado.md` | monografia do TCC de referência, análise dos commits e a comparação medida sobre o mesmo universo |
| `catalogo-e-metodo.md` | `while read`, `modification()`, LSP e `=& new`, `php -l` na base inteira, experimento do Rector, cobertura dos caminhos de escrita (níveis 1–3), decisões de porte, bugs latentes |
| `laravel.md` | login bloqueado, dimensionamento, migração em paralelo com `vendor/` próprio, Tributário × API, token do Passport |
| `ambiente.md` | uids, ferramental versionado, php.ini de paridade, armadilhas de ferramental, permissões do `storage/`, proxy reverso, `/tmp` e sessão compartilhados, comandos úteis |

Referências cruzadas antigas do tipo "ver *Seção X*" continuam valendo: a seção existe com o mesmo
título num desses arquivos (`grep -rn "Seção X" docs/registro/`).
