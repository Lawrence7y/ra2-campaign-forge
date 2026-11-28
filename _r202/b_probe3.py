#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202-B probe3: full T1 region context + sensitivity target regions."""
import sys, struct, bisect
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def it(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if it(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MD={v:COL[VT[v]]['mdisp'] for v in VT};CLS={v:COL[VT[v]]['name'] for v in VT}
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)];INS=[];CALLAT=[];p=0
while p<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p:p+65536],LO+p):
        got=True;INS.append((off,sz,mn,op))
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if it(t): CALLAT.append((off,t))
        p+=sz
    if not got:p+=1
INS.sort();ADDRS=[a for a,_,_,_ in INS]
REG=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3': REG.append((st,a+sz));st=a+sz
if st<HI:REG.append((st,HI))
RL=[r[0] for r in REG]
def rof(v):
    i=bisect.bisect_right(RL,v)-1
    return REG[i] if i>=0 else None
SORT=sorted(set(t for _,t in CALLAT))
def host(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
allsite=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize'];RN=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
while pos<end-4:
    if RAW[pos]==0x66:
        if pos+2<end and RAW[pos+1]==0xC7:
            mo=RAW[pos+2]>>6;pos+=6 if mo==0 else (7 if mo==1 else 11);continue
        pos+=1;continue
    if RAW[pos]!=0xC7:pos+=1;continue
    mo=RAW[pos+1]>>6;rg=(RAW[pos+1]>>3)&7;rm=RAW[pos+1]&7
    if rg!=0 or rm==4 or (rm==5 and mo==0):pos+=1;continue
    va=LO+(pos-T['rawptr'])
    if mo==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0];allsite.append((va,RN[rm],d,im));pos+=7
    elif mo==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0];allsite.append((va,RN[rm],d,im));pos+=10
    else:
        im=struct.unpack_from('<I',RAW,pos+2)[0];allsite.append((va,RN[rm],0,im));pos+=6
vts=[r for r in allsite if r[3] in VT]
def fm(r):return '%s d=%d imm=%s md=%d %s'%(hex(r[0]),r[2],hex(r[3]),MD[r[3]],CLS[r[3]])
for target in (0x5d5b80,0x635f34,0x637114,0x638aa4,0x6cf196,0x6cf209,0x7b1b2b,0x7b27fb):
    r=rof(target);h=host(target)
    print('\n=== FULL %s reg=%s..%s callhost=%s'%(hex(target),hex(r[0]),hex(r[1]),hex(h) if h else 'None'))
    i0=bisect.bisect_left(ADDRS,r[0]);i1=bisect.bisect_left(ADDRS,r[1])
    for a,sz,mn,op in INS[i0:i1]:
        mark=' <<<<TARGET' if a==target else (' <<<<VTS' if any(a==s[0] for s in vts if r[0]<=s[0]<r[1]) else '')
        print('   %s %s %s%s'%(hex(a),mn,op,mark))
    if h and h!=r[0]:
        print('   --- caller contexts of upstream host %s ---'%hex(h))
        for c,t in CALLAT:
            if t!=h:continue
            ic=bisect.bisect_right(ADDRS,c)-1
            print('     CALL %s'%hex(c))
            for aa,sz,mn,op in INS[max(0,ic-9):ic+2]:print('       %s %s %s'%(hex(aa),mn,op))
for target in (0x6cf196,0x7b27fb):
    h=host(target);r=rof(h)
    print('\n=== SENSITIVITY forced %s into host-region %s..%s'%(hex(target),hex(r[0]),hex(r[1])))
    for s in vts:
        if r[0]<=s[0]<r[1]:print('   '+fm(s))
