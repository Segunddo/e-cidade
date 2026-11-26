<?php

namespace App\Domain\Assinador;

use DateTime;
use Illuminate\Database\Eloquent\Model;

/**
 * @property integer $c142_codigo
 * @property integer $c142_usuario
 * @property integer $c142_arquivopfx
 * @property DateTime $c142_data
 * @property DateTime $c142_validade
 */
class CertificadoUsuario extends Model
{
    protected $table = 'configuracoes.certificadosusuarios';
    protected $primaryKey = 'c142_codigo';
    public $timestamps = false;

    protected $casts = [
        'c142_data' => 'datetime',
        'c142_validade' => 'datetime',
    ];

    /**
     * Sobreposicao do 8.5. No Laravel 8 do PR o cast 'DateTime' (maiusculas) le como data, mas gravar
     * c142_data/c142_validade lanca Error 'Call to undefined method DateTime::set()'. O 8.5 repete o 7.4:
     * le como 'datetime' (o Laravel 13 nao entende 'DateTime') e a escrita lanca o mesmo Error.
     */
    public function setAttribute($key, $value)
    {
        if (in_array($key, array('c142_data', 'c142_validade'), true)) {
            if ($value) {
                $this->fromDateTime($value); // o Laravel 8 converte a data antes: valor invalido lanca InvalidFormatException
            }

            throw new \Error('Call to undefined method DateTime::set()');
        }

        return parent::setAttribute($key, $value);
    }
}
