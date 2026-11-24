# -*- coding: utf-8 -*-
r"""_rj_final_checks.py — 三项收口核对（只读）：
(1) 任务书里「不得出现 X」与「必现要素/交付要求含 X」的自相矛盾检查；
(2) 全量谓词化门禁模拟：R9(要素)+R10/R12(断言)+R11(绑定) 对 13 问题域判定；
(3) bindings=0 的真实绑定行逐字摘录。
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
assert hashlib.sha256(PRED.read_bytes()).hexdigest() == "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
spec = importlib.util.spec_from_file_location("_rj_g7p3", PRED)
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
SECT_RE = re.compile(r"for s in (\[[^\]]+\]):")

print("========== (1) 任务书自相矛盾检查 ==========")
for dom in ("c07_slot_20261109", "c07_truth_protocol_20261109",
            "s604_script_hunt_20261109", "s604_script_gap_20261109"):
    r = next(x for x in base["rows"] if x["domain"].rstrip("/").endswith(dom))
    p = runs[r["run"]]
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    v, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
    low = v.get("lowered", "")
    print("\n---", dom, "---")
    for ln in low.split("\n"):
        if re.search(r"不得出现|不许|禁词|越权断言|必现要素|是否已填|实跑输出|改前改后|脚本存在性|可重建|已删除", ln):
            print("   ", ln.strip()[:420])

print("\n========== (2) 全量谓词化门禁模拟（13 问题域） ==========")
sim = []
for r in base["rows"]:
    if not r["gateProblems"]:
        continue
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    text = mp.read_text(encoding="utf-8", errors="replace")
    p = runs.get(r["run"])
    low = ""
    elems, sects = [], []
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
        ms = SECT_RE.search(src)
        if ms:
            try:
                sects = ast.literal_eval(ms.group(1))
            except Exception:
                pass
    r9p, r9w = g7.r9_check(text, [x for x in elems if x]) if elems else ([], [])
    r10p, r10w, r10h = g7.r10_scan(text, r["params"]["banned"])
    r12p, r12h = g7.r12_scan(text, r["params"]["banned"])
    r11p, r11w, binds = g7.r11_scan(text, mp.parent, root=ROOT)
    miss_sect = [s for s in sects if s not in text]
    allp = r9p + r10p + r12p + r11p + ["缺小节 " + s for s in miss_sect]
    rec = {"domain": dom, "problems": allp, "R9": r9p, "R10": r10p,
           "R12": r12p, "R11": r11p, "sections": miss_sect}
    sim.append(rec)
    print("%-46s verdict=%-5s R9=%d R10=%d R12=%d R11=%d 小节=%d  %s"
          % (dom, "PASS" if not allp else "FAIL", len(r9p), len(r10p),
             len(r12p), len(r11p), len(miss_sect),
             " | ".join(allp)[:160]))
fail = [x for x in sim if x["problems"]]
print("\n谓词化后仍不通过 = %d 域：" % len(fail))
for x in fail:
    print("   ", x["domain"], x["problems"])
(WDIR / "_rj_predicatized_sim_out.json").write_text(
    json.dumps({"rows": sim, "still_fail": [x["domain"] for x in fail]},
               ensure_ascii=False, indent=1), encoding="utf-8")

print("\n========== (3) bindings=0 六域的真实绑定行（含 SHA256 的原句） ==========")
for r in base["rows"]:
    if r["bindings"] != 0:
        continue
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    lines = mp.read_text(encoding="utf-8", errors="replace").split("\n")
    print("\n---", dom, "---")
    for n, ln in enumerate(lines, 1):
        if "SHA256" in ln and re.search(r"[0-9a-fA-F]{16,}", ln):
            print("   L%-4d %s" % (n, ln[:320]))
