<?php
// Carrega UM arquivo sem o bootstrap da aplicacao (que exige o ambiente montado): autoload do vendor/ +
// mapa classe->arquivo (gerado pelo e1_lsp, ver docs "Como provar que o verificador funciona").
// Serve para conferir o e1_lsp.py num PHP de verdade, em conteiner descartavel, sem banco e sem rede:
//   docker run --rm -i --network none -v $PWD/ecidade:/var/www/html:ro \
//     -v $PWD/scratchpad/carga_isolada.php:/c.php:ro -v /tmp/mapa.tsv:/mapa.tsv:ro \
//     --entrypoint sh <imagem> -c 'while read f; do php /c.php "$f" </dev/null 2>/dev/null | tail -1; done' < lista
// Saida: arquivo<TAB>OK | arquivo<TAB>FATAL<TAB>mensagem | arquivo<TAB>ERRO<TAB>classe mensagem
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
ini_set('display_errors', '0');
chdir('/var/www/html');
$arq = $argv[1];
register_shutdown_function(function () use ($arq) {
    $e = error_get_last();
    if ($e && in_array($e['type'], [E_ERROR, E_PARSE, E_COMPILE_ERROR, E_CORE_ERROR]))
        echo $arq, "\tFATAL\t", preg_replace('/\s+/', ' ', substr($e['message'], 0, 220)), "\n";
});
function modification($f) { return $f; }   // a aplicacao troca o caminho por uma copia modificada; aqui, o original
@require_once 'vendor/autoload.php';
$M = [];
foreach (file('/mapa.tsv') as $l) { [$k, $v] = explode("\t", rtrim($l)); $M[$k] = $v; }
spl_autoload_register(function ($c) use ($M) { $k = strtolower($c); if (isset($M[$k])) require_once $M[$k]; });
try { require_once $arq; echo $arq, "\tOK\n"; }
catch (Throwable $e) { echo $arq, "\tERRO\t", get_class($e), ' ', substr($e->getMessage(), 0, 160), "\n"; }
