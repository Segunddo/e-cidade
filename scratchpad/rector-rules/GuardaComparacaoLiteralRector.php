<?php
declare(strict_types=1);

namespace ECidade\RectorRules;

use PhpParser\Node;
use PhpParser\Node\Expr\BinaryOp\BooleanOr;
use PhpParser\Node\Expr\BinaryOp\Equal;
use PhpParser\Node\Expr\BinaryOp\Identical;
use PhpParser\Node\Expr\PropertyFetch;
use PhpParser\Node\Expr\Variable;
use PhpParser\Node\Scalar\DNumber;
use PhpParser\Node\Scalar\LNumber;
use PhpParser\Node\Scalar\String_;
use PhpParser\Node\Stmt\Class_;
use PhpParser\NodeVisitor;
use Rector\Rector\AbstractRector;
use Symplify\RuleDocGenerator\ValueObject\CodeSample\CodeSample;
use Symplify\RuleDocGenerator\ValueObject\RuleDefinition;

/**
 * No PHP 5.6 `0 == ""` era true; no PHP 8 e false (RFC "Saner string to number
 * comparisons"). O e-cidade usa `$this->X == "" ? le_do_POST : mantem` em toda
 * classe de dados, com $X declarada como inteiro -- no PHP 8 o POST nunca e lido.
 *
 * Esta regra NAO e um upgrade: e um shim que preserva a semantica do 5.6 nos DOIS
 * runtimes. Por isso nao existe equivalente no Rector.
 *
 *     $this->X == ""  ->  ($this->X === 0 || $this->X === 0.0 || $this->X == "")
 *
 * Literal numerico ("0", "5") fica intocado: `0 == "0"` ja era true nas duas versoes.
 *
 * COMO FAZ: visita cada classe; junta as propriedades cujo valor padrao e um literal
 * INTEIRO (LNumber) -- a forma como as classes db_*_classe.php declaram campos inteiros;
 * e, so dentro dessa classe, troca cada `$this->X == "literal nao numerico"` (X numa
 * dessas propriedades) pela guarda acima. `=== 0 || === 0.0` reproduz o que o 5.6 dava
 * para um 0 inteiro ou float; o `== ""` original fica no fim para os demais valores.
 * Nao trata a forma negada `!=` (essa e medida no passo 6c do verifica_lote.py e
 * corrigida caso a caso, negada_corrige.py), nem o literal do lado esquerdo, nem
 * propriedade de outro objeto.
 *
 * ONDE E USADO: passo 4 do guia, carregada por scratchpad/rector-curado.php
 * (require_once + withRules). O rector_lote.py a lista como "conhecida". Roda no PHP
 * 8.5 dentro do Rector; o CODIGO que ela emite roda nos dois runtimes.
 * Efeito: reescreve as comparacoes nos arquivos-alvo (so sem --dry-run).
 */
final class GuardaComparacaoLiteralRector extends AbstractRector
{
    public function getRuleDefinition(): RuleDefinition
    {
        return new RuleDefinition(
            'Guarda comparacao de propriedade inteira com literal nao-numerico',
            [new CodeSample('$this->x == ""', '($this->x === 0 || $this->x === 0.0 || $this->x == "")')]
        );
    }

    // Visita a CLASSE (e nao o Equal) porque a decisao depende do conjunto de
    // propriedades inteiras da classe, que so e visivel a partir do no Class_.
    public function getNodeTypes(): array
    {
        return [Class_::class];
    }

    /** A comparacao ja esta embrulhada por esta propria regra? */
    private static function ehGuarda(BooleanOr $no): bool
    {
        if (!$no->left instanceof BooleanOr) {
            return false;
        }
        $interno = $no->left;
        // deliberadamente frouxo: so exige a FORMA (duas comparacoes estritas sobre
        // a mesma propriedade). Exigir LNumber/DNumber quebra quando o printer emite
        // 0.0 como 0 -- a reparse muda o tipo do no e a barreira deixa de casar.
        return $interno->left instanceof Identical
            && $interno->left->left instanceof PropertyFetch
            && $interno->right instanceof Identical
            && $interno->right->left instanceof PropertyFetch;
    }

    /**
     * Recebe um Class_. Devolve o mesmo no (alterado no lugar) se embrulhou ao menos
     * uma comparacao, ou null se nao mudou nada (o Rector entao nao conta o arquivo).
     */
    public function refactor(Node $node): ?Node
    {
        // nomes das propriedades declaradas com padrao inteiro, ex.: `var $z01_numcgm = 0;`
        $inteiras = [];
        foreach ($node->getProperties() as $propriedade) {
            foreach ($propriedade->props as $p) {
                if ($p->default instanceof LNumber) {
                    $inteiras[$p->name->toString()] = true;
                }
            }
        }
        if ($inteiras === []) {
            return null;
        }

        $mudou = false;
        $this->traverseNodesWithCallable($node->stmts, function (Node $n) use ($inteiras, &$mudou) {
            // Barreira contra recursao infinita: a guarda que esta regra produz CONTEM
            // o Equal original. Sem isto, o Rector re-entra nela e embrulha de novo ate
            // estourar a memoria -- o processo morre com "Killed", sem traceback.
            if ($n instanceof BooleanOr && self::ehGuarda($n)) {
                return NodeVisitor::DONT_TRAVERSE_CHILDREN;
            }
            if (!$n instanceof Equal || !$n->right instanceof String_) {
                return null;
            }
            // Segunda barreira, e a que de fato segura o laco: quando enterNode devolve
            // um no substituto, o PhpParser percorre os FILHOS dele -- e o Equal original
            // esta la dentro. O no substituto nao passa por enterNode, entao a checagem
            // de forma acima nunca e alcancada. Marcar o proprio Equal resolve.
            if ($n->getAttribute('ecidade_guardado') === true) {
                return null;
            }
            $valor = $n->right->value;
            // literal numerico e seguro nos dois runtimes
            if ($valor !== '' && is_numeric(trim($valor))) {
                return null;
            }
            // so `$this->nome == ...` com nome literal (nao `$this->$var`) e de uma
            // propriedade inteira DESTA classe
            $fetch = $n->left;
            if (!$fetch instanceof PropertyFetch
                || !$fetch->var instanceof Variable
                || $fetch->var->name !== 'this'
                || !$fetch->name instanceof Node\Identifier
                || !isset($inteiras[$fetch->name->toString()])) {
                return null;
            }
            $mudou = true;
            $n->setAttribute('ecidade_guardado', true);
            // clone: cada comparacao estrita recebe o SEU PropertyFetch; o original
            // continua dentro do Equal ($n), que e reaproveitado como ultimo termo
            return new BooleanOr(
                new BooleanOr(
                    new Identical(clone $fetch, new LNumber(0)),
                    new Identical(clone $fetch, new DNumber(0.0))
                ),
                $n
            );
        });

        return $mudou ? $node : null;
    }
}
