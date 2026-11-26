<?php
// PHP8-77: tira o DB::raw( ... ) em volta do texto nos pontos que quebram no Laravel 10+ (o texto fica como esta).
// Entrada: TSV arquivo<TAB>linha (relativo a <raiz>). Edita em bytes: so somem "[\]DB::raw(" e o ")" que o fecha.
// Uso: php php8_77_ajusta.php <raiz ecidade/> <lista.tsv>
$raiz = rtrim($argv[1], '/');
$alvos = array();
foreach (file($argv[2], FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $l) { list($a, $n) = explode("\t", $l); $alvos[$a][] = (int) $n; }
foreach ($alvos as $arq => $linhas) {
    $src = file_get_contents("$raiz/$arq");
    $t = token_get_all($src); $pos = array(); $o = 0;
    foreach ($t as $i => $x) { $pos[$i] = $o; $o += strlen(is_array($x) ? $x[1] : $x); }
    $tx = function ($i) use ($t) { return is_array($t[$i]) ? $t[$i][1] : $t[$i]; };
    $cortes = array();   // [inicio, fim) a remover
    for ($i = 0; $i < count($t); $i++) {
        if (!is_array($t[$i]) || !in_array($t[$i][2], $linhas) || !preg_match('/^\\\\?DB$/', $t[$i][1])) continue;
        $j = $i + 1; if ($tx($j) !== '::' || strtolower($tx($j + 1)) !== 'raw' || $tx($j + 2) !== '(') continue;
        $d = 0; $emStr = false;
        for ($k = $j + 2; $k < count($t); $k++) {
            $s = $tx($k);
            if ($s === '"') $emStr = !$emStr;
            if ($emStr) continue;
            if ($s === '(') $d++; elseif ($s === ')') { $d--; if ($d === 0) break; }
        }
        $cortes[] = array($pos[$i], $pos[$j + 3]);   // "DB::raw(" (com a barra, se houver: o token ja a inclui)
        $cortes[] = array($pos[$k], $pos[$k] + 1);   // ")"
        echo "$arq:", $t[$i][2], "\n";
    }
    usort($cortes, function ($a, $b) { return $b[0] - $a[0]; });
    foreach ($cortes as $c) $src = substr($src, 0, $c[0]) . substr($src, $c[1]);
    file_put_contents("$raiz/$arq", $src);
}
