# -*- coding: utf-8 -*-
"""U3 closure: verify no branch in 0x6F2B40 skips 0x6F3237 bit-0 setter."""
import struct, pefile, hashlib
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
BITSET=0x6F3237
FN_END=0x6F3900  # approximate end
print("=== branches in 0x6F2B40 that could skip 0x6F3237 ===")
found=0
for a,sz,mn,op in disasm(0x6F2B40,0x6F3900):
    if mn.startswith('j') or mn=='ret':
        # parse target
        target=None
        if op.startswith('0x'):
            try: target=int(op,16)
            except: pass
        if target is not None and 0x6F2B40<=target<0x6F3900:
            if a<BITSET<target:
                print("  SKIP CANDIDATE: %08X %s -> %08X (jumps past bit-set)" % (a,mn,target))
                found+=1
        elif mn=='ret' and a<BITSET:
            print("  RET before bit-set at %08X" % a); found+=1
print("skip candidates:",found)
print("\n=== context 0x6F3210..0x6F3245 ===")
for a,sz,mn,op in disasm(0x6F3210,0x6F3245):
    print("  %08X  %-7s %s" % (a,mn,op))
