<?php
function f($a, $b, $c) {
    $x = $a + $b;
    $y = f($x, $c);
    $rs = db_query($conn,
        $sql,
        false);
    list($ano, $mes) = explode('-', $data);
    return $y;
}
