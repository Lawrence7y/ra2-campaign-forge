#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m8：精确解释 697 vs 686 的差，并给出 66 前缀（WORD 装填）的正确处理。"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
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

def extract(fix_mod0, skip_66):
    recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-6:
        if skip_66 and RAW[pos]==0x66:
            # 0x66 前缀：下一条 C7 是 WORD 装填，不属 dword 口径，跳过整条
            if pos+1<len(RAW) and RAW[pos+1]==0xC7:
                m2=RAW[pos+2];mo=m2>>6
                pos += 6 if mo==0 else (7 if mo==1 else 11)
                continue
        if RAW[pos]!=0xC7: pos+=1;continue
        modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
        va=LO+(pos-T['rawptr'])
        if mod==1:
            d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
            recs.append((va,REGNAME[rm],d,im,'m1'));pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
            recs.append((va,REGNAME[rm],d,im,'m2'));pos+=10
        elif mod==0 and fix_mod0:
            im=struct.unpack_from('<I',RAW,pos+2)[0]
            recs.append((va,REGNAME[rm],0,im,'m0'));pos+=6
        else: pos+=1
    return recs
A=extract(False,False)   # R200 原口径
B=extract(True,False)    # m6 口径（66 未处理）
C=extract(True,True)     # 66 前缀已处理
print('A(R200原) %d / B(m6,66未处理) %d / C(66已处理) %d'%(len(A),len(B),len(C)))
def small(rs): return [r for r in rs if 1<=r[2]<=9 and r[3] in VT]
for nm,rs in (('A',A),('B',B),('C',C)):
    s=small(rs)
    print('  %s 小位移次表(1..9,imm in VT) = %d'%(nm,len(s)))
# 差集定位
sa=set(r[0] for r in small(A)); sb=set(r[0] for r in small(B)); sc=set(r[0] for r in small(C))
print('\nA-B:',[hex(x) for x in sorted(sa-sb)])
print('B-A:',[hex(x) for x in sorted(sb-sa)])
print('A-C:',[hex(x) for x in sorted(sa-sc)],' C-A:',[hex(x) for x in sorted(sc-sa)])
# 每条 66 前缀的全部
p66=[];pos=T['rawptr']
while pos<T['rawptr']+T['rawsize']-8:
    if RAW[pos]==0x66 and RAW[pos+1]==0xC7:
        m2=RAW[pos+2];mo=m2>>6;rm=m2&7;rg=(m2>>3)&7
        p66.append((LO+(pos-T['rawptr']),mo,rm,rg))
    pos+=1
c66=collections.Counter(mo for _,mo,_,_ in p66)
print('\n全 .text 66 c7 序列 %d 处，mod 分布 %s'%(len(p66),dict(c66)))
print('  样例',[(hex(a),mo,rm,rg) for a,mo,rm,rg in p66[:12]])
# 正控夹具修正
def synth(code,base,fix):
    out=[];pos=0;cap=len(code)
    while pos<cap-4:
        if code[pos]!=0xC7: pos+=1;continue
        modrm=code[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
        need=6 if mod==0 else (7 if mod==1 else 10)
        if pos+need>cap: break
        if mod==1:
            d=struct.unpack_from('<b',code,pos+2)[0];im=struct.unpack_from('<I',code,pos+3)[0]
            out.append((base+pos,REGNAME[rm],d,im,'m1'));pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',code,pos+2)[0];im=struct.unpack_from('<I',code,pos+6)[0]
            out.append((base+pos,REGNAME[rm],d,im,'m2'));pos+=10
        else:
            im=struct.unpack_from('<I',code,pos+2)[0]
            out.append((base+pos,REGNAME[rm],0,im,'m0'));pos+=6
    return out
syn=bytes.fromhex('c70678563412'+'c7460478563412'+'c7860001000078563412'+'c70778563412')
r=synth(syn,0x1000,True)
print('\n正控修正后（边界 cap-4 + need 检查）:',[(hex(a),rg,d,hex(i),k) for a,rg,d,i,k in r])
print('命中 %d/4'%len(r))
# 66 正控：66 c7 00 imm16 -> 必须是 WORD 不算 dword
syn2=bytes.fromhex('66c7003412'+'c70678563412')
print('66 正控（期望只命中 1 条 dword）:',[(hex(a),rg,d,hex(i),k) for a,rg,d,i,k in synth(syn2,0x2000,True)])
