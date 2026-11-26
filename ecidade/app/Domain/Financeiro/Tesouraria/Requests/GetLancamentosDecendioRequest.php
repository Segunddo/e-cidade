<?php

namespace App\Domain\Financeiro\Tesouraria\Requests;

use App\Http\Requests\DBFormRequest;

class GetLancamentosDecendioRequest extends DBFormRequest
{
    public function rules()
    {
        return [
            'exercicio' => 'required|digits:4',
            'instituicao'  => 'required|integer',
            'dataInicial'  => 'required|date',
            'dataFinal'  => 'required|date',
        ];
    }

    public function messages()
    {
        return [];
    }
}
