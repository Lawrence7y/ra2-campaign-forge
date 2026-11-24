import os, hashlib
ROOT=r'D:\Project\ra2-campaign-forge'
def L(rel):
    return open(os.path.join(ROOT,rel.replace('/',os.sep)),'rb').read().decode('utf-8').split('\n')
def block(rel,a,b):
    ls=L(rel)
    return '\n'.join(ls[a-1:b])
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

# candidate §607 blocks
cands={
 'LEDGER_APPENDIX_DRAFT.md:111-124':'lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md',
 '_la_draft3:13-26':'lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md',
}
print('=== §607 block hashes ===')
for name,rel in cands.items():
    a,b=(111,124) if 'LEDGER' in name else (13,26)
    s=block(rel,a,b)
    print(name,'chars=',len(s),'sha256=',sha(s))
    print('  first:',s.split('\n')[0][:120])
    print('  last :',s.split('\n')[-1][:120])
print()
# find §607 heading & next heading in bound volumes to define block
for rel in ['lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md','lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md','lead/ledger_bound_20261109/_lb2_TEMPLATE.md']:
    ls=L(rel)
    h607=None; h608=None; h609=None
    for i,l in enumerate(ls,1):
        if l.startswith('## §607'): h607=i
        if l.startswith('## §608'): h608=i
        if l.startswith('## §609'): h609=i
    print('####',rel,'§607@',h607,'§608@',h608,'§609@',h609)
    if h607:
        for i in range(h607,min(h607+16,len(ls)+1)):
            print(f'  :{i}: '+ls[i-1][:200])
    print()

# exact sentence match counts across whole repo (md)
target=L('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md')[122]
print('=== repo-wide exact-match count of §607 boundary sentence ===')
print('TARGET:',target)
hits=[]
for dp,dn,fns in os.walk(os.path.join(ROOT,'lead')):
    for f in fns:
        if not f.endswith('.md'): continue
        p=os.path.join(dp,f)
        try: ls=open(p,'r',encoding='utf-8',errors='replace').read().split('\n')
        except: continue
        for i,l in enumerate(ls,1):
            if l==target: hits.append((os.path.relpath(p,ROOT).replace(os.sep,'/'),i))
for h in hits: print(' ',h[0]+':'+str(h[1]))
print('TOTAL=',len(hits))
print()
# §6.3 未验项 sentence (:215) repo-wide
t215=L('lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md')[214]
print('=== repo-wide exact-match count of §6.3 item3 sentence (LEDGER:215) ===')
print('TARGET:',t215)
hits2=[]
for dp,dn,fns in os.walk(os.path.join(ROOT,'lead')):
    for f in fns:
        if not f.endswith('.md'): continue
        p=os.path.join(dp,f)
        try: ls=open(p,'r',encoding='utf-8',errors='replace').read().split('\n')
        except: continue
        for i,l in enumerate(ls,1):
            if l==t215: hits2.append((os.path.relpath(p,ROOT).replace(os.sep,'/'),i))
for h in hits2: print(' ',h[0]+':'+str(h[1]))
print('TOTAL=',len(hits2))
