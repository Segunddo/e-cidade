<?php
// PHP8-51: sobe o kernel de console como o artisan (sem banco) e lista (var_export): cada comando (nome, descricao,
// oculto, argumentos e opcoes com padrao) e cada evento do agendamento (comando, cron, fuso, flags e as 3
// proximas execucoes a partir de 2026-01-01 00:00 no fuso do evento).
chdir('/app');
require '/app/bootstrap.php';
$app = require '/app/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();
$saida = ['comandos' => [], 'agenda' => []];
foreach ($kernel->all() as $nome => $c) {
  $d = $c->getDefinition();
  $saida['comandos'][$nome] = [
    'classe' => get_class($c), 'descricao' => $c->getDescription(), 'oculto' => $c->isHidden(), 'apelidos' => $c->getAliases(),
    'argumentos' => array_map(function ($a) { return [$a->getName(), $a->isRequired(), $a->isArray(), $a->getDefault(), $a->getDescription()]; }, array_values($d->getArguments())),
    'opcoes' => array_map(function ($o) { return [$o->getName(), $o->getShortcut(), $o->acceptValue(), $o->isValueRequired(), $o->isArray(), $o->getDefault(), $o->getDescription()]; }, array_values($d->getOptions())),
  ];
}
ksort($saida['comandos']);
$schedule = $app->make(Illuminate\Console\Scheduling\Schedule::class);
foreach ($schedule->events() as $e) {
  $tz = $e->timezone ? $e->timezone : config('app.timezone');
  $base = new DateTime('2026-01-01 00:00:00', new DateTimeZone($tz));
  $cron = new Cron\CronExpression($e->expression); $prox = [];
  for ($i = 0; $i < 3; $i++) { $prox[] = $cron->getNextRunDate($base, $i)->format('Y-m-d H:i:s P'); }
  $saida['agenda'][] = ['comando' => preg_replace("#^'?[^ ]*php[0-9.]*'? '?artisan'? #", '', $e->command), 'cron' => $e->expression, 'fuso' => $tz,
    'descricao' => $e->description, 'semSobreposicao' => $e->withoutOverlapping, 'umServidor' => $e->onOneServer,
    'segundoPlano' => $e->runInBackground, 'emManutencao' => $e->evenInMaintenanceMode, 'proximas' => $prox];
}
var_export($saida); echo "\n";   // var_export: descricoes em ISO-8859-1 (json_encode falharia)
