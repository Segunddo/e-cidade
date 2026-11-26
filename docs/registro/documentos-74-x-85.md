# Documentos (PDF, planilha, Word, etiquetas e QR) no 7.4 × 8.5, sem banco

**Resumo (PHP8-70):** 39 documentos gerados pelo código próprio, com dados de exemplo e sem banco, saem **iguais** no PHP 7.4 (vendor do
`ecidade/composer.lock` do PR) e no PHP 8.5 (`runtime-85/vendor`): 0 diferenças. Iguais em páginas, tamanho de página, texto,
posição das palavras, imagens e pixels (PDF), nas partes do zip (xlsx, docx) e nos pixels (PNG). Ajuste no código próprio: 2 linhas
em `Parser.php` e 1 propriedade em cada `EtiquetaModelo0{1,2}Builder.php` (avisos do 8.5; o 7.4 fica provado igual).

## 1. Geradores em uso (arquivos `.php` fora do `vendor/`)

| Biblioteca | Arquivos | Versão no 7.4 (lock do PR) | Versão no 8.5 |
|---|---|---|---|
| dompdf | 5 | v0.8.6 | v0.8.6 + patch de 2 linhas (`ecidade/patches/dompdf-0.8.6-php85.patch`) |
| mPDF | 6 | v8.2.4 | v8.2.6 |
| PhpSpreadsheet | 28 (16 em `src/.../TCE/RO/IN22`) | 1.29.1 | 1.29.1 |
| PhpWord | 21 | 0.18.3 | 0.18.3 |
| Pimaco (+ picqer, código de barras) | 6 | v1.4.5 (picqer v0.4.0) | v1.4.5 (picqer v0.4.0) |
| QR Code (`aferrandini/phpqrcode`) | 13 (10 em `fpdf151/impmodelos`) | 1.0.1 | 1.0.1 |
| `bacon/bacon-qr-code`, `endroid/qr-code` | só um `use BaconQrCode\Common\Mode` em `CensoEstado.php`, sem chamada | 1.0.3 / 2.5.1 | iguais |

## 2. O que foi gerado (`ecidade/tests/sistema/documentos/`)

| Gerador | Documentos | Como usa o código próprio |
|---|---|---|
| `gera_dompdf.php` | 4 capas do Protocolo (processo, memorando, ofício, despacho) | os 4 modelos Blade reais de `resources/views/layouts/documentos-template`, mesmas chamadas do `CapaDoDocumento` (A4, `page_text`) |
| `gera_mpdf.php` | 2 PDFs (relatório de consulta, subcontratação) | mesmas opções e chamadas do mPDF de `forms/pdf_lovrot.php` e de `RelatorioSubcontratacaoController`, com os CSS reais; as duas classes não são incluídas porque conectam ao banco |
| `gera_planilha.php` | 21 modelos `config/templates/IN22/*.xlsx` em xlsx + 2 em PDF (mPDF) | a classe real `ECidade\Library\SpreadSheet\Template\Parser` |
| `gera_word.php` | 5 `.docx` (contrato de água, 4 certidões) + 1 com imagem QR | `TemplateProcessor` como em `Contrato.php`; QR como em `ProcessaDocumentoTemplate` |
| `gera_etiquetas.php` | 2 PDFs de etiquetas Pimaco (12 etiquetas cada) + 2 PNG de QR | os `EtiquetaModelo01/02Builder` reais; `EtiquetasPimacoPDF::gerar()` repetido em subclasse do `Pimaco` porque o construtor dela não repassa o `tempDir` do mPDF e o vendor é somente leitura |

A Pimaco usa código de barras Code 128: as barras ficam com as mesmas imagens (122 × 15 px) e os mesmos pixels renderizados nos
dois runtimes, ou seja, **a mesma largura impressa**.

## 3. Resultado

`python3 ecidade/tests/sistema/documentos/compara.py` (da raiz do repositório): roda cada gerador no 7.4 e no 8.5 por
`docker/composer-85/roda-isolado.sh` (imagens do projeto, `--network none`) e compara. **39 de 39 iguais**, `DIFERENCAS: 0`.
Os comparadores foram verificados contra falso "igual": dois PDFs diferentes, dois PNG diferentes e as etiquetas 01 × 02 são
detectados como diferentes.

Uma normalização: no `xl/workbook.xml` do `anexo7.xlsx` o 7.4 grava `'Anexo 10'!$1:$9` e o 8.5 `&#039;Anexo 10&#039;!$1:$9`
(`htmlspecialchars` escapa a aspa simples por padrão a partir do 8.1). É o mesmo XML; o comparador troca `&#039;` por `'`.

## 4. Ajustes no código próprio (7.4 provado igual antes e depois)

| Arquivo | Mudança | Motivo |
|---|---|---|
| `src/Library/SpreadSheet/Template/Parser.php` (linhas 124 e 156) | `str_replace(' ', '', (string)$cell->getValue())` | `getValue()` devolve `null` em células vazias; o 8.5 emitia 54.190 avisos `Passing null to parameter #3`. Agora 0 |
| `app/Domain/Patrimonial/Patrimonio/Builders/EtiquetaModelo01Builder.php` e `…02Builder.php` | `private $barcode;` | `setBarcode()` criava a propriedade dinamicamente (`Creation of dynamic property`, 12 por classe no 8.5). Agora 0 |

Prova do 7.4: saídas do 7.4 antes e depois da mudança idênticas (23 documentos da planilha e 4 das etiquetas, resumo igual).

## 5. Avisos que sobram no 8.5 (sem mudança de saída)

| Gerador | Avisos no 8.5 | Onde |
|---|---|---|
| dompdf | 461 | `dompdf/dompdf` 416, `laravel/framework` 36, `guzzlehttp/promises` 6, `std/DBDate.php` 2 (`getDatasNoIntervalo`: tipo anulável implícito), `opis/closure` 1 |
| mPDF | 10 | 6 + 2 + 1 da carga do `vendor` e 1 do mPDF (o 7.4 também tem esse 1) |
| planilha | 1.353 | `phpoffice/phpspreadsheet` 1.344 (parâmetro anulável implícito), mais os 9 da carga |
| Word | 26 | `phpoffice/phpword` 15, `aferrandini/phpqrcode` 2, mais os 9 da carga |
| etiquetas | 752 | `picqer/php-barcode-generator` 510, `aferrandini/phpqrcode` 133, `proner/phppimaco` 100, mais os 9 da carga |

São todos `Deprecated` de pacote do `vendor/` (e 2 de `std/DBDate.php`, que não foi alterado: a troca de tipos anuláveis implícitos no
legado inteiro é outra tarefa). Não mudam a saída.

## 6. Limites

- Não há banco: cada gerador usa dados de exemplo, não os dados reais de um município. Texto longo, acentos e várias páginas
  estão nos exemplos; fontes de rodapé com `{PAGE_COUNT}` do dompdf e a quebra de página saíram iguais.
- A comparação de PDF usa as mesmas fontes dos dois lados (as embutidas das bibliotecas); fontes do sistema não entram.
- O 8.5 usa o mPDF v8.2.6 (o 7.4, v8.2.4): sem diferença de saída nos 2 PDFs do mPDF, nos 2 da planilha em PDF e nas 2 de etiquetas, que também passam por ele.

## 7. Como reproduzir

```bash
# vendors: 8.5 e a referencia do 7.4 (composer install do ecidade/composer.lock; ecidade/vendor local pode estar desatualizado)
bash docker/composer-85/composer-85.sh install --no-scripts --ignore-platform-req=php+
docker run --rm --network host -u "$(id -u):$(id -g)" -v "$PWD/ecidade:/app:ro" -v "$PWD/runtime-85/referencia-74/vendor:/vendor74" \
  -v "$PWD/runtime-85/composer-home:/composer" -e COMPOSER_VENDOR_DIR=/vendor74 -e COMPOSER_HOME=/composer -w /app \
  ecidade-composer-85:2.11.2 composer --no-interaction install --no-scripts --ignore-platform-reqs --no-plugins
python3 ecidade/tests/sistema/documentos/compara.py            # todos; ou: ... compara.py gera_planilha gera_word
```

Precisa de `pdfinfo`, `pdftotext`, `pdfimages`, `pdftoppm` (poppler-utils) e Python com Pillow no computador de quem roda.

## 8. Repetição com o Laravel 13.43 e o Passport 13.12 no 8.5 (PHP8-70, T-142)

`runtime-85/vendor` reinstalado do `ecidade/composer-85.lock` com `laravel/framework` v13.43.0 (era v8.73.2); o 7.4 continua com o
lock do PR. Dois documentos novos no gerador de etiquetas: o QR da própria Pimaco (`Tag::qrcode`, que usa `endroid/qr-code` 2.5.1 e
`bacon/bacon-qr-code` 1.0.3), sem e com rótulo. Resultado de `compara.py`: **41 documentos, 40 iguais, 1 conhecida, 0 diferenças**
(dompdf 4, mPDF 2, planilha 23, Word 6, etiquetas e QR 6). Com o Laravel 13 o Blade (`Illuminate\View`) dos 4 modelos de capa
continua renderizando igual, e somem os avisos de `laravel/framework`, `guzzlehttp/promises` e `opis/closure` que a carga do vendor
dava no Laravel 8 (9 a 43 por gerador).

| Gerador | Avisos no 8.5 (Laravel 13) |
|---|---|
| dompdf | 418 (`dompdf/dompdf` 416, `std/DBDate.php` 2) |
| mPDF | 1 (o 7.4 também tem) |
| planilha | 1.344 (`phpoffice/phpspreadsheet`) |
| Word | 17 (`phpoffice/phpword` 15, `aferrandini/phpqrcode` 2) |
| etiquetas e QR | 7.348 (`bacon/bacon-qr-code` 6.542, `picqer/php-barcode-generator` 510, `proner/phppimaco` 163, `aferrandini/phpqrcode` 133) |

**Diferença conhecida (`pimaco-qrcode-rotulo.pdf`):** o QR em si sai igual (`pimaco-qrcode.pdf`, sem rótulo, é igual em páginas, texto,
posições, imagens e pixels). Com rótulo, só as linhas do texto sob o QR da imagem embutida (120 × 143 px, linhas 121 a 133) diferem
em pixels: o `endroid/qr-code` desenha o rótulo com o GD, e o 7.4 do PR usa o `libgd` do sistema (GD 2.3.3) enquanto a imagem do 8.5
(`php:8.5-apache`) traz o GD embutido (compatível com 2.1.0): o antialiasing do texto muda. É diferença das imagens dos runtimes, não
do código ou das bibliotecas; o código próprio não chama `Tag::qrcode`. `compara.py` imprime `conhecida` e não conta como diferença.

**`--ignore-platform-req=php+` não sai:** `composer-85.sh prohibits php 8.5.12 --locked` agora lista só 2 pacotes (eram 10):
`bacon/bacon-qr-code` 1.0.3 (`^5.4|^7.0`) e `khanamiryan/qrcode-detector-decoder` 1 (`^5.6|^7.0`). Os dois vêm de
`endroid/qr-code` 2.5.1, que o `proner/phppimaco` v1.4.5 exige (`^2.5`); v1.4.5 é a última versão da Pimaco e não há `endroid/qr-code` 2.x
mais novo. Sem a flag a resolução falha. Os dois pacotes funcionam no 8.5 (o QR sai igual), então a flag fica nos comandos do
`estrutura-85.md`. Sair dela exige trocar a Pimaco por outra biblioteca de etiquetas ou aceitar uma versão própria de
`endroid/qr-code` (4.x ou 5.x), com API diferente do que a Pimaco chama.
