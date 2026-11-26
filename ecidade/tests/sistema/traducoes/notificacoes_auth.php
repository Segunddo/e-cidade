<?php
// Textos de e-mail do proprio framework (ResetPassword, VerifyEmail) com locale pt-br: usam __() sobre chaves em ingles (JSON), que o PR nao traduz.
// App real do PR, sem banco e sem enviar.
chdir('/app');
require '/app/vendor/autoload.php';
$app = require '/app/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$u = new class { public $email = 'a@example.org'; function getEmailForPasswordReset() { return 'a@example.org'; } function routeNotificationFor() { return 'a@example.org'; } function getKey() { return 1; } function getEmailForVerification() { return 'a@example.org'; } };
Illuminate\Auth\Notifications\ResetPassword::createUrlUsing(function () { return 'http://localhost/reset'; });
Illuminate\Auth\Notifications\VerifyEmail::createUrlUsing(function () { return 'http://localhost/verify'; });
foreach ([new Illuminate\Auth\Notifications\ResetPassword('tok'), new Illuminate\Auth\Notifications\VerifyEmail()] as $n) {
    $m = $n->toMail($u);
    echo (new ReflectionClass($n))->getShortName(), "\n  assunto: ", $m->subject, "\n  introducao: ", json_encode($m->introLines), "\n  acao: ", $m->actionText, "\n  final: ", json_encode($m->outroLines), "\n";
}
