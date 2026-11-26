import re,sys,os,collections
os.chdir(sys.argv[1])
dates=[];casts=[];tipos=collections.Counter();both=0
for root,_,fs in os.walk('app'):
    for f in sorted(fs):
        if not f.endswith('.php'): continue
        p=os.path.join(root,f); s=open(p,encoding='latin-1').read()
        for m in re.finditer(r'(?:protected|public)\s+\$(dates|casts)\s*=\s*\[(.*?)\]\s*;',s,re.S):
            ln=s.count('\n',0,m.start())+1
            if m.group(1)=='dates':
                attrs=re.findall(r'[\'"]([^\'"]+)[\'"]',m.group(2)); dates.append((p,ln,attrs))
            else:
                pr=re.findall(r'[\'"]([^\'"]+)[\'"]\s*=>\s*[\'"]([^\'"]+)[\'"]',m.group(2))
                dt=[(a,t) for a,t in pr if t.lower() in ('date','datetime','timestamp','immutable_date','immutable_datetime')]
                if dt:
                    casts.append((p,ln,dt))
                    for a,t in dt: tipos[t]+=1
print('DATES',len(dates),sum(len(a) for _,_,a in dates),'atributos')
print('CASTS_DATA',len(casts),'models',sum(len(d) for _,_,d in casts),'atributos',dict(tipos))
dset={p for p,_,_ in dates}; print('models com $dates e cast de data', len(dset & {p for p,_,_ in casts}))
with open(sys.argv[2],'w') as o:
    o.write('## $dates (%d models)\n\n| arquivo:linha | atributos |\n|---|---|\n'%len(dates))
    for p,l,a in sorted(dates): o.write('| %s:%d | %s |\n'%(p,l,', '.join(a)))
    o.write('\n## $casts de data (%d models)\n\n| arquivo:linha | atributo => tipo |\n|---|---|\n'%len(casts))
    for p,l,d in sorted(casts): o.write('| %s:%d | %s |\n'%(p,l,', '.join('%s => %s'%x for x in d)))
