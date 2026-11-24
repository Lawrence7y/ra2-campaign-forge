# -*- coding: utf-8 -*-
"""_cii_counterexamples.py — 对 5 条不变量逐条构造「违反它」的输入并实跑报警。

纪律：反例 JSON 只写 tempfile.mkdtemp(prefix="_cii_ce_")；不改 _f2_compare.py /
_f2v_run.py / 任何既有产物；零真机、零采样代码；python -I -X utf8 + 绝对路径。
运行：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_cii_counterexamples.py
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
PROJ = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_r8prxhqj\merged_projection.json")

spec = importlib.util.spec_from_file_location("_cii_checks", W / "_cii_checks.py")
cii = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cii)

BASE = json.loads(SRC.read_text(encoding="utf-8"))
MERGED = json.loads(PROJ.read_text(encoding="utf-8"))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_cii_ce_"))
print("TEMP DIR:", TMP)

RESULTS = {}


def probe(name, doc, expect_prefix, expect_merged=False):
    p = TMP / (name + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    v, f = cii.evaluate(doc, expect_merged=expect_merged)
    hit = [x for x in v if x.startswith(expect_prefix)]
    print("[%s] %s  alerts=%d  %s_hit=%d  temp=%s"
          % ("PASS" if hit else "FAIL", name, len(v), expect_prefix, len(hit), p.name))
    for x in v:
        print("      ", x)
    return bool(hit)


# ================= 5 条基线不变量，每条一个能触发报警的构造输入 =================

# INV-1a totals 与 results[] 脱钩（硬编码 9 / 漏计）
d = copy.deepcopy(BASE)
d["totals"]["plus_match"] = 8
RESULTS["INV-1a_totals_pm8"] = probe("CE01_totals_plus_match_8", d, "INV-1 totals.plus_match")

# INV-1b verdict 谎言（problems=[] 却 verdict=FAIL）—— 上游 CE-04 实为空操作 + :90 崩溃，此处真构造
d = copy.deepcopy(BASE)
cands = [(i, r) for i, r in enumerate(d["results"])
         if r["plus"]["problems"] == [] and r["plus"]["verdict"] == "PASS"]
i0 = cands[0][0]
d["results"][i0]["plus"]["verdict"] = "FAIL"
print("     INV-1b verdict lie at results[%d] file=%s problems=[]" %
      (i0, d["results"][i0]["file"].split("\\")[-1]))
RESULTS["INV-1b_verdict_FAIL_no_problems"] = probe("CE01b_verdict_lie", d, "INV-1 (3,plus)")

# INV-1c verdict 第三值 UNKNOWN（上游双 if 漏掉）
d = copy.deepcopy(BASE)
d["results"][i0]["plus"]["verdict"] = "UNKNOWN"
RESULTS["INV-1c_verdict_UNKNOWN"] = probe("CE01c_verdict_UNKNOWN", d, "INV-1 (3,plus)")

# INV-2a 计数越界
d = copy.deepcopy(BASE)
d["totals"]["plus_path"] = 20
RESULTS["INV-2a_plus_path_20"] = probe("CE02_plus_path_20", d, "INV-2 plus_path")

# INV-2b 覆盖单调
d = copy.deepcopy(BASE)
d["totals"]["orig_path"] = 12
RESULTS["INV-2b_orig_path_12"] = probe("CE03_orig_path_12", d, "INV-2 orig_path")

# INV-2c ★ 对称错值：totals 七键一字未改，恒等式全成立，只有集合级报警
d = copy.deepcopy(BASE)
rows = [(i, k, b) for i, r in enumerate(d["results"])
        for k, b in enumerate(r["plus"]["bindings"])]
pr = [(i, k) for i, k, b in rows if b.get("path")]
nr = [(i, k) for i, k, b in rows if not b.get("path")]
(i1, k1), (i2, k2) = pr[0], nr[0]
d["results"][i1]["plus"]["bindings"][k1]["match"] = False
d["results"][i2]["plus"]["bindings"][k2]["match"] = True
# totals 不动；rec 的 plus_match 仍 9，故 INV-1 不报
_, f = cii.evaluate(d)
print("     CE-08 totals unchanged =", d["totals"] == BASE["totals"],
      " recomputed==stored =", all(d["totals"][k] == f["recomputed"][k]
                                   for k in ("bindings", "orig_path", "plus_path",
                                             "orig_match", "plus_match",
                                             "orig_problems", "plus_problems")))
RESULTS["INV-2c_symmetric_drift"] = probe("CE08_symmetric_drift", d, "INV-2 plus_path==plus_match numerically")

# INV-3a 删一条 tier 键（弱 .get 版会被吞进 None 桶）
d = copy.deepcopy(BASE)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("tier") is not None:
            del b["tier"]
            break
    else:
        continue
    break
weak_sum = sum(1 for r in d["results"] for b in r["plus"]["bindings"])
print("     CE-05 weak .get-only partition sum =", weak_sum, "(still 19, no alert)")
RESULTS["INV-3a_drop_tier_key"] = probe("CE05_drop_tier_key", d, "INV-3 (3,0)")

# INV-3b 未知 tier 值
d = copy.deepcopy(BASE)
d["results"][3]["plus"]["bindings"][0]["tier"] = "T9_NOT_A_TIER"
RESULTS["INV-3b_unknown_tier"] = probe("CE05b_unknown_tier", d, "INV-3 (3,0)")

# INV-4 merged 语义存在却不打 merged 标（M=1 E=0）
d = copy.deepcopy(BASE)
b0 = d["results"][29]["plus"]["bindings"][4]
d["results"][29]["plus"]["bindings"][4] = {
    "declared": b0["declared"], "path": None, "match": True,
    "tier": "T2", "citation": b0.get("citation", False),
    "members": [{"path": "x", "sha": b0["declared"], "bytes": 1},
                {"path": "y", "sha": b0["declared"], "bytes": 1}],
    "decl_lines": [13],
}
d["totals"]["plus_path"] = 8
RESULTS["INV-4_merged_without_tier"] = probe("CE07_merged_without_tier", d, "INV-4 M(match_no_path)")

# INV-5a 只声明 schema_version=2 却不落地新维度
d = copy.deepcopy(BASE)
d["schema_version"] = 2
RESULTS["INV-5a_v2_no_policy"] = probe("CE09_v2_no_policy", d, "INV-5 schema_version>=2")

# INV-5b by_kind 自相矛盾
d = copy.deepcopy(BASE)
d["schema_version"] = 2
d["counting_policy"] = "D-XXX"
d["totals"]["plus_match_by_kind"] = {"single_path": 9, "merged_eq": 1}
RESULTS["INV-5b_bykind_inconsistent"] = probe("CE09b_bykind_10_ne_9", d, "INV-5 single_path+merged_eq")

# ============ merged 态（--expect-merged）：4 个上游 gate 静默放过的变异，本门槛必须报警 ============
mi = [(i, k) for i, r in enumerate(MERGED["results"])
      for k, b in enumerate(r["plus"]["bindings"]) if b.get("tier") == "SAMEDOC_LINK_EQ"]
print("MERGED row at", mi)
mi0, mi1 = mi[0]

# G1 merged 行删 members
d = copy.deepcopy(MERGED)
d["results"][mi0]["plus"]["bindings"][mi1].pop("members", None)
RESULTS["M-G1_no_members"] = probe("MG1_no_members", d, "INV-4 (20,0)", expect_merged=True)

# G2 merged 行加单对象三键
d = copy.deepcopy(MERGED)
d["results"][mi0]["plus"]["bindings"][mi1]["verified_path"] = "X"
d["results"][mi0]["plus"]["bindings"][mi1]["recomputed"] = "Y"
d["results"][mi0]["plus"]["bindings"][mi1]["bytes"] = 999
RESULTS["M-G2_single_obj_keys"] = probe("MG2_single_obj_keys", d, "INV-4 (20,0)", expect_merged=True)

# G3 畸形 merged-tier 行：tier=SAMEDOC_LINK_EQ 但 match=None、无 members（上游形状检查被跳过）
d = copy.deepcopy(BASE)
# 一条非 merged 的 (path=None,match=True) 造出 M=1
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("path") is None and b.get("match") is None:
            b["match"] = True
            break
    else:
        continue
    break
# 另一条打 merged tier 但形状全坏，使 E=1 M=1 等式成立
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("path") is None and b.get("match") is None and b.get("tier") is None:
            b["tier"] = "SAMEDOC_LINK_EQ"
            break
    else:
        continue
    break
d["totals"] = cii.recompute(d["results"])
RESULTS["M-G3_malformed_merged_row"] = probe("MG3_malformed_merged_row", d, "INV-4 (19,0)", expect_merged=True)

# G5 v2 缺 counting_policy（上栏已覆盖基线态；此处 merged 态）
d = copy.deepcopy(MERGED)
d["schema_version"] = 2
d["totals"]["plus_match_by_kind"] = {"single_path": 17, "merged_eq": 1}
RESULTS["M-G5_v2_no_policy"] = probe("MG5_v2_no_policy", d, "INV-5 schema_version>=2", expect_merged=True)

# 非 merged 也能造出差 1：证明不能只靠计数判 merged
d = copy.deepcopy(BASE)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("path") is None and b.get("match") is None:
            b["match"] = True
            break
    else:
        continue
    break
d["totals"] = cii.recompute(d["results"])
_, fc = cii.evaluate(d)
print("NON-MERGED-DIFF: plus_path=%d plus_match=%d diff=%d M=%d E=%d merged_present=%s"
      % (d["totals"]["plus_path"], d["totals"]["plus_match"],
         d["totals"]["plus_match"] - d["totals"]["plus_path"],
         fc["M"], fc["E"], fc["merged_present"]))
RESULTS["NONMERGED_diff_plus1"] = probe("NONMERGED_diff_plus1", d, "INV-4 M(match_no_path)")

# 反向差：path 真值但 match=False（现版本可达，见 _civ_structural.py 实跑）
d = copy.deepcopy(BASE)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("match") is True:
            b["match"] = False
            break
    else:
        continue
    break
d["totals"] = cii.recompute(d["results"])
print("REVERSE-DIFF: plus_path=%d plus_match=%d E=%d" %
      (d["totals"]["plus_path"], d["totals"]["plus_match"], 0))
RESULTS["REVERSE_diff"] = probe("REVERSE_diff", d, "INV-5 E=0")

print()
print("== SUMMARY ==")
for k, ok in RESULTS.items():
    print(("  OK   " if ok else "  MISS "), k)
print("ALL_ALERT =", all(RESULTS.values()), " COUNT =", len(RESULTS))
sys.exit(0 if all(RESULTS.values()) else 1)
