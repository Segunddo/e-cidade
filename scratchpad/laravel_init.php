<?php
// PHP8-62: kernel do Laravel (console) de pe, sem banco: versao, rotas, configuracao (so chaves e tipos), providers, env(), cache, sessao, handler.
// Uso: php laravel_init.php [raiz do ecidade, padrao /w/ecidade]  (com o vendor a medir em <raiz>/vendor; saida igual no 7.4 e no 8.5 = sem diferenca)
$raiz = isset($argv[1]) ? $argv[1] : '/w/ecidade';
chdir($raiz);
require 'bootstrap.php';
$app = require 'bootstrap/app.php';
$k = $app->make(Illuminate\Contracts\Console\Kernel::class);
$k->bootstrap();
echo 'versao ', $app->version(), "\n";
echo 'ambiente ', $app->environment(), ' tz_config=', config('app.timezone'), ' tz_php=', date_default_timezone_get(), "\n";

// rotas (route:list instancia controllers e consulta banco; aqui so a tabela de rotas)
$linhas = array();
foreach ($app['router']->getRoutes() as $r) {
    $a = $r->getAction();
    $acao = isset($a['controller']) ? $a['controller'] : ($r->getAction('uses') instanceof Closure ? 'Closure' : (string) $r->getActionName());
    $mw = isset($a['middleware']) ? (array) $a['middleware'] : array();
    sort($mw);
    $m = $r->methods(); sort($m);
    $linhas[] = implode('|', $m) . ' ' . $r->uri() . ' nome=' . ($r->getName() ?: '-') . ' acao=' . $acao . ' mw=' . implode(',', array_map(function ($x) { return is_string($x) ? $x : 'Closure'; }, $mw)) . ' dominio=' . ($r->getDomain() ?: '-');
}
sort($linhas);
echo 'ROTAS ', count($linhas), "\n";
foreach ($linhas as $l) { echo "R $l\n"; }

// comandos do artisan
$cmds = array_keys($k->all()); sort($cmds);
echo 'COMANDOS ', count($cmds), "\n";
foreach ($cmds as $c) { echo "K $c\n"; }

// configuracao efetiva: so chaves e tipos (valores so de uma lista sem segredo)
$cfg = config()->all();
$planos = array();
$walk = function ($v, $p) use (&$walk, &$planos) {
    if (is_array($v) && $v !== array()) { foreach ($v as $k2 => $x) { $walk($x, $p === '' ? (string) $k2 : $p . '.' . $k2); } }
    else { $planos[$p] = is_array($v) ? 'array(vazio)' : gettype($v); }
};
$walk($cfg, '');
ksort($planos);
echo 'CONFIG chaves=', count($planos), ' grupos=', count($cfg), "\n";
foreach ($planos as $c => $t) { echo "C $c : $t\n"; }
foreach (array('app.timezone', 'app.locale', 'app.env', 'cache.default', 'session.driver', 'session.lifetime', 'session.cookie', 'queue.default', 'filesystems.default', 'logging.default', 'database.default', 'auth.defaults.guard', 'hashing.driver') as $c) {
    echo "V $c = ", var_export(config($c), true), "\n";
}

// providers
$carregados = array_keys($app->getLoadedProviders());
sort($carregados);
echo 'PROVIDERS carregados=', count($carregados), ' adiados=', count($app->getDeferredServices()), ' em_config=', count(config('app.providers')), "\n";
foreach ($carregados as $p) { echo "P $p\n"; }
echo 'ALIASES ', count(config('app.aliases')), "\n";

// env()
foreach (array('true', 'false', 'null', '(empty)', '', 'abc', '0', '"aspas"') as $v) {
    putenv("PROBE_X=$v"); $_ENV['PROBE_X'] = $_SERVER['PROBE_X'] = $v;
    echo 'ENV PROBE_X=', var_export($v, true), ' -> ', var_export(env('PROBE_X'), true), "\n";
}
putenv('PROBE_X'); unset($_ENV['PROBE_X'], $_SERVER['PROBE_X']);
echo 'ENV ausente -> ', var_export(env('PROBE_X'), true), ' com padrao -> ', var_export(env('PROBE_X', 'p'), true), "\n";
echo 'DOTENV ', class_exists('Dotenv\Dotenv') ? get_class(Dotenv\Dotenv::createImmutable($raiz)) : 'ausente', "\n";

// cache (store file): TTL em segundos
$c = app('cache');
echo 'CACHE store=', get_class($c->store()->getStore()), "\n";
$c->put('t104_a', 'v', 60);
$arq = glob($raiz . '/storage/framework/cache/data/*/*/*');
$exp = array();
foreach ($arq as $f) { $exp[] = (int) substr(file_get_contents($f), 0, 10) - time(); }
sort($exp);
echo 'CACHE put(60) expira em ~', implode(',', $exp), " s\n";
$c->put('t104_b', 'v', new DateInterval('PT2M'));
echo 'CACHE get=', var_export($c->get('t104_a'), true), ' remember=', var_export($c->remember('t104_c', 30, function () { return 'n'; }), true), "\n";

// sessao
$sm = app('session');
echo 'SESSION driver=', $sm->getDefaultDriver(), ' store=', get_class($sm->driver()->getHandler()), ' nome=', $sm->driver()->getName(), "\n";

// handler
$h = app(Illuminate\Contracts\Debug\ExceptionHandler::class);
echo 'HANDLER ', get_class($h), "\n";
$req = Illuminate\Http\Request::create('/v4/x', 'GET');
foreach (array(
    'excecao simples' => new Exception('ok'),
    'excecao 404' => new Symfony\Component\HttpKernel\Exception\NotFoundHttpException('nada'),
    'excecao com codigo 403' => new Exception('negado', 403),
    'validacao' => Illuminate\Validation\ValidationException::withMessages(array('a' => 'x')),
) as $n => $ex) {
    try { $r = $h->render($req, $ex); echo "H $n: status=", $r->getStatusCode(), ' tipo=', get_class($r), ' corpo=', substr($r->getContent(), 0, 120), "\n"; }
    catch (Throwable $t) { echo "H $n: EXC ", get_class($t), ' ', $t->getMessage(), "\n"; }
}
