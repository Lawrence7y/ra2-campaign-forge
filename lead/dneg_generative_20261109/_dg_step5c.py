# -*- coding: utf-8 -*-
r"""_dg_step5c.py — 第五步(c)：项目内其它「语言构式被枚举化」的正则清单（只读扫描）。
判据：re.compile(...) 的字面串中含 ≥4 个中文选择支（| 分隔且支内是汉字/词组），
且语义上是「语言构式/词表」而非文件路径/字段名/代码 token。输出只落本写域。"""
import re, json, hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge/lead")
rows = []
for p in sorted(ROOT.rglob("*.py")):
    try:
        t = p.read_text("utf-8", errors="ignore")
    except Exception:
        continue
    for i, line in enumerate(t.splitlines(), 1):
        if "re.compile" not in line and "re.findall" not in line:
            continue
        # 抓一段足够长的字面串（跨行则略，只报单行，注明限制）
        for m in re.finditer(r"[rRuUbBfF]*([\"'])(.{20,400}?)\1", line):
            s = m.group(2)
            parts = [x.strip() for x in s.split("|") if x.strip()]
            zh = [x for x in parts if re.search(r"[\u4e00-\u9fff]", x)]
            if len(zh) >= 4:
                rows.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"),
                             "line": i, "n_zh_alternatives": len(zh),
                             "sample": " | ".join(zh[:6]),
                             "raw": line.strip()[:180]})

# 去重（同文件同行只留一条），按选择支数排序
seen, uniq = set(), []
for r in rows:
    k = (r["file"], r["line"])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)
uniq.sort(key=lambda x: -x["n_zh_alternatives"])
print("=== 语言构式枚举化候选（≥4 中文选择支，n=%d）===" % len(uniq))
for r in uniq[:40]:
    print("  %3d %s:%d  %s" % (r["n_zh_alternatives"], r["file"], r["line"], r["sample"][:90]))

# 点名几处与「否定/完成断言」直接相关的（人工核对行号）
FOCUS = [
    "gate_fp7_20261108/_g7_predicates.py",
    "gate_n13_20261109/_n13_pasteable.py",
    "gate_v1v2_20261109/_v12_rule.py",
    "h5_governance_20261109/_h5_pasteable.py",
    "gate_r9sem_20261109/_r9s_predicates.py",
    "re_line_20261105/W7_W4_REVIEW/_w7_c.py",
]
print("\n=== 与否定/完成断言直接相关的既有枚举（人工核对）===")
for f in FOCUS:
    p = ROOT / f
    if not p.is_file():
        print("  MISSING", f)
        continue
    lines = p.read_text("utf-8", errors="ignore").splitlines()
    for i, l in enumerate(lines, 1):
        if "re.compile" in l and l.count("|") >= 4:
            print("  %s:%d  %s" % (f, i, l.strip()[:150]))

out = {"candidates": uniq, "n": len(uniq), "focus_files": FOCUS}
(Path("D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109") /
 "_dg_step5c_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dg_step5c_out.json")
