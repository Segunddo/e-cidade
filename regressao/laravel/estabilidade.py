"""Estabilidade da baseline: duas gravacoes do MESMO alvo devem ser iguais.

Diferenca entre duas gravacoes = campo volatil (timestamp, contador, id gerado na hora). Este
modulo diz QUAIS caminhos do JSON divergem (para virarem `volateis` em `_ajustes.yml`) e separa
o que nao da para mascarar (status, texto, SQL, hashes, cabecalhos) para virar `instaveis`.

Uso: python -m regressao.laravel.estabilidade <dir_a> <dir_b>   (imprime o YAML de ajustes)
"""
import sys
from pathlib import Path

import yaml

from regressao.laravel.caso import _grava_registro, _le_registro
from regressao.laravel.mascara import mascara_json


def caminhos_diferentes(a, b, prefixo: str = "") -> set[str]:
    """Caminhos (pontos; `*` = elemento de lista) onde `a` e `b` diferem. Chave presente de
    um lado so, ou listas de tamanhos diferentes, apontam para o proprio no."""
    if isinstance(a, dict) and isinstance(b, dict):
        saida: set[str] = set()
        for k in set(a) | set(b):
            p = f"{prefixo}.{k}" if prefixo else str(k)
            if k not in a or k not in b:
                saida.add(p)
            else:
                saida |= caminhos_diferentes(a[k], b[k], p)
        return saida
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return {prefixo or "*"}
        saida = set()
        for x, y in zip(a, b):
            saida |= caminhos_diferentes(x, y, f"{prefixo}.*" if prefixo else "*")
        return saida
    return set() if a == b else {prefixo}


def compara_gravacoes(dir_a: Path, dir_b: Path) -> dict[str, dict]:
    """id -> {"json": [caminhos], "outros": [campos nao mascaraveis]} so para casos que diferem.
    Caso que existe so de um lado entra com `outros: ["ausente"]`."""
    dir_a, dir_b = Path(dir_a), Path(dir_b)
    saida: dict[str, dict] = {}
    nomes = {p.name for p in dir_a.glob("*.json")} | {p.name for p in dir_b.glob("*.json")}
    for nome in sorted(n for n in nomes if not n.startswith("_")):
        pa, pb = dir_a / nome, dir_b / nome
        if not (pa.is_file() and pb.is_file()):
            ident = (_le_registro(pa if pa.is_file() else pb))["id"]
            saida[ident] = {"json": [], "outros": ["ausente"]}
            continue
        ra, rb = _le_registro(pa), _le_registro(pb)
        outros = sorted(k for k in set(ra) | set(rb) if k != "json" and ra.get(k) != rb.get(k))
        js = sorted(caminhos_diferentes(ra.get("json"), rb.get("json")))
        if js or outros:
            saida[ra["id"]] = {"json": js, "outros": outros}
    return saida


def sugere_ajustes(difs: dict[str, dict], ajustes_atuais: dict | None = None) -> dict:
    """`volateis` para quem so difere no JSON; `instaveis` (com motivo) para quem difere em
    mais que isso ou no que a mascara nao alcanca (ex.: tamanho de lista, chave que some)."""
    aj = {"volateis": dict((ajustes_atuais or {}).get("volateis") or {}),
          "instaveis": dict((ajustes_atuais or {}).get("instaveis") or {})}
    for cid, d in sorted(difs.items()):
        if d["outros"]:
            aj["instaveis"][cid] = "difere entre duas gravacoes em: " + ", ".join(d["outros"])
        elif any(p in ("", "*") or p.endswith(".*") for p in d["json"]):
            aj["instaveis"][cid] = "tamanho/estrutura do JSON varia entre duas gravacoes"
        else:
            aj["volateis"][cid] = sorted(set(aj["volateis"].get(cid, [])) | set(d["json"]))
    return aj


def remascara(diretorio: Path, volateis: dict[str, list[str]]) -> int:
    """Aplica mascaras a registros ja gravados SEM mascara previa (o que `gravar` produziria
    com esses `campos_volateis` sobre a mesma resposta) e regrava `sha256`. Devolve quantos."""
    from regressao.laravel.caso import nome_arquivo, tipos_mascarados
    n = 0
    for cid, campos in volateis.items():
        arq = Path(diretorio) / nome_arquivo(cid)
        if not arq.is_file() or not campos:
            continue
        reg = _le_registro(arq)
        bruto = reg["json"]
        reg["tipos"] = tipos_mascarados(bruto, campos) if bruto is not None else {}
        reg["json"] = mascara_json(bruto, campos) if bruto is not None else None
        _grava_registro(arq, reg)
        n += 1
    return n


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python -m regressao.laravel.estabilidade <dir_a> <dir_b>", file=sys.stderr)
        return 2
    difs = compara_gravacoes(Path(argv[0]), Path(argv[1]))
    print(f"# {len(difs)} caso(s) diferem entre as duas gravacoes")
    print(yaml.safe_dump(sugere_ajustes(difs), sort_keys=True, allow_unicode=True))
    return 1 if difs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
