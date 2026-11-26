# Rodada sobre a base-php85: antes × depois da migração

Data: 24/11/2026. Código medido: `origin/base-php85` no commit `111125fb5` (PRs #29 a #41 mesclados).
Gabarito: PHP 7.4 / Laravel 8 (referência). Alvo: PHP 8.5. Rodada por área (11 áreas), só PHP.

## Resultado em uma tabela

Casos comuns às duas rodadas: 13.120 (telas, POSTs e relatórios).

| Veredito | Antes da migração | Minha branch (PHP8-31) | **base-php85** |
|---|---|---|---|
| IDENTICO | 5.896 | 9.339 | **11.728** |
| DIVERGE | 6.669 | 3.074 | **573** |
| INCONCLUSIVO | 544 | 697 | 809 |
| ERRO_AMBIENTE | 11 | 10 | 10 |

- Regressões (IDENTICO ou INCONCLUSIVO que viraram DIVERGE ou ERRO_AMBIENTE): **0**.
- 5.831 casos passaram de DIVERGE para IDENTICO em relação ao "antes".
- 265 casos passaram de DIVERGE para INCONCLUSIVO. INCONCLUSIVO **não é aprovação**: significa
  "página de erro idêntica nos dois lados; tela não exercitada".

## DIVERGE por área

| Área | Antes | Minha branch | base-php85 |
|---|---|---|---|
| gestor | 4 | 0 | 0 |
| integracoes | 39 | 39 | 0 |
| cidadao | 762 | 399 | 22 |
| assistenciasocial | 338 | 177 | 35 |
| educacao | 1.146 | 476 | 125 |
| saude | 811 | 298 | 54 |
| recursoshumanos | 1.989 | 1.208 | 244 |
| patrimonial | 2.832 | 1.341 | 125 |
| tributario | 3.080 | 1.384 | 159 |
| financeiro | 3.351 | 1.749 | 317 |
| configuracao | 2.698 | 1.287 | 181 |

As áreas se sobrepõem em alguns prefixos, então a soma das linhas é maior que o total único (573).

## O que ainda diverge (573)

- 559 telas, 9 POSTs, 5 relatórios.
- 509 têm erro 500 no 8.5 (a referência responde). É a lista de trabalho que resta.
- Os 9 POSTs são "SQL de escrita diverge".

## Limites desta rodada

- **O ganho não é só de uma correção.** A base-php85 junta o trabalho de todas as áreas; não dá para
  atribuir o avanço a um commit.
- **Fora do escopo:** fluxos de navegador e bateria Laravel (o Laravel migrado ainda não existe).
  Sintaxe e classes foram medidas à parte (ver abaixo, se já houver resultado).
- Casos que oscilam: um teste de uma tela (`cad1_reliptuender002.php`) mudou de INCONCLUSIVO para
  DIVERGE na rodada anterior, sem edição do arquivo; tratar como oscilação até rodar de novo.
- Áreas ainda em PR aberto (Configuração #44, Educação #46, RH #42, Saúde #35) podem já estar
  parcialmente em base-php85; não foi conferido o que cada PR aberto acrescenta.
﻿
## Sintaxe e classes (rodada à parte, mesma base-php85)

`php -l` e carga das classes nos dois lados (7.4 e 8.5), sobre 13.065 arquivos de tela e 2.629 classes.

| Etapa | IDENTICO | DIVERGE | INCONCLUSIVO | Antes (DIVERGE) |
|---|---|---|---|---|
| Sintaxe | 13.057 | **2** | 6 | 4 |
| Classes (em `111125fb5`) | 1.552 | **1.018** | 59 | 2.532 |
| Classes das 1.018 (em `ceef42c8d`) | 1.017 | **1** | 0 | 1.018 |

- **Sintaxe: 2 arquivos ainda não compilam no 8.5 e compilam no 7.4:** `edu2_certconclusao002.php` e
  `edu4_verifexportcenso003.php`. São correção direta e pequena (erro de compilação).
- 6 arquivos não compilam em nenhum dos dois runtimes (defeito que já existe no 7.4; registrar e avisar
  o dono, não corrigir): `bib3_leitorcons002`, `edu1_diarioavaliacao001`, `edu1_diarioavaliacaoobs001`,
  `fis1_fis_vistorias003`, `mer1_mer_desper_und003`, `pes1_reajusteprog001`.
- **Classes: 1.018 divergiam; 1.017 já foram corrigidas na própria base-php85.** Causa isolada: a mudança de
  semântica do PHP 8 em `0 == ""` (verdadeiro no 7.4, falso no 8). As classes de dados usam
  `$this->campo == "" ? <valor do POST> : $this->campo` com campos que começam em `0`; no 8.5 a comparação
  falha, o POST nunca é lido e o campo fica em `0` (o `1013` do 7.4). A regra
  `scratchpad/rector-rules/GuardaComparacaoLiteralRector.php` reescreve o idioma e preserva o comportamento
  antigo nos dois runtimes. Prova em amostra: 20 das 1.018 passaram a IDENTICO com só essa regra.
  **Atualização de 2026-11-26:** a `guarda/classes-570` (PR #54) e os lotes do Patrimonial aplicaram a regra
  e a bateria de classes, repetida sobre a base-php85 em `ceef42c8d`, deu **1.017 IDENTICO e 1 DIVERGE**
  entre as 1.018 (as outras 1.611 não foram repetidas). A que sobrou:
  `classes/db_iptuconstr_classe.php`, TypeError no 8.5 porque `getParametros()` chama
  `pg_fetch_object($query)` com `$query` falso (no 7.4 é só aviso). É a mesma guarda `pg_*` sobre resultado
  `false` que o grupo já aplica em outros arquivos; lista em `classes-pendentes-base-php85.txt`.
- 57 dos 59 INCONCLUSIVO em classes são "sem saída nos dois lados" (classe não exercitada).
## Como reproduzir

```bash
python -m regressao.php.bateria --saida ~/rodadas/base85/<area> --area <area> --pular sintaxe --pular classes
```

Áreas: gestor, integracoes, cidadao, assistenciasocial, educacao, saude, recursoshumanos, patrimonial,
tributario, financeiro, configuracao. Cerca de 14 horas para as 11. Como ler o relatório:
`regressao/COMO-USAR.md`.

## Lint de toda a árvore (2026-11-26, base-php85 `ceef42c8d`)

O lint da suite só recebia telas dos menus. Com `regressao/php/arvore.py` (etapa nova, rodada de todas as áreas),
**23.676 `.php`** que as telas não cobrem (subpastas `app/`, `src/`, `forms/`, `model/`, `funcoes/`, `libs/`,
`dbagata/`... e 3.441 telas da raiz fora de qualquer área) foram comparados nos dois runtimes em 168 s:
23.661 IDENTICO, **8 DIVERGE**, 7 INCONCLUSIVO (não compilam em nenhum runtime: defeito que já existe no 7.4;
registrar e avisar o dono, não corrigir).

| Arquivo | Erro no 8.5 | Área |
|---|---|---|
| `app/Domain/Patrimonial/Protocolo/Controller/Processo/AndamentoPadrao/CamposDinamicosRespostaController.php` | nome qualificado inesperado (`\CamposDinamicosResposta`) | patrimonial |
| `app/Domain/Patrimonial/Protocolo/Repository/Processo/AndamentoPadrao/CamposDinamicosRepository.php` | nome com namespace inesperado | patrimonial |
| `app/Domain/Patrimonial/Protocolo/Transformers/Processo/AndamentoPadrao/CamposDinamicosResposta.php` | nome qualificado inesperado | patrimonial |
| `dbagata/classes/jpgraph/jpgraph_gantt.php` | assinatura incompatível (`GetColWidth`) | sem_area |
| `dbagata/classes/jpgraph/jpgraph_pie.php` | assinatura incompatível (`StrokeLabel`) | sem_area |
| `ext/php/Michelf/Markdown.php`, `MarkdownExtra.php` | `{}` em offset de string (linhas 800 e 163) | sem_area |
| `integracao_externa/gissonline/iss4_gissonline002.php` | `{}` em offset de string (linha 1767) | tributario |

Os 3 de `AndamentoPadrao` estão em 6 rotas do inventário Laravel (`/v4/api/patrimonial/protocolo/processo/.../campos-dinamicos`):
na bateria do Laravel elas só aparecerão como 500 no 8.5.
