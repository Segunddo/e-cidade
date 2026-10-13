#!/usr/bin/env python3
"""Compara as telas de um modulo entre os runtimes 5.6 (:8080) e 8.5 (:8085).

Restaura uma sessao autenticada antes de CADA requisicao (uma requisicao a
consome/reescreve) e normaliza os identificadores aleatorios, que senao geram
falsos positivos -- alguns deles INTERMITENTES, que e o pior tipo.
"""
import re, subprocess, sys, os

# O projeto vive em ecidade/; sem isto o os.listdir('.') abaixo nao acha as telas.
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))

SID  = sys.argv[1]
PREF = sys.argv[2]
OUT  = sys.argv[3] if len(sys.argv) > 3 else None
SESS = f"/var/lib/php/sessions/sess_{SID}"

def sh(c):
    return subprocess.run(["bash", "-lc", c], capture_output=True)

sh(f"docker exec -u root ecidade_php56 cp {SESS} /tmp/_sess.bak")

def restore():
    sh("docker exec -u root ecidade_php56 sh -c "
       f"'cp /tmp/_sess.bak {SESS}; chown www-data:www-data {SESS}; chmod 600 {SESS}'")

NORM = [
    (re.compile(rb'sid=[0-9a-f]{8,}'),            b'sid=X'),
    (re.compile(rb'arquivo=[A-Za-z0-9+/=]{12,}'), b'arquivo=X'),
    (re.compile(rb'wname[0-9]+'),                 b'wnameX'),
    (re.compile(rb'iframe[A-Za-z0-9]{4,}\.php'),  b'iframeX.php'),
    (re.compile(rb'[0-9a-f]{32}'),                b'MD5X'),
    (re.compile(rb'nomeArquivo[^\s"\']*'),        b'nomeArquivoX'),
    # PDF temporario: o nome carrega PID e timestamp, aleatorios por requisicao.
    (re.compile(rb'tmp/[A-Za-z0-9_]+\.pdf'),      b'tmp/X.pdf'),
    # CSV/TXT temporario com timestamp no nome (arquivo_infra_escola_1791906927.csv);
    # dentro de JSON a barra vem escapada (tmp\/...). Achado no edu2.
    (re.compile(rb'tmp\\?/[A-Za-z0-9_]+\.(?:csv|txt)'), b'tmp/X.arq'),
    # A pagina de erro monta URL absoluta a partir de HTTP_HOST (ver $DB_URL_ABS),
    # entao ela carrega a porta do runtime que a serviu. Diferenca por construcao.
    (re.compile(rb'localhost:80(80|85)'),         b'localhost:PORT'),
    # Data de criacao gravada dentro do PDF pelo FPDF: muda se as duas
    # requisicoes cairem em segundos diferentes. Passou a aparecer depois que
    # tmp/ virou gravavel e os relatorios comecaram a ser gerados de fato.
    (re.compile(rb'/(CreationDate|ModDate) ?\(D:[0-9]{14}[^)]*\)'), b'/DateX'),
]
def norm(b):
    for rx, rep in NORM:
        b = rx.sub(rep, b)
    return b

def fetch(port, page):
    restore()
    # teto de 5 MB: uma pagina com laco infinito (ver -1 >= "" no PHP 8) estoura
    # a memoria do harness e o mata com SIGKILL. Truncada, ela perde o marcador
    # @@ e cai como divergente, que e o desfecho correto.
    r = sh(f"curl -s -m 60 -b 'ECIDADEWINDOWMAIN={SID}' "
           f"-w '\\n@@%{{http_code}}' http://localhost:{port}/{page} | head -c 5000000")
    out = r.stdout
    i = out.rfind(b'\n@@')
    code = out[i+3:].decode(errors='replace') if i >= 0 else '???'
    return code, norm(out[:i] if i >= 0 else out)

files = sorted(f for f in os.listdir('.')
               if re.match(PREF, f, re.IGNORECASE) and f.endswith('.php'))
if os.environ.get('ONLY'):
    files = os.environ['ONLY'].split(',')

print(f"{len(files)} telas\n", flush=True)
div = []
for n, f in enumerate(files, 1):
    c56, b56 = fetch(8080, f)
    c85, b85 = fetch(8085, f)
    if not (c56 == c85 and b56 == b85):
        # CONFIRMAR antes de acusar. Relatorios em PDF carregam um horario
        # DENTRO do fluxo comprimido (FlateDecode), fora do alcance da
        # normalizacao: se as duas requisicoes cairem em segundos diferentes,
        # os bytes mudam. Uma regressao real e persistente; um flake nao.
        c56, b56 = fetch(8080, f)
        c85, b85 = fetch(8085, f)
    if not (c56 == c85 and b56 == b85):
        div.append((f, c56, c85, len(b56), len(b85)))
        print(f"  DIVERGE {f}  56={c56}/{len(b56)}B  85={c85}/{len(b85)}B", flush=True)
    if n % 50 == 0:
        print(f"  ... {n}/{len(files)}", flush=True)

print(f"\n=== {len(files)-len(div)}/{len(files)} identicas, {len(div)} divergentes ===")
if OUT and OUT != '/dev/null':
    with open(OUT, "w") as fh:
        for d in div:
            fh.write(f"{d[0]}\t{d[1]}\t{d[2]}\t{d[3]}\t{d[4]}\n")
