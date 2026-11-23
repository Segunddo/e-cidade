# Compatibilidade PHP 8.5 - parse_str, FPDF e JSON

Frente do grupo: PHP 8.5. A contribuicao nova deste envio e a conferencia e validacao automatizada da migracao ja integrada.

## Escopo

- Atualizar parse_str com um argumento para a forma com resultado explicito e extract.
- Trocar acessos a caracteres com chaves no FPDF e no Services_JSON.
- Separar mudancas e conferir uma amostra, preservando a referencia PHP 7.4.

## Estado real da implementacao em 23/11/2026

Base auditada: base-php85, SHA 111125fb5ff45e3386b436344245754e83774676. A branch migracao/parse-str-e-guardas-sql ja e ancestral da base. A migracao do nucleo entrou pelo PR #39, seguida de ajustes adicionais. As implementacoes ja integradas pertencem aos respectivos autores. Esta entrega nao as reapresenta como mudancas novas.

Nao foi identificado ajuste restante nesses itens dentro dos limites da conferencia. A contribuicao deste pacote e o codigo de auditoria e provas reproduziveis, com registro de evidencias. Nao substitui fontes legados ou repete parse_str em massa.

## Auditoria de parse_str

Analisador lexical com token_get_all, PHP 8.5 e short_open_tag=1. A selecao do Git procurou parse_str nos arquivos versionados de ecidade com extensoes php, inc, class e phtml. Leitura dos blobs sem checkout completo ou conversao de codificacao.

- 7.729 arquivos candidatos lidos.
- 7.768 chamadas diretas reconhecidas, todas com dois argumentos.
- Zero chamadas diretas com menos de dois argumentos, fechamento incompleto ou desempacotamento pendente.

O analisador ignora comentarios e strings, distingue chamadas de metodos/declaracoes e conta argumentos com parenteses/arrays/interpolacao aninhados. Doze cenarios sinteticos passaram no teste do analisador, incluindo short tags e virgula final.

Limite: a auditoria nao resolve eval, aliases importados ou chamadas dinamicas. Contagem de argumentos nao comprova que cada tela funciona. Nao e uma afirmacao sobre todos os caminhos possiveis em tempo de execucao.

## Amostra da forma canonica

Treze consultas sinteticas comparadas em tres rodadas: forma antiga no PHP 7.4.33, forma canonica no PHP 7.4.33 e no PHP 8.5.0. As saidas foram identicas. Incluem arrays, chaves com ponto/espaco, repeticao de chaves, caracteres escapados, valor vazio, zero e sobrescrita de variavel comum.

A prova caracteriza a forma canonica parse_str com resultado, retirada das chaves reservadas e extract. Ela nao executa individualmente os 7.729 arquivos do sistema.

## FPDF e JSON

Os dois arquivos atuais compilam nos CLIs PHP 7.4 e 8.5. A prova dirigida executa 557 verificacoes por rodada, incluindo JSON, Unicode, os 256 bytes Latin1 e um PDF sintetico completo de duas paginas com Courier original.

Referencia base-php74 no PHP 7.4.33 e base atual nos PHPs 7.4.33/8.5.0: resultados e PDFs normalizados identicos. Somente CreationDate e normalizado. E_DEPRECATED excluido dos casos dirigidos; outros avisos falham. O lint registra deprecations remanescentes. Sem banco, login ou bootstrap da aplicacao.

## Reproduzir

Testar o analisador:

```sh
PHP_AUDITOR=/caminho/php85 python3 -m unittest discover -s ferramentas/testes-ci -p test_auditor_parse_str.py -v
```

Auditar uma referencia Git (o caminho e para o diretorio .git ou um bare):

```sh
python3 ferramentas/php85-compatibilidade/auditar_parse_str.py --repo /caminho/e-cidade/.git --ref origin/base-php85 --php /caminho/php85 --out /evidencias/auditoria
```

Amostra parse_str: executar prova_parse_str.php legacy no PHP 7.4 e migrated nos PHPs 7.4/8.5. Comparar as saidas.

Prova das bibliotecas: php -n ferramentas/php85-compatibilidade/prova_offsets_nucleo.php ecidade. O comparador aceita --php74, --php85, --original, --ajustado e --out para repetir as tres rodadas; as arvores precisam conter DBString e Courier originais.

## Validacao no laboratorio e74

Em 23/11/2026, a referencia `regressao-php74` em `b26268c` e o alvo `base-php85` em `111125f` rodaram no Docker com o mesmo dump conferido por SHA-256 e restaurado em um PostgreSQL descartavel. As 13 provas de parse_str e as 557 verificacoes de FPDF/JSON deram resultados iguais em PHP 7.4.33 e 8.5.13. Na prova de offsets, foi usada a opcao `-d disable_functions=mb_convert_encoding` para exercitar a conversao em PHP da biblioteca.

O MCP confirmou a sintaxe de FPDF, JSON e `cem1_cemiterio003.php` nos dois runtimes. O JSON apresentou tres avisos de deprecacao no PHP 8.5. A rodada oficial filtrada `20261123-200207-php-aa51` retornou codigo 0 com cinco casos `IDENTICO`: sintaxe, tres classes e a tela autenticada de cemiterio.

Na comparacao autenticada de relatorios, 31 dos 36 PDFs verificados no catalogo ficaram `IDENTICO`. Cinco PDFs devolveram HTTP 200 na referencia e HTTP 500 no alvo: `con2_contasrecdesp002.php`, `orc2_desppessoal002.php`, `cad2_loteam002.php`, `div2_resumogeraldivida002.php` e `agu2_relconsumo002.php`. Os pontos de falha observados foram quatro operacoes de contagem de resultado PostgreSQL e um calculo de exercicio. A investigacao da causa original e o aceite seguem com as areas responsaveis.

Tarefa proposta PHP8-101, separada do numero da Issue. Relacionar ao nucleo (#16), sem fechar automaticamente seu escopo maior. Nao publicar dump, credenciais, respostas de usuarios ou dados de baselines.

Referencias: https://github.com/Segunddo/e-cidade/tree/migracao/parse-str-e-guardas-sql e https://github.com/Segunddo/e-cidade/pull/39
