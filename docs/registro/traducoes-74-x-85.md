# Traduções pt-BR do PR no Laravel 13

**Resumo (PHP8-94):** as 73 chaves de `resources/lang/pt-br` (auth, paginação, senhas e validação) voltam traduzidas, como no arquivo, no PHP 7.4
(Laravel 8.73.2) e no PHP 8.5 (Laravel 13.43.0): 73 de 73, 0 caindo em inglês. A mensagem de cada uma das 27 regras de validação que o código do PR usa sai
**igual byte a byte** nos dois. As diferenças ficam em coisas que o PR não usa ou que nunca esteve em português: 5 regras de validação que o PR não usa
e o assunto de 2 e-mails do próprio framework (seção 3). Nenhum arquivo foi alterado. Sem banco e sem rede.

## 1. O que existe no código próprio

| Item | Quantidade |
|---|---|
| `resources/lang/en` e `resources/lang/pt-br` | 4 arquivos cada (`auth`, `pagination`, `passwords`, `validation`); `en` em ASCII, `pt-br` em UTF-8 |
| `app.locale` / `app.fallback_locale` | `pt-br` / `en` (`configuration/app.php`) |
| chamadas `__()`, `trans()`, `trans_choice()`, `@lang`, `Lang::` no código próprio | 0 |
| regras de validação usadas em `app/` e `src/` | 27 com mensagem: `array`, `between`, `boolean`, `confirmed`, `date`, `date_format`, `different`, `digits`, `email`, `exists`, `file`, `filled`, `in`, `integer`, `max`, `mimes`, `mimetypes`, `min`, `numeric`, `present`, `regex`, `required`, `required_if`, `required_with`, `required_without`, `string`, `unique` (mais `nullable` e `sometimes`, sem mensagem) |

O Laravel 9+ procura os idiomas em `lang/` na raiz; o PR os tem em `resources/lang/`. O app real do PR (`bootstrap/app.php` + kernel) resolve `path.lang` para
`/app/resources/lang` nos dois runtimes, então nenhuma tradução se perde.

## 2. Resultado (`ecidade/tests/sistema/traducoes/roda.sh`)

`roda.sh` roda 3 trechos no 7.4 (vendor do `ecidade/composer.lock` do PR) e no 8.5 (vendor da integração) por `docker/composer-85/roda-isolado.sh`, com o app real do PR.

| Trecho | O que mede | Resultado |
|---|---|---|
| `idioma.php` | locale, `path.lang`, `trans()` de `validation.required`, `auth.failed`, `auth.throttle` (com `:seconds`), `passwords.reset`, `passwords.user`, `pagination.next`/`previous`, `validation.min.numeric`, `trans_choice('validation.size.array', 2)`, `__()` de chave inexistente e de texto livre | **igual** (14 linhas) |
| `regras.php` (1) | cada chave dos 4 arquivos `pt-br` do PR, via `trans()` | 73 de 73 iguais ao arquivo nos dois |
| `regras.php` (2) | a mensagem de um valor inválido para cada regra (e cada tipo: número, texto, lista) de 50 casos | 45 iguais; 5 diferem, **nenhuma usada pelo PR** |
| `notificacoes_auth.php` | assunto, introdução, botão e fecho de `ResetPassword` e `VerifyEmail` | 2 de 10 linhas diferem (seção 3) |

As chaves usadas pelas regras do PR existem todas em `pt-br/validation.php`, então nenhuma cai no texto em inglês nem na própria chave.

## 3. Diferenças (só registro)

| Item | 7.4 (Laravel 8) | 8.5 (Laravel 13) | Causa |
|---|---|---|---|
| regra `uuid` (o PR não usa) | `validation.uuid` | `The campo field must be a valid UUID.` | o `pt-br/validation.php` do PR não tem a chave; o 13 traz um texto padrão em inglês na própria biblioteca (`Translation/lang`) e o usa como último recurso |
| regras `gt`, `gte`, `lt`, `lte` (o PR não usa) | `validation.gt.numeric`, … | `The campo field must be greater than 5.`, … | idem |
| assunto do e-mail `ResetPassword` (`ResetPasswordController`) | `Reset Password Notification` | `Reset your password` | o texto-padrão do framework mudou no 13 (item "Default Password Reset Subject" do guia de upgrade 13.x); em nenhuma versão está em português, porque o PR não tem `pt-br.json` |
| assunto do e-mail `VerifyEmail` | `Verify Email Address` | `Verify your email address` | idem (o PR não usa `VerifyEmail`) |

Os textos de introdução, botão e fecho dos dois e-mails são iguais nos dois runtimes (em inglês). Traduzir esses e-mails (e as 5 regras) exigiria um `pt-br.json` e chaves novas em `validation.php`: é melhoria, não paridade, e fica fora desta tarefa.

## 4. Limites

- A mensagem por regra aqui é a da regra com um valor inválido; a mensagem de cada form request do PR (1.350 casos) é medida no registro da validação (`validacao-laravel8-7.4-x-8.5.md`), sem repetir.
- Não há textos de `Notification`/`Mailable` próprios traduzidos por chave: o código próprio não chama `__()`.

## 5. Como reproduzir

```bash
bash ecidade/tests/sistema/traducoes/roda.sh   # precisa de runtime-85/vendor e runtime-85/referencia-74/vendor; rc 1 se algum trecho difere
```
