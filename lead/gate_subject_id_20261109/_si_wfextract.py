# -*- coding: utf-8 -*-
"""_si_wfextract.py — 从 dwfrun-*.mjs 的单行 payload 字符串里还原 st_size 附近的门禁代码（只读）。"""
import re
import json
import time
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge")
ZC = ROOT / ".zcode/workflow-runs"
OUTD = ROOT / "lead/gate_subject_id_20261109"

TARGETS = {
    "dwfrun-636adfc5-7ca1-4948-a711-f8027d8de9e2.mjs": "counterpart",
    "dwfrun-a7468d6e-e9f6-4050-896a-7bff15c96903.mjs": "self(本任务)",
    "dwfrun-a4a38b66-4a6b-4794-b2da-29d141c91a60.mjs": "handoff_pack",
    "dwfrun-dcda8414-b411-49a0-bb78-3d9fab5a0a33.mjs": "s604_script_hunt",
}

RX_SIZE = re.compile(r"st_size|getsize\s*\(")


def unescape(s):
    s = s.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\x00")
    return s


def code_context(txt, pos, back=420, fwd=420):
    seg = txt[max(0, pos - back): pos + fwd]
    return unescape(seg)


t0 = time.perf_counter()
out_lines = []
for fname, tag in TARGETS.items():
    p = ZC / fname
    raw = p.read_text(encoding="utf-8", errors="replace")
    out_lines.append("#" * 100)
    out_lines.append("FILE %s  [%s]  bytes=%d" % (fname, tag, raw.stat().st_size if hasattr(raw, 'stat') else -1))
    out_lines.append("#" * 100)
    hits = [m.start() for m in RX_SIZE.finditer(raw)]
    out_lines.append("st_size/getsize 出现次数: %d" % len(hits))
    for k, pos in enumerate(hits[:12]):
        out_lines.append("--- occurrence %d @char%d ---" % (k + 1, pos))
        out_lines.append(code_context(raw, pos))
    # 找门禁相关关键词：要素检查 / gate / REQUIRED / 必含
    for kw in ("必须包含", "要素", "REQUIRED", "GATE", "PASS", "ORPHAN 不等于"):
        idxs = [m.start() for m in re.finditer(re.escape(kw), raw)][:3]
        for pos in idxs:
            out_lines.append("--- kw=%r @char%d ---" % (kw, pos))
            out_lines.append(code_context(raw, pos, back=260, fwd=380))
    out_lines.append("")

elapsed = round(time.perf_counter() - t0, 3)
out_lines.append("elapsedSec=%s" % elapsed)
text = "\n".join(out_lines)
(OUTD / "_si_wfextract_out.txt").write_text(text, encoding="utf-8")
print("written _si_wfextract_out.txt chars=%d elapsedSec=%s" % (len(text), elapsed))
print(text[:3000])
