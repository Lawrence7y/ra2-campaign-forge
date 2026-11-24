# -*- coding: utf-8 -*-
r"""_rj_taskbook.py — 导出 13 个问题域任务书中「必现要素/禁词/绑定行/交付」原句（只读）。"""
import json
import glob
import os
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_rejudge32_20261109"
base = json.loads((ROOT / "lead/gate_doc_name_fix_20261109/_dn_regate_out.json").read_text(encoding="utf-8"))
runs = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}

out = {}
for r in base["rows"]:
    if not r["gateProblems"]:
        continue
    dom = r["domain"].rstrip("/").split("/")[-1]
    p = runs.get(r["run"])
    if not p:
        continue
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    v, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
    low = v.get("lowered", "")
    keep = [ln for ln in low.split("\n")
            if any(k in ln for k in ("必现要素", "【交付】", "不得出现", "绑定行", "回件必须",
                                     "缺要素", "含越界断言", "含既成事实", "复核回件必须"))]
    out[dom] = {"run": r["run"], "gateProblems": r["gateProblems"], "lines": keep}
(WDIR / "_rj_taskbook_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for dom, x in out.items():
    print("\n============", dom, "============")
    print("problems:", x["gateProblems"])
    for ln in x["lines"]:
        print("   ", ln.strip()[:500])
