<?php
/* Caracteriza a forma canonica do grupo, com dados sinteticos. */
error_reporting(E_ALL & ~E_DEPRECATED);
set_error_handler(function($severity,$message,$file,$line) {
    if(!(error_reporting() & $severity)) {return false;}
    throw new ErrorException($message,0,$severity,$file,$line);
});
function legacy_query($query) {
    $nome='anterior';
    parse_str($query);
    unset($query);
    return get_defined_vars();
}
function migrated_query($query) {
    $nome='anterior';
    parse_str($query,$__qs);
    unset($__qs['this'],$__qs['GLOBALS']);
    extract($__qs);
    unset($__qs,$query);
    return get_defined_vars();
}
$mode=isset($argv[1])?$argv[1]:'';
if(!in_array($mode,array('legacy','migrated'),true) || ($mode==='legacy' && PHP_VERSION_ID>=80000)) {
    fwrite(STDERR,"Use legacy no PHP 7.4 ou migrated nos dois runtimes.\n");exit(2);
}
$queries=array('', 'nome=Pedro&idade=20','itens[]=a&itens[]=b',
    'campo.com.ponto=valor&campo+com+espaco=x','x=1&x=2',
    'texto=Jo%C3%A3o+Pessoa','x=&flag&valor=0',
    'n[0]=1&n[1]=2&n[2][a]=b','x=%26%3D%2B','nome=novo',
    'v=-1&decimal=1.5','a=%00','a=um+dois&a=ultimo');
$results=array();
foreach($queries as $query) {
    $variables=$mode==='legacy'?legacy_query($query):migrated_query($query);
    ksort($variables);
    $results[]=$variables;
}
echo json_encode(array('cases'=>count($results),'results'=>$results),JSON_THROW_ON_ERROR),"\n";
