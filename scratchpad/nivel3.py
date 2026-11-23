#!/usr/bin/env python3
"""Nivel 3 (POST real comparando o SQL emitido) em um comando.

Uso (da raiz do repositorio):
    python3 scratchpad/nivel3.py --candidatas <prefixo> [<prefixo> ...]   # quais telas testar
    python3 scratchpad/nivel3.py <tela>                                   # testa a tela escolhida

    python3 scratchpad/nivel3.py --candidatas soc hab
    python3 scratchpad/nivel3.py soc1_visitatipo001
    python3 scratchpad/nivel3.py hab1_avaliacaopergunta001 --tabelas avaliacaopergunta,avaliacaoperguntaopcao
    python3 scratchpad/nivel3.py soc1_visitatipo001 --payload 'as13_descricao=X&incluir=Incluir'

Opcoes:
    --candidatas   lista as telas de inclusao dos prefixos, com a tabela de cada uma e uma sugestao
    --tabelas T    tabelas que a tela grava (padrao: a da classe que a tela instancia, achada no codigo).
                   Todas sao fotografadas e restauradas; informe as filhas quando a tela gravar mais de uma
    --payload P    o formulario a enviar (padrao: gerado pelo scratchpad/payload_auto.py lendo a tela)
    --sid SID      sessao autenticada (padrao: a mais recente do 7.4)

O que o teste faz (cada item era um bloco do nivel 3 no guia):
    1. confere que a tela existe (e sugere o nome certo se nao existir) e acha a tabela no codigo dela;
    2. acha a sessao, confere que ela vale (prova de fumaca) e prepara a copia que o payload_auto.py usa;
    3. liga o log de SQL (log_statement='all') e, ACONTECA O QUE ACONTECER, desliga no fim (finally);
    4. gera o payload lendo o formulario real (payload_auto.py);
    5. roda o scratchpad/escrita_post.py: fotografa as tabelas e sequencias, faz o POST no 7.4, restaura,
       faz no 8.5, restaura, e compara o SQL de escrita de NEGOCIO dos dois lados;
    6. confere, pelas ESTATISTICAS do PostgreSQL (pg_stat_user_tables), se alguma OUTRA tabela recebeu
       linha inserida/alterada/apagada durante o teste. Isso pega o que o log de SQL nao mostra: escrita
       feita por GATILHO dentro do banco -- foi o que deixou lixo na amostra da Saude (CGS). Se aparecer,
       o teste avisa com o nome da tabela, para conferir e limpar.

Vereditos (os do escrita_post.py):
    IDENTICO      o SQL de escrita de negocio foi o mesmo nos dois runtimes -> a tela grava igual
    DIVERGE       SQL diferente -> comparar campo a campo; se um campo de DADO difere, e defeito
                  (provavelmente a guarda 0 == "" faltando na classe)
    INCONCLUSIVO  o POST nao gravou nos dois -> payload recusado (campo obrigatorio, nome do botao);
                  troque de tela ou ajuste o --payload. NAO e aprovacao.

Saida: o resultado vai para o terminal e para ecidade/tmp/nivel3/<data-hora>-<tela>.txt.
Codigo de saida: 0 = IDENTICO; 1 = DIVERGE ou escrita fora das tabelas; 2 = INCONCLUSIVO ou pre-requisito.
(Um ABORTADO do escrita_post.py -- restore recusado por FK -- tambem sai com 1.)

Efeitos colaterais: GRAVA NO BANCO DE VERDADE (o POST nos dois runtimes; o escrita_post.py desfaz nas
tabelas informadas); liga e desliga o log_statement do banco inteiro; copia a sessao para /tmp/_d.bak e
a restaura no container ecidade_php74; cria ecidade/tmp/nivel3/. Nao altera codigo. O --candidatas so le.
Se o payload_auto.py nao gerar payload, sai com 2 sem gravar o arquivo de registro.

Usado em: guia docs/migrar-um-modulo.md, "Nivel 3 -- POST de verdade" / "Em um comando -- nivel3.py"
(dentro de "Passos 4b a 6c -- os portoes"), e na tabela do lote (secao C, linha "nivel 3").

Escolher a tela continua sendo sua decisao: o criterio (uma inclusao por prefixo, tabela simples, evitar
cadastros centrais com gatilhos) esta no guia, e o --candidatas o aplica.
"""
import argparse, datetime, difflib, os, re, subprocess, sys, time

# os caminhos dos scripts chamados (scratchpad/...) sao relativos a raiz: fixa o cwd nela
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ECIDADE = os.path.join(RAIZ, "ecidade")
# O escrita_post.py le portas e containers de regressao/nucleo/ambiente.py, cujo padrao e o ambiente e74 da suite
# de regressao (:8074/:8185, ecidade74_*). Este script testa a pilha da RAIZ; as variaveis exportadas valem.
for _k, _v in {"REGRESSAO_REF_URL": "http://localhost:8080", "REGRESSAO_PHP_NOVO_URL": "http://localhost:8085",
               "REGRESSAO_CONTAINER_REF": "ecidade_php74", "REGRESSAO_CONTAINER_PHP_NOVO": "ecidade_php85",
               "REGRESSAO_CONTAINER_BANCO": "ecidade_database"}.items():
    os.environ.setdefault(_k, _v)
# psql -tA (sem cabecalho, colunas separadas por |) e -c no fim: basta acrescentar o SQL
PSQL = ["docker", "exec", "-i", "ecidade_database", "psql", "-U", "postgres", "-d", "ecidade", "-tAc"]

# Cadastros centrais: muitas tabelas e gatilhos que gravam em outras (a CGS da Saude deixou lixo).
CENTRAIS = re.compile(r"cidadao|cgm|cgs", re.I)
# Tabelas de infraestrutura que mudam em qualquer requisicao (auditoria, sessao, acesso): nao sao
# escrita da tela. Mesma lista do escrita_post.py.
INFRA = re.compile(r"^(db_acount\w*|db_usuariosonline|db_logsacessa|db_menu\w*|db_sessao\w*)$", re.I)

def erro(msg):
    """Pre-requisito faltando: mensagem e codigo de saida 2 (ver o docstring)."""
    print("ERRO: " + msg, file=sys.stderr)
    sys.exit(2)

# stdin=DEVNULL: docker exec -i nao engole a entrada do terminal; saida decodificada em LATIN-1 (banco e tela)
def sh(cmd, timeout=None):
    r = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    return r.returncode, r.stdout.decode("latin-1"), r.stderr.decode("latin-1")

def tabela_da_tela(tela):
    """A tabela que a tela grava: a da primeira classe de dados que ela instancia
    (`new cl_x` ou `db_utils::getDao('x')`). None se a tela nao instancia nenhuma diretamente."""
    b = open(os.path.join(ECIDADE, tela), "rb").read()
    # a primeira ocorrencia no arquivo, de qualquer das duas formas (o mesmo grep do Passo 2 do guia)
    m = re.search(rb"getDao\(\s*['\"]([a-z0-9_]+)|new\s+cl_([a-z0-9_]+)", b, re.I)
    return (m.group(1) or m.group(2)).decode() if m else None

def candidatas(prefixos):
    """Telas de inclusao (<pref>1_...001) dos prefixos, com tabela e sugestao pelo criterio do guia."""
    _, st, _ = sh(["git", "status", "--porcelain", "--", "ecidade/"])
    # porcelain: 'XY caminho' -> l[3:] e o caminho; tira o 'ecidade/' para comparar com os nomes do disco
    alterados = {l[3:].strip()[len("ecidade/"):] for l in st.splitlines()}
    disco = sorted(os.listdir(ECIDADE))
    _, out, _ = sh(PSQL + ["select distinct tablename from pg_tables"])
    no_banco = set(out.split())
    print(f"{'tela':44} {'tabela':26} sugestao")
    for p in prefixos:
        for t in [f for f in disco if re.match(rf"^{re.escape(p)}1_.*001\.php$", f, re.I)]:
            tab = tabela_da_tela(t)
            familia = re.sub(r"\d+\.php$", "", t)          # soc1_visitatipo001.php -> soc1_visitatipo
            # o lote mexeu na familia da tela (001/002/003...) ou na classe da tabela?
            mexida = any(a.startswith(familia) for a in alterados) or \
                     (tab and f"classes/db_{tab}_classe.php" in alterados)
            if not tab:
                sug = "nao serve (nao grava direto: usa model, RPC ou abas)"
            elif tab == "criaabas":
                sug = "nao serve (conteiner de abas: o formulario esta nas abas, ver o passo 8b)"
                tab = "-"
            elif tab not in no_banco:
                sug = f"nao serve (a classe cl_{tab} nao corresponde a uma tabela do banco)"
            elif CENTRAIS.search(t) or CENTRAIS.search(tab):
                sug = "EVITAR (cadastro central: gatilhos gravam em outras tabelas)"
            elif mexida:
                sug = "RECOMENDADA (tabela simples; a familia ou a classe foi alterada pelo lote)"
            else:
                sug = "boa"
            print(f"{t:44} {tab or '-':26} {sug}")
    print("\nCriterio (guia, nivel 3): uma tela de inclusao por prefixo; prefira a RECOMENDADA.\n"
          "A tabela e a da PRIMEIRA classe que a tela instancia: se a tela gravar outra (ou mais de uma), use --tabelas.")

# Sessao autenticada mais recente do 7.4 (as que tem DB_modulo sao as logadas). O sess_?* exclui um
# arquivo "sess_" sem identificador (cookie vazio), que dava SID vazio. SID valido tem 40 caracteres.
def achar_sessao():
    _, out, _ = sh(["docker", "exec", "-i", "ecidade_php74", "sh", "-c",
                    "ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_?*) | head -1"])
    sid = out.strip().rsplit("sess_", 1)[-1]
    if len(sid) != 40:
        erro("nenhuma sessao autenticada. Entre em http://localhost:8090 (dbseller/dbseller) e rode de novo.")
    return sid

def preparar_sessao(sid):
    """Guarda a sessao em /tmp/_d.bak (de onde o payload_auto.py a restaura) e faz a prova de fumaca:
    com sessao vencida, a tela devolveria a pagina de login e o payload sairia vazio."""
    sess = f"/var/lib/php/sessions/sess_{sid}"
    sh(["docker", "exec", "-u", "root", "-i", "ecidade_php74", "sh", "-c",
        f"cp {sess} /tmp/_d.bak && chmod 666 /tmp/_d.bak"])
    _, tam, _ = sh(["curl", "-s", "-o", "/dev/null", "-w", "%{size_download}", "-b", f"ECIDADEWINDOWMAIN={sid}",
                    "http://localhost:8080/cem1_campas001.php"])
    # devolve a sessao ao estado salvo: o GET de teste pode te-la alterado
    sh(["docker", "exec", "-u", "root", "-i", "ecidade_php74", "sh", "-c",
        f"cp /tmp/_d.bak {sess}; chown www-data:www-data {sess}"])
    # tela de modulo ja verificado (cem): com sessao boa vem com milhares de bytes; vencida, poucas dezenas
    if int(tam or 0) < 1000:
        erro(f"a sessao nao vale (tela de teste com {tam} bytes). Entre em http://localhost:8090 e rode de novo.")

def escritas_por_tabela():
    """Linhas inseridas+alteradas+apagadas em cada tabela desde que o banco subiu. Conta TUDO,
    inclusive o que gatilhos gravam -- o que o log de SQL (log_statement) nao mostra."""
    _, out, _ = sh(PSQL + ["select relname, n_tup_ins + n_tup_upd + n_tup_del from pg_stat_user_tables"])
    return {l.split("|")[0]: int(l.split("|")[1]) for l in out.splitlines() if "|" in l}

def main():
    ap = argparse.ArgumentParser(description="Nivel 3 em um comando. Ver o docstring do arquivo.")
    ap.add_argument("tela", nargs="*", help="a tela (ex.: soc1_visitatipo001), ou os prefixos com --candidatas")
    ap.add_argument("--candidatas", action="store_true", help="listar as telas candidatas dos prefixos")
    ap.add_argument("--tabelas", default=None, help="tabelas que a tela grava, separadas por virgula")
    ap.add_argument("--payload", default=None, help="formulario a enviar (padrao: gerado do formulario real)")
    ap.add_argument("--sid", default=None, help="sessao autenticada")
    args = ap.parse_args()
    if args.candidatas:
        return candidatas(args.tela)
    if len(args.tela) != 1:
        sys.exit("Informe UMA tela (ou use --candidatas <prefixos>).")

    # --- 1. a tela e a tabela -------------------------------------------------------------------
    tela = args.tela[0] if args.tela[0].endswith(".php") else args.tela[0] + ".php"
    if not os.path.isfile(os.path.join(ECIDADE, tela)):
        parecidas = difflib.get_close_matches(tela, os.listdir(ECIDADE), n=3, cutoff=0.7)
        erro(f"a tela {tela} nao existe em ecidade/." + (f" Quis dizer: {', '.join(parecidas)}?" if parecidas else ""))
    tabelas = args.tabelas or tabela_da_tela(tela)
    if not tabelas:
        erro(f"{tela} nao instancia uma classe de dados diretamente; informe --tabelas ou escolha outra tela.")
    lista_tab = [t.strip() for t in tabelas.split(",") if t.strip()]
    # confere pelo nome sem schema; a contagem tem de bater com o numero de tabelas pedidas
    _, existe, _ = sh(PSQL + ["select count(*) from pg_tables where tablename in ("
                              + ",".join(f"'{t.split('.')[-1]}'" for t in lista_tab) + ")"])
    if int(existe.strip() or 0) != len(lista_tab):
        erro(f"tabela(s) {tabelas} nao encontrada(s) no banco; informe --tabelas.")

    # --- 2. sessao ------------------------------------------------------------------------------
    sid = args.sid or achar_sessao()
    preparar_sessao(sid)

    pasta = os.path.join(ECIDADE, "tmp", "nivel3")
    os.makedirs(pasta, exist_ok=True)
    arq = os.path.join(pasta, datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + tela.replace(".php", "") + ".txt")
    registro = [f"tela: {tela}", f"tabelas fotografadas/restauradas: {tabelas}"]
    print("\n".join(registro))

    # --- 3 a 6, com o log de SQL ligado so durante o teste ---------------------------------------
    # rc comeca em 2: se algo estourar antes do escrita_post.py, nao sai como aprovado.
    # O RESET do log fica no finally para valer mesmo com excecao (inclusive o timeout).
    rc = 2
    sh(PSQL + ["ALTER DATABASE ecidade SET log_statement='all'"])
    try:
        time.sleep(2)                     # o ALTER DATABASE vale para as conexoes NOVAS
        payload = args.payload
        if payload is None:
            _, payload, err = sh(["python3", "scratchpad/payload_auto.py", sid, tela], timeout=120)
            payload = payload.strip()
        registro.append(f"payload: {payload}")
        print(f"payload: {payload}\n")
        if not payload:
            print("ERRO: o payload_auto.py nao gerou payload (a tela tem formulario?). Use --payload.")
            return 2
        # foto das estatisticas ANTES: a diferenca no fim e o que o teste (ou um gatilho) escreveu
        antes = escritas_por_tabela()
        r = subprocess.run(["python3", "scratchpad/escrita_post.py", sid, tela, ",".join(lista_tab), payload],
                           capture_output=True, stdin=subprocess.DEVNULL, timeout=600)
        rc = r.returncode
        saida = (r.stdout + r.stderr).decode("latin-1")
        print(saida)
        registro.append(saida)
        time.sleep(2)                     # as estatisticas do PostgreSQL sao atualizadas logo apos o commit
        depois = escritas_por_tabela()
        # nao contam como escrita "fora": as tabelas informadas (o POST e o restore mexem nelas) e as
        # copias _n3snap_ que o escrita_post.py cria e apaga
        nomes = {t.split(".")[-1].lower() for t in lista_tab} | {f"_n3snap_{t.replace('.', '_')}" for t in lista_tab}
        fora = sorted(t for t, n in depois.items()
                      if n > antes.get(t, 0) and t.lower() not in nomes and not INFRA.match(t))
        if fora:
            msg = ("ATENCAO: durante o teste, linhas foram gravadas tambem em " + ", ".join(fora) + ".\n"
                   "  Elas NAO foram fotografadas nem restauradas (gatilho, ou a tela grava mais de uma tabela).\n"
                   "  Confira se ficou linha de teste (ex.: TESTE_N3) e apague; na proxima vez, inclua-as em --tabelas\n"
                   "  ou escolha outra tela. Se alguem estiver usando o sistema agora, pode ser escrita dele.")
            print(msg)
            registro.append(msg)
            rc = max(rc, 1)
        else:
            ok = "Nenhuma outra tabela recebeu escrita durante o teste (inclusive por gatilho)."
            print(ok)
            registro.append(ok)
    finally:
        sh(PSQL + ["ALTER DATABASE ecidade RESET log_statement"])
        print("log de SQL desligado (RESET log_statement).")
    with open(arq, "w", encoding="latin-1", errors="replace") as f:
        f.write("\n".join(registro) + "\n")
    print(f"\nRegistro: {os.path.relpath(arq, RAIZ)}")
    return rc

if __name__ == "__main__":
    sys.exit(main())
