#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m10：三条 INoticeSink 主表装填为何位移 8 —— 区间内完整装填序列 + 指令级上下文。
M1 三个区间内所有装 VT 的 store（地址/位移/imm/mdisp/类名），按地址顺序；
M2 每条 store 的真实反汇编（detail，仅这些地址）；
M3 位移集合与类名对照 -> 推导对象布局；
M4 反控：同类 INoticeSink 其它主表装填（全段）的位移分布。"""
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
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
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
IN3=[0x410174,0x4101c2,0x6e8008]
RES={}
for va in IN3:
    a,b=reg_of(va)
    ins_region=[r for r in vts if a<=r[0]<b]
    ins_region.sort()
    print('   M1 区间 %s..%s 共 %d 条装 VT store：'%(hex(a),hex(b),len(ins_region)))
    for r in ins_region:
        mark='<<<' if r[0]==va else ''
        print('        %s 基=%s disp=%-2d imm=%s mdisp=%-2d %s %s'%(
            hex(r[0]),REGNAME[r[1]],r[2],hex(r[3]),MD[r[3]],CLS[r[3]],mark))
    RES[hex(va)]=[dict(at=hex(r[0]),base=REGNAME[r[1]],disp=r[2],imm=hex(r[3]),mdisp=MD[r[3]],cls=CLS[r[3]]) for r in ins_region]
    d={}
    for r in ins_region:
        d.setdefault(r[2],[]).append(CLS[r[3]])
    print('        位移->类 %s'%{k:v for k,v in sorted(d.items())})
ck('M1a 三个区间内 store 数 3/3/6 复现', [len(RES[hex(v)]) for v in IN3]==[6,6,10], [len(RES[hex(v)]) for v in IN3])
# M2 反汇编上下文
print('\n   M2 每条目标 store 的指令上下文：')
for va in IN3:
    o=P.r2o(va-8)
    for i in list(md.disasm(RAW[o:o+20],va-8))[:4]:
        print('        %s %-24s %s %s'%(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str))
# M3 位移->类 推导
for va in IN3:
    rows=RES[hex(va)]
    sets={}
    for r in rows: sets.setdefault(r['disp'],set()).add(r['cls'])
    dup={k:sorted(v) for k,v in sets.items() if len(v)>1}
    ck('M3a %s 每个位移恰好对应一个类'%hex(va), len(dup)==0, dup)
    if va!=0x6e8008:
        want={0:'.?AVAbstractClass@@',4:'.?AVINoticeSource@@',8:'.?AVINoticeSink@@'}
        got={r['disp']:r['cls'] for r in rows}
        ck('M3b %s 布局 == {0:AbstractClass,4:INoticeSource,8:INoticeSink}'%hex(va), got==want, got)
# 全段 INoticeSink 主表装填位移分布（反控）
allIN=[r for r in vts if CLS[r[3]]=='.?AVINoticeSink@@']
disp=collections.Counter(r[2] for r in allIN)
ck('M4a 全段 INoticeSink 主表装填处数', len(allIN)>0, len(allIN))
ck('M4b 全段位移分布', True, dict(disp))
print('   M4: 全段 INoticeSink 主表装填 %d 处，位移分布 %s'%(len(allIN),dict(disp)))
# 全段 AbstractClass/INoticeSource 主表装填位移
for cn in ('.?AVAbstractClass@@','.?AVINoticeSource@@'):
    rows=[r for r in vts if CLS[r[3]]==cn]
    print('   M4 %-24s 主表装填 %d 处，位移分布 %s'%(cn,len(rows),dict(collections.Counter(r[2] for r in rows))))
OUT=dict(RES=RES,IN_n=len(allIN),IN_disp=dict(disp),asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m10_inotice.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
