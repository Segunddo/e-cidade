<?php
// PHP8-51: le os "command" serializados por um runtime (arquivo de jobs.php) e mostra o estado de cada objeto
// (classe e propriedades ordenadas por nome, recursivo), sem restaurar model (identificador fica como esta).
chdir('/app');
require '/app/bootstrap.php';
$app = require '/app/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
function estado($v, $n = 0) {
  if ($v instanceof DateTimeInterface) { return get_class($v) . ' ' . $v->format('Y-m-d H:i:s.u e'); }   // o 7.4 expoe date/timezone como propriedade, o 8 nao
  if (is_object($v)) {
    if ($n > 6) { return get_class($v); }
    $r = new ReflectionObject($v); $o = ['@classe' => get_class($v)];
    foreach ($r->getProperties() as $p) { if ($p->isStatic()) { continue; } $p->setAccessible(true); $o[$p->getDeclaringClass()->getName() . '::' . $p->getName()] = $p->isInitialized($v) ? estado($p->getValue($v), $n + 1) : '<nao inicializada>'; }
    foreach ((array) get_object_vars($v) as $k => $x) { if (!$r->hasProperty($k)) { $o['dinamica::' . $k] = estado($x, $n + 1); } }
    ksort($o); return $o;
  }
  if (is_array($v)) { $o = []; foreach ($v as $k => $x) { $o[$k] = estado($x, $n + 1); } return $o; }
  return $v;
}
foreach (file($argv[1]) as $l) {
  if (strpos($l, '== ') === 0) { $nome = trim(substr($l, 3)); }
  if (strpos($l, 'command: ') === 0) {
    $cmd = str_replace('\0', "\0", rtrim(substr($l, 9), "\n"));
    // SerializesModels restauraria o model pelo banco no __unserialize: troca o identificador por um que nao restaura
    $cmd = str_replace('O:45:"Illuminate\Contracts\Database\ModelIdentifier"', 'O:8:"stdClass"', $cmd);
    try { $o = unserialize($cmd); echo "== $nome\n", var_export(estado($o), true), "\n"; }
    catch (Throwable $e) { echo "== $nome\nERRO ", get_class($e), ': ', $e->getMessage(), "\n"; }
  }
}
