<?php
declare(strict_types=1);

namespace ECidade\RectorRules;

use PhpParser\Node;
use PhpParser\Node\Arg;
use PhpParser\Node\Expr\FuncCall;
use PhpParser\Node\Expr\Variable;
use PhpParser\Node\Name;
use PhpParser\Node\Stmt\Expression;
use Rector\Rector\AbstractRector;
use Symplify\RuleDocGenerator\ValueObject\CodeSample\CodeSample;
use Symplify\RuleDocGenerator\ValueObject\RuleDefinition;

/**
 * O 2o argumento de parse_str() e obrigatorio desde o PHP 8.0.
 *
 * A regra NATIVA do Rector (ParseStrWithResultArgumentRector) acrescenta so o
 * argumento -- e as variaveis que o codigo legado importava do query string
 * DESAPARECEM do escopo, sem erro e sem aviso. Medido no 5.6:
 *
 *     parse_str($s);           ->  $foo existe no escopo
 *     parse_str($s, $result);  ->  $foo NAO existe; so $result
 *
 * Esta regra acrescenta o extract() junto, restaurando o escopo.
 */
final class ParseStrComExtractRector extends AbstractRector
{
    public function getRuleDefinition(): RuleDefinition
    {
        return new RuleDefinition(
            'parse_str() de 1 argumento -> 2 argumentos + extract(), preservando o escopo',
            [new CodeSample('parse_str($s);', 'parse_str($s, $__qs);' . "\n" . 'extract($__qs);')]
        );
    }

    public function getNodeTypes(): array
    {
        return [Expression::class];
    }

    /**
     * @return Node[]|null
     */
    public function refactor(Node $node): ?array
    {
        if (!$node->expr instanceof FuncCall) {
            return null;
        }
        $chamada = $node->expr;
        if (!$this->isName($chamada, 'parse_str') || count($chamada->args) !== 1) {
            return null;
        }
        // arg desempacotado ou nomeado: fora do escopo desta regra
        if (!$chamada->args[0] instanceof Arg) {
            return null;
        }

        $resultado = new Variable('__qs');
        $chamada->args[] = new Arg($resultado);

        return [
            new Expression($chamada),
            new Expression(new FuncCall(new Name('extract'), [new Arg(clone $resultado)])),
        ];
    }
}
