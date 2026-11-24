# -*- coding: utf-8 -*-
r"""_rj_gate_src_dump.py — 导出 6 个 bindings=0 域的门禁源码与任务书关键词命中（只读）。"""
import json
import glob
import os
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_rejudge32_20261109"
runs = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}
base = json.loads((ROOT / "lead/gate_doc_name_fix_20261109/_dn_regate_out.json").read_text(encoding="utf-8"))
targets = ["c07_protocol_attacks_20261109", "c07_slot_20261109",
           "c07_truth_protocol_20261109", "ledger_appendix_20261108",
           "n4_yi_final_20261108", "s604_attribution_20261108"]

def gate_src(low):
    k = low.find("const GATE_CODE = [")
    if k < 0:
        return None
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

out = {}
for r in base["rows"]:
    dom = r["domain"].rstrip("/").split("/")[-1]
    if dom not in targets:
        continue
    p = runs.get(r["run"])
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    i = t.find("export const payload = ")
    v, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
    low = v.get("lowered", "")
    src = gate_src(low)
    # 任务书里所有含「绑定」「SHA256」「sess_」「格式」的句子
    ask_lines = [ln for ln in low.split("\n")
                 if any(k in ln for k in ("绑定", "SHA256", "sess_", "字节数", "复核回件"))]
    out[dom] = {"run": r["run"], "bindingRegex": r["params"]["bindingRegex"],
                "gate_src": src,
                "ask_binding_lines": ask_lines[:40],
                "low_head": low[:200]}
(WDIR / "_rj_gate_src_dump_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for dom, x in out.items():
    print("\n================", dom, "================")
    print("run", x["run"], "bindingRegex", repr(x["bindingRegex"]))
    print("--- gate_src ---")
    print(x["gate_src"])
    print("--- ask binding lines ---")
    for ln in x["ask_binding_lines"]:
        print("   ", ln[:300])
