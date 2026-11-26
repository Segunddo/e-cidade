<?php
// PHP8-12: rotas da base-php74 sem banco e sem instanciar controller (o route:list instancia e um construtor consulta
// o banco). Sobe o app (Laravel 8), troca a RouteCollection por uma que anota onde cada rota foi registrada (arquivo:
// linha), inclusive as que outra rota de mesmo metodo+URI substitui, e depois pergunta a propria colecao qual rota
// responde a cada caminho. Saida: JSON com uma entrada por rota registrada, na ordem de registro.
// Uso (raiz ecidade/, storage gravavel com chaves OAuth descartaveis): php php8_12_rotas.php > rotas.json
require 'vendor/autoload.php';
$app = require 'bootstrap/app.php';

class ColecaoAnotada extends Illuminate\Routing\RouteCollection
{
    public static $log = array();
    public function add(Illuminate\Routing\Route $route)
    {
        $onde = '';
        foreach (debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS) as $f) {
            if (isset($f['file']) && strpos($f['file'], '/vendor/') === false) {
                $onde = str_replace(getcwd() . '/', '', $f['file']) . ':' . $f['line'];
                break;
            }
        }
        self::$log[] = array($route, $onde);
        return parent::add($route);
    }
}
$app['router']->setRoutes(new ColecaoAnotada());
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$col = $app['router']->getRoutes();

$saida = array();
foreach (ColecaoAnotada::$log as $i => $par) {
    list($r, $onde) = $par;
    $acao = $r->getAction('uses');
    $metodos = array_values(array_diff($r->methods(), array('HEAD')));
    // caminho de exemplo: cada {parametro} vira 1 (ou o primeiro valor que casa o where, se houver)
    $caminho = '/' . ltrim(preg_replace_callback('/\{(\w+)\??\}/', function ($m) use ($r) {
        $w = isset($r->wheres[$m[1]]) ? $r->wheres[$m[1]] : null;
        foreach (array('1', 'a', '2026-01-01', 'x1') as $v) { if (!$w || preg_match('#^(' . $w . ')$#', $v)) return $v; }
        return '1';
    }, $r->uri()), '/');
    $responde = array();
    foreach ($metodos as $m) {
        try {
            $q = Illuminate\Http\Request::create($caminho, $m);
            $achou = $col->match($q);
            $responde[$m] = array_search($achou, array_map(function ($p) { return $p[0]; }, ColecaoAnotada::$log), true);
        } catch (Exception $e) {
            $responde[$m] = get_class($e);
        }
    }
    // GET que so le: nome do metodo e corpo (do metodo do controller ou da closure) sem sinal de escrita. O que o
    // corpo delega a outro servico nao e seguido (limite da leitura estatica).
    $leitura = null; $acaoOnde = '';
    if (in_array('GET', $metodos)) {
        try {
            if ($acao instanceof Closure) { $rf = new ReflectionFunction($acao); $nomeM = 'closure'; }
            elseif (is_string($acao) && strpos($acao, '@') !== false) { list($c, $nomeM) = explode('@', $acao); $rf = new ReflectionMethod($c, $nomeM); }
            elseif (is_string($acao) && class_exists($acao)) { $rf = new ReflectionMethod($acao, '__invoke'); $nomeM = '__invoke'; }
            else { $rf = null; }
            if ($rf) {
                $linhas = file($rf->getFileName());
                $corpo = implode('', array_slice($linhas, $rf->getStartLine() - 1, $rf->getEndLine() - $rf->getStartLine() + 1));
                $acaoOnde = str_replace(getcwd() . '/', '', $rf->getFileName()) . ':' . $rf->getStartLine();
                $sinal = '';
                if (preg_match('/(salvar|save|store|criar|create|incluir|inserir|insert|alterar|update|atualiz|excluir|delete|destroy|remover|apagar|processar|gerar|emitir|enviar|importar|exportar|cancel|encerr|inativ|assin|baixar|migr|limpar|reprocess|calcular|lancar)/i', $nomeM, $m)) $sinal = 'nome:' . $m[1];
                elseif (preg_match('/(->save\(|::create\(|->create\(|->update\(|->delete\(|->insert\(|->destroy\(|->forceDelete\(|->sync\(|->attach\(|->detach\(|->increment\(|->decrement\(|DB::(statement|insert|update|delete|unprepared|beginTransaction|transaction)|Storage::(put|delete|move|copy)|dispatch\(|session\(\)->put|->put\(|file_put_contents|unlink\(|Cache::(put|forget|forever))/i', $corpo, $m)) $sinal = 'corpo:' . $m[1];
                $leitura = $sinal === '' ? 'sim' : 'nao ' . $sinal;
            } else { $leitura = 'acao-sem-metodo'; }
        } catch (ReflectionException $e) { $leitura = 'acao-inexistente'; }
    }
    $saida[] = array(
        'ordem' => $i, 'metodos' => $metodos, 'uri' => $r->uri(), 'nome' => $r->getName(),
        'acao' => $acao instanceof Closure ? 'Closure' : (is_string($acao) ? $acao : gettype($acao)),
        'middleware' => array_values($r->middleware()), 'onde' => $onde, 'caminho' => $caminho, 'responde' => $responde,
        'leitura' => $leitura, 'acao_onde' => $acaoOnde,
    );
}
// nomes: quem o getByName do Laravel 8 devolve (ultima rota que ficou na colecao) x a regra do 12+ (primeira)
$nomes = array();
foreach ($col->getRoutes() as $r) {
    if ($n = $r->getName()) { $nomes[$n][] = array_search($r, array_map(function ($p) { return $p[0]; }, ColecaoAnotada::$log), true); }
}
$porNome = array();
foreach ($nomes as $n => $ordens) {
    $porNome[$n] = array('l8' => array_search($col->getByName($n), array_map(function ($p) { return $p[0]; }, ColecaoAnotada::$log), true),
        'l12' => $ordens[0], 'rotas' => $ordens);
}
$incluidos = array_values(array_filter(array_map(function ($f) { return str_replace(getcwd() . '/', '', $f); }, get_included_files()),
    function ($f) { return strpos($f, 'routes/') === 0; }));
echo json_encode(array('rotas' => $saida, 'nomes' => $porNome, 'arquivos_de_rota_carregados' => $incluidos, 'laravel' => $app->version()), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), "\n";
