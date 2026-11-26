<?php
// AutenticacaoRequest declarada duas vezes com o mesmo nome completo: qual arquivo o autoload carrega?
require '/app/vendor/autoload.php';
$c = 'App\Domain\Tributario\ITBI\Requests\AutenticacaoRequest';
echo 'class_exists: ', var_export(class_exists($c), true), "\n";
echo 'arquivo: ', str_replace('/app/', '', (new ReflectionClass($c))->getFileName()), "\n";
echo 'regras: ', implode(',', array_keys((new $c)->rules())), "\n";
