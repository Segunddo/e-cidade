#!/usr/bin/env python3
"""Passo 4 do guia (Rector) em um comando: simula, mostra as regras e, so com --aplicar, aplica ate zerar.

Uso (da raiz do repositorio):
    python3 scratchpad/rector_lote.py <prefixo> [<prefixo> ...]              # SO SIMULA e mostra as regras
    python3 scratchpad/rector_lote.py <prefixo> [<prefixo> ...] --aplicar    # aplica e repete ate 0 arquivos

    python3 scratchpad/rector_lote.py hab
    python3 scratchpad/rector_lote.py soc hab --aplicar
    python3 scratchpad/rector_lote.py hab --aplicar --aceitar NomeDaRegraRector   # regra nova ja conferida

Opcoes:
    --aplicar          grava as alteracoes (sem ele, nada e alterado: e o --dry-run do Rector)
    --aceitar R1,R2    regras NOVAS que voce ja conferiu pelo protocolo do guia e aceita neste lote
    --max-rodadas N    teto de rodadas do --aplicar (padrao 6); passou disso sem zerar = FALHA

Pre-requisitos:
    - container ecidade_php85 no ar e o Rector instalado em ecidade/tmp/rector/ (guia, "Instalar o Rector");
    - os alvos de cada prefixo ja gerados: python3 scratchpad/enumera.py <prefixo> (le ecidade/tmp/<prefixo>_alvos.txt).

O que ele faz, na ordem (cada item era um bloco de comandos do passo 4 do guia):
    1. junta os alvos dos prefixos numa lista so (ecidade/tmp/rector_lote_alvos.txt);
    2. copia a config versionada (scratchpad/rector-curado.php) e as regras proprias (scratchpad/rector-rules/)
       para dentro de ecidade/tmp/rector/ -- a versionada e a que vale; a copia e o que o container le;
    3. confere a SINTAXE da config: com erro nela, o Rector reporta "0 arquivos" sem mensagem nenhuma;
    4. roda a SIMULACAO (--dry-run) e lista as regras que disparariam, com quantos arquivos cada. Os ~15
       avisos "Deprecated" do vendor/ do Laravel vao para um arquivo (sao esperados, ver o guia);
    5. classifica cada regra:
         conhecida   ja conferida e aceita em lotes anteriores (lista REGRAS_ACEITAS abaixo)
         ressalva    aceita, mas exige uma conferencia manual depois (dita na tela)
         NOVA        nunca conferida: o --aplicar e RECUSADO ate voce seguir o protocolo do guia
                     ("Protocolo para regra nova") e passar --aceitar NomeDaRegra -- ou bani-la
       e mostra as linhas que cada regra nova mudaria, que e o primeiro passo do protocolo;
    6. avisa se o modulo tem construtor estilo PHP 4 e o Php4ConstructorRector NAO apareceu: e o sintoma
       do pin de versao quebrado (o Rector desliga essas regras em silencio);
    7. com --aplicar: aplica e repete ate uma rodada dizer 0 arquivos (o Rector nao converge numa passada),
       parando se aparecer regra nova no meio.

Saidas: ecidade/tmp/rector_lote/<AAAAMMDD-HHMM>/ com o JSON e os avisos de cada rodada
(simulacao.json/.err, rodada1.json/.err...). O resumo sai no terminal.

Codigo de saida: 0 = OK; 1 = regra nova (com --aplicar), erro do Rector ou nao zerou; 2 = pre-requisito faltando.
"""
import argparse, collections, datetime, json, os, re, shutil, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ECIDADE = os.path.join(RAIZ, "ecidade")
RECTOR = os.path.join(ECIDADE, "tmp", "rector")          # instalacao (ignorada pelo git)
WEB = "/var/www/html"                                     # ecidade/ visto de dentro do container

# Regras que ja dispararam em lotes anteriores e foram CONFERIDAS e aceitas (o motivo de cada uma
# esta no registro, docs/registro/). Qualquer regra fora daqui e "NOVA" e bloqueia o --aplicar.
REGRAS_ACEITAS = {
    "GuardaComparacaoLiteralRector": "regra propria: guarda do 0 == \"\" ($this->X == literal)",
    "ParseStrComExtractRector": "regra propria: parse_str de 1 argumento -> parse_str($s, $a); extract($a)",
    "Php4ConstructorRector": "construtor com o nome da classe -> __construct",
    "EregToPregMatchRector": "split/ereg (removidas no PHP 7) -> preg_*",
    "ConsistentImplodeRector": "implode($a, ',') -> implode(',', $a); conferida na base-php84 (5.6 e 8.5)",
    "ParenthesizeNestedTernaryRector": "ternario aninhado ganha parenteses (associando a esquerda, como o 7.4)",
    "RenameCastRector": "(real) -> (float); conferida na base-php84 (5.6 e 8.5)",
    "ReplaceEachAssignmentWithKeyCurrentRector": "$x = each($a) -> key()/current()/next()",
    "WrapVariableVariableNameInCurlyBracesRector": "$$x -> ${$x}",
}
# Aceitas, mas com uma conferencia manual obrigatoria depois de aplicar (mostrada na tela).
REGRAS_RESSALVA = {
    "OptionalParametersAfterRequiredRector":
        "da `= null` a parametros e MUDA A ASSINATURA da classe mae: procure `extends <Classe>` na base inteira "
        "e espelhe os padroes na filha, senao ela nao carrega no 8.5 (guia, passo 4; o passo 5b do "
        "verifica_lote.py pega o que escapar)",
}

def sh(cmd, env=None, timeout=None):
    """Roda um comando e devolve (codigo, stdout, stderr) como texto (latin-1: a base e LATIN-1)."""
    r = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout,
                       env={**os.environ, **(env or {})})
    return r.returncode, r.stdout.decode("latin-1"), r.stderr.decode("latin-1")

def classes_php4(b):
    """Classes com construtor estilo PHP 4 (metodo com o nome da classe, sem __construct), olhando CADA
    classe. Mesma logica do enumera.py. Em arquivo com namespace o metodo homonimo nao e construtor."""
    if re.search(rb'^\s*namespace\s+[\w\\]+\s*;', b, re.M):
        return 0
    pos = [(m.start(), m.group(1)) for m in re.finditer(rb'\bclass\s+(\w+)', b)]
    n = 0
    for i, (ini, nome) in enumerate(pos):
        corpo = b[ini: pos[i + 1][0] if i + 1 < len(pos) else len(b)]
        if not re.search(rb'function\s+__construct\s*\(', corpo, re.I) and \
           re.search(rb'function\s+' + re.escape(nome) + rb'\s*\(', corpo, re.I):
            n += 1
    return n

def rodar(lista_container, simular, pasta, nome):
    """Uma execucao do Rector. Devolve (dados do JSON, avisos que NAO sao os Deprecated esperados).
    O JSON e os avisos ficam gravados na pasta da execucao."""
    cmd = ["docker", "exec", "-i", "-e", f"ALVOS={lista_container}", "ecidade_php85",
           "php", "-d", "memory_limit=3G", f"{WEB}/tmp/rector/vendor/bin/rector", "process"]
    if simular:
        cmd.append("--dry-run")
    cmd += ["--config", f"{WEB}/tmp/rector/rector-curado.php", "--no-progress-bar", "--output-format=json"]
    _, out, err = sh(cmd, timeout=3600)
    with open(os.path.join(pasta, nome + ".json"), "w", encoding="latin-1") as f:
        f.write(out)
    with open(os.path.join(pasta, nome + ".err"), "w", encoding="latin-1") as f:
        f.write(err)
    # Os "Deprecated:" vem do vendor/ do Laravel 5.4 que o Rector carrega pelo autoloader: esperados.
    outros = [l for l in err.splitlines() if l.strip() and not l.startswith("Deprecated:")]
    # o JSON comeca no primeiro "{": qualquer texto que o Rector/PHP imprima antes dele no stdout e descartado
    try:
        dados = json.loads(out[out.index("{"):]) if "{" in out else None
    except ValueError:
        dados = None
    return dados, outros

def contar(dados):
    """(arquivos alterados, Counter regra -> numero de arquivos, erros do Rector)."""
    fd = dados.get("file_diffs") or []
    c = collections.Counter()
    for f in fd:
        for r in set(f.get("applied_rectors") or []):   # set: conta ARQUIVOS por regra, nao ocorrencias
            c[r.split("\\")[-1]] += 1
    return fd, c, dados.get("errors") or []

def linhas_da_regra(fd, regra, n=12):
    """As linhas que uma regra mudaria (o passo 1 do protocolo para regra nova do guia)."""
    saida = []
    for f in fd:
        if regra in {r.split("\\")[-1] for r in f.get("applied_rectors") or []}:
            saida.append(f"    ### {f['file']}")
            for l in f.get("diff", "").splitlines():
                if l[:1] in "+-" and l[:3] not in ("+++", "---"):
                    saida.append("      " + l[:150])
        if len(saida) > n * 4:
            saida.append("      ...")
            break
    return saida

def main():
    """Le os argumentos, confere os pre-requisitos, prepara lista e config, simula, classifica as regras e,
    com --aplicar (e sem regra nova nem erro), aplica ate uma rodada alterar 0 arquivos. Sai com sys.exit:
    os codigos estao no docstring do arquivo."""
    ap = argparse.ArgumentParser(description="Passo 4 do guia (Rector) em um comando. Ver o docstring do arquivo.")
    ap.add_argument("prefixos", nargs="+", help="prefixos do lote (ex.: soc hab)")
    ap.add_argument("--aplicar", action="store_true", help="grava as alteracoes (sem ele, so simula)")
    ap.add_argument("--aceitar", default="", help="regras novas ja conferidas, separadas por virgula")
    ap.add_argument("--max-rodadas", type=int, default=6, help="teto de rodadas do --aplicar")
    args = ap.parse_args()
    aceitas_agora = {x.strip() for x in args.aceitar.split(",") if x.strip()}

    # --- pre-requisitos -----------------------------------------------------------------------
    _, ps, _ = sh(["docker", "ps", "--format", "{{.Names}}"])
    if "ecidade_php85" not in ps.split():
        sys.exit("ERRO: o container ecidade_php85 esta parado. Religue (guia, 'Antes de comecar').")
    if not os.path.isfile(os.path.join(RECTOR, "vendor", "bin", "rector")):
        sys.exit("ERRO: Rector nao instalado em ecidade/tmp/rector/. Veja o guia, 'Instalar o Rector'.")
    alvos = []
    for p in args.prefixos:
        a = os.path.join(ECIDADE, "tmp", f"{p}_alvos.txt")
        if not os.path.isfile(a):
            sys.exit(f"ERRO: falta ecidade/tmp/{p}_alvos.txt. Rode antes: python3 scratchpad/enumera.py {p}")
        alvos += [l.strip() for l in open(a, encoding="latin-1") if l.strip()]
    alvos = sorted(set(alvos))
    lista = os.path.join(ECIDADE, "tmp", "rector_lote_alvos.txt")
    with open(lista, "w") as f:
        f.write("\n".join(alvos) + "\n")
    lista_container = f"{WEB}/tmp/rector_lote_alvos.txt"

    pasta = os.path.join(ECIDADE, "tmp", "rector_lote", datetime.datetime.now().strftime("%Y%m%d-%H%M"))
    os.makedirs(pasta, exist_ok=True)

    # --- config e regras: a versionada (scratchpad/) e copiada para onde o container le --------
    shutil.copy("scratchpad/rector-curado.php", os.path.join(RECTOR, "rector-curado.php"))
    os.makedirs(os.path.join(RECTOR, "rector-rules"), exist_ok=True)
    for r in os.listdir("scratchpad/rector-rules"):
        if r.endswith(".php"):
            shutil.copy(os.path.join("scratchpad/rector-rules", r), os.path.join(RECTOR, "rector-rules", r))
    _, out, err = sh(["docker", "exec", "-i", "ecidade_php85", "php", "-l", f"{WEB}/tmp/rector/rector-curado.php"])
    if "No syntax errors" not in out:
        sys.exit("ERRO: a config do Rector tem erro de sintaxe (o Rector reportaria '0 arquivos' sem avisar):\n"
                 + out + err)
    # tamanho da denylist so para o resumo: conta os "::class" entre "->withSkip([" e o primeiro "]);" depois dele
    skip = open("scratchpad/rector-curado.php", encoding="utf-8").read()
    skip = skip[skip.index("->withSkip(["):]
    denylist = len(re.findall(r"::class", skip[:skip.index("]);")]))

    php4 = sum(classes_php4(open(os.path.join(ECIDADE, f), "rb").read())
               for f in alvos if os.path.isfile(os.path.join(ECIDADE, f)))
    print(f"Lote {' '.join(args.prefixos)}: {len(alvos)} arquivos-alvo, {php4} construtores PHP 4 entre eles; "
          f"denylist com {denylist} regras")
    print(f"Saidas em {os.path.relpath(pasta, RAIZ)}/\n")

    # --- simulacao ------------------------------------------------------------------------------
    print("SIMULACAO (--dry-run, nada e gravado):")
    dados, outros = rodar(lista_container, True, pasta, "simulacao")
    if dados is None:
        sys.exit("ERRO: o Rector nao devolveu resultado. Avisos:\n" + "\n".join(outros[:20]))
    fd, regras, erros = contar(dados)
    print(f"  {len(fd)} arquivos seriam alterados, {len(erros)} erros do Rector")
    novas = []
    for r, n in regras.most_common():
        if r in REGRAS_ACEITAS:
            tipo = "conhecida"
        elif r in REGRAS_RESSALVA:
            tipo = "RESSALVA"
        elif r in aceitas_agora:
            tipo = "aceita por voce (--aceitar)"
        else:
            tipo = "NOVA"
            novas.append(r)
        print(f"  {n:5d}  {r:45} {tipo}")
    if outros:
        print("\n  ATENCAO: o Rector emitiu avisos alem dos Deprecated esperados (ver simulacao.err):")
        print("\n".join("    " + l[:160] for l in outros[:10]))
    if erros:
        print("\n  ERROS do Rector:")
        print("\n".join("    " + str(e)[:200] for e in erros[:10]))
    if php4 and "Php4ConstructorRector" not in regras:
        print(f"\n  ATENCAO: ha {php4} construtores PHP 4 nos alvos e o Php4ConstructorRector NAO apareceu. Se eles "
              "ainda nao foram convertidos, o pin de versao (withPhpVersion) quebrou -- ver o guia, passo 4.")
    for r in regras:
        if r in REGRAS_RESSALVA:
            print(f"\n  RESSALVA {r}: {REGRAS_RESSALVA[r]}")
    if novas:
        print(f"\n  REGRA(S) NOVA(S): {', '.join(novas)}. O que cada uma mudaria:")
        for r in novas:
            print(f"\n  == {r}")
            print("\n".join(linhas_da_regra(fd, r)))
        print("\n  Siga o 'Protocolo para regra nova' do guia (passo 4): teste nos DOIS runtimes a construcao que ela "
              "emite. Se for aceitar, rode de novo com --aceitar " + ",".join(novas) +
              "; se nao, bana-a (guia, 'Como banir uma regra').")

    if not args.aplicar:
        print("\nNada foi alterado. Se as regras acima estao certas, rode de novo com --aplicar.")
        sys.exit(0)
    if novas:
        print("\nRECUSADO: --aplicar com regra nova nao conferida. Nada foi alterado.")
        sys.exit(1)
    if erros:
        print("\nRECUSADO: o Rector relatou erros na simulacao. Nada foi alterado.")
        sys.exit(1)

    # --- aplicar ate zerar ------------------------------------------------------------------------
    print("\nAPLICANDO (repete ate uma rodada alterar 0 arquivos):")
    alterados = set()
    # for/else: o else so roda se o laco terminar sem break, isto e, nenhuma rodada chegou a 0 arquivos
    for i in range(1, args.max_rodadas + 1):
        dados, outros = rodar(lista_container, False, pasta, f"rodada{i}")
        if dados is None:
            print(f"  rodada {i}: o Rector nao devolveu resultado (ver rodada{i}.err)")
            sys.exit(1)
        fd, regras, erros = contar(dados)
        alterados |= {f["file"] for f in fd}
        print(f"  rodada {i}: {len(fd)} arquivos alterados" + (f"  ({', '.join(f'{r} {n}' for r, n in regras.most_common())})" if fd else ""))
        surgiu = [r for r in regras if r not in REGRAS_ACEITAS and r not in REGRAS_RESSALVA and r not in aceitas_agora]
        if surgiu or erros:
            print(f"  PARADO: {'regra nova ' + ', '.join(surgiu) if surgiu else 'erros do Rector'} nesta rodada. "
                  "Confira com git diff; para desfazer: git checkout -- <arquivos>.")
            sys.exit(1)
        if not fd:
            break
    else:
        print(f"  NAO ZEROU em {args.max_rodadas} rodadas (use --max-rodadas para mais).")
        sys.exit(1)
    print(f"\nPronto: {len(alterados)} arquivos alterados no total. Proximo passo: "
          f"python3 scratchpad/verifica_lote.py <lote> {' '.join(args.prefixos)}")

if __name__ == "__main__":
    main()
