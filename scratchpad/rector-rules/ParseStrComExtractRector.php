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
 *
 * COMO FAZ: visita cada instrucao-expressao (Expression); se ela e exatamente uma
 * chamada `parse_str(<x>);` com UM argumento posicional, acrescenta `$__qs` como 2o
 * argumento e devolve DUAS instrucoes no lugar da original: a chamada alterada e
 * `extract($__qs);`. parse_str usada dentro de outra expressao (ex.: `$r = parse_str(..)`)
 * nao e tocada -- e parse_str devolve void, entao esse uso nao aparece na pratica.
 * O nome `$__qs` e fixo: duas chamadas no mesmo escopo reaproveitam a variavel, o que
 * e inofensivo porque cada parse_str a sobrescreve antes do seu extract.
 *
 * ONDE E USADO: passo 4 do guia, carregada por scratchpad/rector-curado.php
 * (require_once + withRules); o rector_lote.py a lista como "conhecida". Substitui a
 * nativa ParseStrWithResultArgumentRector, que esta na denylist. Roda no PHP 8.5
 * dentro do Rector; o codigo emitido roda nos dois runtimes (parse_str com 2
 * argumentos e extract existem no 5.6).
 * Efeito: reescreve os arquivos-alvo (so sem --dry-run).
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
     * Recebe um Expression. Devolve null (nada a fazer) ou um array de instrucoes, que o
     * Rector poe no lugar da original -- e assim que uma instrucao vira duas.
     *
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

        // Reaproveita o Expression ORIGINAL em vez de criar um novo. Um no novo nasce
        // sem atributos, e os comentarios ficam presos ao no antigo -- o Rector os
        // descarta em silencio. Medido: 3 arquivos perderam linhas como
        // "//---  parser POST/GET" e codigo comentado acima da chamada.
        $node->expr = $chamada;

        return [
            $node,
            new Expression(new FuncCall(new Name('extract'), [new Arg(clone $resultado)])),
        ];
    }
}
