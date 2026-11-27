<?php
// Cada funcao tem UM caso. Os comentarios dizem se o analisador deve (CANDIDATO) ou nao (OK) apontar o uso do resultado.
function sem_checar($conn) {
    $rs = pg_query($conn, "select 1");
    $n = pg_num_rows($rs);                               // CANDIDATO linha 5
    return $n;
}
function checa_com_if($conn) {
    $rs = pg_query($conn, "select 1");
    if (!$rs) { return 0; }
    return pg_num_rows($rs);                             // OK
}
function checa_identico($conn) {
    $rs = db_query($conn, "select 1");
    if ($rs === false) { die("erro"); }
    return pg_fetch_assoc($rs);                          // OK
}
function usa_na_propria_condicao($conn) {
    $rs = pg_query($conn, "select 1");
    if (pg_num_rows($rs) > 0) { return 1; }              // CANDIDATO linha 20: usar o resultado na condicao nao o checa
    return 0;
}
function atribui_na_condicao($conn) {
    if (!$rs = pg_query($conn, "select 1")) { return 0; }
    return pg_num_rows($rs);                             // OK
}
function com_or_die($conn) {
    $rs = pg_query($conn, "select 1") or die("erro");
    return pg_num_rows($rs);                             // OK
}
function com_silencio_sem_checar($conn) {
    $rs = @pg_query($conn, "select 1");
    return pg_numrows($rs);                              // CANDIDATO linha 33
}
function reatribui($conn, $x) {
    $rs = pg_query($conn, "select 1");
    $rs = $x;
    return pg_num_rows($rs);                             // OK: deixou de ser o resultado da consulta
}
function checa_com_is_resource($conn) {
    $rs = pg_query($conn, "select 1");
    if (is_resource($rs)) { return pg_num_rows($rs); }  // OK
    return 0;
}
function fopen_sem_checar() {
    $fd = fopen("/tmp/x", "w");
    fputs($fd, "a");                                     // CANDIDATO linha 47
}
function escopos_separados($conn) {
    $rs = pg_query($conn, "select 1");
    $f = function () { $rs = 5; return pg_num_rows($rs); };   // OK: outro escopo
    return $f;
}
function ordem_errada($conn) {
    $rs = db_query($conn, "select 1");
    if (pg_numrows($rs) == 0 || !$rs) { return 0; }      // CANDIDATO linha 56: o uso vem ANTES da checagem
    return 1;
}
function dao_sql_record($cl) {
    $rs = $cl->sql_record("select 1");
    return pg_numrows($rs);                              // CANDIDATO linha 61: metodo de DAO do e-Cidade
}
function checa_antes_no_mesmo_if($conn) {
    $rs = pg_query($conn, "select 1");
    if (!$rs || pg_num_rows($rs) == 0) { return 0; }     // OK: a checagem vem primeiro
    return 1;
}
