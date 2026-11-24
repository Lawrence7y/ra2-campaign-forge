"""S13-K1: locate constructors by scanning .text for the class's own vtable
immediate written to [reg+disp], then attribute via function INTERVAL CONTAINMENT
(discipline #14, not entry_at_or_before). Dump all [reg+off] writes in ctor.
Also find GetSize/`new` allocation call sites for cross-check."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *

VTS = {
 "WeaponTypeClass":  [0x7F738C,0x7F7394,0x7F739C,0x7F73B8],
 "WarheadTypeClass": [0x7F6B04,0x7F6B0C,0x7F6B14,0x7F6B30],
 "BulletTypeClass":  [0x7E491C,0x7E4924,0x7E492C,0x7E4948],
 "BulletClass":      [0x7E46B8,0x7E46C0,0x7E46C8,0x7E46E4],
}
MD.skipdata = True
lines=[]
def p(x=""): lines.append(str(x))

# sweep .text raw for `c7 <modrm> <vt bytes>` = mov [reg+disp], imm32  (C7 /0)
# we just scan all instructions linearly and look for mov with imm==vt and mem dest
TEXT_LO, TEXT_HI = TEXT[1], TEXT[2]
start_off = TEXT[3]; end_off = TEXT[4]
import capstone
for cls, vts in VTS.items():
    p(f"\n=== {cls}: ctor candidates (mov [mem],vtable) ===")
    hits = {}
    # linear sweep whole .text with skipdata=True
    for insn in MD.disasm(DATA[start_off:end_off], TEXT_LO):
        if insn.mnemonic != "mov" or len(insn.operands) != 2: continue
        d, s = insn.operands
        if s.type != capstone.x86.X86_OP_IMM: continue
        imm = s.imm & 0xFFFFFFFF
        if imm in vts and d.type == capstone.x86.X86_OP_MEM:
            fn = fn_at(insn.address)
            hits.setdefault(fn, []).append((insn.address, imm, d.mem.disp, fmt_insn(insn)))
    for fn, hs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        p(f"  fn {hex(fn) if fn else 'NONE'} (atlas={ATLAS_FN.get(fn)}): {len(hs)} vtable-writes")
        for h in hs[:8]: p("     " + h[3])
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ctor_candidates.txt","w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
