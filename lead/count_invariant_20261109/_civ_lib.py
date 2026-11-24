# -*- coding: utf-8 -*-
"""_civ_lib.py — 复核员独立实现的 9 条不变量求值器（与 _ci_checks.py 无代码共享）。

只读；零真机；零采样代码；不 import 项目内业务模块；不写盘。
依据：_ci_INVARIANTS.md §2 表格中的定义文字独立重写，不采信撰写员实现。
"""
import json
from collections import Counter

SEVEN = ("bindings", "orig_path", "plus_path", "orig_match",
         "plus_match", "orig_problems", "plus_problems")
WHITELIST = {"T1", "T2", "T2N", "T3", None, "SAMEDOC_LINK", "SAMEDOC_LINK_EQ"}


def recompute(R):
    """独立复刻 _f2_compare.py:65-71 的聚合表达式。"""
    acc = dict.fromkeys(SEVEN, 0)
    for r in R:
        ob = r.get("orig", {}).get("bindings", [])
        nb = r.get("plus", {}).get("bindings", [])
        acc["bindings"] += len(ob)
        acc["orig_path"] += sum(1 for b in ob if b["path"])
        acc["plus_path"] += sum(1 for b in nb if b.get("path"))
        acc["orig_match"] += sum(1 for b in ob if b["match"] is True)
        acc["plus_match"] += sum(1 for b in nb if b.get("match") is True)
        acc["orig_problems"] += len(r.get("orig", {}).get("problems", []))
        acc["plus_problems"] += len(r.get("plus", {}).get("problems", []))
    return acc


def evaluate(doc):
    """返回 (violations:list[str], facts:dict)。每条 violation 以 INV-0X 打头。"""
    out = []
    T = doc.get("totals", {})
    R = doc.get("results", [])
    plus_rows = [(i, k, b) for i, r in enumerate(R)
                 for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    rec = recompute(R)

    # INV-01: totals 七键 == results[] 独立重算
    for k in SEVEN:
        if k not in T:
            out.append("INV-01 missing totals.%s" % k)
        elif T[k] != rec[k]:
            out.append("INV-01 totals.%s=%r != recomputed=%r" % (k, T[k], rec[k]))

    # INV-02: 0 <= 四个计数 <= bindings；sum(len(orig.bindings)) == bindings
    nb = T.get("bindings", 0)
    for k in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if k in T and not (isinstance(T[k], int) and 0 <= T[k] <= nb):
            out.append("INV-02 %s=%r not in [0,%r]" % (k, T[k], nb))
    if nb != rec["bindings"]:
        out.append("INV-02 bindings=%r != sum(len(orig.bindings))=%r" % (nb, rec["bindings"]))

    # INV-03: 覆盖单调
    if T.get("orig_path", 0) > T.get("plus_path", 0):
        out.append("INV-03 orig_path=%r > plus_path=%r" % (T.get("orig_path"), T.get("plus_path")))
    if T.get("orig_match", 0) > T.get("plus_match", 0):
        out.append("INV-03 orig_match=%r > plus_match=%r" % (T.get("orig_match"), T.get("plus_match")))

    # INV-04: problems 非负整数；len(problems)==0 <=> verdict=="PASS"
    for k in ("orig_problems", "plus_problems"):
        if k in T and not (isinstance(T[k], int) and T[k] >= 0):
            out.append("INV-04 %s=%r negative/non-int" % (k, T[k]))
    for i, r in enumerate(R):
        for side in ("orig", "plus"):
            s = r.get(side, {})
            nprob = len(s.get("problems", []))
            if (nprob == 0) != (s.get("verdict") == "PASS"):
                out.append("INV-04 (%d,%s) nproblems=%d verdict=%r inconsistent"
                           % (i, side, nprob, s.get("verdict")))

    # INV-05: tier 分区完备 + 显式键存在 + 白名单
    tc = Counter("<NOKEY>" if "tier" not in b else b.get("tier") for _, _, b in plus_rows)
    if len(plus_rows) != nb or sum(tc.values()) != nb:
        out.append("INV-05 tier partition sum=%d plus_rows=%d != bindings=%r"
                   % (sum(tc.values()), len(plus_rows), nb))
    for i, k, b in plus_rows:
        if "tier" not in b:
            out.append("INV-05 (%d,%d) no explicit tier key" % (i, k))
        elif b.get("tier") not in WHITELIST:
            out.append("INV-05 (%d,%d) tier %r not whitelisted" % (i, k, b.get("tier")))

    # INV-06: 基线恒等锁
    if T.get("plus_path") != T.get("plus_match"):
        out.append("INV-06 plus_path=%r != plus_match=%r" % (T.get("plus_path"), T.get("plus_match")))

    # INV-07: M == E；merged 行形状
    match_true = [(i, k, b) for i, k, b in plus_rows if b.get("match") is True]
    both = [(i, k, b) for i, k, b in match_true if bool(b.get("path"))]
    M = len(match_true) - len(both)
    E = sum(1 for _, _, b in plus_rows if b.get("tier") == "SAMEDOC_LINK_EQ")
    if M != E:
        out.append("INV-07 M=%d != E=%d" % (M, E))
    for i, k, b in plus_rows:
        if b.get("tier") == "SAMEDOC_LINK_EQ":
            # 独立实现 §3(d) 的形状全称量词（撰写员代码只在 match is True 时查，见复核报告）
            if b.get("path") is not None or b.get("match") is not True:
                out.append("INV-07 (%d,%d) merged-tier row not match=True/path=None" % (i, k))
            if not b.get("members") or len(b.get("members", [])) < 2:
                out.append("INV-07 (%d,%d) merged-tier row missing members>=2" % (i, k))
            for key in ("verified_path", "recomputed", "bytes"):
                if key in b:
                    out.append("INV-07 (%d,%d) merged-tier row has %r" % (i, k, key))

    # INV-08: 数值相等 => 集合相等
    P = {(i, k) for i, k, b in plus_rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in plus_rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        out.append("INV-08 numeric equal but SET differs: path\\match=%r match\\path=%r"
                   % (sorted(P - S), sorted(S - P)))

    # INV-09: schema_version >= 2 时强制新维度
    sv = doc.get("schema_version", T.get("schema_version", 1))
    if isinstance(sv, int) and sv >= 2:
        if "counting_policy" not in doc and "counting_policy" not in T:
            out.append("INV-09 no counting_policy")
        k = T.get("plus_match_by_kind")
        if not k:
            out.append("INV-09 no plus_match_by_kind")
        else:
            sp, me = k.get("single_path"), k.get("merged_eq")
            if sp is None or me is None:
                out.append("INV-09 by_kind incomplete %r" % (k,))
            else:
                if sp + me != T.get("plus_match"):
                    out.append("INV-09 sp+me=%r != plus_match=%r" % (sp + me, T.get("plus_match")))
                if sp != T.get("plus_path"):
                    out.append("INV-09 sp=%r != plus_path=%r" % (sp, T.get("plus_path")))

    facts = dict(plus_rows=len(plus_rows), M=M, E=E,
                 merged_present=(M > 0 and E > 0 and M == E),
                 set_equal=(P == S), tiers={str(k): v for k, v in tc.items()},
                 recomputed=rec, plus_path=T.get("plus_path"), plus_match=T.get("plus_match"))
    return out, facts


def naive_evaluate_tier(doc):
    """只用 .get() 计数 + Σ==bindings 的『弱 INV-05』（用于实证『缺键被吞进 None 桶』）。"""
    R = doc.get("results", [])
    T = doc.get("totals", {})
    rows = [b for r in R for b in r.get("plus", {}).get("bindings", [])]
    tc = Counter(b.get("tier") for b in rows)
    bad = []
    if sum(tc.values()) != T.get("bindings", 0) or len(rows) != T.get("bindings", 0):
        bad.append("WEAK-INV-05 sum=%d != bindings=%r" % (sum(tc.values()), T.get("bindings")))
    return bad, dict(tiers={str(k): v for k, v in tc.items()}, sum=sum(tc.values()))
