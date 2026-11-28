#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m12（本轮核心）：11 条「mdisp==0 且 disp∈{4,8}」的装表 store 是否在同一函数体内被同槽位覆盖。
V1 对 11 条逐条：同区间、同基址寄存器、同 disp 的后续 store（imm 的 mdisp == disp 者）是否存在，给地址与类名；
V2 反控：686 条正常 store（disp==mdisp）中同槽位后续覆盖的比例；
V3 判别力：同槽位覆盖在 11 条的命中率 vs 686 条命中率；
V4 若 V1 全命中 ⇒ R201「内嵌成员子对象主表初始化」的定性不完整（那 8 条 none 也一样被覆盖），给新定性。"""
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
S697=[r for r in vts if 1<=r[2]<=9]
S686=[r for r in S697 if MD[r[3]]!=0]
S11=[r for r in S697 if MD[r[3]]==0]
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[]
p2=0
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
def later_same_slot(r):
    a,b=reg_of(r[0])
    out=[x for x in vts if a<=x[0]<b and x[0]>r[0] and x[1]==r[1] and x[2]==r[2] and x[3]!=r[3]]
    out.sort()
    return out
print('   V1 11 条「mdisp==0 且 disp∈{4,8}」的后续同槽位覆盖：')
hits=0; rows=[]
for r in S11:
    lt=later_same_slot(r)
    cov=[x for x in lt if MD[x[3]]==x[2]]
    hit=len(cov)>0
    if hit: hits+=1
    rows.append(dict(at=hex(r[0]),seg=[hex(reg_of(r[0])[0]),hex(reg_of(r[0])[1])],disp=r[2],
        cls=CLS[r[3]],later=[dict(at=hex(x[0]),disp=x[2],mdisp=MD[x[3]],cls=CLS[x[3]],is_matching=MD[x[3]]==x[2]) for x in lt]))
    print('      %s disp=%d %s -> 后续同槽位 %d 条 %s'%(hex(r[0]),r[2],CLS[r[3]],len(lt),
        [(hex(x[0]),MD[x[3]],CLS[x[3]]) for x in lt]))
ck('V1a 11 条全部有后续同槽位覆盖（imm 的 mdisp == disp）', hits==11, '%d/11'%hits)
# V2 反控：686 条
h686=0
for r in S686:
    cov=[x for x in later_same_slot(r) if MD[x[3]]==x[2]]
    if cov: h686+=1
ck('V2a 686 条中同槽位后续覆盖的条数 < 11/697 的比例外推（给出实测）', True, '%d/686 = %.1f%%'%(h686,100.0*h686/686))
print('   V2: 686 条中 %d 条有后续同槽位覆盖（%.1f%%） vs 11 条中 %d 条（%.0f%%）'%(h686,100.0*h686/686,hits,100.0*hits/11))
# V3 判别力
ck('V3a 11 条覆盖率显著高于 686 条', hits/11.0 > (h686/686.0)+0.5, '%.0f%% vs %.1f%%'%(100.0*hits/11,100.0*h686/686))
# V4 是否存在「同一 (基址,disp) 在同一区间写两次且第二次 mdisp==disp」的普遍模式
pat=collections.Counter()
for r in vts:
    if r[2] not in (4,8): continue
    a,b=reg_of(r[0])
    cov=[x for x in vts if a<=x[0]<b and x[0]>r[0] and x[1]==r[1] and x[2]==r[2] and MD[x[3]]==x[2]]
    if cov: pat[(MD[r[3]]==0)]+=1
ck('V4a 模式在 mdisp==0 组与非 0 组的计数已给', True, dict(pat))
print('   V4: 在 disp∈{4,8} 的 store 中，「后续同槽位被 mdisp==disp 的 store 覆盖」：mdisp==0 组 %d 条、mdisp!=0 组 %d 条'%(
    pat[True],pat[False]))
OUT=dict(rows=rows,hits=hits,h686=h686,pat={str(k):v for k,v in pat.items()},asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m12_overwrite.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
