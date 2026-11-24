import sys,re,collections,json
ROOT='/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0,ROOT+'/_r119')
from _pe119 import PE_, BUF
import capstone
T=PE_.sec_by_name('.text')
MD=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=False; MD.skipdata=True
IAT=json.load(open(ROOT+'/_r119/iat_names.json')); IATV={int(k,16):v[1] for k,v in IAT.items()}
def stream(st,n):
    o=PE_.va2off(st); return list(MD.disasm_lite(BUF[o:o+n],st))
def clean_to(cand, site, maxn=0x4000):
    seq=stream(cand,min(maxn, site-cand+0x60))
    seen=False
    for (a,sz,mn,ops) in seq:
        if mn=='.byte': return None
        if a==site: return seq
    return None
def valid_start(site, back=0x1200):
    lo=max(T['va'],site-back)
    o=PE_.va2off(lo); e=PE_.va2off(site)
    blob=BUF[o:e]
    cands=[]
    i=0
    while True:
        i=blob.find(b'\xcc\xcc',i)
        if i<0: break
        j=i
        while j<len(blob) and blob[j]==0xcc: j+=1
        cands.append(lo+j); i=j
    for c in reversed(cands):
        r=clean_to(c,site)
        if r: return c,r
    return None,None
S=[]
for off in range(0,T['vsize'],65536):
    blob=BUF[T['raw']+off:T['raw']+min(off+65536,T['vsize'])]
    for (a,sz,mn,ops) in MD.disasm_lite(blob,T['va']+off):
        if mn=='push' and ops.startswith('0x'):
            try:
                if int(ops,16)==0x7f7c80: S.append(a)
            except ValueError: pass
print('sites',len(S))
c=collections.Counter()
out=[]
for s in S:
    st,seq=valid_start(s)
    c[st]+=1
    out.append({'site':hex(s),'start':hex(st) if st else None})
for k,v in c.most_common(): print(' func',hex(k) if k else None,v)
json.dump(out,open(ROOT+'/_r121/_proto4_starts.json','w'),ensure_ascii=False,indent=1)
