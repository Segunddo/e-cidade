"""Coordenacao da equipe: reivindicar/liberar arquivo, quadro, proximo lote mecanico, padroes ja corrigidos.

Nenhuma destas tools faz commit: elas devolvem a sugestao (`git add` do caminho exato, nunca `-A`).
"""
from __future__ import annotations

import re
import shlex
import subprocess
import time
from collections.abc import Callable
from typing import Any

from servidor.busca import EXTENSOES_PADRAO, _Linhas, buscar, iterar_arquivos, ler_texto
from servidor.config import Config
from servidor.estado import MAX_QUEM, Estado, mesma_pessoa
from servidor.areas import AREAS_GRUPO, SEM_AREA, area_do_arquivo, validar_area
from servidor.padroes import CATALOGO, PADROES, nome_canonico, ocorrencias, ordem_trabalho, padroes_para
from servidor.seguranca import ErroFerramenta, limpar_texto, relativo, resolver_caminho, tem_metacaractere
from servidor.tools.regressao import ler_resultado_regressao

_COMMIT_MIGRA = re.compile(r"^migra\(([a-z0-9_]+)\):")


def _estado(config: Config) -> Estado:
    return Estado(config.arquivo_estado, expira_horas=config.expira_horas)


def _git(config: Config, args: list[str], runner: Callable[..., Any]) -> subprocess.CompletedProcess | None:
    try:
        return runner(["git", "-C", str(config.raiz), *args], capture_output=True, text=True, encoding="utf-8",
                      errors="replace", timeout=20, stdin=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.SubprocessError):
        return None


def quem_sou(config: Config, quem: str | None, git_runner: Callable[..., Any] = subprocess.run) -> str:
    """Identidade COOPERATIVA (sem autenticacao: qualquer um pode dizer qualquer nome; serve para coordenar, nao
    para controlar acesso): parametro > ECIDADE_MCP_USUARIO > git config user.name (nunca o e-mail)."""
    for c in (quem, config.usuario):
        v = limpar_texto(c, MAX_QUEM)
        if v:
            return v
    r = _git(config, ["config", "--get", "user.name"], git_runner)
    if r is not None and r.returncode == 0 and limpar_texto(r.stdout, MAX_QUEM):
        return limpar_texto(r.stdout, MAX_QUEM)
    raise ErroFerramenta("quem_desconhecido",
                         "informe `quem` (seu nome), ou defina ECIDADE_MCP_USUARIO, ou `git config user.name`")


def _caminho_seguro(config: Config, caminho: str, **kw: Any) -> str:
    """Relativo, confinado e sem metacaracteres de shell (vai parar em sugestoes de comando git)."""
    rel = relativo(config.raiz, resolver_caminho(config.raiz, caminho, **kw))
    if tem_metacaractere(caminho) or tem_metacaractere(rel):
        raise ErroFerramenta("caminho_invalido", "caminho com caractere especial de shell (; & | $ ` < > ( ) aspas...)")
    return rel


def _sugestao(config: Config, acao: str, caminho: str) -> str:
    # formato do CONTRIBUINDO.md ("Commits"): `PHP8-NN: descricao curta`, NN = numero da tarefa do grupo
    return (f"git add .mcp/estado/trabalho.json && git commit -m "
            f"{shlex.quote(f'{config.prefixo_commit} {acao} {caminho} no quadro')}")


def _aviso_tarefa(config: Config) -> dict[str, str]:
    if config.tarefa:
        return {}
    return {"aviso_commit": "troque NN pelo numero da tarefa do grupo (formato `PHP8-NN: descricao curta` do "
                            "CONTRIBUINDO.md) ou defina ECIDADE_MCP_TAREFA"}


def _minha_area(config: Config, minha_area: str | None) -> str | None:
    return validar_area(minha_area or config.area)


def _aviso_outra_area(area_arq: str) -> str:
    return (f"o arquivo e da area '{area_arq}' ({AREAS_GRUPO[area_arq]['titulo']}): pela regra 5 do grupo, peca ao "
            "dono da area (ou combine com ele e passe combinado_com_dono=true)")


def reivindicar_arquivo(config: Config, caminho: str, motivo: str, quem: str | None = None,
                        horas: float | None = None, minha_area: str | None = None,
                        combinado_com_dono: bool = False) -> dict[str, Any]:
    rel = _caminho_seguro(config, caminho, tipo="arquivo")
    eu = quem_sou(config, quem)
    area_arq = area_do_arquivo(rel)
    minha = _minha_area(config, minha_area)
    if minha and area_arq and area_arq != minha and not combinado_com_dono:
        raise ErroFerramenta("outra_area", _aviso_outra_area(area_arq), area_do_arquivo=area_arq, sua_area=minha)
    r = _estado(config).reivindicar(rel, eu, motivo or "", horas, area=area_arq)
    out = {**r, "area_do_arquivo": area_arq, "sugestao_commit": _sugestao(config, "reivindica", rel),
           "lembrete": "renove chamando de novo antes de expirar; libere com liberar_arquivo ao terminar",
           **_aviso_tarefa(config)}
    if not minha:
        out["aviso_area"] = ("defina sua area (minha_area ou ECIDADE_MCP_AREA) para o MCP aplicar a regra 'cada pessoa "
                             "na sua area'")
    elif area_arq is None:
        out["aviso_area"] = "arquivo fora da tabela de areas do grupo: combine com o coordenador"
    return out


def liberar_arquivo(config: Config, caminho: str, quem: str | None = None, concluido: bool = False,
                    padroes_corrigidos: list[str] | None = None, observacao: str = "") -> dict[str, Any]:
    rel = _caminho_seguro(config, caminho, deve_existir=False)
    padroes_corrigidos = [nome_canonico(p) for p in padroes_corrigidos or []]
    for p in padroes_corrigidos:
        if p not in PADROES:
            raise ErroFerramenta("padrao_desconhecido", f"padrao {p!r}; validos: {', '.join(PADROES)}")
    eu = quem_sou(config, quem)
    r = _estado(config).liberar(rel, eu, concluido=concluido, padroes=padroes_corrigidos,
                                observacao=observacao or "")
    acao = "conclui" if concluido else "libera"
    padrao = (padroes_corrigidos or ["<padrao>"])[0]
    # formato do CONTRIBUINDO.md: `PHP8-NN: descricao curta`; o trailer deixa o MCP contar
    assunto = f"{config.prefixo_commit} corrige {padrao} em {rel}"
    dica = (f"git add -- {shlex.quote(rel)} && git commit -m {shlex.quote(assunto)} "
            f"-m {shlex.quote('Padrao-MCP: ' + padrao)}" if concluido else "")
    return {**r, "sugestao_commit": _sugestao(config, acao, rel), "commit_do_codigo": dica,
            "lembrete": "mudanca feita pelo Rector vai em commit separado da manual (regra 4 do grupo)",
            **_aviso_tarefa(config)}


def quadro(config: Config) -> dict[str, Any]:
    q = _estado(config).quadro()
    try:
        rodadas = ler_resultado_regressao(config)["rodadas"][:5]
    except ErroFerramenta:
        rodadas = []
    return {
        "reivindicacoes_ativas": q["reivindicacoes_ativas"],
        "reivindicacoes_expiradas": q["reivindicacoes_expiradas"],
        "concluidos_recentes": q["concluidos"][:30],
        "total_concluidos": len(q["concluidos"]),
        "rodadas_recentes": rodadas,
        "expiracao_horas": config.expira_horas,
        "lembrete": "o estado vale entre maquinas so depois de commit/pull de .mcp/estado/trabalho.json",
    }


def proximo_trabalho(config: Config, padrao: str | None = None, caminho: str | None = None, limite: int = 10,
                     quem: str | None = None, reivindicar: bool = False,
                     minha_area: str | None = None) -> dict[str, Any]:
    """Proximo lote: nao compila no 8.5 > quebra em execucao > silencioso (> obsoleto); so arquivos da sua area."""
    if not (1 <= limite <= 50):
        raise ErroFerramenta("parametro_invalido", "limite entre 1 e 50 arquivos")
    eu = quem_sou(config, quem)
    minha = _minha_area(config, minha_area)
    est = _estado(config)
    candidatos = padroes_para(padrao) if padrao else [
        p for p in sorted(CATALOGO, key=ordem_trabalho)
        if p.mecanico in ("sim", "semi") and p.confianca != "baixa" and p.severidade != "laravel"
        and (not p.ruidoso or p.severidade in ("quebra_8_5", "silenciosa"))]
    ativos = est.reivindicados_ativos()
    de_outros = {c for c, r in ativos.items() if not mesma_pessoa(r["quem"], eu)}
    feitos = {k: set(v) for k, v in est.concluidos_por_padrao().items()}
    # UMA varredura para todos os candidatos (arquivos de outra area nem sao lidos)
    base = resolver_caminho(config.raiz, caminho or config.dir_codigo)
    achados: dict[str, dict[str, list[int]]] = {p.nome: {} for p in candidatos}
    outras_areas: dict[str, int] = {}
    fim = time.monotonic() + config.timeout_busca_s
    truncado = False
    for arq in iterar_arquivos(config, base, EXTENSOES_PADRAO):
        if time.monotonic() > fim:
            truncado = True
            break
        rel = relativo(config.raiz, arq)
        if rel in de_outros or tem_metacaractere(rel):  # nome estranho nao entra em lote (iria para comando git)
            continue
        area_arq = area_do_arquivo(rel)
        if minha and (area_arq or SEM_AREA) != minha:
            outras_areas[area_arq or SEM_AREA] = outras_areas.get(area_arq or SEM_AREA, 0) + 1
            continue
        texto = ler_texto(arq, config.max_arquivo)
        if texto is None:
            continue
        linhas = None
        for p in candidatos:
            if len(achados[p.nome]) >= limite or rel in feitos.get(p.nome, ()) or (p.so_em and not p.so_em(rel)):
                continue
            offs = ocorrencias(p, texto)
            if offs:
                linhas = linhas or _Linhas(texto)
                achados[p.nome][rel] = sorted({linhas.linha(o) for o in offs})
        if len(achados[candidatos[0].nome]) >= limite:  # o de maior prioridade ja encheu o lote
            break
    for p in candidatos:
        por_arquivo = achados[p.nome]
        if not por_arquivo:
            continue
        arquivos = [{"arquivo": a, "area": area_do_arquivo(a), "ocorrencias": len(ls), "linhas": ls[:20],
                     "ja_e_seu": a in ativos} for a, ls in list(por_arquivo.items())[:limite]]
        out: dict[str, Any] = {
            "padrao": p.como_dict(), "arquivos": arquivos, "quem": eu, "sua_area": minha,
            "ordem": "nao compila no 8.5 > quebra em execucao > silencioso > obsoleto",
            "passos": ["reivindique (reivindicar=true ou reivindicar_arquivo)",
                       "prove ANTES: a tela/classe no 7.4 x 8.5 (rodar_regressao ou escrita.php do grupo)",
                       "mexa o MINIMO no arquivo do PR; nunca copie o arquivo inteiro da base-php84; salve em ISO-8859-1",
                       "validar_arquivo_php(versao='ambas') em cada arquivo",
                       "prove DEPOIS: a mesma comparacao 7.4 x 8.5 tem de ficar igual",
                       "defeito que ja existe no 7.4: registre e avise o dono, nao corrija",
                       "liberar_arquivo(concluido=true, padroes_corrigidos=[padrao]); commit do Rector separado do manual"],
        }
        if not minha:
            out["aviso_area"] = "sem sua area definida (minha_area ou ECIDADE_MCP_AREA) o lote pode ter arquivo de outra area"
        if outras_areas:
            out["arquivos_de_outras_areas_pulados"] = outras_areas
            if SEM_AREA in outras_areas:
                out["sem_area"] = (f"{outras_areas[SEM_AREA]} arquivo(s) sem dono na tabela do grupo (func_*, classes/, pre*...) "
                                   "ficaram de fora: use minha_area='sem_area' para pegar esse trabalho e combine com o coordenador")
            out["outras_areas"] = "achou trabalho em area de outro? so registre e avise o dono (regra do grupo)"
        if truncado:
            out["aviso"] = f"varredura parou em {config.timeout_busca_s:.0f}s (resultado parcial; restrinja `caminho`)"
        if reivindicar:
            ok, recusados = [], []
            for a in arquivos:
                try:
                    est.reivindicar(a["arquivo"], eu, p.nome, area=a["area"])
                    ok.append(a["arquivo"])
                except ErroFerramenta as e:
                    recusados.append({"arquivo": a["arquivo"], "erro": e.como_dict()})
            out["reivindicados"] = ok
            out["recusados"] = recusados
            out["sugestao_commit"] = _sugestao(config, "reivindica lote de", p.nome)
            out.update(_aviso_tarefa(config))
        return out
    return {"padrao": None, "arquivos": [], "quem": eu, "sua_area": minha,
            "arquivos_de_outras_areas_pulados": outras_areas,
            "mensagem": "nenhum arquivo pendente para os padroes pedidos (fora os reivindicados por outros, os ja "
                        "concluidos e os de outras areas)"}


def padroes_ja_corrigidos(config: Config, contar_em: str | None = None,
                          git_runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    avisos: list[str] = []
    registrados = _estado(config).concluidos_por_padrao()
    commits: dict[str, list[dict[str, str]]] = {}
    r = _git(config, ["log", "-n", "500", "-E", "--grep=^migra\\(", "--grep=^Padrao-MCP: ",
                      "--format=%h%x09%an%x09%s%x09%(trailers:key=Padrao-MCP,valueonly,separator=%x2C)"], git_runner)
    if r is None or r.returncode != 0:
        avisos.append("git log indisponivel: commits com 'Padrao-MCP: <padrao>' nao foram contados")
    else:
        for linha in r.stdout.splitlines():
            partes = linha.split("\t", 3)
            if len(partes) < 3:
                continue
            nomes = [n.strip() for n in (partes[3] if len(partes) > 3 else "").split(",") if n.strip()]
            if (m := _COMMIT_MIGRA.match(partes[2])):
                nomes.append(m.group(1))
            for n in dict.fromkeys(nome_canonico(x) for x in nomes):
                commits.setdefault(n, []).append({"hash": partes[0], "autor": partes[1], "assunto": partes[2]})
    restantes: dict[str, int] = {}
    if contar_em:
        res = buscar(config, padrao="todos", caminho=contar_em, limite=2000)
        restantes = res["totais_por_padrao"]
        if res["truncado"]:
            avisos.append(f"contagem parcial em {contar_em}: {res['motivo_truncado']}")
    padroes = []
    for p in sorted(CATALOGO, key=ordem_trabalho):
        item: dict[str, Any] = {
            "nome": p.nome, "titulo": p.titulo, "severidade": p.severidade, "correcao": p.correcao,
            "forma_canonica": p.exemplo_depois,
            "registrados_no_estado": len(registrados.get(p.nome, [])),
            "arquivos_registrados": registrados.get(p.nome, [])[:50],
            "commits": commits.get(p.nome, [])[:10],
        }
        if contar_em:
            item["restantes_em_contar_em"] = restantes.get(p.nome, 0)
        padroes.append(item)
    return {"padroes": padroes, "avisos": avisos,
            "convencao_commit": f"assunto no formato do CONTRIBUINDO.md: '{config.prefixo_commit} descricao curta' "
                                "(NN = numero da tarefa do grupo; ex.: 'PHP8-31: troca $str{i} por $str[i] em "
                                "db_stdlib.php') + linha 'Padrao-MCP: <nome>' no corpo; um padrao por commit; Rector "
                                "em commit separado do manual; so os caminhos tocados"}
