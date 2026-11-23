"""Executor destacado de uma rodada da regressao (processo filho em sessao propria).

Uso interno: `python executor.py <.mcp/rodadas/ID/meta.json>`. Le o argv ja validado pela tool, confere de novo
que e a suite `regressao` com o venv do projeto (sem shell), roda com cwd na raiz e grava `fim.json` com o codigo
de saida. A saida do comando vai para o log aberto pelo servidor (stdout/stderr deste processo).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MODULOS = {"regressao.php.bateria", "regressao.laravel.bateria", "regressao.completa.fluxos",
           "regressao.completa.orquestra"}


def main(meta_arq: str) -> int:
    meta_p = Path(meta_arq).resolve()
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    raiz = Path(meta["raiz"])
    argv = meta["argv"]
    if (argv[0] != str(raiz / "regressao" / ".venv" / "bin" / "python") or argv[1] != "-m"
            or argv[2] not in MODULOS or not all(isinstance(a, str) for a in argv)):
        print(f"argv recusado: {argv!r}", file=sys.stderr)
        codigo = 126
    else:
        print(f"[executor] {' '.join(argv)}", flush=True)
        codigo = subprocess.run(argv, cwd=raiz, stdin=subprocess.DEVNULL, check=False).returncode
    fim = {"codigo_saida": codigo, "fim": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    tmp = meta_p.with_name("fim.json.tmp")
    tmp.write_text(json.dumps(fim), encoding="utf-8")
    tmp.replace(meta_p.with_name("fim.json"))
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
