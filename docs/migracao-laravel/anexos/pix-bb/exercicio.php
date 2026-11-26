<?php
// Exercita o SDK Pix do BB como o BancoDoBrasil.php (gerarPix e preparaConfiguracao). Contra o duble.php, sem rede.
// Uso: php exercicio.php <autoload.php> <sdk-lib-ou-"-"> <porta-do-duble>
// Saida: uma linha por etapa (o que o SDK devolveu ou o erro), igual nos dois runtimes se o comportamento for igual.
// PIX_ER: mascara de error_reporting (inteiro) para reproduzir a do sistema; sem ela, tudo menos deprecated.
error_reporting(getenv('PIX_ER') !== false ? (int) getenv('PIX_ER') : (E_ALL & ~E_DEPRECATED & ~E_USER_DEPRECATED)); ini_set('display_errors', '1');
// PIX_LARAVEL=1: reproduz o HandleExceptions do Laravel (error_reporting(-1) e erro vira ErrorException, exceto deprecated).
if (getenv('PIX_LARAVEL')) {
    error_reporting(-1);
    set_error_handler(function ($nivel, $msg, $arq, $lin) {
        if ($nivel & (E_DEPRECATED | E_USER_DEPRECATED)) { return true; }
        throw new ErrorException($msg, 0, $nivel, $arq, $lin);
    });
}
require $argv[1];
if ($argv[2] !== '-') {
    spl_autoload_register(function ($c) use ($argv) {
        if (strpos($c, 'Swagger\\Client\\') === 0) { $f = $argv[2] . '/' . str_replace('\\', '/', substr($c, 15)) . '.php'; if (is_file($f)) { require $f; } }
    });
}
$porta = $argv[3];
use GuzzleHttp\Client;
use Swagger\Client\Api\Oauth2Api;
use Swagger\Client\Api\QrCodesApi;
use Swagger\Client\Configuration;
use Swagger\Client\Model\ArrecadacaoqrcodesBody;

function cfg($porta, $modo)
{
    $config = Configuration::getDefaultConfiguration();
    $config->setAmbienteBB('T');
    $config->setHost("http://127.0.0.1:$porta/pix");
    $config->setUrlAutenticacaoOauth2("http://127.0.0.1:$porta/oauth/token");
    $config->setChaveAplicacaoBB('chave-de-teste');
    $config->setUsername('usuario-de-teste');
    $config->setPassword('senha-de-teste');
    file_put_contents('/tmp/duble.modo', $modo);
    return $config;
}
function corpo()
{
    $b = new ArrecadacaoqrcodesBody();
    $b['numero_convenio'] = 1234567;
    $b['codigo_guia_recebimento'] = '83640000000012345678';
    $b['email_devedor'] = 'devedor@example.com';
    $b['codigo_solicitacao_banco_central_brasil'] = 'chave-pix-de-teste';
    $b['valor_original_solicitacao'] = '10.50';
    $b['nome_devedor'] = 'Devedor de Teste';
    $b['quantidade_segundo_expiracao'] = 3600;
    return $b;
}
function tenta($rotulo, $f)
{
    try {
        $r = $f();
        echo $rotulo, ' => ', is_object($r) ? get_class($r) . ' ' . json_encode(\Swagger\Client\ObjectSerializer::sanitizeForSerialization($r)) : var_export($r, true), "\n";
    } catch (\Exception $e) {
        echo $rotulo, ' => EXCECAO ', get_class($e), ': ', substr($e->getMessage(), 0, 160), "\n";
    } catch (\Throwable $e) {
        echo $rotulo, ' => EXCECAO ', get_class($e), ': ', substr($e->getMessage(), 0, 160), "\n";
    }
}
foreach (array('sucesso', 'erro400', 'erro500', 'invalido') as $modo) {
    $config = cfg($porta, $modo);
    tenta("[$modo] gerarAccessToken", function () use ($config) { return (new Oauth2Api(new Client(['verify' => false]), $config))->gerarAccessToken(); });
    $config->setAccessToken('tok-do-duble');
    tenta("[$modo] criaBoletoBancarioId", function () use ($config) {
        return (new QrCodesApi(new Client(['verify' => false]), $config))->criaBoletoBancarioId(corpo(), $config->getAccessToken(), $config->getChaveAplicacaoBB());
    });
}
