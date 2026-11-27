<?php
/* Prova dirigida das duas bibliotecas. Rodar no PHP 7.4 e 8.5.
 * Uso: php -n prova_offsets_nucleo.php /caminho/da/pasta/ecidade
 * Sem banco, rede, sessao ou bootstrap da aplicacao.
 */
error_reporting(E_ALL & ~E_DEPRECATED);
set_error_handler(function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) {
        return false;
    }
    throw new ErrorException($message, 0, $severity, $file, $line);
});
if (($argc !== 2 && $argc !== 3) || !is_dir($argv[1])) {
    fwrite(STDERR, "Informe a pasta ecidade para a prova dirigida.\n");
    exit(2);
}
$root = realpath($argv[1]);
// Usa a dependencia original, sem bootstrap do aplicativo.
// A prova cobre Services_JSON; o wrapper JSON e o login ficam fora do escopo.
require $root . '/std/DBString.php';
function modification($file) { return $file; }
require $root . '/libs/JSON.php';
require $root . '/fpdf151/fpdf.php';

$results = array();
function record_case($name, $actual, $expected) {
    global $results;
    if ($actual !== $expected) {
        throw new RuntimeException('Resultado inesperado em ' . $name);
    }
    $results[$name] = $actual;
}
$json = new Services_JSON(SERVICES_JSON_LOOSE_TYPE);
record_case('json_encode_ascii', $json->encode('Cidade'), '"Cidade"');
record_case('json_encode_escape', $json->encode("a\"b\\c\n"), '"a\\"b\\\\c\\n"');
record_case('json_encode_unicode', $json->encode("a\xc3\xa7\xc3\xa3o"), '"a\\u00e7\\u00e3o"');
record_case('json_encode_array', $json->encode(array(1, true, null)), '[1,true,null]');
record_case('json_decode_array', $json->decode_interno('[1,true,null]'), array(1, true, null));
record_case('json_decode_unicode', $json->decode_interno('"a\\u00e7\\u00e3o"'), "a\xc3\xa7\xc3\xa3o");
record_case('json_decode_nested', $json->decode_interno('{"cidade":"A","valores":[1,2]}'), array('cidade'=>'A', 'valores'=>array(1,2)));
record_case('json_decode_escape', $json->decode_interno('"a\\"b\\\\c\\n"'), "a\"b\\c\n");
record_case('json_utf16_utf8', bin2hex($json->utf162utf8("\x00\xe7")), 'c3a7');
record_case('json_utf8_utf16', bin2hex($json->utf82utf16("\xc3\xa7")), '00e7');

// Fonte sintetica de largura fixa, sem depender de arquivos de fontes do app.
// Permite exercitar GetStringWidth, Write e orientacao com a classe FPDF real.
function synthetic_pdf() {
    $pdf = new FPDF();
    $widths = array();
    for ($i=0; $i<256; $i++) { $widths[chr($i)] = 600; }
    $pdf->CurrentFont = array('cw'=>$widths, 'i'=>1);
    $pdf->FontSize = 10;
    return $pdf;
}
$pdf = synthetic_pdf();
record_case('fpdf_string_width_ascii', $pdf->GetStringWidth('abc'), 18);
record_case('fpdf_string_width_latin1', $pdf->GetStringWidth("a\xe7"), 12);
record_case('fpdf_string_width_empty', (float)$pdf->GetStringWidth(''), 0.0);
$pdf->_beginpage('landscape');
record_case('fpdf_orientation', $pdf->CurOrientation, 'L');
$pdf->Write(5, "Texto de prova\nlinha dois");
record_case('fpdf_write_contains_text', strpos($pdf->pages[1], 'Texto de prova') !== false, true);
record_case('fpdf_write_second_line', strpos($pdf->pages[1], 'linha dois') !== false, true);

// Exercita os 256 bytes de texto Latin1 sem converter a codificacao.
for ($i=0; $i<256; $i++) {
    record_case('fpdf_byte_'.$i, $pdf->GetStringWidth(chr($i)), 6);
}
foreach (array(0, 1, 2, 79, 256, 1024) as $length) {
    record_case('fpdf_length_'.$length, (float)$pdf->GetStringWidth(str_repeat('A', $length)), (float)($length*6));
}
// Conversoes puramente PHP, sem mbstring, incluindo limites de 1/2/3 bytes.
$points = array(0, 1, 31, 32, 127, 128, 255, 256, 2047, 2048, 55295, 57344, 65535);
for ($point=0; $point<65536; $point+=257) {
    if ($point<55296 || $point>57343) { $points[]=$point; }
}
foreach (array_unique($points) as $point) {
    $utf16=pack('n', $point);
    $utf8=$json->utf162utf8($utf16);
    // A biblioteca da referencia devolve ASCII com um byte nesta funcao.
    // Preserva esse comportamento, sem introduzir uma correcao funcional.
    $expected=$point<128 ? bin2hex(chr($point)) : bin2hex($utf16);
    record_case('unicode_reference_'.$point, bin2hex($json->utf82utf16($utf8)), $expected);
}
$jsonValues=array('', '0', 0, -7, 12.5, false, true, null,
    array(), array(0, '', false, null), array('cidade'=>'Joao Pessoa', 'total'=>12.5),
    array(array('id'=>1), array('id'=>2)), "\t\r\n\b\f", "\xc3\xa7\xe2\x82\xac");
foreach ($jsonValues as $i=>$value) {
    $encoded=$json->encode($value);
    record_case('json_roundtrip_'.$i, $json->decode($encoded), $value);
}
// PDF completo com a fonte Courier original do repositorio.
// A data de criacao e o unico campo normalizado para a comparacao.
define('FPDF_FONTPATH', $root.'/fpdf151/font/');
$document=new FPDF();
$document->Open();
$document->SetCompression(false);
$document->SetTitle('Prova sintetica do nucleo');
$document->AddPage('portrait');
$document->SetFont('Courier', '', 12);
$document->Write(6, "Documento sintetico\nTexto Latin1: a\xe7\xe3o\n");
$document->AddPage('landscape');
$document->SetFont('Courier', '', 12);
$document->Write(6, 'Pagina em paisagem');
$document->Close();
$normalized=preg_replace('/D:[0-9]{14}/', 'D:20000101000000', $document->buffer, -1, $dateCount);
record_case('pdf_creation_date_fields', $dateCount, 1);
record_case('pdf_header', substr($normalized, 0, 5), '%PDF-');
record_case('pdf_eof', substr(trim($normalized), -5), '%%EOF');
record_case('pdf_page_count', $document->PageNo(), 2);
record_case('pdf_first_text', strpos($normalized, 'Documento sintetico')!==false, true);
record_case('pdf_second_text', strpos($normalized, 'Pagina em paisagem')!==false, true);
if ($argc===3) {
    $output=fopen($argv[2], 'xb');
    if ($output===false) { throw new RuntimeException('Nao foi possivel criar PDF de prova.'); }
    if (fwrite($output, $normalized)!==strlen($normalized)) {
        throw new RuntimeException('Escrita incompleta do PDF de prova.');
    }
    fclose($output);
}
ksort($results);
echo json_encode(array('cases'=>count($results), 'results'=>$results,
    'pdf_normalized_sha256'=>hash('sha256', $normalized)), JSON_UNESCAPED_SLASHES), "\n";
