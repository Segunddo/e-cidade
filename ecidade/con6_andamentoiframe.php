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

  require(modification("libs/db_stdlib.php"));
  require(modification("libs/db_conecta.php"));
  parse_str($HTTP_SERVER_VARS['QUERY_STRING'], $__qs); unset($__qs['this'], $__qs['GLOBALS']); extract($__qs);
?>

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<meta http-equiv="Expires" CONTENT="0">
<link href="estilos.css" rel="stylesheet" type="text/css">
</head>
<Script>
 function abreJanelaAndamentos(numeroOrdem) {
   window.open("con6_andamentolista.php?ordem="+numeroOrdem,'','width=580,height=400');
 }
 function abreJanelaAnexos(numOrd) {
   window.open("con6_andamentoimagens.php?ordem="+numOrd,'','width=600,height=500');
 }
</Script>

<body bgcolor=#CCCCCC leftmargin="0" topmargin="0" marginwidth="0" marginheight="0" onLoad="a=1" >
<table width="100%" border="0" cellspacing="0" cellpadding="0">
  <tr> 
    <td height="400" align="left" valign="top" bgcolor="#CCCCCC">
<?php
  // SQL que localiza andamentos a serem exibidos
  $result = db_query("select o.codordem,  o.dataprev,to_char(o.dataordem,'DD/MM/YYYY') as dataordem, o.descricao, o.id_usuario, o.usureceb, o.coddepto,
		  			 p.descrdepto, u.nome, no.nome as nomeusureceb , to_char(o.dtrecebe,'DD/MM/YYYY') as dtrecebe
					 from db_ordem o
  					 inner join db_depusu d on d.coddepto = o.coddepto  
        			 inner join db_depart p  on p.coddepto = o.coddepto
					 inner join db_usuarios u on u.id_usuario = o.id_usuario
					 left outer join db_usuarios no on no.id_usuario = o.usureceb
					 where o.usureceb is null and o.coddepto in 
					 (select de.coddepto from db_depart de inner join db_depusu du on du.coddepto=de.coddepto where du.id_usuario = $DB_id_usuario)
					 and o.codordem not in(select codordem from db_ordemfim)

  					 union

  					 select o.codordem,o.dataprev, to_char(o.dataordem,'DD/MM/YYYY') as dataordem, o.descricao, o.id_usuario, o.usureceb, o.coddepto,
		  			 p.descrdepto, u.nome, no.nome as nomeusureceb ,to_char(o.dtrecebe,'DD/MM/YYYY') as dtrecebe
					 from db_ordem o
        			 inner join db_depart p  on p.coddepto = o.coddepto
					 inner join db_usuarios u on u.id_usuario = o.id_usuario
					 left outer join db_usuarios no on no.id_usuario = o.usureceb
  					 where (o.usureceb = $DB_id_usuario or  o.usureceb='0')  and
  					 o.codordem not in(select codordem from db_ordemfim) order by dataprev ".(@$ordem==""?"desc":@$ordem)."");
							   
							   
  $num = ($result ? pg_numrows($result) : null);
  if ($num==0) {
    echo "
          <table width=\"100%\" border=\"1\" align=\"center\" cellpadding=\"0\" cellspacing=\"0\">
            <tr> 
               <td nowrap bgcolor=\"#CDCDFF\"  style=\"font-size:13px\"><div align=\"center\"><strong>Consulta retornou sem resultados.</strong></div></td>
            </tr>
          </table>
		";
  } else {
    echo "
          <table width=\"100%\" border=\"1\" align=\"center\" cellpadding=\"0\" cellspacing=\"0\">
            <tr align=\"center\"   bgcolor=\"#CDCDFF\"  style=\"font-size:11px\">
              <td width=\"2%\">&nbsp;</td>
              <td width=\"2%\">&nbsp;</td>
              <td width=\"6%\">Cod.</td>
              <td width=\"10%\" title=\"Data do recebimento pelo usuário\">Recebido</td>
              <td width=\"10%\">Data</td>
              <td width=\"20%\"  nowrap>Data de Previsão &nbsp;</td><td title='Clique para mudar a ordem de exibição' style='border: 1px #transparent'><a href='con6_andamentoiframe.php?ordem=".(isset($ordem) && $ordem == 'asc'?'desc':'asc')."'><img border='0' src='imagens/cubeb1.gif' width='20' height='20'></img></a> </td>
              <td width=\"20%\">Cadastrado por:</td>
              <td width=\"20%\">Destinat&aacute;rio:</td>
              <td width=\"20%\">Departamento:</td>
              <td width=\"20%\">Destinat&aacute;rio anterior:</td>
           </tr>
        ";
	for ($i=0;$i<$num;$i++) {
       //Loaliza o destinatario do ultimo andamento, caso a ordem tenha mais de um andamento.
	   $ordemAtual = ($result ? pg_result($result,$i,"codordem") : null);
	   $selecionaDestinatarioUltimoAndamento = db_query("select o.codordem, o.dtini, o.id_usuario, u.nome 
	                                                    from db_ordemandam o
														inner join db_usuarios u on u.id_usuario = o.id_usuario
													    where o.codordem = $ordemAtual
														order by o.dtini, o.codandam
													   ");
	   $numReg = ($selecionaDestinatarioUltimoAndamento ? pg_numrows($selecionaDestinatarioUltimoAndamento) : null);
	   if ($numReg > 1) {
	     $nomeUltimoDestinatario = ($selecionaDestinatarioUltimoAndamento ? pg_result($selecionaDestinatarioUltimoAndamento,$numReg-2,"nome") : null);
		 $tag = "<td onclick=\"abreJanelaAndamentos($ordemAtual)\">+</td>";
	   } else {
	     $nomeUltimoDestinatario = "";
		 if ($numReg == 1) {
		   $tag = "<td onclick=\"abreJanelaAndamentos($ordemAtual)\">+</td>";
		 } else {
		   $tag = "<td>&nbsp;</td>";
		 }
	   }
	   
	   // Define a cor do fundo da linha
	   if ($i%2==0) {$cor="#97B5E6";} else {$cor="#E796A4";}
	   // mostra imagem com link sinalizando que esta ordem tem arquivo anexo.
	   $pesquisaImagem = db_query("select codordem from db_ordemimagens where codordem = $ordemAtual limit 1");
	   $numPesquisaImagem = ($pesquisaImagem ? pg_numrows($pesquisaImagem) : null);
	   if ($numPesquisaImagem == 0) {
	     $tagAnexo = "<td>&nbsp;</td>";
	   } else {
	     $tagAnexo = "<td onclick=\"abreJanelaAnexos(".($pesquisaImagem ? pg_result($pesquisaImagem,0,"codordem") : null).")\">a&nbsp;</td>";
	   }
	   $tag2     = "onClick=\"parent.location.href='con6_ordemandamento.php?cod_ord_and=".($result ? pg_result($result,$i,"codordem") : null)."'\"";
              if(($result ? pg_result($result,$i,"nomeusureceb") : null)==''){
                  $cor="#999999";
              }
       echo "
           <tr align=\"center\" onMouseOut=\"document.getElementById('descr_$i').style.visibility='hidden'\" onMouseOver=\"document.getElementById('descr_$i').style.visibility='visible'\"  style=\"font-size:12px\" bgcolor=\"". $cor ."\" style=\"cursor:hand\" >
            ".$tag."
            ".$tagAnexo."
             <td ".$tag2.">".($result ? pg_result($result,$i,"codordem") : null)."&nbsp;</td>
             <td ".$tag2.">".($result ? pg_result($result,$i,"dtrecebe") : null)."&nbsp;</td>
             <td ".$tag2.">".($result ? pg_result($result,$i,"dataordem") : null)."&nbsp;</td>
             <td ".$tag2." colspan='2'>".db_formatar(($result ? pg_result($result,$i,"dataprev") : null),'d')."&nbsp;</td>
             <td ".$tag2.">".($result ? pg_result($result,$i,"nome") : null)."&nbsp;</td>
             <td ".$tag2.">".($result ? pg_result($result,$i,"nomeusureceb") : null)."&nbsp;</td>
             <td ".$tag2.">".($result ? pg_result($result,$i,"descrdepto") : null)."&nbsp;</td>
             <td ".$tag2.">".$nomeUltimoDestinatario."&nbsp;</td>
           </tr>
	  <tr>
	  <td>
	  <table id='descr_$i' bgcolor='#cccccc' style='position:absolute;visibility:hidden;border: 2px outset #cccccc'>
	    <tr style=\"font-size:13px\">
		<td colspan=\"4\"> Descrição ordem ".($result ? pg_result($result,$i,"codordem") : null).": ".str_replace("\n","<br>",($result ? pg_result($result,$i,"descricao") : null))."&nbsp;</td>
	    </tr>
	  </table>  
	  </td>
	  </tr>
           ";
    }
    echo"
         </table> 
        ";
  }
?>
	
	</td>
  </tr>
</table>
</body>
</html>