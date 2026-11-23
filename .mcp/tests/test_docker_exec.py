import subprocess

import pytest

from servidor.docker_exec import DockerExec, caminho_no_conteiner, comando_ferramenta
from servidor.seguranca import ErroFerramenta


class Runner:
    """Falso subprocess.run: responde por prefixo do comando e registra as chamadas."""

    def __init__(self, respostas=None, excecao=None):
        self.chamadas = []
        self.respostas = respostas or {}
        self.excecao = excecao

    def __call__(self, argv, **kw):
        self.chamadas.append((argv, kw))
        if self.excecao:
            raise self.excecao
        chave = argv[1]
        cod, out, err = self.respostas.get(chave, (0, "", ""))
        return subprocess.CompletedProcess(argv, cod, out, err)


def test_executa_com_lista_de_argumentos_sem_shell(config):
    r = Runner({"inspect": (0, "true\n", ""), "exec": (0, "No syntax errors detected in x.php\n", "")})
    d = DockerExec(config, runner=r)
    res = d.executar(config.container_alvo, ["php", "-l", "/var/www/html/x.php"], timeout=30)
    assert res.codigo_saida == 0 and "No syntax errors" in res.stdout
    argv, kw = r.chamadas[-1]
    assert argv[:5] == ["docker", "exec", "-w", "/var/www/html", "ecidade74_php85"]
    assert argv[5:9] == ["timeout", "-k", "5", "30s"]
    assert argv[9:] == ["php", "-l", "/var/www/html/x.php"]
    assert kw.get("shell") in (None, False)
    assert kw["timeout"] > 30


def test_conteiner_inexistente_vira_erro_estruturado(config):
    r = Runner({"inspect": (1, "", "Error: No such object: ecidade74_php85\n")})
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=r).executar(config.container_alvo, ["php", "-v"], timeout=10)
    assert e.value.codigo == "conteiner_indisponivel"
    assert len(r.chamadas) == 1  # nem tentou o exec


def test_conteiner_parado(config):
    r = Runner({"inspect": (0, "false\n", "")})
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=r).executar(config.container_ref, ["php", "-v"], timeout=10)
    assert e.value.codigo == "conteiner_parado"


def test_docker_ausente(config):
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=Runner(excecao=FileNotFoundError("docker"))).executar(
            config.container_ref, ["php", "-v"], timeout=10)
    assert e.value.codigo == "docker_indisponivel"


def test_timeout(config):
    class R(Runner):
        def __call__(self, argv, **kw):
            if argv[1] == "inspect":
                return subprocess.CompletedProcess(argv, 0, "true\n", "")
            raise subprocess.TimeoutExpired(argv, kw["timeout"])
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=R()).executar(config.container_ref, ["php", "-v"], timeout=10)
    assert e.value.codigo == "tempo_esgotado"


def test_conteiner_fora_da_allowlist(config):
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=Runner()).executar("outro-projeto-postgres-1", ["php", "-v"], timeout=10)
    assert e.value.codigo == "conteiner_nao_permitido"


def test_todos_os_comandos_das_ferramentas_passam_na_allowlist(config):
    from servidor.docker_exec import FERRAMENTAS, _validar_argv
    for f in FERRAMENTAS:
        _validar_argv(comando_ferramenta(f, "/var/www/html/a.php", nivel=2), "/var/www/html")


@pytest.mark.parametrize("argv", [["sh", "-c", "rm -rf /"], ["bash"], ["php", "-r", "system('id');"],
                                  ["php", "a\x00b"], [],
                                  ["php", "-l", "/etc/passwd"], ["php", "-l", "/var/www/html/../../etc/passwd"],
                                  ["php", "-d", "auto_prepend_file=/tmp/x", "-l", "/var/www/html/a.php"],
                                  ["php", "-d", "display_errors=stderr", "-l", "/etc/passwd"],
                                  ["php", "-d", "auto_prepend_file=/tmp/x", "-d", "display_errors=stderr",
                                   "vendor/bin/phpstan", "analyse", "/var/www/html/a.php"],
                                  ["php", "-d", "memory_limit=1G", "-d", "display_errors=stderr",
                                   "vendor/bin/phpstan", "analyse", "--configuration=/tmp/x.neon",
                                   "/var/www/html/a.php"]])
def test_binario_ou_argumento_fora_da_allowlist(config, argv):
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=Runner({"inspect": (0, "true", "")})).executar(
            config.container_ref, argv, timeout=10)
    assert e.value.codigo == "comando_nao_permitido"


def test_saida_grande_e_truncada(config):
    r = Runner({"inspect": (0, "true", ""), "exec": (0, "x" * (config.max_saida + 500), "")})
    res = DockerExec(config, runner=r).executar(config.container_ref, ["php", "-v"], timeout=10)
    assert res.truncado and len(res.stdout) < config.max_saida + 200


def test_exec_125_no_such_container(config):
    r = Runner({"inspect": (0, "true", ""), "exec": (125, "", "Error response from daemon: No such container: x")})
    with pytest.raises(ErroFerramenta) as e:
        DockerExec(config, runner=r).executar(config.container_ref, ["php", "-v"], timeout=10)
    assert e.value.codigo == "conteiner_indisponivel"


def test_caminho_no_conteiner(config):
    p = config.raiz / "ecidade" / "tela001.php"
    assert caminho_no_conteiner(config, p) == "/var/www/html/tela001.php"
    with pytest.raises(ErroFerramenta) as e:
        caminho_no_conteiner(config, config.raiz / "regressao" / "x.py")
    assert e.value.codigo == "fora_do_codigo"


def test_comando_ferramenta():
    # display_errors=stderr: os conteineres tem display_errors=Off (paridade) e o motivo do erro de sintaxe so iria
    # para o log do PHP; sem isso o lint diria "Errors parsing" sem a linha nem a causa (visto ao vivo na task 6)
    assert comando_ferramenta("lint", "/var/www/html/a.php") == ["php", "-d", "display_errors=stderr", "-l",
                                                                 "/var/www/html/a.php"]
    stan = comando_ferramenta("phpstan", "/var/www/html/a.php", nivel=5)
    assert stan[:5] == ["php", "-d", "memory_limit=1G", "-d", "display_errors=stderr"]
    assert "--level=5" in stan and "--error-format=json" in stan
    assert "--level=5" not in comando_ferramenta("phpstan", "/var/www/html/a.php")
    assert comando_ferramenta("pint", "/var/www/html/a.php") == ["vendor/bin/pint", "--test", "/var/www/html/a.php"]
    with pytest.raises(ErroFerramenta):
        comando_ferramenta("rm", "/x")
