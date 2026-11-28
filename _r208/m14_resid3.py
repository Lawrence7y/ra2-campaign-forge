# -*- coding: utf-8 -*-
"""R208 m14：3 条残留（Aircraft/Infantry/Unit mdisp=8, slot0 是真函数体）定性。
核验：①其 slot0 是否 == 本类主视图 slot0；②函数体内是否有 ecx/esi 上的 -8 调整；
③与 75 条共享桩的差别是否恰为 slot0；④该 3 类的 mdisp=8 基类 pTD。
"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
phys=sorted({x for a in CHD for x in BCA[a]})
def tn(t):
    n=P.cstr(t+8,300); return n.decode('latin1') if n else '?'
R={b:dict(pTD=P.dw(b),nc=P.dw(b+4),m=s32(P.dw(b+8)),attr=P.dw(b+20)) for b in phys}
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
A={c:tuple(P.dw(vt[c]+4*k) for k in range(vlen(vt[c]))) for c in vt}
emb={a:a+16 for a in CHD}
targets=[c for c in COL if COL[c]['mdisp']==8 and c!=emb[COL[c]['pCHD']] and len(A[c])==1 and A[c][0] not in (0x410580,)]
md=Cs(CS_ARCH_X86,CS_MODE_32)
print('目标 %d 条' % len(targets))
for c in targets:
    H=COL[c]['pCHD']; prim=emb[H]
    raw=P.RAW[P.r2o(A[c][0]):P.r2o(A[c][0])+96]
    ins=list(md.disasm(raw,A[c][0]))[:20]
    txt=[('%s %s'%(i.mnemonic,i.op_str)) for i in ins]
    pt={R[b]['pTD'] for b in BCA[H] if R[b]['m']==8}
    print('  0x%x %-30s slot0=0x%x  主视图slot0=0x%x  相同?%s' %
          (c,COL[c]['name'],A[c][0],A[prim][0],A[c][0]==A[prim][0]))
    print('     mdisp=8 基类 pTD: %s' % [tn(t) for t in pt])
    print('     前 20 条: %s' % '; '.join(txt))
    adj8=[t for t in txt if ('- 8' in t or '+ 8' in t) and 'ecx' in t]
    print('     含 ecx±8 调整的指令: %s' % adj8)
    print('     字节 %s' % raw[:32].hex())
print('== 75 条共享桩组的 mdisp=8 基类 pTD ==')
stub=[c for c in COL if COL[c]['mdisp']==8 and c!=emb[COL[c]['pCHD']] and len(A[c])==1 and A[c][0]==0x410580]
ptdset=set()
for c in stub:
    H=COL[c]['pCHD']
    ptdset|={tn(R[b]['pTD']) for b in BCA[H] if R[b]['m']==8}
print('  桩组 %d 条，其 mdisp=8 的基类 pTD 集合 %s' % (len(stub),sorted(ptdset)))
print('== 3 条残留类的 mdisp=8 pTD 集合 vs 桩组 ==')
for c in targets:
    H=COL[c]['pCHD']
    print('  %-30s %s  在桩组集合中? %s' % (COL[c]['name'],
        [tn(R[b]['pTD']) for b in BCA[H] if R[b]['m']==8],
        any(tn(R[b]['pTD']) in ptdset for b in BCA[H] if R[b]['m']==8)))
