<?php
// PHP8-38: middlewares do app/Http (sem banco): pipeline do kernel com requisicoes em memoria.
// Uso: bash scratchpad/roda_middlewares.sh   (roda este arquivo no 7.4 e no 8.5 e compara; ver docs/migracao-laravel/middlewares-sessao.md)
$raiz = $argv[1]; $vendor = $argv[2];
$avisos = array();
set_error_handler(function ($no, $msg, $arq, $lin) use (&$avisos) {
    $avisos[] = $msg . ' @ ' . basename($arq) . ':' . $lin; return true;
});
error_reporting(E_ALL);
foreach (array('logs', 'framework/cache/data', 'framework/sessions', 'framework/views') as $d) { if (!is_dir('/tmp/storage/' . $d)) { mkdir('/tmp/storage/' . $d, 0777, true); } }   // storage em /tmp (tmpfs do roda-isolado.sh)
ob_start();
ini_set('session.save_path', '/tmp/storage/framework/sessions');
define('LARAVEL_START', microtime(true));
require $vendor . '/autoload.php';
spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'App\\') === 0) { $f = $raiz . '/app/' . str_replace('\\', '/', substr($c, 4)) . '.php'; if (is_file($f)) { require $f; } }
});
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Pipeline\Pipeline;

$app = require $raiz . '/bootstrap/app.php';
$app->useStoragePath('/tmp/storage');
$app->instance('request', Request::create('/'));
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$pular = isset($argv[3]) && $argv[3] !== '' ? explode(',', $argv[3]) : array();   // providers do app a nao carregar (so para medir os middlewares quando o app ainda nao sobe no Laravel 13)
if (!$pular) {
    $kernel->bootstrap();
} else {
    $rm = new ReflectionObject($kernel);
    if ($rm->hasMethod('bootstrappers')) { $m = $rm->getMethod('bootstrappers'); if (PHP_VERSION_ID < 80100) { $m->setAccessible(true); } $boots = $m->invoke($kernel); }
    else { $pp = new ReflectionProperty('Illuminate\\Foundation\\Http\\Kernel', 'bootstrappers'); if (PHP_VERSION_ID < 80100) { $pp->setAccessible(true); } $boots = $pp->getValue($kernel); }
    $app->bootstrapWith(array_slice($boots, 0, 2));   // LoadEnvironmentVariables, LoadConfiguration
    config(array('app.providers' => array_values(array_diff(config('app.providers'), $pular))));
    $app->bootstrapWith(array_slice($boots, 2));
    echo 'PROVIDERS NAO CARREGADOS: ' . implode(',', $pular) . "\n";
}
date_default_timezone_set(config('app.timezone'));

$e = function ($s) { return str_replace(array("\r", "\n"), array('\\r', '\\n'), $s); };
$dump = function ($r) use ($e) {
    $o = array('status=' . $r->getStatusCode());
    $h = $r->headers->allPreserveCase();
    ksort($h);
    foreach ($h as $k => $v) {
        $lk = strtolower($k);
        if ($lk === 'date' || $lk === 'set-cookie') { continue; }
        $o[] = "h:$k=" . $e(implode('|', $v));
    }
    foreach ($r->headers->getCookies() as $c) {
        $v = $c->getValue();
        $o[] = 'cookie:' . $c->getName() . ' valor=' . (strlen((string) $v) > 20 ? '<' . strlen($v) . ' bytes>' : $v)
            . ' path=' . $c->getPath() . ' dominio=' . var_export($c->getDomain(), true) . ' secure=' . var_export($c->isSecure(), true)
            . ' httponly=' . var_export($c->isHttpOnly(), true) . ' samesite=' . var_export($c->getSameSite(), true)
            . ' minutos=' . ($c->getExpiresTime() ? (int) round(($c->getExpiresTime() - time()) / 60) : 0);
    }
    $o[] = 'corpo=' . $e(substr((string) $r->getContent(), 0, 300));
    return implode("\n    ", $o);
};
$caso = function ($nome, array $mws, Request $req, $final = null) use ($app, $dump, $e) {
    echo "CASO $nome\n";
    $final = $final ?: function ($r) { return new Response('ok:' . json_encode($r->all()), 200); };
    try {
        $r = (new Pipeline($app))->send($req)->through($mws)->then($final);
        echo '    ' . $dump($r) . "\n";
    } catch (Throwable $x) {
        echo '    EXC ' . get_class($x) . ' code=' . $x->getCode() . ' status=' . (method_exists($x, 'getStatusCode') ? $x->getStatusCode() : '-') . ' msg=' . $e($x->getMessage()) . "\n";
    }
};
$setenv = function (array $v) { foreach ($v as $k => $val) { if ($val === null) { putenv($k); unset($_ENV[$k], $_SERVER[$k]); } else { putenv("$k=$val"); $_ENV[$k] = $_SERVER[$k] = $val; } } };
$req = function ($uri = '/x', $m = 'GET', $p = array(), $cookies = array(), $server = array(), $content = null) {
    $r = Request::create($uri, $m, $p, $cookies, array(), $server, $content);
    $route = new Illuminate\Routing\Route(array('GET', 'POST'), '/x', function () { return 'ok'; });
    $route->bind($r);
    $r->setRouteResolver(function () use ($route) { return $route; });
    return $r;
};
$A = 'App\\Http\\Middleware\\';
$hexa = function ($r) { $f = function ($v) use (&$f) { return is_array($v) ? array_map($f, $v) : (is_string($v) ? 'hex:' . bin2hex($v) : $v); }; return new Response(json_encode($f($r->all())), 200); };

// inventario do kernel
$k = new ReflectionClass('App\\Http\\Kernel');
$kobj = $app->make('App\\Http\\Kernel');
foreach (array('middleware', 'middlewareGroups', 'routeMiddleware') as $p) {
    $rp = new ReflectionProperty('Illuminate\\Foundation\\Http\\Kernel', $p); $rp->setAccessible(true);
    echo "KERNEL $p: " . json_encode($rp->getValue($kobj), JSON_UNESCAPED_SLASHES) . "\n";
}
echo 'CONFIG session: ' . json_encode(array_intersect_key(config('session'), array_flip(array('driver', 'lifetime', 'expire_on_close', 'encrypt', 'cookie', 'path', 'domain', 'secure', 'http_only', 'same_site', 'lottery')))) . "\n";
echo 'CONFIG cache.default=' . config('cache.default') . ' auth.defaults=' . json_encode(config('auth.defaults')) . "\n";

// 1) TrimStrings + ConvertEmptyStringsToNull (global)
$g = array($A . 'TrimStrings', Illuminate\Foundation\Http\Middleware\ConvertEmptyStringsToNull::class);
$caso('trim+vazio-para-null GET', $g, $req('/x?a=%20%20oi%20&b=&c[]=%20z%20&password=%20s%20&password_confirmation=%20s%20'));
$caso('trim+vazio-para-null POST json', $g, $req('/x', 'POST', array(), array(), array('CONTENT_TYPE' => 'application/json'), json_encode(array('a' => ' x ', 'b' => '', 'n' => 5, 'l' => array(' y ', '')))));
// 2) Cors
foreach (array(array(null, null), array('http://a.com', null), array('http://a.com', '*'), array('http://a.com', 'http://a.com,http://b.com'), array('http://c.com', 'http://a.com,http://b.com')) as $c) {
    $setenv(array('ALLOWED_ORIGINS' => $c[1]));
    unset($_SERVER['HTTP_ORIGIN']); if ($c[0] !== null) { $_SERVER['HTTP_ORIGIN'] = $c[0]; }
    $caso('cors origin=' . var_export($c[0], true) . ' ALLOWED=' . var_export($c[1], true), array($A . 'CorsMiddleware'), $req('/x'));
}
unset($_SERVER['HTTP_ORIGIN']); $setenv(array('ALLOWED_ORIGINS' => null));
// 3) DBRequest (utf8_decode)
$u = "a\xc3\xa7\xc3\xa3o";
$caso('dbrequest utf8', array($A . 'DBRequestMiddleware'), $req('/x?_path=a&t=' . urlencode($u) . '&n=12&arr[0]=' . urlencode($u) . '&arr[k][]=' . urlencode($u)), $hexa);
$caso('dbrequest null+bool', array($A . 'DBRequestMiddleware'), $req('/x', 'POST', array(), array(), array('CONTENT_TYPE' => 'application/json'), json_encode(array('a' => null, 'b' => true, 'c' => 1.5, 'd' => '', 'e' => array(null)))), $hexa);
// 4) AuthRedesim
foreach (array(array(null, null), array('k1', null), array('k1', 'k1'), array('k1', 'k2')) as $c) {
    $setenv(array('REDESIM_ACCESS_KEY_ID' => $c[1]));
    $caso('redesim header=' . var_export($c[0], true) . ' env=' . var_export($c[1], true), array($A . 'AuthRedesimMiddleware'), $req('/x', 'GET', array(), array(), $c[0] === null ? array() : array('HTTP_ACCESSKEYID' => $c[0])));
}
$setenv(array('REDESIM_ACCESS_KEY_ID' => null));
// 5) AuthSim
$setenv(array('SSP_USER' => 'u', 'SSP_PASS' => 'p', 'SSP_WHITE_LIST' => '10.0.0.1,10.0.0.2'));
$tok = function ($user, $hash) { return 'Basic ' . base64_encode("$user:$hash") . '='; };
$ok = hash('sha256', 'p' . date('Y-m-d'));
foreach (array(
    array('10.0.0.1', $tok('u', $ok)), array('10.0.0.9', $tok('u', $ok)), array('10.0.0.1', null),
    array('10.0.0.1', $tok('x', $ok)), array('10.0.0.1', $tok('u', 'errado')), array('10.0.0.1', 'Basic ' . base64_encode('semdoispontos') . '='),
) as $c) {
    $s = array('REMOTE_ADDR' => $c[0]); if ($c[1] !== null) { $s['HTTP_AUTHORIZATION'] = $c[1]; }
    $caso('authsim ip=' . $c[0] . ' auth=' . ($c[1] === null ? 'nenhum' : substr(md5($c[1]), 0, 6)), array($A . 'AuthSimMiddleware'), $req('/x', 'GET', array(), array(), $s));
}
$setenv(array('SSP_USER' => null, 'SSP_PASS' => null, 'SSP_WHITE_LIST' => null));
$caso('authsim sem env', array($A . 'AuthSimMiddleware'), $req('/x', 'GET', array(), array(), array('REMOTE_ADDR' => '10.0.0.1', 'HTTP_AUTHORIZATION' => 'x')));
// 6) grupo web sem StartWebSession/Database (esses tocam banco)
$web = array($A . 'EncryptCookies', Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse::class, Illuminate\Session\Middleware\StartSession::class,
    Illuminate\View\Middleware\ShareErrorsFromSession::class, $A . 'VerifyCsrfToken', Illuminate\Routing\Middleware\SubstituteBindings::class);
$caso('web GET', $web, $req('/x'));
$caso('web POST sem token', $web, $req('/x', 'POST', array('a' => 1)));
$caso('web POST token invalido', $web, $req('/x', 'POST', array('a' => 1, '_token' => 'x')));
$caso('web GET cookie lixo', $web, $req('/x', 'GET', array(), array('laravel_session' => 'lixo', 'outro' => 'valor')));
// 7) grupo api: throttle + bindings (cache file)
$caso('api throttle 1', array(Illuminate\Routing\Middleware\ThrottleRequests::class . ':2000,1', Illuminate\Routing\Middleware\SubstituteBindings::class), $req('/x', 'GET', array(), array(), array('REMOTE_ADDR' => '9.9.9.9')));
$caso('api throttle 2', array(Illuminate\Routing\Middleware\ThrottleRequests::class . ':2000,1'), $req('/x', 'GET', array(), array(), array('REMOTE_ADDR' => '9.9.9.9')));
$caso('api throttle limite 1,1 (2a)', array(Illuminate\Routing\Middleware\ThrottleRequests::class . ':1,1'), $req('/x', 'GET', array(), array(), array('REMOTE_ADDR' => '9.9.9.8')));
$caso('api throttle limite 1,1 (2a)', array(Illuminate\Routing\Middleware\ThrottleRequests::class . ':1,1'), $req('/x', 'GET', array(), array(), array('REMOTE_ADDR' => '9.9.9.8')));
// 8) RedirectIfAuthenticated, WindowSession (sem cabecalho)
$caso('guest sem usuario', array($A . 'RedirectIfAuthenticated'), $req('/x'));
$caso('window sem cabecalho', array($A . 'WindowSessionMiddleware'), $req('/x'));

// 9) sessao nativa do PHP pelo WindowSessionMiddleware (arquivo, sem banco)
spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'ECidade\\') === 0) { $f = $raiz . '/src/' . str_replace('\\', '/', substr($c, 8)) . '.php'; if (is_file($f)) { require $f; } }
});
define('ECIDADE_REQUEST_ROOT', '/');
$caso('window com cabecalho X-Window-Session (sem sessao iniciada)', array($A . 'WindowSessionMiddleware'), $req('/x', 'GET', array(), array(), array('HTTP_X_WINDOW_SESSION' => 'w1')));
session_start();
$caso('window com cabecalho X-Window-Session (sessao iniciada)', array($A . 'WindowSessionMiddleware'), $req('/x', 'GET', array(), array(), array('HTTP_X_WINDOW_SESSION' => 'w1')), function ($r) {
    $p = session_get_cookie_params();
    ksort($p);
    return new Response('nome=' . session_name() . ' status=' . session_status() . ' idlen=' . strlen(session_id()) . ' cookie_params=' . json_encode($p)
        . ' chaves=' . json_encode(array_keys($_SESSION ?? array())), 200);
});
// log
$log = glob('/tmp/storage/logs/*.log');
foreach ($log as $f) { foreach (file($f) as $l) { if (preg_match('/^\[[0-9-]+ [0-9:]+\] (.*)$/', $l, $m)) { echo 'LOG ' . $m[1] . "\n"; } } }
file_put_contents('php://stderr', 'AVISOS ' . count($avisos) . "\n" . implode("\n", array_unique($avisos)) . "\n");

ob_end_flush();
