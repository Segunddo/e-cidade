"""Prompts: roteiros padronizados para a IA de cada pessoa seguir do mesmo jeito (regras do grupo embutidas)."""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

REGRAS_COMUNS = """Regras fixas (valem para todo o trabalho):
- Leia antes ecidade://grupo/regras (ou a tool regras_do_grupo), ecidade://docs/regras-arquitetura e
  ecidade://docs/breaking-changes.
- O gabarito e a referencia PHP 7.4/Laravel 8 do PR #8. Mudanca de comportamento visivel ao usuario e regressao,
  nao melhoria. Alvo: PHP 8.5 com Laravel 13 + Passport 13 (composer proprio do 8.5; o 7.4 fica intacto).
- O codigo do PR tem prioridade: mexa o MINIMO no arquivo do PR. NUNCA copie arquivo inteiro da base-php84
  (desfaz mudancas funcionais do PR); dela, so o trecho necessario, e so se o 8.5 ainda difere do 7.4.
- Prove 7.4 x 8.5 ANTES e DEPOIS (php -l nos dois e a tela/classe comparada). Se o 8.5 ja se comporta como o 7.4,
  nao mexa.
- O codigo e ISO-8859-1: nao salve em UTF-8 (estraga os acentos).
- Mudanca automatica (Rector) em commit SEPARADO da mudanca manual.
- So atualizar: defeito que ja existe no 7.4 (inclusive de seguranca) e REGISTRADO e avisado ao dono da area, nao
  corrigido; falha de seguranca nunca vai para o repositorio.
- Cada pessoa na sua area; arquivo de outra area -> peca ao dono. composer.json/lock/vendor sao do grupo Laravel.
- PHP/PHPStan/Pint so pelas tools (rodam no Docker do projeto). Nunca rode shell livre.
- Commit so dos caminhos que voce tocou (git add <caminho>), nunca `git add -A`/`git add .`; assunto no formato do
  CONTRIBUINDO.md, `PHP8-NN: descricao curta` (NN = numero da tarefa do grupo; ex.: "PHP8-31: troca $str{i} por
  $str[i] em db_stdlib.php"); sem push nem push --force sem pedido.
- INCONCLUSIVO e ERRO_AMBIENTE da regressao NUNCA sao aprovacao."""


def registrar(mcp: MCPServer) -> None:
    @mcp.prompt(name="migrar-arquivo", title="Migrar um arquivo para PHP 8.5",
                description="Roteiro completo para migrar UM arquivo: reivindicar, provar 7.4 x 8.5 antes, mexer o "
                            "minimo no arquivo do PR, validar nos dois PHPs, provar depois e liberar")
    def migrar_arquivo(caminho: str) -> str:
        return f"""Migre o arquivo `{caminho}` do e-Cidade da base PHP 7.4/Laravel 8 (PR #8) para PHP 8.5 (e Laravel 13
se for codigo Laravel), sem mudar o comportamento.

{REGRAS_COMUNS}

Passos:
1. `quadro` para ver se alguem ja esta nele; procure nas branches do grupo se alguem ja fez (nao repetir trabalho);
   depois `reivindicar_arquivo(caminho="{caminho}", motivo="migracao")` (recusa se for de outra area).
2. PROVA ANTES: `validar_arquivo_php(caminho="{caminho}", versao="ambas")` e a comparacao 7.4 x 8.5 da tela/classe
   (`rodar_regressao` com prefixo da tela, ou `ferramentas_do_grupo` -> cmp.py/escrita.php). Se ja e igual, PARE.
3. `buscar_codigo_legado(padrao="todos", caminho="{caminho}")` e leia o arquivo inteiro e os includes que ele usa.
4. Corrija so as linhas necessarias, partindo do arquivo da base-php74 (o do PR). Use a forma padrao do grupo
   (`padroes_ja_corrigidos`); da base-php84 so o trecho, adaptado, e nunca $$x[$i], split() ou break fora de laco.
   Defeito que ja existe no 7.4: registre e avise o dono, nao corrija. Salve em ISO-8859-1.
5. PROVA DEPOIS: valide de novo nas duas versoes (`lint`; e `phpstan` com versao="alvo" se for classe/model) e
   repita a comparacao 7.4 x 8.5: tem de ficar igual. Se o arquivo tambem roda no 7.4, prove que o 7.4 nao mudou.
6. So com IDENTICO (ou DIVERGE explicada e aceita pelo usuario): `liberar_arquivo(caminho="{caminho}",
   concluido=true, padroes_corrigidos=[...])`.
7. Mostre ao usuario: o diff, a prova antes/depois e a sugestao de commit (`git add {caminho}`; assunto
   `PHP8-NN: descricao curta`, com o numero da tarefa do grupo; se houve Rector, um commit so dele). Nao faca push."""

    @mcp.prompt(name="auditar-model", title="Auditar um Model Eloquent para Laravel 13",
                description="Revisao (sem editar) de um Model Eloquent: o que quebra ou muda do Laravel 8 ao 13")
    def auditar_model(caminho: str) -> str:
        return f"""Audite o Model `{caminho}` para a ida Laravel 8 -> 13 (PHP 8.5, composer proprio do 8.5). NAO edite
nada: produza um relatorio.

{REGRAS_COMUNS}

Verifique e cite linha a linha:
1. `buscar_codigo_legado(padrao="laravel", caminho="{caminho}")` e `padrao="todos"` ($dates, DB::raw, validated,
   env() fora de configuration/, Cache::put em segundos, helpers removidos, Carbon diffIn*, Doctrine DBAL).
2. Propriedades: `$dates` (sai no 10: vira `$casts` datetime), `$casts`, `$fillable`/`$guarded`, `$appends`,
   `$hidden`, `$table`/`$primaryKey`/`$keyType`/`$incrementing` (PostgreSQL com schemas), `$timestamps`, `$dateFormat`.
3. Datas: Carbon 2 -> 3 (diffIn* com sinal e float), serializacao de datas (toArray/JSON) e fuso.
4. Relacionamentos, accessors/mutators, scopes, eventos, observers; `OAuthenticatable` se for o model de usuario
   (Passport 13).
5. Defeitos que ja existem no Laravel 8 do PR (Cache::put em segundos, array_pluck/str_random, env() fora de
   configuration/): marque como "registrar e avisar o dono", NAO como correcao.
6. Rode `validar_arquivo_php(caminho="{caminho}", ferramentas=["lint", "phpstan"], versao="alvo")`.
7. Liste as rotas/telas que usam o Model e diga qual bateria da regressao (laravel/php) cobre cada uma.

Formato do relatorio: tabela `linha | problema | versao que quebra | correcao proposta | risco`, depois
"o que a regressao cobre", "defeitos a registrar" e "o que precisa de teste manual"."""

    @mcp.prompt(name="corrigir-padrao-mecanico", title="Corrigir um padrao mecanico em lote",
                description="Pega o proximo lote de arquivos de UM padrao (ex.: parse_str_1_arg) na sua area, prova "
                            "antes, corrige com a forma canonica, prova depois e registra")
    def corrigir_padrao_mecanico(padrao: str, limite: str = "10") -> str:
        return f"""Corrija em lote o padrao legado `{padrao}` (no maximo {limite} arquivos), de forma mecanica e
identica ao que o grupo ja faz.

{REGRAS_COMUNS}

Passos:
1. `padroes_ja_corrigidos()` para ver a forma canonica e os commits anteriores; `ferramentas_do_grupo()` para ver se
   ha regra Rector do grupo para este padrao (ex.: GuardaComparacaoLiteralRector para `== ""`).
2. `proximo_trabalho(padrao="{padrao}", limite={limite}, reivindicar=true, minha_area=<sua area>)`: ele pula o que
   outros reivindicaram, o que ja foi concluido e arquivos de outras areas.
3. PROVA ANTES: `validar_arquivo_php(versao="ambas")` e a comparacao 7.4 x 8.5 de cada arquivo/tela do lote. Arquivo
   em que o 8.5 ja se comporta como o 7.4 sai do lote.
4. Em cada arquivo do PR, troque SO as ocorrencias do padrao pela forma canonica (`exemplo_depois`), sem copiar nada
   da base-php84 por inteiro. Ocorrencia que nao se encaixa (ex.: separador regex): a mao, anotada. Salve em
   ISO-8859-1.
5. PROVA DEPOIS: `validar_arquivo_php(versao="ambas")` e `rodar_regressao(bateria="php", prefixo=[...])` com as telas
   tocadas; leia com `ler_resultado_regressao`. Telas DIVERGE por este padrao viram IDENTICO ou mostram a proxima
   camada (efeito "cebola"): reporte qual.
6. Defeito que ja existia no 7.4 e apareceu no caminho: registre e avise o dono, nao corrija.
7. `liberar_arquivo(..., concluido=true, padroes_corrigidos=["{padrao}"])` para cada arquivo pronto; libere sem
   concluir os que ficaram para tras.
8. Proponha os commits: o que o Rector fez num commit SO DELE, o manual em outro; `git add <cada caminho>`; assunto
   `PHP8-NN: descricao curta` com o numero da tarefa do grupo (ex.: "PHP8-31: troca each() por foreach em 3
   arquivos") e a linha `Padrao-MCP: {padrao}` no corpo; o commit de `.mcp/estado/trabalho.json` separado."""

    @mcp.prompt(name="verificar-com-regressao", title="Verificar uma mudanca com a regressao",
                description="Escolhe a bateria e o recorte certos para uma mudanca, roda e interpreta o resultado")
    def verificar_com_regressao(alvo: str) -> str:
        return f"""Verifique com a suite de regressao a mudanca em: {alvo}

{REGRAS_COMUNS}

Passos:
1. Leia ecidade://regressao/como-usar (se existir) para lembrar o que cada bateria prova.
2. Escolha o recorte: telas legadas (`*.php` na raiz de ecidade/) -> bateria `php` com `prefixo` ancorado
   (ex.: `^arr1_grupotaxa001\\\\.php$`) ou `area`; codigo Laravel (`app/`, rotas `/v4`, `rest/v1`) -> bateria `laravel`
   (so compara; a baseline do Laravel 8 nunca e regravada pelo MCP); fluxo de navegador -> `fluxos`.
3. `rodar_regressao(...)` e anote o id. Cada rodada restaura o banco de teste (~4 min) e so roda uma por vez.
4. `ler_resultado_regressao(id=...)` ate `status=concluida`. Interprete:
   - IDENTICO: mesma resposta que a referencia 7.4 (no escopo do que foi exercitado).
   - DIVERGE: achado real; abra o diff e explique a causa (`ler_triagem(busca=...)` mostra se ja era conhecido).
   - INCONCLUSIVO: NAO exercitado (ex.: 500 nos dois lados, tela sem parametros). Nao conta como aprovado.
   - ERRO_AMBIENTE: a rodada nao vale; corrija o ambiente (conteiner, sessao, baseline) e rode de novo.
5. Regressao em area de outra pessoa: so documente e avise o dono.
6. Liste os casos da mudanca (as telas/rotas/fluxos que o arquivo alcanca) e o veredito de cada um.
7. A mudanca so pode seguir com IDENTICO em TODOS os casos da mudanca (ou DIVERGE explicada e aceita pelo usuario) e
   nenhum ERRO_AMBIENTE. INCONCLUSIVO num caso da mudanca NAO libera: o caso nao foi exercitado; diga o que falta
   para exercita-lo (parametros, dados, outro recorte) e rode de novo.
8. Responda com: comando usado, totais por veredito, o veredito de cada caso da mudanca, DIVERGE novas com causa, o
   que NAO foi exercitado e se a mudanca pode seguir pelo criterio do passo 7."""
