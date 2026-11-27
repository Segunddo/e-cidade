"""regressao/rastro/instrumenta.py: cache por hash, remocao e links (docker simulado)."""
import json

import pytest

from regressao.rastro import instrumenta


class DockerFalso:
    """Simula o contêiner: `instrumentador.php` grava `<arq>` instrumentado na pasta de saida do host."""

    def __init__(self, raiz):
        self.raiz = raiz
        self.instrumentados: list[str] = []
        self.links: list[str] = []
        self.removidos: list[str] = []
        self.lotes = 0

    def _stdin(self, stdin):
        stdin.seek(0)
        return [l for l in stdin.read().decode().splitlines() if l]

    def __call__(self, args, timeout, stdin=None, stdout=None):
        if args[0] == "cp":
            return b""
        cmd = args[-1]
        if "instrumentador.php" in cmd:
            self.lotes += 1
            saida = self.raiz / "tmp" / "ecidade-rastro"
            linhas = []
            for arq in self._stdin(stdin):
                self.instrumentados.append(arq)
                destino = saida / arq
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes((self.raiz / arq).read_bytes() + b"\n/*inst*/")
                status = "sem_parse" if "ruim" in arq else "ok"
                linhas.append(json.dumps({"arquivo": arq, "status": status, "sondas": 1}))
            return ("\n".join(linhas) + "\n").encode()
        if "liga.php" in cmd:
            self.links += self._stdin(stdin)
            return b'{"feitos":0}\n'
        if "xargs" in cmd and "rm" in cmd:
            self.removidos += self._stdin(stdin)
            return b""
        return b""


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    raiz = tmp_path / "ecidade"
    for rel, txt in {"a.php": "<?php\n$a=1;\n", "b.php": "<?php\n$b=2;\n", "dir/c.php": "<?php\n$c=3;\n",
                     "dir/ruim.php": "<?php\n$x = ;\n", "x.txt": "texto", "vendor/v.php": "<?php\n",
                     "tmp/t.php": "<?php\n", "libs/node_modules/z.php": "<?php\n"}.items():
        p = raiz / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    falso = DockerFalso(raiz)
    monkeypatch.setattr(instrumenta, "_docker", falso)
    chamadas_lint: list[list[str]] = []
    monkeypatch.setattr(instrumenta, "_lint", lambda c, arqs: chamadas_lint.append(list(arqs)) or {})
    saida = raiz / "tmp" / "ecidade-rastro"

    def roda(**kw):
        return instrumenta.instrumenta_arvore(raiz, saida, container="c85", estado=tmp_path / "estado.json",
                                              versao=kw.pop("versao", "v1"), **kw)
    return dict(raiz=raiz, saida=saida, falso=falso, roda=roda, lint=chamadas_lint, estado=tmp_path / "estado.json")


def test_primeira_execucao_instrumenta_tudo(ctx):
    r = ctx["roda"]()
    assert r.total == 4 and r.reprocessados == 4 and r.ignorados_cache == 0
    assert sorted(ctx["falso"].instrumentados) == ["a.php", "b.php", "dir/c.php", "dir/ruim.php"]
    assert r.sem_parse == ["dir/ruim.php"]
    assert (ctx["saida"] / "a.php").read_bytes().endswith(b"/*inst*/")


def test_segunda_execucao_sem_mudanca_reprocessa_zero(ctx):
    ctx["roda"]()
    ctx["falso"].instrumentados.clear()
    ctx["falso"].lotes = 0
    r = ctx["roda"]()
    assert r.reprocessados == 0 and r.ignorados_cache == 4
    assert ctx["falso"].instrumentados == [] and ctx["falso"].lotes == 0


def test_arquivo_alterado_e_o_unico_reprocessado(ctx):
    ctx["roda"]()
    ctx["falso"].instrumentados.clear()
    (ctx["raiz"] / "b.php").write_text("<?php\n$b=99;\n", encoding="utf-8")
    r = ctx["roda"]()
    assert ctx["falso"].instrumentados == ["b.php"] and r.reprocessados == 1 and r.ignorados_cache == 3


def test_mudar_a_versao_do_instrumentador_reprocessa_tudo(ctx):
    ctx["roda"](versao="v1")
    ctx["falso"].instrumentados.clear()
    r = ctx["roda"](versao="v2")
    assert r.reprocessados == 4 and len(ctx["falso"].instrumentados) == 4


def test_arquivo_removido_some_da_saida_e_do_manifesto(ctx):
    ctx["roda"]()
    (ctx["raiz"] / "a.php").unlink()
    r = ctx["roda"]()
    assert r.removidos == 1 and r.total == 3
    assert "a.php" in ctx["falso"].removidos and "a.php.json" in ctx["falso"].removidos     # o mapa fica em outra arvore
    assert "a.php" not in json.loads(ctx["estado"].read_text())["arquivos"]


def test_nao_instrumenta_vendor_tmp_node_modules(ctx):
    ctx["roda"]()
    inst = ctx["falso"].instrumentados
    assert not any(p.startswith(("vendor/", "tmp/")) or "node_modules" in p for p in inst)


def test_links_para_o_que_nao_e_instrumentado_so_na_primeira_vez(ctx):
    ctx["roda"]()
    links = ctx["falso"].links
    assert "+x.txt" in links and "+vendor" in links and "+tmp" in links
    assert "+libs/node_modules/z.php" in links                      # .php excluido da instrumentacao vira link
    assert not any(l.startswith("+vendor/") for l in links)          # vendor/ e um unico link de diretorio
    ctx["falso"].links.clear()
    ctx["roda"]()
    assert ctx["falso"].links == []


def test_falha_de_lint_que_ja_existe_no_original_nao_e_defeito_nosso(ctx, monkeypatch):
    def lint(c, arqs):
        return {a: "erro" for a in arqs if a.endswith("a.php") or a.endswith("b.php")}   # instrumentados E originais de a e b
    monkeypatch.setattr(instrumenta, "_lint", lint)
    r = ctx["roda"]()
    assert r.falhas_lint == [] and r.falhas_ja_no_original == ["a.php", "b.php"]


def test_falha_de_lint_so_no_instrumentado_e_defeito_nosso(ctx, monkeypatch):
    monkeypatch.setattr(instrumenta, "_lint", lambda c, arqs: {a: "erro" for a in arqs if a.startswith("tmp/ecidade-rastro/") and a.endswith("a.php")})
    r = ctx["roda"]()
    assert r.falhas_lint == ["a.php"] and r.falhas_ja_no_original == []


def test_lint_so_dos_arquivos_reprocessados_e_com_prefixo_da_saida(ctx):
    ctx["roda"]()
    assert all(a.startswith("tmp/ecidade-rastro/") for a in ctx["lint"][0])
    assert "tmp/ecidade-rastro/dir/ruim.php" not in ctx["lint"][0]    # sem_parse nao e linteado como instrumentado
    ctx["lint"].clear()
    ctx["roda"]()
    assert ctx["lint"] == []
