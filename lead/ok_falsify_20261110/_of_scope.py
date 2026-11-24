# -*- coding: utf-8 -*-
"""_of_scope.py — 只读扩面普查：对普查全名单 413 件逐件跑出口判据。

输入（全部只读）：
  lead/const_exit_20261109/_ce_final_out.json      rows -> 名单 + census_cls
  lead/exit_criterion_20261110/_ec_s4_results.json results -> 已交付子集 (rel)
  lead/exit_criterion_20261110/_ec_criterion.py    analyze_file(abs_path, rel)
输出（唯一写入）：
  lead/ok_falsify_20261110/_of_scope_out.json
控制台：两张计数表（含三维分组完整表）。不修改任何被检脚本。
"""
import collections
import importlib.util
import json
import os
import sys

# 禁止导入判据模块时落 __pycache__（本脚本唯一允许写入的文件只有输出 JSON）
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

CENSUS_JSON = os.path.join(ROOT, "lead", "const_exit_20261109", "_ce_final_out.json")
SUBSET_JSON = os.path.join(ROOT, "lead", "exit_criterion_20261110", "_ec_s4_results.json")
CRITERION_PY = os.path.join(ROOT, "lead", "exit_criterion_20261110", "_ec_criterion.py")
OUT_JSON = os.path.join(HERE, "_of_scope_out.json")

REL_CENSUS = "lead/const_exit_20261109/_ce_final_out.json"
REL_SUBSET = "lead/exit_criterion_20261110/_ec_s4_results.json"
REL_CRITERION = "lead/exit_criterion_20261110/_ec_criterion.py"


def load_criterion():
    spec = importlib.util.spec_from_file_location("_of_ec_criterion", CRITERION_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def failed_items(e):
    """把 e 字典里值为 FAIL/UNKNOWN 的键拼成 E3=FAIL,E4=FAIL；全 PASS 返回空串。"""
    if not isinstance(e, dict):
        return ""
    return ",".join("%s=%s" % (k, e[k]) for k in sorted(e)
                    if e[k] in ("FAIL", "UNKNOWN"))


def table_lines(rows):
    by_cv = collections.Counter((r["crit_cls"], r["crit_verdict"]) for r in rows)
    by_3 = collections.Counter((r["census_cls"], r["crit_cls"], r["crit_verdict"])
                                for r in rows)
    cv_order = sorted({k[0] for k in by_cv})
    v_order = sorted({k[1] for k in by_cv})
    c_order = sorted({r["census_cls"] for r in rows})

    lines = []
    lines.append("== 表1：按 (crit_cls, crit_verdict) 分组计数 ==")
    lines.append("%-18s %-18s %8s" % ("crit_cls", "crit_verdict", "n"))
    for cc in cv_order:
        for vv in v_order:
            if (cc, vv) in by_cv:
                lines.append("%-18s %-18s %8d" % (cc, vv, by_cv[(cc, vv)]))
    lines.append("%-18s %-18s %8d" % ("TOTAL", "", len(rows)))
    lines.append("")
    lines.append("== 表2：按 (census_cls, crit_cls, crit_verdict) 三维分组完整计数表 ==")
    lines.append("%-18s %-18s %-18s %8s" %
                 ("census_cls", "crit_cls", "crit_verdict", "n"))
    # 全组合输出（含 0 计数组合），按字典序；末尾附各 census_cls 小计与总计
    combos = {(cc, vv) for cc in cv_order for vv in v_order}
    for census_cls in c_order:
        subtotal = 0
        for cc, vv in sorted(combos):
            n = by_3.get((census_cls, cc, vv), 0)
            subtotal += n
            lines.append("%-18s %-18s %-18s %8d" % (census_cls, cc, vv, n))
        lines.append("%-18s %-18s %-18s %8d" %
                     (census_cls, "[SUBTOTAL]", "", subtotal))
    lines.append("%-18s %-18s %-18s %8d" % ("TOTAL", "", "", len(rows)))

    cv_list = [{"crit_cls": k[0], "crit_verdict": k[1], "n": v}
               for k, v in sorted(by_cv.items())]
    tri_list = [{"census_cls": k[0], "crit_cls": k[1], "crit_verdict": k[2], "n": v}
                for k, v in sorted(by_3.items())]
    return lines, cv_list, tri_list


def main():
    with open(CENSUS_JSON, encoding="utf-8") as f:
        census_rows = json.load(f)["rows"]
    with open(SUBSET_JSON, encoding="utf-8") as f:
        subset_results = json.load(f)["results"]
    delivered = {r["rel"] for r in subset_results}
    ec = load_criterion()

    print("census rows = %d" % len(census_rows))
    print("delivered subset results = %d ; unique rel = %d" %
          (len(subset_results), len(delivered)))
    if len(subset_results) != 263 or len(delivered) != 263:
        print("WARN：已交付子集条数不是 263（按实际条数标记，不做补齐）")
    print("criterion = %s ; analyze_file = %r" %
          (REL_CRITERION, getattr(ec, "analyze_file", None)))

    rows = []
    n_raised = 0
    for cr in census_rows:
        rel = cr["rel"]
        abs_path = os.path.join(ROOT, rel.replace("/", os.sep))
        item = {
            "rel": rel,
            "census_cls": cr["cls"],
            "crit_cls": None,
            "crit_verdict": None,
            "failed_items": "",
            "in_delivered_subset": rel in delivered,
        }
        try:
            r = ec.analyze_file(abs_path, rel)
            item["crit_cls"] = r["class"]
            item["crit_verdict"] = r["verdict"]
            item["failed_items"] = failed_items(r.get("e"))
        except Exception as exc:
            # 判据抛异常：如实登记，不跳过、不猜测分类
            n_raised += 1
            item["crit_cls"] = "ANALYZER_RAISED"
            item["crit_verdict"] = "ANALYZER_RAISED"
            item["failed_items"] = ""
            item["exception_type"] = type(exc).__name__
            item["exception_message"] = str(exc)[:500]
        rows.append(item)

    lines, cv_list, tri_list = table_lines(rows)
    text = "\n".join(lines)
    print("")
    print(text)
    print("")
    print("ANALYZER_RAISED = %d" % n_raised)
    for r in rows:
        if r["crit_cls"] == "ANALYZER_RAISED":
            print("  RAISED %-18s %s" % (r["exception_type"], r["rel"]))
    print("TOTAL = %d" % len(rows))

    out = {
        "n": len(rows),
        "n_delivered_subset_results": len(subset_results),
        "n_delivered_subset_unique": len(delivered),
        "n_analyzer_raised": n_raised,
        "sources": {"census": REL_CENSUS,
                    "delivered_subset": REL_SUBSET,
                    "criterion": REL_CRITERION},
        "rows": rows,
        "summary": {
            "n": len(rows),
            "by_crit_cls_verdict": cv_list,
            "by_census_crit_verdict": tri_list,
            "three_way_table_text": text,
        },
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("written: %s" % OUT_JSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
