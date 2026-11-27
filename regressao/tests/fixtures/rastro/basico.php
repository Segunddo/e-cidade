<?php
function soma($a, $b) {
    $r = $a + $b;
    return $r;
}
function &ref(array &$arr) { return $arr[0]; }
class C {
    const K = 1;
    public $p = [1, 2];
    public static function f($d = 5) { static $z = 0; $z++; return $z + $d; }
}
$x = 3;
$x .= 'a';
list($p, $q) = explode(',', '1,2');
[$m, $n] = [10, 20];
if (count([1, 2]) > 1) {
    $ramo = 'if-chaves';
} elseif ($x) {
    $ramo = 'elseif';
} else {
    $ramo = 'else';
}
if ($x) $semchave = 'sem chaves'; else $semchave = 'else sem chaves';
$i = 3; $acc = [];
while ($i > 0) { $acc[] = $i; $i--; }
do { $i++; } while ($i < 2);
$t = $x ? implode('-', $acc) : 'vazio';
try { throw new Exception('boom'); } catch (Exception $e) { $msg = $e->getMessage(); }
$arr = [3, 1, 2]; $r2 = &ref($arr);
for ($k = 0; $k < 2; $k++) { $f = $k * 2; }
switch ($x) { case '3a': $sw = 'a'; break; default: $sw = 'd'; }
$g = function ($v) use ($x) { $w = strlen($v) + 1; return $w; };
$h = fn($v) => $v ? strlen($v) : 0;
echo json_encode([soma(1, 2), $x, $p, $q, $m, $n, $ramo, $semchave, $acc, $i, $t, $msg, $f, $sw, C::f(), C::f(), $g('ab'), $h('abc')]), "\n";
?>
<b>html</b>
<?php $depois = 5 ?>
fim <?= $depois ?>

