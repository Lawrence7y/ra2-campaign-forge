# -*- coding: utf-8 -*-
"""_f2_compare.py — 第三步：同一份 30 件清单，原版 r11_scan vs 增强版 r11_scan_plus 实跑对比。

断言（要求 d 行为保留）：每件绑定行条数与 declared 序列与原版逐一相同；
差异只允许出现在 path/match/problems/warnings 上。
输出：_f2_compare_out.json + 控制台逐条表。
"""
import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
G7 = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
F2PLUS = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_r11plus.py"
G9OUT = REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json"
OUT = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_compare_out.json"

G7_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES = 11743

raw = G7.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assert sha == G7_SHA and len(raw) == G7_BYTES, "g7 指纹失配"
spec = importlib.util.spec_from_file_location("_g7_predicates_cmp", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

spec2 = importlib.util.spec_from_file_location("_f2_r11plus", F2PLUS)
f2p = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(f2p)

reg = json.loads(G9OUT.read_text(encoding="utf-8"))
results = []
tot = {"bindings": 0, "orig_path": 0, "plus_path": 0, "orig_match": 0,
       "plus_match": 0, "orig_problems": 0, "plus_problems": 0}
for r in reg["results_30"]:
    p = Path(r["file"])
    text = p.read_bytes().decode("utf-8")
    d_dir = p.parent
    o_prob, o_warn, o_bind = g7.r11_scan(text, d_dir, root=REPO)
    n_prob, n_warn, n_bind = f2p.r11_scan_plus(text, d_dir, root=REPO)
    # 要求 d：绑定行条数与 declared 序列必须逐一相同
    assert len(o_bind) == len(n_bind), "绑定行条数漂移 %s" % p
    assert [b["declared"] for b in o_bind] == [b["declared"] for b in n_bind], \
        "declared 序列漂移 %s" % p
    # 原版采到 path 的绑定，增强版必须仍采到（原样）
    for ob, nb in zip(o_bind, n_bind):
        if ob["path"] is not None:
            assert nb["path"] == ob["path"], "原 T1 path 丢失 %s: %r→%r" % (p, ob["path"], nb["path"])
    # R9/R10/R12 判定取自回归 JSON（本次不动这些谓词）
    others_fail = any(r["predicates"][k]["verdict"] == "FAIL"
                      for k in ("R9", "R10", "R12"))
    row = {
        "file": str(p),
        "other_predicates_fail": others_fail,
        "orig": {"problems": o_prob, "warnings": o_warn, "bindings": o_bind,
                 "verdict": "FAIL" if o_prob else "PASS"},
        "plus": {"problems": n_prob, "warnings": n_warn, "bindings": n_bind,
                 "verdict": "FAIL" if n_prob else "PASS"},
        "orig_overall": ("FAIL" if (o_prob or others_fail) else "PASS"),
        "plus_overall": ("FAIL" if (n_prob or others_fail) else "PASS"),
    }
    results.append(row)
    tot["bindings"] += len(o_bind)
    tot["orig_path"] += sum(1 for b in o_bind if b["path"])
    tot["plus_path"] += sum(1 for b in n_bind if b.get("path"))
    tot["orig_match"] += sum(1 for b in o_bind if b["match"] is True)
    tot["plus_match"] += sum(1 for b in n_bind if b.get("match") is True)
    tot["orig_problems"] += len(o_prob)
    tot["plus_problems"] += len(n_prob)

print("== 30 件汇总 ==")
print(json.dumps(tot, ensure_ascii=False, indent=2))
print()
print("== 逐条绑定行表（file 短名 / L 行号 / declared 前 12 / 原 path / 新 path / 新 tier / 新 match）==")
for row in results:
    p = Path(row["file"])
    short = str(p.relative_to(REPO))
    for i, (ob, nb) in enumerate(zip(row["orig"]["bindings"], row["plus"]["bindings"])):
        print("%-58s L%-4d %s  orig_path=%-38r plus_path=%-52r tier=%-4r match=%r cite=%r" % (
            short, 0, ob["declared"][:12], ob["path"], nb.get("path"),
            nb.get("tier"), nb.get("match"), nb.get("citation")))
print()
print("== 逐件 problems 对比（只允许 #30 减少 1 条 R3-3c → 引文降级，其余不变）==")
for row in results:
    if row["orig"]["problems"] != row["plus"]["problems"]:
        print("CHANGED %s\n  orig=%s\n  plus=%s" % (
            row["file"], row["orig"]["problems"], row["plus"]["problems"]))
print()
print("== 逐件 verdict 对比（R11 级与 overall 级）==")
for row in results:
    o11, n11 = row["orig"]["verdict"], row["plus"]["verdict"]
    oo, no = row["orig_overall"], row["plus_overall"]
    if (o11, oo) != (n11, no):
        print("VERDICT CHANGED %s: R11 %s→%s, overall %s→%s" % (
            row["file"], o11, n11, oo, no))
print("(未打印者 = 无变化)")

OUT.write_text(json.dumps({"totals": tot, "results": results}, ensure_ascii=False, indent=2),
               encoding="utf-8")
print()
print("已写 %s" % OUT)
