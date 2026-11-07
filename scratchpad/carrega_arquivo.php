<?php
// Uso: php carrega_arquivo.php <arquivo relativo a ecidade/>   (um arquivo por processo)
// Inclui o arquivo com o bootstrap da aplicacao e imprime "OK" ou o fatal.
// Pega o que o `php -l` nao ve: assinatura incompativel com a classe MAE (LSP)
// quando mae e filha estao em arquivos diferentes -- o PHP 8 so a checa ao
// declarar a classe, e o lint olha um arquivo de cada vez. Achado com as classes
// FolhaPagamento{Salario,Adiantamento,Suplementar}, que nao carregavam no 8.5.
// Rodar nos DOIS runtimes e comparar: so interessa o que carrega no 5.6 e nao no 8.5.
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING & ~E_STRICT);
ini_set('display_errors', '0');
chdir('/var/www/html');
$arq = $argv[1];
register_shutdown_function(function () use ($arq) {
    $e = error_get_last();
    if ($e && in_array($e['type'], array(E_ERROR, E_PARSE, E_COMPILE_ERROR, E_CORE_ERROR))) {
        echo $arq, "\tFATAL\t", preg_replace('/\s+/', ' ', substr($e['message'], 0, 200)), "\n";
    }
});
require_once('bootstrap.php');
require_once('definitions.php');
require_once(modification("libs/db_stdlib.php"));
try {
    include_once(modification($arq));
    echo $arq, "\tOK\n";
} catch (Exception $e) {
    echo $arq, "\tEXC\t", get_class($e), "\n";
} catch (Throwable $e) {      // so existe no 7+; no 5.6 nunca e avaliado
    echo $arq, "\tERRO\t", get_class($e), ' ', substr($e->getMessage(), 0, 160), "\n";
}
