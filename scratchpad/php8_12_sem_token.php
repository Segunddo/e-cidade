<?php
// PHP8-12 (T-128): o que cada rota /v4 e /rest/v1 responde SEM token e com token malformado, pelo kernel HTTP do
// Laravel em processo (sem servidor, sem rede, sem banco). Mesmo script no 7.4 e no 8.5; compara-se a saida.
// Uso (raiz ecidade/, storage gravavel, pcntl; as chaves OAuth de teste o proprio script gera): MODO=neutro|real SAIDA=saida.jsonl php php8_12_sem_token.php
//   MODO=real   : pilha de middleware do PR como esta (o DatabaseMiddleware global tenta o banco antes de tudo).
//   MODO=neutro : so o DatabaseMiddleware global vira passagem direta; o resto da pilha e do PR. Nenhuma conexao e aberta
//                 (o resolvedor do pgsql do Laravel levanta um marcador e anota "tentou_banco").
// Cada pedido roda num processo filho (pcntl_fork): exit/die de um controller nao derruba a medicao.
$_SERVER['HOME'] = getcwd() . '/tmp';
// o pai nunca escreve na saida do PHP (nem avisos do boot): qualquer byte enviado antes faz o filho ver "headers already sent"
// chaves OAuth de teste (o boot do Passport as le): geradas aqui, na hora, so se faltarem; storage/ e tmpfs e e descartado
if (!is_file('storage/oauth-private.key')) {
    $chave = openssl_pkey_new(array('private_key_bits' => 2048));
    openssl_pkey_export($chave, $privada);
    file_put_contents('storage/oauth-private.key', $privada);
    file_put_contents('storage/oauth-public.key', openssl_pkey_get_details($chave)['key']);
    chmod('storage/oauth-private.key', 0600);
    chmod('storage/oauth-public.key', 0600);
}
ob_start();
require 'bootstrap.php';
require_once modification('libs/db_stdlib.php');
$app = require 'bootstrap/app.php';

class TentouBanco extends RuntimeException {}
class Passagem { public function handle($request, Closure $next) { return $next($request); } }

$modo = getenv('MODO') ?: 'neutro';
if ($modo === 'neutro') {
    $app->bind(App\Http\Middleware\DatabaseMiddleware::class, Passagem::class);
}
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->instance("request", Illuminate\Http\Request::create("/"));
$kernel->bootstrap();
// nenhuma conexao pelo Laravel: o resolvedor do driver levanta o marcador (e o filho anota)
$GLOBALS['tentou_banco'] = false;
foreach (array('pgsql', 'mysql', 'sqlite', 'sqlsrv') as $drv) {
    $app['db']->extend($drv, function () { $GLOBALS['tentou_banco'] = true; throw new TentouBanco('conexao de banco pedida'); });
}

$avisosBoot = ob_get_clean();
$saida = fopen(getenv('SAIDA') ?: 'php://stdout', 'w');
fwrite($saida, json_encode(array('boot' => true, 'modo' => $modo, 'php' => PHP_VERSION, 'laravel' => $app->version(), 'avisos_de_boot' => substr_count($avisosBoot, 'Deprecated'), 'avisos_de_boot_texto' => preg_split('/\n+/', trim(str_replace(getcwd(), '/app', $avisosBoot)))), JSON_UNESCAPED_SLASHES) . "\n");
ob_start();
$vivas = array();
foreach ($app['router']->getRoutes()->getRoutes() as $r) {
    if (strpos($r->uri(), 'v4') === 0 || strpos($r->uri(), 'rest/v1') === 0) { $vivas[] = $r; }
}

function caminho($r) {
    return '/' . ltrim(preg_replace_callback('/\{(\w+)\??\}/', function ($m) use ($r) {
        $w = isset($r->wheres[$m[1]]) ? $r->wheres[$m[1]] : null;
        foreach (array('1', 'a', '2026-01-01', 'x1') as $v) { if (!$w || preg_match('#^(' . $w . ')$#', $v)) return $v; }
        return '1';
    }, $r->uri()), '/');
}
function normaliza($s) {
    $s = str_replace(getcwd(), '/app', $s);
    $s = preg_replace('/\b20\d\d-\d\d-\d\d[T ]\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:?\d\d)?\b/', '<data>', $s);
    return $s;
}
$cabecalhos = array('content-type', 'cache-control', 'www-authenticate', 'location', 'allow', 'vary',
    'access-control-allow-origin', 'access-control-allow-methods', 'x-ratelimit-limit', 'content-disposition');
$casos = array(
    array('sem_token', array(), 'json'),
    array('bearer_x', array('HTTP_AUTHORIZATION' => 'Bearer x'), 'json'),
    array('sem_token', array(), 'html'),
    array('bearer_x', array('HTTP_AUTHORIZATION' => 'Bearer x'), 'html'),
);
$tmp = sys_get_temp_dir() . '/t128_' . getmypid();
foreach ($vivas as $i => $r) {
    foreach (array_values(array_diff($r->methods(), array('HEAD'))) as $metodo) {
        foreach ($casos as $c) {
            list($auth, $srv, $accept) = $c;
            if ($accept === 'json') { $srv['HTTP_ACCEPT'] = 'application/json'; }
            $linha = array('rota' => $i, 'metodo' => $metodo, 'uri' => $r->uri(), 'auth' => $auth, 'accept' => $accept);
            @unlink($tmp);
            $pid = pcntl_fork();
            if ($pid === 0) {
                pcntl_alarm(20);
                $res = array();
                ob_start();
                try {
                    $resp = $kernel->handle(Illuminate\Http\Request::create(caminho($r), $metodo, array(), array(), array(), $srv));
                    $res['status'] = $resp->getStatusCode();
                    $h = array();
                    foreach ($cabecalhos as $n) { if ($resp->headers->has($n)) { $h[$n] = implode(',', (array) $resp->headers->all($n)); } }
                    $res['cabecalhos'] = $h;
                    $corpo = $resp instanceof Symfony\Component\HttpFoundation\BinaryFileResponse ? '<arquivo>' : (string) $resp->getContent();
                    $res['corpo'] = normaliza(substr($corpo, 0, 2000));
                    $res['corpo_md5'] = md5(normaliza($corpo));
                } catch (Throwable $e) {
                    $res['status'] = 'excecao';
                    $res['corpo'] = get_class($e) . ': ' . normaliza($e->getMessage());
                }
                $res['saida_direta'] = normaliza(substr(ob_get_clean(), 0, 500));
                $res['tentou_banco'] = $GLOBALS['tentou_banco'] || (isset($res['corpo']) && preg_match('/\bpg_\w+\(|conexao de banco pedida|could not find driver/', $res['corpo']));
                file_put_contents($tmp, json_encode($res, JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR));
                exit(0);
            }
            pcntl_waitpid($pid, $st);
            $res = is_file($tmp) ? json_decode(file_get_contents($tmp), true) : null;
            $linha += $res ?: array('status' => 'filho-morreu', 'corpo' => 'sinal/saida do filho: ' . $st, 'tentou_banco' => null);
            fwrite($saida, json_encode($linha, JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR) . "\n");
        }
    }
}
@unlink($tmp);
