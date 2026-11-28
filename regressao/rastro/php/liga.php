<?php
// Cria/remove links simbolicos na arvore instrumentada para tudo que NAO e instrumentado (assets, vendor/,
// tmp/, .php excluidos...), de modo que a copia funcione sozinha sem duplicar centenas de MB.
// stdin: uma instrucao por linha:  "+<rel>"  link  saida/<rel> -> raiz/<rel>
//                                 "-<rel>"  remove saida/<rel>
// Uso: php liga.php --raiz=/var/www/html --saida=/var/www/html/tmp/ecidade-rastro
$o = getopt('', ['raiz:', 'saida:']);
$raiz = rtrim($o['raiz'] ?? '', '/');
$saida = rtrim($o['saida'] ?? '', '/');
if ($raiz === '' || $saida === '') {
    fwrite(STDERR, "uso: php liga.php --raiz=DIR --saida=DIR\n");
    exit(2);
}
$feitos = 0;

/** O diretorio so contem links simbolicos (em qualquer nivel)? Nunca apagamos o que nao for link. */
function soTemLinks(string $dir): bool
{
    foreach (scandir($dir) as $n) {
        if ($n === '.' || $n === '..') {
            continue;
        }
        $p = "$dir/$n";
        if (is_link($p)) {
            continue;
        }
        if (!is_dir($p) || !soTemLinks($p)) {
            return false;
        }
    }
    return true;
}

function apagaLinks(string $dir): void
{
    foreach (scandir($dir) as $n) {
        if ($n === '.' || $n === '..') {
            continue;
        }
        $p = "$dir/$n";
        is_link($p) ? @unlink($p) : apagaLinks($p);
    }
    @rmdir($dir);
}

while (($l = fgets(STDIN)) !== false) {
    $l = rtrim($l, "\r\n");
    if ($l === '') {
        continue;
    }
    $op = $l[0];
    $rel = substr($l, 1);
    $dest = "$saida/$rel";
    if ($op === '+') {
        if (is_dir($dest) && !is_link($dest) && soTemLinks($dest)) {
            apagaLinks($dest);   // diretorio real so de links (herdado de uma versao anterior) cede lugar ao link do diretorio inteiro
        }
        if (is_link($dest) || file_exists($dest)) {
            continue;
        }
        $dir = dirname($dest);
        if (!is_dir($dir)) {
            @mkdir($dir, 0777, true);
        }
        if (@symlink("$raiz/$rel", $dest)) {
            $feitos++;
        }
    } elseif ($op === '-') {
        if (is_link($dest) || is_file($dest)) {
            @unlink($dest);
            $feitos++;
        }
    }
}
echo json_encode(['feitos' => $feitos]) . "\n";
