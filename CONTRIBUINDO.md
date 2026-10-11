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

## Subir o ambiente (passo a passo)

Primeira vez, leva uns 15 a 20 minutos para baixar e montar tudo.

**1. Clone dentro do WSL** (no Windows, abra o terminal do Ubuntu; não use `C:\`):

```bash
git clone https://github.com/Segunddo/e-cidade.git
cd e-cidade
```

**2. Suba os containers (PHP 5.6 + banco):**

```bash
docker compose up -d --build
```

**3. Descompacte o banco e rode a instalação:**

```bash
docker exec -it ecidade_php56 gunzip docker/database/ecidade_base.sql.gz
docker exec -it ecidade_php56 bash docker/install.sh
docker exec -it ecidade_php56 chmod -R 775 /var/www/html
```

O `install.sh` termina com três avisos `[OK]`: banco criado, variáveis configuradas e dependências instaladas.

**4. Corrija a senha do login.** A senha `dbseller` do README não bate com o banco (dá "Senha Inválida"). Rode uma vez:

```bash
docker exec ecidade_database psql -U postgres -d ecidade -c "update configuracoes.db_usuarios set senha='699f20e7463e44c725953babb3a499fb34259571' where id_usuario=1"
```

Agora entre em `http://localhost:8080` com **login `dbseller` e senha `dbseller`**.

**5. O `gunzip` deixa o Git sujo.** Ele apaga `docker/database/ecidade_base.sql.gz` (versionado) e cria `ecidade_base.sql`. Não faça commit desses dois arquivos.

## PHP 8.4 (a partir da semana 2)

O PHP 8.4 roda como um segundo container, usando o mesmo código e o mesmo banco. Faça **depois** dos passos acima.

```bash
docker compose -f docker-compose.yml -f docker-compose.php84.yml up -d --build ecidade_php84
docker exec ecidade_php84 mkdir -p extension/log tmp
docker exec ecidade_php84 chmod -R 777 extension/log tmp
```

Abra `http://localhost:8084`. As duas versões ficam lado a lado: `:8080` é o PHP 5.6 (o que funciona) e `:8084` é o PHP 8.4 (o que estamos migrando).

**Cuidados:**

- **Não rode o `install.sh` no container 8.4.** O `composer.json` chama `php5.6` fixo, então a instalação só funciona no container 5.6.
- **Ele vai dar erro no começo.** É esperado: o núcleo ainda não foi migrado. O primeiro erro conhecido está em `libs/db_stdlib.php` (chaves `{}` para ler caractere de string, linhas 149 e 155).
- **O sistema esconde avisos do PHP.** A configuração `php.error_reporting` em `config/application.php` desliga avisos, notices e deprecations. Para ver tudo, troque por `E_ALL` (esse arquivo não é versionado). Com `E_ALL`, o tratador de erros `src/V3/Error/Handler/Error.php` quebra, porque o PHP 8 não envia o 5º parâmetro.
- **Os logs ficam em** `extension/log/error.log` (do sistema) e `/var/log/php_errors.log` (dentro do container).
- **Para ver erros de sintaxe de um módulo sem precisar do login funcionando:** `docker exec ecidade_php84 php -l /var/www/html/ARQUIVO.php`.
