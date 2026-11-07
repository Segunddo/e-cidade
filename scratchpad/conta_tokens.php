<?php
// Conta construcoes que nao sobrevivem ao PHP 8, olhando SO tokens de codigo
// (comentario e string ficam de fora, ao contrario de um regex sobre bytes).
// Uso: php conta_tokens.php <raiz>   (ONDE=1 lista no stderr cada guarda faltando)      -> imprime "categoria<TAB>ocorrencias<TAB>arquivos"
$raiz = $argv[1];
$tot = []; $arq = [];
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($raiz, FilesystemIterator::SKIP_DOTS));
foreach ($it as $f) {
    $src = file_get_contents($f->getPathname());
    $t = @token_get_all($src);
    // tokens uteis: descarta espaco e comentario
    $k = [];
    foreach ($t as $x) {
        if (is_array($x) && in_array($x[0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT])) continue;
        $k[] = $x;
    }
    $n = count($k);
    $c = ['split(' => 0, 'ereg*(' => 0, 'each(' => 0, 'parse_str 1 arg' => 0,
          'construtor PHP4' => 0, 'guarda 0=="" faltando' => 0];
    $txt = function ($i) use ($k) { return is_array($k[$i]) ? $k[$i][1] : $k[$i]; };
    $id  = function ($i) use ($k) { return is_array($k[$i]) ? $k[$i][0] : null; };
    // propriedades inicializadas com inteiro
    $intprops = [];
    for ($i = 0; $i < $n - 3; $i++) {
        if (in_array($id($i), [T_VAR, T_PUBLIC]) && $id($i+1) === T_VARIABLE && $txt($i+2) === '='
            && in_array($id($i+3), [T_LNUMBER]) ) {
            $intprops[substr($txt($i+1), 1)] = true;
        }
        if (in_array($id($i), [T_VAR, T_PUBLIC]) && $id($i+1) === T_VARIABLE && $txt($i+2) === '='
            && $txt($i+3) === '-' && $id($i+4) === T_LNUMBER) {
            $intprops[substr($txt($i+1), 1)] = true;
        }
    }
    $classe = null; $prof = 0; $profClasse = -1; $metodos = [];
    $fecha = function () use (&$classe, &$metodos, &$c) {
        if ($classe !== null && isset($metodos[strtolower($classe)]) && !isset($metodos['__construct'])) $c['construtor PHP4']++;
    };
    for ($i = 0; $i < $n; $i++) {
        $s = $txt($i);
        if ($id($i) === T_CLASS && $id($i+1) === T_STRING) { $fecha(); $classe = $txt($i+1); $metodos = []; $profClasse = $prof; }
        if ($s === '{' || $id($i) === T_CURLY_OPEN || $id($i) === T_DOLLAR_OPEN_CURLY_BRACES) $prof++;
        if ($s === '}') { $prof--; if ($classe !== null && $prof === $profClasse) { $fecha(); $classe = null; } }
        if ($id($i) === T_FUNCTION && $id($i+1) === T_STRING && $classe !== null && $prof === $profClasse + 1) $metodos[strtolower($txt($i+1))] = true;
        if ($id($i) === T_STRING && $i + 1 < $n && $txt($i+1) === '(') {
            $prev = $i > 0 ? $id($i-1) : null;
            if (in_array($prev, [T_OBJECT_OPERATOR, T_DOUBLE_COLON, T_FUNCTION, T_NEW])) continue;
            $nome = strtolower($s);
            if ($nome === 'split' || $nome === 'spliti') $c['split(']++;
            elseif (in_array($nome, ['ereg', 'eregi', 'ereg_replace', 'eregi_replace'])) $c['ereg*(']++;
            elseif ($nome === 'each') $c['each(']++;
            elseif ($nome === 'parse_str') {
                $p = 0; $virg = false;
                for ($j = $i + 1; $j < $n; $j++) {
                    $tj = $txt($j);
                    if ($tj === '(') $p++; elseif ($tj === ')') { $p--; if ($p === 0) break; }
                    elseif ($tj === ',' && $p === 1) $virg = true;
                }
                if (!$virg) $c['parse_str 1 arg']++;
            }
        }
        // $this -> prop == '<literal>'   (prop inteira, literal nao numerico)
        if ($id($i) === T_VARIABLE && $s === '$this' && $id($i+1) === T_OBJECT_OPERATOR && $id($i+2) === T_STRING
            && isset($intprops[$txt($i+2)]) && $id($i+3) === T_IS_EQUAL && $id($i+4) === T_CONSTANT_ENCAPSED_STRING) {
            $lit = substr($txt($i+4), 1, -1);
            if ($lit !== '' && ctype_digit(trim($lit))) continue;
            // guardado?  ... === 0.0 || $this->prop == ''      ou     ... == null || ($this->prop == '')
            $j = $i - 1; while ($j >= 0 && $txt($j) === '(') $j--;
            if ($j >= 0 && $id($j) === T_BOOLEAN_OR) {
                $a = $j - 1; while ($a >= 0 && $txt($a) === ')') $a--;
                if ($a >= 0 && (($id($a) === T_DNUMBER) || ($id($a) === T_STRING && strtolower($txt($a)) === 'null'))) continue;
            }
            $c['guarda 0=="" faltando']++; if (getenv("ONDE")) fwrite(STDERR, $f->getPathname().":".$k[$i][2].": ".$txt($i+2)." == ".$txt($i+4)."\n");
        }
    }
    $fecha();
    foreach ($c as $cat => $v) { if ($v) { $tot[$cat] = ($tot[$cat] ?? 0) + $v; $arq[$cat] = ($arq[$cat] ?? 0) + 1; } }
}
foreach (['guarda 0=="" faltando', 'construtor PHP4', 'parse_str 1 arg', 'split(', 'ereg*(', 'each('] as $cat)
    printf("%s\t%d\t%d\n", $cat, $tot[$cat] ?? 0, $arq[$cat] ?? 0);
