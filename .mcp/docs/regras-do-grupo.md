# Regras do grupo

Resumo fiel do `CONTRIBUINDO.md` e do guia "Migração do PHP 7.4 para o 8.5 a partir do PR #8" (18/11/2026). A
íntegra do guia está no resource `ecidade://grupo/guia-7.4-para-8.5`. Em caso de dúvida, vale o que o grupo
combinou; este arquivo só junta as regras num lugar para a sua IA.

## O que estamos fazendo

- A branch oficial é a **`base-php74`**, criada do PR #8 da DBSeller (PHP 7.4 + Laravel 8).
- **A referência é o 7.4.** "Funciona igual" quer dizer igual ao 7.4 do PR. Onde o PR mudou o comportamento, vale o
  PR.
- **Alvo:** PHP 8.5 com **Laravel 13 + Passport 13**. O Laravel 13 exige PHP 8.3 ou mais e não roda no 7.4: o
  **7.4 fica intacto com o Laravel 8 do PR** e o 8.5 ganha bibliotecas próprias (um composer só dele). Assim a
  referência nunca muda e dá para comparar os dois lado a lado.
- A `base-php84` está congelada: não recebe mais trabalho. Serve de guia, com cuidado (ver abaixo).

## Regras do grupo (CONTRIBUINDO.md)

1. **Nunca `git add .` nem `git add -A`.** Adicione arquivo por arquivo.
2. **Trabalhe no WSL/Linux, não em `C:\`.** O repositório tem 107 grupos de arquivos que só diferem em
   maiúsculas/minúsculas, e o Windows não guarda os dois.
3. **Não salve em UTF-8.** O código é **ISO-8859-1** (acentos). Configure o editor para não converter.
4. **Separe mudança automática de manual.** Um commit só com o que o Rector fez, outro com o que você corrigiu à mão.
5. **Cada pessoa mexe só na sua área.** Precisa de um arquivo de outra área? Peça ao dono.
6. **`composer.json`, `composer.lock` e `vendor/` são do grupo Laravel.** Não mexa sem combinar.
7. **Nunca `git push --force`, nem `git reset --hard` sem avisar.**
8. **Pull request pequeno.** Com centenas de arquivos, divida.

### Áreas (sugestão inicial do CONTRIBUINDO.md)

| Área | Valor para o MCP (`minha_area` / `ECIDADE_MCP_AREA`) | Prefixos e pastas |
|---|---|---|
| Núcleo e coordenação | `nucleo` | `libs/`, `dbforms/`, `config/`, `FrontController.php`, login |
| Educação | `educacao` | `edu`, `src/Educacao` |
| Pessoal (RH) | `pessoal` | `pes`, `src/RecursosHumanos` |
| Financeiro | `financeiro` | `con`, `cai`, `orc`, `emp` |
| Tributário e Patrimonial | `tributario_patrimonial` | `cad`, `iss`, `fis`, `pro`, `arr`, `div`, `itb`, `com`, `mat`, `pat`, `lic`, `aco` |
| Saúde e demais | `saude_demais` | `sau`, `ate`, `lab`, `far`, `agu`, `mer`, `vei`, `bib`, `ouv`, `soc` |
| Sem dono na tabela | `sem_area` | `func_*`, `classes/`, `pre*`, `rec*`, `jur*`, `cem*` … (o grupo ainda não distribuiu; escolha de propósito e combine com o coordenador) |

Arquivo fora da tabela (ex.: `app/`, outros prefixos): combine com o coordenador.

## Fluxo de cada tarefa

```bash
git checkout base-php74
git pull
git checkout -b area/assunto           # ex.: financeiro/each-removido
# ... trabalhe; a cada coisa pronta:
git add arquivo1.php arquivo2.php      # sempre arquivo por arquivo
git commit -m "PHP8-31: troca each() por foreach em 3 arquivos"   # PHP8-NN: NN = número da tarefa do grupo
git pull origin base-php74             # resolva conflitos do seu lado
# abra o pull request de area/assunto para base-php74 (o coordenador aceita)
```

Nome da branch: `area/assunto`, minúsculo, sem espaço.

## Regras de método (usadas pela frente Laravel; propostas para todos)

| Regra | Na prática |
|---|---|
| **Não repetir trabalho** | Antes de começar, procure nas branches do grupo e na `base-php74` se alguém já fez. |
| **Funciona igual ao 7.4** | Se o 8.5 já se comporta exatamente como o 7.4, não se mexe. Só muda o que difere ou não roda, com prova antes e depois. |
| **O código do PR tem prioridade** | O que o PR implementou e roda no 8.5 fica como está. Ninguém troca pela versão da `base-php84` nem por uma própria. Onde o 8.5 exige mudança, mexe-se o **mínimo** no arquivo do PR, **sem copiar arquivo inteiro** de outra base. |
| **Só atualizar** | Não acrescentar função, não mudar o que o sistema faz, não "aproveitar para corrigir". Defeito encontrado (inclusive de segurança) é **registrado e avisado ao dono da área**, não corrigido na migração. |
| **O 7.4 fica intacto** | Mudança num arquivo que o 7.4 também usa só com prova de que o 7.4 continua igual (bateria antes/depois), ou então vai para algo que só o 8.5 lê. |
| **Não tocar no banco** | Testes com banco só leitura sempre que der. Telas que gravam rodam num contêiner próprio, com o vigia do banco conferindo que só gravou o que o sistema grava sozinho (log de acesso, sessão, usuários on-line, tokens). Relatórios só depois de ler o código e confirmar que não gravam. |
| **Não limpar registros de auditoria** | Gravação de auditoria feita pelo próprio sistema durante o teste fica como está. |
| **Seguir precedente** | Se o grupo já resolveu um caso igual de um jeito, siga o mesmo jeito e registre a diferença medida (ex.: `break` fora de laço virou `exit`). |
| **Regressão em área de outro** | Só documentar e avisar o dono. |
| **Commits** | Formato do `CONTRIBUINDO.md`: **`PHP8-NN: descrição curta`**, NN = número da tarefa do grupo (ex.: `PHP8-31: troca $str{i} por $str[i] em db_stdlib.php`); corpo dizendo o que foi medido. Decidido em 19/11/2026 (decisão 11); o histórico anterior, com "verbo no presente" sem prefixo, fica como está. |
| **Documentos autocontidos** | Cada registro em `docs/registro/` se explica sozinho, sem citar ferramentas internas nem nomes de quem fez. **Falha de segurança nunca vai para o repositório.** |

## Usar a `base-php84` como guia, com cuidado

Parte do que foi corrigido na `base-php84` era diferença entre o 5.6 e o 7, que o 7.4 do PR **já tem**. Copiar
essas correções agora muda o comportamento em relação à referência.

| Correção na `base-php84` | Ainda vale do 7.4 ao 8.5? |
|---|---|
| `$$x[$i]` e `$o->$p[$i]` (mudaram de sentido no PHP 7.0) | **não**: o 7.4 já lê do jeito novo; mexer agora mudaria o resultado |
| `split()` (removido no 7.0, coberto por função de compatibilidade) | **não**, se a mesma função de compatibilidade estiver no 7.4 e no 8.5 |
| `break` fora de laço | **não**: já é erro de compilação no 7.4; se compila no 7.4, não existe |
| `$s{i}` → `$s[i]` | **sim**: removido no 8.0 |
| `pg_lo_export` com a conexão no fim | **sim**: removido no 8.0 |
| Construtor do jpgraph e assinaturas compatíveis | **sim**: 8.0 |
| Comparação `== ""` com inteiro | **sim**: 8.0 |
| `each()`, `create_function`, `count(null)` | **sim**: 8.0 |

**A prioridade é o código do PR:**

- Se o PR já resolveu e funciona no 8.5, fica o do PR.
- Se o PR resolveu, mas não roda no 8.5, ajusta-se o código do PR no mínimo para rodar, mantendo a estrutura e o
  jeito dele.
- Se o PR não mexeu e o ponto quebra no 8.5, aí sim a `base-php84` serve de modelo, adaptada ao código atual do
  arquivo. Não se copia o arquivo inteiro de lá.
- **Nunca** se copia um arquivo inteiro da `base-php84` por cima do da `base-php74`: isso desfaz as mudanças
  funcionais do PR (Financeiro, Patrimonial, Tributário, Folha, Educação, Saúde).

Regra prática: antes de aplicar uma correção vinda da `base-php84`, rode o trecho no 7.4 e no 8.5. Se o 8.5 já se
comporta como o 7.4, não mexa. Se precisa mexer, parta do arquivo da `base-php74` e mude só as linhas necessárias.

## Como provar que ficou igual

- **Sintaxe:** `php -l` no 7.4 e no 8.5 em todo arquivo mexido (`validar_arquivo_php(versao="ambas")`).
- **Telas:** a mesma requisição no 7.4 e no 8.5 e a comparação dos bytes da resposta (`scratchpad/cmp.py`,
  `docs/como-testamos.md`; no MCP, `rodar_regressao`). Telas com JavaScript: navegador automático.
- **Escrita:** nível 1 em memória (`scratchpad/escrita.php`); gravação real só em contêiner próprio com o vigia do
  banco.
- **Documentos:** PDF, planilha e Word comparados pelo conteúdo (páginas, texto, imagens).
- **APIs:** status, corpo normalizado e tipo de conteúdo, rota por rota, contra a linha de base do 7.4.
- **Integrações externas** (Pix, bancos): sempre contra dublê local, sem rede, nunca chamada real.
- **Linhas de base:** as gravadas no 5.6 viram histórico. Todas são gravadas de novo no 7.4.

## O que o MCP faz com estas regras

- `reivindicar_arquivo` recusa arquivo de outra área (`outra_area`) se você informar a sua; `proximo_trabalho` só
  devolve arquivos da sua área e na ordem **não compila no 8.5 > quebra em execução > silencioso > obsoleto**.
- `buscar_codigo_legado` lê o código como ISO-8859-1 e nunca grava nada.
- As sugestões de commit seguem o formato `PHP8-NN: descrição curta` (o NN vem de `ECIDADE_MCP_TAREFA`; sem ela, a
  sugestão sai com `NN` e um aviso para trocar) e lembram de separar Rector de manual.
- Os prompts `migrar-arquivo` e `corrigir-padrao-mecanico` repetem: mínimo no arquivo do PR, nada copiado da
  `base-php84`, prova 7.4 × 8.5 antes e depois, ISO-8859-1, commit do Rector separado, defeito registrado e não
  corrigido.
