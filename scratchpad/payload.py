#!/usr/bin/env python3
"""Extrai o esqueleto do POST de uma tela, lendo o formulario que o 5.6 emite.

Montar payload a mao e o que limita o nivel 3 -- e onde eu errei duas vezes:
o botao de submit muda de nome conforme a operacao (incluir/alterar/excluir),
campos obrigatorios nao aparecem no db_input (a data vem de _dia/_mes/_ano), e
alguns campos so existem como <select> ou hidden.

Uso: python3 scratchpad/payload.py <SID> <tela.php>
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

print(f"  tela: {TELA}   bytes: {len(h)}")
forms = re.findall(r'<form[^>]*>', h, re.I)
print(f"  forms: {len(forms)}")
for f in forms[:3]: print(f"    {f[:110]}")

def attrs(tag):
    return dict(re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', tag))

campos, submits, selects = [], [], []
for tag in re.findall(r'<input[^>]*>', h, re.I):
    a = attrs(tag); n = a.get("name","")
    if not n: continue
    t = a.get("type","text").lower()
    if t in ("submit","button","image"): submits.append((n, a.get("value","")))
    elif t != "reset": campos.append((n, a.get("value",""), t))
for m in re.finditer(r'<select[^>]*name\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</select>', h, re.I|re.S):
    ops = re.findall(r'<option[^>]*value\s*=\s*["\']?([^"\'>\s]*)', m.group(2), re.I)
    selects.append((m.group(1), ops[:6]))
for m in re.finditer(r'<textarea[^>]*name\s*=\s*["\']([^"\']+)["\']', h, re.I):
    campos.append((m.group(1), "", "textarea"))

print(f"\n  BOTOES DE SUBMIT ({len(submits)}) -- um deles vai no payload:")
for n,v in submits: print(f"    {n} = {v!r}")
print(f"\n  SELECTS ({len(selects)}):")
for n,o in selects: print(f"    {n:34s} opcoes: {o}")
print(f"\n  CAMPOS ({len(campos)}):")
for n,v,t in campos: print(f"    {n:34s} [{t:8s}] valor atual: {v!r}")
print("\n  ESQUELETO (preencher os vazios):")
part = [f"{n}={v}" for n,v,t in campos if t!="checkbox"]
print("    '" + "&".join(part) + "'")
