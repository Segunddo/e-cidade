#!/usr/bin/env python3
"""Mapa classe -> arquivo para o carga_isolada.php (nome qualificado com namespace, minusculo).

Uso (da raiz do repo): python3 scratchpad/e1_mapa.py > /tmp/mapa.tsv
Ficam de fora vendor/ (o autoload do composer cuida) e as COPIAS de classes em integracao_externa/ e
extension/ -- com elas, `db_utils` apontava para integracao_externa/gissonline/lib/db_utils.php e 56 arquivos
davam "Cannot redeclare class db_utils", um defeito do carregador e nao do codigo.
"""
import os, re

m = {}
for d, ds, fs in os.walk("ecidade"):
    ds[:] = [x for x in ds if x not in ("vendor", "tmp", "storage", "node_modules", "integracao_externa", "extension")]
    for f in fs:
        if f.endswith(".php"):
            p = os.path.join(d, f); b = open(p, "rb").read()
            ns = re.search(rb"^\s*namespace\s+([\w\\]+)\s*[;{]", b, re.M)
            pre = (ns.group(1).decode() + "\\") if ns else ""
            for x in re.finditer(rb"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait)\s+(\w+)", b, re.M):
                m.setdefault((pre + x.group(1).decode()).lower(), p[len("ecidade/"):])
print("".join(f"{k}\t{v}\n" for k, v in m.items()), end="")
