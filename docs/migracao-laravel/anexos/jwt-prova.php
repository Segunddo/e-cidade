<?php
// Prova isolada (sem banco, sem rede): emite e valida JWT pelo caminho do league/oauth2-server 8.3.2.
// uso: php prova.php <dir-vendor> <dir-chaves>
require $argv[1] . '/vendor/autoload.php';
$k = $argv[2];

use League\OAuth2\Server\CryptKey;
use League\OAuth2\Server\Entities\AccessTokenEntityInterface;
use League\OAuth2\Server\Entities\ClientEntityInterface;
use League\OAuth2\Server\Entities\Traits\AccessTokenTrait;
use League\OAuth2\Server\Entities\Traits\EntityTrait;
use League\OAuth2\Server\Entities\Traits\TokenEntityTrait;
use League\OAuth2\Server\AuthorizationValidators\BearerTokenValidator;
use League\OAuth2\Server\Repositories\AccessTokenRepositoryInterface;
use Nyholm\Psr7\ServerRequest;

class Tok implements AccessTokenEntityInterface { use AccessTokenTrait, EntityTrait, TokenEntityTrait; }
class Cli implements ClientEntityInterface {
    use EntityTrait, League\OAuth2\Server\Entities\Traits\ClientTrait;
    public function __construct() { $this->identifier = '7'; }
}
class Repo implements AccessTokenRepositoryInterface {
    public function getNewToken(ClientEntityInterface $c, array $s, $u = null) {}
    public function persistNewAccessToken(AccessTokenEntityInterface $t) {}
    public function revokeAccessToken($id) {}
    public function isAccessTokenRevoked($id) { return false; }
}
class Esc implements League\OAuth2\Server\Entities\ScopeEntityInterface {
    use EntityTrait;
    public function __construct($i) { $this->identifier = $i; }
    public function jsonSerialize() { return $this->identifier; }
}

function emite(string $priv, string $exp): string {
    $t = new Tok();
    $t->setIdentifier('abc123');
    $t->setClient(new Cli());
    $t->setUserIdentifier('42');
    $t->addScope(new Esc('*'));
    $t->setExpiryDateTime(new DateTimeImmutable($exp));
    $t->setPrivateKey(new CryptKey($priv, null, false));
    return (string) $t;
}
function valida(string $jwt, string $pub): string {
    $v = new BearerTokenValidator(new Repo());
    $v->setPublicKey(new CryptKey($pub, null, false));
    try {
        $r = $v->validateAuthorization((new ServerRequest('GET', '/'))->withHeader('authorization', 'Bearer ' . $jwt));
        return 'VALIDO user=' . $r->getAttribute('oauth_user_id') . ' client=' . $r->getAttribute('oauth_client_id')
            . ' scopes=' . json_encode($r->getAttribute('oauth_scopes')) . ' id=' . $r->getAttribute('oauth_access_token_id');
    } catch (League\OAuth2\Server\Exception\OAuthServerException $e) {
        return 'RECUSADO code=' . $e->getCode() . ' msg=' . $e->getMessage() . ' hint=' . $e->getHint();
    }
}
function dec(string $p) { return json_decode(base64_decode(strtr($p, '-_', '+/')), true); }
function forma(string $jwt): array {
    [$h, $c, $s] = explode('.', $jwt);
    $cl = dec($c);
    foreach (['iat', 'nbf', 'exp'] as $n) { $cl[$n] = is_numeric($cl[$n] ?? null) ? 'num' : var_export($cl[$n] ?? null, true); }
    ksort($cl);
    return ['header' => dec($h), 'claims' => $cl, 'sig_bytes' => strlen(base64_decode(strtr($s, '-_', '+/')))];
}

$a = "file://$k/a.key"; $pubA = "file://$k/a.pub"; $b = "file://$k/b.key";
$validoTok  = emite($a, '+1 hour');
$expiradoTok = emite($a, '-1 hour');
$outraChave = emite($b, '+1 hour');
$adulterado = preg_replace('/\.[^.]+\./', '.' . rtrim(strtr(base64_encode(json_encode(['sub' => '1'])), '+/', '-_'), '=') . '.', $validoTok);

$pp = Lcobucci\JWT\Configuration::forUnsecuredSigner()->parser()->parse($validoTok)->claims();
$out = [
    'php' => PHP_VERSION,
    'jwt' => class_exists(Composer\InstalledVersions::class) ? Composer\InstalledVersions::getPrettyVersion('lcobucci/jwt') : '?',
    'forma_valido' => forma($validoTok),
    'passport_parse' => ['jti' => $pp->get('jti'), 'sub' => $pp->get('sub'), 'aud' => $pp->get('aud'), 'scopes' => $pp->get('scopes')],
    'valido' => valida($validoTok, $pubA),
    'expirado' => valida($expiradoTok, $pubA),
    'assinatura_errada' => valida($outraChave, $pubA),
    'payload_adulterado' => valida($adulterado, $pubA),
    'lixo' => valida('abc.def.ghi', $pubA),
];
echo json_encode($out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), "\n";
