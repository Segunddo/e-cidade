#!/usr/bin/env python3
"""Gera um payload de PRIMEIRA TENTATIVA para o nivel 3, lendo o formulario real.

Nao substitui o olho: gera o esqueleto com valores plausiveis e o nivel 3 diz se
exercitou (INSERT de negocio) ou se voltou INCONCLUSIVO. So os inconclusivos
precisam de ajuste manual -- que e onde o custo do nivel 3 realmente esta.

Uso: python3 scratchpad/payload_auto.py <SID> <tela.php>
Saida: a querystring, em uma linha.

Como faz: restaura a sessao a partir de /tmp/_d.bak, faz um GET da tela no 7.4
  (:8080), le <input>, <select> e <textarea> por expressao regular e da a cada
  campo um valor plausivel pela heuristica de valor() (pelo NOME do campo);
  acrescenta no fim o PRIMEIRO botao de submit (em tela 001, o de inclusao).
Entradas: SID de uma sessao autenticada; a tela (relativa a ecidade/).
  Exige /tmp/_d.bak no container ecidade_php74 (prova de fumaca do guia ou
  nivel3.py); se faltar, o cp falha em silencio e a sessao e usada como esta.
Efeitos colaterais: sobrescreve o arquivo de sessao com /tmp/_d.bak; o GET nao
  grava no banco. Nao altera codigo.
Limites: os valores NAO sao codificados para URL (espaco, & ou ' num valor
  quebram a querystring ou o comando curl do escrita_post.py); campo repetido
  fica com o ultimo visto.
Usado em: guia (docs/migrar-um-modulo.md), Nivel 3, "Passo 3 -- gerar o payload
  lendo o formulario"; chamado pelo nivel3.py e pelo demo_nivel3.sh.
"""
import re, subprocess, sys
SID, TELA = sys.argv[1], sys.argv[2]
SESS = f"/var/lib/php/sessions/sess_{SID}"
subprocess.run(["bash","-lc",
  f'docker exec -u root -i ecidade_php74 sh -c "cp /tmp/_d.bak {SESS}; chown www-data:www-data {SESS}"'],
  capture_output=True)
h = subprocess.run(["bash","-lc",
  f'curl -s -b "ECIDADEWINDOWMAIN={SID}" http://localhost:8080/{TELA}'],
  capture_output=True).stdout.decode("latin-1")

# atributos da tag como dict; so os valores entre aspas sao lidos
def attrs(t): return dict(re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', t))

campos, submit = {}, None
for tag in re.findall(r'<input[^>]*>', h, re.I):
    a = attrs(tag); n = a.get("name","")
    if not n: continue
    t = a.get("type","text").lower()
    if t in ("submit","button","image"):
        # o botao de INCLUSAO; dtjs_* sao os seletores de calendario, nao submit real
        if not n.startswith("dtjs_") and submit is None: submit = (n, a.get("value",""))
        continue
    if t == "reset": continue
    campos[n] = ("", t)
# select: ja resolve o valor -- a primeira <option> com value nao vazio (a vazia
# costuma ser o "Selecione")
for m in re.finditer(r'<select[^>]*name\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</select>', h, re.I|re.S):
    ops = [o for o in re.findall(r'<option[^>]*value\s*=\s*["\']?([^"\'>\s]*)', m.group(2), re.I) if o]
    campos[m.group(1)] = (ops[0] if ops else "", "select")
for m in re.finditer(r'<textarea[^>]*name\s*=\s*["\']([^"\']+)["\']', h, re.I):
    campos[m.group(1)] = ("", "textarea")

# Heuristica pelo nome do campo. A ORDEM importa: _dia/_mes/_ano (data quebrada
# em tres campos escondidos) antes do teste generico de "dt"/"data"; textos
# reconheciveis recebem TESTE_N3 (facil de achar se sobrar linha de teste no
# banco); chave/codigo/sequencial ficam vazios para a sequencia gerar; o resto, "1".
def valor(n, atual, tipo):
    if atual: return atual                      # select ja resolvido
    b = n.lower()
    if b.endswith("_dia"): return "31"
    if b.endswith("_mes"): return "12"
    if b.endswith("_ano"): return "2026"
    if "dt" in b or "data" in b: return "31/12/2026"
    if tipo == "textarea": return "OBS_N3"
    if any(k in b for k in ("descr","nome","obs","just","motiv","hist")): return "TESTE_N3"
    if any(k in b for k in ("sequencial","codigo","chave")): return ""   # chave: deixa a sequencia
    return "1"

qs = "&".join(f"{n}={valor(n,a,t)}" for n,(a,t) in campos.items())
if submit: qs += f"&{submit[0]}={submit[1]}"
print(qs)
