<?php
// env() fora de configuration/: com a configuracao em cache o .env nao e carregado. Mede no Application real.
require '/app/vendor/autoload.php';
$app = new Illuminate\Foundation\Application('/app');
$f = new ReflectionMethod(Illuminate\Foundation\Bootstrap\LoadEnvironmentVariables::class, 'bootstrap');
$src = implode('', array_slice(file($f->getFileName()), $f->getStartLine() - 1, $f->getEndLine() - $f->getStartLine() + 1));
echo preg_match('/configurationIsCached\(\)\s*\)\s*\{\s*return/', $src) ? "bootstrap(): volta sem carregar o .env quando a configuracao esta em cache\n" : "bootstrap(): NAO ha retorno antecipado com configuracao em cache\n";
echo 'Illuminate\Foundation\Application ', Illuminate\Foundation\Application::VERSION, "\n";
