import time
from pathlib import Path

from regressao.nucleo.normaliza import hash_corpo


def grava_hashes_de_hashes(diretorio: Path, tela_para_hash: dict[str, str], rodada: str | None = None) -> Path:
    """Como grava_hashes, mas a partir de {tela: sha256 do corpo normalizado} (o orquestrador
    descarta os corpos prefixo a prefixo e guarda so o hash)."""
    rodada = rodada or time.strftime("%Y%m%d_%H%M%S")
    diretorio.mkdir(parents=True, exist_ok=True)
    destino = diretorio / f"hashes_{rodada}.tsv"
    linhas = [f"{tela}\t{h}\n" for tela, h in sorted(tela_para_hash.items())]
    destino.write_text("".join(linhas), encoding="utf-8", newline="\n")
    return destino


def grava_hashes(diretorio: Path, tela_para_corpo: dict[str, bytes], rodada: str | None = None) -> Path:
    """Escreve hashes_<rodada>.tsv: 'tela<TAB>sha256 do corpo normalizado', ordenado por tela
    (duas rodadas diferem limpo com diff)."""
    return grava_hashes_de_hashes(diretorio, {t: hash_corpo(c) for t, c in tela_para_corpo.items()}, rodada)


def _le(arquivo: Path) -> dict[str, str]:
    r = {}
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if linha:
            tela, _, h = linha.partition("\t")
            r[tela] = h
    return r


def compara_hashes(a: Path, b: Path) -> list[str]:
    """Telas cujo hash mudou entre a e b, ordenadas por nome. Tela so em `a` sai como
    '-tela' (sumiu) e so em `b` como '+tela' (apareceu): nunca se omite tela desaparecida."""
    ha, hb = _le(a), _le(b)
    saida = []
    for tela in sorted(set(ha) | set(hb)):
        if tela not in hb:
            saida.append(f"-{tela}")
        elif tela not in ha:
            saida.append(f"+{tela}")
        elif ha[tela] != hb[tela]:
            saida.append(tela)
    return saida
