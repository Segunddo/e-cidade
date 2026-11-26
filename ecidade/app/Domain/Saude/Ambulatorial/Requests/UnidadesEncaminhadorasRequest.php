<?php

namespace App\Domain\Saude\Ambulatorial\Requests;

use App\Http\Requests\DBFormRequest;

class UnidadesEncaminhadorasRequest extends DBFormRequest
{

    /**
     * @return array
     */
    public function rules()
    {
        return [
            'ativo' => 'required|boolean',
            'descricao' => 'required|string'
        ];
    }

    /**
     * @return array
     */
    public function messages()
    {
        return [];
    }
}
