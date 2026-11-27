<?php
// Instrumentador: le caminhos relativos (um por linha) em stdin, relativos a --raiz, e grava em --saida
// a copia instrumentada (+ <arquivo>.map.json). Uma linha JSON por arquivo em stdout:
//   {"arquivo":..., "status":"ok|sem_parse|conflito_marcador|erro", "sondas":N}
// Uso: php instrumentador.php --raiz=/var/www/html --saida=/var/www/html/tmp/ecidade-rastro [--funcoes=arq]
require __DIR__ . '/autoload.php';
require __DIR__ . '/sondas.php';

use PhpParser\Lexer\Emulative;
use PhpParser\NodeTraverser;
use PhpParser\ParserFactory;

$o = getopt('', ['raiz:', 'saida:', 'funcoes::']);
$raiz = rtrim($o['raiz'] ?? '', '/');
$saida = rtrim($o['saida'] ?? '', '/');
if ($raiz === '' || $saida === '') {
    fwrite(STDERR, "uso: php instrumentador.php --raiz=DIR --saida=DIR [--funcoes=ARQ]\n");
    exit(2);
}
$arqFuncoes = $o['funcoes'] ?? (__DIR__ . '/../funcoes.txt');
$funcoes = [];
foreach (file($arqFuncoes, FILE_IGNORE_NEW_LINES) ?: [] as $l) {
    $l = strtolower(trim($l));
    if ($l !== '' && $l[0] !== '#') {
        $funcoes[$l] = true;
    }
}

$lexer = new Emulative(['usedAttributes' => ['comments', 'startLine', 'endLine', 'startTokenPos', 'endTokenPos', 'startFilePos', 'endFilePos']]);
$parser = (new ParserFactory)->create(ParserFactory::PREFER_PHP7, $lexer);

function grava(string $caminho, string $conteudo): void
{
    $dir = dirname($caminho);
    if (!is_dir($dir)) {
        @mkdir($dir, 0777, true);
    }
    file_put_contents($caminho, $conteudo);
}

while (($arq = fgets(STDIN)) !== false) {
    $arq = rtrim($arq, "\r\n");
    if ($arq === '') {
        continue;
    }
    $fonte = @file_get_contents("$raiz/$arq");
    if ($fonte === false) {
        echo json_encode(['arquivo' => $arq, 'status' => 'erro', 'sondas' => 0]) . "\n";
        continue;
    }
    $status = 'ok';
    $n = 0;
    $saidaTexto = $fonte;
    if (strpos($fonte, '/*R*/') !== false) {
        $status = 'conflito_marcador';
    } else {
        try {
            $ast = $parser->parse($fonte);
            $tokens = $lexer->getTokens();
            $pos = [];
            $p = 0;
            foreach ($tokens as $i => $t) {
                $pos[$i] = $p;
                $p += strlen(is_array($t) ? $t[1] : $t);
            }
            $v = new Sondas($fonte, $tokens, $pos, $funcoes);
            $t = new NodeTraverser();
            $t->addVisitor($v);
            $t->traverse($ast);
            $saidaTexto = $v->aplica();
            $n = $v->sondas();
            if ($n > 0) {
                grava("$saida/$arq.map.json", json_encode($v->mapa(), JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE));
            }
        } catch (\Throwable $e) {
            $status = 'sem_parse';
            $saidaTexto = $fonte;
            $n = 0;
            $msg = get_class($e) . ': ' . substr($e->getMessage(), 0, 200) . ' @' . basename($e->getFile()) . ':' . $e->getLine();
        }
    }
    grava("$saida/$arq", $saidaTexto);
    $linha = ['arquivo' => $arq, 'status' => $status, 'sondas' => $n];
    if (isset($msg)) {
        $linha['msg'] = $msg;
        unset($msg);
    }
    echo json_encode($linha) . "\n";
}
