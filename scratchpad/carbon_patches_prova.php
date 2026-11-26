<?php
// PHP8-55: prova antes/depois dos patches do Carbon 3 aplicados: pega do PROPRIO arquivo (antes = arvore original, depois = arvore corrigida)
// a expressao de cada uso e a executa com a entrada real do uso. Sem banco, sem rede.
// Uso: php carbon_patches_prova.php <vendor com nesbot/carbon> <raiz ecidade> (relogio fixo 2030-01-01 23:30 America/Sao_Paulo)
// eval(): so executa expressoes lidas de arquivos do proprio repositorio (app/Domain), em medicao local sem rede e sem banco; nunca entrada externa.
error_reporting(E_ALL & ~E_DEPRECATED);
date_default_timezone_set('America/Sao_Paulo');
require $argv[1] . '/autoload.php';
use Carbon\Carbon;
$raiz = rtrim($argv[2], '/');
Carbon::setTestNow(Carbon::create(2030, 1, 1, 23, 30, 0, 'America/Sao_Paulo'));
setlocale(LC_TIME, array('pt_BR', 'pt_BR.ISO-8859-1', 'ptb'));   // como o boot do AppServiceProvider com a T-139

class_alias('Carbon\\Carbon', 'Carbon');   // o eval() abaixo roda sem os "use" do arquivo de origem

// a expressao de um uso: junta as linhas do arquivo a partir da N-esima que contem $agulha ate fechar o comando (';', ',' ou '{') e aplica $re (1o grupo)
function expr($arq, $agulha, $re, $n = 1)
{
    $t = explode("\n", file_get_contents($arq));
    foreach ($t as $i => $l) {
        if (strpos($l, $agulha) !== false && --$n === 0) {
            $s = '';
            for ($k = $i; $k < count($t); $k++) {
                $s .= ' ' . trim($t[$k]);
                if (preg_match('/[;,{]\s*$/', $t[$k])) { break; }
            }
            $s = trim(preg_replace('/\s+/', ' ', $s));
            if (!preg_match($re, $s, $m)) { throw new Exception("regex nao casou em: $s"); }
            return $m[1];
        }
    }
    throw new Exception("agulha '$agulha' nao achada em $arq");
}
function roda($id, $arq, $agulha, $re, $vars, $n = 1)
{
    try {
        $e = expr($arq, $agulha, $re, $n);
        extract($vars);
        $e = str_replace('$this->', '$self->', $e);
        $r = eval('return ' . $e . ';');
        $o = $r instanceof DateTimeInterface ? get_class($r) . '|' . $r->format('Y-m-d H:i:s P') : (is_string($r) ? $r . ' [' . bin2hex($r) . ']' : var_export($r, true));
    } catch (Throwable $x) {
        $o = 'EXC ' . get_class($x) . ': ' . substr(preg_replace('/\s+/', ' ', $x->getMessage()), 0, 80);
    }
    echo "$id | $o\n";
}
$A = $raiz . '/app/Domain/';
$apro = $A . 'Financeiro/Contabilidade/Services/ApropriacaoDecimoFeriasService.php';
$ts = Carbon::now()->getTimestamp();   // DB_datausu = time()
$req = new class($ts) { private $t; function __construct($t) { $this->t = $t; } function get($k) { return $this->t; } };
$atrib = '/= (.*);$/';

roda('P01a ApropriacaoDecimoFeriasService:61 nomeMes (c01_data=2025-03-01)', $apro, '"nomeMes" =>', '/"nomeMes" => (.*),$/', array('paramentro' => (object) array('c01_data' => Carbon::create(2025, 3, 1))));
roda('P01b ApropriacaoDecimoFeriasService:73 nomeMes proximaCompetenciaApropriar (2025-03)', $apro, '$nomeMes = ', $atrib, array('ano' => 2025, 'mes' => 3), 1);
roda('P01c ApropriacaoDecimoFeriasService:98 nomeMes proximaCompetenciaExtornar (2025-03)', $apro, '$nomeMes = ', $atrib, array('apropriacao' => (object) array('c145_exercicio' => 2025, 'c145_mes' => 3)), 2);
roda('P01d ImprimirRelatorioTemplateService:87 dataAtualExtenso (agora = 2030-01-01)', $A . 'Configuracao/GeradorRelatorio/Services/ImprimirRelatorioTemplateService.php', '$dataAtualExtenso = ', $atrib, array('date' => Carbon::now()));
roda('P02a RegistroAulaController:67 DB_datausu = time() as 23:30 locais', $A . 'Educacao/Escola/Controllers/RegistroAulaController.php', '$dataSistema = Carbon::createFromTimestamp', $atrib, array('request' => $req));
roda('P02b RegistroAulaController:77 DB_datausu', $A . 'Educacao/Escola/Controllers/RegistroAulaController.php', "\$filtros['dataSistema'] = ", $atrib, array('request' => $req));
roda('P02c CalendarioController:83 DB_datausu', $A . 'Educacao/Escola/Controllers/CalendarioController.php', '$dataSistema = Carbon::createFromTimestamp', $atrib, array('request' => $req));
foreach (array('passado (trava de 15 min atras)' => 15, 'futuro (relogio atrasado: 15 min a frente)' => -15) as $rot => $min) {
    roda("P03 ApropriacaoDecimoFeriasService:382 diffInMinutes $rot", $apro, 'diffInMinutes', '/if \((.*) > 10\) \{$/', array('data' => Carbon::now()->subMinutes($min)));
}
$rh = $A . 'RecursosHumanos/Pessoal/';
foreach (array('1990-05-20', '2012-12-31', '2031-06-01') as $nasc) {
    $dep = (object) array('rh31_dtnasc' => $nasc);
    roda("P04a RhDependController:73 idade nasc=$nasc", $rh . 'Controller/RhDependController.php', '$dependente->idade = ', $atrib, array('dependente' => $dep));
    $o = new class($nasc) { public $attributes; function __construct($n) { $this->attributes = array('rh31_dtnasc' => $n); } };
    roda("P04b RhDepend:27 idade nasc=$nasc", $rh . 'Model/RhDepend.php', "Carbon::parse(\$this->attributes", '/return (.*);$/', array('self' => $o));
    roda("P04c AjudaCustoService:246 idadeLancamento nasc=$nasc, 1 mes", $rh . 'Services/AjudaCusto/AjudaCustoService.php', '$idadeLancamento = ', $atrib, array('dependente' => $dep, 'ajudaCusto' => (object) array('rh312_quantidade' => 1)));
}
