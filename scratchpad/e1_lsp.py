#!/usr/bin/env python3
"""Acha, SO PELO CODIGO, as herancas que CARREGAM no PHP 7.4 e dao FATAL no 8.x (o defeito do passo 5b).

E um caminho INDEPENDENTE do passo 5b: o 5b carrega os arquivos num PHP de verdade; este le o texto.
Os dois concordarem e a evidencia de que o 5b esta certo (docs: "Como provar que o verificador funciona").

Regras (os tipos quase nao aparecem no codigo legado; os casos com tipo saem como conferir_tipo):
  - PHP 7.4: assinatura incompativel com metodo CONCRETO da mae = so E_WARNING (a classe carrega);
             com metodo abstrato ou de interface = fatal (ja quebra no 7.4: nao e regressao).
  - PHP 8:   qualquer incompatibilidade = fatal, e um parametro opcional seguido de obrigatorio
             passa a contar como obrigatorio (o caso cl_cgs_und_ext da Saude).
  - Compativel = a filha aceita toda chamada que a mae aceita:
       total(filha) >= total(mae) (ou a filha tem ...$variadico), obrigatorios(filha) <= obrigatorios(mae)
       e o & (por referencia) igual em cada posicao.
  - __construct e metodos private da mae ficam fora (o PHP nao confere).
  - A mae e resolvida como o PHP resolve: namespace do arquivo + `use` (sem isso, o
    src/.../Sagres/Tipos/FolhaPagamento.php era tomado pela mae de FolhaPagamentoSalario).

Uso (da raiz do repo): python3 scratchpad/e1_lsp.py ecidade > /tmp/lsp.tsv
Saida TSV: filha, metodo, mae, arquivo_filha, arquivo_mae, motivo, quebra (so_no_8 | fatal_nos_dois | conferir_tipo)

Validado em 19/11/2026 na base-php74: das filhas so_no_8 que carregam sozinhas, todas deram
"must be compatible" no PHP 8.5 e carregaram no 7.4 (84 filhas, 24 familias); nenhum falso positivo.
"""
import os, re, sys

RAIZ = sys.argv[1]
PULA_DIR = {"vendor", "node_modules", ".git", "tmp", "storage"}

def limpa(b):
    """Tira comentarios e o conteudo das strings (mantem as aspas), para chaves/parenteses nao enganarem."""
    s = b.decode("latin-1")
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if s.startswith("/*", i):
            j = s.find("*/", i + 2); i = n if j < 0 else j + 2; out.append(" "); continue
        if s.startswith("//", i) or c == "#":
            j = s.find("\n", i); i = n if j < 0 else j; continue
        if c in "'\"":
            j = i + 1
            while j < n and s[j] != c:
                j += 2 if s[j] == "\\" else 1
            out.append(c + c); i = j + 1; continue
        if s.startswith("<<<", i):                       # heredoc/nowdoc
            m = re.match(r"<<<\s*['\"]?(\w+)['\"]?", s[i:])
            if m:
                fim = re.compile(r"^\s*" + m.group(1) + r"\b", re.M)
                k = fim.search(s, i + m.end())
                i = n if not k else k.end(); out.append("''"); continue
        out.append(c); i += 1
    return "".join(out)

def fecha(s, i, a, f):
    """indice do fechamento do delimitador aberto em s[i]."""
    d = 0
    for j in range(i, len(s)):
        if s[j] == a: d += 1
        elif s[j] == f:
            d -= 1
            if d == 0: return j
    return len(s)

def params(txt):
    ps, d, cur = [], 0, ""
    for c in txt:
        if c in "([": d += 1
        elif c in ")]": d -= 1
        if c == "," and d == 0: ps.append(cur); cur = ""
        else: cur += c
    if cur.strip(): ps.append(cur)
    r = []
    for p in ps:
        p = p.strip()
        tipo = re.match(r"^\??\s*([A-Za-z_\\][\w\\]*)\s+[&.]*\s*\$", p)
        r.append(dict(opt="=" in p, ref="&" in p.split("$")[0], var="..." in p,
                      tipo=tipo.group(1).lower() if tipo else ""))
    return r

def obrig(ps, php8):
    if php8:   # opcional antes de obrigatorio conta como obrigatorio
        return max([k for k, p in enumerate(ps) if not p["opt"] and not p["var"]], default=-1) + 1
    return sum(1 for p in ps if not p["opt"] and not p["var"])

RX_CLS = re.compile(r"\b(abstract\s+|final\s+)?(class|interface|trait)\s+(\w+)(\s+extends\s+([\w\\,\s]+?))?(\s+implements\s+([\w\\,\s]+?))?\s*\{", re.I)
RX_MET = re.compile(r"((?:\b(?:public|protected|private|static|abstract|final|var)\s+)*)function\s*&?\s*(\w+)\s*\(", re.I)
RX_NS = re.compile(r"^\s*namespace\s+([\w\\]+)\s*[;{]", re.M | re.I)
RX_USE = re.compile(r"^\s*use\s+([\w\\]+)(?:\s+as\s+(\w+))?\s*;", re.M | re.I)

classes = {}   # nome QUALIFICADO minusculo (ns\classe) -> dict
curto = {}     # nome curto -> [qualificados]

def resolve(nome, ns, uses):
    """Como o PHP resolve um nome de classe escrito no arquivo."""
    nome = nome.strip()
    if nome.startswith("\\"): return nome[1:].lower()
    prim = nome.split("\\")[0].lower()
    if prim in uses: return (uses[prim] + nome[len(prim):]).lower()
    return ((ns + "\\" + nome) if ns else nome).lower()

for d, ds, fs in os.walk(RAIZ):
    ds[:] = [x for x in ds if x not in PULA_DIR]
    for f in fs:
        if not f.endswith((".php", ".inc", ".class")): continue
        p = os.path.join(d, f)
        try: s = limpa(open(p, "rb").read())
        except OSError: continue
        mns = RX_NS.search(s); ns = mns.group(1) if mns else ""
        uses = {(u.group(2) or u.group(1).split("\\")[-1]).lower(): u.group(1) for u in RX_USE.finditer(s)}
        for m in RX_CLS.finditer(s):
            a = m.end() - 1; b = fecha(s, a, "{", "}"); corpo = s[a + 1:b]
            mets, k = {}, 0
            while True:                          # so os metodos do nivel do corpo
                mm = RX_MET.search(corpo, k)
                if not mm: break
                pa = mm.end() - 1; pf = fecha(corpo, pa, "(", ")")
                mods = mm.group(1).lower()
                mets[mm.group(2).lower()] = dict(nome=mm.group(2), ps=params(corpo[pa + 1:pf]),
                    priv="private" in mods, abst="abstract" in mods or m.group(2).lower() == "interface")
                prox = corpo.find("{", pf); semi = corpo.find(";", pf)
                k = (semi + 1) if (semi >= 0 and (prox < 0 or semi < prox)) else (fecha(corpo, prox, "{", "}") + 1)
            nome = m.group(3); kind = m.group(2).lower()
            pais = [resolve(x, ns, uses) for x in (m.group(5) or "").split(",") if x.strip()]
            ifs = [resolve(x, ns, uses) for x in (m.group(7) or "").split(",") if x.strip()]
            q = ((ns + "\\") if ns else "").lower() + nome.lower()
            if q in classes: continue            # nome repetido: fica o primeiro
            classes[q] = dict(nome=nome, arq=os.path.relpath(p, RAIZ), kind=kind,
                pai=pais[0] if kind == "class" and pais else "", ifs=ifs + (pais if kind == "interface" else []),
                mets=mets)
            curto.setdefault(nome.lower(), []).append(q)

def acha(q):
    if q in classes: return classes[q]
    c = curto.get(q.split("\\")[-1], [])      # namespace nao resolvido: so se o nome curto for unico
    return classes[c[0]] if len(c) == 1 else None

def ancestral(c, met):
    """(classe, metodo) mais proximo acima de c que declara met: mae, avos, interfaces."""
    cand, visto = [], set()
    pai = acha(c["pai"]) if c["pai"] else None
    while pai and pai["arq"] + pai["nome"] not in visto:
        visto.add(pai["arq"] + pai["nome"])
        if met in pai["mets"]: cand.append((pai, pai["mets"][met])); break
        pai = acha(pai["pai"]) if pai["pai"] else None
    fila, vis = list(c["ifs"]), set()
    while fila:
        i = acha(fila.pop())
        if not i or i["arq"] + i["nome"] in vis: continue
        vis.add(i["arq"] + i["nome"])
        if met in i["mets"]: cand.append((i, i["mets"][met]))
        fila += i["ifs"]
    return cand

def incompat(f, m, php8):
    fp, mp, mot = f["ps"], m["ps"], []
    if len(fp) < len(mp) and not any(p["var"] for p in fp): mot.append(f"filha tem {len(fp)} param., mae {len(mp)}")
    if obrig(fp, php8) > obrig(mp, php8): mot.append(f"filha exige {obrig(fp, php8)}, mae {obrig(mp, php8)}")
    if any(a["ref"] != b["ref"] for a, b in zip(fp, mp)): mot.append("& diferente")
    return mot

for c in classes.values():
    if c["kind"] != "class": continue
    for met, f in c["mets"].items():
        if met == "__construct": continue
        for dono, m in ancestral(c, met):
            if m["priv"]: continue
            i8, i7 = incompat(f, m, True), incompat(f, m, False)
            tip = any(a["tipo"] != b["tipo"] and a["tipo"] for a, b in zip(f["ps"], m["ps"]))
            if not i8 and not tip: continue
            abstrato = m["abst"] or dono["kind"] == "interface"
            quebra = "fatal_nos_dois" if (i7 and abstrato) else ("so_no_8" if i8 else "conferir_tipo")
            print("\t".join([c["nome"], f["nome"], dono["nome"], c["arq"], dono["arq"],
                             "; ".join(i8) or "tipo do parametro difere", quebra]))
