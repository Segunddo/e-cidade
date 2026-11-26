<?php
// PHP8-55: models Eloquent em memoria (sem conexao): datas, $dates, $casts, toArray()/toJson().
// Uso: php datas.php <raiz do ecidade> > saida.txt   (saida igual nos dois runtimes = sem diferenca)
$raiz = rtrim($argv[1] ?? '/app', '/');
error_reporting(E_ALL);
$avisos = array();
set_error_handler(function ($no, $msg, $arq, $lin) use (&$avisos) {
    $avisos[] = $msg . ' @ ' . basename($arq) . ':' . $lin;
    return true;
});
date_default_timezone_set('America/Sao_Paulo');
$vendor = rtrim($argv[2] ?? ($raiz . '/vendor'), '/');
require $vendor . '/autoload.php';
spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'App\\') === 0) { $f = $raiz . '/app/' . str_replace('\\', '/', substr($c, 4)) . '.php'; if (is_file($f)) { require $f; } }
});

$cap = new Illuminate\Database\Capsule\Manager;
$cap->addConnection(array('driver' => 'pgsql', 'host' => '0.0.0.0', 'port' => 1, 'database' => 'x',
    'username' => 'x', 'password' => 'x', 'charset' => 'latin1', 'collation' => '', 'prefix' => ''));
$cap->setAsGlobal();
$cap->bootEloquent();
Carbon\Carbon::setTestNow('2030-01-01 12:00:00');

// models: arquivos com $dates ou $casts de data
$classes = array();
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($raiz . '/app', FilesystemIterator::SKIP_DOTS));
foreach ($it as $f) {
    if (substr($f, -4) !== '.php') { continue; }
    $s = file_get_contents($f);
    if (!preg_match('/\$(dates|casts)\s*=/', $s)) { continue; }
    if (!preg_match('/^namespace\s+([^;]+);/m', $s, $ns) || !preg_match('/^(?:abstract\s+)?class\s+(\w+)/m', $s, $cl)) { continue; }
    $classes[] = $ns[1] . '\\' . $cl[1];
}
sort($classes);

$amostras = array('d' => '2021-03-15', 'dh' => '2021-03-15 10:20:30', 'us' => '2021-03-15 10:20:30.123456',
    'br' => '15/03/2021', 'ts' => 1615810830, 'nulo' => null, 'vazio' => '');
$ehData = function ($tipo) {
    return in_array(strtolower($tipo), array('date', 'datetime', 'timestamp', 'immutable_date', 'immutable_datetime'), true);
};
$show = function ($v) {
    if ($v instanceof DateTimeInterface) { return get_class($v) . '|' . $v->format('Y-m-d H:i:s.u P'); }
    return var_export($v, true);
};
$totalModels = 0;
foreach ($classes as $c) {
    try { $ok = class_exists($c); } catch (Throwable $e) { $ok = false; }
    if (!$ok) { echo "MODEL $c NAO_CARREGA\n"; continue; }
    try { $m = new $c; } catch (Throwable $e) { echo "MODEL $c NEW: " . get_class($e) . ': ' . $e->getMessage() . "\n"; continue; }
    if (!$m instanceof Illuminate\Database\Eloquent\Model) { continue; }
    $totalModels++;
    $attrs = array();
    foreach ($m->getDates() as $a) { $attrs[$a] = 'dates'; }
    foreach ($m->getCasts() as $a => $t) { if ($ehData($t)) { $attrs[$a] = (isset($attrs[$a]) ? 'dates+' : '') . 'cast:' . $t; } }
    echo "MODEL $c fmt=" . (function () { return $this->getDateFormat(); })->call($m) . ' attrs=' . count($attrs) . "\n";
    foreach ($attrs as $a => $origem) {
        foreach ($amostras as $nome => $v) {
            $m = new $c;
            $m->setRawAttributes(array($a => $v));
            $p = "  $a [$origem] $nome";
            try { echo "$p get=" . $show($m->getAttribute($a)) . "\n"; } catch (Throwable $e) { echo "$p get EXC " . get_class($e) . ': ' . $e->getMessage() . "\n"; }
            try { $arr = $m->attributesToArray(); echo "$p arr=" . $show($arr[$a] ?? '(ausente)') . "\n"; } catch (Throwable $e) { echo "$p arr EXC " . get_class($e) . ': ' . $e->getMessage() . "\n"; }
            try { $j = json_decode($m->toJson(), true); echo "$p json=" . var_export($j[$a] ?? '(ausente)', true) . "\n"; } catch (Throwable $e) { echo "$p json EXC " . get_class($e) . ': ' . $e->getMessage() . "\n"; }
            // escrita: setAttribute -> valor guardado
            try {
                $w = new $c; $w->setAttribute($a, $v);
                echo "$p set=" . $show($w->getAttributes()[$a] ?? '(ausente)') . "\n";
            } catch (Throwable $e) { echo "$p set EXC " . get_class($e) . ': ' . $e->getMessage() . "\n"; }
        }
        // escrita com objeto Carbon / DateTime
        foreach (array('carbon' => function () { return Carbon\Carbon::parse('2021-03-15 10:20:30.123456'); },
                       'datetime' => function () { return new DateTime('2021-03-15 10:20:30'); }) as $n => $mk) {
            try {
                $w = new $c; $w->setAttribute($a, $mk());
                echo "  $a [$origem] $n set=" . $show($w->getAttributes()[$a] ?? '(ausente)') . "\n";
            } catch (Throwable $e) { echo "  $a [$origem] $n set EXC " . get_class($e) . ': ' . $e->getMessage() . "\n"; }
        }
    }
}
echo "TOTAL_MODELS $totalModels\n";
file_put_contents('php://stderr', "AVISOS " . count($avisos) . "\n" . implode("\n", array_unique($avisos)) . "\n");
