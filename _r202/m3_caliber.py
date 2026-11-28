#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m3：口径与函数网格的对齐度定量 + 三种函数归属口径下重算 697 条装表三分类。
F1 697 复现（含 11 条 mdisp==0）与 686/11 二分；
F2 6,719 个去重 CALLAT 目标中有多少是指令起点 / 区间起点 —— 反汇编失同步 vs 区间合并的定量；
F3 候选入口网格 E = CALLAT目标 ∪ 序言位 ∪ ret/int3 之后的区间起点；
F4 四种归属口径的三分类 + 未归属；
F5 反控。"""
import sys, struct, json, bisect, collections, statistics
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MD={vt:COL[VT[vt]]['mdisp'] for vt in VT}
CLS={vt:COL[VT[vt]]['name'] for vt in VT}

def extract():
    rec=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-4:
        if RAW[pos]==0x66:
            if pos+2<end and RAW[pos+1]==0xC7:
                mo=RAW[pos+2]>>6; pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
            pos+=1; continue
        if RAW[pos]!=0xC7: pos+=1; continue
        modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1; continue
        va=LO+(pos-T['rawptr'])
        if mod==1:
            d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
            rec.append((va,rm,d,im)); pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
            rec.append((va,rm,d,im)); pos+=10
        else:
            im=struct.unpack_from('<I',RAW,pos+2)[0]; rec.append((va,rm,0,im)); pos+=6
    return rec
allsite=extract()
vts=[r for r in allsite if r[3] in VT]
mainall=[r for r in vts if MD[r[3]]==0]
sub=[r for r in vts if 1<=r[2]<=9]          # 697，含 11 条 mdisp==0
ck('F1a 小位移（1..9）装 VT store == 697', len(sub)==697, len(sub))
G1=[r for r in sub if MD[r[3]]!=0]; G2=[r for r in sub if MD[r[3]]==0]
ck('F1b 697 = 686 次表 + 11 主表', (len(G1),len(G2))==(686,11), (len(G1),len(G2)))
ck('F1c 686 的 disp8==mdisp 全等', all(r[2]==MD[r[3]] for r in G1), sum(1 for r in G1 if r[2]==MD[r[3]]))
ck('F1d 686 的 mdisp 分布 4:345/8:341', collections.Counter(MD[r[3]] for r in G1)==collections.Counter({4:345,8:341}),
   dict(collections.Counter(MD[r[3]] for r in G1)))
ck('F1e 11 条的 disp8 只 {4,8}', set(r[2] for r in G2)=={4,8}, sorted(set(r[2] for r in G2)))
print('   F1: 697 = 686(mdisp 4/8) + 11(mdisp 0)；11 条地址 %s'%[hex(r[0]) for r in G2])

# ---------- 反汇编 ----------
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[];CALLAT=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op))
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t))
        p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]; ASET=set(ADDRS); I2R={a:i for i,a in enumerate(ADDRS)}
SORT=sorted(set(t for _,t in CALLAT)); TGT=set(SORT)
REGION=[];st=LO;nb=0;ENDRET=[]
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); ENDRET.append(mn.startswith('ret')); st=a+sz; nb+=1
if st<HI: REGION.append((st,HI)); ENDRET.append(False)
RL=[r[0] for r in REGION]; RSET=set(RL)
ck('F2a 区间数 31968', len(REGION)==31968, len(REGION))

# F2 对齐度
tgt_insstart=sum(1 for t in SORT if t in ASET)
tgt_regstart=sum(1 for t in SORT if t in RSET)
ck('F2b CALLAT 目标落在指令起点的比例 > 90%', tgt_insstart/len(SORT)>0.90,
   '%d/%d=%.1f%%'%(tgt_insstart,len(SORT),100.0*tgt_insstart/len(SORT)))
ck('F2c CALLAT 目标落在区间起点的比例 < 20%', tgt_regstart/len(SORT)<0.20,
   '%d/%d=%.1f%%'%(tgt_regstart,len(SORT),100.0*tgt_regstart/len(SORT)))
print('   F2: 去重 CALLAT 目标 %d；指令起点 %d(%.1f%%)；区间起点 %d(%.1f%%)'%(
    len(SORT),tgt_insstart,100.0*tgt_insstart/len(SORT),tgt_regstart,100.0*tgt_regstart/len(SORT)))
# 区间长度分布 / 区间内有几个 CALLAT 目标（合并证据）
cnt_in=collections.Counter()
for (a,b) in REGION:
    k=bisect.bisect_left(SORT,b)-bisect.bisect_left(SORT,a)
    cnt_in[k]+=1
ck('F2d 区间内含 >1 个 CALLAT 目标的区间数 > 0', sum(v for k,v in cnt_in.items() if k>1)>0,
   dict(sorted(cnt_in.items())[:6]))
mlen=sorted(b-a for a,b in REGION)
print('   F2: 区间长度 p50=%d p90=%d max=%d；含 0/1/2/3+ 目标 %d/%d/%d/%d'%(mlen[len(mlen)//2],mlen[int(len(mlen)*.9)],mlen[-1],
   cnt_in[0],cnt_in[1],cnt_in[2],sum(v for k,v in cnt_in.items() if k>=3)))

# F3 候选入口网格
def has_prologue(a):
    i=I2R.get(a)
    if i is None: return False
    w=INS[i:i+4]
    if not w: return False
    m=[x[2] for x in w]; op=[x[3].replace(' ','') for x in w]
    for k in range(min(3,len(m)-1)):
        if m[k]=='push' and op[k]=='ebp' and m[k+1]=='mov' and op[k+1]=='ebp,esp': return True
        if m[k]=='mov' and op[k]=='edi,edi':
            for j in range(k+1,min(k+3,len(m)-1)):
                if m[j]=='push' and op[j]=='ebp' and m[j+1]=='mov' and op[j+1]=='ebp,esp': return True
    if m[0]=='sub' and op[0].startswith('esp,'): return True
    if m[0]=='push' and op[0] in ('ebx','esi','edi','ecx','edx','eax','ebp'): return True
    return False
prol=set(a for a in RL if has_prologue(a))
PROL=set(); 
for a in ADDRS:
    if has_prologue(a): PROL.add(a)
ck('F3a 序言位（全指令起点扫）> 0', len(PROL)>0, len(PROL))
ck('F3b 序言位中区间起点 == 序言位全集（区间起点必在指令起点集内）', prol==PROL, (len(prol),len(PROL)))
E=set(SORT)|PROL
ck('F3c 候选入口网格 |E| 在 1000..15000', 1000<len(E)<15000, len(E))
EL=sorted(E)
print('   F3: |E|=%d (CALLAT %d / 序言 %d / 交集 %d)'%(len(E),len(SORT),len(PROL),len(set(SORT)&PROL)))

# F4 归属口径
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
def seg_of(va):
    i=bisect.bisect_right(EL,va)-1
    if i<0: return None
    j=bisect.bisect_right(EL,va)
    return (EL[i], EL[j] if j<len(EL) else HI)
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in vts: brs[reg_of(r[0])]+=1
def cls_reg(pred):
    c=collections.Counter()
    for r in sub:
        rg=reg_of(r[0])
        if rg is None: c['noreg']+=1; continue
        if not pred(rg): c['out']+=1; continue
        if brm[rg]>0 and brs[rg]>0: c['both']+=1
        elif brs[rg]>0: c['only_sub']+=1
        else: c['none']+=1
    return c
C_ALL=cls_reg(lambda rg: True)
ck('F4a 口径A（R201 原口径，全部区间）689/0/8', (C_ALL['both'],C_ALL['only_sub'],C_ALL['none'])==(689,0,8), dict(C_ALL))
C_CAL=cls_reg(lambda rg: rg[0] in TGT)
C_PRL=cls_reg(lambda rg: rg[0] in PROL)
C_E  =cls_reg(lambda rg: rg[0] in E)
for nm,c in [('B 区间起点∈CALLAT',C_CAL),('C 区间起点∈序言',C_PRL),('D 区间起点∈E',C_E)]:
    print('   F4 %-18s both=%-3d only_sub=%-3d none=%-2d out=%-4d'%(nm,c['both'],c['only_sub'],c['none'],c['out']))
    ck('F4x %s 五数相加==697'%nm, sum(c.values())==697, dict(c))
# 口径E：按 E 网格切段
brm2=collections.defaultdict(int); brs2=collections.defaultdict(int)
for r in mainall: brm2[seg_of(r[0])]+=1
for r in vts: brs2[seg_of(r[0])]+=1
cE=collections.Counter()
for r in sub:
    sg=seg_of(r[0])
    if sg is None: cE['noreg']+=1; continue
    if brm2[sg]>0 and brs2[sg]>0: cE['both']+=1
    elif brs2[sg]>0: cE['only_sub']+=1
    else: cE['none']+=1
ck('F4e 口径E（E 网格切段）五数相加==697', sum(cE.values())==697, dict(cE))
print('   F4 口径E(E 网格)     both=%-3d only_sub=%-3d none=%-2d'%(cE['both'],cE['only_sub'],cE['none']))
# 未落入任何真入口区间的那批 store 的分布
out=[r for r in sub if reg_of(r[0])[0] not in E]
ck('F4f 未落入 E 区间起点的 store 数 == 697-14', len(out)==697-14, len(out))
# F5 反控：错误网格（CALLAT 目标 +1 字节）
Ebad=sorted(set(t+1 for t in SORT)|PROL)
def seg_bad(va):
    i=bisect.bisect_right(Ebad,va)-1
    return None if i<0 else (Ebad[i],Ebad[i+1] if i+1<len(Ebad) else HI)
brmb=collections.defaultdict(int); brsb=collections.defaultdict(int)
for r in mainall: brmb[seg_bad(r[0])]+=1
for r in vts: brsb[seg_bad(r[0])]+=1
cb=collections.Counter()
for r in sub:
    sg=seg_bad(r[0])
    if sg is None: cb['noreg']+=1; continue
    if brmb[sg]>0 and brsb[sg]>0: cb['both']+=1
    elif brsb[sg]>0: cb['only_sub']+=1
    else: cb['none']+=1
ck('F5a 错误网格结果与正确网格不同', (cb['both'],cb['only_sub'],cb['none'])!=(cE['both'],cE['only_sub'],cE['none']), dict(cb))
print('   F5 错误网格(+1B) both=%d only_sub=%d none=%d'%(cb['both'],cb['only_sub'],cb['none']))
OUT=dict(n697=len(sub),n686=len(G1),n11=len(G2),g2=[hex(r[0]) for r in G2],
  tgt=len(SORT),tgt_ins=tgt_insstart,tgt_reg=tgt_regstart,
  prolog=len(PROL),E=len(E),Einter=len(set(SORT)&PROL),
  A=dict(C_ALL),B=dict(C_CAL),C=dict(C_PRL),D=dict(C_E),E_seg=dict(cE),bad=dict(cb),
  reglen=dict(p50=mlen[len(mlen)//2],p90=mlen[int(len(mlen)*.9)],max=mlen[-1]),
  cnt_in={str(k):v for k,v in cnt_in.items()},asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m3_caliber.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
