import json
import subprocess

import pytest

from servidor.docker_exec import DockerExec
from servidor.seguranca import ErroFerramenta
from servidor.tools.validar import conferir_config_phpstan, validar_arquivo_php

NEON_PROJETO = """parameters:
    bootstrapFiles:
        - libs/db_stdlib.php
        - dbforms/db_funcoes.php
        - bootstrap.php

    fileExtensions:
        - php
"""


def test_config_phpstan_do_projeto_e_aceita(config):
    (config.raiz / "ecidade" / "phpstan.neon").write_text(NEON_PROJETO)
    conferir_config_phpstan(config)


@pytest.mark.parametrize("neon", [
    "parameters:\n    bootstrapFiles:\n        - /tmp/mal.php\n",
    "parameters:\n    bootstrapFiles:\n        - ../../fora.php\n",
    "includes:\n    - /home/alguem/x.neon\n",
    "parameters:\n    bootstrapFiles: [ok.php, /etc/x.php]\n",
    "parameters:\n    bootstrapFiles:\n        - %env.HOME%/x.php\n",
])
def test_config_phpstan_apontando_para_fora_e_recusada(config, neon):
    (config.raiz / "ecidade" / "phpstan.neon").write_text(neon)
    with pytest.raises(ErroFerramenta) as e:
        conferir_config_phpstan(config)
    assert e.value.codigo == "config_phpstan_recusada"
    item = roda(config, FakeDocker(), caminho="ecidade/tela001.php", ferramentas=["phpstan"],
                versao="alvo")["resultados"][0]
    assert item["erro"]["codigo"] == "config_phpstan_recusada"


def test_config_phpstan_caminho_do_conteiner_e_includes_do_vendor(config):
    (config.raiz / "ecidade" / "phpstan.neon").write_text(
        "includes:\n    - %rootDir%/conf/bleedingEdge.neon\nparameters:\n    bootstrapFiles:\n"
        "        - /var/www/html/bootstrap.php\n")
    conferir_config_phpstan(config)


class FakeDocker:
    """Simula `docker`: inspect por conteiner e respostas por ferramenta/conteiner."""

    def __init__(self, ativos=("ecidade74_php74", "ecidade74_php85"), respostas=None):
        self.ativos = ativos
        self.respostas = respostas or {}
        self.chamadas = []

    def __call__(self, argv, **kw):
        self.chamadas.append(argv)
        if argv[1] == "inspect":
            nome = argv[-1]
            if nome in self.ativos:
                return subprocess.CompletedProcess(argv, 0, "true\n", "")
            return subprocess.CompletedProcess(argv, 1, "", f"Error: No such object: {nome}")
        conteiner = argv[4]
        cmd = argv[9:]
        chave = (conteiner, "phpstan" if "vendor/bin/phpstan" in cmd and cmd[0] == "php" else cmd[0])
        if cmd[0] == "test":
            chave = (conteiner, "test:" + cmd[-1])
        cod, out, err = self.respostas.get(chave, (0, "No syntax errors detected", ""))
        return subprocess.CompletedProcess(argv, cod, out, err)


def roda(config, fake, **kw):
    return validar_arquivo_php(config, docker=DockerExec(config, runner=fake), **kw)


def test_lint_nas_duas_versoes(config):
    fake = FakeDocker(respostas={("ecidade74_php85", "php"): (255, "PHP Parse error: syntax error in "
                                                              "/var/www/html/tela001.php on line 2\n", "")})
    r = roda(config, fake, caminho="ecidade/tela001.php")
    por = {x["versao"]: x for x in r["resultados"]}
    assert por["7.4 (referencia)"]["ok"] is True
    assert por["8.5 (alvo)"]["ok"] is False and "line 2" in por["8.5 (alvo)"]["saida"]
    assert r["ok"] is False and "8.5" in r["resumo"]
    cmds = [c for c in fake.chamadas if c[1] == "exec"]
    assert all(c[-5:] == ["php", "-d", "display_errors=stderr", "-l", "/var/www/html/tela001.php"] for c in cmds)


def test_so_alvo(config):
    fake = FakeDocker()
    r = roda(config, fake, caminho="ecidade/tela001.php", versao="alvo")
    assert [x["conteiner"] for x in r["resultados"]] == ["ecidade74_php85"]
    assert r["ok"] is True


def test_conteiner_fora_vira_erro_no_item_sem_derrubar(config):
    fake = FakeDocker(ativos=("ecidade74_php74",))
    r = roda(config, fake, caminho="ecidade/tela001.php")
    por = {x["versao"]: x for x in r["resultados"]}
    assert por["7.4 (referencia)"]["ok"] is True
    assert por["8.5 (alvo)"]["ok"] is False
    assert por["8.5 (alvo)"]["erro"]["codigo"] == "conteiner_indisponivel"
    assert r["ok"] is False


def test_phpstan_json(config):
    saida = json.dumps({"totals": {"errors": 0, "file_errors": 2},
                        "files": {"/var/www/html/tela001.php": {"errors": 2, "messages": [
                            {"message": "Function split not found.", "line": 2, "ignorable": True},
                            {"message": "Undefined variable: $x", "line": 3, "ignorable": True}]}},
                        "errors": []})
    fake = FakeDocker(respostas={("ecidade74_php85", "phpstan"): (1, saida, "")})
    r = roda(config, fake, caminho="ecidade/tela001.php", ferramentas=["phpstan"], versao="alvo", nivel_phpstan=3)
    item = r["resultados"][0]
    assert item["ok"] is False and item["mensagens"][0] == {"linha": 2, "mensagem": "Function split not found."}
    exec_ = [c for c in fake.chamadas if c[1] == "exec" and "analyse" in c][0]
    assert "--level=3" in exec_ and "--error-format=json" in exec_


def test_phpstan_com_avisos_antes_do_json(config):
    saida = ("Deprecated: Non-canonical cast (double) is deprecated in phar:///x on line 202\n"
             "Deprecated: algo {com chaves} on line 3\n"
             + json.dumps({"totals": {"errors": 0, "file_errors": 0}, "files": {}, "errors": []}) + "\n")
    fake = FakeDocker(respostas={("ecidade74_php85", "phpstan"): (0, saida, "")})
    item = roda(config, fake, caminho="ecidade/tela001.php", ferramentas=["phpstan"], versao="alvo")["resultados"][0]
    assert item["ok"] is True and item["mensagens"] == []


def test_phpstan_sem_nivel_explica(config):
    fake = FakeDocker(respostas={("ecidade74_php85", "phpstan"): (1, "", "Note: Using configuration file x\n"
                                                                            "No rules detected\n")})
    item = roda(config, fake, caminho="ecidade/tela001.php", ferramentas=["phpstan"], versao="alvo")["resultados"][0]
    assert item["ok"] is False and "nivel_phpstan" in item["aviso"]


def test_phpstan_saida_nao_json(config):
    fake = FakeDocker(respostas={("ecidade74_php85", "phpstan"): (255, "Fatal error: memoria", "")})
    item = roda(config, fake, caminho="ecidade/tela001.php", ferramentas=["phpstan"], versao="alvo")["resultados"][0]
    assert item["ok"] is False and "memoria" in item["saida"]


def test_pint_indisponivel(config):
    fake = FakeDocker(respostas={("ecidade74_php85", "test:vendor/bin/pint"): (1, "", "")})
    item = roda(config, fake, caminho="ecidade/tela001.php", ferramentas=["pint"], versao="alvo")["resultados"][0]
    assert item["ok"] is False and item["erro"]["codigo"] == "ferramenta_indisponivel"


def test_arquivo_fora_de_ecidade(config):
    (config.raiz / "regressao" / "x.php").write_text("<?php")
    with pytest.raises(ErroFerramenta) as e:
        roda(config, FakeDocker(), caminho="regressao/x.php")
    assert e.value.codigo == "fora_do_codigo"


def test_caminho_fora_da_raiz(config):
    with pytest.raises(ErroFerramenta) as e:
        roda(config, FakeDocker(), caminho="../../etc/passwd")
    assert e.value.codigo == "caminho_fora_da_raiz"


def test_ferramenta_desconhecida(config):
    with pytest.raises(ErroFerramenta) as e:
        roda(config, FakeDocker(), caminho="ecidade/tela001.php", ferramentas=["rm"])
    assert e.value.codigo == "ferramenta_desconhecida"
