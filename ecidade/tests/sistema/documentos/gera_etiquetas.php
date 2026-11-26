<?php
// Etiquetas Pimaco do Patrimonio (EtiquetaModelo01/02Builder + EtiquetasPimacoPDF reais) e QR Code (PHPQRCode, como ArrecadacaoPixService e mod_imprime2).
require __DIR__ . '/lib.php';

use App\Domain\Patrimonial\Patrimonio\Builders\EtiquetaModelo01Builder;
use App\Domain\Patrimonial\Patrimonio\Builders\EtiquetaModelo02Builder;

// EtiquetasPimacoPDF::gerar() faz addTag + WriteHTML(render) + Output em arquivo, e o construtor dela nao repassa o tempDir do mPDF
// (no runtime o padrao, vendor/mpdf/mpdf/tmp, e gravavel; aqui o vendor e somente leitura). Esta subclasse do Pimaco repete essas
// tres linhas com o tempDir em /tmp e devolve o PDF em string; as tags vem dos Builders reais.
class EtiquetasParaTeste extends \Proner\PhpPimaco\Pimaco
{
    private $dados;

    public function __construct($dados, $template, $path)
    {
        parent::__construct($template, $path, '/tmp/mpdf/');
        $this->dados = $dados;
    }

    public function pdfEmString()
    {
        foreach ($this->dados as $tag) {
            $this->addTag($tag);
        }
        $this->pdf->WriteHTML($this->render());
        return $this->pdf->Output('', 'S');
    }
}

foreach ([1 => EtiquetaModelo01Builder::class, 2 => EtiquetaModelo02Builder::class] as $n => $classe) {
    $tags = [];
    for ($i = 1; $i <= 12; $i++) {
        $b = new $classe();
        $b->setInstituicao('PREFEITURA MUNICIPAL DE EXEMPLO');
        $b->setCodigo(1000 + $i);
        $b->setPlaca(sprintf('%06d', 5000 + $i));
        $b->setDescricao("Cadeira giratoria modelo $i com descricao longa");
        $b->setBarcode(sprintf('%06d', 5000 + $i));
        $b->create();
        $tags[] = $b->getEtiqueta();
    }
    $dir = ECIDADE_PATH . 'app/Domain/Patrimonial/Patrimonio/Relatorios/TemplatesEtiquetas/';
    $e = new EtiquetasParaTeste($tags, "A4351_MODELO0$n", $dir);
    emitir("pimaco-modelo0$n.pdf", $e->pdfEmString());
}

foreach (['L' => 4, 'M' => 5] as $nivel => $tam) {
    \PHPQRCode\QRcode::png('https://exemplo.gov.br/pix/00020126580014br.gov.bcb.pix0136123e4567-e89b-12d3-a456-426655440000', "/tmp/qr_$nivel.png", $nivel, $tam, 2);
    emitir("qr-$nivel.png", file_get_contents("/tmp/qr_$nivel.png"));
}

// QR da propria Pimaco (Tag::qrcode -> endroid/qr-code 2.5 -> bacon/bacon-qr-code 1.0): o codigo proprio so usa barras, mas a
// biblioteca expoe o QR e as duas dependencias excluem o PHP 8 no composer; aqui se mede se geram o mesmo QR no 8.5.
foreach (['pimaco-qrcode.pdf' => false, 'pimaco-qrcode-rotulo.pdf' => true] as $nome => $comRotulo) {
    $tags = [];
    for ($i = 1; $i <= 6; $i++) {
        $tag = new \Proner\PhpPimaco\Tag();
        $tag->setPadding(2);
        $tag->p("PLACA " . (5000 + $i))->br();
        $url = "https://exemplo.gov.br/bem/" . (5000 + $i);
        $comRotulo ? $tag->qrcode($url, 'BEM ' . (1000 + $i)) : $tag->qrcode($url);
        $tags[] = $tag;
    }
    $e = new EtiquetasParaTeste($tags, 'A4351_MODELO01', ECIDADE_PATH . 'app/Domain/Patrimonial/Patrimonio/Relatorios/TemplatesEtiquetas/');
    emitir($nome, $e->pdfEmString());
}
