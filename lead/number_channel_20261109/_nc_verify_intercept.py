# -*- coding: utf-8 -*-
"""(d) 逐条核更正记录 + 全归档 #11/#15/#17 字面断言 census。
只读；用法: python -I -X utf8 <绝对路径>
"""
import io
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"

# 审计件 §4.2 列的严格口径 9 条逐条更正件（claim_id -> [(文件, 行区间, 应含关键词)])
STRICT = {
    1: ("lead/stale_pass_20261109/STALE_PASS_INVENTORY.md", [(65, 72, ["4 行", "117"]),
                                                            (103, 110, ["4 行", "7 处"])]),
    2: ("lead/stale_pass_20261109/STALE_PASS_INVENTORY.md", [(55, 60, ["3 行", "纠正"]),
                                                            (65, 70, ["4 行"]),
                                                            (103, 110, ["7 处", "4 行"])]),
    3: ("lead/keff_calc_20261109/KEFF_CALC.md", [(100, 115, ["0.037475", "fp_rate", "口径错置"]),
                                               (100, 107, ["0.037475", "两层"])]),
    4: ("lead/keff_calc_20261109/KEFF_CALC.md", [(100, 115, ["两层", "0.033631"])]),
    5: ("lead/keff_calc_20261109/KEFF_CALC.md", [(104, 112, ["似然", "后验"]),
                                               (254, 259, ["2.0526", "1.877"])]),
    6: ("lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md", [(144, 150, ["GP-A1", "CATCH", "PASS"])]),
    7: ("lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md", [(135, 140, ["误报", "R10"])]),
    8: ("lead/gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md", [(388, 406, ["2 条", "不判"])]),
    12: ("lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md", [(48, 57, ["13 域", "6 域", "10 域", "5 域"])]),
    13: ("lead/minhard_check_20261109/MINHARD_SET_CHECK.md", [(170, 185, ["不成立", "2 件", "6 件"])]),
    14: ("lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md", [(76, 90, ["find = -1", "find = 172", "纠正"])]),
    18: ("lead/score_decomp_20261109/_sd_report.md", [(215, 221, ["0 分", "18 分"])]),
}

# 注意：审计件 §4.2 说「9 条逐条更正件」，但上面枚举了 12 个 id（1,2,3,4,5,6,7,8,12,13,14,18）。
# 这是审计件自认「条号与 9 条口径的精确一一对应本会话未逐条重枚举，标未验」的地方。


def lines_of(rel):
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)), "r", encoding="utf-8") as f:
        return f.read().split("\n")


res = {"strict_records": {}}
for cid, (rel, windows) in STRICT.items():
    L = lines_of(rel)
    checks = []
    for a, b, keys in windows:
        seg = "\n".join(L[a - 1: min(b, len(L))])
        checks.append({"lines": "%d-%d" % (a, b),
                       "keys": keys,
                       "hit": {k: (k in seg) for k in keys},
                       "all_hit": all(k in seg for k in keys)})
    res["strict_records"][str(cid)] = {
        "file": rel, "checks": checks,
        "pass": all(c["all_hit"] for c in checks),
    }

res["n_strict_ids_enumerated_in_audit_4_2"] = len(STRICT)
res["n_strict_pass"] = sum(1 for v in res["strict_records"].values() if v["pass"])

# ---- 全归档 .mjs census：#11/#15/#17 的字面断言短语 ----
PHRASES = {
    "11": ["挑错中稿", "挑错文件", "n4_yi_final 是门禁挑错"],
    "15": ["SELF_TEST=FAIL 是脚本缺陷", "脚本缺陷"],
    "17": ["修好就能插", "H5 修好就能插生产门禁", "修好后仍有 4 项缺陷"],
}
archive_dir = os.path.join(ROOT, ".zcode", "workflow-runs")
files = sorted(f for f in os.listdir(archive_dir)
               if f.startswith("dwfrun-") and f.endswith(".mjs"))
res["n_archived_mjs_in_main_archive"] = len(files)
census = {}
for cid, ph in PHRASES.items():
    hits = []
    for fn in files:
        p = os.path.join(archive_dir, fn)
        try:
            txt = io.open(p, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for i, line in enumerate(txt.split("\n")):
            for q in ph:
                if q in line:
                    hits.append({"file": fn, "line": i + 1, "phrase": q,
                                 "context": line.strip()[:180]})
                    break
    census[cid] = {"n_hits": len(hits), "hits": hits[:20]}
res["literal_phrase_census"] = census

print(json.dumps(res, ensure_ascii=False, indent=2))
