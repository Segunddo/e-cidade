<?php
$nome = 'dinamica'; $$nome = 'valor';
extract(['ex1' => 'a', 'ex2' => 'b']);
// eval intencional: fixture de teste com string CONSTANTE, para provar que codigo dinamico nao quebra a instrumentacao.
eval('$ev = 7;');
echo $dinamica, $ex1, $ex2, $ev, "\n";
$arr = ['a' => 1];
foreach ($arr as $k => $v) { $out = "$k=$v"; }
echo $out, "\n";
