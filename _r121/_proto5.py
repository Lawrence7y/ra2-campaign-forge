import sys,re,collections,json
ROOT='/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0,ROOT+'/_r119')
from _pe119 import PE_, BUF
import capstone
T=PE_.sec_by_name('.text')
MD=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=False; MD.skipdata=True
IAT=json.load(open(ROOT+'/_r119/iat_names.json')); IATV={int(k,16):v[1] for k,v in IAT.items()}
def sites(t):
    out=[]
    for off in range(0,T['vsize'],65536):
        blob=BUF[T['raw']+off:T['raw']+min(off+65536,T['vsize'])]
        for (a,sz,mn,ops) in MD.disasm_lite(blob,T['va']+off):
            if mn=='push' and ops.startswith('0x'):
                try:
                    if int(ops,16)==t: out.append(a)
                except ValueError: pass
    return out
def stream(st,n):
    o=PE_.va2off(st); return list(MD.disasm_lite(BUF[o:o+n],st))
def find_start(site, back=0x1000):
    """backward-scan candidates = byte after each ret(0xc3)/ret imm(0xc2 xx xx)/padding run; accept the
    nearest whose forward linear decode reaches `site` exactly with no .byte."""
    lo=max(T['va'],site-back); o=PE_.va2off(lo); e=PE_.va2off(site)
    blob=BUF[o:e]
    cands=set()
    for i,ch in enumerate(blob):
        if ch==0xC3: cands.add(lo+i+1)
        if ch==0xC2: cands.add(lo+i+3)
    # skip padding
    out=[]
    for c in sorted(cands, reverse=True):
        # skip leading nops/int3
        cc=c
        while True:
            oc=PE_.va2off(cc)
            if BUF[oc] in (0x90,0xCC): cc+=1
            else: break
        if cc>=site: continue
        seq=stream(cc, site-cc+0x90)
        ok=False
        for (a,sz,mn,ops) in seq:
            if mn=='.byte': ok=False; break
            if a==site: ok=True; break
        if ok: out.append(cc)
        if len(out)>=3: break
    return out
S=sites(0x7f7c80)
res=[]
c=collections.Counter()
for s in S:
    cs=find_start(s)
    res.append({'site':hex(s),'cands':[hex(x) for x in cs]})
    c[len(cs)]+=1
print('n sites',len(S),'cand-count dist',dict(c))
print('first 6', [ (r['site'],r['cands']) for r in res[:6]])
print('unanimous?', all(len(r['cands'])==1 for r in res))
json.dump(res,open(ROOT+'/_r121/_proto5_starts.json','w'),indent=1)
