<?php
// T-102: gera o HTML das 4 capas do Protocolo (Blade do vendor de cada lado) com dados fixos, sem banco. Roda no
// 7.4 e no 8.5; o HTML dos dois e comparado e cada dompdf le o do proprio lado. Uso: php html_capas.php <ecidade> <vendor> <saida>
list(, $e, $v, $out) = $argv;
require "$v/autoload.php";
require "$e/std/DBDate.php";
require "$e/app/Helpers/Imagem.php";
$blade = new Illuminate\View\Compilers\BladeCompiler(new Illuminate\Filesystem\Filesystem, sys_get_temp_dir());
$dados = [
  'instituicao_telefone' => '(51) 3333-4444', 'instituicao_nome' => 'Prefeitura Municipal de São João',
  'instituicao_municipio' => 'São João', 'instituicao_uf' => 'RS', 'instituicao_estado' => 'Rio Grande do Sul',
  'titular_cgm' => '12345', 'titular_nome' => 'José da Conceição Ávila', 'titular_cpfcnpj' => '12345678909',
  'titular_logradouro' => 'Rua Açores, 100', 'titular_bairro' => 'Centro', 'titular_municipio' => 'São João',
  'requerente' => 'Maria Antônia', 'departamento_nome' => '10 - Secretaria de Administração',
  'departamento_transferencia_nome' => '11 - Gabinete', 'data_processo' => '20/11/2026', 'nome_atendente' => 'Atendente Fixo',
  'hora_processo' => '10:30', 'numero_processo' => '123/2026',
  'observacao' => str_repeat('<p>Observação com acentuação: ação, pão, órgão &amp; <b>negrito</b>.</p>', 40),
  'tipo_processo_descricao' => 'Requerimento Genérico', 'nome_usuario_aprovou' => 'Usuário Emissor',
];
$capas = ['capa-do-processo' => 'imagens/files/Brasao.png', 'capa-do-despacho' => 'imagens/files/Brasao.jpg',
          'capa-do-memorando' => 'imagens/files/Brasao.png', 'capa-do-oficio' => 'imagens/files/Brasao.jpg'];
// 3 variacoes por capa: completa; sem logo, sem titular e texto curto; texto longo (varias paginas, palavra sem espaco)
$curta = array_diff_key($dados, array_flip(['titular_cgm', 'titular_nome', 'titular_cpfcnpj', 'titular_logradouro', 'titular_bairro', 'titular_municipio', 'requerente']));
$curta['observacao'] = 'Curta.';
$longa = $dados;
$longa['observacao'] = str_repeat('<p>Parágrafo longo ' . str_repeat('palavra ', 60) . str_repeat('X', 150) . '</p>', 60);
$variacoes = ['' => [$dados, true], '-curta' => [$curta, false], '-longa' => [$longa, true]];
foreach ($capas as $capa => $logo) foreach ($variacoes as $suf => list($base, $comLogo)) {
  $d = $base + ['instituicao_logo' => $comLogo ? App\Helpers\Imagem::caminhoArquivoParaBase64("$e/$logo") : ''];
  $php = $blade->compileString(file_get_contents("$e/resources/views/layouts/documentos-template/$capa.blade.php"));
  ob_start(); extract($d); $__env = null; eval('?>' . $php); $html = ob_get_clean();
  file_put_contents("$out/$capa$suf.html", $html);
  echo $capa, $suf, ' ', strlen($html), "\n";
}
