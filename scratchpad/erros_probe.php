<?php
// Mede, sem banco e sem rede, a configuracao EFETIVA de erros e o que um Notice/Warning/Deprecated faz (resposta e log).
// Uso (via Apache/mod_php ou CLI):  erros_probe.php?camada=a|b|c   (CLI: php erros_probe.php <camada>)
//   a = so o php.ini da imagem (mais o que o proprio script faz)
//   b = depois de ECIDADE_PATH/bootstrap.php (o que a tela legada carrega: config/application.default.php + libs)
//   c = depois do bootstrap do kernel HTTP do Laravel do PR (HandleExceptions)
// Saida: JSON (configuracao efetiva + o que cada disparo fez) entre as marcas ###JSON e ###FIM; o corpo fora delas e o que o PHP
// escreveu na resposta (display_errors).
$camada = isset($_GET['camada']) ? $_GET['camada'] : (isset($argv[1]) ? $argv[1] : 'a');
$exibir = isset($_GET['exibir']) ? $_GET['exibir'] : (isset($argv[2]) ? $argv[2] : '');   // 'on' = liga display_errors antes dos disparos
$raiz = '/e';
$nomes = array(E_ERROR => 'E_ERROR', E_WARNING => 'E_WARNING', E_PARSE => 'E_PARSE', E_NOTICE => 'E_NOTICE', E_CORE_ERROR => 'E_CORE_ERROR',
    E_CORE_WARNING => 'E_CORE_WARNING', E_COMPILE_ERROR => 'E_COMPILE_ERROR', E_COMPILE_WARNING => 'E_COMPILE_WARNING',
    E_USER_ERROR => 'E_USER_ERROR', E_USER_WARNING => 'E_USER_WARNING', E_USER_NOTICE => 'E_USER_NOTICE', 2048 => 'E_STRICT',
    E_RECOVERABLE_ERROR => 'E_RECOVERABLE_ERROR', E_DEPRECATED => 'E_DEPRECATED', E_USER_DEPRECATED => 'E_USER_DEPRECATED');
$ordem = array();
ob_start();
echo "###CORPO_INICIO\n";
$antes_bootstrap = array();

if ($camada === 'b') {
    chdir($raiz);
    ini_set('error_log', '/var/log/php_errors.log');
    require $raiz . '/bootstrap.php';
    // o app.php registra os ouvintes do evento app.error (e o log extension/log/error.log) antes de despachar a tela
    try {
        ECidade\V3\Extension\Registry::get('app.container')->get('app.configData')->loadEvents();
    } catch (\Throwable $e) {
        echo "loadEvents falhou: " . get_class($e) . ': ' . $e->getMessage() . "\n";
    }
} elseif ($camada === 'c') {
    chdir($raiz);
    // as constantes/autoload do Laravel do PR, como public/index.php; sem tratar requisicao nem banco
    define('LARAVEL_START', microtime(true));
    require $raiz . '/vendor/autoload.php';
    $app = require $raiz . '/bootstrap/app.php';
    $app->instance('request', Illuminate\Http\Request::create('http://localhost/v4/probe', 'GET'));   // o Kernel::handle faz isto antes de bootstrap()
    $app->make(Illuminate\Contracts\Http\Kernel::class)->bootstrap();
}

// o que muitas telas fazem: ini_set('error_reporting', <texto>) (68 arquivos .php, 61 na raiz de ecidade/: git grep -lE "ini_set\(\s*['\"]error_reporting['\"]" -- 'ecidade/*.php' ':!ecidade/vendor'); ?er=<texto> reproduz
$er = isset($_GET['er']) ? $_GET['er'] : (isset($argv[3]) ? $argv[3] : null);
$er_resultado = null;
if ($er !== null) {
    $er_resultado = array('texto' => $er, 'ini_set_devolveu' => ini_set('error_reporting', $er), 'error_reporting_depois' => error_reporting());
}
if ($exibir === 'on') {
    ini_set('display_errors', '1');
}

function ini_efetivo($nomes)
{
    $er = error_reporting();
    $ativos = array();
    foreach ($nomes as $bit => $n) {
        if ($er & $bit) {
            $ativos[] = $n;
        }
    }
    $o = array('error_reporting_atual' => $er, 'error_reporting_ini' => ini_get('error_reporting'), 'niveis_ativos' => $ativos);
    foreach (array('display_errors', 'display_startup_errors', 'log_errors', 'error_log', 'html_errors', 'ignore_repeated_errors', 'track_errors', 'docref_root', 'error_prepend_string', 'error_append_string', 'xmlrpc_errors') as $k) {
        $v = ini_get($k);
        $o[$k] = $v === false ? '(inexistente)' : $v;
    }
    return $o;
}

$res = array(
    'php' => PHP_VERSION, 'sapi' => php_sapi_name(), 'camada' => $camada, 'exibir' => $exibir,
    'php_ini' => php_ini_loaded_file(), 'ini_adicionais' => php_ini_scanned_files() ? array_map('trim', explode(',', php_ini_scanned_files())) : array(),
    'ini_set_error_reporting' => $er_resultado,
    'efetivo_antes_dos_disparos' => ini_efetivo($nomes),
);

// o handler corrente (o legado e o Laravel instalam um): so a classe
$h = set_error_handler(function () { return false; });
restore_error_handler();
$res['set_error_handler_antes'] = is_array($h) ? (is_object($h[0]) ? get_class($h[0]) : $h[0]) . '::' . $h[1] : (is_object($h) ? get_class($h) : (string)$h);

$disparos = array(
    'variavel_indefinida (7.4 Notice; 8.x Warning)' => function () { echo $naoExiste; },
    'indice_indefinido (7.4 Notice; 8.x Warning)' => function () { $a = array(); echo $a['k']; },
    'arquivo_inexistente (Warning nos dois)' => function () { return file_get_contents('/inexistente/x'); },
    'E_USER_NOTICE' => function () { trigger_error('aviso de usuario', E_USER_NOTICE); },
    'E_USER_WARNING' => function () { trigger_error('alerta de usuario', E_USER_WARNING); },
    'E_USER_DEPRECATED' => function () { trigger_error('depreciado de usuario', E_USER_DEPRECATED); },
    'utf8_encode (Deprecated desde o 8.2)' => function () { return utf8_encode("a\xe9"); },
);
$res['disparos'] = array();
foreach ($disparos as $rot => $f) {
    $antes = ob_get_length();
    $erro = null;
    try {
        $f();
    } catch (\Throwable $e) {
        $erro = get_class($e) . ': ' . substr($e->getMessage(), 0, 120);
    }
    $depois = ob_get_length();
    $res['disparos'][$rot] = array('excecao' => $erro, 'bytes_na_resposta' => $depois - $antes);
}
$res['efetivo_depois_dos_disparos'] = ini_efetivo($nomes);
$corpo = ob_get_clean();
echo $corpo;
echo "\n###JSON\n", json_encode($res, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR), "\n###FIM\n";
