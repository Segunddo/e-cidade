# Área Assistência Social (branch `assistencia-social/migracao`)

### 📐 Dimensionada (11/11/2026)

Primeira área depois que as sete anteriores entraram na `base-php84` (PRs #2–#8). A branch **nasce da `base-php84`** (não da
área anterior) e segue o formato `area/assunto` do `CONTRIBUINDO.md` — decisão do usuário.

`scratchpad/dimensiona.py` (depois da Configuração): **57 telas de menu faltando** (68 no menu), 2 módulos (**Social** 44,
**Habitação** 13), **32 a alterar** só pelas telas (descontadas as 11 classes do falso positivo). **1 fantasma:**
`soc1_cidadao003.php`.

| Prefixo | Telas da área faltando | Outras áreas pendentes | Em disco | A alterar (só as telas) | A alterar (prefixo inteiro) |
|---|---|---|---|---|---|
| `soc` | 44 | — | 87 (`soc1_` 8, `soc2_` 42, `soc3_` 17, `soc4_` 20) | 4 | **9** |
| `hab` | 13 | — | 52 (`hab1_` 41, `hab2_` 2, `hab4_` 9) | 28 | **33** |

Nenhuma outra área pendente (Cidadão, Integrações, Gestor) usa `soc` ou `hab`. Hoje há **13 telas/abas `hab` no `map`**
(`hab1_workflow*` do Financeiro, `hab1_avaliacao*` da Configuração); com o prefixo inteiro no `location`, saem do `map`.

#### Divisão (aprovada pelo usuário, 11/11/2026)

**Um lote só: `soc` e `hab` inteiros pelo `location`** (~42 a alterar; 139 telas na bateria). As abas desses prefixos vão junto
com o `location`. Valem as regras de sempre: bateria do lote, bateria completa no fim da área, conferência pelo proxy, e o envio
(PR para a `base-php84`) só depois.

| Lote | Universo | Alterados | `php -l` 5.6/8.5 | Carga (LSP) | Classes | Escrita | Forma negada | **Bateria** |
|---|---|---|---|---|---|---|---|---|
| único `soc`+`hab` | 1.987 | 31 Rector + 3 à mão (2 em biblioteca compartilhada) | 1.987/1.987 | 371/371 (12 falham nos dois) | 803 (diffs só do harness) | 0 fora dos conhecidos | 2.210 pares, 0 div. | **138/139** (1 de ambiente) |

**Lote único — `soc` e `hab` inteiros** (139 arquivos; 11/11/2026). 48 alvos, 37 reais. `split()`: 92, todos `"#"`. Rector em
**31 arquivos**, só regras vetadas (22 guardas, 22 construtores, 22 `split`, 9 `parse_str`), 0 na 2ª passada; nenhuma
`OptionalParametersAfterRequired`. Remanescentes 0; lint 1.987/1.987 nos dois; portão 0; carga 371/371.

Bateria 137/139 → **138/139**. À mão:
- **`model/social/FamiliaRepository.model.php`:** `getInstance()` é `protected function` (não estática) e é chamado como estático
  pelos métodos `static` do repositório — aviso no 5.6, fatal no 8 (`soc2_beneficiosfamilia002`). Não usa `$this` → **`static`**
  (mesma correção do jpgraph no Financeiro).
- **`dbagata/classes/core/AgataQuery.class:95` — BIBLIOTECA COMPARTILHADA, defeito latente das áreas anteriores.**
  `($this->records <= ($this->Limit + $this->OffSet)) or ($this->Limit == 0)`: `Limit`/`OffSet` vêm do XML de cada relatório
  (`['Config']['Limit']`) e podem chegar `""`. No 8, `"" + ""` é `TypeError`; e, pior, **`"" == 0` é falso no 8 e verdadeiro no 5.6**
  (medido): consertar só a soma faria o relatório devolver **zero linhas em silêncio**. → `(int)` nos três (`(int)"" == 0` é
  verdadeiro nos dois). Qualquer relatório do dbagata sem limite no XML quebrava no 8.5; as baterias anteriores não passaram por
  nenhum por GET.
- **`dbagata/classes/pclzip/pclzip.lib.php:2381` — biblioteca compartilhada:** `@fread($v_file, $p_header['size'])` com tamanho 0
  (arquivo vazio indo para o ZIP): no 5.6 `false`, no 8 `ValueError` → `($p_header['size'] > 0 ? @fread(…) : false)`. Só este
  dos 32 `fread` do arquivo (o que apareceu).

**A 1 restante é de AMBIENTE, não de código:** `soc2_declaracaoinss002.php` gera um `.sxw` e o converte por
`model/configuracao/DocumentConverter.model.php`, que chama o comando `file` (tipo do arquivo) e o `soffice` (LibreOffice). **As
imagens têm as ferramentas trocadas:** a do 5.6 tem o LibreOffice (`libreoffice-writer` no Dockerfile) e **não tem `file`**; a do
8.5 tem `file` e **não tem LibreOffice**. O 5.6 para em "Falhou ao determinar o tipo de arquivo", o 8.5 em "Falhou em executar o
soffice" — nenhum dos dois gera o documento neste ambiente. **Pendência para o grupo:** a imagem do 8.5 sem LibreOffice faria
falhar, em produção, toda tela que converte documento (6 arquivos usam o `DocumentConverter`).

Bateria dirigida: dispensada — a **bateria completa** do fim da área (a seguir, pedida junto com o lote) cobre todas as telas
servidas, inclusive as que usam `dbagata/` e o `FamiliaRepository`.

Roteamento: **`soc|hab`** no `location`, na `FASE_A` e nos dois scripts; `map` regenerado → **1.307 entradas** (saíram as 6 telas
`hab` de menu que estavam nele: `hab1_avaliacao001/002/003`, `hab1_workflow001/002/003`). Conferido: `soc2_`, `/w/2/hab1_`,
`hab1_workflow001`, `Soc4_` → 8.5; `login`, `con1_` → 5.6. Passo 8b (84 telas da área no 8.5): nada indo ao 5.6. Pelo banco:
**67/67** telas de menu da Assistência Social em disco no 8.5 (+ 1 fantasma).

### Bateria completa do fim da área (11/11/2026, quarta)

`map` **1.307/1.307**. `location` **9.436/9.470** (30 divergentes + 4 timeouts), conferidas nome a nome contra a bateria final da
Configuração:
- **Saiu** `orc2_receitasDespesasPrevidenciariasServidores002` (a intermitente do horário no PDF).
- **Entrou** `soc2_declaracaoinss002` (a de ambiente, acima).
- **4 timeouts**, todos telas registradas: `edu4_verifexportcenso002`, `rec2_espelhoponto002` e duas das 8 do Censo do Educação
  (`edu4_importacaoatualizacaoaluno002`, `edu4_atualizacadastrocenso002`) — laço eterno **no 5.6**; antes contadas como
  divergentes com o 5.6 em `000`, agora caíram no teto de tempo.
- **Entrou `cai3_gerfinanc001`** (500 nos dois, corpos diferentes) — **não é do lote nem do porte: é o CACHE DO `modification()`
  VERSIONADO POR ENGANO.** Ver abaixo.

### ⚠ ACHADO: 28 arquivos de cache do `modification()` foram versionados por engano (e o `git pull` os ressuscita)

O no 8.5 executava `extension/modification/data/cache/user/dbseller/cai3_gerfinanc001.php`, uma cópia com `parse_str` de 1
argumento, e não o `cai3_gerfinanc001.php` portado. **Mecanismo** (`src/V3/Modification/Data/FileSync.php:43`): o cache é
considerado válido quando `filemtime(cache) > filemtime(original)`. **Origem:** os 28 arquivos de
`ecidade/extension/modification/data/cache/user/dbseller/` entraram no repositório no commit `34c49b37c` (03/10, "Adota a
estrutura ecidade/"), junto com a reorganização — **o `master` não tem nenhum**; são estado de execução, não código. Nunca foram
atualizados. Enquanto o original era mais novo, o sistema ignorava a cópia. O `git pull` da `base-php84` (11/11, 19:09) gravou as
cópias com a data do pull, **mais nova que a dos originais**, e o sistema passou a executá-las.

Conferido: **25 dos 28** cópias ficaram mais novas que o original — inclusive núcleo (`libs/db_conecta.php`,
`libs/db_sessoes.php`, `dbforms/db_funcoes.php`, `dbforms/db_classesgenericas.php`), 9 telas de folha (`pes4_*abertura*`,
`pes4_*fechamento*`), `inicio.php`, scripts e CSS. Só o `cai3_gerfinanc001` acusou na bateria porque é o único cuja cópia tem
construção que quebra no PHP 8; as outras rodam código desatualizado igual nos dois runtimes. **Confirmado:** um `touch` no
original (só a data, sem mudar conteúdo) faz a tela voltar a sair idêntica. **Qualquer clone novo do repositório tem o mesmo
risco** (o git grava os arquivos com a data do clone, em ordem não garantida).

**Correção (decisão do usuário: na mesma PR da área):** os 28 arquivos saíram do repositório (`git rm`, que também apagou as
cópias locais) e `/extension/modification/data/cache` entrou no `ecidade/.gitignore`, ao lado de `/extension/modification/log`.
O diretório pertence ao usuário do host (775), então o Apache não regenera o cache e o sistema usa os originais — o mesmo que no
teste do `touch`. Checagem rápida das 17 telas cujas cópias saíram: **16/17 idênticas**, inclusive `cai3_gerfinanc001` e as 9 de
folha. A 17ª, **`func_histocorrencia.php`**, nunca foi portada (`parse_str` de 1 argumento): antes, chamada direto no 8.5, a cópia
em cache rodava no lugar dela. No uso real ela vai ao 5.6 (o proxy não manda `func_` ao 8.5) — não é regressão; entra na frente
das `func_` (ver `dimensionamento.md`).

Como a remoção tira cópias de arquivos que toda tela carrega (`db_conecta`, `db_sessoes`, `db_funcoes`,
`db_classesgenericas`), **a bateria completa precisa ser refeita**. Ela foi iniciada e **interrompida a pedido do usuário** em
950/9.470; ele pediu para rodá-la depois.

### ⚠ Duas regressões do Tributário, mal classificadas desde então — e a CATEGORIA `pg_lo_export` (12/11/2026)

Achadas ao montar `docs/divergencias-conhecidas.md` (pedido do usuário, depois de ele questionar um "200 no 5.6, 500 no 8.5").
Conferido o caminho real de cada tela da linha de base: todas as outras se sustentam; **duas não**. Corrigidas nesta PR
(decisão do usuário).

- **`iss1_tabalvara_depto001.php`** (aba de `iss1_isstipoalvara002/003/005/006`): `$cltabdesc->k07_instit = …` com `$cltabdesc`
  nunca criado. O registro do Tributário dizia "bug pré-existente", mas **o 5.6 cria o objeto sozinho e monta a aba**; o 8 trata
  como fatal — e a linha roda sempre, com ou sem parâmetro. → `if (empty($cltabdesc)) $cltabdesc = new stdClass();` (medido no 5.6:
  cria `stdClass` a partir de `null` e de `""`). `$cltabdesc` não é lido depois.
- **`iss3_emissaoalvaraeventos001.php`**: o registro dizia que o `pg_lo_export($oid, $arquivo, $conn)` era tolerado pelo 5.6.
  **Medido: no 5.6 essa ordem antiga FUNCIONA** (exporta o arquivo certo); no 8 é `ArgumentCountError`. A ordem
  `($conn, $oid, $arquivo)` funciona igual nos dois (medido, inclusive com o OID em string).

**É uma categoria, não uma tela: 14 chamadas na ordem antiga**, todas reordenadas (o resto da linha intocado):
- telas servidas pelo 8.5: `edu2_aluno002:139`, `edu2_fichaaluno002:157`, `edu3_alunos001:168`, `edu4_escola.RPC:328`,
  `lab4_emissaoresult001:106`, `pes4_autprocvalores.RPC:304`, `sys4_cadastrotemplateRPC:112`;
- compartilhados: **`libs/db_stdlib.php:3735`** (núcleo, `db_buscaImagemBanco`), **`std/DBLargeObject.php:101`**,
  **`model/documentoTemplate.model.php:85`** (o caminho da `iss3`), `classes/db_db_bancos_classe.php:468`,
  `forms/db_frmalunodados.php:68`;
- fora do 8.5 hoje: `cad3_conscadastro_002_marica:62`, `model/integracao/transparencia/IntegracaoLicitacao.model.php:264`.
Conferido o `$conn` de cada ponto: escopo global (do `db_conecta.php`), `global $conn`, parâmetro ou atribuição — nenhum
indefinido (duas detecções ambíguas, `edu4_escola.RPC` e `lab4_emissaoresult001`, conferidas à mão: escopo global). As formas de 2
argumentos (`pg_lo_export($oid, $arquivo)`, 11 pontos) já funcionam nos dois e ficaram como estão. **Nenhuma bateria via a
categoria:** nenhuma chega a exportar um arquivo guardado no banco (foto de aluno, laudo, template, logotipo). Verificação:
`DBLargeObject::leitura()` chamada direto nos dois runtimes com um objeto criado na hora — **igual nos dois** com a correção; a
versão antiga (`HEAD`) dá `ArgumentCountError` no 8.5. As 12 telas envolvidas (as duas regressões pelo caminho real e as 7 servidas
que exportam): **12/12 idênticas**. Lint dos 15 PHP alterados nos dois; 0 chamadas na ordem antiga restantes.

**Junto, o resto do commit acidental de 03/10:** os **28 marcadores de sincronização** vazios de
`extension/modification/data/file/sync/user/dbseller/` (a `FileSync` compara a data deles com a do original para decidir se usa o
cache) saíram do repositório, e `/extension/modification/data/file/sync` entrou no `.gitignore`. Sobrou do mesmo commit só
`extension/modification/data/file/file-type-modification.data`, que não é marcador — intocado.

A bateria completa pós-remoção do cache foi **parada em 6.750/9.470** (log parcial guardado, 29 diferenças, todas da linha de base),
porque as correções acima mexem em arquivos que quase toda tela carrega; será refeita do zero.

**Estado:** lote concluído; cache, marcadores e as 14 chamadas corrigidos (commits locais). **Falta refazer a bateria completa**,
depois a conferência pelo proxy e a PR única.
