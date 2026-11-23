<?php

require dirname(__DIR__, 4) . '/runtime-85/pimaco-vendor/autoload.php';

use App\Domain\Patrimonial\Patrimonio\Builders\EtiquetaModelo01Builder;
use App\Domain\Patrimonial\Patrimonio\Builders\EtiquetaModelo02Builder;
use App\Domain\Patrimonial\Patrimonio\Relatorios\EtiquetasPimacoPDF;
use Proner\PhpPimaco\Tag;

define('ECIDADE_PATH', dirname(__DIR__, 3) . '/');

$outputDir = sys_get_temp_dir() . '/ecidade-pimaco-output/';
if (!is_dir($outputDir . 'tmp') && !mkdir($outputDir . 'tmp', 0777, true) && !is_dir($outputDir . 'tmp')) {
    throw new RuntimeException("Nao foi possivel criar {$outputDir}tmp");
}
if (!chdir($outputDir)) {
    throw new RuntimeException("Nao foi possivel usar {$outputDir}");
}

function emitir(string $nome, string $conteudo): void
{
    echo json_encode([
        'nome' => $nome,
        'b64' => base64_encode($conteudo),
    ], JSON_THROW_ON_ERROR), PHP_EOL;
}

function gerarPdf(array $tags, string $template): string
{
    $path = ECIDADE_PATH . 'app/Domain/Patrimonial/Patrimonio/Relatorios/TemplatesEtiquetas/';
    $relatorio = new EtiquetasPimacoPDF($tags, $template, $path);
    $arquivo = $relatorio->gerar();
    $conteudo = file_get_contents($arquivo);

    if ($conteudo === false || !unlink($arquivo)) {
        throw new RuntimeException("Nao foi possivel ler/remover {$arquivo}");
    }

    return $conteudo;
}

$builders = [
    1 => EtiquetaModelo01Builder::class,
    2 => EtiquetaModelo02Builder::class,
];

foreach ($builders as $modelo => $builderClass) {
    $tags = [];

    for ($i = 1; $i <= 12; $i++) {
        $builder = new $builderClass();
        $builder->setInstituicao('PREFEITURA MUNICIPAL DE EXEMPLO');
        $builder->setCodigo(1000 + $i);
        $builder->setPlaca(sprintf('%06d', 5000 + $i));
        $builder->setDescricao("Cadeira giratoria modelo $i com descricao longa");
        $builder->setBarcode(sprintf('%06d', 5000 + $i));
        $builder->create();
        $tags[] = $builder->getEtiqueta();
    }

    emitir("pimaco-modelo0$modelo.pdf", gerarPdf($tags, "A4351_MODELO0$modelo"));
}

foreach (['pimaco-qrcode.pdf' => false, 'pimaco-qrcode-rotulo.pdf' => true] as $nome => $comRotulo) {
    $tags = [];

    for ($i = 1; $i <= 6; $i++) {
        $tag = new Tag();
        $tag->setPadding(2);
        $tag->p('PLACA ' . (5000 + $i))->br();
        $url = 'https://exemplo.gov.br/bem/' . (5000 + $i);

        if ($comRotulo) {
            $tag->qrcode($url, 'BEM ' . (1000 + $i));
        } else {
            $tag->qrcode($url);
        }

        $tags[] = $tag;
    }

    emitir($nome, gerarPdf($tags, 'A4351_MODELO01'));
}
