<?php

namespace ECidade\Tributario\Caixa\Entity\Collection;

use ECidade\Tributario\Library\ArrayCollection;
use ECidade\Tributario\Caixa\Entity\Recibo;

final class ReciboCollection extends ArrayCollection
{
    public function add($recibo) // PHP 8 (LSP): a mae nao restringe o tipo; os chamadores passam Recibo
    {
        parent::add($recibo);
    }
}
