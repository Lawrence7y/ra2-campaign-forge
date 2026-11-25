# -*- coding: utf-8 -*-
"""R128 deepseek auditor final verification. disasm_lite only, streaming, no detail=True."""
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().strip('\x00'),IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),
       s.PointerToRawData,s.Misc_VirtualSize,s.SizeOfRawData) for s in pe.sections]
def rd(va,n):
    for nm,lo,hi,ptr,vs,rs in SECS:
        if lo<=va<hi:
            off=va-lo
            if off>=rs: return b''
            return pe.__data__[ptr+off:ptr+off+min(n,rs-off)]
    return None
def u32(va):
    b=rd(va,4); return None if not b or len(b)<4 else struct.unpack('<I',b)[0]
def i32(va):
    b=rd(va,4); return None if not b or len(b)<4 else struct.unpack('<i',b)[0]
def cstr(va,n=200):
    b=rd(va,n)
    if not b: return None
    z=b.find(b'\x00'); return b[:z if z>=0 else len(b)].decode('latin-1')
d=open(EXE,'rb').read()
T=d[0x1000:0x1000+0x3e0000]; TVA=0x401000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def off(va): return va-TVA

# ---------- A ----------
print('### A. 0x87f7e8')
import re
raw=re.findall(re.escape(bytes.fromhex('c705e8f78700')),T)
print(' raw pattern c7 05 e8 f7 87 00 in .text:',len(raw))
for m in re.finditer(re.escape(bytes.fromhex('c705e8f78700')),T):
    va=m.start()+TVA
    imm=struct.unpack('<I',T[m.start()+6:m.start()+10])[0]
    print('  at %s imm=%s full=%s'%(hex(va),hex(imm),T[m.start():m.start()+10].hex()))
print(' raw 89 05 e8f78700 (mov [0x87f7e8],eax):',len(re.findall(re.escape(bytes.fromhex('8905e8f78700')),T)))
# resync sweep
writes=[]; refs=0
o=0; n=len(T)
while o<n:
    g=list(md.disasm_lite(T[o:o+16],TVA+o,1))
    if not g:
        o+=1; continue
    a,s,m,op=g[0]
    if '0x87f7e8' in op:
        refs+=1
        if op.startswith('dword ptr [0x87f7e8],'): writes.append((a,m,op,T[o:o+s].hex()))
    o+=s
print(' resync-sweep refs to 0x87f7e8:',refs,' write-form:',len(writes))
for w in writes: print('  ',hex(w[0]),w[1],w[2],w[3])
print(' BSS check rd(0x87f7e8,16)=',repr(rd(0x87f7e8,16)),' .data raw end VA=',hex(0x812000+0x6c000))
print(' section of 0x87f7e8:',[nm for nm,lo,hi,ptr,vs,rs in SECS if lo<=0x87f7e8<hi])

vt=0x7e1964
print(' [vt-4]=%s  [vt]=%s'%(hex(u32(vt-4)),hex(u32(vt))))
col=u32(vt-4)
print(' COL(%s) raw=%s'%(hex(col),rd(col,20).hex(' ')))
sig,uoff,cdoff,ptd,pchd=struct.unpack('<IIIII',rd(col,20))
print('  signature=%s offset=%s cdOffset=%s pTD=%s pCHD=%s'%(sig,hex(uoff),hex(cdoff),hex(ptd),hex(pchd)))
print('  TD raw=%s'%rd(ptd,16).hex(' '))
print('  class name=%r'%cstr(ptd+8))
chsig,chattr,chcnt,chbca=struct.unpack('<IIII',rd(pchd,16))
print('  CHD sig=%s attr=%s numBase=%d pBCA=%s'%(chsig,hex(chattr),chcnt,hex(chbca)))
for i in range(chcnt):
    bcd=u32(chbca+4*i)
    t,ncb,mdisp,pdisp,vdisp,attr=struct.unpack('<Iiiiii',rd(bcd,24))
    print('   [%2d] BCD=%s TD=%s name=%-22r ncb=%2d mdisp=%5d pdisp=%3d vdisp=%d attr=%s'%(
        i,hex(bcd),hex(t),cstr(t+8),ncb,mdisp,pdisp,vdisp,hex(attr)))
print('  slot0 = %s'%hex(u32(vt)))
print('  vtable dwords:',[hex(u32(vt+4*k)) for k in range(8)])

# ---------- B ----------
print('\n### B. GUIDs')
def gfmt(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8]); r=b[8:16]
    return '{%08X-%04X-%04X-%02X%02X-%s}'%(d1,d2,d3,r[0],r[1],''.join('%02X'%x for x in r[2:]))
for va in (0x7ea6e8,0x7e36c0,0x7f7c90):
    b=rd(va,16)
    print(' %s bytes=%s  ->  %s'%(hex(va),b.hex(' '),gfmt(b)))

# ---------- C ----------
print('\n### C. 0x7ea6e8 comparison sites')
o=0; hits=[]
while o<n:
    g=list(md.disasm_lite(T[o:o+16],TVA+o,1))
    if not g:
        o+=1; continue
    a,s,m,op=g[0]
    if '0x7ea6e8' in op: hits.append((a,s,m,op))
    o+=s
print(' hits:',len(hits))
for a,s,m,op in hits:
    seg=T[off(a):off(a)+32]
    print('  %s  %s %s   bytes=%s'%(hex(a),m,op,seg.hex()))
    idx=seg.find(b'\xf3\xa7')
    i=0; rel=[]
    for aa,ss,mm,oo in md.disasm_lite(seg,a):
        rel.append((hex(aa),mm,oo))
        if aa==a: rel_off=aa-a
    print('     32B window disasm:',rel)
    print('     f3a7 at rel=%s (abs=%s)'%(idx,hex(a+idx) if idx>=0 else None))
print(' raw count of bf e8 a6 7e 00 in .text:',len(re.findall(re.escape(bytes.fromhex('bfe8a67e00')),T)))

# ---------- D ----------
print('\n### D. 0x429270 +0xf0')
calls=[]
for a,s,m,op in md.disasm_lite(T[off(0x429270):off(0x429270)+0xf0],0x429270):
    print('  %x %-16s %s %s'%(a,T[off(a):off(a)+s].hex(),m,op))
    if m=='call' and op.startswith('dword ptr [') and '+' not in op and '-' not in op:
        calls.append((a,op))
print(' call dword ptr [reg] count:',len(calls))
for a,op in calls:
    reg=op[len('dword ptr ['):-1]
    last=None
    for a2,s2,m2,o2 in md.disasm_lite(T[off(0x429270):off(a)-0x429270],0x429270):
        if m2.startswith('mov') and o2.startswith(reg+','):
            last=(a2,m2,o2)
        elif m2 in ('xor','pop','push','lea','and','or','add','sub','inc','dec') and o2.startswith(reg+',') or o2==reg:
            if m2 not in ('push',): last=(a2,m2,o2)
    print('   %s reg=%s last-write=%s'%(hex(a),reg,last))

# ---------- E ----------
print('\n### E. 0x429360 +0x90')
edis=[]; edxw=[]
for a,s,m,op in md.disasm_lite(T[off(0x429360):off(0x429360)+0x90],0x429360):
    print('  %x %-16s %s %s'%(a,T[off(a):off(a)+s].hex(),m,op))
    if m=='mov' and op.startswith('edi, 0x'): edis.append((a,op))
    if m.startswith('mov') and op.startswith('dword ptr [edx],'): edxw.append((a,op,T[off(a):off(a)+s].hex()))
print(' mov edi,abs:',[(hex(a),o) for a,o in edis])
print(' writes [edx]:',[(hex(a),o,b) for a,o,b in edxw])
