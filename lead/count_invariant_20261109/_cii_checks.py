# -*- coding: utf-8 -*-
"""_cii_checks.py — 本会话独立实现的 5 条计数不变量求值器（只读，不写盘，不 import 业务模块）。

与上游 _ci_checks.py / _civ_lib.py 不共享实现；按本会话 COUNT_INVARIANTS.md §3 的定义重写。
修正上游复核指出的 4 处缺陷：
  缺陷1 不宣称 match is True <=> path 真值 是控制流结构性后果（只承认单向蕴含）；
  缺陷2 verdict 与 problems 双向一致检查无格式化崩溃；
  缺陷3 merged 行形状检查用全称量词 ∀ b: tier=="SAMEDOC_LINK_EQ"，不以 match is True 为门槛；
  缺陷4 门槛 = 完整 5 条，不是弱化版；条件化恒等只在 E==0 时锁基线恒等。

用法：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_cii_checks.py <json> [--expect-merged]
"""
import json
import sys
from collections import Counter
from pathlib import Path

SEVEN = ("bindings", "orig_path", "plus_path", "orig_match",
         "plus_match", "orig_problems", "plus_problems")
TIER_WHITELIST = {"T1", "T2", "T2N", "T3", None,
                  "SAMEDOC_LINK", "SAMEDOC_LINK_EQ"}
MERGED_TIER = "SAMEDOC_LINK_EQ"
SINGLE_OBJECT_KEYS = ("verified_path", "recomputed", "bytes")


def recompute(R):
    """独立复刻 _f2_compare.py:65-71 的 7 个聚合表达式（totals 不作权威）。"""
    acc = dict.fromkeys(SEVEN, 0)
    for r in R:
        ob = r.get("orig", {}).get("bindings", [])
        nb = r.get("plus", {}).get("bindings", [])
        acc["bindings"] += len(ob)                                             # :65
        acc["orig_path"] += sum(1 for b in ob if b["path"])                   # :66
        acc["plus_path"] += sum(1 for b in nb if b.get("path"))               # :67
        acc["orig_match"] += sum(1 for b in ob if b["match"] is True)         # :68
        acc["plus_match"] += sum(1 for b in nb if b.get("match") is True)     # :69
        acc["orig_problems"] += len(r.get("orig", {}).get("problems", []))    # :70
        acc["plus_problems"] += len(r.get("plus", {}).get("problems", []))    # :71
    return acc


def evaluate(doc, expect_merged=False):
    """doc = json.loads(...); return (violations:list[str], facts:dict)。
    violations 非空 = 报警。每条以 INV-1..INV-5 打头，便于 grep。"""
    v = []
    T = doc.get("totals", {})
    R = doc.get("results", [])
    if not isinstance(R, list):
        return ["INV-1 results_not_list"], {"n_results": 0}
    rows = [(i, k, b) for i, r in enumerate(R)
            for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    rec = recompute(R)

    # ---------- INV-1 计数重算与明细一致（防硬编码 / 计数口径与明细脱钩 / verdict 谎言） ----------
    for k in SEVEN:
        if k not in T:
            v.append("INV-1 missing totals.%s" % k)
        elif T[k] != rec[k]:
            v.append("INV-1 totals.%s=%r != recomputed=%r" % (k, T[k], rec[k]))
    for k in ("orig_problems", "plus_problems"):
        if not (isinstance(T.get(k), int) and T[k] >= 0):
            v.append("INV-1 %s=%r negative/non-int" % (k, T.get(k)))
    for i, r in enumerate(R):
        for side in ("orig", "plus"):
            s = r.get(side, {})
            nprob = len(s.get("problems", []))
            verdict = s.get("verdict")
            # 双向等价（含第三值 UNKNOWN / None 也必须报警）；无 % 占位符参数个数错误
            if (nprob == 0) != (verdict == "PASS"):
                v.append("INV-1 (%d,%s) nproblems=%d verdict=%r inconsistent"
                         % (i, side, nprob, verdict))

    # ---------- INV-2 上界 / 覆盖单调 / 集合级恒等（防对称错值） ----------
    nb = T.get("bindings", 0)
    for k in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if not (isinstance(T.get(k), int) and 0 <= T[k] <= nb):
            v.append("INV-2 %s=%r not in [0,%r]" % (k, T.get(k), nb))
    if rec["bindings"] != nb or len(rows) != nb:
        v.append("INV-2 sum(len(orig.bindings))=%d plus_rows=%d != bindings=%r"
                 % (rec["bindings"], len(rows), nb))
    if T.get("orig_path", 0) > T.get("plus_path", 0):
        v.append("INV-2 orig_path=%r > plus_path=%r coverage not monotone"
                 % (T.get("orig_path"), T.get("plus_path")))
    if T.get("orig_match", 0) > T.get("plus_match", 0):
        v.append("INV-2 orig_match=%r > plus_match=%r coverage not monotone"
                 % (T.get("orig_match"), T.get("plus_match")))
    P = {(i, k) for i, k, b in rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        v.append("INV-2 plus_path==plus_match numerically but SET differs: "
                 "path\\match=%r match\\path=%r" % (sorted(P - S), sorted(S - P)))

    # ---------- INV-3 tier 维度完备（防 .get() 把缺键吞进 None 桶） ----------
    tc = Counter("<NOKEY>" if "tier" not in b else b.get("tier") for _, _, b in rows)
    if sum(tc.values()) != nb:
        v.append("INV-3 tier partition sum=%d != bindings=%r" % (sum(tc.values()), nb))
    for i, k, b in rows:
        if "tier" not in b:
            v.append("INV-3 (%d,%d) missing explicit tier key" % (i, k))
        elif b.get("tier") not in TIER_WHITELIST:
            v.append("INV-3 (%d,%d) tier %r not whitelisted" % (i, k, b.get("tier")))

    # ---------- INV-4 merged 判别 + 形状全称量词 ----------
    M = sum(1 for _, _, b in rows
            if not b.get("path") and b.get("match") is True)
    E = sum(1 for _, _, b in rows if b.get("tier") == MERGED_TIER)
    if M != E:
        v.append("INV-4 M(match_no_path)=%d != E(merged_tier)=%d "
                 "(non-merged cause OR missing merged dimension)" % (M, E))
    shape_bad = []
    for i, k, b in rows:
        if b.get("tier") != MERGED_TIER:
            continue                     # ★ 全称量词：只看 tier，不要求 match is True
        if b.get("path") is not None or b.get("match") is not True:
            shape_bad.append("INV-4 (%d,%d) merged-tier row not match=True/path=None" % (i, k))
        if not isinstance(b.get("members"), list) or len(b.get("members", [])) < 2:
            shape_bad.append("INV-4 (%d,%d) merged-tier row missing members>=2" % (i, k))
        for key in SINGLE_OBJECT_KEYS:
            if key in b:
                shape_bad.append("INV-4 (%d,%d) merged-tier row has single-object key %r"
                                 % (i, k, key))
    v.extend(shape_bad)
    if rec["plus_match"] - rec["plus_path"] != E:
        v.append("INV-4 plus_match-plus_path=%d != merged_eq=%d"
                 % (rec["plus_match"] - rec["plus_path"], E))
    merged_present = (E > 0 and M == E and not shape_bad
                      and rec["plus_match"] - rec["plus_path"] == E)
    if merged_present != expect_merged:
        v.append("INV-4 merged_present=%r != expected=%r" % (merged_present, expect_merged))

    # ---------- INV-5 新维度存在性 + 条件化恒等（INV-06 的正确重定义） ----------
    sv = doc.get("schema_version", T.get("schema_version", 1))
    has_policy = ("counting_policy" in doc) or ("counting_policy" in T)
    v2 = (isinstance(sv, int) and sv >= 2) or has_policy
    if v2:
        if not has_policy:
            v.append("INV-5 schema_version>=2 but no counting_policy")
        k = T.get("plus_match_by_kind")
        if not isinstance(k, dict):
            v.append("INV-5 schema_version>=2 but no plus_match_by_kind")
        else:
            sp, me = k.get("single_path"), k.get("merged_eq")
            if not (isinstance(sp, int) and isinstance(me, int)):
                v.append("INV-5 plus_match_by_kind incomplete %r" % (k,))
            else:
                if sp != rec["plus_path"]:
                    v.append("INV-5 single_path=%r != plus_path=%r" % (sp, rec["plus_path"]))
                if sp + me != rec["plus_match"]:
                    v.append("INV-5 single_path+merged_eq=%d != plus_match=%r"
                             % (sp + me, rec["plus_match"]))
                if me != E:
                    v.append("INV-5 merged_eq=%d != E(merged_tier)=%d" % (me, E))
    # 条件化恒等：E==0 时守恒等（基线）；E>0 时差必须等于 E
    if E == 0:
        if rec["plus_path"] != rec["plus_match"]:
            v.append("INV-5 E=0 but baseline identity broken: plus_path=%d != plus_match=%d"
                     % (rec["plus_path"], rec["plus_match"]))
    else:
        if rec["plus_match"] - rec["plus_path"] != E:
            v.append("INV-5 merged state identity incomplete: plus_match-plus_path=%d != E=%d"
                     % (rec["plus_match"] - rec["plus_path"], E))

    facts = dict(
        n_results=len(R), bindings=nb, recomputed=rec,
        plus_path=T.get("plus_path"), plus_match=T.get("plus_match"),
        set_equal=(P == S), P_size=len(P), S_size=len(S),
        path_minus_match=sorted(P - S), match_minus_path=sorted(S - P),
        tiers={("<NOKEY>" if k == "<NOKEY>" else "NONE" if k is None else str(k)): n
               for k, n in tc.items()},
        tier_explicit=sum(1 for _, _, b in rows if "tier" in b),
        M=M, E=E, shape_bad=len(shape_bad), merged_present=merged_present,
        expect_merged=expect_merged, schema_version=sv,
    )
    return v, facts


def main():
    if len(sys.argv) not in (2, 3):
        print("usage: _cii_checks.py <json> [--expect-merged]")
        return 2
    p = Path(sys.argv[1])
    doc = json.loads(p.read_text(encoding="utf-8"))
    em = len(sys.argv) == 3 and sys.argv[2] == "--expect-merged"
    v, f = evaluate(doc, expect_merged=em)
    print("FILE:", str(p), " expect_merged =", em)
    print("FACTS:", json.dumps(f, ensure_ascii=False, sort_keys=True, default=str))
    if v:
        print("ALERT violations=%d" % len(v))
        for x in v:
            print("  -", x)
        return 1
    print("OK violations=0 (all 5 invariants hold)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
