# -*- coding: utf-8 -*-
"""S1-S4 对照实跑：Gen-2 缺陷门禁 vs 方案 A 门禁。只打印。"""
import json, subprocess, sys, os

HERE = r"D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109"
SB = os.path.join(HERE, "_dn_sandbox")
GEN2 = os.path.join(HERE, "_dn_gate_gen2.py")
PLANA = os.path.join(HERE, "_dn_gate_planA.py")

def run(script, args):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", script] + args,
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": None, "problems": ["输出不可解析: " + r.stdout[:80] + r.stderr[:80]]}

cases = [
    ("S1 正常（仅主件齐要素）", "S1", "MAIN.md"),
    ("S2 违禁词藏主件（侧件更大更干净）", "S2", "MAIN.md"),
    ("S3 主件缺要素中稿补齐（中稿更大）", "S3", "MAIN.md"),
    ("S4 主件缺失（侧件在场）", "S4", "MAIN.md"),
]
print("%-38s | %-28s | %s" % ("场景", "Gen-2(max 猜大)", "方案A(显式命名)"))
for label, sub, main_name in cases:
    d = os.path.join(SB, sub)
    g2 = run(GEN2, [d])
    pa = run(PLANA, [d, main_name])
    print("%-38s | ok=%-5s doc=%-16s | ok=%-5s doc=%s" % (
        label, g2["ok"], g2["doc"], pa["ok"], pa["doc"]))
    if not g2["ok"]:
        print("    gen2 problems:", "；".join(g2["problems"]))
    if not pa["ok"]:
        print("    planA problems:", "；".join(pa["problems"]))
    print("    gen2 docSha256 =", g2["docSha256"][:16], "planA docSha256 =", pa["docSha256"][:16])
