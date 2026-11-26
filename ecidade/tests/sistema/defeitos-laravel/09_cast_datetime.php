<?php
// App\Domain\Assinador\CertificadoUsuario declara 'c142_data' => 'DateTime' (nome de classe, nao 'datetime'): o Eloquent o trata como cast
// de CLASSE (class_exists('DateTime')), nao como cast de data. Mede leitura e escrita do modelo real, sem banco.
require '/app/vendor/autoload.php';
// o arquivo do PR e carregado de proposito, antes do autoload: a sobreposicao do 8.5 (app-85/), se existir, vence no PSR-4 e mediria outro codigo
require_once '/app/app/Domain/Assinador/CertificadoUsuario.php';
use App\Domain\Assinador\CertificadoUsuario;

// formato de data fixo: sem ele o modelo pede a conexao ao banco (getDateFormat) e o trecho nao tem banco
function novo() { $x = new CertificadoUsuario(); (function () { $this->dateFormat = 'Y-m-d H:i:s'; })->call($x); return $x; }
function tenta($rotulo, callable $f) {
    try { $r = $f(); echo str_pad($rotulo, 42), is_scalar($r) || $r === null ? var_export($r, true) : get_debug_type($r), "\n"; }
    catch (\Throwable $e) { echo str_pad($rotulo, 42), get_class($e), ': ', $e->getMessage(), "\n"; }
}
$m = new CertificadoUsuario();
$rm = new ReflectionMethod($m, 'isClassCastable');
if (PHP_VERSION_ID < 80100) { $rm->setAccessible(true); }
echo 'isClassCastable c142_data: ', var_export($rm->invoke($m, 'c142_data'), true), "\n";
tenta('set c142_data = new DateTime', function () { $x = novo(); $x->c142_data = new DateTime('2026-11-20 10:00:00'); return $x->getAttributes(); });
tenta("set c142_data = '2026-11-20 10:00:00'", function () { $x = novo(); $x->c142_data = '2026-11-20 10:00:00'; return $x->getAttributes(); });
tenta('set c142_data = null', function () { $x = novo(); $x->c142_data = null; return $x->getAttributes(); });
tenta('forceFill([c142_validade => DateTime])', function () { return novo()->forceFill(['c142_validade' => new DateTime('2027-01-01')])->getAttributes(); });
tenta('set de outro campo (c142_codigo)', function () { $x = novo(); $x->c142_codigo = 7; return $x->getAttributes(); });
$lido = novo()->setRawAttributes(['c142_data' => '2026-11-20 10:00:00', 'c142_validade' => '2027-01-01 00:00:00'], true);
tenta('get c142_data (valor cru do banco)', function () use ($lido) { return $lido->c142_data; });
tenta('toArray()', function () use ($lido) { return $lido->toArray(); });
