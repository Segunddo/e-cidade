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
| Classes | 1.552 | **1.018** | 59 | 2.532 |

- **Sintaxe: 2 arquivos ainda não compilam no 8.5 e compilam no 7.4:** `edu2_certconclusao002.php` e
  `edu4_verifexportcenso003.php`. São correção direta e pequena (erro de compilação).
- 6 arquivos não compilam em nenhum dos dois runtimes (defeito que já existe no 7.4; registrar e avisar
  o dono, não corrigir): `bib3_leitorcons002`, `edu1_diarioavaliacao001`, `edu1_diarioavaliacaoobs001`,
  `fis1_fis_vistorias003`, `mer1_mer_desper_und003`, `pes1_reajusteprog001`.
- **Classes: 1.018 ainda divergem — causa isolada e correção comprovada.** Não é o banco nem o teste: é a
  mudança de semântica do PHP 8 em `0 == ""` (verdadeiro no 7.4, falso no 8). As classes de dados usam o idioma
  `$this->campo == "" ? <valor do POST> : $this->campo` com campos que começam em `0`; no 8.5 a comparação
  falha, o POST nunca é lido e o campo fica em `0` (o `1013` do 7.4). Todas as 1.018 têm o idioma (1.017 com
  campo inicializado em 0) e nenhuma diverge sem ele. As 1.552 IDENTICO já têm a guarda da regra
  `scratchpad/rector-rules/GuardaComparacaoLiteralRector.php`, que reescreve para
  `($this->x === 0 || $this->x === 0.0 || $this->x == "" ? ... )` e preserva o comportamento antigo nos dois
  runtimes. **Prova:** a regra foi aplicada a uma amostra de 20 das 1.018 (sorteio fixo, semente 7) e a bateria
  de classes devolveu 20 de 20 IDENTICO; só essa regra disparou (115 linhas trocadas). A amostra foi revertida;
  nada disso está aplicado na árvore. **Ação:** aplicar a regra às 1.018 num commit Rector separado do manual
  (lista em `classes-sem-guarda-base-php85.txt`), um responsável só; `classes/` não tem dono de área
  (`sem_area`), então precisa de decisão do coordenador. Depois, repetir a bateria e só então distribuir as
  divergências restantes por área; parte dos 509 erros 500 das telas pode sumir junto.
- 57 dos 59 INCONCLUSIVO em classes são "sem saída nos dois lados" (classe não exercitada).
## Como reproduzir

```bash
python -m regressao.php.bateria --saida ~/rodadas/base85/<area> --area <area> --pular sintaxe --pular classes
```

Áreas: gestor, integracoes, cidadao, assistenciasocial, educacao, saude, recursoshumanos, patrimonial,
tributario, financeiro, configuracao. Cerca de 14 horas para as 11. Como ler o relatório:
`regressao/COMO-USAR.md`.