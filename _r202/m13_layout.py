#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m13（定稿）：11 条 mdisp==0 装表的两种机制分离 —— 同槽位后继覆盖是否发生。
W1 11 条逐条：区间内 (基址,disp) 槽位的完整写入序列（含 imm/mdisp/类名/是否主表）；
W2 「后继同槽位覆盖」命中：3 条 INoticeSink 有、8 条模板成员无（判别力）；
W3 位移语义：disp==0 的 store 才写 this 自身 vfptr；disp>0 写的是 this+disp 处子对象；
W4 反控：686 条正常次表 store 的同槽位序列长度分布（应恒为 1）；
W5 5 处 INoticeSink 主表装填的位移与后继覆盖。"""
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
def slot_seq(r):
    a,b=reg_of(r[0])
    seq=[x for x in vts if a<=x[0]<b and x[1]==r[1] and x[2]==r[2]]
    seq.sort()
    return seq
def has_later_cover(r):
    return any(x[0]>r[0] and MD[x[3]]==x[2] for x in slot_seq(r))
print('   W1 11 条 mdisp==0 store 的槽位写入序列：')
mech={}
for r in S11:
    seq=slot_seq(r)
    cov=has_later_cover(r)
    mech[hex(r[0])]=dict(disp=r[2],cls=CLS[r[3]],cover=cov,
        seq=[dict(at=hex(x[0]),mdisp=MD[x[3]],cls=CLS[x[3]],primary=MD[x[3]]==0) for x in seq],
        host=[c for c in (CLS[x[3]] for x in seq) if not c.startswith('.?AV?$')])
    print('      %s disp=%d %s 槽位序列 %d 条 后继覆盖=%s'%(hex(r[0]),r[2],CLS[r[3]],len(seq),cov))
    for x in seq: print('         %s mdisp=%d %s'%(hex(x[0]),MD[x[3]],CLS[x[3]]))
covs=[k for k,v in mech.items() if v['cover']]
nocov=[k for k,v in mech.items() if not v['cover']]
ck('W2a 11 条中后继同槽位覆盖命中 3 条', len(covs)==3, covs)
ck('W2b 命中 3 条恰是 .?AVINoticeSink@@ 的三条',
   set(covs)=={'0x410174','0x4101c2','0x6e8008'} and all('INoticeSink' in mech[k]['cls'] for k in covs), covs)
ck('W2c 未命中 8 条全是模板容器成员类',
   all(cls.startswith('.?AV?$') for k in nocov for cls in [mech[k]['cls']]), len(nocov))
print('   W2: ⇒ 两种机制：3 条 INoticeSink 的 +8/+12 主表随后被基类 AbstractClass/TaskForceClass 次表同槽位覆盖（多继承布局）；8 条模板成员主表无覆盖（内嵌成员子对象初始化）')
# W3 位移语义
ck('W3a 11 条位移全 ∈ {4,8} 且无 0', set(r[2] for r in S11)=={4,8}, sorted(set(r[2] for r in S11)))
ck('W3b 686 条 disp 全 ∈ {4,8} 且 == mdisp', all(r[2]==MD[r[3]] and r[2] in (4,8) for r in S686), '')
# W4 686 槽位序列长度分布
L=collections.Counter()
for r in S686: L[len(slot_seq(r))]+=1
ck('W4a 686 条槽位序列长度 100%% 为 1', L[1]==686, dict(L))
print('   W4: 686 条正常次表 store 的槽位序列长度分布 %s（恒 1 ⇒ 同一槽位在真实函数体内只装一次）'%dict(L))
# W5 INoticeSink 5 处
allIN=[r for r in vts if CLS[r[3]]=='.?AVINoticeSink@@']
print('   W5 全段 INoticeSink 主表装填 %d 处：'%len(allIN))
for r in allIN:
    print('      %s 基=%s disp=%d 后继覆盖=%s'%(hex(r[0]),['eax','ecx','edx','ebx','esp','ebp','esi','edi'][r[1]],r[2],has_later_cover(r)))
ck('W5a INoticeSink 主表装填总 5 处', len(allIN)==5, len(allIN))
ck('W5b 其中 disp==8 的 3 处后继覆盖 / disp!=8 的 2 处不覆盖',
   all(has_later_cover(r) for r in allIN if r[2]==8) and not any(has_later_cover(r) for r in allIN if r[2]!=8),
   [(hex(r[0]),r[2],has_later_cover(r)) for r in allIN])
OUT=dict(mech=mech,cov=covs,nocov=nocov,slot_len=dict(L),
  IN5=[(hex(r[0]),r[2],has_later_cover(r)) for r in allIN],asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m13_layout.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
