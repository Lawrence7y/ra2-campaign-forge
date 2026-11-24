# -*- coding: utf-8 -*-
r"""_rj_r9r11_check.py — 对 13 个问题域逐项跑 R9 要素归一 / R11 绑定回验（只读）。
输出：lead/gate_rejudge32_20261109/_rj_r9r11_out.json + 控制台摘要。
"""
import hashlib
import importlib.util
import json
import re
import ast
import glob
import os
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_rejudge32_20261109"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
raw = PRED.read_bytes()
assert hashlib.sha256(raw).hexdigest() == "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
spec = importlib.util.spec_from_file_location("_rj_g7p2", PRED)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

base = json.loads((ROOT / "lead/gate_doc_name_fix_20261109/_dn_regate_out.json").read_text(encoding="utf-8"))
runs = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}

def gate_src(low):
    k = low.find("const GATE_CODE = [")
    end = low.find("].join", k)
    body = low[k + len("const GATE_CODE = ["):end]
    lit = re.compile(r'"((?:[^"\\]|\\.)*)"')
    parts = []
    for m in lit.finditer(body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts) if parts else None

LOOP_RE = re.compile(r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)")
BRE = re.compile(r"(?:B=\s*(?:len\()?)re\.findall\((r'[^']*'|r\"[^\"]*\")")

out = []
for r in base["rows"]:
    if not r["gateProblems"]:
        continue
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    text = mp.read_text(encoding="utf-8", errors="replace")
    p = runs.get(r["run"])
    low = ""
    elems = []
    if p:
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        i = t.find("export const payload = ")
        v, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
        low = v.get("lowered", "")
        src = gate_src(low) or ""
        for m in LOOP_RE.finditer(src):
            try:
                elems += ast.literal_eval(m.group(2))
            except Exception:
                pass
    # 真实 B= 绑定正则
    src = gate_src(low) or ""
    mb = BRE.search(src)
    real_bpat = mb.group(1)[2:-1] if mb else None
    real_bcount = len(re.findall(real_bpat, text, re.M)) if real_bpat else None
    # R11
    r11p, r11w, binds = g7.r11_scan(text, mp.parent, root=ROOT)
    rec = {"domain": dom, "main": r["main"],
           "gateProblems": r["gateProblems"],
           "baseline_bindings": r["bindings"],
           "baseline_bindingRegex": r["params"]["bindingRegex"],
           "real_B_regex": real_bpat, "real_B_count": real_bcount,
           "r11": {"problems": r11p, "warnings": r11w,
                   "bindings": [dict(b) for b in binds]},
           "r9": []}
    for k in elems:
        raw_present, _ = g7.r9_element_present(text, k)
        rec["r9"].append({"token": k, "raw_literal": k in text,
                          "r9_present": raw_present})
    out.append(rec)

(WDIR / "_rj_r9r11_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for rec in out:
    print("\n====", rec["domain"], "====")
    print("  gateProblems:", rec["gateProblems"])
    print("  baseline bindings=%s (regex=%r)" % (rec["baseline_bindings"], rec["baseline_bindingRegex"]))
    print("  REAL B regex=%r  -> count=%s" % (rec["real_B_regex"], rec["real_B_count"]))
    print("  R11 problems=%s warnings=%s bindings=%d" % (
        rec["r11"]["problems"], rec["r11"]["warnings"], len(rec["r11"]["bindings"])))
    for b in rec["r11"]["bindings"]:
        print("      bind:", {k: b[k] for k in ("declared", "path", "match", "bytes") if k in b})
    for e in rec["r9"]:
        if not e["raw_literal"]:
            print("  R9 elem %-30r raw=%s r9_present=%s" % (e["token"], e["raw_literal"], e["r9_present"]))
