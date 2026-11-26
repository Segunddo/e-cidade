<?php
// PHP8-77: SQL gerado so pelo Grammar (sem conexao) dos 4 tipos de DB::raw que quebram no Laravel 10+, na forma de
// hoje e na ajustada, e as operacoes de arquivo do codigo (Storage do disco local e Illuminate\Filesystem\Filesystem)
// numa pasta descartavel. Roda igual no 7.4 (Laravel 8) e no 8.5 (Laravel 13): docker --network none, sem banco.
// Uso: php php8_77_trecho.php <vendor/autoload.php> <pasta descartavel>
require $argv[1];
$pasta = rtrim($argv[2], '/');
date_default_timezone_set('America/Sao_Paulo');
use Illuminate\Database\Capsule\Manager as Capsule;
$cap = new Capsule();
// configuracao de pgsql sem servidor: o PDO so seria aberto ao executar, e nada executa (toSql e pretend)
$cap->addConnection(array('driver' => 'pgsql', 'host' => 'sem-servidor', 'database' => 'x', 'username' => 'x', 'password' => 'x', 'charset' => 'latin1', 'prefix' => '', 'schema' => 'public'));
$db = $cap->getConnection();
function mostra($rotulo, $f) {
    try { $r = $f(); } catch (Throwable $e) { $r = 'ERRO ' . get_class($e) . ': ' . $e->getMessage(); }
    echo $rotulo, "\t", is_string($r) ? preg_replace('/\s+/', ' ', $r) : json_encode($r), "\n";
}
function pretend($db, $f) {   // a conexao finge executar: devolve o SQL que iria ao banco
    $log = $db->pretend($f);
    return implode(' | ', array_map(function ($q) { return $q['query']; }, $log));
}
// textos tirados dos pontos do codigo (o SQL de hoje e o proprio texto do DB::raw)
$sel = "select h16_codigo, h16_regist from rhpessoal where rh01_regist = 1";            // Concessao.php:87 (forma)
$ins = "insert into isscadsimples ( q38_sequencial ) select 1";                          // AtualizaCadastroOptantes...:89 (forma)
$ddl = "CREATE SCHEMA matriculaonline";                                                   // migration m24478:22
$case = "(CASE WHEN disbanco.dtpago IS NOT NULL THEN disbanco.dtpago = '2026-11-20' ELSE arrepaga.k00_dtpaga = '2026-11-20' END)"; // ItbinumpreRepository.php:74
$campo = "( select sum(x) from y ) AS inflatores";                                       // ProjecaoDespesaService.php:~611
foreach (array('select' => $sel, 'select-insert' => $ins) as $k => $q) {
    mostra("conexao-$k hoje", function () use ($db, $q) { return pretend($db, function ($c) use ($q) { $c->select($c->raw($q)); }); });
    mostra("conexao-$k ajustado", function () use ($db, $q) { return pretend($db, function ($c) use ($q) { $c->select($q); }); });
}
mostra('conexao-statement hoje', function () use ($db, $ddl) { return pretend($db, function ($c) use ($ddl) { $c->statement($c->raw($ddl)); }); });
mostra('conexao-statement ajustado', function () use ($db, $ddl) { return pretend($db, function ($c) use ($ddl) { $c->statement($ddl); }); });
mostra('whereRaw hoje', function () use ($db, $case) { return $db->table('itbinumpre')->whereRaw($db->raw($case))->toSql(); });
mostra('whereRaw ajustado', function () use ($db, $case) { return $db->table('itbinumpre')->whereRaw($case)->toSql(); });
mostra('selectRaw-implode hoje', function () use ($db, $campo) { return $db->table('detalhamento')->selectRaw(implode(', ', array('pl20_codigo', $db->raw($campo))))->toSql(); });
mostra('selectRaw-implode ajustado', function () use ($db, $campo) { return $db->table('detalhamento')->selectRaw(implode(', ', array('pl20_codigo', $campo)))->toSql(); });
// controle: Expression como argumento do Builder (os 390 pontos que nao quebram)
mostra('builder-select', function () use ($db) { return $db->table('t')->select(array('a', $db->raw('round(b, 2) as b')))->where($db->raw('cast(c as int)'), 1)->orderBy($db->raw('d'))->toSql(); });
mostra('builder-whereBetween', function () use ($db) { return $db->table('bens')->whereBetween($db->raw('cast(t52_ident as int)'), array(1, 9))->toSql(); });
// insert/update pelo Grammar (o log do pretend do 13 ja troca os ? pelos valores; o SQL enviado e o do Grammar)
mostra('builder-insert-valor', function () use ($db) { $q = $db->table('procandamint'); return $db->getQueryGrammar()->compileInsert($q, array('p78_data' => $db->raw('CURRENT_TIMESTAMP(0)'), 'p78_codigo' => 1)); });
mostra('builder-update-valor', function () use ($db) { $q = $db->table('procandamint')->where('p78_codigo', 1); return $db->getQueryGrammar()->compileUpdate($q, array('p78_data' => $db->raw('CURRENT_TIMESTAMP(0)'))); });
mostra('builder-from', function () use ($db) { return $db->table($db->raw('(select 1) as sub'))->toSql(); });

// Storage: disco local como no configuration/filesystems.php (root = storage_path('app')), raiz na pasta descartavel
$app = new Illuminate\Container\Container();
$app['config'] = new Illuminate\Config\Repository(array('filesystems' => array('default' => 'local',
    'disks' => array('local' => array('driver' => 'local', 'root' => $pasta . '/storage/app')))));
$fs = new Illuminate\Filesystem\FilesystemManager($app);
$lock = 'apropriacao_decimo_ferias_1.lock';   // nome de exemplo; o do codigo vem de ApropriacaoDecimoFeriasService
$texto = "Processando apropria\xe7\xe3o/estorno de d\xe9cimo ou f\xe9rias";   // ISO-8859-1, como no codigo
mostra('storage exists antes', function () use ($fs, $lock) { return $fs->exists($lock); });
mostra('storage put', function () use ($fs, $lock, $texto) { return $fs->put($lock, $texto); });
mostra('storage exists', function () use ($fs, $lock) { return $fs->exists($lock); });
mostra('storage get = texto', function () use ($fs, $lock, $texto) { return $fs->get($lock) === $texto; });
mostra('storage lastModified e inteiro', function () use ($fs, $lock) { $t = $fs->lastModified($lock); return gettype($t) . (abs($t - time()) < 60 ? ' agora' : ' ?'); });
mostra('storage path', function () use ($fs, $lock, $pasta) { return str_replace($pasta, '<pasta>', $fs->path($lock)); });
mostra('storage arquivo no disco', function () use ($pasta, $lock) { return is_file($pasta . '/storage/app/' . $lock); });
mostra('storage delete', function () use ($fs, $lock) { return $fs->delete($lock); });
mostra('storage exists depois', function () use ($fs, $lock) { return $fs->exists($lock); });
mostra('storage delete inexistente', function () use ($fs, $lock) { return $fs->delete($lock); });
// Illuminate\Filesystem\Filesystem (TemplatesXlsRelatoriosLegaisService): isDirectory, makeDirectory, move, delete
$f = new Illuminate\Filesystem\Filesystem();
$dir = $pasta . '/storage/financeiro/templates';
file_put_contents($pasta . '/modelo.xlsx', 'x');
mostra('filesystem isDirectory antes', function () use ($f, $dir) { return $f->isDirectory($dir); });
mostra('filesystem makeDirectory', function () use ($f, $dir) { return $f->makeDirectory($dir, 0755, true); });
mostra('filesystem move', function () use ($f, $pasta, $dir) { return $f->move($pasta . '/modelo.xlsx', $dir . '/modelo.xlsx'); });
mostra('filesystem delete', function () use ($f, $dir) { return $f->delete($dir . '/modelo.xlsx'); });
mostra('filesystem delete inexistente', function () use ($f, $dir) { return $f->delete($dir . '/modelo.xlsx'); });
