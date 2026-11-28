#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m2：697 vs 686 的差 11 条到底在哪 —— 三种提取器变体逐条对照。
V1 旧（不识别 0x66 前缀、不取 mod==0）；V2 识别 0x66、不取 mod==0；V3 识别 0x66、取 mod==0。
同时给差集的逐条反汇编上下文（detail，仅目标地址）。"""
import sys, struct, json, collections
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

def extract(skip66, take_mod0):
    rec=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-4:
        if skip66 and RAW[pos]==0x66:
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
            im=struct.unpack_from('<I',RAW,pos+2)[0]
            if take_mod0: rec.append((va,rm,0,im))
            pos+=6
    return rec
V1=[r for r in extract(False,False) if 1<=r[2]<=9 and r[3] in VT]
V2=[r for r in extract(True,False)  if 1<=r[2]<=9 and r[3] in VT]
V3=[r for r in extract(True,True)   if 1<=r[2]<=9 and r[3] in VT]
ck('V1 旧提取器 小位移 == 697', len(V1)==697, len(V1))
ck('V2 识 0x66 不取 mod0 == 686', len(V2)==686, len(V2))
ck('V3 识 0x66 取 mod0 == 686', len(V3)==686, len(V3))
S1={r[0] for r in V1};S2={r[0] for r in V2};S3={r[0] for r in V3}
ck('V1-V2 差 11 条', len(S1-S2)==11, len(S1-S2))
ck('V2==V3 同集合', S2==S3, len(S2^S3))
print('   差集地址: %s'%[hex(x) for x in sorted(S1-S2)])
# 逐条对照差集：在 V1 里是什么，在真实反汇编里是什么
print('\n   ---- 差集逐条真实反汇编（detail，仅这些地址）----')
DIFF=sorted(S1-S2)
for va in DIFF:
    o=P.r2o(va-1)
    ins=list(md.disasm(RAW[o:o+16],va-1))
    real=[(hex(i.address),i.bytes.hex(),i.mnemonic+' '+i.op_str) for i in ins[:2]]
    v1=[r for r in V1 if r[0]==va][0]
    print('   V1@%s %s'%(hex(va),real))
    print('      V1 解析: disp=%d imm=%s mdisp=%d cls=%s'%(v1[2],hex(v1[3]),MD[v1[3]],CLS[v1[3]]))
# 差集里 imm 是否落 VT 且 mdisp==0
dif=[r for r in V1 if r[0] in set(DIFF)]
ck('差集 11 条中 mdisp==0 的条数', True, '%d/11'%sum(1 for r in dif if MD[r[3]]==0))
ck('差集 11 条中的 mdisp 分布', True, dict(collections.Counter(MD[r[3]] for r in dif)))
ck('差集 11 条的 disp8 分布', True, dict(collections.Counter(r[2] for r in dif)))
# G2（697 里 disp8 != mdisp）是不是恰好就是差集
G2=[r for r in V1 if r[2]!=MD[r[3]]]
ck('V1 的 disp8!=mdisp 恰 11 条', len(G2)==11, len(G2))
ck('V1 的 disp8!=mdisp 集合 == 差集', {r[0] for r in G2}==set(DIFF), sorted({r[0] for r in G2}))
print('   G2(V1) 地址: %s'%[hex(r[0]) for r in G2])
# 反控：V2 里 disp8 vs mdisp 全等？
ck('V2 的 disp8 全等 mdisp（686/686）', all(r[2]==MD[r[3]] for r in V2),
   sum(1 for r in V2 if r[2]==MD[r[3]]))
ck('V2 的 mdisp 分布 == {4:345,8:341}',
   collections.Counter(MD[r[3]] for r in V2)==collections.Counter({4:345,8:341}),
   dict(collections.Counter(MD[r[3]] for r in V2)))
# 646/...  V2 的 disp 分布
ck('V2 的 disp8 分布', True, dict(collections.Counter(r[2] for r in V2)))
json.dump(dict(V1=len(V1),V2=len(V2),V3=len(V3),diff=[hex(x) for x in DIFF],
   diff_mdisp=dict(collections.Counter(MD[r[3]] for r in dif)),
   v2_mdisp=dict(collections.Counter(MD[r[3]] for r in V2)),
   v2_disp=dict(collections.Counter(r[2] for r in V2)),asserts=N,fails=fails),
   open('/home/t628/projects/ra2-campaign-forge/_r202/m2_697diff.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
