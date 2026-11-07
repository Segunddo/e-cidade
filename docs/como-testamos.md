# Como as telas e os POSTs são testados

Oct 25, 2026 · @Diego

**Para quem quer entender, ou repetir, como se prova que uma tela migrada para o PHP 8.5 se comporta igual à original.** A primeira parte descreve os testes automáticos que produzem os números do trabalho. A segunda ensina a fazer a mesma verificação à mão, pelo navegador e pelo banco, sem rodar script nenhum. No fim há um roteiro curto de demonstração.

O registro completo, com cada número e cada defeito encontrado, fica em `docs/registro/` (índice no fim do `CLAUDE.md`). O passo a passo do porte de um módulo está em `docs/migrar-um-modulo.md`.

## 1. A ideia central: o sistema antigo é o gabarito

A migração não troca o PHP 5.6 pelo 8.5 de uma vez. As duas versões rodam **lado a lado**, sobre o **mesmo código** e o **mesmo banco**:

```
                     ┌──────────────────────────┐
  :8080  ──────────► │ PHP 5.6  (original)      │ ──┐
                     └──────────────────────────┘   │
                     ┌──────────────────────────┐   ├──► mesmo PostgreSQL
  :8085  ──────────► │ PHP 8.5  (migrado)       │ ──┘    mesma sessão
                     └──────────────────────────┘        mesmo código-fonte
  :8090  ──► nginx: telas migradas → 8.5, o resto → 5.6   (é o endereço de uso)
```

Como código, banco e sessão são os mesmos, **a única diferença entre as duas portas é a versão do PHP**. Então o teste é simples de enunciar: fazer o mesmo pedido às duas e comparar as respostas. Se forem iguais, a migração preservou o comportamento. Se diferirem, o PHP 8.5 está fazendo algo que o 5.6 não fazia.

**Equivalente não é o mesmo que correto.** Se a tela original já calculava errado, a migrada deve calcular **o mesmo errado**. O objetivo é migrar, não consertar. Corrigir um defeito antigo mudaria a saída do 5.6, e aí não haveria mais gabarito.

### Por que não basta "abrir a tela e ver se carrega"

O defeito mais grave encontrado no projeto não dá erro nenhum. No PHP 5.6, `0 == ""` é verdadeiro; no 8.5, é falso. As classes de dados usam essa comparação para decidir se leem o valor digitado no formulário:

```php
var $cm34_tipo = 0;
$this->cm34_tipo = ($this->cm34_tipo == "" ? <valor do formulário> : $this->cm34_tipo);
```

No 8.5 o valor digitado nunca é lido. A tela abre normalmente, o botão funciona, e o registro é recusado ("campo não informado") ou gravado com `0`. Quem só olha se a tela carrega não vê nada. Por isso os testes comparam o **conteúdo** da resposta e o **SQL gravado**, não apenas a ausência de erro.

## 2. Preparação comum a todos os testes

1. Suba o ambiente (comandos no topo do `CLAUDE.md`, seção *Como subir o ambiente*).
2. Faça login **uma vez**, em `http://localhost:8090` ou `http://localhost:8080`, com `dbseller`/`dbseller`. O login só funciona no 5.6, porque passa pelo Laravel 5.4, que não roda no PHP 8.
3. O login grava um arquivo de sessão no volume compartilhado, e os dois PHPs o leem. Os testes automáticos precisam do **id dessa sessão** (o SID):

```bash
docker exec ecidade_php56 sh -c 'ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_*) | head -1' | sed 's#.*/sess_##'
```

Cada requisição regrava a sessão. Por isso os scripts tiram uma cópia dela no início e a restauram antes de **cada** pedido. Sem isso, o segundo pedido já encontraria um estado diferente do primeiro.

## 3. Os testes automáticos

São quatro níveis, do mais barato ao mais completo. Cada um cobre algo que o anterior não enxerga.

| Nível | O que compara | Ferramenta | Pega |
|---|---|---|---|
| 0. Sintaxe | o arquivo compila nos dois PHPs? | `php -l` | erro de compilação |
| A. Telas (GET) | o HTML/PDF de cada tela, byte a byte | `scratchpad/cmp.py` | erro, campo sumido, layout de relatório |
| 1. Escrita em memória | o estado do objeto depois de ler um formulário | `scratchpad/escrita.php` | o `0 == ""` em todas as classes de dados |
| 3. POST real | o SQL que cada PHP grava no banco | `scratchpad/escrita_post.py` | tudo no caminho de gravação, ponta a ponta |

### 3.1 Sintaxe: `php -l` nos dois PHPs

Todo arquivo alterado precisa compilar **nos dois** runtimes, porque os dois servem o mesmo arquivo. É a verificação mais fraca: no projeto inteiro só 87 arquivos falham na sintaxe do 8.5, enquanto o `0 == ""` sozinho tem mais de 19 mil ocorrências que compilam perfeitamente.

```bash
docker exec -i ecidade_php56 php -l /var/www/html/<arquivo> </dev/null
docker exec -i ecidade_php85 php -l /var/www/html/<arquivo> </dev/null
```

O `</dev/null` é obrigatório dentro de um laço `while read`. Sem ele, o `php` consome o resto da lista e o laço termina na primeira volta, dizendo "0 erros".

### 3.2 Telas: a bateria GET (`cmp.py`)

Para cada tela de um prefixo, o comparador restaura a sessão, pede a tela ao 5.6, restaura de novo, pede ao 8.5 e compara as duas respostas byte a byte.

```bash
python3 scratchpad/cmp.py <SID> '^cem[0-9]*_'                          # todas as telas do Cemitério
ONLY="cem1_campas001.php,cem2_renovacoes.php" python3 scratchpad/cmp.py <SID> '^cem'   # só algumas
```

A saída lista as divergentes e termina com um resumo:

```
  DIVERGE cem1_xxx.php  56=200/18668B  85=500/4558B
=== 114/116 identicas, 2 divergentes, 0 timeout ===
```

Três detalhes fazem dessa comparação um teste confiável, e não uma fonte de alarmes falsos:

- **Normalização.** Algumas partes da página mudam a cada pedido, mesmo sem migração: id de sessão, nome de arquivo temporário, data gravada dentro do PDF, a porta na URL da página de erro. O comparador troca essas partes por um marcador antes de comparar. Cada regra nasceu de um falso positivo real; a lista está no início do `cmp.py`.
- **Confirmação.** Antes de acusar uma divergência, ele refaz o par de pedidos. Uma regressão real é persistente; um relógio que virou de segundo entre os dois pedidos, não.
- **Timeout não conta como igual.** Se um dos lados não responde, a tela vai para a coluna `TIMEOUT`, e o processo que ficou rodando no servidor é encerrado. Antes dessa regra, uma tela travada nos dois lados contava como idêntica e ainda travava as telas seguintes.

**Limite:** a bateria só faz GET, sem parâmetros. Ela prova que a tela abre igual, não que grava igual. Para isso existem os níveis 1 e 3.

### 3.3 Escrita em memória: nível 1 (`escrita.php`)

Testa as **classes de dados** (`classes/db_<tabela>_classe.php`) sem banco e sem HTTP. Para cada classe, preenche o "formulário" com valores conhecidos (`1012`, `1013`…), chama o método que lê o formulário (`atualizacampos()`) e imprime o valor final de cada campo. Roda nos dois PHPs e compara.

```bash
cp scratchpad/escrita.php scratchpad/porclasse.sh ecidade/tmp/
# lista.txt: um caminho de classe por linha, ex.: classes/db_cgm_classe.php
for v in 56 85; do
  docker exec -i ecidade_php$v sh /var/www/html/tmp/porclasse.sh /var/www/html/tmp/escrita.php \
    < lista.txt | sort > escrita_$v.txt
done
diff escrita_56.txt escrita_85.txt && echo "nenhum campo diferente"
```

`porclasse.sh` roda uma classe por processo, para que um erro fatal numa classe não interrompa as outras e as faça parecer "iguais" por falta de saída.

Com o `0 == ""` sem correção, a diferença aparece assim:

```
5.6:  z01_numcgm='1012'
8.5:  z01_numcgm=0          <- o valor do formulário não foi lido
```

É barato (segundos para centenas de classes) e cobre a maior parte das correções do projeto. Mas não passa pela tela, pela validação dela nem pelo banco.

### 3.4 POST real: nível 3 (`escrita_post.py`)

É o teste mais completo: envia o **mesmo formulário** às duas portas, como um usuário faria, e compara o **SQL que cada PHP gravou** no banco.

O obstáculo é que os dois PHPs usam o mesmo banco. Se o 5.6 grava um registro, o 8.5 já encontra o banco diferente. O script resolve isso assim:

```
1. foto das tabelas envolvidas e das suas sequências (numeradores)
2. POST no 5.6   → captura, pelo log do PostgreSQL, o SQL gravado
3. restaura as tabelas e as sequências para a foto
4. POST no 8.5   → captura o SQL gravado
5. restaura de novo  → o banco termina como começou
6. compara o SQL de negócio dos dois lados
```

Para capturar o SQL, o PostgreSQL precisa registrar cada comando. Ligue isso antes e desligue depois:

```bash
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade SET log_statement='all';"

python3 scratchpad/escrita_post.py <SID> <tela.php> <tabelas,separadas,por,vírgula> '<campos do formulário>'

docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade RESET log_statement;"
```

Exemplo real, com resultado:

```
  snapshot: assentamentofuncional=0 linhas  assenta=0 linhas  | sequencias=1
  destes, escrita de NEGOCIO: 5.6=3  8.5=3
    5.6> insert into assenta( h16_codigo ,h16_regist ,h16_assent ,... ) values ( 4 ,1 ,1 ,...
    8.5> insert into assenta( h16_codigo ,h16_regist ,h16_assent ,... ) values ( 4 ,1 ,1 ,...
  == SQL de escrita de NEGOCIO IDENTICO nos dois runtimes ==
```

**Os quatro resultados possíveis:**

| Resultado | Significa | O que fazer |
|---|---|---|
| `IDENTICO` | os dois PHPs gravaram o mesmo SQL | nada: é o que se quer |
| `DIVERGE` | gravaram SQL diferente | investigar; às vezes é só um numerador de uma tabela que não estava na foto |
| `INCONCLUSIVO` | nada foi gravado nos dois lados | o formulário enviado não passou na validação da tela; ajustar os campos |
| `ABORTADO` | o banco recusou a restauração por chave estrangeira | a tela grava também numa tabela filha; acrescentá-la ao 2º argumento, **antes** da mãe |

`INCONCLUSIVO` não é aprovação. Sem essa regra, um formulário errado que não grava nada nos dois lados aparecia como "idêntico" e dava a impressão de teste feito.

**Escrita de negócio e escrita de infraestrutura.** Cada pedido também grava auditoria e sessão (`db_acount*`, `db_usuariosonline`…). Essas linhas carregam hora e numeradores próprios e diferem por natureza. O script as separa e compara só o que a tela grava de fato.

**Montar o formulário é a parte cara.** `scratchpad/payload_auto.py <SID> <tela.php>` lê o formulário que o 5.6 emite e gera um primeiro rascunho (nomes reais dos campos, botão certo, opções dos `<select>`). Em cerca de metade das telas ele basta. Nas outras é preciso ajustar à mão; as causas que já apareceram estão no `CLAUDE.md` (seção do nível 3 em RH) e os formulários que funcionaram ficam em `scratchpad/n3_rh_payloads.tsv`:

- a chave é digitada pelo usuário, porque a tabela não tem numerador automático;
- a tela é um contêiner com abas, e o formulário real está numa tela interna (`*004.php`);
- a gravação é feita por JavaScript, que chama um `.RPC.php` com JSON;
- a tela precisa de dados que a base de exemplo não tem. Nesse caso semeiam-se os registros mínimos, roda-se o teste e apaga-se tudo no fim. Foi assim no cálculo da folha e no estágio probatório.

#### A demonstração pronta

`scratchpad/demo_nivel3.sh`, sem argumentos, faz o nível 3 na tela onde o `0 == ""` foi descoberto (Cemitério → Tipos de isenção → Inclusão), em três rodadas:

1. código migrado → `IDENTICO`
2. correção desfeita temporariamente → `DIVERGE` (o 8.5 não grava nada: o teste **pega** o defeito)
3. correção restaurada → `IDENTICO`

A rodada 2 é a que prova que o teste funciona: um teste que nunca falha não prova nada. O script devolve o arquivo ao estado do git e desliga o log do banco no fim, mesmo se algo falhar no meio. Também aceita uma tela qualquer: `scratchpad/demo_nivel3.sh <tela.php> <tabelas>`.

## 4. Como testar à mão

Tudo o que os scripts fazem pode ser repetido pelo navegador e por um cliente do banco. É mais lento, mas mostra o mecanismo sem intermediários.

### 4.1 Duas janelas, dois navegadores

O login só funciona no 5.6, e a sessão do e-cidade é presa à janela. Para ter as duas versões abertas sem que uma atrapalhe a outra, use **dois navegadores diferentes** (por exemplo Firefox e Chrome), ou um navegador normal e uma janela privada:

| Janela | Endereço | O que você vê |
|---|---|---|
| A, "original" | `http://localhost:8080` | todo o sistema no PHP 5.6 |
| B, "migrado" | `http://localhost:8090` | as telas migradas no PHP 8.5; o resto no 5.6 |

Faça login nas duas com `dbseller`/`dbseller`. A porta `8085` (8.5 direto) não serve para navegar, porque nela não há login.

**Como saber qual PHP serviu a tela.** Na janela B, abra as ferramentas do navegador (F12) → aba **Rede**, recarregue a tela e clique no pedido dela. O cabeçalho de resposta `X-Ecidade-Runtime` diz `PHP-8.5 (migrado)` ou `PHP-5.6 (referencia)`. Confira isso antes de tirar qualquer conclusão: algumas telas de menu migradas só redirecionam para outra tela que ainda roda no 5.6 (por exemplo, eSocial → Cadastro de Formulários vai para `hab1_avaliacao002.php`, de Habitação).

### 4.2 Teste manual de tela (GET)

1. Abra a mesma tela nas duas janelas, pelo mesmo caminho de menu.
2. Compare o que aparece: campos, rótulos, listas de opções (`<select>`), valores já preenchidos, botões.
3. Em relatórios, gere o PDF nas duas com os mesmos filtros e compare as páginas.

Os defeitos encontrados nesse nível foram quase todos **sutis**: um campo de descrição que some, uma lista que vem vazia, uma coluna do relatório que desce de linha. Olhe com atenção o que está faltando, não só se há mensagem de erro.

Para uma comparação exata da mesma tela, sem depender do olho, use a bateria só nela:

```bash
ONLY="<tela.php>" python3 scratchpad/cmp.py <SID> '^<prefixo>'
```

### 4.3 Teste manual de gravação (POST)

Os dois PHPs gravam no mesmo banco. O teste manual é: incluir o mesmo registro em cada janela e comparar as linhas gravadas. Exemplo com a tela onde o `0 == ""` apareceu.

**Tela:** Cemitério → Cadastros → Tipos de Isenção → Inclusão (`cem1_cemiterioisencao001.php`).

1. Conecte um cliente ao banco (pgAdmin, ou `docker exec -it ecidade_database psql -U postgres -d ecidade`). Veja o que existe antes:

   ```sql
   SELECT * FROM cemiterioisencao ORDER BY cm34_sequencial;
   ```

2. **Janela A (5.6):** inclua um tipo de isenção. Use uma descrição fácil de achar, como `TESTE_MANUAL_56`, e preencha tipo e data limite.
3. **Janela B (8.5):** inclua outro com os **mesmos valores**, mudando só a descrição para `TESTE_MANUAL_85`.
4. Compare as duas linhas:

   ```sql
   SELECT * FROM cemiterioisencao WHERE cm34_descricao LIKE 'TESTE_MANUAL%';
   ```

   Os campos devem ser iguais, exceto a descrição e o código sequencial, que é o próximo número disponível e por isso difere entre as duas inclusões.
5. Apague os registros de teste. O banco é compartilhado, e linhas esquecidas mudam o resultado dos testes seguintes:

   ```sql
   DELETE FROM cemiterioisencao WHERE cm34_descricao LIKE 'TESTE_MANUAL%';
   ```

**Como ver o defeito acontecer à mão.** Sem a correção do `0 == ""`, o passo 3 falha: a tela do 8.5 recusa a inclusão com "campo não informado", mesmo com o campo preenchido, e nenhuma linha `TESTE_MANUAL_85` aparece no passo 4. Para mostrar isso, não edite o código à mão: rode `scratchpad/demo_nivel3.sh`, que desfaz a correção só durante a rodada 2 e a restaura no fim.

**Para ver o SQL exato que cada janela gravou**, ligue o registro de comandos antes dos passos 2 e 3, acompanhe o log e desligue no fim:

```bash
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade SET log_statement='all';"
docker logs -f --since 1m ecidade_database 2>&1 | grep -ai 'insert into cemiterioisencao'
# ... faça as inclusões ...
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade RESET log_statement;"
```

O log do banco está em português (`ERRO:`, `INSTRUÇÃO:`), por causa do idioma configurado no PostgreSQL.

### 4.4 Cuidados no teste manual

- **Tabela vazia não testa nada.** A base de exemplo tem muitas tabelas vazias. Uma tela de consulta sobre uma tabela vazia mostra "nenhum registro" nos dois PHPs, e isso não prova que a consulta funciona. Cadastre dados primeiro, pelo próprio sistema.
- **Erro nos dois lados não é defeito da migração.** Se a tela quebra igual no 5.6, o defeito já existia. Exemplo: Pessoal → Tabelas → Cargos → Inclusão (`pes1_rhfuncao001.php`) para na metade da página nos dois, porque chama uma função (`isParaiba()`) que não existe no código.
- **Valor óbvio já ocupado.** Em Jurídico → Advogados → Inclusão, o CGM 1 é recusado como duplicado nos dois PHPs. Não é defeito: é o único advogado que já existe na base.
- **Apague o que incluir.** Os testes automáticos assumem o banco no estado original.

## 5. O que os testes provam, e o que não provam

**Provam:** que, para as telas e os formulários exercitados, o PHP 8.5 produz a mesma saída e grava o mesmo SQL que o 5.6, com o código e o banco fixos.

**Não provam:**

- que as regras de negócio estão corretas: o gabarito é o sistema antigo, com os defeitos dele;
- o comportamento com parâmetros que a bateria não envia: ela abre cada tela sem filtros;
- o JavaScript das telas: os testes automáticos não executam JavaScript;
- os dados de outra prefeitura: a base de exemplo é pequena, e muitas tabelas estão vazias.

Resultados atuais, por área: Tributário 2.154 de 2.160 telas idênticas, Educação 1.534 de 1.551 e Recursos Humanos 1.537 de 1.538. Toda divergência restante foi investigada, e nenhuma é defeito de migração. No POST real, 68 dos 70 cadastros de RH gravaram SQL idêntico; os 2 restantes quebram também no 5.6. Os detalhes de cada número estão no `CLAUDE.md`.

## 6. Roteiro de demonstração (cerca de 15 minutos)

1. **O ambiente.** `docker ps` mostra os quatro containers: PHP 5.6, PHP 8.5, banco e proxy.
2. **Duas versões, uma origem.** Na janela B (`:8090`), abra uma tela do Cemitério e mostre o cabeçalho `X-Ecidade-Runtime: PHP-8.5`. Abra o login e mostre `PHP-5.6`.
3. **O defeito invisível.** Mostre as duas linhas de código da seção 1 e explique por que a tela abre normalmente e mesmo assim grava errado.
4. **O teste que pega o defeito.** Rode `scratchpad/demo_nivel3.sh` e mostre a sequência `IDENTICO` → `DIVERGE` → `IDENTICO`.
5. **O mesmo, à mão.** Faça a inclusão da seção 4.3 nas duas janelas e mostre as duas linhas no pgAdmin. Apague-as no fim.
6. **Em escala.** Rode a bateria de um módulo pequeno, por exemplo `python3 scratchpad/cmp.py <SID> '^not[0-9]*_'` (Notificações, 14 telas), e mostre o resumo `14/14 identicas`.
