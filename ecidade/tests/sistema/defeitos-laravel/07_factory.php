<?php
// database/factories/ModelFactory.php usa $factory->define (legacy-factories). O que acontece ao carregar?
require '/app/vendor/autoload.php';
try {
    include '/app/database/factories/ModelFactory.php';
    echo "incluiu sem erro\n";
} catch (\Throwable $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}
