# Dimensionamento das próximas áreas

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

### 🗺️ DIMENSIONAMENTO DAS PRÓXIMAS ÁREAS (13/10/2026)

Medido no banco (mesma cadeia `atendcadarea → … → db_itensmenu`), descontando o que já é
servido pelo 8.5 e o que os commits `Porta …` já pagaram. Arquivos a alterar = fecho das sete
frentes a partir das telas de menu (estimativa: na Fase B, 428 previstos viraram ~526).

| Área | Módulos | Telas que faltam | Universo | Já pago | A alterar |
|---|---|---|---|---|---|
| Financeiro | 6 | 910 | 2.568 | 340 | 788 |
| Patrimonial | 8 | 713 | 2.224 | 344 | 674 |
| Recursos Humanos | 4 | 685 | 1.925 | 300 | 492 |
| Saúde | 8 | 474 | 1.192 | 84 | 507 |
| Educação | 5 | 467 | 1.617 | 296 | 514 |
| Configuração | 1 | 203 | 905 | 298 | 219 |
| Assistência Social | 2 | 65 | 305 | 102 | 73 |
| Cidadão | 1 | 34 | 108 | 35 | 13 |
| Gestor / Integrações | 1+1 | 7+8 | 41+60 | — | 8+5 |

Somadas isoladas dão 3.293; a união é 2.783 — a ordem pré-paga o resíduo da seguinte. Cinco
áreas cadastradas não têm módulo ligado (Geoprocessamento, Administração, DBLeis, Comercial,
Implantação). Contando telas distintas, Tributário tem 1.031 (o 1.056 conta por módulo).

**Escolhida: Educação** — não a maior nem a mais barata, mas a única que permite comparar as
duas estratégias (big-bang 8.4 do TCC de referência × strangler fig 8.5) **sobre o mesmo módulo**.

#### Refeito em 18/10/2026, depois da Educação — `scratchpad/dimensiona.py`

Mesmo método, agora reproduzível: telas de menu existentes em disco que o 8.5 ainda não serve
(nem pelo `location` nem pelo `map`), fecho das sete frentes pelo `enumera.py` (`TELAS=`).
Conferência do instrumento: Tributário e Educação saem com **0 faltando** (1.066 − 7 fantasmas
= 1.059 e 481 − 1 = 480, os mesmos números conferidos pelo proxy em 15/10).

| Área | Módulos | Telas que faltam | Universo | Já pago | **A alterar** | em 13/10 |
|---|---|---|---|---|---|---|
| Financeiro | 6 | 949 | 2.674 | 401 | **771** | 788 |
| Patrimonial | 8 | 713 | 2.239 | 419 | **622** | 674 |
| Saúde | 8 | 492 | 1.322 | 165 | **505** | 507 |
| Recursos Humanos | 4 | 700 | 1.989 | 337 | **486** | 492 |
| Configuração | 1 | 203 | 920 | 361 | **173** | 219 |
| Assistência Social | 2 | 67 | 323 | 131 | **62** | 73 |
| Cidadão | 1 | 35 | 109 | 35 | **13** | 13 |
| Integrações / Gestor | 1+1 | 13+7 | 77+41 | 39+21 | **9+8** | 5+8 |

União: **2.358** (era 2.783). A Educação pré-pagou ~425 arquivos das outras áreas, sobretudo
Patrimonial (−52, as `mat`) e Configuração (−46). Saúde e RH quase não mudaram: são as áreas com
menos código em comum com as já feitas. "Telas que faltam" no Financeiro subiu de 910 para 949
porque a correção da 10ª lacuna passou a contar as entradas de menu com parâmetro.

Ressalvas de leitura: "a alterar" é estimativa estática — nas duas áreas feitas o real saiu
13–23% acima (correções à mão e lacunas) — e não conta os commits `EXPERIMENTO:` como pagos.

#### Refeito em 22/10/2026, depois de Recursos Humanos

`dimensiona.py` passou a contar RH como concluída e a conhecer `rh|eso|rec|pes` no `location`. Conferência
do instrumento: Tributário, Educação e RH saem com **0 telas faltando** (fantasmas 7, 1 e 4, os mesmos
registrados).

| Área | Módulos | Telas que faltam | Universo | Já pago | **A alterar** | em 18/10 |
|---|---|---|---|---|---|---|
| Financeiro | 6 | 945 | 3.586 | 881 | **641** | 771 |
| Saúde | 8 | 492 | 2.482 | 704 | **534** | 505 |
| Patrimonial | 8 | 712 | 3.075 | 873 | **469** | 622 |
| Configuração | 1 | 203 | 1.923 | 848 | **137** | 173 |
| Assistência Social | 2 | 64 | 1.405 | 682 | **50** | 62 |
| Cidadão | 1 | 35 | 1.066 | 539 | **29** | 13 |
| Integrações / Gestor | 1+1 | 9+7 | 1.015+375 | 538+162 | **20+18** | 9+8 |

União: **1.711** (era 2.358). Duas coisas mudaram ao mesmo tempo, e a leitura precisa separá-las:

- **O que RH pré-pagou.** Patrimonial (−153) e Financeiro (−130) caíram mais: RH tocou muitas classes de
  `classes/` compartilhadas com eles — inclusive os 316 DAOs da 13ª lacuna, 168 deles de domínios de
  Financeiro/Patrimonial. As telas que faltam caíram pouco (Financeiro 949 → 945, Assistência Social 67 → 64,
  Integrações 13 → 9, Patrimonial 713 → 712) — são as telas compartilhadas que a Fase B de RH roteou pelo `map`.
- **A 8ª frente da enumeração (13ª lacuna).** O fecho agora segue `new Classe`/`Classe::` de `model/`/`std/`
  até `classes/`, e por isso **todos os universos cresceram muito** (Financeiro 2.674 → 3.586). "Universo" e
  "já pago" **não são comparáveis** com a tabela de 18/10. Nas áreas com pouco código em comum com as já
  feitas, a frente nova achou mais trabalho do que o pago: Saúde +29, Cidadão +16, Integrações +11, Gestor +10.
  Esses aumentos são correções de medição, não regressão: em 18/10 essas classes já precisavam de porte, só
  não eram enxergadas.
