<?php
// mPDF como o codigo proprio o usa: forms/pdf_lovrot.php (relatorios de consulta) e RelatorioSubcontratacaoController.
// As duas classes puxam o banco ao serem incluidas, entao as opcoes e as chamadas do mPDF sao repetidas aqui.
require __DIR__ . '/lib.php';

use Mpdf\HTMLParserMode;
use Mpdf\Mpdf;
use Mpdf\Output\Destination;

$linhas = '';
for ($i = 1; $i <= 120; $i++) {
    $linhas .= "<tr><td>$i</td><td>Descri\xe7\xe3o do item $i</td><td style=\"text-align:right\">" . number_format($i * 1234.5, 2, ',', '.') . '</td></tr>';
}
$tabela = '<table width="100%" border="1"><tr><th>C' . "\xf3" . 'd</th><th>Descri' . "\xe7\xe3" . 'o</th><th>Valor</th></tr>' . $linhas . '</table>';

// pdf_lovrot.php (constructor, config, cabecalho, rodape e montedPageHTML)
$m = new Mpdf(['tempDir' => '/tmp/mpdf/', 'orientation' => 'P', 'margin' => 0, 'margin_top' => 5, 'margin_left' => 5,
    'margin_right' => 5, 'margin_bottom' => 17, 'padding' => 0, 'format' => 'A4']);
$m->charset_in = 'iso-8859-1';
$m->WriteHTML(file_get_contents(ECIDADE_PATH . 'forms/style/pdf_lovrot.css'), HTMLParserMode::HEADER_CSS);
$m->WriteHTML('<div name="header"><h3 style="font-size: 16px">Prefeitura Municipal de Exemplo<br><div style="font-size: 12px">Rua A, 1 - Exemplo - EX</div></h3></div>');
$m->SetHTMLFooter('<div style="font-size: 8px">Base: ecidade_exemplo | Sistema: e-Cidade | Usu&aacute;rio: Exemplo P&aacute;gina {PAGENO} / {nbpg}</div>');
$m->WriteHTML($tabela, HTMLParserMode::HTML_BODY);
emitir('mpdf-lovrot.pdf', $m->Output('', Destination::STRING_RETURN));

// RelatorioSubcontratacaoController
$m = new Mpdf(['tempDir' => '/tmp/mpdf/', 'orientation' => 'P', 'format' => [210, 297], 'autoMarginPadding' => 0]);
$m->WriteHTML(file_get_contents(ECIDADE_PATH . 'storage/assets/css/style.css'), HTMLParserMode::HEADER_CSS);
$m->SetHTMLHeader('<div>Relatório de Subcontratação - Exemplo</div>');
$m->setFooter('{PAGENO}');
$m->AddPage('', '', '', '', '', 5, 5, 35, 15, 2, 0);
$m->WriteHTML('<main>' . mb_convert_encoding($tabela, 'UTF-8', 'ISO-8859-1') . '</main>');
emitir('mpdf-subcontratacao.pdf', $m->Output('', Destination::STRING_RETURN));
