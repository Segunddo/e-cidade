<?php
declare(strict_types=1);

namespace ECidade\RectorRules;

use PhpParser\Node;
use PhpParser\Node\Expr;
use PhpParser\Node\Expr\BinaryOp\Div;
use PhpParser\Node\Expr\BinaryOp\Equal;
use PhpParser\Node\Expr\BinaryOp\Greater;
use PhpParser\Node\Expr\BinaryOp\Smaller;
use PhpParser\Node\Expr\Cast\Double;
use PhpParser\Node\Expr\ConstFetch;
use PhpParser\Node\Expr\Ternary;
use PhpParser\Node\Expr\UnaryMinus;
use PhpParser\Node\Name;
use PhpParser\Node\Scalar\LNumber;
use Rector\Rector\AbstractRector;
use Symplify\RuleDocGenerator\ValueObject\CodeSample\CodeSample;
use Symplify\RuleDocGenerator\ValueObject\RuleDefinition;

/**
 * No 7.4, `A / 0` so avisava e devolvia INF, -INF ou NAN (0/0); no 8.0 e DivisionByZeroError.
 * Reproduz o 7.4 nos dois runtimes:
 *     A / B  ->  ((float) B == 0 ? ((float) A > 0 ? INF : ((float) A < 0 ? -INF : NAN)) : A / B)
 * Com B != 0 a conta e a mesma. So quando A e B sao "puros" (variavel, propriedade, indice, literal, cast,
 * aritmetica entre puros): A e B passam a ser avaliados mais de uma vez.
 */
final class DivisaoComoNo74Rector extends AbstractRector
{
    public function getRuleDefinition(): RuleDefinition
    {
        return new RuleDefinition('A / B como no PHP 7.4 (INF/NAN em vez de DivisionByZeroError)',
            [new CodeSample('$a / $b', '((float) $b == 0 ? ((float) $a > 0 ? INF : ((float) $a < 0 ? -INF : NAN)) : $a / $b)')]);
    }

    public function getNodeTypes(): array
    {
        return [Ternary::class, Div::class];
    }

    private static function puro(Expr $e): bool
    {
        if ($e instanceof Expr\Variable) return is_string($e->name);
        if ($e instanceof Expr\PropertyFetch) return self::puro($e->var) && $e->name instanceof Node\Identifier;
        if ($e instanceof Expr\ArrayDimFetch) return self::puro($e->var) && ($e->dim === null || self::puro($e->dim));
        if ($e instanceof Node\Scalar) return true;
        if ($e instanceof ConstFetch) return true;
        if ($e instanceof Expr\Cast) return self::puro($e->expr);
        if ($e instanceof UnaryMinus || $e instanceof Expr\UnaryPlus) return self::puro($e->expr);
        if ($e instanceof Expr\BinaryOp) return self::puro($e->left) && self::puro($e->right);
        if ($e instanceof Expr\ErrorSuppress) return self::puro($e->expr);
        return false;
    }

    private static function jaGuardada(Ternary $t): bool
    {
        return $t->else instanceof Div && $t->cond instanceof Equal && $t->cond->left instanceof Double;
    }

    public function refactor(Node $node): ?Node
    {
        if ($node instanceof Ternary) {
            // marca a divisao interna da propria guarda para nao reprocessar
            if (self::jaGuardada($node)) {
                $node->else->setAttribute('guardada74', true);
            }
            return null;
        }
        /** @var Div $node */
        if ($node->getAttribute('guardada74') || $node->right instanceof Node\Scalar\LNumber && $node->right->value !== 0
            || $node->right instanceof Node\Scalar\DNumber && $node->right->value != 0) {
            return null; // divisor literal nao nulo: nunca divide por zero
        }
        if (!self::puro($node->left) || !self::puro($node->right)) {
            return null;
        }
        $a = $node->left;
        $b = $node->right;
        $div = new Div($a, $b);
        $div->setAttribute('guardada74', true);
        $inf = new ConstFetch(new Name('INF'));
        $nan = new ConstFetch(new Name('NAN'));
        $sinal = new Ternary(new Greater(new Double(clone $a, ["kind" => Double::KIND_FLOAT]), new LNumber(0)), $inf,
            new Ternary(new Smaller(new Double(clone $a, ["kind" => Double::KIND_FLOAT]), new LNumber(0)), new UnaryMinus(clone $inf), $nan));
        return new Ternary(new Equal(new Double(clone $b, ["kind" => Double::KIND_FLOAT]), new LNumber(0)), $sinal, $div);
    }
}
