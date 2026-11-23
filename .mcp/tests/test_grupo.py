import subprocess
from pathlib import Path

import pytest

from servidor.seguranca import ErroFerramenta
from servidor.tools.grupo import descricao_do_cabecalho, ferramentas_do_grupo, regras_do_grupo

REGRAS_REAIS = Path(__file__).resolve().parents[1] / "docs" / "regras-do-grupo.md"


@pytest.fixture
def repo(config):
    (config.raiz / ".mcp" / "docs" / "regras-do-grupo.md").write_text(REGRAS_REAIS.read_text(encoding="utf-8"))
    sp = config.raiz / "scratchpad"
    (sp / "rector-rules").mkdir(parents=True)
    (sp / "cmp.py").write_text('#!/usr/bin/env python3\n"""Compara as telas de um modulo entre os runtimes.\n\nMais."""\n')
    (sp / "escrita.php").write_bytes("<?php\n// Exercita o CAMINHO DE ESCRITA das classes de dados\n// sem tocar no banco (situação).\n".encode("iso-8859-1"))
    (sp / "rector-rules" / "Guarda.php").write_text("<?php\ndeclare(strict_types=1);\nnamespace X;\n"
                                                     "final class GuardaComparacaoLiteralRector extends AbstractRector {}\n")
    (sp / "porclasse.sh").write_text("#!/bin/bash\n# Roda um processo por classe\nexit 0\n")
    (sp / ".env").write_text("SEGREDO=1")
    return config


def test_regras_do_grupo_inteiras_e_por_topico(repo):
    r = regras_do_grupo(repo)
    assert "Regras do grupo (CONTRIBUINDO.md)" in r["topicos"]
    assert "ISO-8859-1" in r["texto"] and "Laravel 13" in r["texto"]
    r = regras_do_grupo(repo, topico="base-php84")
    assert "$$x[$i]" in r["texto"] and "Nunca" in r["texto"] and "Fluxo" not in r["texto"]
    r = regras_do_grupo(repo, topico="metodo")
    assert "Só atualizar" in r["texto"]
    with pytest.raises(ErroFerramenta) as e:
        regras_do_grupo(repo, topico="nao existe")
    assert e.value.codigo == "topico_inexistente"


def test_regras_do_repo_real_falam_laravel_13_e_nao_12():
    texto = REGRAS_REAIS.read_text(encoding="utf-8")
    assert "Laravel 13 + Passport 13" in texto and "Laravel 12" not in texto


def git_falso(arvore):
    def run(argv, **kw):
        assert argv[0] == "git" and "-C" in argv
        if argv[3] == "ls-tree":
            return subprocess.CompletedProcess(argv, 0, "\n".join(arvore).encode(), b"")
        if argv[3] == "show":
            caminho = argv[4].split(":", 1)[1]
            return subprocess.CompletedProcess(argv, 0, arvore[caminho].encode("latin-1"), b"")
        return subprocess.CompletedProcess(argv, 1, b"", b"")
    return run


def test_ferramentas_do_grupo_arvore_e_ref(repo):
    arvore = {"scratchpad/cmp.py": '"""outra versao"""',
              "scratchpad/rector-rules/ParseStrComExtractRector.php": "<?php\n/**\n * Troca parse_str de 1 argumento\n */\nclass P {}",
              "scratchpad/../segredo": "x", "scratchpad/.env": "S=1"}
    r = ferramentas_do_grupo(repo, git_runner=git_falso(arvore))
    por = {f["arquivo"]: f for f in r["ferramentas"]}
    assert por["scratchpad/cmp.py"]["origem"] == "arvore de trabalho"
    assert por["scratchpad/cmp.py"]["descricao"].startswith("Compara as telas de um modulo")
    assert "situação" in por["scratchpad/escrita.php"]["descricao"]
    assert "GuardaComparacaoLiteralRector" in por["scratchpad/rector-rules/Guarda.php"]["descricao"]
    assert por["scratchpad/porclasse.sh"]["descricao"] == "Roda um processo por classe"
    so_ref = por["scratchpad/rector-rules/ParseStrComExtractRector.php"]
    assert so_ref["origem"] == "so em origin/base-php74" and "parse_str" in so_ref["descricao"]
    assert "scratchpad/.env" not in por and not any(".." in k for k in por)
    assert "scratchpad/escrita.php" in r["destaques"]


def test_ferramentas_ref_invalida_ou_ausente(repo):
    with pytest.raises(ErroFerramenta):
        ferramentas_do_grupo(repo, ref="--output=/tmp/x")
    r = ferramentas_do_grupo(repo, ref="origin/nao-existe",
                             git_runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 128, b"", b"bad"))
    assert any("indisponivel" in a for a in r["avisos"]) and r["ferramentas"]


def test_descricao_sem_cabecalho():
    assert descricao_do_cabecalho("x.tsv", "a\tb\n") == "(dados)"
    assert descricao_do_cabecalho("x.php", "<?php\necho 1;\n") == "(sem cabecalho)"
