import re,sys,collections,subprocess,os
os.chdir(sys.argv[1])
cmd=r"grep -rnE '\bCarbon\b' --include=*.php --include=*.inc . | grep -v '^\./vendor' | grep -vE '^\S+:[0-9]+:\s*use '"
out=subprocess.run(['bash','-c',cmd],capture_output=True).stdout.decode('latin-1')
c=collections.Counter(); rows=[]
for l in out.splitlines():
    m=re.match(r'^(?:\./)?([^:]+):(\d+):(.*)$',l)
    if not m: continue
    f,n,t=m.groups()
    k=re.search(r'Carbon::(\w+)',t)
    if k: key='Carbon::'+k.group(1)
    elif re.search(r'new\s+\\?(?:\w+\\)*Carbon\b',t): key='new Carbon'
    elif re.search(r'@(param|return|var|property)',t): key='docblock'
    elif re.search(r'\bCarbon\s+\$',t): key='tipo em assinatura'
    elif 'Carbon::class' in t or "Carbon'" in t or 'Carbon"' in t: key='nome da classe como texto'
    else: key='outro'
    c[key]+=1; rows.append((f,int(n),key,t.strip()[:100]))
print('TOTAL',sum(c.values()),'arquivos',len({r[0] for r in rows}))
for k,v in c.most_common(): print(v,k)
with open(sys.argv[2],'w') as o:
    for r in rows: o.write('\t'.join(map(str,r))+'\n')
print([r for r in rows if r[2]=='outro'][:6])
