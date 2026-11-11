# 🏙️ e-Cidade

O **e-Cidade** é um sistema integrado desenvolvido para a gestão municipal. Ele atende as áreas financeira, patrimonial, tributária, de recursos humanos, de educação e de saúde. A ferramenta é destinada ao uso diário por servidores públicos do município e também pelos cidadãos. Seu principal objetivo é automatizar, agilizar e simplificar os processos da administração pública, promovendo uma gestão mais transparente, eficiente e que melhore o atendimento à população.

---

## 🚀 Tecnologias e Requisitos

Este projeto é considerado legado e utiliza as seguintes tecnologias fundamentais:
*   **Backend:** PHP 5.6
*   **Frontend:** HTML e Javascript
*   **Banco de Dados:** PostgreSQL
*   **Servidor Web:** Apache ou Nginx

> ⚠️ **Atenção:** Devido aos requisitos legados (como o PHP 5.6), o uso do **Docker** é o ambiente de desenvolvimento fortemente recomendado. A instalação manual convencional encontra-se atualmente em construção.

---

## 📌 Repositórios de Código

O e-Cidade trabalha com um modelo de repositório oficial e um repositório espelho para facilitar as contribuições:

*   **Repositório Oficial (Portal do Software Público Brasileiro):** Localizado em http://softwarepublico.gov.br/gitlab/e-cidade/. Este é o ambiente institucional de referência, servindo sempre como a fonte oficial onde são mantidas as versões do projeto.
*   **Repositório Espelho (GitHub):** Disponibilizado em https://github.com/DBSeller/e-cidade, com o apoio e manutenção da DBSeller Serviços de Informática Ltda. Ele funciona como um ambiente colaborativo adicional que permite maior interação da comunidade e facilita o envio de contribuições via *issues* e *pull requests*.
*   **Sincronização:** Todo o código-fonte enviado e mantido no GitHub é refletido e incorporado no repositório oficial.

---

## ▶️ Como rodar o projeto hoje (migração para PHP 8 em andamento)

O projeto está sendo migrado de PHP 5.6 para PHP 8, e hoje roda com **dois runtimes lado a lado**, sobre o **mesmo banco**:

| Serviço | Container | Porta | Papel |
|---|---|---|---|
| PHP 5.6 | `ecidade_php56` | 8080 | referência; login, Laravel (`/v4/*`) e as telas ainda não migradas |
| PHP 8.5 | `ecidade_php85` | 8085 | telas já migradas |
| PostgreSQL 16 | `ecidade_database` | — | banco único, em LATIN1 |
| Proxy (nginx) | `ecidade_proxy` | **8090** | **use este endereço**: manda cada tela para o runtime certo |

O proxy decide pelo nome do arquivo (`docker/proxy/nginx.conf` e a lista `docker/proxy/faseb_map.conf`), e os dois runtimes
compartilham a sessão de login e o `/tmp` por volumes do Docker. Para quem usa, é um sistema só.

### Pré-requisitos

- **Docker** com o **Compose v2** (o comando é `docker compose`, com espaço) e **git**.
- **Linux, ou WSL no Windows** (trabalhe dentro do WSL, não em `C:\`): o repositório tem arquivos cujos nomes só diferem em
  maiúsculas e minúsculas, e o Windows não guarda os dois.
- **Espaço em disco**: as imagens ocupam ~3,7 GB e o banco ~2 GB. O log do container do banco cresce bastante com o uso (ver
  *Problemas comuns* abaixo).

### Passo a passo, do clone até rodando

**1. Clone o repositório e use a branch `base-php84`** (a versão oficial do grupo, com tudo o que já foi migrado):

```bash
git clone https://github.com/Segunddo/e-cidade.git
cd e-cidade
git checkout base-php84
```

> ⚠️ **Mantenha o nome da pasta `e-cidade`.** O Docker Compose usa o nome da pasta para nomear a rede (`e-cidade_ecidade`), e o
> PHP 8.5 e o proxy se conectam a ela por esse nome. Clonando com outro nome, os passos 6 e 7 falham.

**2. Crie os volumes compartilhados** (sessão de login e `/tmp`, usados pelos dois runtimes):

```bash
docker volume create ecidade_sessions
docker volume create ecidade_tmp
```

**3. Suba o PHP 5.6 e o banco**, já com a sessão compartilhada. Na primeira vez, o `--build` monta as imagens (uns 15 a 20 minutos):

```bash
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d --build
```

**4. Descompacte o banco e rode a instalação:**

```bash
docker exec ecidade_php56 gunzip -k docker/ecidade_base.sql.gz
docker exec -it ecidade_php56 bash docker/install.sh
```

O `-k` mantém o `.gz` original, que é versionado (sem ele, o git passa a mostrar o arquivo como apagado). O `install.sh` cria o
banco, gera o `.env` e o `libs/db_conn.php` e instala as dependências; ele termina com três avisos `[OK]`.

**5. Corrija a senha do login e ajuste as permissões:**

```bash
docker exec ecidade_database psql -U postgres -d ecidade -c "update configuracoes.db_usuarios set senha='699f20e7463e44c725953babb3a499fb34259571' where id_usuario=1"

docker exec -u root ecidade_php56 sh -c 'chmod 1777 /tmp; cd /var/www/html; chmod -R 777 storage bootstrap/cache; chmod 777 extension/log tmp arquivos; chmod 666 extension/log/*.log; true'
```

A senha `dbseller` do arquivo de instalação não bate com o banco (dá "Senha Inválida") sem o `update`. As permissões evitam três
falhas conhecidas: o volume do `/tmp` nasce sem permissão de escrita; sem `tmp/` e `arquivos/` graváveis, relatórios falham antes
de gerar; e sem os arquivos de `extension/log` graváveis, toda tela autenticada dá erro 500.

**6. Suba o PHP 8.5:**

```bash
docker compose -f docker-compose.php85.yml up -d --build
```

**7. Suba o proxy:**

```bash
docker compose -f docker-compose.proxy.yml up -d
```

**8. Acesse http://localhost:8090** com **login `dbseller` e senha `dbseller`**.

Para saber qual runtime atendeu uma tela, veja o cabeçalho `X-Ecidade-Runtime` da resposta (no navegador: ferramentas do
desenvolvedor → Rede → cabeçalhos da resposta) ou pelo terminal:

```bash
curl -sI http://localhost:8090/login.php           | grep -i x-ecidade   # PHP-5.6 (referencia)
curl -sI http://localhost:8090/sau1_sau_cid001.php | grep -i x-ecidade   # PHP-8.5 (migrado)
```

As portas 8080 (só PHP 5.6) e 8085 (só PHP 8.5) continuam acessíveis para depuração. O 8085 não tem login próprio: ele usa a
sessão aberta pelo 8090 ou pelo 8080.

### No dia a dia

- **Depois de reiniciar a máquina** os containers ficam parados. Religue **nesta ordem** (o PHP 8.5 e o proxy dependem da rede
  criada pelo PHP 5.6):

  ```bash
  docker start ecidade_database ecidade_php56
  docker start ecidade_php85 ecidade_proxy
  docker exec -u root ecidade_php56 chmod 1777 /tmp
  ```

- **Para parar:** `docker stop ecidade_proxy ecidade_php85 ecidade_php56 ecidade_database`.
- ⚠️ **O banco não tem volume de persistência.** `docker stop`/`docker start` preservam os dados, mas **`docker compose down`
  apaga o container do banco e todos os dados**; nunca use `--remove-orphans`, que apagaria os quatro containers. Se o banco for
  perdido, repita os passos 3 a 5.
- **O PHP 8.4** (versão-alvo do grupo) tem um serviço próprio, que o proxy não usa:
  `docker compose -f docker-compose.yml -f docker-compose.php84.yml up -d --build ecidade_php84` (porta 8084; ver o cabeçalho do
  `docker-compose.php84.yml`). Atenção: esse arquivo monta a raiz do repositório (`./`), e não `./ecidade/`, onde o código fica
  desde a reorganização das pastas.

### Problemas comuns

- **Erro 500 em toda tela depois de logar:** os arquivos de `ecidade/extension/log/` perderam a permissão de escrita; repita o
  `chmod` do passo 5.
- **Disco enchendo:** o log do container do banco registra todo erro de SQL e cresce para gigabytes. Para zerá-lo sem tocar nos dados:

  ```bash
  sudo truncate -s 0 $(docker inspect -f '{{.LogPath}}' ecidade_database)
  ```

- **`network e-cidade_ecidade not found` nos passos 6 ou 7:** a pasta do clone tem outro nome (ver o aviso do passo 1) ou o PHP 5.6
  ainda não foi subido.
- **Mais detalhes do processo de migração** (estado, decisões, armadilhas): `CLAUDE.md` e `docs/registro/`.

---

## 🐳 Instalação com Docker (Recomendado)

> ℹ️ Esta é a instalação **original**, só com o PHP 5.6. Para rodar o projeto como ele está hoje, com as telas migradas para
> PHP 8, siga a seção **▶️ Como rodar o projeto hoje**, acima.

O projeto está configurado em containers para simplificar ao máximo sua execução e isolar o ambiente.

**Pré-requisitos:** Certifique-se de ter instalado o [Docker](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/) e o [Docker Compose](https://docs.docker.com/compose/install/#install-compose).

### Passo a Passo da Instalação

1.  **Clonar o projeto:**
    Baixe o repositório oficial em sua máquina e acesse a pasta gerada:
    ```bash
    git clone http://softwarepublico.gov.br/gitlab/e-cidade/e-cidade.git
    cd e-cidade
    ```
2.  **Subir os containers:**
    A partir do diretório raiz do e-Cidade, construa e inicie os serviços executando o comando abaixo:
    ```bash
    docker-compose up -d --build
    ```
    *Nota: Todos os containers possuem um volume mapeado da raiz do e-Cidade diretamente para a pasta `/var/www/html/` de cada container respectivo.*
3.  **Descompactar o banco de dados:**
    ```bash
    docker exec -it ecidade_php56 gunzip docker/ecidade_base.sql.gz
    ```
4.  **Executar o Script de Instalação:**
    Rode o script de instalação por dentro do container PHP:
    ```bash
    docker exec -it ecidade_php56 bash docker/install.sh
    ```
5.  **Ajustar permissões do sistema:**
    Na raiz do e-Cidade, aplique as permissões adequadas na pasta para garantir o funcionamento correto:
    ```bash
    docker exec -it ecidade_php56 chmod -R 775 /var/www/html
    ```
6.  **Acessar a Aplicação:**
    Após finalizar, o sistema estará pronto para acesso através do navegador nos seguintes endereços:
    *   http://localhost:8080
    *   http://127.0.0.1:8080
    
    **Credenciais Padrão de Acesso:**
    *   **Login:** `dbseller`
    *   **Senha:** `dbseller`

---

## 🧰 Solução de Problemas (Troubleshooting)

*   **A porta 8080 já está em uso?** Altere o arquivo `docker-compose.yml`, mudando a configuração de `8080:80` para outra porta disponível (ex: `8081:80`) e acesse através de http://localhost:8081.
*   **O script `install.sh` não foi encontrado?** Verifique se o seu terminal está no diretório correto (raiz do projeto) e se o arquivo reside no caminho `docker/install.sh`.
*   **Ocorreu erro de permissão no script?** Você pode conceder a permissão de execução usando o comando: `chmod +x docker/install.sh`.
*   **Deseja reinstalar (refazer o sistema e o banco)?** Remova tudo (volumes e imagens) com o comando `docker-compose down -v --rmi all` e, após isso, repita os passos 4 e 5 da instalação.

### Estrutura dos Containers

A arquitetura das imagens no Docker funciona com o seguinte roteamento:
```text
                              +----------+
                              |  browser |          
                              +----------+
                                |       |
                                |       |
                            +----------------+  
                            | localhost:8080 |
                            +----------------+  
                                |       |               
                                |       |             
                            +----------------+            
                            | ecidade-apache |            
                            +----------------+            
                                |        |                
                                |        |         
                            ____|        |_____           
                          /                   \          
                          /                     \         
                  +------------------------------------+
                  |           POSTGRES 5432            |
                  +------------------------------------+
```

---

## 🤝 Como Contribuir

A evolução contínua da ferramenta depende da comunidade, e contribuições são muito bem-vindas! Para contribuir, sugerimos utilizar o repositório espelho no GitHub seguindo este fluxo:

1.  Acesse o GitHub e clique em **Fork** no projeto.
2.  Crie uma nova *branch* para o seu desenvolvimento:
    ```bash
    git checkout -b minha-feature
    ```
3.  Implemente as correções ou melhorias necessárias.
4.  Realize o *commit* descrevendo a sua alteração:
    ```bash
    git commit -m "feat: descrição da alteração"
    ```
5.  Envie o código para o seu repositório (*fork*):
    ```bash
    git push origin minha-feature
    ```
6.  Acesse a página do repositório original e clique em **Compare & Pull Request**, fornecendo uma descrição clara da sua modificação.

---

## 📢 Comunicação e Suporte

*   **Grupo Oficial do Telegram:** Para comunicação direta, alinhamentos da comunidade, suporte e dúvidas, participe do canal através do link https://t.me/eCidadeCE.
*   **Registro de Problemas (Issues):** Para demandas técnicas específicas ou bugs, recomenda-se registrar uma *Issue* nos repositórios, a fim de manter a rastreabilidade do problema sempre que possível.