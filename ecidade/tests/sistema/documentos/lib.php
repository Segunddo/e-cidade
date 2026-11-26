<?php
// Base dos geradores de documento sem banco. Roda no 7.4 e no 8.5 (docker/composer-85/roda-isolado.sh).
// Cada documento sai em stdout como uma linha JSON {"nome":..., "b64":...}; avisos do PHP vao para stderr.
error_reporting(E_ALL);
ini_set('display_errors', 'stderr');
define('ECIDADE_PATH', '/app/');
define('ECIDADE_TEMP_MPDF_PATH', '/tmp/mpdf/');
@mkdir('/tmp/mpdf', 0777, true);
@mkdir('/tmp/dompdf', 0777, true);
date_default_timezone_set('America/Sao_Paulo');
require '/app/vendor/autoload.php';
require_once '/app/src/Core/Autoloader.php'; // namespace ECidade\ (como bootstrap.php, sem as outras dependencias do bootstrap)
$ecidadeLoader = new ECidade\Core\Autoloader();
$ecidadeLoader->addNamespace('ECidade\\', ECIDADE_PATH . 'src/', false, false); // sem modification()
$ecidadeLoader->register();

function emitir($nome, $bytes)
{
    echo json_encode(['nome' => $nome, 'b64' => base64_encode($bytes)]), "\n";
}
