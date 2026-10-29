# Independent derivation of the release's file list: git ls-tree at the pin, filtered by package_spec.json's own
# exclude and seed globs, compared with the record (path, class, sha256 of the committed bytes). Uses no release tooling.
import json,re,subprocess,sys,hashlib
pin=sys.argv[1];rec=json.load(open('releases/starter-3.2.0.json'))
spec=json.loads(subprocess.check_output(['git','show',f'{pin}:release/package_spec.json']))
def rx(g):
    out='';i=0
    while i<len(g):
        if g.startswith('**/',i): out+='(?:.*/)?';i+=3
        elif g.startswith('**',i): out+='.*';i+=2
        elif g[i]=='*': out+='[^/]*';i+=1
        elif g[i]=='?': out+='[^/]';i+=1
        else: out+=re.escape(g[i]);i+=1
    return re.compile('^'+out+'$')
EX=[rx(g) for g in spec['exclude']];SE=[rx(g) for g in spec['seed']]
rows=subprocess.check_output(['git','ls-tree','-r','-z',pin]).decode().split('\0')
mine={}
for r in rows:
    if not r: continue
    meta,path=r.split('\t',1);mode,typ,sha=meta.split()
    if typ!='blob' or mode=='120000': continue
    if any(x.match(path) for x in EX): continue
    cls='seed' if any(x.match(path) for x in SE) else 'managed'
    blob=subprocess.check_output(['git','cat-file','blob',sha])
    mine[path]=(cls,hashlib.sha256(blob).hexdigest())
theirs={f['path']:(f['class'],f['sha256']) for f in rec['files']}
print('pin',pin);print('ls-tree files',len(mine),'managed',sum(1 for v in mine.values() if v[0]=='managed'),'seed',sum(1 for v in mine.values() if v[0]=='seed'))
print('record files',len(theirs),'managed',sum(1 for v in theirs.values() if v[0]=='managed'),'seed',sum(1 for v in theirs.values() if v[0]=='seed'))
print('only in ls-tree',sorted(set(mine)-set(theirs))[:5],'| only in record',sorted(set(theirs)-set(mine))[:5])
print('class or sha256 differs',[p for p in mine if p in theirs and mine[p]!=theirs[p]][:5])
sk=sorted({p.split('/')[2] for p in mine if p.startswith('.claude/skills/') and p.count('/')>=3 and p.endswith('SKILL.md')})
print('skills',len(sk),'record skills',len(rec['skills']),'equal',sk==sorted(rec['skills']))
print('RESULT','MATCH' if mine==theirs and sk==sorted(rec['skills']) else 'DIFFERENT')
