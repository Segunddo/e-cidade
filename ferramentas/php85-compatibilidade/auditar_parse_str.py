"""Audita chamadas diretas de parse_str numa referencia Git, sem checkout."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

def audit(repo, ref, php, out):
    repo=Path(repo).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    git=['git','--git-dir='+str(repo)]
    php_version=subprocess.check_output([php,'-n','-r','echo PHP_VERSION_ID;']).decode()
    if int(php_version)<80000:raise ValueError('Use PHP 8 para os tokens de nomes qualificados.')
    sha=subprocess.check_output(git+['rev-parse',ref+'^{commit}']).decode().strip()
    candidates=subprocess.run(git+['grep','-I','-l','-z','-e','parse_str',sha,'--','ecidade'],capture_output=True)
    if candidates.returncode not in (0,1):raise RuntimeError(candidates.stderr.decode(errors='replace'))
    paths=[name.split(b':',1)[1].decode('utf8',errors='surrogateescape')
           for name in candidates.stdout.split(b'\0') if name]
    paths=[p for p in paths if Path(p).suffix.lower() in ('.php','.inc','.class','.phtml')]
    tree=subprocess.check_output(git+['ls-tree','-r','-z',sha,'--','ecidade'])
    objects={}
    for row in tree.split(b'\0'):
        if row:
            meta,name=row.split(b'\t',1);mode,kind,oid=meta.split()
            if mode in (b'100644',b'100755') and kind==b'blob':
                objects[name.decode('utf8',errors='surrogateescape')]=oid
    worker=Path(__file__).with_name('auditar-parse-str.php')
    records=[]
    for start in range(0,len(paths),100):
        batch=paths[start:start+100]
        request=b'\n'.join(objects[p] for p in batch)+b'\n'
        blob_data=subprocess.check_output(git+['cat-file','--batch'],input=request)
        cursor=0;entries=[]
        for path in batch:
            end=blob_data.index(b'\n',cursor);header=blob_data[cursor:end].split();size=int(header[2]);cursor=end+1
            source=blob_data[cursor:cursor+size];cursor+=size+1
            entries.append(json.dumps({'path':path,'source_base64':base64.b64encode(source).decode()},ensure_ascii=True))
        result=subprocess.run([php,'-n','-d','short_open_tag=1',str(worker)],input=('\n'.join(entries)+'\n').encode(),capture_output=True,timeout=90)
        if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        if len(rows)!=len(batch):raise RuntimeError('Resposta parcial do analisador.')
        records.extend(rows)
    calls=[dict(path=row['path'],**call) for row in records for call in row['calls']]
    pending=[call for call in calls if not call['closed'] or call['arguments']<2 or call['unpacked']]
    report={'ref':ref,'commit':sha,'candidate_files':len(paths),'direct_calls':len(calls),
            'argument_counts':{str(n):sum(c['arguments']==n for c in calls) for n in sorted({c['arguments'] for c in calls})},
            'pending_count':len(pending),'pending':pending,'files':records,
            'scope':'Chamadas diretas nomeadas parse_str em arquivos PHP/inc/class/phtml; nao resolve eval, aliases ou chamadas dinamicas.'}
    (out/'parse-str.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='ascii')
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','pending')},indent=2),flush=True)
    if pending:print(json.dumps(pending[:30],indent=2),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['repo','ref','php','out']:p.add_argument('--'+name,required=True)
    a=p.parse_args();audit(a.repo,a.ref,a.php,a.out)
