<?php
// rt.php - biblioteca de execucao das sondas. Carregada por auto_prepend_file SO no vhost instrumentado.
// Compativel com PHP 7.4 e 8.5 (sem tipos de propriedade, sem `match`, sem union types).
//
// Liga quando a requisicao traz o cabecalho `X-Rastro-Id: <id>` (ou, em CLI, a variavel RASTRO_ID);
// escreve /tmp/rastro/<id>.jsonl. Sem id, as funcoes so devolvem o valor (custo ~zero).
// Excecoes tratadas pelo proprio e-Cidade (pagina "Erro interno") nao passam por aqui: o Executor le
// o log da aplicacao (extension/log/error.log). Aqui entram avisos/notices e erros fatais.

final class RtRastro
{
    public static $on = false;
    private static $arq = '';
    private static $buf = array();
    private static $seq = 0;
    private static $teto = 2000000;
    private static $truncado = false;
    private static $anterior = null;
    private static $nProbes = 0;
    private static $prefixos = array('/var/www/html/tmp/ecidade-rastro/', '/var/www/html/');
    // Tipos de erro que o handler da aplicacao receberia sem nos (o PHP nao expoe a mascara de um handler ja registrado).
    // Padrao: todos. No vhost do rastro vem de RASTRO_MASCARA (= php.error_reporting do e-Cidade).
    private static $mascara = E_ALL;

    public static function liga()
    {
        $id = isset($_SERVER['HTTP_X_RASTRO_ID']) ? $_SERVER['HTTP_X_RASTRO_ID'] : getenv('RASTRO_ID');
        if (!is_string($id) || !preg_match('/^[A-Za-z0-9_.-]{1,80}$/', $id)) {
            return;
        }
        if (!is_dir('/tmp/rastro')) {
            @mkdir('/tmp/rastro', 0777, true);
        }
        self::$arq = '/tmp/rastro/' . $id . '.jsonl';
        @file_put_contents(self::$arq, '');
        $teto = getenv('RASTRO_TETO');
        if ($teto !== false && ctype_digit($teto)) {
            self::$teto = (int) $teto;
        }
        $m = isset($_SERVER['RASTRO_MASCARA']) ? $_SERVER['RASTRO_MASCARA'] : getenv('RASTRO_MASCARA');
        if (is_string($m) && ctype_digit($m)) {
            self::$mascara = (int) $m;
        }
        $pref = getenv('RASTRO_PREFIXOS');
        if (is_string($pref) && $pref !== '') {
            self::$prefixos = explode(':', $pref);
        }
        self::$on = true;
        self::$anterior = set_error_handler(array('RtRastro', 'erro'));
        register_shutdown_function(array('RtRastro', 'fim'));
    }

    // ---- resumo de valores ---------------------------------------------------------------------

    private static function utf8($s)
    {
        return function_exists('mb_convert_encoding') ? mb_convert_encoding($s, 'UTF-8', 'ISO-8859-1') : $s;
    }

    private static function canon($v, $prof, &$orc)
    {
        if ($orc <= 0) {
            return '~';
        }
        if ($v === null) { $t = 'N'; }
        elseif (is_bool($v)) { $t = $v ? 'true' : 'false'; }
        elseif (is_int($v)) { $t = (string) $v; }
        elseif (is_float($v)) { $t = var_export($v, true); }
        elseif (is_string($v)) { $t = 's' . strlen($v) . ':' . (strlen($v) > 200 ? substr($v, 0, 200) . '..' . md5($v) : $v); }
        elseif (is_resource($v)) { $t = self::tipoRecurso($v); }
        elseif (is_object($v)) {
            $c = get_class($v);
            if ($c === 'PgSql\\Result') { $t = 'pgresult'; }
            elseif ($c === 'PgSql\\Connection') { $t = 'pgconn'; }
            elseif ($v instanceof Closure) { $t = 'Closure'; }
            elseif ($prof <= 0) { $t = $c . '{..}'; }
            else {
                $partes = array();
                foreach ((array) $v as $k => $x) {
                    $partes[] = str_replace("\0", '.', (string) $k) . '=' . self::canon($x, $prof - 1, $orc);
                    if (count($partes) >= 40) { $partes[] = '..'; break; }
                }
                $t = $c . '{' . implode(',', $partes) . '}';
            }
        } elseif (is_array($v)) {
            if ($prof <= 0) {
                $t = 'array(' . count($v) . ')';
            } else {
                $partes = array();
                foreach ($v as $k => $x) {
                    $partes[] = $k . '=>' . self::canon($x, $prof - 1, $orc);
                    if (count($partes) >= 60) { $partes[] = '..(' . count($v) . ')'; break; }
                }
                $t = '[' . implode(',', $partes) . ']';
            }
        } else {
            $t = gettype($v);
        }
        $orc -= strlen($t);
        return $t;
    }

    private static function tipoRecurso($r)
    {
        $tipo = get_resource_type($r);
        if (strpos($tipo, 'pgsql result') === 0) { return 'pgresult'; }
        if (strpos($tipo, 'pgsql link') === 0) { return 'pgconn'; }
        return 'resource:' . $tipo;   // nunca o numero do recurso
    }

    public static function resumo($v)
    {
        if ($v === '__unset__' || $v === '__expr__') {
            return array('t' => 'marca', 'r' => $v);
        }
        if ($v === null) { $t = 'null'; }
        elseif (is_bool($v)) { $t = 'bool'; }
        elseif (is_int($v)) { $t = 'int'; }
        elseif (is_float($v)) { $t = 'float'; }
        elseif (is_string($v)) { $t = 'string'; }
        elseif (is_array($v)) { $t = 'array'; }
        elseif (is_resource($v)) { $t = self::tipoRecurso($v); }
        elseif (is_object($v)) {
            $c = get_class($v);
            $t = ($c === 'PgSql\\Result') ? 'pgresult' : (($c === 'PgSql\\Connection') ? 'pgconn' : 'object');
        } else { $t = gettype($v); }
        $orc = 6000;
        $c = self::canon($v, 3, $orc);
        $r = array('t' => $t, 'r' => self::utf8(substr($c, 0, 300)), 'h' => md5($c));
        if (is_string($v)) { $r['n'] = strlen($v); }
        if (is_array($v)) { $r['n'] = count($v); }
        return $r;
    }

    // ---- eventos -------------------------------------------------------------------------------

    private static function local()
    {
        // frames: [0] local() em evento(), [1] evento() em __rt_x(), [2] __rt_x() no ponto de chamada do codigo do usuario
        $bt = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 3);
        $f = isset($bt[2]['file']) ? $bt[2]['file'] : '';
        $l = isset($bt[2]['line']) ? $bt[2]['line'] : 0;
        return array(self::relativo($f), $l);
    }

    private static function relativo($f)
    {
        foreach (self::$prefixos as $p) {
            if ($p !== '' && strncmp($f, $p, strlen($p)) === 0) {
                return substr($f, strlen($p));
            }
        }
        return $f;
    }

    public static function evento($kind, $sonda, $nome, $v, $fl = null, $extra = null)
    {
        if (!self::$on || self::$truncado) {
            return;
        }
        if (self::$seq >= self::$teto) {
            self::$truncado = true;
            self::$buf[] = json_encode(array('s' => self::$seq, 'k' => 'T'));
            self::descarrega();
            return;
        }
        // A aplicacao instala o proprio handler de erros em algum ponto do inicio: nas 20 primeiras sondas
        // reverifica a cada uma, depois a cada 20 (custo desprezivel), e volta a ficar na frente.
        if (($sonda !== 0) && (++self::$nProbes <= 20 || self::$nProbes % 20 === 0)) {
            self::garante();
        }
        if ($fl === null) {
            $fl = self::local();
        }
        $e = array('s' => ++self::$seq, 'p' => $sonda, 'f' => $fl[0], 'l' => $fl[1], 'k' => $kind, 'n' => $nome, 'v' => $v);
        if ($extra !== null) {
            $e['a'] = $extra;
        }
        self::$buf[] = json_encode($e, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE | JSON_PARTIAL_OUTPUT_ON_ERROR);
        if (count(self::$buf) >= 500) {
            self::descarrega();
        }
    }

    public static function descarrega()
    {
        if (self::$buf) {
            @file_put_contents(self::$arq, implode("\n", self::$buf) . "\n", FILE_APPEND);
            self::$buf = array();
        }
    }

    /** Se a aplicacao trocou o handler de erros depois de nos, volta a ficar na frente (encadeando o dela). */
    private static function garante()
    {
        $atual = set_error_handler(array('RtRastro', 'erro'));
        if ($atual === array('RtRastro', 'erro')) {
            restore_error_handler();
            return;
        }
        self::$anterior = $atual;
    }

    public static function erro($no, $msg, $arq = '', $lin = 0)
    {
        $recebidos = func_get_args();   // o 7.4 entrega 5 argumentos ($errcontext), o 8.x entrega 4: repassar IGUAL
        $rotulo = array(E_WARNING => 'warning', E_NOTICE => 'notice', E_DEPRECATED => 'deprecated',
            E_USER_WARNING => 'user_warning', E_USER_NOTICE => 'user_notice', E_USER_DEPRECATED => 'user_deprecated',
            E_USER_ERROR => 'user_error', E_STRICT => 'strict', E_RECOVERABLE_ERROR => 'recoverable');
        $v = array('t' => 'aviso', 'r' => self::utf8(substr((string) $msg, 0, 300)), 'h' => md5((string) $msg));
        $v['sup'] = !(error_reporting() & $no);
        self::evento('w', 0, isset($rotulo[$no]) ? $rotulo[$no] : (string) $no, $v, array(self::relativo((string) $arq), (int) $lin));
        // So repassa o que o handler da aplicacao receberia sem nos (a mascara dele); o resto cai no tratamento padrao do PHP.
        if (self::$anterior !== null && (self::$mascara & $no)) {
            return call_user_func_array(self::$anterior, $recebidos);
        }
        return false;
    }

    public static function fim()
    {
        if (!self::$on) {
            return;
        }
        $e = error_get_last();
        if ($e && ($e['type'] & (E_ERROR | E_PARSE | E_CORE_ERROR | E_COMPILE_ERROR | E_USER_ERROR | E_RECOVERABLE_ERROR))) {
            $v = array('t' => 'fatal', 'r' => self::utf8(substr($e['message'], 0, 300)), 'h' => md5($e['message']));
            self::evento('e', 0, 'fatal', $v, array(self::relativo($e['file']), (int) $e['line']));
        }
        self::descarrega();
    }
}

function __rt_a($id, $nome, $valor)
{
    if (RtRastro::$on) { RtRastro::evento('a', $id, $nome, RtRastro::resumo($valor)); }
}

function __rt_c($id, $fn, $args, $ret)
{
    if (RtRastro::$on) {
        $a = array();
        foreach ($args as $x) { $a[] = RtRastro::resumo($x); }
        RtRastro::evento('c', $id, $fn, RtRastro::resumo($ret), null, $a);
    }
    return $ret;
}

function __rt_t($id, $v)
{
    if (RtRastro::$on) { RtRastro::evento('b', $id, 'cond', array('t' => 'bool', 'r' => $v ? 'true' : 'false')); }
    return $v;
}

function __rt_r($id, $v)
{
    if (RtRastro::$on) { RtRastro::evento('r', $id, '', RtRastro::resumo($v)); }
    return $v;
}

function __rt_x($id, $e)
{
    if (RtRastro::$on) {
        $c = get_class($e);
        RtRastro::evento('x', $id, $c, array('t' => 'excecao', 'r' => substr($c . ': ' . $e->getMessage(), 0, 300), 'h' => md5($c . $e->getMessage())));
    }
}

RtRastro::liga();
