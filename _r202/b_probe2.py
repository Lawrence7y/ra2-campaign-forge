#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202-B probe2: T1 fallback evidence, sensitivity control, 3/3/6 recheck."""
import sys, struct, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2] != 0: continue
        if P.where(w[i+3]) != '.data' or P.where(w[i+4]) != '.rdata': continue
        nm = P.cstr(w[i+3]+8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i] = dict(mdisp=s32(w[i+1]), name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata','.data'):
    base,w,n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i] = P.dw(base+4*i-4)
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}; CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
REGNAME = ['eax','ecx','edx','ebx','esp','ebp','esi','edi']
BUF = RAW[T['rawptr']:T['rawptr']+(HI-LO)]; INS=[]; CALLAT=[]; p2=0
while p2 < len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536], LO+p2):
        got=True; INS.append((off,sz,mn,op))
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t))
        p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]
REGION=[]; st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3': REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
SORT=sorted(set(t for _,t in CALLAT))
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
print('=== host_of vs reg_of for 8 none ===')
for a in (0x5d5b80,0x635f34,0x637114,0x638aa4,0x6cf196,0x6cf209,0x7b1b2b,0x7b27fb):
    r=reg_of(a); h=host_of(a)
    print('%s reg=%s..%s host=%s hostreg=%s..%s same=%s' % (hex(a),hex(r[0]),hex(r[1]),hex(h) if h else 'None',hex(reg_of(h)[0]) if h else '-',hex(reg_of(h)[1]) if h else '-', reg_of(h)==r if h else 'n/a'))
print('\n=== fallback targets: prologue + callers inside region ===')
for target in (0x635f34,0x637114,0x638aa4):
    r=reg_of(target)
    print('\n--- target %s region=%s..%s' % (hex(target),hex(r[0]),hex(r[1])))
    i0=bisect.bisect_left(ADDRS,r[0]); i1=bisect.bisect_left(ADDRS,r[1])
    for a,sz,mn,op in INS[i0:min(i1,i0+45)]: print('   PRO %s %s %s' % (hex(a),mn,op))
    calls=[(a,t) for a,t in CALLAT if r[0]<=t<r[1] or r[0]<=a<r[1]]
    print('   calls in/into region: %d %s' % (len(calls),[(hex(a),hex(t)) for a,t in calls[:12]]))
    for a,t in calls[:6]:
        ia=bisect.bisect_right(ADDRS,a)-1
        print('     CTX call %s -> %s' % (hex(a),hex(t)))
        for aa,sz,mn,op in INS[max(0,ia-10):ia+1]: print('       %s %s %s' % (hex(aa),mn,op))
print('\n=== INoticeSink 3/3/6 recheck ===')
allsite=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
while pos<end-4:
    if RAW[pos]==0x66:
        if pos+2<end and RAW[pos+1]==0xC7:
            mo=RAW[pos+2]>>6; pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
        pos+=1; continue
    if RAW[pos]!=0xC7: pos+=1; continue
    modrm=RAW[pos+1]; mod=modrm>>6; reg=(modrm>>3)&7; rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1; continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0]; im=struct.unpack_from('<I',RAW,pos+3)[0]; allsite.append((va,REGNAME[rm],d,im)); pos+=7
    elif mod==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0]; im=struct.unpack_from('<I',RAW,pos+6)[0]; allsite.append((va,REGNAME[rm],d,im)); pos+=10
    else:
        im=struct.unpack_from('<I',RAW,pos+2)[0]; allsite.append((va,REGNAME[rm],0,im)); pos+=6
vts=[r for r in allsite if r[3] in VT]
for a in (0x410174,0x4101c2,0x6e8008):
    r=reg_of(a); rs=[s for s in vts if r[0]<=s[0]<r[1]]
    subrs=[s for s in rs if MD[s[3]]!=0]
    ins=[s for s in rs if 'INoticeSink' in CLS[s[3]]]
    print('%s region=%s..%s vts=%d sub(mdisp!=0)=%d INoticeSink=%d sub_INotice=%d' % (hex(a),hex(r[0]),hex(r[1]),len(rs),len(subrs),len(ins),sum(1 for s in ins if MD[s[3]]!=0)))
    for s in subrs: print('    SUB %s d=%d imm=%s md=%d %s' % (hex(s[0]),s[2],hex(s[3]),MD[s[3]],CLS[s[3]]))
