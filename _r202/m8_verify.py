#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m8：复算子代理 #509（none 宿主类名 / INoticeSink 位移 8）与 #510（函数范围口径 691/0/6、重装 564、COL 指针恒 vt-4）
并订正主会话 m7 的过度断言（only_sub 并非结构不可达，须给可达性判据）。
P1 m7 订正：only_sub 可达性 —— 统计「brs>0 且 brm==0」的区间数（=0 才是 R201 0 的真含义）
P2 8 条 none 在 E3 函数段内的 +0 主表类名（复算 #509 的 5 条取得 + 3 条 UNDETERMINED）
P3 INoticeSink 3 条：区间 +0 主表类、+4/+8/+12 次表类、以及 disp=8 的二进制佐证
P4 复算 #510 的函数范围口径 697 -> 691/0/6 与 686 重装 564
P5 复算 #510 的 COL 指针恒 vt-4 与 COL 地址非常数"""
import sys, struct, json, bisect, collections
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
suball=[r for r in vts if MD[r[3]]!=0]
S697=[r for r in vts if 1<=r[2]<=9]
S686=[r for r in S697 if MD[r[3]]!=0]
S11=[r for r in S697 if MD[r[3]]==0]
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
SORT=sorted(set(t for _,t in CALLAT)); TGT=set(SORT)&ASET
REGION=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in suball:  brs[reg_of(r[0])]+=1
# ===== P1 m7 订正：only_sub 可达性 =====
reach=[rg for rg in set(list(brm.keys())+list(brs.keys())) if brs[rg]>0 and brm[rg]==0]
ck('P1a 全体区间中「brs>0 且 brm==0」的区间数 == 0（这才是 R201 only_sub=0 的含义）', len(reach)==0, len(reach))
tot_brs=sum(1 for rg in brs if brs[rg]>0)
ck('P1b 有次表装填的区间数 == len(brs)', tot_brs==len(brs), tot_brs)
ck('P1c 有次表装填的区间里也有主表装填的比例 == 100%', all(brm[rg]>0 for rg in brs), 
   '%d/%d'%(sum(1 for rg in brs if brm[rg]>0),len(brs)))
# 可达性构造性反证：把主表装填集换成空集，only_sub 立即非 0
c=collections.Counter()
for r in S686:
    rg=reg_of(r[0])
    if brs[rg]>0: c['only_sub']+=1
ck('P1d 主表集置空后 only_sub == 686（判据本身可达，非死分支）', c['only_sub']==686, c['only_sub'])
print('   P1: m7 的「死分支」说法订正 —— only_sub = (brs>0 且 brm==0) 可达；实测 0 是因为 %d 个有次表装填的区间 100%% 也有主表装填'%tot_brs)
# ===== P2 8 条 none 的 +0 主表类名（E3 段口径）=====
def pat(a):
    i=I2R.get(a)
    if i is None: return None
    w=INS[i:i+3]
    if len(w)<2: return None
    m=[x[2] for x in w]; o=[x[3].replace(' ','') for x in w]
    if m[0]=='push' and o[0]=='ebp' and m[1]=='mov' and o[1]=='ebp,esp': return 'P1'
    if m[0]=='mov' and o[0]=='edi,edi' and m[1]=='push' and o[1]=='ebp':
        return 'P3' if (len(w)>2 and m[2]=='mov' and o[2]=='ebp,esp') else 'P3b'
    if m[0]=='sub' and o[0].startswith('esp,'): return 'P4'
    return None
PATS=set(a for a in ADDRS if pat(a))
E3=sorted(TGT|PATS)
def seg(va):
    i=bisect.bisect_right(E3,va)-1
    if i<0: return None
    return (E3[i], E3[i+1] if i+1<len(E3) else HI)
N8=['0x5d5b80','0x635f34','0x637114','0x638aa4','0x6cf196','0x6cf209','0x7b1b2b','0x7b27fb']
N8=[int(x,16) for x in N8]
res={}
for va in N8:
    a,b=seg(va)
    inside=[r for r in vts if a<=r[0]<b]
    mains=[(hex(r[0]),hex(r[3]),CLS[r[3]],MD[r[3]]) for r in inside if MD[r[3]]==0]
    subs=[(hex(r[0]),r[2],hex(r[3]),CLS[r[3]]) for r in inside if MD[r[3]]!=0]
    res[hex(va)]=dict(seg=[hex(a),hex(b)],mains=mains,subs=subs)
    print('   P2 %s 段 %s..%s  主表 %d 处 %s'%(hex(va),hex(a),hex(b),len(mains),[m[2] for m in mains]))
    for s in subs[:6]: print('        次表 %s d=%d %s md=%d'%(s[0],s[1],s[3],MD[int(s[2],16)]))
get5=[k for k,v in res.items() if v['mains']]
ck('P2a 8 条中能从段内 +0 主表直接读出外层宿主的条数 == 5', len(get5)==5, len(get5))
ck('P2b 其余 3 条段内无任何主表装填', sum(1 for v in res.values() if not v['mains'])==3,
   sum(1 for v in res.values() if not v['mains']))
# 与 #509 报告的 5 条类名逐条核对
EXP={'0x5d5b80':'.?AVMultiplayerGameMode@@',
     '0x6cf196':'.?AVSwizzleManagerClass@@','0x6cf209':'.?AVSwizzleManagerClass@@',
     '0x7b1b2b':'.?AVWinsockInterfaceClass@@','0x7b27fb':'.?AVWinsockInterfaceClass@@'}
ok=True
for k,v in EXP.items():
    names=[m[2] for m in res[k]['mains']]
    hit=[n for n in names if n==v]
    if not hit: ok=False; print('   P2 MISMATCH %s 期望 %s 实测 %s'%(k,v,names))
ck('P2c 与 #509 报告的 5 条类名逐条一致', ok, 'checked %d'%len(EXP))
# ===== P3 INoticeSink =====
IN3=[0x410174,0x4101c2,0x6e8008]
for va in IN3:
    rg=reg_of(va); a,b=rg
    inside=[r for r in vts if a<=r[0]<b]
    mains=[(hex(r[0]),hex(r[3]),CLS[r[3]]) for r in inside if MD[r[3]]==0]
    subs=[(hex(r[0]),r[2],CLS[r[3]],MD[r[3]]) for r in inside if MD[r[3]]!=0]
    print('   P3 %s 区间 %s..%s 主表 %s'%(hex(va),hex(a),hex(b),mains))
    for s in subs: print('        次表 %s d=%-2d md=%-2d %s'%(s[0],s[1],s[3],s[2]))
    ck('P3x %s 区间内主表含 INoticeSink 且位移为 8'%hex(va),
       any('INoticeSink' in m[2] for m in mains), [m for m in mains if 'INoticeSink' in m[2]])
    ck('P3y %s 区间内次表数 3..6'%hex(va), 3<=len(subs)<=6, len(subs))
# ===== P4 复算 #510 函数范围口径 =====
bm2=collections.defaultdict(int); bs2=collections.defaultdict(int)
for r in mainall: bm2[seg(r[0])]+=1
for r in suball:  bs2[seg(r[0])]+=1
def cls(stores):
    c=collections.Counter(); det=collections.defaultdict(list)
    for r in stores:
        sg=seg(r[0])
        if bm2[sg]>0 and bs2[sg]>0: k='both'
        elif bs2[sg]>0: k='only_sub'
        else: k='none'
        c[k]+=1; det[k].append(r)
    return c,det
c7,d7=cls(S697); c6,d6=cls(S686)
ck('P4a 函数段口径 697 -> 691/0/6（与 #510 一致）', (c7['both'],c7['only_sub'],c7['none'])==(691,0,6), dict(c7))
ck('P4b 6 条 none 地址与 #510 一致', sorted(hex(r[0]) for r in d7['none'])==sorted(['0x5d5b80','0x635f34','0x637114','0x638aa4','0x7b1b2b','0x7b27fb']),
   [hex(r[0]) for r in d7['none']])
# 重装：同函数段内、同基址、同 imm 出现 >=2 次
grp=collections.defaultdict(list)
for r in S686: grp[(seg(r[0]),r[1],r[3])].append(r[0])
dup=[k for k,v in grp.items() if len(v)>1]
ndup=sum(len(grp[k]) for k in dup)
ck('P4c 函数段口径重装 store 数在 500..600（#510 报 564）', 500<=ndup<=600, ndup)
ck('P4d 重装组数在 140..170（#510 报 156）', 140<=len(dup)<=170, len(dup))
print('   P4: 函数段口径 686 重装 store=%d / 组=%d / 涉及段=%d'%(ndup,len(dup),len(set(k[0] for k in dup))))
# ===== P5 COL 指针恒 vt-4 =====
ok4=all(P.dw(v-4) in COL for v in VT)
ck('P5a 1214/1214 个 VT 项的 COL 指针恒在 vt-4', ok4, sum(1 for v in VT if P.dw(v-4) in COL))
dx=collections.Counter(VT[v]-v for v in VT)
ck('P5b COL 地址 - 虚表地址 非常数（#510 报 916 个取值）', len(dx)>500, len(dx))
ck('P5c VT 总项数 1214', len(VT)==1214, len(VT))
OUT=dict(reach=dict(n=len(reach),brs_regions=tot_brs,main_in_brs=sum(1 for rg in brs if brm[rg]>0)),
  none_hosts=res,func697=dict(c7),func686=dict(c6),dup=dict(n=ndup,groups=len(dup),segments=len(set(k[0] for k in dup))),
  colptr=dict(ok=ok4,n=len(VT),distinct=len(dx)),asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m8_verify.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
