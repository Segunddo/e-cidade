# FrontController.php: lógica, rotas e compatibilidade
## Lógica do arquivo FrontController.php

    O código compara com o preg_match se no caminho da URL $_SERVER estão os files api/v1/, v4/ ou rest/v1/. 
    Se não houver um chamado para eles, os if's não serão executados e o arquivo app.php é carregado sem restrição de repetições. 
    Se estiverem sendo chamados, o código entra nos ifs e carregam os files (api/v1/ → api/api.php | v4/, rest/v1/ → public/index.php) 1 única vez durante a execução, impedindo o public/index.php de ser carregado 2 vezes sem necessidade.


## Rotas 
**PUBLIC/INDEX.PHP**

    Após direcionar os arquivos a serem tratados, o index.php inicializa e executa a aplicação Laravel importando pelo use Illuminate\Contracts\Http\Kernel; o contrato do kernel, responsável pelo processamento das requisições HTTP.
    Os arquivos de inicialização /../bootstrap.php e de compatibilidade libs/db_stdlib.php são carregados usando a função modification.
    No $app = require_once __DIR__.'/../bootstrap/app.php'; o boostrap configura a aplicação retornando o $app e montando o Laravel.
    O $kernel pede ao container da aplicação a instância do kernel e recebe o kernel HTTP, ele então coordena o processamento da requisição por meio do Laravel.
    Request::capture() cria o objeto da requisição a partir do HTTP recebido, que é processado pelo kernel e produz uma resposta.
    A resposta é enviada ao cliente e as tarefas do kernel são encerradas logo após.


**API.PHP**

    Após direcionar os arquivos a serem tratados, o api.php prepara e executa a API, primeiramente, importando as classes da API, dos provedores de serviços, da sessão, do banco de dados e do Silex que monta e executa tudo, além da inicialização única do bootstrap.php com os recursos básicos do sistema.
    O Silex cria o $app, ativa o modo de depuração e disponibiliza o class loader. No ApplicationConfig::APPLICATION_PREFIX as rotas são definidas registrando o ServiceControllerServiceProvider e o APIServiceProvider.
    O RouteConfig::isGuarded($ecidadeRequest->getUri()) definirá qual fluxo a API seguirá:
            →na rota protegida há o registro de provedores para conteúdo, consultas, banco, autenticação, sessão, persistência de dados do usuário e respostas, também incluindo a compatibilidade dbforms/db_funcoes.php. O finish destrói a sessão no fim e desconecta o banco.
            →a rota não protegida registra uma função before, executada antes, então a sessão se inicia, verifica se existe DB_login e, se houver, obtém os dados de conexão da sessão e cria a conexão PostgreSQL.
    O tratamento de erros $app→error(function (Exception $e, $code) use ($app)) transforma as exceções em JSON com statusCode e message, incluindo o stacktrace com a ativação do debug.
    $app->run(); inicia o tratamento da requisição: o Silex encontra a rota correspondente, executa os serviços e devolve a resposta.
    A compatibilidade é feita pela inclusão do require_once modification("libs/db_stdlib.php");.
    O código também prepara para utilizar os recursos de modifications do sistema, o código remove do REQUEST_URI trechos no formato /w/<número>. Depois cria objetos Front e EcidadeRequest, registra a requisição no Registry e chama createWindow().


## Compatibilidade

**FrontController.php:** usa recursos básicos de PHP (preg_match, require e require_once) e não chama APIs Laravel. Isso não comprova que os arquivos para os quais ele encaminha sejam compatíveis.
        *PHP 8.5 → Compatível,*
        *Laravel 12 → Desconhecido*

**public/index.php e inicialização Laravel:** o projeto fixa Laravel 5.4. em composer.json, e o lock registra 5.4.36 em composer.lock. Isso exclui Laravel 12. Para PHP 8.5, embora a exigência PHP do projeto seja aberta (>=5.6.4), há dependências travadas com limite <8.0.0; além disso, a biblioteca legada incluída usa each(), removida no PHP 8.
        *PHP 8.5 → Incompatível,*
        *Laravel 12 → Incompatível*

**api/api.php e dependências da API:** essa API usa Silex 2.2.4 e Symfony 3, não APIs Laravel diretamente. Porém, compartilha as dependências do projeto, que excluem PHP 8.5, e inclui a biblioteca legada que contém each(). Não há evidência suficiente para aprová-la com Laravel 12; ela não é, por si, uma aplicação Laravel.
        *PHP 8.5 → Incompatível,*
        *Laravel 12 → Desconhecido*

**bootstrap.php, bootstrap/app.php, app/Http/Kernel.php e libs/db_stdlib.php:** são partes compartilhadas ou necessárias aos fluxos acima. O bootstrap carrega dependências antigas; o Kernel e a configuração da aplicação pertencem à estrutura Laravel 5.4; e db_stdlib.php define print_vars() usando each().
        *PHP 8.5 → Incompatível,*
        *Laravel 12 → Incompatível* 


**Não foram feitos testes para determinar mais precisamente a compatibilidade.**