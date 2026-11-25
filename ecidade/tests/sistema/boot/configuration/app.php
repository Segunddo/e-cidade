<?php

$config = require __DIR__ . '/../../../../configuration/app.php';
$config['env'] = 'production';
$config['debug'] = false;
$config['key'] = 'base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=';
$config['providers'] = array_merge(
    Illuminate\Support\ServiceProvider::defaultProviders()->toArray(),
    [
        App\Providers\AppServiceProvider::class,
        App\Providers\BroadcastServiceProvider::class,
        App\Providers\QueueServiceProvider::class,
        App\Providers\EventServiceProvider::class,
        App\Providers\RouteServiceProvider::class,
        App\Providers\CustomValidationProvider::class,
        App\Domain\Patrimonial\Providers\PatrimonialServiceProvider::class,
    ]
);

return $config;
