# compara.py <lock antes> <lock depois>: entram, saem, sobem de versao maior
import json,sys,re
def ld(p):
    l=json.load(open(p)); r={}
    for sec in ('packages','packages-dev'):
        for x in l.get(sec,[]): r[x['name']]=(x['version'],sec)
    return r
a,b=ld(sys.argv[1]),ld(sys.argv[2])
def maior(v):
    m=re.match(r'v?(\d+)(?:\.(\d+))?',v); 
    if not m: return v
    M=int(m.group(1)); return (M, int(m.group(2) or 0)) if M==0 else (M,)
print('entram', len(set(b)-set(a)))
for n in sorted(set(b)-set(a)): print('  +',n,b[n][0],b[n][1])
print('saem', len(set(a)-set(b)))
for n in sorted(set(a)-set(b)): print('  -',n,a[n][0])
mm=[n for n in sorted(set(a)&set(b)) if maior(a[n][0])!=maior(b[n][0])]
print('versao maior', len(mm))
for n in mm: print('  ^',n,a[n][0],'->',b[n][0])
print('total antes',len(a),'depois',len(b))
