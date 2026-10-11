# Como trabalhamos neste repositório

Projeto: migrar o e-Cidade de PHP 5.6 para PHP 8.4. Leia este arquivo antes do primeiro commit.

## Branches

| Branch | Para quê | Quem mexe |
| --- | --- | --- |
| `master` | Código original. Referência de "como era antes" | Ninguém |
| `base-php84` | Versão oficial do grupo, só com o que já foi migrado e abre | Só o coordenador, aceitando pull requests |
| `area/assunto` | Trabalho de cada pessoa | Cada um na sua |

Nome da branch: `area/assunto`, minúsculo, sem espaço. Exemplos: `nucleo/string-offset`, `educacao/telas`, `pessoal/pes-telas`.

## Fluxo de cada tarefa

```bash
git checkout base-php84
git pull
git checkout -b educacao/telas        # sua branch, criada a partir da base

# trabalhe, e a cada coisa pronta:
git add arquivo1.php arquivo2.php     # sempre arquivo por arquivo
git commit -m "PHP8-31: o que foi feito, em uma linha"
git push -u origin educacao/telas
```

Depois abra um **pull request** de `educacao/telas` para `base-php84`.
Antes de abrir, rode `git pull origin base-php84` na sua branch para resolver conflitos do seu lado.

## Regras

1. **Nunca use `git add .` nem `git add -A`.** Adicione arquivo por arquivo. O banco de dados do Docker (`gunzip`) apaga um arquivo versionado, e o Windows cria falsos "modificados".
2. **Trabalhe dentro do WSL (Linux), não em `C:\`.** O repositório tem 107 grupos de arquivos com nomes que só diferem em maiúsculas/minúsculas, e o Windows não guarda os dois.
3. **Não salve arquivos em UTF-8.** O código usa ISO-8859-1 (acentos). Configure o editor para não converter.
4. **Separe mudança automática de manual.** Um commit só para o que o Rector fez, outro para o que você corrigiu à mão.
5. **Cada pessoa mexe só na sua área.** Precisa de um arquivo de outra área? Peça ao dono.
6. **`composer.json`, `composer.lock` e `vendor/` são do grupo Laravel.** Não mexa sem combinar.
7. **Nunca use `git push --force`, nem `git reset --hard` sem avisar.**
8. **Pull request pequeno.** Se tem centenas de arquivos e ninguém consegue revisar, divida.

## Commits

Formato: `PHP8-NN: descrição curta`. Exemplo: `PHP8-31: troca $str{i} por $str[i] em db_stdlib.php`.

## Divisão por área (sugestão inicial)

| # | Área | Prefixos na raiz |
| --- | --- | --- |
| 1 | Núcleo e coordenação | `libs/`, `dbforms/`, `config/`, `FrontController.php`, login |
| 2 | Educação | `edu`, `src/Educacao` |
| 3 | Pessoal (RH) | `pes`, `src/RecursosHumanos` |
| 4 | Financeiro | `con`, `cai`, `orc`, `emp` |
| 5 | Tributário e Patrimonial | `cad`, `iss`, `fis`, `pro`, `arr`, `div`, `itb`, `com`, `mat`, `pat`, `lic`, `aco` |
| 6 | Saúde e demais | `sau`, `ate`, `lab`, `far`, `agu`, `mer`, `vei`, `bib`, `ouv`, `soc` |

## Subir o ambiente

Veja `docker/README.md`. Resumo: `docker compose up -d --build`, depois o `gunzip` do banco e o `docker/install.sh`.
Acesso em `http://localhost:8080`.
