# Ambiente da regressão (`e74`) e laboratório Laravel

Para usar sem ler isto: `regressao/bin/regressao ambiente-sobe` / `ambiente-para` (explicação em
[`../COMO-USAR.md`](../COMO-USAR.md)). Aqui fica o que cada arquivo desta pasta sobe e por quê.

## Ambiente `e74` (base PHP 7.4)

`docker-compose.e74.yml` (projeto `-p e74`) sobe, com rede (`e74_ecidade74`) e volumes (`e74_sessions`, `e74_tmp`)
próprios:

| Contêiner | Porta | Papel |
|---|---|---|
| `ecidade74_php74` | 8074 | **referência** (gabarito): PHP 7.4 + Laravel 8 do PR #8, imagem de `docker/php74-apache` |
| `ecidade74_php85` | 8185 | **alvo PHP 8.5**: Dockerfile em `php85/` + `php85/paridade-74.ini` (php.ini alinhado ao do 7.4 no que muda a saída) |
| `ecidade74_proxy` | 8190 | uma origem só, como o usuário vai usar: `proxy/nginx-e74.conf` + `proxy/map-e74.conf` (hoje tudo vai ao 7.4; uma tela vai ao 8.5 com uma linha `<arquivo.php> php85;`) |
| `ecidade74_database` | nenhuma | PostgreSQL 16 (`docker/database`); a suíte fala com ele por `docker exec` e o recria do dump a cada bateria |

```bash
docker compose -p e74 -f regressao/lab/docker-compose.e74.yml up -d      # = regressao/bin/regressao ambiente-sobe (mais o laboratório)
docker compose -p e74 -f regressao/lab/docker-compose.e74.yml stop       # = regressao/bin/regressao ambiente-para
```

Não use `down` sem querer: ele remove os contêineres `ecidade74_*` e o banco volta vazio (o dump recria; os arquivos
locais do e-Cidade ficam). Instalação do zero passo a passo: [`../README.md`, seção 1](../README.md#1-pré-requisitos).
O ambiente não toca na pilha da raiz (`ecidade_*`, 8080/8085/8090) nem em outros projetos do host: nomes, portas, rede e
volumes são todos próprios. O proxy do grupo (`docker/proxy/*`, raiz) serve a pilha da raiz; o daqui é o
`proxy/*-e74.conf`.

## Laboratório Laravel (:8187)

`docker-compose.lar12.yml` (projeto próprio `e74-lar12`) sobe o contêiner `ecidade74_lar12` em
**http://localhost:8187**, o alvo padrão da bateria Laravel (`REGRESSAO_LARAVEL_NOVO_URL`; contêiner em
`REGRESSAO_CONTAINER_LARAVEL_NOVO`, ambos em `regressao/nucleo/ambiente.py`). O nome `lar12` é histórico: o alvo do
grupo é **Laravel 13 + Passport 13** (guia do grupo), que ainda não existe.

Hoje o laboratório roda o **mesmo runtime do `ecidade74_php85`** (imagem `ecidade74-php85:latest`, mesmos volumes e
`php85/paridade-74.ini`) sobre o código apontado por `LAR12_CODIGO`. O padrão é o `./ecidade` atual, ou seja: **ele mede
o Laravel 8 da base sob PHP 8.5**. Resultado: o Laravel 8 sobe, mas não emite token (`lcobucci/jwt` 3.4 testa a chave
com `is_resource()`), e a bateria Laravel dá um `ERRO_AMBIENTE` (`laravel:banco`). Detalhes em
`regressao/baseline/lab-lar12-resultado.md`.

```bash
# da raiz do repositório; requer o ambiente e74 no ar (rede, volumes, banco) e a imagem ecidade74-php85:latest
docker compose -p e74-lar12 -f regressao/lab/docker-compose.lar12.yml up -d
docker compose -p e74-lar12 -f regressao/lab/docker-compose.lar12.yml stop

# quando houver o código com o Laravel 13 (caminho absoluto, ou relativo a regressao/lab/)
LAR12_CODIGO=/home/<voce>/ecidade-laravel13 docker compose -p e74-lar12 -f regressao/lab/docker-compose.lar12.yml up -d --force-recreate

# rodada só do Laravel contra o laboratório (o console artisan usa o ecidade74_lar12)
regressao/.venv/bin/python -m regressao.laravel.bateria comparar --saida ~/rodadas/X --alvo http://localhost:8187
```

`LAR12_IMAGEM` troca a imagem (padrão `ecidade74-php85:latest`). O contêiner usa o banco `ecidade74_database` e a
rede `e74_ecidade74` (externos: `down` deste projeto não os remove). O código novo precisa trazer o próprio `vendor/` e
o `.env` (o contêiner não roda `composer install`). Logs: `docker exec ecidade74_lar12 tail /var/log/php_errors.log`;
o Laravel escreve em `storage/logs/laravel.log` do código montado (com o padrão, o mesmo arquivo da referência). O
`ecidade_lar12` (:8087) da pilha antiga não é usado nem tocado.
