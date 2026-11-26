<?php
// Bootstrap da suite: autoload do vendor de cada runtime + bootstrap do e-cidade (autoloader de src/, definicoes,
// handlers), o mesmo que o phpunit.xml do projeto usa. Nao abre conexao nem sessao.
require_once __DIR__ . '/../../vendor/autoload.php';
require_once __DIR__ . '/../../bootstrap.php';
