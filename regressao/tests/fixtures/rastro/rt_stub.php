<?php
// Substituto neutro do rt.php: so devolve os valores, para provar que as sondas nao mudam o comportamento.
function __rt_a($id, $nome, $valor) {}
function __rt_c($id, $fn, $args, $ret) { return $ret; }
function __rt_t($id, $v) { return $v; }
function __rt_r($id, $v) { return $v; }
function __rt_x($id, $e) {}
