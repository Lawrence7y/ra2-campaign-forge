# -*- coding: utf-8 -*-
"""_ci_checks.py — _f2_compare_out.json 的计数不变量回归器（只读；零真机；零采样代码）。

用法：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/count_invariant_20261109/_ci_checks.py <path-to-json>

设计要点（本次核心风险）：
  * 每条 INV 都写成「等式/不等式」，从 results[] 独立重算，绝不把 totals 当权威。
  * INV-01/02/03/05/06/08 检测「计数一致性 / 维度缺失」；
    INV-04/09 检测「problems 非负 / verdict 与 problems 一致」；
    INV-07 是 merged 判别式（当前盘应当为 False，插入 merged 必须变 True）。
  * 返回 (violations, facts)：violations 非空 => 报警；exit code 1。
  * 不 import 任何项目内模块；不写盘；不触碰只读域。
"""
import json
import sys
from collections import Counter
from pathlib import Path

# 现盘允许的 tier 取值（本会话实读 _f2_compare_out.json 得 T1/T2/T2N/T3/None）
ALLOWED_TIERS = {"T1", "T2", "T2N", "T3", None}
MERGED_TIER = "SAMEDOC_LINK_EQ"
UNIQUE_TIER = "SAMEDOC_LINK"


def evaluate(doc):
    """doc = json.loads(...); 返回 (violations:list[str], facts:dict)"""
    v = []
    T = doc.get("totals", {})
    R = doc.get("results", [])
    if not isinstance(R, list):
        return ["FATAL results_not_list"], {"n_results": 0}

    all_rows = []
    for i, r in enumerate(R):
        for k, b in enumerate(r.get("plus", {}).get("bindings", [])):
            all_rows.append((i, k, b))
        for k, b in enumerate(r.get("orig", {}).get("bindings", [])):
            all_rows.append(("orig", i, k, b))
    plus_rows = [(i, k, b) for i, r in enumerate(R)
                 for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    orig_rows = [b for r in R for b in r.get("orig", {}).get("bindings", [])]

    # ---- 从 results[] 独立重算 7 键（复刻 _f2_compare.py:65-71） ----
    rec = dict(bindings=0, orig_path=0, plus_path=0, orig_match=0,
               plus_match=0, orig_problems=0, plus_problems=0)
    for r in R:
        ob = r.get("orig", {}).get("bindings", [])
        nb = r.get("plus", {}).get("bindings", [])
        rec["bindings"] += len(ob)                                   # :65
        rec["orig_path"] += sum(1 for b in ob if b.get("path"))     # :66
        rec["plus_path"] += sum(1 for b in nb if b.get("path"))     # :67
        rec["orig_match"] += sum(1 for b in ob if b.get("match") is True)  # :68
        rec["plus_match"] += sum(1 for b in nb if b.get("match") is True)  # :69
        rec["orig_problems"] += len(r.get("orig", {}).get("problems", []))  # :70
        rec["plus_problems"] += len(r.get("plus", {}).get("problems", []))  # :71

    # ---- INV-01：totals 七键 == 从 results[] 独立重算（防计数口径漏改/硬编码） ----
    for key in sorted(rec):
        if key not in T:
            v.append("INV-01 missing key totals.%s" % key)
        elif T[key] != rec[key]:
            v.append("INV-01 totals.%s=%r != recomputed=%r" % (key, T[key], rec[key]))

    # ---- INV-02：path / match 计数不超过 bindings ----
    for key in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if key in T and T[key] > T.get("bindings", 0):
            v.append("INV-02 %s=%r > bindings=%r" % (key, T[key], T.get("bindings")))
    if T.get("bindings", 0) != rec["bindings"]:
        v.append("INV-02 totals.bindings=%r != sum(len(orig.bindings))=%r"
                 % (T.get("bindings"), rec["bindings"]))

    # ---- INV-03：orig ≤ plus 覆盖单调（增强版不得丢原版已采 path） ----
    if T.get("orig_path", 0) > T.get("plus_path", 0):
        v.append("INV-03 orig_path=%r > plus_path=%r" % (T.get("orig_path"), T.get("plus_path")))
    if T.get("orig_match", 0) > T.get("plus_match", 0):
        v.append("INV-03 orig_match=%r > plus_match=%r" % (T.get("orig_match"), T.get("plus_match")))

    # ---- INV-04：problems 非负且与 problems[] 长度一致、verdict 与 problems 一致 ----
    for key in ("orig_problems", "plus_problems"):
        if key in T and (not isinstance(T[key], int) or T[key] < 0):
            v.append("INV-04 %s=%r is negative/non-int" % (key, T[key]))
    for r in R:
        for side in ("orig", "plus"):
            s = r.get(side, {})
            np = len(s.get("problems", []))
            if np and s.get("verdict") == "PASS":
                v.append("INV-04 %s.verdict=PASS but problems=%d" % (side, np))
            if np == 0 and s.get("verdict") == "FAIL":
                v.append("INV-04 %s.verdict=FAIL but problems=0" % (side, np))

    # ---- INV-05：tier 完备 = 每条 plus 绑定恰一个 tier，计数和 == bindings ----
    tiers = Counter(("<ABSENT>" if "tier" not in b else b.get("tier"))
                    for _, _, b in plus_rows)
    if len(plus_rows) != T.get("bindings", 0):
        v.append("INV-05 n_plus_rows=%d != bindings=%r" % (len(plus_rows), T.get("bindings")))
    if sum(tiers.values()) != T.get("bindings", 0):
        v.append("INV-05 sum(tier_counts)=%d != bindings=%r" % (sum(tiers.values()), T.get("bindings")))
    # ★ 每条绑定必须显式带 tier 键：缺键会被 .get() 悄悄归进 None 桶而不改变计数和，
    #   这正是「维度缺失被恒等掩盖」的一个实例（见 CE-05 反例）。
    for i, k, b in plus_rows:
        if "tier" not in b:
            v.append("INV-05 binding (%d,%d) missing explicit tier key" % (i, k))
    for t in tiers:
        if t != "<ABSENT>" and t not in ALLOWED_TIERS and t not in (MERGED_TIER, UNIQUE_TIER):
            v.append("INV-05 unknown tier %r" % (t,))
    # 现盘（schema v1）无 merged/unique；这一条是"维度缺失"的探针，不是恒等式：
    # 由 INV-07 / 外部 policy 决定是否允许出现，故此处只报 unknown，不报 merged 存在。

    # ---- INV-06：现盘巧合恒等 plus_path == plus_match（基线锁；merged 后必须改） ----
    # ★ 这不是"应当永远成立"的物理律，而是当前语料的基线快照。
    #   merged 接入后此式必然被打破 → 见 INV-07 与第三步。
    if T.get("plus_path") != T.get("plus_match"):
        v.append("INV-06 plus_path=%r != plus_match=%r (baseline identity broken; "
                 "must reconcile with plus_match_by_kind)" %
                 (T.get("plus_path"), T.get("plus_match")))

    # ---- INV-07：merged 判别式（现盘 False；插入 merged 后 True） ----
    # 定义 M = 无单一 path 却 match=True 的绑定数 = plus_match - (path∧match 数)
    both = sum(1 for _, _, b in plus_rows
               if bool(b.get("path")) and b.get("match") is True)
    match_true = sum(1 for _, _, b in plus_rows if b.get("match") is True)
    path_true = sum(1 for _, _, b in plus_rows if bool(b.get("path")))
    M = match_true - both
    E = sum(1 for _, _, b in plus_rows if b.get("tier") == MERGED_TIER)
    facts = dict(
        n_results=len(R), bindings=T.get("bindings"),
        tiers={("<ABSENT>" if k == "<ABSENT>" else "NONE" if k is None else str(k)): v
               for k, v in tiers.items()},
        plus_path=T.get("plus_path"), plus_match=T.get("plus_match"),
        plus_path_recomputed=rec["plus_path"], plus_match_recomputed=rec["plus_match"],
        path_and_match=both, match_true=match_true, path_true=path_true,
        M_match_no_path=M, E_merged_tier=E,
        merged_present=(M > 0 and E > 0 and M == E),
        recomputed=rec, has_totals_7=all(k in T for k in rec),
    )
    # 判别式本体（见第三步(d)）：
    #   merged_present := (M > 0) ∧ (E > 0) ∧ (M == E)
    #   ∧  (每条 M 行都带 members 且不带单对象三键)
    if M != E:
        v.append("INV-07 M(match_no_path)=%d != E(merged_tier)=%d => non-merged cause "
                 "of plus_match>plus_path OR missing merged dimension" % (M, E))
    for _, _, b in plus_rows:
        if (not b.get("path")) and b.get("match") is True and b.get("tier") == MERGED_TIER:
            if not b.get("members"):
                v.append("INV-07 merged row missing members (纪律三)")
            for k in ("verified_path", "recomputed", "bytes"):
                if k in b:
                    v.append("INV-07 merged row has single-object key %r (纪律一)" % k)

    # ---- INV-08：set 级而非仅数值级（防「数字凑巧相等」掩盖维度缺失） ----
    P = {(i, k) for i, k, b in plus_rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in plus_rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        v.append("INV-08 plus_path==plus_match numerically but SET differs: "
                 "path\\match=%r match\\path=%r" % (sorted(P - S), sorted(S - P)))
    facts["set_equal"] = (P == S)

    # ---- INV-09：新维度存在性（改口径后的强制项；现盘缺维度即报警） ----
    # 只有声明了 schema_version>=2 或 counting_policy 的文件才强制；否则按 v1 放行。
    sv = doc.get("schema_version", T.get("schema_version", 1))
    if isinstance(sv, int) and sv >= 2:
        if "counting_policy" not in doc and "counting_policy" not in T:
            v.append("INV-09 schema_version>=2 but no counting_policy")
        if "plus_match_by_kind" not in T:
            v.append("INV-09 schema_version>=2 but no plus_match_by_kind")
        else:
            k = T["plus_match_by_kind"]
            sp, me = k.get("single_path"), k.get("merged_eq")
            if sp is None or me is None:
                v.append("INV-09 plus_match_by_kind incomplete %r" % (k,))
            else:
                if sp + me != T.get("plus_match"):
                    v.append("INV-09 single_path+merged_eq=%d != plus_match=%r"
                             % (sp + me, T.get("plus_match")))
                if sp != T.get("plus_path"):
                    v.append("INV-09 single_path=%r != plus_path=%r" % (sp, T.get("plus_path")))
    return v, facts


def main():
    if len(sys.argv) != 2:
        print("usage: _ci_checks.py <json>")
        return 2
    p = Path(sys.argv[1])
    doc = json.loads(p.read_text(encoding="utf-8"))
    v, f = evaluate(doc)
    print("FILE:", str(p))
    print("FACTS:", json.dumps(f, ensure_ascii=False, sort_keys=True, default=str))
    if v:
        print("ALERT violations=%d" % len(v))
        for x in v:
            print("  -", x)
        return 1
    print("OK violations=0 (all invariants hold)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
