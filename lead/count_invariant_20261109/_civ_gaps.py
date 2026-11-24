# -*- coding: utf-8 -*-
"""_civ_gaps.py — 复核员专查「恒等掩盖缺失」：对推荐门槛做变异测试。

构造全部落 tempfile.mkdtemp(prefix="_civ_gap_")；同时跑撰写员 _ci_checks.py /
_ci_gate.py / 复核员独立 _civ_lib.evaluate()，比较谁报警谁静默。
"""
import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "count_invariant_20261109"
SRC = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_compare_out.json"
FRESH = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_r8prxhqj\merged_projection.json")
PY, FLAGS = sys.executable, ["-I", "-X", "utf8"]


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


lib = load("_civ_lib", W / "_civ_lib.py")
ci = load("_ci_checks", W / "_ci_checks.py")
gate = load("_ci_gate", W / "_ci_gate.py")
BASE = json.loads(SRC.read_text(encoding="utf-8"))
PROJ = json.loads(FRESH.read_text(encoding="utf-8"))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_civ_gap_"))
print("TEMP:", TMP)


def probe(name, doc, expect_merged=False):
    p = TMP / (name + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        wv, wf = ci.evaluate(doc)
        werr = None
    except Exception as e:
        wv, werr = ["<CRASH:%s: %s>" % (type(e).__name__, e)], "%s" % e
    try:
        gv = gate.gate(doc, expect_merged=expect_merged)
    except Exception as e:
        gv = ["<CRASH:%s: %s>" % (type(e).__name__, e)]
    iv, ifc = lib.evaluate(doc)
    # CLI 实跑（证明不是内存求值器差异）
    r1 = subprocess.run([PY] + FLAGS + [str(W / "_ci_checks.py"), str(p)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    r2 = subprocess.run([PY] + FLAGS + [str(W / "_ci_gate.py"), str(p)] +
                        (["--expect-merged"] if expect_merged else []),
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    def brief(r):
        o = ((r.stdout or "") + (r.stderr or "")).splitlines()
        return [l.strip() for l in o if l.strip().startswith("- ") or "ALERT" in l or "OK violations=0" in l]
    print()
    print("=== %s (expect_merged=%s) ===" % (name, expect_merged))
    print("  _ci_checks.py   rc=%d %r%s" % (r1.returncode, brief(r1),
                                          "  [in-process crash: %s]" % werr if werr else ""))
    print("  _ci_gate.py     rc=%d %r" % (r2.returncode, brief(r2)))
    print("  INDEPENDENT     rc=%s %r" % ("1" if iv else "0", iv))
    return dict(checks=wv, gate=gv, indep=iv, rc_checks=r1.returncode, rc_gate=r2.returncode)


# G1: merged 投影删掉 merged 行的 members（§3(d) 全称量词要求 members∧len>=2）
d = copy.deepcopy(PROJ)
mi = [(i, k) for i, r in enumerate(d["results"])
      for k, b in enumerate(r["plus"]["bindings"]) if b.get("tier") == "SAMEDOC_LINK_EQ"]
print("merged row at", mi)
i, k = mi[0]
d["results"][i]["plus"]["bindings"][k].pop("members")
g1 = probe("G1_merged_row_no_members", d, expect_merged=True)

# G2: merged 行加单对象三键 verified_path/recomputed/bytes
d = copy.deepcopy(PROJ)
d["results"][i]["plus"]["bindings"][k]["verified_path"] = "X"
d["results"][i]["plus"]["bindings"][k]["recomputed"] = "Y"
d["results"][i]["plus"]["bindings"][k]["bytes"] = 999
g2 = probe("G2_merged_row_single_obj_keys", d, expect_merged=True)

# G3: merged-tier 行 path 被填成真值（违反 §3(d) path is None），totals 同步
d = copy.deepcopy(PROJ)
d["results"][i]["plus"]["bindings"][k]["path"] = "fake_single_object.md"
rec = lib.recompute(d["results"])
d["totals"]["plus_path"] = rec["plus_path"]
d["totals"]["plus_match"] = rec["plus_match"]
g3 = probe("G3_merged_tier_path_not_none", d, expect_merged=True)

# G4: 逐件 verdict 与 problems 明细不同步（problems=[] 却 verdict="FAIL"）
#     INV-02/04 规格写的是「len(problems)==0 <=> verdict==PASS」；
#     _ci_checks.py 逐件查，_ci_gate.py 完全不查逐件 verdict。
d = copy.deepcopy(BASE)
target = [(i, r) for i, r in enumerate(d["results"]) if r["plus"]["problems"] == []
          and r["plus"]["verdict"] == "PASS"]
print("PASS docs with problems=[] :", [(i, r["file"].split(chr(92))[-1]) for i, r in target][:5])
i0 = target[0][0]
d["results"][i0]["plus"]["verdict"] = "FAIL"   # 明细不动，totals 不动
g4 = probe("G4_verdict_FAIL_problems_empty", d)

# G4b: verdict 取第三值（既非 PASS 也非 FAIL），INV-04 的双条件实现不覆盖
d = copy.deepcopy(BASE)
d["results"][i0]["plus"]["verdict"] = "UNKNOWN"
g4b = probe("G4b_verdict_UNKNOWN", d)

# G7: 恒等掩盖缺失 —— 构造 M==E==0、7 键全等、P!=S 的「缺维度」输入
#     取一条 (path 真/match True) 与一条 (path None/match None) 对调：
#     A 行去掉 path 并 match=False；B 行加 path 并 match=True ⇒ 数字仍 9/9，
#     但 P 与 S 各偏一格；tier 一个都不加 ⇒ E=0, M=0 ⇒ INV-07 双零不报警。
d = copy.deepcopy(BASE)
rows = [(i, k, b) for i, r in enumerate(d["results"]) for k, b in enumerate(r["plus"]["bindings"])]
pr = [(i, k) for i, k, b in rows if b.get("path")]
nr = [(i, k) for i, k, b in rows if not b.get("path")]
(i1, k1), (i2, k2) = pr[0], nr[0]
d["results"][i1]["plus"]["bindings"][k1]["path"] = None
d["results"][i1]["plus"]["bindings"][k1]["match"] = False
d["results"][i2]["plus"]["bindings"][k2]["path"] = "swapped.md"
d["results"][i2]["plus"]["bindings"][k2]["match"] = True
g7 = probe("G7_identity_masks_missing_dimension", d)

# G5: 未知 tier 值（INV-05 白名单；gate 无白名单）
d = copy.deepcopy(BASE)
d["results"][3]["plus"]["bindings"][0]["tier"] = "T9_NOT_A_TIER"
g5 = probe("G5_unknown_tier", d)

# G6: schema_version=2 但无 counting_policy（INV-09 规格要求；gate 只查 by_kind）
d = copy.deepcopy(BASE)
d["schema_version"] = 2
d["totals"]["plus_match_by_kind"] = {"single_path": 9, "merged_eq": 0}
g6 = probe("G6_v2_no_counting_policy", d)

print()
print("=== 汇总：哪条门槛静默放过 ===")
rows = [
    ("G1 merged 行无 members", g1),
    ("G2 merged 行带单对象三键", g2),
    ("G3 merged-tier 行 path 非 None", g3),
    ("G4 verdict=FAIL 但 problems=[]", g4),
    ("G4b verdict=UNKNOWN", g4b),
    ("G5 未知 tier 值", g5),
    ("G6 v2 缺 counting_policy", g6),
    ("G7 恒等掩盖维度缺失 (M=E=0)", g7),
]
for name, g in rows:
    print("  %-36s checks=%s gate=%s indep=%s" %
          (name, "ALERT" if g["checks"] else "SILENT",
           "ALERT" if g["gate"] else "SILENT",
           "ALERT" if g["indep"] else "SILENT"))
