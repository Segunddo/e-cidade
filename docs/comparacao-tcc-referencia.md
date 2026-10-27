# Comparação com o TCC de referência — migração da área Educação

Comparação medida entre dois trabalhos que migraram o mesmo módulo do e-cidade (Educação)
para PHP 8:

| | TCC de referência | Este trabalho |
|---|---|---|
| Trabalho | ARAUJO, G. J. F. de. *Relato de experiência da migração assistida por IA generativa do módulo de educação do E-Cidade do PHP 5.6 para PHP 8.4.* TCC, UFPB, 2026. | Projeto de Engenharia de Software, UFPB, 2026 |
| Código | branch `tcc-gerson-banca` de `ltdufpb/e-cidade` | branch `2educacao-migrado` |
| Alvo | PHP 8.4 | PHP 8.5 |
| Estratégia | *big-bang*: o runtime inteiro sobe para 8.4 | *strangler fig*: 5.6 e 8.5 convivem atrás de um proxy |
| Critério de validação | "carregou sem erro fatal, tela em branco, código exibido ou interrupção visível" — 520 telas navegadas à mão | comparação **byte a byte** contra o 5.6 vivo, mais o caminho de escrita |

> **Como ler este documento.** Os números abaixo **não** dizem que o trabalho de referência
> está errado. Ele declara o próprio critério — *"isso não comprova regras de negócio"* — e o
> cumpre. O que a comparação mostra é a **diferença entre os dois critérios de verificação**:
> o que uma navegação "a tela abriu" encontra, e o que uma comparação contra o sistema original
> encontra.

---

## 1. Como a comparação foi montada

O objetivo era medir os dois trabalhos **sobre o mesmo universo e pelo mesmo critério**.

**Universo:** os ~2.795 arquivos que as sete frentes de enumeração alcançam a partir das telas
da área Educação (prefixos `edu`, `mer`, `bib`, `tre`, `sec`, `esc`, `rel`, mais as classes,
formulários e bibliotecas que essas telas carregam).

**Código de referência:** a branch foi trazida só para leitura
(`git fetch … tcc-gerson-banca:refs/remotes/gerson/tcc-gerson-banca`) e aberta numa *worktree*
separada. Ela ainda usa a estrutura anterior à reorganização do repositório (arquivos na raiz,
e não em `ecidade/`).

**Ambiente — só o código muda.** Um terceiro container, na porta 8086, idêntico ao nosso 8.5:

| | Nosso 8.5 (`:8085`) | Código de referência (`:8086`) |
|---|---|---|
| Imagem | a mesma | a mesma |
| PHP | 8.5.10 | 8.5.10 |
| Sessão e `/tmp` | volumes compartilhados com o 5.6 | os mesmos volumes |
| `php.ini` | `paridade-56.ini` | o mesmo |
| `vendor/` | o nosso | o mesmo (a referência não alterou `composer.json` nem `composer.lock`) |
| Configuração local | `.env`, `config/*.php`, `libs/db_conn.php`, `extension/data/` | cópias idênticas |
| **Código** | **o nosso** | **o da referência** |

A referência do comportamento correto é sempre o **PHP 5.6 rodando o sistema original** (`:8080`).

**Limitação declarada:** o trabalho de referência mirou PHP **8.4**, e aqui rodou em **8.5**.
Todos os fatais encontrados pertencem a categorias que quebram desde o PHP 8.0, portanto valem
igualmente para o 8.4. Nenhum resultado depende de algo exclusivo do 8.5.

---

## 2. Resumo

| | TCC de referência | Este trabalho |
|---|---|---|
| Comparações `0 == ""` sem correção | **3.685 em 730 arquivos** | **0** |
| Campos do formulário que deixam de ser lidos no POST | **3.606 em 730 classes** | **0** |
| Telas equivalentes ao 5.6 (de 1.551) | **1.316 (84,8%)** | **1.534 (98,9%)** |
| Telas com defeito de migração | **≥ 203** | **0** |
| Defeito presente em toda tela | **1** | **0** |
| O código migrado roda também no 5.6 | não | sim |

As três medições — estática, caminho de escrita e telas — estão detalhadas a seguir.

---

## 3. Medição estática

Contagem feita pelo **tokenizer do próprio PHP** (`token_get_all`), que distingue código de
comentário e de string. Um regex sobre bytes conta ocorrências dentro de comentários e
superestima; o tokenizer não. Ferramenta: `scratchpad/conta_tokens.php`.

| Construção incompatível com PHP 8 | Antes da migração | Referência | Este trabalho |
|---|---|---|---|
| **comparação `0 == ""` sem guarda** | 3.685 em 730 arq. | **3.685 em 730 arq.** | **0** |
| construtor estilo PHP 4 | 646 | 0 | 0 |
| `parse_str()` de 1 argumento | 545 | 0 | 0 ¹ |
| `split()` | 2.759 | 776 ² | 0 |
| `ereg*()` | 13 | 0 | 0 |
| `each()` | 3 | 0 | 0 |

¹ Resta um, em `mer1_mer_desper_und003.php`, arquivo que **já não compila no PHP 5.6** (chave
aberta na linha 57) e por isso ficou fora da migração.

² **Os 776 `split()` restantes não são defeito.** O pacote `vendor/dbseller/legacy` define um
`split()` para PHP ≥ 7, implementado como `explode()`. Todos os 776 usam separador literal
(`"#"` 775 vezes, `"_"` uma vez) e nenhum usa o 3º argumento, então o polyfill devolve o mesmo
resultado do 5.6. O polyfill só erraria com separador que é expressão regular (`" +"`, `"\|"`),
porque o `split()` original interpretava o separador como regex POSIX e o `explode()` não. A
mesma observação vale contra este trabalho: as conversões de `split` para `preg_split` não
eram necessárias para as telas rodarem, exceto nesses separadores com regex.

### Por que o `0 == ""` é o que importa

A única categoria em que os dois trabalhos diferem é também a única **silenciosa**:

```
PHP 5.6:  0 == ""  ->  true
PHP 8.x:  0 == ""  ->  false     (RFC "Saner string to number comparisons")
```

O idioma está em todas as classes de dados do e-cidade:

```php
var $ed80_i_codigo = 0;                                     // propriedade inicializada com INTEIRO
...
$this->ed80_i_codigo = ($this->ed80_i_codigo == ""          // 5.6: true  -> lê o valor do formulário
                        ? @$GLOBALS["HTTP_POST_VARS"]["ed80_i_codigo"]
                        : $this->ed80_i_codigo);            // 8.x: false -> mantém 0
```

O código é válido nas duas versões, não gera erro nem aviso, e a tela abre normalmente. A
correção adotada neste trabalho reproduz o 5.6 sem alterar nenhum dado:

```php
$this->X == ""   ->   ($this->X === 0 || $this->X === 0.0 || $this->X == "")
```

---

## 4. Caminho de escrita — o efeito medido

A medição estática conta onde o defeito *está*; esta mede o que ele *faz*. O harness
`escrita.php` preenche o POST de cada classe de dados, chama `atualizacampos()` — o método que lê
o formulário — e compara o estado do objeto com o do 5.6. Foram 756 classes da área, uma por
processo, para que um erro fatal numa classe não interrompa as outras.

| | Campos com valor diferente do 5.6 | Classes afetadas |
|---|---|---|
| **TCC de referência** | **3.606** | **730** |
| **Este trabalho** | **0** ³ | 0 |

³ Uma linha difere, e é um artefato conhecido do instrumento: o construtor de
`RequisicaoMaterial` exige argumento, e o harness o instancia sem nenhum.

Exemplo real, na classe de abono de faltas (`classes/db_abonofalta_classe.php`):

```
                  ed80_i_codigo   ed80_i_diarioavaliacao   ed80_i_justificativa
PHP 5.6           '1012'          '1013'                   '1014'
Referência        0               0                        0
Este trabalho     '1012'          '1013'                   '1014'
```

**Consequência prática:** o valor que o usuário digitou é descartado. Ou a validação seguinte
recusa o formulário ("Campo não informado"), ou o `0` é gravado no banco. Em nenhum dos dois
casos a tela "abre com erro" — por isso o defeito passa por um critério de navegação e só
aparece comparando com o sistema original.

---

## 5. Telas — 1.551 comparadas contra o 5.6

### Resultado bruto

| | Idênticas ao 5.6 |
|---|---|
| TCC de referência | 424 de 1.551 |
| Este trabalho | 1.534 de 1.551 |

O número bruto da referência é dominado por um defeito único, presente em todas as telas
(seção 6). Para separar esse defeito dos defeitos de cada tela, as 1.087 divergências foram
classificadas uma a uma.

### Classificação das 1.087 divergências da referência

| Categoria | Telas | É defeito de migração? |
|---|---|---|
| idêntica depois de recortar o menu (seção 6) | 482 | sim — o **mesmo** defeito, único |
| só espaço em branco (falta a quebra de linha no fim do documento) | 294 | não — efeito da conversão de *short tags*, irrelevante para o navegador |
| quebra nos dois runtimes, só muda a mensagem de erro | 85 | não — defeito pré-existente; a referência exibe a exceção, o original diz "Erro interno" |
| **erro 500 só na referência** (200 no 5.6) | **175** | **sim** |
| **página truncada / conteúdo faltando** | **26** | **sim** |
| outra diferença de conteúdo | 22 | provável — não verificadas uma a uma |
| **acentuação corrompida** | **2** | **sim** |
| erro 500 no 5.6, 200 na referência | 1 | — |

Somando as idênticas (424 + 482), as que diferem só em espaço (294) e as que quebram nos dois
(85), **1.316 das 1.551 telas** da referência são equivalentes ao 5.6.

### As causas dos 175 erros 500

Cada fatal foi lido no log do container. As causas são as categorias que este trabalho
catalogou e corrigiu:

| Erro | Telas | Onde |
|---|---|---|
| `pg_num_fields()` recebe `false` | 81 | `libs/db_stdlib.php:1330`, função `db_fieldsmemory()` — **núcleo** |
| `pg_num_rows()` recebe `false` | 44 | várias telas |
| `get_magic_quotes_runtime()` não existe | 24 | `fpdf151/fpdf.php:1375` — **núcleo**; função removida no PHP 8.0 |
| `reset()` recebe `null` | 4 | |
| `pg_fetch_result()` recebe `false` | 3 | |
| `count()` recebe `null` | 3 | |
| `file_get_contents("")` / `fopen("")` | 3 | |
| `cal_days_in_month()` com mês inválido | 2 | |
| outros (`pg_fetch_*`, `mktime`, `pg_last_error`…) | 11 | |

**105 dos 175 fatais vêm de dois pontos do núcleo** — corrigidos uma vez neste trabalho, ainda no
piloto, e responsáveis por quebrar dezenas de telas na referência.

Por que a navegação manual não os encontrou: os erros de `pg_*` só disparam quando a consulta
SQL **falha** (consultas com coluna inexistente ou `GROUP BY` malformado, defeitos que o 5.6
engolia), e não quando a tabela está vazia. São caminhos que uma navegação com dados comuns
raramente percorre — e que a comparação com o 5.6, tela por tela, percorre todos.

### Exemplos dos outros defeitos

**Acentuação corrompida** — arquivo LATIN-1 regravado como UTF-8 (o mesmo problema que o
commit PHP8-21 da referência corrigiu em 7 outros arquivos):

```
PHP 5.6:     alert('Erro ao localizar vínculo com a escola.');
Referência:  alert('Erro ao localizar vÃ­nculo com a escola.');
```

**Constante indefinida** — a validação de e-mail do cadastro de aluno some da página, porque
a referência morre ao avaliar `$GLOBALS[Sed47_c_emailresp]`:

```
PHP 5.6:     Vemailresp = ""; Vemail = ""; if (jsValidaEmail(...) == false) { return false; }
Referência:  (bloco ausente)
```

---

## 6. O defeito presente em toda tela

No código de referência, a camada nova do sistema (`ECidade\V3`) **não enxerga o login da
sessão**, enquanto a função legada lê normalmente — no mesmo container, com a mesma sessão:

```
                                   Este trabalho      Referência
db_getsession("DB_login")          'dbseller'         'dbseller'
Request->session()->get(...)       'dbseller'         NULL
ECIDADE_DESKTOP                    true               false
```

Com isso o sistema conclui que a extensão *Desktop* está desligada para o usuário, e a função
`db_menu()` — chamada em praticamente toda tela — emite o **menu clássico** (~400 linhas de HTML)
no lugar do estilo e do script que integram a tela ao desktop. A tela abre, mas fora da
integração com a interface atual.

**O que está provado:** a diferença vem do código. Os containers 8085 e 8086 só diferem no
código, e o estado da extensão é lido igual nos dois (`isEnabled('Desktop', 'dbseller')` dá
`true` em ambos) — o que muda é o usuário que a camada V3 entrega.

**O que não está localizado:** a linha exata. A referência alterou 21.967 arquivos; as classes da
camada V3 que leem a sessão (`Request`, `Session`, `Front`) são idênticas às originais, e as
alteradas (`ParameterBag`, `Container`, `Registry`) são equivalentes.

**Como foi separado das outras medições:** a comparação usou uma normalização (`NORM_MENU=1` no
`cmp.py`) que recorta **só as partes exclusivas** de cada ramo do `db_menu()` — o estilo do
desktop de um lado, o menu clássico e o script de barra de status do outro. A parte comum (os
scripts de ajuda) continua sendo comparada. Para garantir que a normalização não escondesse nada,
ela foi aplicada também ao nosso lado: a amostra continuou 40 de 40 idêntica.

---

## 7. Onde os dois trabalhos convergem

A comparação também confirma o que os dois fizeram igual, de forma independente:

| Categoria | Referência | Este trabalho |
|---|---|---|
| construtores estilo PHP 4 → `__construct` | corrigidos (646) | corrigidos (646) |
| `parse_str()` de 1 argumento | corrigidos, com `extract(…, EXTR_SKIP)` | corrigidos, com `extract()` |
| `ereg*()` e `each()` | corrigidos | corrigidos |
| offset de string com chaves `{}` | corrigido | corrigido |
| guardas `pg_*` contra resultado falso | aplicadas onde apareceram | aplicadas onde apareceram |
| acentuação LATIN-1 | mordidos (PHP8-21 corrigiu 7 arquivos) | tratada editando em bytes |

As diferenças de resultado não vêm de categorias desconhecidas de um dos lados — o catálogo
dos dois é quase o mesmo. Vêm de **quais ocorrências cada critério consegue enxergar**.

---

## 8. Por que o critério de verificação decide

| | Navegação ("a tela carregou") | Comparação com o 5.6 vivo |
|---|---|---|
| Encontra erro fatal no caminho navegado | sim | sim |
| Encontra fatal em caminho de dado incomum (SQL que falha) | raramente | **sim** — percorre toda tela |
| Encontra campo de formulário não lido (`0 == ""`) | **não** — a tela abre normalmente | **sim** — caminho de escrita |
| Encontra campo que some da tela, PDF com layout deslocado | **não** — a tela abre normalmente | **sim** — byte a byte |
| Exige o sistema original em funcionamento | não | **sim** |

A última linha é a razão de ser da estratégia: no *big-bang*, o 5.6 deixa de existir no momento
em que o runtime sobe de versão, e com ele desaparece a referência contra a qual comparar. No
*strangler fig*, os dois runtimes convivem sobre o mesmo banco, e o "antes" continua disponível
para cada tela, a cada lote.

A própria monografia de referência aponta esse caminho como trabalho futuro: *"Avançar requer
base mínima, cenários iguais antes e depois e participação de especialista no domínio."*

---

## 9. Limitações desta comparação

- **Versão do PHP:** a referência mirou 8.4 e rodou aqui em 8.5. Os fatais encontrados quebram
  desde o 8.0; nenhum resultado depende do 8.5.
- **22 telas** com "outra diferença de conteúdo" não foram verificadas uma a uma; não entram na
  contagem de defeitos (o "≥ 203").
- **A causa do defeito da camada V3 não foi localizada** — só provado que é do código.
- **O banco de exemplo tem muitas tabelas vazias.** Isso afeta os dois lados igualmente, mas
  significa que nenhuma das duas medições exercita todos os caminhos de dado.
- **O caminho de escrita (nível 1)** mede o estado do objeto depois de ler o formulário, sem
  gravar no banco. Ele cobre o defeito do `0 == ""`, mas não as validações que só acontecem na
  tela.

---

## 10. Como reproduzir

```bash
# 1. trazer a branch de referência (só leitura)
git fetch --no-tags https://github.com/ltdufpb/e-cidade.git \
    tcc-gerson-banca:refs/remotes/gerson/tcc-gerson-banca

# 2. worktree + configuração local não versionada
W=ecidade/tmp/tcc_gerson
git worktree add --detach $W refs/remotes/gerson/tcc-gerson-banca
for f in .env config/application.php config/ecidade_config.php config/preferencias.json \
         config/require_extensions.xml libs/db_acessa.php libs/db_conn.php; do
  cp -p ecidade/$f $W/$f
done
cp -rp ecidade/extension/data $W/extension/
mkdir -p $W/storage $W/bootstrap/cache $W/extension/log $W/tmp $W/arquivos
chmod -R 777 $W/storage $W/bootstrap/cache $W/extension/log $W/tmp $W/arquivos

# 3. terceiro container, idêntico ao 8.5 exceto pelo código
docker run -d --name ecidade_tcc_gerson --network e-cidade_ecidade -p 8086:80 \
  -e DB_HOST=ecidade_database -e DB_PORT=5432 -e DB_DATABASE=ecidade \
  -e DB_USERNAME=postgres -e DB_PASSWORD=postgres \
  -v $PWD/$W:/var/www/html -v $PWD/ecidade/vendor:/var/www/html/vendor:ro \
  -v ecidade_sessions:/var/lib/php/sessions -v ecidade_tmp:/tmp \
  -v $PWD/docker/php85-apache/paridade-56.ini:/usr/local/etc/php/conf.d/zz-paridade-56.ini:ro \
  $(docker inspect ecidade_php85 --format '{{.Config.Image}}')

# 4. telas: 5.6 x referência, com o defeito do menu separado
NORM_MENU=1 PORTA_B=8086 python3 scratchpad/cmp.py <SID> '^edu[0-9]*_' /dev/null

# 5. estático, por token (o scratchpad/ fica fora do container: copiar antes)
docker cp scratchpad/conta_tokens.php ecidade_php85:/tmp/conta_tokens.php
docker exec ecidade_php85 php -d short_open_tag=1 /tmp/conta_tokens.php /var/www/html/tmp/tcc_gerson

# remover depois
docker rm -f ecidade_tcc_gerson && git worktree remove ecidade/tmp/tcc_gerson
```

Os detalhes de cada medição, as decisões tomadas no caminho e as armadilhas encontradas estão
na seção *⚖️ COMPARAÇÃO MEDIDA COM O TCC DE REFERÊNCIA* de `docs/registro/trabalho-relacionado.md`.
