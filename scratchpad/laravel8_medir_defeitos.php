<?php
// Mede, sem banco e sem rede, o que o Laravel 8.73.2 (illuminate/support e illuminate/cache) faz com o TTL de Cache::put e quais helpers existem.
// Uso: ver docs/registro/defeitos-laravel8-do-pr.md (composer install de illuminate/*:8.73.2 numa pasta e php:7.4-cli --network none).
require __DIR__ . '/vendor/autoload.php';
use Carbon\Carbon;
use Illuminate\Cache\ArrayStore;
use Illuminate\Cache\Repository;

echo 'PHP ', PHP_VERSION, "\n";
foreach (array('array_pluck', 'str_random', 'array_get', 'str_slug', 'str_contains', 'env', 'data_get', 'class_basename') as $f) {
    echo str_pad($f, 15), function_exists($f) ? 'existe' : 'NAO EXISTE', "\n";
}
$base = Carbon::create(2026, 1, 1, 12, 0, 0, 'UTC');
function vive($ttl, $depois) {
    global $base;
    Carbon::setTestNow($base->copy());
    $c = new Repository(new ArrayStore());
    $c->put('k', 'v', $ttl);
    Carbon::setTestNow($base->copy()->addSeconds($depois));
    $r = $c->get('k') === 'v' ? 'ainda no cache' : 'EXPIRADO';
    Carbon::setTestNow();
    return $r;
}
echo "\nCache::put(chave, valor, N) -- N inteiro e SEGUNDOS no Laravel 8 (era MINUTOS no 5.4)\n";
foreach (array(array(5, 4), array(5, 6), array(5, 120), array(10, 9), array(10, 11), array(10, 120), array(60, 59), array(60, 61)) as $p) {
    echo sprintf("  put(..., %2d) depois de %3d s: %s\n", $p[0], $p[1], vive($p[0], $p[1]));
}
echo "\nTTL fracionario (expiraEm / 60000, como no LicitaconObrasClient e BnafarClient)\n";
foreach (array(3600000, 1800000, 30000) as $ms) {
    $ttl = $ms / 60000;
    $c = new Repository(new ArrayStore());
    $c->put('k', 'v', $ttl);
    Carbon::setTestNow($base->copy());
    echo sprintf("  expira em %d ms -> TTL %s: ", $ms, var_export($ttl, true));
    $c2 = new Repository(new ArrayStore()); Carbon::setTestNow($base->copy()); $c2->put('k', 'v', $ttl);
    $seg = 0; while ($seg < 7200) { Carbon::setTestNow($base->copy()->addSeconds($seg)); if ($c2->get('k') !== 'v') break; $seg++; }
    Carbon::setTestNow();
    echo "vive ", $seg, " s (esperado pelo codigo: ", $ms / 1000, " s)\n";
}
echo "\nCarbon como TTL (ProcessoEletronico: Carbon::now()->addMinutes(10)): ";
Carbon::setTestNow($base->copy()); $c = new Repository(new ArrayStore()); $c->put('k', 'v', Carbon::now()->addMinutes(10));
Carbon::setTestNow($base->copy()->addMinutes(9)); echo 'aos 9 min ', $c->get('k') === 'v' ? 'ainda no cache' : 'EXPIRADO';
Carbon::setTestNow($base->copy()->addMinutes(11)); echo '; aos 11 min ', $c->get('k') === 'v' ? 'ainda no cache' : 'EXPIRADO', "\n";
