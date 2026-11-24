# -*- coding: utf-8 -*-
"""U3: InfantryClass factory Create -> constructor + trace +0x14 writes in ObjectClass base."""
import struct, pefile, hashlib, bisect
from capstone import *
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
def va_of_fo(fo):
    for s in secs:
        if s["raw"]<=fo<s["raw"]+s["rawsize"]: return s["va"]+(fo-s["raw"]),s["name"]
    return None,None

# Find InfantryClass factory TD
name=b".?AV?$TClassFactory@VInfantryClass@@@@"
i=data.find(name)
if i>=0:
    va,_=va_of_fo(i); TD=va-8
    print("InfantryClass factory TD=%08X" % TD)
    # COLs
    pat=struct.pack("<I",TD); j=data.find(pat); cols=[]
    while j!=-1:
        v,_=va_of_fo(j)
        if v:
            c=v-0xC
            if u32(c) in (0,1): cols.append(c)
        j=data.find(pat,j+1)
    print("COLs: %s" % " ".join("%08X"%c for c in cols))
    for c in cols:
        patc=struct.pack("<I",c); k=data.find(patc); vts=[]
        while k!=-1:
            v,_=va_of_fo(k)
            if v and k%4==0: vts.append(v+4)
            k=data.find(patc,k+1)
        for vt in vts:
            slots=[u32(vt+4*n) for n in range(8)]
            print("  COL %08X vt %08X slots: %s" % (c,vt," ".join("%08X"%s for s in slots)))
            # find Create = slot with a call to operator new / a constructor; disassemble each slot fn briefly
            for n,s in enumerate(slots):
                if s and 0x401000<=s<0x7e1000:
                    code=[mn for a,sz,mn,op in disasm(s,s+0x30)]
                    if 'call' in code[:12]:
                        pass
else:
    print("INF factory name not found")

# Search all functions for 'or byte [reg+0x14],1' pattern (80 4? 14 01) via disasm across likely ObjectClass methods
print("\n=== search byte pattern: same-function writes [reg+0x14] with OR 1 ===")
T=[s for s in secs if s["name"]==".text"][0]; T0,T1=T["va"],T["va"]+T["rawsize"]; TR=T["raw"]
# raw byte patterns for 'or byte ptr [reg+0x14],1' : 80 48..4F 14 01 (no disp32), and 80 8? 14 00 00 00 01 (disp32)
for pat_desc,pat in [("or byte [reg+0x14],1 (short)",bytes.fromhex("8048")),]:
    pass
# simpler: scan disasm for 'or byte ptr [X + 0x14], 1' or 'mov byte...,1' over full text with capstone (reuse earlier rows saved file)
# Instead print known setter function 0x4D31E0 and 0x5F3900 full to find bit0 set
print("\n--- 0x5F3900 full to find bit0 writes ---")
for a,sz,mn,op in disasm(0x5F3900,0x5F3B00):
    if '0x14' in op and '[' in op:
        print("  %08X  %-7s %s" % (a,mn,op))
