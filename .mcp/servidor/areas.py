"""Areas do grupo (CONTRIBUINDO.md, "Divisao por area (sugestao inicial)"): cada pessoa mexe so na sua area.

Telas da raiz de ecidade/ vao pela sigla do nome (`con1_x.php` -> `con`); pastas, pelo comeco do caminho.
Arquivo fora da tabela = sem area definida (combine com o coordenador).
"""
from __future__ import annotations

import re

AREAS_GRUPO: dict[str, dict] = {
    "nucleo": {"titulo": "Nucleo e coordenacao", "siglas": (),
               "pastas": ("libs/", "dbforms/", "config/"), "arquivos": ("frontcontroller.php", "login.php")},
    "educacao": {"titulo": "Educacao", "siglas": ("edu",), "pastas": ("src/educacao/",), "arquivos": ()},
    "pessoal": {"titulo": "Pessoal (RH)", "siglas": ("pes",), "pastas": ("src/recursoshumanos/",), "arquivos": ()},
    "financeiro": {"titulo": "Financeiro", "siglas": ("con", "cai", "orc", "emp"), "pastas": (), "arquivos": ()},
    "tributario_patrimonial": {"titulo": "Tributario e Patrimonial",
                               "siglas": ("cad", "iss", "fis", "pro", "arr", "div", "itb", "com", "mat", "pat",
                                          "lic", "aco"), "pastas": (), "arquivos": ()},
    "saude_demais": {"titulo": "Saude e demais",
                     "siglas": ("sau", "ate", "lab", "far", "agu", "mer", "vei", "bib", "ouv", "soc"),
                     "pastas": (), "arquivos": ()},
}
SEM_AREA = "sem_area"  # nao e dono de ninguem na tabela: func_*, classes/, pre*, rec*, jur* ... (escolha-a de proposito)
AREAS_VALIDAS = (*AREAS_GRUPO, SEM_AREA)
_SIGLA = re.compile(r"^([a-z]+)\d*_")


def area_do_arquivo(rel: str) -> str | None:
    """`ecidade/con1_x.php` -> 'financeiro'; None se a tabela do grupo nao cobre o arquivo."""
    r = rel[len("ecidade/"):] if rel.startswith("ecidade/") else rel
    r = r.lower()
    for nome, a in AREAS_GRUPO.items():
        if r in a["arquivos"] or r.startswith(a["pastas"]):
            return nome
    if "/" not in r:
        m = _SIGLA.match(r)
        if m:
            for nome, a in AREAS_GRUPO.items():
                if m.group(1) in a["siglas"]:
                    return nome
    return None


def area_efetiva(rel: str) -> str:
    """Como area_do_arquivo, mas devolve 'sem_area' em vez de None (permite escolher esse trabalho)."""
    return area_do_arquivo(rel) or SEM_AREA


def validar_area(area: str | None) -> str | None:
    if area in (None, ""):
        return None
    if area not in AREAS_VALIDAS:
        from servidor.seguranca import ErroFerramenta
        raise ErroFerramenta("parametro_invalido", f"area {area!r}; validas: {', '.join(AREAS_VALIDAS)}")
    return area
