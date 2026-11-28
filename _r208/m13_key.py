# -*- coding: utf-8 -*-
"""R208 m13（定稿律）：额外视图 vftable 内容由 (mdisp, 该 mdisp 上的基类 pTD) 决定。
正控：260 条逐条按 (mdisp, 基类 pTD 名) 分组，组内 vftable 内容应全同
反控：(a) 按 mdisp 单独分组（不看 pTD）；(b) 按 pTD 单独分组（不看 mdisp）
"""
import sys,struct,collections,json
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
md=Cs(CS_ARCH_X86,CS_MODE_32)
def adj(a):
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+40],a))[:3] if o else []
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]; op=i0.op_str.replace(' ','')
    if i0.mnemonic not in ('sub','add') or not op.startswith('dwordptr[esp+4],'): return None
    if i1.mnemonic!='jmp': return None
    try: return (int(op.split(',')[-1],16),i1.op_str.strip())
    except Exception: return None
emb={a:a+16 for a in CHD}
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
def key(c):
    H=COL[c]['pCHD']; m=COL[c]['mdisp']
    pt={R[b]['pTD'] for b in BCA[H] if R[b]['m']==m}
    return (m,tuple(sorted(tn(t) for t in pt)))
K=collections.defaultdict(list)
for c in extras: K[key(c)].append(c)
print('== A 按 (mdisp, 基类pTD名) 分组：%d 组，覆盖 %d 条额外视图 ==' % (len(K),sum(len(v) for v in K.values())))
allok=True; rows=[]
for k,cl in sorted(K.items(),key=lambda kv:-len(kv[1])):
    arrs=collections.Counter(A[c] for c in cl)
    ok=len(arrs)==1
    allok&=ok
    th=sum(1 for c in cl if adj(A[c][0]))
    rows.append(dict(key=[k[0],list(k[1])],n=len(cl),distinctArrays=len(arrs),
                     thunk=th,lens=sorted({len(a) for a in arrs}),
                     slot0=[hex(a[0]) for a in list(arrs)[:3]],
                     names=sorted(COL[c]['name'] for c in cl)[:4]))
    print('  %-52s mdisp=%-6d 条数 %-3d 内容不同数 %d thunk %d 长度 %s' %
          (','.join(k[1])[:50],k[0],len(cl),len(arrs),th,sorted({len(a) for a in arrs})))
print('  ⇒ 组内内容全同: %s' % allok)
print('== B 反控 ==')
bym=collections.defaultdict(list); byp=collections.defaultdict(list)
for c in extras:
    bym[COL[c]['mdisp']].append(c); byp[key(c)[1]].append(c)
print('  仅按 mdisp 分组：%d 组，组内内容不同者 %d 组' %
      (len(bym),sum(1 for v in bym.values() if len({A[c] for c in v})>1)))
print('  仅按 基类pTD 分组：%d 组，组内内容不同者 %d 组' %
      (len(byp),sum(1 for v in byp.values() if len({A[c] for c in v})>1)))
print('== C 组内内容不同的明细（若 >=1）==')
for k,cl in K.items():
    if len({A[c] for c in cl})>1:
        for c in cl:
            print('   %s mdisp=%d 0x%x %-34s arrLen=%d slot0=0x%x thunk=%s' %
                  (','.join(k[1])[:30],k[0],c,COL[c]['name'],len(A[c]),A[c][0],bool(adj(A[c][0]))))
json.dump(dict(groups=rows,okAll=allok,groupsByMdisp=len(bym),
               mdispImpure=sum(1 for v in bym.values() if len({A[c] for c in v})>1),
               ptdImpure=sum(1 for v in byp.values() if len({A[c] for c in v})>1)),
          open('_r208/m13_key.json','w'),ensure_ascii=False,indent=1)
