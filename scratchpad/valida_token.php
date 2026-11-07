<?php
// Valida um token emitido pelo Passport 4 (PHP 5.6) com a biblioteca que o Passport
// novo usa por baixo -- league/oauth2-server -- na versao do vendor indicado.
// Uso: php valida_token.php <vendor/autoload.php> <arquivo com o token> <oauth-public.key>
require $argv[1];

use League\OAuth2\Server\CryptKey;
use League\OAuth2\Server\ResourceServer;
use League\OAuth2\Server\Repositories\AccessTokenRepositoryInterface;
use League\OAuth2\Server\Entities\AccessTokenEntityInterface;
use GuzzleHttp\Psr7\ServerRequest;

// O mesmo que o Passport faz: o token so vale se existir na tabela e nao estiver revogado.
class Repo implements AccessTokenRepositoryInterface {
    public $forcarRevogado = false;
    public function getNewToken($c, array $s, $u = null): AccessTokenEntityInterface { throw new Exception('nao usado'); }
    public function persistNewAccessToken($t): void { throw new Exception('nao usado'); }
    public function revokeAccessToken($id): void { throw new Exception('nao usado'); }
    public function isAccessTokenRevoked($id): bool {
        if ($this->forcarRevogado) return true;
        $c = pg_connect('host=ecidade_database dbname=ecidade user=postgres password=postgres');
        $r = pg_query_params($c, 'select revoked from oauth_access_tokens where id = $1', [$id]);
        $l = pg_fetch_assoc($r);
        if (!$l) { echo "    (token nao existe em oauth_access_tokens)\n"; return true; }
        return $l['revoked'] === 't';
    }
}

$token = trim(file_get_contents($argv[2]));
$chave = new CryptKey('file://' . $argv[3], null, false);

function testa($nome, $token, $revogado, $chave) {
    $repo = new Repo; $repo->forcarRevogado = $revogado;
    $rs = new ResourceServer($repo, $chave);
    $req = (new ServerRequest('GET', '/v4/api/tributario/teste'))->withHeader('Authorization', 'Bearer ' . $token);
    try {
        $a = $rs->validateAuthenticatedRequest($req)->getAttributes();
        printf("  %-38s ACEITO   usuario=%s cliente=%s escopos=%s\n", $nome, $a['oauth_user_id'], $a['oauth_client_id'], json_encode($a['oauth_scopes']));
    } catch (Throwable $e) {
        printf("  %-38s RECUSADO (%s)\n", $nome, substr($e->getMessage() . ' ' . ($e->getPrevious() ? $e->getPrevious()->getMessage() : ''), 0, 90));
    }
}

[$h, $p, $s] = explode('.', $token);
$claims = json_decode(base64_decode(strtr($p, '-_', '+/')), true);
$claims['sub'] = '999';   // adulterado: outro usuario, mesma assinatura
$adulterado = $h . '.' . rtrim(strtr(base64_encode(json_encode($claims)), '+/', '-_'), '=') . '.' . $s;

testa('1. token real do 5.6', $token, false, $chave);
testa('2. controle: token adulterado', $adulterado, false, $chave);
testa('3. controle: mesmo token, revogado', $token, true, $chave);
