# Os 9 pacotes da trava do PR que excluem o PHP 8.5 (PHP8-87)

Medido em 20/11/2026, sem banco: resolução no Composer 2.11.2 / PHP 8.5.12 (a imagem pinada de
`docker/composer-85/`) e trechos isolados em contêineres `--network none`. A referência é o 7.4 do PR, na imagem
construída de `docker/php74-apache` (PHP 7.4.33), com o `vendor/` instalado do `ecidade/composer.lock`. O 8.5 roda na
imagem de `docker/php85-apache` (PHP 8.5.12), com o `vendor/` instalado do `ecidade/composer-85.lock`. O
`composer.json`/`composer.lock` do 7.4 não mudam.

## O que muda no composer do 8.5

| Pacote | 7.4 (PR) | 8.5 | Quem pede (`composer why`) | Por quê |
|---|---|---|---|---|
| `dompdf/dompdf` | v0.8.6 | **v0.8.6 + patch de 2 linhas** | `dbseller/e-cidade` (`^0.8.3`) | ver *dompdf* abaixo |
| `mpdf/mpdf` | v8.2.4 | v8.2.6 | `dbseller/e-cidade` (`^8.0`), `proner/phppimaco` (`^8.0`) | 8.2.4 declara `… \|\| ~8.3.0`; 8.2.6 é a menor com `~8.5.0` |
| `ezyang/htmlpurifier` | v4.17.0 | v4.19.0 | `phpoffice/phpspreadsheet` 1.29.1 (`^4.15`) | 4.19.0 é a menor com `~8.5.0` |
| `laminas/laminas-escaper` | 2.12.0 | 2.18.0 | `phpoffice/phpword` 0.18.3 (`^2.2`) | 2.18.0 é a menor que aceita o 8.5 (`~8.2.0 \|\| … \|\| ~8.5.0`) |
| `nette/schema` | v1.2.5 | v1.3.3 | `league/config` 1.2.0 (`^1.2`) ← `league/commonmark` ← Laravel | 1.3.3 é a menor com `8.1 - 8.5`; pede `nette/utils ^4.0` |
| `nette/utils` | v3.2.10 | v4.0.8 | `nette/schema` | 3.x vai até `<8.4`; 4.0.8 é a menor com `8.0 - 8.5` |
| `fzaninotto/faker` (dev) | v1.9.2 | sai | `dbseller/e-cidade` (dev) | abandonado; nenhuma versão aceita o 8.5 |
| `fakerphp/faker` (dev) | — | v1.10.0 | `dbseller/e-cidade` (dev, `^1.10`) | sucessor com o mesmo namespace `Faker\`; 1.10.0 é a menor com `^8.0` |
| `cweagans/composer-patches` | — | 1.7.3 | `dbseller/e-cidade` (`^1.7`) | aplica o patch do dompdf na instalação |
| `phpoffice/phpspreadsheet` | 1.29.1 | 1.29.1 | — | não muda: a 1.29.1 já declara `^7.4 \|\| ^8.0` |

As versões menores foram escolhidas com `--with` no `update`, sem mudar a restrição do `composer-85.json`. Com isso,
`mpdf ^8.0` fica em 8.2.6. Antes de escolher cada uma, foram lidos os metadados de todas as versões (packagist p2).

**Como saiu a trava** (o comando único de `docker/composer-85/composer-85.sh`):

```bash
bash docker/composer-85/composer-85.sh update --no-install --no-scripts --ignore-platform-req=php+ \
  dompdf/dompdf mpdf/mpdf ezyang/htmlpurifier laminas/laminas-escaper nette/schema nette/utils \
  fakerphp/faker fzaninotto/faker cweagans/composer-patches \
  --with mpdf/mpdf:8.2.6 --with ezyang/htmlpurifier:4.19.0 --with laminas/laminas-escaper:2.18.0 \
  --with nette/schema:1.3.3 --with nette/utils:4.0.8 --with fakerphp/faker:1.10.0 --with cweagans/composer-patches:1.7.3
```

Resultado: 167 pacotes. Sobre a trava anterior do 8.5 (a do PR com a troca do `lcobucci/jwt` para 4.1.5 e o
`lcobucci/clock` 2.0.0 da PHP8-60): 5 sobem de versão, 1 sai (`fzaninotto/faker`) e entram 2 (`fakerphp/faker` e
`cweagans/composer-patches`). O dompdf fica no mesmo commit (`db91d81`). O `composer.json`/`composer.lock` do 7.4
seguem com o `sha256` da base (`69367bdc…` e `38fe5a63…`).

**`composer prohibits php 8.5.12 --locked` depois:** sobram 2, que não são desta tarefa:

| Pacote | Exige | Fica para |
|---|---|---|
| `bacon/bacon-qr-code` 1.0.3 | `^5.4\|^7.0` | PHP8-70 (documentos): vem do `proner/phppimaco` 1.4.5 → `endroid/qr-code` 2.5.1 (`bacon ^1.0.3`) |
| `khanamiryan/qrcode-detector-decoder` 1 | `^5.6\|^7.0` | idem (`endroid/qr-code` 2.5.1 fixa a versão `1`) |

O `dbseller/sdk-api-pix-bb` 2.0.0 declara `>=7.4.0` e não aparece nessa lista. O que o impede no 8.5 é outra coisa, e
fica para a PHP8-91.

## dompdf: 0.8.6 com patch, não 1.0.0

A 0.8.6 declara `php ^7.1`. A menor versão que aceita o 8.5 é a 1.0.0. As duas foram medidas com as 4 capas do
Protocolo (`app/Domain/Patrimonial/Protocolo/Services/CapaDoDocumento.php` e `CapaDoDespacho.php`: Blade → `loadHtml`,
`setPaper('A4')`, `render`, 3× `page_text`):

| No 8.5 | Resultado contra o 7.4 |
|---|---|
| 0.8.6 sem patch | erro fatal no `render()`: `TypeError: round(): Argument #1 ($num) must be of type int\|float, string given` em `src/Css/Style.php:3304` (`set_z_index('auto')`) |
| 1.0.0 | 0/4 iguais. A quebra de página muda: em 3 das 4 capas, 1 parágrafo passa para a outra página. A 1.0.0 dá o mesmo PDF no 7.4 e no 8.5 (4/4), então a diferença vem da versão, não do PHP |
| 0.8.6 + só a linha do `z_index` | 0/4 iguais, sem erro: o layout desmonta (cabeçalho sobreposto ao corpo) |
| **0.8.6 + as 2 linhas** | **12/12 iguais** (as 4 capas × 3 variações de dados, até 11 páginas) |

As 2 linhas (`ecidade/patches/dompdf-0.8.6-php85.patch`) reproduzem o que o 7.4 faz:

- `src/Css/Style.php`, `set_z_index`: `round($val) != $val && $val !== "auto"` vira
  `round((float)$val) != (float)$val && $val !== "auto"`. No 7.4, `round('auto')` só avisa e devolve `float(0)`; no
  8.x, a mesma chamada é `TypeError`. Com o `(float)` explícito, a condição dá o mesmo resultado que a linha original
  no 7.4, nos 7.4 e 8.5: 19 valores iguais (`auto`, números, texto numérico, `5px`, `abc`, `inherit`, vazio, `null`,
  espaços, `1e2`, `0x1A`, `true`, `false`; `anexos/pacotes-85/zindex.php`).
- `src/FrameReflower/Block.php:378`: `$height === "auto" && $content_height > $height` vira
  `$height === "auto" && $content_height > 0`. No 7.4, `11.8 > "auto"` compara com `"auto"` convertido em 0 e dá
  verdadeiro, então a altura do bloco vira a do conteúdo. No 8.x, número contra texto não numérico compara como texto
  (`"11.8" > "auto"`), dá falso, e o bloco fica com altura `auto`: o bloco seguinte se sobrepõe.

A 2ª linha foi achada pela árvore de frames (posição e estilo calculado de cada frame, pelo callback `end_frame`):
7.4 × 8.5, primeira diferença. Depois dela, as 4 árvores ficaram iguais, com 0,001 pt de arredondamento numa
coordenada, que não aparece no PDF.

**Como o 8.5 aceita a 0.8.6 só para esse pacote:** um repositório `package` no `composer-85.json` com o mesmo zip e o
mesmo commit da 0.8.6 (`db91d81866c69a42dad1d2926f61515a1e3f42c5`). Ele declara a mesma `require` do pacote, menos a
versão do PHP, que passa de `^7.1` para `^7.1 || ^8.0`. Repositório declarado no `composer.json` raiz vence o
packagist, então só essa definição do `dompdf/dompdf` existe para o Composer do 8.5. Nenhum outro pacote ganha
exceção de versão do PHP. O `--ignore-platform-req=php+` do comando continua, por causa dos 2 da tabela acima.

**O patch na instalação:** `cweagans/composer-patches` (`extra.patches`; o `allow-plugins` do `composer-85.json` já
libera só ele). O `install` roda **com plugins** (o comando registrado não usa `--no-plugins`); sem eles, o dompdf
entraria sem patch. Conferido com `docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+`
sobre a trava nova: a saída mostra
`Applying patches for dompdf/dompdf`, e o `diff -r` contra o zip da 0.8.6 mostra só as 2 linhas e o `PATCHES.txt`
que o plugin grava. A licença do dompdf é LGPL-2.1, e o patch traz só as linhas trocadas.

**Como tirar o patch:** quando o 8.5 puder usar outra versão com o mesmo PDF, apagar o repositório `package`, a
entrada de `extra.patches`, `ecidade/patches/dompdf-0.8.6-php85.patch` e o `cweagans/composer-patches`, se nenhum
outro pacote o usar. Depois, regerar a trava com o comando único.

## Avisos de segurança: os mesmos do 7.4, ignorados por ID

O Composer 2.11 bloqueia no `update` as versões com aviso de segurança publicado, e a trava do PR já tem versões com
aviso. O `composer-85.json` lista em `config.audit.ignore` só os IDs dos avisos que a trava do PR já tem (os mesmos
que o `composer audit --locked` acusa sobre o `composer.lock`). Conferido:

- `update` com a lista: passa.
- Aviso que não está na lista continua bloqueando. Teste: pedir `twig/twig` 2.0.0 foi recusado com `these were not
  loaded, because they are affected by security advisories`.
- `composer audit --locked` da trava do 8.5, contra o `composer.json` do 7.4 e sem a lista: nenhum aviso que a trava
  do PR não tenha.

## Prova 7.4 × 8.5 nos usos do código (critério 2)

`anexos/pacotes-85/roda.sh` roda tudo sem rede. Ele monta o `ecidade/` só para leitura e o `vendor/` de cada lado em
`ecidade/vendor`, como no runtime, e compara. Antes, cria `ecidade/vendor` como ponto de montagem, se faltar. Se um
`docker run` falha ou falta saída de um dos lados, ele para com `FALHOU` e código de saída 1, em vez de comparar
saídas vazias:

```bash
bash docs/migracao-laravel/anexos/pacotes-85/roda.sh ecidade <vendor do 7.4> runtime-85/vendor <imagem 7.4> <imagem 8.5> <saída>
```

Os PDFs são comparados pelo conteúdo (`compara.sh`, poppler): número e tamanho de página (`pdfinfo`), texto
(`pdftotext -layout`) e imagem de cada página (`pdftoppm` a 60 dpi, md5). O binário não serve para comparar, porque
o PDF grava a data de criação.

| Pacote | Uso real reproduzido | Casos | Diferentes |
|---|---|---|---|
| dompdf | `CapaDoDocumento`/`CapaDoDespacho` sobre o HTML dos 4 templates `resources/views/layouts/documentos-template/capa-do-*.blade.php` (compilados pelo Blade de cada lado, dados fixos, logo PNG e JPG): completa; sem logo, sem titular e texto curto; texto longo | 12 PDFs | 0 (também a 300 dpi e na posição de cada palavra, `pdftotext -bbox`) |
| mPDF | `forms/pdf_lovrot.php` (ISO-8859-1, CSS, cabeçalho com imagem, rodapé `{PAGENO}/{nbpg}`), `RelatorioSubcontratacaoController` (opções, CSS, `SetHTMLHeader`, `AddPage` com margens), `db_download_todos_arquivos_visualizador.php` (`Image` por página) e o writer `Mpdf` do PhpSpreadsheet de `src/Library/SpreadSheet/Template/Parser.php` (paisagem e retrato) | 5 PDFs | 0 |
| Faker | `database/factories/ModelFactory.php` (`name`, `unique()->safeEmail`), sementes 1, 42 e 2026 | 150 | 0 |
| laminas-escaper | sem chamada no código do e-cidade; é usado pelo writer HTML do PhpWord. `escapeHtml`, `escapeHtmlAttr`, `escapeJs`, `escapeUrl` e `escapeCss` sobre 11 entradas (acentos, `<>&"'`, controle, UTF-8 inválido) | 55 | 0 |
| htmlpurifier | sem chamada no código do e-cidade; o PhpSpreadsheet só o usa no writer HTML, para comentários (`Writer/Html.php:1819`), e não no PDF que o `Parser.php` usa. `purify` sobre as 11 entradas | 11 | 0 |
| nette/schema, nette/utils | sem chamada no código do e-cidade; entram por `Str::markdown` do Laravel (`league/config`). Markdown com tabela, link, HTML e vazio | 6 | 0 |
| PhpWord (escaper por dentro) | writer HTML com textos acentuados e link | 1 | 0 |

A `ModelFactory.php` não roda no Laravel 8 do PR, por defeito de antes desta tarefa
(`docs/registro/defeitos-laravel8-do-pr.md`). Aqui se prova só o que ela pede ao Faker.

## Com o Laravel 13 na trava do 8.5

A trava do 8.5 passou a ter o Laravel 13.43.0 (PHP8-62). Nenhum dos 9 pacotes desta tarefa muda de versão com ela:
dompdf 0.8.6 com o patch, mPDF 8.2.6, PhpSpreadsheet 1.29.1, PhpWord 0.18.3, htmlpurifier 4.19.0, laminas-escaper
2.18.0, nette/schema 1.3.3, nette/utils 4.0.8 e Faker 1.10.0 continuam como estavam. Mudam pacotes que esses usos
atravessam, e a prova os alcança:

- o Blade que compila as capas (`laravel/framework` 13): o `roda.sh` compila o HTML das capas nos dois lados e compara
  os 12 antes do dompdf;
- o `Str::markdown` (`laravel/framework` 13 e `league/commonmark` 2.10.7), por onde entram os pacotes `nette`;
- o `mpdf/psr-http-message-shim` 2.0.1, o `psr/log` 2.0.0 e o `psr/simple-cache` 3.0.0, que o mPDF e o PhpSpreadsheet
  carregam.

O `composer-85.sh install --no-scripts --ignore-platform-req=php+` sobre a trava do Laravel 13 instala o dompdf com o
patch: o `diff -r` contra o do 7.4 mostra só as 2 linhas e o `PATCHES.txt`. Com essa trava, o mesmo `roda.sh` dá:

| O quê | Casos | Diferentes |
|---|---|---|
| HTML das capas compilado pelo Blade (Laravel 8.73.2 no 7.4, 13.43.0 no 8.5) | 12 | 0 |
| dompdf | 12 PDFs | 0 |
| mPDF | 5 PDFs | 0 |
| Faker | 150 | 0 |
| laminas-escaper, htmlpurifier, nette, PhpWord | 55, 11, 6, 1 | 0 |

## Lacunas

- Só os usos achados no código foram reproduzidos, com HTML e dados fixos. Uma capa com CSS que os 4 templates não
  usam pode passar por linha do dompdf 0.8.6 que não foi exercitada. O mesmo tipo de comparação (número × texto) pode
  existir em outro ponto do pacote.
- Os trechos não passam pelo Laravel de pé, que é da etapa da inicialização (PHP8-62), nem pelo banco: os dados das
  capas são fixos.
- Os `Deprecated` do 8.5 nesses pacotes (parâmetro nulo implícito, `E_STRICT`, tipos de retorno) não mudam a saída e
  ficam como estão.
