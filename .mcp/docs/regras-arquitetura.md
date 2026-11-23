# Regras de arquitetura e de trabalho da migração

Valem para **toda pessoa e toda IA** que mexe no e-Cidade nesta migração: base PHP 7.4/Laravel 8 do PR #8 → PHP 8.5
com **Laravel 13 + Passport 13** (o 7.4 fica intacto com o Laravel 8; o 8.5 tem composer próprio). A IA lê este
arquivo pelo resource `ecidade://docs/regras-arquitetura`. As regras do grupo (CONTRIBUINDO.md e o guia de
18/11/2026) estão em `ecidade://grupo/regras` e **prevalecem** sobre este arquivo se houver diferença.

## 1. Regras de trabalho (não negociáveis)

1. **O gabarito é a referência 7.4 do PR.** Migrar é fazer o mesmo sistema rodar no PHP 8.5 (Laravel 13) **com o
   mesmo comportamento**. Mudou o que o usuário vê (tela, PDF, valor, mensagem)? É regressão, mesmo que "pareça
   melhor". Se o 8.5 já se comporta como o 7.4, **não se mexe**.
2. **O código do PR tem prioridade; o mínimo necessário.** Mexa só as linhas que o 8.5 exige, no arquivo do PR.
   **Nunca copie arquivo inteiro da `base-php84`** (desfaz mudanças funcionais do PR) e nunca traga dela o que o
   7.4 já resolve (`$$x[$i]`, `split()` com compatibilidade, `break` fora de laço). Não reformate, não renomeie,
   não "aproveite para melhorar". **Só atualizar**: defeito que já existe no 7.4 (inclusive de segurança) é
   registrado e avisado ao dono da área, não corrigido; falha de segurança nunca vai para o repositório.
3. **Prova antes e depois**: `php -l` no 7.4 e no 8.5 e a comparação da tela/classe 7.4 × 8.5. Arquivo que o 7.4
   também usa só muda com prova de que o 7.4 continua igual.
4. **ISO-8859-1**: o código não é salvo em UTF-8 (estraga os acentos). Trabalhe no WSL/Linux, nunca em `C:\`.
5. **Cada pessoa na sua área** (tabela em `ecidade://grupo/regras`); arquivo de outra área, peça ao dono.
   `composer.json`, `composer.lock` e `vendor/` são do grupo Laravel.
6. **Reivindique antes de editar** (`reivindicar_arquivo`) e **libere ao terminar** (`liberar_arquivo`). Veja o
   `quadro` antes de começar. A reivindicação expira em 4 h: renove se ainda estiver trabalhando.
7. **Valide nos dois PHPs pelo MCP** (`validar_arquivo_php`, que roda no Docker do projeto). Nada de "no meu PHP
   local funciona": a versão do PHP tem de ser a mesma para todos.
8. **Rode a regressão** (`rodar_regressao`) cobrindo o que você tocou e leia o resultado
   (`ler_resultado_regressao`). Só segue com **zero DIVERGE nova sem explicação** e **nenhum ERRO_AMBIENTE**.
   **INCONCLUSIVO e ERRO_AMBIENTE nunca são aprovação.**
9. **Commits pequenos e por caminho**: `git add <arquivo1> <arquivo2>` — **nunca `git add -A` nem `git add .`**
   (o repositório tem arquivos locais de ambiente, dumps e segredos que não podem subir). Assunto no formato do
   `CONTRIBUINDO.md`: **`PHP8-NN: descrição curta`**, NN = número da tarefa do grupo (ex.: `PHP8-31: troca $str{i}
   por $str[i] em db_stdlib.php`; decisão 11, 19/11/2026), corpo dizendo o que foi medido e a linha
   `Padrao-MCP: <padrao>` para o MCP contar. **O que o Rector fez vai num commit só dele**, separado do manual. O
   estado vai em commit separado (`PHP8-NN: reivindica ecidade/x.php no quadro`). Branch `area/assunto` a partir da
   `base-php74`; pull request pequeno.
10. **Sem push** sem pedido explícito de quem é dono da tarefa; **nunca `git push --force` nem `git reset --hard`**
    sem avisar. O repositório no GitHub é **público**.
11. **Nunca** coloque divergência nova em `regressao/conhecidas.tsv` para "ficar verde": esse arquivo só aceita
   divergência que **já existia antes da migração**, com prova.
12. **Nunca regrave baseline** (`gravar --confirmo-sobrescrever`) com código migrado. O MCP nem oferece isso: a
   baseline é a foto da referência 7.4.
13. **Não toque no banco** fora do teste combinado (banco só leitura sempre que der; não limpe registros de
    auditoria que o próprio sistema grava).
14. **Segredos**: não leia, copie nem cole `.env`, `libs/db_conn.php`, chaves `oauth-*.key`, senhas ou hashes em
    issue, commit, prompt ou log.

## 2. Código novo ou reescrito (PHP 8.5 / Laravel 13)

Estas regras valem para **código novo** e para classes que você precisa reescrever. Código legado que só recebe a
correção mecânica (seção 1, regra 2) **não** é reestruturado.

> **Fase atual: o MESMO código roda nos dois PHPs.** A regressão compara a referência 7.4 com o 8.5 sobre a mesma
> pasta `ecidade/`. Se você usar sintaxe que só existe no PHP 8 (promoção de propriedade no construtor, `readonly`,
> `enum`, `match`, tipos união, argumentos nomeados, `?->`), a **referência 7.4 quebra** e a regressão perde o
> gabarito. Por isso, **até a virada**, todo código em `ecidade/` precisa compilar e funcionar no 7.4 **e** no 8.5
> (`validar_arquivo_php(versao="ambas")`). Os exemplos abaixo são compatíveis com os dois. Código que **só o 8.5 lê**
> (as bibliotecas próprias do 8.5, com Laravel 13) e o código depois da virada podem usar `final readonly class` e
> promoção no construtor.

### 2.1 Tipagem estrita

- Todo arquivo PHP novo começa com:

  ```php
  <?php

  declare(strict_types=1);
  ```

- **Não** acrescente `strict_types` em arquivo legado só "de carona": ele muda a conversão de tipos das chamadas
  feitas *dentro* do arquivo (ex.: `str_pad(123, ...)` passa a dar `TypeError`) e isso é mudança de comportamento.
- Tipos em parâmetros, retornos e propriedades. Nulo sempre explícito: `?Foo $x = null` (o nulo implícito
  `Foo $x = null` é depreciado no 8.4).
- Sem propriedades dinâmicas (depreciadas no 8.2): declare a propriedade na classe.

### 2.2 Onde cada coisa mora (Laravel em `ecidade/app/`)

O projeto já organiza o código Laravel por domínio: `app/Domain/<Área>/<Módulo>/{Services,Repositories,DTO,Action}`
(ex.: `app/Domain/Tributario/ISSQN/Services/Redesim/Action`, `app/Domain/Integracoes/EFDReinf/DTO`). Siga isso:

| Peça | Faz | Não faz |
|---|---|---|
| **Controller** (`app/Http/Controllers`) | valida a entrada (FormRequest), monta o DTO, chama **uma** Action, devolve a resposta | regra de negócio, SQL |
| **Action** (`.../Action/NomeDoCasoDeUso.php`) | **um** caso de uso, método público único `executar(Dto $dados): Resultado` (ou `__invoke`) | falar com HTTP/sessão |
| **DTO** (`.../DTO/`) | carrega dados entre camadas; `final class` com propriedades tipadas preenchidas no construtor e só lidas depois (após a virada: `final readonly class` com promoção) | lógica |
| **Service** | regra de negócio reutilizada por várias Actions | conhecer Request/Response |
| **Repository** | acesso a dados (Eloquent/Query Builder/SQL) | regra de negócio |

```php
<?php

declare(strict_types=1);

namespace App\Domain\Tributario\ISSQN\DTO;

final class EmitirGuiaDto
{
    public int $inscricao;
    public string $competencia;
    public ?string $observacao;

    public function __construct(int $inscricao, string $competencia, ?string $observacao = null)
    {
        $this->inscricao = $inscricao;
        $this->competencia = $competencia;
        $this->observacao = $observacao;
    }
}
```

(Propriedade tipada `public string $x;` existe desde o 7.4. Trate o DTO como imutável: ninguém altera as
propriedades depois do construtor.)

```php
<?php

declare(strict_types=1);

namespace App\Domain\Tributario\ISSQN\Action;

use App\Domain\Tributario\ISSQN\DTO\EmitirGuiaDto;
use App\Domain\Tributario\ISSQN\Repository\GuiaRepository;

final class EmitirGuia
{
    private GuiaRepository $guias;

    public function __construct(GuiaRepository $guias)
    {
        $this->guias = $guias;
    }

    public function executar(EmitirGuiaDto $dados): int
    {
        return $this->guias->criar($dados->inscricao, $dados->competencia, $dados->observacao);
    }
}
```

### 2.3 Injeção de dependência no construtor

- Dependências entram **pelo construtor** (propriedade `private` tipada; após a virada, promoção com
  `private readonly`) e o container do Laravel resolve.
- Evite `app(Foo::class)`, `resolve()`, `new` de serviços dentro de métodos e facades dentro de regra de negócio
  (em controller e em código de borda, facade é aceitável).
- Nada de estado global novo (`global $x`, `$GLOBALS`, variáveis de sessão lidas no meio da regra). O legado usa
  `db_getsession()`: **encapsule** a leitura na borda e passe o valor no DTO.

### 2.4 Banco

- PostgreSQL com muitos schemas e `search_path` por banco: em Model novo, declare `$table` qualificado se a tabela
  não estiver no `search_path` padrão.
- Consulta que pode falhar: teste o retorno antes de usar (`pg_*` com `false` é `TypeError` no PHP 8).
- Nada de SQL concatenado com entrada do usuário em código novo: use bindings.

### 2.5 Testes e validação

- Código novo vem com teste (PHPUnit da versão do Laravel alvo).
- Antes de pedir revisão: `validar_arquivo_php(..., ferramentas=["lint", "phpstan"], versao="ambas")` e a bateria
  da regressão que cobre a área.

## 3. Como a IA deve trabalhar (resumo para colar no prompt)

1. `quadro` → `reivindicar_arquivo` → ler o arquivo e os includes.
2. `buscar_codigo_legado(padrao="todos", caminho=<arquivo>)` e o guia `ecidade://docs/breaking-changes`.
3. Corrigir o mínimo com a forma canônica (`padroes_ja_corrigidos`).
4. `validar_arquivo_php(versao="ambas")` → `rodar_regressao` → `ler_resultado_regressao`.
5. `liberar_arquivo(concluido=true, padroes_corrigidos=[...])` → sugerir commit por caminho. Sem push.
