import subprocess
from pathlib import Path
from types import SimpleNamespace

from regressao.laravel import caso as mod_caso
from regressao.nucleo import git
from regressao.php import bateria as php_bateria

RAIZ = Path("/repo")


def runner(rc=0, out="", err="", chamadas=None):
    def f(cmd):
        if chamadas is not None:
            chamadas.append(cmd)
        return SimpleNamespace(returncode=rc, stdout=out, stderr=err)
    return f


def test_sujo_regressao_olha_so_a_pasta_regressao_e_fica_separado_do_repo_inteiro():
    ch: list = []
    r = git.sujo_regressao(RAIZ, runner=runner(out=" M regressao/a.py\n?? regressao/b.py\n", chamadas=ch))
    assert r == {"git_sujo_regressao": True,
                 "git_sujo_regressao_arquivos": [" M regressao/a.py", "?? regressao/b.py"]}
    assert ch[0][-4:] == ["status", "--porcelain", "--", "regressao"]
    limpo = git.sujo_regressao(RAIZ, runner=runner(out=""))
    assert limpo == {"git_sujo_regressao": False, "git_sujo_regressao_arquivos": []}


def test_sujo_regressao_limita_a_lista_e_nao_confunde_com_o_flag_do_repo():
    out = "".join(f" M regressao/f{i}.py\n" for i in range(30))
    r = git.sujo_regressao(RAIZ, runner=runner(out=out))
    assert len(r["git_sujo_regressao_arquivos"]) == git.LIMITE_ARQUIVOS
    assert "git_sujo" not in r and "git_sujo_arquivos" not in r


def test_sujo_regressao_indisponivel_quando_git_falha():
    r = git.sujo_regressao(RAIZ, runner=runner(rc=128, err="fatal: dubious ownership\n"))
    assert r["git_sujo_regressao"] == "indisponivel: fatal: dubious ownership"
    assert r["git_sujo_regressao_arquivos"] == []


def test_commit_ok_usa_safe_directory_e_c():
    ch: list = []
    assert git.commit(RAIZ, runner=runner(out="abc123\n", chamadas=ch)) == "abc123"
    assert ch[0][:6] == ["git", "-c", "safe.directory=/repo", "-C", "/repo", "rev-parse"]


def test_commit_curto_passa_short():
    ch: list = []
    git.commit(RAIZ, curto=True, runner=runner(out="abc\n", chamadas=ch))
    assert "--short" in ch[0]


def test_commit_codigo_nao_zero_e_indisponivel_com_a_1a_linha_do_stderr():
    r = git.commit(RAIZ, runner=runner(rc=128, err="fatal: not a git repository\nresto\n"))
    assert r == "indisponivel: fatal: not a git repository"


def test_commit_dubious_ownership_nao_vira_vazio():
    r = git.commit(RAIZ, runner=runner(rc=128, err="fatal: detected dubious ownership in repository at '/repo'\n"))
    assert r.startswith("indisponivel: fatal: detected dubious ownership")


def test_commit_sem_stderr_e_saida_vazia_nunca_devolve_string_vazia():
    assert git.commit(RAIZ, runner=runner(rc=1)).startswith("indisponivel: ")
    assert git.commit(RAIZ, runner=runner(rc=0, out="")).startswith("indisponivel: ")


def test_git_ausente():
    def f(cmd):
        raise FileNotFoundError("git")
    assert git.commit(RAIZ, runner=f).startswith("indisponivel: FileNotFoundError")
    assert git.sujo(RAIZ, runner=f)["git_sujo"].startswith("indisponivel: ")


def test_timeout_do_git():
    def f(cmd):
        raise subprocess.TimeoutExpired("git", 30)
    assert git.commit(RAIZ, runner=f).startswith("indisponivel: TimeoutExpired")


def test_sujo_arvore_limpa_e_suja_com_limite_de_20():
    assert git.sujo(RAIZ, runner=runner(out="")) == {"git_sujo": False, "git_sujo_arquivos": []}
    out = "".join(f" M arq{i}.py\n" for i in range(30))
    r = git.sujo(RAIZ, runner=runner(out=out))
    assert r["git_sujo"] is True and len(r["git_sujo_arquivos"]) == 20 and r["git_sujo_arquivos"][0] == " M arq0.py"


def test_sujo_com_falha_e_indisponivel():
    r = git.sujo(RAIZ, runner=runner(rc=128, err="fatal: x\n"))
    assert r == {"git_sujo": "indisponivel: fatal: x", "git_sujo_arquivos": []}


def test_caso_commit_e_a_bateria_php_usam_o_helper(monkeypatch):
    monkeypatch.setattr(git, "_roda", runner(out="deadbee\n"))
    assert mod_caso._commit() == "deadbee"
    meta = php_bateria._metadados_ambiente()
    assert meta["git_commit"] == "deadbee" and meta["git_sujo"] is True


def test_helper_real_no_repo_nao_devolve_vazio():
    r = git.commit(Path(__file__).resolve().parents[2])
    assert r and (len(r) == 40 or r.startswith("indisponivel: "))
