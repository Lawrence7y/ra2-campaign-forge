"""P1+SBH 合批后按 verify_hooks 同口径重算（只读，复用 tools/verify_hooks.py 的抽取函数）。"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
MERGED = LEAD / "goal3_p1sbh_merge_20261020/_work/out_fuzz0.cpp"

spec = importlib.util.spec_from_file_location("vh", ROOT / "tools" / "verify_hooks.py")
vh = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(vh)


def profile(cpp_text, hdr_text, ini_text, label):
    impl = vh.extract_hook_impls(cpp_text)
    inst = vh.extract_vtable_installs(cpp_text)
    rem = vh.extract_vtable_removes(cpp_text)
    inl = vh.extract_inline_pairs(cpp_text)
    fns = vh.extract_install_remove_fns(cpp_text)
    keys = vh.extract_ini_keys(ini_text)
    reads = vh.extract_loadconfig_reads(cpp_text)
    addrs = vh.extract_header_addrs(hdr_text)
    d = {
        "label": label,
        "hook_impls": len(impl),
        "vtable_installs": len(inst),
        "vtable_removes": len(rem),
        "inline_pairs": len(inl),
        "install_fns": len(fns.get("install", [])),
        "remove_fns": len(fns.get("remove", [])),
        "ini_keys": sum(len(v) for v in keys.values()) if isinstance(keys, dict) else len(keys),
        "loadconfig_reads": len(reads),
        "header_addrs": len(addrs),
        "_installs": inst,
        "_removes": rem,
        "_inline": inl,
        "_reads": reads,
    }
    return d


def sig(items):
    out = []
    for it in items:
        if isinstance(it, dict):
            out.append(json.dumps({k: it[k] for k in sorted(it) if k != "line"}, sort_keys=True, ensure_ascii=False))
        else:
            out.append(str(it))
    return out


mother = profile(
    (ROOT / "ra2render/blitter_hooks.cpp").read_text(encoding="utf-8", errors="replace"),
    (ROOT / "ra2render/ra2render.h").read_text(encoding="utf-8", errors="replace"),
    (ROOT / "ra2render/ra2render.ini").read_text(encoding="utf-8", errors="replace"),
    "MOTHER",
)
merged = profile(
    MERGED.read_text(encoding="utf-8", errors="replace"),
    (ROOT / "ra2render/ra2render.h").read_text(encoding="utf-8", errors="replace"),
    (ROOT / "ra2render/ra2render.ini").read_text(encoding="utf-8", errors="replace"),
    "MERGED",
)

KEYS = ["hook_impls", "vtable_installs", "vtable_removes", "inline_pairs",
        "install_fns", "remove_fns", "ini_keys", "loadconfig_reads", "header_addrs"]

print("=== counts: MOTHER vs MERGED ===")
for k in KEYS:
    a, b = mother[k], merged[k]
    flag = "" if a == b else "   <== DELTA %+d" % (b - a)
    print(f"  {k:18} {a:>4} -> {b:>4}{flag}")

print("\n=== element-wise identity (install/remove/inline/reads) ===")
for name in ("_installs", "_removes", "_inline", "_reads"):
    a, b = sig(mother[name]), sig(merged[name])
    same = a == b
    print(f"  {name:12} mother={len(a):>3} merged={len(b):>3} IDENTICAL={same}")
    if not same:
        only_m = [x for x in a if x not in b]
        only_g = [x for x in b if x not in a]
        print(f"     only-in-mother({len(only_m)}): {only_m[:3]}")
        print(f"     only-in-merged({len(only_g)}): {only_g[:3]}")

print("\n=== SBH-specific additions in merged ===")
txt = MERGED.read_text(encoding="utf-8", errors="replace")
for m in ("g_enableSbhGuard", "EnableSbhGuard", "InstallSbhGuardPatch",
          "RemoveSbhGuardPatch", "0x7CFC9B", "0x7CFC9F", "0x7CFE12", "0xFE00FFFF"):
    print(f"  {m:22} {txt.count(m)}")

print("\n=== json ===")
print(json.dumps({"mother": {k: mother[k] for k in KEYS},
                  "merged": {k: merged[k] for k in KEYS}}, ensure_ascii=False, indent=1))
