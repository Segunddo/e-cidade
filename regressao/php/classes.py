import tempfile
from pathlib import Path

from regressao.nucleo.banco import ErroAmbienteBanco, _docker
from regressao.php.sintaxe import containers_php
from regressao.nucleo.veredito import Caso, Veredito

AREA = "php-classes"
RAIZ = Path(__file__).resolve().parents[2]
SCRATCH = RAIZ / "scratchpad"
DESTINO = RAIZ / "ecidade" / "tmp"
TIMEOUT_CLASSES = 900


def _parse(saida: str) -> dict[str, dict[str, str]]:
    """Registros de escrita.php: 'arq<TAB>campo<TAB>valor'; valores var_export podem
    ocupar varias linhas (continuacao, anexada com \\n, espacos preservados).
    'SEM_SAIDA arq' cria a classe vazia; '<ERRO>' e um campo como outro."""
    classes: dict[str, dict[str, str]] = {}
    atual: tuple[str, str] | None = None
    linhas = saida.split("\n")
    if linhas and linhas[-1] == "":
        linhas.pop()
    for linha in linhas:
        if linha.startswith("#"):
            continue
        if linha.startswith("SEM_SAIDA ") and "\t" not in linha:
            classes.setdefault(linha[len("SEM_SAIDA "):].strip(), {})
            atual = None
            continue
        partes = linha.split("\t", 2)
        if len(partes) >= 2 and partes[0].endswith(".php"):
            cls, campo = partes[0], partes[1]
            classes.setdefault(cls, {})[campo] = partes[2] if len(partes) == 3 else ""
            atual = (cls, campo)
        elif atual is not None:
            cls, campo = atual
            classes[cls][campo] += "\n" + linha
    return classes


def compara_classes(saida_ref: str, saida85: str) -> list[Caso]:
    """saida_ref = referencia (PHP 7.4); saida85 = alvo PHP 8.5."""
    a, b = _parse(saida_ref), _parse(saida85)
    casos = []
    for cls in sorted(set(a) | set(b)):
        ca, cb = a.get(cls, {}), b.get(cls, {})
        if not ca and not cb:
            casos.append(Caso(cls, AREA, Veredito.INCONCLUSIVO, "sem saida nos dois lados"))
            continue
        difs = [f"{k}: ref={ca.get(k, '<ausente>')} 8.5={cb.get(k, '<ausente>')}"
                for k in sorted(set(ca) | set(cb)) if ca.get(k) != cb.get(k)]
        if difs:
            casos.append(Caso(cls, AREA, Veredito.DIVERGE, "; ".join(difs), "\n".join(difs)))
        elif set(ca) == {"<ERRO>"}:
            casos.append(Caso(cls, AREA, Veredito.INCONCLUSIVO,
                              f"mesma excecao nos dois lados ({ca['<ERRO>']}); classe nao exercitada"))
        else:
            casos.append(Caso(cls, AREA, Veredito.IDENTICO))
    return casos


def roda_classes(lista: list[str]) -> list[Caso]:
    try:
        DESTINO.mkdir(parents=True, exist_ok=True)
        for nome in ("escrita.php", "porclasse.sh"):
            (DESTINO / nome).write_bytes((SCRATCH / nome).read_bytes())
        saidas = []
        with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8") as f:
            f.write("\n".join(lista) + "\n")
            f.flush()
            for c in containers_php():
                with open(f.name, "rb") as entrada:
                    saidas.append(_docker(
                        ["exec", "-i", c, "sh", "/var/www/html/tmp/porclasse.sh",
                         "/var/www/html/tmp/escrita.php"],
                        TIMEOUT_CLASSES, stdin=entrada,
                    ).decode("utf-8", errors="replace"))
    except (ErroAmbienteBanco, OSError) as e:
        return [Caso("classes", AREA, Veredito.ERRO_AMBIENTE, str(e))]
    return compara_classes(*saidas)
