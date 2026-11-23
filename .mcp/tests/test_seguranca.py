import os
from pathlib import Path

import pytest

from servidor.config import Config, carregar_config
from servidor.seguranca import (
    ErroFerramenta,
    decodificar,
    eh_negado,
    eh_segredo,
    limitar,
    limpar_texto,
    tem_metacaractere,
    relativo,
    resolver_caminho,
    validar_regex,
)


def test_decodificar_iso_8859_1_por_padrao():
    assert decodificar("Situação débito".encode("iso-8859-1")) == "Situação débito"
    assert decodificar(b"ascii puro") == "ascii puro"
    assert decodificar("Gestão".encode("utf-8")) == "Gestão"  # arquivo novo em UTF-8 valido
    assert decodificar(b"\xff\xfe\x80") == "\xff\xfe\x80"  # latin-1 nunca falha


def test_config_padroes_do_ambiente_e74(raiz):
    c = carregar_config({"ECIDADE_MCP_RAIZ": str(raiz)})
    assert c.raiz == raiz.resolve()
    assert c.container_ref == "ecidade74_php74"
    assert c.container_alvo == "ecidade74_php85"
    assert c.container_banco == "ecidade74_database"
    assert c.expira_horas == 4.0
    assert c.arquivo_estado == raiz.resolve() / ".mcp" / "estado" / "trabalho.json"


def test_config_nomes_de_conteiner_por_env(raiz):
    c = carregar_config({
        "ECIDADE_MCP_RAIZ": str(raiz),
        "REGRESSAO_CONTAINER_REF": "outro74",
        "REGRESSAO_CONTAINER_PHP_NOVO": "outro85",
        "ECIDADE_MCP_EXPIRA_HORAS": "1.5",
    })
    assert (c.container_ref, c.container_alvo, c.expira_horas) == ("outro74", "outro85", 1.5)


def test_config_raiz_padrao_e_o_repositorio():
    c = carregar_config({})
    assert (c.raiz / ".mcp" / "servidor" / "config.py").is_file()


def test_config_env_invalida_vira_erro_estruturado(raiz):
    with pytest.raises(ErroFerramenta) as e:
        carregar_config({"ECIDADE_MCP_RAIZ": str(raiz), "ECIDADE_MCP_EXPIRA_HORAS": "abc"})
    assert e.value.codigo == "config_invalida"


def test_resolve_relativo_dentro_da_raiz(config):
    p = resolver_caminho(config.raiz, "ecidade/tela001.php")
    assert p == config.raiz / "ecidade" / "tela001.php"
    assert relativo(config.raiz, p) == "ecidade/tela001.php"


@pytest.mark.parametrize("caminho", ["../fora.txt", "ecidade/../../fora.txt", "ecidade/../ecidade/tela001.php"])
def test_bloqueia_ponto_ponto(config, caminho):
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, caminho)
    assert e.value.codigo == "caminho_fora_da_raiz"


def test_bloqueia_absoluto_fora(config, tmp_path):
    fora = tmp_path / "fora.txt"
    fora.write_text("x")
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, str(fora))
    assert e.value.codigo == "caminho_fora_da_raiz"


def test_aceita_absoluto_dentro(config):
    p = resolver_caminho(config.raiz, str(config.raiz / "ecidade" / "tela001.php"))
    assert p.name == "tela001.php"


def test_symlink_para_fora_e_bloqueado(config, tmp_path):
    fora = tmp_path / "segredo.txt"
    fora.write_text("x")
    os.symlink(fora, config.raiz / "ecidade" / "atalho.php")
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, "ecidade/atalho.php")
    assert e.value.codigo == "caminho_fora_da_raiz"


def test_diretorio_symlink_para_fora_e_bloqueado(config, tmp_path):
    d = tmp_path / "outro"
    d.mkdir()
    (d / "a.php").write_text("<?php")
    os.symlink(d, config.raiz / "ecidade" / "dir")
    with pytest.raises(ErroFerramenta):
        resolver_caminho(config.raiz, "ecidade/dir/a.php")


@pytest.mark.parametrize("caminho", [".git/config", "ecidade/.env", "ecidade/storage/oauth-private.key",
                                     "ecidade/libs/db_conn.php"])
def test_bloqueia_git_e_segredos(config, caminho):
    alvo = config.raiz / caminho
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("segredo")
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, caminho)
    assert e.value.codigo == "caminho_proibido"


def test_env_qualquer_variante_e_segredo():
    for nome in (".env", ".env.example", ".env.local", "laravel.log", "auth.json", "oauth-public.key", "a.pem"):
        assert eh_segredo(Path("ecidade") / nome), nome
    assert not eh_segredo(Path("ecidade/db_conn.php.dist"))


@pytest.mark.parametrize("caminho", [
    "ecidade/config/application.php", "ecidade/config/ecidade_config.php", "ecidade/storage/logs/laravel.log",
    "ecidade/storage/app/x.php", "ecidade/extension/log/error.log", "ecidade/tmp/relatorio.php",
    "ecidade/bootstrap/cache/config.php", "ecidade/auth.json", "ecidade/qualquer.log", "ecidade/.env.local",
])
def test_negado_por_caminho(config, caminho):
    alvo = config.raiz / caminho
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text("<?php $senha = 'x';")
    assert eh_negado(alvo.relative_to(config.raiz))
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, caminho)
    assert e.value.codigo == "caminho_proibido"


def test_config_comum_nao_e_negado(config):
    for c in ("ecidade/config/app.php", "ecidade/libs/db_stdlib.php", "ecidade/bootstrap/app.php"):
        assert not eh_negado(Path(c)), c


def test_symlink_interno_para_env_e_negado(config):
    (config.raiz / "ecidade" / ".env").write_text("DB_PASSWORD=x")
    os.symlink(config.raiz / "ecidade" / ".env", config.raiz / "ecidade" / "inocente.php")
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, "ecidade/inocente.php")
    assert e.value.codigo == "caminho_proibido"


def test_symlink_com_nome_de_segredo_para_arquivo_comum_e_negado(config):
    os.symlink(config.raiz / "ecidade" / "tela001.php", config.raiz / "ecidade" / "x.log")
    with pytest.raises(ErroFerramenta):
        resolver_caminho(config.raiz, "ecidade/x.log")


def test_limpar_texto():
    assert limpar_texto("a\r\nb\x1b[31mvermelho\x1b[0m\x07‮!", 100) == "a bvermelho!"
    assert limpar_texto("<<<<<<< x", 100) == "<<<<<<< x"
    assert len(limpar_texto("x" * 500, 80)) == 80
    assert limpar_texto(None, 10) == ""


def test_metacaracteres():
    assert not tem_metacaractere("ecidade/arr1_grupotaxa001.php")
    for ruim in ("a;rm", "a$(x)", "a`x`", "a|b", "a'b", "a\nb", "a&b", "a>b"):
        assert tem_metacaractere(ruim), ruim


def test_inexistente_e_tipo(config):
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, "ecidade/nao_existe.php")
    assert e.value.codigo == "caminho_inexistente"
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, "ecidade", tipo="arquivo")
    assert e.value.codigo == "tipo_invalido"
    assert resolver_caminho(config.raiz, "ecidade/novo.php", deve_existir=False).name == "novo.php"


@pytest.mark.parametrize("caminho", ["", "a\x00b", "x" * 2000])
def test_caminho_malformado(config, caminho):
    with pytest.raises(ErroFerramenta) as e:
        resolver_caminho(config.raiz, caminho)
    assert e.value.codigo == "caminho_invalido"


def test_regex_validada():
    assert validar_regex(r"parse_str\(").search("parse_str(")
    with pytest.raises(ErroFerramenta) as e:
        validar_regex("(")
    assert e.value.codigo == "regex_invalida"
    with pytest.raises(ErroFerramenta):
        validar_regex("a" * 500)


def test_limitar():
    assert limitar("abc", 10) == ("abc", False)
    texto, cortado = limitar("x" * 100, 10)
    assert cortado and texto.startswith("x" * 10) and "truncado" in texto


def test_erro_como_dict():
    e = ErroFerramenta("codigo_x", "mensagem", detalhe=1)
    assert e.como_dict() == {"codigo": "codigo_x", "mensagem": "mensagem", "detalhes": {"detalhe": 1}}
