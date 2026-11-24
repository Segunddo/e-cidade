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

## Como reproduzir

```bash
python -m regressao.php.bateria --saida ~/rodadas/base85/<area> --area <area> --pular sintaxe --pular classes
```

Áreas: gestor, integracoes, cidadao, assistenciasocial, educacao, saude, recursoshumanos, patrimonial,
tributario, financeiro, configuracao. Cerca de 14 horas para as 11. Como ler o relatório:
`regressao/COMO-USAR.md`.