# Ambiente: containers, proxy, sessão, /tmp, permissões e ferramental

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

### ARMADILHA (resolvida): uids no mesmo bind mount

Os dois containers montam o mesmo diretório. **Ambos rodam `www-data` como uid 33** — isso é
deliberado e precisa continuar assim: garante que a única variável entre os ambientes seja a
versão do PHP.

Houve uma tentativa de remapear o 8.5 para uid 1000 (para casar com o dono dos arquivos no
host). **Foi revertida**, porque criou duas quebras reais e enganosas:

1. Criar `extension/log/` pelo host (uid 1000) derrubou o **5.6** — o Logger lança exceção
   fatal quando não consegue escrever ali, e o :8080 passou a dar erro.
2. Depois, `application.log` criado pelo 5.6 (uid 33, modo 664) ficou ilegível para o 8.5
   (uid 1000), derrubando o :8085 numa tela do `tra` — sintoma que parecia falha de migração
   e era permissão de arquivo.

Requisito para as pastas de runtime:
```bash
chmod 777 extension/log && chmod 666 extension/log/*.log
```

### FERRAMENTAL: só `scratchpad/cmp.py` é versionado — o resto se perdeu

`scratchpad/` **não está no `.gitignore`, mas também nunca foi commitado**. Os scripts que
produziram os números deste arquivo — `incompat.py`, `depgraph.py`, `esforco.py`,
`afetados.txt` — **não existem mais em disco**. As medições continuam válidas (estão
registradas aqui), mas não são reproduzíveis sem reescrever as ferramentas.

O comparador de telas foi reescrito do zero **duas vezes** pelo mesmo motivo. Como as regras de
normalização dele *são* a metodologia acumulada — cada uma nasceu de um falso positivo real —
ele passou a ser versionado em **`scratchpad/cmp.py`**:

```bash
# restaura a sessao antes de cada requisicao e compara as duas portas
cd /home/diego/e-cidade
python3 scratchpad/cmp.py <SID> '^agua?[0-9]*_' divergentes.txt
ONLY="tela1.php,tela2.php" python3 scratchpad/cmp.py <SID> '^x_'   # subconjunto
```

Quem for regerar as outras ferramentas: commitá-las também.

### ⚠ CATEGORIA NOVA: AMBIENTE — o php.ini do 8.5 não reproduzia o do 5.6

Achada em `tre2_linha001.php`: HTTP 200 nos dois, **1 byte** no 8.5, nenhum fatal em log
nenhum. O arquivo começa com um **espaço antes do `<?php`**:

```
5.6  output_buffering = 4096  (php.ini do Ubuntu)  -> o espaco fica no buffer, a sessao abre
8.5  output_buffering = 0     (imagem sem php.ini) -> o espaco sai, os cabecalhos ja foram,
                                                      a sessao nao abre e a tela encerra
```

Corrigir no código mudaria a saída do `:8080` (é conserto, não migração). A correção fiel é de
**ambiente**: `docker/php85-apache/paridade-56.ini`, montado em `conf.d` por
`docker-compose.php85.yml`. **Não por rebuild**: o rebuild falhou sem rede para o
`deb.debian.org` e, pior, a camada do `apt` não estava em cache — reconstruir reinstalaria todos
os pacotes em versão nova, outra variável. Com o bind mount o binário segue **8.5.10**.

Comparadas as 228 diretivas dos dois runtimes web, há mais quatro que mudam saída e **não**
foram alinhadas, por falta de defeito observado (regra de corrigir na aparição):

| Diretiva | 5.6 | 8.5 | Risco |
|---|---|---|---|
| `serialize_precision` | 17 | -1 | `json_encode(0.1)` → `0.10000000000000001` × `0.1`; `.RPC.php` com dinheiro |
| `request_order` | GP | (vazio) | `$_REQUEST` passa a incluir cookies |
| `variables_order` | GPCS | EGPCS | `$_ENV` preenchido |
| `default_charset` | UTF-8 | ISO-8859-1 | só o cabeçalho HTTP |

Escala da forma achada: **3 scripts na raiz** com saída antes do `<?php` (`tre`, um `emp`, um
`sau`) — nenhum no Tributário, por isso nenhuma bateria anterior a viu.

#### ⚠ CORREÇÃO: 8 das 14 divergências "caracterizadas" do Tributário eram ESTA causa

Bateria completa depois do ini: **Fase A 1.807/1.813, Fase B 347/347 — 2.154/2.160**. Antes
eram 14 divergências; sobraram **6** (2 fragmentos do `agu`, `fis1_sanitario004`, as 3 do
`iss`). As 8 que sumiram — as 4 do `itb`, `cem1_itenserv002`, `jur_enviarremessatj`,
`fis1_tiafprazoproc002/003` — **quebram nos dois** e agora devolvem a **mesma** página de erro
(ex.: 500/4.558 B nos dois). O defeito é da referência, como estava registrado; mas a
*divergência* era o buffer: no 5.6 o tratador de erro descartava a saída retida e emitia o 500,
no 8.5 a saída já tinha ido e restava um 200 truncado.

**Lição:** "quebra no 5.6 e funciona no 8.5" era leitura errada do sintoma — o 8.5 não
funcionava, só não conseguia mais *dizer* que falhou. Paridade de ambiente faz parte da
invariante "a única variável é a versão do PHP", e ela nunca tinha sido medida diretiva a
diretiva.

### FERRAMENTAL: duas armadilhas de hoje

- **O harness não está no container.** `scratchpad/` fica na raiz, fora do bind mount
  (`./ecidade`). Chamado como `/var/www/html/scratchpad/escrita.php`, o php não acha o arquivo,
  a saída sai **vazia nos dois** e o diff vazio parece aprovação. Copiar com `docker cp` (a skill
  foi corrigida; o manual já fazia assim).
- **Lista sem `\n` final perde o último arquivo no `while read`.** O `enumera.py` gravava sem;
  o lint do `tre` verificou 59 de 60. Corrigido na origem.

### PERMISSÕES: `storage/` bloqueava o login nos DOIS ambientes

`storage/` e `bootstrap/cache` eram `775 diego`, e nenhum container (uid 33) conseguia escrever.
O Laravel falhava com `storage/logs/laravel.log ... Permission denied` e `/v4/oauth/token`
devolvia 500 **também no 5.6**. Corrigido com `chmod -R 777 storage bootstrap/cache`; depois
disso o 5.6 passou a emitir token válido (HTTP 200). Ambiente novo precisa desse passo.

## Comandos úteis

### PROXY REVERSO — origem única (montado e verificado) ⭐

**Use `http://localhost:8090`.** É o endereço do sistema durante a migração.

```
http://localhost:8090
   /tra1_*, /tra_*  ->  PHP 8.5   (módulo migrado)
   /*               ->  PHP 5.6   (login, /v4/* do Laravel, demais módulos)
```

Arquivos: `docker/proxy/nginx.conf` + `docker-compose.proxy.yml`. Cada resposta traz o
cabeçalho `X-Ecidade-Runtime` dizendo qual runtime a serviu — útil para demonstrar em banca
que a mesma sessão navega entre dois PHPs. Verificado: `/tra1_acidentes001.php` responde com
`X-Powered-By: PHP/8.5.10` e `/login.php` com o 5.6.

**Por que origem única é obrigatório, não conveniência:** a sessão do e-cidade é *por janela*
e presa à origem. Com 5.6 em :8080 e 8.5 em :8085 são origens distintas, e a janela aberta
pelo login não encontra a sessão do outro lado — o sintoma é "Sessão inválida (12)". Sob uma
origem só, o navegador envia os mesmos cookies para ambos.

**Para migrar o próximo módulo:** acrescente o prefixo dele à alternância `(?:cem|tra)` do
`location` no nginx. Essa linha é literalmente o avanço da migração.

**ARMADILHA `/w/<n>/` — o prefixo de janela do desktop v3.** Na navegação real pelo menu, as
URLs **não** são `/cem1_campas001.php` e sim `/w/2/cem1_campas001.php` — o desktop prefixa
tudo com o id da janela (ver `ECIDADE_REQUEST_PATH`). Um `location ~ ^/(cem|tra)_` casa só
o acesso direto ao arquivo e **nunca dispara na navegação real**: o sintoma é o módulo
continuar respondendo pelo 5.6 mesmo com o roteamento "verificado" por curl. O padrão correto
aceita o prefixo como opcional:

```nginx
location ~ ^(?:/w/[0-9]+)?/(?:cem|tra)[0-9]?_ { ... }
```

Verificado: `/cem1_campas001.php`, `/w/1/cem1_...` e `/w/2/cem1_...` respondem pelo 8.5,
enquanto `/w/2/extension/desktop/...` e `/w/2/skins/estilos.php` continuam no 5.6.

Para descobrir as URLs reais de um módulo, o log do proxy é a fonte definitiva:
`docker logs ecidade_proxy 2>&1 | grep -aoE '"(GET|POST) [^ ]+'`

**ARMADILHA MAIÚSCULAS — vale para o roteamento E para a enumeração.** O e-cidade tem
arquivos com o prefixo de módulo **capitalizado**: `Cem1_legista001.php`, `Con1_*`, `Cai1_*`,
`Amb1_*`, `Cus1_*`. São **29 na raiz** (Con1 9, Cai1 6, Amb1 6, Cus1 5, Cem1 3), de 15.694.

Poucos, mas causam duas falhas silenciosas distintas:

1. **Roteamento:** `location ~ ` é sensível a caso, então essas telas continuam no 5.6
   mesmo com o módulo portado — sem erro, só o `X-Ecidade-Runtime` denunciando. Corrigido
   usando **`location ~*`** (insensível a caso).
2. **Enumeração:** o levantamento do módulo com `re.match(r"^cem[0-9]*_", f)` também é
   sensível a caso e **deixou 3 arquivos fora do porte** — dois deles ainda com `parse_str`
   de 1 argumento. Detectado pelo usuário navegando a tela, não pelas verificações.

**Ao enumerar um módulo, usar sempre `re.IGNORECASE`:**
```python
re.match(r"^cem[0-9]*_", f, re.IGNORECASE)
```

Lição: uma verificação que só testa os nomes que a própria enumeração gerou nunca encontra
o que a enumeração deixou de fora. Vale conferir `ls | grep -iE '^<prefixo>[0-9]*_'` contra
a lista enumerada antes de dar o módulo por concluído.

**ARMADILHA `Host $host` vs `$http_host`:** o e-cidade monta URLs absolutas a partir de
`HTTP_HOST` (ver `$DB_URL_ABS` em `libs/db_stdlib.php`). A variável `$host` do nginx
**descarta a porta**; com ela o sistema gerava `http://localhost/skins/estilos.php?...`,
o navegador buscava na porta 80 e **a tela vinha inteira sem CSS, JS nem fontes**. Usar
sempre `proxy_set_header Host $http_host;`, que preserva `localhost:8090`. Sintoma
enganoso: parece falha de migração e é configuração de proxy.

Nota operacional: o nginx.conf entra por bind mount de **arquivo único**; editar o arquivo no
host cria um inode novo e o container continua com o antigo. Depois de editar, use
`docker compose -f docker-compose.proxy.yml up -d --force-recreate` (um `nginx -s reload` não basta).

### `/tmp` COMPARTILHADO — obrigatório, como a sessão (montado e verificado)

Volume Docker externo `ecidade_tmp`, montado em `/tmp` nos **dois** containers.

**Por que:** `dbforms/db_classesgenericas.php` usa `tempnam()` para gerar
`/tmp/iframe<aleatório>.php` e devolve ao navegador um iframe apontando para
`dbforms/db_classes_iframe_alterar_excluir.php?arquivo=<base64 do caminho>`.

Com dois runtimes isso quebra de forma espetacular: a tela do módulo migrado é servida pelo
**8.5** e grava o temporário no `/tmp` dele, mas `dbforms/` **não casa com o regex do proxy**
e a requisição do iframe vai para o **5.6**, que não encontra o arquivo. O iframe erra e
repete — **loop infinito de POSTs**.

Sintomas medidos antes da correção:

```
6.717 requisições a itb1_itbitransacao111.php no log do proxy
7.847 arquivos /tmp/iframe*.php órfãos no container 8.5   (contra 69 no 5.6)
```

No navegador: primeira requisição GET com iniciador `subdocument`, seguida de dezenas de
POSTs com iniciador `db_classes_iframe_alterar_excluir.php`. **Não acontece no :8080 puro** —
só na origem mista, o que o torna um falso "defeito da migração do módulo".

Verificado depois da correção: o mesmo fluxo devolve **HTTP 200 / 3.057 bytes idênticos**
pelo `:8080` (puro 5.6) e pelo `:8090` (misto).

**Regra geral que decorre disso:** os dois runtimes precisam compartilhar **todo estado de
runtime**, não só o banco. Já são três: banco, sessão (`/var/lib/php/sessions`) e agora
`/tmp`. Ao encontrar comportamento estranho que só ocorre no `:8090`, suspeitar primeiro de
estado não compartilhado, antes de procurar defeito de porte.

### Sessão compartilhada entre os runtimes (montada e verificada)

Volume Docker externo `ecidade_sessions`, montado em `/var/lib/php/sessions` nos **dois**
containers; o 8.5 tem `session.save_path` apontado para lá. Verificado: o 5.6 grava uma
sessão e o 8.5 a lê com o conteúdo correto.

Como o login roda no Laravel 5.4 (que não funciona em PHP 8), o fluxo do piloto é:
**autenticar em :8080 e navegar o módulo migrado em :8085 com a mesma sessão.** Cookies de
`localhost` não distinguem porta, então o navegador envia a sessão para as duas.

Detalhe da sessão do e-cidade: ela é **por janela**. O cookie `ECIDADEWINDOWMAIN` é o *nome*
da sessão (`session_name()`) e seu valor é o *id* (`session_id()`) — ver `src/V3/Window/Session.php`.
Não é `PHPSESSID`. Uma requisição consome/reescreve a sessão, então testes com curl precisam
recriá-la a cada chamada.

```bash
# ambiente de referência (PHP 5.6) + volume de sessão compartilhada
docker volume create ecidade_sessions
docker compose -f docker-compose.yml -f docker-compose.sessions.yml up -d   # :8080

# permissões exigidas por Laravel e pelo logger (senão /v4/oauth/token dá 500)
chmod -R 777 storage bootstrap/cache
chmod 777 extension/log
# sem isto os relatórios não são gerados e 11% das telas falham antes de executar
chmod 777 tmp arquivos

# ambiente de migração (PHP 8.5)
docker compose -f docker-compose.php85.yml up -d --build # :8085
docker compose -f docker-compose.php85.yml down

# erros do runtime 8.5
docker exec ecidade_php85 cat /var/log/php_errors.log
tail -f extension/log/error.log        # log da própria aplicação

composer test                 # vendor/bin/phpunit
npx cypress open              # specs em tests/cypress/integration
```
