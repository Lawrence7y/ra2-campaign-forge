"""Check card's slot-85 guess + verify Fire wrappers call the 0x6FDD50 body."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R

out = []
def p(s=""): out.append(str(s))

p("=== Card hypothesis: Fire at +0x154 slot 85 -> what is it? ===")
for label, vt in [("TechnoClass", 0x7F4960), ("FootClass", 0x7E8C94)]:
    for slot in (85,):
        v = R.u32(vt + 4*slot)
        p(f"   {label} slot {slot} (+0x{4*slot:X}) -> 0x{v:08X}  atlas_fn={R.fn_at(v)}")

p("\n=== Fire wrappers: full disasm (verify they reach 0x6FDD50) ===")
for name, va, nb in [("Foot/Aircraft 0x415EE0", 0x415EE0, 96),
                     ("Unit 0x741340", 0x741340, 160),
                     ("Infantry 0x51DF60", 0x51DF60, 160)]:
    p(f"\n--- {name} ---")
    p(R.dump_insns(R.disasm(va, nb)))

txt = "\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE\fire_slots_wrappers.txt","w",encoding="utf-8").write(txt)
print(txt)
