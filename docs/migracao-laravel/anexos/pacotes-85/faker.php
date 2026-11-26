<?php
// T-102: o que database/factories/ModelFactory.php pede ao Faker (name, unique()->safeEmail), com semente fixa.
require $argv[1] . '/autoload.php';
foreach ([1, 42, 2026] as $semente) {
  $f = Faker\Factory::create(); $f->seed($semente);
  for ($i = 0; $i < 50; $i++) { echo $semente, "\t", $f->name, "\t", $f->unique()->safeEmail, "\n"; }
}
