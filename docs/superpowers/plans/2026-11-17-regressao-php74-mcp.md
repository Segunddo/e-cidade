# Regressão sobre PHP 7.4 + servidor MCP — plano

> Para agentes: use superpowers:subagent-driven-development. Um implementador por tarefa, revisão por tarefa.

**Goal:** portar e adaptar a suíte `regressao/` à base PHP 7.4/Laravel 8 e criar o servidor MCP Python em `.mcp/`.
**Spec:** `docs/superpowers/specs/2026-11-17-regressao-php74-mcp-design.md`
**Fonte da suíte:** branch local `regressao` (repo `~/e-cidade`), diretório `regressao/` (502 testes) — copiar com
`git -C ~/e-cidade archive regressao regressao | tar -x -C ~/e-cidade-74` (NÃO trazer `.venv` nem `baseline.dump`).
Leia `regressao/README.md`, `regressao/baseline/triagem-divergencias.md`, `regressao/baseline/decisoes-migracao.md` e
`regressao/baseline/lab-lar12-resultado.md` da fonte para o contexto histórico (lá o gabarito era PHP 5.6/Laravel 5.4).

## Global Constraints
- Worktree `~/e-cidade-74`, branch `regressao-php74`; nunca `git add -A` (adicione caminhos); commits sem trailer
  Co-Authored-By; sem push; não imprimir e-mail/segredos/hash de senha.
- Não tocar nos contêineres existentes (`ecidade_*` e os de outro projeto local na porta 8080) nem parar/religar esse projeto. Novo ambiente = projeto
  compose `e74`, nomes `ecidade74_*`, portas: referência 7.4 :8074, PHP 8.5 :8185, proxy :8190, lab Laravel 12 :8187,
  banco sem porta publicada (ou 55432). Memória do host curta (15 GB; Docker já caiu): `sync; echo 3 > /proc/sys/vm/drop_caches`
  (root) antes de rodadas longas; rodadas longas DESTACADAS (`setsid nohup … < /dev/null &`).
- Use PowerShell + `wsl -d Ubuntu-24.04 -- bash` com scripts em arquivo (CRLF -> `tr -d '\r'`).
- Vereditos IDENTICO/DIVERGE/INCONCLUSIVO/ERRO_AMBIENTE; INCONCLUSIVO/ERRO_AMBIENTE nunca são aprovação; o gabarito é a 7.4.
- Texto de docs em português simples; `COMO-USAR.md` para quem não participou do projeto.

## Review Focus
1. Baseline Laravel gravada contra o Laravel 8 SEMPRE com a proteção `--confirmo-sobrescrever`/alvo de referência.
2. Nenhuma ferramenta MCP executa shell livre nem lê/escreve fora da raiz do repo; erros viram resposta estruturada.
3. stdout do MCP só carrega JSON-RPC.
4. Reivindicação de arquivos expira e não perde dados em corrida (escrita atômica do JSON).
5. Rodada "antes" não é aprovação de nada: relatório diz o que não foi exercitado.

### Task 1: Ambiente 7.4 isolado + portar a suíte
- Copie `regressao/` da fonte; crie `regressao/lab/docker-compose.e74.yml` (projeto `e74`; serviços: banco a partir de
  `docker/database/Dockerfile` da base 7.4 com dump `docker/ecidade_base.sql.gz`; php74 :8074 a partir de
  `docker/php74-apache`; php85 :8185 (reutilize/construa a imagem PHP 8.5 usada na branch antiga, veja `~/e-cidade/docker*`
  e `docker-compose.php85.yml`, com `paridade` ini equivalente se existir); proxy :8190 (veja `docker-compose.proxy.yml`);
  sessões compartilhadas (veja `docker-compose.sessions.yml`). Torne os nomes de contêiner/portas/URLs configuráveis por
  variáveis (`REGRESSAO_REF_URL`, `REGRESSAO_NOVO_URL`, `REGRESSAO_PROXY_URL`, nomes de contêiner) em `regressao/nucleo/ambiente.py`
  com os padrões da 7.4. Gere env/arquivos locais exigidos pelo login web (como na branch antiga: `config/require_extensions.xml`,
  `extension/log/`, `libs/db_acessa.php`, hash da senha do `dbseller`) SEM commitar o que é gitignored.
- Crie o venv, rode `pytest regressao/tests -q` (unitários verdes sem Docker). Tire o dump baseline do banco 7.4 recém-subido
  (`regressao/baseline/baseline.dump` gitignored, sha256 em `baseline.dump.sha256` commitado) e copie o dump para
  `<seu-diretorio>/ecidade74-baseline.dump` (fora do git). Registre versões no `regressao/README` (7.4/Laravel 8).
- Verificação: login web pelos 3 runtimes (referência, 8.5, proxy) devolve a tela; `confere_baseline` ok.

### Task 2: Bateria PHP sobre 7.4 x 8.5
- Substitua toda referência a "5.6" por "referência" (7.4) em código, mensagens, catálogos e docs; ajuste `docker exec` de
  nomes de contêiner, caminhos de sessão e `cmp.py` normalizações (warnings do 7.4 vs 8.5). Reverifique os catálogos
  (`catalogo_posts.tsv`, `catalogo_relatorios.tsv`): rode cada linha ao vivo e atualize `verificado`.
- Rode amostras ao vivo (poucos prefixos) e prove que IDENTICO/DIVERGE fazem sentido; NÃO rode a rodada completa ainda.

### Task 3: Bateria Laravel sobre Laravel 8
- Regenere o inventário de rotas (`php artisan route:list --json` no contêiner de referência), ajuste `rotas.py`/gerador
  ao Laravel 8 (controllers com namespace, Passport 10, `Route::` fluente), token OAuth (`laravel_sobe`), mascara/redação.
  Regrave a baseline (`gravar --confirmo-sobrescrever` contra a referência) e confirme duas comparações seguidas
  idênticas. Atualize casos (`casos/*.yml`), console (artisan do Laravel 8; allowlist), arquivos por conteúdo.
- Laboratório `ecidade_lar12` (:8187): serviço PHP 8.5 que monta `LAR12_CODIGO` (padrão `./ecidade`); rode `comparar` e
  guarde o resultado em `regressao/baseline/lab-lar12-resultado.md` (o Laravel 8 sobre PHP 8.5 provavelmente quebra; é o achado).

### Task 4: Fluxos, orquestrador completo e documentação de uso
- Ajuste fluxos Playwright (baselines regravadas contra a referência, duas comparações estáveis), orquestrador `completa`
  (nomes, `--comparar`), resumo/relatório.
- Escreva `regressao/COMO-USAR.md` (público: dev, QA, gestor): o que é, pré-requisitos, "rodar em 3 comandos", como ler o
  relatório, quando é verde/vermelho, glossário dos vereditos, perguntas frequentes, o que a suíte NÃO prova; mantenha
  `regressao/README.md` técnico. Atualize `docs/` e o README raiz só com um link curto.

### Task 5: Servidor MCP (`.mcp/`)
- Python (SDK oficial `mcp`/FastMCP + `pydantic`), stdio, logs só em stderr. Estrutura: `.mcp/pyproject.toml` (ou
  `requirements.txt` com versões fixas), `.mcp/servidor/` (`main.py`, `config.py`, `seguranca.py` confinamento/allowlist,
  `docker_exec.py`, `tools/`, `prompts.py`, `resources.py`, `estado.py`), `.mcp/docs/regras-arquitetura.md`,
  `.mcp/docs/guia-breaking-changes.md` (PHP 7.4->8.5; Laravel 8->12; baseie-se em `decisoes-migracao.md`), `.mcp/estado/`
  (`trabalho.json`, `README`), `.mcp/tests/`, `.mcp/README.md` (3 passos), `.cursor/mcp.json`, `.vscode/mcp.json`,
  e snippet de `claude mcp add` (arquivo `.mcp.json` na raiz para Claude Code).
- Resources: regras, breaking changes, `regressao/COMO-USAR.md`, triagem, decisões, estado atual.
- Tools (pydantic): `analisar_composer`, `buscar_codigo_legado` (regex/ripgrep, com padrões nomeados: parse_str_1_arg,
  construtor_php4, split/each/ereg, create_function, etc.), `validar_arquivo_php` (php -l/PHPStan/Pint no contêiner da
  versão alvo), `rodar_regressao` (prefixo/área, destacado, devolve id da rodada), `ler_resultado_regressao`,
  `ler_triagem`, `reivindicar_arquivo`, `liberar_arquivo`, `quadro`, `proximo_trabalho`, `padroes_ja_corrigidos`.
- Prompts: `migrar-arquivo`, `auditar-model`, `corrigir-padrao-mecanico`, `verificar-com-regressao`.
- Testes: pytest com cliente MCP em processo (listar tools, chamar com entradas válidas/inválidas, confinamento, corrida
  de reivindicação), e um teste que garante que nada escreve em stdout. `claude mcp`/inspector smoke test descrito no README.

### Task 6: Rodada "antes" na 7.4 e triagem
- Rodada completa destacada (`orquestra --saida ~/rodadas/antes74 --alvo-laravel <referência>` para auto-consistência) e
  PHP 7.4 x 8.5 completo (renovação de sessão já existe); complemente o que falhar. Escreva
  `regressao/baseline/triagem-divergencias.md` (7.4 x 8.5) e `decisoes-migracao.md` atualizado (impacto, ordem, esforço).
- Fim: pare os contêineres `ecidade74_*` (não os antigos nem os de outro projeto local).
