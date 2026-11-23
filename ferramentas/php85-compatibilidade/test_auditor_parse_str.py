"""Cenarios sinteticos que conferem a contagem lexical de argumentos."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

PHP=os.environ.get('PHP_AUDITOR') or shutil.which('php')

@unittest.skipUnless(PHP,'Informe PHP_AUDITOR apontando para PHP 8 ou instale PHP no PATH')
class AuditorCases(unittest.TestCase):
    def test_cenarios_lexicais(self):
        version=subprocess.check_output([PHP,'-n','-r','echo PHP_VERSION_ID;'])
        if int(version)<80000:self.skipTest('O analisador exige PHP 8 para nomes qualificados')
        cases=[('um','<?php parse_str($q);',[[1,False]]),
               ('dois','<?php parse_str($q,$r);',[[2,False]]),
               ('aninhado','<?php \\parse_str(foo(a(1,2),[3,4]),$r);',[[2,False]]),
               ('metodo','<?php $x->parse_str($q); X::parse_str($q);',[]),
               ('namespace','<?php Other\\parse_str($q);',[]),
               ('comentario','<?php /* parse_str($q); */ $s="parse_str(x)";',[]),
               ('virgula_final','<?php parse_str($q,);',[[1,False]]),
               ('unpack','<?php parse_str(...$args);',[[1,True]]),
               ('interpolado','<?php parse_str("{$map[\'x\']},z=1",$r);',[[2,False]]),
               ('nomeado','<?php parse_str($q,result:$r);',[[2,False]]),
               ('short_tag','<? parse_str($q); ?>',[[1,False]]),
               ('declaracao','<?php namespace X; function &parse_str($q) {}',[])]
        data='\n'.join(json.dumps({'path':name,'source_base64':base64.b64encode(source.encode()).decode()})
                       for name,source,_ in cases)+'\n'
        result=subprocess.run([PHP,'-n','-d','short_open_tag=1',str(Path(__file__).with_name('auditar-parse-str.php'))],
                              input=data.encode(),capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(rows),len(cases))
        for row,(name,_,expected) in zip(rows,cases):
            with self.subTest(name=name):
                self.assertEqual(row['path'],name)
                self.assertEqual([[c['arguments'],c['unpacked']] for c in row['calls']],expected)

if __name__=='__main__':unittest.main()
