# -*- coding: utf-8 -*-
"""R208 m9：159 条「非 thunk 额外视图」的数组来源判定（H_c：== 该 mdisp 上基类 pTD 的主视图 vftable）。
正控：逐条按 BCA 找 mdisp 对应的 BCD.pTD，再找该 pTD 的主视图 COL，比数组
反控：(a) 与同类其它 mdisp 的基类主视图比；(b) 与随机 COL 的数组比
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
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
REC={b:(P.dw(b),P.dw(b+4),s32(P.dw(b+8)),s32(P.dw(b+12)),s32(P.dw(b+16)),P.dw(b+20))
     for a in CHD for b in BCA[a]}
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
    try: return (i0.mnemonic,int(op.split(',')[-1],16),i1.op_str.strip())
    except Exception: return None
emb={a:a+16 for a in CHD}
# pTD -> primary COL (mdisp==0)
p2primary={}
for c,v in COL.items():
    if v['mdisp']==0: p2primary.setdefault(v['pTD'],c)
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
nth=[c for c in extras if not adj(A[c][0])]
print('非 thunk 额外视图 %d' % len(nth))
okc=0; miss=[]
for c in nth:
    H=COL[c]['pCHD']; m=COL[c]['mdisp']
    pt=[REC[b][0] for b in BCA[H] if REC[b][2]==m]
    done=False
    for t in set(pt):
        pc=p2primary.get(t)
        if pc is not None and A.get(pc)==A[c]:
            okc+=1; done=True; break
    if not done:
        miss.append((hex(c),COL[c]['name'],m,[P.cstr(t+8,120).decode('latin1') for t in set(pt)],
                     [hex(p2primary[t]) for t in set(pt) if t in p2primary],
                     [len(A[p2primary[t]]) if t in p2primary else None for t in set(pt)], len(A[c])))
print('== A 数组 == mdisp 对应基类 pTD 的主视图数组的 %d/%d' % (okc,len(nth)))
for x in miss[:10]: print('   miss',x)
print('== B 反控 ==')
import random; random.seed(208)
tot=ok=0
for c in nth:
    other=[p for t,p in p2primary.items() if t not in {REC[b][0] for b in BCA[COL[c]['pCHD']]}]
    if not other: continue
    p=random.choice(other); tot+=1; ok+=(A[p]==A[c])
print('   与随机非基类主视图数组相等 %d/%d' % (ok,tot))
# 分组明细
groups=collections.defaultdict(list)
for c,a in A.items(): groups[a].append(c)
dup=[(a,cl) for a,cl in groups.items() if len(cl)>1]
print('== C 重复组明细 ==')
for a,cl in sorted(dup,key=lambda x:-len(x[1])):
    print('   组 size %d：mdisp 集合 %s；COL 数 %d；数组长度 %d；slot0=0x%x' %
          (len(cl),collections.Counter(COL[c]['mdisp'] for c in cl).most_common(),len(cl),len(a),a[0] if a else 0))
    print('      成员前 6: %s' % [COL[c]['name'] for c in sorted(cl)[:6]])
    # 该数组是否等于任一 mdisp==0 COL 的数组
    prim=[c for c in COL if COL[c]['mdisp']==0 and A.get(c)==a]
    print('      等于某主视图数组? %s' % [hex(x) for x in prim][:3])
json.dump(dict(nothunk=len(nth),okBase=okc,miss=[[x[0],x[1],x[2],x[3],[str(y) for y in x[4]],x[5],x[6]] for x in miss[:12]],
               ctrl=[ok,tot],
               groups=[[len(cl),[[str(k),v] for k,v in collections.Counter(COL[c]['mdisp'] for c in cl).most_common()],
                        [hex(c) for c in sorted(cl)[:8]]] for a,cl in sorted(dup,key=lambda x:-len(x[1]))]),
          open('_r208/m9_base.json','w'),ensure_ascii=False,indent=1)
