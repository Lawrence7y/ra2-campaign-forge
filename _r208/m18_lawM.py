# -*- coding: utf-8 -*-
"""R208 m18（定稿）：律 M —— 额外视图 vftable 数组的三形态与生成键。
三形态：
  T（调整 thunk）：slot0 = sub dword ptr [esp+4], m ; jmp T，T == 本类主视图 slot0
  S（共享静态表）：数组在同类键 (m, 基类 pTD 名) 内跨类逐字节相同
  I（类自实现）  ：类重写了该接口 ⇒ 函数体内做 this 调整（lea reg,[reg-m]），数组逐类唯一
生成键：
  T 形态：数组 == f(m, T)（同一 T 且同一 m ⇒ 同一数组）
  S 形态：数组 == g(m, 基类 pTD 名)
  I 形态：数组 == 类自身代码（逐类唯一）
正控：三键逐条计分；反控：T 键去掉 T（只按 m）、S 键去掉 pTD（只按 m）
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
emb={a:a+16 for a in CHD}
extras=[c for c in COL if c!=emb[COL[c]['pCHD']]]
kind={}; kT={}; kS={}
for c in extras:
    a=adj(A[c][0])
    if a: kind[c]='T'; kT[c]=(COL[c]['mdisp'],a[1].lower())
    else:
        H=COL[c]['pCHD']; m=COL[c]['mdisp']
        shared=sum(1 for d in extras if d!=c and A[d]==A[c])
        kind[c]='S' if shared else 'I'
        kS[c]=(m,tuple(sorted(tn(R[b]['pTD']) for b in BCA[H] if R[b]['m']==m)))
print('== A 三形态计数 ==')
print('  T %d / S %d / I %d 合计 %d' % (sum(1 for c in kind if kind[c]=='T'),
      sum(1 for c in kind if kind[c]=='S'),sum(1 for c in kind if kind[c]=='I'),len(kind)))
ck('A.1 T+S+I == 260', len(kind)==260, len(kind))
ck('A.2 I 恰 3 条', sum(1 for c in kind if kind[c]=='I')==3, [COL[c]['name'] for c in kind if kind[c]=='I'])
print('== B 键函数据判别力 ==')
def impure(keys):
    g=collections.defaultdict(set)
    for c,k in keys.items(): g[k].add(A[c])
    return sum(1 for k,v in g.items() if len(v)>1), len(g)
t_imp,t_g=impure(kT); s_imp,s_g=impure(kS)
print('  T 键 (m, T)：%d 组，组内多数组 %d 组' % (t_g,t_imp))
print('  S 键 (m, 基类pTD)：%d 组，组内多数组 %d 组' % (s_g,s_imp))
ck('B.1 T 键在 T 形态内纯（组内数组唯一）', t_imp==0, (t_imp,t_g))
ck('B.2 S 键在 S 形态内纯（组内数组唯一）', s_imp==0, (s_imp,s_g))
# 反控
g1=collections.defaultdict(set)
for c,k in kT.items(): g1[k[0]].add(A[c])
g2=collections.defaultdict(set)
for c,k in kS.items(): g2[k[0]].add(A[c])
i1=sum(1 for k,v in g1.items() if len(v)>1); i2=sum(1 for k,v in g2.items() if len(v)>1)
print('  反控 T 只按 m：%d 组，多数组 %d 组' % (len(g1),i1))
print('  反控 S 只按 m：%d 组，多数组 %d 组' % (len(g2),i2))
ck('B.3 反控两档均劣于全键', i1>0 and i2>0, (i1,i2))
print('== C S 形态的组明细 ==')
for k,cl in sorted(collections.defaultdict(list,{k:[c for c in kS if kS[c]==k] for k in set(kS.values())}).items(),key=lambda kv:-len(kv[1])):
    if len(cl)>=2:
        print('  mdisp=%-6d 基类 %-24s 条数 %-3d slot0=0x%x 长度 %d' %
              (k[0],','.join(k[1])[:22],len(cl),A[cl[0]][0],len(A[cl[0]])))
print('== D I 形态三条 ==')
for c in [x for x in kind if kind[x]=='I']:
    raw=P.RAW[P.r2o(A[c][0]):P.r2o(A[c][0])+400]
    ins=list(md.disasm(raw,A[c][0]))
    hits=[('%s %s'%(i.mnemonic,i.op_str),hex(i.address)) for i in ins if '- 8' in i.op_str or '- 0x8' in i.op_str]
    print('  0x%x %-30s 指令 %d 条，-8 调整 %s' % (c,COL[c]['name'],len(ins),hits[:3]))
json.dump(dict(T=sum(1 for c in kind if kind[c]=='T'),S=sum(1 for c in kind if kind[c]=='S'),
               I=sum(1 for c in kind if kind[c]=='I'),tGroups=t_g,tImpure=t_imp,sGroups=s_g,sImpure=s_imp,
               ctrl_m_only_T=i1,ctrl_m_only_S=i2,asserts=NA,fails=fails),
          open('_r208/m18_lawM.json','w'),ensure_ascii=False,indent=1)
print('== 断言 %d / FAIL %d =='%(NA,len(fails)),fails)
