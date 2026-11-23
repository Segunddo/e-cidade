#!/usr/bin/env python3
"""Compara as telas de um modulo entre a referencia (PHP 7.4) e o alvo (PHP 8.5).

Uso: python3 scratchpad/cmp.py <SID> <regex do nome da tela> [arquivo de saida]

Alvos (URL vista do host) e containers vem de regressao/nucleo/ambiente.py: REGRESSAO_REF_URL /
REGRESSAO_CONTAINER_REF (padrao :8074 / ecidade74_php74) e REGRESSAO_PHP_NOVO_URL /
REGRESSAO_CONTAINER_PHP_NOVO (padrao :8185 / ecidade74_php85). A saida marca a referencia com `ref=`
e o alvo com `85=`; regressao/php/telas.py interpreta essas linhas.

Pilha do compose da raiz (a do grupo, base-php74): mesmos argumentos, com as variaveis REGRESSAO_* apontando
para os containers e portas dela (tabela em regressao/COMO-USAR.md, "Usar com a pilha do grupo").

Restaura uma sessao autenticada antes de CADA requisicao (uma requisicao a
consome/reescreve) e normaliza os identificadores aleatorios, que senao geram
falsos positivos -- alguns deles INTERMITENTES, que e o pior tipo.
"""
import os
import re
import shlex
import subprocess
import sys
from urllib.parse import urlsplit

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
from regressao.nucleo.ambiente import alvos_do_ambiente, containers_do_ambiente  # noqa: E402

ARQ_BACKUP = "/tmp/_sess.bak"


def sh(c):
    return subprocess.run(["bash", "-lc", c], capture_output=True)


def lados():
    """[(rotulo, url base sem barra final, container)] da referencia e do alvo."""
    a, c = alvos_do_ambiente(), containers_do_ambiente()
    return [("ref", a.ref.rstrip("/"), c.ref), ("85", a.php_novo.rstrip("/"), c.php_novo)]


NORM_FIXAS = [
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
    # Data de criacao gravada dentro do PDF pelo FPDF: muda se as duas
    # requisicoes cairem em segundos diferentes. Passou a aparecer depois que
    # tmp/ virou gravavel e os relatorios comecaram a ser gerados de fato.
    (re.compile(rb'/(CreationDate|ModDate) ?\(D:[0-9]{14}[^)]*\)'), b'/DateX'),
    # PHP 8: "failed to open stream" -> "Failed to open stream" (mesmo warning nos dois runtimes)
    (re.compile(rb'[Ff]ailed to open stream'), b'failed to open stream'),
]


def regras_norm():
    """Regras fixas + o host:porta de cada alvo do ambiente. A pagina de erro monta URL absoluta a partir
    de HTTP_HOST (ver $DB_URL_ABS), entao ela carrega a porta do runtime que a serviu: diferenca por
    construcao. So os hosts dos alvos configurados sao trocados (nao qualquer porta)."""
    a = alvos_do_ambiente()
    hosts = sorted({urlsplit(u).netloc for u in (a.ref, a.php_novo, a.laravel_novo, a.proxy)
                    if urlsplit(u).netloc}, key=len, reverse=True)
    regras = list(NORM_FIXAS)
    if hosts:
        portas = re.compile(b"|".join(re.escape(h.encode()) for h in hosts))
        regras.append((portas, b"localhost:PORT"))
    return regras


def norm(b, regras):
    for rx, rep in regras:
        b = rx.sub(rep, b)
    return b


# NORM_MENU=1: troca o trecho emitido pelo db_menu() por um marcador nos DOIS lados.
# Usado so na comparacao com o TCC de referencia, onde o desktop vem desligado por um
# defeito do codigo dele (a camada V3 perde o login da sessao) e o db_menu() emite o
# menu classico (~400 linhas) no lugar do estilo/script do desktop. Separa esse defeito
# unico, sistematico, dos defeitos por tela.
MENU = [re.compile(rb'<style>\s*\nbody\.no-menu.*?</script>\n?', re.S),                          # ramo desktop
        re.compile(rb'<div id="db-menu">.*?</div>(?=<div id="db-tooltip")', re.S),                # ramo classico: menu
        re.compile(rb'<script>\s*\(window\.CurrentWindow \|\| parent\.CurrentWindow\)\.bstatus.*?autoCompleteMenu\(\);\s*\}\s*</script>', re.S)]  # classico: status

# Telas que contatam servico EXTERNO real: a bateria nao pode disparar conexao a
# terceiros. iss4_siss002 tem fixo o IP do SISS (200.192.137.56); o pg_connect leva
# ~134 s para desistir, igual nos dois runtimes -- nao e regressao, e rede.
PULAR = {'iss4_siss002.php'}
# Telas que DESTROEM a sessao autenticada do harness (session_destroy/logout): dispara-las invalida tudo o que
# vem depois ("Sessao invalida" em massa). Achadas na rodada antes: edu4_informacoesdump.php e
# cad4_geracarneiptutxt_cli.php. Espelha regressao/php/telas.py::PULAR_SESSAO.
PULAR_SESSAO = {'edu4_informacoesdump.php', 'cad4_geracarneiptutxt_cli.php'}


def main(argv, diretorio=None):
    # O projeto vive em ecidade/; sem isto o os.listdir abaixo nao acha as telas.
    diretorio = diretorio or os.path.join(RAIZ, 'ecidade')
    sid, pref = argv[1], argv[2]
    out_arq = argv[3] if len(argv) > 3 else None
    sess = f"/var/lib/php/sessions/sess_{sid}"
    (r_ref, url_ref, c_ref), (r_novo, url_novo, c_novo) = lados()
    regras = regras_norm()

    sh(f"docker exec -u root {c_ref} cp {sess} {ARQ_BACKUP}")

    def restore():
        # volume de sessoes e /tmp compartilhados: restaurar no container da referencia vale para os dois
        sh(f"docker exec -u root {c_ref} sh -c "
           f"'cp {ARQ_BACKUP} {sess}; chown www-data:www-data {sess}; chmod 600 {sess}'")

    def fetch(url, container, page):
        restore()
        # teto de 5 MB: uma pagina com laco infinito (ver -1 >= "" no PHP 8) estoura
        # a memoria do harness e o mata com SIGKILL. Truncada, ela perde o marcador
        # @@ e cai como divergente, que e o desfecho correto.
        r = sh(f"curl -s -m 60 -b 'ECIDADEWINDOWMAIN={sid}' "
               f"-w '\\n@@%{{http_code}}@%{{time_total}}' {shlex.quote(f'{url}/{page}')} | head -c 5000000")
        out = r.stdout
        i = out.rfind(b'\n@@')
        code = out[i+3:].decode(errors='replace') if i >= 0 else '???'
        code, _, t = code.partition('@')
        # Resposta que bateu no -m 60 sai TRUNCADA com codigo 200, e cada lado corta num
        # ponto diferente: parecia divergencia. Achado no mer3_mer_nutriitem002 (~53 s nos
        # dois runtimes; sob a carga da bateria passa de 60). Vira TIMEOUT.
        try:
            if t and float(t) >= 59.5:
                code = '000'
        except ValueError:
            pass
        if code == '000':
            # O curl desistiu, mas o PHP CONTINUA rodando no servidor -- e segura o
            # flock do arquivo de sessao. Como a sessao e compartilhada, toda tela
            # seguinte trava nos DOIS runtimes e "timeout nos dois" parecia identico.
            # Achado no edu4: `while(!feof(false))` e laco eterno no runtime antigo.
            sh(f"docker exec -u root {container} sh -c 'm=$(pgrep -o apache2); for p in $(pgrep apache2); do "
               f"[ $p = $m ] && continue; [ \"$(cut -d\\  -f3 /proc/$p/stat)\" = R ] && kill $p; done; true'")
        corpo = norm(out[:i] if i >= 0 else out, regras)
        if os.environ.get('NORM_MENU'):
            for rx in MENU:
                corpo = rx.sub(b'', corpo)
        return code, corpo

    files = sorted(f for f in os.listdir(diretorio)
                   if re.match(pref, f, re.IGNORECASE) and f.endswith('.php'))
    if os.environ.get('ONLY'):
        files = os.environ['ONLY'].split(',')
    for f in sorted(set(files) & PULAR):
        print(f"  PULADA {f}  (contata servico externo)", flush=True)
    for f in sorted(set(files) & PULAR_SESSAO):
        print(f"  PULADA {f}  (destroi a sessao do harness)", flush=True)
    files = [f for f in files if f not in PULAR and f not in PULAR_SESSAO]

    print(f"{len(files)} telas\n", flush=True)
    div = []
    tout = []
    for n, f in enumerate(files, 1):
        ca, ba = fetch(url_ref, c_ref, f)
        cb, bb = fetch(url_novo, c_novo, f)
        if '000' in (ca, cb):
            tout.append(f)
            print(f"  TIMEOUT {f}  {r_ref}={ca}  {r_novo}={cb}  (nao conta como identica)", flush=True)
            continue
        if not (ca == cb and ba == bb):
            # CONFIRMAR antes de acusar. Relatorios em PDF carregam um horario
            # DENTRO do fluxo comprimido (FlateDecode), fora do alcance da
            # normalizacao: se as duas requisicoes cairem em segundos diferentes,
            # os bytes mudam. Uma regressao real e persistente; um flake nao.
            ca, ba = fetch(url_ref, c_ref, f)
            cb, bb = fetch(url_novo, c_novo, f)
        if not (ca == cb and ba == bb):
            div.append((f, ca, cb, len(ba), len(bb)))
            print(f"  DIVERGE {f}  {r_ref}={ca}/{len(ba)}B  {r_novo}={cb}/{len(bb)}B", flush=True)
        if n % 50 == 0:
            print(f"  ... {n}/{len(files)}", flush=True)

    print(f"\n=== {len(files)-len(div)-len(tout)}/{len(files)} identicas, {len(div)} divergentes, {len(tout)} timeout ===")
    if out_arq and out_arq != '/dev/null':
        with open(out_arq, "w") as fh:
            for d in div:
                fh.write(f"{d[0]}\t{d[1]}\t{d[2]}\t{d[3]}\t{d[4]}\n")


if __name__ == "__main__":
    main(sys.argv)
