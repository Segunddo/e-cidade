<?php
// PHP8-51: das classes de app/ cujo arquivo cita ShouldQueue (lista no stdin, um caminho app/... por linha), imprime
// as que de fato implementam Illuminate\Contracts\Queue\ShouldQueue (reflexao; pega "implements \Nome\Qualificado").
chdir('/app');
require '/app/bootstrap.php';
foreach (file('php://stdin', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $arq) {
  $classe = str_replace('/', '\\', preg_replace(['#^app/#', '#\.php$#'], ['App/', ''], $arq));
  if (class_exists($classe) && is_subclass_of($classe, Illuminate\Contracts\Queue\ShouldQueue::class)) { echo $classe, "\n"; }
}
