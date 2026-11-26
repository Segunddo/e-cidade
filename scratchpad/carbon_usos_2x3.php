<?php
// PHP8-55: usos do Carbon do codigo proprio (arquivo:linha) com a entrada real de cada um, Carbon 2 x 3. Sem banco, sem rede.
// Uso: php scratchpad/carbon_usos_2x3.php <pasta vendor com nesbot/carbon>   (relogio fixo 2030-01-01 23:30 America/Sao_Paulo; ver docs/migracao-laravel/carbon3-usos.md)
error_reporting(E_ALL & ~E_DEPRECATED);
date_default_timezone_set('America/Sao_Paulo');
require $argv[1] . '/autoload.php';
use Carbon\Carbon;
Carbon::setTestNow(Carbon::create(2030, 1, 1, 23, 30, 0, 'America/Sao_Paulo'));
$f = function ($v) {
    if ($v instanceof DateTimeInterface) { return get_class($v) . '|' . $v->format('Y-m-d H:i:s P'); }
    return var_export($v, true);
};
$caso = function ($id, $rot, $fn) use ($f) {
    try { $r = $fn(); $o = $f($r); } catch (Throwable $e) { $o = 'EXC ' . get_class($e) . ': ' . substr(preg_replace('/\s+/', ' ', $e->getMessage()), 0, 90); }
    echo "$id | $rot => $o\n";
};
// 1) formatLocalized: ApropriacaoDecimoFeriasService.php:61,73,98 e ImprimirRelatorioTemplateService.php:87
//    O locale vem do boot do AppServiceProvider (linhas 25-39): setlocale(LC_TIME,'pt-br') (falha) e, se PHP_VERSION_ID < LIMITE, a lista ptb/pt_BR/...
//    LIMITE = 74000 no PR (vale so no PHP 7); 90000 com a correcao da PHP8-62 (T-139). Saida em hexa: o mes vem em ISO-8859-1 (mar\xe7o).
$hx = function ($v) { return is_string($v) ? $v . ' [' . bin2hex($v) . ']' : var_export($v, true); };
$caso1 = function ($id, $rot, $fn) use ($hx) {
    try { $o = $hx($fn()); } catch (Throwable $e) { $o = 'EXC ' . get_class($e) . ': ' . substr(preg_replace('/\s+/', ' ', $e->getMessage()), 0, 70); }
    echo "$id | $rot => $o\n";
};
$boot = function ($limite) {
    setlocale(LC_TIME, 'C');
    $a = setlocale(LC_TIME, 'pt-br');
    if (PHP_VERSION_ID < $limite) { setlocale(LC_TIME, array('ptb', 'pt_BR', 'portuguese-brazil', 'portuguese-brazilian', 'bra', 'brazil', 'br')); }
    return setlocale(LC_TIME, 0);
};
$pt = function ($c, $fmt) { return mb_convert_encoding($c->copy()->locale('pt_BR')->translatedFormat($fmt), 'ISO-8859-1', 'UTF-8'); };
foreach (array('boot original (PHP_VERSION_ID < 74000)' => 74000, 'boot com a T-139 (PHP_VERSION_ID < 90000)' => 90000) as $nome => $lim) {
    $lc = $boot($lim);
    $caso1('U1', "$nome [LC_TIME=$lc] c01_data=2025-03-01 ->formatLocalized('%B')", function () { return Carbon::parse('2025-03-01')->formatLocalized('%B'); });
    $caso1('U2', "$nome Carbon::create(2025,3,1)->formatLocalized('%B')", function () { return Carbon::create(2025, 3, 1)->formatLocalized('%B'); });
    $caso1('U3', "$nome Carbon::now()->formatLocalized('%d de %B de %Y')", function () { return Carbon::now()->formatLocalized('%d de %B de %Y'); });
    $caso1('U1', "  proposta B: strftime('%B', ts)", function () { return @strftime('%B', Carbon::parse('2025-03-01')->getTimestamp()); });
    $caso1('U3', "  proposta B: strftime('%d de %B de %Y', ts)", function () { return @strftime('%d de %B de %Y', Carbon::now()->getTimestamp()); });
    $caso1('U1', "  proposta C: locale('pt_BR')->translatedFormat('F') em ISO-8859-1", function () use ($pt) { return $pt(Carbon::parse('2025-03-01'), 'F'); });
    $caso1('U3', "  proposta C: locale('pt_BR')->translatedFormat('d \\d\\e F \\d\\e Y') em ISO-8859-1", function () use ($pt) { return $pt(Carbon::now(), 'd \\d\\e F \\d\\e Y'); });
}
setlocale(LC_TIME, 'C');
// 2) createFromTimestamp: DB_datausu = time() (DefaultSession.php:115), usado em ->format('Y-m-d') (ProfissionalEscolaRepository.php:120, ConteudoDesenvolvidoRepository.php:87)
$agora = Carbon::now()->getTimestamp();
$caso('U5', 'RegistroAulaController.php:67/77, CalendarioController.php:83: createFromTimestamp(time()=23:30 local)->format(Y-m-d)', function () use ($agora) { return Carbon::createFromTimestamp($agora)->format('Y-m-d'); });
$caso('U5', '  idem, objeto', function () use ($agora) { return Carbon::createFromTimestamp($agora); });
$caso('U5', '  proposta: createFromTimestamp($ts, date_default_timezone_get())->format(Y-m-d)', function () use ($agora) { return Carbon::createFromTimestamp($agora, date_default_timezone_get())->format('Y-m-d'); });
$meia = mktime(0, 0, 0, 3, 15, 2021);
$caso('U6', 'DiarioClassePdf.php:362/1110/1116: createFromTimestamp(meia-noite local de 2021-03-15) month/day', function () use ($meia) { $c = Carbon::createFromTimestamp($meia); return $c->month . '/' . $c->day; });
$tarde = mktime(22, 0, 0, 3, 15, 2021);
$caso('U6', '  idem com 22:00 local', function () use ($tarde) { $c = Carbon::createFromTimestamp($tarde); return $c->month . '/' . $c->day; });
$caso('U6', '  lt() entre o periodo do diario (2021-03-15 00:00 local) e a data de saida (createFromTimestamp)', function () use ($meia) { return Carbon::parse('2021-03-15')->lt(Carbon::createFromTimestamp($meia)); });
// 3) diffInMinutes: ApropriacaoDecimoFeriasService.php:377/382 (arquivo de trava; mtime x agora, > 10)
$mt_passado = Carbon::now()->subMinutes(15)->getTimestamp(); $mt_futuro = Carbon::now()->addMinutes(15)->getTimestamp();
$caso('U7', 'mtime 15 min no passado: createFromTimestamp->diffInMinutes(new Carbon()) > 10', function () use ($mt_passado) { $d = Carbon::createFromTimestamp($mt_passado); return array($d->diffInMinutes(new Carbon()), $d->diffInMinutes(new Carbon()) > 10); });
$caso('U7', 'mtime 15 min no futuro (relogio atrasado)', function () use ($mt_futuro) { $d = Carbon::createFromTimestamp($mt_futuro); return array($d->diffInMinutes(new Carbon()), $d->diffInMinutes(new Carbon()) > 10); });
$caso('U7', '  proposta: diffInMinutes(new Carbon(), true) no futuro', function () use ($mt_futuro) { $d = Carbon::createFromTimestamp($mt_futuro); return array($d->diffInMinutes(new Carbon(), true), $d->diffInMinutes(new Carbon(), true) > 10); });
$caso('U7', '  proposta: diffInMinutes(new Carbon(), true) no passado', function () use ($mt_passado) { $d = Carbon::createFromTimestamp($mt_passado); return array($d->diffInMinutes(new Carbon(), true), $d->diffInMinutes(new Carbon(), true) > 10); });
// 4) age: RhDepend.php:27, RhDependController.php:73, AjudaCustoService.php:246 (subMonth(rh312_quantidade)->age comparado com rh311_idademax)
foreach (array('1990-05-20', '2012-12-31', '2031-06-01') as $n) {
    $caso('U8', "Carbon::parse('$n')->age", function () use ($n) { return Carbon::parse($n)->age; });
    $caso('U8', "  proposta abs(Carbon::parse('$n')->age)", function () use ($n) { return abs(Carbon::parse($n)->age); });
    $caso('U8', "Carbon::parse('$n')->subMonth(6)->age (rh312_quantidade=6)", function () use ($n) { return Carbon::parse($n)->subMonth(6)->age; });
}
// 5) createFromFormat com os formatos do codigo e valores de colunas date/timestamp
foreach (array(array('Y-m-d', '2021-03-15'), array('Y-m-d', '2021-03-15 10:20:30'), array('Y-m-d', ''), array('d/m/Y', '15/03/2021'), array('d/m/Y', '2021-03-15'), array('Ymd', '20210315'), array('Y-m-d H:i', '2021-03-15 10:20'), array('Y-m-d', '2021-02-30'), array('Y-m-d', null)) as $c) {
    $caso('U9', "createFromFormat({$c[0]}, " . var_export($c[1], true) . ")", function () use ($c) { return Carbon::createFromFormat($c[0], $c[1]); });
}
// 6) cadeias: RedesimAlterarInscricaoService.php:396 (addMonth(1)->firstOfMonth), Alvara/AlvaraBaseReport.php:65 (getTimestamp), TriagemLaboratorialRepository.php:176/177 (startOfDay/endOfDay), UnificacaoCgsRepository.php:223 (toDateString)
foreach (array('2021-01-31', '2021-12-15', '2021-03-15') as $n) {
    $caso('U10', "createFromFormat(Y-m-d,'$n')->addMonth(1)->firstOfMonth()->format(Y-m-d)", function () use ($n) { return Carbon::createFromFormat('Y-m-d', $n)->addMonth(1)->firstOfMonth()->format('Y-m-d'); });
}
$caso('U11', 'parse(2021-03-15)->startOfDay / endOfDay', function () { return array(Carbon::parse('2021-03-15 10:00')->startOfDay()->format('Y-m-d H:i:s.u'), Carbon::parse('2021-03-15 10:00')->endOfDay()->format('Y-m-d H:i:s.u')); });
$caso('U11', 'toDateString / getTimestamp', function () { return array(Carbon::parse('2021-03-15 10:00')->toDateString(), Carbon::parse('2021-03-15 10:00')->getTimestamp()); });
$caso('U12', 'between (ProcessoInscricaoController.php:94, ProcessoInscricaoService.php:101)', function () { $d = Carbon::parse('2021-03-15'); return array($d->between(Carbon::parse('2021-03-01'), Carbon::parse('2021-03-31')), $d->between(Carbon::parse('2021-03-15'), Carbon::parse('2021-03-15'))); });
$caso('U13', 'AuthServiceProvider.php:35-37 Carbon::now()->addDay() / addDays(2): tipo devolvido', function () { return array(get_class(Carbon::now()->addDay()), Carbon::now()->addDay()->format('Y-m-d H:i'), Carbon::now()->addDays(2)->format('Y-m-d H:i')); });
$caso('U14', 'addMinutes(10) (ProcessoEletronico.php:208, requisicaoMaterial.model.php:550)', function () { return Carbon::now()->addMinutes(10)->format('Y-m-d H:i:s'); });
$caso('U15', 'now()->subDay() (PruneOldTokens.php:33)', function () { return Carbon::now()->subDay()->format('Y-m-d H:i:s'); });
