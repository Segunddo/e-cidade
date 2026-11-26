<?php
// php8_62_carrega_lista.php <lista>: roda php8_62_carrega.php num processo proprio para cada arquivo da lista
// (caminhos relativos a ecidade/) e imprime "arquivo<TAB>OK" ou a primeira linha de "Fatal".
// Uso: bash docker/composer-85/roda-isolado.sh 8.5 scratchpad/php8_62_carrega_lista.php /trecho/<lista>
$lista = file($argv[1], FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
foreach ($lista as $f) {
    $saida = [];
    exec('php -d display_errors=1 -d log_errors=0 /trecho/php8_62_carrega.php ' . escapeshellarg($f) . ' 2>&1 </dev/null', $saida);
    $r = '';
    foreach ($saida as $l) {
        if (strpos($l, 'Fatal') !== false || $l === 'OK') { $r = $l; break; }
    }
    echo $f, "\t", $r, "\n";
}
