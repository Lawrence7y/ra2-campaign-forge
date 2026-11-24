#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W29 recon2: CSF/string-table loader + control-flow closure. Read-only."""
import struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
data = open(EXE,"rb").read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin1"), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
def va2off(va):
    rva=va-IB
    for n,srva,vsz,raw,rsz in secs:
        if srva<=rva<srva+max(vsz,rsz):
            o=raw+(rva-srva)
            if o<raw+rsz: return o
    return None
def off2va(off):
    for n,rva,vsz,raw,rsz in secs:
        if raw<=off<raw+rsz: return IB+rva+(off-raw)
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32)
def disasm(va,n,label=""):
    off=va2off(va)
    print("\n---- DISASM %s VA=0x%08X RVA=0x%08X FOFF=0x%08X (n=%d) ----"%(label,va,va-IB,off if off is not None else -1,n))
    if off is None: print(" !! unmapped"); return
    c=0
    for i in md.disasm(data[off:off+n*8],va):
        o=va2off(i.address)
        print("  VA=0x%08X RVA=0x%08X FOFF=0x%08X  %-22s  %-7s %s"%(i.address,i.address-IB,o if o is not None else -1," ".join("%02X"%x for x in i.bytes),i.mnemonic,i.op_str))
        c+=1
        if c>=n: break

def cstr(va,maxlen=180):
    off=va2off(va)
    if off is None: return "<unmapped>"
    b=data[off:off+maxlen]
    z=b.find(b"\x00")
    s=b if z<0 else b[:z]
    return repr(s)

print("==== C-STRING CONTEXTS (CSF / lang related) ====")
for va in [0x840C58,0x840C6E,0x840C71,0x840C78,0x840CAF,0x840CB2,0x840CFD,0x840D00,0x840D40,0x840D4C,0x840D5C,0x8457EC,0x82C15B,0x826198,0x8261A8,0x827B04,0x81B1D8]:
    print("  VA=0x%08X FOFF=0x%08X  %s"%(va,va2off(va) or -1,cstr(va)))

def find_all(h,n):
    o=[];s=0
    while True:
        p=h.find(n,s)
        if p<0:break
        o.append(p);s=p+1
    return o
def xrefs(va,label):
    pat=struct.pack("<I",va);hits=find_all(data,pat)
    print("\n---- XREF imm32 0x%08X (%s): %d ----"%(va,label,len(hits)))
    for h in hits[:30]:
        sec="?"
        for n,rva,vsz,raw,rsz in secs:
            if raw<=h<raw+rsz:sec=n
        p2=data[h-2] if h>=2 else 0;p1=data[h-1] if h>=1 else 0
        hint=""
        if p1==0x68:hint="push imm32"
        elif 0xB8<=p1<=0xBF:hint="mov r32,imm32"
        elif p2==0xFF and p1==0x15:hint="call [imm32]"
        print("   FOFF=0x%08X VA=0x%08X sec=%-7s prev=%02X %02X %s"%(h,off2va(h) or -1,sec,p2,p1,hint))
    if len(hits)>30:print("   ...+%d"%(len(hits)-30))

print("\n==== XREFS to language/CSF literal VAs ====")
for va,lab in [(0x840C58,"'Unable to initialize'"),(0x840C6E,"'ra2.csf'#1"),(0x840CAF,"'ra2.csf'#2"),(0x840CFD,"'ra2.csf'#3"),(0x840D00,"'.csf' tail"),(0x840D40,"'ra2md.str'"),(0x840D4C,"'LANGUAGE.MIX'"),(0x840D5C,"'LANGMD.MIX'"),(0x8457EC,"'.csf'#4"),(0x827B04,"'DESC:'")]:
    xrefs(va,lab)

print("\n==== IAT RESOLVE (pefile DIRECTORY_ENTRY_IMPORT) ====")
pe2=pefile.PE(EXE)
imp={}
for d in pe2.DIRECTORY_ENTRY_IMPORT:
    dll=d.dll.decode("latin1")
    for e in d.imports:
        imp[e.address]= (dll, e.name.decode("latin1") if e.name else "ord%d"%e.ordinal)
for slot in [0x7E11BC,0x7E1208,0x7E120C,0x7E1300,0x7E1148,0x7E11A8,0x7E1460,0x7E1200,0x7E11E0]:
    print("  [0x%08X] -> %s"%(slot,imp.get(slot,"<not in first thunk / not found>")))

disasm(0x473D9B,60,"Get_File continued (MIX hit / seek / fail)")
disasm(0x473E01,24,"Get_File 0x473E01 (MIX cached -> BufferClass)")
disasm(0x473E24,14,"Get_File 0x473E24 (both miss -> fail)")
disasm(0x473E39,30,"Get_File 0x473E39 (disk read path)")
disasm(0x5B4507,30,"MixFileClass::Find tail (next MIX / hit return)")
disasm(0x6BD835,44,"Startup 0x6BD835 (string-table gate, correctly synced)")
disasm(0x7346A0,130,"0x7346A0 string-table loader (part 1)")
disasm(0x734777,20,"0x734777 (Get_File call #1 in str loader)")
disasm(0x7349C2,20,"0x7349C2 (Get_File call #2 in str loader)")
disasm(0x734947,20,"0x734947 (empty-name branch)")
disasm(0x734F50,30,"0x734F50 (other callers of 0x7346A0)")
print("\nDONE recon2")
