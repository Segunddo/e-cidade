<?php
// T-102: as 4 formas de uso do mPDF no codigo do PR, com as mesmas opcoes e chamadas, entrada fixa, sem banco.
//  M1 forms/pdf_lovrot.php (GerarPDFLovrot)    M2 RelatorioSubcontratacaoController
//  M3 db_download_todos_arquivos_visualizador  M4 src/Library/SpreadSheet/Template/Parser.php (writer Mpdf do PhpSpreadsheet)
// Uso: php mpdf.php <vendor> <ecidade> <saida>
list(, $v, $e, $out) = $argv;
require "$v/autoload.php";
use Mpdf\Mpdf; use Mpdf\HTMLParserMode; use Mpdf\Output\Destination;
@mkdir("$out/tmp"); chdir($e);   // pdf_lovrot usa src relativo "imagens/files/..."
$latin = function ($s) { return mb_convert_encoding($s, 'ISO-8859-1', 'UTF-8'); };
$linhas = ''; for ($i = 1; $i <= 150; $i++) { $linhas .= "<tr><td>$i</td><td>" . $latin("Descrição do item nº $i - ação/órgão") . "</td><td>" . number_format($i * 1234.56, 2, ',', '.') . "</td></tr>"; }

// M1
$m = new Mpdf(['tempDir' => "$out/tmp", 'orientation' => 'P', 'margin' => 0, 'margin_top' => 5, 'margin_left' => 5,
  'margin_right' => 5, 'margin_bottom' => 17, 'padding' => 0, 'format' => 'A4']);
$m->charset_in = 'iso-8859-1';
$m->WriteHTML(file_get_contents("$e/forms/style/pdf_lovrot.css"), HTMLParserMode::HEADER_CSS);
$m->WriteHTML($latin('<div name="header"><div style="float: left; width: 60%;"><img width="78" style="float:left; margin-right: 2em" src="imagens/files/Brasao.png"><h3 style="font-size: 16px">Prefeitura de São João<br><div style="font-weight: 300; font-size: 12px">Rua A, 1, Sala 2<br>São João - RS<br>(51) 3333-4444 - CNPJ: 00.000.000/0001-91<br>a@b.c<br>www.x</div></h3></div><div style="border: solid 1px #000; float: left; width: 39%; height: 115px; background: #eee; border-radius: 1em 1em 1em 0"><div style="padding: 1em 2em; font-size: 12px"><b>Exerc&iacute;cio:</b> 2026</div></div></div>'));
$rod = '<div><table style="font-size: 8px; width: 100%"><tr><td>Base: b | Sistema: e-Cidade | Usu&aacute;rio: Fulano</td></tr></table><table style="width: 100%; font-size: 8px;"><tr><td>Departamento</td><td style="text-align: right">TOKENFIXO - P&aacute;gina {PAGENO} / {nbpg}</td></tr></table></div>';
$m->SetHTMLFooter($rod); $m->DefHTMLFooterByName('myFooter', $rod);
$m->WriteHTML("<table border='1'>$linhas</table>", HTMLParserMode::HTML_BODY);
$m->Output("$out/m1_lovrot.pdf", Destination::FILE);

// M2
$m = new Mpdf(['tempDir' => "$out/tmp", 'orientation' => 'P', 'format' => [210, 297], 'autoMarginPadding' => 0]);
$m->WriteHTML(file_get_contents("$e/storage/assets/css/style.css"), HTMLParserMode::HEADER_CSS);
$m->SetHTMLHeader('<table width="100%"><tr><td><img src="imagens/files/Brasao.jpg" width="60"></td><td>Prefeitura de São João<br>Relatório de Subcontratação<br>Período: 01/01/2026 a 20/11/2026</td></tr></table>');
$m->setFooter('{PAGENO}');
$m->AddPage('', '', '', '', '', 5, 5, 35, 15, 2, 0);
$m->WriteHTML('<main><table border="1" width="100%">' . mb_convert_encoding($linhas, 'UTF-8', 'ISO-8859-1') . '</table><p>Rodapé do corpo.</p></main>');
$m->Output("$out/m2_subcontratacao.pdf", Destination::FILE);

// M3
$m = new Mpdf(['orientation' => 'P', 'pagenumPrefix' => 'Pag ', 'nbpgPrefix' => '/', 'tempDir' => "$out/tmp"]);
$m->setFooter('{PAGENO}{nbpg}');
foreach (['imagens/files/Brasao.png', 'imagens/files/Brasao.jpg', 'imagens/files/Brasao2.png'] as $arq) { $m->AddPage(); $m->Image($arq, 15, 10); }
$m->Output("$out/m3_visualizador.pdf", Destination::FILE);

// M4
$s = new PhpOffice\PhpSpreadsheet\Spreadsheet(); $w = $s->getActiveSheet();
$w->fromArray([['Código', 'Descrição', 'Valor']], null, 'A1');
for ($i = 1; $i <= 80; $i++) { $w->fromArray([[$i, "Item ação nº $i", $i * 10.5]], null, 'A' . ($i + 1)); }
$w->getStyle('C2:C81')->getNumberFormat()->setFormatCode('#,##0.00');
foreach ([['m4_parser_save', true], ['m4_parser_download', false]] as list($nome, $paisagem)) {
  $wr = new PhpOffice\PhpSpreadsheet\Writer\Pdf\Mpdf($s);
  $wr->setTempDir("$out/tmp");
  if ($paisagem) { $wr->setOrientation(PhpOffice\PhpSpreadsheet\Worksheet\PageSetup::ORIENTATION_LANDSCAPE); }
  $wr->setPaperSize(PhpOffice\PhpSpreadsheet\Worksheet\PageSetup::PAPERSIZE_A4);
  $wr->save("$out/$nome.pdf");
}
echo "ok\n";
