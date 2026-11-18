# CI de sintaxe do lote

## Objetivo

CI significa integracao continua. O GitHub Actions executa verificacoes quando o pull request recebe uma alteracao e mostra os resultados para os revisores.

Este pacote implementa o caso CI-01 da proposta do PR #14. Verifica a sintaxe dos PHP adicionados ou alterados no lote, no PHP 7.4 e no 8.5. Os testes funcionais do catalogo verificam os fluxos da aplicacao em outra etapa.

## Procedimento

1. Receber um PR destinado a base-php74.
2. Selecionar PHP adicionados ou alterados desde o ancestral comum entre a base e o commit do PR. Preservar espacos nos caminhos e excluir removidos. Renomes entram como adicoes.
3. Testar a ferramenta e preparar as imagens PHP 7.4 e 8.5.
4. Conferir um PHP sintetico valido e outro invalido para exercitar o lint.
5. Rodar php -n -d short_open_tag=1 -l nos arquivos selecionados. Se o arquivo falhar, conferir sua versao anterior no mesmo runtime.
6. Gerar JSON, Markdown e resumo na pagina da execucao.

O conteudo e lido do Git em bytes. Os containers usam montagem de leitura e ficam sem rede durante o lint. As imagens sao baixadas na preparacao. O processo dispensa credenciais do banco e da aplicacao.

## Resultados

| Estado | Significado | Codigo |
| --- | --- | --- |
| SEM_NOVA_FALHA | Os arquivos selecionados passaram no runtime. | 0 |
| SEM_PHP_ALTERADO | Zero PHP selecionados no lote. | 0 |
| NOVA_FALHA | Falha atual e versao anterior valida ou ausente. | 1 |
| INCONCLUSIVO | Arquivo falha tanto na base quanto no lote. | 2 |
| ERRO_AMBIENTE | Falha na selecao ou na execucao. | 2 |

FALHA_NOS_DOIS identifica cada arquivo do resultado inconclusivo. As causas dos erros precisam ser analisadas. Um erro de ambiente interrompe o lote e o resumo informa selecionados e conferidos. A proposta pede revisao em caso de erro ou inconclusivo. A equipe deve revisar esse criterio antes de configurar o check como obrigatorio.

SEM_PHP_ALTERADO significa que o workflow verificou a ferramenta e os exemplos sinteticos. Os fluxos funcionais do sistema seguem pendentes.

## Consulta no GitHub

Abra Checks no PR e escolha o job da versao PHP. Na pagina da execucao, veja o resumo e os artefatos lint-php-7.4 e lint-php-8.5, com JSON e Markdown disponiveis por 14 dias. Falhas de preparacao aparecem nos logs da etapa.

Os dois jobs rodam independentemente, com limite de 20 minutos cada. Cada invocacao de lint em Docker tem limite de 45 segundos e 256 MB. Cancelamentos e relatorios parciais requerem analise.

## Validacao

Quatorze testes locais passaram, cobrindo classificacao, codigos, resumo, preservacao de bytes LATIN1, argumentos do Docker, falhas, timeout, links simbolicos e selecao de renomes/exclusoes em Git real temporario. PHP e Docker sao simulados nesses testes.

Um teste adicional confere PHP valido e invalido em Docker quando ECIDADE_LINT_IMAGE esta configurado. Ele foi pulado localmente e roda no workflow. A primeira execucao remota falhou ao abrir /lint/arquivo.php. A correcao de permissoes da copia temporaria aguarda nova execucao no GitHub.

Comando de teste: python3 -B -m unittest discover -s ferramentas/testes-ci -p 'test_*.py' -v

## Limites

O lint roda isolado sem php.ini da aplicacao, com short_open_tag=1. Nao carrega includes, Laravel, banco ou servicos externos. Erros de fluxo exigem execucao funcional. A versao anterior usada na comparacao vem do ancestral comum do diff. A proposta precisa ser exercitada no GitHub e revisada pela equipe.

Referencias:
- https://docs.github.com/en/actions/get-started/continuous-integration
- https://www.php.net/manual/en/features.commandline.options.php

## Correcao de leitura no Docker

A copia temporaria usa pasta 0755 e arquivo 0644 antes de iniciar o container. Isso permite leitura com --cap-drop=ALL mesmo quando o UID do runner difere do UID do container. Apenas a copia temporaria recebe essas permissoes; os fontes do projeto nao sao alterados. O bind mount continua somente leitura e sem rede. Um teste verifica as permissoes antes da chamada ao Docker.
