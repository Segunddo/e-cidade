<?php
// Mesmo roteiro do grant.php (13), no 7.4 com Laravel 8.73.2 / Passport 10.4.2 / oauth2-server 8.3.2 / jwt 3.4.0. php grant10.php <original|proposto>
error_reporting(E_ALL & ~E_DEPRECATED);
require '/w/vendor/autoload.php';
$modo = $argv[1] ?? 'original';
spl_autoload_register(function ($c) use ($modo) {
    if (strpos($c, 'App\\') === 0) {
        $rel = str_replace('\\', '/', substr($c, 4)) . '.php';
        foreach (($modo === 'proposto' ? ['/s85/', '/pr/app/'] : ['/pr/app/']) as $d) { if (is_file($d . $rel)) { require $d . $rel; return; } }
    }
});
use Laravel\Passport\Passport;
use Laravel\Passport\Bridge;
use App\Domain\Configuracao\Usuario\Models\Usuario;
function passo($t, $f) { try { $r = $f(); echo "[ok]   $t", $r === null ? '' : " => $r", "\n"; return $r; } catch (Throwable $e) { echo "[FALHA] $t => ", get_class($e), ': ', substr(str_replace("\n", ' ', $e->getMessage()), 0, 170), "\n"; return null; } }
$app = Orchestra\Testbench\Foundation\Application::create(null, null, ['load_environment_variables' => false]);
$app['config']->set('app.key', 'base64:' . base64_encode(random_bytes(32)));
$app['config']->set('auth.guards.api', ['driver' => 'passport', 'provider' => 'users']);
$app['config']->set('auth.providers.users', ['driver' => 'eloquent', 'model' => 'UsuarioMem']);
$app['env'] = 'local';
Passport::loadKeysFrom('/w/keys');
class UsuarioMem extends Usuario {
    public function findForPassport($login) { if ($login !== 'dbseller') { return null; } $u = new static(); $u->forceFill(['id_usuario' => 1, 'login' => 'dbseller', 'senha' => 'x']); return $u; }
}
class ClienteMem extends Laravel\Passport\Client {
    public function __construct() { $this->setRawAttributes(['id' => 9999999, 'name' => 'e-cidade', 'secret' => 'segredo-de-teste', 'redirect' => 'http://localhost', 'personal_access_client' => 0, 'password_client' => 1, 'revoked' => 0, 'provider' => null], true); }
}
class ClientesMem extends Laravel\Passport\ClientRepository {
    public function __construct() {}
    public function findActive($id) { return (string) $id === '9999999' ? new ClienteMem() : null; }
}
class AccessMem extends Bridge\AccessTokenRepository {
    public static $vivos = [];
    public function __construct() {}
    public function persistNewAccessToken(League\OAuth2\Server\Entities\AccessTokenEntityInterface $t) { static::$vivos[$t->getIdentifier()] = true; }
    public function revokeAccessToken($id) { unset(static::$vivos[$id]); }
    public function isAccessTokenRevoked($id) { return !isset(static::$vivos[$id]); }
}
class RefreshMem extends Bridge\RefreshTokenRepository {
    public static $vivos = [];
    public function __construct() {}
    public function persistNewRefreshToken(League\OAuth2\Server\Entities\RefreshTokenEntityInterface $t) { static::$vivos[$t->getIdentifier()] = true; }
    public function revokeRefreshToken($id) { unset(static::$vivos[$id]); }
    public function isRefreshTokenRevoked($id) { return !isset(static::$vivos[$id]); }
}
passo('registrar AuthServiceProvider do PR + PassportServiceProvider', function () use ($app) {
    $app->register(App\Providers\AuthServiceProvider::class);
    $app->register(Laravel\Passport\PassportServiceProvider::class);
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
});
$app->singleton(Laravel\Passport\ClientRepository::class, function () { return new ClientesMem(); });
$app->singleton(Bridge\AccessTokenRepository::class, function () { return new AccessMem(); });
$app->singleton(Bridge\RefreshTokenRepository::class, function () { return new RefreshMem(); });
$srv = $app->make(League\OAuth2\Server\AuthorizationServer::class);
$svc = new App\Domain\Configuracao\Usuario\Services\AuthService($srv);
$req = new ReflectionMethod($svc, 'requestToPassport'); $req->setAccessible(true);
$dados = ['grant_type' => 'password', 'username' => 'dbseller', 'password' => 'qualquer', 'client_id' => '9999999', 'client_secret' => 'segredo-de-teste'];
passo('password grant (AuthService::requestToPassport do PR)', function () use ($req, $svc, $dados) { $r = $req->invoke($svc, $dados); return json_encode(['chaves' => array_keys($r), 'token_type' => $r['token_type'], 'expires_in_ok' => $r['expires_in'] > 80000 && $r['expires_in'] <= 86400]); });
passo('refresh_token', function () use ($req, $svc, $dados) {
    $r = $req->invoke($svc, $dados);
    $n = $req->invoke($svc, ['grant_type' => 'refresh_token', 'refresh_token' => $r['refresh_token'], 'client_id' => '9999999', 'client_secret' => 'segredo-de-teste']);
    return json_encode(['chaves' => array_keys($n), 'novo_access' => $n['access_token'] !== $r['access_token']]);
});
$res = $req->invoke($svc, $dados);
$dec = function ($j, $i) { $c = json_decode(base64_decode(strtr(explode('.', $j)[$i], '-_', '+/')), true); if ($i == 1) { foreach (['iat', 'nbf', 'exp', 'jti'] as $k) { $c[$k] = 'x'; } ksort($c); } return $c; };
echo "claims: ", json_encode($dec($res['access_token'], 1)), "\ncabecalho: ", json_encode($dec($res['access_token'], 0)), "\n";
passo('Bearer valido (ResourceServer)', function () use ($app, $res) { $r = $app->make(League\OAuth2\Server\ResourceServer::class)->validateAuthenticatedRequest((new GuzzleHttp\Psr7\ServerRequest('GET', '/'))->withHeader('Authorization', 'Bearer ' . $res['access_token'])); return 'user=' . $r->getAttribute('oauth_user_id') . ' client=' . $r->getAttribute('oauth_client_id'); });
passo('Bearer adulterado e recusado', function () use ($app, $res) { try { $app->make(League\OAuth2\Server\ResourceServer::class)->validateAuthenticatedRequest((new GuzzleHttp\Psr7\ServerRequest('GET', '/'))->withHeader('Authorization', 'Bearer ' . substr($res['access_token'], 0, -3) . 'AAA')); return 'ACEITO (errado)'; } catch (League\OAuth2\Server\Exception\OAuthServerException $e) { return 'recusado code=' . $e->getCode(); } });
passo('segredo errado e recusado', function () use ($req, $svc, $dados) { try { $req->invoke($svc, ['client_secret' => 'errado'] + $dados); return 'ACEITO (errado)'; } catch (League\OAuth2\Server\Exception\OAuthServerException $e) { return 'recusado code=' . $e->getCode(); } });
$cc = $req->invoke($svc, ['grant_type' => 'client_credentials', 'client_id' => '9999999', 'client_secret' => 'segredo-de-teste']);
echo "claims client_credentials: ", json_encode($dec($cc['access_token'], 1)), "\n";
// ---- clientCredential (Kernel do PR: CheckClientCredentials) ----
class TokensMem extends Laravel\Passport\TokenRepository {
    public function find($id) { $t = new Laravel\Passport\Token(); $t->setRawAttributes(['id' => $id, 'scopes' => '["*"]', 'revoked' => 0], true); return $t; }
}
$app->singleton(Laravel\Passport\TokenRepository::class, function () { return new TokensMem(); });
$app['router']->aliasMiddleware('clientCredential', Laravel\Passport\Http\Middleware\CheckClientCredentials::class);
$app['config']->set('app.debug', false);
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$n = 0;
foreach (['token de cliente (client_credentials)' => $cc['access_token'], 'token invalido' => 'x'] as $rot => $t) {
    $uri = '/cc' . (++$n);
    $app['router']->get($uri, function () { return 'passou'; })->middleware('clientCredential');
    passo("rota com clientCredential, $rot", function () use ($kernel, $t, $uri) {
        $r = $kernel->handle(Illuminate\Http\Request::create($uri, 'GET', [], [], [], ['HTTP_AUTHORIZATION' => 'Bearer ' . $t, 'HTTP_ACCEPT' => 'application/json']));
        return 'HTTP ' . $r->getStatusCode();
    });
}
