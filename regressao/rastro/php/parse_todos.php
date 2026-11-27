<?php
// Le caminhos relativos (um por linha) em stdin ou em argv[1..], relativos ao cwd (raiz do sistema),
// e imprime "OK\t<arq>" ou "FALHA\t<arq>\t<mensagem>" por arquivo.
// Usa nikic/php-parser do proprio ecidade/vendor, em modo PHP 7 (sintaxe do e-Cidade).
require '/var/www/html/vendor/autoload.php';

use PhpParser\Error;
use PhpParser\ParserFactory;

$parser = (new ParserFactory)->create(ParserFactory::PREFER_PHP7);

$arquivos = array_slice($argv, 1);
if (!$arquivos) {
    while (($l = fgets(STDIN)) !== false) {
        $l = rtrim($l, "\r\n");
        if ($l !== '') {
            $arquivos[] = $l;
        }
    }
}

foreach ($arquivos as $arq) {
    $fonte = @file_get_contents($arq);
    if ($fonte === false) {
        echo "FALHA\t$arq\tnao foi possivel ler\n";
        continue;
    }
    try {
        $parser->parse($fonte);
        echo "OK\t$arq\n";
    } catch (Error $e) {
        echo "FALHA\t$arq\t" . str_replace(["\r", "\n", "\t"], ' ', substr($e->getMessage(), 0, 300)) . "\n";
    } catch (\Throwable $e) {
        echo "FALHA\t$arq\t" . get_class($e) . ': ' . str_replace(["\r", "\n", "\t"], ' ', substr($e->getMessage(), 0, 280)) . "\n";
    }
}
