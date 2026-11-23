# Catálogo de incompatibilidades e método de verificação

> Movido do `CLAUDE.md` em 26/10/2026, sem alteração de conteúdo. Índice no `CLAUDE.md`,
> seção *Onde está cada coisa*.

### ARMADILHA DE MEDIÇÃO: `php -l` dentro de `while read` engole a lista

```bash
while read f; do php -l "$f" | grep -q "No syntax errors" || echo "$f"; done < lista.txt
```

**Isto não verifica a lista.** O `php` (e o `docker exec`) herdam o stdin do laço e consomem
o resto do arquivo. O laço dá uma volta só, e o resultado é um tranquilizador "0 arquivos com
erro" — foi exatamente o que a primeira medição de `dbagata/` devolveu, escondendo os 11.

Correção: `php -l "$f" </dev/null` (e `docker exec -i` com o redirecionamento explícito).

Mesma família das outras armadilhas deste arquivo: **uma verificação que falha em silêncio é
pior que verificação nenhuma**, porque encerra a investigação.

### CRÍTICO: `modification()` troca o arquivo executado em tempo de execução

**O arquivo que você edita em `libs/` pode NÃO ser o que roda.**

Todo include legado passa por `include(modification("caminho"))`. A função `modification()`
(definida em `definitions.php`) consulta o usuário logado (`$_SESSION['DB_login']`) e, se
existir uma cópia personalizada, **devolve o caminho dela em vez do original**:

```
extension/modification/data/cache/user/<login>/<caminho original>
```

Hoje há **23 arquivos sobrescritos para o usuário `dbseller`** — entre eles quatro do núcleo:
`libs/db_stdlib.php`, `libs/db_conecta.php`, `libs/db_sessoes.php`,
`dbforms/db_classesgenericas.php` e `dbforms/db_funcoes.php`.

**Isso causou uma lacuna real no porte:** o núcleo foi corrigido nos originais, mas o runtime
de `dbseller` continuava carregando as cópias em `cache/`, que tinham exatamente as mesmas
incompatibilidades. Foram portadas depois (mesma receita); a árvore inteira (46 arquivos)
passa `php -l` no 8.5.

Detalhes operacionais:
- **A árvore é versionada** (desde o commit `88c53b8`). Só `extension/modification/log`
  segue no `.gitignore`. O motivo: as correções feitas nas cópias de `cache/` se perderiam
  numa limpeza da pasta, e o sistema voltaria a quebrar em PHP 8 mesmo com o porte aplicado.
- As cópias em `file/sync/user/<login>/` estão **vazias (0 bytes)** — quem executa é `cache/`,
  e ele **não é reproduzível** a partir do `sync`: é a única cópia dessas customizações.
- Os arquivos de `cache/` pertencem a `root`; para editá-los:
  `docker exec -u root ecidade_php56 chmod 666 /var/www/html/<caminho>`
- **Toda varredura e todo porte precisam incluir `extension/modification/`.** Medir só a
  árvore principal subestima o trabalho e deixa o runtime real sem correção.
- `vendor/dbseller/legacy/bootstrap/PHP_53.php` fornece polyfills (ex.: `session_is_registered`,
  removida no PHP 5.4). Por isso código que falha em teste CLI isolado funciona na web —
  **teste sempre pelo bootstrap da aplicação**, nunca com `php -r` puro.

### DUAS CATEGORIAS NOVAS descobertas no piloto

Nenhuma das duas aparece em varredura de texto; **só o `php -l` do PHP 8.5 as revela**.

**1. Assinatura incompatível com a classe pai (LSP)** — E_STRICT no PHP 5.6, **fatal desde o
PHP 7.0**. Ex.: `SuperScriptText::GetWidth(&$aImg)` sobrescrevendo `Text::GetWidth($aImg)`
(por referência vs. por valor), ou filha com menos parâmetros que a mãe. Regra de correção:
o **pai manda** na passagem por referência e nos defaults; o **filho mantém os nomes** dos
parâmetros (o corpo os usa) e herda os parâmetros extras opcionais.

**2. `=& new` (atribuição por referência de objeto novo)** — removida no PHP 7.0, gera
*parse error*. Base inteira: **8 arquivos / 25 ocorrências**. Desde o PHP 5 objetos já são
manipulados por handle, então remover o `&` é equivalente.

Como não são detectáveis por grep, a forma de medi-las na base inteira é rodar
`php -l` sob PHP 8.5 em todos os arquivos.

### ✅ MEDIÇÃO FEITA: `php -l` nos dois runtimes, na base inteira

**33.057 arquivos PHP** (excluindo `vendor/`, `node_modules/`, `.git`), com `</dev/null` para
o `php` não engolir a lista:

| | Arquivos com erro de sintaxe |
|---|---|
| PHP 5.6 | 101 (pré-existentes) |
| PHP 8.5 | 187 |
| **Só quebram no 8.5** | **87 — 0,26% da base** |

Distribuição: raiz **51**, `dbagata/` 10, `app/` 5, `src/` 4, `fpdf151/` 4, `model/` 3,
`libs/` 3, demais 7. Apenas **2** são da área Tributário ainda não portada.

Causas:

| Causa | Arquivos |
|---|---|
| `unexpected token "{"` — offset de string com chaves | 26 |
| `Invalid numeric literal` — octal inválido (`08`, `09`) | 6 |
| `unexpected token ";"` / `"["` | 9 |
| nome totalmente qualificado / `namespace` inesperado | 6 |
| **`Unparenthesized a ? b : c ? d : e`** — associatividade removida no PHP 8.0 | 3 |
| **`The (real) cast has been removed`** — PHP 8.0 | 1 |
| `Unterminated comment` | 1 |
| demais | 35 |

**Este número é o argumento central do trabalho, em uma linha.** A incompatibilidade que uma
ferramenta de sintaxe encontra na base inteira são **87 arquivos**. As categorias que
realmente custam — `0 == ""` (19.401 ocorrências), construtores PHP 4 (3.587 classes),
`sizeof(null)`, comparação de ordem com string — **não aparecem em nenhuma delas**. Um
`php -l` limpo em 100% da base não diria nada sobre o sistema calcular tributo errado.

Duas categorias novas apareceram só aqui, ambas fatais de compilação no PHP 8.0 e invisíveis
ao grep: **ternário aninhado sem parênteses** (`a ? b : c ? d : e`) e **cast `(real)`**.

### ✅ EXPERIMENTO: Rector 2.6.7 medido contra o porte manual do `div`

A pergunta "por que não usar o Rector?" era legítima e eu a respondia por raciocínio, não por
medição — violando o princípio do próprio projeto. O experimento: reconstruir o estado
**pré-porte** dos 163 arquivos que o commit do `div` alterou, rodar o Rector sobre eles, e
comparar três árvores — original, saída do Rector, meu resultado.

Config: `withPhpSets(php80: true)` — só os conjuntos de upgrade de versão, que é o "grupo (a)"
da taxonomia do TCC de referência. Rodou em 1m12s e parseou os short tags sem problema
(136 dos 163 arquivos usam `<?`).

#### Cobertura por categoria

| | ANTES | RECTOR | MEU |
|---|---|---|---|
| guarda `0 == ""` | 0 | **0** | **763** |
| `split(` restante | 381 | 1 | 0 |
| `parse_str` de 1 arg restante | 62 | 2 | 0 |
| construtor PHP 4 restante | 80 | 0 | 0 |
| offset `{}` restante | 2 | **0** | 0 |

#### Onde o Rector é melhor que o meu ferramental — e não é pouco

1. **Ele não toca em comentário.** Dois dos três "restantes" dele eram código comentado
   (`// $arr = split("-", ...)`). **Meu regex editou os dois**, porque não distingue código de
   comentário. Inofensivo aqui, mas é ruído no diff e revela a natureza do instrumento.
2. **Ele pegou o offset `$aDebitos[$i]->origem{0}`**, que meu regex não cobria — a lacuna de
   detecção que registrei na seção do `div` e que só o `php -l` tinha achado.
3. **Ele converte `split()` sempre para `preg_split`**, preservando a semântica POSIX do
   separador. Meu `porta.py` converte para `explode` e **aborta** quando o separador tem
   metacaractere. A solução dele é mais geral e dispensa a classificação manual.

#### Onde ele não serve — e por que isso decide a questão

**1. Zero guardas `0 == ""`.** As 763 correções — **58% do trabalho** — estão inteiramente
fora do alcance dele. Não é limitação da ferramenta: a guarda não é um upgrade, é um *shim*
que preserva a semântica do 5.6, e o código é válido nas duas versões.

**2. A saída dele NÃO roda em PHP 5.6.**

| | PHP 5.6 | PHP 8.5 |
|---|---|---|
| Saída do Rector | **19 de 163 com erro de sintaxe** | 0 |
| Meu resultado | **0** | 0 |

Causa: regras que emitem sintaxe de PHP 7+. Exemplo literal em `cai3_gerfinanc001.php:1753`:

```php
ANTES   if (!isset($certidao)) { ... }
RECTOR  $certidao ??= "";            // ??= e PHP 7.4 -> parse error no 5.6
MEU     if (!isset($certidao)) { ... }
```

Regras responsáveis: `IfToNullCoalescingAssignRector` (6), `ClosureToArrowFunctionRector` (4),
`TernaryToNullCoalescingRector` (3), `NullCoalescingOperatorRector` (3). **Isso quebra a
restrição central do strangler fig**: os dois containers montam o mesmo diretório, então um
arquivo que não parseia no 5.6 derruba a referência — que serve o login e todos os módulos
ainda não migrados.

**3. A regra de `parse_str` descarta variáveis do escopo, em silêncio.**

```
parse_str($s);            -> $foo existe em escopo        (comportamento do 5.6)
parse_str($s, $result);   -> $foo NAO existe; so $result  (verificado no proprio 5.6)
```

O Rector criou **60 chamadas com 2º argumento e acrescentou `extract()` em zero delas**
(24 `extract` antes, 24 depois). Nos 60 casos, as variáveis que o código legado importava do
query string deixam de existir — sem erro, sem aviso. Se quebra ou não depende de o código
adiante lê-las, o que exige análise caso a caso. Minha correção acrescenta
`extract($__qs)` nas 62, restaurando o escopo mecanicamente.

**4. Ele trocou `$HTTP_*_VARS` por `$_SERVER`/`$_POST` — 317 ocorrências em 67 arquivos.**
Exatamente a mudança registrada aqui como **não-mudança deliberada**: nesse ambiente os
`$HTTP_*_VARS` estão indefinidos (removidos no PHP 5.4) e o código se protege disso; trocá-los
**popula valores hoje vazios**. É mudança de comportamento, não migração.

#### SEGUNDA RODADA: a lista curada funciona — e o custo dela está medido

A pergunta seguinte era "então o Rector com regras escolhidas seria melhor?". Também medi.

Partindo dos conjuntos por versão e **excluindo 14 regras**, uma a uma com motivo:

| Motivo da exclusão | Regras | Efeito no 5.6 |
|---|---|---|
| emitem sintaxe de PHP 7+ | `IfToNullCoalescingAssign`, `ClosureToArrowFunction`, `TernaryToNullCoalescing`, `NullCoalescingOperator`, `ListToArrayDestruct`, `ClassPropertyAssignToConstructorPromotion`, `ChangeSwitchToMatch`, `ClassOnObject`, `StringableForToString`, `RemoveUnusedVariableInCatch` | *parse error* |
| emitem **função** que não existe no 5.6 | `StrStartsWithRector` (`str_starts_with`), `RandomFunctionRector` (`random_int`) | **fatal só em execução** |
| mudam comportamento | `ReplaceHttpServerVarsByServerRector`, `ParseStrWithResultArgumentRector` | silencioso |

Resultado: **129 arquivos alterados, 0 erro de sintaxe no 5.6 e no 8.5, 0 função ausente.**
A lista curada **satisfaz a restrição de dois runtimes.** A resposta é sim.

#### O que a lista curada cobre, e o que sobra

| | ANTES | CURADO | MEU |
|---|---|---|---|
| `split(` restante | 381 | **1** (é comentário) | 0 |
| construtor PHP 4 | 80 | **0** | 0 |
| offset `{}` | 2 | **0** | 0 |
| `parse_str` de 1 arg | 62 | **62** | 0 |
| guarda `0 == ""` | 0 | **0** | 763 |

Equivalência verificada nos dois runtimes para as 381 conversões — o Rector gera
`preg_split("#\##m", $x)` onde eu gero `explode("#", $x)`, e o resultado é `===` idêntico.

#### O custo que a pergunta esconde

**1. Duas das regras perigosas são invisíveis ao `php -l`.** `str_starts_with` e `random_int`
compilam no 5.6 e explodem em execução. Achei-as não por inspeção, mas perguntando ao próprio
runtime quais funções ele não conhece — **passo de verificação novo**, hoje na skill:

```bash
# funcoes que aparecem SO na saida do Rector, conferidas contra o 5.6
docker exec ecidade_php56 php -r 'foreach(file("lista.txt",2) as $f)
  if(!function_exists(trim($f))) echo trim($f),"\n";'
```

Sem ele, o lint diria "0 erros" e 93 arquivos quebrariam na tela.

**2. A exclusão é uma *denylist*, e denylist é frágil.** Uma atualização do Rector pode
acrescentar regras aos conjuntos por versão e reintroduzir o problema **em silêncio**. Um
`withRules()` (allowlist) seria mais seguro, mas exige reconfigurar regras como
`RenameFunctionRector`, que os conjuntos alimentam com o mapa de funções removidas.

**3. Uma das regras não é só desabilitável — precisa ser substituída.** Com
`ParseStrWithResultArgumentRector` excluída, os 62 `parse_str` ficam **intocados**: o
ferramental próprio continua necessário para eles. A ferramenta não sai de cena.

#### Resposta à pergunta, com o escopo certo

**SUPERADO — ver *DECISÃO: Rector adotado*.** Esta conclusão valia enquanto faltavam as regras
da camada semântica. Escritas (196 linhas), o Rector passou a fazer 100% do porte, e a resposta
deixou de ser "só a camada sintática".

*Texto original:* **Sim, para a camada sintática, e vale a pena a partir de `fis` (353) e `iss` (400)** — onde
o volume paga a montagem da lista. Para os sete prefixos pequenos restantes, montar e validar
a lista custa mais do que as poucas dezenas de correções sintáticas que ela faria.

E não substitui nada da camada semântica: as 763 guardas `0 == ""`, as guardas `pg_*`, os
casts e o `sizeof(null)` continuam sem regra equivalente.

**Portão de verificação obrigatório ao usar o Rector aqui**, nesta ordem: `php -l` nos dois
runtimes → conferência de funções contra o 5.6 → bateria byte-a-byte. O segundo é o que
nenhuma ferramenta de sintaxe faz por você.

#### Ressalva honesta: isto não prova que o Rector é inútil aqui

Os problemas 2 e 4 vêm dos **conjuntos por versão**, que misturam o que é exigido com o que é
opcional — a mesma queixa que o TCC de referência registrou. Uma configuração por **lista
explícita de regras** evitaria os dois. O problema 3 é defeito da regra em si e exige
desabilitá-la. O problema 1 é estrutural e nenhuma configuração resolve.

Das 14 regras mais aplicadas, só 5 eram exigidas pela versão de destino; as outras 9
(`StrStartsWithRector` 93, `ExplicitPublicClassMethodRector` 89, `VarToPublicPropertyRector` 86,
`LongArrayToShortArrayRector` 27…) são modernização, e inflam o diff sem necessidade.

#### Conclusão: o desenho correto é híbrido

| Camada | Instrumento | Por quê |
|---|---|---|
| Sintática (1.927 das 4.641 correções) | **Rector, com lista explícita de regras** | AST não erra onde regex erra: comentários, chamada aninhada, `->prop{}` |
| Semântica (2.714) | ferramental próprio | `0 == ""`, guardas `pg_*`, casts, `sizeof(null)` — não existem como regra |
| Verificação | comparação byte-a-byte entre runtimes | nenhuma ferramenta substitui |

**Não refiz os cinco módulos já portados** — eles estão verificados byte-a-byte, e trocar o
instrumento agora custaria mais do que ganha. A recomendação vale para os sete prefixos
restantes, e principalmente para `fis` (353) e `iss` (400), onde o volume justifica montar a
lista de regras.

Reproduzir: a montagem está em `tmp/rector/` (gitignored). O passo que importa é reconstruir o
estado pré-porte com `git show <commit>^:<arquivo>` e comparar **três** árvores, não duas —
sem a original não dá para saber quem mudou o quê.

### ✅ COBERTURA DOS CAMINHOS DE ESCRITA — o maior ponto cego, agora medido

A bateria de telas faz só `GET`. O idioma `$this->X == "" ? POST : $this->X` vive em
`atualizacampos()`, que lê `HTTP_POST_VARS` — **nunca populado num GET**. Resultado: **763 das
837 correções** que sobram ao ferramental próprio nunca eram exercitadas por nenhuma
verificação. Era o maior risco em aberto do projeto.

Três níveis possíveis de cobertura, com custos muito diferentes:

| Nível | O que faz | Custo | Cobre |
|---|---|---|---|
| **1. Estado do objeto** | popula `HTTP_POST_VARS`, chama `atualizacampos()`, compara o estado entre runtimes | trivial — extensão do harness que já existia | as 763 guardas (**91%** do que falta) |
| 2. SQL gerado | compara o SQL que cada runtime montaria, sem executar | médio — o método que monta SQL varia por classe | + validações da classe |
| 3. POST real | requisição de verdade nos dois, comparando resposta **e** efeito no banco | alto — exige restaurar o estado do banco entre os dois lados | tudo, inclusive guardas `pg_*` e validação da tela |

**Nível 1 implementado e provado** — `scratchpad/escrita.php`:

```bash
php scratchpad/escrita.php <arquivo com a lista de classes>   # nos DOIS runtimes, depois diff
```

Prova de conceito contra o defeito já conhecido de `classes/db_cgm_classe.php`:

```
versao ANTES das 11 guardas  ->  18 linhas divergentes entre 5.6 e 8.5
versao DEPOIS                ->  0 divergentes

    z01_numcgm='1012'   |   z01_numcgm=0        <- 5.6 le o POST, 8.5 mantem 0
```

**Ele teria apanhado esse defeito do núcleo automaticamente** — eu o encontrei por acaso, na
verificação de remanescentes do `div`.

#### O que ele achou na primeira execução real

Rodado sobre as **311 classes** dos cinco módulos portados, **9.817 campos** comparados:
**64 linhas divergentes em 12 classes**. Onze são do `tra` (órfão, já registradas como não
corrigidas). A décima segunda era nova — e revelou uma **variante do idioma que o catálogo não
tinha**:

```php
var $k40_tipoanulacao = 0;                                    // INTEIRO
$this->k40_tipoanulacao = ($this->k40_tipoanulacao == "f" ? POST : $this->k40_tipoanulacao);
```

Compara com **`"f"`**, não com `""`. Mesma falha:

```
0 == "f"      PHP 5.6: true        PHP 8.5: false
```

Causa: no 5.6 a string **não-numérica** era coagida para 0 e casava com a propriedade inteira;
no PHP 8 vira comparação de string. Vale para **qualquer literal não-numérico** — literal
numérico (`"0"`, `"5"`) é seguro nos dois.

Escala na base inteira: **13 ocorrências em 5 arquivos**.

| Arquivo | Literal | Módulo |
|---|---|---|
| `classes/db_rechumano_classe.php` (8) | `" "` | Educação |
| `classes/db_aluno_classe.php` (2) | `" "` | Educação |
| `classes/db_cadtipoparc_classe.php` | `"f"` | Caixa — **corrigido** (estava no universo do `div`) |
| `classes/db_tipoproc_classe.php` | `"f"` | Protocolo |
| `classes/db_inscricaorestosapagar_classe.php` | `"f"` | Contabilidade |

Duas delas são de **Educação** — o módulo do TCC de referência, mais um defeito que o critério
deles ("a tela carrega") não encontraria.

`enumera.py` e `porta.py` foram estendidos para tratar qualquer literal não-numérico, não só `""`.

#### ✅ NÍVEL 3 IMPLEMENTADO — `scratchpad/escrita_post.py`

**O problema central:** os dois runtimes compartilham o banco, então o primeiro `POST` muda o
estado que o segundo veria. A saída não é comparar o estado final — é comparar **o SQL que
cada runtime emite**, que é exatamente onde o defeito se manifesta, com snapshot/restore entre
os dois lados.

```bash
# exige log_statement ligado:
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade SET log_statement='all';"

python3 scratchpad/escrita_post.py <SID> <tela.php> <tabelas,virgula> '<payload>'

# e desligar ao terminar:
docker exec ecidade_database psql -U postgres -c "ALTER DATABASE ecidade RESET log_statement;"
```

Fluxo: snapshot das tabelas **e das sequências** → `POST` no `:8080`, captura o SQL do log →
restore → `POST` no `:8085`, captura → restore → compara.

**Prova no defeito original do catálogo** (`cm34_tipo`, Cemitério → Tipos de isenção):

```
COM a guarda:
  5.6> insert into cemiterioisencao(...) values ( 11 ,'TESTE_N3' ,2 ,'2026-12-31' ,'X' )
  8.5> insert into cemiterioisencao(...) values ( 11 ,'TESTE_N3' ,2 ,'2026-12-31' ,'X' )
  == IDENTICO ==

SEM a guarda:
  5.6> insert into cemiterioisencao(...) values ( 11 ,'TESTE_N3' ,2 ,... )
  8.5> <ausente>                      <- nao insere nada: cm34_tipo fica 0 e a validacao recusa
  == DIVERGE ==
```

É o sintoma exato que o usuário reportou quando a categoria foi descoberta.

#### Três detalhes que o nível 3 obrigou a resolver

**1. Restaurar a tabela não basta — tem que restaurar a SEQUÊNCIA.** Sem isso o segundo
runtime recebe o próximo número e o `INSERT` diverge por motivo benigno (`values ( 6 ...)`
contra `( 7 ...)`). E `pg_get_serial_sequence` **não enxerga** as sequências do e-cidade,
porque elas são criadas sem `OWNED BY` — o harness casa pelo nome (`<tabela>_%_seq`).

**2. `DELETE`, nunca `TRUNCATE CASCADE`.** O `DELETE` respeita a chave estrangeira e **falha**
se alguém referencia a tabela — que é a rede de segurança. `TRUNCATE CASCADE` apagaria as
tabelas vizinhas em silêncio. Quando a FK barra, a resposta é acrescentar a tabela filha ao
conjunto (apagar filho→pai, repovoar pai→filho), não forçar.

**3. Separar escrita de NEGÓCIO da de INFRAESTRUTURA.** Cada requisição emite ~36 statements,
dos quais ~10 são de escrita, e quase todos são auditoria (`db_acount*`, `db_logsacessa`) ou
sessão (`db_usuariosonline`). Esses carregam sequência e relógio e divergem **por construção**.
Filtrados, sobra 1 statement — o que importa.

#### A limitação real do nível 3: o payload

O harness está pronto; o custo que resta é **construir um `POST` válido por tela**. Não é
mecânico:

- o botão de submit muda de nome conforme a operação (`incluir`/`alterar`/`excluir`), não é
  `db_opcao` como o código sugere;
- campos obrigatórios não aparecem no `db_input` do form (a data do exemplo é montada de
  `_dia`/`_mes`/`_ano`);
- a chave costuma vir como **argumento** de `incluir($chave)`, não pelo idioma do POST — por
  isso `advog` e `aguahidromarca` não exercitam o defeito, mesmo tendo guardas.

**Consequência prática:** o que limita o nível 3 é **montar o payload**, não o custo de
execução. Medido: **5 s por ciclo** (2 POSTs + 2 restores), o que daria **~12 min** para as
148 telas de um módulo — viável como bateria, não só como teste dirigido. O nível 1
(`escrita.php`) continua sendo o filtro barato que aponta a classe e o campo onde dirigi-lo
primeiro.

#### Por que NÃO um banco por runtime

Pergunta levantada e medida, em vez de respondida por intuição.

| | DB compartilhado + restore (adotado) | DB por runtime |
|---|---|---|
| Custo por tela | **5 s** | ~2 s |
| Disco extra | 0 | 1.075 MB |
| Configuração | `log_statement`, um toggle | override de `libs/db_conn.php` por container |
| Invariante do GET | preservada de graça | exige ressincronizar os dois bancos |
| Observável | SQL emitido — **completo** com `log_statement='all'` | linhas + SQL |
| Modo de falha | restore barrado por FK → **aborta** | bancos derivam em silêncio |

Três razões para ficar com o compartilhado:

1. **O observável não melhora.** Com `log_statement='all'` todo SQL é capturado; comparar
   linhas não acrescenta cobertura.
2. **Quebraria a invariante da bateria GET.** Hoje "mesmos dados, só o PHP difere" é garantido
   por construção; com dois bancos vira uma condição que pode derivar sem aviso.
3. **`libs/db_conn.php` fixa `$DB_BASE`, está no `.gitignore` e é lido pelos dois containers
   pelo mesmo bind mount.** Separar exige editar arquivo não versionado ou acrescentar bind
   mount de arquivo único ao compose do 8.5.

Medição que sustenta a escolha: **as tabelas de negócio do Tributário têm no máximo 252
linhas** — o restore é barato. As tabelas de milhão de linhas (`ceplogradouros`,
`cadenderrua*`) são dados de referência de endereço, que nenhum formulário escreve e que
portanto nunca entram num conjunto de restore.

**Quando dois bancos seria melhor:** tabelas de negócio grandes, ou bateria de escrita rodando
continuamente em CI. Nenhuma das duas é o caso aqui.

#### O que o nível 1 NÃO cobre

As outras 74 correções — `parse_str`, guardas `pg_*`, casts, `sizeof(null)` — vivem no código
**da tela**, não da classe, e só o nível 3 as exercita. Continua valendo a regra: *uma tela
"sem erro" cuja tabela está vazia não foi exercitada de verdade*.

### Decisões de porte tomadas (e o porquê)

- **`each()` → ponteiro explícito, não `foreach`.** Em `db_libpessoal.php` há dois laços
  sobre o mesmo array; o segundo depende do ponteiro interno já exaurido pelo primeiro e
  por isso **nunca executa**. Trocar por `foreach` faria o segundo laço rodar — mudança
  silenciosa de comportamento. Usou-se `key()`/`current()`/`next()`, que reproduz `each()`
  exatamente nos dois runtimes.
- **`$HTTP_*_VARS` NÃO foram tocados.** Removidos no PHP 5.4, já estão indefinidos no
  ambiente 5.6 atual (o código se protege com `if (!empty($HTTP_SERVER_VARS))`). Trocar por
  `$_SERVER` popularia valores hoje vazios — mudança de comportamento, não migração.
  Em PHP 8 geram apenas *Warning*. Tarefa separada e deliberada.
- **Acentos LATIN-1 em classes de regex** (`preg_replace("/[ÁÀÂÃ]/", ...)`): editados em
  nível de **byte**, via Python. Editar como texto UTF-8 corromperia os bytes. Sem o
  modificador `/u`, o PCRE é byte-a-byte igual ao POSIX `ereg` original — equivalência
  confirmada por teste de caracterização.
- **JavaScript embutido preservado.** `dbforms/db_classesgenericas.php` linhas 1682/1736
  contêm `str.split()` — é JS dentro do HTML, não PHP. Varreduras automáticas por `split(`
  **precisam excluir esses casos**.

### Bugs latentes encontrados (pré-existentes, NÃO corrigidos)

Não foram tocados por serem mudança de comportamento, não migração. Valem menção no relatório:

- `libs/db_libpessoal.php:113-114` — `strtoupper(split(...))` aplica `strtoupper` a um array,
  e a linha seguinte usa `$count($cmp_)` com `$count` indefinido (chamada de função variável
  em variável nula). **Esse ramo já falha no PHP 5.6**; é código morto.
- `std/DBString.php:661` — o `ereg_replace(",", "\.", ...)` insere uma barra invertida
  literal (`1234,56` → `1234\.56`), que depois vai para `number_format()`. Comportamento
  preservado fielmente com `str_replace`, mas o resultado provavelmente não é o pretendido.

## Movido de `trabalho-relacionado.md` em 27/10/2026

> Estas subseções estavam fisicamente depois da comparação com o TCC no `CLAUDE.md` antigo, e a divisão de
> 26/10 as levou junto. Texto sem alteração.

##### ⚠ CORREÇÃO ao catálogo: por que é o ORIGINAL que executa, e não a cópia do `modification/`

A seção *CRÍTICO: `modification()`* diz que as cópias executam; a sonda do `pre` mostrou o
original executando, sem explicação. **O mecanismo, lido em `definitions.php` e
`src/V3/Modification/Data/FileSync.php`:**

1. se o arquivo de sincronia é **mais novo** que o original → usa a cópia;
2. se o original é **mais novo** (toda vez que edito um arquivo do núcleo) → tenta **regenerar**
   a cópia reaplicando as modificações XML sobre o original;
3. a regeneração **falha** — `extension/modification/log` não é gravável pelos containers — e o
   `catch` devolve **o original**. O `application.log` registra isso: **225 mil** linhas
   `modification() - update file: … Não foi possível abrir o arquivo para escrita`.

Consequências: neste ambiente, para todo arquivo editado depois da sincronia, **os dois
runtimes executam o original** — a comparação continua válida, mas as correções replicadas nas
cópias **não estão sendo exercitadas**. Num ambiente com a pasta gravável, as cópias seriam
**regeneradas a partir do original já portado** (o desejado), desde que as modificações XML
ainda se apliquem. Manter as cópias corrigidas continua sendo o lado seguro.

##### ⚠ A bateria contatava um servidor EXTERNO real: `iss4_siss002.php`

Apareceu como `TIMEOUT` nos dois runtimes, numa tela antes idêntica. É um script de lote (lê
`$argv`) com **IP de terceiro fixo no código**: `$DB_SERVIDOR_SISS = "200.192.137.56"`
(`colocation.sissbr.com.br`). Cada execução da bateria disparava um `pg_connect` a esse
servidor; hoje ele leva **134 s** para desistir, igual nos dois — antes a rede recusava na hora.
Não é regressão; é rede. Mas **testes automatizados não podem contatar serviço real de
terceiros**: o `cmp.py` ganhou a lista `PULAR`, reportada como `PULADA`.


##### ⚠ O INSTRUMENTO, de novo: timeout nos dois contava como IDÊNTICO — e travava o resto

O `cmp.py` desistia em 60 s, mas **o PHP seguia rodando** no servidor, segurando o `flock` do
arquivo de sessão. Como a sessão é compartilhada, **toda tela seguinte travava nos dois
runtimes** — e "000 nos dois" era contado como idêntico. Sintoma: bateria de 148 telas passando
de 10 minutos, e duas telas inocentes (`exportarsituacaoalunonovo001`, `…aluno.RPC.php`)
aparecendo como "travadas" por virem logo depois de um órfão.

Corrigido no `cmp.py`: `000` em qualquer lado vira **`TIMEOUT`**, contado à parte, e o worker
órfão (estado `R`) daquele container é encerrado. Refeita a bateria: 132 idênticas, 10
divergentes, 6 timeouts — e as duas inocentes ficaram idênticas.

Duas armadilhas no diagnóstico, as duas da família *verificação que falha em silêncio*:

- **`ls -l /proc/<pid>/fd` dá `Permission denied`** dentro do container (restrição de
  ptrace), e com `2>/dev/null` o resultado vazio pareceu "nenhum processo segura a sessão".
  Duas hipóteses descartadas com base numa checagem que não enxergava nada.
- **`grep` sem `-a`** sobre `libs/db_stdlib.php` (LATIN-1) não achou o `exit` do
  `db_redireciona` — o arquivo foi tratado como binário.

**Baterias anteriores:** nenhuma teve duração anormal, que é o sintoma deste defeito; o risco
de "timeout contado como idêntico" existia, mas não há sinal de que tenha ocorrido.


#### ARMADILHA DE FERRAMENTAL: o opcache do 8.5 revalida a cada 2 s

Automatizei o ciclo "requisitar → ler o fatal → guardar a linha → repetir". Ele aplicou a
mesma guarda **15 vezes aninhada** na mesma linha: o 8.5 tem `opcache.revalidate_freq = 2`, e
a requisição seguinte chegava antes da revalidação, executando o código antigo e acusando o
mesmo fatal. Desfeito (uma guarda por linha, diff conferido). **Esperar 3 s depois de editar e
antes de requisitar.** O 5.6 não tem opcache, então o sintoma só aparece de um lado.
