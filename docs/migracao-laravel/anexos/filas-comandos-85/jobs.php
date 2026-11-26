<?php
// PHP8-51: payload de fila de uma classe ShouldQueue, sem banco e sem fila de verdade: o createPayload do proprio
// Laravel (SyncQueue), com o uuid normalizado, e o unserialize de volta. Uso: php jobs.php <classe>
// Objeto: construtor real com argumentos fixos (classe tipada -> instancia sem construtor); se o construtor
// precisar de banco/servico e falhar, objeto sem construtor com cada propriedade propria = valor fixo.
chdir('/app');
require '/app/bootstrap.php';
$app = require '/app/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$classe = $argv[1];
$rc = new ReflectionClass($classe);
$origem = 'construtor';
try {
  // valores do tipo que o codigo espera, para os parametros que nao aceitam texto
  $fixos = ['datausu' => 1767225600, 'filtros' => ['relatorio' => 1, 'DB_itemmenu_acessado' => 1, 'tipo' => 'RREO', 'anexo' => 1,
    'consolidado' => 0, 'DB_instit' => 1, 'DB_modulo' => 1, 'pdf' => 'a.pdf', 'xls' => 'a.xls']];
  $args = [];
  foreach ($rc->getConstructor()->getParameters() as $p) {
    $t = $p->getType();
    if ($t && !$t->isBuiltin()) { $args[] = (new ReflectionClass($t->getName()))->newInstanceWithoutConstructor(); }
    elseif (array_key_exists($p->getName(), $fixos)) { $args[] = $fixos[$p->getName()]; }
    elseif ($p->isDefaultValueAvailable()) { $args[] = $p->getDefaultValue(); }
    else { $args[] = 'v_' . $p->getName(); }
  }
  $obj = $rc->newInstanceArgs($args);
} catch (Throwable $e) {
  $origem = 'sem construtor (' . get_class($e) . ')';
  $obj = $rc->newInstanceWithoutConstructor();
  foreach ($rc->getProperties() as $p) {
    if ($p->isStatic() || $p->getDeclaringClass()->getName() !== $classe) { continue; }
    $p->setAccessible(true);
    if ($p->getValue($obj) === null) { $p->setValue($obj, 'v_' . $p->getName()); }
  }
}
if ($obj instanceof Illuminate\Notifications\Notification) {
  $u = new App\Domain\Configuracao\Usuario\Models\Usuario(); $u->forceFill(['id_usuario' => 7]); $u->exists = true;
  $obj = new Illuminate\Notifications\SendQueuedNotifications(new Illuminate\Database\Eloquent\Collection([$u]), $obj, ['database']);
}
$q = new Illuminate\Queue\SyncQueue(); $q->setContainer($app); $q->setConnectionName('sync');
$payload = Closure::bind(function () use ($obj) { return $this->createPayload($obj, 'default', ''); }, $q, Illuminate\Queue\Queue::class)();
$p = json_decode($payload, true);
$p['uuid'] = '<uuid>';
echo "== $classe\norigem: $origem\n";
$cmd = $p['data']['command']; unset($p['data']['command']);
echo 'payload: ', json_encode($p, JSON_UNESCAPED_SLASHES), "\n";
echo 'command: ', str_replace("\0", '\0', $cmd), "\n";
try { $volta = unserialize($cmd); echo 'unserialize: ', get_class($volta), ' ', serialize($volta) === $cmd ? 'reserializa igual' : 'reserializa DIFERENTE', "\n"; }
catch (Throwable $e) { echo 'unserialize: ', get_class($e), ': ', $e->getMessage(), "\n"; }
