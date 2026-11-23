# Regressão sobre a base PHP 7.4 + servidor MCP — design

Data: 2026-11-17. Branch de trabalho: `regressao-php74` (worktree `~/e-cidade-74`), a partir de
`origin/referencia/dbseller-php74` (PHP >=7.4, Laravel ^8.0, Passport ^10.0, PHPUnit ^8.5).

## Intenção
A migração anterior (PHP 5.6/Laravel 5.4 -> 8.5/12) foi abandonada: outra equipe entregou uma base PHP 7.4/Laravel 8
e a migração recomeça dela. O trabalho de regressão feito na branch `regressao` (suíte diferencial + golden master)
precisa valer para esta base, e a equipe, cada pessoa com a sua IA, precisa trabalhar em conjunto e de forma padronizada
por um servidor MCP versionado no repositório.

## Objetivos
1. Suíte `regressao/` funcionando sobre a base 7.4: referência = PHP 7.4/Laravel 8 (gabarito), alvo = PHP 8.5/Laravel 12.
2. Três baterias (PHP diferencial 7.4 x 8.5; Laravel golden master gravado no Laravel 8; completa com fluxos de navegador),
   uma rodada "antes" real e a triagem das divergências 7.4 x 8.5.
3. Servidor MCP local (stdio, Python, SDK oficial `mcp`) em `.mcp/`, com Resources, Tools, Prompts e coordenação via Git.
4. Documentação fácil: `COMO-USAR.md` (regressão) e `.mcp/README.md` (3 passos), sem jargão desnecessário.

## Não-objetivos
- Migrar o código do e-Cidade (a suíte e o MCP medem e orientam; não migram).
- Servidor central/HTTP (abordagem C): fica para depois, se a equipe crescer.
- Publicar (push) sem pedido explícito do usuário.

## Anti-objetivos
- Gravar baseline com o sistema migrado; contar INCONCLUSIVO/ERRO_AMBIENTE como aprovação; mascarar diferença real;
  mexer em containers/dados fora do projeto (outro projeto local na porta 8080 não deve ser tocado: a referência usa porta própria).

## Abordagens consideradas
- A) Só o pedido original (2 resources, 3 tools, 2 prompts): simples, mas só padroniza regras.
- B) A + tools de migração (rodar regressão no Docker, ler triagem, próximo lote mecânico) + estado compartilhado no Git
  (`.mcp/estado/`): coordenação sem servidor. **Escolhida pelo usuário.**
- C) B + servidor HTTP central com locks/fila: mais poder, exige hospedagem/autenticação.

## Decisões (todas minhas, com o usuário tendo delegado)
- Python, SDK `mcp` (FastMCP), `pydantic` para validação. Transporte stdio; nunca imprimir em stdout (só stderr/logging).
- Execução de PHP/PHPStan/Pint e da regressão sempre DENTRO do Docker do repositório (versão de PHP igual para todos);
  lista fechada de comandos, sem shell livre, caminhos confinados à raiz do repositório.
- Coordenação: `.mcp/estado/trabalho.json` (quem reivindicou o quê, com data e expiração) + convenção de commit;
  tools `reivindicar_arquivo`, `liberar_arquivo`, `quadro`, `proximo_trabalho`.
- Ambiente da regressão na 7.4: projeto compose próprio (`-p e74`), contêineres `ecidade74_*` e portas próprias
  (referência 7.4 em :8074, alvo PHP 8.5 em :8085 -> :8185 se conflitar, proxy :8090 -> :8190), para NÃO parar outro
  projeto local na porta 8080 e NÃO tocar nos contêineres da stack antiga.
- Alvo padrão da bateria Laravel: `ecidade_lar12` em :8087 (código por `LAR12_CODIGO`); o Laravel 12 real não existe,
  o laboratório mostra o que falha.

## Entregáveis
`regressao/` (portada e adaptada), `regressao/COMO-USAR.md`, `.mcp/**`, `.cursor/mcp.json`, `.vscode/mcp.json`,
`.mcp/docs/regras-arquitetura.md`, `.mcp/docs/guia-breaking-changes.md` (7.4->8.5, Laravel 8->12), relatório da rodada
"antes", triagem 7.4 x 8.5.
