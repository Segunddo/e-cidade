"""Documentos do MCP: alvo Laravel 13, regras do grupo presentes e codificacao certa."""
from pathlib import Path

import pytest

MCP = Path(__file__).resolve().parents[1]
RAIZ = MCP.parent
# guia-7.4-para-8.5.md e o texto do grupo na integra (cita o 12 como "serviria de parada"): fica fora da checagem
NOSSOS = [MCP / "README.md", MCP / "estado" / "README.md", *(p for p in (MCP / "docs").glob("*.md")
                                                               if p.name != "guia-7.4-para-8.5.md")]


@pytest.mark.parametrize("arq", NOSSOS, ids=lambda p: p.name)
def test_alvo_e_laravel_13_nunca_12(arq):
    texto = arq.read_text(encoding="utf-8")
    assert "Laravel 12" not in texto and "Laravel 8 -> 12" not in texto and "8 → 12" not in texto


def test_codigo_do_servidor_nao_fala_laravel_12():
    for p in (MCP / "servidor").rglob("*.py"):
        assert "Laravel 12" not in p.read_text(encoding="utf-8"), p


def test_regras_e_numeros_do_guia_do_grupo_nos_docs():
    regras = (MCP / "docs" / "regras-do-grupo.md").read_text(encoding="utf-8")
    for frase in ("git add .", "WSL", "ISO-8859-1", "Rector", "Cada pessoa mexe só na sua área",
                  "composer.json", "push --force", "Pull request pequeno", "Não repetir trabalho",
                  "Funciona igual ao 7.4", "O código do PR tem prioridade", "Só atualizar", "O 7.4 fica intacto",
                  "Não tocar no banco", "auditoria", "Seguir precedente", "PHP8-NN: descrição curta",
                  "Documentos autocontidos", "git checkout base-php74", "Laravel 13 + Passport 13"):
        assert frase in regras, frase
    # decisao 11 (19/11/2026): o formato de commit e o do CONTRIBUINDO.md, em todos os documentos do MCP
    for doc in ("regras-do-grupo.md", "regras-arquitetura.md"):
        texto = (MCP / "docs" / doc).read_text(encoding="utf-8")
        assert "PHP8-NN" in texto and "decisão em aberto" not in texto, doc
    readme = (MCP / "README.md").read_text(encoding="utf-8")
    assert "PHP8-NN: descrição curta" in readme and "ECIDADE_MCP_TAREFA" in readme
    assert "verbo no presente" not in readme
    guia = (MCP / "docs" / "guia-breaking-changes.md").read_text(encoding="utf-8")
    for numero in ("32 arquivos", "84 usos", "40 usos", "36.729", "4.054", "152 classes", "1.832", "113 arq",
                   "10 pacotes", "dbseller/sdk-api-pix-bb", "proner/phppimaco", "Cache::put", "array_pluck",
                   "str_random", "82 usos", "$$x[$i]", "break` fora de laço", "Passport 13"):
        assert numero in guia, numero
    arq = (MCP / "docs" / "regras-arquitetura.md").read_text(encoding="utf-8")
    assert "base-php84" in arq and "ISO-8859-1" in arq and "Laravel 13" in arq and "migra(" not in arq


def test_guia_do_grupo_convertido_e_fiel():
    guia = (MCP / "docs" / "guia-7.4-para-8.5.md").read_text(encoding="utf-8")
    for trecho in ("# Migração do PHP 7.4 para o 8.5 a partir do PR #8", "36.729 vezes em 4.054 arquivos",
                   "152 classes em 143 arquivos", "Laravel 13 + Passport 13", "737 migrations",
                   "| `$$x[$i]` e `$o->$p[$i]`", "## Glossário"):
        assert trecho in guia, trecho
    assert "<" + "div" not in guia and "<" + "td" not in guia
