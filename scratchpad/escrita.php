<?php
// Exercita o CAMINHO DE ESCRITA das classes de dados sem HTTP e sem tocar no
// banco. Popula HTTP_POST_VARS como um formulario faria, chama atualizacampos()
// e imprime o estado resultante.
//
// E AQUI que vive o idioma `$this->X == "" ? POST : $this->X`, responsavel por
// 763 das 837 correcoes que a bateria de telas NAO exercita -- ela faz so GET,
// e HTTP_POST_VARS nunca e populado num GET.
//
// Uso: php scratchpad/escrita.php <arquivo com a lista de classes>
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
chdir('/var/www/html');
require_once('bootstrap.php');
require_once('definitions.php');
require_once(modification("libs/db_stdlib.php"));

foreach (explode("\n", trim(file_get_contents($argv[1]))) as $arq) {
    if (!$arq || !is_file($arq)) continue;
    $src = file_get_contents($arq);
    if (!preg_match('/class\s+(\w+)/i', $src, $m)) continue;
    $cls = $m[1];
    if (!class_exists($cls)) { @include_once(modification($arq)); }
    if (!class_exists($cls)) continue;

    preg_match_all('/(?:var|public)\s+\$(\w+)\s*=/', $src, $p);
    $post = [];
    foreach (array_unique($p[1]) as $i => $campo) { $post[$campo] = (string)(1000 + $i); }
    $GLOBALS['HTTP_POST_VARS'] = $post;
    $_POST = $post;

    try {
        $o = new $cls();
        if (method_exists($o, 'atualizacampos')) { $o->atualizacampos(); }
        foreach (get_object_vars($o) as $k => $v) {
            if (is_object($v) || is_array($v) || !isset($post[$k])) continue;
            echo "$arq\t$k\t", var_export($v, true), "\n";
        }
    } catch (Throwable $e) {
        echo "$arq\t<ERRO>\t", get_class($e), "\n";
    }
}
