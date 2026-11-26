<?php
// Mede, sem banco e sem rede, a validacao do Laravel 8.73.2 com as regras REAIS dos form requests da base-php74.
// Para cada form request: instancia com dados em memoria, le rules()/messages()/attributes() e roda o Validator com 5 entradas
// (vazia, valida montada pelas regras, chave obrigatoria ausente, todos os campos vazios, todos os campos array).
// Regras que dependem de banco (exists, unique) sao tiradas e listadas. Saida: JSON canonico (mesmo arquivo nos dois PHPs => iguais).
// Uso: php laravel8_validacao_medir.php <pasta ecidade> <saida.json>   (autoload do vendor ao lado deste arquivo ou em $VENDOR)
$deprec = array();
set_error_handler(function ($no, $str) use (&$deprec) {
    if ($no === E_DEPRECATED || $no === E_USER_DEPRECATED) {
        $deprec[preg_replace('#^.*/vendor/#', 'vendor/', $str)] = true;
        return true;
    }
    return false;
});
require (getenv('VENDOR') ?: __DIR__ . '/vendor') . '/autoload.php';

use Illuminate\Filesystem\Filesystem;
use Illuminate\Support\Arr;
use Illuminate\Translation\FileLoader;
use Illuminate\Translation\Translator;
use Illuminate\Validation\Factory;
use Illuminate\Validation\Rules\DatabaseRule;

$raiz = rtrim($argv[1], '/');
$saida = $argv[2];

spl_autoload_register(function ($c) use ($raiz) {
    if (strpos($c, 'App\\') === 0) {
        $f = $raiz . '/app/' . str_replace('\\', '/', substr($c, 4)) . '.php';
        if (is_file($f)) {
            require_once $f;
        }
    }
});

$loader = new FileLoader(new Filesystem(), $raiz . '/resources/lang');
$translator = new Translator($loader, 'pt-br');
$translator->setFallback('en');
$factory = new Factory($translator);

// classes de form request: arquivos de app/ que estendem FormRequest, DBFormRequest ou BaseFormRequest
$classes = array();
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($raiz . '/app', FilesystemIterator::SKIP_DOTS));
foreach ($it as $f) {
    if (substr($f->getFilename(), -4) !== '.php') {
        continue;
    }
    $src = file_get_contents($f->getPathname());
    if (!preg_match('/^class\s+(\w+)\s+extends\s+(FormRequest|DBFormRequest|BaseFormRequest)\b/m', $src, $m) &&
        !preg_match('/^abstract\s+class\s+(\w+)\s+extends\s+(FormRequest|DBFormRequest|BaseFormRequest)\b/m', $src, $m)) {
        continue;
    }
    if (!preg_match('/^namespace\s+([^;]+);/m', $src, $ns)) {
        continue;
    }
    $classes[$ns[1] . '\\' . $m[1]] = $f->getPathname();
}
ksort($classes);

function amostra($regras)
{
    $r = is_array($regras) ? $regras : explode('|', (string) $regras);
    foreach ($r as $x) {
        if (!is_string($x)) {
            continue;
        }
        $nome = strtolower(strtok($x, ':'));
        $arg = strpos($x, ':') !== false ? substr($x, strpos($x, ':') + 1) : '';
        switch ($nome) {
            case 'integer':
                return 1;
            case 'numeric':
                return 1.5;
            case 'boolean':
                return true;
            case 'array':
                return array(1);
            case 'email':
                return 'a@b.com';
            case 'url':
                return 'https://exemplo.com';
            case 'ip':
                return '127.0.0.1';
            case 'json':
                return '{"a":1}';
            case 'date':
                return '2026-01-15';
            case 'date_format':
                return date($arg === 'd/m/Y' ? 'd/m/Y' : ($arg !== '' ? $arg : 'Y-m-d'), 1768478400);
            case 'in':
                return explode(',', $arg)[0];
            case 'digits':
                return str_repeat('1', max(1, (int) $arg));
        }
    }
    return 'abc';
}

$resultado = array('classes' => count($classes), 'sem_regras' => array(), 'erro_ao_ler' => array(), 'regras_de_banco' => array(), 'casos' => array());
foreach ($classes as $classe => $arquivo) {
    require_once $arquivo;
    if (!class_exists($classe)) {
        $resultado['erro_ao_ler'][$classe] = 'classe nao carregou';
        continue;
    }
    try {
        $rc = new ReflectionClass($classe);
        if ($rc->isAbstract()) {
            continue;
        }
        $req = $classe::create('/', 'POST', array());
        $regras = method_exists($req, 'rules') ? $req->rules() : array();
        $mensagens = $req->messages();
        $atributos = $req->attributes();
    } catch (Throwable $e) {
        $resultado['erro_ao_ler'][$classe] = get_class($e) . ': ' . substr($e->getMessage(), 0, 100);
        continue;
    }
    if (empty($regras) || !is_array($regras)) {
        $resultado['sem_regras'][] = $classe;
        continue;
    }
    // tira o que depende de banco
    $limpas = array();
    $banco = array();
    foreach ($regras as $campo => $r) {
        $lista = is_array($r) ? $r : explode('|', (string) $r);
        $mantidas = array();
        foreach ($lista as $x) {
            if (is_string($x) && preg_match('/^(exists|unique):/i', $x)) {
                $banco[] = $campo . ' => ' . strtok($x, ',');
            } elseif (is_object($x) && $x instanceof DatabaseRule) {
                $banco[] = $campo . ' => ' . get_class($x);
            } else {
                $mantidas[] = $x;
            }
        }
        $limpas[$campo] = $mantidas;
    }
    if ($banco) {
        $resultado['regras_de_banco'][$classe] = $banco;
    }

    $campos = array_keys($limpas);
    $valida = array();
    $obrigatorio = null;
    foreach ($limpas as $campo => $r) {
        Arr::set($valida, str_replace('*', '0', $campo), amostra($r));
        if ($obrigatorio === null && in_array('required', array_map('strval', array_filter($r, 'is_string')), true)) {
            $obrigatorio = $campo;
        }
    }
    $vazios = array();
    $arrays = array();
    foreach ($campos as $campo) {
        Arr::set($vazios, str_replace('*', '0', $campo), '');
        Arr::set($arrays, str_replace('*', '0', $campo), array('x'));
    }
    $ausente = $valida;
    if ($obrigatorio !== null) {
        Arr::forget($ausente, str_replace('*', '0', $obrigatorio));
    }
    $entradas = array('vazia' => array(), 'valida' => $valida, 'ausente' => $ausente, 'vazios' => $vazios, 'arrays' => $arrays);
    foreach ($entradas as $nome => $dados) {
        try {
            $v = $factory->make($dados, $limpas, $mensagens, $atributos);
            $passa = !$v->fails();
            $erros = $v->errors()->toArray();
            ksort($erros);
            $caso = array('passa' => $passa, 'erros' => $erros);
            if ($passa) {
                $caso['validado'] = $v->validated();
            }
        } catch (Throwable $e) {
            $caso = array('excecao' => get_class($e) . ': ' . substr($e->getMessage(), 0, 120));
        }
        $resultado['casos'][$classe][$nome] = $caso;
    }
}
$resultado['deprecations'] = array_keys($deprec);
sort($resultado['deprecations']);
ksort($resultado['regras_de_banco']);
ksort($resultado['erro_ao_ler']);
sort($resultado['sem_regras']);
file_put_contents($saida, json_encode($resultado, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR) . "\n");
echo 'PHP ' . PHP_VERSION . ': ' . count($classes) . " form requests, " . count($resultado['casos']) . " com regras, " .
    count($resultado['regras_de_banco']) . " com exists/unique, " . count($resultado['erro_ao_ler']) . " nao leram\n";
