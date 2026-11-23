#!/usr/bin/env python3
"""Troca constante indefinida por (defined('X') ? X : 'X') NA APARICAO, uma linha por vez.
No 5.6 constante indefinida vira a string com o mesmo nome (notice); no PHP 8 e Error.
Uso (da raiz):  python3 scratchpad/const_ciclo.py tela1.php [...]   (exige /tmp/_sess.bak, ver cmp.py)
    SID=<sessao> python3 scratchpad/const_ciclo.py tela1.php [...]   (SID e obrigatorio)

Como faz, por rodada (ate 40 por tela): zera ecidade/extension/log/error.log, restaura a sessao de
/tmp/_sess.bak, faz GET da tela no 8.5 (:8085), procura no log 'Undefined constant "X"' com arquivo
e linha, e troca SO naquela linha o X solto por (defined('X') ? X : 'X') -- o que reproduz o 5.6
(string com o nome) e continua usando a constante se um dia ela for definida. Espera 3 s (opcache).
Entradas: variavel de ambiente SID e as telas (relativas a ecidade/).
Saida (stdout): uma linha por troca (constante, arquivo, linha) e o "fim:" de cada tela.
Efeitos colaterais: ALTERA ARQUIVOS DE CODIGO em ecidade/ (bytes); apaga o error.log compartilhado
a cada rodada; sobrescreve o arquivo de sessao. Nao roda php -l -- revisar o diff (a troca pode
pegar o mesmo nome dentro de uma string entre espacos, e troca TODAS as ocorrencias da linha).
Usado em: correcao na aparicao de telas que quebram so no 8.5 (Passo 7); nao aparece no guia
docs/migrar-um-modulo.md -- foi usado na Educacao (docs/registro/area-educacao.md).
"""
import subprocess, re, sys, time
import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SID=os.environ["SID"]; SESS=f"/var/lib/php/sessions/sess_{SID}"
for tela in sys.argv[1:]:
  for rodada in range(40):
    # log zerado: o fatal lido abaixo e o desta requisicao
    open("ecidade/extension/log/error.log","w").close()
    subprocess.run(["docker","exec","-u","root","ecidade_php74","sh","-c",f"cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}"])
    subprocess.run(["curl","-s","-m","30","-o","/dev/null","-b",f"ECIDADEWINDOWMAIN={SID}",f"http://localhost:8085/{tela}"])
    log=open("ecidade/extension/log/error.log","rb").read()
    m=re.search(rb"Undefined constant \"(\w+)\"' in (?:/var/www/html/)?(\S+) on line (\d+)",log)
    if not m:
        e=re.search(rb"E_ERROR - (.{0,160})",log); print(tela,"fim:", e.group(1).decode("latin1") if e else "sem fatal"); break
    c,f,l=m.group(1),"ecidade/"+m.group(2).decode(),int(m.group(3)); ls=open(f,"rb").read().split(b"\n")
    # So o nome SOLTO: nao precedido de letra/digito/_, $ (variavel), aspas (string), > (->X) ou : (::X);
    # nao seguido de letra/digito/_, aspas ou ( (chamada de funcao).
    new,n=re.subn(rb"(?<![\w$'\">:])"+c+rb"(?![\w'\"(])", b"(defined('"+c+b"') ? "+c+b" : '"+c+b"')", ls[l-1])
    if n==0: print(tela,"nao trocou",f,l,ls[l-1][:120]); break
    ls[l-1]=new; open(f,"wb").write(b"\n".join(ls)); time.sleep(3)
    print(tela,"const",c.decode(),f[8:],l)
