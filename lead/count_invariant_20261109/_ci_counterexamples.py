# -*- coding: utf-8 -*-
"""_ci_counterexamples.py — 构造违反每条不变量的输入并实跑 _ci_checks.evaluate()，证明会报警。

纪律：反例 JSON 只写到临时目录（tempfile.mkdtemp）；不改既有产物、不改 _f2_compare.py /
_f2v_run.py、不落只读域；零真机、零采样代码；python -I -X utf8 + 绝对路径。
运行：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_ci_counterexamples.py
"""
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "count_invariant_20261109"
SRC = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_compare_out.json"

spec = importlib.util.spec_from_file_location("_ci_checks", W / "_ci_checks.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

base = json.loads(SRC.read_text(encoding="utf-8"))
tmp = pathlib.Path(tempfile.mkdtemp(prefix="_ci_ce_"))
print("TEMP DIR:", tmp)


def run(name, doc):
    """写临时 JSON → 跑 checker CLI → 返回 (alerts, facts)"""
    p = tmp / (name + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    v, f = ci.evaluate(doc)
    return p, v, f


def show(name, p, v, f, expect):
    hit = [x for x in v if x.startswith(expect)]
    print("[%s] %s  alerts=%d  %s_hit=%d  temp=%s" %
          ("PASS" if hit else "FAIL", name, len(v), expect, len(hit), p.name))
    for x in v:
        print("      ", x)
    return bool(hit)


RESULTS = {}

# ---- CE-01 违反 INV-01：硬编码 plus_match=9，其余全真（also breaks INV-06 baseline? no） ----
d = copy.deepcopy(base)
d["totals"]["plus_match"] = 9  # 与现盘同值；此反例演示「值没变」检测不出，见 CE-01b
# 真实故意改坏：把 plus_match 改成 8（模拟漏计 1 条），同时仅改 totals
d2 = copy.deepcopy(base)
d2["totals"]["plus_match"] = 8
p, v, f = run("CE01_hardcode_plus_match_8", d2)
RESULTS["CE-01 (totals.plus_match=8)"] = show("CE-01", p, v, f, "INV-01")

# ---- CE-02 违反 INV-02：plus_path > bindings ----
d = copy.deepcopy(base)
d["totals"]["plus_path"] = 20
p, v, f = run("CE02_plus_path_20_gt_bindings", d)
RESULTS["CE-02 (plus_path=20>19)"] = show("CE-02", p, v, f, "INV-02")

# ---- CE-03 违反 INV-03：orig_path > plus_path（原版采到反而增强版丢了） ----
d = copy.deepcopy(base)
d["totals"]["orig_path"] = 12
p, v, f = run("CE03_orig_path_12", d)
RESULTS["CE-03 (orig_path=12>plus_path=9)"] = show("CE-03", p, v, f, "INV-03")

# ---- CE-04 违反 INV-04：problems 负数 + verdict 与 problems 不一致 ----
d = copy.deepcopy(base)
d["totals"]["plus_problems"] = -1
d["results"][0]["plus"]["verdict"] = "FAIL"  # problems=[] 却判 FAIL
p, v, f = run("CE04_neg_problems_and_verdict", d)
RESULTS["CE-04 (plus_problems=-1, verdict lie)"] = show("CE-04", p, v, f, "INV-04")

# ---- CE-05 违反 INV-05：tier 分布不完备（删 1 条绑定行的 tier 键 → 计数和 18≠19） ----
d = copy.deepcopy(base)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("tier") is not None:
            del b["tier"]
            break
    else:
        continue
    break
p, v, f = run("CE05_drop_one_tier_key", d)
RESULTS["CE-05 (drop one tier key)"] = show("CE-05", p, v, f, "INV-05")

# ---- CE-06 违反 INV-06：把 1 条 match=True 行的 match 改成 False（制造 plus_match=8≠9） ----
d = copy.deepcopy(base)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("match") is True:
            b["match"] = False
            break
    else:
        continue
    break
d["totals"]["plus_match"] = 8  # 同步 totals，避免 INV-01 抢先报警，隔离出 INV-06
p, v, f = run("CE06_break_baseline_identity", d)
RESULTS["CE-06 (plus_path=9,plus_match=8)"] = show("CE-06", p, v, f, "INV-06")

# ---- CE-07 违反 INV-07：改 1 条为「无 path 且 match=True」但漏掉 merged 维度 ----
#      这正是「巧合恒等掩盖维度缺失」的本尊：一个 merged 语义却没有 merged 标记。
d = copy.deepcopy(base)
b0 = d["results"][29]["plus"]["bindings"][4]   # 现有 match=True 的一条
d["results"][29]["plus"]["bindings"][4] = {
    "declared": b0["declared"], "path": None, "match": True,
    "tier": "T2", "citation": b0.get("citation", False),
    "members": [{"path": "x", "sha": b0["declared"], "bytes": 1},
                {"path": "y", "sha": b0["declared"], "bytes": 1}],
    "decl_lines": [13],
}  # 没有 SAMEDOC_LINK_EQ tier，但有 members → M=1, E=0
d["totals"]["plus_path"] = 8
d["totals"]["plus_match"] = 9
p, v, f = run("CE07_merged_semantics_without_merged_tier", d)
RESULTS["CE-07 (M=1,E=0: 维度缺失)"] = show("CE-07", p, v, f, "INV-07")

# ---- CE-08 违反 INV-08：数值相等但集合不同（把 A 行 match 关掉、把 B 行 match 打开） ----
d = copy.deepcopy(base)
rows = [(i, k, b) for i, r in enumerate(d["results"])
        for k, b in enumerate(r["plus"]["bindings"])]
path_rows = [(i, k) for i, k, b in rows if b.get("path")]
non_path_rows = [(i, k) for i, k, b in rows if not b.get("path")]
i0, k0 = path_rows[0]
i1, k1 = non_path_rows[0]
d["results"][i0]["plus"]["bindings"][k0]["match"] = False
d["results"][i1]["plus"]["bindings"][k1]["match"] = True
# totals 不变（9/9），故 INV-01/06 都不报；只有集合级 INV-08 报
p, v, f = run("CE08_numeric_equal_set_differs", d)
RESULTS["CE-08 (9==9 but SET differs)"] = show("CE-08", p, v, f, "INV-08")

# ---- CE-09 违反 INV-09：声明 schema_version=2 但不带 counting_policy / by_kind ----
d = copy.deepcopy(base)
d["schema_version"] = 2
p, v, f = run("CE09_v2_without_policy", d)
RESULTS["CE-09 (v2 but no policy)"] = show("CE-09", p, v, f, "INV-09")

# ---- CE-09b：v2 且 by_kind 自相矛盾（single_path+merged_eq != plus_match） ----
d = copy.deepcopy(base)
d["schema_version"] = 2
d["counting_policy"] = "D-XXX"
d["totals"]["plus_match_by_kind"] = {"single_path": 9, "merged_eq": 1}  # 10 != 9
p, v, f = run("CE09b_v2_bykind_inconsistent", d)
RESULTS["CE-09b (v2 by_kind 9+1!=9)"] = show("CE-09b", p, v, f, "INV-09")

print()
print("== SUMMARY ==")
for k, ok in RESULTS.items():
    print(("  OK   " if ok else "  MISS "), k)
print("ALL_ALERT =", all(RESULTS.values()), " COUNT =", len(RESULTS))
sys.exit(0 if all(RESULTS.values()) else 1)
