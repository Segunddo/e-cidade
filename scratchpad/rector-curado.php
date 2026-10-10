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
        Rector\Php70\Rector\FuncCall\RandomFunctionRector::class,   // random_int
        // As duas abaixo NAO estavam na denylist herdada do experimento do `div`:
        // elas nunca dispararam la. No `iss` dispararam, emitiram funcao inexistente
        // no 5.6 e passaram batido pelo php -l. E a fragilidade da denylist, medida.
        Rector\Php80\Rector\NotIdentical\StrContainsRector::class,  // str_contains (PHP 8.0)
        Rector\Php73\Rector\FuncCall\ArrayKeyFirstLastRector::class, // array_key_first (PHP 7.3)
                                                                      // e ainda remove o reset(),
                                                                      // mudando o ponteiro do array

        // --- mudam COMPORTAMENTO, nao sao migracao ---
        // popula valores hoje vazios (os $HTTP_*_VARS estao indefinidos desde o 5.4)
        Rector\Php53\Rector\Variable\ReplaceHttpServerVarsByServerRector::class,
        // acrescenta 2o argumento SEM extract(): as variaveis somem do escopo, em silencio
        Rector\Php72\Rector\FuncCall\ParseStrWithResultArgumentRector::class,
    ]);
