# -*- coding: utf-8 -*-
"""_f2w_final.py — 撰写员收尾复验：①六保护件指纹（写报告前后各一次之「前次」）；
②_f2_compare_out.json 的 warnings 总数；③写域产出件清单指纹。只读。"""
import hashlib
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
D = REPO / "lead" / "r11_f2_fix_20261109"

print("== ① 六保护件指纹（收尾复验）==")
EXPECTED = {
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/gate_r9r12_20261109/_g9_regression_out.json": ("7f16da217dba02008546d643bb51c0100d7126939df947ad0c46a4fd478f11d8", 123691),
    "lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md": ("dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0", 37578),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
all_ok = True
for rel, (esha, ebytes) in EXPECTED.items():
    b = (REPO / rel).read_bytes()
    sha, nb = hashlib.sha256(b).hexdigest(), len(b)
    ok = (sha == esha and nb == ebytes)
    all_ok = all_ok and ok
    print("%s %s/%d %s" % ("OK " if ok else "DRIFT", sha[:16], nb, rel))
print("六保护件全部 UNCHANGED =", all_ok)

print()
print("== ② warnings 总数（_f2_compare_out.json 本轮复跑版）==")
cmp_ = json.loads((D / "_f2_compare_out.json").read_text(encoding="utf-8"))
ow = sum(len(r["orig"]["warnings"]) for r in cmp_["results"])
pw = sum(len(r["plus"]["warnings"]) for r in cmp_["results"])
print("orig_warnings=%d plus_warnings=%d" % (ow, pw))

print()
print("== ③ 写域新产出件（本轮撰写员 _f2w_*）==")
for f in sorted(D.glob("_f2w_*")):
    b = f.read_bytes()
    print(hashlib.sha256(b).hexdigest(), len(b), f.name)
