# -*- coding: utf-8 -*-
"""Global map of vptr-install sites: every `mov <mem>, imm32` whose imm is in
the vtable VA range. Groups by target vtable. Independent of final.tsv."""
import io, os, sys, json, bisect
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
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
text = pe.sections[0]
text_va = IB + text.VirtualAddress
text_sz = text.Misc_VirtualSize
code = bytes(buf[text_va - IB:text_va - IB + text_sz])

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
mdv = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdv.detail = True
mdv.skipdata = True

stores = []
n = 0
for i in md.disasm(code, text_va):
    n += 1
    if i.mnemonic != "mov" or len(i.operands) != 2:
        continue
    a, b = i.operands
    if a.type != capstone.x86.X86_OP_MEM or b.type != capstone.x86.X86_OP_IMM:
        continue
    v = b.imm & 0xFFFFFFFF
    if not (0x7E0000 <= v < 0x800000):
        continue
    base = i.reg_name(a.mem.base) if a.mem.base else "ABS"
    stores.append((i.address, v, base, a.mem.disp, i.op_str, i.size))

print("insns=%d  vptr-stores=%d" % (n, len(stores)), file=sys.stderr)
io.open(os.path.join(HERE, "vptr_stores.tsv"), "w", encoding="utf-8").write(
    "site\tvt\tbase\tdisp\tsize\tinsn\n" +
    "\n".join("%08X\t%08X\t%s\t%08X\t%d\t%s" % (s[0], s[1], s[2], s[3], s[5], s[4]) for s in stores))

# index by vt
by_vt = {}
for s in stores:
    by_vt.setdefault(s[1], []).append(s)

VT = {
 '0040B880': 0x7E17CC, '0040B930': 0x7E17CC, '0040F7C0': 0x7E1E84, '0040F870': 0x7E1E84,
 '0040FD90': 0x7E1ED4, '0040FE40': 0x7E1ED4, '00410260': 0x7E1F50, '00413F80': 0x7E22A4,
 '0041C180': 0x7E22A4, '00431E80': 0x7E3A2C, '00431F70': 0x7E3A2C, '004322A0': 0x7E1668,
 '004324B0': 0x7E1668, '004393D0': 0x7E3D10, '004393F0': 0x7E3D10, '00459EC0': 0x7E3EBC,
 '0046B7E0': 0x7E4678, '0046B890': 0x7E4678,
}
SITE = {
 '0040B880': 0x40B563, '0040B930': 0x40B563, '0040F7C0': 0x40F4AD, '0040F870': 0x40F4AD,
 '0040FD90': 0x40FB4D, '0040FE40': 0x40FB4D, '00410260': 0x410198, '00413F80': 0x413D87,
 '0041C180': 0x413D87, '00431E80': 0x431A8A, '00431F70': 0x431A8A, '004322A0': 0x4014C4,
 '004324B0': 0x4014C4, '004393D0': 0x4385E1, '004393F0': 0x4385E1, '00459EC0': 0x43B71F,
 '0046B7E0': 0x4662FD, '0046B890': 0x4662FD,
}
print()
print("### All install sites per vtable used by this batch")
seen = set()
for e in sorted(VT):
    vt = VT[e]
    if vt in seen:
        continue
    seen.add(vt)
    lst = by_vt.get(vt, [])
    print("vt=%08X  total_install_sites=%d" % (vt, len(lst)))
    for s in sorted(lst):
        chosen = "   <== CHOSEN for %s" % e if s[0] == SITE[e] else ""
        print("    site=%08X base=%-4s disp=%08X insn=%s%s" % (s[0], s[2], s[3], s[4], chosen))
    if not lst:
        print("    !! no install site found by linear sweep")
