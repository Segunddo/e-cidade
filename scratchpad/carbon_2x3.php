<?php
// PHP8-55: Carbon 2 x 3 nos usos do codigo, sem banco e sem conexao.
// Uso: php carbon_2x3.php <pasta vendor com nesbot/carbon>   (rodar com cada vendor e comparar com diff)
error_reporting(E_ALL & ~E_DEPRECATED);
date_default_timezone_set('America/Sao_Paulo');
require $argv[1] . '/autoload.php';
use Carbon\Carbon;
Carbon::setTestNow(Carbon::create(2030, 1, 1, 12, 0, 0, 'America/Sao_Paulo'));
$f = function ($v) {
    if ($v instanceof DateTimeInterface) { return get_class($v) . '|' . $v->format('Y-m-d H:i:s.u P e'); }
    return var_export($v, true);
};
$t = function ($rot, $fn) use ($f) { try { echo "$rot => " . $f($fn()) . "\n"; } catch (Throwable $e) { echo "$rot => EXC " . get_class($e) . "\n"; } };
// createFromFormat com os formatos do codigo
foreach (array(
    array('Y-m-d', '2021-03-15'), array('Y-m-d', '2021-02-30'), array('Y-m-d', ''), array('Y-m-d', '15/03/2021'),
    array('d/m/Y', '15/03/2021'), array('d/m/Y', '2021-03-15'), array('Ymd', '20210315'), array('Y-m-d H:i', '2021-03-15 10:20'),
    array('Y-m-d', '2021-03-15 10:20:30'), array('D M d Y H:i:s e+', 'Mon Mar 15 2021 10:20:30 GMT-0300 (Brasilia Standard Time)'),
    array('Y-m-d', null), array('Y-m-d', 0), array('!Y-m-d', '2021-03-15'),
) as $c) { $t("createFromFormat({$c[0]}, " . var_export($c[1], true) . ')', function () use ($c) { return Carbon::createFromFormat($c[0], $c[1]); }); }
// createFromTimestamp (RegistroAula, Calendario, DiarioClasse, ApropriacaoDecimoFerias)
foreach (array(1615777200, 1615810830, 0, '1615777200') as $ts) {
    $t("createFromTimestamp(" . var_export($ts, true) . ')', function () use ($ts) { return Carbon::createFromTimestamp($ts); });
    $t("  ->format(Y-m-d)", function () use ($ts) { return Carbon::createFromTimestamp($ts)->format('Y-m-d H:i'); });
    $t("  ->startOfDay", function () use ($ts) { return Carbon::createFromTimestamp($ts)->startOfDay(); });
    $t("  ->getTimestamp", function () use ($ts) { return Carbon::createFromTimestamp($ts)->getTimestamp(); });
}
// parse / create / now
foreach (array('2021-03-15', '2021-03-15 10:20:30', '15/03/2021', '', 'abc', '2021-03-15T10:20:30-03:00', '2021-03-15T10:20:30Z', null) as $s) {
    $t('parse(' . var_export($s, true) . ')', function () use ($s) { return Carbon::parse($s); });
}
$t('create(2021,3,1)', function () { return Carbon::create(2021, 3, 1); });
$t('create(2021,13,1)', function () { return Carbon::create(2021, 13, 1); });
$t('create(2021,2,31)', function () { return Carbon::create(2021, 2, 31); });
$t("create('2021','03',1)", function () { return Carbon::create('2021', '03', 1); });
$t('now()', function () { return Carbon::now(); });
$t('new Carbon()', function () { return new Carbon(); });
$t('new Carbon(string)', function () { return new Carbon('2021-03-15'); });
// diff
$past = Carbon::parse('2029-12-31 11:00:00'); $fut = Carbon::parse('2030-01-01 13:30:30');
$t('past->diffInMinutes(now)', function () use ($past) { return $past->diffInMinutes(new Carbon()); });
$t('fut->diffInMinutes(now)', function () use ($fut) { return $fut->diffInMinutes(new Carbon()); });
$t('past->diffInDays(now)', function () use ($past) { return $past->diffInDays(new Carbon()); });
$t('past->diff(now)->days', function () use ($past) { return $past->diff(new Carbon())->days; });
$t('past->diff(new DateTime)->format(%y)', function () use ($past) { return $past->diff(new DateTime('2030-01-01'))->format('%y'); });
$t('past->diffInMinutes(now) > 10', function () use ($past) { return $past->diffInMinutes(new Carbon()) > 10; });
// aritmetica e comparacao
$d = Carbon::parse('2021-01-31');
$t('addMonth', function () use ($d) { return $d->copy()->addMonth(); });
$t('addDays(2)', function () use ($d) { return $d->copy()->addDays(2); });
$t('subDay', function () use ($d) { return $d->copy()->subDay(); });
$t('addMinutes(2)', function () use ($d) { return $d->copy()->addMinutes(2); });
$t('endOfDay', function () use ($d) { return $d->copy()->endOfDay(); });
$t('between', function () use ($d) { return $d->between(Carbon::parse('2021-01-01'), Carbon::parse('2021-12-31')); });
$t('toDateString', function () use ($d) { return $d->toDateString(); });
$t('toJSON', function () use ($d) { return $d->toJSON(); });
$t('json_encode', function () use ($d) { return json_encode($d); });
$t('__toString', function () use ($d) { return (string) $d; });
$t('format(c)', function () use ($d) { return $d->format('c'); });
$t('timestamp', function () use ($d) { return $d->timestamp; });
$t('year/month/day', function () use ($d) { return $d->year . '-' . $d->month . '-' . $d->day; });
$t('dayOfWeek', function () use ($d) { return $d->dayOfWeek; });
$t('lte/gt', function () use ($d) { return array($d->lte(Carbon::parse('2021-02-01')), $d->gt(Carbon::parse('2021-02-01'))); });
// age (RhDepend.php:27, RhDependController.php:73, AjudaCustoService.php:247 com subMonth)
foreach (array('1990-05-20', '2029-12-31', '2031-06-01') as $nasc) {
    $t("parse($nasc)->age", function () use ($nasc) { return Carbon::parse($nasc)->age; });
    $t("parse($nasc)->subMonth(3)->age", function () use ($nasc) { return Carbon::parse($nasc)->subMonth(3)->age; });
}
echo "TZ " . date_default_timezone_get() . "\n";
