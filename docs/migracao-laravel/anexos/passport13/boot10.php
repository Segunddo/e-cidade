<?php
// Boot do Laravel 8 / Passport 10.4.2 (o do PR) no 7.4 com o AuthServiceProvider original ou o proposto. php boot10.php <original|proposto>
error_reporting(E_ALL & ~E_DEPRECATED);
require '/w/vendor/autoload.php';
$modo = $argv[1] ?? 'original';
spl_autoload_register(function ($c) use ($modo) {
    if (strpos($c, 'App\\') === 0) {
        $rel = str_replace('\\', '/', substr($c, 4)) . '.php';
        foreach (($modo === 'proposto' ? ['/s85/', '/pr/app/'] : ['/pr/app/']) as $d) { if (is_file($d . $rel)) { require $d . $rel; return; } }
    }
});
$app = Orchestra\Testbench\Foundation\Application::create(null, null, ['load_environment_variables' => false]);
$app['config']->set('auth.guards.api', ['driver' => 'passport', 'provider' => 'users']);
$app['config']->set('auth.providers.users', ['driver' => 'eloquent', 'model' => App\Domain\Configuracao\Usuario\Models\Usuario::class]);
try {
    $app->register(App\Providers\AuthServiceProvider::class);
    $app->register(Laravel\Passport\PassportServiceProvider::class);
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
    echo "PHP ", PHP_VERSION, " BOOT OK\n";
    $rs = [];
    foreach ($app['router']->getRoutes() as $r) { if (strpos($r->uri(), 'oauth') !== false) { $rs[] = implode('|', $r->methods()) . ' ' . $r->uri(); } }
    sort($rs); echo implode("\n", $rs), "\n";
    echo "clientCredential: ", $app['router']->getMiddleware()['clientCredential'] ?? '(sem alias)', "\n";
} catch (Throwable $e) {
    echo "FALHA: ", get_class($e), ': ', $e->getMessage(), "\n";
}
