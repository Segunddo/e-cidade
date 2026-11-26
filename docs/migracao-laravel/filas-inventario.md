# Inventário das filas do PR e resultado 7.4 × 8.5 por classe (PHP8-51)

Levantado em 20/11/2026 só por leitura do código e pela saída da medição de `filas-comandos-85.md`, sem banco, sem
rede e sem fila de verdade. Serve de ponto de partida para refazer a comparação quando o Laravel 13 entrar.

## Conexão de fila configurada

- `ecidade/configuration/queue.php:18`: `'default' => env('QUEUE_DRIVER', 'sync')`.
- `ecidade/.env.example:25`: `QUEUE_DRIVER=sync`. Com esse valor, o job roda na mesma requisição, sem fila.
- Conexões declaradas no mesmo arquivo: `sync`, `database` (tabela `jobs`), `beanstalkd`, `sqs` e `redis`
  (`retry_after` 90 nas três que têm). Falhas vão para a tabela `failed_jobs`.
- Filas com nome no código: `ReciboRepository::QUEUE_NAME` e `ReciboRepository::QUEUE_CREATE_NAME` (Pix).
- `app/Domain/RecursosHumanos/Pessoal/Controller/ContraChequesController.php:145` reenvia um payload já gravado com
  `Queue::connection(...)->pushRaw(...)`: durante a migração, o payload gravado por um runtime pode ser lido pelo outro (ver a leitura cruzada em
  `filas-comandos-85.md`).

Qual conexão cada instalação usa de fato depende do `.env` dela, que não está no repositório.

## Pontos de despacho: `filas-despachos.tsv`

29 pontos com arquivo:linha (13 `dispatch(`, 4 `::dispatch`, 11 `->notify(` e 1 `pushRaw`), com a forma, a classe,
`onQueue`, `onConnection`, atraso e para onde vai. As outras formas (`Notification::send`, `Bus::dispatch`/`chain`/
`batch`, `dispatchNow`, `Queue::push`) não aparecem no código.

| Vai para | Pontos |
|---|---|
| fila (classe `ShouldQueue`) | 19 |
| fila, reenvio de payload gravado (`pushRaw`) | 1 |
| na hora (a classe não é `ShouldQueue`) | 9 |

## Classes de fila: `filas-classes.tsv`

As 18 classes `ShouldQueue` de `app/` (16 jobs e 2 notificações; a mesma lista de `filas-comandos-85.md`), cada uma
com:

- onde é despachada (arquivo:linha). `DeleteFileStorage` não tem ponto de despacho no código.
- os itens do inventário Laravel 8 → 13 (`inventario-8-a-13-ocorrencias.tsv`) que citam o arquivo dela. As 18 citam
  `13.x Collection Model Serialization Restores Eager-Loaded Relations` e
  `13.x Queued Notifications and Missing Models`, e há 1 caso de `10.x The dispatch() Helper Return Value` e 1 de
  `10.x Database Expressions`.
- o resultado 7.4 × 8.5 hoje, com o Laravel 8 do PR, lido da saída do `roda.sh` de `filas-comandos-85.md`:

| Resultado | Classes |
|---|---|
| payload igual; `command` igual byte a byte; estado cruzado igual nas 4 leituras | 16 |
| payload igual; `command` com as mesmas partes em outra ordem; estado cruzado igual nas 4 leituras | 2 |

As 2 da segunda linha são as notificações `EmissaoRelatorioLegalNotification` e `UserNotificationAcordoVencimento`.
A ordem muda pelo `ReflectionClass::getProperties()` do PHP 8, explicado em `filas-comandos-85.md`.

## Como reproduzir

```bash
bash docs/migracao-laravel/anexos/filas-comandos-85/roda.sh <vendor do 7.4> <vendor do 8.5> <saída>
python3 docs/migracao-laravel/anexos/filas-comandos-85/inventario_filas.py ecidade \
  docs/migracao-laravel/inventario-8-a-13-ocorrencias.tsv \
  docs/migracao-laravel/filas-despachos.tsv docs/migracao-laravel/filas-classes.tsv <saída>
```

Sem o último argumento, a tabela de classes sai sem a coluna do resultado.

## Lacunas

- Despacho com nome de classe montado em tempo de execução não aparece na busca por texto.
- O resultado é com o Laravel 8 do PR nos dois runtimes. Com o Laravel 13, a medição tem de ser refeita, a começar
  pelas classes dos itens do inventário acima.
- Nenhum job é executado (`handle()`), como em `filas-comandos-85.md`.
