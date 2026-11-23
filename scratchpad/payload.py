#!/usr/bin/env python3
"""Extrai o esqueleto do POST de uma tela, lendo o formulario que o 7.4 emite.

Montar payload a mao e o que limita o nivel 3 -- e onde eu errei duas vezes:
o botao de submit muda de nome conforme a operacao (incluir/alterar/excluir),
campos obrigatorios nao aparecem no db_input (a data vem de _dia/_mes/_ano), e
alguns campos so existem como <select> ou hidden.

Uso: python3 scratchpad/payload.py <SID> <tela.php>

O que faz: mostra, para AJUSTE A MAO, tudo o que o formulario da tela tem --
  botoes de submit (nome e valor), <select> com as primeiras opcoes, campos
  (<input> e <textarea>) com tipo e valor atual -- e um esqueleto de querystring.
  E a versao "para ler" do payload_auto.py (que preenche os valores sozinho).
Como faz: restaura a sessao a partir de /tmp/_d.bak, faz um GET da tela no 7.4
  (:8080, o gabarito) e extrai as tags com expressoes regulares (sem parser HTML).
Entradas: SID de uma sessao autenticada; a tela (relativa a ecidade/).
  Exige /tmp/_d.bak no container ecidade_php74 (criado pela prova de fumaca do
  guia ou pelo nivel3.py); se faltar, o cp falha em silencio e a sessao e usada
  como esta.
Saida (stdout): o relatorio do formulario e o esqueleto (sem os checkboxes).
Efeitos colaterais: sobrescreve o arquivo de sessao com /tmp/_d.bak; o GET nao
  grava no banco (mas a tela roda, como em qualquer abertura). Nao altera codigo.
Usado em: guia (docs/migrar-um-modulo.md), Nivel 3, "Passo 3 -- gerar o payload
  lendo o formulario", para ver o formulario antes de montar o --payload a mao.
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

print(f"  tela: {TELA}   bytes: {len(h)}")
forms = re.findall(r'<form[^>]*>', h, re.I)
print(f"  forms: {len(forms)}")
for f in forms[:3]: print(f"    {f[:110]}")

# atributos de uma tag como dict; so os COM ASPAS (simples ou duplas) -- atributo
# sem aspas (name=x) nao e lido
def attrs(tag):
    return dict(re.findall(r'(\w+)\s*=\s*["\']([^"\']*)["\']', tag))

campos, submits, selects = [], [], []
for tag in re.findall(r'<input[^>]*>', h, re.I):
    a = attrs(tag); n = a.get("name","")
    if not n: continue
    t = a.get("type","text").lower()
    if t in ("submit","button","image"): submits.append((n, a.get("value","")))
    elif t != "reset": campos.append((n, a.get("value",""), t))
# <select name=...>...</select> (re.S: o conteudo atravessa linhas); das <option>
# pega o value com ou sem aspas, e mostra so as 6 primeiras
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
# checkbox fica de fora: marcado ou nao, depende da tela -- incluir a mao se precisar
part = [f"{n}={v}" for n,v,t in campos if t!="checkbox"]
print("    '" + "&".join(part) + "'")
