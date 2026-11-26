<?php
// configuration/mail.php do PR lida pelo MailManager: que transporte e que parametros saem de cada MAIL_DRIVER / MAIL_ENCRYPTION.
// Nada se conecta: so cria o transporte e le host, porta e criptografia.
define('ECIDADE_PATH', '/app/');
require '/app/vendor/autoload.php';
use Illuminate\Foundation\Application;
use Illuminate\Mail\MailManager;

Illuminate\Container\Container::setInstance(new Application('/app')); // resource_path() do arquivo de configuracao
$base = require '/app/configuration/mail.php';
$cenarios = [
    'smtp tls 587' => ['driver' => 'smtp', 'host' => 'smtp.exemplo.invalid', 'port' => 587, 'encryption' => 'tls', 'username' => 'u', 'password' => 'p'],
    'smtp ssl 465' => ['driver' => 'smtp', 'host' => 'smtp.exemplo.invalid', 'port' => 465, 'encryption' => 'ssl', 'username' => 'u', 'password' => 'p'],
    'smtp sem criptografia 25' => ['driver' => 'smtp', 'host' => 'smtp.exemplo.invalid', 'port' => 25, 'encryption' => null, 'username' => null, 'password' => null],
    'smtp padrao do arquivo' => ['driver' => 'smtp'],
    'log' => ['driver' => 'log'],
    'array' => ['driver' => 'array'],
    'sendmail' => ['driver' => 'sendmail', 'sendmail' => '/usr/sbin/sendmail -bs'],
    'mail (funcao mail() do PHP)' => ['driver' => 'mail'],
];
$simfony = class_exists('Symfony\Component\Mailer\Mailer');
foreach ($cenarios as $nome => $over) {
    $app = new Application('/app');
    $app->instance('config', new Illuminate\Config\Repository(['mail' => array_merge($base, $over), 'logging' => ['default' => 'null', 'channels' => ['null' => ['driver' => 'monolog', 'handler' => Monolog\Handler\NullHandler::class]]]]));
    $app->instance('events', new Illuminate\Events\Dispatcher($app));
    $files = new Illuminate\Filesystem\Filesystem();
    $resolver = new Illuminate\View\Engines\EngineResolver();
    $app->instance('view', new Illuminate\View\Factory($resolver, new Illuminate\View\FileViewFinder($files, ['/app/resources/views']), $app['events']));
    $app->bind(Psr\Log\LoggerInterface::class, function () { return new Psr\Log\NullLogger(); });
    try {
        $mailer = (new MailManager($app))->mailer();
        $t = $simfony ? $mailer->getSymfonyTransport() : $mailer->getSwiftMailer()->getTransport();
        $linha = (new ReflectionClass($t))->getShortName();
        if ($t instanceof Swift_SmtpTransport) {
            $linha .= sprintf(' host=%s porta=%s criptografia=%s usuario=%s', $t->getHost(), $t->getPort(), var_export($t->getEncryption(), true), var_export($t->getUsername(), true));
        } elseif ($t instanceof Symfony\Component\Mailer\Transport\Smtp\EsmtpTransport) {
            $s = $t->getStream();
            $linha .= sprintf(' host=%s porta=%s criptografia=%s usuario=%s', $s->getHost(), $s->getPort(), var_export($s->isTLS() ? 'tls-implicito' : null, true), var_export($t->getUsername(), true));
        }
    } catch (Throwable $e) {
        $linha = 'EXCECAO ' . get_class($e) . ': ' . substr($e->getMessage(), 0, 80);
    }
    echo str_pad($nome, 30), ' -> ', $linha, "\n";
}
