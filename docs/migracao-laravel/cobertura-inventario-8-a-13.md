# Cobertura do inventario 8 -> 13: cada item em uso x tarefa que cobre (PHP8-62)

Levantamento (so leitura, sem banco, nada de codigo mudado) sobre `inventario-8-a-13.md` (guias 9 a 13): dos 238 itens, os **47** que o codigo usa ou que so tem verificacao manual (42 `USA` + 5 `MANUAL` "Miscellaneous").
Para cada um: a tarefa do quadro que mede ou cobre (e o que ela mede), ou a razao de nao ser preciso. Tabela completa, com contagens e `arquivo:linha`: `cobertura-inventario-8-a-13.tsv`
(gerada por `python3 scratchpad/cobertura_inventario.py --escreve`; sem `--escreve` o script confere que os 47 itens do inventario estao na tabela). Estado das tarefas em 20/11/2026: F = Feito, QA, R = Revisao, D = Fazendo, S = na fila.

## Resumo (47 itens)

| Situacao | Itens | Significa |
|---|---|---|
| COBERTO | 32 | uma tarefa do quadro mede o item (ver tabela) |
| SEM EFEITO | 6 | lido/medido: o que o guia muda nao acontece no codigo (falso positivo da regex ou condicao que nao ocorre) |
| MANUAL | 5 | "Miscellaneous" de cada guia: so remete ao diff do esqueleto `laravel/laravel`; nao ha lista de quebras nem codigo proprio a medir |
| BANCO | 2 | so da para medir com banco (parte sem banco ja coberta) |
| **SEM TAREFA** | **2** | **nenhuma tarefa mede: viram tarefa nova (abaixo)** |

Das 32 cobertas, hoje: **2** tem todas as tarefas Feitas (Minimum Stability, Doctrine DBAL Removal); **10** dependem de ao menos uma tarefa ainda **na fila** (`T-145` filas/agendamento, `T-147` rotas sem autenticacao no 13, `T-150` e-mails,
`T-152` cache, `T-153` logs): enquanto essas nao rodam, esses itens seguem sem medida; as outras **20** estao em Revisao, QA ou Fazendo. Os numeros saem de `python3 scratchpad/cobertura_inventario.py`.

## Nao coberto por nenhuma tarefa: 2 itens (migrations)

Os dois sao do Schema builder e **nao precisam de banco** para medir: o SQL sai do `Grammar` do PostgreSQL a partir do `Blueprint` (como a T-111 fez com `DB::raw`). Importam porque a instalacao do zero do PR roda as
migrations (1.186 no repositorio).

| Item (guia) | Ocorrencias | arquivo:linha (exemplos) | Risco |
|---|---|---|---|
| 11.x Modifying Columns | 3 em 2 arquivos | `database/migrations/2021_10_25_083540_alter_secret_to_oauth_clients.php:17`, `:29`; `2024_08_13_093320_M28685_ajuste_schema_tabela_mensageriaacordo.php:243` (`->change()`) | medio: sem DBAL o `change()` do 11+ tem de repetir todos os modificadores da coluna; o SQL do `ALTER` muda |
| 11.x Floating-Point Types | 14 em 5 arquivos | `2021_12_14_114408_M19629_create_pix_tipo_debito.php:23-24` (`double(8,2)`), `2024_08_08_094811_m28016_rotina_elaboracao_pca.php:93-96` (`float`), `2022_02_11_105019_m17145_emissao_termo_divida.php:39-42`, `2024_10_10_130358_m28977_criacao_estrutura_notas_parciais.php:109,146,149`, `2022_05_26_163234_M20866_Createe_assentperc.php:20` | baixo: no PostgreSQL os tipos ficam `double precision`/`float(53)`, nao medido |

**Tarefa nova sugerida:** "Migrations no Laravel 13 sem banco: compilar o SQL do `Blueprint` pelo `Grammar` do PostgreSQL (7.4 com o vendor do PR x 8.5 com o Laravel 13) para os `->change()`, `float`/`double`
e, se der, as 1.186 migrations; diferenca de SQL com causa e correcao minima na migration (no proprio arquivo se o 7.4 fica igual) ou na sobreposicao". Area back; sem banco.

## Depende de banco (parte sem banco ja coberta): 2 itens

| Item | Ocorrencias | O que ja se mede | O que falta (banco) |
|---|---|---|---|
| 13.x Collection Model Serialization Restores Eager-Loaded Relations | 40 em 20 arquivos (`SerializesModels`) | payload serializado dos jobs (T-131 D, T-145 S) | restaurar as relacoes ao reler o model |
| 13.x Queued Notifications and Missing Models | 18 em 18 arquivos | render dos e-mails/notificacoes (T-127 F, T-150 S), payload (T-145) | descarte quando o model nao existe mais |

## Sem efeito (6 itens): o que o guia muda nao ocorre no codigo

| Item | Evidencia |
|---|---|
| 9.x The `when` / `unless` Methods (231 chamadas em 65 arquivos) | o guia 9 so muda quando o 1o argumento e uma **Closure** (passa a ser executada). `python3 scratchpad/cobertura_inventario.py --when`: 231 chamadas, **0** com Closure como condicao |
| 9.x Belongs To Many firstOrNew/firstOrCreate/updateOrCreate (1) | `BaseDisciplinaRepository.php:29` e `$this->newQuery()->updateOrCreate(`: model, nao relacao `BelongsToMany` |
| 10.x ULID Columns (1) | o item e `->ulid()` sem argumento; o codigo tem `->uuid('id')` (`2022_10_24_103009_create_notifications_table.php:17`) |
| 10.x The `dispatch()` Helper Return Value (12) | as 12 chamadas sao instrucoes `dispatch(new Job(...));`, sem usar o valor devolvido |
| 11.x Password Rehashing (1) | so o scaffold `RegisterController.php:68` (`bcrypt`), sem rota que o chame (`Auth::routes()` nao existe); o login e do Passport (T-135) |
| 12.x Container Class Dependency Resolution (8) | 6 sao `->make(` de repositorios (`TermoRepository` e outros), 2 sao `$app->make(Console\Kernel::class)` sem parametro com valor padrao |

## Observacoes

- **T-155 (Collections/Str/Arr no L13):** nenhum item `USA` do inventario e de `Str::`/`Arr::`/helpers; so ha 3 `when()` sobre Collection (`PcaspService.php:122,129`, `ProgramaEstrategicoService.php:208`), sem efeito. O escopo da T-155 vem da busca nos usos do
  codigo (nao do inventario); o inventario nao aponta quebra de `Collection`/`Str`/`Arr` em uso.
- **Falsos positivos:** o inventario e por expressao regular. Alem dos 6 acima, `Eloquent Model casts Method` (58 `$casts =`, propriedade continua valendo) e `Cache Prefixes` (4 de `database.php` sao `prefix` de conexao) so contam como usos; entram como COBERTO (T-124/T-146, T-152).
- **Carbon 3, Passport 13 e Eloquent** (os de maior risco: `Updating Passport` alto, `Carbon 3` medio) ja tem tarefa propria: T-134/T-144, T-130/T-135, T-124/T-146.
- Tarefas do quadro que **nao** vem de nenhum item `USA` (T-154 cliente HTTP, T-156 JSON da API, T-148 defeitos revalidados, T-136 pacotes) cobrem riscos que o inventario por guia nao enxerga; ficam fora desta tabela.

## Repetir

```bash
python3 scratchpad/cobertura_inventario.py            # confere os 47 itens do inventario contra a tabela e imprime o resumo
python3 scratchpad/cobertura_inventario.py --when     # as 231 chamadas de when/unless e quantas usam Closure como condicao
python3 scratchpad/cobertura_inventario.py --escreve  # regrava cobertura-inventario-8-a-13.tsv
```
