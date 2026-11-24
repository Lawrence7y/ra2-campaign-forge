# -*- coding: utf-8 -*-
# R17-R21-6F4A70_SEM : reproducible static RE of 0x6F4A70. Read-only on image.
import struct, os, hashlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = os.path.dirname(os.path.abspath(__file__))
d = open(IMG,"rb").read()
sha = hashlib.sha256(d).hexdigest().upper()
pe=struct.unpack_from("<I",d,0x3c)[0]; coff=pe+4
nsec=struct.unpack_from("<H",d,coff+2)[0]; opt=coff+20
ib=struct.unpack_from("<I",d,opt+28)[0]
sect=opt+struct.unpack_from("<H",d,coff+16)[0]
secs=[]
for i in range(nsec):
    o=sect+i*40; nm="".join(chr(b) if 32<=b<127 else "." for b in d[o:o+8])
    vs,va,rs,ra=struct.unpack_from("<IIII",d,o+8); secs.append((nm,va,vs,ra,rs))
def off(va):
    r=va-ib
    for nm,va0,vs,ra,rs in secs:
        if va0<=r<va0+max(vs,rs): return ra+(r-va0)
    return None
def u32(va):
    o=off(va); return struct.unpack_from("<I",d,o)[0] if o is not None else None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
START=0x6F4A70; LAST_RET_END=0x6F4AA3; NEXT=0x6F4AB0
# --- disasm.txt ---
o=off(START); code=d[o:o+(NEXT-START)]
dl=["; IMAGE: "+IMG,
    "; SHA256: "+sha,
    "; VA->file: imagebase=%08X .text RVA %08X RA %08X (fileoff = VA-0x400000)"%(ib,secs[0][1],secs[0][3]),
    "; pre-anchor: 0x6F4A63 C3(ret) + 12x90 -> entry 0x6F4A70",
    "; tail(byte-measured): last RET 0x6F4AA0 C2 04 00 ends 0x6F4AA3;",
    ";   0x6F4AA3..0x6F4AAF = 13x90 pad; next func anchor 0x6F4AB0: 83 EC 0C",
    "; body length = 0x%X (51) bytes; to next anchor = 0x%X (64) bytes"%(LAST_RET_END-START,NEXT-START),
    "; --- anchored full-function disassembly ---"]
for ins in md.disasm(code,START):
    if ins.address>=NEXT: break
    tag=""
    if ins.mnemonic=="call": tag="  ; CALL"
    if ins.mnemonic=="ret": tag="  ; RET-EXIT"
    dl.append("%08X: %-20s %-6s %s%s"%(ins.address,ins.bytes.hex(" "),ins.mnemonic,ins.op_str,tag))
open(os.path.join(OUT,"disasm.txt"),"w",encoding="utf-8").write("\n".join(dl)+"\n")
# --- calls.tsv ---
rows=["address\tform\ttarget\tverdict",
"0x6F4A78\tdirect rel32 (E8)\t0x5F5850\tthiscall helper(this=ecx,stack arg=[esp+4]); symbolic name NOT obtained",
"0x6F4A91\tindirect [reg+disp] (FF /2)\tvptr+0x274 = vtable slot #157\tvirtual call: target NOT unique; base TechnoClass vtable 0x7F4960 slot157=0x65ACB0 is only one family member",
""]
open(os.path.join(OUT,"calls.tsv"),"w",encoding="utf-8").write("\n".join(rows))
print("IMAGE:",IMG)
print("SHA256:",sha)
print("slice 0x6F4A70..0x6F4AA2 len",0x33,"pad",13,"next",hex(NEXT))
print("wrote disasm.txt, calls.tsv")
