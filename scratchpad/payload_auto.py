#!/usr/bin/env python3
"""Gera um payload de PRIMEIRA TENTATIVA para o nivel 3, lendo o formulario real.

Nao substitui o olho: gera o esqueleto com valores plausiveis e o nivel 3 diz se
exercitou (INSERT de negocio) ou se voltou INCONCLUSIVO. So os inconclusivos
precisam de ajuste manual -- que e onde o custo do nivel 3 realmente esta.

Uso: python3 scratchpad/payload_auto.py <SID> <tela.php>
Saida: a querystring, em uma linha.
"""
import re, subprocess, sys
SID, TELA = sys.argv[1], sys.argv[2]
SESS = f"/var/lib/php/sessions/sess_{SID}"
subprocess.run(["bash","-lc",
  f'docker exec -u root -i ecidade_php56 sh -c "cp /tmp/_d.bak {SESS}; chown www-data:www-data {SESS}"'],
  capture_output=True)
h = subprocess.run(["bash","-lc",
  f'curl -s -b "ECIDADEWINDOWMAIN={SID}" http://localhost:8080/{TELA}'],
  capture_output=True).stdout.decode("latin-1")

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
for m in re.finditer(r'<select[^>]*name\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</select>', h, re.I|re.S):
    ops = [o for o in re.findall(r'<option[^>]*value\s*=\s*["\']?([^"\'>\s]*)', m.group(2), re.I) if o]
    campos[m.group(1)] = (ops[0] if ops else "", "select")
for m in re.finditer(r'<textarea[^>]*name\s*=\s*["\']([^"\']+)["\']', h, re.I):
    campos[m.group(1)] = ("", "textarea")

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
