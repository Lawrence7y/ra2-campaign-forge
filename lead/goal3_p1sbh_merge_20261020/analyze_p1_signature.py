"""P1 五参数签名对 verify_hooks 口径的影响：三档对照（mother / P1 / P1+SBH）。

只读分析，不改任何母本与工具。
"""
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
SRC = {
    "MOTHER": ROOT / "ra2render/blitter_hooks.cpp",
    "P1": LEAD / "goal3_p1sbh_merge_20261020/_work/p1base.cpp",
    "P1+SBH": LEAD / "goal3_p1sbh_merge_20261020/_work/out_fuzz0.cpp",
}

RE_4ARG_INST = re.compile(
    r"PatchVTablePointer\s*\(\s*([^,]+),\s*([^,]+),\s*[^,]+,\s*\"([^\"]+)\"\s*\)")
RE_5ARG_INST = re.compile(
    r"PatchVTablePointer\s*\(\s*([^,]+),\s*([^,]+),\s*[^,]+,\s*\"([^\"]+)\"\s*,\s*([^)]+)\)")
RE_4ARG_REM = re.compile(
    r"PatchVTablePointer\s*\(\s*([^,]+),\s*[^,]+,\s*nullptr,\s*\"([^\"]+)\"\s*\)")
RE_3ARG_REM = re.compile(
    r"PatchVTablePointer\s*\(\s*([^,]+),\s*nullptr,\s*\"([^\"]+)\"\s*\)")


def body(cpp, fn, kind):
    pat = r"%s\s+%s\s*\(\s*\)\s*\{(.*?)\n\}" % (kind, fn)
    m = re.search(pat, cpp, re.S)
    return m.group(1) if m else ""


print(f"{'file':8} {'install calls':>14} {'4arg':>6} {'5arg':>6} {'remove calls':>13} {'4arg':>6} {'3arg':>6}")
for name, p in SRC.items():
    t = p.read_text(encoding="utf-8", errors="replace")
    ib = body(t, "InstallVTableHooks", "bool")
    rb = body(t, "RemoveVTableHooks", "void")
    print(f"{name:8} {ib.count('PatchVTablePointer'):>14} "
          f"{len(RE_4ARG_INST.findall(ib)):>6} {len(RE_5ARG_INST.findall(ib)):>6} "
          f"{rb.count('PatchVTablePointer'):>13} "
          f"{len(RE_4ARG_REM.findall(rb)):>6} {len(RE_3ARG_REM.findall(rb)):>6}")

print()
print("=== sample remove call forms ===")
for name, p in SRC.items():
    t = p.read_text(encoding="utf-8", errors="replace")
    rb = body(t, "RemoveVTableHooks", "void")
    first = [l.strip() for l in rb.split("\n") if "PatchVTablePointer" in l][:1]
    print(f"  {name:8} {first}")

print()
print("=== 5-arg install: expected-orig targets (P1+SBH) ===")
t = SRC["P1+SBH"].read_text(encoding="utf-8", errors="replace")
ib = body(t, "InstallVTableHooks", "bool")
for target, hook, nm, exp in RE_5ARG_INST.findall(ib):
    print(f"  {' '.join(target.split()):50} -> {' '.join(exp.split())}")

print()
print("=== inline patch sites (9 code points) ===")
for name, p in SRC.items():
    t = p.read_text(encoding="utf-8", errors="replace")
    saves = sorted(set(re.findall(r"memcpy\(\s*(s_orig\w+)\s*,", t)))
    print(f"  {name:8} {len(saves)}: {saves}")
