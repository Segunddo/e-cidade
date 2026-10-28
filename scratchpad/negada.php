<?php
// Forma NEGADA do 0 == "": mede se `$this->X != ""` da resultado diferente entre os runtimes
// no estado em que o metodo realmente o avalia -- campo AUSENTE do formulario (POST vazio),
// depois do atualizacampos() que o proprio metodo chama antes (modo lido por
// scratchpad/negada_alvos.py). Nao chama alterar()/excluir(): nao toca no banco.
//
// Uso: php negada.php <tsv do negada_alvos.py>   (rodar nos DOIS runtimes e comparar)
// Saida: classe  campo  metodo  modo  tipo  valor  resultado-de-(X != "")
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
chdir('/var/www/html');
require_once('bootstrap.php');
require_once('definitions.php');
require_once(modification("libs/db_stdlib.php"));

$GLOBALS['HTTP_POST_VARS'] = array();
$_POST = array();
foreach (explode("\n", trim(file_get_contents($argv[1]))) as $l) {
    if (!$l) continue;
    list($arq, $campo, $metodo, $modo, $tipo) = explode("\t", $l);
    $src = file_get_contents($arq);
    if (!preg_match('/class\s+(\w+)/i', $src, $m)) continue;
    $cls = $m[1];
    if (!class_exists($cls)) { @include_once(modification($arq)); }
    if (!class_exists($cls)) { echo "$l\t<SEM_CLASSE>\n"; continue; }
    try {
        $o = new $cls();
        if ($modo != 'sem' && method_exists($o, 'atualizacampos')) { $o->atualizacampos($modo == 'true'); }
        $v = $o->$campo;
        echo "$l\t", var_export($v, true), "\t", ($v != "" ? 'true' : 'false'), "\n";
    } catch (Throwable $e) {
        echo "$l\t<ERRO>\t", get_class($e), "\n";
    }
}
