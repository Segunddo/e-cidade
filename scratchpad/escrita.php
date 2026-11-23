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
//
// Usado no passo 6b do guia (docs/migrar-um-modulo.md), SEMPRE atraves do
// scratchpad/porclasse.sh (uma classe por processo), copiado como /tmp/esc.php:
//   docker exec -i <container> sh /tmp/pc.sh /tmp/esc.php < /tmp/cls.txt > /tmp/w_<container>.txt
// NAO usar com o harness_robusto.sh: este harness emite varias linhas por classe.
//
// Entrada: arquivo com um caminho por linha, relativo a ecidade/ (classes/db_x_classe.php).
// Como faz, por classe:
//   1. acha o nome da classe (primeira ocorrencia de `class X` no fonte) e a inclui se preciso;
//   2. coleta as propriedades declaradas com valor inicial (`var $x =` / `public $x =`) e
//      monta um POST falso com um valor distinto para cada uma: "1000", "1001", ... (strings,
//      como chegariam de um formulario), em HTTP_POST_VARS e em $_POST;
//   3. instancia, chama atualizacampos() (se existir) e imprime cada propriedade escalar que
//      estava no POST com o valor que ficou nela.
// Saida (TAB entre os campos), varias linhas por classe:
//   <arquivo>  <campo>  <valor em var_export>
//   <arquivo>  <ERRO>   <classe do erro>     (so no 8.5; no 5.6 Throwable nao existe e o processo morre)
// Arquivo inexistente, sem `class`, cuja classe nao carrega ou sem campo no POST: nenhuma
// linha (o porclasse.sh a marca como SEM_SAIDA).
// Comparar 5.6 x 8.5 com diff; os artefatos conhecidos estao na tabela do passo 6b.
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

    // propriedades com inicializador: `var $campo =` ou `public $campo =` (as das classes de dados)
    preg_match_all('/(?:var|public)\s+\$(\w+)\s*=/', $src, $p);
    $post = [];
    foreach (array_unique($p[1]) as $i => $campo) { $post[$campo] = (string)(1000 + $i); }
    $GLOBALS['HTTP_POST_VARS'] = $post;
    $_POST = $post;

    try {
        $o = new $cls();
        if (method_exists($o, 'atualizacampos')) { $o->atualizacampos(); }
        // so os campos que o "formulario" enviou; objetos e arrays ficam de fora
        foreach (get_object_vars($o) as $k => $v) {
            if (is_object($v) || is_array($v) || !isset($post[$k])) continue;
            echo "$arq\t$k\t", var_export($v, true), "\n";
        }
    } catch (Throwable $e) {
        echo "$arq\t<ERRO>\t", get_class($e), "\n";
    }
}
