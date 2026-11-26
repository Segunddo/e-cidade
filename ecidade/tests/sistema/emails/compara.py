#!/usr/bin/env python3
"""Roda email.php no 7.4 (SwiftMailer, vendor do lock do PR) e no 8.5 (Symfony Mailer, Laravel 13) por roda-isolado.sh e compara
cada e-mail por conteudo: assunto, remetente, destinatarios, cabecalhos relevantes, partes (tipo, charset, corpo decodificado).
A ordem dos cabecalhos e a quebra de linha do quoted-printable mudam entre os dois transportes e nao contam.
Uso (raiz do repositorio): python3 ecidade/tests/sistema/emails/compara.py   -> rc 1 se algum e-mail difere."""
import email, email.policy, os, re, subprocess, sys, tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
RODA = os.path.join(RAIZ, 'docker/composer-85/roda-isolado.sh')
ENVX = 'MAIL_DRIVER=array\nMAIL_FROM_ADDRESS=prefeitura@example.org\nMAIL_FROM_NAME=Prefeitura Exemplo\nREDESIM_MAIL_ADDRESS_ON_ERROR=erro1@example.org,erro2@example.org\n'
RELEVANTES = ['subject', 'from', 'to', 'cc', 'bcc', 'reply-to', 'sender', 'mime-version', 'content-type', 'content-transfer-encoding']


def roda(versao):
    vendor = os.path.join(RAIZ, 'runtime-85/referencia-74/vendor' if versao == '7.4' else 'runtime-85/vendor')
    with tempfile.NamedTemporaryFile('w', suffix='.env') as f:
        f.write(ENVX); f.flush()
        env = dict(os.environ, ENV_EXTRA=f.name, VENDOR=vendor)
        p = subprocess.run(['bash', RODA, versao, os.path.join(os.path.dirname(__file__), 'email.php')], capture_output=True, env=env)
    if p.returncode != 0:
        sys.exit('ERRO: email.php no %s rc=%d\n%s' % (versao, p.returncode, p.stderr[-1500:].decode('latin-1')))
    # latin-1: bijetivo; os modelos .blade do PR sao ISO-8859-1 e o texto sai em bytes crus nos dois runtimes
    return p.stdout.decode('latin-1'), [l for l in p.stderr.decode('latin-1').splitlines() if re.match(r'(Deprecated|Warning|Notice):', l)]


def blocos(saida):
    partes = re.split(r'^== (.*)$', saida, flags=re.M)
    cab = partes[0]
    return cab, {partes[i]: partes[i + 1].strip('\n') for i in range(1, len(partes), 2)}


def resumo(texto):
    if texto.startswith('EXCECAO'):
        return {'excecao': texto.splitlines()[0]}
    m = email.message_from_string(texto, policy=email.policy.default)
    r = {h: ' | '.join(sorted(str(v) for v in m.get_all(h, []))) for h in RELEVANTES if m.get_all(h)}
    r['partes'] = []
    for p in m.walk():
        if p.is_multipart():
            r['partes'].append((p.get_content_type(), 'multipart'))
            continue
        corpo = p.get_payload(decode=True) or b''
        txt = re.sub(r'\s+', ' ', corpo.decode(p.get_content_charset() or 'utf-8', 'replace')).strip() if p.get_content_maintype() == 'text' else len(corpo)
        r['partes'].append((p.get_content_type(), p.get_content_charset(), p.get_filename(), txt))
    return r


def main():
    s74, a74 = roda('7.4')
    s85, a85 = roda('8.5')
    c74, b74 = blocos(s74); c85, b85 = blocos(s85)
    dif = 0
    for linha in c74.splitlines():
        par = [l for l in c85.splitlines() if l.split(':')[0] == linha.split(':')[0]]
        print('  cabecalho  7.4: %s | 8.5: %s' % (linha, par[0] if par else '-'))
    if set(b74) != set(b85):
        print('DIFERE: conjuntos de e-mails %s x %s' % (sorted(b74), sorted(b85))); dif += 1
    for nome in sorted(set(b74) & set(b85)):
        r74, r85 = resumo(b74[nome]), resumo(b85[nome])
        if r74 == r85:
            print('  igual   %s (%d partes)' % (nome, len(r74.get('partes', []))))
        else:
            dif += 1
            ks = [k for k in set(r74) | set(r85) if r74.get(k) != r85.get(k)]
            print('  DIFERE  %s: %s' % (nome, ', '.join(sorted(ks))))
            for k in sorted(ks):
                print('     7.4 %s: %s\n     8.5 %s: %s' % (k, str(r74.get(k))[:300], k, str(r85.get(k))[:300]))
    print('avisos 7.4=%d, 8.5=%d' % (len(a74), len(a85)))
    print('DIFERENCAS: %d' % dif)
    sys.exit(1 if dif else 0)


if __name__ == '__main__':
    main()
