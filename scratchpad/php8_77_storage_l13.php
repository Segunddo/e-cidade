<?php
// PHP8-77: Storage com os discos do PR (ecidade/configuration/filesystems.php, lido como esta), sem subir o app e sem banco.
// A raiz do app (storage_path) e uma pasta descartavel em /tmp. Roda igual no 7.4 (Laravel 8) e no 8.5 (Laravel 13).
// Uso: bash docker/composer-85/roda-isolado.sh <7.4|8.5> scratchpad/php8_77_storage_l13.php
ini_set('display_errors', 'stderr');
error_reporting(E_ALL & ~E_DEPRECATED);
require '/app/vendor/autoload.php';
date_default_timezone_set('America/Sao_Paulo');

$raiz = '/tmp/raiz-storage';
@mkdir($raiz . '/storage', 0777, true);
$app = new Illuminate\Foundation\Application($raiz);
$app->instance('config', new Illuminate\Config\Repository(array(
    'filesystems' => require '/app/configuration/filesystems.php',
)));
Illuminate\Support\Facades\Facade::setFacadeApplication($app);
$fs = new Illuminate\Filesystem\FilesystemManager($app);
$app->instance('filesystem', $fs);

function mostra($rotulo, $f) {
    global $raiz;
    try { $r = $f(); } catch (Throwable $e) { $r = 'ERRO ' . get_class($e) . ': ' . $e->getMessage(); }
    $r = is_string($r) ? $r : json_encode($r);
    echo $rotulo, "\t", str_replace($raiz, '<raiz>', preg_replace('/\s+/', ' ', $r)), "\n";
}

mostra('config default', function () { return config('filesystems.default'); });
mostra('config discos', function () { return array_keys(config('filesystems.disks')); });
$texto = "Processando apropria\xe7\xe3o/estorno de d\xe9cimo ou f\xe9rias";   // ISO-8859-1, como no codigo
foreach (array('local', 'public', 'templates_financeiro') as $d) {
    $disco = $fs->disk($d);
    $a = 'pasta/arquivo_' . $d . '.txt';
    mostra("$d root", function () use ($disco) { return $disco->path(''); });
    mostra("$d exists antes", function () use ($disco, $a) { return $disco->exists($a); });
    mostra("$d missing antes", function () use ($disco, $a) { return $disco->missing($a); });
    mostra("$d get inexistente", function () use ($disco, $a) { return $disco->get($a); });
    mostra("$d put", function () use ($disco, $a, $texto) { return $disco->put($a, $texto); });
    mostra("$d exists", function () use ($disco, $a) { return $disco->exists($a); });
    mostra("$d get = texto", function () use ($disco, $a, $texto) { return $disco->get($a) === $texto; });
    mostra("$d size", function () use ($disco, $a) { return $disco->size($a); });
    mostra("$d lastModified", function () use ($disco, $a) { $t = $disco->lastModified($a); return gettype($t) . (abs($t - time()) < 60 ? ' agora' : ' ?'); });
    mostra("$d mimeType", function () use ($disco, $a) { return $disco->mimeType($a); });
    mostra("$d path", function () use ($disco, $a) { return $disco->path($a); });
    mostra("$d url", function () use ($disco, $a) { return $disco->url($a); });
    mostra("$d files", function () use ($disco) { return $disco->files('pasta'); });
    mostra("$d allFiles", function () use ($disco) { return $disco->allFiles(); });
    mostra("$d directories", function () use ($disco) { return $disco->directories(); });
    mostra("$d append", function () use ($disco, $a) { $disco->append($a, 'fim'); return substr($disco->get($a), -4); });
    mostra("$d prepend", function () use ($disco, $a) { $disco->prepend($a, 'ini'); return substr($disco->get($a), 0, 4); });
    mostra("$d copy", function () use ($disco, $a) { return $disco->copy($a, 'pasta/copia.txt'); });
    mostra("$d copy para existente", function () use ($disco, $a) { return $disco->copy($a, 'pasta/copia.txt'); });
    mostra("$d move", function () use ($disco) { return $disco->move('pasta/copia.txt', 'outra/movida.txt'); });
    mostra("$d makeDirectory", function () use ($disco) { return $disco->makeDirectory('nova/sub'); });
    mostra("$d getVisibility", function () use ($disco, $a) { return $disco->getVisibility($a); });
    mostra("$d delete", function () use ($disco, $a) { return $disco->delete($a); });
    mostra("$d delete inexistente", function () use ($disco, $a) { return $disco->delete($a); });
    mostra("$d deleteDirectory", function () use ($disco) { return $disco->deleteDirectory('outra'); });
    mostra("$d deleteDirectory inexistente", function () use ($disco) { return $disco->deleteDirectory('outra'); });
    mostra("$d arquivos no disco", function () use ($disco) { return $disco->allFiles(); });
}
// Facade, como no codigo (Storage:: sem disco = default)
mostra('Storage::put', function () { return Illuminate\Support\Facades\Storage::put('apropriacao_decimo_ferias_1.lock', 'x'); });
mostra('Storage::exists', function () { return Illuminate\Support\Facades\Storage::exists('apropriacao_decimo_ferias_1.lock'); });
mostra('Storage::path', function () { return Illuminate\Support\Facades\Storage::path('backup/triagem.csv'); });
mostra('Storage::delete', function () { return Illuminate\Support\Facades\Storage::delete('apropriacao_decimo_ferias_1.lock'); });
mostra('s3 disco', function () use ($fs) { return get_class($fs->disk('s3')); });
