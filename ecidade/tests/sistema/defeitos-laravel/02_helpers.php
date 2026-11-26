<?php
// Helpers removidos do Laravel 6 (laravel/helpers): existem neste vendor?
require '/app/vendor/autoload.php';
foreach (['array_pluck', 'str_random', 'array_get', 'str_slug', 'str_contains', 'env', 'data_get', 'class_basename'] as $f) {
    echo str_pad($f, 15), function_exists($f) ? 'existe' : 'NAO EXISTE', "\n";
}
echo 'laravel/helpers: ', is_dir('/app/vendor/laravel/helpers') ? 'instalado' : 'ausente', "\n";
echo 'laravel/legacy-factories: ', is_dir('/app/vendor/laravel/legacy-factories') ? 'instalado' : 'ausente', "\n";
try {
    echo 'array_pluck([[a=>1],[a=>2]], a) = ', json_encode(array_pluck([['a' => 1], ['a' => 2]], 'a')), "\n";
} catch (\Throwable $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}
