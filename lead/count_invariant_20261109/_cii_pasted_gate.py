# -*- coding: utf-8 -*-
# 粘贴到回归脚本；doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
# 本片段 = lead/count_invariant_20261109/_cii_checks.py 的 evaluate() 等价实现；
# 零真机、零采样代码、只读、不写盘、不 import 项目业务模块。
from collections import Counter

SEVEN = ("bindings", "orig_path", "plus_path", "orig_match",
         "plus_match", "orig_problems", "plus_problems")
TIERS = {"T1", "T2", "T2N", "T3", None, "SAMEDOC_LINK", "SAMEDOC_LINK_EQ"}
MERGED = "SAMEDOC_LINK_EQ"

def ci_gate(doc, expect_merged=False):
    T, R = doc.get("totals", {}), doc.get("results", [])
    v = []
    rows = [(i, k, b) for i, r in enumerate(R)
            for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    # ---- INV-1: totals 必须从 results[] 独立重算（复刻 _f2_compare.py:65-71）----
    rec = dict.fromkeys(SEVEN, 0)
    for r in R:
        ob, nb = r["orig"]["bindings"], r["plus"]["bindings"]
        rec["bindings"]      += len(ob)                                        # :65
        rec["orig_path"]     += sum(1 for b in ob if b["path"])               # :66
        rec["plus_path"]     += sum(1 for b in nb if b.get("path"))           # :67
        rec["orig_match"]    += sum(1 for b in ob if b["match"] is True)      # :68
        rec["plus_match"]    += sum(1 for b in nb if b.get("match") is True)  # :69
        rec["orig_problems"] += len(r["orig"]["problems"])                    # :70
        rec["plus_problems"] += len(r["plus"]["problems"])                    # :71
    for k in SEVEN:
        if T.get(k) != rec[k]:
            v.append("INV-1 totals.%s=%r != recomputed=%r" % (k, T.get(k), rec[k]))
    if not all(isinstance(T.get(k), int) and T[k] >= 0
               for k in ("orig_problems", "plus_problems")):
        v.append("INV-1 negative/non-int problems")
    for i, r in enumerate(R):                     # 双向等价：第三值 verdict 也报警
        for side in ("orig", "plus"):
            s = r[side]
            if (len(s.get("problems", [])) == 0) != (s.get("verdict") == "PASS"):
                v.append("INV-1 (%d,%s) verdict/problems inconsistent" % (i, side))

    # ---- INV-2: 上界 / 单调 / ★集合级恒等 ----
    nb = T.get("bindings", 0)
    for k in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if not (isinstance(T.get(k), int) and 0 <= T[k] <= nb):
            v.append("INV-2 %s out of [0,bindings]" % k)
    if rec["bindings"] != nb or len(rows) != nb:
        v.append("INV-2 bindings/plus_rows mismatch")
    if T.get("orig_path", 0) > T.get("plus_path", 0) or \
       T.get("orig_match", 0) > T.get("plus_match", 0):
        v.append("INV-2 coverage not monotone")
    P = {(i, k) for i, k, b in rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        v.append("INV-2 numeric equal but SET differs: %r / %r"
                 % (sorted(P - S), sorted(S - P)))          # CE-08 唯一抓得到的断言

    # ---- INV-3: tier 显式键 + 白名单（.get() 会把缺键吞进 None 桶）----
    if sum(Counter("<NOKEY>" if "tier" not in b else b.get("tier")
                   for _, _, b in rows).values()) != nb:
        v.append("INV-3 tier partition incomplete")
    for i, k, b in rows:
        if "tier" not in b:
            v.append("INV-3 (%d,%d) missing explicit tier key" % (i, k))
        elif b.get("tier") not in TIERS:
            v.append("INV-3 (%d,%d) tier %r not whitelisted" % (i, k, b.get("tier")))

    # ---- INV-4: merged 判别；形状检查用全称量词 ∀ tier==MERGED ----
    M = sum(1 for _, _, b in rows if not b.get("path") and b.get("match") is True)
    E = sum(1 for _, _, b in rows if b.get("tier") == MERGED)
    if M != E:
        v.append("INV-4 M=%d != E=%d (non-merged cause OR missing merged dimension)" % (M, E))
    bad = 0
    for i, k, b in rows:
        if b.get("tier") != MERGED:
            continue
        if b.get("path") is not None or b.get("match") is not True:
            v.append("INV-4 (%d,%d) merged row not match=True/path=None" % (i, k)); bad += 1
        if not isinstance(b.get("members"), list) or len(b.get("members", [])) < 2:
            v.append("INV-4 (%d,%d) merged row missing members>=2" % (i, k)); bad += 1
        for key in ("verified_path", "recomputed", "bytes"):
            if key in b:
                v.append("INV-4 (%d,%d) merged row has %r" % (i, k, key)); bad += 1
    if rec["plus_match"] - rec["plus_path"] != E:
        v.append("INV-4 plus_match-plus_path != merged_eq=%d" % E)
    present = (E > 0 and M == E and not bad
               and rec["plus_match"] - rec["plus_path"] == E)
    if present != expect_merged:
        v.append("INV-4 merged_present=%r != expected=%r" % (present, expect_merged))

    # ---- INV-5: 新维度存在性 + 条件化恒等（INV-06 的正确重定义）----
    sv = doc.get("schema_version", T.get("schema_version", 1))
    policy = ("counting_policy" in doc) or ("counting_policy" in T)
    if (isinstance(sv, int) and sv >= 2) or policy:
        if not policy:
            v.append("INV-5 schema_version>=2 but no counting_policy")
        k = T.get("plus_match_by_kind")
        if not isinstance(k, dict):
            v.append("INV-5 no plus_match_by_kind")
        else:
            sp, me = k.get("single_path"), k.get("merged_eq")
            if not (isinstance(sp, int) and isinstance(me, int)):
                v.append("INV-5 by_kind incomplete")
            else:
                if sp != rec["plus_path"]:   v.append("INV-5 single_path != plus_path")
                if sp + me != rec["plus_match"]: v.append("INV-5 sp+me != plus_match")
                if me != E:                  v.append("INV-5 merged_eq != E")
    if E == 0:
        if rec["plus_path"] != rec["plus_match"]:
            v.append("INV-5 E=0 but baseline identity broken")
    elif rec["plus_match"] - rec["plus_path"] != E:
        v.append("INV-5 merged state identity incomplete")
    return v

# CI 用法（缺一不可）：
#   v = ci_gate(json.loads(Path(p).read_text(encoding="utf-8")), expect_merged=False)
#   assert not v, "\n".join(v)
#   且必须同时跑 _cii_counterexamples.py：ALL_ALERT=True COUNT=17 才算门槛有效；
#   改口径后另跑 ci_gate(proj, expect_merged=True)，期望 violations=0。
