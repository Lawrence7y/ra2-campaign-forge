"""三档对照：MOTHER / P1 / P1+SBH，用 verify_hooks.v2.py 的抽取函数。"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
V2 = LEAD / "goal3_verifyhooks_fix_20261020/verify_hooks.v2.py"
MERGEWORK = LEAD / "goal3_p1sbh_merge_20261020/_work"

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("vh2", V2)
vh2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh2)

variants = {
    "MOTHER": ROOT / "ra2render/blitter_hooks.cpp",
    "P1": MERGEWORK / "p1base.cpp",
    "P1+SBH": MERGEWORK / "out_fuzz0.cpp",
}

ini_mother = (ROOT / "ra2render/ra2render.ini").read_text(encoding="utf-8", errors="replace")
ini_v2_path = LEAD / "goal3_verifyhooks_fix_20261020/ra2render.ini.v2"
ini_v2 = (ini_v2_path.read_text(encoding="utf-8", errors="replace")
          if ini_v2_path.exists() else None)

print("ini.v2 exists:", ini_v2 is not None)
print()
print(f"{'variant':9} {'inst':>5} {'rem':>5} {'sym':>5} {'inline':>7} {'reads':>6} {'iniKeys':>8}")
for name, p in variants.items():
    t = p.read_text(encoding="utf-8", errors="replace")
    inst = vh2.extract_vtable_installs(t)
    rem = vh2.extract_vtable_removes(t)
    inl = vh2.extract_inline_pairs(t)
    reads = vh2.extract_loadconfig_reads(t)
    keys = vh2.extract_ini_keys(ini_mother)
    sym = len(inst) == len(rem)
    print(f"{name:9} {len(inst):>5} {len(rem):>5} {str(sym):>5} {len(inl):>7} {len(reads):>6} {sum(len(v) for v in keys.values()):>8}")

print()
print("=== install/remove name pairing per variant ===")
for name, p in variants.items():
    t = p.read_text(encoding="utf-8", errors="replace")
    inst = vh2.extract_vtable_installs(t)
    rem = vh2.extract_vtable_removes(t)
    it = {x["target_expr"] for x in inst}
    rt = {x["target_expr"] for x in rem}
    print(f"  {name:9} install targets={len(it)} remove targets={len(rt)} "
          f"both={len(it & rt)} install_only={len(it - rt)} remove_only={len(rt - it)}")

print()
print("=== expect_orig populated (5-arg detection) ===")
for name, p in variants.items():
    t = p.read_text(encoding="utf-8", errors="replace")
    inst = vh2.extract_vtable_installs(t)
    n5 = sum(1 for x in inst if x.get("expect_orig"))
    print(f"  {name:9} with expect_orig = {n5} / {len(inst)}")

print()
print("=== ini key gap check (LoadConfig reads vs ini keys) ===")
for label, ini_text in (("MOTHER ini", ini_mother), ("v2 ini", ini_v2)):
    if ini_text is None:
        print(f"  {label}: MISSING")
        continue
    keys = vh2.extract_ini_keys(ini_text)
    allkeys = set()
    for v in keys.values():
        allkeys.update(v)
    for name, p in variants.items():
        t = p.read_text(encoding="utf-8", errors="replace")
        reads = set(vh2.extract_loadconfig_reads(t))
        missing = sorted(reads - allkeys)
        print(f"  {label:11} vs {name:9} reads={len(reads):>2} iniKeys={len(allkeys):>2} missing={missing}")
