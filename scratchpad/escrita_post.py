#!/usr/bin/env python3
"""NIVEL 3 da cobertura de escrita: submete um POST REAL aos dois runtimes e
compara o SQL que cada um emite.

O problema central: os dois runtimes compartilham o banco, entao o primeiro POST
muda o estado que o segundo veria. A saida e comparar o SQL EMITIDO -- que e
onde o defeito `0 == <literal>` se manifesta (o campo sai 0 em vez do valor
submetido) -- com snapshot/restore das tabelas afetadas entre os dois lados.

Exige log_statement ligado:
    ALTER DATABASE ecidade SET log_statement = 'all';
e, ao terminar:
    ALTER DATABASE ecidade RESET log_statement;

Uso:
  python3 scratchpad/escrita_post.py <SID> <tela.php> <tabelas,virgula> <payload>
Exemplo:
  python3 scratchpad/escrita_post.py <SID> jur1_advog001.php advog \
     'db_opcao=Incluir&v57_numcgm=19&v57_oab=OAB123&v57_matriculaadvogado=M1'
"""
import re, subprocess, sys, os

SID, TELA, TABELAS, PAYLOAD = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]
SESS = f"/var/lib/php/sessions/sess_{SID}"
DB   = "docker exec -i ecidade_database psql -U postgres -d ecidade"

def sh(c, entrada=None):
    return subprocess.run(["bash","-lc",c], capture_output=True, input=entrada)

def sequencias(t):
    """Sequencias da tabela. O e-cidade as cria SEM OWNED BY, entao
    pg_get_serial_sequence nao as enxerga -- casa pelo nome."""
    q = "select relname from pg_class where relkind='S' and relname like '" + t + "\\_%\\_seq'"
    r = sh(DB + ' -tAc "' + q + '"')
    return [x for x in r.stdout.decode("latin1").split() if x]

def snapshot():
    """COPY de cada tabela + last_value das sequencias. LATIN1 -- nao decodificar.
    Sem repor a sequencia, o segundo runtime recebe o numero seguinte e o INSERT
    diverge por motivo benigno."""
    snap = {t: sh(f'{DB} -c "COPY {t} TO STDOUT"').stdout for t in TABELAS}
    seq = {}
    for t in TABELAS:
        for sq in sequencias(t):
            seq[sq] = sh(DB + ' -tAc "select last_value, is_called from ' + sq + '"').stdout.decode().strip()
    snap["__seq__"] = seq
    return snap

def restaurar(snap):
    """DELETE respeita FK e falha se alguem referencia -- e a rede de seguranca.
    TRUNCATE CASCADE apagaria tabelas vizinhas em silencio."""
    for t in TABELAS:                      # apaga filho -> pai
        r = sh(f'{DB} -c "DELETE FROM {t}"')
        if r.returncode != 0:
            sys.exit(f"ABORTADO: nao consegui limpar {t}: {r.stderr.decode('latin1')[:200]}")
    for t in reversed(TABELAS):            # repovoa pai -> filho
        sh(f'{DB} -c "COPY {t} FROM STDIN"', entrada=snap[t])
    for sq, v in snap['__seq__'].items():
        lv, chamada = [x.strip() for x in v.split('|')]
        cal = 'true' if chamada == 't' else 'false'
        sh(DB + ' -c "select setval(\'' + sq + '\', ' + lv + ', ' + cal + ')"')

def restaurar_sessao():
    sh("docker exec -u root ecidade_php56 sh -c "
       f"'cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}; chmod 600 {SESS}'")

def linhas_log():
    return int(sh("docker logs ecidade_database 2>&1 | wc -l").stdout.strip() or 0)

PREFIXO = re.compile(rb'^\d{4}-\d{2}-\d{2} [\d:.]+ [^ ]+ \[\d+\] LOG:\s+[^:]*:\s*')
def capturar(desde):
    """Statements emitidos depois de `desde`, sem o prefixo de log, juntando
    continuacoes de linha."""
    bruto = sh(f"docker logs ecidade_database 2>&1 | tail -n +{desde+1}").stdout
    out = []
    for l in bruto.split(b'\n'):
        m = PREFIXO.match(l)
        if m:   out.append(bytearray(l[m.end():]))
        elif out and l.strip(): out[-1] += b' ' + l.strip()
    return [bytes(x) for x in out]

NORM = [(re.compile(rb"'\d{4}-\d{2}-\d{2}[ T][\d:.]+'"), b"'<TS>'"),   # timestamps
        (re.compile(rb'\s+'), b' ')]
def norm(s):
    for rx, rep in NORM: s = rx.sub(rep, s)
    return s.strip()

def requisitar(porta):
    restaurar_sessao()
    antes = linhas_log()
    sh(f"curl -s -m 60 -b 'ECIDADEWINDOWMAIN={SID}' -X POST "
       f"--data '{PAYLOAD}' -o /dev/null http://localhost:{porta}/{TELA}")
    sh("sleep 1")
    return [norm(s) for s in capturar(antes)]

sh(f"docker exec -u root ecidade_php56 cp {SESS} /tmp/_sess.bak")
snap = snapshot()
print("  snapshot: " + "  ".join(t + "=" + str(len(snap[t].splitlines())) + " linhas"
      for t in TABELAS) + "  | sequencias=" + str(len(snap["__seq__"])))

a = requisitar(8080); restaurar(snap)
b = requisitar(8085); restaurar(snap)
print(f"  statements: 5.6={len(a)}  8.5={len(b)}")

# so o que escreve -- e onde o defeito aparece
esc = re.compile(rb'^\s*(insert|update|delete)\b', re.I)
ea, eb = [s for s in a if esc.match(s)], [s for s in b if esc.match(s)]
print(f"  destes, INSERT/UPDATE/DELETE: 5.6={len(ea)}  8.5={len(eb)}")

# Separa escrita de NEGOCIO da de INFRAESTRUTURA. A auditoria (db_acount*) e a
# sessao (db_usuariosonline) carregam sequencia e relogio, que divergem por
# construcao entre duas requisicoes -- nao sao defeito.
INFRA = re.compile(rb'\b(db_acount\w*|db_usuariosonline|db_logsacessa|db_menu\w*|db_sessao\w*)\b', re.I)
na, nb = [s for s in ea if not INFRA.search(s)], [s for s in eb if not INFRA.search(s)]
print(f"  destes, escrita de NEGOCIO: 5.6={len(na)}  8.5={len(nb)}")
for s in na[:6]: print(f"    5.6> {s.decode('latin1')[:140]}")
for s in nb[:6]: print(f"    8.5> {s.decode('latin1')[:140]}")
ea, eb = na, nb

# INCONCLUSIVO != IDENTICO. Com os dois lados vazios o teste nao exercitou nada
# -- payload errado, tela inexistente, validacao recusando antes do INSERT. Sem
# esta guarda o harness APROVA o nada, que e o pior resultado possivel: da a
# impressao de cobertura onde nao houve nenhuma.
if not ea and not eb:
    print("  == INCONCLUSIVO: nenhuma escrita de negocio nos DOIS runtimes ==")
    print("     o POST nao chegou a gravar. Conferir: a tela existe? o nome do")
    print("     botao de submit esta certo? a validacao recusou antes do INSERT?")
    sys.exit(2)

if ea == eb:
    print("  == SQL de escrita de NEGOCIO IDENTICO nos dois runtimes ==")
else:
    print("  == DIVERGE ==")
    for i in range(max(len(ea), len(eb))):
        x = ea[i].decode('latin1') if i < len(ea) else '<ausente>'
        y = eb[i].decode('latin1') if i < len(eb) else '<ausente>'
        if x != y:
            print(f"    5.6: {x[:150]}")
            print(f"    8.5: {y[:150]}")
sys.exit(0 if ea == eb else 1)
