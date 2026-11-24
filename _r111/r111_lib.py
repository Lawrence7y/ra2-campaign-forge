"""共享：全段指令起点 + ret + HB（r109e 同构造），带磁盘缓存。"""
import json, os, pickle
ROOT='/home/t628/projects/ra2-campaign-forge'
TS,TE,IB=0x401000,0x7e038d,0x400000
CACHE=os.path.join(ROOT,'_r111/bounds.pkl')
def build(raw):
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False; md.skipdata=True
    starts=[];rets=[];pos=TS
    while pos<TE:
        hi=min(pos+65536,TE)
        last=pos
        for a,sz,m,o in md.disasm_lite(raw[pos-IB:hi-IB+16],pos):
            if a>=hi: break
            last=a+sz; starts.append(a)
            if m.startswith('ret'): rets.append(a)
        if last<=pos: last=pos+1
        pos=last
    SSET=set(starts)
    def rsz(r):
        q=r-IB
        while raw[q] in (0x66,0x67,0xf2,0xf3,0x2e,0x3e,0x26,0x36,0x64,0x65): q+=1
        return (q-(r-IB))+(3 if raw[q] in (0xc2,0xca) else 1)
    HB=set()
    for r in sorted(rets):
        q=r+rsz(r); n=0
        while q<TE and raw[q-IB] in (0x90,0xcc) and n<64: q+=1; n+=1
        if n and q%4==0 and q in SSET: HB.add(q)
    return starts,rets,sorted(HB)
def get(raw):
    if os.path.exists(CACHE):
        d=pickle.load(open(CACHE,'rb'))
        return d['starts'],d['rets'],d['HB']
    s,r,h=build(raw)
    pickle.dump({'starts':s,'rets':r,'HB':h},open(CACHE,'wb'))
    return s,r,h
