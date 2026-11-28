<?php
if ($aut == 't') { echo 1; }
if ($aut != 'abc') { echo 2; }
if ('t' == $aut) { echo 3; }
if ($v == '') { echo 4; }
if ($n == 0) { echo 5; }
if ($n == 1) { echo 6; }
if ($a == '10') { echo 7; }
if ($a === 't') { echo 8; }
if (trim($a) == 't') { echo 9; }
if ($_GET['x'] == 't') { echo 10; }
if ($a . $b == 't') { echo 11; }
if ('a' == 'b') { echo 12; }
if ($o->campo == 't') { echo 13; }
switch ($aut) {
    case 't': echo 14; break;
    case '1': echo 15; break;
    case 'x': echo 16; break;
}
if ($aut == "t$suf") { echo 17; }
$k = 0;
if ($k == 't') { echo 21; }
$c = count($lista);
if ($c == 'abc') { echo 22; }
$s = 'texto';
if ($s == 't') { echo 23; }
