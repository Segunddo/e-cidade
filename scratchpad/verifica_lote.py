#!/usr/bin/env python3
"""Roda TODAS as verificacoes automaticas de um lote e junta o resultado num relatorio so.

Uso (da raiz do repositorio):
    python3 scratchpad/verifica_lote.py <nome-do-lote> <prefixo> [<prefixo> ...] [opcoes]

    python3 scratchpad/verifica_lote.py as soc hab
    python3 scratchpad/verifica_lote.py as soc hab --so 6b,6c        # so alguns passos
    python3 scratchpad/verifica_lote.py as soc hab --continuar       # nao para no primeiro que falhar
    python3 scratchpad/verifica_lote.py as soc hab --base origin/base-php84   # lote ja commitado
    python3 scratchpad/verifica_lote.py fim-assist --tudo            # TUDO: a bateria completa do fim da area
    python3 scratchpad/verifica_lote.py teste --tudo --amostra 40    # TUDO, mas com amostra (teste rapido)

Opcoes:
    --so PASSOS   lista separada por virgula, entre: 4b,5,5b,6,6b,6c,7 (padrao: todos)
    --continuar   segue para os passos seguintes mesmo depois de uma FALHA
    --base REF    referencia do git contra a qual o lote e medido no 4b e no 5 (padrao: HEAD,
                  isto e, as alteracoes ainda nao commitadas; com --tudo o padrao e master). Depois
                  do commit do lote, passe o commit anterior a ele, ex. --base origin/base-php84
    --sid SID     sessao autenticada a usar na bateria (padrao: a mais recente do 7.4)
    --tudo        em vez de prefixos, verifica TUDO: o universo sao os arquivos que a migracao alterou
                  (diff contra o master, o codigo antes da migracao) e as classes entre eles; a bateria roda
                  em todas as telas que o proxy manda ao 8.5 (location + map). E a bateria completa do fim da
                  area (guia, fluxo D): ~3 h. Use --amostra para testar antes.
    --amostra N   limita cada lista a N itens espalhados (teste rapido; NAO vale como bateria completa)
    --telas A,B   a bateria roda so nestas telas (ex.: reconferir uma divergencia)
    --conhecidas F lista de divergencias JA caracterizadas: so as que ficarem FORA dela contam como possivel
                  regressao e sao diagnosticadas (e o criterio do fim da area). Aceita o
                  docs/divergencias-conhecidas.md (padrao, se existir; linhas "Corrigida" nao entram) ou
                  qualquer lista com o nome da tela no 1o campo, como o 7_divergentes.txt de uma bateria anterior

Pre-requisitos:
    - os containers ecidade_database, ecidade_php74 e ecidade_php85 no ar;
    - o universo de cada prefixo ja gerado: python3 scratchpad/enumera.py <prefixo>
      (o script le ecidade/tmp/<prefixo>_universo.txt);
    - o Rector ja aplicado (passo 4). Este script NAO altera codigo nem o banco.

O que ele roda, nesta ordem (os detalhes de cada passo estao em docs/migrar-um-modulo.md):
    4b  funcoes novas no diff existem no PHP 7.4?
    5   php -l no universo, nos dois runtimes
    5b  cada arquivo com extends/implements carrega nos dois (assinatura incompativel, LSP)
    6   instanciar as classes: o estado inicial e igual nos dois?
    6b  caminho de escrita: atualizacampos() le o formulario igual nos dois?
    6c  forma negada `$this->x != ""`: decide igual nos dois? (so as classes do lote contam)
    7   bateria: cada tela dos prefixos responde byte a byte igual nos dois?
        e, para cada tela que divergir, um DIAGNOSTICO automatico: pede a tela de novo aos dois runtimes
        com os logs limpos, junta o erro fatal do PHP (arquivo e linha), os erros de SQL do PostgreSQL e,
        se os dois responderem 200, o trecho onde as paginas comecam a diferir; e classifica pela tabela
        de decisao do guia (regressao, pre-existente, quebra nos dois, silenciosa, nao reproduziu).

Ficam DE FORA de proposito: o passo 4 (Rector: exige conferir regra nova antes de aplicar),
o nivel 3 (POST real: grava no banco e exige escolher a tela), os passos 8/8b (mudam o proxy)
e qualquer correcao (guarda_ciclo, negada_corrige: exigem olhar caso a caso).

Saida: uma pasta por execucao, ecidade/tmp/verif/<lote>-<AAAAMMDD-HHMM>/, com
    RELATORIO.md   uma pagina: o veredito, uma linha de numeros por passo e o que corrigir.
                   E o UNICO arquivo que precisa ser lido.
    DETALHES.md    tudo: para cada passo, o criterio, os numeros e as linhas que importam, o
                   diagnostico de cada tela divergente e os artefatos conhecidos.
    <passo>_*.txt  saida bruta de cada passo
A pasta fica dentro de ecidade/ (montada nos containers como /var/www/html), entao os
containers leem e escrevem nela sem `docker cp`. ecidade/tmp/ e ignorada pelo git.

Usado em: passos 4b a 7 de cada lote (guia, "Verificar o lote de uma vez") e, com --tudo, na bateria completa
do fim da area (guia, fluxo D). Metodo geral: cada passo roda um harness de scratchpad/ (porclasse.sh,
carrega_arquivo.php, instancia_classes.php, escrita.php, negada*.py/php, cmp.py) nos DOIS containers sobre a
mesma lista, compara as saidas e devolve um Resultado; o relatorio junta os Resultados.

Codigo de saida: 0 = tudo OK; 1 = algum passo com FALHA ou INVESTIGAR; 2 = pre-requisito faltando.

Situacoes de cada passo:
    OK          o criterio do passo foi atingido
    FALHA       o criterio nao foi atingido: e defeito (ou o teste nao rodou inteiro)
    INVESTIGAR  ha divergencia que precisa de diagnostico (pode ser defeito pre-existente)
    AVISO       nada a corrigir, mas algo merece atencao (ex.: nenhuma alteracao no diff)
    PULADO      fora do --so, ou nao rodou porque um passo anterior falhou
"""
import argparse, collections, datetime, os, re, shlex, subprocess, sys

# ---------------------------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------------------------

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # raiz do repositorio
os.chdir(RAIZ)
ECIDADE = os.path.join(RAIZ, "ecidade")      # montado como /var/www/html nos dois containers
WEB = "/var/www/html"
RT = {"74": "ecidade_php74", "85": "ecidade_php85"}
PASSOS = ["4b", "5", "5b", "6", "6b", "6c", "7"]
# O cmp.py (passo 7) le portas e containers de regressao/nucleo/ambiente.py, cujo padrao e o ambiente e74 da
# suite de regressao (:8074/:8185, ecidade74_*). Este script mede a pilha da RAIZ: sem estas variaveis o passo 7
# compararia outro ambiente (ou nenhum). Exportadas antes de rodar, as do usuario valem (setdefault).
for _k, _v in {"REGRESSAO_REF_URL": "http://localhost:8080", "REGRESSAO_PHP_NOVO_URL": "http://localhost:8085",
               "REGRESSAO_CONTAINER_REF": "ecidade_php74", "REGRESSAO_CONTAINER_PHP_NOVO": "ecidade_php85",
               "REGRESSAO_CONTAINER_BANCO": "ecidade_database"}.items():
    os.environ.setdefault(_k, _v)

# Artefatos conhecidos dos harnesses dos passos 6 e 6b: classes que aparecem diferentes entre
# os runtimes por causa do TESTE, nao da migracao. Registrados em Patrimonial, Financeiro e
# Saude; explicados no guia (passos 6 e 6b). UMA lista so: ela gera o filtro (uma linha de diff
# que case com algum padrao e ignorada; QUALQUER outra conta como divergencia) e a secao
# "Artefatos conhecidos" do fim do relatorio.
#   (padrao no texto da linha, classe, o que aparece no diff, por que nao e defeito)
ARTEFATOS_LISTA = [
    (r"requisicaoMaterial\.model", "RequisicaoMaterial",
     "`ArgumentCountError` so no 8.5 (no 7.4, valores `NULL`)",
     "o construtor exige 1 argumento e o teste faz `new X()` sem nenhum. O PHP 7.4 so avisava e seguia; o 8 recusa. "
     "O sistema de verdade sempre passa o argumento"),
    (r"solicitacaocompras\.model", "solicitacaoCompra",
     "`ArgumentCountError` so no 8.5 (no 7.4, `SEM_SAIDA`)", "idem"),
    (r"lancamentoContabil", "lancamentoContabil", "`ArgumentCountError` so no 8.5", "idem"),
    (r"ordemPagamento", "ordemPagamento", "`ArgumentCountError` so no 8.5", "idem"),
    (r"avaliacaogruporespostatrabalhointermitente", "cl_avaliacaogruporespostatrabalhointermitente",
     "`ERRO ... Exception` no 8.5 e `SEM_SAIDA` (ou um \"pulado\") no 7.4",
     "o construtor procura um arquivo `.dd.xml` que nao existe nesta base e falha NOS DOIS: o 8.5 captura a "
     "excecao e o teste a imprime; o 7.4 morre sem imprimir nada"),
    # SO a linha do campo datausu: o padrao era a classe inteira e, na base-php74 (empenho.php com construtor
    # PHP 4 ainda nao portado), escondia o defeito real -- sCamposNota vazio no 8.5 e o estado do passo 6.
    (r"classes/empenho\.php\tdatausu\t", "empenho, campo datausu", "`1969-12-31` no 7.4 contra a data de hoje no 8.5",
     "so acontece SEM sessao (sem a data do usuario logado), que e condicao do teste, nao do uso real"),
]
ARTEFATOS = re.compile("|".join(p for p, *_ in ARTEFATOS_LISTA))

# ---------------------------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------------------------

def sh(cmd, entrada=None, timeout=None, env=None):
    """Roda um comando (lista de argumentos) e devolve (codigo, stdout, stderr) como texto.
    latin-1 nos dois sentidos: 64% da base e LATIN-1, e utf-8 estrito quebraria na leitura.
    env: variaveis a acrescentar ao ambiente (ex.: ONLY para o cmp.py)."""
    r = subprocess.run(cmd, input=entrada.encode("latin-1") if entrada is not None else None,
                       stdin=None if entrada is not None else subprocess.DEVNULL,
                       capture_output=True, timeout=timeout, env={**os.environ, **(env or {})})
    return r.returncode, r.stdout.decode("latin-1"), r.stderr.decode("latin-1")

def dentro(caminho_host):
    """Caminho de um arquivo de ecidade/ visto de DENTRO dos containers."""
    return WEB + "/" + os.path.relpath(caminho_host, ECIDADE)

def ler(caminho):
    # latin-1 nunca falha na leitura (todo byte e um caractere): serve para LATIN-1 e para UTF-8 "cru"
    with open(caminho, encoding="latin-1") as f:
        return f.read()

def linhas(caminho):
    """Linhas nao vazias. split("\\n") (so o LF) e nao splitlines(): lido como latin-1, um texto UTF-8 (ou um byte
    0x85 de um arquivo LATIN-1) vira caracteres que o splitlines() trata como quebra de linha."""
    return [l.rstrip("\r") for l in ler(caminho).split("\n") if l.strip()]

def gravar(caminho, texto):
    # errors="replace": texto vindo de UTF-8 (ex.: log do docker) pode ter caractere fora do latin-1
    with open(caminho, "w", encoding="latin-1", errors="replace") as f:
        f.write(texto)

def diff_linhas(a, b):
    """Linhas so de um lado (multiconjunto: a ordem nao importa, repeticao conta)."""
    ca, cb = collections.Counter(a), collections.Counter(b)
    return sorted((ca - cb).elements()), sorted((cb - ca).elements())

def amostra(itens, n=15):
    """Lista para o relatorio, cortada em n itens com a contagem do resto."""
    itens = list(itens)
    corpo = "\n".join(itens[:n])
    if len(itens) > n:
        corpo += f"\n... e mais {len(itens) - n} (ver o arquivo bruto)"
    return corpo

def curta(itens, n=5):
    """Lista curta para o RELATORIO.md: os n primeiros em `codigo`, e "(+N)" com o resto."""
    itens = list(itens)
    corpo = ", ".join(f"`{x}`" for x in itens[:n])
    return corpo + (f" (+{len(itens) - n})" if len(itens) > n else "")

class Resultado:
    """O que cada passo devolve: situacao, uma linha de resumo e o texto completo (DETALHES.md).
    numeros: a coluna "Numeros" do RELATORIO.md (padrao: o resumo); itens: as linhas de "O que corrigir"."""
    def __init__(self, situacao, resumo, detalhe="", arquivos=(), numeros=None, itens=()):
        self.situacao, self.resumo, self.detalhe, self.arquivos = situacao, resumo, detalhe, list(arquivos)
        self.numeros, self.itens = numeros or resumo, list(itens)

# ---------------------------------------------------------------------------------------------
# Pre-requisitos
# ---------------------------------------------------------------------------------------------

def preparar(args):
    """Confere containers, universos e sessao. Devolve o contexto usado pelos passos."""
    _, out, _ = sh(["docker", "ps", "--format", "{{.Names}}"])
    faltam = [c for c in ("ecidade_database", "ecidade_php74", "ecidade_php85") if c not in out.split()]
    if faltam:
        sys.exit(f"ERRO: container(s) parado(s): {', '.join(faltam)}. Religue (docs/migrar-um-modulo.md, "
                 "'Antes de comecar').")

    # Arquivos alterados em relacao a --base, relativos a ecidade/ (usado no 4b e no 5; no --tudo,
    # e o proprio universo).
    _, out, _ = sh(["git", "diff", "--name-only", args.base, "--", "ecidade/"])
    alterados = {l[len("ecidade/"):] for l in out.splitlines() if l.startswith("ecidade/")}

    telas = None
    if args.tudo:
        # TUDO: o universo sao os arquivos que a migracao alterou (diff contra o master, o codigo antes
        # da migracao). Sao eles que podem regredir; e as classes alteradas sao as portadas -- uma classe
        # nunca portada pertence a area que o 7.4 ainda serve e diverge por construcao (6c).
        codigo = sorted(f for f in alterados if f.endswith((".php", ".class", ".inc"))
                        and os.path.isfile(os.path.join(ECIDADE, f)))
        telas = telas_servidas()
    else:
        universo = set()
        for p in args.prefixos:
            u = os.path.join(ECIDADE, "tmp", f"{p}_universo.txt")
            if not os.path.isfile(u):
                sys.exit(f"ERRO: falta {os.path.relpath(u)}. Rode antes: python3 scratchpad/enumera.py {p}")
            universo |= set(linhas(u))
        codigo = sorted(f for f in universo if f.endswith((".php", ".class", ".inc"))
                        and os.path.isfile(os.path.join(ECIDADE, f)))
    classes = sorted(f for f in codigo if f.startswith("classes/"))
    if args.amostra:
        codigo, classes = espalhar(codigo, args.amostra), espalhar(classes, args.amostra)
        if telas:
            telas = {"location": espalhar(telas["location"], args.amostra),
                     "map": espalhar(telas["map"], max(1, args.amostra // 4))}
    if args.telas:                       # telas pedidas explicitamente: so elas na bateria
        telas = {"location": [], "map": [t if t.endswith(".php") else t + ".php" for t in args.telas.split(",")]}

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    pasta = os.path.join(ECIDADE, "tmp", "verif", f"{args.lote}-{ts}")
    os.makedirs(pasta, exist_ok=True)
    os.chmod(pasta, 0o777)          # os containers (www-data/root) escrevem aqui

    gravar(os.path.join(pasta, "universo_codigo.txt"), "\n".join(codigo) + "\n")
    gravar(os.path.join(pasta, "classes.txt"), "\n".join(classes) + "\n")
    return {"pasta": pasta, "codigo": codigo, "classes": classes, "alterados": alterados, "telas": telas,
            "conhecidas": carregar_conhecidas(args.conhecidas), "sid": args.sid or achar_sessao()}

def espalhar(lista, n):
    """Amostra de n itens espalhados pela lista (deterministica: a mesma a cada execucao)."""
    if n <= 0 or len(lista) <= n:
        return list(lista)
    passo = len(lista) / n
    return [lista[int(i * passo)] for i in range(n)]

def telas_servidas():
    """As telas que o proxy manda ao 8.5, como no fluxo D do guia: as do `location` (prefixos lidos do
    nginx.conf) e as do `map` (faseb_map.conf, com a grafia do disco; o map guarda em minuscula)."""
    ng = ler(os.path.join(RAIZ, "docker", "proxy", "nginx.conf"))
    # So a linha ATIVA (nao comentada) do location. Na base-php74 o bloco nasce comentado: nada vai ao
    # 8.5, e o marcador abaixo (que nao casa com nenhuma tela) faz a lista do location sair vazia.
    m = re.search(r"^[ \t]*location ~\* \^\(\?:/w/\[0-9\]\+\)\?/\(\?:\(\?:([^)]+)\)", ng, re.M)
    pref = m.group(1) if m else "nenhum_prefixo_no_85"
    rx = re.compile(rf"^(?:{pref})[0-9]*_", re.I)
    disco = {f.lower(): f for f in os.listdir(ECIDADE)}
    loc = sorted(f for f in disco.values() if f.endswith(".php") and rx.match(f))
    mp = sorted({disco[m.group(1)] for l in ler(os.path.join(RAIZ, "docker", "proxy", "faseb_map.conf")).splitlines()
                 for m in [re.match(r"\s+(\S+)\s+php85;", l)] if m and m.group(1) in disco} - set(loc))
    return {"location": loc, "map": mp, "regex": rf"^(?:{pref})[0-9]*_"}

def carregar_conhecidas(caminho):
    """Telas que JA divergiam e estao caracterizadas (defeito pre-existente, fragmento, horario...). Na
    bateria, so as divergencias FORA desta lista contam como possivel regressao. Aceita:
      - docs/divergencias-conhecidas.md: a 1a coluna de cada linha da tabela; linhas marcadas
        "Corrigida" NAO entram (se uma delas voltar a divergir, e regressao); "x002/003.php" vira duas;
      - qualquer outra lista (ex.: o 7_divergentes.txt de uma bateria anterior): o 1o campo de cada linha.
    Padrao (caminho None): docs/divergencias-conhecidas.md, se existir."""
    if caminho is None:
        caminho = os.path.join(RAIZ, "docs", "divergencias-conhecidas.md")
        if not os.path.isfile(caminho):
            return None
    nomes = set()
    if caminho.endswith(".md"):
        for l in open(caminho, encoding="utf-8", errors="replace").read().split("\n"):   # o .md e UTF-8
            if not l.startswith("| `") or "Corrigida" in l:
                continue
            for tok in re.findall(r"`([^`]+)`", l.split("|")[1]):
                for t in re.split(r",\s*", tok):
                    m = re.match(r"^(.*?)(\d+)((?:/\d+)+)\.php$", t.strip())
                    if m:   # edu1_calendarioescola002/003.php -> 002 e 003
                        for num in [m.group(2)] + m.group(3).strip("/").split("/"):
                            nomes.add(f"{m.group(1)}{num}.php")
                    elif t.strip().endswith(".php"):
                        nomes.add(t.strip())
    else:
        for l in linhas(caminho):
            if l.split() and l.split()[0].endswith(".php"):
                nomes.add(l.split()[0])
    rel = os.path.relpath(caminho, RAIZ)
    return {"arquivo": rel if not rel.startswith("..") else caminho, "nomes": nomes}

def achar_sessao():
    """A sessao autenticada MAIS RECENTE do 7.4. O sess_?* exclui o arquivo "sess_" sem
    identificador (criado por requisicao com cookie vazio), que vinha primeiro e dava SID vazio."""
    _, out, _ = sh(["docker", "exec", "-i", "ecidade_php74", "sh", "-c",
                    "ls -t $(grep -la DB_modulo /var/lib/php/sessions/sess_?*) | head -1"])
    sid = out.strip().rsplit("sess_", 1)[-1]
    if len(sid) != 40:
        sys.exit("ERRO: nenhuma sessao autenticada. Entre em http://localhost:8090 (dbseller/dbseller) e rode de novo.")
    return sid

# ---------------------------------------------------------------------------------------------
# Passos
# ---------------------------------------------------------------------------------------------

def passo_4b(ctx, args):
    """Funcoes que APARECERAM nas linhas novas do diff e nao existem no PHP 7.4.
    O Rector pode emitir funcao do PHP 7/8 (str_contains, array_key_first) que compila no 7.4
    e so explode em execucao -- nenhum `php -l` pega."""
    _, d, _ = sh(["git", "diff", "-U0", args.base, "--", "ecidade/"])
    if not d.strip():
        return Resultado("AVISO", f"nenhuma alteracao em ecidade/ em relacao a {args.base}",
                         f"O diff contra `{args.base}` esta vazio. Se o lote ja foi commitado, rode com "
                         "`--base <commit anterior ao lote>`; se o Rector ainda nao rodou, rode-o antes.",
                         numeros="nada alterado no lote")
    # (?<!function ) exclui DECLARACOES: sem ele, "__construct" seria acusada como ausente
    rx = re.compile(r"(?<![\$>:\w])(?<!function )([a-z_][a-z0-9_]{2,})\s*\(")
    nov, vel = set(), set()
    for l in d.split("\n"):              # diff de codigo LATIN-1: so o \n quebra linha
        if l.startswith(("+++", "---")):
            continue
        if l.startswith("+"):
            nov |= set(rx.findall(l))
        elif l.startswith("-"):
            vel |= set(rx.findall(l))
    novas = sorted(nov - vel)
    arq = os.path.join(ctx["pasta"], "4b_funcoes_novas.txt")
    gravar(arq, "\n".join(novas) + "\n")
    # A pergunta e "o 8.5 conhece e o 7.4 NAO?": so isso e funcao NOVA do PHP (str_contains...). Perguntar so
    # ao 7.4 acusaria tambem nomes que nao sao funcoes do PHP -- JavaScript dentro do PHP (alert, append) e
    # funcoes do proprio e-cidade, que nao estao carregadas -- e no --tudo deu 286 falsos "ausentes".
    existe = {}
    for rt in ("74", "85"):
        _, out, _ = sh(["docker", "exec", "-i", f"ecidade_php{rt}", "php", "-r",
                        f'foreach(file("{dentro(arq)}", FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES) as $f)'
                        ' if(function_exists(trim($f))) echo trim($f),"\\n";'])
        existe[rt] = {l.strip() for l in out.split("\n") if l.strip()}
    # exit e die sao CONSTRUCOES da linguagem no 7.4 (funcionam, mas function_exists diz que nao) e viraram
    # funcoes de verdade no PHP 8.4. Aparecem pelas correcoes `break` -> `exit` e nao sao ausencia nenhuma.
    ausentes = sorted(existe["85"] - existe["74"] - {"exit", "die"})
    if ausentes:
        return Resultado("FALHA", f"{len(novas)} nomes novos, {len(ausentes)} funcoes do PHP 8 AUSENTES no 7.4",
                         "Funcoes que o Rector emitiu e o PHP 7.4 nao tem. Banir a regra que as emitiu e refazer o "
                         "passo 4 (guia: 'Como banir uma regra').\n\n```\n" + amostra(ausentes) + "\n```", [arq],
                         numeros=f"{len(ausentes)} funcoes que o 7.4 nao tem",
                         itens=[f"funcoes que o 7.4 nao tem (banir a regra do Rector que as emitiu): {curta(ausentes)}"])
    do_php = sorted(existe["74"] & existe["85"])
    return Resultado("OK", f"{len(do_php)} funcoes do PHP novas no diff, 0 ausentes no 7.4",
                     "Funcoes do PHP que aparecem nas linhas novas (todas existem no 7.4): " + (", ".join(do_php) or "nenhuma")
                     + f". Outros {len(novas) - len(do_php)} nomes novos nao sao funcoes do PHP (funcoes do e-cidade, "
                     "JavaScript dentro do PHP) e nao interessam aqui.", [arq])

def lint(ctx, rt, lista):
    """Arquivos da lista que NAO passam no `php -l` do runtime, com a mensagem de erro ({arquivo: mensagem}).
    O laco roda DENTRO do container (um docker exec so): um docker exec por arquivo seria lento demais.
    `ctx` nao e usado.
    `</dev/null` no php: sem ele o php consome o stdin do laco e o laco da uma volta so."""
    script = ('while IFS= read -r f; do m=$(php -l "$f" 2>&1 </dev/null) || '
              'printf "%s\\t%s\\n" "$f" "$(echo "$m" | grep -a -m1 -i error)"; done < ' + shlex.quote(dentro(lista)))
    _, out, _ = sh(["docker", "exec", "-i", RT[rt], "sh", "-c", f"cd {WEB}; {script}"], timeout=3600)
    return dict(l.split("\t", 1) for l in out.splitlines() if "\t" in l)

def passo_5(ctx, args):
    """`php -l` em TODO o universo, nos dois runtimes. Um arquivo que nao parseia no 7.4 derruba
    o runtime que serve o login; um que nao parseia no 8.5 derruba a tela migrada."""
    lista = os.path.join(ctx["pasta"], "universo_codigo.txt")
    e56, e85 = lint(ctx, "74", lista), lint(ctx, "85", lista)
    for rt, e in (("74", e56), ("85", e85)):
        gravar(os.path.join(ctx["pasta"], f"5_lint_erros_{rt}.txt"), "".join(f"{k}\t{v}\n" for k, v in sorted(e.items())))
    so56 = sorted(set(e56) - set(e85))
    so85 = sorted(set(e85) - set(e56))
    nos_dois = sorted(set(e56) & set(e85))
    quebrados_pelo_lote = [f for f in nos_dois if f in ctx["alterados"]]
    n = len(ctx["codigo"])
    det = [f"{n} arquivos verificados em cada runtime."]
    if so56:
        det.append("**So no 7.4** (o lote quebrou o runtime de referencia):\n```\n" + amostra(f"{f}  {e56[f]}" for f in so56) + "\n```")
    if so85:
        det.append("**So no 8.5:**\n```\n" + amostra(f"{f}  {e85[f]}" for f in so85) + "\n```")
    if quebrados_pelo_lote:
        det.append("**Falham nos dois E foram alterados pelo lote** (o lote pode te-los quebrado):\n```\n"
                   + amostra(quebrados_pelo_lote) + "\n```")
    if nos_dois:
        det.append(f"Falham nos dois e nao foram alterados (pre-existentes, so registrar): {len(nos_dois) - len(quebrados_pelo_lote)}.")
    arqs = [os.path.join(ctx["pasta"], f"5_lint_erros_{rt}.txt") for rt in ("74", "85")]
    if so56 or so85 or quebrados_pelo_lote:
        partes = [f"{len(so85)} quebram so no 8.5"] + ([f"{len(so56)} so no 7.4"] if so56 else []) \
                 + ([f"{len(quebrados_pelo_lote)} alterados quebram nos dois"] if quebrados_pelo_lote else [])
        nome = lambda fs: curta(os.path.basename(f) for f in fs)
        itens = ([f"nao compilam no 8.5: {nome(so85)}"] if so85 else []) \
                + ([f"o lote quebrou no 7.4: {nome(so56)}"] if so56 else []) \
                + ([f"alterados pelo lote e quebrados nos dois: {nome(quebrados_pelo_lote)}"] if quebrados_pelo_lote else [])
        return Resultado("FALHA", f"{n} arquivos: {len(so56)} so no 7.4, {len(so85)} so no 8.5, "
                         f"{len(quebrados_pelo_lote)} alterados que falham nos dois", "\n\n".join(det), arqs,
                         numeros=", ".join(partes), itens=itens)
    return Resultado("OK", f"{n} arquivos, 0 erros novos ({len(nos_dois)} pre-existentes)", "\n\n".join(det), arqs)

def por_processo(ctx, rt, harness, lista, saida):
    """Roda um harness PHP UMA ENTRADA POR PROCESSO (scratchpad/porclasse.sh): um fatal mata so
    aquele processo, e o resto da lista continua. Com a lista inteira num processo so, o 7.4
    morreu na classe 119 de 772 no soc e o diff comparou 103 classes sem acusar nada.
    Devolve o numero de entradas processadas (o #TOTAL do porclasse.sh)."""
    c = RT[rt]
    sh(["docker", "cp", "scratchpad/porclasse.sh", f"{c}:/tmp/pc.sh"])
    sh(["docker", "cp", harness, f"{c}:/tmp/h_{os.path.basename(harness)}"])
    _, out, err = sh(["docker", "exec", "-i", c, "sh", "/tmp/pc.sh", f"/tmp/h_{os.path.basename(harness)}"],
                     entrada=ler(lista), timeout=7200)
    gravar(saida, out)
    m = re.search(r"#TOTAL (\d+)", err)
    return int(m.group(1)) if m else -1

def comparar_harness(ctx, nome, harness, explicacao):
    """Passos 6 e 6b: roda o harness nos dois runtimes e compara as saidas, ignorando os
    artefatos conhecidos. Criterio: as duas rodadas cobrem a lista inteira E nao sobra
    nenhuma linha de diferenca fora dos artefatos."""
    lista = os.path.join(ctx["pasta"], "classes.txt")
    n = len(ctx["classes"])
    s = {rt: os.path.join(ctx["pasta"], f"{nome}_{rt}.txt") for rt in RT}
    tot = {rt: por_processo(ctx, rt, harness, lista, s[rt]) for rt in RT}
    a, b = linhas(s["74"]), linhas(s["85"])
    so56, so85 = diff_linhas(a, b)
    reais56 = [l for l in so56 if not ARTEFATOS.search(l)]
    reais85 = [l for l in so85 if not ARTEFATOS.search(l)]
    vistos = {cls for pad, cls, *_ in ARTEFATOS_LISTA for l in so56 + so85 if re.search(pad, l)}
    ctx.setdefault("artefatos_vistos", set()).update(vistos)
    sem = {rt: sum(1 for l in linhas(s[rt]) if l.startswith("SEM_SAIDA")) for rt in RT}
    det = [explicacao,
           f"Classes na lista: {n}. Processadas: 7.4={tot['74']}, 8.5={tot['85']}. "
           f"Sem saida (nada a testar ou o processo morreu): 7.4={sem['74']}, 8.5={sem['85']}.",
           "Artefatos conhecidos que apareceram (ignorados; explicados no fim do relatorio): "
           + (", ".join(sorted(vistos)) or "nenhum")]
    if reais56 or reais85:
        det.append("**Diferencas fora dos artefatos** (`<` = 7.4, `>` = 8.5):\n```\n"
                   + amostra([f"< {l}" for l in reais56] + [f"> {l}" for l in reais85], 30) + "\n```")
    if tot["74"] != n or tot["85"] != n:
        return Resultado("FALHA", f"incompleto: {n} classes, processadas 7.4={tot['74']} 8.5={tot['85']}",
                         "\n\n".join(det), s.values())
    if reais56 or reais85:
        # para o RELATORIO.md: as classes (e, no 6b, os campos) por tras das linhas de diferenca; linhas que
        # nao comecam por um arquivo .php (avisos que o harness imprime sem sessao) ficam so no DETALHES.md
        cols = [l.split("\t") for l in reais56 + reais85]
        cols = [c for c in cols if c[0].endswith(".php")]
        classes = collections.Counter(c[0] for c in {tuple(c[:2]) for c in cols})
        mais = [f"{os.path.basename(c)} ({k})" for c, k in classes.most_common()]
        if nome.startswith("6b"):
            numeros = f"{len(classes)} classes, {sum(classes.values())} campos"
            itens = [f"campos lidos errado no 8.5 (falta a guarda `0 == \"\"`): {len(classes)} classes; "
                     f"as com mais campos: {curta(mais)}"]
        else:
            numeros = f"{len(classes)} classes"
            itens = [f"estado inicial diferente (construtor que nao roda no 8.5?): "
                     f"{curta(os.path.basename(c) for c in sorted(classes))}"]
        return Resultado("FALHA", f"{n} classes, {len(reais56) + len(reais85)} linhas de diferenca fora dos artefatos",
                         "\n\n".join(det), s.values(), numeros=numeros, itens=itens)
    return Resultado("OK", f"{n} classes, so artefatos conhecidos ({len(vistos)})", "\n\n".join(det), s.values())

def passo_5b(ctx, args):
    """Carregar cada arquivo com extends/implements nos dois runtimes. O `php -l` olha um arquivo
    de cada vez e nao ve assinatura incompativel entre filha e mae em arquivos diferentes (LSP):
    no PHP 8 isso e fatal ao declarar a classe."""
    alvo = []
    for f in ctx["codigo"]:
        with open(os.path.join(ECIDADE, f), "rb") as fh:
            if re.search(rb"\b(extends|implements)\b", fh.read()):
                alvo.append(f)
    if not alvo:
        return Resultado("OK", "nenhum arquivo com extends/implements na lista", "Nada a carregar.")
    lista = os.path.join(ctx["pasta"], "5b_lista.txt")
    gravar(lista, "\n".join(alvo) + "\n")
    s = {}
    for rt in RT:
        sh(["docker", "cp", "scratchpad/carrega_arquivo.php", f"{RT[rt]}:/tmp/ca.php"])
        # Cada linha sai como <arquivo><TAB><ultima linha do harness>. O nome vai na frente porque
        # o harness nem sempre imprime "<arquivo><TAB>OK": um arquivo que exige login imprime so
        # "Feche seu navegador e faca login novamente.", e sem o nome a linha ficava sem dono.
        _, out, _ = sh(["docker", "exec", "-i", RT[rt], "sh", "-c",
                        f'while read f; do r=$(php /tmp/ca.php "$f" </dev/null 2>/dev/null | tail -1); '
                        f'printf "%s\\t%s\\n" "$f" "$r"; done < {shlex.quote(dentro(lista))}'],
                       timeout=3600)
        s[rt] = os.path.join(ctx["pasta"], f"5b_carga_{rt}.txt")
        gravar(s[rt], out)
    # "OK" quando o harness terminou em "<arquivo><TAB>OK"; qualquer outra coisa e a mensagem de falha
    res = {}
    for rt in RT:
        res[rt] = {}
        for l in linhas(s[rt]):
            f, _, r = l.partition("\t")
            res[rt][f] = ["OK"] if r.endswith("\tOK") else [r.split("\t", 1)[-1] or "sem saida"]
    quebra = sorted(f for f in alvo if res["74"].get(f, ["?"])[0] == "OK" and res["85"].get(f, ["?"])[0] != "OK")
    nos_dois = sum(1 for f in alvo if res["74"].get(f, ["?"])[0] != "OK" and res["85"].get(f, ["?"])[0] != "OK")
    det = [f"Arquivos com extends/implements: {len(alvo)}. Com resultado: 7.4={len(res['74'])}, 8.5={len(res['85'])}. "
           f"Falham nos dois (pre-existentes): {nos_dois}."]
    if len(res["74"]) != len(alvo) or len(res["85"]) != len(alvo):
        return Resultado("FALHA", f"incompleto: {len(alvo)} arquivos, resultados 7.4={len(res['74'])} 8.5={len(res['85'])}",
                         "\n\n".join(det), s.values())
    if quebra:
        det.append("**Carregam no 7.4 e NAO no 8.5:**\n```\n"
                   + amostra(f"{f}  {' '.join(res['85'][f])}" for f in quebra) + "\n```")
        lsp = [f for f in quebra if re.search(r"must be compatible|Could not check compatibility", " ".join(res["85"][f]))]
        outros = [f for f in quebra if f not in lsp]
        itens = ([f"heranca (assinatura incompativel com a mae): {curta(os.path.basename(f) for f in lsp)}"] if lsp else []) \
                + ([f"outro motivo (nao compila no 8.5, ou inclui arquivo que nao compila): "
                    f"{curta(os.path.basename(f) for f in outros)}"] if outros else [])
        return Resultado("FALHA", f"{len(alvo)} arquivos, {len(quebra)} so quebram no 8.5", "\n\n".join(det), s.values(),
                         numeros=f"{len(quebra)} quebram so no 8.5 ({len(lsp)} por heranca)", itens=itens)
    return Resultado("OK", f"{len(alvo)} arquivos, 0 so no 8.5 ({nos_dois} falham nos dois)", "\n\n".join(det), s.values())

def passo_6(ctx, args):
    """Passo 6: scratchpad/instancia_classes.php sobre classes.txt, via comparar_harness()."""
    return comparar_harness(ctx, "6_classes", "scratchpad/instancia_classes.php",
                            "Instancia cada classe e compara uma assinatura do estado inicial. Pega construtor estilo "
                            "PHP 4 que ficou sem renomear: no PHP 8 ele nao executa, sem erro nem aviso.")

def passo_6b(ctx, args):
    """Passo 6b: scratchpad/escrita.php sobre classes.txt, via comparar_harness()."""
    return comparar_harness(ctx, "6b_escrita", "scratchpad/escrita.php",
                            "Simula um formulario enviado (um valor por campo), chama atualizacampos() e compara o que "
                            "cada campo leu. Uma linha `< campo '1003'` / `> campo 0` e a guarda `0 == \"\"` faltando: "
                            "dado errado gravado em silencio.")

def passo_6c(ctx, args):
    """Forma negada `$this->x != ""`. Mede em TODAS as classes (negada_alvos.py nao recebe prefixo)
    e o negada_compara.py separa o que e do lote. So os pares do lote decidem o resultado."""
    p = ctx["pasta"]
    tsv = os.path.join(p, "6c_negada.tsv")
    sh(["python3", "scratchpad/negada_alvos.py", os.path.relpath(tsv, ECIDADE)])  # o script entra em ecidade/
    cls = os.path.join(p, "6c_classes.txt")
    gravar(cls, "\n".join(sorted({l.split("\t")[0] for l in linhas(tsv)})) + "\n")
    s = {}
    for rt in RT:
        sh(["docker", "cp", "scratchpad/negada.php", f"{RT[rt]}:/tmp/negada.php"])
        # UM arquivo temporario POR RUNTIME: o /tmp e compartilhado entre os containers
        script = (f'cd {WEB}; while read c; do grep -F "$(printf "%s\\t" "$c")" {shlex.quote(dentro(tsv))} > /tmp/_neg_{rt}.tsv; '
                  f'php -d display_errors=0 /tmp/negada.php /tmp/_neg_{rt}.tsv 2>/dev/null </dev/null; done < {shlex.quote(dentro(cls))}')
        _, out, _ = sh(["docker", "exec", "-i", RT[rt], "sh", "-c", script], timeout=7200)
        s[rt] = os.path.join(p, f"6c_negada_{rt}.txt")
        gravar(s[rt], out)
    _, out, _ = sh(["python3", "scratchpad/negada_compara.py", s["74"], s["85"], os.path.join(p, "classes.txt")])
    rel = os.path.join(p, "6c_comparacao.txt")
    gravar(rel, out)
    # o negada_compara.py imprime "VEREDITO: PASSOU|INCOMPLETO|INVESTIGAR" e os cabecalhos "== DO LOTE: N pares"
    # e "== FORA DO LOTE: N pares"; e deles que saem a situacao e o resumo
    m = re.search(r"VEREDITO: (\w+)", out)
    veredito = m.group(1) if m else "?"
    fora = re.search(r"== FORA DO LOTE: (\d+) pares", out)
    dentro_lote = re.search(r"^== DO LOTE: (\d+) pares", out, re.M)   # ^ e "== ": senao casa com o "FORA DO LOTE"
    resumo = f"{dentro_lote.group(1) if dentro_lote else '?'} divergencias no lote ({fora.group(1) if fora else '?'} fora do lote, ignoradas)"
    det = ("Saida do negada_compara.py. Os pares FORA DO LOTE sao de classes que o lote nao usa (areas ainda "
           "servidas pelo 7.4) e nao se corrigem aqui.\n\n```\n" + out.strip() + "\n```")
    situacao = {"PASSOU": "OK", "INCOMPLETO": "FALHA", "INVESTIGAR": "INVESTIGAR"}.get(veredito, "FALHA")
    # para o RELATORIO.md: os pares DO LOTE por tipo (linhas "   TIPO classe campo metodo   7.4=... 8.5=...")
    pares = collections.defaultdict(list)
    for l in out.split("== DO LOTE", 1)[-1].splitlines():
        c = l.split()
        if len(c) >= 4 and c[0] in ("FORMA_NEGADA", "VALOR_DIFERENTE", "ERRO", "SO_DE_UM_LADO"):
            pares[c[0]].append(f"{os.path.basename(c[1])} {c[2]} {c[3]}")
    itens = []
    if pares["FORMA_NEGADA"]:
        ncls = len({p.split()[0] for p in pares["FORMA_NEGADA"]})
        itens.append(f"forma negada a corrigir (`negada_corrige.py`): {len(pares['FORMA_NEGADA'])} pares em {ncls} classes: "
                     f"{curta(pares['FORMA_NEGADA'], 3)}")
    if pares["VALOR_DIFERENTE"]:
        itens.append(f"{len(pares['VALOR_DIFERENTE'])} pares com valor diferente: a classe ficou sem a guarda do `==` (o mesmo do 6b)")
    for t in ("ERRO", "SO_DE_UM_LADO"):
        if pares[t]:
            itens.append(f"{t}: {curta(pares[t], 3)}")
    numeros = (f"{len(pares['FORMA_NEGADA'])} pares a corrigir" if situacao != "FALHA" else resumo) \
              + (f", {len(pares['VALOR_DIFERENTE'])} sem a guarda do ==" if pares["VALOR_DIFERENTE"] else "")
    return Resultado(situacao, resumo, det, [s["74"], s["85"], rel], numeros=numeros, itens=itens)

def normalizacao_do_cmp():
    """A MESMA normalizacao que o cmp.py aplica antes de comparar (sid, nomes temporarios, datas
    de PDF...). Lida do proprio cmp.py, e nao copiada, para o diagnostico enxergar exatamente a
    diferenca que a bateria enxergou. Devolve uma funcao bytes -> bytes."""
    fonte = ler("scratchpad/cmp.py")
    if "def regras_norm(" in fonte:
        # cmp.py da regressao-php74 (PR #30): so roda a bateria sob __main__; importado, da as mesmas regras
        # (fixas + host:porta de cada runtime)
        import importlib.util
        spec = importlib.util.spec_from_file_location("cmp_bateria", os.path.join(RAIZ, "scratchpad", "cmp.py"))
        cmp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cmp)
        regras = cmp.regras_norm()
        return lambda b: cmp.norm(b, regras)
    # cmp.py da base: roda a bateria ao ser importado, entao so a lista NORM = [...] e lida (ela vem antes de
    # "def norm(" e nao usa nada alem de re)
    bloco = fonte[fonte.index("NORM = ["): fonte.index("def norm(")]
    ns = {"re": re}
    exec(bloco, ns)
    def norm(b):
        for rx, rep in ns["NORM"]:
            b = rx.sub(rep, b)
        return b
    return norm

LOG_PHP = os.path.join(ECIDADE, "extension", "log", "error.log")

def pedir(porta, tela, sid, sess):
    """Pede UMA tela a uma porta, como a bateria faz (sessao restaurada antes), e devolve
    (codigo HTTP, corpo, erros fatais do PHP, erros de SQL do PostgreSQL) daquele pedido.
    O error.log e zerado antes, e o log do banco e lido so a partir do instante do pedido."""
    sh(["docker", "exec", "-u", "root", "ecidade_php74", "sh", "-c",
        f"cp /tmp/_diag_sess.bak {sess}; chown www-data:www-data {sess}"])
    open(LOG_PHP, "w").close()
    t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    r = subprocess.run(["curl", "-s", "-m", "60", "-b", f"ECIDADEWINDOWMAIN={sid}", "-w", "\n@@%{http_code}",
                        f"http://localhost:{porta}/{tela}"], capture_output=True, stdin=subprocess.DEVNULL)
    corpo, _, codigo = r.stdout.rpartition(b"\n@@")   # o -w acrescenta "\n@@<codigo>" ao fim do corpo
    import time; time.sleep(1)               # o Logger e o PostgreSQL gravam logo depois da resposta
    fatais = sorted({re.sub(r"^\[[^]]*\]\s*", "", l).strip() for l in ler(LOG_PHP).split("\n")
                     if "E_ERROR" in l or "Uncaught" in l})
    _, out, err = sh(["docker", "logs", "--since", t0, "ecidade_database"])
    # o docker devolve o log ja em UTF-8 (com o caractere de substituicao no lugar do LATIN-1 que nao
    # converteu); o sh() decodificou como latin-1, entao desfaz e decodifica como UTF-8
    sql, ls = [], (out + err).encode("latin-1").decode("utf-8", "replace").splitlines()
    for i, l in enumerate(ls):
        if "ERRO:" in l:                     # o log do PostgreSQL e em PORTUGUES (locale pt_BR)
            sql.append(l.split("ERRO:", 1)[1].strip()
                       + (" | " + ls[i + 1].split(":", 1)[-1].strip() if i + 1 < len(ls) and "INSTRU" in ls[i + 1] else ""))
    return codigo.decode() or "000", corpo, fatais, sql

def trecho_diferente(a, b, contexto=80):
    """Onde dois corpos (ja normalizados) comecam a diferir, com um pouco de texto em volta."""
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    ini = max(0, i - contexto)
    fmt = lambda x: x[ini:i + contexto].decode("latin-1").replace("\n", "\\n")
    return i, fmt(a), fmt(b)

def diagnosticar(telas, sid, p):
    """Para cada tela divergente: pede de novo aos dois runtimes, coleta os erros e classifica
    pela tabela de decisao do guia (passo 7). Devolve as linhas para o relatorio."""
    norm = normalizacao_do_cmp()
    sess = f"/var/lib/php/sessions/sess_{sid}"
    sh(["docker", "exec", "-u", "root", "ecidade_php74", "cp", sess, "/tmp/_diag_sess.bak"])
    saida = []
    try:
        for tela in telas:
            c56, b56, f56, q56 = pedir(8080, tela, sid, sess)
            c85, b85, f85, q85 = pedir(8085, tela, sid, sess)
            n56, n85 = norm(b56), norm(b85)
            if c56 == c85 and n56 == n85:
                tipo = "NAO REPRODUZIU (identica agora: diferenca ocasional, ex. horario)"
            elif c56 == "200" and c85 != "200":
                tipo = "REGRESSAO: quebra so no 8.5 -> corrigir"
            elif c56 != "200" and c85 == "200":
                tipo = "PRE-EXISTENTE: quebra so no 7.4 (defeito da referencia) -> registrar, nao corrigir"
            elif c56 != "200" and c85 != "200":
                tipo = "QUEBRA NOS DOIS (pre-existente ou dado ausente) -> nao mexer; conferir se a causa e a mesma"
            else:
                tipo = "SILENCIOSA: 200 nos dois, conteudo diferente -> o tipo mais perigoso, ver o trecho"
            bloco = [f"### {tela}", "", f"- 7.4: HTTP {c56}, {len(b56)} bytes; 8.5: HTTP {c85}, {len(b85)} bytes",
                     f"- **Classificacao: {tipo}**"]
            for rt, fat, sql in (("8.5", f85, q85), ("7.4", f56, q56)):
                for x in fat[:3]:
                    bloco.append(f"- erro do PHP no {rt}: `{x[:400]}`")
                for x in sql[:3]:
                    bloco.append(f"- erro de SQL no {rt}: `{x[:400]}`")
            if c56 == c85 == "200" and n56 != n85:
                pos, t56, t85 = trecho_diferente(n56, n85)
                bloco += [f"- as paginas comecam a diferir no byte {pos}:", "", "```",
                          f"7.4: ...{t56}...", f"8.5: ...{t85}...", "```"]
            if not (f56 or f85 or q56 or q85) and not (c56 == c85 == "200"):
                bloco.append("- nenhum erro registrado nos logs: ver o corpo da resposta (pagina de erro da aplicacao?)")
            for rt, b in (("74", b56), ("85", b85)):
                gravar(os.path.join(p, "7_corpo_" + tela.replace("/", "_") + f"_{rt}.html"), b.decode("latin-1"))
            saida.append("\n".join(bloco))
    finally:
        sh(["docker", "exec", "-u", "root", "ecidade_php74", "sh", "-c",
            f"cp /tmp/_diag_sess.bak {sess}; chown www-data:www-data {sess}; rm -f /tmp/_diag_sess.bak"])
    return saida

def passo_7(ctx, args):
    """Bateria byte a byte (scratchpad/cmp.py) em todas as telas dos prefixos. O cmp.py restaura a
    sessao antes de cada pedido, normaliza o que muda a cada requisicao e refaz o par antes de acusar."""
    p = ctx["pasta"]
    # Prova de fumaca: com sessao invalida as duas portas devolvem a mesma pagina de login e a
    # bateria daria "tudo identico" sem ter testado nada. Exige uma tela de verdade (> 1 KB).
    sid = ctx["sid"]
    sess = f"/var/lib/php/sessions/sess_{sid}"
    sh(["docker", "exec", "-u", "root", "ecidade_php74", "cp", sess, "/tmp/_verif_sess.bak"])
    _, tam, _ = sh(["curl", "-s", "-o", "/dev/null", "-w", "%{size_download}", "-b", f"ECIDADEWINDOWMAIN={sid}",
                    "http://localhost:8080/cem1_campas001.php"])
    sh(["docker", "exec", "-u", "root", "ecidade_php74", "sh", "-c",
        f"cp /tmp/_verif_sess.bak {sess}; chown www-data:www-data {sess}; rm -f /tmp/_verif_sess.bak"])
    if int(tam or 0) < 1000:
        return Resultado("FALHA", f"sessao invalida (tela de teste com {tam} bytes)",
                         "A sessao nao esta autenticada: a bateria compararia duas paginas de login. Entre em "
                         "http://localhost:8090 (dbseller/dbseller) e rode de novo, ou passe --sid.")
    div = os.path.join(p, "7_divergentes.txt")
    log = os.path.join(p, "7_bateria.log")
    # Uma ou mais rodadas do cmp.py: (descricao, regex, lista ONLY). No modo de lote, uma rodada pelo
    # regex dos prefixos. No --tudo, uma pelo regex do location e outra com a lista do map -- a lista
    # inteira do location (~9 mil nomes) nao caberia numa variavel de ambiente (limite de 128 KB).
    t = ctx["telas"]
    if t is None:
        rodadas = [("prefixos " + " ".join(args.prefixos),
                    "^(?:" + "|".join(re.escape(x) for x in args.prefixos) + ")[0-9]*_", None)]
    else:
        rodadas = []
        if t["location"]:
            todas_loc = not args.amostra and not args.telas
            rodadas.append((f"location ({len(t['location'])} telas)", t.get("regex") if todas_loc else "^$",
                            None if todas_loc else t["location"]))
        if t["map"]:
            rodadas.append((f"map/lista ({len(t['map'])} telas)", "^$", t["map"]))
    ok = tot = nd = nt = 0
    textos, linhas_div, divs = [], [], []
    for desc, rx, lista in rodadas:
        tmp_div = div + ".parcial"
        env = {"ONLY": ",".join(lista)} if lista else None
        _, out, err = sh(["python3", "scratchpad/cmp.py", sid, rx, tmp_div], timeout=8 * 3600, env=env)
        textos.append(f"##### {desc}\n{out}{err}")
        # a ultima linha do cmp.py; se ela nao veio, o cmp.py morreu no meio e a rodada nao vale
        m = re.search(r"=== (\d+)/(\d+) identicas, (\d+) divergentes, (\d+) timeout ===", out)
        if not m:
            gravar(log, "\n".join(textos))
            return Resultado("FALHA", f"a bateria nao terminou: {desc} (ver 7_bateria.log)",
                             "```\n" + (out + err)[-2000:] + "\n```", [log])
        a, b, c, d = map(int, m.groups())
        ok, tot, nd, nt = ok + a, tot + b, nd + c, nt + d
        linhas_div += [l for l in (out + err).splitlines() if l.strip().startswith(("DIVERGE", "TIMEOUT", "PULADA"))]
        if os.path.isfile(tmp_div):
            divs.append(ler(tmp_div)); os.remove(tmp_div)
    gravar(log, "\n".join(textos))
    gravar(div, "".join(divs))

    # Separar as divergencias JA CONHECIDAS (caracterizadas) das NOVAS. So as novas sao diagnosticadas e
    # so elas decidem o resultado: e o criterio de regressao do fim da area (fluxo D do guia).
    divergentes = [l.split()[1] for l in linhas_div if l.strip().startswith("DIVERGE")]
    tout = [l.split()[1] for l in linhas_div if l.strip().startswith("TIMEOUT")]
    con = ctx["conhecidas"]
    nomes_con = con["nomes"] if con else set()
    novas = [x for x in divergentes if x not in nomes_con]
    velhas = [x for x in divergentes if x in nomes_con]
    # Timeout so no 7.4 (8.5 respondeu) e laco eterno da referencia: pre-existente. Timeout no 8.5 e
    # que pode ser regressao (laco que o PHP 8 passou a fazer). O cmp.py marca a referencia com `56=` (versao
    # da base) ou `ref=` (versao da regressao-php74, que o PR #30 traz): os dois rotulos valem.
    tout_56 = [l.split()[1] for l in linhas_div if l.strip().startswith("TIMEOUT")
               and re.search(r"\b(?:56|ref)=000\b", l) and "85=000" not in l]
    tout_novos = [x for x in tout if x not in nomes_con and x not in tout_56]
    testadas = set((t["location"] + t["map"]) if t else [])
    sumiram = sorted(x for x in nomes_con & testadas if x not in divergentes and x not in tout) if con else []

    det = (f"Rodadas: {'; '.join(r[0] for r in rodadas)}. Resultado: **{ok}/{tot} identicas**, {nd} divergentes, "
           f"{nt} timeout.")
    if con:
        det += (f"\n\nDivergencias conhecidas: lista `{con['arquivo']}` ({len(nomes_con)} telas). Desta execucao: "
                f"**{len(novas)} novas**, {len(velhas)} ja conhecidas" + (f", {len(tout_novos)} timeouts novos" if tout else "")
                + ". So as novas sao possivel regressao e so elas sao diagnosticadas.")
        if velhas:
            det += "\n\nJa conhecidas (nao diagnosticadas): " + ", ".join(velhas)
        if sumiram:
            det += ("\n\nConhecidas que agora saem **identicas** (foram corrigidas? atualize a lista): "
                    + ", ".join(sumiram))
    else:
        det += ("\n\nSem lista de divergencias conhecidas (`--conhecidas`, ou docs/divergencias-conhecidas.md): "
                "toda divergencia e tratada como nova.")
    # Independe da lista de conhecidas: timeout so no 7.4 e sempre pre-existente. (O `if sumiram` e o `else`
    # acima ja estiveram presos a este `if` por engano -- ver scratchpad/testes/test_verifica_relatorio.py.)
    if tout_56:
        det += ("\n\nTimeout so no 7.4 (laco eterno da referencia; o 8.5 respondeu) -- pre-existente, nao conta: "
                + ", ".join(tout_56))
    det += ("\n\nCada divergencia nova precisa de diagnostico (guia, passo 7: tabela de decisao): pode ser regressao "
            "(quebra so no 8.5) ou defeito pre-existente (quebra igual, ou so no 7.4).")
    if linhas_div:
        det += "\n\n```\n" + amostra(linhas_div, 40) + "\n```"
    if novas:
        # Diagnostico automatico de cada divergente NOVA (os timeouts nao: repetir o pedido levaria mais
        # 60 s cada e o motivo de um timeout raramente aparece em log).
        det += ("\n\n**Diagnostico automatico** (cada tela pedida de novo aos dois runtimes, com os logs limpos; "
                "a classificacao segue a tabela de decisao do guia, passo 7). As paginas de cada lado ficam na "
                "pasta como `7_corpo_<tela>_74.html` / `_85.html`.\n\n" + "\n\n".join(diagnosticar(novas, sid, p)))
    arquivos = [log, div] if divergentes else [log]
    if novas or tout_novos:
        # para o RELATORIO.md: as telas novas agrupadas pela causa, lida dos codigos HTTP do cmp.py
        # (linha "DIVERGE <tela>  ref=<cod>/<bytes>B  85=<cod>/<bytes>B")
        grupos = collections.defaultdict(list)
        for l in linhas_div:
            c = l.split()
            if c[0] == "DIVERGE" and c[1] in novas:
                cr = c[2].split("=")[1].split("/")[0] if len(c) > 2 else "?"
                c8 = c[3].split("=")[1].split("/")[0] if len(c) > 3 else "?"
                causa = (f"erro {c8} so no 8.5" if c8.startswith("5") and not cr.startswith("5")
                         else "conteudo diferente" if cr == c8 else f"codigo diferente (7.4 {cr}, 8.5 {c8})")
                grupos[causa].append(c[1])
        itens = [f"{len(v)} com {k}: {curta(v)}" for k, v in sorted(grupos.items(), key=lambda x: -len(x[1]))]
        if tout_novos:
            itens.append(f"{len(tout_novos)} com timeout no 8.5: {curta(tout_novos)}")
        itens.append("diagnostico de cada tela (log de erro de cada lado) em DETALHES.md")
        return Resultado("INVESTIGAR", f"{ok}/{tot} identicas, {len(novas)} divergencias novas"
                         + (f" ({len(velhas)} conhecidas)" if con else "") + f", {len(tout_novos)} timeout", det, arquivos,
                         numeros=f"{len(novas)} de {tot} divergem" + (f", {len(tout_novos)} timeout" if tout_novos else ""),
                         itens=itens)
    if divergentes or tout:
        return Resultado("OK", f"{ok}/{tot} identicas; as {len(divergentes) + len(tout)} restantes sao conhecidas "
                         "ou pre-existentes", det, arquivos)
    return Resultado("OK", f"{ok}/{tot} telas identicas", det, arquivos)

FUNCOES = {"4b": passo_4b, "5": passo_5, "5b": passo_5b, "6": passo_6, "6b": passo_6b, "6c": passo_6c, "7": passo_7}
TITULOS = {"4b": "funcoes que so existem no PHP 8", "5": "php -l nos dois runtimes", "5b": "heranca (carga dos arquivos)",
           "6": "construtor (instanciar classes)", "6b": "formulario lido errado (0 == \"\")",
           "6c": "forma negada != \"\"", "7": "telas byte a byte"}

# ---------------------------------------------------------------------------------------------
# Relatorio
# ---------------------------------------------------------------------------------------------

def relatorio(ctx, args, resultados, inicio):
    """Escreve os dois arquivos da pasta: RELATORIO.md (uma pagina: veredito, tabela e o que corrigir) e
    DETALHES.md (tudo: cabecalho completo, uma secao por passo com as linhas e o diagnostico, os artefatos)."""
    _, br, _ = sh(["git", "branch", "--show-current"])
    _, hd, _ = sh(["git", "log", "-1", "--format=%h %s"])
    fim = datetime.datetime.now()
    alvo = ("TUDO o que a migracao alterou (contra `" + args.base + "`)") if args.tudo else " ".join(args.prefixos)
    if args.amostra:
        alvo += f" -- AMOSTRA de {args.amostra} por lista (nao vale como bateria completa)"

    # --- RELATORIO.md: uma pagina ---
    ruins = [k for k, res in resultados.items() if res.situacao in ("FALHA", "INVESTIGAR")]
    veredito = "REPROVADO" if ruins else "APROVADO"
    rodou = [k for k in PASSOS if k in resultados]
    if len(rodou) < len(PASSOS):
        veredito += f" (so os passos {', '.join(rodou)})"
    duracao = str(fim - inicio).split(".")[0]
    s = [f"# Lote `{args.lote}` ({alvo}): {veredito}", "",
         f"{inicio:%d/%m/%Y %H:%M} | {duracao} | {len(ctx['codigo'])} arquivos, {len(ctx['classes'])} classes | "
         f"base: `{args.base}`", "",
         "| Passo | Verifica | Resultado | Numeros |", "| --- | --- | --- | --- |"]
    for k in PASSOS:
        res = resultados.get(k)
        s.append(f"| {k} | {TITULOS[k]} | {res.situacao if res else 'pulado'} | {res.numeros if res else ''} |")
    corrigir = [(k, i) for k in PASSOS if k in ruins for i in resultados[k].itens]
    if corrigir:
        s += ["", "## O que corrigir", ""] + [f"- **{k}:** {i}" for k, i in corrigir]
    s += ["", "Detalhes completos (linhas de cada passo, diagnostico de cada tela, artefatos conhecidos): "
          "`DETALHES.md`. Arquivos brutos de cada passo: nesta pasta.",
          "Fora desta verificacao (rodar a mao, ver o guia): passo 4 (Rector), nivel 3 (POST real), passos 8/8b."]
    caminho = os.path.join(ctx["pasta"], "RELATORIO.md")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(s) + "\n")

    # --- DETALHES.md: tudo ---
    r = [f"# Detalhes da verificacao do lote `{args.lote}` ({alvo})", "",
         f"- Data: {inicio:%d/%m/%Y %H:%M} (duracao {str(fim - inicio).split('.')[0]})",
         f"- Branch: `{br.strip()}`, HEAD `{hd.strip()}`; alteracoes medidas contra `{args.base}` "
         f"({len(ctx['alterados'])} arquivos alterados em ecidade/)",
         f"- Universo: {len(ctx['codigo'])} arquivos de codigo, {len(ctx['classes'])} classes",
         f"- Pasta: `{os.path.relpath(ctx['pasta'], RAIZ)}`", "",
         "| Passo | O que verifica | Situacao | Resumo |", "| --- | --- | --- | --- |"]
    for k in PASSOS:
        res = resultados.get(k)
        r.append(f"| {k} | {TITULOS[k]} | **{res.situacao if res else 'PULADO'}** | {res.resumo if res else ''} |")
    r += ["", "Situacoes: OK = criterio atingido; FALHA = defeito ou teste incompleto; INVESTIGAR = divergencia a "
          "diagnosticar; AVISO = nada a corrigir, mas conferir; PULADO = nao rodou.",
          "Fora deste relatorio (rodar a mao, ver o guia): passo 4 (Rector), nivel 3 (POST real), passos 8/8b (roteamento)."]
    for k in PASSOS:
        res = resultados.get(k)
        if not res:
            continue
        r += ["", f"## {k} - {TITULOS[k]}: {res.situacao}", "", res.detalhe]
        if res.arquivos:
            r += ["", "Arquivos brutos: " + ", ".join(f"`{os.path.basename(a)}`" for a in res.arquivos)]
    # Secao final: o que sao os artefatos conhecidos que os passos 6 e 6b ignoram
    vistos = ctx.get("artefatos_vistos", set())
    r += ["", "## Artefatos conhecidos (passos 6 e 6b)", "",
          "Classes que aparecem diferentes entre o 7.4 e o 8.5 por causa do **teste**, nao da migracao. Os passos 6 e 6b "
          "ignoram as linhas delas; qualquer **outra** diferenca conta como defeito. Registrados nas areas Patrimonial, "
          "Financeiro e Saude e explicados no guia (`docs/migrar-um-modulo.md`, passos 6 e 6b).", "",
          "| Apareceu nesta execucao? | Classe | O que aparece | Por que nao e defeito |", "| --- | --- | --- | --- |"]
    for _, cls, oque, porque in ARTEFATOS_LISTA:
        r.append(f"| {'**sim**' if cls in vistos else 'nao'} | `{cls}` | {oque} | {porque} |")
    with open(os.path.join(ctx["pasta"], "DETALHES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(r) + "\n")
    return caminho

# ---------------------------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------------------------

def main():
    """Le os argumentos, prepara o contexto, roda os passos escolhidos em ordem (parando no primeiro com FALHA ou
    INVESTIGAR, salvo --continuar), escreve o RELATORIO.md e sai com 1 se algum passo ficou FALHA/INVESTIGAR."""
    ap = argparse.ArgumentParser(description="Roda as verificacoes automaticas de um lote (ver o docstring do arquivo).")
    ap.add_argument("lote", help="nome do lote, usado no nome da pasta de saida (ex.: as)")
    ap.add_argument("prefixos", nargs="*", help="prefixos das telas do lote (ex.: soc hab); nao use com --tudo")
    ap.add_argument("--tudo", action="store_true",
                    help="verificar TUDO o que a migracao alterou e todas as telas servidas pelo 8.5 (fim de area)")
    ap.add_argument("--amostra", type=int, default=0, help="limitar cada lista a N itens espalhados (teste rapido)")
    ap.add_argument("--telas", default=None, help="bateria so nestas telas (separadas por virgula)")
    ap.add_argument("--conhecidas", default=None,
                    help="lista de divergencias ja conhecidas (padrao: docs/divergencias-conhecidas.md, se existir)")
    ap.add_argument("--so", default=",".join(PASSOS), help="passos a rodar, separados por virgula")
    ap.add_argument("--continuar", action="store_true", help="nao parar no primeiro passo que falhar")
    ap.add_argument("--base", default=None, help="referencia do git para medir as alteracoes (padrao: HEAD; no --tudo, master)")
    ap.add_argument("--sid", default=None, help="sessao autenticada para a bateria")
    args = ap.parse_args()
    if args.tudo == bool(args.prefixos):
        sys.exit("ERRO: informe os prefixos do lote OU --tudo (um dos dois).")
    if args.base is None:
        args.base = "master" if args.tudo else "HEAD"
    escolhidos = [x.strip() for x in args.so.split(",") if x.strip()]
    invalidos = [x for x in escolhidos if x not in FUNCOES]
    if invalidos:
        sys.exit(f"ERRO: passo(s) desconhecido(s): {', '.join(invalidos)}. Validos: {', '.join(PASSOS)}")

    inicio = datetime.datetime.now()
    ctx = preparar(args)
    alvo = "TUDO" if args.tudo else " ".join(args.prefixos)
    extra = (f", {len(ctx['telas']['location'])} + {len(ctx['telas']['map'])} telas (location + map)" if ctx["telas"] else "")
    print(f"Lote {args.lote} ({alvo}{', AMOSTRA ' + str(args.amostra) if args.amostra else ''}): "
          f"{len(ctx['codigo'])} arquivos, {len(ctx['classes'])} classes{extra}")
    print(f"Saida em {os.path.relpath(ctx['pasta'], RAIZ)}/\n")

    resultados, parar = {}, False
    for k in PASSOS:
        if k not in escolhidos or parar:
            continue
        print(f"  {k:3} {TITULOS[k]:32} ...", end="", flush=True)
        try:
            res = FUNCOES[k](ctx, args)
        except subprocess.TimeoutExpired:
            res = Resultado("FALHA", "estourou o tempo limite", "O passo nao terminou no tempo limite.")
        resultados[k] = res
        print(f"\r  {k:3} {TITULOS[k]:32} {res.situacao:10} {res.resumo}")
        if res.situacao in ("FALHA", "INVESTIGAR") and not args.continuar:
            parar = True
            print("\n  Parado no primeiro passo com problema (use --continuar para seguir mesmo assim).")

    caminho = relatorio(ctx, args, resultados, inicio)
    print(f"\nRelatorio: {os.path.relpath(caminho, RAIZ)}")
    ruins = [k for k, r in resultados.items() if r.situacao in ("FALHA", "INVESTIGAR")]
    sys.exit(1 if ruins else 0)

if __name__ == "__main__":
    main()
