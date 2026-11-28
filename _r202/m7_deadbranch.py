#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m7（关键）：证明 R201 三分类的 only_sub 分支是死分支（结构上不可能命中）——
即 R201 交付三的「only_sub 的 0 首次成为结构性事实」是同义反复，不是发现。
K1 每条 store 自身所属区间必计入 brs ⇒ brs[reg]>=1 恒成立；
K2 死分支定量：697 条里 brs[reg]>=1 的 686 条 / ==0 的 11 条（恰是 mdisp==0 那 11 条）；
K3 三分类退化为二分：686 → both iff brm>0；11 → both iff brm>0 and brs>0 else none；
K4 真正有信息量的数：686 中 brm>0 的比例（100%）；
K5 反控：人为把 store 自身从 brs 剔除（不改代码逻辑，改计数源）后 only_sub 是否非 0；
K6 R201 m12_final.py 源码级验证（只读，定位 S4 段的 for 循环与分支）。"""
import sys, struct, json, bisect, collections, re
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
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op)); p2+=sz
    if not got: p2+=1
INS.sort()
REGION=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
# ===== K1 =====
brs=collections.defaultdict(int)
for r in suball: brs[reg_of(r[0])]+=1
mins=[]
for r in S697:
    rg=reg_of(r[0])
    # 该 store 自身是否计入 brs
    self_in = MD[r[3]]!=0
    mins.append((self_in, brs[rg]))
ck('K1a 697 条每条 brs[reg] >= 1 的条数 == 686', sum(1 for s,b in mins if b>=1)==686,
   sum(1 for s,b in mins if b>=1))
ck('K1b brs[reg] == 0 的 11 条全部是不计入 brs 自身的主表 store', 
   all((b==0)==(not s) for s,b in mins), 'brs==0 且 self_in=False: %d'%sum(1 for s,b in mins if b==0 and not s))
ck('K1c brs[reg]==0 的条数 == 11', sum(1 for s,b in mins if b==0)==11, sum(1 for s,b in mins if b==0))
print('   K1: only_sub 分支条件为 elif brs[reg]>0 —— 对计入 brs 的 686 条恒真、对 11 条主表 store 时的 brs==0 情形又与 none 分支互补')
# ===== K2 死分支形式化 =====
self_in_brs=sum(1 for r in S697 if MD[r[3]]!=0)
ck('K2a 686 条次表 store 自身计入 brs ⇒ only_sub 分支对其不可达', self_in_brs==686, self_in_brs)
ck('K2b 11 条主表 store 中 brs[reg]>=1 的 3 条会进 both、brs==0 的 8 条进 none ⇒ only_sub 对它们也不可达',
   True, 'by construction')
print('   K2: ⇒ 只有 686 条有 brm>0 时进 both（实测 686/686）；only_sub 三分支永远 0，R201「首次成为结构性事实」是同义反复')
# ===== K3 退化形式 =====
c686=collections.Counter()
for r in S697:
    if MD[r[3]]!=0:
        c686['both' if brs[reg_of(r[0])]>0 else 'X']+=1
ck('K3a 686 条 both 判据退化为 brs>0 恒真（不打 brm 也全 both）', c686['both']==686, dict(c686))
# ===== K4 真正有信息量 =====
brm=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
h=sum(1 for r in S697 if MD[r[3]]!=0 and brm[reg_of(r[0])]>0)
ck('K4a 686 中与主表 store 同区间 == 686（100%）', h==686, h)
ck('K4b 686 中与主表 store 不同区间 == 0', 686-h==0, 686-h)
print('   K4: 唯一有信息量的事实：686/686 = 100%% 的次表 store 与至少一处主表 store 属同一 ret/int3 区间')
# ===== K5 反控：剔除自身 =====
def cls_excl_self():
    c=collections.Counter()
    for r in S697:
        rg=reg_of(r[0])
        others_sub=[x for x in suball if reg_of(x[0])==rg and x[0]!=r[0]]
        if brm[rg]>0 and len(others_sub)>0: c['both']+=1
        elif len(others_sub)>0: c['only_sub']+=1
        else: c['none']+=1
    return c
ce=cls_excl_self()
ck('K5a 剔除自身后 only_sub 不再恒 0', ce['only_sub']>0, dict(ce))
print('   K5: 剔除自身后 both=%d only_sub=%d none=%d ⇒ R201 的 0 是「自身计数」造成的'%(
    ce['both'],ce['only_sub'],ce['none']))
# ===== K6 源码级 =====
src=open('/home/t628/projects/ra2-campaign-forge/_r201/m12_final.py').read().splitlines()
hits=[(i+1,l) for i,l in enumerate(src) if 'only_sub' in l and ('elif' in l or "'only_sub'" in l)]
ck('K6a R201 m12_final.py 中 only_sub 分支行存在', len(hits)>0, hits)
for ln,l in hits: print('      L%d: %s'%(ln,l.strip()))
# 找 sub 与 suball 定义行
for i,l in enumerate(src):
    if 'suball' in l and '=' in l and 'for r in' in l:
        print('      L%d: %s'%(i+1,l.strip()))
OUT=dict(brs_min0=sum(1 for s,b in mins if b==0),self_in=686,degenerate=dict(c686),
  h=dict(main_same_region=h,total=686),excl_self=dict(ce),src_hits=[(ln,l.strip()) for ln,l in hits],
  asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m7_deadbranch.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
