<?php
// PHP8-62: locale LC_TIME depois do boot do kernel (AppServiceProvider::boot) e as datas por extenso que dependem dele. Sem banco.
// Uso: php locale_lc_time.php <raiz do ecidade> <pasta vendor>   (saida em hexa dos bytes: ISO-8859-1 conta; igual no 7.4 e no 8.5 = sem diferenca)
error_reporting(E_ALL & ~E_DEPRECATED);
$raiz = $argv[1]; $vendor = $argv[2];
date_default_timezone_set('America/Sao_Paulo');
define('LARAVEL_START', microtime(true));
require $vendor . '/autoload.php';
spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'App\\') === 0) { $f = $raiz . '/app/' . str_replace('\\', '/', substr($c, 4)) . '.php'; if (is_file($f)) { require $f; } }
});
use Carbon\Carbon;
$app = require $raiz . '/bootstrap/app.php';
$app->useStoragePath('/tmp/storage');
$app->instance('request', Illuminate\Http\Request::create('/'));
echo 'antes do boot LC_TIME=', var_export(setlocale(LC_TIME, 0), true), "\n";
$app->make(Illuminate\Contracts\Http\Kernel::class)->bootstrap();
echo 'config(app.locale)=', config('app.locale'), "\n";
echo 'depois do boot LC_TIME=', var_export(setlocale(LC_TIME, 0), true), "\n";
$h = function ($s) { return $s . ' [' . bin2hex($s) . ']'; };
Carbon::setTestNow(Carbon::create(2025, 3, 1, 12, 0, 0));
$ts = mktime(12, 0, 0, 3, 1, 2025); // sabado, 2025-03-01
foreach (array('%B', '%d de %B de %Y', '%A', '%a %b', '%A, %d de %B') as $fmt) {
    echo "formatLocalized('$fmt') = ", $h(Carbon::create(2025, 3, 1)->formatLocalized($fmt)), "\n";
    echo "strftime('$fmt')        = ", $h(@strftime($fmt, $ts)), "\n";
}
echo "ucfirst(formatLocalized('%B')) (ApropriacaoDecimoFeriasService.php:61) = ", $h(ucfirst(Carbon::parse('2025-03-01')->formatLocalized('%B'))), "\n";
echo "formatLocalized('%d de %B de %Y') (ImprimirRelatorioTemplateService.php:87) = ", $h(Carbon::now()->formatLocalized('%d de %B de %Y')), "\n";
echo "date('F l') (nao depende do locale) = ", date('F l', $ts), "\n";
