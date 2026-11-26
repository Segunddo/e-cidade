<?php
// Duble HTTP local do Pix do BB (router do `php -S`): grava cada pedido em $DUBLE_LOG e devolve respostas fixas.
// Modo lido de /tmp/duble.modo (escrito pelo exercicio): sucesso (padrao), erro400, erro500, invalido. Nenhuma chamada sai do container.
$modo = is_file('/tmp/duble.modo') ? trim(file_get_contents('/tmp/duble.modo')) : 'sucesso';
$cab = array();
foreach ($_SERVER as $k => $v) {
    if (strpos($k, 'HTTP_') === 0) { $cab[strtolower(str_replace('_', '-', substr($k, 5)))] = $v; }
}
if (isset($_SERVER['CONTENT_TYPE'])) { $cab['content-type'] = $_SERVER['CONTENT_TYPE']; }
foreach (array('authorization') as $s) { if (isset($cab[$s])) { $cab[$s] = preg_replace('/^(\w+) .*/', '$1 <segredo>', $cab[$s]); } }
unset($cab['host'], $cab['content-length'], $cab['connection']);
ksort($cab);
$uri = $_SERVER['REQUEST_URI'];
$linha = array('metodo' => $_SERVER['REQUEST_METHOD'], 'uri' => $uri, 'cabecalhos' => $cab, 'corpo' => file_get_contents('php://input'));
file_put_contents(getenv('DUBLE_LOG') ?: '/tmp/duble.jsonl', json_encode($linha) . "\n", FILE_APPEND);
header('Content-Type: application/json');
if ($modo === 'erro400') {
    http_response_code(400);
    echo json_encode(array('erros' => array(array('codigo' => '4769000', 'versao' => '1', 'mensagem' => 'Parametro invalido', 'ocorrencia' => 'x'))));
    exit;
}
if ($modo === 'erro500') { http_response_code(500); echo json_encode(array('erro' => 'interno')); exit; }
if ($modo === 'invalido') { http_response_code(201); echo '{nao-e-json'; exit; }
if (strpos($uri, '/oauth/token') !== false) {
    echo json_encode(array('access_token' => 'tok-do-duble', 'token_type' => 'Bearer', 'expires_in' => 600));
    exit;
}
http_response_code(201);
echo json_encode(array('timestampCriacaoSolicitacao' => '2026-11-14T10:00:00', 'estadoSolicitacao' => 'ATIVA', 'codigoConciliacaoSolicitante' => 'C123',
    'numeroVersaoSolicitacaoPagamento' => 1, 'linkQrCode' => 'http://duble/qr/1', 'qrCode' => '00020126duble'));
