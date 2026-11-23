<?php
// DivisaoComoNo74Rector sozinha (PHP8-40). Uso, no container 8.5, de ecidade/: ALVOS=lista.txt (caminhos relativos a ecidade/) rector process --config <este arquivo>
require_once __DIR__ . '/rector-rules/DivisaoComoNo74Rector.php';
use ECidade\RectorRules\DivisaoComoNo74Rector;
use Rector\Config\RectorConfig;
use Rector\ValueObject\PhpVersion;
$paths = [];
foreach (file(getenv('ALVOS'), FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $l) {
    $p = '/var/www/html/' . trim($l);
    if (is_file($p)) { $paths[] = $p; }
}
if (!$paths) { fwrite(STDERR, "SEM ALVOS\n"); exit(2); }
return RectorConfig::configure()->withPaths($paths)->withPhpVersion(PhpVersion::PHP_74)->withRules([DivisaoComoNo74Rector::class]);
