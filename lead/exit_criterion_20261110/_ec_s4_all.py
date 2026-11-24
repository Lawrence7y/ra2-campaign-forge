# -*- coding: utf-8 -*-
"""_ec_s4_all.py — 第四步：263 件 NO_EXIT_AT_ALL 全量三分类 + 与普查 cls 交叉核对。
读 lead/const_exit_20261109/_ce_final_out.json（只读）取名单；对每件跑 _ec_criterion。
输出 _ec_s4_results.json + 控制台汇总。不改任何被检脚本。
"""
import collections
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

spec = importlib.util.spec_from_file_location(
    "_ec_criterion", os.path.join(HERE, "_ec_criterion.py"))
EC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EC)

CENSUS = os.path.join(ROOT, "lead", "const_exit_20261109", "_ce_final_out.json")


def main():
    with open(CENSUS, encoding="utf-8") as f:
        census = json.load(f)
    rows = census["rows"]
    print("census rows = %d ; final_classes = %s" % (len(rows), census["final_classes"]))
    no_exit = [r["rel"] for r in rows if r["cls"] == "NO_EXIT_AT_ALL"]
    print("NO_EXIT_AT_ALL = %d" % len(no_exit))

    results = []
    my_exit_disagree = []
    for rel in no_exit:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            r = EC.analyze_file(p, rel)
        except Exception as e:  # 判据自身异常 → 显式 UNKNOWN，不许静默
            r = {"rel": rel, "class": "UNKNOWN", "verdict": "NEEDS_FIX",
                 "e": {}, "reasons": [("RUNNER", rel, "判据运行异常 %r → 需人工" % (e,))],
                 "facts": {}}
        results.append(r)
        if r["facts"].get("n_exit", 0) > 0:
            my_exit_disagree.append((rel, r["facts"]["exit_lines"]))

    cls_cnt = collections.Counter(r["class"] for r in results)
    verdict_cnt = collections.Counter(r["verdict"] for r in results)
    print("\n== 263 件三分类 ==")
    for k, v in cls_cnt.most_common():
        print("  %-9s %d" % (k, v))
    print("== verdict 分布 ==")
    for k, v in verdict_cnt.most_common():
        print("  %-15s %d" % (k, v))

    print("\n== 我的显式出口检测与普查 NO_EXIT 判定的分歧（应为 0）==")
    print("  分歧数 =", len(my_exit_disagree))
    for rel, lines in my_exit_disagree[:10]:
        print("    %s exits@%s" % (rel, lines))

    print("\n== 代表件 ==")
    by_cls = collections.defaultdict(list)
    for r in results:
        by_cls[r["class"]].append(r)
    for cls in ("GATE", "ARTIFACT", "PROBE", "UNKNOWN"):
        lst = by_cls.get(cls, [])
        print("  [%s] %d 件，代表前 5：" % (cls, len(lst)))
        for r in lst[:5]:
            first = r["reasons"][0] if r["reasons"] else ("?", r["rel"], "?")
            print("    %-13s %s  | %s %s" % (r["verdict"], r["rel"], first[0], str(first[2])[:90]))

    print("\n== GATE 类全名单（NEEDS_FIX 明细）==")
    for r in by_cls.get("GATE", []):
        codes = sorted({x[0] for x in r["reasons"]})
        print("  %-11s %s  %s" % (r["verdict"], r["rel"], ",".join(codes)))

    print("\n== UNKNOWN 类全名单 ==")
    for r in by_cls.get("UNKNOWN", []):
        print("  %s" % r["rel"])

    out = os.path.join(HERE, "_ec_s4_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"n_no_exit": len(no_exit),
                   "cls_counts": dict(cls_cnt),
                   "verdict_counts": dict(verdict_cnt),
                   "exit_disagree": my_exit_disagree,
                   "results": results}, f, ensure_ascii=False, indent=1)
    print("\n结果已写 %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
