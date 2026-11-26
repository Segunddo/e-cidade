<?php

namespace App\Domain\Educacao\Escola\Models;

use Illuminate\Database\Eloquent\Model;

class AtividadeProfissionalEscola extends Model
{
    protected $table = 'escola.rechumanoativ';
    protected $primaryKey = 'ed22_i_codigo';
    protected $casts = ['ed22_datainicio' => 'datetime', 'ed22_datafim' => 'datetime'];
    public $timestamps = false;
    public $incrementing = false;

    public function atividade()
    {
        return $this->belongsTo(AtividadeProfissional::class, 'ed22_i_atividade', 'ed01_i_codigo');
    }

    public function profissionalEscola()
    {
        return $this->belongsTo(ProfissionalEscola::class, 'ed22_i_rechumanoescola', 'ed75_i_codigo');
    }

    public function turnoReferente()
    {
        return $this->belongsTo(TurnoReferente::class, 'ed22_turno', 'ed231_i_turno');
    }
}
