"""O laboratorio Laravel 12 (regressao/lab/docker-compose.lar12.yml) e o mesmo runtime do PHP 8.5 do e74, so com
outro codigo montado: mesma imagem, mesmos volumes, mesmo ini de paridade; porta/container do ambiente."""
from pathlib import Path

import yaml

LAB = Path(__file__).resolve().parents[1] / "lab"


def _servicos(nome):
    return yaml.safe_load((LAB / nome).read_text(encoding="utf-8"))


def test_laboratorio_e_o_runtime_do_php85_do_e74_com_outro_codigo():
    e74 = _servicos("docker-compose.e74.yml")
    lab = _servicos("docker-compose.lar12.yml")
    php85 = e74["services"]["ecidade74_php85"]
    svc = lab["services"]["ecidade74_lar12"]
    assert lab["name"] != e74["name"]                 # projeto proprio: down do lab nao derruba o e74
    assert svc["container_name"] == "ecidade74_lar12"
    assert svc["ports"] == ["127.0.0.1:8187:80"]
    assert svc["pull_policy"] == "never" and "build" not in svc
    assert svc["image"] == "${LAR12_IMAGEM:-ecidade74-php85:latest}"
    assert php85["image"].endswith("ecidade74-php85:latest}")
    assert svc["environment"]["DB_HOST"] == "ecidade74_database"
    vols = svc["volumes"]
    assert vols[0] == "${LAR12_CODIGO:-../../ecidade}:/var/www/html/"
    paridade = [v for v in php85["volumes"] if "paridade" in v]
    assert paridade and paridade[0] in vols           # mesmo ini de paridade do php85
    assert "e74_sessions:/var/lib/php/sessions" in vols and "e74_tmp:/tmp" in vols
    assert lab["volumes"]["e74_sessions"] == {"external": True} and lab["volumes"]["e74_tmp"] == {"external": True}
    assert e74["volumes"]["sessions"]["name"] == "e74_sessions" and e74["volumes"]["tmp"]["name"] == "e74_tmp"
    assert lab["networks"]["e74"] == {"external": True, "name": e74["networks"]["ecidade74"]["name"]}


def test_portas_do_ambiente_so_no_localhost():
    """Login de teste conhecido (dbseller/dbseller): as portas nao podem aparecer na rede local."""
    portas = {nome: svc.get("ports", [])
              for arq in ("docker-compose.e74.yml", "docker-compose.lar12.yml")
              for nome, svc in _servicos(arq)["services"].items()}
    assert portas == {"ecidade74_database": [], "ecidade74_php74": ["127.0.0.1:8074:80"],
                      "ecidade74_php85": ["127.0.0.1:8185:80"], "ecidade74_proxy": ["127.0.0.1:8190:80"],
                      "ecidade74_lar12": ["127.0.0.1:8187:80"]}
