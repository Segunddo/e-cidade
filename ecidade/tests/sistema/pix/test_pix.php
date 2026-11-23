<?php

declare(strict_types=1);

require dirname(__DIR__, 4) . '/runtime-85/pix-vendor/autoload.php';

use App\Domain\Patrimonial\Protocolo\Model\Cgm;
use App\Domain\Tributario\Arrecadacao\Pix\Bancos\BancoDoBrasil;
use GuzzleHttp\Client;
use GuzzleHttp\Handler\MockHandler;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use GuzzleHttp\Psr7\Response;
use Illuminate\Foundation\Application;
use Swagger\Client\Api\Oauth2Api;
use Swagger\Client\Api\QrCodesApi;
use Swagger\Client\Configuration;
use Swagger\Client\Model\InlineResponse201;

function assertSameValue($expected, $actual, string $message): void
{
    if ($expected !== $actual) {
        throw new RuntimeException(
            "{$message}: expected " . var_export($expected, true) .
            ", got " . var_export($actual, true)
        );
    }
}

function makeClient(array $responses, array &$history): Client
{
    $stack = HandlerStack::create(new MockHandler($responses));
    $stack->push(Middleware::history($history));

    return new Client(['handler' => $stack]);
}

assertSameValue('13.43.0', Application::VERSION, 'Laravel version');

$oauthHistory = [];
$oauthConfig = Configuration::getDefaultConfiguration();
$oauthConfig->setUsername('test-client');
$oauthConfig->setPassword('test-secret');
$oauthConfig->setUrlAutenticacaoOauth2('https://oauth.sandbox.bb.com.br/oauth/token');
$oauth = new Oauth2Api(
    makeClient([new Response(200, [], '{"access_token":"fake-access-token"}')], $oauthHistory),
    $oauthConfig
);

$accessToken = $oauth->gerarAccessToken();
assertSameValue('fake-access-token', $accessToken, 'OAuth access token');
assertSameValue(1, count($oauthHistory), 'OAuth request count');
assertSameValue('POST', $oauthHistory[0]['request']->getMethod(), 'OAuth HTTP method');
assertSameValue(
    'https://oauth.sandbox.bb.com.br/oauth/token',
    (string) $oauthHistory[0]['request']->getUri(),
    'OAuth URL'
);
assertSameValue(
    'Basic ' . base64_encode('test-client:test-secret'),
    $oauthHistory[0]['request']->getHeaderLine('Authorization'),
    'OAuth Basic authentication'
);
parse_str((string) $oauthHistory[0]['request']->getBody(), $oauthForm);
assertSameValue('client_credentials', $oauthForm['grant_type'], 'OAuth grant type');

$bank = (new ReflectionClass(BancoDoBrasil::class))->newInstanceWithoutConstructor();
$cgm = new Cgm();
$cgm->setAttribute('z01_cgccpf', '12345678901');
$cgm->setAttribute('z01_email', 'teste@example.invalid');
$cgm->setAttribute('z01_nome', mb_convert_encoding('João Teste', 'ISO-8859-1', 'UTF-8'));
$bank->setCgm($cgm);
$bank->setCodigoBarras('001234567890');
$bank->setValor('12.34');
$bank->setVencimento(date('Y-m-d', strtotime('+1 day')));

foreach ([
    'covenantCode' => 12345,
    'pixKey' => 'test-pix-key',
    'countyCnpj' => false,
] as $property => $value) {
    $reflection = new ReflectionProperty(App\Domain\Tributario\Arrecadacao\Pix\PixInfo::class, $property);
    $reflection->setValue($bank, $value);
}

$prepareBody = new ReflectionMethod(BancoDoBrasil::class, 'preparaCorpo');
$body = $prepareBody->invoke($bank);
assertSameValue('João Teste', $body['nome_devedor'], 'Production PIX debtor encoding');
assertSameValue('Arrecadacao Pix', $body['descricao_solicitacao_pagamento'], 'Production PIX description');
assertSameValue(12345, $body['numero_convenio'], 'Production PIX covenant');

$qrHistory = [];
$qrConfig = Configuration::getDefaultConfiguration();
$qrConfig->setHost('https://api.hm.bb.com.br/pix-bb/v1');
$qrConfig->setAmbienteBB('T');
$qrConfig->setAccessToken($accessToken);
$qr = new QrCodesApi(
    makeClient([
        new Response(201, [], json_encode([
            'timestampCriacaoSolicitacao' => '2026-11-21T12:00:00Z',
            'estadoSolicitacao' => 'ATIVA',
            'codigoConciliacaoSolicitante' => 'test-txid',
            'numeroVersaoSolicitacaoPagamento' => 1,
            'linkQrCode' => 'https://pix.example/qr/test',
            'qrCode' => '000201-test',
        ], JSON_THROW_ON_ERROR)),
    ], $qrHistory),
    $qrConfig
);

$response = $qr->criaBoletoBancarioId($body, $accessToken, 'test-app-key');
if (!$response instanceof InlineResponse201) {
    throw new RuntimeException('QR request did not return InlineResponse201.');
}

assertSameValue('test-txid', $response->getCodigoConciliacaoSolicitante(), 'QR response reconciliation code');
assertSameValue('000201-test', $response->getQrCode(), 'QR response payload');
assertSameValue(1, count($qrHistory), 'QR request count');
assertSameValue('POST', $qrHistory[0]['request']->getMethod(), 'QR HTTP method');
assertSameValue(
    'https://api.hm.bb.com.br/pix-bb/v1/arrecadacao-qrcodes?gw-dev-app-key=test-app-key',
    (string) $qrHistory[0]['request']->getUri(),
    'QR URL'
);
assertSameValue('Bearer fake-access-token', $qrHistory[0]['request']->getHeaderLine('Authorization'), 'QR bearer token');
$requestBody = json_decode((string) $qrHistory[0]['request']->getBody(), true, 512, JSON_THROW_ON_ERROR);
assertSameValue(12345, $requestBody['numeroConvenio'], 'QR request covenant');
assertSameValue('S', $requestBody['indicadorCodigoBarras'], 'QR request barcode indicator');
assertSameValue(12.34, $requestBody['valorOriginalSolicitacao'], 'QR request amount');
assertSameValue('João Teste', $requestBody['nomeDevedor'], 'QR request debtor encoding');
assertSameValue('Arrecadacao Pix', $requestBody['descricaoSolicitacaoPagamento'], 'QR request description');

echo "OK: PHP 8.5 + Laravel 13; OAuth e emissao PIX BB simulados; payload de producao e encoding conferidos.\n";
