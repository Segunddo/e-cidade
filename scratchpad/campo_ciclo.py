#!/usr/bin/env python3
"""Guarda pg_result() com COLUNA inexistente e pg_free_result(false), NA APARICAO, uma linha por vez.

Uso (da raiz do repo):  python3 scratchpad/campo_ciclo.py tela1.php [tela2.php ...]

Irmao do guarda_ciclo.py (que trata resultado FALSO); este trata resultado valido sem a coluna:
  pg_result($r,$l,"col")  ->  (pg_field_num($r,"col") >= 0 ? pg_result($r,$l,"col") : false)   (false no 5.6)
  pg_free_result($r)      ->  ($r ? pg_free_result($r) : null)                                  (NULL no 5.6)
Alterne os dois ate a tela parar de fatalar: uma guarda expoe a proxima. SID pela variavel de ambiente SID, como no guarda_ciclo.py.

Como faz, por rodada (ate 20 por tela): zera ecidade/extension/log/error.log, restaura a sessao de
/tmp/_sess.bak, faz GET da tela no 8.5 (:8085), procura no log um dos dois fatais acima, e reescreve
SO a linha apontada com a guarda correspondente; espera 3 s (opcache) e repete.
Entradas: SID (variavel de ambiente; se faltar, usa um SID fixo antigo que provavelmente ja nao vale)
e as telas (relativas a ecidade/). Exige /tmp/_sess.bak no ecidade_php74 (criado pelo cmp.py).
Diferente do guarda_ciclo.py, NAO faz chdir: tem de rodar da raiz do repositorio.
Saida (stdout): uma linha por guarda (arquivo, linha, linha nova) e o "fim:" de cada tela.
Efeitos colaterais: ALTERA ARQUIVOS DE CODIGO em ecidade/ (bytes, preserva LATIN-1); apaga o
error.log compartilhado a cada rodada; sobrescreve o arquivo de sessao. Nao roda php -l.
Usado em: guia docs/migrar-um-modulo.md, Passo 7, "Os dois ciclos automaticos de guarda pg_*".
"""
import re,subprocess,sys,time
import os; SID=os.environ.get("SID","1fbc7ac662c9b02f322530bad6b8b9e9d61507c3"); SESS=f"/var/lib/php/sessions/sess_{SID}"
# pg_result($r, <linha>, "col"|'col'): grupo 1 = resultado, 2 = linha (sem virgula/parenteses),
# 3 = nome da coluna LITERAL. Coluna em variavel ou linha com chamada aninhada nao casa.
# pg_field_num devolve -1 se a coluna nao existe; o 5.6 devolvia false nesse caso.
rx_res=re.compile(rb'\bpg_result\(\s*(\$\w+)\s*,([^,()]+),\s*("[^"]*"|\'[^\']*\')\s*\)')
rx_free=re.compile(rb'\bpg_free_result\(\s*(\$\w+)\s*\)')
for tela in sys.argv[1:]:
  for rodada in range(20):
    # log zerado: o fatal lido abaixo e o desta requisicao
    open("ecidade/extension/log/error.log","w").close()
    subprocess.run(["docker","exec","-u","root","ecidade_php74","sh","-c",f"cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}"])
    subprocess.run(["curl","-s","-o","/dev/null","-b",f"ECIDADEWINDOWMAIN={SID}",f"http://localhost:8085/{tela}"])
    log=open("ecidade/extension/log/error.log","rb").read()
    # grupo 1 diz qual dos dois fatais (coluna ausente ou pg_free_result(false)); 2 e 3 = arquivo e linha
    m=re.search(rb"with message '(Argument #3 must be a field name from this result set|pg_free_result\(\): Argument #1 \(\$result\) must be of type PgSql.Result, false given)' in (?:/var/www/html/)?(\S+) on line (\d+)",log)
    if not m:
      e=re.search(rb"E_ERROR - (.{0,200})",log); print(tela,"fim:", e.group(1).decode("latin1") if e else "sem fatal"); break
    f="ecidade/"+m.group(2).decode(); l=int(m.group(3)); ls=open(f,"rb").read().split(b"\n")
    if m.group(1).startswith(b"Argument"):
      new,n=rx_res.subn(lambda x: b"(pg_field_num("+x.group(1)+b","+x.group(3)+b") >= 0 ? "+x.group(0)+b" : false)", ls[l-1])
    else:
      new,n=rx_free.subn(lambda x: b"("+x.group(1)+b" ? "+x.group(0)+b" : null)", ls[l-1])
    if n==0: print(tela,"linha nao guardavel",f,l,ls[l-1][:150]); break
    ls[l-1]=new; open(f,"wb").write(b"\n".join(ls)); print(tela,"guarda",f,l,":",new.strip()[:160].decode("latin1")); time.sleep(3)
