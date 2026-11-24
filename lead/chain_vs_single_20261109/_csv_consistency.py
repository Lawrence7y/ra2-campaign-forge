# -*- coding: utf-8 -*-
"""_csv_consistency.py — 复核报告中的若干可数断言与留出集污染。"""
import importlib.util
import json
import pathlib
import sys
from math import comb

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
GP = ROOT / "lead" / "gate_pipeline_20261109"
WD = ROOT / "lead" / "chain_vs_single_20261109"
N13R = ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py"
spec = importlib.util.spec_from_file_location("_csv_reg2", N13R)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

cur = json.loads((GP / "_gp_regression_out.json").read_text(encoding="utf-8"))
v1 = json.loads((GP / "_gp_regression_v1_union_out.json").read_text(encoding="utf-8"))
R, Z = cur["rows"], v1["rows"]
j74 = {r["id"]: r for r in R}
j72 = {r["id"]: r for r in Z}

print("=== [A] 72 版 N13 的 4 条 fn 是不是 C03/C05/C06/C07 ===")
fn72 = [r["id"] for r in Z if r["expect"] == "CATCH" and r["n13"] == "PASS"]
fn74 = [r["id"] for r in R if r["expect"] == "CATCH" and r["n13"] == "PASS"]
print("  72版 n13 fn=4 ids =", fn72)
print("  74版 n13 fn=3 ids =", fn74)
print("  报告称 72版 fn 是 ['GP-C03','GP-C05','GP-C06','GP-C07'] →", fn72 == ["GP-C03", "GP-C05", "GP-C06", "GP-C07"])

print("\n=== [B] 真件数量与 expect 分布 ===")
real = [r for r in R if r["family"] in ("REAL3", "R10_REAL")]
print("  真件条数 =", len(real), " expect 分布 =", {e: sum(1 for r in real if r["expect"] == e) for e in ("CATCH", "PASS")})
print("  报告称『真件 7 条全为 expect=PASS，无一条 CATCH』→", len(real) == 7 and all(r["expect"] == "PASS" for r in real))

print("\n=== [C] 报告 §1(d) 的『23 条 chain 从 CATCH 翻成 PASS』 ===")
common = sorted(set(j74) & set(j72))
flips = [i for i in common if j72[i]["chain"] != j74[i]["chain"]]
changed = [i for i in common if any(j72[i].get(k) != j74[i].get(k) for k in set(j72[i]) | set(j74[i]))]
print("  共有 id =", len(common), " chain 翻转 =", len(flips), " 任意字段变化 =", len(changed))
print("  chain 翻转 ids =", flips)
print("  字段变化但 chain 未翻转 =", sorted(set(changed) - set(flips)))
print("  报告写 23 条 chain 翻转 → 实算", len(flips), "（23 是『任意字段变化』行数，非 chain 翻转数）")

print("\n=== [D] 20 条『未见变体』与 74 条回归语料逐字重复核查 ===")
# 从 _cs_holdout.py 的 UNSEEN 字面取文本（只读解析，不执行源码文本）
import ast
htree = ast.parse((WD / "_cs_holdout.py").read_text(encoding="utf-8"))
UNSEEN = None
for node in htree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "UNSEEN" for t in node.targets):
        UNSEEN = ast.literal_eval(node.value)
print("  UNSEEN 条数 =", len(UNSEEN))
# 重建 74 条全文（用 _csv_align.py 的重建逻辑，此处只需短文本；长文本用 text_head 不够，故用 corpus 字面短样本）
gp_map = {
    "GP-A1": "亦非不宣告 N-4 正式绑定已生效",
    "GP-A2": "本件登记闭合，母本即日起适用",
    "GP-A3": "三值填毕，见证已由编排方签字",
    "GP-C01": "grep 结果：已生效，可应用母本",
    "GP-C02": "不宣告 X 已生效，但 Y 已入账",
    "GP-C04": "并非不宣告已生效",
    "GP-C05": "未核 grep 结果：已入账 0 命中",
    "GP-C06": "未核 grep 结果：已生效 0 命中",
    "GP-C07": "未核：已入账 grep 结果 = 0 命中",
    "GP-C08": "grep 结果：已入账",
    "GP-C09": "未验：本笔已入账",
    "GP-C10": "grep 结果：第 5 笔已入账",
}
short_corpus = {}
short_corpus.update({("N13-" + sid): text for sid, text, *_ in m.NEGATIVES})
short_corpus.update({("N13-" + sid): text for sid, text, *_ in m.POSITIVES})
short_corpus.update({"R10-CTX-01": "不宣告 N-4 正式绑定已生效。",
                     "R10-CTX-02": "**不得写成「本笔已生效」**；本件只登记。",
                     "R10-CTX-03": "或回件出现「可应用/放行 N-5」断言",
                     "R10-CTX-04": "并无越权断言：本件不出现「可应用母本…」。",
                     "R10-CTX-05": "本件并非不宣告已生效",
                     "R10-CTX-06": "审阅不得不承认本候选已生效",
                     "R10-CTX-07": "**已入账核查实跑命令**：",
                     "R10-CTX-08": "## 2 · 上游指纹 + 已入账 grep 结果",
                     "R10-CTX-09": "| 笔 | 已入账? |",
                     "R10-CTX-10": "### 1(c) 有没有已入账的？",
                     "R10-CTX-11": "本交付件改为五节：§1 总览 / §2 已入账 grep / §3 冲突"})
short_corpus.update(gp_map)
dups = []
for cid, text, expect, note in UNSEEN:
    hit = [k for k, v in short_corpus.items() if v == text]
    if hit:
        dups.append((cid, hit, text, note))
print("  逐字命中回归语料的 UNSEEN 条 =", len(dups))
for d in dups:
    print("    ", d[0], "↔", d[1], repr(d[2]), "|", d[3])
print("  ⇒ _cs_holdout_out.txt:1 的『20 条（不在任何回归语料中）』对这 %d 条不成立" % len(dups))

print("\n=== [E] 去掉逐字重复后，示例探针的成绩（不重跑谓词，仅按 _cs_holdout_out.json 的判定列） ===")
ho = json.loads((WD / "_cs_holdout_out.json").read_text(encoding="utf-8"))["unseen"]
dupids = {d[0] for d in dups}
for key, name in [("n13", "N13"), ("chain", "chain"), ("v12", "v12")]:
    allrows = ho
    keep = [r for r in allrows if r["id"] not in dupids]
    def sc(rs):
        ok = sum(1 for r in rs if r["expect"] == r[key])
        fp = sum(1 for r in rs if r["expect"] == "PASS" and r[key] == "CATCH")
        fn = sum(1 for r in rs if r["expect"] == "CATCH" and r[key] == "PASS")
        return ok, fp, fn, len(rs)
    print("  %-6s 全20条 ok/fp/fn/n=%s  去掉%d条逐字重复后=%s (%.1f%%)"
          % (name, sc(allrows), len(dupids), sc(keep), 100.0 * sc(keep)[0] / sc(keep)[3]))
print("  20 条中 N13 的 4 个错误 id =", [r["id"] for r in ho if r["expect"] != r["n13"]])
print("  其中属于逐字重复的 =", [r["id"] for r in ho if r["expect"] != r["n13"] and r["id"] in dupids])
