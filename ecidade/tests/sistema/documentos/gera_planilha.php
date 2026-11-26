<?php
// ECidade\Library\SpreadSheet\Template\Parser (real) sobre os 21 modelos de config/templates/IN22, sem banco.
require __DIR__ . '/lib.php';

use ECidade\Library\SpreadSheet\Template\Parser;

$arquivos = glob(ECIDADE_PATH . 'config/templates/IN22/*.xlsx');
sort($arquivos);
foreach ($arquivos as $arq) {
    $p = new Parser();
    $p->loadXLS($arq);
    $p->addVariable('#ano#', '2026');
    $p->addVariable('#municipio#', 'Exemplo');
    $p->parse();
    $saida = '/tmp/saida_' . basename($arq);
    $p->save($saida);
    emitir('xlsx-' . basename($arq), file_get_contents($saida));
    if (in_array(basename($arq), ['anexo2.xlsx', 'anexo12.xlsx'], true)) {
        $pdf = '/tmp/saida_' . basename($arq, '.xlsx') . '.pdf';
        $p->save($pdf);
        emitir('xlsx-pdf-' . basename($arq, '.xlsx') . '.pdf', file_get_contents($pdf));
    }
}
