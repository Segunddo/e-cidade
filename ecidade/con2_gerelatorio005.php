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
include(modification("libs/db_sessoes.php"));
include(modification("libs/db_usuariosonline.php"));


 if($limite==0){
  $limit="";
 }else{
   $limit=" limit ".$limite;
 }
  $resultsql = @db_query(str_replace('\\','',$sql.@$limit ));
  $result = db_query("select max(codger) + 1 from db_gerador");

  if(@$libera==true){
      db_query("update  db_gerador set  nomeger='$nome', tituloger='$titulo', finalidadeger='$finalidade', sqlger='$sql', limiteger=$limite,visualizacao='$visualizacao',intercalar1='$intercalar1', intercalar2='$intercalar2', pcabecaltura=$pcabecaltura,pcorpaltura=$pcorpaltura  where codger=$codigo ");
  }else{
     $resultsql = @db_query(str_replace('\\','',$sql.@$limit ));
     $result = db_query("select max(codger) + 1 from db_gerador");
     $codger = ($result ? pg_result($result,0,0) : null);
     $codger = $codger==""?"1":$codger;
      db_query("insert into db_gerador values($codger,'$nome','$titulo','$finalidade','$sql',$limite,'$visualizacao','$intercalar1','$intercalar2',$pcabecaltura,$pcorpaltura)");
  }


 $HTTP_SERVER_VARS['SCRIPT_FILENAME'];
 $root = substr($HTTP_SERVER_VARS['SCRIPT_FILENAME'],0,strrpos($HTTP_SERVER_VARS['SCRIPT_FILENAME'],"/"));
 $nomeok=preg_replace(" ","",$nome);
 $arquivo = ($root."/"."gerador/".$nomeok."002.php");
 $fd = fopen($arquivo,"w");
 $fd && fputs($fd,'<?php '."\n");
 $fd && fputs($fd,'  include(modification("fpdf151/pdfger.php"));'."\n");
 $fd && fputs($fd,'  // variaveis de cabeçalho;'."\n");
 $fd && fputs($fd,'  db_postmemory($HTTP_SERVER_VARS);'."\n");
 $fd && fputs($fd,'if($limite==0||$limite=="" ){'."\n");
 $fd && fputs($fd,'  unset($limit);'."\n");
 $fd && fputs($fd,'}else{'."\n");
 $fd && fputs($fd,'  $limit=" limit ".$limite;'."\n");
 $fd && fputs($fd,'}'."\n");
 $fd && fputs($fd,'  $resultsql = db_query(str_replace(\'\\\\\',\'\',\''.$sql.'\'.@$limit));'."\n");
 $fd && fputs($fd,'  if($resultsql==false){'."\n");
 $fd && fputs($fd,'    echo "Verifique os dados a serem gerados.<br>";'."\n");
 $fd && fputs($fd,'    echo "'.$sql.'";'."\n");
 $fd && fputs($fd,'  }'."\n");
 $fd && fputs($fd,'  $head1 = $nome;'."\n");
 $fd && fputs($fd,'  $head2 = "";'."\n");
 $fd && fputs($fd,'  $head3 = "";'."\n");
 $fd && fputs($fd,'  $head4 = $titulo;'."\n");
 $fd && fputs($fd,'  $head5 = "";'."\n");
 $fd && fputs($fd,'  $head6 = "";'."\n");
 $fd && fputs($fd,'  $head7 = "";'."\n");
 $fd && fputs($fd,'  $head8 = substr($finalidade, 0,30);'."\n");
 $fd && fputs($fd,'  $head9 = substr($finalidade,30,30);'."\n");
 $fd && fputs($fd,'  $DB_instit = db_getsession("DB_instit");'."\n");
 $fd && fputs($fd,'  $pdf = new PDF();'."\n");
 $fd && fputs($fd,'  $pdf->Open();'."\n");
 $fd && fputs($fd,'  $pdf->AliasNbPages();'."\n");
 $fd && fputs($fd,' $pdf->AddPage($visualizacao);'."\n");
 $fd && fputs($fd,' // monta cabecalho do relatório'."\n");
 $fd && fputs($fd,' $pdf->setY(40);'."\n");
 $fd && fputs($fd,' $pdf->setX(5);'."\n");
 $fd && fputs($fd,' $clrotulolov = new rotulolov;'."\n");
 $fd && fputs($fd,' $fm_numfields = pg_numfields($resultsql);'."\n");
 $fd && fputs($fd,' $tamanho = array();'."\n");
 $fd && fputs($fd,' if($visualizacao=="L"){'."\n");
 $fd && fputs($fd,'   $maxlargura=300;'."\n");
 $fd && fputs($fd,' }else{'."\n");
 $fd && fputs($fd,'       $maxlargura=185;'."\n");
 $fd && fputs($fd,' }'."\n");
 $fd && fputs($fd,' $nova="";'."\n");

  $resultsql = db_query(str_replace('\\','',$sql));
  for ($i = 0;$i < $fm_numfields;$i++){
    $v="cabecfonte_".$i;
    $fd && fputs($fd,' $cabecfonte_'.$i.'="'.$$v.'";'."\n");
    $cabecfonte=$$v;

    $v="cabeccortexto_".$i;
    $fd && fputs($fd,' $cabeccortexto_'.$i.'="'.$$v.'";'."\n");
    $cabeccortexto=$$v;

    $v="cabectamanho_".$i;
    $fd && fputs($fd,' $cabectamanho_'.$i.'="'.$$v.'";'."\n");
    $cabectamanho=$$v;

    $v="cabecn_".$i;
    $fd && fputs($fd,' $cabecn_'.$i.'="'.@$$v.'";'."\n");
    $cabecn=@$$v;

    $v="cabeci_".$i;
    $fd && fputs($fd,' $cabeci_'.$i.'="'.@$$v.'";'."\n");
    $cabeci=@$$v;

    $v="cabecs_".$i;
    $fd && fputs($fd,' $cabecs_'.$i.'="'.@$$v.'";'."\n");
    $cabecs=@$$v;

    $v="cabeccortexto_".$i;
    $fd && fputs($fd,' $cabeccortexto_'.$i.'="'.$$v.'";'."\n");
    $cabeccortexto=$$v;

    $v="cabeccorborda_".$i;
    $fd && fputs($fd,' $cabeccorborda_'.$i.'="'.$$v.'";'."\n");
    $cabeccorborda=$$v;

    $v="cabeccorfundo_".$i;
    $fd && fputs($fd,' $cabeccorfundo_'.$i.'="'.$$v.'";'."\n");
    $cabeccorfundo=$$v;

    $v="cabecaltura_".$i;
    $fd && fputs($fd,' $cabecaltura_'.$i.'="'.$$v.'";'."\n");
    $cabecaltura=$$v;

    $v="cabeclargura_".$i;
    $fd && fputs($fd,' $cabeclargura_'.$i.'="'.$$v.'";'."\n");
    $cabeclargura=$$v;

//corpo

    $v="corpfonte_".$i;
    $fd && fputs($fd,' $corpfonte_'.$i.'="'.$$v.'";'."\n");
    $corpfonte=$$v;

    $v="corpopcao_".$i;
    $fd && fputs($fd,' $corpopcao_'.$i.'="'.$$v.'";'."\n");
    $corpopcao=$$v;

    $v="corpcortexto_".$i;
    $fd && fputs($fd,' $corpcortexto_'.$i.'="'.$$v.'";'."\n");
    $corpcortexto=$$v;

    $v="corptamanho_".$i;
    $fd && fputs($fd,' $corptamanho_'.$i.'="'.$$v.'";'."\n");
    $corptamanho=$$v;

    $v="corpn_".$i;
    $fd && fputs($fd,' $corpn_'.$i.'="'.@$$v.'";'."\n");
    $corpn=@$$v;

    $v="corpi_".$i;
    $fd && fputs($fd,' $corpi_'.$i.'="'.@$$v.'";'."\n");
    $corpi=@$$v;

    $v="corps_".$i;
    $fd && fputs($fd,' $corps_'.$i.'="'.@$$v.'";'."\n");
    $corps=@$$v;

    $v="corpcorborda_".$i;
    $fd && fputs($fd,' $corpcorborda_'.$i.'="'.$$v.'";'."\n");
    $corpcorborda=$$v;

    $v="corpcorfundo_".$i;
    $fd && fputs($fd,' $corpcorfundo_'.$i.'="'.$$v.'";'."\n");
    $corpcorfundo=$$v;

    $v="corpaltura_".$i;
    $fd && fputs($fd,' $corpaltura_'.$i.'="'.$$v.'";'."\n");
    $corpaltura=$$v;

    $v="corplargura_".$i;
    $fd && fputs($fd,' $corplargura_'.$i.'="'.$$v.'";'."\n");
    $corplargura=$$v;

    $coluna = ($resultsql ? pg_fieldname($resultsql,$i) : null);

    if(@$libera==true){
      //db_query("update  db_gerpref set coluna ='$coluna',cabecfonte='$cabecfonte', cabectamanho=$cabectamanho, cabecn='$cabecn', cabeci='$cabeci', cabecs='$cabecs',cabeccortexto='$cabeccortexto', cabeccorborda='$cabeccorborda', cabeccorfundo='$cabeccorfundo', cabecaltura=$cabecaltura, cabeclargura='$cabeclargura', corpfonte='$corpfonte',corpopcao='$corpopcao',corptamanho=$corptamanho, corpn='$corpn', corpi='$corpi',corps='$corps', corpcortexto='$corpcortexto', corpcorborda='$corpcorborda', corpcorfundo='$corpcorfundo', corpaltura='$corpaltura', corplargura='$corplargura' where codger=$codigo");
      if($i==0){
        db_query("delete from db_gerpref where codger=$codigo");
      }
      db_query("insert into db_gerpref values ($codigo,'$coluna','$cabecfonte',$cabectamanho,'$cabecn','$cabeci','$cabecs','$cabeccortexto','$cabeccorborda','$cabeccorfundo',$cabecaltura,$cabeclargura,'$corpfonte','$corpopcao',$corptamanho,'$corpn','$corpi','$corps','$corpcortexto','$corpcorborda','$corpcorfundo',$corpaltura,$corplargura)");

    }else{
      db_query("insert into db_gerpref values ($codger,'$coluna','$cabecfonte',$cabectamanho,'$cabecn','$cabeci','$cabecs','$cabeccortexto','$cabeccorborda','$cabeccorfundo',$cabecaltura,$cabeclargura,'$corpfonte','$corpopcao',$corptamanho,'$corpn','$corpi','$corps','$corpcortexto','$corpcorborda','$corpcorfundo',$corpaltura,$corplargura)");
    }
 }
 $fd && fputs($fd,' for ($i = 0;$i < $fm_numfields;$i++){'."\n");
 $fd && fputs($fd,'   $cabecfonte="cabecfonte_".$i;'."\n");
 $fd && fputs($fd,'   $cabectamanho="cabectamanho_".$i;'."\n");
 $fd && fputs($fd,'   $n="cabecn_".$i;'."\n");
 $fd && fputs($fd,'   $it="cabeci_".$i;'."\n");
 $fd && fputs($fd,'   $s="cabecs_".$i;'."\n");
 $fd && fputs($fd,'   $pdf->SetFont($$cabecfonte,@$$s.@$$n.@$$it ,$$cabectamanho);'."\n");

 $fd && fputs($fd,'   $cabeccortexto="cabeccortexto_".$i;'."\n");
 $fd && fputs($fd,'   $cor= explode("#", $$cabeccortexto);'."\n");
 $fd && fputs($fd,'   $pdf->SetTextColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'   $cabeccorborda="cabeccorborda_".$i;'."\n");
 $fd && fputs($fd,'   $cor= explode("#", $$cabeccorborda);'."\n");
 $fd && fputs($fd,'   $pdf->SetDrawColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'   $cabeccorfundo="cabeccorfundo_".$i;'."\n");
 $fd && fputs($fd,'   $cor= explode("#", $$cabeccorfundo);'."\n");
 $fd && fputs($fd,'   $pdf->SetFillColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");



 $fd && fputs($fd,'   $clrotulolov->label(pg_fieldname($resultsql,$i));'."\n");
 $fd && fputs($fd,'   $cabecaltura="cabecaltura_".$i;'."\n");
 $fd && fputs($fd,'   $cabeclargura="cabeclargura_".$i;'."\n");
 $fd && fputs($fd,'   $x=$pdf->getx();'."\n");
 $fd && fputs($fd,'   if($$cabeclargura+$x > $maxlargura){'."\n");
 $fd && fputs($fd,'     $pdf->ln($$cabecaltura);//não funciona '."\n");
 $fd && fputs($fd,'     $pdf->setX(5);'."\n");
 $fd && fputs($fd,'   }'."\n");
 $fd && fputs($fd,'   $pdf->Cell($$cabeclargura,$$cabecaltura,$clrotulolov->titulo,"LRBT",($i==($fm_numfields-1)?1:0),"",1);'."\n");
 $fd && fputs($fd,'   if($clrotulolov->tamanho==""){'."\n");
 $fd && fputs($fd,' 	  $tamanho[$i] = 20;'."\n");
 $fd && fputs($fd,'   }else{'."\n");
 $fd && fputs($fd,' 	  $tamanho[$i] = (($clrotulolov->tamanho>strlen($clrotulolov->titulo)?$clrotulolov->tamanho:strlen($clrotulolov->titulo))*2)+2;'."\n");
 $fd && fputs($fd,'   }'."\n");
 $fd && fputs($fd,' }'."\n");
 $fd && fputs($fd,'  $pdf->ln(2);'."\n");
 $fd && fputs($fd,' // corpo do relatório'."\n");
 $fd && fputs($fd,' $linha = 0;'."\n");
 $fd && fputs($fd,' for ($xi=0;$xi<pg_numrows($resultsql);$xi++){'."\n");
 $fd && fputs($fd,'   $pdf->setX(5);'."\n");
 $fd && fputs($fd,'   //db_fieldsmemory($resultsql,$i);'."\n");
 $fd && fputs($fd,'   for ($c=0;$c<$fm_numfields;$c++){'."\n");
 $fd && fputs($fd,'     $corpfonte="corpfonte_".$c;'."\n");
 $fd && fputs($fd,'     $corptamanho="corptamanho_".$c;'."\n");
 $fd && fputs($fd,'     $n="corpn_".$c;'."\n");
 $fd && fputs($fd,'     $it="corpi_".$c;'."\n");
 $fd && fputs($fd,'     $s="corps_".$c;'."\n");
 $fd && fputs($fd,'     $pdf->SetFont($$corpfonte,$$s.$$n.$$it ,$$corptamanho);'."\n");

 $fd && fputs($fd,'   $corpcortexto="corpcortexto_".$c;'."\n");
 $fd && fputs($fd,'   $cor= explode("#", $$corpcortexto);'."\n");
 $fd && fputs($fd,'   $pdf->SetTextColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");

 $fd && fputs($fd,'   $corpcorborda="corpcorborda_".$c;'."\n");
 $fd && fputs($fd,'   $cor= explode("#", $$corpcorborda);'."\n");
 $fd && fputs($fd,'   $pdf->SetDrawColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");

 $fd && fputs($fd,'   //cores que irão intercalar'."\n");
 $fd && fputs($fd,'   $corpcorfundo="corpcorfundo_".$c;'."\n");
 $fd && fputs($fd,'   if($$corpcorfundo =="255#255#255"){'."\n");
 $fd && fputs($fd,'     if($xi % 2!=0){'."\n");
 $fd && fputs($fd,'      $cor= explode("#","'.$intercalar1.'");'."\n");
 $fd && fputs($fd,'      $pdf->SetFillColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'     }else{'."\n");
 $fd && fputs($fd,'      $cor= explode("#","'.$intercalar2.'");'."\n");
 $fd && fputs($fd,'      $pdf->SetFillColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'     }'."\n");
 $fd && fputs($fd,'   }else{'."\n");
 $fd && fputs($fd,'         $corpcorfundo="corpcorfundo_".$c;'."\n");
 $fd && fputs($fd,'         $cor= explode("#",$$corpcorfundo);'."\n");
 $fd && fputs($fd,'         $pdf->SetFillColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'   }'."\n");




 $fd && fputs($fd,'     $corpaltura="corpaltura_".$c;'."\n");
 $fd && fputs($fd,'     $corplargura="corplargura_".$c;'."\n");
 $fd && fputs($fd,'     $x=$pdf->getx();'."\n");
 $fd && fputs($fd,'     if($$corplargura+$x > $maxlargura) {'."\n");
 $fd && fputs($fd,'      $pdf->ln($$corpaltura);'."\n");
 $fd && fputs($fd,'      $pdf->setX(5);'."\n");
 $fd && fputs($fd,'     }'."\n");

 $fd && fputs($fd,'     $y=$pdf->getY();'."\n");
 $fd && fputs($fd,'     if($visualizacao=="L"){'."\n");
 $fd && fputs($fd,'       if($y>=180){'."\n");
 $fd && fputs($fd,'         $nova=true; '."\n");
 $fd && fputs($fd,'       }'."\n");
 $fd && fputs($fd,'     }else{'."\n");
 $fd && fputs($fd,'           if($y>=270){'."\n");
 $fd && fputs($fd,'              $nova=true; '."\n");
 $fd && fputs($fd,'            }'."\n");
 $fd && fputs($fd,'     }'."\n");
 $fd && fputs($fd,'     if($c<($fm_numfields-1)){'."\n");
 $fd && fputs($fd,'       $quebra=0;'."\n");
 $fd && fputs($fd,'     }else{'."\n");
 $fd && fputs($fd,'          $quebra=1;'."\n");
 $fd && fputs($fd,'     } '."\n");
 $fd && fputs($fd,'     $pdf->Cell($$corplargura,$$corpaltura,pg_result($resultsql,$xi,$c),1,$quebra,"",1);'."\n");
 $fd && fputs($fd,'   } '."\n");
 $fd && fputs($fd,'   if($nova==true){'."\n");
 $fd && fputs($fd,'     $nova = false;'."\n");
 $fd && fputs($fd,'     //Imprime cabeçalho, caso pdf tenha mais de uam pagina '."\n");
 $fd && fputs($fd,'     $pdf->AddPage($visualizacao);'."\n");
 $fd && fputs($fd,'     $pdf->setX(5);'."\n");
 $fd && fputs($fd,'     for ($cabec=0;$cabec < $fm_numfields;$cabec++){'."\n");
 $fd && fputs($fd,'       $cabecfonte="cabecfonte_".$cabec;'."\n");
 $fd && fputs($fd,'       $cabectamanho="cabectamanho_".$cabec;'."\n");
 $fd && fputs($fd,'       $n="cabecn_".$cabec;'."\n");
 $fd && fputs($fd,'       $it="cabeci_".$cabec;'."\n");
 $fd && fputs($fd,'       $s="cabecs_".$cabec;'."\n");
 $fd && fputs($fd,'       $pdf->SetFont($$cabecfonte,$$s.$$n.$$it ,$$cabectamanho);'."\n");

 $fd && fputs($fd,'       $cabeccortexto="cabeccortexto_".$cabec;'."\n");
 $fd && fputs($fd,'       $cor= explode("#", $$cabeccortexto);'."\n");
 $fd && fputs($fd,'       $pdf->SetTextColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'       $cabeccorborda="cabeccorborda_".$cabec;'."\n");
 $fd && fputs($fd,'       $cor= explode("#", $$cabeccorborda);'."\n");
 $fd && fputs($fd,'       $pdf->SetDrawColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'       $cabeccorfundo="cabeccorfundo_".$cabec;'."\n");
 $fd && fputs($fd,'       $cor= explode("#", $$cabeccorfundo);'."\n");
 $fd && fputs($fd,'       $pdf->SetFillColor(@$cor[0],@$cor[1],@$cor[2]);'."\n");
 $fd && fputs($fd,'       $clrotulolov->label(pg_fieldname($resultsql,$cabec));'."\n");
 $fd && fputs($fd,'       $cabecaltura="cabecaltura_".$cabec;     '."\n");
 $fd && fputs($fd,'       $cabeclargura="cabeclargura_".$cabec;     '."\n");
 $fd && fputs($fd,'       $x=$pdf->getx(); '."\n");
 $fd && fputs($fd,'       if($$cabeclargura+$x > $maxlargura){'."\n");
 $fd && fputs($fd,'         $pdf->ln($$altura);//não funciona   '."\n");
 $fd && fputs($fd,'         $pdf->setX(5);'."\n");
 $fd && fputs($fd,'       } '."\n");
 $fd && fputs($fd,'       $clrotulolov->label(pg_fieldname($resultsql,$cabec));'."\n");
 $fd && fputs($fd,'       $pdf->Cell($$cabeclargura,$$cabecaltura,$clrotulolov->titulo,"LRBT",($cabec==($fm_numfields-1)?1:0),"L",1);'."\n");
 $fd && fputs($fd,'       //$pdf->Cell((($clrotulolov->tamanho>strlen($clrotulolov->titulo)?$clrotulolov->tamanho:strlen($clrotulolov->titulo))*2)+2,4,$clrotulolov->titulo,"LRBT",($cabec==($fm_numfields-1)?1:0),"L",0);'."\n");
 $fd && fputs($fd,'     }'."\n");
 $fd && fputs($fd,'     $pdf->ln(1);	   '."\n");
 $fd && fputs($fd,'   } '."\n");
 $fd && fputs($fd,' }'."\n");
 $fd && fputs($fd,' $pdf->setX(5);'."\n");
 $fd && fputs($fd,' for($s=0;$s<$fm_numfields;$s++){'."\n");
 $fd && fputs($fd,'       $corpopcao="corpopcao_".$s;'."\n");
 $fd && fputs($fd,'       $corplargura="corplargura_".$s;'."\n");
 $fd && fputs($fd,'       $pdf->SetFillColor(200,200,200);'."\n");
 $fd && fputs($fd,'       if($s<($fm_numfields-1)){'."\n");
 $fd && fputs($fd,'         $quebra=0;'."\n");
 $fd && fputs($fd,'       }else{'."\n");
 $fd && fputs($fd,'             $quebra=1;'."\n");
 $fd && fputs($fd,'       }'."\n");
 $fd && fputs($fd,'       if($$corpopcao!="nenhuma"){'."\n");
 $fd && fputs($fd,'         $pdf->Cell($$corplargura,4,"Total",1,$quebra,"LRBT",1);'."\n");
 $fd && fputs($fd,'       }else{'."\n");
 $fd && fputs($fd,'         $pdf->Cell($$corplargura,4,"",1,$quebra,"LRBT",0);'."\n");
 $fd && fputs($fd,'       }'."\n");
 $fd && fputs($fd,'     }'."\n");
 $fd && fputs($fd,'       $pdf->setX(5);'."\n");
 $fd && fputs($fd,'       $soma=0;'."\n");
 $fd && fputs($fd,'       $contador=0;'."\n");
 $fd && fputs($fd,'       $preenchido=0;'."\n");
 $fd && fputs($fd,'       for($cc=0;$cc<$fm_numfields;$cc++){'."\n");
 $fd && fputs($fd,'         if($cc<($fm_numfields-1)){'."\n");
 $fd && fputs($fd,'           $quebra=0;'."\n");
 $fd && fputs($fd,'         }else{'."\n");
 $fd && fputs($fd,'            $quebra=1;'."\n");
 $fd && fputs($fd,'         }'."\n");
 $fd && fputs($fd,'         $corplargura="corplargura_".$cc;'."\n");
 $fd && fputs($fd,'         $pdf->SetFillColor(200,200,200);'."\n");
 $fd && fputs($fd,'         $corpopcao="corpopcao_".$cc;'."\n");
 $fd && fputs($fd,'         switch($$corpopcao){'."\n");
 $fd && fputs($fd,'                case "somar":'."\n");
 $fd && fputs($fd,'                       for($d=0; $d< pg_numrows($resultsql) ; $d++){'."\n");
 $fd && fputs($fd,'                         $result=pg_result($resultsql, $d, $cc);'."\n");
 $fd && fputs($fd,'                         $soma+=$result;'."\n");
 $fd && fputs($fd,'                       }'."\n");
 $fd && fputs($fd,'                      $pdf->Cell($$corplargura,4,$soma,1,$quebra,"LRBT",1);'."\n");
 $fd && fputs($fd,'                       break;'."\n");
 $fd && fputs($fd,'                case "preenchidos":'."\n");
 $fd && fputs($fd,'                      for($d=0; $d< pg_numrows($resultsql) ; $d++){'."\n");
 $fd && fputs($fd,'                       $result=pg_result($resultsql, $d, $cc);'."\n");
 $fd && fputs($fd,'                        if($result!=""){'."\n");
 $fd && fputs($fd,'                           $preenchido+=1;'."\n");
 $fd && fputs($fd,'                        }'."\n");
 $fd && fputs($fd,'                      }'."\n");
 $fd && fputs($fd,'                      $pdf->Cell($$corplargura,4,$preenchido,1,$quebra,"LRBT",1);'."\n");
 $fd && fputs($fd,'                      break;'."\n");
 $fd && fputs($fd,'                case "contar":'."\n");
 $fd && fputs($fd,'                    for($d=0; $d< pg_numrows($resultsql) ; $d++){'."\n");
 $fd && fputs($fd,'                       $result=pg_result($resultsql, $d, $cc);'."\n");
 $fd && fputs($fd,'                       $contador+=1;'."\n");
 $fd && fputs($fd,'                     }'."\n");
 $fd && fputs($fd,'                     $pdf->Cell($$corplargura,4,$contador,1,$quebra,"LRBT",1);'."\n");
 $fd && fputs($fd,'                     break;'."\n");
 $fd && fputs($fd,'                case "nenhuma";'."\n");
 $fd && fputs($fd,'                     $pdf->Cell($$corplargura,4,"",0,$quebra,"LRBT",0);'."\n");
 $fd && fputs($fd,'                     break;'."\n");
 $fd && fputs($fd,'       }'."\n");
 $fd && fputs($fd,'     }'."\n");



 $fd && fputs($fd,' //$pdf->Cell(200,2,"","",1,"L",0);'."\n");
 $fd && fputs($fd,' //$pdf->Cell(200,0,"","LRBT",1,"L",0);'."\n");
 $fd && fputs($fd,'  //$tmpfile=tempnam("tmp","tmp.pdf");'."\n");
 $fd && fputs($fd,' $pdf->Output();'."\n");
 $fd && fputs($fd,'?>'."\n");
 $fd && fclose($fd);
// echo "<script> location.href=\"con2_gerelatorio001.php\"</script>";
// $nome=basename($arquivo);
//system ("cp /home/dbpref/public_html/dbportal2/tmp/pdf_GTxfxS  /home/dbpref/public_html/dbportal2/tmp/xxx.php" );
// echo "<script> location.href=\"tmp/regua.php\"</script>";

  if(@$libera==true){
   system("rm -f gerador/".$nomeok."001.php");
 }
 $visualizacaook=$visualizacao=="P"?"Retrato":"Paisagem";
 $HTTP_SERVER_VARS['SCRIPT_FILENAME'];
 $root = substr($HTTP_SERVER_VARS['SCRIPT_FILENAME'],0,strrpos($HTTP_SERVER_VARS['SCRIPT_FILENAME'],"/"));
 $arquivo = ($root."/"."gerador/".$nomeok."001.php");
 $fd = fopen($arquivo,"w");
 $fd && fputs($fd,'<?'."\n");
 $fd && fputs($fd,'require(modification("libs/db_stdlib.php"));'."\n");
 $fd && fputs($fd,'require(modification("libs/db_conecta.php"));'."\n");
 $fd && fputs($fd,'?>'."\n");
 $fd && fputs($fd,'<html>'."\n");
 $fd && fputs($fd,'<head>'."\n");
 $fd && fputs($fd,'  <title>DBSeller Inform&aacute;tica Ltda - P&aacute;gina Inicial</title>'."\n");
 $fd && fputs($fd,'   <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'."\n");
 $fd && fputs($fd,' <meta http-equiv="Expires" CONTENT="0">'."\n");
 $fd && fputs($fd,' <script language="JavaScript" type="text/javascript" src="../scripts/scripts.js"></script>'."\n");
 $fd && fputs($fd,' <link href="../estilos.css" rel="stylesheet" type="text/css">'."\n");
 $fd && fputs($fd,'</head>'."\n");
 $fd && fputs($fd,'<body bgcolor=#CCCCCC bgcolor="#cccccc" leftmargin="0" topmargin="0" marginwidth="0" marginheight="0" onLoad="a=1" >'."\n");
 $fd && fputs($fd,'<script>'."\n");
 $fd && fputs($fd,' function nova(){'."\n");
 $fd && fputs($fd,'  location.href="../con2_gerelatorio006.php?vaite=true";'."\n");
 $fd && fputs($fd,'}'."\n");
 $fd && fputs($fd,'  function abra(){'."\n");
 $fd && fputs($fd,' var   titulo=document.form1.titulo.value;   '."\n");
 $fd && fputs($fd,' var   finalidade=document.form1.finalidade.value;   '."\n");
 $fd && fputs($fd,' var   visualizacao=document.form1.visualizacao.value;   '."\n");
 $fd && fputs($fd,' var   limite=document.form1.limite.value;   '."\n");
 $fd && fputs($fd,' window.open("'.$nomeok.'002.php?nome='.$nome.'&titulo="+titulo+"&finalidade="+finalidade+"&limite="+limite+"&visualizacao="+visualizacao+"&veri=res","Relatório","toolbar=no,menubar=no,scrollbars=no,resizable=yes,location=no,directories=no,status=no");'."\n");
 $fd && fputs($fd,' }'."\n");
 $fd && fputs($fd,'</script>'."\n");
 $fd && fputs($fd,'<br>'."\n");
 $fd && fputs($fd,'<table border="0" cellpadding="0" align="center" cellspacing="0" bgcolor="#cccccc"><br><br>'."\n");
 $fd && fputs($fd,'<form name="form1" method="post">'."\n");
 $fd && fputs($fd,'  <tr align="100%">'."\n");
 $fd && fputs($fd,'   <td height="35" align="center" colspan="2"><h5>Dados Referentes ao Relatório</h5></td>'."\n");
 $fd && fputs($fd,' </tr>'."\n");
 $fd && fputs($fd,'  <tr>'."\n");
 $fd && fputs($fd,'   <td height="35" width="10%"><b>Nome:</b></td>'."\n");
 $fd && fputs($fd,'   <td>'.$nome.'</td>'."\n");
 $fd && fputs($fd,' </tr> '."\n");
 $fd && fputs($fd,' <tr > '."\n");
 $fd && fputs($fd,'   <td height="35"><b>Sintaxe SQL:</b></td>'."\n");
 $fd && fputs($fd,'   <td>'.$sql.'</td>'."\n");
 $fd && fputs($fd,' </tr> '."\n");
 $fd && fputs($fd,' <tr> '."\n");
 $fd && fputs($fd,'   <td height="35"><b>Titulo:</b></td>'."\n");
 $fd && fputs($fd,'   <td><input type="text" name="titulo" value="'.$titulo.'"></td>'."\n");
 $fd && fputs($fd,' </tr> '."\n");
 $fd && fputs($fd,' <tr> '."\n");
 $fd && fputs($fd,'   <td height="35"><b>Finalidade:</b></td>'."\n");
 $fd && fputs($fd,'   <td><input type="text" name="finalidade" value="'.$finalidade.'"></td>'."\n");
 $fd && fputs($fd,' <tr> '."\n");
 $fd && fputs($fd,'   <td height="35"><b>Pagina:</b></td> '."\n");
 $fd && fputs($fd,'   <td><select  name="visualizacao">'."\n");
                if($visualizacao=="P"){
 $fd && fputs($fd,'      <option value="P" selected >Retrato</option>'."\n");
 $fd && fputs($fd,'      <option value="L" >Paisagem</option>'."\n");
                }
                if($visualizacao=="L"){
 $fd && fputs($fd,'      <option value="P">Retrato</option>'."\n");
 $fd && fputs($fd,'      <option value="L" selected>Paisagem</option>'."\n");
                }
 $fd && fputs($fd,'   </td> '."\n");
 $fd && fputs($fd,' </tr> '."\n");
 $fd && fputs($fd,'   <td nowrap ><b>Limite de linhas:</b></td>'."\n");
   $fd && fputs($fd,'   <td><input  type="text" name="limite" value="'.$limite.'"></td>'."\n");
 $fd && fputs($fd,' </tr> '."\n");
 $fd && fputs($fd,' <tr>'."\n");
 $fd && fputs($fd,'   <td height="40" align="center" colspan="2">'."\n");
 $fd && fputs($fd,'      <input type="button" name="abrir" value="Gerar Relatório" onclick="abra()">'."\n");
$fd && fputs($fd,'   </td>'."\n");
 $fd && fputs($fd,' </tr>'."\n");
 $fd && fputs($fd,'</form1>'."\n");
 $fd && fputs($fd,'</table>  '."\n");
 $fd && fputs($fd,'</body>'."\n");
 $fd && fputs($fd,'</html>'."\n");
 $fd && fclose($fd);
  echo "<script> location.href=\"con2_gerelatorio006.php?nome=".$nomeok."001.php\"</script>";
?>
