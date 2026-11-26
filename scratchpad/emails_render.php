<?php
// Renderiza, SEM BANCO e SEM REDE, os e-mails e as notificacoes REAIS da base-php74 com o mailer "array" (nada sai).
// As classes de app/ sao as do repositorio; so o que tocaria banco (DBConfig, InstituicaoRepository, Acordo,
// MensageriaAcordoDia, Item, Relatorio) e trocado por stubs em memoria (emails_stubs.php). O mesmo script roda no 7.4 e no 8.5,
// com o vendor do Laravel 8 (PR) ou do Laravel 13; a saida e um JSON canonico, comparavel por diff.
// Uso: php emails_render.php <pasta ecidade> <saida.json> <l8|l13>   (vendor/autoload ao lado deste arquivo ou em $VENDOR)
$deprec = array();
set_error_handler(function ($no, $str, $file = '', $line = 0) use (&$deprec) {
    if ($no === E_DEPRECATED || $no === E_USER_DEPRECATED) {
        $deprec[preg_replace('#^.*/vendor/#', 'vendor/', $str) . ' @ ' . preg_replace('#^.*/(vendor|app|std|libs)/#', '$1/', $file) . ':' . $line] = true;
        return true;
    }
    return false;
});
error_reporting(E_ALL);

$raiz = rtrim($argv[1], '/');
$saida = $argv[2];
$modo = $argv[3];
$vendor = getenv('VENDOR') ?: __DIR__ . '/vendor';
require $vendor . '/autoload.php';

use Illuminate\Config\Repository;
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Facade;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Notification;

// ambiente de e-mail de exemplo (endereco fictício, nada sai)
foreach (array(
    'REDESIM_MAIL_ADDRESS_ON_ERROR' => 'erros@exemplo.invalid,outro@exemplo.invalid',
    'MAIL_FROM_ADDRESS' => 'sistema@exemplo.invalid',
    'APP_NAME' => 'e-Cidade',
) as $k => $v) {
    putenv("$k=$v");
    $_ENV[$k] = $v;
    $_SERVER[$k] = $v;
}

define('ECIDADE_PATH', sys_get_temp_dir() . '/emails_render_ecidade/');
@mkdir(ECIDADE_PATH . 'imagens/files', 0777, true);
// PNG 1x1 fixo
file_put_contents(ECIDADE_PATH . 'imagens/files/logo.png', base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=='));

require __DIR__ . '/emails_stubs.php';
require_once $raiz . '/libs/db_utils.php';
require_once $raiz . '/std/DBString.php';
require_once $raiz . '/app/Helpers/Imagem.php';

spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'App\\') === 0) {
        $f = $raiz . '/app/' . str_replace('\\', '/', substr($c, 4)) . '.php';
        if (is_file($f)) {
            require_once $f;
        }
    }
});

$tmp = sys_get_temp_dir() . '/emails_render_' . getmypid();
@mkdir($tmp . '/views', 0777, true);
$app = new Application($tmp);
$app->useStoragePath($tmp);
$app->instance('request', Illuminate\Http\Request::create('http://localhost'));
$cfgMail = include $raiz . '/configuration/mail.php';   // a configuracao REAL do PR, como esta
$saidaCfg = array('configuracao_do_pr' => array_keys($cfgMail), 'driver_do_pr' => $cfgMail['driver']);
$cfgPr = $cfgMail;
$cfgPr['driver'] = 'array';
// o Laravel 13 ainda le a chave legada 'driver' (MailManager::getDefaultDriver/getConfig), entao a configuracao do PR vale como esta
$cfgMail['driver'] = 'array';          // mailer array: nada sai
$cfgMail['from'] = array('address' => 'sistema@exemplo.invalid', 'name' => 'e-Cidade');
$app->instance('config', new Repository(array(
    'app' => array('name' => 'e-Cidade', 'env' => 'production', 'url' => 'http://localhost', 'locale' => 'pt-br', 'timezone' => 'America/Sao_Paulo', 'key' => 'base64:' . base64_encode(str_repeat('a', 32)), 'cipher' => 'AES-256-CBC'),
    'view' => array('paths' => array($raiz . '/resources/views'), 'compiled' => $tmp . '/views'),
    'mail' => $cfgMail,
    'queue' => array('default' => 'sync', 'connections' => array('sync' => array('driver' => 'sync'))),
    'broadcasting' => array('default' => 'null', 'connections' => array('null' => array('driver' => 'null'))),
)));
date_default_timezone_set('America/Sao_Paulo');
Facade::setFacadeApplication($app);
foreach (array(
    Illuminate\Filesystem\FilesystemServiceProvider::class,
    Illuminate\View\ViewServiceProvider::class,
    Illuminate\Bus\BusServiceProvider::class,
    Illuminate\Queue\QueueServiceProvider::class,
    Illuminate\Mail\MailServiceProvider::class,
    Illuminate\Notifications\NotificationServiceProvider::class,
    Illuminate\Translation\TranslationServiceProvider::class,
) as $p) {
    $app->register($p);
}

// a configuracao de e-mail do PR, como esta (so a chave 'driver' trocada por 'array'), resolve um mailer neste Laravel?
$res0 = tenta0(function () use ($app, $cfgPr) {
    $orig = $app['config']->get('mail');
    $app['config']->set('mail', $cfgPr);
    $app->forgetInstance('mail.manager');
    $app->forgetInstance('mailer');
    try {
        $m = $app->make('mail.manager')->mailer();
        return array('resolve' => get_class($m));
    } finally {
        $app['config']->set('mail', $orig);
        $app->forgetInstance('mail.manager');
        $app->forgetInstance('mailer');
    }
});
function tenta0($f)
{
    try {
        return $f();
    } catch (\Throwable $e) {
        return array('EXCECAO' => get_class($e), 'mensagem' => preg_replace('#/[^\s]*/vendor/#', 'vendor/', $e->getMessage()));
    }
}

// mensagem serializada como sairia pelo transporte: cabecalhos de assunto/de/para e o corpo, sem Date/Message-ID/boundary
function limpa_bruto($s)
{
    $s = preg_replace(array('/\r\n/', '/^(Message-ID|Date): .*$/mi', '/boundary="?[A-Za-z0-9_=+\/-]+"?/', '/^--[A-Za-z0-9_=+\/-]+(--)?$/m'), array("\n", '$1: X', 'boundary=B', '--B'), $s);
    return preg_replace('/^(Received|X-Mailer): .*\n/mi', '', $s);
}

function limpa($s)
{
    return preg_replace(array('/\r\n/', '/[0-9a-f]{32}@[^\s>]+/', '/^Date: .*$/m', '/boundary=_=_swift_[A-Za-z0-9_=]+/', '/_=_swift_[A-Za-z0-9_=]+/'), array("\n", 'ID@host', 'Date: X', 'boundary=B', 'B'), $s);
}

// extrai uma mensagem do transporte array, nos dois mundos (SwiftMailer no L8, Symfony Mailer no L13)
function extrai($app, $modo)
{
    $mailer = $app->make('mailer');
    $msgs = array();
    if ($modo === 'l8') {
        $t = $mailer->getSwiftMailer()->getTransport();
        foreach ($t->messages() as $m) {
            $partes = array();
            foreach ($m->getChildren() as $c) {
                $partes[] = array('tipo' => $c->getContentType(), 'corpo' => limpa($c->getBody()));
            }
            $cab = array();
            foreach ($m->getHeaders()->getAll() as $h) {
                $cab[] = $h->getFieldName();
            }
            $msgs[] = array(
                'assunto' => $m->getSubject(), 'de' => $m->getFrom(), 'para' => $m->getTo(), 'cc' => $m->getCc() ?: array(),
                'responder_a' => $m->getReplyTo() ?: array(), 'tipo' => $m->getContentType(), 'charset' => $m->getCharset(),
                'corpo' => limpa($m->getBody()), 'partes' => $partes, 'cabecalhos' => $cab, 'bruto' => limpa_bruto($m->toString()),
            );
        }
        $t->flush();
    } else {
        $t = $mailer->getSymfonyTransport();
        foreach ($t->messages() as $sm) {
            $m = $sm->getOriginalMessage();
            $fmt = function ($l) {
                $o = array();
                foreach ($l as $a) {
                    $o[$a->getAddress()] = $a->getName();
                }
                return $o;
            };
            $cab = array();
            foreach ($m->getHeaders()->all() as $h) {
                $cab[] = $h->getName();
            }
            $msgs[] = array(
                'assunto' => $m->getSubject(), 'de' => $fmt($m->getFrom()), 'para' => $fmt($m->getTo()), 'cc' => $fmt($m->getCc()),
                'responder_a' => $fmt($m->getReplyTo()), 'tipo' => $m->getHtmlBody() !== null ? 'text/html' : 'text/plain', 'charset' => $m->getHtmlCharset(),
                'corpo' => limpa((string)$m->getHtmlBody()), 'texto' => limpa((string)$m->getTextBody()), 'partes' => array(), 'cabecalhos' => $cab, 'bruto' => limpa_bruto($sm->toString()),
            );
        }
        $t->flush();
    }
    return $msgs;
}

function tenta($f)
{
    try {
        return $f();
    } catch (\Throwable $e) {
        return array('EXCECAO' => get_class($e), 'mensagem' => preg_replace('#/[^\s]*/vendor/#', 'vendor/', $e->getMessage()));
    }
}

$res = array('config_do_pr_sem_adaptar' => $res0, 'php' => PHP_MAJOR_VERSION . '.' . PHP_MINOR_VERSION, 'laravel' => $app->version(), 'modo' => $modo, 'config' => $saidaCfg);

// notificavel real do PR (Usuario), sem banco: atributos em memoria
$usuario = new App\Domain\Configuracao\Usuario\Models\Usuario();
$usuario->forceFill(array('id_usuario' => 7, 'nome' => 'Maria da Silva', 'login' => 'maria', 'email' => 'maria@exemplo.invalid'));

// 1) Mailable via Mail::send, como o RedesimService:440
$res['mail_redesim'] = tenta(function () use ($app, $modo) {
    $e = new \RuntimeException('Falha de exemplo: coluna inexistente');
    $m = new App\Mail\RedesimErrorToProcessEstablishmentsMail('12.345.678/0001-90', $e);
    Mail::send($m);
    $r = extrai($app, $modo);
    foreach ($r as &$x) {
        // o stack trace traz caminhos desta maquina: normaliza
        $x['corpo'] = preg_replace('#(Arquivo: )[^<]*#', '$1ARQ', $x['corpo']);
        $x['corpo'] = preg_replace('#(Linha: )\d+#', '$1N', $x['corpo']);
        $x['corpo'] = preg_replace('#(Stacktrace:</h4>\s*<br>\s*).*#s', '$1TRACE', $x['corpo']);
        $x['bruto'] = preg_replace('#Stacktrace:.*#s', 'Stacktrace: TRACE', $x['bruto']);   // o PHP 8.4 muda o rotulo {closure} da pilha: fica fora da comparacao
        $x['texto'] = isset($x['texto']) ? preg_replace('#(Stacktrace:\s*).*#s', '$1TRACE', preg_replace('#(Arquivo: )[^\n]*#', '$1ARQ', $x['texto'])) : null;
    }
    return $r;
});

// 2) Mailable sem a configuracao de ambiente (o build() deve lancar a excecao do PR)
$res['mail_redesim_sem_env'] = tenta(function () use ($app, $modo) {
    putenv('REDESIM_MAIL_ADDRESS_ON_ERROR');
    unset($_ENV['REDESIM_MAIL_ADDRESS_ON_ERROR'], $_SERVER['REDESIM_MAIL_ADDRESS_ON_ERROR']);
    try {
        $m = new App\Mail\RedesimErrorToProcessEstablishmentsMail('X', new \Exception('x'));
        Mail::send($m);
        return extrai($app, $modo);
    } finally {
        putenv('REDESIM_MAIL_ADDRESS_ON_ERROR=erros@exemplo.invalid,outro@exemplo.invalid');
        $_ENV['REDESIM_MAIL_ADDRESS_ON_ERROR'] = $_SERVER['REDESIM_MAIL_ADDRESS_ON_ERROR'] = 'erros@exemplo.invalid,outro@exemplo.invalid';
    }
});

// 3) Notification de e-mail (canal mail + database) pelo ChannelManager real; ShouldQueue ignorado com sendNow
$res['notificacao_acordo'] = tenta(function () use ($app, $modo, $usuario) {
    $n = new App\Notifications\UserNotificationAcordoVencimento(5, 11);
    Notification::sendNow($usuario, $n, array('mail'));
    $msgs = extrai($app, $modo);
    return array('via' => $n->via($usuario), 'toArray' => $n->toArray(), 'emails' => $msgs);
});

// 4) Notifications so de banco/broadcast: o payload e toArray()
$res['notificacao_user'] = tenta(function () use ($usuario) {
    $n = new App\Notifications\UserNotification("T\xedtulo de exemplo", "Mensagem com acentua\xe7\xe3o");
    return array('via' => $n->via($usuario), 'toArray' => $n->toArray(), 'json' => json_encode($n->toArray(), JSON_UNESCAPED_UNICODE));
});
$res['notificacao_assinatura'] = tenta(function () use ($usuario) {
    $n = new App\Notifications\SolicitacaoAssinaturaNotification('Assinar documento', "H\xe1 um documento para assinar", 'web/patrimonial/protocolo/assinatura');
    return array('via' => $n->via($usuario), 'toArray' => $n->toArray(), 'json' => json_encode($n->toArray(), JSON_UNESCAPED_UNICODE));
});
$res['notificacao_relatorio_legal'] = tenta(function () use ($usuario) {
    $n = new App\Notifications\EmissaoRelatorioLegalNotification(array(
        'relatorio' => 1, 'DB_itemmenu_acessado' => 99, 'tipo' => 'RREO', 'anexo' => '3', 'consolidado' => '0',
        'DB_instit' => 1, 'DB_modulo' => 209, 'pdf' => 'a.pdf', 'xls' => 'a.xls',
    ));
    return array('via' => $n->via($usuario), 'toArray' => json_decode(json_encode($n->toArray()), true));
});

// 5) Imagem::caminhoArquivoParaBase64 (usada no e-mail do acordo): hash do resultado
$res['imagem_base64'] = tenta(function () {
    $r = App\Helpers\Imagem::caminhoArquivoParaBase64(ECIDADE_PATH . 'imagens/files/logo.png');
    return array('prefixo' => substr($r, 0, 30), 'md5' => md5($r));
});

// strings em ISO-8859-1 (invalidas em UTF-8) viram UTF-8 com a marca [ISO], para o JSON nao perder o texto e o diff ver o byte
function utf($v)
{
    if (is_array($v)) {
        $o = array();
        foreach ($v as $k => $x) {
            $o[utf($k)] = utf($x);
        }
        return $o;
    }
    if (is_string($v) && !mb_check_encoding($v, 'UTF-8')) {
        return '[ISO]' . mb_convert_encoding($v, 'UTF-8', 'ISO-8859-1');
    }
    return $v;
}
ksort($deprec);
$res['deprecations'] = array_keys($deprec);
file_put_contents($saida, json_encode(utf($res), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR) . "\n");
echo "ok $saida\n";
