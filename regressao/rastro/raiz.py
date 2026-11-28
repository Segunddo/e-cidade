"""Raiz do codigo que os contêineres EXECUTAM.

`T.DIR_TELAS` e `<onde o pacote esta>/ecidade`. Quem roda a ferramenta de um worktree (ou de uma copia) enxerga um snapshot diferente do que o
Apache serve: o instrumentador le o que esta montado em `/var/www/html`, mas os hashes do cache e o teste de existencia eram feitos na outra
arvore (o cache nunca era aproveitado e podia dar por atual um arquivo que mudou). A fonte da verdade e o ponto de montagem do contêiner.
"""
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.php import telas as T

DESTINO = "/var/www/html"


def raiz_montada(container: str | None = None) -> Path:
    """Diretorio do host montado em /var/www/html. Cai em `T.DIR_TELAS` se o docker nao responder ou o caminho nao existir no host."""
    try:
        container = container or containers_do_ambiente().php_novo
        saida = _docker(["inspect", "-f", '{{range .Mounts}}{{if eq .Destination "' + DESTINO + '"}}{{.Source}}{{end}}{{end}}', container], 20)
        p = Path(saida.decode().strip())
        if str(p) and p.is_dir():
            return p
    except Exception:
        pass
    return T.DIR_TELAS
