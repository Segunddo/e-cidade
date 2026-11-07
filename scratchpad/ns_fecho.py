#!/usr/bin/env python3
"""15a lacuna: classes COM NAMESPACE (src/, app/, api/) carregadas por autoload PSR-4.

Nenhuma das oito frentes do enumera.py as segue: elas resolvem include, `new cl_*`,
`getDao()` e as classes de model/ e std/ por nome curto. Uma tela legada que faz
`new \\ECidade\\Patrimonial\\Protocolo\\Container` (ou `use ...;` + `Container::`) carrega
src/Patrimonial/Protocolo/Container.php sem que nenhum universo o liste.

Mapa (bootstrap.php e composer.json):  ECidade\\Api\\ -> api/   ECidade\\ -> src/   App\\ -> app/

Uso:  python3 scratchpad/ns_fecho.py <lista de arquivos (relativos a ecidade/)> [<saida>]
Saida: os arquivos de src/app/api alcancados (transitivamente) que NAO estao na lista.

Tambem e importado pelo enumera.py como a 9a frente (`refs()`), com o cwd ja em ecidade/.
"""
import os, re, sys

if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ecidade'))
PREFIXOS = [("ECidade\\Api\\", "api/"), ("ECidade\\", "src/"), ("App\\", "app/")]

RX_NS    = re.compile(rb'^\s*namespace\s+([\w\\]+)\s*;', re.M)
RX_USE   = re.compile(rb'^\s*use\s+([\w\\]+)(?:\s+as\s+(\w+))?\s*;', re.M | re.I)
RX_FQ    = re.compile(rb'\\?\b((?:ECidade|App)(?:\\\w+)+)')          # nomes qualificados no codigo
RX_CURTO = re.compile(rb'(?:new|extends|implements|instanceof)\s+(\w+)|\b(\w+)::', re.I)

def arquivo(fqcn):
    fqcn = fqcn.lstrip("\\")
    for pref, base in PREFIXOS:
        if fqcn.startswith(pref):
            p = base + fqcn[len(pref):].replace("\\", "/") + ".php"
            return p if os.path.isfile(p) else None
    return None

# Servicos registrados por CHAVE DE TEXTO no bootstrap.php:
#   Registry::get('app.container')->register('patrimonial.container', function(...) {
#     return new ECidade\Patrimonial\Container(...); });
# e pedidos assim: Registry::get('app.container')->get('patrimonial.container').
# Sem isto o fecho nao chega a src/Patrimonial/Protocolo/Container.php -- o arquivo que
# revelou a lacuna (ouv4_solicitacaoprocessoeletronico.RPC.php).
SERVICOS = {}
_b = open("bootstrap.php", "rb").read()
for m in re.finditer(rb"->register\('([\w.]+)',\s*function[^{]*\{(.*?)\n\}\);", _b, re.S):
    SERVICOS[m.group(1)] = {a for a in (arquivo(x.group(1).decode()) for x in RX_FQ.finditer(m.group(2))) if a}
RX_GET = re.compile(rb"->get\('([\w.]+)'\)")

def refs(p):
    try: b = open(p, "rb").read()
    except OSError: return set()
    b = re.sub(rb'/\*.*?\*/', b'', b, flags=re.S)                     # comentario de bloco
    b = re.sub(rb'(?m)^\s*(?://|#).*$', b'', b)                        # comentario de linha
    out = set()
    for m in RX_GET.finditer(b):
        out |= SERVICOS.get(m.group(1), set())
    for m in RX_FQ.finditer(b):
        a = arquivo(m.group(1).decode()); a and out.add(a)
    usos = {}
    for m in RX_USE.finditer(b):
        fq = m.group(1).decode(); usos[(m.group(2) or fq.split("\\")[-1].encode()).decode()] = fq
        a = arquivo(fq); a and out.add(a)
    ns = RX_NS.search(b)
    for m in RX_CURTO.finditer(b):
        curto = (m.group(1) or m.group(2)).decode()
        if curto in usos: a = arquivo(usos[curto])
        elif ns: a = arquivo(ns.group(1).decode() + "\\" + curto)    # mesmo namespace, sem use
        else: a = None
        a and out.add(a)
    return out

if __name__ == "__main__":
    inicio = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    vistos, fila = set(inicio), list(inicio)
    while fila:
        for d in refs(fila.pop()):
            if d not in vistos: vistos.add(d); fila.append(d)
    novos = sorted(vistos - set(inicio))
    if len(sys.argv) > 2: open(sys.argv[2], "w").write("\n".join(novos) + ("\n" if novos else ""))
    print(f"  partida: {len(inicio)} arquivos | alcancados em src/app/api fora da lista: {len(novos)}")
