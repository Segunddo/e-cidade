#!/usr/bin/env python3
"""Troca constante indefinida por (defined('X') ? X : 'X') NA APARICAO, uma linha por vez.
No 5.6 constante indefinida vira a string com o mesmo nome (notice); no PHP 8 e Error.
Uso (da raiz):  python3 scratchpad/const_ciclo.py tela1.php [...]   (exige /tmp/_sess.bak, ver cmp.py)
"""
import subprocess, re, sys, time
import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SID=os.environ["SID"]; SESS=f"/var/lib/php/sessions/sess_{SID}"
for tela in sys.argv[1:]:
  for rodada in range(40):
    open("ecidade/extension/log/error.log","w").close()
    subprocess.run(["docker","exec","-u","root","ecidade_php56","sh","-c",f"cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}"])
    subprocess.run(["curl","-s","-m","30","-o","/dev/null","-b",f"ECIDADEWINDOWMAIN={SID}",f"http://localhost:8085/{tela}"])
    log=open("ecidade/extension/log/error.log","rb").read()
    m=re.search(rb"Undefined constant \"(\w+)\"' in (?:/var/www/html/)?(\S+) on line (\d+)",log)
    if not m:
        e=re.search(rb"E_ERROR - (.{0,160})",log); print(tela,"fim:", e.group(1).decode("latin1") if e else "sem fatal"); break
    c,f,l=m.group(1),"ecidade/"+m.group(2).decode(),int(m.group(3)); ls=open(f,"rb").read().split(b"\n")
    new,n=re.subn(rb"(?<![\w$'\">:])"+c+rb"(?![\w'\"(])", b"(defined('"+c+b"') ? "+c+b" : '"+c+b"')", ls[l-1])
    if n==0: print(tela,"nao trocou",f,l,ls[l-1][:120]); break
    ls[l-1]=new; open(f,"wb").write(b"\n".join(ls)); time.sleep(3)
    print(tela,"const",c.decode(),f[8:],l)
