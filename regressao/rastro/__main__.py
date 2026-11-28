"""CLI do rastreador:  python -m regressao.rastro <comando>

  instrumenta [--forcar]                 instrumenta a arvore inteira (so reprocessa o que mudou) e liga o vhost 8091
  equivalencia [--amostra N]             portao: a arvore instrumentada responde igual a normal? (N telas, semente fixa)
  rastreia TELA... [--saida DIR]         rastreia as telas nos dois PHP e escreve o relatorio
  rastreia --de-rodada DIR [--area A]    rastreia as telas DIVERGE de uma rodada da bateria (DIR/[A/]resultado.json)
"""
import argparse
import json
import sys
from pathlib import Path

from regressao.nucleo.ambiente import containers_do_ambiente
from regressao.nucleo.banco import _docker
from regressao.php import telas as T
from regressao.rastro import equivalencia, executor, servidor
from regressao.rastro.classifica import Resultado, classifica
from regressao.rastro.evento import le_rastro
from regressao.rastro.raiz import raiz_montada
from regressao.rastro.relatorio import escreve_relatorio

SAIDA_PADRAO = Path("rastro-saida")


def _leitor_de_mapas(container: str):
    """`le(arquivo, sonda) -> nomes das variaveis lidas pela sonda`, lendo o .json do mapa dentro do contêiner (com cache)."""
    cache: dict[str, dict] = {}

    def le(arquivo: str, sonda: int) -> list[str]:
        if arquivo not in cache:
            try:
                bruto = _docker(["exec", container, "sh", "-c", f"cat {servidor.MAPAS}/{arquivo}.json 2>/dev/null; true"], 30)
                cache[arquivo] = json.loads(bruto or b"{}")
            except ValueError:
                cache[arquivo] = {}
        return list(cache[arquivo].get(str(sonda), {}).get("le", []))
    return le


def rastreia_telas(telas: list[str], saida: Path) -> dict:
    c = containers_do_ambiente()
    for n in (c.ref, c.php_novo):
        servidor.liga_vhost(n)
    sid = executor.nova_sessao()
    le = _leitor_de_mapas(c.php_novo)
    resultados, rastros = {}, {}
    for tela in telas:
        try:
            a = executor.roda_requisicao(sid, tela, f"r74a_{tela}", c.ref)
            b = executor.roda_requisicao(sid, tela, f"r74b_{tela}", c.ref)
            n = executor.roda_requisicao(sid, tela, f"r85_{tela}", c.php_novo)
            resultados[tela] = classifica(le_rastro(a.rastro), le_rastro(n.rastro), le_rastro(b.rastro),
                                          (a.status, a.corpo), (n.status, n.corpo), le=le)
            rastros[tela] = {"ref74": a.rastro, "ref74_2": b.rastro, "alvo85": n.rastro}
        except Exception as e:     # uma tela com problema nao derruba as outras: fica INCONCLUSIVO com o motivo
            resultados[tela] = Resultado("INCONCLUSIVO", nota=f"erro ao rastrear: {type(e).__name__}: {str(e)[:160]}")
            rastros[tela] = {}
        print(f"{resultados[tela].veredito:24} {tela}", flush=True)
    arq = escreve_relatorio(resultados, saida, rastros)
    print("relatorio:", arq)
    return resultados


def rastreia_telas_xdebug(telas: list[str], saida: Path) -> dict:
    """Backend B: rastro pelo Xdebug (nada instrumentado). Mesmo classificador e relatorio."""
    from regressao.rastro import xdebug
    c = containers_do_ambiente()
    for n in (c.ref, c.php_novo):
        xdebug.prepara(n)                  # instala se faltar; deixa em mode=off
        xdebug.modo(n, "trace")            # so durante o rastreio: o trace custa alguns ms por requisicao
    try:
        return _rastreia_xdebug(telas, saida, c, xdebug)
    finally:
        for n in (c.ref, c.php_novo):
            xdebug.modo(n, "off")


def _rastreia_xdebug(telas, saida, c, xdebug) -> dict:
    from regressao.rastro import estatica
    sid = executor.nova_sessao()
    funcoes = xdebug.funcoes_da_lista()
    le_linha = estatica.leitor_de_linhas(c.php_novo)       # fase C: variaveis lidas por linha, para a cadeia por dependencia
    resultados, rastros = {}, {}
    for tela in telas:
        try:
            a, ea = xdebug.roda_requisicao_xdebug(sid, tela, c.ref, funcoes)
            b, eb = xdebug.roda_requisicao_xdebug(sid, tela, c.ref, funcoes)
            n, en = xdebug.roda_requisicao_xdebug(sid, tela, c.php_novo, funcoes)
            r = classifica(ea, en, eb, (a.status, a.corpo), (n.status, n.corpo), le_linha=le_linha)
            if r.sintoma is not None and not r.cadeia:     # a analise estatica nao achou o que a linha le: contexto por proximidade
                s = r.sintoma
                r.cadeia = [e for e in en if e.tipo == "a" and e.arquivo == s.arquivo and s.linha - 12 <= e.linha <= s.linha][-6:]
                r.nota = (r.nota + " | " if r.nota else "") + "cadeia = ultimas atribuicoes do arquivo nas 12 linhas antes do sintoma (sem dependencia de dados)"
            resultados[tela] = r
            rastros[tela] = {}
        except Exception as e:
            resultados[tela] = Resultado("INCONCLUSIVO", nota=f"erro ao rastrear: {type(e).__name__}: {str(e)[:160]}")
            rastros[tela] = {}
        print(f"{resultados[tela].veredito:24} {tela}", flush=True)
    print("relatorio:", escreve_relatorio(resultados, saida, rastros))
    return resultados


def telas_divergentes(diretorio: Path, area: str | None) -> list[str]:
    arq = diretorio / area / "resultado.json" if area else diretorio / "resultado.json"
    casos = json.loads(arq.read_text(encoding="utf-8"))["casos"]
    return sorted({c["id"].split(":", 1)[1] for c in casos if c["veredito"] == "DIVERGE" and c["id"].startswith("tela:")})


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m regressao.rastro", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("instrumenta"); i.add_argument("--forcar", action="store_true")
    e = sub.add_parser("equivalencia"); e.add_argument("--amostra", type=int, default=200)
    c = sub.add_parser("cruza", help="compara os relatorios dos backends: sondas (A) x Xdebug (B)")
    c.add_argument("a", type=Path, help="pasta (ou relatorio.md) do backend de sondas")
    c.add_argument("b", type=Path, help="pasta (ou relatorio.md) do backend Xdebug")
    c.add_argument("--saida", type=Path, default=Path("cruzamento"))
    s = sub.add_parser("estatica", help="fase C: lista, so lendo o codigo, os usos de resultado de consulta sem checagem")
    s.add_argument("--saida", type=Path, default=None)
    s.add_argument("--modo", choices=("candidatos", "comparacoes"), default="candidatos",
                   help="candidatos = resultado de consulta sem checagem; comparacoes = == / != / switch com literal (0 == 't' mudou no PHP 8)")
    r = sub.add_parser("rastreia")
    r.add_argument("telas", nargs="*"); r.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    r.add_argument("--de-rodada", type=Path); r.add_argument("--area")
    r.add_argument("--backend", choices=("sondas", "xdebug"), default="sondas",
                   help="sondas = arvore instrumentada (padrao); xdebug = trace do Xdebug, sem instrumentar nada")
    a = p.parse_args(argv)

    if a.cmd == "instrumenta":
        from regressao.rastro.instrumenta import instrumenta_arvore
        raiz = raiz_montada()
        res = instrumenta_arvore(raiz, raiz / "tmp" / "ecidade-rastro", forcar=a.forcar)
        print(res)
        c = containers_do_ambiente()
        for n in (c.ref, c.php_novo):
            servidor.liga_vhost(n)
        return 0 if not res.falhas_lint else 1
    if a.cmd == "equivalencia":
        res = equivalencia.confere_equivalencia(executor.nova_sessao(), equivalencia.amostra_telas(a.amostra))
        print(f"{res.total} telas | diferentes: {res.diferentes} | instaveis: {len(res.instaveis)}")
        return 0 if not res.diferentes else 1
    if a.cmd == "cruza":
        from regressao.rastro import cruza
        ler = lambda p: cruza.le_relatorio((p / "relatorio.md" if p.is_dir() else p).read_text(encoding="utf-8"))
        linhas = cruza.cruza(ler(a.a), ler(a.b))
        md, _ = cruza.escreve(linhas, a.saida)
        print(cruza.resumo(linhas), "->", md)
        return 0
    if a.cmd == "estatica":
        from regressao.php.arvore import lista_arvore
        from regressao.rastro import estatica
        arquivos = lista_arvore(frozenset(), raiz_montada())
        if a.modo == "comparacoes":
            achados = estatica.comparacoes(arquivos)
            saida = a.saida or Path("comparacoes-estaticas.tsv")
            linhas = ["arquivo\tlinha\ttipo\tevidencia\top\texpressao\tliteral"]
            linhas += [f"{arq}\t{c['linha']}\t{c['tipo']}\t{c['evidencia']}\t{c['op']}\t{c['expressao']}\t{c['literal']}"
                       for arq, cs in sorted(achados.items()) for c in sorted(cs, key=lambda c: c["linha"])]
        else:
            achados = estatica.candidatos(arquivos)
            saida = a.saida or Path("candidatos-estaticos.tsv")
            linhas = ["arquivo\tlinha\tfuncao\tvariavel\torigem"]
            linhas += [f"{arq}\t{c['linha']}\t{c['funcao']}\t{c['variavel']}\t{c['origem']}"
                       for arq, cs in sorted(achados.items()) for c in sorted(cs, key=lambda c: c["linha"])]
        saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        print(f"{len(linhas) - 1} {a.modo} em {len(achados)} arquivos -> {saida}")
        return 0
    telas = list(a.telas) + (telas_divergentes(a.de_rodada, a.area) if a.de_rodada else [])
    if not telas:
        p.error("informe telas ou --de-rodada")
    (rastreia_telas_xdebug if a.backend == "xdebug" else rastreia_telas)(telas, a.saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
