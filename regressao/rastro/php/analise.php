<?php
// Analise ESTATICA (fase C): le .php (caminhos em stdin, relativos a --raiz) e imprime UMA linha JSON por arquivo que tem algo a dizer.
//   --modo=candidatos : usos de resultado de consulta (pode ser `false`) sem checagem        {"arquivo", "candidatos":[{linha, funcao, variavel, origem}]}
//   --modo=comparacoes: `==`/`!=`/switch entre literal (texto nao numerico, '' ou 0) e outra expressao (muda no PHP 8: 0 == 't')  {"arquivo", "comparacoes":[{linha, tipo, op, expressao, literal}]}
//   --modo=leituras   : variaveis lidas por linha (para a cadeia por dependencia do backend Xdebug)  {"arquivo", "leituras":{"<linha>":[vars]}}
// Nao executa nada, nao instrumenta nada: por isso nao ha cache nem "reinstrumentar".
require __DIR__ . '/autoload.php';

use PhpParser\Node;
use PhpParser\Node\Expr;
use PhpParser\Node\Stmt;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitorAbstract;
use PhpParser\ParserFactory;

// Funcoes que devolvem `false` quando falham (o PHP 7.4 so avisava ao usar o resultado; o 8.x lanca TypeError).
const FALSOS = ['pg_query', 'pg_exec', 'pg_query_params', 'pg_execute', 'pg_prepare', 'db_query', 'fopen', 'file_get_contents', 'opendir'];
// Metodos de DAO do e-Cidade que devolvem `false` quando a consulta falha ($cl->sql_record($sql)): o idioma dominante do codigo.
const METODOS_FALSOS = ['sql_record'];
// Funcoes que exigem o resultado valido como PRIMEIRO argumento.
const SUMIDOUROS = ['pg_num_rows', 'pg_numrows', 'pg_fetch_assoc', 'pg_fetch_array', 'pg_fetch_object', 'pg_fetch_row', 'pg_fetch_all',
    'pg_fetch_result', 'pg_result', 'pg_num_fields', 'pg_affected_rows', 'pg_field_name', 'pg_free_result', 'pg_result_seek',
    'db_fieldsmemory', 'fputs', 'fwrite', 'fclose', 'fgets', 'feof', 'readdir', 'closedir'];
// Funcoes cujo argumento CONTA como checagem do valor (`is_resource($rs)`, `isset($rs)`...).
const CHECAGENS = ['is_resource', 'is_bool', 'is_object', 'is_null', 'is_array', 'isset', 'empty', 'pg_last_error', 'is_a'];
// Funcoes que devolvem inteiro/numero.
const INTEIROS = ['count', 'sizeof', 'strlen', 'intval', 'floatval', 'pg_num_rows', 'pg_numrows', 'pg_affected_rows', 'pg_num_fields', 'array_sum',
    'round', 'floor', 'ceil', 'abs', 'mktime', 'time', 'strtotime'];
// Funcoes que sempre devolvem string: comparar o resultado com um literal nao muda de comportamento no PHP 8.
const STRINGS = ['trim', 'ltrim', 'rtrim', 'strtolower', 'strtoupper', 'ucfirst', 'ucwords', 'substr', 'str_replace', 'str_pad', 'implode',
    'sprintf', 'date', 'basename', 'dirname', 'pg_result', 'pg_fetch_result', 'pg_field_name', 'strval', 'json_encode', 'nl2br',
    'htmlspecialchars', 'addslashes', 'md5', 'urlencode', 'utf8_decode', 'utf8_encode', 'number_format', 'db_formatar'];

final class Analise extends NodeVisitorAbstract
{
    public array $candidatos = [];
    public array $leituras = [];
    public array $comparacoes = [];
    /** @var array<int,array{origem:array,guardada:array}> */
    private array $escopos = [];
    /** @var Node[] */
    private array $pilha = [];

    public function __construct(private string $modo)
    {
        $this->escopos[] = ['origem' => [], 'guardada' => []];
    }

    private function nome(Node $n): string
    {
        if ($n instanceof Expr\FuncCall && $n->name instanceof Node\Name) {
            return strtolower($n->name->getLast());
        }
        return '';
    }

    /** Origem que pode devolver `false`: funcao da lista ou metodo de DAO (`$cl->sql_record(...)`). */
    private function devolveFalso(Node $rhs): bool
    {
        if ($rhs instanceof Expr\ErrorSuppress) {
            $rhs = $rhs->expr;
        }
        if ($rhs instanceof Expr\MethodCall && $rhs->name instanceof Node\Identifier) {
            return in_array(strtolower($rhs->name->toString()), METODOS_FALSOS, true);
        }
        return in_array($this->nome($rhs), FALSOS, true);
    }

    private function escopo(): array
    {
        return $this->escopos[count($this->escopos) - 1];
    }

    private function marca(string $v, string $campo, mixed $valor): void
    {
        $this->escopos[count($this->escopos) - 1][$campo][$v] = $valor;
    }

    /**
     * Esta ocorrencia de variavel e uma CHECAGEM (`!$rs`, `$rs === false`, `if ($rs)`, `isset($rs)`...)? So conta se ela esta numa
     * condicao e NAO e argumento de uma chamada (`pg_num_rows($rs)` dentro de um if nao checa $rs), exceto as funcoes de checagem.
     * A marca e feita NA ORDEM DE AVALIACAO: em `pg_numrows($r) == 0 || !$r` o uso vem antes da checagem.
     */
    private function ehChecagem(): bool
    {
        for ($i = count($this->pilha) - 2; $i >= 0; $i--) {
            $p = $this->pilha[$i];
            $filho = $this->pilha[$i + 1];
            if ($p instanceof Expr\FuncCall || $p instanceof Expr\MethodCall || $p instanceof Expr\StaticCall || $p instanceof Expr\New_) {
                if ($filho instanceof Node\Arg) {
                    if ($p instanceof Expr\FuncCall && in_array($this->nome($p), CHECAGENS, true)) {
                        continue;
                    }
                    return false;
                }
                continue;
            }
            if ($p instanceof Stmt\If_ || $p instanceof Stmt\ElseIf_ || $p instanceof Stmt\While_ || $p instanceof Stmt\Do_ || $p instanceof Stmt\Switch_) {
                return $p->cond === $filho;
            }
            if ($p instanceof Stmt\For_) {
                return in_array($filho, $p->cond, true);
            }
            if ($p instanceof Expr\Ternary) {
                if ($p->cond === $filho) {
                    return true;
                }
                continue;
            }
            if ($p instanceof Expr\BooleanNot || $p instanceof Expr\BinaryOp\BooleanOr || $p instanceof Expr\BinaryOp\BooleanAnd
                || $p instanceof Expr\BinaryOp\LogicalOr || $p instanceof Expr\BinaryOp\LogicalAnd || $p instanceof Expr\Isset_
                || $p instanceof Expr\Empty_ || $p instanceof Expr\BinaryOp\Identical || $p instanceof Expr\BinaryOp\NotIdentical
                || $p instanceof Expr\BinaryOp\Equal || $p instanceof Expr\BinaryOp\NotEqual) {
                return true;
            }
            if ($p instanceof Stmt) {
                return false;
            }
        }
        return false;
    }

    private function dentroDeCondicao(Node $assign): bool
    {
        for ($i = count($this->pilha) - 2; $i >= 0; $i--) {
            $p = $this->pilha[$i];
            if ($p instanceof Expr\BooleanNot || $p instanceof Expr\BinaryOp\BooleanOr || $p instanceof Expr\BinaryOp\BooleanAnd
                || $p instanceof Expr\BinaryOp\LogicalOr || $p instanceof Expr\BinaryOp\LogicalAnd || $p instanceof Expr\Ternary
                || $p instanceof Expr\BinaryOp\Identical || $p instanceof Expr\BinaryOp\NotIdentical
                || $p instanceof Expr\BinaryOp\Equal || $p instanceof Expr\BinaryOp\NotEqual) {
                return true;
            }
            if ($p instanceof Stmt\If_ || $p instanceof Stmt\ElseIf_ || $p instanceof Stmt\While_ || $p instanceof Stmt\Do_) {
                return $p->cond === ($this->pilha[$i + 1] ?? null);
            }
            if ($p instanceof Stmt) {
                return false;
            }
        }
        return false;
    }

    public function enterNode(Node $n)
    {
        $this->pilha[] = $n;
        if ($n instanceof Stmt\Function_ || $n instanceof Stmt\ClassMethod || $n instanceof Expr\Closure || $n instanceof Expr\ArrowFunction) {
            $this->escopos[] = ['origem' => [], 'guardada' => []];
        }
        if ($this->modo === 'candidatos') {
            if ($n instanceof Expr\Variable && is_string($n->name)) {
                $pai = $this->pilha[count($this->pilha) - 2] ?? null;
                if (!($pai instanceof Expr\Assign && $pai->var === $n) && $this->ehChecagem()) {
                    $this->marca($n->name, 'guardada', true);
                }
            } elseif ($n instanceof Expr\FuncCall) {
                $nome = $this->nome($n);
                $a0 = $n->args[0]->value ?? null;
                if (in_array($nome, SUMIDOUROS, true) && $a0 instanceof Expr\Variable && is_string($a0->name)) {
                    $e = $this->escopo();
                    if (isset($e['origem'][$a0->name]) && empty($e['guardada'][$a0->name])) {
                        $this->candidatos[] = ['linha' => $n->getStartLine(), 'funcao' => $nome, 'variavel' => $a0->name,
                                               'origem' => $e['origem'][$a0->name]];
                    }
                }
            }
        } elseif ($this->modo === 'comparacoes') {
            if ($n instanceof Expr\BinaryOp\Equal || $n instanceof Expr\BinaryOp\NotEqual) {
                $this->comparacao($n->left, $n->right, $n->getStartLine(), $n instanceof Expr\BinaryOp\Equal ? '==' : '!=');
            } elseif ($n instanceof Stmt\Switch_) {
                foreach ($n->cases as $c) {
                    if ($c->cond !== null) {
                        $this->comparacao($n->cond, $c->cond, $c->getStartLine(), 'switch');
                    }
                }
            }
        } else {
            if ($n instanceof Expr\FuncCall || $n instanceof Expr\MethodCall || $n instanceof Expr\StaticCall || $n instanceof Expr\New_) {
                $this->leCall($n);
            } elseif ($n instanceof Expr\Variable && is_string($n->name)) {
                if (!$this->eEscrita()) {
                    $this->leituras[$n->getStartLine()][$n->name] = true;
                }
            }
        }
        return null;
    }

    /**
     * `==`/`!=`/`switch` entre um LITERAL e outra expressao. O PHP 8 mudou o resultado quando um lado e inteiro (ou vazio/null) e o outro uma
     * string nao numerica: `0 == 't'` era true no 7.4 e e false no 8.x (e `0 == ''` idem). Nao ha aviso nem excecao: so a resposta muda.
     * Tipos: texto (literal nao numerico), vazio (''), zero (0). Nao aponta quando o outro lado e sabidamente string.
     */
    private function comparacao(Node $a, Node $b, int $linha, string $op): void
    {
        foreach ([[$a, $b], [$b, $a]] as [$lit, $outro]) {
            $tipo = null;
            if ($lit instanceof Node\Scalar\String_) {
                $tipo = $lit->value === '' ? 'vazio' : (is_numeric($lit->value) ? null : 'texto');
            } elseif ($lit instanceof Node\Scalar\LNumber && $lit->value === 0) {
                $tipo = 'zero';
            }
            if ($tipo !== null && !$this->eLiteral($outro) && !$this->eSabidamenteString($outro)
                && !(($op === '==' || $op === '!=') && $this->protegida($op, $this->imprime($outro)))) {
                // Evidencia de inteiro so agrava `texto`/`vazio` ($k = 0; $k == 't'). Contra o literal 0 ela e inocua ($k = 0; $k == 0).
                $inteiro = $tipo !== 'zero' && ($this->podeSerZero($outro) || $this->atribuicaoAlcanca($outro));
                $this->comparacoes[] = ['linha' => $linha, 'tipo' => $tipo, 'op' => $op, 'evidencia' => $inteiro ? 'inteiro' : '',
                                        'expressao' => $this->imprime($outro), 'literal' => $this->imprime($lit)];
                return;
            }
        }
    }

    private function eZeroLiteral(?Node $n): bool
    {
        return ($n instanceof Node\Scalar\LNumber && $n->value === 0) || ($n instanceof Node\Scalar\DNumber && $n->value == 0.0)
            || ($n instanceof Node\Scalar\String_ && $n->value === '0');
    }

    /**
     * O resultado nao muda de forma observavel quando o zero ja e tratado: (a) `$v == '' ? 0 : $v` devolve 0 nos dois casos;
     * (b) a mesma expressao e testada contra 0 na mesma condicao (`$v == 0 || $v == ''`, `$v != '' && $v !== 0`).
     */
    private function protegida(string $op, string $texto): bool
    {
        $cmp = $this->pilha[count($this->pilha) - 1];
        $pai = $this->pilha[count($this->pilha) - 2] ?? null;
        if ($pai instanceof Expr\Ternary && $pai->cond === $cmp && $pai->if !== null) {
            [$zero, $resto] = $op === '==' ? [$pai->if, $pai->else] : [$pai->else, $pai->if];
            if ($this->eZeroLiteral($zero) && $this->imprime($resto) === $texto) {
                return true;
            }
        }
        $raiz = $cmp;
        $dono = null;
        for ($i = count($this->pilha) - 2; $i >= 0; $i--) {
            $p = $this->pilha[$i];
            if ($p instanceof Expr\BinaryOp\BooleanOr || $p instanceof Expr\BinaryOp\BooleanAnd || $p instanceof Expr\BinaryOp\LogicalOr
                || $p instanceof Expr\BinaryOp\LogicalAnd || $p instanceof Expr\BooleanNot) {
                $raiz = $p;
                continue;
            }
            $dono = $p;
            break;
        }
        // (c) `if ($v == '') { $v = 0; }`: repete o zero, o resultado final e o mesmo
        if ($op === '==' && ($dono instanceof Stmt\If_ || $dono instanceof Stmt\ElseIf_) && $dono->cond === $raiz) {
            foreach ($dono->stmts as $s) {
                $e = $s instanceof Stmt\Expression ? $s->expr : null;
                if ($e instanceof Expr\Assign && $this->eZeroLiteral($e->expr) && $this->imprime($e->var) === $texto) {
                    return true;
                }
            }
        }
        return $this->guardaZero($raiz, $texto, $cmp);
    }

    private function guardaZero(Node $n, string $texto, Node $exceto): bool
    {
        if ($n !== $exceto && ($n instanceof Expr\BinaryOp\Equal || $n instanceof Expr\BinaryOp\NotEqual || $n instanceof Expr\BinaryOp\Identical
                || $n instanceof Expr\BinaryOp\NotIdentical)) {
            foreach ([[$n->left, $n->right], [$n->right, $n->left]] as [$z, $x]) {
                if ($this->eZeroLiteral($z) && $this->imprime($x) === $texto) {
                    return true;
                }
            }
        }
        // (d) o tipo ja e testado na mesma condicao: `is_string($v) && $v == ''`, `gettype($v) == 'string' && ...`
        if ($n instanceof Expr\FuncCall && in_array($this->nome($n), ['is_string', 'gettype', 'is_numeric', 'is_int', 'is_integer', 'ctype_digit'], true)
            && isset($n->args[0]) && $this->imprime($n->args[0]->value) === $texto) {
            return true;
        }
        foreach ($n->getSubNodeNames() as $sub) {
            $v = $n->$sub;
            foreach (is_array($v) ? $v : [$v] as $f) {
                if ($f instanceof Node && $this->guardaZero($f, $texto, $exceto)) {
                    return true;
                }
            }
        }
        return false;
    }

    /** Numero que PODE ser 0: literal 0, ou expressao numerica nao literal (count(), aritmetica, cast...). `5` nunca muda de comportamento. */
    private function podeSerZero(Node $n): bool
    {
        if ($n instanceof Node\Scalar\LNumber) {
            return $n->value === 0;
        }
        if ($n instanceof Node\Scalar\DNumber) {
            return $n->value == 0.0;
        }
        // `$x + 1` / `1 + $x`: so e 0 se $x for -1; nos contadores e codigos do e-Cidade isso nao ocorre (heuristica declarada no baseline)
        if ($n instanceof Expr\BinaryOp\Plus && (($n->left instanceof Node\Scalar\LNumber && $n->left->value > 0)
                || ($n->right instanceof Node\Scalar\LNumber && $n->right->value > 0))) {
            return false;
        }
        return $this->eInteiro($n);
    }

    /** Ramos de `if/elseif/else` (por if) em que a pilha atual esta: {id do if => then|ei<N>|else|cond}. */
    private function ramos(): array
    {
        $r = [];
        for ($i = 0; $i < count($this->pilha) - 1; $i++) {
            $p = $this->pilha[$i];
            if (!($p instanceof Stmt\If_)) {
                continue;
            }
            $f = $this->pilha[$i + 1];
            $id = spl_object_id($p);
            if ($f === $p->cond) {
                $r[$id] = 'cond';
            } elseif ($p->else !== null && $f === $p->else) {
                $r[$id] = 'else';
            } elseif (($k = array_search($f, $p->elseifs, true)) !== false) {
                $r[$id] = 'ei' . $k;
            } else {
                $r[$id] = 'then';
            }
        }
        return $r;
    }

    /** Duas posicoes em ramos DIFERENTES do mesmo if nunca executam na mesma passada: a atribuicao de um nao chega ao outro. */
    private function exclusivos(array $a, array $b): bool
    {
        foreach ($a as $id => $ramo) {
            if (isset($b[$id]) && $b[$id] !== $ramo && $ramo !== 'cond' && $b[$id] !== 'cond') {
                return true;
            }
        }
        return false;
    }

    /** A variavel recebeu, antes e em ramo que pode chegar aqui, um numero que pode ser 0 (`$k = 0; ... $k == 't'`). */
    private function atribuicaoAlcanca(Node $n): bool
    {
        if (!($n instanceof Expr\Variable && is_string($n->name))) {
            return false;
        }
        $atual = $this->ramos();
        foreach ($this->escopo()['inteiros'][$n->name] ?? [] as $ramos) {
            if (!$this->exclusivos($ramos, $atual)) {
                return true;
            }
        }
        return false;
    }

    /** Expressao que sabidamente produz inteiro/numero: literal, cast, aritmetica, count()/strlen()/pg_num_rows()... */
    private function eInteiro(Node $n): bool
    {
        if ($n instanceof Node\Scalar\LNumber || $n instanceof Node\Scalar\DNumber || $n instanceof Expr\Cast\Int_ || $n instanceof Expr\Cast\Double) {
            return true;
        }
        if ($n instanceof Expr\UnaryMinus || $n instanceof Expr\UnaryPlus) {
            return $this->eInteiro($n->expr);
        }
        if ($n instanceof Expr\BinaryOp\Plus || $n instanceof Expr\BinaryOp\Minus || $n instanceof Expr\BinaryOp\Mul || $n instanceof Expr\BinaryOp\Mod) {
            return true;
        }
        return $n instanceof Expr\FuncCall && in_array($this->nome($n), INTEIROS, true);
    }

    private function eLiteral(Node $n): bool
    {
        return $n instanceof Node\Scalar || $n instanceof Expr\ConstFetch || $n instanceof Expr\ClassConstFetch
            || ($n instanceof Expr\Array_ && !$n->items);
    }

    private function eSabidamenteString(Node $n): bool
    {
        if ($n instanceof Expr\BinaryOp\Concat || $n instanceof Expr\Cast\String_) {
            return true;
        }
        if ($n instanceof Expr\FuncCall) {
            return in_array($this->nome($n), STRINGS, true);
        }
        if ($n instanceof Expr\ArrayDimFetch && $n->var instanceof Expr\Variable && is_string($n->var->name)) {
            return in_array($n->var->name, ['_GET', '_POST', '_REQUEST', '_COOKIE', '_SERVER', 'HTTP_GET_VARS', 'HTTP_POST_VARS',
                'HTTP_SERVER_VARS', 'HTTP_COOKIE_VARS'], true);
        }
        return false;
    }

    private function imprime(Node $n): string
    {
        static $p = null;
        $p ??= new \PhpParser\PrettyPrinter\Standard();
        $s = str_replace("\n", ' ', $p->prettyPrintExpr($n));
        return strlen($s) > 80 ? substr($s, 0, 77) . '...' : $s;
    }

    /** A variavel (topo da pilha) e ALVO de uma atribuicao: `$x = ...` ou desestruturacao `list($a, $b) = ...` / `[$a, $b] = ...`. */
    private function eEscrita(): bool
    {
        $filho = $this->pilha[count($this->pilha) - 1];
        for ($i = count($this->pilha) - 2; $i >= 0; $i--) {
            $p = $this->pilha[$i];
            if ($p instanceof Expr\Assign || $p instanceof Expr\AssignRef) {
                return $p->var === $filho;
            }
            if (!($p instanceof Expr\ArrayItem || $p instanceof Expr\List_ || $p instanceof Expr\Array_)) {
                return false;
            }
            $filho = $p;
        }
        return false;
    }

    /** Uma chamada que ocupa varias linhas: as variaveis dos argumentos valem para TODAS as linhas dela (o Xdebug pode reportar qualquer uma). */
    private function leCall(Node $n): void
    {
        $nomes = [];
        $this->variaveis($n, $nomes);
        for ($l = $n->getStartLine(); $l <= $n->getEndLine(); $l++) {
            foreach ($nomes as $v => $_) {
                $this->leituras[$l][$v] = true;
            }
        }
    }

    private function variaveis(Node $no, array &$nomes): void
    {
        if ($no instanceof Expr\Variable && is_string($no->name)) {
            $nomes[$no->name] = true;
        }
        foreach ($no->getSubNodeNames() as $sub) {
            $v = $no->$sub;
            foreach (is_array($v) ? $v : [$v] as $f) {
                if ($f instanceof Node) {
                    $this->variaveis($f, $nomes);
                }
            }
        }
    }

    public function leaveNode(Node $n)
    {
        array_pop($this->pilha);
        if ($n instanceof Stmt\Function_ || $n instanceof Stmt\ClassMethod || $n instanceof Expr\Closure || $n instanceof Expr\ArrowFunction) {
            array_pop($this->escopos);
        }
        if ($this->modo === 'comparacoes' && $n instanceof Expr\Assign && $n->var instanceof Expr\Variable && is_string($n->var->name)) {
            $ramos = $this->ramos();
            $i = count($this->escopos) - 1;
            if ($this->podeSerZero($n->expr)) {
                $this->escopos[$i]['inteiros'][$n->var->name][] = $ramos;
            } elseif (!$ramos) {
                unset($this->escopos[$i]['inteiros'][$n->var->name]);   // atribuicao nao numerica fora de ramo: reinicia
            }
        }
        if ($this->modo === 'candidatos' && $n instanceof Expr\Assign && $n->var instanceof Expr\Variable && is_string($n->var->name)) {
            $v = $n->var->name;
            $this->pilha[] = $n;   // a pilha ainda deve conter o proprio Assign para dentroDeCondicao()
            $dentro = $this->dentroDeCondicao($n);
            array_pop($this->pilha);
            if ($this->devolveFalso($n->expr)) {
                $this->marca($v, 'origem', $n->getStartLine());
                $this->marca($v, 'guardada', $dentro);
            } else {
                $e = $this->escopos[count($this->escopos) - 1];
                unset($e['origem'][$v], $e['guardada'][$v]);
                $this->escopos[count($this->escopos) - 1] = $e;
            }
        }
        return null;
    }
}

$o = getopt('', ['raiz:', 'modo:']);
$raiz = rtrim($o['raiz'] ?? '/var/www/html', '/');
$modo = $o['modo'] ?? 'candidatos';
$parser = (new ParserFactory)->create(ParserFactory::PREFER_PHP7);
while (($arq = fgets(STDIN)) !== false) {
    $arq = rtrim($arq, "\r\n");
    $fonte = $arq === '' ? false : @file_get_contents("$raiz/$arq");
    if ($fonte === false) {
        continue;
    }
    try {
        $ast = $parser->parse($fonte);
        $a = new Analise($modo);
        $t = new NodeTraverser();
        $t->addVisitor($a);
        $t->traverse($ast);
    } catch (\Throwable $e) {
        continue;
    }
    if ($modo === 'candidatos' && $a->candidatos) {
        echo json_encode(['arquivo' => $arq, 'candidatos' => $a->candidatos]) . "\n";
    } elseif ($modo === 'comparacoes') {
        if ($a->comparacoes) {
            echo json_encode(['arquivo' => $arq, 'comparacoes' => $a->comparacoes]) . "\n";
        }
    } elseif ($modo === 'leituras') {
        $l = [];
        foreach ($a->leituras as $linha => $vars) {
            $l[$linha] = array_keys($vars);
        }
        echo json_encode(['arquivo' => $arq, 'leituras' => (object) $l]) . "\n";
    }
}
