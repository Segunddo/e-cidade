<?php
// Forma NEGADA do 0 == "": mede se `$this->X != ""` da resultado diferente entre os runtimes
// no estado em que o metodo realmente o avalia -- campo AUSENTE do formulario (POST vazio),
// depois do atualizacampos() que o proprio metodo chama antes (modo lido por
// scratchpad/negada_alvos.py). Nao chama alterar()/excluir(): nao toca no banco.
//
// Uso: php negada.php <tsv do negada_alvos.py>   (rodar nos DOIS runtimes e comparar)
// Saida: classe  campo  metodo  modo  tipo  valor  resultado-de-(X != "")
//   (TAB entre os campos; as 5 primeiras colunas repetem a linha de entrada; "valor" em
//   var_export, "resultado" = true/false). Variantes: "<linha>  <SEM_CLASSE>" e
//   "<linha>  <ERRO>  <classe do erro>" (este so no 8.5; no 5.6 Throwable nao existe).
//
// Usado no passo 6c do guia (docs/migrar-um-modulo.md): copiado como /tmp/negada.php e rodado
// por classe (um processo por classe, com o TSV filtrado para ela), nos dois runtimes; as duas
// saidas vao para o scratchpad/negada_compara.py.
// Como faz: POST vazio para todas as linhas; para cada linha, instancia a classe, chama
// atualizacampos() no modo anotado (false/true; 'sem' = nao chama) e avalia `$o->campo != ""`
// -- aproxima o estado do metodo naquele ponto: so o construtor e o ultimo atualizacampos()
// anterior sao reproduzidos, nada mais que o metodo faca antes da comparacao.
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
chdir('/var/www/html');
require_once('bootstrap.php');
require_once('definitions.php');
require_once(modification("libs/db_stdlib.php"));

// formulario vazio: o campo medido esta AUSENTE do POST (o caso em que a forma negada importa)
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
