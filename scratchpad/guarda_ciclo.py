#!/usr/bin/env python3
"""Guarda `pg_*` sobre resultado false NA APARICAO, uma linha por vez.

Uso (da raiz do repo):  SID=<sessao> python3 scratchpad/guarda_ciclo.py tela1.php [tela2.php ...]

Para cada tela: requisita no 8.5, le o fatal do extension/log/error.log, e se for
pg_num_rows/pg_numrows/pg_result/pg_fetch_* sobre `$var` aplica, SO naquela linha,
`($var ? pg_xxx($var...) : null)` -- null e o valor medido no 5.6 para todas elas.
Repete ate a tela parar de fatalar. Qualquer outro fatal encerra e e mostrado.

Depois de rodar, REVISAR: (1) nenhuma linha guardada seguida de `===`/`!==` sobre o
resultado (a guarda devolve null, o 5.6 tambem -- mas confira); (2) o diff.
Exige a sessao restaurada em /tmp/_sess.bak (o cmp.py faz isso ao rodar).
"""
import subprocess, re, sys, time, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SID=os.environ["SID"]; SESS=f"/var/lib/php/sessions/sess_{SID}"
rx=re.compile(rb'\b(pg_num_rows|pg_numrows|pg_result|pg_fetch_result|pg_fetch_assoc|pg_fetch_object|pg_fetch_array|pg_fetch_row)\(\s*(\$\w+)\s*((?:,[^()]*)?)\)')
for tela in sys.argv[1:]:
  for rodada in range(15):
    open("ecidade/extension/log/error.log","w").close()
    subprocess.run(["docker","exec","-u","root","ecidade_php56","sh","-c",f"cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}"])
    subprocess.run(["curl","-s","-o","/dev/null","-b",f"ECIDADEWINDOWMAIN={SID}",f"http://localhost:8085/{tela}"])
    log=open("ecidade/extension/log/error.log","rb").read()
    m=re.search(rb"with message '(pg_\w+)\(\): Argument #1 \(\$result\) must be of type PgSql.Result, false given' in (?:/var/www/html/)?(\S+) on line (\d+)",log)
    if not m:
        e=re.search(rb"E_ERROR - (.{0,200})",log); print(tela,"fim:", e.group(1).decode("latin1") if e else "sem fatal"); break
    f="ecidade/"+m.group(2).decode(); l=int(m.group(3)); ls=open(f,"rb").read().split(b"\n")
    new,n=rx.subn(lambda x: b"("+x.group(2)+b" ? "+x.group(0)+b" : null)", ls[l-1])
    if n==0: print(tela,"linha nao guardavel",f,l,ls[l-1][:120]); break
    ls[l-1]=new; open(f,"wb").write(b"\n".join(ls)); time.sleep(3);  # opcache revalida a cada 2 s
    print(tela,"guarda",f[8:],l,":",new.strip().decode("latin1")[:110])
