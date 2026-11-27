# Rastreador - instrumentacao da arvore inteira (2026-11-27)

Instrumentador `regressao/rastro/php/instrumentador.php` (php-parser v4.19.1, emenda de bytes) sobre `ecidade/` no contêiner PHP 8.5. Saida: `ecidade/tmp/ecidade-rastro/` (git-ignored).

- Arquivos `.php` instrumentados: **36712** em **338.4 s** (8 processos em paralelo, lotes de 200)
- Sem parse (copiados como estao, sem sonda): **11** (os mesmos 11 de `rastro-parse-2026-11-27.md`)
- Links simbolicos para o que nao e instrumentado: **11852** (`vendor/` e `tmp/` como um unico link cada)
- **Defeitos nossos de lint: 0** (instrumentado nao compila e o original compila), `php -l` nos dois PHP em 285.3 s
- Falhas de lint que **ja existiam no original** (mesmo arquivo, mesmo PHP): 21
- **Segunda execucao sem mudancas:** 0 arquivos reprocessados, 36712 do cache, em 3.1 s

## Defeito encontrado e corrigido na propria medicao

A primeira passada deu 3 arquivos que nao compilavam (`impcarne.php`, `model/itemSolicitacao.model.php`, `model/ppadespesa.model.php`). Causa: uma divisao sem espaco antes de uma chamada instrumentada (`$a/count($b)`) fazia a sonda comecar com `/*R*/` e o texto virava `//*R*/`, um **comentario de linha** que engolia o resto da linha. Correcao: todo marcador comeca com um espaco (` /*R*/`). Fixture `tests/fixtures/rastro/divisao.php` cobre o caso. Depois disso: 0 defeitos.

## Falhas que ja existiam no original (nao sao da instrumentacao)

- `app/Domain/Financeiro/Contabilidade/RN/Services/SIAI/RREO/AnexoTrezeService.php`
- `app/Domain/Patrimonial/Protocolo/Controller/Processo/AndamentoPadrao/CamposDinamicosRespostaController.php`
- `app/Domain/Patrimonial/Protocolo/Repository/Processo/AndamentoPadrao/CamposDinamicosRepository.php`
- `app/Domain/Patrimonial/Protocolo/Transformers/Processo/AndamentoPadrao/CamposDinamicosResposta.php`
- `bib3_leitorcons002.php`
- `classes/db_cursoedu_ext_classe.php`
- `dbagata/classes/jpgraph/jpgraph_gantt.php`
- `dbagata/classes/jpgraph/jpgraph_pie.php`
- `edu1_diarioavaliacao001.php`
- `edu1_diarioavaliacaoobs001.php`
- `ext/php/Michelf/Markdown.php`
- `ext/php/Michelf/MarkdownExtra.php`
- `fis1_fis_vistorias003.php`
- `integracao_externa/gissonline/iss4_gissonline002.php`
- `libs/jpgraph/jpgraph_gantt.php`
- `mer1_mer_desper_und003.php`
- `model/contabilidade/arquivos/siai/v2021/SiaiArquivoPPAXML.model.php`
- `pes1_reajusteprog001.php`
- `src/Financeiro/Contabilidade/Sagres/ArquivosSagresFiscalInterface.php`
- `src/Saude/Agendamento/Exame/Cota/Mensal/Municipio/Interface.php`
- `src/Saude/Agendamento/Exame/Cota/Mensal/Prestador/Interface.php`
