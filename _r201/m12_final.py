#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m12（最终定稿）：本轮四条结论的权威核算，断言方向与实测一致。
S1 R200 only_main 命名/判据不一致（代码级证据）
S2 R200 窗口跨函数污染（区间数分布）
S3 697 = 686 次表 + 11 主表（disp8 vs mdisp 二分）
S4 区间口径下 689/697 同区间双装，8/697 单装，0 个 only_sub —— 比 R200 宿主级更强
S5 主表装填面：8 代表类每类 4..6 处、分布 4..6 个区间
全部数字与 m1..m11 + 审计 A1..A8 对齐。"""
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
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
# --- R200 原口径（不含 mod0）---
recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
while pos<end-6:
    if RAW[pos]!=0xC7: pos+=1;continue
    modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
        recs.append((va,REGNAME[rm],d,im));pos+=7
    elif mod==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
        recs.append((va,REGNAME[rm],d,im));pos+=10
    else: pos+=1
sub=[r for r in recs if 1<=r[2]<=9 and r[3] in VT]
# --- 指令流 ---
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
INS.sort();ADDRS=[a for a,_,_,_ in INS]
BEND=sorted(a+sz for a,sz,mn,op in INS if mn.startswith('ret') or mn=='int3')
SORT=sorted(set(t for _,t in CALLAT))
REGION=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def next_entry(c):
    i=bisect.bisect_right(SORT,c)
    return SORT[i] if i<len(SORT) else HI

# ===== S1 =====
ck('S1a R200 697 复现', len(sub)==697, len(sub))
byhost=collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)
catH=collections.Counter();om=[]
for h,rs in byhost.items():
    if h is None: continue
    hi=min(next_entry(h),h+4096);o=P.r2o(h)
    hm=hs=False
    for i in md.disasm(RAW[o:o+(hi-h)],h):
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv=int(i.op_str.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv not in VT: continue
            if MD[iv]==0: hm=True
            else: hs=True
    k='both' if (hm and hs) else ('only_sub' if hs else 'only_main')
    catH[k]+=1
    if k=='only_main': om.append((h,hm,hs))
ck('S1b R200 三分类 251/0/11 复现',(catH['both'],catH['only_sub'],catH['only_main'])==(251,0,11),dict(catH))
hm6=sum(1 for _,hm,_ in om if hm)
ck('S1c only_main 的 11 个里装主表 6 / 零装填 5',(hm6,11-hm6)==(6,5),(hm6,11-hm6))
print('   S1: R200 第三支 else 的代码判据是 not(has_main and has_sub)，落盘命名却写 only_main(只装主表)')
print('       11 个里实际装主表 %d、完全零装表 %d ⇒ 命名与判据不符'%(hm6,11-hm6))

# ===== S2 =====
pol=[]
for h in byhost:
    if h is None: continue
    hi=min(next_entry(h),h+4096)
    pol.append(bisect.bisect_left(BEND,hi)-bisect.bisect_left(BEND,h))
ck('S2a 窗口内区间数中位数 >= 2', statistics.median(pol)>=2,
   'p50=%s p90=%s max=%s'%(statistics.median(pol),sorted(pol)[int(len(pol)*.9)],max(pol)))
n1=sum(1 for x in pol if x==1)
ck('S2b 恰含 1 区间的窗口 < 半数', n1<len(pol)/2,'%d/%d'%(n1,len(pol)))
print('   S2: 262 窗口内 ret/int3 区间 p50=%d mean=%.2f max=%d；恰含 1 个 %d(%.1f%%)'%(
    statistics.median(pol),sum(pol)/len(pol),max(pol),n1,100.0*n1/len(pol)))

# ===== S3 =====
G1=[r for r in sub if r[2]==MD[r[3]]]; G2=[r for r in sub if r[2]!=MD[r[3]]]
ck('S3a 686 / 11',(len(G1),len(G2))==(686,11),(len(G1),len(G2)))
ck('S3b G1 的 mdisp 全为 4/8 且 >0', all(MD[r[3]] in (4,8) for r in G1), dict(collections.Counter(MD[r[3]] for r in G1)))
ck('S3c G2 的 mdisp 全 0', all(MD[r[3]]==0 for r in G2), dict(collections.Counter(MD[r[3]] for r in G2)))
ck('S3d G1/G2 位移都只 4/8', set(r[2] for r in G1)|set(r[2] for r in G2)=={4,8},
   sorted(set(r[2] for r in G1)|set(r[2] for r in G2)))
print('   S3: 697 = 686 次表(disp8==mdisp, 4:%d/8:%d) + 11 主表(disp8!=mdisp, mdisp==0)'%(
    sum(1 for r in G1 if MD[r[3]]==4),sum(1 for r in G1 if MD[r[3]]==8)))

# ===== S4：区间口径 =====
allsite=[];pos=T['rawptr']
while pos<end-4:
    if RAW[pos]==0x66:
        if pos+2<end and RAW[pos+1]==0xC7:
            mo=RAW[pos+2]>>6; pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
        pos+=1; continue
    if RAW[pos]!=0xC7: pos+=1;continue
    modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0];allsite.append((va,REGNAME[rm],d,im));pos+=7
    elif mod==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0];allsite.append((va,REGNAME[rm],d,im));pos+=10
    else:
        im=struct.unpack_from('<I',RAW,pos+2)[0];allsite.append((va,REGNAME[rm],0,im));pos+=6
vts=[r for r in allsite if r[3] in VT]
mainall=[r for r in vts if MD[r[3]]==0]
suball=[r for r in vts if MD[r[3]]!=0]
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in suball:  brs[reg_of(r[0])]+=1
cS=collections.Counter()
for r in sub:
    reg=reg_of(r[0])
    if reg is None: cS['noreg']+=1; continue
    if brm[reg]>0 and brs[reg]>0: cS['both']+=1
    elif brs[reg]>0: cS['only_sub']+=1
    else: cS['none']+=1
print('   S4: 区间口径 store 级 both=%d only_sub=%d none=%d noreg=%d'%(cS['both'],cS['only_sub'],cS['none'],cS['noreg']))
ck('S4a store 级 both == 689', cS['both']==689, cS['both'])
ck('S4b store 级 only_sub == 0', cS['only_sub']==0, cS['only_sub'])
ck('S4c store 级 none == 8', cS['none']==8, cS['none'])
ck('S4d 三者相加 == 697', cS['both']+cS['only_sub']+cS['none']==697, cS['both']+cS['only_sub']+cS['none'])
ck('S4e 同区间双装率 > 98%', cS['both']/697.0>0.98, '%.2f%%'%(100.0*cS['both']/697))
# 8 条 none 逐条
none_rows=[r for r in sub if brs[reg_of(r[0])]==0]
ck('S4f none 逐条 8 条', len(none_rows)==8, len(none_rows))
for r in none_rows:
    reg=reg_of(r[0])
    print('      none at=%s disp=%d imm=%s cls=%s 区间 %s..%s 主表=%d 次表=%d'%(
        hex(r[0]),r[2],hex(r[3]),CLS[r[3]],hex(reg[0]),hex(reg[1]),brm[reg],brs[reg]))
ck('S4g 8 条 none 全为 mdisp==0 主表装填（区间内无任何次表装填）',
   len(none_rows)==8 and all(MD[r[3]]==0 for r in none_rows), sum(1 for r in none_rows if MD[r[3]]==0))

# ===== S5 =====
rep=['.?AVAirstrikeClass@@','.?AVAlphaShapeClass@@','.?AVBombClass@@','.?AVLightSourceClass@@',
     '.?AVWaveClass@@','.?AVWalkLocomotionClass@@','.?AVVoxelAnimTypeClass@@','.?AVCellClass@@']
OWN={}
for cn in rep:
    sites=[r for r in mainall if CLS[r[3]]==cn]
    regs=set(reg_of(r[0]) for r in sites)
    OWN[cn]=dict(n=len(sites),regions=len(regs),sites=[hex(r[0]) for r in sites[:6]])
    print('   %-34s 主表装填 %2d 处 / %d 个区间 %s'%(cn,len(sites),len(regs),OWN[cn]['sites'][:3]))
ck('S5a 8 代表类主表装填数在 4..6', all(4<=OWN[c]['n']<=6 for c in rep), {c:OWN[c]['n'] for c in rep})
ck('S5b 每类主表装填处数 == 区间数', all(OWN[c]['n']==OWN[c]['regions'] for c in rep),
   {c:(OWN[c]['n'],OWN[c]['regions']) for c in rep})

json.dump(dict(S1=dict(cat=dict(catH),om_has_main=hm6,om_zero=11-hm6),
               S2=dict(p50=statistics.median(pol),mean=sum(pol)/len(pol),max=max(pol),n1=n1,n=len(pol)),
               S3=dict(G1=len(G1),G2=len(G2)),
               S4=dict(cat=dict(cS),none=[(hex(r[0]),r[2],hex(r[3]),CLS[r[3]]) for r in none_rows]),
               S5=OWN,regions=len(REGION),asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m12_final.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
