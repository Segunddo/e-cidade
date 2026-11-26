<?php
// Capas do Protocolo (CapaDoDocumento): mesmo template Blade e mesmas chamadas do Dompdf, dados de exemplo, sem banco.
require __DIR__ . '/lib.php';

use Dompdf\Dompdf;
use Dompdf\Options;
use Illuminate\Container\Container;
use Illuminate\Events\Dispatcher;
use Illuminate\Filesystem\Filesystem;
use Illuminate\View\Compilers\BladeCompiler;
use Illuminate\View\Engines\CompilerEngine;
use Illuminate\View\Engines\EngineResolver;
use Illuminate\View\Factory;
use Illuminate\View\FileViewFinder;

require_once ECIDADE_PATH . 'std/DBDate.php'; // usada pelos templates do memorando e do oficio
@mkdir('/tmp/views', 0777, true);
$files = new Filesystem();
$resolver = new EngineResolver();
$resolver->register('blade', function () use ($files) {
    return new CompilerEngine(new BladeCompiler($files, '/tmp/views'));
});
$view = new Factory($resolver, new FileViewFinder($files, [ECIDADE_PATH . 'resources/views']), new Dispatcher(new Container()));

$dados = [
    'instituicao_nome' => 'Prefeitura Municipal de Exemplo', 'instituicao_estado' => 'DE EXEMPLO',
    'instituicao_telefone' => '(00) 0000-0000', 'instituicao_municipio' => 'Exemplo', 'instituicao_uf' => 'EX',
    'data_processo' => '20/11/2026', 'hora_processo' => '10:30', 'numero_processo' => '123/2026',
    'tipo_processo_descricao' => 'Requerimento de Certidão', 'departamento_nome' => '1 - Protocolo Geral',
    'departamento_transferencia_nome' => '2 - Secretaria de Administração',
    'nome_atendente' => 'Atendente Exemplo', 'nome_usuario_aprovou' => 'Usuario Exemplo',
    'titular_cgm' => '1001', 'titular_nome' => 'Fulano de Tal', 'titular_cpfcnpj' => '000.000.000-00',
    'titular_logradouro' => 'Rua das Flores, 100', 'titular_bairro' => 'Centro', 'titular_municipio' => 'Exemplo',
    'requerente' => 'Fulano de Tal',
    'observacao' => str_repeat('Observação do processo com texto longo para quebrar linha e testar a pagina. ', 40),
];
$capas = ['capa-do-processo', 'capa-do-memorando', 'capa-do-oficio', 'capa-do-despacho'];
foreach ($capas as $capa) {
    $html = $view->make('layouts.documentos-template.' . $capa, $dados)->render();
    $opcoes = new Options();
    $opcoes->set('fontCache', '/tmp/dompdf');
    $opcoes->set('tempDir', '/tmp/dompdf');
    $dompdf = new Dompdf($opcoes);
    $dompdf->loadHtml($html);
    $dompdf->setPaper('A4');
    $dompdf->render();
    $c = $dompdf->getCanvas();
    $c->page_text(30, 811, 'Base: ecidade_exemplo', null, 7, [0, 0, 0]);
    $c->page_text(30, 820, 'host/menu Emissor: Usuario Exemplo Exercício: 2026 Data: 20/11/2026 - 10:30:00', null, 7, [0, 0, 0]);
    $c->page_text(530, 820, 'Página {PAGE_NUM} de {PAGE_COUNT}', null, 7, [0, 0, 0]);
    emitir("dompdf-$capa.pdf", $dompdf->output());
}
