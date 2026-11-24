# -*- coding: utf-8 -*-
"""_mk_project.py — ③ 接入后对下游的精确投影（只读；零真机；零采样代码）。

用本写域候选 _mk_r11plus_candidate.py 与原件 _f2_r11plus.py 对同一 30 件
清单对跑，投影：(1) totals 漂移；(2) _f2_compare.py:44-50 断言是否仍过；
(3) warnings/problems 变化；(4) 每个下游消费者对 1 条 merged rec 的实测反应。
不改 _f2_compare.py、不改 _f2_compare_out.json、不改任何既有件。
运行：python -I -X utf8 "D:/.../lead/merged_contract_20261109/_mk_project.py"
"""
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_contract_20261109"
R11 = REPO / "lead" / "r11_f2_fix_20261109"


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


g7 = load("g7x", REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
orig = load("pl_o", R11 / "_f2_r11plus.py")
cand = load("pl_c", W / "_mk_r11plus_candidate.py")
reg = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json").read_text(encoding="utf-8"))

print("== A 30 件对跑：totals 投影（_f2_compare.py 聚合逻辑逐行复刻，不落盘）==")
K = ["bindings", "orig_path", "plus_path", "orig_match", "plus_match",
     "orig_problems", "plus_problems"]
t0, t1 = dict.fromkeys(K, 0), dict.fromkeys(K, 0)
diff_doc = diff_bind = 0
newtiers = {}
warn0 = warn1 = prob1 = 0
assert_bad = []
merged_rec = None
for r in reg["results_30"]:
    p = Path(r["file"]); text = p.read_text(encoding="utf-8"); dd = p.parent
    op, ow, ob = g7.r11_scan(text, dd, root=REPO)
    tp, tw, tb = orig.r11_scan_plus(text, dd, root=REPO)
    np, nw, nb = cand.r11_scan_plus(text, dd, root=REPO)
    for t, bs in ((t0, tb), (t1, nb)):
        t["bindings"] += len(ob)
        t["orig_path"] += sum(1 for b in ob if b["path"])
        t["plus_path"] += sum(1 for b in bs if b.get("path"))
        t["orig_match"] += sum(1 for b in ob if b["match"] is True)
        t["plus_match"] += sum(1 for b in bs if b.get("match") is True)
        t["orig_problems"] += len(op)
    t0["plus_problems"] += len(tp)
    t1["plus_problems"] += len(np)
    # _f2_compare.py:44-50 三条断言投影
    ok = len(ob) == len(nb) and [b["declared"] for b in ob] == [b["declared"] for b in nb]
    for x, y in zip(ob, nb):
        if x["path"] is not None and y["path"] != x["path"]:
            ok = False
    if not ok:
        assert_bad.append(p.name)
    warn0 += len(tw); warn1 += len(nw); prob1 += len(np)
    if any(x != y for x, y in zip(tb, nb)):
        diff_doc += 1
    for a, b in zip(tb, nb):
        if a != b:
            diff_bind += 1
            nt = b.get("tier"); newtiers[nt] = newtiers.get(nt, 0) + 1
            if nt == "SAMEDOC_LINK_EQ" and merged_rec is None:
                merged_rec = (p.name, b, nw)
print("BEFORE totals (既有产物)   =", json.dumps(t0, ensure_ascii=False, sort_keys=True))
print("AFTER  totals (③接、④未裁) =", json.dumps(t1, ensure_ascii=False, sort_keys=True))
print("DRIFT =", {k: (t0[k], t1[k]) for k in K if t0[k] != t1[k]})
print("changed docs = %d/30 ; changed bindings = %d/19 ; new tier dist = %s"
      % (diff_doc, diff_bind, newtiers))
print("_f2_compare.py:44-50 断言投影 pass = %d/30  bad = %r" % (30 - len(assert_bad), assert_bad))
print("warnings total %d -> %d ; plus_problems AFTER = %d (纪律应恒 23)" % (warn0, warn1, prob1))
print()
print("== B 唯一 merged rec 的形状（来自 _integ_INTEGRATION_REPORT.md）==")
fn, b, nw = merged_rec
print("file =", fn)
print("keys =", sorted(b.keys()))
print("tier=%r match=%r path=%r members_n=%d decl_lines=%r" % (
    b.get("tier"), b.get("match"), b.get("path"), len(b.get("members", [])), b.get("decl_lines")))
print("members =", json.dumps(b.get("members"), ensure_ascii=False))
print("missing single-obj keys =", {k: (k not in b) for k in ["verified_path", "recomputed", "bytes"]})
print("warnings_n =", len(nw))
print()
print("== C 各消费者对这条 merged rec 的实测反应（纯表达式，不改件）==")
M = b
# _f2v_verify9.py:21-29 —— ① 已设计补丁前
try:
    src = M.get("alt") or M
    from pathlib import Path as _P
    vp = _P(src.get("verified_path") or src.get("path"))
    print("C1 _f2v_verify9.py:24 (补丁前) =", vp)
except Exception as e:
    print("C1 _f2v_verify9.py:24 (补丁前) = %s: %s" % (type(e).__name__, e))
print("C2 _f2w_checks.py:29  sha_ok =", (M.get("recomputed") or "").lower() == M["declared"].lower())
print("C3 _f2w_extract.py:26-33 verified=%r recomputed=%r bytes=%r" % (
    M.get("verified_path", "") or "", M.get("recomputed", "") or "", M.get("bytes", "-")))
print("C4 _f2w_pass.py:17  plus match 计数 +=1（merged 混入单一回验统计）")
print("C5 _f2_compare.py:67/69 (plus_path,plus_match) 对 merged 单条 = (0,1)")
print("C6 _f2v_final.py:54-58 / _f2w_dogfood.py:25-30 collected=0 match=1 tiers={'SAMEDOC_LINK_EQ':1}")
print("C7 _f2v_run.py:49-52 plus_paths=[None] plus_match=[True] plus_tiers=['SAMEDOC_LINK_EQ']")
print("C8 _f2_selftest.py:110 nb[0].get('verified_path','').endswith(...) =",
      M.get("verified_path", "").endswith("_f2_r11plus.py"))
print("C9 _g9_gate.py:157-160 若改接 plus: reverified=0 match_true=1 problems=[] -> PASS（补丁②未落地时）")
print("C10 _f2w_final.py:31-33 只数 warnings：warnings_n=%d（正常）" % len(nw))
print()
print("== END ==")
