<?php
// uso: php teste_phar.php <phar> <saida.xls>  -- carrega todas as classes e gera um XLS (Excel5) deterministico
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING & ~2048);
$phar = $argv[1]; $saida = $argv[2];
require_once("phar://$phar/PHPExcel.php");
$it = new RecursiveIteratorIterator(new Phar($phar)); $ok = 0; $falha = array();
foreach ($it as $f) {
    $rel = substr($f->getPathname(), strlen("phar://$phar/"));
    if (substr($rel, -4) !== '.php' || strpos($rel, 'PHPExcel/') !== 0) continue;
    // renderizadores de grafico e de PDF exigem bibliotecas externas (JpGraph, TCPDF...) ausentes: falham igual em qualquer runtime
    if (strpos($rel, 'PHPExcel/Chart/Renderer/') === 0 || strpos($rel, 'PHPExcel/Writer/PDF/') === 0) continue;
    $cls = str_replace('/', '_', substr($rel, 0, -4));
    // so arquivos que declaram EXATAMENTE a classe do nome (JAMA/ e afins nao seguem a convencao)
    if (!preg_match('/^\s*(abstract\s+|final\s+)?(class|interface)\s+'.preg_quote($cls,'/').'\b/mi', file_get_contents($f->getPathname()))) continue;
    try { if (class_exists($cls) || interface_exists($cls)) $ok++; } catch (Throwable $e) { $falha[] = "$cls: ".$e->getMessage(); }
}
echo "classes/interfaces carregadas: $ok", ($falha ? " | FALHAS: ".implode('; ', $falha) : ""), "\n";
$x = new PHPExcel();
$x->getProperties()->setCreated(0)->setModified(0)->setCreator('teste')->setLastModifiedBy('teste');
PHPExcel_Cell::setValueBinder(new PHPExcel_Cell_AdvancedValueBinder());
$s = $x->setActiveSheetIndex(0);
foreach (array('A','B','C','D','E') as $c) $x->getActiveSheet()->getColumnDimension($c)->setAutoSize(true);
$dados = array(array('Nome','Matricula','Valor','Admissao','Ativo'), array('JOSE DA SILVA', 123, '1.234,56', '2024-03-15', true),
               array('MARIA', '0042', 'R$ 99,90', '15/03/2024', false), array('', 0, '', '', null), array('ÁÉÍÓÚ ção', -7.5, '3%', '2024-12-31 10:00', 'x'));
foreach ($dados as $i => $l) foreach ($l as $j => $v) $s->setCellValueByColumnAndRow($j, $i + 1, $v);
$w = PHPExcel_IOFactory::createWriter($x, 'Excel5'); $w->save($saida);
echo "bytes: ", filesize($saida), " md5: ", md5_file($saida), "\n";
