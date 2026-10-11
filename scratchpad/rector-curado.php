<?php
/**
 * Config CURADA do Rector para o e-cidade.
 *
 * Parte dos conjuntos por versao (o "grupo (a)" da taxonomia do TCC de referencia:
 * so o que a versao de destino EXIGE) e exclui 14 regras, cada uma com motivo medido.
 * A restricao central do projeto e que o MESMO arquivo precisa rodar em PHP 5.6 e 8.5,
 * porque os dois containers montam o mesmo diretorio.
 *
 * Uso (de dentro do container 8.5):
 *   ALVOS=/var/www/html/tmp/iss_alvos.txt \
 *   tmp/rector/vendor/bin/rector process --config scratchpad/rector-curado.php --dry-run
 */
require_once __DIR__ . '/rector-rules/GuardaComparacaoLiteralRector.php';
require_once __DIR__ . '/rector-rules/ParseStrComExtractRector.php';

use ECidade\RectorRules\GuardaComparacaoLiteralRector;
use ECidade\RectorRules\ParseStrComExtractRector;
use Rector\Config\RectorConfig;
use Rector\ValueObject\PhpVersion;

$lista = getenv('ALVOS') ?: '/var/www/html/tmp/iss_alvos.txt';
$raiz  = '/var/www/html/';
$paths = [];
foreach (file($lista, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $l) {
    $p = $raiz . trim($l);
    if (is_file($p)) { $paths[] = $p; }
}
if (!$paths) { fwrite(STDERR, "SEM ALVOS em $lista\n"); exit(2); }

return RectorConfig::configure()
    ->withPaths($paths)
    // OBRIGATORIO. Sem este pin, o Rector resolve a versao alvo do composer.json do
    // projeto (">=5.6.4") e DESLIGA EM SILENCIO toda regra com version bonding --
    // inclusive Php4ConstructorRector (122 arquivos) e EregToPregMatchRector (118).
    // O run reporta "[OK] N files would have been changed" sem nenhum aviso.
    ->withPhpVersion(PhpVersion::PHP_80)
    ->withPhpSets(php80: true)
    // As duas regras PROPRIAS: cobrem a camada semantica, que nao existe como regra
    // nativa porque nao e upgrade -- e shim que preserva a semantica do 5.6.
    ->withRules([
        GuardaComparacaoLiteralRector::class,
        ParseStrComExtractRector::class,
    ])
    ->withSkip([
        // --- emitem sintaxe de PHP 7+ -> parse error no 5.6, derruba a REFERENCIA ---
        Rector\Php74\Rector\If_\IfToNullCoalescingAssignRector::class,
        Rector\Php74\Rector\Closure\ClosureToArrowFunctionRector::class,
        Rector\Php70\Rector\Ternary\TernaryToNullCoalescingRector::class,
        Rector\Php74\Rector\Assign\NullCoalescingOperatorRector::class,
        Rector\Php71\Rector\List_\ListToArrayDestructRector::class,
        Rector\Php80\Rector\Class_\ClassPropertyAssignToConstructorPromotionRector::class,
        Rector\Php80\Rector\Switch_\ChangeSwitchToMatchRector::class,
        Rector\Php80\Rector\FuncCall\ClassOnObjectRector::class,
        Rector\Php80\Rector\Class_\StringableForToStringRector::class,
        Rector\Php80\Rector\Catch_\RemoveUnusedVariableInCatchRector::class,

        // --- emitem FUNCAO que nao existe no 5.6: compila e explode em execucao ---
        Rector\Php80\Rector\Identical\StrStartsWithRector::class,   // str_starts_with
        // 4o CRESCIMENTO da denylist (amb/pre), e a QUARTA vez que ela cresce.
        // Irma da de cima; escapou ate aqui so por nunca ter disparado. Emite
        // str_ends_with() -- PHP 8.0, MEDIDO como inexistente no 5.6. Passa no
        // php -l e e fatal so em execucao: modo de falha nº 2 do catalogo.
        Rector\Php80\Rector\Identical\StrEndsWithRector::class,        // str_ends_with
        // Reescreve `$x == ""` para `$x == 0`. NAO reproduz o 5.6 -- medido nos
        // dois runtimes, diverge em 2 dos 6 valores:
        //                5.6 `== ""`    8.5 `== 0`
        //     ""           true          FALSE    <- diverge
        //     "0"          false         TRUE     <- diverge
        // Esta categoria pertence ao GuardaComparacaoLiteralRector, que e fiel.
        Rector\Php71\Rector\BinaryOp\BinaryOpBetweenNumberAndStringRector::class,

        // 5o CRESCIMENTO (cad). A mais PERIGOSA achada ate aqui.
        // RemoveExtraParameters APAGA argumentos reais quando a chamada passa mais
        // do que a assinatura declara. Em cad1_ruas003.php ela produziu:
        //     $cllogradcep->excluir("","","j65_lograd=$j14_codigo");
        //  -> $cllogradcep->excluir("","");          <- o WHERE do DELETE SUMIU
        // e em cad1_aba2ruas001.php apagou os dois argumentos de um incluir().
        // MEDIDO: o PHP 8.5 ainda ACEITA argumentos extras em funcao de usuario
        // (func_num_args() devolve 3 nos dois runtimes), entao a regra nao e
        // exigida pela versao de destino -- e limpeza, e limpeza que apaga SQL.
        Rector\Php71\Rector\FuncCall\RemoveExtraParametersRector::class,
        // Transformou a constante indefinida `l` em `\L` (maiuscula e totalmente
        // qualificada) em classes/db_averbacao_classe.php. Muda o VALOR: no 5.6
        // uma constante indefinida vira a string do proprio nome, "l" -- nao "L".
        Rector\Php73\Rector\ConstFetch\SensitiveConstantNameRector::class,
        // `($x)?$x:' '` -> `$x ?: ' '`. Parseia nos dois e e equivalente, mas e
        // modernizacao (grupo "c"), e o foco declarado nao e modernizar.
        Rector\Php53\Rector\Ternary\TernaryToElvisRector::class,
        Rector\Php70\Rector\FuncCall\RandomFunctionRector::class,   // random_int
        // As duas abaixo NAO estavam na denylist herdada do experimento do `div`:
        // elas nunca dispararam la. No `iss` dispararam, emitiram funcao inexistente
        // no 5.6 e passaram batido pelo php -l. E a fragilidade da denylist, medida.
        Rector\Php80\Rector\NotIdentical\StrContainsRector::class,  // str_contains (PHP 8.0)
        Rector\Php73\Rector\FuncCall\ArrayKeyFirstLastRector::class, // array_key_first (PHP 7.3)
        // Terceira rodada da mesma licao: esta regra nunca disparou no div nem no iss,
        // e disparou no dvr. Emite `$x ?? null`, e o ?? e PHP 7.0 -> PARSE ERROR no 5.6.
        // (Medido: `$x["k"] ?? null` nao parseia no 5.6 e parseia no 8.5.)
        Rector\Php70\Rector\StmtsAwareInterface\IfIssetToCoalescingRector::class,

        // --- MODERNIZACAO: nao e exigida pela versao de destino -------------------
        // No `iss` estas quatro responderam por 77% do diff (6.480 de 8.409 linhas) e
        // zero da migracao. Medido que desliga-las NAO custa nada obrigatorio: split,
        // spliti, ereg*, offsets {} e create_function sao convertidos por regras
        // dedicadas, nao por estas.
        Rector\Renaming\Rector\FuncCall\RenameFunctionRector::class,        // pg_numrows -> pg_num_rows
        Rector\Php52\Rector\Property\VarToPublicPropertyRector::class,      // var $x -> public $x
        Rector\Visibility\Rector\ClassMethod\ExplicitPublicClassMethodRector::class,
        Rector\Php54\Rector\Array_\LongArrayToShortArrayRector::class,      // array() -> []

        // --- each(): o foreach NAO e equivalente ----------------------------------
        // O e-cidade tem laços que dependem do ponteiro interno ja exaurido por um
        // laco anterior, e que por isso NUNCA executam (ver db_libpessoal.php no
        // CLAUDE.md). Trocar por foreach faz o segundo laco rodar -- mudanca
        // silenciosa de comportamento. O Rector nao tem como ver o reset() anterior.
        // Tratar a mao, com key()/current()/next(), conferindo o contexto.
        Rector\Php72\Rector\While_\WhileEachToForeachRector::class,
        Rector\Php72\Rector\Assign\ListEachRector::class,
                                                                      // e ainda remove o reset(),
                                                                      // mudando o ponteiro do array

        // --- mudam COMPORTAMENTO, nao sao migracao ---
        // popula valores hoje vazios (os $HTTP_*_VARS estao indefinidos desde o 5.4)
        Rector\Php53\Rector\Variable\ReplaceHttpServerVarsByServerRector::class,
        // acrescenta 2o argumento SEM extract(): as variaveis somem do escopo, em silencio
        Rector\Php72\Rector\FuncCall\ParseStrWithResultArgumentRector::class,
    ]);
