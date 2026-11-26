<?php

return [
    // Passport 13 (Laravel 13, so no 8.5): prefixo das rotas do Passport, que o Passport 10 recebia em
    // Passport::routes() (app/Providers/AuthServiceProvider.php). O Passport 10 do 7.4 nao le esta chave.
    'path' => 'v4/oauth',
];
