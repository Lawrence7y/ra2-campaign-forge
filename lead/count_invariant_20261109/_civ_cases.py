# -*- coding: utf-8 -*-
"""_civ_cases.py — 复核员独立实跑 10 个反例 + 3 组额外反例（第三步 c / 第四步 c）。

构造全在 tempfile.mkdtemp(prefix="_civ_ce_")；不改既有产物、不落既有写域。
对每条：先写临时 JSON，再用独立求值器 _civ_lib.evaluate() 判断「是否真的报警」。
"""
import copy
import json
import pathlib
import sys
import tempfile
import importlib.util

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "count_invariant_20261109"
SRC = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_compare_out.json"
spec = importlib.util.spec_from_file_location("_civ_lib", W / "_civ_lib.py")
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

BASE = json.loads(SRC.read_text(encoding="utf-8"))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_civ_ce_"))
print("TEMP:", TMP)
RESULTS = {}


def run(name, doc, expect_prefix, note=""):
    p = TMP / (name + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    v, f = lib.evaluate(doc)
    hit = [x for x in v if (expect_prefix is not None and x.startswith(expect_prefix))]
    ok = (expect_prefix is None) or bool(hit)
    print("[%s] %s expect=%s alerts=%d hit=%d %s" %
          ("PASS" if ok else "FAIL", name, expect_prefix, len(v), len(hit), note))
    for x in v:
        print("      ", x)
    RESULTS[name] = ok
    return p, v, f


# ---- ②(5条) + 其余 9 条：逐条独立构造 ----
# CE-01: totals.plus_match=8，results[] 不动
d = copy.deepcopy(BASE); d["totals"]["plus_match"] = 8
run("CE01_totals_pm8", d, "INV-01")

# CE-02: totals.plus_path=20 (>bindings 19)
d = copy.deepcopy(BASE); d["totals"]["plus_path"] = 20
run("CE02_pp20", d, "INV-02")

# CE-03: totals.orig_path=12 (>plus_path 9)
d = copy.deepcopy(BASE); d["totals"]["orig_path"] = 12
run("CE03_op12", d, "INV-03")

# CE-04: plus_problems=-1 且 #0 plus.verdict="FAIL" 而 problems=[]
d = copy.deepcopy(BASE); d["totals"]["plus_problems"] = -1
d["results"][0]["plus"]["verdict"] = "FAIL"
run("CE04_neg_and_verdict_lie", d, "INV-04")

# CE-05: 删 (3,0) 的 tier 键。同时跑弱版(.get 计数)证明 Σ 不变不报警
d = copy.deepcopy(BASE)
b30 = d["results"][3]["plus"]["bindings"][0]
oldtier = b30.pop("tier")
p, v, f = run("CE05_drop_tier_key", d, "INV-05", "(removed tier=%r)" % oldtier)
weak, wf = lib.naive_evaluate_tier(d)
print("      WEAK(.get-only) alerts=%d  tiers=%r sum=%d  -> concealment=%s" %
      (len(weak), wf["tiers"], wf["sum"], "YES(no alert)" if not weak else "NO"))
RESULTS["CE05_weak_no_alert"] = (len(weak) == 0)

# CE-06: 把 1 条 match=True 改 False 并同步 totals（隔离 INV-06）
d = copy.deepcopy(BASE)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("match") is True:
            b["match"] = False
            break
    else:
        continue
    break
d["totals"]["plus_match"] = 8
run("CE06_break_identity", d, "INV-06")

# CE-07: path=None/match=True/tier=T2 带 members 但不打 merged 标
d = copy.deepcopy(BASE)
b0 = d["results"][29]["plus"]["bindings"][4]
d["results"][29]["plus"]["bindings"][4] = {
    "declared": b0["declared"], "path": None, "match": True, "tier": "T2",
    "citation": b0.get("citation"), "members": [{"x": 1}, {"y": 2}], "decl_lines": [13]}
d["totals"]["plus_path"] = 8; d["totals"]["plus_match"] = 9
run("CE07_merged_without_tier", d, "INV-07")

# CE-08: 成对对称错值；totals 一字节不改
d = copy.deepcopy(BASE)
rows = [(i, k, b) for i, r in enumerate(d["results"]) for k, b in enumerate(r["plus"]["bindings"])]
pr = [(i, k) for i, k, b in rows if b.get("path")]
nr = [(i, k) for i, k, b in rows if not b.get("path")]
i0, k0 = pr[0]; i1, k1 = nr[0]
d["results"][i0]["plus"]["bindings"][k0]["match"] = False
d["results"][i1]["plus"]["bindings"][k1]["match"] = True
p, v, f = run("CE08_symmetric_drift", d, "INV-08",
              "(totals unchanged=%s)" % (d["totals"] == BASE["totals"]))
RESULTS["CE08_totals_byte_unchanged"] = (d["totals"] == BASE["totals"])
# 同时确认：7 键独立重算仍全等 rec（故 INV-01..04/06 全不报）
rec = lib.recompute(d["results"])
print("      RECOMPUTED==STORED(7keys)=%s ; INV-01 alerts=%d ; INV-06 alerts=%d" %
      (rec == d["totals"], len([x for x in v if x.startswith("INV-01")]),
       len([x for x in v if x.startswith("INV-06")])))
RESULTS["CE08_no_recompute_alert"] = (rec == d["totals"] and
                                       not [x for x in v if x.startswith("INV-01")] and
                                       not [x for x in v if x.startswith("INV-06")])

# CE-09: 只加 schema_version=2
d = copy.deepcopy(BASE); d["schema_version"] = 2
run("CE09_v2_no_policy", d, "INV-09")

# CE-09b: by_kind={single_path:9, merged_eq:1} 而 plus_match=9
d = copy.deepcopy(BASE); d["schema_version"] = 2; d["counting_policy"] = "X"
d["totals"]["plus_match_by_kind"] = {"single_path": 9, "merged_eq": 1}
run("CE09b_bykind_inconsistent", d, "INV-09")

# ---- ③(c)1：非 merged 造出 plus_match>plus_path ----
d = copy.deepcopy(BASE)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("path") is None and b.get("match") is None:
            b["match"] = True
            break
    else:
        continue
    break
d["totals"]["plus_match"] = 10
p, v, f = run("CIV_nonmerged_diff_plus1", d, "INV-07",
              "plus_path=%r plus_match=%r" % (d["totals"]["plus_path"], d["totals"]["plus_match"]))
print("      plus_match>plus_path=%s M=%d E=%d merged_present=%s TRUE_MERGED=%s" %
      (d["totals"]["plus_match"] > d["totals"]["plus_path"], f["M"], f["E"],
       f["merged_present"],
       any(b.get("tier") == "SAMEDOC_LINK_EQ" for r in d["results"]
           for b in r["plus"]["bindings"])))
RESULTS["CIV_nonmerged_diff_plus1_no_merged"] = (
    d["totals"]["plus_match"] > d["totals"]["plus_path"] and f["E"] == 0 and
    f["merged_present"] is False and
    not any(b.get("tier") == "SAMEDOC_LINK_EQ" for r in d["results"]
            for b in r["plus"]["bindings"]))

# ---- ③(c)2：反向差 plus_match<plus_path ----
d = copy.deepcopy(BASE)
for r in d["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("match") is True:
            b["match"] = False
            break
    else:
        continue
    break
d["totals"]["plus_match"] = 8
p, v, f = run("CIV_reverse_diff", d, "INV-06",
              "plus_path=%r plus_match=%r E=%d" % (d["totals"]["plus_path"],
                                                    d["totals"]["plus_match"], f["E"]))
RESULTS["CIV_reverse_diff"] = (d["totals"]["plus_path"] > d["totals"]["plus_match"] and f["E"] == 0)

# ---- 纯 7 键计数无法区分：两份 results[] 不同但 7-key totals 完全相同 ----
# 构造 A：非 merged 差1 (pp=9,pm=10); 构造 B：把差1 换成 merged 标，且 totals 同 7 键
dA = copy.deepcopy(BASE)
for r in dA["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("path") is None and b.get("match") is None:
            b["match"] = True; break
    else: continue
    break
dA["totals"]["plus_match"] = 10
dB = copy.deepcopy(BASE)
for r in dB["results"]:
    for b in r["plus"]["bindings"]:
        if b.get("path") is None and b.get("match") is None:
            b["match"] = True; b["tier"] = "SAMEDOC_LINK_EQ"
            b["members"] = [{"x": 1}, {"y": 2}]; break
    else: continue
    break
dB["totals"]["plus_match"] = 10
print()
print("=== 7-key totals 投影多对一实证 ===")
print("  A(non-merged) totals =", json.dumps(dA["totals"], sort_keys=True))
print("  B(merged-tier) totals=", json.dumps(dB["totals"], sort_keys=True))
print("  totals EQUAL =", dA["totals"] == dB["totals"],
      " results[] EQUAL =", dA["results"] == dB["results"])
va, fa = lib.evaluate(dA); vb, fb = lib.evaluate(dB)
print("  A: M=%d E=%d merged_present=%s alerts=%r" % (fa["M"], fa["E"], fa["merged_present"], [x[:30] for x in va]))
print("  B: M=%d E=%d merged_present=%s alerts=%r" % (fb["M"], fb["E"], fb["merged_present"], [x[:30] for x in vb]))
RESULTS["CIV_7key_multitoone"] = (dA["totals"] == dB["totals"] and dA["results"] != dB["results"])

# ---- INV-07 形状全称量词漏洞：构造 M==E 但 merged-tier 行本身畸形 ----
#  独立构造：① 把一条 (path=None,match=None) 行改成 match=True/tier=T2  => M=1
#            ② 把另一条 (path=None,match=None) 行改成 tier=SAMEDOC_LINK_EQ/match=None
#               （无 members、无单对象三键）                        => E=1
#  totals 同步成自洽值。M==E=1 ⇒ 撰写员实现的 INV-07 唯一等式不报；
#  而其形状检查只在 (not path and match is True and tier==MERGED) 时才跑，
#  故畸形 merged 行被跳过。复核员独立实现按 §3(d) 全称量词检查所有 merged-tier 行 ⇒ 报警。
d = copy.deepcopy(BASE)
cands = [(ri, ki) for ri, r in enumerate(d["results"])
         for ki, b in enumerate(r["plus"]["bindings"])
         if b.get("path") is None and b.get("match") is None]
(ra, ka), (rb, kb) = cands[0], cands[1]
d["results"][ra]["plus"]["bindings"][ka]["match"] = True
d["results"][ra]["plus"]["bindings"][ka]["tier"] = "T2"
d["results"][rb]["plus"]["bindings"][kb]["tier"] = "SAMEDOC_LINK_EQ"  # match 仍 None，无 members
rec = lib.recompute(d["results"])
d["totals"]["plus_path"] = rec["plus_path"]
d["totals"]["plus_match"] = rec["plus_match"]
p, v, f = run("CIV_merged_row_shape_gap", d, None,
              "M=%d E=%d" % (f["M"], f["E"]))
# 同时跑撰写员实现 _ci_checks.evaluate() 作对照
import importlib.util as _ilu
_s = _ilu.spec_from_file_location("_ci_checks_ref", W / "_ci_checks.py")
_ci = _ilu.module_from_spec(_s); _s.loader.exec_module(_ci)
wv, wf = _ci.evaluate(d)
print("      WRITER _ci_checks INV-07 alerts=%r ; INDEPENDENT INV-07 alerts=%r" %
      ([x for x in wv if x.startswith("INV-07")], [x for x in v if x.startswith("INV-07")]))
print("      independent shape-check caught = %s" % any("merged-tier row" in x for x in v))
RESULTS["CIV_merged_row_shape_gap"] = (
    f["M"] == f["E"] == 1 and
    not [x for x in wv if x.startswith("INV-07")] and
    any("merged-tier row" in x for x in v))

# ---- 基线（对照组）：0 报警 ----
p, v, f = run("CIV_BASELINE", copy.deepcopy(BASE), None)
print("      BASELINE alerts=%d (expected 0)" % len(v))
RESULTS["CIV_BASELINE_zero_alerts"] = (len(v) == 0)

print()
print("== SUMMARY ==")
for k, ok in RESULTS.items():
    print("  %s %s" % ("OK   " if ok else "MISS ", k))
ALL = all(RESULTS[k] for k in RESULTS if k != "CIV_BASELINE")
CE_KEYS = [k for k in RESULTS if k.startswith("CE0")]
print("CE_ALL_ALERT =", all(RESULTS[k] for k in CE_KEYS), " CE_COUNT =", len(CE_KEYS))
print("ALL_ASSERTIONS =", all(RESULTS.values()))
sys.exit(0 if all(RESULTS.values()) else 1)
