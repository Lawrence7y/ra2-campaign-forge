# -*- coding: utf-8 -*-
"""Byte-level audit of every 0x7E1668 immediate occurrence. Read-only."""
import io, os, sys
sys.dont_write_bytecode = True
IB = 0x400000
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
import pefile, capstone
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.get_data(),
                 s.Name.rstrip(b"\x00").decode("latin-1")))
end = max(va + max(vs, rs) for va, vs, rs, _d, _n in secs)
buf = bytearray(end - IB + 16)
sec_of = {}
for va, vs, rs, d, nm in secs:
    buf[va-IB:va-IB+len(d)] = d
    for o in range(va-IB, va-IB+len(d)): sec_of[o]=nm
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True; md.skipdata = True

pat = bytes([0x68,0x16,0x7E,0x00])
occ=[]
for o in range(0,len(buf)-4):
    if buf[o:o+4]==pat: occ.append(o)
print("raw occurrences=",len(occ))

# For each occurrence, show 12 bytes before + imm, and try decode from each candidate start
print("\n=== UNDECODED-as-mem-store occurrences (byte context) ===")
for o in occ:
    va=IB+o
    decoded_store=None
    for back in range(0,16):
        s=va-back
        if s<IB: continue
        r=list(md.disasm(bytes(buf[s-IB:s-IB+24]),s,count=1))
        if not r: continue
        ins=r[0]
        if ins.address+ins.size!=va+4: continue
        if ins.mnemonic!="mov": continue
        op=ins.operands
        if len(op)==2 and op[0].type==capstone.x86.X86_OP_MEM and op[1].type==capstone.x86.X86_OP_IMM and (op[1].imm&0xffffffff)==0x7E1668:
            decoded_store=ins; break
    if decoded_store is None:
        ctx=bytes(buf[o-12:o+4])
        print(" %08X ctx=%s sec=%s" % (va,ctx.hex(),sec_of.get(o,"?")))

print("\n=== non-esp/ebp decoded stores full context ===")
for o in occ:
    va=IB+o
    for back in range(0,16):
        s=va-back
        if s<IB: continue
        r=list(md.disasm(bytes(buf[s-IB:s-IB+24]),s,count=1))
        if not r: continue
        ins=r[0]
        if ins.address+ins.size!=va+4: continue
        if ins.mnemonic!="mov": continue
        op=ins.operands
        if len(op)==2 and op[0].type==capstone.x86.X86_OP_MEM and op[1].type==capstone.x86.X86_OP_IMM and (op[1].imm&0xffffffff)==0x7E1668:
            mo=op[0].mem
            base=ins.reg_name(mo.base) if mo.base else ""
            if base not in ("esp","ebp"):
                ctx=bytes(buf[s-IB-8:s-IB+ins.size+8])
                print(" site=%08X bytes=%s op='%s %s' base=%s disp=0x%x ctx=%s" %
                      (s,ins.bytes.hex(),ins.mnemonic,ins.op_str,base,mo.disp&0xffffffff,ctx.hex()))
            break
