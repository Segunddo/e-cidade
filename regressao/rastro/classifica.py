"""Classifica uma tela a partir dos rastros 7.4 (duas execucoes) e 8.5 e das respostas finais.

REGRA (do dono do projeto): divergiu no meio mas o resultado final e igual -> correto (RECONVERGENTE, so informativo);
divergiu e o resultado final difere -> defeito (CAUSAL): apontar a PRIMEIRA divergencia que nao reconverge e a cadeia de
atribuicoes que levou ao valor errado.

RUIDO: o que ja difere entre as DUAS execucoes do 7.4 (`ref` x `ref2`) varia sozinho (data, ordem, ids) e nao e culpa da migracao.
TRUNCADO: rastro cortado (teto de eventos) nunca e RECONVERGENTE nem IDENTICO: o veredito e INCONCLUSIVO.
CADEIA: segue para tras, por NOME de variavel dentro do mesmo arquivo, as atribuicoes que alimentaram a sonda causal
(`le` vem do .map.json do instrumentador). Nao e analise de fluxo de dados completa (isso e a fase 3).
"""
from dataclasses import dataclass, field
from typing import Callable

from regressao.rastro.alinha import Divergencia, alinha, alinha_completo
from regressao.rastro.evento import Evento
from regressao.rastro.executor import corpo_normalizado

PROFUNDIDADE_CADEIA = 20
# Avisos que nao mudam o comportamento (depreciacao, notice): informativos, nunca candidatos a causa.
AVISOS_INFORMATIVOS = frozenset({"deprecated", "user_deprecated", "notice", "user_notice", "strict"})


def comportamental(d: Divergencia) -> bool:
    return not (d.tipo == "w" and d.nome in AVISOS_INFORMATIVOS)


# Infraestrutura do e-Cidade/vendor: divergencias de INICIALIZACAO (ordem do autoloader, chaves novas de funcoes do PHP, objeto de
# sessao) que quase nunca explicam uma diferenca de comportamento. Sem sintoma, nao podem ser apontadas como causa.
INFRA = ("src/V3/", "src/Core/", "config/", "app.php", "FrontController.php", "definitions.php", "bootstrap.php")


def e_infra(d: Divergencia) -> bool:
    return d.arquivo.startswith(INFRA) or "vendor/" in d.arquivo


def diferenca_da_resposta(resp_ref: tuple[int, bytes], resp_alvo: tuple[int, bytes], max_linhas: int = 6) -> list[str]:
    """Primeiras linhas (normalizadas) em que a resposta do 7.4 e a do 8.5 diferem. `-` = so no 7.4, `+` = so no 8.5."""
    import difflib
    a = corpo_normalizado(resp_ref[1]).decode("latin-1").splitlines()
    b = corpo_normalizado(resp_alvo[1]).decode("latin-1").splitlines()
    saida = [f"HTTP {resp_ref[0]} (7.4) x {resp_alvo[0]} (8.5)"] if resp_ref[0] != resp_alvo[0] else []
    for l in difflib.unified_diff(a, b, lineterm="", n=0):
        if l.startswith(("---", "+++", "@@")):
            continue
        saida.append(l[:160])
        if len(saida) >= max_linhas:
            break
    return saida


@dataclass
class Resultado:
    veredito: str                                   # IDENTICO | DIVERGE-RECONVERGENTE | DIVERGE-CAUSAL | INCONCLUSIVO
    causal: Divergencia | None = None
    sintoma: Divergencia | None = None              # primeira excecao/fatal so de um lado: onde a execucao ESTOUROU
    cadeia: list = field(default_factory=list)      # Evento (do alvo), em ordem cronologica
    reconvergentes: list = field(default_factory=list)
    outras: list = field(default_factory=list)      # divergencias que nao reconvergem mas nao ligam ao sintoma (informativo)
    diff_resposta: list = field(default_factory=list)   # primeiras linhas em que a RESPOSTA difere (sem excecao a explicar)
    ruido: list = field(default_factory=list)
    truncado: bool = False
    nota: str = ""


def _reconverge(d: Divergencia, pares: list) -> bool:
    """A variavel/chamada voltou a ter o mesmo valor em algum ponto POSTERIOR do rastro?"""
    if d.motivo != "valor" or d.tipo not in ("a", "c", "r", "b"):
        return False                                # aviso, excecao, evento so de um lado: comportamento, nao valor
    for r, a, ordem in pares:
        if ordem <= d.ordem or r.arquivo != d.arquivo or r.tipo != d.tipo:
            continue
        if d.tipo == "a":
            mesmo = r.nome == d.nome
        elif d.sonda:                                   # backend de sondas: a mesma sonda
            mesmo = r.sonda == d.sonda
        else:                                           # backend Xdebug (sem sonda): a mesma chamada na mesma linha
            mesmo = (r.nome, r.linha) == (d.nome, d.linha)
        if mesmo:
            return True
    return False


def cadeia_causal(causal: Divergencia, alvo: list[Evento], le: Callable[[str, int], list[str]]) -> list[Evento]:
    """Atribuicoes (do alvo) que alimentaram a sonda causal, de tras para frente por nome de variavel."""
    ponte = [e for e in alvo if e.arquivo == causal.arquivo and e.sonda == causal.sonda and e.sonda]
    inicio = ponte[causal.ocorrencia] if causal.ocorrencia < len(ponte) else (ponte[-1] if ponte else None)
    if inicio is None:
        return []
    faltam = set(le(causal.arquivo, causal.sonda))
    cadeia: list[Evento] = []
    for e in reversed([x for x in alvo if x.seq < inicio.seq and x.arquivo == causal.arquivo]):
        if len(cadeia) >= PROFUNDIDADE_CADEIA or not faltam:
            break
        if e.tipo == "a" and e.nome in faltam:
            cadeia.append(e)
            faltam.discard(e.nome)
            faltam |= set(le(e.arquivo, e.sonda))
    return list(reversed(cadeia))


def classifica(ref: list[Evento], alvo: list[Evento], ref2: list[Evento], resp_ref: tuple[int, bytes],
               resp_alvo: tuple[int, bytes], le: Callable[[str, int], list[str]] = lambda a, s: [],
               le_linha: Callable[[str, int], list[str]] | None = None) -> Resultado:
    truncado = any(e.tipo == "T" for e in (*ref, *alvo))
    if truncado:   # nunca conclui nada: nem gasta tempo/memoria alinhando rastros que bateram no teto
        return Resultado("INCONCLUSIVO", truncado=True,
                         nota="rastro truncado (teto de eventos): nao da para concluir; a tela repete muito (laco longo)")
    divs, pares = alinha_completo(ref, alvo)
    chaves_ruido = {d.chave for d in alinha(ref, ref2)}
    ruido = [d for d in divs if d.chave in chaves_ruido]
    reais = [d for d in divs if d.chave not in chaves_ruido]
    finais_iguais = (resp_ref[0], corpo_normalizado(resp_ref[1])) == (resp_alvo[0], corpo_normalizado(resp_alvo[1]))
    reconv = [d for d in reais if _reconverge(d, pares)]
    sem_volta = [d for d in reais if d not in reconv]

    if not reais:
        if finais_iguais:
            return Resultado("IDENTICO", ruido=ruido)
        return Resultado("INCONCLUSIVO", ruido=ruido,
                         nota="a resposta difere mas o rastro e igual: a diferenca esta em codigo sem sonda")
    if finais_iguais:
        return Resultado("DIVERGE-RECONVERGENTE", reconvergentes=reais, ruido=ruido)
    candidatas = [d for d in sem_volta if comportamental(d)] or [d for d in reais if comportamental(d)] or reais
    sintoma = next((d for d in reais if d.tipo == "e"), None)
    nota = "" if sem_volta else "toda divergencia voltou a igualar; a primeira foi escolhida"
    if sintoma is not None:
        nomes = _nomes_lidos_na_linha(sintoma, ref, alvo, le, le_linha)
        # Segue os dados ATE o sintoma: a causa e a divergencia (que nao reconverge) numa variavel que alimenta a linha que estourou.
        # So conta diferenca de VALOR na mesma ocorrencia: uma atribuicao que so existe de um lado e diferenca de fluxo/contagem
        # (e as vezes de versao do Xdebug), nao um valor errado que alimentou o sintoma.
        alimentam = [d for d in candidatas if d.tipo == "a" and d.motivo == "valor" and d.arquivo == sintoma.arquivo and d.nome in nomes]
        causal = alimentam[0] if alimentam else sintoma
        cadeia = cadeia_de_nomes(nomes, alvo or ref, sintoma.arquivo, le, le_linha)
        # A chamada que lancou a excecao so aparece no 7.4 (no 8.5 ela nao chegou a retornar): e parte do sintoma, nao "outra".
        outras = [d for d in candidatas if d is not causal and d is not sintoma
                  and (d.arquivo, d.linha) != (sintoma.arquivo, sintoma.linha)]
        # Mais relevantes primeiro: no mesmo arquivo do sintoma e mais perto dele (o ruido de inicializacao vem por ultimo).
        outras.sort(key=lambda d: (d.arquivo != sintoma.arquivo, -d.ordem))
        if not alimentam:
            nota = ("a causa e o proprio sintoma: o 8.x endureceu esse erro; os dados que chegaram a ele estao na cadeia"
                    if sintoma.motivo == "aviso_x_excecao" else nota)
        return Resultado("DIVERGE-CAUSAL", causal=causal, sintoma=sintoma, cadeia=cadeia, reconvergentes=reconv,
                         ruido=ruido, outras=outras, nota=nota)
    # Sem excecao/fatal: a resposta difere "em silencio". So divergencias FORA da infraestrutura podem ser apontadas como causa.
    do_codigo = [d for d in candidatas if not e_infra(d)]
    if not do_codigo:
        return Resultado("INCONCLUSIVO", reconvergentes=reconv, ruido=ruido, outras=candidatas,
                         diff_resposta=diferenca_da_resposta(resp_ref, resp_alvo),
                         nota="a resposta difere sem excecao e as divergencias do rastro sao so de infraestrutura "
                              "(src/V3, src/Core, vendor), que nao explicam a diferenca: compare as linhas da resposta")
    causal = do_codigo[0]
    return Resultado("DIVERGE-CAUSAL", causal=causal, cadeia=cadeia_causal(causal, alvo, le), reconvergentes=reconv,
                     ruido=ruido, outras=[d for d in candidatas if d is not causal],
                     diff_resposta=diferenca_da_resposta(resp_ref, resp_alvo), nota=nota)


def _lidas(e: Evento, le: Callable[[str, int], list[str]], le_linha: Callable[[str, int], list[str]] | None) -> list[str]:
    """Variaveis lidas por um evento: pela sonda (backend de sondas) ou pela LINHA, via analise estatica (backend Xdebug)."""
    if e.sonda:
        return le(e.arquivo, e.sonda)
    return le_linha(e.arquivo, e.linha) if le_linha else []


def _nomes_lidos_na_linha(sintoma: Divergencia, ref: list[Evento], alvo: list[Evento], le: Callable[[str, int], list[str]],
                          le_linha: Callable[[str, int], list[str]] | None = None) -> set[str]:
    """Variaveis lidas na linha do sintoma: pelas sondas que existem ali (em qualquer dos dois rastros) e/ou pela analise estatica."""
    nomes: set[str] = set()
    for e in (*ref, *alvo):
        if e.sonda and e.arquivo == sintoma.arquivo and e.linha == sintoma.linha:
            nomes |= set(le(e.arquivo, e.sonda))
    if le_linha:
        nomes |= set(le_linha(sintoma.arquivo, sintoma.linha))
    return nomes


def cadeia_de_nomes(nomes: set[str], trace: list[Evento], arquivo: str, le: Callable[[str, int], list[str]],
                    le_linha: Callable[[str, int], list[str]] | None = None) -> list[Evento]:
    """Ultima atribuicao de cada variavel em `nomes` (e, transitivamente, das que ela leu), em ordem cronologica."""
    faltam = set(nomes)
    cadeia: list[Evento] = []
    for e in reversed([x for x in trace if x.arquivo == arquivo and x.tipo == "a"]):
        if len(cadeia) >= PROFUNDIDADE_CADEIA or not faltam:
            break
        if e.nome in faltam:
            cadeia.append(e)
            faltam.discard(e.nome)
            faltam |= set(_lidas(e, le, le_linha))
    return list(reversed(cadeia))
