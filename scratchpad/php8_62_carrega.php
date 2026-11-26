<?php
// carrega.php <arquivo>: carrega o arquivo com o autoload do 8.5 e o do legado ECidade\ (src/)
error_reporting(E_ALL & ~E_DEPRECATED);
require '/app/vendor/autoload.php';
spl_autoload_register(function ($c) {
    $p = '/app/src/' . str_replace(['ECidade\\', '\\'], ['', '/'], $c) . '.php';
    if (is_file($p)) require_once $p;
});
require_once '/app/' . $argv[1];
echo "OK\n";
