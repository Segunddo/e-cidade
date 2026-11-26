<?php
// PHP8-62: o cliente HTTP do PR (Guzzle direto: `new Client(...)`, request/get/post/put/delete/requestAsync()->wait(), headers, form_params, json,
// multipart, auth, base_uri, verify, http_errors e os erros ClientException/ServerException/ConnectException) contra um duble local
// (php -S 127.0.0.1, dentro do contêiner, sem rede). Cada caso imprime o pedido que o duble recebeu e o que o cliente observou.
// Uso (roda-isolado.sh): php http_cliente_prova.php <vendor com guzzlehttp/guzzle>. Relogio e boundary normalizados.
error_reporting(E_ALL & ~E_DEPRECATED);
date_default_timezone_set('America/Sao_Paulo');
require $argv[1] . '/autoload.php';
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;
use GuzzleHttp\Exception\ConnectException;
use GuzzleHttp\Exception\ServerException;
use GuzzleHttp\Exception\RequestException;

$dir = sys_get_temp_dir() . '/http_duble_' . getmypid();
mkdir($dir);
$log = $dir . '/log.jsonl';
file_put_contents($dir . '/router.php', <<<'PHP'
<?php
$log = getenv('DUBLE_LOG');
$h = array();
foreach (getallheaders() as $k => $v) { $h[strtolower($k)] = $v; }
ksort($h);
$body = file_get_contents('php://input');
file_put_contents($log, json_encode(array('metodo' => $_SERVER['REQUEST_METHOD'], 'uri' => $_SERVER['REQUEST_URI'], 'cabecalhos' => $h, 'corpo' => $body)) . "\n", FILE_APPEND);
$p = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
switch (true) {
    case $p === '/ok': header('Content-Type: application/json'); echo '{"ok":true,"acentuacao":"ação"}'; break;
    case $p === '/criado': http_response_code(201); header('Content-Type: application/json'); header('Location: /ok'); echo '{"id":7}'; break;
    case $p === '/vazio': http_response_code(204); break;
    case $p === '/xml': header('Content-Type: application/xml'); echo '<r><s>ok</s></r>'; break;
    case $p === '/e400': http_response_code(400); header('Content-Type: application/json'); echo '{"erro":"requisicao invalida","campo":"cnpj"}'; break;
    case $p === '/e401': http_response_code(401); echo 'nao autorizado'; break;
    case $p === '/e404': http_response_code(404); echo str_repeat('x', 300); break;
    case $p === '/e500': http_response_code(500); echo 'falha interna'; break;
    case $p === '/e503': http_response_code(503); header('Retry-After: 5'); echo ''; break;
    case $p === '/redireciona': http_response_code(302); header('Location: /ok'); break;
    case $p === '/gz': header('Content-Encoding: gzip'); header('Content-Type: text/plain'); echo gzencode('texto comprimido'); break;
    case $p === '/lento': usleep(1500000); echo 'tarde'; break;
    default: http_response_code(404); echo 'sem rota';
}
PHP
);
$porta = 0;
for ($t = 0; $t < 20 && !$porta; $t++) {
    $p = random_int(20000, 60000);
    $s = @stream_socket_server("tcp://127.0.0.1:$p", $e, $m);
    if ($s) { fclose($s); $porta = $p; }
}
$proc = proc_open(array(PHP_BINARY, '-S', "127.0.0.1:$porta", '-t', $dir, $dir . '/router.php'), array(1 => array('file', '/dev/null', 'w'), 2 => array('file', '/dev/null', 'w')), $pipes, $dir, array('DUBLE_LOG' => $log, 'PHP_CLI_SERVER_WORKERS' => '4'));
for ($i = 0; $i < 50; $i++) { if (@fsockopen('127.0.0.1', $porta)) { break; } usleep(100000); }
$base = "http://127.0.0.1:$porta";

function norm($s, $porta)
{
    $s = str_replace("127.0.0.1:$porta", 'HOST', $s);
    return preg_replace(array('/[0-9a-f]{32}/', '/boundary=[0-9A-Za-z]+/', '/--[0-9a-f]{13}/'), array('BOUNDARY', 'boundary=BOUNDARY', '--BOUNDARY'), $s);
}
function ultimo($log, $porta)
{
    $l = file($log, FILE_IGNORE_NEW_LINES);
    $r = json_decode(end($l), true);
    $r['cabecalhos']['host'] = 'HOST';
    $ua = isset($r['cabecalhos']['user-agent']) ? $r['cabecalhos']['user-agent'] : '';
    $r['cabecalhos']['user-agent'] = preg_replace('#^(GuzzleHttp/\d+).*$#', '$1 <versao do curl e do PHP>', $ua);
    $r['corpo'] = norm($r['corpo'], $porta);
    if (isset($r['cabecalhos']['content-type'])) { $r['cabecalhos']['content-type'] = norm($r['cabecalhos']['content-type'], $porta); }
    return $r;
}
$n = 0;
function caso($id, $rot, callable $f, $log, $porta)
{
    global $n;
    $antes = file_exists($log) ? count(file($log)) : 0;
    try {
        $r = $f();
        $obs = array('status' => $r->getStatusCode(), 'razao' => $r->getReasonPhrase(), 'tipo' => $r->getHeaderLine('Content-Type'),
            'corpo' => norm((string) $r->getBody(), $porta), 'location' => $r->getHeaderLine('Location'));
    } catch (Throwable $e) {
        $obs = array('excecao' => get_class($e), 'mensagem' => norm(preg_replace('/\s+/', ' ', $e->getMessage()), $porta));
        if ($e instanceof RequestException && $e->getResponse()) {
            $obs['resposta'] = array('status' => $e->getResponse()->getStatusCode(), 'corpo' => norm((string) $e->getResponse()->getBody(), $porta));
        }
        $obs['mensagem'] = preg_replace('/after \d+ milliseconds/', 'after N milliseconds', $obs['mensagem']);
        if ($e instanceof ConnectException) { $obs['mensagem'] = preg_replace('/\(see https:[^)]*\)/', '(see curl)', preg_replace('/ for http:\/\/[^ ]+/', ' for URL', $obs['mensagem'])); }
    }
    $depois = file_exists($log) ? count(file($log)) : 0;
    echo "== $id | $rot\n";
    echo '   recebido: ' . json_encode($depois > $antes ? ultimo($log, $porta) : '(nenhum pedido)', JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
    echo '   cliente : ' . json_encode($obs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
}

$c = new Client();
$cv = new Client(array('verify' => false));
$cb = new Client(array('base_uri' => $base . '/'));
// 1) formas de chamada do codigo do PR
caso('H01', 'request GET + headers (ConsultaSituacaoContribuinteService: timeout dentro de headers)', function () use ($c, $base) {
    return $c->request('GET', "$base/ok?x=1&y=a b", array('headers' => array('autenticacao' => 'tok', 'Accept' => 'application/xml', 'timeout' => 20)));
}, $log, $porta);
caso('H02', 'get com verify=false (CertificadoPfxService)', function () use ($cv, $base) { return $cv->get("$base/ok"); }, $log, $porta);
caso('H03', 'post form_params + headers (EAuth/PNCP/Redesim)', function () use ($c, $base) {
    return $c->post("$base/criado", array('headers' => array('Accept' => 'application/json'), 'form_params' => array('grant_type' => 'client_credentials', 'client_id' => 'a b', 'nome' => 'AÇÃO', 'lista' => array(1, 2))));
}, $log, $porta);
caso('H04', 'post json', function () use ($c, $base) {
    return $c->post("$base/criado", array('json' => array('cnpj' => '12.345.678/0001-90', 'itens' => array(array('n' => 1)), 'texto' => "a\xc3\xa7\xc3\xa3o")));
}, $log, $porta);
caso('H05', 'post multipart (Storage\\Curl\\Post)', function () use ($c, $base) {
    return $c->post("$base/criado", array('headers' => array('Authorization' => 'Bearer t', 'Accept' => 'application/json'), 'multipart' => array(
        array('name' => 'file', 'contents' => "conteudo\ndo arquivo", 'filename' => 'a.txt'), array('name' => 'visibility', 'contents' => 'public'))));
}, $log, $porta);
caso('H06', 'auth basico', function () use ($c, $base) { return $c->request('GET', "$base/ok", array('auth' => array('usuario', 'senha'))); }, $log, $porta);
caso('H07', 'base_uri + URI relativa', function () use ($cb) { return $cb->request('GET', 'ok?z=2'); }, $log, $porta);
caso('H08', 'put', function () use ($c, $base) { return $c->put("$base/ok", array('headers' => array('Content-Type' => 'application/json'), 'body' => '{"a":1}')); }, $log, $porta);
caso('H09', 'delete', function () use ($c, $base) { return $c->delete("$base/ok"); }, $log, $porta);
caso('H10', 'requestAsync POST ->wait() (PNCPClient)', function () use ($cb) { return $cb->requestAsync('POST', 'criado', array('headers' => array('Authorization' => 'tk'), 'json' => array('a' => 1)))->wait(); }, $log, $porta);
caso('H11', 'requestAsync DELETE ->wait()', function () use ($cb) { return $cb->requestAsync('DELETE', 'ok')->wait(); }, $log, $porta);
caso('H12', 'requestAsync PUT ->wait()', function () use ($cb) { return $cb->requestAsync('PUT', 'ok', array('body' => 'x=1'))->wait(); }, $log, $porta);
// 2) respostas e erros
foreach (array('e400' => 'ClientException 400 com corpo JSON', 'e401' => '401', 'e404' => '404 com corpo longo (300 bytes)', 'e500' => 'ServerException 500', 'e503' => '503 vazio') as $p => $rot) {
    caso("H13$p", "erro: $rot", function () use ($c, $base, $p) { return $c->request('GET', "$base/$p"); }, $log, $porta);
}
caso('H14', 'http_errors=false em 500 (sem excecao)', function () use ($c, $base) { return $c->request('GET', "$base/e500", array('http_errors' => false)); }, $log, $porta);
caso('H15', 'requestAsync 404 ->wait(): excecao', function () use ($cb) { return $cb->requestAsync('GET', 'e404')->wait(); }, $log, $porta);
caso('H16', 'redirecionamento 302 (padrao: segue)', function () use ($c, $base) { return $c->request('GET', "$base/redireciona"); }, $log, $porta);
caso('H17', 'resposta gzip (decode_content padrao)', function () use ($c, $base) { return $c->get("$base/gz"); }, $log, $porta);
caso('H18', 'resposta 204 vazia', function () use ($c, $base) { return $c->get("$base/vazio"); }, $log, $porta);
caso('H19', 'XML (SimpleXMLElement no codigo)', function () use ($c, $base) { return $c->get("$base/xml"); }, $log, $porta);
caso('H20', 'timeout de 1 s numa resposta de 1,5 s (opcao timeout)', function () use ($c, $base) { return $c->get("$base/lento", array('timeout' => 1)); }, $log, $porta);
caso('H21', 'porta fechada: ConnectException', function () use ($c) { return $c->get('http://127.0.0.1:9/ok', array('connect_timeout' => 2)); }, $log, $porta);
caso('H22', 'host que nao resolve: ConnectException', function () use ($c) { return $c->get('http://servidor.invalido/ok', array('connect_timeout' => 2)); }, $log, $porta);
// 3) objetos PSR-7 usados no AuthService
$req = new GuzzleHttp\Psr7\ServerRequest('POST', '/v4/login', array('Content-Type' => 'application/json'), '{"a":1}');
echo "== H23 | ServerRequest/Response PSR-7 (AuthService)\n   cliente : " . json_encode(array(
    'metodo' => $req->getMethod(), 'uri' => (string) $req->getUri(), 'ct' => $req->getHeaderLine('Content-Type'), 'corpo' => (string) $req->getBody(),
    'resp' => (string) (new GuzzleHttp\Psr7\Response(201, array('X-A' => 'b'), 'ok'))->getBody(), 'status' => (new GuzzleHttp\Psr7\Response(201))->getStatusCode(),
), JSON_UNESCAPED_SLASHES) . "\n";
proc_terminate($proc);
echo '# php ' . PHP_VERSION . ', curl ' . curl_version()['version'] . ', default_charset ' . ini_get('default_charset') . "\n";
echo '# guzzle ' . Composer\InstalledVersions::getPrettyVersion('guzzlehttp/guzzle') . ', psr7 ' . Composer\InstalledVersions::getPrettyVersion('guzzlehttp/psr7') . ', promises ' . Composer\InstalledVersions::getPrettyVersion('guzzlehttp/promises') . "\n";
