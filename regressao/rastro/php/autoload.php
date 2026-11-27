<?php
// Autoloader minimo so do nikic/php-parser (PSR-4 `PhpParser\` -> lib/PhpParser). O autoload completo do
// e-Cidade carrega o sistema inteiro e enche a saida de avisos de depreciacao.
error_reporting(E_ALL & ~E_DEPRECATED);
spl_autoload_register(function (string $classe): void {
    if (strncmp($classe, 'PhpParser\\', 10) === 0) {
        $arq = '/var/www/html/vendor/nikic/php-parser/lib/' . str_replace('\\', '/', $classe) . '.php';
        if (is_file($arq)) {
            require $arq;
        }
    }
});
