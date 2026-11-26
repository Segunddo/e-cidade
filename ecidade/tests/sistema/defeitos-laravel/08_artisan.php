<?php
// artisan do PR: arquivo/comando em $argv[1]; saida e rc pelo proprio artisan. Uso: roda-isolado.sh <v> 08_artisan.php schedule:list
$_SERVER['argv'] = array_merge(['artisan'], array_slice($argv, 1));
$_SERVER['argc'] = count($_SERVER['argv']);
require '/app/artisan';
