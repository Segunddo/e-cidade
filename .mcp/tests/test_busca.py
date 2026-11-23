import os
import time

import pytest

from servidor.busca import buscar, iterar_arquivos
from servidor.seguranca import ErroFerramenta


@pytest.fixture
def repo(config):
    e = config.raiz / "ecidade"
    (e / "tela002.php").write_text("<?php\n$a = split('-', $b);\nparse_str($x, $__qs);\n")
    (e / "classes" / "db_x_classe.php").write_text("<?php\nclass cl_x {\n  function cl_x() {}\n}\n")
    (e / "latin1.php").write_bytes("<?php\n// Situa\xe7\xe3o\nparse_str($q);\n".encode("latin-1").replace(b"\\xe7", b"\xe7"))
    (e / "vendor" / "pkg").mkdir(parents=True)
    (e / "vendor" / "pkg" / "v.php").write_text("<?php parse_str($q);")
    (e / ".env").write_text("parse_str($senha);")
    (e / "js.js").write_text("parse_str($q);")
    return config


def test_padrao_nomeado(repo):
    r = buscar(repo, padrao="parse_str_1_arg")
    arquivos = sorted({o["arquivo"] for o in r["ocorrencias"]})
    assert arquivos == ["ecidade/latin1.php", "ecidade/tela001.php"]
    o = [x for x in r["ocorrencias"] if x["arquivo"] == "ecidade/tela001.php"][0]
    assert o["linha"] == 2 and o["padrao"] == "parse_str_1_arg" and "parse_str" in o["trecho"]
    assert r["totais_por_padrao"] == {"parse_str_1_arg": 2}
    assert r["truncado"] is False


def test_latin1_nao_quebra(repo):
    r = buscar(repo, padrao="parse_str_1_arg", caminho="ecidade/latin1.php")
    assert r["ocorrencias"][0]["linha"] == 3


def test_latin1_com_acentos_e_decodificado_como_iso_8859_1(repo):
    (repo.raiz / "ecidade" / "acentos.php").write_bytes(
        "<?php\n// Situação do débito: não há\nif ($x == \"\") { echo 'Atualização'; }\n"
        .encode("iso-8859-1"))
    r = buscar(repo, regex="Situa", caminho="ecidade/acentos.php")
    assert r["ocorrencias"][0]["trecho"] == "// Situação do débito: não há"
    r = buscar(repo, padrao="comparacao_vazio", caminho="ecidade/acentos.php")
    assert "Atualização" in r["ocorrencias"][0]["trecho"]


def test_pula_vendor_segredos_e_extensoes(repo):
    r = buscar(repo, padrao="parse_str_1_arg")
    nomes = {o["arquivo"] for o in r["ocorrencias"]}
    assert not any("vendor" in n or n.endswith(".env") or n.endswith(".js") for n in nomes)


def test_todos(repo):
    r = buscar(repo, padrao="todos")
    assert r["totais_por_padrao"]["split"] == 1
    assert r["totais_por_padrao"]["construtor_php4"] == 1
    assert "count_null" not in r["totais_por_padrao"]


def test_todos_com_ruidosos(repo):
    (repo.raiz / "ecidade" / "pg.php").write_text("<?php\n$n = pg_numrows($rs); $c = count($x);\n")
    assert "pg_aliases" not in buscar(repo, padrao="todos")["totais_por_padrao"]
    r = buscar(repo, padrao="todos", incluir_ruidosos=True)
    assert r["totais_por_padrao"]["pg_aliases"] == 1 and r["totais_por_padrao"]["count_null"] == 1


def test_resumo_por_severidade_e_env_fora_de_configuration(repo):
    e = repo.raiz / "ecidade"
    (e / "configuration").mkdir()
    (e / "configuration" / "database.php").write_text("<?php return ['p' => env('DB_PASSWORD', '')];\n")
    (e / "app").mkdir()
    (e / "app" / "Servico.php").write_text("<?php $u = env('PIX_URL'); Cache::put('k', 1, 10);\n")
    r = buscar(repo, padrao="laravel")
    assert {o["arquivo"] for o in r["ocorrencias"] if o["padrao"] == "env_fora_config"} == {"ecidade/app/Servico.php"}
    assert r["resumo_por_severidade"]["laravel"]["padroes"] == {"cache_put_ttl": 1, "env_fora_config": 1}
    t = buscar(repo, padrao="todos")["resumo_por_severidade"]
    assert t["quebra_8_5"]["padroes"]["split"] == 1 and t["silenciosa"]["padroes"]["construtor_php4"] == 1


def test_regex_livre(repo):
    r = buscar(repo, regex=r"\$__qs")
    assert [(o["arquivo"], o["linha"]) for o in r["ocorrencias"]] == [("ecidade/tela002.php", 3)]
    assert r["ocorrencias"][0]["padrao"] == "regex"


def test_limite_trunca(repo):
    for i in range(5):
        (repo.raiz / "ecidade" / f"m{i}.php").write_text("<?php\nparse_str($a);\nparse_str($b);\n")
    r = buscar(repo, padrao="parse_str_1_arg", limite=3)
    assert len(r["ocorrencias"]) == 3 and r["truncado"] is True and "limite" in r["motivo_truncado"]


def test_sem_padrao_nem_regex_lista_catalogo(repo):
    r = buscar(repo)
    assert any(p["nome"] == "parse_str_1_arg" for p in r["catalogo"])


def test_padrao_e_regex_juntos_e_erro(repo):
    with pytest.raises(ErroFerramenta) as e:
        buscar(repo, padrao="split", regex="x")
    assert e.value.codigo == "parametro_invalido"


def test_padrao_desconhecido(repo):
    with pytest.raises(ErroFerramenta) as e:
        buscar(repo, padrao="nao_existe")
    assert e.value.codigo == "padrao_desconhecido"


def test_caminho_confinado(repo):
    with pytest.raises(ErroFerramenta) as e:
        buscar(repo, padrao="split", caminho="../")
    assert e.value.codigo == "caminho_fora_da_raiz"


def test_symlink_para_fora_e_ignorado_na_varredura(repo, tmp_path):
    fora = tmp_path / "fora"
    fora.mkdir()
    (fora / "x.php").write_text("<?php parse_str($q);")
    os.symlink(fora / "x.php", repo.raiz / "ecidade" / "link.php")
    nomes = {o["arquivo"] for o in buscar(repo, padrao="parse_str_1_arg")["ocorrencias"]}
    assert "ecidade/link.php" not in nomes


def test_prazo_esgotado_devolve_parcial(repo):
    r = buscar(repo, padrao="parse_str_1_arg", prazo_s=0)
    assert r["truncado"] is True and "tempo" in r["motivo_truncado"]


def test_regex_nao_le_segredos_logs_nem_configs(repo):
    e = repo.raiz / "ecidade"
    for rel in ("config/application.php", "config/ecidade_config.php", "storage/logs/laravel.log",
                "storage/framework/x.php", "extension/log/error.php", "tmp/t.php", "bootstrap/cache/config.php"):
        (e / rel).parent.mkdir(parents=True, exist_ok=True)
        (e / rel).write_text("<?php $SENHA_SECRETA = 'x';\n")
    (e / "laravel.log").write_text("SENHA_SECRETA\n")
    r = buscar(repo, regex="SENHA_SECRETA", extensoes=(".php", ".log"))
    assert r["ocorrencias"] == []
    for c in ("ecidade/config/application.php", "ecidade/storage/logs/laravel.log", "ecidade/laravel.log"):
        with pytest.raises(ErroFerramenta) as ex:
            buscar(repo, regex=".", caminho=c, extensoes=(".php", ".log"))
        assert ex.value.codigo == "caminho_proibido"


def test_symlink_interno_para_env_nao_e_varrido(repo):
    os.symlink(repo.raiz / "ecidade" / ".env", repo.raiz / "ecidade" / "inocente.php")
    r = buscar(repo, regex="senha")
    assert r["ocorrencias"] == []


def test_arquivo_explicito_respeita_extensao(repo):
    (repo.raiz / "ecidade" / "dados.json").write_text('{"senha": 1}')
    with pytest.raises(ErroFerramenta) as e:
        buscar(repo, regex=".", caminho="ecidade/dados.json")
    assert e.value.codigo == "extensao_nao_permitida"


def test_regex_ponto_nao_vira_leitura_do_arquivo(repo):
    (repo.raiz / "ecidade" / "grande.php").write_text("".join(f"linha {i}\n" for i in range(500)))
    r = buscar(repo, regex=".", caminho="ecidade/grande.php", limite=2000)
    assert len(r["ocorrencias"]) == 20
    assert r["arquivos_com_linhas_omitidas"] == ["ecidade/grande.php"]


def test_regex_teto_de_bytes(repo):
    for i in range(80):
        (repo.raiz / "ecidade" / f"g{i:02}.php").write_text("".join(f"{'x' * 190} {j}\n" for j in range(30)))
    r = buscar(repo, regex=".", limite=2000)
    assert r["truncado"] and "KB" in r["motivo_truncado"]
    assert sum(len(o["trecho"]) for o in r["ocorrencias"]) <= 60_000


def test_regex_catastrofica_responde_no_prazo_e_mata_o_processo(repo):
    (repo.raiz / "ecidade" / "redos.php").write_text("a" * 40 + "!\n")
    t = time.monotonic()
    r = buscar(repo, regex="(a+)+$", caminho="ecidade/redos.php", prazo_s=2)
    assert time.monotonic() - t < 6
    assert r["truncado"] and "tempo" in r["motivo_truncado"]
    from servidor import busca as b
    assert not os.path.exists(f"/proc/{b.ULTIMO_WORKER_PID}")  # morto e colhido: nao fica CPU presa


def test_padrao_tambem_limita_linhas_por_arquivo(repo):
    (repo.raiz / "ecidade" / "muitos.php").write_text("<?php\n" + "parse_str($a);\n" * 50)
    r = buscar(repo, padrao="parse_str_1_arg", caminho="ecidade/muitos.php")
    assert len(r["ocorrencias"]) == 20 and r["totais_por_padrao"]["parse_str_1_arg"] == 50


def test_iterar_ignora_git(repo):
    (repo.raiz / ".git").mkdir()
    (repo.raiz / ".git" / "a.php").write_text("x")
    todos = [p.relative_to(repo.raiz).as_posix() for p in iterar_arquivos(repo, repo.raiz, (".php",))]
    assert not any(t.startswith(".git") for t in todos)
