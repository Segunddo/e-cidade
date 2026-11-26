<?php
// T-102: as chamadas de CapaDoDocumento/CapaDoDespacho (app/Domain/Patrimonial/Protocolo/Services) sobre o HTML fixo:
// new Dompdf, loadHtml, setPaper('A4'), render, 3x page_text, output. Texto do rodape fixo (sem data/hora/host).
// Uso: php dompdf.php <vendor> <dir html> <saida>
list(, $v, $in, $out) = $argv;
require "$v/autoload.php";
use Dompdf\Dompdf;
foreach (glob("$in/*.html") as $f) {
  $dompdf = new Dompdf();
  $dompdf->loadHtml(file_get_contents($f));
  $dompdf->setPaper('A4');
  $dompdf->render();
  $dompdf->getCanvas()->page_text(30, 811, "Base: base_fixa", null, 7, array(0, 0, 0));
  $dompdf->getCanvas()->page_text(30, 820, "host/fixo Menu > Fixo Emissor: Usuario Exercicio: 2026 Data: 20/11/2026 - 10:00:00", null, 7, array(0, 0, 0));
  $dompdf->getCanvas()->page_text(530, 820, "Pagina {PAGE_NUM} de {PAGE_COUNT}", null, 7, array(0, 0, 0));
  file_put_contents("$out/" . basename($f, '.html') . '.pdf', $dompdf->output());
  echo basename($f), " ok\n";
}
