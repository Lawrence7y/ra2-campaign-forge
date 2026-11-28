# -*- coding: utf-8 -*-
"""R208 m17（定稿律 m）：额外视图 vftable 的两种生成方式与判别律。
L_m1：额外视图 vftable 的 slot0 若为 this 调整 thunk（sub [esp+4], mdisp ; jmp T），则该数组**逐类唯一**，
      且 T == 本类主视图 slot0（101/101 已测）。
L_m2：若不是 thunk，则数组在该 (mdisp, 基类 pTD) 内**跨类逐字节相同**（共享静态数组）。
L_m3：例外只有一种：类自己真实现了该接口 ⇒ 编译器把 this 调整内联进函数体（lea esi,[edi-8]），
      既无 thunk 也不共享。实测 AircraftClass / InfantryClass / UnitClass 三条。
正控：三律逐条计分
反控：把 thunk 判据换成「slot0 在 0x410xxx 区间」这种粗判据，看判别力崩坏
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
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
R={b:dict(pTD=P.dw(b),m=s32(P.dw(b+8))) for b in phys}
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
def hasinline(a,n=96):
    """函数体内是否有 lea reg,[reg-imm] 形式的 this 调整"""
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+n],a))
    for i in ins:
        if i.mnemonic=='lea' and '- ' in i.op_str and 'esp' not in i.op_str: return i.op_str
    return None
emb={a:a+16 for a in CHD}
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
def key(c):
    H=COL[c]['pCHD']; m=COL[c]['mdisp']
    return (m,tuple(sorted(tn(R[b]['pTD']) for b in BCA[H] if R[b]['m']==m)))
K=collections.defaultdict(list)
for c in extras: K[key(c)].append(c)
print('== L_m1 thunk ⇒ 数组逐类唯一，且 T == 本类主视图 slot0 ==')
thk=[c for c in extras if adj(A[c][0])]
dupin=[c for c in thk if sum(1 for d in extras if A[d]==A[c])>1]
okT=sum(1 for c in thk if adj(A[c][0])[1].lower()==hex(A[emb[COL[c]['pCHD']]][0]).lower())
print('  thunk 数 %d；其中数组与他类重复 %d；T==主视图 slot0 %d/%d' % (len(thk),len(dupin),okT,len(thk)))
ck('L_m1.1 thunk 共 %d 条，无一条数组跨类重复' % len(thk), len(dupin)==0, len(dupin))
ck('L_m1.2 thunk 目标恒 == 本类主视图 slot0（%d/%d）' % (okT,len(thk)), okT==len(thk), okT)
ck('L_m1.3 thunk 立即数恒 == COL.mdisp', all(adj(A[c][0])[0]==COL[c]['mdisp'] for c in thk),
   [(hex(c),adj(A[c][0])[0],COL[c]['mdisp']) for c in thk if adj(A[c][0])[0]!=COL[c]['mdisp']][:5])
print('== L_m2 非 thunk ⇒ 数组在 (mdisp,基类pTD) 内共享 ==')
nth=[c for c in extras if not adj(A[c][0])]
sh=[c for c in nth if sum(1 for d in extras if A[d]==A[c])>1]
print('  非 thunk %d 条；数组有同伴（>=2 条共享）%d 条；无同伴 %d 条' % (len(nth),len(sh),len(nth)-len(sh)))
ck('L_m2.1 非 thunk 中 %d 条共享，例外仅 3 条' % (len(sh)), len(nth)-len(sh)==3, len(nth)-len(sh))
resid=[c for c in nth if c not in sh]
for c in resid:
    print('   例外 0x%x %-30s mdisp=%d 内联调整=%s' % (c,COL[c]['name'],COL[c]['mdisp'],hasinline(A[c][0])))
ck('L_m2.2 3 条例外的 slot0 函数体内含 lea reg,[reg-imm] 内联 this 调整',
   all(hasinline(A[c][0]) for c in resid), [hasinline(A[c][0]) for c in resid])
print('== L_m2 细化：共享组内是否有多个不同数组（同键不同数组）==')
multi=[(k,cl) for k,cl in K.items() if len({A[c] for c in cl})>1]
print('  同键多数组的组数 %d' % len(multi))
for k,cl in multi:
    arrs=collections.Counter(A[c] for c in cl)
    print('   键 %s mdisp=%d 条数 %d 数组数 %d；thunk %d/%d；数组规模 %s' %
          (','.join(k[1])[:44],k[0],len(cl),len(arrs),sum(1 for c in cl if adj(A[c][0])),len(cl),
           sorted({len(a) for a in arrs})))
ck('L_m2.3 同键内多数组的组，其成员全部是 thunk 类（数组唯一性来自每类自己的 dtor）',
   all(all(adj(A[c][0]) for c in cl) for k,cl in multi), [(k[0],sum(1 for c in cl if adj(A[c][0])),len(cl)) for k,cl in multi])
print('== 反控 ==')
coarse=[c for c in extras if 0x410000<=A[c][0]<0x411000]
print('  粗判据「slot0 在 0x410xxx」命中 %d 条（真 thunk %d 条）；其中非 thunk 的 %d 条' %
      (len(coarse),len(thk),sum(1 for c in coarse if not adj(A[c][0]))))
ck('反控.1 粗判据与 thunk 判据不等价', len(coarse)!=len(thk), (len(coarse),len(thk)))
print('== 汇总 ==')
summary=dict(extras=len(extras),thunk=len(thk),nothunk=len(nth),shared=len(sh),resid=len(resid),
             groups=len(K),multiArrGroups=len(multi),asserts=NA,fails=fails)
print(summary)
json.dump(summary,open('_r208/m17_final.json','w'),ensure_ascii=False,indent=1)
