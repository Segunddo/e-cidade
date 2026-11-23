import json
import subprocess
import sys
import time

from servidor import executor
from servidor.docker_exec import DockerExec
from servidor.tools.regressao import ler_resultado_regressao, rodar_regressao


def _python_falso(raiz, corpo="echo rodou \"$@\"; exit 3"):
    py = raiz / "regressao" / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("#!/bin/sh\n" + corpo + "\n")
    py.chmod(0o755)
    return py


def _meta(tmp_path, raiz, argv):
    m = tmp_path / "meta.json"
    m.write_text(json.dumps({"raiz": str(raiz), "argv": argv}))
    return m


def test_executor_roda_e_grava_fim(config, tmp_path):
    py = _python_falso(config.raiz)
    m = _meta(tmp_path, config.raiz, [str(py), "-m", "regressao.php.bateria", "--saida", "x"])
    assert executor.main(str(m)) == 3
    assert json.loads((tmp_path / "fim.json").read_text())["codigo_saida"] == 3


def test_executor_recusa_argv_estranho(config, tmp_path):
    m = _meta(tmp_path, config.raiz, ["/bin/sh", "-c", "touch /tmp/pwned"])
    assert executor.main(str(m)) == 126
    m = _meta(tmp_path, config.raiz, [str(config.raiz / "regressao/.venv/bin/python"), "-m", "os", "x"])
    assert executor.main(str(m)) == 126


def test_rodada_destacada_de_verdade(config):
    _python_falso(config.raiz, "echo rodou \"$@\"; sleep 1; exit 1")
    ok = lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "true\n", "")  # noqa: E731
    r = rodar_regressao(config, bateria="php", prefixo=["^arr1_"], docker=DockerExec(config, runner=ok))
    limite = time.time() + 30
    while time.time() < limite:
        st = ler_resultado_regressao(config, id=r["id"])
        if st["status"] == "concluida":
            break
        assert st["status"] == "em_andamento"
        time.sleep(0.2)
    assert st["status"] == "concluida" and st["codigo_saida"] == 1
    assert "rodou -m regressao.php.bateria" in st["log_final"]
    assert "--prefixo=^arr1_" in st["log_final"]
