# Correções transversais (branch `nucleo/correcoes-transversais`)

Correções que valem para **todas as áreas já na `base-php84`**, achadas durante a verificação da área Assistência Social
(11–12/11/2026). Estavam na branch `assistencia-social/migracao` (PR #10) junto com o lote da área; em 12/11/2026 o usuário
decidiu **refazer a Assistência Social à mão** e pediu para separar estas correções numa branch própria antes de apagar aquela.

Ficaram de fora, por serem da área: o lote `soc`/`hab` (Rector em 31 arquivos), o roteamento de `soc|hab` e a correção do
`model/social/FamiliaRepository.model.php` (`getInstance()` chamado como estático sem ser estático: aviso no 5.6, fatal no 8; a
correção fiel é declará-lo `static`, porque não usa `$this`).

## 1. O cache do `modification()` versionado por engano

**O que era:** 28 arquivos de `ecidade/extension/modification/data/cache/user/dbseller/` e 28 marcadores vazios de
`ecidade/extension/modification/data/file/sync/user/dbseller/`. São **estado de execução** (o `master` original não tem nenhum) e
entraram no repositório no commit `34c49b37c` (03/10/2026, "Adota a estrutura ecidade/"), junto com a reorganização das pastas.

**Por que quebra:** o `FileSync` (`src/V3/Modification/Data/FileSync.php:43`) usa a cópia em cache quando o marcador é **mais
novo** que o original. Um `git pull` ou um clone novo grava esses arquivos com a data do momento, e o sistema passa a executar
**código antigo no lugar do portado**. Achado porque `cai3_gerfinanc001.php` passou a quebrar no 8.5 (`parse_str` de 1 argumento,
na cópia) depois do `git pull` da `base-php84` de 11/11. **25 das 28 cópias** estavam mais novas que o original, inclusive do
núcleo (`libs/db_conecta.php`, `libs/db_sessoes.php`, `dbforms/db_funcoes.php`, `dbforms/db_classesgenericas.php`), 9 telas de folha
(`pes4_*abertura*`, `pes4_*fechamento*`), `inicio.php`, scripts e CSS. Só uma acusou na bateria porque é a única cuja cópia tem
construção que quebra no PHP 8; as outras rodavam código desatualizado igual nos dois runtimes. Confirmado: um `touch` no original
faz a tela voltar a sair idêntica.

**Correção:** os 56 arquivos saem do repositório, e `/extension/modification/data/cache` e `/extension/modification/data/file/sync`
entram no `ecidade/.gitignore`, ao lado de `/extension/modification/log`. Sem as cópias, o sistema usa os originais. Sobrou do mesmo
commit só `extension/modification/data/file/file-type-modification.data`, que não é marcador — intocado.

## 2. `pg_lo_export` na ordem antiga — 14 pontos (e as duas regressões que a revelaram)

Achadas ao montar `docs/divergencias-conhecidas.md`, conferindo o caminho real de cada tela que dava "200 no 5.6, 500 no 8.5".

- **`iss1_tabalvara_depto001.php`** (aba de `iss1_isstipoalvara002/003/005/006`): `$cltabdesc->k07_instit = …` com `$cltabdesc`
  nunca criado. O registro do Tributário dizia "bug pré-existente", mas **o 5.6 cria o objeto sozinho e monta a aba**; o 8 trata como
  fatal, e a linha roda sempre. → `if (empty($cltabdesc)) $cltabdesc = new stdClass();` (medido no 5.6: cria `stdClass` a partir de
  `null` e de `""`). `$cltabdesc` não é lido depois.
- **`iss3_emissaoalvaraeventos001.php`**: o registro dizia que o 5.6 "tolerava" `pg_lo_export($oid, $arquivo, $conn)`. **Medido:
  no 5.6 essa ordem antiga funciona** (exporta o arquivo certo); no 8 é `ArgumentCountError`. A ordem `($conn, $oid, $arquivo)`
  funciona igual nos dois (medido, inclusive com o OID em string).

**É uma categoria: 14 chamadas na ordem antiga**, todas reordenadas (o resto da linha intocado):
- telas servidas pelo 8.5: `edu2_aluno002:139`, `edu2_fichaaluno002:157`, `edu3_alunos001:168`, `edu4_escola.RPC:328`,
  `lab4_emissaoresult001:106`, `pes4_autprocvalores.RPC:304`, `sys4_cadastrotemplateRPC:112`;
- compartilhados: **`libs/db_stdlib.php:3735`** (núcleo, `db_buscaImagemBanco`), **`std/DBLargeObject.php:101`**,
  **`model/documentoTemplate.model.php:85`** (o caminho da `iss3`), `classes/db_db_bancos_classe.php:468`,
  `forms/db_frmalunodados.php:68`;
- fora do 8.5 hoje: `cad3_conscadastro_002_marica:62`, `model/integracao/transparencia/IntegracaoLicitacao.model.php:264`.

Conferido o `$conn` de cada ponto: escopo global (do `db_conecta.php`), `global $conn`, parâmetro ou atribuição — nenhum indefinido
(`edu4_escola.RPC` e `lab4_emissaoresult001` conferidos à mão: escopo global). As formas de 2 argumentos (`pg_lo_export($oid,
$arquivo)`, 11 pontos) já funcionam nos dois e ficaram como estão. **Nenhuma bateria via a categoria:** nenhuma chega a exportar um
arquivo guardado no banco (foto de aluno, laudo, template, logotipo). Verificação: `DBLargeObject::leitura()` chamada direto nos dois
runtimes com um objeto criado na hora — igual com a correção; a versão anterior dá `ArgumentCountError` no 8.5.

## 3. `dbagata` (biblioteca de relatórios de todas as áreas)

- **`dbagata/classes/core/AgataQuery.class:95`:** `($this->records <= ($this->Limit + $this->OffSet)) or ($this->Limit == 0)`.
  `Limit`/`OffSet` vêm do XML de cada relatório (`['Config']['Limit']`) e podem chegar `""`. No 8, `"" + ""` é `TypeError`, e
  **`"" == 0` é falso no 8 e verdadeiro no 5.6** (medido): consertar só a soma faria o relatório devolver **zero linhas em silêncio**.
  → `(int)` nos três pontos (`(int)"" == 0` é verdadeiro nos dois). Defeito latente desde as áreas anteriores: nenhuma bateria passou
  por relatório do dbagata sem limite no XML.
- **`dbagata/classes/pclzip/pclzip.lib.php:2381`:** `@fread($v_file, $p_header['size'])` com tamanho 0 (arquivo vazio indo para o
  ZIP): `false` no 5.6, `ValueError` no 8 → `($p_header['size'] > 0 ? @fread(…) : false)`. Só este dos 32 `fread` do arquivo.

## 4. Ambiente (registrado, sem alteração)

As imagens Docker têm ferramentas trocadas: a do 5.6 tem o LibreOffice (`libreoffice-writer` no Dockerfile) e **não tem o comando
`file`**; a do 8.5 tem `file` e **não tem o LibreOffice**. `model/configuracao/DocumentConverter.model.php` usa os dois, então
nenhum runtime gera documento convertido neste ambiente (achado em `soc2_declaracaoinss002.php`). **Com a imagem do 8.5 como está,
toda tela que converte documento falharia em produção** (6 arquivos usam o conversor); a imagem precisa do `libreoffice-writer`.

## Verificação

Estas correções foram verificadas **dentro da branch da Assistência Social**, que as continha. A bateria completa final daquela branch
(depois de todas elas): `map` **1.307/1.307**, `location` **9.439/9.470**, nenhuma diferença nova; saíram `cai3_gerfinanc001`,
`iss1_tabalvara_depto001` e `iss3_emissaoalvaraeventos001`. Nesta branch, separada: lint dos arquivos alterados nos dois runtimes e
as telas afetadas comparadas de novo (abaixo).
