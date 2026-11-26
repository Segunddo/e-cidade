<?php
// PHP8-77: classifica cada chamada DB::raw( do codigo (fora de vendor/) pelo contexto, so lendo os arquivos.
// No Laravel 10 a Expression deixou de ter __toString(): quebra quando vira texto (concatenacao, cast, interpolacao,
// funcao de texto) ou quando vai para um metodo que espera texto (*Raw do Builder, select/statement da conexao).
// Categorias: QUEBRA-* (corrigir), OK-* (o Builder aceita a Expression), VER-* (decidido lendo o uso; ver o registro).
// Uso: php php8_77_db_raw.php <raiz ecidade/>  -> TSV: arquivo, linha, categoria, contexto, trecho
$raiz = rtrim($argv[1], '/');
$texto = array('selectraw', 'whereraw', 'orwhereraw', 'havingraw', 'orhavingraw', 'orderbyraw', 'groupbyraw', 'fromraw');
$conexao = array('select', 'selectone', 'statement', 'unprepared', 'insert', 'update', 'delete', 'affectingstatement', 'cursor');
$aceita = array('select', 'addselect', 'where', 'orwhere', 'wherein', 'wherenotin', 'orderby', 'groupby', 'having',
    'join', 'leftjoin', 'rightjoin', 'on', 'orwhere', 'value', 'pluck', 'from', 'table', 'wherecolumn', 'update',
    'insert', 'max', 'min', 'sum', 'count', 'avg', 'where_in', 'when', 'orderbydesc', 'firstwhere', 'join_sub', 'raw');
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($raiz, FilesystemIterator::SKIP_DOTS));
foreach ($it as $f) {
    $p = $f->getPathname(); $rel = substr($p, strlen($raiz) + 1);
    if (substr($p, -4) !== '.php' || strpos($rel, 'vendor/') === 0 || strpos($rel, 'tmp/') === 0) continue;
    $src = file_get_contents($p);
    if (stripos($src, 'DB::raw') === false) continue;
    $t = token_get_all($src);
    $n = count($t);
    // tokens de dentro de string com interpolacao ("{$x}", heredoc): nao contam como (, ), {, } do codigo
    $emStr = array(); $dentro = false;
    for ($i = 0; $i < $n; $i++) {
        $x = $t[$i];
        if ($x === '"' || (is_array($x) && in_array($x[0], array(T_START_HEREDOC, T_END_HEREDOC)))) { $dentro = !$dentro; continue; }
        if ($dentro) $emStr[$i] = true;
    }
    $sig = function ($i, $passo) use ($t, $n, $emStr) {   // proximo token significativo
        for ($i += $passo; $i >= 0 && $i < $n; $i += $passo) {
            if (isset($emStr[$i])) continue;
            if (is_array($t[$i]) && in_array($t[$i][0], array(T_WHITESPACE, T_COMMENT, T_DOC_COMMENT))) continue;
            return $i;
        }
        return -1;
    };
    $txt = function ($x) { return is_array($x) ? $x[1] : $x; };
    for ($i = 0; $i < $n; $i++) {
        if (!is_array($t[$i]) || !in_array($t[$i][0], array(T_STRING, T_NAME_FULLY_QUALIFIED, T_NAME_QUALIFIED)) || !preg_match('/(^|\\\\)DB$/', $t[$i][1])) continue;
        $a = $sig($i, 1); $b = $sig($a, 1);
        if ($a < 0 || $txt($t[$a]) !== '::' || $b < 0 || strtolower($txt($t[$b])) !== 'raw') continue;
        $linha = $t[$i][2];
        // fim da chamada DB::raw(...)
        $abre = $sig($b, 1); $d = 0; $fim = $abre;
        for ($k = $abre; $k < $n; $k++) { if (isset($emStr[$k])) continue; $s = $txt($t[$k]); if ($s === '(') $d++; elseif ($s === ')') { $d--; if ($d === 0) { $fim = $k; break; } } }
        $depois = $sig($fim, 1); $antes = $sig($i, -1);
        $sd = $depois >= 0 ? $txt($t[$depois]) : ''; $sa = $antes >= 0 ? $txt($t[$antes]) : '';
        // metodo/funcao de que e argumento: volta ate o '(' que abre
        $d = 0; $metodo = '';
        for ($k = $antes; $k >= 0; $k--) {
            if (isset($emStr[$k])) continue;
            $s = $txt($t[$k]);
            if ($s === ')' || $s === ']') $d++;
            elseif ($s === '(' || $s === '[') {
                if ($d === 0) {
                    if ($s === '(') { $m = $sig($k, -1); $metodo = $m >= 0 ? $txt($t[$m]) : ''; break; }
                    $metodo = '[';   // dentro de array: segue para fora ate o '(' ou a atribuicao que recebe o array
                    continue;
                }
                $d--;
            }
            elseif ($d === 0 && ($s === ';' || $s === '{' || $s === '}')) break;
            elseif ($d === 0 && $metodo === '[' && ($s === '=' || $s === 'return')) { $metodo = '[' . ($s === '=' ? '=' . $txt($t[$sig($k, -1)]) : 'return'); break; }
        }
        if ($metodo !== '' && $metodo[0] === '[' && $k >= 0 && $txt($t[$k]) === '(') { $m = $sig($k, -1); $metodo = '[' . ($m >= 0 ? $txt($t[$m]) : ''); }
        $ml = strtolower($metodo);
        if ($sd === '.' || $sa === '.' || $sa === '.=' ) $cat = 'QUEBRA-concatena';
        elseif (is_array($t[$antes]) && $t[$antes][0] === T_STRING_CAST) $cat = 'QUEBRA-cast';
        elseif ($sd === '->') $cat = 'VER-metodo-na-expressao';
        elseif (in_array($ml, array('whereraw', 'orwhereraw'))) $cat = 'OK-whereRaw';   // o Grammar do 10+ faz getValue() no whereRaw (medido)
        elseif (in_array($ml, $texto)) $cat = 'QUEBRA-metodo-raw';
        elseif ($metodo !== '' && $metodo[0] === '[') { $dentro = strtolower(substr($metodo, 1));
            $cat = in_array($dentro, $aceita) ? 'OK-array-para-o-builder' : (in_array($dentro, $texto) ? 'QUEBRA-array-para-raw' : 'VER-array-em-' . $dentro); }
        elseif (in_array($ml, $aceita)) $cat = 'OK-argumento-do-builder';
        elseif ($ml === '') $cat = ($sa === '=' || $sa === 'return' || $sa === '=>') ? 'VER-atribuido-ou-devolvido' : 'VER-outro';
        else $cat = 'VER-argumento-de-' . $ml;
        // DB::select/statement(DB::raw(...)): a conexao recebe a Expression como texto
        if (in_array($ml, $conexao)) {
            $q = $sig($sig($k, -1), -1); $qq = $q >= 0 ? $txt($t[$q]) : '';
            if ($qq === '::' || $qq === '->') {
                $r = $sig($q, -1); $dono = $r >= 0 ? $txt($t[$r]) : '';
                $conn = $qq === '::' && preg_match('/(^|\\\\)DB$/', $dono);
                if (!$conn && $dono === ')') {   // ...->select(: so e a conexao se a cadeia vem de connection()/getConnection()
                    $d2 = 0;
                    for ($j = $r; $j >= 0; $j--) { if (isset($emStr[$j])) continue; $s2 = $txt($t[$j]); if ($s2 === ')') $d2++; elseif ($s2 === '(') { $d2--; if ($d2 === 0) break; } }
                    $fn = $j > 0 ? strtolower($txt($t[$sig($j, -1)])) : '';
                    $conn = in_array($fn, array('connection', 'getconnection'));
                }
                if (!$conn && $dono !== ')' && preg_match('/connection$/i', $dono)) $conn = true;   // $this->connection->select(
                if ($conn) $cat = 'QUEBRA-conexao-' . $ml;
            }
        }
        $trecho = '';
        for ($j = $i; $j <= $fim && strlen($trecho) < 90; $j++) $trecho .= $txt($t[$j]);
        echo $rel, "\t", $linha, "\t", $cat, "\t", $metodo, "\t", preg_replace('/\s+/', ' ', substr($trecho, 0, 90)), "\n";
    }
}
