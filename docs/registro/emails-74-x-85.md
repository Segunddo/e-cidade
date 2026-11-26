# E-mails do PR com o Laravel 13 (Symfony Mailer), sem enviar

**Resumo:** os e-mails do código próprio saem **iguais** em conteúdo no PHP 7.4 (Laravel 8.73.2 + SwiftMailer 6.3.0) e no PHP 8.5
(Laravel 13.43.0 + Symfony Mailer 8.1.10): 4 de 4 (assunto, remetente, destinatários, cabeçalhos relevantes, tipo e charset das partes, corpo
decodificado), 0 diferenças. A `configuration/mail.php` do PR (formato antigo, com `driver`) é lida pelo Laravel 13; 8 cenários de
configuração, 7 iguais ou equivalentes e 1 com diferença de mecanismo (`smtp` com `tls` na 587, seção 3). Nada foi enviado: transporte `array`, `--network none`, sem banco.

## 1. O que existe no código próprio

| Onde | O quê |
|---|---|
| `app/Mail/NotificacaoAcordoVencimento.php` | `Mailable`, view `emails.acordo.notificar-acordo-vencido`, logo em base64 no corpo |
| `app/Mail/RedesimErrorToProcessEstablishmentsMail.php` | `Mailable`, view `emails.redesim.errorToProcessEstablishments`; `Mail::send` em `RedesimService.php:440`; remetente e destinatários do `.env` |
| `app/Notifications/UserNotificationAcordoVencimento.php` | `toMail()` devolve o `NotificacaoAcordoVencimento` (`via`: `database`, `mail`) |
| `app/Notifications/` (3 outras) | só `database`/`broadcast`, sem e-mail |

Nenhum arquivo do código próprio usa `Swift_*`, `getSwiftMailer()` ou `getSwiftMessage()` (busca em `app/`, `src/`, `classes/`, `libs/`, `model/`).
Os 3 pontos de e-mail do PR usam só a API do `Mailable`/`Mail::send`, que o Laravel 9+ manteve.

## 2. Resultado (`ecidade/tests/sistema/emails/compara.py`)

Roda `email.php` no 7.4 (vendor do `ecidade/composer.lock` do PR) e no 8.5 (vendor da integração) por `docker/composer-85/roda-isolado.sh`, com
`ENV_EXTRA` (`MAIL_DRIVER=array`, remetente e destinatários fictícios), num `Application` do Laravel sem o bootstrap do kernel (o app do PR
ainda não sobe no 8.5: `php artisan list` termina com `Call to undefined method Laravel\Passport\Passport::routes()` em `app/Providers/AuthServiceProvider.php:31`, porque o Passport 13 não tem `routes()`). Dubles só para as duas buscas no banco que os `Mailable` fazem; o resto é o código do PR.

| E-mail | Assunto / remetente / destinatários | Corpo |
|---|---|---|
| `NotificacaoAcordoVencimento` (pelo `toMail`) | iguais | HTML igual (1 parte `text/html; charset=utf-8`, logo inline em base64) |
| `RedesimErrorToProcessEstablishmentsMail` | iguais (2 destinatários, remetente com o nome da instituição) | HTML igual |
| mesmo e-mail sem `REDESIM_MAIL_ADDRESS_ON_ERROR` | mesma exceção: `E-mail não pode ser enviado pois não foi feita a configuração.` | n/a |
| `Mail::raw` | iguais | texto igual (`text/plain; charset=utf-8`) |

Não contam como diferença, porque o conteúdo decodificado é o mesmo: a **ordem dos cabeçalhos** (Swift: `Message-ID`, `Date`, `Subject`, `From`, `To`;
Symfony: `From`, `To`, `Subject`, `MIME-Version`, `Date`, `Message-ID`) e a **quebra de linha do quoted-printable**. `Message-ID`, `Date`,
`boundary` e `cid:` são normalizados. Os e-mails do PR não têm anexo (o logo vai em base64 no HTML). Os comparadores foram verificados contra "igual"
falso: dois e-mails diferentes são detectados. O 8.5 não emitiu aviso `Deprecated` neste trecho.

## 3. A configuração do PR no Laravel 13 (`config_mail.php`)

`configuration/mail.php` usa o formato antigo (`driver`, `host`, `port`, `encryption`, `username`, `password`, `from`). O Laravel 13 ainda lê esse formato
(`MailManager::getConfig`, `getDefaultDriver` e `createSymfonyTransport` caem em `mail.driver` por compatibilidade), então nenhuma chave precisou mudar.

| Cenário (`MAIL_DRIVER` / `MAIL_ENCRYPTION`) | 7.4 (SwiftMailer) | 8.5 (Symfony Mailer) | Igual? |
|---|---|---|---|
| `smtp`, `tls`, 587 | `Swift_SmtpTransport`, criptografia `tls` | `EsmtpTransport`, sem TLS implícito | **mecanismo** |
| `smtp`, `ssl`, 465 | criptografia `ssl` | `EsmtpTransport`, TLS implícito | sim |
| `smtp`, sem criptografia, 25 | host e porta iguais, usuário `NULL` | host e porta iguais, usuário `''` | sim (sem autenticação nos dois) |
| `smtp` com os valores padrão do arquivo | `smtp.mailtrap.io:2525` | `smtp.mailtrap.io:2525` | sim |
| `log` | `LogTransport` | `LogTransport` | sim |
| `array` | `ArrayTransport` | `ArrayTransport` | sim |
| `sendmail` | `Swift_SendmailTransport` | `SendmailTransport` | sim |
| `mail` (`mail()` do PHP) | `Swift_SendmailTransport` | `SendmailTransport` | sim |

**Diferença de mecanismo (`tls`, porta 587):** no SwiftMailer, `encryption=tls` abre a conexão e **exige** STARTTLS; no Symfony Mailer o transporte SMTP
faz STARTTLS **quando o servidor oferece** e segue sem criptografia quando não oferece (só `ssl` força TLS desde a conexão). Em servidores que
oferecem STARTTLS (o caso comum da porta 587) o resultado é o mesmo; em um servidor que não oferece, o 7.4 falha e o 8.5 envia sem criptografia.
Não foi medida uma conexão (sem rede). Se isso importar, o ajuste é de configuração (`MAIL_ENCRYPTION=ssl` e porta 465), não de código.

## 4. Limites

- O que sai de verdade pela rede (servidor SMTP, autenticação, STARTTLS) não foi exercitado: só a criação do transporte e o conteúdo da mensagem.
- Os e-mails em fila (`UserNotificationAcordoVencimento` implementa `ShouldQueue`) dependem do banco e do serializador de fila; a geração do conteúdo é a medida aqui.
- A medição não passa pelo `kernel` do app do PR (não sobe no 8.5 por causa do Passport 13); a leitura de configuração é a do `MailManager` com o arquivo real.

## 5. Como reproduzir

```bash
python3 ecidade/tests/sistema/emails/compara.py     # e-mails, rc 0 se iguais (precisa de runtime-85/vendor e runtime-85/referencia-74/vendor)
for v in 7.4 8.5; do VENDOR=<vendor do $v> bash docker/composer-85/roda-isolado.sh $v ecidade/tests/sistema/emails/config_mail.php; done
```
