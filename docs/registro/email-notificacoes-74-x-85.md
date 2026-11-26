# E-mails e notificações: inventário e renderização 7.4 × 8.5 (sem enviar, sem banco)

Mostra o que o PR (Laravel 8.73.2) monta de e-mail e de notificação, e se o PHP 8.5 monta o mesmo que o 7.4.
**Nada saiu e nenhum banco foi aberto**: o mailer foi o `array` (a mensagem fica na memória do transporte), os contêineres rodaram com `--network none`, e as 6 buscas no banco que as classes fazem foram trocadas por dados de exemplo em memória (seção 3).

**Resultado em uma linha:** com o mesmo vendor do Laravel 8.73.2, as 2 mensagens de e-mail (assunto, remetente, destinatários, corpo HTML e a mensagem serializada como sairia) e os 4 payloads de notificação saem **idênticos no 7.4 e no 8.5**; a única diferença é que o 8.5 registra 76 avisos de depreciação (74 em `vendor/`, 2 em código do PR). Com o Laravel 13 (SwiftMailer sai, Symfony Mailer entra), o assunto, os endereços e o corpo continuam iguais; muda só a ordem dos cabeçalhos.

## 1. Inventário

### Configuração de e-mail

| Onde | O quê |
|---|---|
| `ecidade/configuration/mail.php:19` | `'driver' => env('MAIL_DRIVER', 'smtp')`: formato antigo (uma chave `driver`, sem `default`/`mailers`); host, porta, criptografia, usuário e senha vêm de `MAIL_HOST`, `MAIL_PORT`, `MAIL_ENCRYPTION`, `MAIL_USERNAME`, `MAIL_PASSWORD` (`:32`, `:45`, `:74`, `:87`, `:89`); remetente de `MAIL_FROM_ADDRESS`/`MAIL_FROM_NAME` (`:59-60`) |
| `ecidade/.env.example:31-37` | `MAIL_DRIVER=smtp` com host de teste e `MAIL_FROM_ADDRESS` vazio; `:76-77`: `REDESIM_MAIL_ADDRESS_ON_ERROR` e `HABILITA_EMAIL_ERRO_PROCESSAMENTO_ESTABELECIMENTO_REDESIM`; `:22` `BROADCAST_DRIVER=log`, `:25` `QUEUE_DRIVER=sync` |
| `ecidade/configuration/app.php:155-156`, `:224-225` | `MailServiceProvider`, `NotificationServiceProvider` e os aliases `Mail` e `Notification` |

Driver configurado por padrão: `smtp`. Nenhuma credencial é lida ou exibida aqui.

### Mailables (2) — `extends Mailable`

| Classe | View | Quem chama |
|---|---|---|
| `app/Mail/NotificacaoAcordoVencimento.php:12` | `resources/views/emails/acordo/notificar-acordo-vencido.blade.php` | `UserNotificationAcordoVencimento::toMail` (`app/Notifications/UserNotificationAcordoVencimento.php:77`) |
| `app/Mail/RedesimErrorToProcessEstablishmentsMail.php:11` | `resources/views/emails/redesim/errorToProcessEstablishments.blade.php` | `Mail::send(...)` em `app/Domain/Tributario/ISSQN/Services/Redesim/RedesimService.php:440` |

### Notifications (4) — `extends Notification`, todas em `app/Notifications/`

| Classe | Canais (`via`) | Fila (`ShouldQueue`) | Quem notifica |
|---|---|---|---|
| `UserNotification.php:8` | `broadcast`, `database` | não | 8 chamadas: `MensageriaService.php:83`, `NotificarTransferenciaProcessoService.php:25`, `ConcessaoDireitosService.php:481`, `IntegracaoBnafarService.php:31`, `AnulaCDAServices.php:98`, `InclusaoInicialServices.php:79`, `SolicitacaoAssinaturaService.php:238`, `ExportarLoteBnafarJob.php:55` |
| `SolicitacaoAssinaturaNotification.php:10` | `broadcast`, `database` | não | `NoticarAssinanteDocumentoService.php:101` |
| `EmissaoRelatorioLegalNotification.php:12` | `broadcast`, `database` | sim | `NovaLRF/AnexosService.php:157` |
| `UserNotificationAcordoVencimento.php:13` | `database`, **`mail`** | sim | `NotificarAcordoVencimentoService.php:49` |

Só a última tem canal de e-mail. As outras três vão pelo banco (`database`, tabela `notifications`, migration `2022_10_24_103009`) e pelo `broadcast`; nenhuma define `toDatabase` nem `toBroadcast`, então o payload é o `toArray()`.
O `Notifiable` está em `app/User.php:16` e em `app/Domain/Configuracao/Usuario/Models/Usuario.php:60`.

Contagens, da raiz do repositório:

| Contagem | Comando | Resultado |
|---|---|---|
| Mailables | `git grep -lE 'extends Mailable' -- ecidade/app \| wc -l` | 2 |
| Notifications | `git grep -lE 'extends Notification\b' -- ecidade/app \| wc -l` | 4 |
| chamadas `->notify(` | `git grep -hE '\->notify\(' -- ecidade/app ecidade/src \| wc -l` | 11 |
| chamadas `Mail::send` | `git grep -hE 'Mail::send' -- ecidade/app ecidade/src \| wc -l` | 1 |

### Fora do Laravel (não renderizado aqui)

- `ecidade/src/Lib/Mail/SendMail.php:9` (`extends PHPMailer`, SMTP lido de `libs/config.mail.php`), usado em `src/Educacao/Escola/Service/NotificacaoTransferenciaService.php:76` e `:146`;
- a função nativa `mail()`: 24 chamadas em 20 arquivos (`git grep -hE '(^|[^_>:a-zA-Z])mail\(' -- 'ecidade/*.php' ':!ecidade/vendor' ':!ecidade/libs/PHPMailer*' ':!ecidade/fpdf151' ':!ecidade/dbagata' ':!ecidade/tests' | wc -l`), por exemplo `classes/db_tarefa_classe.php:669`, `con1_db_ordem001.php:371`;
- a biblioteca `libs/mail/` (`db_smtp1_class.php`, `db_smtp2_class.php`).

Esses caminhos não usam `Mail::`/`Mailable` e dependem de servidor SMTP ou `sendmail` reais; ficam para quem testar o envio de ponta a ponta.

## 2. Como foi medido

`scratchpad/emails_roda.sh` roda `scratchpad/emails_render.php` três vezes, cada uma num contêiner descartável (`--network none`, `ecidade/` montado só leitura em `/e`, vendor montado só leitura em `/e/vendor`):

| Execução | PHP | Vendor |
|---|---|---|
| `l8-74` | 7.4.33 | `composer install` do `ecidade/composer.lock` do PR (Laravel 8.73.2, SwiftMailer 6.3.0) |
| `l8-85` | 8.5.12 | vendor do `composer-85.lock` (`docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+`; Laravel 8.73.2, SwiftMailer 6.3.0, `lcobucci/jwt` 4.1.5) |
| `l13-85` | 8.5.12 | Laravel 13.43.0 (Symfony Mailer 8.1) resolvido à parte, só para esta comparação |

```bash
bash scratchpad/emails_roda.sh ecidade <vendor 7.4> <vendor 8.5> <vendor L13> <img 7.4> <img 8.5> <pasta de saida>
python3 scratchpad/emails_compara.py <saida>/l8-74.json <saida>/l8-85.json     # 7.4 x 8.5
python3 scratchpad/emails_compara.py <saida>/l8-85.json <saida>/l13-85.json    # Laravel 8 x 13
```

As imagens são as construídas de `docker/php74-apache` e `docker/php85-apache` (com o `php.ini` delas; os nomes locais usados foram `t102-php74-ref` e `ecidade-login-php85`, equivalentes às `ecidade-php74-apache` e `ecidade-php85-apache` que o `docker/composer-85/roda-isolado.sh` constrói). Uma primeira rodada em imagens só de CLI, sem `php.ini`, deu os mesmos JSON; a medição foi repetida nas imagens do projeto e os três arquivos de resultado saíram idênticos aos desta pasta. Os resultados desta medição estão em `docs/registro/email-notificacoes-resultados/` (`l8-74.json`, `l8-85.json`, `l13-85.json`).

O script monta um `Application` mínimo (config, view, mail, notifications, fila `sync`), com `mail.driver = array`, e usa as classes **reais** de `app/`:
`Mail::send` para o Mailable do Redesim (como no `RedesimService.php:440`); `Notification::sendNow` com o `Usuario` real do PR (atributos em memória) para o e-mail do acordo, passando pelo `ChannelManager` e pelo `MailChannel`; e `via()`/`toArray()` das outras notificações.
A mensagem é lida do transporte `array` e normalizada: sem `Date`, `Message-ID`, `boundary` nem o rótulo da pilha (a pilha de exceção que o e-mail do Redesim carrega muda de texto no PHP 8.4, onde `{closure}` passa a `{closure:arquivo:linha}`).
Textos em ISO-8859-1 saem no JSON como UTF-8 com a marca `[ISO]`.

## 3. Dados de exemplo (nenhum banco)

`scratchpad/emails_stubs.php` troca só as classes que consultariam o banco, antes de o PR carregá-las:

| Classe trocada | Quem a usa | Dado de exemplo |
|---|---|---|
| `DBConfig::find` | construtor de `NotificacaoAcordoVencimento` | `logo = logo.png` (um PNG 1×1 gravado em pasta temporária) |
| `InstituicaoRepository::find` | `build()` do e-mail do Redesim | nome "Prefeitura de São João" (ISO-8859-1) |
| `Acordo::find`, `MensageriaAcordoDia::find` | construtor de `UserNotificationAcordoVencimento` | acordo 12/2026, início 10/01/2026, fim 25/11/2026, 5 dias; assunto e mensagem com `[numero]`, `[ano]`, `[dias]`, `[data_inicial]`, `[data_final]` |
| `Item::find`, `Relatorio::find` | construtor de `EmissaoRelatorioLegalNotification` | "Anexos da LRF" e "Anexo 3 - RREO" |

O resto (substituição de marcadores, `DBString::utf8_encode_all`, `Imagem::caminhoArquivoParaBase64`, views Blade, `url()`) é o código do PR. Variáveis de ambiente de exemplo: `REDESIM_MAIL_ADDRESS_ON_ERROR` com 2 endereços `.invalid`, `MAIL_FROM_ADDRESS` `sistema@exemplo.invalid`.

## 4. Resultados

| Caso | O que se comparou | 7.4 × 8.5 (Laravel 8) | Laravel 8 × 13 (8.5) |
|---|---|---|---|
| e-mail do acordo (`UserNotificationAcordoVencimento` → `NotificacaoAcordoVencimento`) | `via`, `toArray`, assunto, remetente, destinatário, corpo HTML, mensagem serializada | igual | igual (muda só a ordem dos cabeçalhos) |
| e-mail de erro do Redesim (`Mail::send`) | assunto, remetente, 2 destinatários, corpo HTML, mensagem serializada | igual | igual (muda só a ordem dos cabeçalhos) |
| Redesim sem `REDESIM_MAIL_ADDRESS_ON_ERROR` | exceção do `build()` (classe e texto) | igual | igual |
| `UserNotification` | `via`, `toArray`, JSON | igual | igual |
| `SolicitacaoAssinaturaNotification` | `via`, `toArray`, JSON | igual | igual |
| `EmissaoRelatorioLegalNotification` | `via`, `toArray` (incluindo os links via `url()`) | igual | igual |
| `Imagem::caminhoArquivoParaBase64` | prefixo e `md5` do resultado | igual | igual |

`python3 scratchpad/emails_compara.py` dá `IGUAL` para `l8-74.json` × `l8-85.json` (sem contar o campo `deprecations`, que só existe no 8.5).

**Laravel 8 × 13.** A configuração do PR (`driver` único, sem `default`/`mailers`) é aceita sem mudança pelo Laravel 13: o `MailManager` ainda lê `mail.driver` por compatibilidade (`getDefaultDriver`, `getConfig`). O que muda:
no Laravel 8 a mensagem do transporte tem `Content-Type`, `MIME-Version`, `Date` e `Message-ID` desde a montagem e a lista de cabeçalhos sai nessa ordem; no 13 o Symfony os acrescenta no envio e a ordem final é `From`, `To`, `Subject`, `Message-ID`, `MIME-Version`, `Date`, `Content-Type`.
Os valores dos cabeçalhos de assunto/remetente/destinatário e o corpo (quoted-printable) são os mesmos nos dois.
Na leitura em memória, o nome do destinatário vem `null` no SwiftMailer e `""` no Symfony, e `getTextBody()` vem `""`: são diferenças de API, não da mensagem.

### Avisos de depreciação (8.5)

| Execução | Avisos |
|---|---|
| `l8-74` (PHP 7.4) | 0 |
| `l8-85` (PHP 8.5, Laravel 8) | 76: `laravel/framework` 54, `swiftmailer/swiftmailer` 13, `guzzlehttp/promises` 6, `opis/closure` 1 (74 em `vendor/`) e 2 em código do PR; sem `lcobucci/jwt`, que o `composer-85.lock` já traz na 4.1.5 (a 3.4 gerava 3 avisos de `Token`) |
| `l13-85` (PHP 8.5, Laravel 13) | 2 (os mesmos 2 do PR) |

Os 2 do PR: `app/Notifications/EmissaoRelatorioLegalNotification.php:49` (propriedade dinâmica `$titulo`, criação depreciada desde o PHP 8.2) e `std/DBString.php:813` (`utf8_encode()`, depreciada desde o 8.2; usada por `utf8_encode_all`, que as notificações chamam). O `HandleExceptions` do Laravel 8.73.2 registra depreciação no canal `deprecations` em vez de lançar exceção (`handleError` → `handleDeprecation`), então nenhum dos dois derruba a notificação no 8.5.
A lista completa está no campo `deprecations` de cada JSON.

## 5. Limites

- **Só o que o `array` mostra.** Não foi testado o envio por SMTP real, o `sendmail`, a entrega, o anexo nem a codificação final no servidor de e-mail; o transporte `array` guarda a mensagem como o Laravel a monta.
- **Notificações de fila.** As duas `ShouldQueue` foram executadas na hora (`sendNow`); a serialização do job na fila não faz parte desta medição.
- **Canais `database` e `broadcast`.** Comparou-se o payload (`toArray`), que é o que os dois canais gravam ou emitem; a gravação em `notifications` e a emissão no canal exigem banco e servidor de broadcast.
- **Dados de exemplo.** Os textos reais vêm do cadastro de mensageria do acordo e dos nomes de instituição, que estão no banco (ISO-8859-1); o exemplo usa acentos ISO para exercitar a conversão, mas não cobre todo o conteúdo possível.
- **Caminhos fora do Laravel** (seção 1) não foram renderizados.
- **O Laravel 13 é só comparação.** O PR roda no Laravel 8; a medição com o 13 mostra o que muda no e-mail quando o framework for trocado, usando as classes do PR sem alteração.
