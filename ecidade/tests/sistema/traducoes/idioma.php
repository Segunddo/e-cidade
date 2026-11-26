<?php
// Onde o Laravel procura os arquivos de idioma e o que o tradutor devolve, com o app real do PR (bootstrap/app.php + kernel).
// Roda no 7.4 (Laravel 8) e no 8.5 (Laravel 13), sem banco.
chdir('/app');
require '/app/vendor/autoload.php';
$app = require '/app/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
echo 'locale: ', $app->getLocale(), ' | fallback: ', config('app.fallback_locale'), "\n";
echo 'path.lang: ', var_export($app['path.lang'], true), "\n";
echo 'langPath(): ', var_export($app->langPath(), true), "\n";
foreach (['validation.required' => [], 'auth.failed' => [], 'auth.throttle' => ['seconds' => 5], 'passwords.reset' => [], 'passwords.user' => [], 'pagination.next' => [], 'pagination.previous' => []] as $k => $r) {
    echo str_pad($k, 22), trans($k, $r), "\n";
}
echo 'validation.min.numeric: ', trans('validation.min.numeric', ['attribute' => 'idade', 'min' => 3]), "\n";
echo 'trans_choice: ', trans_choice('validation.size.array', 2, ['attribute' => 'itens', 'size' => 2]), "\n";
echo '__(chave inexistente): ', __('nao.existe'), "\n";
echo '__(texto livre): ', __('Texto livre'), "\n";
