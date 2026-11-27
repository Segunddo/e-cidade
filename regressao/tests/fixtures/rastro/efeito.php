<?php
$n = 0;
function efeito() { global $n; $n++; return 'abc'; }
$len = strlen(efeito());
$c = count([efeito(), efeito()]);
echo $len, $c, $n, "\n";
