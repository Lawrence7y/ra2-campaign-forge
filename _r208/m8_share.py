# -*- coding: utf-8 -*-
"""R208 m8（决定性）：额外视图 vftable 的两种形态判定。
H_a：slot0 是 this 调整 thunk（sub [esp+4], mdisp ; jmp T），T == 本类主视图 slot0。
H_b：slot0 不是调整 thunk ⇒ 该额外视图 vftable 是某个已有 vftable 的**整数组重复**（基类共享，无需 thunk）。
正控：1214 张 vftable 数组的两两相等分组
反控：把「整数组相等」随机化（随机抽同尺寸数组比较）
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
print('vftable %d 槽 %d' % (len(A),sum(len(x) for x in A.values())))
# 数组相等分组
groups=collections.defaultdict(list)
for c,a in A.items(): groups[a].append(c)
dup=[(a,cl) for a,cl in groups.items() if len(cl)>1]
print('== A 整数组相等的组数 %d，涉及 COL %d 条' % (len(dup),sum(len(cl) for _,cl in dup)))
print('   组规模分布 %s' % collections.Counter(len(cl) for _,cl in dup).most_common())
md=Cs(CS_ARCH_X86,CS_MODE_32)
def adj(a):
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+40],a))[:3] if o else []
    if len(ins)<2: return None
    i0,i1=ins[0],ins[1]
    op=i0.op_str.replace(' ','')
    if i0.mnemonic not in ('sub','add') or not op.startswith('dwordptr[esp+4],'): return None
    if i1.mnemonic!='jmp': return None
    try: imm=int(op.split(',')[-1],16)
    except Exception: return None
    return (i0.mnemonic,imm,i1.op_str.strip())
emb={a:a+16 for a in CHD}
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
thk=[c for c in extras if adj(A[c][0])]
nth=[c for c in extras if not adj(A[c][0])]
print('== B 额外视图 %d：slot0 是 thunk %d / 非 thunk %d' % (len(extras),len(thk),len(nth)))
# H_b：非 thunk 的是否整数组重复
inDup={c for _,cl in dup for c in cl}
okB=sum(1 for c in nth if c in inDup)
print('   非 thunk 中整数组重复 %d/%d' % (okB,len(nth)))
# 与之重复的对象里，是否有 mdisp==0 的主视图
okB2=0; ex=[]
for c in nth:
    mates=[m for m in groups[A[c]] if m!=c]
    prim=[m for m in mates if COL[m]['mdisp']==0]
    if prim: okB2+=1
    elif len(ex)<6: ex.append((hex(c),COL[c]['mdisp'],[COL[m]['name']+'|'+str(COL[m]['mdisp']) for m in mates][:3]))
print('   其中存在 mdisp==0 主视图同数组者 %d/%d' % (okB2,len(nth)))
print('   反例(非 thunk 且无主视图同伴) 前 6: %s' % ex)
# 反控：随机配对同长度数组
import random; random.seed(208)
same=0;tot=0
for _ in range(400):
    a,b=random.sample(list(A),2)
    if len(A[a])==len(A[b]):
        tot+=1; same+= (A[a]==A[b])
print('== C 反控 随机同长数组对相等数 %d/%d' % (same,tot))
# H_a：thunk 目标 == 本类主视图 slot0?
okA=0; tgtMiss=[]
for c in thk:
    m,imm,T=adj(A[c][0])
    prim=emb[COL[c]['pCHD']]
    if T.lower()==hex(A[prim][0]).lower(): okA+=1
    else: tgtMiss.append((hex(c),COL[c]['name'],m,imm,T,hex(A[prim][0])))
print('== D thunk 目标 == 本类主视图 slot0 的 %d/%d' % (okA,len(thk)))
for x in tgtMiss[:8]: print('   miss',x)
# thunk 立即数 == COL.mdisp ?
okImm=sum(1 for c in thk if adj(A[c][0])[1]==COL[c]['mdisp'])
print('== E thunk 立即数 == COL.mdisp 的 %d/%d（符号考虑：add 形式为负）' % (okImm,len(thk)))
print('== F 其余 mdisp 分布（thunk 组 / 非 thunk 组）==')
print('   thunk mdisp %s' % collections.Counter(COL[c]['mdisp'] for c in thk).most_common())
print('   非 thunk mdisp %s' % collections.Counter(COL[c]['mdisp'] for c in nth).most_common())
json.dump(dict(extra=len(extras),thunk=len(thk),nothunk=len(nth),dupGroups=len(dup),
               dupCols=sum(len(cl) for _,cl in dup),okB=okB,okB2=okB2,okA=okA,okImm=okImm,
               ctrl=[same,tot],
               tgtMiss=tgtMiss[:10],
               ex=[[x[0],x[1],x[2]] for x in ex]),
          open('_r208/m8_share.json','w'),ensure_ascii=False,indent=1)
