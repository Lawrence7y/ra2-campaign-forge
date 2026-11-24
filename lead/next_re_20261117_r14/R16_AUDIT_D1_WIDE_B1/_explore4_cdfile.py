# -*- coding: utf-8 -*-
"""Deep dive: CDFileClass site 004014C4 / host 004011C0, plus prologues of the
other ctor_body hosts. Decide whether host is really a constructor/factory."""
import io, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
IB = 0x400000
import pefile, capstone

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d

def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o + 4], "little") if 0 <= o <= len(buf) - 4 else None

def cstr(va, n=200):
    o = va - IB
    if o < 0 or o >= len(buf):
        return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

def rtti_of(vt):
    col = u32(vt - 4)
    if not col:
        return None
    sig, off, cd, td = u32(col), u32(col + 4), u32(col + 8), u32(col + 12)
    return dict(col=col, sig=sig, off=off, cd=cd, td=td, mg=cstr(td + 8) if td else None)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, n=64):
    o = va - IB
    return list(md.disasm(bytes(buf[o:o + n]), va))

print("### RTTI identity of vtables in play")
for vt in (0x7E1668, 0x7E16B0, 0x7E1F50, 0x7E22A4, 0x7E3A2C, 0x7E3D10, 0x7E3EBC,
           0x7E17CC, 0x7E1E84, 0x7E1ED4, 0x7E4678):
    print("  vt=%08X -> %s" % (vt, rtti_of(vt)))

print()
print("### 004011C0 (claimed host of CDFileClass rows) head")
for ins in dis(0x4011C0, 96):
    print("   %08X: %-10s %s" % (ins.address, ins.mnemonic, ins.op_str))

print()
print("### full linear disasm 0x4011C0 .. 0x4014E0 (which function region? prints selectively)")
ins_all = dis(0x4011C0, 0x330)
print("   total insns decoded:", len(ins_all), "last addr=%08X" % ins_all[-1].address)
# find rets and any 'mov [mem], imm' writes of vtable-like values
rets = [i for i in ins_all if i.mnemonic in ("ret", "retf", "retn")]
print("   rets at:", [("%08X" % i.address) for i in rets])
vt_writes = []
for i in ins_all:
    if i.mnemonic == "mov" and len(i.operands) == 2:
        a, b = i.operands
        if a.type == capstone.x86.X86_OP_MEM and b.type == capstone.x86.X86_OP_IMM:
            v = b.imm & 0xFFFFFFFF
            if 0x7E0000 <= v <= 0x7FFFFF:
                reg = i.reg_name(a.mem.base) if a.mem.base else "ABS"
                vt_writes.append((i.address, reg, a.mem.disp, v))
for w in vt_writes:
    print("   vptr-write %08X: base=%-4s disp=%08X value=%08X   (site=%s)" % (
        w[0], w[1], w[2], w[3], "YES" if w[0] == 0x4014C4 else ""))

print()
print("### calls made by 004011C0 region (direct)")
for i in ins_all:
    if i.mnemonic == "call" and i.operands and i.operands[0].type == capstone.x86.X86_OP_IMM:
        print("   %08X -> %08X" % (i.address, i.operands[0].imm & 0xFFFFFFFF))
