# Prova isolada do boot do Laravel 13

## Resultado

Foi criado um teste isolado com PHP 8.5.12 e Laravel 13.43.0. Ele executa o `bootstrap/app.php`
real do e-cidade, resolve o `App\Http\Kernel`, inicializa os providers incluídos no teste e carrega
as rotas reais: **1.412 rotas registradas**.

Com isso, a inicialização legada do container Laravel e o mapeamento atual das rotas funcionam
nesse recorte, sem alterar o Composer, o `vendor/` ou a configuração usados pela aplicação atual.
Isso **não significa que o Laravel inteiro ou a aplicação estejam migrados**.

## Como reproduzir

```bash
bash ecidade/tests/sistema/boot/roda-boot-85.sh
```

O perfil em `ecidade/tests/sistema/boot/` fixa `laravel/framework` em `13.43.0` e instala as
dependências em `runtime-85/boot-vendor/`. Não usa nem atualiza o `ecidade/vendor/` compartilhado.
O teste cria cache e storage temporários e os remove ao terminar.

O teste usa o `configuration/app.php` real como base, mas troca a lista de providers pelo conjunto
isolado descrito abaixo. Para evitar qualquer conexão com o banco compartilhado, configura SQLite
em memória. Nenhuma rota HTTP é executada e nenhum serviço externo é chamado.

## O que foi exercitado

- `App\Application` e seu caminho especial de configuração `ecidade/configuration/`.
- Os vínculos de kernels definidos em `bootstrap/app.php`; o kernel resolvido é o
  `App\Http\Kernel`.
- O boot de `AppServiceProvider`, `BroadcastServiceProvider`, `QueueServiceProvider`,
  `EventServiceProvider`, `RouteServiceProvider`, `CustomValidationProvider` e
  `PatrimonialServiceProvider`.
- O carregamento dos arquivos de rotas reais pelo `RouteServiceProvider`.

O provider de filas apenas registra callbacks; o teste não executa jobs. A conexão SQLite serve
somente para permitir que `AppServiceProvider` registre o listener de consultas.

## O que continua sem prova

O perfil não instala os pacotes específicos do restante da aplicação e, por isso, não carrega
todos os providers de `configuration/app.php`. Uma tentativa usando essa lista completa parou no
`Laravel\Tinker\TinkerServiceProvider`, que não existe no perfil mínimo — isso identifica uma
dependência ausente no teste, não uma falha confirmada do boot da aplicação.

Permanecem fora da prova:

- `AuthServiceProvider` e o Passport. O Composer principal ainda declara `laravel/passport ^10.0`,
  e esse provider chama `Passport::routes()`. A compatibilidade desse código com uma versão de
  Passport adequada ao Laravel 13 ainda precisa ser medida antes de alterá-lo.
- `Intervention\Image` e sua versão atual, `^2.7`.
- `Laravel\Tinker` com a versão compatível com Laravel 13.
- O pipeline de uma requisição HTTP, incluindo middlewares, autenticação, sessão e as rotas
  executadas. O teste registra as rotas, mas não as atende.
- O comando Artisan e o kernel de console em execução.

Portanto, o próximo passo para declarar o boot completo é resolver essas dependências no perfil
isolado, incluir os providers restantes um a um, e testar requisições com banco isolado e sem
integrações reais. Só depois de essa prova passar deve-se planejar a troca do `vendor/` e do
bootstrap de produção. Nenhuma alteração foi feita no bootstrap de produção.