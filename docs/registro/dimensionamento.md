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

#### Refeito em 29/10/2026, depois de Patrimonial

`dimensiona.py` passou a contar Patrimonial como concluída (`JA` com `PATRIM`) e a conhecer `ac|aco|ouv|lic|vei|pat|com` no
`location`. Esta é a primeira medição com a **9ª frente** (classes com namespace, 15ª lacuna), por isso todos os universos
cresceram.

| Área | Módulos | Telas que faltam | Universo | Já pago | **A alterar** | em 22/10 |
|---|---|---|---|---|---|---|
| Financeiro | 6 | 926 | 5.007 | 999 | **601** | 641 |
| Saúde | 8 | 489 | 3.036 | 748 | **530** | 534 |
| Configuração | 1 | 201 | 2.521 | 892 | **127** | 137 |
| Assistência Social | 2 | 62 | 1.918 | 725 | **48** | 50 |
| Cidadão | 1 | 35 | 1.828 | 706 | **29** | 29 |
| Integrações | 1 | 9 | 1.823 | 712 | **18** | 20 |
| Gestor | 1 | 7 | 1.089 | 347 | **19** | 18 |

União: **1.254** (era 1.711). Patrimonial pré-pagou sobretudo Financeiro (−40; as classes de empenho, contratos e compras
são compartilhadas) e Configuração (−10). As telas que faltam caíram pouco (Financeiro 945 → 926), porque são as telas
compartilhadas que a Fase B de Patrimonial roteou pelo `map`. Gestor subiu 1 (18 → 19): a 9ª frente alcança uma classe
que antes não era vista. É correção de medição, não regressão.

Ressalva de leitura, a mesma de antes: "a alterar" é estimativa estática. Nas quatro áreas feitas, o real saiu acima por
causa das correções à mão e das lacunas descobertas no caminho. Em Patrimonial, a estimativa era 469 e o real foi ~710:
Fase A ~580 (538 pelo Rector + ~45 à mão) e Fase B ~130 (110 pelo Rector, 16 nas abas do passo 8b, 2 à mão). As
correções da 15ª lacuna e da forma negada foram feitas nas branches das áreas anteriores e não entram nessa conta.

#### Refeito em 30/10/2026, depois do Financeiro

`dimensiona.py` passou a contar o Financeiro como concluído (`JA` com `FINANC`); o `location` do script já tinha
`cus|pla|pl|tes|emp|orc|cai`. Conferido à parte, pelo mesmo critério (banco → em disco → `location` ou `map`): **as cinco áreas
concluídas têm 0 telas de menu fora do 8.5** — Tributário 1.059, Educação 480, Recursos Humanos 701, Patrimonial 743,
Financeiro 992.

| Área | Módulos | Telas que faltam | Universo | Já pago | **A alterar** | em 29/10 |
|---|---|---|---|---|---|---|
| Saúde | 8 | 489 | 3.036 | 750 | **530** | 530 |
| Configuração | 1 | 186 | 2.488 | 907 | **110** | 127 |
| Assistência Social | 2 | 59 | 1.903 | 726 | **43** | 48 |
| Cidadão | 1 | 35 | 1.828 | 709 | **28** | 29 |
| Integrações | 1 | 9 | 1.823 | 715 | **17** | 18 |
| Gestor | 1 | 7 | 1.089 | 347 | **19** | 19 |

Fantasmas (entrada de menu sem arquivo): Configuração 5, Assistência Social 1, Cidadão 5. União: **668** (era 1.254 com o
Financeiro). O Financeiro pré-pagou sobretudo Configuração (201 → 186 telas, 127 → 110 a alterar: telas `con`/`cai`
compartilhadas que entraram pelo `map`) e um pouco de Assistência Social. **A Saúde não mudou** (530): não compartilha quase
nada com o Financeiro, e é agora a maior área restante, com 489 telas, mais que todas as outras somadas (296).

Ressalva de sempre: "a alterar" é estimativa estática. No Financeiro a estimativa era 601; o real foi **1.168 pelo Rector**
(soma dos 6 lotes) **mais ~420 correções à mão** (LSP, guardas `pg_*`, `count(null)`, comentário sem fechamento), além do `tra`.
A estimativa conta arquivos a partir das telas de menu; o porte por prefixo inteiro (`cai`) e as abas do passo 8b alcançaram
muito mais.
