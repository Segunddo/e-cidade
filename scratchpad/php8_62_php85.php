<?php
// php85.php <lock>: pacotes da trava cuja restricao de php nao aceita o PHP em execucao
copy('/usr/local/bin/composer', '/tmp/c.phar'); require 'phar:///tmp/c.phar/vendor/autoload.php';
use Composer\Semver\Semver;
$l = json_decode(file_get_contents($argv[1]), true);
foreach (array_merge($l['packages'], $l['packages-dev']) as $p) {
    $c = $p['require']['php'] ?? null;
    if ($c !== null && !Semver::satisfies(PHP_VERSION, $c)) echo $p['name'], ' ', $p['version'], ' php ', $c, "\n";
}
