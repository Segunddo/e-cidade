<?php
// Dubles em memoria das buscas no banco que os Mailables/Notifications do PR fazem (nenhuma conexao e aberta).
// So estas classes sao trocadas; o resto da renderizacao e o codigo do PR. Textos em ISO-8859-1, como a base.
namespace App\Domain\Configuracao\Instituicao\Model {
    class DBConfig { public static function find($id) { return (object)array('logo' => 'logo.png'); } }
}
namespace App\Domain\Configuracao\Instituicao\Repository {
    class InstituicaoRepository { public function find($id) { return new class { public function getNome() { return "Prefeitura de S\xe3o Jo\xe3o"; } }; } }
}
namespace App\Domain\Patrimonial\Contratos\Models {
    class Acordo {
        public $ac16_instit = 1, $ac16_numeroacordo = 12, $ac16_anousu = 2026, $ac16_datainicio = '2026-01-10', $ac16_datafim = '2026-11-25';
        public static function find($id) { return new self; }
    }
    class MensageriaAcordoDia {
        public $id = 5, $dia = 5, $mensageriaAcordo;
        public static function find($id) {
            $m = new self;
            $m->mensageriaAcordo = (object)array(
                'ac51_assunto' => "Acordo [numero]/[ano] vence em [dias] dias",
                'ac51_mensagem' => "O acordo n\xba [numero]/[ano] (in\xedcio [data_inicial], fim [data_final]) vence em [dias] dias. A\xe7\xe3o necess\xe1ria.",
            );
            return $m;
        }
    }
}
namespace App\Domain\Configuracao\Menu\Models {
    class Item { public $descricao = "Anexos da LRF"; public static function find($id) { return new self; } }
}
namespace App\Domain\Configuracao\RelarorioLegal\Model {
    class Relatorio { public $o42_descrrel = "Anexo 3 - RREO"; public static function find($id) { return new self; } }
}
