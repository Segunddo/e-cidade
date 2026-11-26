<?php
// PHP8-51: o mesmo que o ecidade/artisan, para rodar pelo roda-isolado.sh (que executa /trecho/<arquivo>): o
// __DIR__ do artisan seria /trecho, entao os caminhos vao fixos em /app. Uso: php artisan.php <comando> [args]
chdir('/app');
$_SERVER['argv'] = $argv = array_merge(['artisan'], array_slice($argv, 1));
require '/app/bootstrap.php';
$app = require_once '/app/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$status = $kernel->handle(
    $input = new Symfony\Component\Console\Input\ArgvInput,
    new Symfony\Component\Console\Output\ConsoleOutput
);
$kernel->terminate($input, $status);
exit($status);
