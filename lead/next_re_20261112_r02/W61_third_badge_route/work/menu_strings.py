#!/usr/bin/env python3
# W61: resolve all string-VA immediates referenced by campaign-menu code 0x52D800..0x52F400
import sys, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=sys.argv[1]
data=open(EXE,"rb").read(); pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase
def rva2off(r):
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
    return None
def va2off(v): return rva2off(v-IB)
def cstr(va,n=100):
    o=va2off(va)
    if o is None: return None
    b=data[o:o+n].split(b"\x00")[0]
    if not b or any(c<0x20 or c>0x7e for c in b): return None
    return b.decode("latin1")
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
START=0x52D800; END=0x52F400
o=va2off(START); code=data[o:o+(END-START)]
seen={}
for ins in md.disasm(code,START):
    for op in ins.operands:
        if op.type==2:  # X86_OP_IMM
            v=op.imm & 0xFFFFFFFF
            if 0x810000<=v<=0x8B0000:
                s=cstr(v)
                if s and v not in seen:
                    seen[v]=(ins.address,s)
print("=== string-VA immediates in 0x52D800..0x52F400 ===")
for v,(addr,s) in sorted(seen.items()):
    print("  VA=0x%08X  used@0x%08X  %r" % (v,addr,s))
print("total unique: %d" % len(seen))
# also: all absolute .data addresses referenced (mov/mem) resolving to pointers-to-strings
print("\n=== pointer-to-string dereferences for globals 0x825C20..0x825CA8 (initial values) ===")
for va in range(0x825C20,0x825CAC,4):
    off=va2off(va)
    if off is None: continue
    w=struct.unpack_from("<I",data,off)[0]
    s=cstr(w) if 0x800000<=w<0x900000 else None
    print("  [0x%08X] = 0x%08X  %s" % (va,w, ("-> %r"%s) if s else ""))
