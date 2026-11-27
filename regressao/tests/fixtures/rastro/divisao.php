<?php
// Divisao SEM espaco antes de uma chamada instrumentada: a sonda nao pode virar `//` (comentario de linha).
$a = 10/count([1, 2]);
$b = $a/strlen("ab");
$c = round(@array_sum([1, 2, 3])
           /count([1, 2, 3]), 2);
$d = ($a/count([1]));
$e = $a */*c*/ 2;
echo $a, ",", $b, ",", $c, ",", $d, ",", $e, "\n";
