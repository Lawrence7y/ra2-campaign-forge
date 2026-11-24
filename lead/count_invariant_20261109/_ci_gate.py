# -*- coding: utf-8 -*-
"""_ci_gate.py — 可粘贴回归门槛的独立可跑封装（只读；零真机；零采样代码）。

用法：
  python -I -X utf8 D:/.../lead/count_invariant_20261109/_ci_gate.py <json> [--expect-merged]
  python -I -X utf8 D:/.../lead/count_invariant_20261109/_ci_gate.py --selftest

selftest 跑三类输入：现盘基线（期望全过）、CE-08 对称错值（期望 INV-08 报警）、
非 merged 的 plus_match>plus_path（期望 INV-07 报警）。全部落临时目录。
"""
import copy
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
BASE = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_compare_out.json"


def gate(json_doc, expect_merged=False):
    T, R = json_doc.get("totals", {}), json_doc.get("results", [])
    v = []
    rows = [(i, k, b) for i, r in enumerate(R)
            for k, b in enumerate(r.get("plus", {}).get("bindings", []))]
    # (1) totals 必须从 results[] 独立重算  —— INV-01
    rec = dict(bindings=0, orig_path=0, plus_path=0, orig_match=0,
               plus_match=0, orig_problems=0, plus_problems=0)
    for r in R:
        ob, nb = r["orig"]["bindings"], r["plus"]["bindings"]
        rec["bindings"] += len(ob)                                        # :65
        rec["orig_path"] += sum(1 for b in ob if b["path"])              # :66
        rec["plus_path"] += sum(1 for b in nb if b.get("path"))          # :67
        rec["orig_match"] += sum(1 for b in ob if b["match"] is True)     # :68
        rec["plus_match"] += sum(1 for b in nb if b.get("match") is True) # :69
        rec["orig_problems"] += len(r["orig"]["problems"])                # :70
        rec["plus_problems"] += len(r["plus"]["problems"])                # :71
    for k in rec:
        if T.get(k) != rec[k]:
            v.append("INV-01 totals.%s=%r != recomputed=%r" % (k, T.get(k), rec[k]))
    # (2) 上界 / 单调 / 非负  —— INV-02/03/04
    for k in ("orig_path", "plus_path", "orig_match", "plus_match"):
        if not (0 <= T.get(k, -1) <= T.get("bindings", 0)):
            v.append("INV-02 %s out of [0,bindings]" % k)
    if T.get("orig_path", 0) > T.get("plus_path", 0) or \
       T.get("orig_match", 0) > T.get("plus_match", 0):
        v.append("INV-03 coverage not monotone")
    if any(T.get(k, -1) < 0 for k in ("orig_problems", "plus_problems")):
        v.append("INV-04 negative problems")
    # (3) tier 完备 + 显式键存在  —— INV-05
    tiers = Counter("<ABSENT>" if "tier" not in b else b.get("tier") for _, _, b in rows)
    if sum(tiers.values()) != T.get("bindings") or tiers.get("<ABSENT>"):
        v.append("INV-05 tier partition incomplete %r" % dict(tiers))
    # (4) merged 判别：正交维度  —— INV-07
    M = sum(1 for _, _, b in rows if not b.get("path") and b.get("match") is True)
    E = sum(1 for _, _, b in rows if b.get("tier") == "SAMEDOC_LINK_EQ")
    if M != E:
        v.append("INV-07 M=%d != E=%d (non-merged cause OR missing merged dimension)" % (M, E))
    merged_present = (M > 0 and E > 0 and M == E)
    if merged_present != expect_merged:
        v.append("INV-07 merged_present=%r != expected=%r" % (merged_present, expect_merged))
    # (5) ★ 集合级：防「数字相等掩盖集合不等」  —— INV-08
    P = {(i, k) for i, k, b in rows if bool(b.get("path"))}
    S = {(i, k) for i, k, b in rows if b.get("match") is True}
    if T.get("plus_path") == T.get("plus_match") and P != S:
        v.append("INV-08 numeric equal but SET differs: %r / %r" % (sorted(P - S), sorted(S - P)))
    # (6) 条件化恒等  —— INV-06 重定义
    if expect_merged:
        if T.get("plus_match", 0) - T.get("plus_path", 0) != E:
            v.append("INV-06 plus_match-plus_path != merged_eq=%d" % E)
    elif T.get("plus_path") != T.get("plus_match"):
        v.append("INV-06 baseline identity broken without merged")
    # (7) 改口径后新维度  —— INV-09
    if json_doc.get("schema_version", T.get("schema_version", 1)) >= 2:
        k = T.get("plus_match_by_kind")
        if not k or k.get("single_path") != T.get("plus_path") or \
           k.get("single_path", 0) + k.get("merged_eq", 0) != T.get("plus_match"):
            v.append("INV-09 by_kind inconsistent with totals")
    return v


def selftest():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="_ci_gate_"))
    print("TEMP:", tmp)
    cases = []

    d0 = copy.deepcopy(base)
    p0 = tmp / "baseline.json"
    p0.write_text(json.dumps(d0, ensure_ascii=False), encoding="utf-8")
    v0 = gate(d0, expect_merged=False)
    cases.append(("baseline expect_merged=False", p0, v0, 0))

    # CE-08 对称错值：7 键全等但集合不同 ⇒ 必须报警
    d1 = copy.deepcopy(base)
    rows = [(i, k) for i, r in enumerate(d1["results"])
            for k, b in enumerate(r["plus"]["bindings"])]
    pr = [(i, k) for i, k in rows if d1["results"][i]["plus"]["bindings"][k].get("path")]
    nr = [(i, k) for i, k in rows if not d1["results"][i]["plus"]["bindings"][k].get("path")]
    d1["results"][pr[0][0]]["plus"]["bindings"][pr[0][1]]["match"] = False
    d1["results"][nr[0][0]]["plus"]["bindings"][nr[0][1]]["match"] = True
    p1 = tmp / "symmetric_drift.json"
    p1.write_text(json.dumps(d1, ensure_ascii=False), encoding="utf-8")
    v1 = gate(d1, expect_merged=False)
    cases.append(("CE-08 symmetric drift", p1, v1, "INV-08"))

    # 非 merged 的 plus_match>plus_path ⇒ 必须报警 INV-07
    d2 = copy.deepcopy(base)
    for r in d2["results"]:
        for b in r["plus"]["bindings"]:
            if b.get("path") is None and b.get("match") is None:
                b["match"] = True
                break
        else:
            continue
        break
    d2["totals"]["plus_match"] = 10
    p2 = tmp / "nonmerged_cause.json"
    p2.write_text(json.dumps(d2, ensure_ascii=False), encoding="utf-8")
    v2 = gate(d2, expect_merged=False)
    cases.append(("non-merged plus_match>plus_path", p2, v2, "INV-07"))

    ok = True
    for name, p, v, expect in cases:
        if expect == 0:
            passed = (len(v) == 0)
            print("[%s] %s alerts=%d expected=0 temp=%s" %
                  ("PASS" if passed else "FAIL", name, len(v), p.name))
        else:
            passed = any(x.startswith(expect) for x in v)
            print("[%s] %s alerts=%d expected=%s temp=%s" %
                  ("PASS" if passed else "FAIL", name, len(v), expect, p.name))
        for x in v:
            print("      ", x)
        ok = ok and passed
    print("SELFTEST_ALL_PASS =", ok)
    return 0 if ok else 1


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        return selftest()
    if len(sys.argv) not in (2, 3):
        print("usage: _ci_gate.py <json> [--expect-merged] | --selftest")
        return 2
    doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    em = len(sys.argv) == 3 and sys.argv[2] == "--expect-merged"
    v = gate(doc, expect_merged=em)
    print("FILE:", sys.argv[1], " expect_merged =", em)
    for x in v:
        print("  -", x)
    print(("ALERT violations=%d" % len(v)) if v else "OK violations=0")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
