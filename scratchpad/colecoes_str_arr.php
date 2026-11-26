<?php
// PHP8-62 (T-155): Collection, Str::, Arr:: e helpers que o codigo do PR usa, com entradas no formato dos usos reais
// (arrays de arrays, objetos stdClass como os de DB::select/pg_fetch_object, valores numericos em texto). Sem banco, sem rede.
// Uso: bash docker/composer-85/roda-isolado.sh <7.4|8.5> scratchpad/colecoes_str_arr.php /app /app/vendor
error_reporting(E_ALL & ~E_DEPRECATED);
date_default_timezone_set('America/Sao_Paulo');
$raiz = $argv[1]; $vendor = $argv[2];
require $vendor . '/autoload.php';
use Illuminate\Support\Arr;
use Illuminate\Support\Collection;
use Illuminate\Support\Str;

$j = function ($v) {
    if ($v instanceof Illuminate\Contracts\Support\Arrayable) { $v = array('__' . get_class($v) => $v->toArray()); }
    return json_encode($v, JSON_PARTIAL_OUTPUT_ON_ERROR | JSON_UNESCAPED_UNICODE | JSON_PRESERVE_ZERO_FRACTION);
};
$caso = function ($rot, $fn) use ($j) {
    try { $r = $fn(); echo "$rot => " . (is_object($r) && !($r instanceof Illuminate\Contracts\Support\Arrayable) && !($r instanceof stdClass) ? get_class($r) : $j($r)) . "\n"; }
    catch (Throwable $e) { echo "$rot => EXC " . get_class($e) . ': ' . substr(preg_replace('/\s+/', ' ', $e->getMessage()), 0, 90) . "\n"; }
};
$obj = function (array $a) { return (object) $a; };
// linhas como as de DB::select / pg_fetch_object (campos em texto)
$linhas = array($obj(array('id' => '3', 'nome' => 'Beta', 'valor' => '10.50', 'grupo' => 'a', 'exclusao' => 'f')),
                $obj(array('id' => '1', 'nome' => 'Alfa', 'valor' => '2.25', 'grupo' => 'b', 'exclusao' => 't')),
                $obj(array('id' => '2', 'nome' => 'Acao', 'valor' => '10.50', 'grupo' => 'a', 'exclusao' => 'f')),
                $obj(array('id' => '4', 'nome' => 'Zulu', 'valor' => '0', 'grupo' => 'b', 'exclusao' => 'f')));
$arrays = array(array('o11_descricao' => 'Norte', 'ano' => 2024), array('o11_descricao' => 'Sul', 'ano' => 2025), array('o11_descricao' => 'Leste', 'ano' => 2024));
$ids = array('3', '1', '2', '4', '2');

// ---- collect() + os metodos usados (inventario: map, filter, each, reduce, implode, max, count, shift, first, sortBy, groupBy, push, merge, contains, diff, search, has, values, flatMap, whereIn, isEmpty, all, toArray, toJson, last)
$caso('collect(explode) ->all', function () { return collect(explode('-', '1-2-3'))->all(); });
$caso('collect(linhas)->map(id)->all', function () use ($linhas) { return collect($linhas)->map(function ($l) { return $l->id; })->all(); });
$caso('collect(linhas)->map(modifica o objeto)->first()', function () use ($linhas, $obj) { $c = collect(array($obj(array('v' => '1'))))->map(function ($l) { $l->v = (int) $l->v + 1; return $l; }); return $c->first(); });
$caso('collect(linhas)->filter(callback)->count()', function () use ($linhas) { return collect($linhas)->filter(function ($l) { return $l->exclusao === 'f'; })->count(); });
$caso('collect(linhas)->filter(callback)->values()', function () use ($linhas) { return collect($linhas)->filter(function ($l) { return $l->grupo == 'a'; })->values()->map(function ($l) { return $l->id; })->all(); });
$caso('collect(linhas)->filter(callback) chaves preservadas', function () use ($linhas) { return array_keys(collect($linhas)->filter(function ($l) { return $l->grupo == 'b'; })->all()); });
$caso('collect(array)->filter() sem callback', function () { return collect(array(0, '', null, '0', 'a', array(), false, 1))->filter()->all(); });
$caso('collect(linhas)->each (retorna false interrompe)', function () use ($linhas) { $v = array(); collect($linhas)->each(function ($l, $k) use (&$v) { $v[] = $l->id; if ($l->id == '1') { return false; } }); return $v; });
$caso('collect(valores)->reduce(soma, 0)', function () use ($linhas) { return collect($linhas)->reduce(function ($t, $l) { return $l->valor + $t; }, 0); });
$caso('collect(arrays)->implode(chave, ", ")', function () use ($arrays) { return collect($arrays)->implode('o11_descricao', ', '); });
$caso('collect(array)->implode(",")', function () { return collect(array('a', 'b', 3))->implode(','); });
$caso('collect(linhas)->implode(chave de objeto)', function () use ($linhas) { return collect($linhas)->implode('nome', '|'); });
$caso('collect(vazia)->implode', function () { return collect(array())->implode('x', ','); });
$caso('collect(numeros)->max()', function () { return collect(array(3, 10, 2))->max(); });
$caso('collect(textos numericos)->max()', function () { return collect(array('3', '10', '2'))->max(); });
$caso('collect(vazia)->max()', function () { return collect(array())->max(); });
$caso('collect(linhas)->max(valor)', function () use ($linhas) { return collect($linhas)->max('valor'); });
$caso('collect(linhas)->sum(valor)', function () use ($linhas) { return collect($linhas)->sum('valor'); });
$caso('collect(linhas)->sum(callback)', function () use ($linhas) { return collect($linhas)->sum(function ($l) { return (float) $l->valor; }); });
$caso('collect(linhas)->avg(valor)', function () use ($linhas) { return collect($linhas)->avg('valor'); });
$caso('collect(linhas)->pluck(nome, id)', function () use ($linhas) { return collect($linhas)->pluck('nome', 'id')->all(); });
$caso('collect(linhas)->pluck(nome)', function () use ($linhas) { return collect($linhas)->pluck('nome')->all(); });
$caso('collect(arrays)->shift()', function () use ($arrays) { $c = collect($arrays); $p = $c->shift(); return array($p, $c->count()); });
$caso('collect(linhas)->first(callback)', function () use ($linhas) { return collect($linhas)->first(function ($l) { return $l->valor > 5; }); });
$caso('collect(linhas)->first(callback, default)', function () use ($linhas) { return collect($linhas)->first(function ($l) { return $l->valor > 99; }, 'nada'); });
$caso('collect(vazia)->first()', function () { return collect(array())->first(); });
$caso('collect(linhas)->last()', function () use ($linhas) { return collect($linhas)->last()->id; });
// sortBy: o PHP 7.4 nao tinha sort estavel; o 8.0+ tem (empates mantem a ordem)
$caso('collect(linhas)->sortBy(valor) (empate 10.50)', function () use ($linhas) { return collect($linhas)->sortBy('valor')->map(function ($l) { return $l->id; })->all(); });
$caso('collect(linhas)->sortBy(valor)->values()', function () use ($linhas) { return collect($linhas)->sortBy('valor')->values()->map(function ($l) { return $l->id; })->all(); });
$caso('collect(linhas)->sortByDesc(valor) (empate 10.50)', function () use ($linhas) { return collect($linhas)->sortByDesc('valor')->map(function ($l) { return $l->id; })->all(); });
$caso('collect(linhas)->sortBy(grupo) (varios empates)', function () use ($linhas) { return collect($linhas)->sortBy('grupo')->map(function ($l) { return $l->id; })->all(); });
$caso('collect(linhas)->sortBy(callback nome)', function () use ($linhas) { return collect($linhas)->sortBy(function ($l) { return $l->nome; })->map(function ($l) { return $l->id; })->all(); });
// sortBy com muitos empates (> 16 linhas: o sort do PHP 7 deixa de ser estavel; o do PHP 8 e). Usos reais: sortBy('fonte_recurso'), sortBy('estrutural'), sortBy('natureza'), sortBy('o15_recurso'), sortByDesc('pageNumber')
$grande = array();
for ($i = 1; $i <= 40; $i++) { $grande[] = (object) array('id' => $i, 'grupo' => 'g' . ($i % 3), 'num' => (string) ($i % 4)); }
$ord = function ($c) { return implode(',', $c->map(function ($l) { return $l->id; })->values()->all()); };
$caso('sortBy(grupo) 40 linhas, 3 valores (empates)', function () use ($grande, $ord) { return $ord(collect($grande)->sortBy('grupo')); });
$caso('sortBy(num texto) 40 linhas, 4 valores', function () use ($grande, $ord) { return $ord(collect($grande)->sortBy('num')); });
$caso('sortByDesc(num) 40 linhas', function () use ($grande, $ord) { return $ord(collect($grande)->sortByDesc('num')); });
$caso('sortBy(callback grupo) 40 linhas', function () use ($grande, $ord) { return $ord(collect($grande)->sortBy(function ($l) { return $l->grupo; })); });
$caso('sortBy(grupo) 12 linhas (<= 16)', function () use ($grande, $ord) { return $ord(collect(array_slice($grande, 0, 12))->sortBy('grupo')); });
$caso('sortBy(id unico) 40 linhas invertidas', function () use ($grande, $ord) { return $ord(collect(array_reverse($grande))->sortBy('id')); });
$caso('collect(ids texto)->sort()', function () use ($ids) { return collect($ids)->sort()->all(); });
$caso('collect(ids texto)->sort()->values()', function () use ($ids) { return collect($ids)->sort()->values()->all(); });
$caso('collect(misto)->sort()', function () { return collect(array('10', 9, '1e1', 'abc', 2.5))->sort()->values()->all(); });
$caso('collect(linhas)->groupBy(grupo)', function () use ($linhas) { return collect($linhas)->groupBy('grupo')->map(function ($g) { return $g->map(function ($l) { return $l->id; })->all(); })->all(); });
$caso('collect(linhas)->groupBy(callback)', function () use ($linhas) { return collect($linhas)->groupBy(function ($l) { return $l->valor; })->keys()->all(); });
$caso('collect(linhas)->keyBy(id)', function () use ($linhas) { return collect($linhas)->keyBy('id')->keys()->all(); });
$caso('collect([])->push->push', function () { $c = collect(array()); $c->push('a'); $c->push('b'); return $c->all(); });
$caso('collect(a)->merge(b) chaves de texto', function () { return collect(array('a' => 1, 'b' => 2))->merge(array('b' => 3, 'c' => 4))->all(); });
$caso('collect(a)->merge(b) chaves numericas', function () { return collect(array(1, 2))->merge(array(3, 4))->all(); });
$caso('collect(ids)->contains(valor texto)', function () use ($ids) { return array(collect($ids)->contains('2'), collect($ids)->contains(2), collect($ids)->contains('9')); });
$caso('collect(linhas)->contains(chave, valor)', function () use ($linhas) { return collect($linhas)->contains('nome', 'Alfa'); });
$caso('collect(linhas)->contains(callback)', function () use ($linhas) { return collect($linhas)->contains(function ($l) { return $l->id == 4; }); });
$caso('collect(a)->diff(b)', function () { return collect(array('1', '2', '3', '5'))->diff(array(2, '3'))->all(); });
$caso('collect(a)->search(valor)', function () { return array(collect(array('a', 'b', '2', 2))->search('2'), collect(array('a', 'b', '2', 2))->search(2, true), collect(array('a'))->search('z')); });
$caso('collect(a)->has(chave)', function () { return array(collect(array('a' => null, 'b' => 1))->has('a'), collect(array('b' => 1))->has('x'), collect(array('b' => 1))->has(array('b', 'x'))); });
$caso('collect(ids)->unique()->values()', function () use ($ids) { return collect($ids)->unique()->values()->all(); });
$caso('collect(linhas)->flatMap', function () use ($arrays) { return collect($arrays)->flatMap(function ($a) { return array($a['o11_descricao'], $a['ano']); })->all(); });
$caso('collect(linhas)->whereIn(id, [..])', function () use ($linhas) { return collect($linhas)->whereIn('id', array(1, 2))->map(function ($l) { return $l->id; })->values()->all(); });
$caso('collect(linhas)->whereNotIn(id, [..])', function () use ($linhas) { return collect($linhas)->whereNotIn('id', array('1', '2'))->map(function ($l) { return $l->id; })->values()->all(); });
$caso('collect(linhas)->where(chave, valor)', function () use ($linhas) { return collect($linhas)->where('grupo', 'a')->map(function ($l) { return $l->id; })->values()->all(); });
$caso('collect(linhas)->where(chave, op, valor)', function () use ($linhas) { return collect($linhas)->where('valor', '>', 5)->map(function ($l) { return $l->id; })->values()->all(); });
$caso('collect(linhas)->reject(callback)', function () use ($linhas) { return collect($linhas)->reject(function ($l) { return $l->exclusao == 't'; })->map(function ($l) { return $l->id; })->values()->all(); });
$caso('collect(a)->isEmpty / isNotEmpty', function () { return array(collect(array())->isEmpty(), collect(array(0))->isEmpty(), collect(array(1))->isNotEmpty()); });
$caso('collect(linhas)->when(cond, callback) / unless', function () use ($linhas) { return array(collect($linhas)->when(true, function ($c) { return $c->take(1); })->count(), collect($linhas)->unless(true, function ($c) { return $c->take(1); })->count()); });
$caso('collect(a)->toArray (objetos aninhados)', function () use ($obj) { return collect(array($obj(array('a' => 1)), array('b' => collect(array(1, 2)))))->toArray(); });
$caso('collect(a)->toJson / jsonSerialize', function () use ($obj) { $c = collect(array($obj(array('a' => '1')), 'x' => array(1))); return array($c->toJson(), $c->jsonSerialize()); });
$caso('collect(a)->map->toArray ordem de chaves', function () { return collect(array(array('b' => 1, 'a' => 2)))->map(function ($x) { return $x; })->toArray(); });
$caso('collect(a)->pad / take / slice / chunk', function () { $c = collect(array(1, 2, 3, 4, 5)); return array($c->take(2)->all(), $c->slice(1, 2)->values()->all(), $c->chunk(2)->map(function ($x) { return $x->values()->all(); })->all()); });
$caso('collect(a)->count / countBy', function () { return array(collect(array(1, 2))->count(), collect(array('a', 'b', 'a'))->countBy()->all()); });
$caso('collect(a)->median / mode', function () { return array(collect(array(1, 2, 3, 4))->median(), collect(array(1, 1, 2))->mode()); });
$caso('collect(a)->zip / combine / flip', function () { return array(collect(array(1, 2))->zip(array('a', 'b'))->toArray(), collect(array('a', 'b'))->combine(array(1, 2))->all(), collect(array('a' => 1))->flip()->all()); });
$caso('collect(string)->all (collect de nao-array)', function () { return collect('abc')->all(); });
$caso('collect(null)->all', function () { return collect(null)->all(); });

// ---- Str::random e Str::replaceFirst (os unicos Str:: do codigo) -- ver locais no doc
$caso('Str::random(8) tamanho e alfabeto', function () { $r = Str::random(8); return array(strlen($r), (bool) preg_match('/^[A-Za-z0-9]{8}$/', $r)); });
$caso('Str::random() padrao 16', function () { return strlen(Str::random()); });
foreach (array(array('a', 'X', 'banana'), array('', 'X', 'banana'), array('z', 'X', 'banana'), array('an', '', 'banana'), array('1', '9', 'a1b1'), array('A', 'x', 'abc')) as $c) {
    $caso("Str::replaceFirst('{$c[0]}', '{$c[1]}', '{$c[2]}')", function () use ($c) { return Str::replaceFirst($c[0], $c[1], $c[2]); });
}
// ---- Arr::get (62 usos)
$dados = array('a' => 1, 'b' => array('c' => 2, 'd' => null), 'x.y' => 'literal', 3 => 'tres', 'obj' => (object) array('k' => 'v'), 'e' => '');
foreach (array(array('a'), array('b.c'), array('b.d'), array('b.d', 'padrao'), array('b.z', 'padrao'), array('x.y'), array('3'), array(3), array('obj.k'), array('e', 'padrao'), array(null), array(null, 'padrao'), array('b.c.d', 'padrao'), array('a', function () { return 'cb'; }), array('z', function () { return 'cb'; })) as $c) {
    $nome = 'Arr::get($dados, ' . json_encode($c[0]) . (isset($c[1]) ? ', ' . (is_object($c[1]) ? 'Closure' : json_encode($c[1])) : '') . ')';
    $caso($nome, function () use ($dados, $c) { return count($c) > 1 ? Arr::get($dados, $c[0], $c[1]) : Arr::get($dados, $c[0]); });
}
$caso('Arr::get(null, "a", "p")', function () { return Arr::get(null, 'a', 'p'); });
$caso('Arr::get(string, "a", "p")', function () { return Arr::get('abc', 'a', 'p'); });
$caso('Arr::get(ArrayObject, "a")', function () { return Arr::get(new ArrayObject(array('a' => 7)), 'a'); });
$caso('Arr::get(Collection, "a")', function () { return Arr::get(collect(array('a' => 8)), 'a'); });
// ---- helpers globais usados (inventario: e, tap, value, last, blank, collect, with)
$caso('e()', function () { return array(e('<a href="x">&amp;</a>'), e("a'b"), e(null), e(1.5)); });
$caso('e(valor, doubleEncode false)', function () { return e('&amp; &', false); });
$caso('tap(valor, callback)', function () { return tap(array(1), function (&$v) { $v[] = 2; }); });
$caso('tap(objeto, callback)', function () { return tap((object) array('a' => 1), function ($o) { $o->a = 2; }); });
$caso('value(valor / closure)', function () { return array(value(5), value(function () { return 6; }), value(function ($x) { return $x . '!'; }, 'a')); });
$caso('last / head', function () { return array(last(array(1, 2, 3)), head(array(1, 2, 3)), last(array()), head(array())); });
$caso('blank / filled', function () { return array(blank(''), blank(' '), blank(null), blank(0), blank(false), blank(array()), blank('0'), filled('a')); });
$caso('with(valor, callback)', function () { return array(with(3, function ($x) { return $x * 2; }), with(3)); });
$caso('data_get(array/objeto, caminho)', function () { return array(data_get(array('a' => array('b' => 1)), 'a.b'), data_get((object) array('a' => (object) array('b' => 2)), 'a.b'), data_get(array('a' => array(array('b' => 1), array('b' => 2))), 'a.*.b'), data_get(array(), 'x', 'pad')); });
$caso('optional / transform', function () { return array(optional(null)->x, optional((object) array('x' => 1))->x, optional(null, function ($v) { return 1; })); });
$caso('class_basename', function () { return array(class_basename('App\Domain\Foo'), class_basename(new stdClass)); });
$caso('funcoes removidas existem?', function () { return array(function_exists('array_pluck'), function_exists('str_random'), function_exists('array_get'), function_exists('str_slug'), function_exists('str_contains')); });
$caso('str_contains (PHP 8 nativo x polyfill)', function () { return array(str_contains('abc', 'b'), str_contains('abc', ''), str_contains('', ''), str_contains('abc', 'B')); });
