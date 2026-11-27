<?php
// Analise ESTATICA (fase C): le .php (caminhos em stdin, relativos a --raiz) e imprime UMA linha JSON por arquivo que tem algo a dizer.
//   --modo=candidatos : usos de resultado de consulta (pode ser `false`) sem checagem        {"arquivo", "candidatos":[{linha, funcao, variavel, origem}]}
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

final class Analise extends NodeVisitorAbstract
{
    public array $candidatos = [];
    public array $leituras = [];
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
    } elseif ($modo === 'leituras') {
        $l = [];
        foreach ($a->leituras as $linha => $vars) {
            $l[$linha] = array_keys($vars);
        }
        echo json_encode(['arquivo' => $arq, 'leituras' => (object) $l]) . "\n";
    }
}
