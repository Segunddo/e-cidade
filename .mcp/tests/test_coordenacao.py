import subprocess

import pytest

from servidor.seguranca import ErroFerramenta
from servidor.tools import coordenacao as co


@pytest.fixture
def repo(config):
    e = config.raiz / "ecidade"
    for i in range(4):
        (e / f"t{i}.php").write_text("<?php\nparse_str($HTTP_SERVER_VARS['QUERY_STRING']);\n")
    (e / "s.php").write_text("<?php\n$a = split('-', $b);\n")
    return config


def git_falso(saida="", cod=0):
    def run(argv, **kw):
        assert argv[0] == "git" and "-C" in argv
        return subprocess.CompletedProcess(argv, cod, saida, "")
    return run


def test_reivindicar_e_liberar(repo):
    r = co.reivindicar_arquivo(repo, "ecidade/t1.php", "parse_str", quem="ana")
    assert r["quem"] == "ana" and r["caminho"] == "ecidade/t1.php"
    assert "git add .mcp/estado/trabalho.json" in r["sugestao_commit"]
    with pytest.raises(ErroFerramenta) as e:
        co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="bruno")
    assert e.value.codigo == "ja_reivindicado"
    r = co.liberar_arquivo(repo, "ecidade/t1.php", quem="ana", concluido=True, padroes_corrigidos=["parse_str_1_arg"])
    assert r["concluido"] is True


def test_sugestoes_de_commit_com_aspas_de_shell(repo):
    import shlex
    r = co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="ana")
    partes = shlex.split(r["sugestao_commit"])
    assert partes[-2:] == ["-m", "PHP8-NN: reivindica ecidade/t1.php no quadro"]
    assert "ECIDADE_MCP_TAREFA" in r["aviso_commit"]
    r = co.liberar_arquivo(repo, "ecidade/t1.php", quem="ana", concluido=True, padroes_corrigidos=["split"])
    assert shlex.split(r["commit_do_codigo"]) == ["git", "add", "--", "ecidade/t1.php", "&&", "git", "commit", "-m",
                                                  "PHP8-NN: corrige split em ecidade/t1.php",
                                                  "-m", "Padrao-MCP: split"]
    assert "Rector" in r["lembrete"]


def test_sugestoes_de_commit_com_o_numero_da_tarefa(repo):
    """Formato do CONTRIBUINDO.md: `PHP8-NN: descricao curta`, com NN vindo de ECIDADE_MCP_TAREFA."""
    import dataclasses
    import shlex
    cfg = dataclasses.replace(repo, tarefa="31")
    r = co.reivindicar_arquivo(cfg, "ecidade/t2.php", "x", quem="ana")
    assert shlex.split(r["sugestao_commit"])[-1] == "PHP8-31: reivindica ecidade/t2.php no quadro"
    assert "aviso_commit" not in r
    r = co.liberar_arquivo(cfg, "ecidade/t2.php", quem="ana", concluido=True, padroes_corrigidos=["parse_str_1_arg"])
    assert "PHP8-31: corrige parse_str_1_arg em ecidade/t2.php" in shlex.split(r["commit_do_codigo"])
    r = co.proximo_trabalho(cfg, padrao="split", quem="ana", reivindicar=True)
    assert shlex.split(r["sugestao_commit"])[-1] == "PHP8-31: reivindica lote de split no quadro"
    assert co.padroes_ja_corrigidos(cfg, git_runner=git_falso())["convencao_commit"].startswith(
        "assunto no formato do CONTRIBUINDO.md: 'PHP8-31: descricao curta'")


def test_tarefa_do_commit_vem_do_ambiente():
    from servidor.config import carregar_config
    assert carregar_config({"ECIDADE_MCP_TAREFA": " 031 "}).prefixo_commit == "PHP8-31:"
    assert carregar_config({}).prefixo_commit == "PHP8-NN:"
    for ruim in ("31a", "-3", "PHP8-31", "1234567", "３１"):
        with pytest.raises(ErroFerramenta) as e:
            carregar_config({"ECIDADE_MCP_TAREFA": ruim})
        assert e.value.codigo == "config_invalida", ruim


def test_area_do_arquivo_pela_tabela_do_grupo():
    from servidor.areas import area_do_arquivo
    casos = {"ecidade/con2_conhist002.php": "financeiro", "ecidade/cai4_x.php": "financeiro",
             "ecidade/edu1_aluno001.php": "educacao", "ecidade/pes1_reajusteprog001.php": "pessoal",
             "ecidade/cad1_lote002.php": "tributario_patrimonial", "ecidade/sau1_x.php": "saude_demais",
             "ecidade/libs/db_stdlib.php": "nucleo", "ecidade/dbforms/db_funcoes.php": "nucleo",
             "ecidade/login.php": "nucleo", "ecidade/src/Educacao/X.php": "educacao",
             "ecidade/src/RecursosHumanos/Y.php": "pessoal", "ecidade/prot1_x.php": None,
             "ecidade/app/Http/Kernel.php": None, "ecidade/tela001.php": None}
    for rel, area in casos.items():
        assert area_do_arquivo(rel) == area, rel


def test_reivindicar_arquivo_de_outra_area(repo):
    (repo.raiz / "ecidade" / "con1_x.php").write_text("<?php")
    with pytest.raises(ErroFerramenta) as e:
        co.reivindicar_arquivo(repo, "ecidade/con1_x.php", "x", quem="ana", minha_area="educacao")
    assert e.value.codigo == "outra_area" and e.value.detalhes["area_do_arquivo"] == "financeiro"
    assert "dono" in e.value.mensagem
    r = co.reivindicar_arquivo(repo, "ecidade/con1_x.php", "x", quem="ana", minha_area="educacao",
                               combinado_com_dono=True)
    assert r["area"] == "financeiro" and r["area_do_arquivo"] == "financeiro"
    r = co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="ana")
    assert "aviso_area" in r
    with pytest.raises(ErroFerramenta):
        co.reivindicar_arquivo(repo, "ecidade/t2.php", "x", quem="ana", minha_area="inventada")


def test_area_pelo_ambiente(repo):
    from dataclasses import replace
    (repo.raiz / "ecidade" / "con1_x.php").write_text("<?php")
    with pytest.raises(ErroFerramenta) as e:
        co.reivindicar_arquivo(replace(repo, area="pessoal"), "ecidade/con1_x.php", "x", quem="ana")
    assert e.value.codigo == "outra_area"


def test_proximo_trabalho_respeita_area_e_prioriza_o_que_nao_compila(repo):
    e = repo.raiz / "ecidade"
    (e / "con1_a.php").write_text("<?php\nparse_str($q);\n")
    (e / "con1_b.php").write_text("<?php\n$c = $s{0};\n")          # nao compila no 8.5
    (e / "edu1_c.php").write_text("<?php\n$c = $s{0};\nparse_str($q);\n")
    r = co.proximo_trabalho(repo, quem="ana", minha_area="financeiro")
    assert r["padrao"]["nome"] == "chaves_offset_string"
    assert [a["arquivo"] for a in r["arquivos"]] == ["ecidade/con1_b.php"]
    assert r["arquivos"][0]["area"] == "financeiro"
    assert r["arquivos_de_outras_areas_pulados"]["educacao"] == 1
    r = co.proximo_trabalho(repo, quem="ana", minha_area="financeiro", padrao="parse_str_1_arg", reivindicar=True)
    assert [a["arquivo"] for a in r["arquivos"]] == ["ecidade/con1_a.php"]
    assert co.quadro(repo)["reivindicacoes_ativas"][0]["area"] == "financeiro"
    assert any("ISO-8859-1" in p for p in r["passos"]) and any("base-php84" in p for p in r["passos"])


@pytest.mark.parametrize("nome", ["a;rm -rf ~.php", "a$(id).php", "a`id`.php", "a'b.php", "a|b.php"])
def test_caminho_com_metacaractere_de_shell_e_recusado(repo, nome):
    (repo.raiz / "ecidade" / nome).write_text("<?php")
    with pytest.raises(ErroFerramenta) as e:
        co.reivindicar_arquivo(repo, f"ecidade/{nome}", "x", quem="ana")
    assert e.value.codigo == "caminho_invalido"


def test_quem_cooperativo_normalizado(repo):
    co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="Ana")
    r = co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem=" ana ")
    assert r["renovada"] is True
    assert co.quem_sou(repo, "  bia\x1b[31m\r\n") == "bia"


def test_reivindicar_caminho_confinado_e_existente(repo):
    with pytest.raises(ErroFerramenta) as e:
        co.reivindicar_arquivo(repo, "../x.php", "x", quem="ana")
    assert e.value.codigo == "caminho_fora_da_raiz"
    with pytest.raises(ErroFerramenta) as e:
        co.reivindicar_arquivo(repo, "ecidade/nao.php", "x", quem="ana")
    assert e.value.codigo == "caminho_inexistente"


def test_liberar_com_padrao_desconhecido(repo):
    co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="ana")
    with pytest.raises(ErroFerramenta) as e:
        co.liberar_arquivo(repo, "ecidade/t1.php", quem="ana", concluido=True, padroes_corrigidos=["inventado"])
    assert e.value.codigo == "padrao_desconhecido"


def test_quem_vem_do_env_ou_git(repo, monkeypatch):
    assert co.quem_sou(repo, None, git_runner=git_falso("Ana Dev\n")) == "Ana Dev"
    with pytest.raises(ErroFerramenta) as e:
        co.quem_sou(repo, None, git_runner=git_falso("", 1))
    assert e.value.codigo == "quem_desconhecido"
    from dataclasses import replace
    assert co.quem_sou(replace(repo, usuario="env-user"), None) == "env-user"


def test_quadro(repo):
    co.reivindicar_arquivo(repo, "ecidade/t1.php", "parse_str", quem="ana")
    q = co.quadro(repo)
    assert q["reivindicacoes_ativas"][0]["caminho"] == "ecidade/t1.php"
    assert "rodadas_recentes" in q and q["expiracao_horas"] == 4.0


def test_proximo_trabalho_pula_reivindicados_e_concluidos(repo):
    co.reivindicar_arquivo(repo, "ecidade/t0.php", "x", quem="bruno")
    co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="ana")
    co.liberar_arquivo(repo, "ecidade/t1.php", quem="ana", concluido=True, padroes_corrigidos=["parse_str_1_arg"])
    r = co.proximo_trabalho(repo, quem="ana", limite=10)
    assert r["padrao"]["nome"] == "parse_str_1_arg"
    assert [a["arquivo"] for a in r["arquivos"]] == ["ecidade/t2.php", "ecidade/t3.php", "ecidade/tela001.php"]
    assert r["arquivos"][0]["linhas"] == [2]


def test_proximo_trabalho_reivindica_o_lote(repo):
    r = co.proximo_trabalho(repo, padrao="split", quem="ana", reivindicar=True)
    assert [a["arquivo"] for a in r["arquivos"]] == ["ecidade/s.php"]
    assert r["reivindicados"] == ["ecidade/s.php"]
    assert co.quadro(repo)["reivindicacoes_ativas"][0]["quem"] == "ana"


def test_proximo_trabalho_sem_nada(repo):
    r = co.proximo_trabalho(repo, padrao="create_function", quem="ana")
    assert r["arquivos"] == [] and "nenhum" in r["mensagem"]


def test_padroes_ja_corrigidos(repo):
    co.reivindicar_arquivo(repo, "ecidade/t1.php", "x", quem="ana")
    co.liberar_arquivo(repo, "ecidade/t1.php", quem="ana", concluido=True, padroes_corrigidos=["parse_str_1_arg"])
    log = "abc123\tAna\tmigra(parse_str_1_arg): 12 telas de arrecadacao\nabd456\tBia\tmigra(split): balancetes\n"
    r = co.padroes_ja_corrigidos(repo, contar_em="ecidade", git_runner=git_falso(log))
    p = {x["nome"]: x for x in r["padroes"]}
    assert p["parse_str_1_arg"]["registrados_no_estado"] == 1
    assert p["parse_str_1_arg"]["commits"][0]["assunto"].startswith("migra(parse_str_1_arg)")
    assert p["split"]["commits"][0]["hash"] == "abd456"
    assert p["parse_str_1_arg"]["restantes_em_contar_em"] == 5  # contagem e do codigo, nao do estado
    assert p["parse_str_1_arg"]["forma_canonica"].startswith("parse_str(")


def test_padroes_ja_corrigidos_git_falha_vira_aviso(repo):
    r = co.padroes_ja_corrigidos(repo, git_runner=git_falso("", 128))
    assert any("git" in a for a in r["avisos"])


def test_arquivos_sem_dono_aparecem_e_podem_ser_escolhidos(repo):
    e = repo.raiz / "ecidade"
    (e / "con1_a.php").write_text("<?php\nparse_str($q);\n")
    (e / "pre1_x.php").write_text("<?php\nparse_str($q);\n")
    (e / "func_y.php").write_text("<?php\nparse_str($q);\n")
    r = co.proximo_trabalho(repo, quem="ana", minha_area="financeiro")
    assert r["arquivos_de_outras_areas_pulados"]["sem_area"] >= 2
    assert "minha_area='sem_area'" in r["sem_area"]
    r = co.proximo_trabalho(repo, quem="ana", minha_area="sem_area")
    achados = {a["arquivo"] for a in r["arquivos"]}
    assert {"ecidade/func_y.php", "ecidade/pre1_x.php"} <= achados and "ecidade/con1_a.php" not in achados
    assert all(a["area"] is None for a in r["arquivos"])
    assert "financeiro" in r["arquivos_de_outras_areas_pulados"]
