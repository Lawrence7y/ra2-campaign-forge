# -*- coding: utf-8 -*-
"""F2V-06: ⑥c 警告消息完整性（完整路径非 'C'）；load_g7 指纹失配拒绝；
dogfood：补丁报告自扫两版对照。"""
import hashlib
import importlib.util
import shutil
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "r11_f2_fix_20261109"
FX = W / "_f2v_fixtures"

spec = importlib.util.spec_from_file_location("_f2p", W / "_f2_r11plus.py")
plus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plus)

s2 = importlib.util.spec_from_file_location("_g7x", REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
g7 = importlib.util.module_from_spec(s2)
s2.loader.exec_module(g7)

print("===== ⑥c 警告消息（不在盘 T2 候选）=====")
doc2 = "被核对象 SHA256 = %s，字节数 = 3（`C:\\no\\such_dir\\missing.md:5-6`）\n" % (
    hashlib.sha256((FX / "_f2v_other.txt").read_bytes()).hexdigest())
p2, w2, b2 = plus.r11_scan_plus(doc2, FX, root=REPO)
for m in p2:
    print("problem:", m)
for m in w2:
    print("warning:", m)

print("\n===== load_g7 指纹失配拒绝（用本写域篡改副本，不碰保护件）=====")
tampered = FX / "_f2v_g7_tampered_copy.py"
raw = (REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py").read_bytes()
tampered.write_bytes(raw + b"\n# tampered\n")
plus.G7_PREDICATES_PATH = tampered
plus._g7_cache = None
try:
    plus.load_g7()
    print("!!! 未拒绝——指纹门失效")
except RuntimeError as e:
    print("拒绝运行 OK：", str(e)[:120])
finally:
    plus.G7_PREDICATES_PATH = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
    plus._g7_cache = None
    tampered.unlink()

print("\n===== dogfood：补丁报告 _f2_F2_PATCH_REPORT.md 自扫两版对照 =====")
rep = W / "_f2_F2_PATCH_REPORT.md"
text = rep.read_text(encoding="utf-8")
op, ow, ob = g7.r11_scan(text, W, root=REPO)
pp, pw, pb = plus.r11_scan_plus(text, W, root=REPO)
print("orig: bindings=%d collected=%d match=%d problems=%d warnings=%d" % (
    len(ob), sum(1 for b in ob if b["path"]), sum(1 for b in ob if b["match"] is True), len(op), len(ow)))
print("plus: bindings=%d collected=%d match=%d problems=%d warnings=%d" % (
    len(pb), sum(1 for b in pb if b.get("path")), sum(1 for b in pb if b.get("match") is True), len(pp), len(pw)))
tiers = {}
for b in pb:
    if b.get("match") is True:
        tiers[b.get("tier")] = tiers.get(b.get("tier"), 0) + 1
print("plus match tiers:", tiers)
newp = [m for m in pp if m not in op]
print("plus new problems vs orig:", newp)
