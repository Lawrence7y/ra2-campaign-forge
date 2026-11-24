# -*- coding: utf-8 -*-
"""Verify: (1) [0xA8E9A0] op.access 23W/100R + cmp breakdown; (2) gate fn this class via vtable; (3) literal values of the 11 sites."""
import pefile, struct, hashlib
from capstone import *
from capstone.x86 import *
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(EXE,"rb").read()
print("SHA256",hashlib.sha256(data).hexdigest().upper())
pe = pefile.PE(EXE, fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1")
    secs.append(dict(name=nm,va=BASE+s.VirtualAddress,vsize=s.Misc_VirtualSize,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
def sec_of(va):
    for s in secs:
        if s["va"]<=va<s["va"]+max(s["vsize"],s["rawsize"]): return s
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]; TRAW=TEXT["raw"]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
# 1) global access count
W=[];R=[];mn={}
va=T0
while va<T1:
    got=list(md.disasm(data[TRAW+(va-T0):TRAW+(va-T0)+16],va,count=1))
    if not got: va+=1; continue
    i=got[0]
    try: ops=i.operands
    except: ops=[]
    for k,o in enumerate(ops):
        if o.type==X86_OP_MEM and o.mem.base==0 and o.mem.index==0 and (o.mem.disp&0xFFFFFFFF)==0xA8E9A0:
            w=bool(o.access&CS_AC_WRITE)
            (W if w else R).append(i.address)
            mn[i.mnemonic]=mn.get(i.mnemonic,0)+1
    va+=i.size
print("\n=== [0xA8E9A0] linear .text capstone op.access ===")
print("writes=%d reads=%d total=%d"%(len(W),len(R),len(W)+len(R)))
print("mnemonic histogram (all accesses):",sorted(mn.items(),key=lambda x:-x[1]))
print("cmp count:",mn.get('cmp',0))
print("write addresses:",[hex(x) for x in W])
# 2) gate fn 47C620 vtable slot -> class
print("\n=== gate fn 47C620 vtable slots & class ===")
def try_col(vt):
    p=u32(vt-4)
    if p and sec_of(p):
        td=u32(p+0xC)
        if td and sec_of(td):
            b=rd(td+8,96);z=b.find(b"\x00")
            nm=b[:z].decode('latin1') if z!=-1 else ''
            if nm.startswith('.?AV'): return hex(p),hex(td),nm
    return None
for s in secs:
    if s["name"]==".text": continue
    for off in range(0,s["rawsize"]-3,4):
        v=struct.unpack_from("<I",data,s["raw"]+off)[0]
        if v==0x47C620:
            slot=s["va"]+off
            print("  slot %08X"%slot)
            for base in range(slot,slot-0x100,-4):
                r=try_col(base)
                if r: print("    vtable_base candidate %08X -> %s"%(base,r)); break
# 3) literal values of 11 sites: read the imm byte from instruction bytes
print("\n=== literal imm byte at the 11 sites (byte at site+1..+3) ===")
for sa in [0x4CCA64,0x5C0247,0x5C0920,0x76AB55,0x77A74D,0x7B23F4,0x7CD0C0,0x7CD0C9,0x7CD0F7,0x7CD12D,0x7CD1B8]:
    b=rd(sa,8)
    print("  %08X: %s"%(sa,b.hex(' ')))
