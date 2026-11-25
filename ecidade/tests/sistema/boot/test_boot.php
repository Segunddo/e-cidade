<?php

require __DIR__ . '/../../../../runtime-85/boot-vendor/autoload.php';

$ecidadePath = realpath(__DIR__ . '/../../..');
$cachePath = getenv('BOOT_TEST_CACHE');
$configCachePath = __DIR__ . '/configuration/config-cache.php';

if ($ecidadePath === false || $cachePath === false || $cachePath === '') {
    throw new RuntimeException('Caminhos do teste de boot nao foram configurados.');
}

if (!mkdir($cachePath . '/bootstrap/cache', 0777, true) && !is_dir($cachePath . '/bootstrap/cache')) {
    throw new RuntimeException('Nao foi possivel criar o cache temporario do teste.');
}

if (!mkdir($cachePath . '/storage', 0777, true) && !is_dir($cachePath . '/storage')) {
    throw new RuntimeException('Nao foi possivel criar o storage temporario do teste.');
}

putenv('APP_CONFIG_CACHE=' . $configCachePath);

$app = require $ecidadePath . '/bootstrap/app.php';
$app->useBootstrapPath($cachePath . '/bootstrap');
$app->useStoragePath($cachePath . '/storage');

if ($app->configPath() !== $ecidadePath . '/configuration') {
    throw new RuntimeException('O caminho customizado de configuracao do e-cidade foi alterado.');
}

$app->instance('request', Illuminate\Http\Request::create('/'));

$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);

if (!$kernel instanceof App\Http\Kernel) {
    throw new RuntimeException('O bootstrap nao vinculou o kernel HTTP da aplicacao.');
}

try {
    $kernel->bootstrap();
} catch (Throwable $exception) {
    fwrite(STDERR, $exception . PHP_EOL);
    exit(1);
}

$routeCount = count($app['router']->getRoutes());

if ($routeCount === 0) {
    throw new RuntimeException('O boot nao registrou rotas da aplicacao.');
}

echo sprintf(
    "OK: PHP %s + Laravel %s; bootstrap existente, providers selecionados e %d rotas carregados.\n",
    PHP_VERSION,
    Illuminate\Foundation\Application::VERSION,
    $routeCount
);
