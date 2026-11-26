<?php
// Cache::put com TTL inteiro: segundos (Laravel >= 5.8). Usa o illuminate/cache do vendor montado em /app/vendor.
require '/app/vendor/autoload.php';
use Carbon\Carbon;
use Illuminate\Cache\ArrayStore;
use Illuminate\Cache\Repository;

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
foreach ([[5, 4], [5, 6], [10, 9], [10, 11], [60, 59], [60, 61]] as $p) {
    echo sprintf("put(..., %2d) depois de %3d s: %s\n", $p[0], $p[1], vive($p[0], $p[1]));
}
foreach ([3600000, 1800000, 30000] as $ms) {
    $ttl = $ms / 60000;
    Carbon::setTestNow($base->copy());
    $c = new Repository(new ArrayStore());
    $c->put('k', 'v', $ttl);
    $seg = 0;
    while ($seg < 7200) { Carbon::setTestNow($base->copy()->addSeconds($seg)); if ($c->get('k') !== 'v') break; $seg++; }
    Carbon::setTestNow();
    echo sprintf("expira em %d ms -> TTL %s: vive %d s\n", $ms, var_export($ttl, true), $seg);
}
Carbon::setTestNow($base->copy());
$c = new Repository(new ArrayStore());
$c->put('k', 'v', Carbon::now()->addMinutes(10));
Carbon::setTestNow($base->copy()->addMinutes(9)); $a = $c->get('k') === 'v' ? 'ainda no cache' : 'EXPIRADO';
Carbon::setTestNow($base->copy()->addMinutes(11)); $b = $c->get('k') === 'v' ? 'ainda no cache' : 'EXPIRADO';
echo "Carbon addMinutes(10): aos 9 min $a; aos 11 min $b\n";
