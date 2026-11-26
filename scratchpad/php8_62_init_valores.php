<?php
// PHP8-62: valores de configuracao que o Laravel 13 passa a mesclar dos padroes dele e que mudam comportamento
ini_set('display_errors', 'stderr'); error_reporting(E_ALL & ~E_DEPRECATED);
chdir('/app'); require 'bootstrap.php'; $app = require 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
foreach (array('session.same_site', 'session.partitioned', 'session.secure', 'session.http_only', 'hashing.rehash_on_login', 'auth.password_timeout',
    'passport.path', 'passport.guard', 'passport.middleware', 'passport.connection', 'app.previous_keys', 'cache.prefix', 'session.cookie',
    'database.connections.pgsql.search_path', 'database.connections.pgsql.sslmode', 'logging.deprecations', 'app.maintenance.driver') as $c) {
    echo $c, ' = ', json_encode(config($c)), "\n";
}
$r = $app['router']->getRoutes()->getByName('passport.token');
echo 'rota passport.token = ', $r ? $r->uri() : '-', "\n";
