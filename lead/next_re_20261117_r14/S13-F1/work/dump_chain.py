"""Dump full disassembly of every function on the fire->death chain + extract call-site tables.
Call-site attribution uses fn_at (interval containment, discipline #14).
Call TARGET addresses come from raw bytes (atlas-independent channel).
"""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"

FUNCS = [
    ("Techno_Fire", 0x6FDD50),
    ("Foot_Fire_wrapper", 0x415EE0),
    ("Unit_Fire_wrapper", 0x741340),
    ("Infantry_Fire_wrapper", 0x51DF60),
    ("Bullet_ctor", 0x466380),
    ("Bullet_Construct", 0x4664C0),
    ("Bullet_AI_Update", 0x4666E0),
    ("Bullet_Fire_hit", 0x468D80),
    ("Bullet_Detonate", 0x4690B0),
    ("Bullet_LoseTarget", 0x468430),
    ("DamageArea", 0x489280),
    ("V1_Verses_scale", 0x4891C6),
    ("ReceiveDamage", 0x701900),
    ("FireDeathWeapon", 0x70D690),
    ("ClearRefs_70D4A0", 0x70D4A0),
    ("GetTotalDamage_candidate", 0x4891C6),
]

KNOWN = {
    0x6FDD50:"TechnoClass::Fire", 0x415EE0:"Foot/Aircraft Fire wrap", 0x741340:"Unit Fire wrap",
    0x51DF60:"Infantry Fire wrap", 0x466380:"BulletClass ctor", 0x4664C0:"BulletClass::Construct",
    0x4666E0:"BulletClass::AI/Update", 0x468D80:"BulletClass::Fire(hit)", 0x4690B0:"BulletClass::Detonate",
    0x468430:"BulletClass::LoseTarget", 0x489280:"DamageArea", 0x4891C6:"V1 Verses scale block",
    0x701900:"TechnoClass::ReceiveDamage", 0x70D690:"FireDeathWeapon", 0x70D4A0:"ClearRefs",
    0x7C5F00:"_ftol", 0x65C7E0:"Randomizer::RandomRanged", 0x65C780:"Randomizer::Random",
    0x5657A0:"Map::TryGetCellAt", 0x568350:"Map::IsCellInMap",
}

all_calls = []
for name, va in FUNCS:
    sz = R.ATLAS_FN.get(va, {}).get("size")
    nb = sz if sz else 0x400
    insns = R.disasm(va, nb)
    # full dump to own file
    with open(os.path.join(EV, f"fn_{name}_{va:08X}.txt"), "w", encoding="utf-8") as f:
        f.write(f"; {name} @0x{va:08X} atlas_size={sz} n_insn={len(insns)}\n")
        f.write(R.dump_insns(insns))
        f.write("\n")
    # call sites
    for insn in insns:
        t = R.call_target(insn)
        if t is not None:
            parent = R.fn_at(t)
            all_calls.append((name, va, insn.address, t, parent,
                              KNOWN.get(t, KNOWN.get(parent, ""))))

# write call-site table
with open(os.path.join(EV, "call_sites.tsv"), "w", encoding="utf-8") as f:
    f.write("caller_func\tcaller_entry\tcall_site\ttarget\ttarget_fn_interval\tname\n")
    for row in all_calls:
        f.write(f"{row[0]}\t0x{row[1]:08X}\t0x{row[2]:08X}\t0x{row[3]:08X}\t0x{row[4]:08X}\t{row[5]}\n")

print("Dumped", len(FUNCS), "functions; extracted", len(all_calls), "call sites")
# Print call sites for key hops
keys = ["Techno_Fire", "Bullet_AI_Update", "Bullet_Fire_hit", "Bullet_Detonate",
        "DamageArea", "ReceiveDamage", "V1_Verses_scale", "FireDeathWeapon", "Bullet_Construct"]
for cname in keys:
    print(f"\n=== {cname} call sites ===")
    for row in all_calls:
        if row[0] == cname:
            nm = row[5] or (KNOWN.get(row[4],""))
            print(f"  0x{row[2]:08X} -> 0x{row[3]:08X}  [{nm}]  parent=0x{row[4]:08X}")
