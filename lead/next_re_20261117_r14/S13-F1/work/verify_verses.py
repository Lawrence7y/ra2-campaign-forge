"""Verify S13-K1 Verses = double[11] @ WarheadTypeClass+0xA0 (byte-level, atlas-independent).
Channels:
 A) loader 0x75D3A0: lea ebx,[esi+0xA0] / mov ebp,0xB / fstp qword[ebx] / add ebx,8
 B) ctor 0x75CEC0: lea esi,[ebp+0xA0] / mov ecx,0x14 / rep movsd (11 doubles = 0x58 bytes)
 C) FPU access sites: fmul/fld qword [reg+idx*8+0xA0] full .text sweep
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone

out = []
def p(s=""):
    out.append(str(s))

p("=== CHANNEL A: WarheadTypeClass::LoadFromINI 0x75D3A0 (Verses loader window) ===")
# Dump around 0x75DDE0..0x75DE60
p(R.dump_insns(R.disasm(0x75DDE0, 0x90)))

p("\n=== CHANNEL B: WarheadTypeClass ctor 0x75CEC0 (rep movsd init) ===")
p(R.dump_insns(R.disasm(0x75D180, 0x40)))

p("\n=== CHANNEL C: full .text sweep for FPU qword [reg+idx*8+0xA0] (capstone skipdata=True) ===")
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
MD.skipdata = True
base, hi = R.TEXT[1], R.TEXT[2]
hits = []
for insn in MD.disasm(R.read(base, hi - base), base):
    if insn.mnemonic not in ("fmul", "fld", "fstp", "fcomp", "fcom", "fild", "fistp", "movsd", "mulsd", "addsd", "comisd", "ucomisd"):
        continue
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.scale == 8 and op.mem.disp == 0xA0:
            hits.append((insn.address, insn.mnemonic, insn.op_str, R.fmt_insn(insn)))
for h in hits:
    p(f"   {h[0]:08X}  {h[1]}  {h[2]}   || {h[3]}")
p(f"\n   TOTAL FPU Verses-index accesses = {len(hits)}")
p("   (warhead_abi doc claims 9: V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)")

p("\n=== CHANNEL D: constant 0xB (loop count) near loader ===")
for va in (0x75DE0C,):
    p(f"   {va:08X}: bytes={R.read(va,8).hex(' ')} -> {R.fmt_insn(R.disasm(va,8)[0])}")
p("   default string @0x847C40 = " + repr(R.cstr(0x847C40, 128)))
p("   key 'Verses' @0x847C38 = " + repr(R.cstr(0x847C38, 16)))

p("\n=== CHANNEL E: ctor rep movsd count (0x14 dwords = 0x50 bytes = 10? or 0x58=11 doubles) ===")
p("   0x75D1A7 window:")
p(R.dump_insns(R.disasm(0x75D19C, 0x20)))

txt = "\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE\verify_verses.txt", "w", encoding="utf-8").write(txt)
print(txt)
