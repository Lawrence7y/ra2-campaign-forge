"""Dump vtable slots for combat classes (RTTI-measured vtables from S13-K1, NOT vtables_v2.json).
Measure slot count by .rdata contiguous pointer run; read slots directly.
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R

out = []
def p(s=""):
    out.append(str(s))

# RTTI-measured vftables (S13-K1 EVIDENCE/rtti_extract.txt) + doc clue vtables
VT = {
    "WeaponTypeClass": 0x7F73B8,
    "WarheadTypeClass": 0x7F6B30,
    "BulletTypeClass": 0x7E4948,
    "BulletClass": 0x7E46E4,
    "TechnoClass(clue)": 0x7F4960,
    "BuildingClass(clue)": 0x7E3EBC,
    "FootClass(clue)": 0x7E8C94,
    "UnitClass(clue)": 0x7F5C70,
    "InfantryClass(clue)": 0x7EB058,
    "AircraftClass(clue)": 0x7E22A4,
}

KNOWN = {
    0x6FDD50: "TechnoClass::Fire (doc v243)",
    0x415EE0: "Foot/Aircraft Fire wrapper (doc)",
    0x741340: "Unit Fire wrapper (doc)",
    0x51DF60: "Infantry Fire wrapper (doc)",
    0x466380: "BulletClass ctor (S13-K1)",
    0x4664C0: "BulletClass::Construct (doc)",
    0x4666E0: "BulletClass::AI/Update (doc v23)",
    0x468D80: "BulletClass::Fire (doc)",
    0x4690B0: "BulletClass::Detonate (doc)",
    0x468430: "BulletClass::LoseTarget (doc)",
    0x468090: "BulletClass::Draw (doc v69)",
    0x701900: "TechnoClass::ReceiveDamage (doc v91)",
    0x70D690: "FireDeathWeapon (doc)",
    0x489280: "DamageArea (doc)",
    0x4891C6: "V1 Verses scale block (doc)",
}

p("=== Vtable slot runs (contiguous in .rdata; atlas-independent) ===")
for name, va in VT.items():
    # count forward while u32 is a code address in .text
    n = 0
    while True:
        v = R.u32(va + 4 * n)
        if v is None or not (R.TEXT[1] <= v < R.TEXT[2]):
            break
        n += 1
        if n > 400:
            break
    p(f"\n{name} vt=0x{va:08X} run_len={n}")
    # print slots that match known addresses
    for i in range(n):
        v = R.u32(va + 4 * i)
        if v in KNOWN:
            p(f"   slot {i} (+0x{4*i:X}) -> 0x{v:08X}  {KNOWN[v]}")

p("\n=== Verify specific slot indices from card/doc ===")
checks = [
    ("TechnoClass v243 Fire", 0x7F4960, 243),
    ("TechnoClass v241 GreatestThreat", 0x7F4960, 241),
    ("BulletClass v23 AI/Update", 0x7E46E4, 23),
    ("BulletClass v69 Draw", 0x7E46E4, 69),
    ("BulletClass v124 MoveTo", 0x7E46E4, 124),
    ("FootClass v243 Fire", 0x7E8C94, 243),
    ("UnitClass v243 Fire", 0x7F5C70, 243),
    ("InfantryClass v243 Fire", 0x7EB058, 243),
    ("BuildingClass v243 Fire", 0x7E3EBC, 243),
    ("WarheadTypeClass v25 loader", 0x7F6B30, 25),
    ("BulletTypeClass v25 loader", 0x7E4948, 25),
]
for label, vt, slot in checks:
    v = R.u32(vt + 4 * slot)
    p(f"   {label}: vt+0x{4*slot:X} -> 0x{v:08X}" + (f"  [{KNOWN.get(v,'')}]" if v in KNOWN else ""))

txt = "\n".join(out)
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE\vt_slots.txt", "w", encoding="utf-8").write(txt)
print(txt)
