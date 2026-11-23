"""Coordenacao da equipe: `.mcp/estado/trabalho.json`, versionado no Git.

Formato (chaves ordenadas, um item por caminho, para o merge do Git ser simples):

    {"versao": 1,
     "reivindicacoes": {"ecidade/x.php": {"quem", "motivo", "desde", "expira"}},
     "concluidos":     {"ecidade/x.php": {"quem", "quando", "padroes": [...], "observacao"}}}

Escrita: trava de arquivo (`flock` em trabalho.json.lock) + ler-modificar-gravar + arquivo temporario no
mesmo diretorio + fsync + `os.replace` (atomico). Reivindicacao expira (padrao 4 h); expiradas sao removidas
na proxima escrita e ignoradas na leitura.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from servidor.seguranca import ErroFerramenta, limpar_texto

VERSAO = 1
ESPERA_TRAVA_S = 15.0


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _de_iso(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


_CONFLITO = re.compile(r"^(<{7}|={7}|>{7})(\s|$)", re.M)
MAX_QUEM, MAX_MOTIVO, MAX_OBSERVACAO = 80, 200, 500


def mesma_pessoa(a: str, b: str) -> bool:
    """Identidade COOPERATIVA (sem autenticacao): compara nomes sem diferenca de caixa/espacos."""
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def _validar_forma(dados: Any, nome: str) -> None:
    def ruim(msg: str) -> ErroFerramenta:
        return ErroFerramenta("estado_corrompido", f"{nome}: {msg}; corrija o arquivo (veja .mcp/estado/README.md)")
    if not isinstance(dados, dict) or dados.get("versao") != VERSAO:
        raise ruim("versao desconhecida ou formato invalido")
    for chave in ("reivindicacoes", "concluidos"):
        dados.setdefault(chave, {})
        if not isinstance(dados[chave], dict):
            raise ruim(f"'{chave}' precisa ser objeto")
    for c, r in dados["reivindicacoes"].items():
        if not isinstance(r, dict) or not all(isinstance(r.get(k), str) for k in ("quem", "expira")):
            raise ruim(f"reivindicacao de {c[:100]!r} sem 'quem'/'expira' texto")
        if not isinstance(r.get("area", ""), str):
            raise ruim(f"reivindicacao de {c[:100]!r} com 'area' que nao e texto")
    for c, v in dados["concluidos"].items():
        if (not isinstance(v, dict) or not isinstance(v.get("quem"), str)
                or not isinstance(v.get("padroes", []), list)
                or not all(isinstance(p, str) for p in v.get("padroes", []))):
            raise ruim(f"concluido de {c[:100]!r} com forma invalida")


class _ChaveDuplicada(ValueError):
    def __init__(self, chave: str):
        super().__init__(chave)
        self.chave = chave


def _sem_duplicadas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    """object_pairs_hook: um merge do git pode repetir a chave de um caminho; o json padrao ficaria calado com a
    ULTIMA e perderia a outra reivindicacao."""
    dados: dict[str, Any] = {}
    for k, v in pares:
        if k in dados:
            raise _ChaveDuplicada(k)
        dados[k] = v
    return dados


def _quem(quem: str) -> str:
    q = limpar_texto(quem, MAX_QUEM)
    if not q:
        raise ErroFerramenta("quem_desconhecido", "informe quem esta trabalhando (nome nao vazio)")
    return q


class Estado:
    def __init__(self, arquivo: Path, *, agora: Callable[[], datetime] = _agora, expira_horas: float = 4.0):
        self.arquivo = Path(arquivo)
        self.agora = agora
        self.expira_horas = expira_horas

    # ---------- infraestrutura ----------

    @property
    def _trava(self) -> Path:
        return self.arquivo.with_name(self.arquivo.name + ".lock")

    @contextmanager
    def _travado(self):
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self._trava, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            limite = time.monotonic() + ESPERA_TRAVA_S
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() > limite:
                        raise ErroFerramenta("estado_ocupado",
                                             "outro processo esta gravando o estado; tente de novo") from None
                    time.sleep(0.02)
            yield
        finally:
            os.close(fd)  # fechar solta o flock

    def _ler(self) -> dict[str, Any]:
        try:
            texto = self.arquivo.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"versao": VERSAO, "reivindicacoes": {}, "concluidos": {}}
        if _CONFLITO.search(texto):  # so no INICIO de linha: um motivo "<<<<<<< x" dentro do JSON nao conta
            raise ErroFerramenta("estado_corrompido",
                                 f"{self.arquivo.name} tem marcas de conflito do git: resolva o conflito "
                                 "(mantenha as entradas dos dois lados) e faca commit so desse arquivo")
        try:
            dados = json.loads(texto, object_pairs_hook=_sem_duplicadas)
        except json.JSONDecodeError as e:
            raise ErroFerramenta("estado_corrompido", f"{self.arquivo.name} nao e JSON valido: {e}") from None
        except _ChaveDuplicada as e:
            raise ErroFerramenta("estado_corrompido",
                                 f"{self.arquivo.name} tem a chave {e.chave[:100]!r} duplicada (sobra de merge do git): "
                                 "deixe uma entrada so por caminho e faca commit so desse arquivo",
                                 chave_duplicada=e.chave[:200]) from None
        _validar_forma(dados, self.arquivo.name)
        return dados

    def _gravar(self, dados: dict[str, Any]) -> None:
        texto = json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        fd, tmp = tempfile.mkstemp(dir=self.arquivo.parent, prefix=".trabalho.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(texto)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp, 0o644)  # mkstemp cria 0600; o arquivo versionado fica legivel como os outros
            os.replace(tmp, self.arquivo)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise
        try:
            dfd = os.open(self.arquivo.parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            pass

    def _expirada(self, r: dict[str, Any], agora: datetime) -> bool:
        try:
            return _de_iso(r["expira"]) <= agora
        except (KeyError, ValueError):
            return True

    def _atualizar(self, fn: Callable[[dict[str, Any], datetime], Any]) -> Any:
        with self._travado():
            dados = self._ler()
            agora = self.agora()
            dados["reivindicacoes"] = {c: r for c, r in dados["reivindicacoes"].items()
                                       if not self._expirada(r, agora)}
            resultado = fn(dados, agora)
            self._gravar(dados)
            return resultado

    # ---------- operacoes ----------

    def reivindicar(self, caminho: str, quem: str, motivo: str, horas: float | None = None,
                    area: str | None = None) -> dict[str, Any]:
        horas = self.expira_horas if horas is None else horas
        if not (0 < horas <= 72):
            raise ErroFerramenta("parametro_invalido", "horas precisa estar entre 0 e 72")
        quem, motivo = _quem(quem), limpar_texto(motivo, MAX_MOTIVO)

        def fn(dados, agora):
            atual = dados["reivindicacoes"].get(caminho)
            if atual and not mesma_pessoa(atual["quem"], quem):
                raise ErroFerramenta("ja_reivindicado", f"{caminho} esta com {atual['quem']} ate {atual['expira']}",
                                     quem=atual["quem"], expira=atual["expira"], motivo=atual.get("motivo", ""))
            novo = {"quem": quem, "motivo": motivo, "desde": atual["desde"] if atual else _iso(agora),
                    "expira": _iso(agora + timedelta(hours=horas))}
            if area:
                novo["area"] = limpar_texto(area, 40)
            dados["reivindicacoes"][caminho] = novo
            return {"caminho": caminho, **novo, "renovada": bool(atual)}

        return self._atualizar(fn)

    def liberar(self, caminho: str, quem: str, *, concluido: bool = False, padroes: list[str] | None = None,
                observacao: str = "") -> dict[str, Any]:
        quem, observacao = _quem(quem), limpar_texto(observacao, MAX_OBSERVACAO)

        def fn(dados, agora):
            atual = dados["reivindicacoes"].get(caminho)
            if atual is None:
                raise ErroFerramenta("nao_reivindicado", f"{caminho} nao esta reivindicado (ou ja expirou)")
            if not mesma_pessoa(atual["quem"], quem):
                raise ErroFerramenta("reivindicado_por_outro", f"{caminho} esta com {atual['quem']}",
                                     quem=atual["quem"], expira=atual["expira"])
            del dados["reivindicacoes"][caminho]
            if concluido:
                antes = dados["concluidos"].get(caminho, {})
                todos = list(dict.fromkeys([*antes.get("padroes", []), *(padroes or [])]))
                dados["concluidos"][caminho] = {"quem": quem, "quando": _iso(agora), "padroes": todos,
                                                "observacao": observacao}
            return {"caminho": caminho, "liberado": True, "concluido": concluido}

        return self._atualizar(fn)

    def quadro(self) -> dict[str, Any]:
        dados = self._ler()
        agora = self.agora()
        ativas, expiradas = [], []
        for c, r in sorted(dados["reivindicacoes"].items()):
            (expiradas if self._expirada(r, agora) else ativas).append({"caminho": c, **r})
        concluidos = sorted(({"caminho": c, **v} for c, v in dados["concluidos"].items()),
                            key=lambda x: x.get("quando", ""), reverse=True)
        return {"reivindicacoes_ativas": ativas, "reivindicacoes_expiradas": expiradas, "concluidos": concluidos}

    def reivindicados_ativos(self) -> dict[str, dict[str, Any]]:
        return {i["caminho"]: i for i in self.quadro()["reivindicacoes_ativas"]}

    def concluidos_por_padrao(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for c, v in sorted(self._ler()["concluidos"].items()):
            for p in v.get("padroes", []):
                out.setdefault(p, []).append(c)
        return out
