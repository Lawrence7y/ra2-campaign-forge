#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m4：复核 R201 的 both=689/only_sub=0/none=8 并做分子分母同质性分解。
G1 完全复用 R201 m12 的 S4 语义复现 689/0/8；
G2 把 689 拆成「次表 store 贡献」与「主表 store 自计」两部分；
G3 证明 none 按定义只能是 mdisp==0 的 11 条之子集（R201 交付四部分是定义产物）；
G4 在纯次表 store（686）口径上重算三分类（正确分母）；
G5 反控。"""
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
sub=[r for r in vts if 1<=r[2]<=9]          # 697（R201 口径）
sub686=[r for r in sub if MD[r[3]]!=0]       # 686 纯次表
sub11=[r for r in sub if MD[r[3]]==0]        # 11 主表
# ---- 指令流与区间 ----
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
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in suball:  brs[reg_of(r[0])]+=1
# ===== G1 复现 R201 S4 =====
cat=collections.Counter(); rows=[]
for r in sub:
    rg=reg_of(r[0])
    if rg is None: cat['noreg']+=1; continue
    if brm[rg]>0 and brs[rg]>0: k='both'
    elif brs[rg]>0: k='only_sub'
    else: k='none'
    cat[k]+=1; rows.append((r,k))
ck('G1a 复现 R201 both=689', cat['both']==689, cat['both'])
ck('G1b 复现 R201 only_sub=0', cat['only_sub']==0, cat['only_sub'])
ck('G1c 复现 R201 none=8', cat['none']==8, cat['none'])
ck('G1d 三数相加 697', cat['both']+cat['only_sub']+cat['none']==697, sum(cat.values()))
# ===== G2 689 的分子分解 =====
both686=[r for r,k in rows if k=='both' and MD[r[3]]!=0]
both11 =[r for r,k in rows if k=='both' and MD[r[3]]==0]
os686  =[r for r,k in rows if k=='only_sub' and MD[r[3]]!=0]
ck('G2a both 中来自纯次表 store == 686', len(both686)==686, len(both686))
ck('G2b both 中来自主表 store（自身即主表）== 3', len(both11)==3, len(both11))
ck('G2c only_sub 中来自主表 store == 0', len([r for r,k in rows if k=='only_sub' and MD[r[3]]==0])==0, '')
ck('G2d 689 == 686 + 3', cat['both']==len(both686)+len(both11), (len(both686),len(both11)))
print('   G2: both 689 = 686(次表 store 落主表区间) + 3(主表 store 自计)；3 条自计地址 %s'%[hex(r[0]) for r in both11])
# ===== G3 none 的定义产物性 =====
none_rows=[r for r,k in rows if k=='none']
ck('G3a none 8 条全是 mdisp==0（定义上必然）', all(MD[r[3]]==0 for r in none_rows), sum(1 for r in none_rows if MD[r[3]]==0))
ck('G3b none ⊂ 11 条主表 store', set(r[0] for r in none_rows)<=set(r[0] for r in sub11), len(set(r[0] for r in none_rows)))
ck('G3c none 8 == 11 - 3（3 条 in-both 的补）', len(none_rows)==len(sub11)-len(both11), (len(none_rows),len(sub11),len(both11)))
print('   G3: none 8 由 "区间内无次表 store" 定义 ⇒ 只可能来自 11 条 mdisp==0；11 = 8(none) + 3(both) 完全划分')
# 反控：把 11 条主表 store 从 sub 里剔除后，none 必为 0
cat686=collections.Counter()
for r in sub686:
    rg=reg_of(r[0])
    if brm[rg]>0 and brs[rg]>0: cat686['both']+=1
    elif brs[rg]>0: cat686['only_sub']+=1
    else: cat686['none']+=1
ck('G4a 纯次表 686 口径：none == 0', cat686['none']==0, cat686['none'])
ck('G4b 纯次表 686 口径：only_sub == 0', cat686['only_sub']==0, cat686['only_sub'])
ck('G4c 纯次表 686 口径：both == 686（100%）', cat686['both']==686, cat686['both'])
print('   G4: 正确分母 686 ⇒ both=686 only_sub=0 none=0，同区间率 100%%（R201 的 98.85% 分母含 11 条非同质 store）')
# ===== G5 反控 =====
# 反控1：把主表 store 全删，brm 依赖 still ok? 用 suball 作为 brm 来源
brm2=collections.defaultdict(int)
for r in mainall: brm2[reg_of(r[0])]+=1
ck('G5a brm 与 brs 来源不重叠', len(set(mainall)&set(suball))==0, len(mainall))
# 反控2：打乱区间划分（每个区间向右扩 64 字节）不应改变 686/0/0
cat2=collections.Counter()
for r in sub686:
    rg=reg_of(r[0]); rg2=(rg[0],rg[1]+64)
    if brm[rg2]>0 and brs[rg2]>0: cat2['both']+=1
    elif brs[rg2]>0: cat2['only_sub']+=1
    else: cat2['none']+=1
ck('G5b 扰动区间终点 +64 后 686 口径仍 both==686', cat2['both']==686, dict(cat2))
# 反控3：把 brs 换成「自身即次表」的恒真式，验证 both 会退化为 brm>0 计数（判别力检查）
cat3=collections.Counter()
for r in sub:
    rg=reg_of(r[0])
    cat3['both' if brm[rg]>0 else 'only_sub']+=1
ck('G5c 恒真式 brs>0 得 both=697（说明 brs 判据在 686 上恒成立、无区分力）', cat3['both']==697, dict(cat3))
OUT=dict(cat=dict(cat),both686=len(both686),both11=len(both11),both11_addrs=[hex(r[0]) for r in both11],
  none8=[hex(r[0]) for r in none_rows],cat686=dict(cat686),cat_perturb=dict(cat2),cat_taut=dict(cat3),
  asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m4_both689.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
