<?php
// E-mails do PR sem banco e sem enviar: os 2 Mailables e o toMail da notificacao, com a configuracao real de configuration/mail.php
// (driver "array" por ENV_EXTRA), num container minimo (sem o bootstrap do app, que nao sobe no 8.5 ainda). Roda no 7.4 (SwiftMailer)
// e no 8.5 (Symfony Mailer). Dubles so para as 2 buscas no banco que os Mailables fazem; o resto e o codigo do PR.
namespace App\Domain\Configuracao\Instituicao\Model { class DBConfig { public static function find($id) { return (object) ['logo' => 'Brasao.default.png']; } } }
namespace App\Domain\Configuracao\Instituicao\Repository { class InstituicaoRepository { public function find($id) { return new class { public function getNome() { return "Prefeitura de S\xc3\xa3o Jo\xc3\xa3o"; } }; } } }
namespace {
error_reporting(E_ALL);
define('ECIDADE_PATH', '/app/');
require '/app/vendor/autoload.php';
require_once '/app/app/Helpers/Imagem.php';

use Illuminate\Container\Container;
use Illuminate\Events\Dispatcher;
use Illuminate\Filesystem\Filesystem;
use Illuminate\Mail\MailManager;
use Illuminate\View\Compilers\BladeCompiler;
use Illuminate\View\Engines\CompilerEngine;
use Illuminate\View\Engines\EngineResolver;
use Illuminate\View\Factory;
use Illuminate\View\FileViewFinder;

@mkdir('/tmp/views', 0777, true);
$app = new Illuminate\Foundation\Application('/app'); // so a classe (paths e container); sem bootstrap do kernel
Container::setInstance($app);
$app->instance('config', new Illuminate\Config\Repository(['mail' => require '/app/configuration/mail.php']));
$app->instance('events', new Dispatcher($app));
$files = new Filesystem();
$resolver = new EngineResolver();
$resolver->register('blade', function () use ($files) { return new CompilerEngine(new BladeCompiler($files, '/tmp/views')); });
$app->instance('view', new Factory($resolver, new FileViewFinder($files, ['/app/resources/views']), $app['events']));
$app->bind(Illuminate\Contracts\View\Factory::class, function () use ($app) { return $app['view']; });
$app->bind(Psr\Log\LoggerInterface::class, function () { return new Psr\Log\NullLogger(); });

$manager = new MailManager($app);
$mailer = $manager->mailer();
$simfony = class_exists('Symfony\Component\Mailer\Mailer');
$transport = $simfony ? $mailer->getSymfonyTransport() : $mailer->getSwiftMailer()->getTransport();
echo 'transporte: ', $simfony ? 'Symfony ' : 'Swift ', (new ReflectionClass($transport))->getShortName(), "\n";
echo 'remetente padrao: ', json_encode($app['config']['mail.from']), "\n";

function normaliza($s) {
    $s = preg_replace('/^(Message-ID|Date|Content-ID): .*$/mi', '$1: <normalizado>', $s);
    $s = preg_replace('/cid:[^"\s>]+/', 'cid:NORM', $s);
    if (preg_match_all('/boundary="?([^"\s;]+)"?/', $s, $m)) { foreach (array_unique($m[1]) as $i => $b) { $s = str_replace($b, "LIMITE$i", $s); } }
    return str_replace("\r\n", "\n", $s);
}
function envia($rotulo, $mailable) {
    global $mailer, $transport, $simfony;
    if (method_exists($transport, 'flush')) { $transport->flush(); }
    try { $mailer->send($mailable); } catch (Throwable $e) { echo "== $rotulo\nEXCECAO ", get_class($e), ': ', $e->getMessage(), "\n"; return; }
    foreach ($transport->messages() as $m) {
        echo "== $rotulo\n";
        $raw = $simfony ? $m->getOriginalMessage()->toString() : $m->toString();
        echo normaliza($raw), "\n";
    }
}
// 1. Notificacao de acordo: o que o toMail monta (Mailable NotificacaoAcordoVencimento)
$n = (new ReflectionClass(App\Notifications\UserNotificationAcordoVencimento::class))->newInstanceWithoutConstructor();
$n->instituicao_id = 1; $n->title = "Acordo 12/2026 vence em 5 dias"; $n->message = "O acordo n\xc2\xba 12 vence em 25/11/2026 (a\xc3\xa7\xc3\xa3o necess\xc3\xa1ria).";
$dest = (object) ['nome' => "Jos\xc3\xa9 da Silva", 'email' => 'jose@example.org'];
echo 'via: ', json_encode($n->via($dest)), "\n";
envia('NotificacaoAcordoVencimento (toMail)', $n->toMail($dest));
// 2. Redesim: Mail::send do RedesimService
$erro = new Exception('Falha ao processar o estabelecimento <b>99</b> & cia');
envia('RedesimErrorToProcessEstablishmentsMail', new App\Mail\RedesimErrorToProcessEstablishmentsMail('12.345.678/0001-90', $erro));
// 3. sem REDESIM_MAIL_ADDRESS_ON_ERROR o build() recusa
putenv('REDESIM_MAIL_ADDRESS_ON_ERROR='); $_ENV['REDESIM_MAIL_ADDRESS_ON_ERROR'] = ''; $_SERVER['REDESIM_MAIL_ADDRESS_ON_ERROR'] = '';
envia('Redesim sem destinatario', new App\Mail\RedesimErrorToProcessEstablishmentsMail('1', $erro));
// 4. Mail::raw
if (method_exists($mailer, 'raw')) {
    if (method_exists($transport, 'flush')) { $transport->flush(); }
    $mailer->raw("Texto simples com acentua\xc3\xa7\xc3\xa3o", function ($m) { $m->to('x@example.org')->from('de@example.org', 'De')->subject('Assunto raw'); });
    foreach ($transport->messages() as $m) { echo "== Mail::raw\n", normaliza($simfony ? $m->getOriginalMessage()->toString() : $m->toString()), "\n"; }
}
}
