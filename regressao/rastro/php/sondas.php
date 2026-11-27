<?php
// Visitor que calcula as EMENDAS de texto (nunca reimprime o arquivo): cada emenda e (posicao, ordem, texto).
// Toda sonda e escrita numa unica linha entre marcadores /*R*/ ... /*R*/ para que um teste a remova
// e recupere o original byte a byte. Chamado por instrumentador.php.

use PhpParser\Node;
use PhpParser\Node\Expr;
use PhpParser\Node\Stmt;
use PhpParser\NodeFinder;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitorAbstract;

final class Sondas extends NodeVisitorAbstract
{
    // O marcador comeca com ESPACO: sem ele, uma divisao sem espaco (`$a/count($b)`) viraria `//*R*/...`, que e um
    // comentario de linha e engole o resto da linha. O espaco faz parte do marcador (sai junto com a sonda).
    const M = ' /*R*/';

    /** @var array<int,array{0:int,1:int,2:string}> */
    private array $edits = [];
    private int $seq = 0;
    private int $nextId = 1;
    /** @var array<int,array<string,mixed>> */
    private array $mapa = [];
    /** @var array<int,Node> */
    private array $stack = [];
    /** @var array<int,bool> */
    private array $porRef = [];
    /** @var array<int,array<int,array{0:int,1:string}>> */
    private array $fechar = [];
    private NodeFinder $finder;

    /**
     * @param array<int,mixed> $tokens  tokens do lexer (arrays [id,texto,linha] ou strings)
     * @param array<int,int>   $tokPos  posicao em bytes de cada token
     * @param array<string,true> $funcoes nomes (minusculos) de funcoes com sonda de chamada
     */
    public function __construct(private string $src, private array $tokens, private array $tokPos, private array $funcoes)
    {
        $this->finder = new NodeFinder();
    }

    public function sondas(): int { return $this->nextId - 1; }
    public function mapa(): array { return $this->mapa; }

    public function aplica(): string
    {
        $e = $this->edits;
        usort($e, fn($a, $b) => [$a[0], $a[1]] <=> [$b[0], $b[1]]);
        $out = '';
        $ultimo = 0;
        foreach ($e as [$pos, , $txt]) {
            $out .= substr($this->src, $ultimo, $pos - $ultimo) . $txt;
            $ultimo = $pos;
        }
        return $out . substr($this->src, $ultimo);
    }

    // ---- utilidades ----------------------------------------------------------------------------

    private function registra(string $tipo, int $linha, string $nome, array $le): int
    {
        $id = $this->nextId++;
        $this->mapa[$id] = ['linha' => $linha, 'tipo' => $tipo, 'nome' => $nome, 'le' => array_values($le)];
        return $id;
    }

    private function emenda(int $pos, string $txt): void
    {
        $this->edits[] = [$pos, $this->seq++, $txt];
    }

    /** @return string[] nomes de variaveis simples lidas dentro de $no */
    private function variaveis(Node|array $no): array
    {
        $achadas = $this->finder->findInstanceOf($no, Expr\Variable::class);
        $nomes = [];
        foreach ($achadas as $v) {
            if (is_string($v->name)) {
                $nomes[$v->name] = $v->name;
            }
        }
        return array_values($nomes);
    }

    private function tokenTexto(int $i): string
    {
        $t = $this->tokens[$i] ?? '';
        return is_array($t) ? $t[1] : $t;
    }

    private function tokenId(int $i): int|string
    {
        $t = $this->tokens[$i] ?? '';
        return is_array($t) ? $t[0] : $t;
    }

    /** indice do token significativo anterior (pula espacos e comentarios); -1 se nao ha */
    private function anterior(int $idx): int
    {
        for ($i = $idx - 1; $i >= 0; $i--) {
            $id = $this->tokenId($i);
            if ($id === T_WHITESPACE || $id === T_COMMENT || $id === T_DOC_COMMENT) {
                continue;
            }
            return $i;
        }
        return -1;
    }

    /** O comando esta numa LISTA de comandos (nao e corpo sem chaves de if/else/while/for/do)? */
    private function emLista(Node $n): bool
    {
        $a = $this->anterior((int) $n->getAttribute('startTokenPos'));
        if ($a < 0) {
            return true;
        }
        $id = $this->tokenId($a);
        if ($id === '{' || $id === ';' || $id === '}' || $id === ':') {
            return true;
        }
        return in_array($id, [T_OPEN_TAG, T_OPEN_TAG_WITH_ECHO, T_CLOSE_TAG, T_INLINE_HTML], true);
    }

    private function abre(Node $n, string $fn, string $extra, int $id): void
    {
        $this->emenda((int) $n->getAttribute('startFilePos'), self::M . $fn . '(' . $id . $extra . ',' . self::M);
        $this->fechar[spl_object_id($n)][] = [(int) $n->getAttribute('endFilePos') + 1, self::M . ')' . self::M];
    }

    // ---- visitor -------------------------------------------------------------------------------

    public function enterNode(Node $n)
    {
        // Contextos de expressao constante: nao pode haver chamada de funcao nem sonda.
        if ($n instanceof Node\Param || $n instanceof Stmt\ClassConst || $n instanceof Stmt\Const_
            || $n instanceof Stmt\StaticVar || $n instanceof Stmt\PropertyProperty
            || $n instanceof Stmt\DeclareDeclare) {
            return NodeTraverser::DONT_TRAVERSE_CHILDREN;
        }
        $this->stack[] = $n;

        if ($n instanceof Stmt\Function_ || $n instanceof Stmt\ClassMethod || $n instanceof Expr\Closure
            || $n instanceof Expr\ArrowFunction) {
            $this->porRef[] = (bool) $n->byRef;
        }

        if ($n instanceof Stmt\Expression) {
            $this->atribuicao($n);
        } elseif ($n instanceof Stmt\Return_ && $n->expr !== null && !end($this->porRef)) {
            $id = $this->registra('retorno', $n->getStartLine(), '', $this->variaveis($n->expr));
            $this->abre($n->expr, '__rt_r', '', $id);
        } elseif ($n instanceof Stmt\If_ || $n instanceof Stmt\ElseIf_ || $n instanceof Stmt\While_
            || $n instanceof Stmt\Do_ || $n instanceof Expr\Ternary) {
            $id = $this->registra('ramo', $n->getStartLine(), 'cond', $this->variaveis($n->cond));
            $this->abre($n->cond, '__rt_t', '', $id);
        } elseif ($n instanceof Expr\FuncCall) {
            $this->chamada($n);
        } elseif ($n instanceof Stmt\Catch_ && $n->var instanceof Expr\Variable && is_string($n->var->name) && $n->stmts) {
            $this->catchSonda($n);
        }
        return null;
    }

    public function leaveNode(Node $n)
    {
        if ($n instanceof Node\Param || $n instanceof Stmt\ClassConst || $n instanceof Stmt\Const_
            || $n instanceof Stmt\StaticVar || $n instanceof Stmt\PropertyProperty
            || $n instanceof Stmt\DeclareDeclare) {
            return null;
        }
        array_pop($this->stack);
        if ($n instanceof Stmt\Function_ || $n instanceof Stmt\ClassMethod || $n instanceof Expr\Closure
            || $n instanceof Expr\ArrowFunction) {
            array_pop($this->porRef);
        }
        $k = spl_object_id($n);
        if (isset($this->fechar[$k])) {
            foreach (array_reverse($this->fechar[$k]) as [$pos, $txt]) {
                $this->emenda($pos, $txt);
            }
            unset($this->fechar[$k]);
        }
        return null;
    }

    private function atribuicao(Stmt\Expression $n): void
    {
        $e = $n->expr;
        $nomes = [];
        if (($e instanceof Expr\Assign || $e instanceof Expr\AssignOp) && $e->var instanceof Expr\Variable && is_string($e->var->name)) {
            $nomes = [$e->var->name];
        } elseif ($e instanceof Expr\Assign && ($e->var instanceof Expr\List_ || $e->var instanceof Expr\Array_)) {
            foreach ($e->var->items as $item) {
                if ($item !== null && $item->value instanceof Expr\Variable && is_string($item->value->name)) {
                    $nomes[] = $item->value->name;
                }
            }
        }
        if (!$nomes || !$this->emLista($n)) {
            return;
        }
        $fim = (int) $n->getAttribute('endTokenPos');
        if ($this->tokenId($fim) !== ';') {   // comando terminado pela tag de fechamento: nao ha onde inserir
            return;
        }
        $le = $this->variaveis($e->expr);
        $txt = '';
        foreach ($nomes as $nome) {
            $id = $this->registra('atrib', $n->getStartLine(), $nome, $le);
            $txt .= '__rt_a(' . $id . ",'" . $nome . "',\$" . $nome . ');';
        }
        $this->emenda((int) $n->getAttribute('endFilePos') + 1, self::M . $txt . self::M);
    }

    private function chamada(Expr\FuncCall $n): void
    {
        if (!($n->name instanceof Node\Name)) {
            return;
        }
        $nome = strtolower($n->name->getLast());
        if (!isset($this->funcoes[$nome]) || (count($n->name->getParts()) > 1 && !$n->name->isFullyQualified())) {
            return;
        }
        foreach ($n->args as $a) {
            if (!($a instanceof Node\Arg) || $a->unpack) {
                return;
            }
        }
        $pai = $this->stack[count($this->stack) - 2] ?? null;
        if ($pai instanceof Expr\AssignRef) {   // `$x =& f()` exige a chamada pura
            return;
        }
        $args = [];
        foreach ($n->args as $a) {
            $v = $a->value;
            if ($v instanceof Expr\Variable && is_string($v->name)) {
                $args[] = 'isset($' . $v->name . ')?$' . $v->name . ":'__unset__'";
            } else {
                $args[] = "'__expr__'";
            }
        }
        $id = $this->registra('chamada', $n->getStartLine(), $nome, $this->variaveis($n->args));
        $this->abre($n, '__rt_c', ",'" . $nome . "',[" . implode(',', $args) . ']', $id);
    }

    private function catchSonda(Stmt\Catch_ $n): void
    {
        $primeiro = $n->stmts[0];
        $a = $this->anterior((int) $primeiro->getAttribute('startTokenPos'));
        if ($a < 0 || $this->tokenId($a) !== '{') {
            return;
        }
        $id = $this->registra('excecao', $n->getStartLine(), $n->var->name, []);
        $pos = $this->tokPos[$a] + 1;
        $this->emenda($pos, self::M . '__rt_x(' . $id . ',$' . $n->var->name . ');' . self::M);
    }
}
