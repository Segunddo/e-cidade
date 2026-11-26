<?php

namespace App\Domain\Financeiro\Tesouraria\Models;

use Illuminate\Database\Eloquent\Model;

class Slip extends Model
{
    protected $table = 'caixa.slip';
    protected $primaryKey = 'k17_codigo';

    public $timestamps = false;

    protected $casts = [
        'k17_data' => 'datetime',
        'k17_dtaut' => 'datetime',
        'k17_dtanu' => 'datetime',
        'k17_dtestorno' => 'datetime',
    ];

    public function decendio()
    {
        return $this->hasOne(Decendio::class, 'k230_slip', 'k17_codigo');
    }
}
