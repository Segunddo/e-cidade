<?php
// E_DEPRECATED excluido como faz config/application.php:27 -- o vendor/ emite
// dezenas delas no PHP 8 e elas nao sao objeto desta verificacao.
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
// Uso: php scratchpad/instancia_classes.php <arquivo com a lista de classes>
// Instancia cada classe do universo do modulo e imprime uma assinatura do estado
// inicializado. Rodado nos DOIS runtimes, o diff prova que os construtores
// renomeados (PHP4 -> __construct) continuam executando e produzindo o mesmo estado.
chdir('/var/www/html');
// bootstrap.php registra o autoloader do namespace ECidade\, sem o qual
// modification() falha -- ele nao esta no psr-4 do composer.json.
require_once('bootstrap.php');
require_once('definitions.php');
require_once(modification("libs/db_stdlib.php"));
// db_conecta exige sessao valida ("Sessao invalida (12)") e a instanciacao das
// classes nao depende de conexao -- o que se compara aqui e o ESTADO INICIAL
// que o construtor produz.
$n_ok = 0;
foreach (explode("\n", trim(file_get_contents($argv[1]))) as $arq) {
    if (!$arq) continue;
    if (!preg_match('/class\s+(\w+)/i', file_get_contents($arq), $m)) continue;
    $cls = $m[1];
    if (!class_exists($cls)) { @include_once(modification($arq)); }
    if (!class_exists($cls)) { echo "$arq\tSEM_CLASSE\n"; continue; }
    try {
        $o = new $cls();
        $v = get_object_vars($o); ksort($v);
        // Assinatura SEM serialize(): no PHP 8 serializar um objeto interno como
        // DOMElement e fatal (no 5.6 era permitido), e isso quebrava o proprio
        // instrumento de medicao. Objetos entram pelo nome da classe.
        $sig = "";
        foreach ($v as $k => $x) {
            $sig .= $k . "=" . (is_object($x) ? "<" . get_class($x) . ">"
                              : (is_array($x) ? "[" . count($x) . "]"
                              : var_export($x, true))) . ";";
        }
        echo "$arq\t$cls\t" . count($v) . "\t" . md5($sig) . "\n"; $n_ok++;
    } catch (Throwable $e) {
        echo "$arq\t$cls\tERRO\t" . get_class($e) . ": " . $e->getMessage() . " @ " . $e->getFile() . ":" . $e->getLine() . "\n";
    }
}

// Guarda contra o falso "passou": um diff de dois arquivos VAZIOS reporta zero
// divergencias. Ja aconteceu duas vezes. Se nada foi instanciado, grita.
if (!isset($n_ok) || $n_ok === 0) { fwrite(STDERR, "SEM_SAIDA: nenhuma classe instanciada\n"); exit(2); }
