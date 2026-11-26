<?php
// PhpWord TemplateProcessor sobre os modelos .docx do codigo (Contrato.php: contrato de agua; certidoes do cadastro).
require __DIR__ . '/lib.php';

use PhpOffice\PhpWord\Settings;
use PhpOffice\PhpWord\TemplateProcessor;

Settings::setTempDir('/tmp');
$modelos = array_merge(
    [ECIDADE_PATH . 'documentos/templates/agua/contrato.docx'],
    glob(ECIDADE_PATH . 'documentos/templates/cadastro/*.docx')
);
sort($modelos);
foreach ($modelos as $m) {
    $t = new TemplateProcessor($m);
    foreach ($t->getVariables() as $v) {
        $t->setValue($v, 'Valor de ' . $v . ' & acentuação');
    }
    $saida = '/tmp/saida_' . basename($m);
    $t->saveAs($saida);
    emitir('docx-' . basename($m), file_get_contents($saida));
}

// ProcessaDocumentoTemplate::buildQrCode: QRcode::png + TemplateProcessor::setImageValue num modelo com a variavel ${qr}
$pw = new \PhpOffice\PhpWord\PhpWord();
$pw->addSection()->addText('Verifique em: ${qr}');
\PhpOffice\PhpWord\IOFactory::createWriter($pw, 'Word2007')->save('/tmp/modelo_qr.docx');
\PHPQRCode\QRcode::png('https://exemplo.gov.br/verifica/123', '/tmp/qr_doc.png', 'L', 5, 1);
$t = new TemplateProcessor('/tmp/modelo_qr.docx');
$t->setImageValue('qr', '/tmp/qr_doc.png');
$t->saveAs('/tmp/saida_qr.docx');
emitir('docx-com-qr.docx', file_get_contents('/tmp/saida_qr.docx'));
