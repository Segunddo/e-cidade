"""Processo separado que aplica a regex do USUARIO (buscar_codigo_legado(regex=...)).

Roda isolado (`python -I regex_worker.py`), recebe por stdin um JSON com a regex e a lista de arquivos JA
validados pelo servidor, e escreve um JSON por linha no stdout (flush a cada arquivo). O servidor le com prazo e
mata este processo ao estourar o tempo ou os limites: uma regex catastrofica como `(a+)+$` nao prende o servidor.
Autocontido de proposito (nao importa nada do pacote).
"""
import json
import re
import sys


def _texto(caminho: str, max_bytes: int):
    try:
        with open(caminho, "rb") as f:
            dados = f.read(max_bytes + 1)
    except OSError:
        return None
    if len(dados) > max_bytes:
        return None
    # mesma regra de servidor.seguranca.decodificar: ISO-8859-1 por padrao; UTF-8 so se valido
    if dados.isascii():
        return dados.decode("ascii")
    try:
        return dados.decode("utf-8")
    except UnicodeDecodeError:
        return dados.decode("latin-1", errors="replace")


def main() -> None:
    req = json.loads(sys.stdin.read())
    rx = re.compile(req["regex"])
    max_linha, max_trecho, por_arquivo = req["max_linha"], req["max_trecho"], req["por_arquivo"]
    out = sys.stdout
    for absoluto, rel in req["arquivos"]:
        texto = _texto(absoluto, req["max_bytes"])
        if texto is None:
            continue
        achados = 0
        for n, linha in enumerate(texto.splitlines(), start=1):
            if len(linha) > max_linha or not rx.search(linha):
                continue
            achados += 1
            if achados > por_arquivo:  # o resto do arquivo nao e devolvido (nao vira leitura do arquivo inteiro)
                out.write(json.dumps({"a": rel, "omitidas": True}) + "\n")
                break
            t = linha.strip()
            t = t[:max_trecho] + ("..." if len(t) > max_trecho else "")
            out.write(json.dumps({"a": rel, "l": n, "t": t}, ensure_ascii=False) + "\n")
        out.write(json.dumps({"varrido": rel}) + "\n")
        out.flush()
    out.write('{"fim": true}\n')
    out.flush()


if __name__ == "__main__":
    main()
