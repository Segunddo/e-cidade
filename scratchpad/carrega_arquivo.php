<?php
// Uso: php carrega_arquivo.php <arquivo relativo a ecidade/>   (um arquivo por processo)
// Inclui o arquivo com o bootstrap da aplicacao e imprime "OK" ou o fatal.
// Pega o que o `php -l` nao ve: assinatura incompativel com a classe MAE (LSP)
// quando mae e filha estao em arquivos diferentes -- o PHP 8 so a checa ao
// declarar a classe, e o lint olha um arquivo de cada vez. Achado com as classes
// FolhaPagamento{Salario,Adiantamento,Suplementar}, que nao carregavam no 8.5.
// Rodar nos DOIS runtimes e comparar: so interessa o que carrega no 5.6 e nao no 8.5.
//
// Usado no passo 5b do guia (docs/migrar-um-modulo.md), sobre os arquivos do universo
// que tem extends/implements. Copiado para o container como /tmp/ca.php:
//   docker exec -i ecidade_php$v sh -c 'while read f; do php /tmp/ca.php "$f" </dev/null 2>/dev/null | tail -1; done' < /tmp/carga.txt
// (o `| tail -1` fica so com a ultima linha: o veredito vem depois de qualquer saida do arquivo incluido)
//
// Como faz: sobe o mesmo bootstrap que as telas usam (bootstrap.php, definitions.php,
// db_stdlib.php), inclui o arquivo via modification() -- que resolve o caminho e pode
// apontar para a copia em extension/modification/, como nas telas -- e imprime o veredito. Um fatal nao e
// capturavel por try/catch no 5.6, entao quem o relata e a funcao de shutdown.
//
// Saida (uma linha, TAB entre os campos):
//   <arquivo>  OK
//   <arquivo>  FATAL  <mensagem, ate 200 caracteres, espacos colapsados>   (fatal nao capturado)
//   <arquivo>  EXC    <classe da Exception>
//   <arquivo>  ERRO   <classe do Error> <mensagem>    (so no 8.5: o fatal vira Error capturavel)
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING & ~E_STRICT);
ini_set('display_errors', '0');
chdir('/var/www/html');
$arq = $argv[1];
// Roda no fim do processo, inclusive depois de um fatal: se o ultimo erro for de um dos
// tipos fatais, imprime a linha FATAL (nesse caso o "OK" abaixo nunca chegou a sair).
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
