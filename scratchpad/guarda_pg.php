<?php
// Decisao 2a do grupo, arquivo a arquivo: pg_x($rs, ...) -> ($rs ? pg_x($rs, ...) : null)
// So quando o 1o argumento e uma variavel simples ($rs ou $this->rs). No 7.4, pg_*(false/null/"") so avisava e
// devolvia NULL; com resultado valido o objeto/resource e verdadeiro e a chamada segue igual.
// Uso: php guarda_pg.php <lista de arquivos>   (reescreve no lugar, byte a byte fora das chamadas)
$FUNC = '/^pg_(num_?rows|num_?fields|fetch_\w+|result|field_?name|field_?type|field_?num|field_?size|affected_rows|free_?result|numfields|fieldname|last_oid|result_error|result_status)$/i';
$total = 0;
foreach (file($argv[1], FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $arq) {
    $src = file_get_contents($arq);
    $t = token_get_all($src);
    $n = count($t);
    $txt = function ($k) use ($t) { return is_array($t[$k]) ? $t[$k][1] : $t[$k]; };
    $prox = function ($k) use ($t, $n) { // proximo token significativo
        for ($k++; $k < $n; $k++) {
            if (!is_array($t[$k]) || !in_array($t[$k][0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT])) return $k;
        }
        return $n;
    };
    $ant = function ($k) use ($t) {
        for ($k--; $k >= 0; $k--) {
            if (!is_array($t[$k]) || !in_array($t[$k][0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT])) return $k;
        }
        return -1;
    };
    $troca = []; // [inicio, fim, texto da variavel]
    for ($i = 0; $i < $n; $i++) {
        if (!is_array($t[$i]) || $t[$i][0] !== T_STRING || !preg_match($FUNC, $t[$i][1])) continue;
        $a = $ant($i);
        if ($a >= 0 && is_array($t[$a]) && in_array($t[$a][0], [T_OBJECT_OPERATOR, T_DOUBLE_COLON, T_FUNCTION, T_NEW, T_NS_SEPARATOR])) continue;
        $p = $prox($i);
        if ($p >= $n || $txt($p) !== '(') continue;
        // 1o argumento: $var  ou  $this->prop
        $v = $prox($p);
        if (!is_array($t[$v]) || $t[$v][0] !== T_VARIABLE) continue;
        $var = $t[$v][1];
        $f = $prox($v);
        if (is_array($t[$f]) && $t[$f][0] === T_OBJECT_OPERATOR) {
            $s = $prox($f);
            if (!is_array($t[$s]) || $t[$s][0] !== T_STRING) continue;
            $var .= '->' . $t[$s][1];
            $f = $prox($s);
        }
        if (!in_array($txt($f), [',', ')'], true)) continue;
        // ja guardada? (... $var ? pg_x(...)
        if ($a >= 0 && $txt($a) === '?') continue;
        // fecha-parenteses da chamada
        $prof = 0;
        for ($j = $p; $j < $n; $j++) {
            $c = $txt($j);
            if ($c === '(' || (is_array($t[$j]) && in_array($t[$j][0], [T_CURLY_OPEN, T_DOLLAR_OPEN_CURLY_BRACES]))) $prof++;
            elseif ($c === ')') { if (--$prof === 0) break; }
        }
        if ($j >= $n) continue;
        $troca[] = [$i, $j, $var];
        $i = $j; // chamadas aninhadas dentro dos argumentos ficam como estao (raro)
    }
    if (!$troca) continue;
    $abre = []; $fecha = [];
    foreach ($troca as [$ini, $fim, $var]) { $abre[$ini] = "($var ? "; $fecha[$fim] = ' : null)'; }
    $out = '';
    for ($k = 0; $k < $n; $k++) { $out .= ($abre[$k] ?? '') . $txt($k) . ($fecha[$k] ?? ''); }
    file_put_contents($arq, $out);
    $total += count($troca);
    echo $arq, "\t", count($troca), "\n";
}
fwrite(STDERR, "total $total\n");
