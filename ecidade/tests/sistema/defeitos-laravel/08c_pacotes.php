<?php
// Os dois defeitos do artisan sao de pacote; medidos sem subir o app (o app do 8.5 nao sobe: ver T-143).
require '/app/vendor/autoload.php';
// 8.1 schedule:list: a linha que passa o timezone
$f = (new ReflectionClass(Illuminate\Console\Scheduling\ScheduleListCommand::class))->getFileName();
foreach (file($f) as $n => $l) { if (stripos($l, 'setTimezone') !== false || stripos($l, "option('timezone'") !== false) echo 'ScheduleListCommand.php:', $n + 1, ': ', trim($l), "\n"; }
// 8.2 list --format=json com descricao em ISO-8859-1 (Symfony JsonDescriptor)
$app = new Symfony\Component\Console\Application('teste', '1');
$app->setAutoExit(false);
$cmd1 = (new Symfony\Component\Console\Command\Command('ok:acento'))->setDescription("Gera\xE7\xE3o de lan\xE7amentos");
method_exists($app, 'addCommand') ? $app->addCommand($cmd1) : $app->add($cmd1);
$out = new Symfony\Component\Console\Output\BufferedOutput();
$app->run(new Symfony\Component\Console\Input\ArrayInput(['command' => 'list', '--format' => 'json']), $out);
echo 'list --format=json com descricao em ISO-8859-1: ', strlen($out->fetch()), " bytes\n";
$app2 = new Symfony\Component\Console\Application('teste', '1');
$app2->setAutoExit(false);
$cmd2 = (new Symfony\Component\Console\Command\Command('ok:ascii'))->setDescription('Geracao de lancamentos');
method_exists($app2, 'addCommand') ? $app2->addCommand($cmd2) : $app2->add($cmd2);
$out2 = new Symfony\Component\Console\Output\BufferedOutput();
$app2->run(new Symfony\Component\Console\Input\ArrayInput(['command' => 'list', '--format' => 'json']), $out2);
echo 'list --format=json so com ASCII: ', strlen($out2->fetch()) > 0 ? 'com saida' : 'vazio', "\n";
