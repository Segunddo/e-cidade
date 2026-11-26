<?php
// (1) Toda chave dos arquivos pt-br do PR (resources/lang/pt-br/*.php) volta traduzida pelo tradutor, sem cair no ingles nem na propria chave;
// (2) a mensagem de cada regra de validacao que o codigo do PR usa (um valor invalido por regra e por tipo), com o app real, sem banco.
chdir('/app');
require '/app/vendor/autoload.php';
$app = require '/app/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

function achata($a, $p = '') { $o = []; foreach ($a as $k => $v) { if (is_array($v)) { $o += achata($v, $p . $k . '.'); } else { $o[$p . $k] = $v; } } return $o; }
$total = $traduzidas = 0; $falhas = [];
foreach (['auth', 'pagination', 'passwords', 'validation'] as $arq) {
    foreach (achata(require "/app/resources/lang/pt-br/$arq.php") as $k => $esperado) {
        if (!is_string($esperado) || $k === 'attributes' || strpos($k, 'attributes.') === 0 || strpos($k, 'custom') === 0) { continue; }
        $total++;
        $obtido = trans("$arq.$k");
        if ($obtido === $esperado) { $traduzidas++; } else { $falhas[] = "$arq.$k"; }
    }
}
echo "chaves do pt-br do PR: $total, devolvidas como no arquivo: $traduzidas, diferentes: ", count($falhas), "\n";
foreach (array_slice($falhas, 0, 10) as $f) { echo "  diferente: $f => ", trans($f), "\n"; }

$app['validator']->setPresenceVerifier(new class implements Illuminate\Validation\PresenceVerifierInterface {
    public function getCount($collection, $column, $value, $excludeId = null, $idColumn = null, array $extra = []) { return 0; }
    public function getMultiCount($collection, $column, array $values, array $extra = []) { return 0; }
});
$casos = [
    ['required', null], ['filled', ''], ['present', 'x', 'remove'], ['string', 5], ['integer', 'a'], ['numeric', 'a'], ['boolean', 'a'], ['array', 'a'],
    ['email', 'x'], ['date', 'x'], ['date_format:d/m/Y', '2026-01-01'], ['digits:3', '12'], ['in:a,b', 'c'], ['regex:/^[0-9]+$/', 'a'],
    ['different:outro', 'x', null, ['outro' => 'x']], ['confirmed', 'a', null, ['a_confirmation' => 'b']],
    ['min:3', 1, 'num'], ['min:3', 'ab', 'str'], ['min:3', [1], 'arr'], ['max:3', 9, 'num'], ['max:3', 'abcd', 'str'], ['max:3', [1, 2, 3, 4], 'arr'],
    ['between:2,4', 9, 'num'], ['between:2,4', 'abcdef', 'str'], ['between:2,4', [1], 'arr'],
    ['size:2', 9, 'num'], ['size:2', 'abc', 'str'], ['size:2', [1], 'arr'],
    ['required_if:o,1', null, null, ['o' => 1]], ['required_with:o', null, null, ['o' => 1]], ['required_without:o', null], ['exists:tabela,coluna', 'x'], ['unique:tabela,coluna', 'x'],
    ['file', 'x'], ['mimes:pdf', 'x'], ['mimetypes:application/pdf', 'x'], ['after:2026-01-01', '2025-01-01'], ['before:2026-01-01', '2027-01-01'], ['url', 'x'], ['image', 'x'], ['accepted', 'no'], ['alpha', '1'], ['uuid', 'x'], ['json', 'x'], ['ip', 'x'], ['gt:5', 1, 'num'], ['gte:5', 1, 'num'], ['lt:5', 9, 'num'], ['lte:5', 9, 'num'], ['same:outro', 'x', null, ['outro' => 'y']],
];
foreach ($casos as $c) {
    $dados = ($c[3] ?? []) + (isset($c[2]) && $c[2] === 'remove' ? [] : ['campo' => $c[1]]);
    $v = $app['validator']->make($dados, ['campo' => $c[0]]);
    $v->setAttributeNames(['campo' => 'campo']);
    $msg = $v->fails() ? $v->errors()->first('campo') : '(passou)';
    echo str_pad($c[0] . (isset($c[2]) && $c[2] !== 'remove' ? ' [' . $c[2] . ']' : ''), 34), $msg, "\n";
}
