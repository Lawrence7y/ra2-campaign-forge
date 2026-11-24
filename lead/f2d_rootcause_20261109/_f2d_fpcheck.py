# -*- coding: utf-8 -*-
"""F2-d 调查：编排方指纹复核（只读，hashlib 实算）"""
import hashlib, json, os

ROOT = r"D:\Project\ra2-campaign-forge"

EXPECT = {
    "lead/r11_f2_fix_20261109/R11_F2_COVERAGE_FIX.md": ("99ba9f979018df66f39a996859e24ed207b566b15f6bcdec7055b85a1f379435", 25282),
    "lead/r11_f2_fix_20261109/_f2_r11plus.py": ("83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    "lead/r11_f2_fix_20261109/_f2_repro_out.json": ("3bc0ed8b26f90e235888ed1c386ee0f3179cdcc54bf9092b6ca167dda2ecfa72", 28386),
    "lead/r11_f2_fix_20261109/_f2_compare_out.json": ("148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1", 44958),
    "lead/r11_f2_fix_20261109/_f2_context_probe_out.txt": ("e48e15469c28508303c4eb2c733e44d0129191107a5700a7beeed36e7cc89580", 44054),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md": ("dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0", 37578),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

out = {}
for rel, (esh, eb) in EXPECT.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        out[rel] = {"status": "MISSING"}
        continue
    b = open(p, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    out[rel] = {
        "status": "MATCH" if (h == esh and len(b) == eb) else "MISMATCH",
        "sha256": h,
        "bytes": len(b),
        "expect_sha": esh,
        "expect_bytes": eb,
    }

print(json.dumps(out, ensure_ascii=False, indent=1))
