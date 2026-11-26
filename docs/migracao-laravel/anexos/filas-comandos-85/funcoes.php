<?php
// PHP8-51: funcoes que o Laravel 6 removeu e que o codigo do PR ainda chama (array_pluck, str_random), e
// str_contains (20 chamadas): no 7.4 vem do symfony/polyfill-php80, no 8.5 e nativa. Mesmo carregamento das telas.
chdir('/app');
require '/app/bootstrap.php';
$casos = [
  'array_pluck (ComissaoController.php:75)' => function () { return array_pluck([['m' => 1], ['m' => 2]], 'm'); },
  'str_random (ModelFactory.php:22)' => function () { return str_random(10); },
];
$sc = [['abc', 'b'], ['abc', ''], ['', ''], ['', 'a'], [null, 'a'], ['abc', null], [123, '2'], [1.5, '.'], [true, '1'],
  ["Consist\xeancia de CPF/CNPJ: Apenas v\xe1lidos", "Apenas v\xe1lidos"], ['CPF ALUNO X', 'CPF ALUNO'], ['ABC', 'b'], [['a'], 'a'], ['a', ['a']]];
foreach ($sc as $i => $a) { $casos["str_contains #$i " . json_encode(array_map(function ($x) { return is_string($x) ? utf8_encode($x) : $x; }, $a))] = function () use ($a) { return str_contains($a[0], $a[1]); }; }
foreach ($casos as $nome => $f) {
  try { $r = $f(); echo "$nome => ", var_export($r, true), "\n"; }
  catch (Throwable $e) { echo "$nome => ", get_class($e), ': ', $e->getMessage(), "\n"; }
}
echo 'str_contains vem de: ', (new ReflectionFunction('str_contains'))->isInternal() ? 'nativa' : 'polyfill', "\n";
