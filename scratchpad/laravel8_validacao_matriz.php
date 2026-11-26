<?php
// Matriz regra x tipo de entrada com o validador do Laravel 8.73.2, sem banco e sem rede: cada regra que o codigo da base-php74 usa
// (so as que nao tocam o banco) contra 12 valores (inclusive array, null, '' e tipos trocados). Saida JSON canonica; igual nos dois PHPs => sem diferenca.
// Uso: php laravel8_validacao_matriz.php <pasta ecidade> <saida.json>   (autoload do vendor ao lado ou em $VENDOR)
$deprec = array();
set_error_handler(function ($no, $str) use (&$deprec) {
    if ($no === E_DEPRECATED || $no === E_USER_DEPRECATED) { return true; }
    return false;
});
require (getenv('VENDOR') ?: __DIR__ . '/vendor') . '/autoload.php';

use Illuminate\Filesystem\Filesystem;
use Illuminate\Translation\FileLoader;
use Illuminate\Translation\Translator;
use Illuminate\Validation\Factory;

$tr = new Translator(new FileLoader(new Filesystem(), rtrim($argv[1], '/') . '/resources/lang'), 'pt-br');
$tr->setFallback('en');
$f = new Factory($tr);

$regras = array('required', 'nullable', 'sometimes', 'filled', 'present', 'integer', 'numeric', 'string', 'boolean', 'array', 'json', 'email', 'url', 'ip',
    'date', 'date_format:Y-m-d', 'date_format:d/m/Y', 'digits:4', 'digits:2', 'max:10', 'min:2', 'in:1,2,3', 'regex:/^[0-9]+$/', 'different:outro',
    'required_if:outro,1', 'required_with:outro', 'required_without:outro', 'file', 'mimes:pdf');
$valores = array('texto' => 'abc', 'numero_texto' => '2026', 'data' => '2026-01-15', 'int' => 7, 'float' => 1.5, 'bool' => true, 'vazio' => '',
    'nulo' => null, 'array' => array('x'), 'array_aninhado' => array(array('a' => 1)), 'zero' => '0', 'longo' => str_repeat('a', 300));
$saida = array();
foreach ($regras as $r) {
    foreach ($valores as $nome => $valor) {
        try {
            $v = $f->make(array('campo' => $valor, 'outro' => 1), array('campo' => $r));
            $falha = $v->fails();
            $e = $v->errors()->toArray();
            $saida[$r][$nome] = $falha ? array('falha', isset($e['campo']) ? $e['campo'] : array()) : 'passa';
        } catch (Throwable $t) {
            $saida[$r][$nome] = 'EXCECAO ' . get_class($t) . ': ' . substr($t->getMessage(), 0, 110);
        }
    }
}
file_put_contents($argv[2], json_encode($saida, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n");
echo 'PHP ' . PHP_VERSION . ': ' . count($regras) . ' regras x ' . count($valores) . " valores\n";
