<?php
// Valida um token emitido pelo Passport 4 (PHP 5.6) com a biblioteca que o Passport
// novo usa por baixo -- league/oauth2-server -- na versao do vendor indicado.
// Uso: php valida_token.php <vendor/autoload.php> <arquivo com o token> <oauth-public.key>
//
// Script de investigacao pontual (16/10/2026) da migracao do Laravel, nao um passo do guia: provou que o
// login pode ficar no 5.6 enquanto as rotas /v4/api/* passam ao 8.5 (docs/registro/laravel.md, "TESTE: o
// token do Passport 4 (5.6) vale no Passport novo (8.5)"; docs/migrar-laravel.md).
// COMO FAZ: monta o ResourceServer do league/oauth2-server (a classe que o Passport usa para validar o
// bearer) com a chave publica dada e um repositorio que le a revogacao da tabela oauth_access_tokens do
// banco compartilhado, e valida tres pedidos GET com "Authorization: Bearer": o token real, o mesmo token
// com o `sub` trocado (controle: a assinatura deixa de bater) e o token real com revogacao forcada
// (controle). Os dois controles TEM de sair RECUSADO; senao o teste nao prova nada.
// ONDE RODA: so em PHP 7.1+ (tipos de retorno void, desestruturacao [..] = ...), com o vendor/ do Laravel
// NOVO (ex.: o container ecidade_lar12, ver laravel.md) -- nao no 5.6. Precisa alcancar o host
// ecidade_database (rede do compose). Cuidado: no ecidade_lar12 o storage/ e sobreposto por uma pasta vazia;
// passe um caminho onde a chave exista (senao "Invalid key supplied", que e o teste, nao a compatibilidade).
// ENTRADAS: o autoload do vendor a testar, um arquivo com o JWT (emitido por POST :8080/v4/oauth/token) e a
// oauth-public.key. SAIDA: uma linha por caso, ACEITO (usuario, cliente, escopos) ou RECUSADO (motivo).
// Nao grava nada (so le o banco).
require $argv[1];

use League\OAuth2\Server\CryptKey;
use League\OAuth2\Server\ResourceServer;
use League\OAuth2\Server\Repositories\AccessTokenRepositoryInterface;
use League\OAuth2\Server\Entities\AccessTokenEntityInterface;
use GuzzleHttp\Psr7\ServerRequest;

// O mesmo que o Passport faz: o token so vale se existir na tabela e nao estiver revogado.
// So isAccessTokenRevoked() e chamado na validacao de um bearer; os outros metodos existem porque a interface
// exige e lancam excecao se alguem os usar. $forcarRevogado liga o 3o caso (controle de revogacao).
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
// 3o argumento false: nao conferir as permissoes do arquivo da chave (por padrao o CryptKey reclama de
// chave com permissao aberta demais)
$chave = new CryptKey('file://' . $argv[3], null, false);

// Valida um pedido com o token dado e imprime ACEITO com os atributos que o ResourceServer poe no pedido
// (oauth_user_id, oauth_client_id, oauth_scopes) ou RECUSADO com a mensagem (e a da excecao anterior, se houver).
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

// Controle negativo 1: decodifica o payload do JWT (cabecalho.payload.assinatura, base64url), troca o `sub` e
// recodifica mantendo a assinatura ORIGINAL -- um validador correto tem de recusar.
[$h, $p, $s] = explode('.', $token);
$claims = json_decode(base64_decode(strtr($p, '-_', '+/')), true);
$claims['sub'] = '999';   // adulterado: outro usuario, mesma assinatura
$adulterado = $h . '.' . rtrim(strtr(base64_encode(json_encode($claims)), '+/', '-_'), '=') . '.' . $s;

testa('1. token real do 5.6', $token, false, $chave);
testa('2. controle: token adulterado', $adulterado, false, $chave);
testa('3. controle: mesmo token, revogado', $token, true, $chave);
