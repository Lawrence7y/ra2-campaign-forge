#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m7：定位提取器丢 11 条（697->686）与正控第 4 条丢失的根因。"""
import sys, struct
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
def synth_trace(code,base,fix):
    out=[];pos=0;cap=len(code)
    while pos<cap-6:
        if code[pos]!=0xC7: pos+=1;continue
        modrm=code[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0):
            print('  skip at +%d: C7 %02x (mod=%d reg=%d rm=%d)'%(pos,modrm,mod,reg,rm))
            pos+=1;continue
        va=base+pos
        if mod==1:
            d=struct.unpack_from('<b',code,pos+2)[0];im=struct.unpack_from('<I',code,pos+3)[0]
            out.append((va,REGNAME[rm],d,im,'m1'));pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',code,pos+2)[0];im=struct.unpack_from('<I',code,pos+6)[0]
            out.append((va,REGNAME[rm],d,im,'m2'));pos+=10
        elif mod==0 and fix:
            im=struct.unpack_from('<I',code,pos+2)[0]
            out.append((va,REGNAME[rm],0,im,'m0'));pos+=6
        else: pos+=1
    return out
syn=bytes.fromhex('c70678563412'+'c7460478563412'+'c7860001000078563412'+'c70778563412')
print('synth 目标 4 条，期望 m0(esi)/m1(esi+4)/m2(esi+0x100)/m0(edi)')
print('实际:',[(hex(a),r,d,hex(i),k) for a,r,d,i,k in synth_trace(syn,0x1000,True)])

# 现网：697 -> 686 丢了哪 11 条
T=P.B['.text'];LO=T['lo'];RAW=P.RAW
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
def in_text(x): return x is not None and LO<=x<P.B['.text']['hi_file']
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
def extract(fix):
    recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-6:
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
        elif mod==0 and fix:
            im=struct.unpack_from('<I',RAW,pos+2)[0]
            recs.append((va,REGNAME[rm],0,im,'m0'));pos+=6
        else: pos+=1
    return recs
o=extract(False); n=extract(True)
os_=set(r[0] for r in o); ns_=set(r[0] for r in n)
print('\n旧 %d 新 %d，旧有-new有 = %d 条'%(len(o),len(n),len(os_-ns_)))
for a in sorted(os_-ns_):
    i=LO+(a-LO)
    off=P.r2o(a)
    print('  丢: %s 前16字节=%s'%(hex(a),RAW[off-6:off+10].hex()))
print('新增 %d 条'%len(ns_-os_))
