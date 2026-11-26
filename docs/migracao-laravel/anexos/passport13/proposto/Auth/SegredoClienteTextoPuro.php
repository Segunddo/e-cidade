<?php

namespace App\Auth;

use Illuminate\Contracts\Hashing\Hasher;

/**
 * Passport 13 confere o segredo do cliente com Hasher::check(); o e-cidade guarda o segredo dos clientes OAuth
 * (oauth_clients.secret) em texto puro, como o Passport 10 conferia. Ligado so ao Bridge\ClientRepository.
 */
class SegredoClienteTextoPuro implements Hasher
{
    public function info($hashedValue)
    {
        return [];
    }

    public function make($value, array $options = [])
    {
        return $value;
    }

    public function check($value, $hashedValue, array $options = [])
    {
        return is_string($hashedValue) && $hashedValue !== '' && hash_equals($hashedValue, (string) $value);
    }

    public function needsRehash($hashedValue, array $options = [])
    {
        return false;
    }
}
