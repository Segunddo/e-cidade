<?php
// uso: php teste_phar.php <phar> <saida.xls>  -- carrega todas as classes e gera um XLS (Excel5) deterministico
//
// O QUE FAZ: teste funcional do ext/php/PHPExcel.phar (biblioteca de terceiros dentro de .phar, a 12a lacuna,
// docs/registro/area-recursos-humanos.md, "PHPExcel.phar PORTADO"). Script de investigacao pontual daquele
// porte, nao um passo do guia; serve de novo se o .phar for mexido.
// COMO FAZ: (1) percorre o .phar e, para cada PHPExcel/<Caminho>.php que declara a classe/interface
// PHPExcel_<Caminho>, chama class_exists() -- o autoloader do proprio PHPExcel carrega o arquivo, o que pega
// erro de declaracao, assinatura incompativel (LSP) e construtor; (2) gera uma planilha pelo escritor Excel5
// com texto, numero, moeda, data, booleano, nulo e acento, com datas de criacao/modificacao fixas.
// Roda nos DOIS runtimes (sintaxe de 5.6): a comparacao feita foi 5.6 com o .phar original = 5.6 com o novo
// = 8.5 com o novo, pelo md5 do XLS, descontados os 16 bytes do carimbo de hora do conteiner OLE (que mudam
// ate entre duas execucoes do mesmo .phar).
// Uso tipico (scratchpad/ nao e montado: copiar antes):
//   docker cp scratchpad/teste_phar.php ecidade_php85:/tmp/teste_phar.php
//   docker exec ecidade_php85 php /tmp/teste_phar.php /var/www/html/ext/php/PHPExcel.phar /tmp/t85.xls
// ENTRADAS: caminho do .phar e do .xls a gravar. SAIDAS: no stdout, "classes/interfaces carregadas: N" (e as
// falhas capturadas) e "bytes: ... md5: ..."; efeito: grava o .xls.
//
// 2048 = E_STRICT, escrito como numero porque a constante e descontinuada no PHP 8.4.
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
    // Throwable so existe a partir do PHP 7: no 5.6 o catch compila mas nunca casa, e uma falha de carga e fatal
    try { if (class_exists($cls) || interface_exists($cls)) $ok++; } catch (Throwable $e) { $falha[] = "$cls: ".$e->getMessage(); }
}
echo "classes/interfaces carregadas: $ok", ($falha ? " | FALHAS: ".implode('; ', $falha) : ""), "\n";
$x = new PHPExcel();
// datas fixas e autor fixo: sem isso o XLS carregaria a hora da execucao e o md5 nunca bateria
$x->getProperties()->setCreated(0)->setModified(0)->setCreator('teste')->setLastModifiedBy('teste');
PHPExcel_Cell::setValueBinder(new PHPExcel_Cell_AdvancedValueBinder());
$s = $x->setActiveSheetIndex(0);
foreach (array('A','B','C','D','E') as $c) $x->getActiveSheet()->getColumnDimension($c)->setAutoSize(true);
$dados = array(array('Nome','Matricula','Valor','Admissao','Ativo'), array('JOSE DA SILVA', 123, '1.234,56', '2024-03-15', true),
               array('MARIA', '0042', 'R$ 99,90', '15/03/2024', false), array('', 0, '', '', null), array('ÁÉÍÓÚ ção', -7.5, '3%', '2024-12-31 10:00', 'x'));
// o AdvancedValueBinder (ligado acima) tenta reconhecer numero, porcentagem, moeda e data dentro do texto:
// os valores variados abaixo exercitam esse parser, que e onde 5.6 e 8.5 poderiam divergir
foreach ($dados as $i => $l) foreach ($l as $j => $v) $s->setCellValueByColumnAndRow($j, $i + 1, $v);
$w = PHPExcel_IOFactory::createWriter($x, 'Excel5'); $w->save($saida);
echo "bytes: ", filesize($saida), " md5: ", md5_file($saida), "\n";
