<?php
// T-102: pacotes sem chamada direta no codigo proprio, pelo caminho por onde as bibliotecas do PR os usam:
//  E laminas-escaper  (PhpWord Writer\HTML: new Escaper(), escapeHtml/escapeHtmlAttr; e os demais metodos)
//  P htmlpurifier      (PhpSpreadsheet Writer\Html: comentario de celula, new HTMLPurifier + purify)
//  N nette/schema+utils (league/config <- league/commonmark <- Illuminate\Support\Str::markdown)
//  W PhpWord Writer HTML inteiro (usa o escaper) com texto acentuado
require $argv[1] . '/autoload.php';
$tmp = $argv[2];
$entradas = ['texto simples', 'ação <b>órgão</b> & "aspas" \'apost\'', '<script>alert(1)</script>', "linha1\nlinha2\t\x01",
  'javascript:x()', 'ü€ 日本 😀', ' ', '', 'a=b&c=d?e#f', '</style><x>', "\xc3\x28"];
$e = new Laminas\Escaper\Escaper('utf-8');
foreach ($entradas as $i => $s) {
  foreach (['escapeHtml', 'escapeHtmlAttr', 'escapeJs', 'escapeUrl', 'escapeCss'] as $m) {
    try { $r = $e->$m($s); } catch (Throwable $x) { $r = get_class($x) . ': ' . $x->getMessage(); }
    echo "E\t$i\t$m\t", json_encode($r), "\n";
  }
}
$p = new HTMLPurifier(); $p->config->set('Cache.SerializerPath', $tmp);
foreach ($entradas as $i => $s) { echo "P\t$i\t", json_encode($p->purify($s)), "\n"; }
foreach (["# Título\n\nTexto *ênfase* e **forte**, [link](http://x)\n\n- a\n- b\n\n| a | b |\n|---|---|\n| 1 | 2 |", "<b>html</b> & `código`", ''] as $i => $md) {
  echo "N\t$i\t", json_encode(Illuminate\Support\Str::markdown($md)), "\n";
  echo "N\t$i\tinline\t", json_encode((new League\CommonMark\CommonMarkConverter(['html_input' => 'escape']))->convertToHtml($md)->getContent()), "\n";
}
$w = new PhpOffice\PhpWord\PhpWord(); $sec = $w->addSection();
foreach ($entradas as $s) { if (mb_check_encoding($s, "UTF-8")) { $sec->addText(htmlspecialchars($s, ENT_COMPAT | ENT_HTML401, "UTF-8")); } }   // flags explicitas: o padrao mudou no PHP 8.1
$sec->addLink('http://x/?a=1&b=2', 'link ação');
$html = PhpOffice\PhpWord\IOFactory::createWriter($w, 'HTML'); $html->save("$tmp/w.html");
echo "W\t", json_encode(preg_replace('/<meta name="(created|modified)"[^>]*>/', '', file_get_contents("$tmp/w.html"))), "\n";
