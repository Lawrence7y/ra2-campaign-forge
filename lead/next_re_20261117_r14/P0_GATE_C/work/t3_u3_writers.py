# -*- coding: utf-8 -*-
"""U3: full 0x47C420 filter + check Unlimbo wrapper 0x5683C0 + identify +0x14 writers by RTTI."""
import struct, pefile, hashlib, bisect
from capstone import *
from capstone.x86 import *
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(EXE,"rb").read()
pe = pefile.PE(EXE, fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1")
    secs.append(dict(name=nm,va=BASE+s.VirtualAddress,vsize=s.Misc_VirtualSize,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
def sec_of(va):
    for s in secs:
        if s["va"]<=va<s["va"]+max(s["vsize"],s["rawsize"]): return s
    return None
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def disasm(start,end):
    out=[]; va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: out.append((va,1,"?","")); va+=1; continue
        i=got[0]
        try: ops=i.op_str
        except: ops=""
        out.append((i.address,i.size,i.mnemonic,ops)); va+=i.size
    return out

print("=== 0x47C3D0 filter code [0x47C420,0x47C450) ===")
for a,sz,mn,op in disasm(0x47C420,0x47C450):
    print("  %08X  %-7s %s" % (a,mn,op))

print("\n=== Unlimbo wrapper 0x5683C0: [reg+0x14] writes ===")
for a,sz,mn,op in disasm(0x5683C0,0x5687F0):
    if ('0x14' in op and '[' in op and 'esp' not in op):
        print("  >>> %08X  %-7s %s" % (a,mn,op))
print("  (full small scan done)")

# RTTI class of functions writing const 0/1 to [reg+0x14]
def col_class(colva):
    if u32(colva) not in (0,1): return None
    td=u32(colva+0xC)
    if td is None: return None
    b=rd(td+8,64); z=b.find(b"\x00")
    if z==-1: return None
    nm=b[:z].decode("latin1")
    return nm if nm.startswith(".?A") else None
def class_of_fn(f):
    pat=struct.pack("<I",f); out=[]
    for s in secs:
        if s["name"] not in (".rdata",".data"): continue
        blob=data[s["raw"]:s["raw"]+s["rawsize"]]; i=blob.find(pat)
        while i!=-1:
            if i%4==0:
                slot=s["va"]+i
                for back in range(0,0x300,4):
                    vb=slot-back; col=u32(vb-4)
                    if col is None: continue
                    nm=col_class(col)
                    if nm: out.append(nm); break
            i=blob.find(pat,i+1)
    return sorted(set(out))
WRITER_FNS = {
 0x4CC9A0:"4CCA5B/64", 0x59D6AD:"59DEA5", 0x5D5B60:"5D5B79",
 0x77A700:"77A71C/74D", 0x7B24E0:"7B251D", 0x7B3720:"7B377A",
 0x5C0240:"5C0247", 0x5C07D0:"5C0920",
 0x4D31E0:"4D34E0", 0x588C10:"588C1F", 0x58BF70:"58BFB9", 0x58C800:"58CE24",
 0x5F3900:"5F3B39", 0x5FA350:"5FA36D", 0x5FA620:"5FA75A", 0x6B9450:"6B94A1",
 0x6E8000:"6E8022", 0x6F2B40:"6F3237", 0x715C5E:"715C5E", 0x76AAF0:"76AB55",
 0x76ABE0:"76AC24", 0x76AC90:"76AD13", 0x76B180:"76B298", 0x779690:"7796C8",
 0x7B19C0:"7B19D8", 0x7C30D0:"7C317D",
}
print("\n=== RTTI classes of [reg+0x14] byte-writer functions ===")
for f,tags in WRITER_FNS.items():
    print("  fn %08X (tags %s): %s" % (f,tags,class_of_fn(f) or "UNRESOLVED"))
