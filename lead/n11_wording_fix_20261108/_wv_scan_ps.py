# -*- coding: utf-8 -*-
# _wv_scan_ps.py — 独立复核员同族表述扫描（只读；词表由复核员自行设计，广于撰写人词表）
import io, os, re
BASE = r"D:\Project\ra2-campaign-forge"
TARGETS = {
    "_ps":     r"lead\n11_protocol_spec_20261108\_ps_N11_MIN_OBS_PROTOCOL_SPEC.md",
    "OBS":     r"lead\n11_protocol_spec_20261108\OBSERVATION_PROTOCOL_SPEC.md",
    "DRAFT":   r"lead\n11_wording_fix_20261108\_wf_wording_fix_draft_20261109.md",
    "RULING":  r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
    "DIMMAP":  r"lead\n11_dimmap_20261108\DIM_COLUMN_MAPPING.md",
    "DM":      r"lead\n11_dimmap_20261108\_dm_DIM_MAP_20261108.md",
}
# 独立词表：比撰写人更宽（加 双射/口径/数目词/带圈数字/括号变体）
WORDS = [
    "一一对应", "一一", "双射", "对应", "配对",
    "13项", "13 项", "十三", "12项", "12 项", "十二", "11项", "11 项", "十一",
    "裁决列名", "列名", "颗粒度", "拆分", "分写", "拆为", "拆",
    "无缺漏", "缺漏", "完整", "逐项", "映射", "⑧", "⑨", "⑩", "⑪", "⑫", "⑬",
    "D-08", "D-09", "D-10",
]
OUT = os.path.join(BASE, r"lead\n11_wording_fix_20261108\_wv_scan_out.txt")
buf = []
for tag, rel in TARGETS.items():
    p = os.path.join(BASE, rel)
    lines = io.open(p, "r", encoding="utf-8").read().splitlines()
    buf.append(f"===== {tag} {rel} totalLines={len(lines)} =====")
    n = 0
    for i, ln in enumerate(lines, 1):
        hits = [w for w in WORDS if w in ln]
        if hits:
            n += 1
            buf.append(f"L{i} [{';'.join(hits)}]")
            buf.append(f"    {ln.strip()[:150]}")
    buf.append(f"-- {tag} hitLines={n} / {len(lines)}")
io.open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("written", OUT, "lines=", len(buf))
