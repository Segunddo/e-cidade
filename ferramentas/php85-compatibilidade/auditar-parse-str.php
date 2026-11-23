<?php
/* Leitura lexical. Entrada JSONL com path e source_base64, saida sem fonte. */
function parse_str_calls($source) {
    $raw=token_get_all($source);
    $tokens=array();$line=1;
    foreach($raw as $token) {
        if(is_array($token)) {
            $line=$token[2];
            if(!in_array($token[0],array(T_WHITESPACE,T_COMMENT,T_DOC_COMMENT),true)) {
                $tokens[]=array($token[0],$token[1],$line);
            }
            $line+=substr_count($token[1],"\n");
        } else {
            $tokens[]=array(null,$token,$line);
            $line+=substr_count($token,"\n");
        }
    }
    $calls=array();
    foreach($tokens as $index=>$token) {
        if($token[0]===null || strtolower(ltrim($token[1],'\\'))!=='parse_str') {continue;}
        $previous=$index>0?$tokens[$index-1]:null;
        if($previous && $previous[1]==='&' && $index>1 && $tokens[$index-2][0]===T_FUNCTION) {continue;}
        if($previous && (in_array($previous[1],array('->','?->','::'),true) ||
            in_array($previous[0],array(T_FUNCTION,T_NEW),true))) {continue;}
        if(!isset($tokens[$index+1]) || $tokens[$index+1][1]!=='(') {continue;}
        $depth=1;$arguments=0;$segment=false;$closed=false;$dynamic=false;
        for($j=$index+2;$j<count($tokens);$j++) {
            $part=$tokens[$j];
            if($part[0]!==null) {
                $segment=true;
                if($depth===1 && $part[0]===T_ELLIPSIS) {$dynamic=true;}
                // Interpolacao de string possui abertura tokenizada.
                if(in_array($part[0],array(T_CURLY_OPEN,T_DOLLAR_OPEN_CURLY_BRACES),true)) {$depth++;}
                continue;
            }
            if(in_array($part[1],array('(','[','{'),true)) {$depth++;$segment=true;continue;}
            if(in_array($part[1],array(')',']','}'),true)) {
                $depth--;
                if($depth===0) {$arguments+=$segment?1:0;$closed=true;break;}
                $segment=true;continue;
            }
            if($part[1]===',' && $depth===1) {$arguments+=$segment?1:0;$segment=false;continue;}
            $segment=true;
        }
        $calls[]=array('line'=>$token[2],'arguments'=>$arguments,'closed'=>$closed,'unpacked'=>$dynamic);
    }
    return $calls;
}
if(realpath($_SERVER['SCRIPT_FILENAME'])===__FILE__) {
    while(($line=fgets(STDIN))!==false) {
        try {
            $entry=json_decode($line,true,512,JSON_THROW_ON_ERROR);
            $source=base64_decode($entry['source_base64'],true);
            if($source===false) {throw new RuntimeException('Base64 invalido');}
            echo json_encode(array('path'=>$entry['path'],'calls'=>parse_str_calls($source)),JSON_THROW_ON_ERROR),"\n";
        } catch(Throwable $error) {
            fwrite(STDERR,'Falha na leitura lexical: '.$error->getMessage()."\n");exit(2);
        }
    }
}
