<?php
/*
 *     E-cidade Software Publico para Gestao Municipal                
 *  Copyright (C) 2009  DBSeller Servicos de Informatica             
 *                            www.dbseller.com.br                     
 *                         e-cidade@dbseller.com.br                   
 *                                                                    
 *  Este programa e software livre; voce pode redistribui-lo e/ou     
 *  modifica-lo sob os termos da Licenca Publica Geral GNU, conforme  
 *  publicada pela Free Software Foundation; tanto a versao 2 da      
 *  Licenca como (a seu criterio) qualquer versao mais nova.          
 *                                                                    
 *  Este programa e distribuido na expectativa de ser util, mas SEM   
 *  QUALQUER GARANTIA; sem mesmo a garantia implicita de              
 *  COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM           
 *  PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais  
 *  detalhes.                                                         
 *                                                                    
 *  Voce deve ter recebido uma copia da Licenca Publica Geral GNU     
 *  junto com este programa; se nao, escreva para a Free Software     
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA          
 *  02111-1307, USA.                                                  
 *  
 *  Copia da licenca no diretorio licenca/licenca_en.txt 
 *                                licenca/licenca_pt.txt 
 */

include(modification("libs/db_conn.php"));
require(modification("libs/db_stdlib.php"));
define('FPDF_FONTPATH','fpdf151/font/');
require(modification('fpdf151/fpdf.php'));

parse_str($HTTP_SERVER_VARS["QUERY_STRING"], $__qs); unset($__qs['this'], $__qs['GLOBALS']); extract($__qs);

if(!($conn = pg_connect("host=$DB_SERVIDOR dbname=$DB_BASE port=$DB_PORTA user=$DB_USUARIO password=$DB_SENHA"))) {
  echo "Erro(10) ao tentar conectar no servidor.";
  exit;
}

  $campos = db_query("select nomecam,posxmodelo,posymodelo from db_carnescampos where codmodelo = $codigo");
  $result = db_query("select * from cgm limit 10");
  $nomeimg = db_query("select nomemodelo,imgmodelo,orientacao from db_carnesimg where codmodelo = $codigo");
  $arquivo = str_replace(" ","_",($nomeimg ? pg_result($nomeimg,0,"nomemodelo") : null)).".jpg";
  db_query("begin");
  $oid = ($nomeimg ? pg_result($nomeimg,0,"imgmodelo") : null);
  try { pg_loexport($oid,$arquivo); } catch (\Throwable $e) { }
  db_query("end");
  $orientacao = ($nomeimg ? pg_result($nomeimg,0,"orientacao") : null);
  if($orientacao == "R") {
    $orientacao = "P";
	$W = 595;
	$H = 842;
  } else {
    $orientacao = "L";
	$W = 842;
	$H = 595;
  }
  $pdf = new FPDF($orientacao,"pt","A4");
  $pdf->Open();

  $numrows = ($result ? pg_numrows($result) : null);
  $numfields = ($campos ? pg_numrows($campos) : null);
  
  for($i = 0;$i < $numrows;$i++) {
    $pdf->AddPage();
    $pdf->image("tmp/".$arquivo,0,0,$W,$H);
    $pdf->SetFont('Arial','',10);
    $pdf->SetTextColor(0,0,0);
	for($j = 0;$j < $numfields;$j++) {
      db_fieldsmemory($campos,$j);	  
      $pdf->Text($posxmodelo,$posymodelo,($result ? pg_result($result,$i,$nomecam) : null));    
    }
  }
  $pdf->Output();
?>