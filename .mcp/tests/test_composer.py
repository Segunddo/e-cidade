import json

import pytest

from servidor.seguranca import ErroFerramenta
from servidor.tools.composer import aceita_versao, analisar_composer


@pytest.mark.parametrize("restricao,esperado", [
    (">=7.4", True), ("^7.3|^8.0", True), ("^7.2", False), ("~7.1", False), ("~8.0", True),
    ("7.1.* || 7.2.*", False), ("^8.1", True), (">=7.1 <8.0", False), (">=7.1,<8.4", False),
    ("*", True), ("^5.3.3 || ^7.0 || ^8.0", True), (">=5.6", True), ("8.5.*", True), ("<8.5", False),
    ("^7.4 || ~8.0.0 || ~8.1.0", False), ("~8.5.0", True), (">=7.2.5", True), ("^8.2|^8.3|^8.4", True),
])
def test_aceita_php_85(restricao, esperado):
    assert aceita_versao(restricao, (8, 5, 0)) is esperado


def test_restricao_ilegivel_devolve_none():
    assert aceita_versao("dev-master as 1.0", (8, 5, 0)) is None


@pytest.fixture
def composer(config):
    e = config.raiz / "ecidade"
    (e / "composer.json").write_text(json.dumps({
        "require": {"php": ">=7.4", "laravel/framework": "^8.0", "laravel/passport": "^10.0",
                    "fzaninotto/faker": "^1.9", "guzzlehttp/guzzle": "7.5.0", "ext-pgsql": "*"},
        "require-dev": {"phpunit/phpunit": "^8.5"},
    }))
    (e / "composer.lock").write_text(json.dumps({
        "packages": [
            {"name": "laravel/framework", "version": "v8.73.2", "require": {"php": "^7.3|^8.0"}},
            {"name": "velho/pacote", "version": "1.0.0", "require": {"php": "^7.1"}},
            {"name": "sem/php", "version": "2.0.0", "require": {}},
        ],
        "packages-dev": [{"name": "phpunit/phpunit", "version": "8.5.39", "require": {"php": ">=7.2"}}],
    }))
    return config


def test_analisa_composer(composer):
    r = analisar_composer(composer)
    assert r["php_requerido"] == ">=7.4"
    assert r["laravel_framework"] == {"restricao": "^8.0", "instalado": "v8.73.2"}
    nomes = {p["nome"]: p for p in r["alertas"]}
    assert "laravel/framework" in nomes and "^13" in nomes["laravel/framework"]["sugestao"]
    assert "Laravel 12" not in json.dumps(r)
    assert "grupo Laravel" in r["dono"]
    assert r["bloqueios_conhecidos"] == []
    assert "fzaninotto/faker" in nomes and "fakerphp/faker" in nomes["fzaninotto/faker"]["sugestao"]
    assert "phpunit/phpunit" in nomes
    assert "ext-pgsql" not in nomes
    lock = r["lock"]
    assert lock["total_pacotes"] == 4
    assert [p["nome"] for p in lock["php_85_fora_da_restricao"]] == ["velho/pacote"]
    assert lock["sem_restricao_php"] == 1


def test_bloqueios_pix_e_pimaco_e_composer_latin1(config):
    e = config.raiz / "ecidade"
    texto = json.dumps({"description": "Gestão pública",
                        "require": {"php": ">=7.4", "dbseller/sdk-api-pix-bb": "^2.0", "proner/phppimaco": "1.4.5"}},
                       ensure_ascii=False)
    (e / "composer.json").write_bytes(texto.encode("latin-1"))
    r = analisar_composer(config)
    assert {b["nome"] for b in r["bloqueios_conhecidos"]} == {"dbseller/sdk-api-pix-bb", "proner/phppimaco"}
    nomes = {p["nome"]: p for p in r["alertas"]}
    assert "Guzzle 7.5.0" in nomes["dbseller/sdk-api-pix-bb"]["problema"]


def test_sem_lock(config):
    (config.raiz / "ecidade" / "composer.json").write_text('{"require": {"php": "^7.4"}}')
    r = analisar_composer(config)
    assert r["lock"] is None and "composer.lock" in r["avisos"][0]


def test_json_invalido(config):
    (config.raiz / "ecidade" / "composer.json").write_text("{nao json")
    with pytest.raises(ErroFerramenta) as e:
        analisar_composer(config)
    assert e.value.codigo == "json_invalido"


def test_caminho_confinado(config):
    with pytest.raises(ErroFerramenta) as e:
        analisar_composer(config, "../composer.json")
    assert e.value.codigo == "caminho_fora_da_raiz"
