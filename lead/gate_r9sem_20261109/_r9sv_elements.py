# -*- coding: utf-8 -*-
"""_r9sv_elements.py — 对比独立提取与撰写人提取的 32 域必现要素清单。"""
import ast
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
B = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json").read_text("utf-8"))
reg = json.loads((ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text("utf-8"))
theirs = {r["domain"]: r.get("elements", []) for r in reg["domains32"]["rows"]}

# 撰写人的严格 LOOP_RE（_r9s_regress.py:75-77）
STRICT = re.compile(
    r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)"
)
# 我 _r9sv_verify.py 里的宽松提取
LOOSE = re.compile(r"for\s+(\w+)\s+in\s+(\[[^\]]*\])\s*:\s*\n\s*if\s+\1\s+not in")
STR_Q = re.compile(r'"((?:[^"\\]|\\.)*)"')


def gsrc(low):
    k = low.find("const GATE_CODE = [")
    e = low.find("].join", k)
    if k < 0 or e < 0:
        return ""
    body = low[k + len("const GATE_CODE = ["):e]
    parts = []
    for m in STR_Q.finditer(body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts)


def extract(src, rx):
    els = []
    for m in rx.finditer(src):
        try:
            els += [x for x in ast.literal_eval(m.group(2)) if x]
        except Exception:
            pass
    return els


tot_th = tot_st = tot_lo = 0
for r in B["rows"]:
    p = ROOT / ".zcode/workflow-runs" / r["run"]
    t = p.read_text("utf-8", errors="replace")
    i = t.find("export const payload = ")
    d, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
    src = gsrc(d.get("lowered", ""))
    st = extract(src, STRICT)
    lo = extract(src, LOOSE)
    th = theirs.get(r["domain"], [])
    tot_th += len(th); tot_st += len(st); tot_lo += len(lo)
    if len(th) != len(st) or len(st) != len(lo) or th != st:
        print("DIFF", r["domain"], "their=%d strict=%d loose=%d" % (len(th), len(st), len(lo)))
        print("   their :", json.dumps(th, ensure_ascii=False)[:300])
        print("   strict:", json.dumps(st, ensure_ascii=False)[:300])
        print("   loose :", json.dumps(lo, ensure_ascii=False)[:300])
print("TOTALS their=%d strict=%d loose=%d" % (tot_th, tot_st, tot_lo))
