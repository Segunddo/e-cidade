import json
import multiprocessing as mp
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from servidor.estado import Estado
from servidor.seguranca import ErroFerramenta

T0 = datetime(2026, 11, 17, 12, 0, 0, tzinfo=timezone.utc)


class Relogio:
    def __init__(self, t=T0):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def estado(tmp_path, relogio):
    return Estado(tmp_path / "estado" / "trabalho.json", agora=relogio, expira_horas=4)


def test_arquivo_novo_e_vazio(estado):
    q = estado.quadro()
    assert q["reivindicacoes_ativas"] == [] and q["concluidos"] == []


def test_reivindica_e_grava_json_legivel(estado):
    r = estado.reivindicar("ecidade/a.php", "ana", "parse_str")
    assert r["quem"] == "ana" and r["expira"] == "2026-11-17T16:00:00Z"
    dados = json.loads(estado.arquivo.read_text())
    assert dados["versao"] == 1
    assert dados["reivindicacoes"]["ecidade/a.php"]["quem"] == "ana"
    assert estado.arquivo.read_text().endswith("\n")


def test_outro_nao_pode_reivindicar_o_mesmo(estado):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    with pytest.raises(ErroFerramenta) as e:
        estado.reivindicar("ecidade/a.php", "bruno", "y")
    assert e.value.codigo == "ja_reivindicado"
    assert e.value.detalhes["quem"] == "ana"


def test_mesma_pessoa_renova(estado, relogio):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    relogio.t = T0 + timedelta(hours=1)
    r = estado.reivindicar("ecidade/a.php", "ana", "x", horas=2)
    assert r["expira"] == "2026-11-17T15:00:00Z" and r["renovada"] is True


def test_expira_em_4h_e_libera_para_outro(estado, relogio):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    relogio.t = T0 + timedelta(hours=4, seconds=1)
    q = estado.quadro()
    assert q["reivindicacoes_ativas"] == []
    assert q["reivindicacoes_expiradas"][0]["caminho"] == "ecidade/a.php"
    r = estado.reivindicar("ecidade/a.php", "bruno", "y")
    assert r["quem"] == "bruno"


def test_escrita_limpa_expiradas(estado, relogio):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    relogio.t = T0 + timedelta(hours=5)
    estado.reivindicar("ecidade/b.php", "bruno", "y")
    dados = json.loads(estado.arquivo.read_text())
    assert list(dados["reivindicacoes"]) == ["ecidade/b.php"]


def test_liberar_so_o_dono(estado):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    with pytest.raises(ErroFerramenta) as e:
        estado.liberar("ecidade/a.php", "bruno")
    assert e.value.codigo == "reivindicado_por_outro"
    r = estado.liberar("ecidade/a.php", "ana")
    assert r["liberado"] is True
    assert estado.quadro()["reivindicacoes_ativas"] == []


def test_liberar_sem_reivindicacao(estado):
    with pytest.raises(ErroFerramenta) as e:
        estado.liberar("ecidade/a.php", "ana")
    assert e.value.codigo == "nao_reivindicado"


def test_liberar_concluido_registra_padroes(estado, relogio):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    relogio.t = T0 + timedelta(minutes=30)
    estado.liberar("ecidade/a.php", "ana", concluido=True, padroes=["parse_str_1_arg"], observacao="ok")
    q = estado.quadro()
    assert q["concluidos"][0] == {"caminho": "ecidade/a.php", "quem": "ana", "quando": "2026-11-17T12:30:00Z",
                                  "padroes": ["parse_str_1_arg"], "observacao": "ok"}
    assert estado.concluidos_por_padrao() == {"parse_str_1_arg": ["ecidade/a.php"]}


def test_concluir_de_novo_acumula_padroes(estado):
    for p in ("parse_str_1_arg", "split"):
        estado.reivindicar("ecidade/a.php", "ana", "x")
        estado.liberar("ecidade/a.php", "ana", concluido=True, padroes=[p])
    assert estado.quadro()["concluidos"][0]["padroes"] == ["parse_str_1_arg", "split"]


def test_json_corrompido_por_conflito_do_git(estado):
    estado.arquivo.parent.mkdir(parents=True, exist_ok=True)
    estado.arquivo.write_text("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> outro\n")
    with pytest.raises(ErroFerramenta) as e:
        estado.quadro()
    assert e.value.codigo == "estado_corrompido"
    assert "conflito" in e.value.mensagem


def test_motivo_com_marca_de_conflito_nao_corrompe(estado):
    estado.reivindicar("ecidade/a.php", "ana", "<<<<<<< x")
    estado.reivindicar("ecidade/b.php", "ana", "=======")
    q = estado.quadro()
    assert [r["motivo"] for r in q["reivindicacoes_ativas"]] == ["<<<<<<< x", "======="]


def test_texto_livre_e_sanitizado(estado):
    r = estado.reivindicar("ecidade/a.php", "  ana\r\n\x1b[31m ", "m\x1b[2J\x07otivo\r\nlinha2" + "x" * 500)
    assert r["quem"] == "ana"
    assert r["motivo"].startswith("motivo linha2") and len(r["motivo"]) == 200
    estado.liberar("ecidade/a.php", "ana", concluido=True, observacao="ok\x1b]0;titulo\x07‮fim")
    assert estado.quadro()["concluidos"][0]["observacao"] == "okfim"


def test_quem_vazio_depois_de_limpar(estado):
    with pytest.raises(ErroFerramenta) as e:
        estado.reivindicar("ecidade/a.php", "\x1b[0m \r\n", "x")
    assert e.value.codigo == "quem_desconhecido"


def test_quem_normalizado_na_comparacao(estado):
    estado.reivindicar("ecidade/a.php", "Ana Souza", "x")
    r = estado.reivindicar("ecidade/a.php", "  ana   souza ", "x")
    assert r["renovada"] is True
    assert estado.liberar("ecidade/a.php", "ANA SOUZA")["liberado"] is True


@pytest.mark.parametrize("conteudo", [
    '[]', '{"versao": 1, "reivindicacoes": []}', '{"versao": 1, "reivindicacoes": {"a": "x"}}',
    '{"versao": 1, "reivindicacoes": {"a": {"quem": 1, "expira": "x"}}}',
    '{"versao": 1, "concluidos": {"a": {"quem": "x", "padroes": [1]}}}',
])
def test_forma_invalida_vira_estado_corrompido(estado, conteudo):
    estado.arquivo.parent.mkdir(parents=True, exist_ok=True)
    estado.arquivo.write_text(conteudo)
    with pytest.raises(ErroFerramenta) as e:
        estado.quadro()
    assert e.value.codigo == "estado_corrompido"
    with pytest.raises(ErroFerramenta) as e:
        estado.reivindicar("ecidade/z.php", "ana", "x")
    assert e.value.codigo == "estado_corrompido"


@pytest.mark.parametrize("onde,chave", [("reivindicacoes", "ecidade/a.php"), ("raiz", "reivindicacoes")])
def test_chave_duplicada_vira_estado_corrompido_estruturado(estado, onde, chave):
    """Um merge do git pode deixar a mesma chave duas vezes; o json padrao ficaria com a ULTIMA, calado."""
    r = '{"quem": "ana", "motivo": "", "desde": "2026-11-17T12:00:00Z", "expira": "2026-11-17T16:00:00Z"}'
    if onde == "raiz":
        texto = '{"versao": 1, "reivindicacoes": {}, "concluidos": {}, "reivindicacoes": {}}'
    else:
        texto = ('{"versao": 1, "concluidos": {}, "reivindicacoes": {"ecidade/a.php": ' + r
                 + ', "ecidade/a.php": ' + r.replace("ana", "bia") + '}}')
    estado.arquivo.parent.mkdir(parents=True, exist_ok=True)
    estado.arquivo.write_text(texto)
    for op in (estado.quadro, lambda: estado.reivindicar("ecidade/b.php", "ana", "x")):
        with pytest.raises(ErroFerramenta) as e:
            op()
        assert e.value.codigo == "estado_corrompido"
        assert e.value.detalhes["chave_duplicada"] == chave and "duplicada" in e.value.mensagem
    assert estado.arquivo.read_text() == texto  # nada foi sobrescrito


def test_arquivo_gravado_fica_com_permissao_0644(estado):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    assert estado.arquivo.stat().st_mode & 0o777 == 0o644


def test_escrita_atomica_nao_deixa_temporarios(estado):
    for i in range(5):
        estado.reivindicar(f"ecidade/{i}.php", "ana", "x")
    sobras = [p.name for p in estado.arquivo.parent.iterdir() if p.name.endswith(".tmp")]
    assert sobras == []


def test_falha_na_escrita_preserva_o_arquivo_anterior(estado, monkeypatch):
    estado.reivindicar("ecidade/a.php", "ana", "x")
    antes = estado.arquivo.read_text()

    def explode(*a, **k):
        raise OSError("disco cheio")
    monkeypatch.setattr(os, "replace", explode)
    with pytest.raises(OSError):
        estado.reivindicar("ecidade/b.php", "ana", "x")
    assert estado.arquivo.read_text() == antes
    assert [p for p in estado.arquivo.parent.iterdir() if p.name.endswith(".tmp")] == []


def test_horas_invalidas(estado):
    with pytest.raises(ErroFerramenta) as e:
        estado.reivindicar("ecidade/a.php", "ana", "x", horas=0)
    assert e.value.codigo == "parametro_invalido"


# ---- corrida com 2 processos de verdade ----

def _trabalhador(arquivo: str, quem: str, caminhos: list[str], fila) -> None:
    est = Estado(Path(arquivo), expira_horas=4)
    ganhos = []
    for c in caminhos:
        try:
            est.reivindicar(c, quem, "corrida")
            ganhos.append(c)
        except ErroFerramenta as e:
            assert e.codigo == "ja_reivindicado", e.codigo
    fila.put((quem, ganhos))


def _corre(arquivo, tarefas):
    ctx = mp.get_context("spawn")
    fila = ctx.Queue()
    procs = [ctx.Process(target=_trabalhador, args=(str(arquivo), q, cs, fila)) for q, cs in tarefas]
    for p in procs:
        p.start()
    res = dict(fila.get(timeout=120) for _ in procs)
    for p in procs:
        p.join(timeout=60)
        assert p.exitcode == 0
    return res


def test_corrida_dois_processos_arquivos_distintos_nao_perde_nada(tmp_path):
    arq = tmp_path / "trabalho.json"
    a = [f"ecidade/a{i}.php" for i in range(40)]
    b = [f"ecidade/b{i}.php" for i in range(40)]
    res = _corre(arq, [("ana", a), ("bruno", b)])
    dados = json.loads(arq.read_text())
    assert len(res["ana"]) == 40 and len(res["bruno"]) == 40
    assert set(dados["reivindicacoes"]) == set(a) | set(b)


def test_corrida_dois_processos_mesmo_arquivo_um_vencedor(tmp_path):
    arq = tmp_path / "trabalho.json"
    comuns = [f"ecidade/c{i}.php" for i in range(40)]
    res = _corre(arq, [("ana", comuns), ("bruno", list(reversed(comuns)))])
    dados = json.loads(arq.read_text())
    assert set(res["ana"]).isdisjoint(res["bruno"])
    assert set(res["ana"]) | set(res["bruno"]) == set(comuns)
    for c in comuns:
        dono = dados["reivindicacoes"][c]["quem"]
        assert c in res[dono]
