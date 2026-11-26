<?php
// PHP8-38: as classes de middleware que o Kernel do app (app/Http/Kernel.php) usa existem no vendor? (sem banco; nao instancia o app)
// Uso: bash docker/composer-85/roda-isolado.sh <7.4|8.5> scratchpad/middlewares_classes.php /app /app/vendor
error_reporting(E_ALL & ~E_DEPRECATED);
$raiz = $argv[1]; $vendor = $argv[2];
require $vendor . '/autoload.php';
spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'App\\') === 0) { $f = $raiz . '/app/' . str_replace('\\', '/', substr($c, 4)) . '.php'; if (is_file($f)) { require $f; } }
});
$r = new ReflectionClass('App\\Http\\Kernel');
$def = $r->getDefaultProperties();
$aliases = isset($def['routeMiddleware']) ? $def['routeMiddleware'] : array();
$resolve = function ($m) use ($aliases) {
    $nome = strpos($m, ':') !== false ? substr($m, 0, strpos($m, ':')) : $m;
    return isset($aliases[$nome]) ? $aliases[$nome] : $nome;
};
$vistos = array();
$linha = function ($onde, $m) use ($resolve, &$vistos) {
    $c = $resolve($m); $chave = $onde . '|' . $m;
    if (isset($vistos[$chave])) { return; }
    $vistos[$chave] = 1;
    $existe = class_exists($c) || interface_exists($c);
    $pai = '';
    if ($existe) { $rc = new ReflectionClass($c); $pai = $rc->getParentClass() ? ' extends ' . $rc->getParentClass()->getName() : ''; }
    echo str_pad($onde, 8) . ' ' . $m . ($c !== $m ? " -> $c" : '') . ' existe=' . var_export($existe, true) . $pai . "\n";
};
foreach ($def['middleware'] as $m) { $linha('global', $m); }
foreach ($def['middlewareGroups'] as $g => $ms) { foreach ($ms as $m) { $linha($g, $m); } }
foreach ($aliases as $a => $m) { $linha('alias', $a); }
