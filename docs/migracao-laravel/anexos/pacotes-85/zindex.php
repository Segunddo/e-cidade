<?php
// PHP8-87: condicao de retorno do set_z_index do dompdf 0.8.6 (true = o valor e ignorado), linha original x linha do
// patch, para 19 valores. Uso: php zindex.php original|patch. A original so roda sem erro no 7.4 (no 8.x: TypeError).
$vals = ['auto', '0', '1', '-3', '2.5', '10', 1, 2.0, '5px', 'abc', 'inherit', '', null, ' 7', '7 ', '1e2', '0x1A', true, false];
foreach ($vals as $v) {
  if ($argv[1] === 'original') { $r = @(round($v) != $v && $v !== "auto"); }
  else { $r = (round((float)$v) != (float)$v && $v !== "auto"); }
  echo var_export($v, true), "\t", var_export($r, true), "\n";
}
