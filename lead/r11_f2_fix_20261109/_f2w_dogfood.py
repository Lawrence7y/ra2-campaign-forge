# -*- coding: utf-8 -*-
"""_f2w_dogfood.py — 交付轮收尾：①本报告 R11_F2_COVERAGE_FIX.md 自扫两版对照；
②写入后六保护件指纹复验；③本件指纹。只读。"""
import hashlib
import importlib.util
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
D = REPO / "lead" / "r11_f2_fix_20261109"

s1 = importlib.util.spec_from_file_location("_g7x", REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
g7 = importlib.util.module_from_spec(s1)
s1.loader.exec_module(g7)
s2 = importlib.util.spec_from_file_location("_f2p", D / "_f2_r11plus.py")
plus = importlib.util.module_from_spec(s2)
s2.loader.exec_module(plus)

rep = D / "R11_F2_COVERAGE_FIX.md"
text = rep.read_text(encoding="utf-8")
op, ow, ob = g7.r11_scan(text, D, root=REPO)
pp, pw, pb = plus.r11_scan_plus(text, D, root=REPO)
print("== dogfood：R11_F2_COVERAGE_FIX.md 自扫 ==")
print("orig: bindings=%d collected=%d match=%d problems=%d warnings=%d" % (
    len(ob), sum(1 for b in ob if b["path"]), sum(1 for b in ob if b["match"] is True), len(op), len(ow)))
print("plus: bindings=%d collected=%d match=%d problems=%d warnings=%d" % (
    len(pb), sum(1 for b in pb if b.get("path")), sum(1 for b in pb if b.get("match") is True), len(pp), len(pw)))
tiers = {}
for b in pb:
    if b.get("match") is True:
        tiers[b.get("tier")] = tiers.get(b.get("tier"), 0) + 1
print("plus match tiers:", tiers)
print("plus new problems vs orig:", [m for m in pp if m not in op])
print("plus warnings:", pw)

print()
print("== 写入后六保护件指纹复验 ==")
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
print("== 本件指纹 ==")
rb = rep.read_bytes()
print(hashlib.sha256(rb).hexdigest(), len(rb), rep.name)
