<?php

namespace App\Domain\Financeiro\Tesouraria\Requests;

use App\Http\Requests\DBFormRequest;

class GetDetalhamentoDecendioRequest extends DBFormRequest
{
    public function rules()
    {
        return [
            'exercicio' => 'required|digits:4',
            'instituicao' => 'required|integer',
            'dataInicial' => 'required|date',
            'dataFinal' => 'required|date',
            'reduzidos' => 'required',
            'desdobramento' => 'required',
            'conta_pagadora' => 'required',
        ];
    }

    public function messages()
    {
        return [];
    }
}
