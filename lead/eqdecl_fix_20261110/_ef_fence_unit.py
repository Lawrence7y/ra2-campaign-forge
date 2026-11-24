# -*- coding: utf-8 -*-
"""
_ef_fence_unit.py — 修版 (a) 围栏状态机单测（合成文本，不触碰被检文档）。
覆盖：闭合围栏 / 未闭合兜底 / ~~~ 围栏 / 带信息串开行 / 加长闭行 / scan_file 全链路
（围栏内裸等式 → SKIP·K7·CODE；同一裸等式在围栏外 → FAIL·F1 正控）。
运行： python -I -X utf8 <本文件>
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil

HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_fix_20261110")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
_spec = importlib.util.spec_from_file_location("_ef_detector", HERE / "_ef_detector.py")
eq = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(eq)

TMP = HERE / "_ef_fence_unit_tmp"
TMP.mkdir(exist_ok=True)

CASES_SYNTH = {
    "closed": {
        "lines": ["前言。\n", "```\n", "chain_changed=18 | 集合恒等? True\n", "```\n", "后记。\n"],
        "expect_inside": {3},
        "expect_ranges": [[2, 4]],
    },
    "unclosed_eof": {
        "lines": ["前言。\n", "```python\n", "x = 集合恒等? True\n", "y = 2\n"],
        "expect_inside": {3, 4},
        "expect_ranges": [[2, None]],
    },
    "tilde": {
        "lines": ["a\n", "~~~\n", "集合恒等? True\n", "~~~\n", "b\n"],
        "expect_inside": {3},
        "expect_ranges": [[2, 4]],
    },
    "longer_close": {
        "lines": ["a\n", "```\n", "x 集合恒等? True\n", "`````\n", "b\n"],
        "expect_inside": {3},
        "expect_ranges": [[2, 4]],
    },
    "info_string_open": {
        "lines": ["a\n", "```text 输出\n", "集合恒等? True\n", "```\n", "b\n"],
        "expect_inside": {3},
        "expect_ranges": [[2, 4]],
    },
    "shorter_close_not_close": {
        # 开行 4 反引号，闭行只有 3 个 ⇒ 不闭，兜底到文件尾
        "lines": ["a\n", "````\n", "x 集合恒等? True\n", "```\n", "y 集合恒等? True\n"],
        "expect_inside": {3, 4, 5},
        "expect_ranges": [[2, None]],
    },
}

CASES_SCAN = {
    "in_fence_bare_eq": {
        "text": "说明：以下是上一任务实跑输出。\n```\nchain_changed=18 | unresolved_changed=18 | 集合恒等? True\n```\n",
        "expect_line": 3, "expect_verdict": "SKIP", "expect_ftype": None,
        "expect_skip": "K7_code_fence_interior", "expect_cat": "CODE",
    },
    "outside_fence_bare_eq_ctrl": {
        "text": "说明行。\nchain_changed=18 | unresolved_changed=18 | 集合恒等? True\n尾行。\n",
        "expect_line": 2, "expect_verdict": "FAIL", "expect_ftype": "F1",
        "expect_skip": None, "expect_cat": "SUBSTANTIVE",
    },
}


def main() -> int:
    rows = []
    ok_all = True
    for cid, c in CASES_SYNTH.items():
        inside, ranges = eq.code_fence_lines(c["lines"])
        ok = (inside == c["expect_inside"] and
              [[a, b] for a, b in ranges] == c["expect_ranges"])
        ok_all = ok_all and ok
        rows.append({"case": cid, "inside": sorted(inside),
                     "ranges": [list(r) for r in ranges],
                     "expect_inside": sorted(c["expect_inside"]),
                     "expect_ranges": c["expect_ranges"], "passed": ok})
    for cid, c in CASES_SCAN.items():
        p = TMP / f"_unit_{cid}.md"
        p.write_text(c["text"], encoding="utf-8")
        rec = eq.scan_file(p)
        hit = None
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            hit = next((x for x in rec[bucket] if x["line"] == c["expect_line"]), None)
            if hit:
                break
        ok = (hit is not None and hit["verdict"] == c["expect_verdict"] and
              hit["failure_type"] == c["expect_ftype"] and
              hit.get("skip_reason") == c["expect_skip"] and
              hit["category"] == c["expect_cat"])
        ok_all = ok_all and ok
        rows.append({"case": cid, "verdict": hit["verdict"] if hit else None,
                     "failure_type": hit["failure_type"] if hit else None,
                     "category": hit["category"] if hit else None,
                     "skip_reason": hit.get("skip_reason") if hit else None,
                     "expect": [c["expect_verdict"], c["expect_ftype"],
                                c["expect_skip"], c["expect_cat"]],
                     "passed": ok,
                     "n_code_fence_lines": rec.get("n_code_fence_lines")})
    shutil.rmtree(TMP, ignore_errors=True)
    out = {"n_cases": len(rows), "n_passed": sum(1 for r in rows if r["passed"]),
           "n_failed": sum(1 for r in rows if not r["passed"]), "cases": rows,
           "ALL_PASS": ok_all}
    (HERE / "_ef_fence_unit_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(("PASS " if r["passed"] else "FAIL "), r["case"],
              {k: v for k, v in r.items() if k not in ("case", "passed")})
    print("ALL_PASS =", ok_all)
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
