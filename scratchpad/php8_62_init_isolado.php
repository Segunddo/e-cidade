<?php
// PHP8-62: roda scratchpad/laravel_init.php pelo docker/composer-85/roda-isolado.sh, mostrando erros e avisos no stderr
// (o php.ini das imagens do projeto so os registra). Uso: bash docker/composer-85/roda-isolado.sh <7.4|8.5> scratchpad/php8_62_init_isolado.php
ini_set('display_errors', 'stderr');
ini_set('memory_limit', '1G');
error_reporting(E_ALL);
$argv = array($argv[0], '/app');
require '/trecho/laravel_init.php';
