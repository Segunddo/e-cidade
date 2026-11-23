"""Atalho regressao/bin/regressao: `ver-ultimo` escolhe a rodada certa (sem Docker, sem venv)."""
import os
import subprocess
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "regressao"


def _rodada(raiz: Path, nome: str, idade_s: int, resumo: str | None = None) -> Path:
    d = raiz / nome
    d.mkdir()
    (d / "execucao.log").write_text(f"log de {nome}\n")
    if resumo is not None:
        (d / "resumo.md").write_text(resumo)
    t = time.time() - idade_s
    os.utime(d, (t, t))
    return d


def _ver_ultimo(rodadas: Path) -> str:
    env = {**os.environ, "REGRESSAO_RODADAS": str(rodadas)}
    r = subprocess.run(["bash", str(SCRIPT), "ver-ultimo"], env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_ver_ultimo_usa_a_mais_recente_por_data_e_ignora_pastas_fora_do_padrao(tmp_path):
    # por nome, "20261118-...-pequena" viria depois de "20261117-..." e "antes74" viria por ultimo
    _rodada(tmp_path, "20261118-090000-pequena", idade_s=7200, resumo="Resultado: VELHA\n")
    _rodada(tmp_path, "20261117-230000-completa", idade_s=60, resumo="Resultado: NOVA\n")
    _rodada(tmp_path, "antes74", idade_s=0, resumo="Resultado: MANUAL\n")
    saida = _ver_ultimo(tmp_path)
    assert "20261117-230000-completa" in saida and "Resultado: NOVA" in saida


def test_ver_ultimo_mostra_a_rodada_da_trava_quando_ela_esta_viva(tmp_path):
    em_curso = _rodada(tmp_path, "20261117-100000-completa", idade_s=7200)
    _rodada(tmp_path, "20261118-100000-pequena", idade_s=0, resumo="Resultado: OUTRA\n")
    (tmp_path / ".em-andamento").write_text(f"{os.getpid()}\t{em_curso}\n")  # pid vivo: o do pytest
    saida = _ver_ultimo(tmp_path)
    assert str(em_curso) in saida and "ainda em andamento" in saida


def test_ver_ultimo_sem_rodadas(tmp_path):
    (tmp_path / "antes74").mkdir()
    assert "nenhuma rodada" in _ver_ultimo(tmp_path)
